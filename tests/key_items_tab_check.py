"""Key Items tab test (tools/build_mod.py --fix key_items_tab_open; phase 1, part 7).

The pause menu's Key Items tab (Spiritual Stones and Medallions) is "???" until Link owns a stone: the game's
program opens it when Link owns the first item of any row of the pause menu table's StoneArray (read from the
program; in game 2026-11-24 a Medallion alone left it closed and the Kokiri Emerald opened it). The fix adds a
row for each of the two green tunics every file starts with.

Read from the game's own files: the table's lists, the three stones' rows and the six Medallions' rows, that
rows naming no model and no place exist in the game (NoDisplayArray), and that the game's own new-file list
gives both tunics. Then the fix read back, its size table entry, and a whole build read back from the mod
folder. Only reads the game; the build goes to a temporary folder that is removed again.

    python tests/key_items_tab_check.py "C:\\...\\romfs"
"""
import contextlib
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import sizes  # noqa: E402
import start_state  # noqa: E402
from formats import zstd, byml, restbl  # noqa: E402

FIX = 'key_items_tab_open'
TABLE = build_mod.POUCH_TABLE
STONES = ['Item_Stone_Forest', 'Item_Stone_Fire', 'Item_Stone_Water']
MEDALS = ['Item_Medal_Light', 'Item_Medal_Forest', 'Item_Medal_Fire', 'Item_Medal_Water', 'Item_Medal_Shadow',
          'Item_Medal_Spirit']
TUNICS = ('Obj_Armor_Child_Normal', 'Armor_Adult_Normal')
GAME_ENTRY = 46824                       # the table's entry in the game's resource size table


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def firsts(rows):
    return [str(r['Actor'][0]['ActorShort']) for r in rows]


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path):
        p = os.path.join(romfs, *path.split('/'))
        return open(p, 'rb').read() if os.path.exists(p) else zstd.decompress(open(p + '.zs', 'rb').read(), d)

    good = True

    # ---- the game's files
    old = plain(TABLE)
    game = byml.loads(old).root
    good &= check('the pause menu\'s table has a list of the three Spiritual Stones (StoneArray) and one of the six '
                  'Medallions (MedalArray)',
                  firsts(game['StoneArray']) == STONES == build_mod.KEY_ITEMS_STONES
                  and firsts(game['MedalArray']) == MEDALS, (firsts(game['StoneArray']), firsts(game['MedalArray'])))
    good &= check('  every one of those nine rows names one item, the model the page shows for it and its place '
                  'on the page',
                  all(len(r['Actor']) == 1 and str(r['Actor'][0]['PouchActorShort']) == f + '_ImportantMenu'
                      and str(r['BtnName']).startswith('N_Info_')
                      for f, r in zip(STONES + MEDALS, list(game['StoneArray']) + list(game['MedalArray']))))
    good &= check('  the Medallions\' rows are marked for the adult only, the stones\' rows have no age mark (in '
                  'game the mark made no difference to the tab)',
                  all(r['Actor'][0].get('IsUsableAdult') is True and 'IsUsableChild' not in r['Actor'][0]
                      for r in game['MedalArray'])
                  and not any(k.startswith('IsUsable') for r in game['StoneArray'] for k in r['Actor'][0]))
    bare = [r for r in game['NoDisplayArray'] if 'BtnName' not in r and 'PouchActorShort' not in r['Actor'][0]]
    good &= check('  the game has rows that name no model and no place on a page (NoDisplayArray: %d of its %d)'
                  % (len(bare), len(game['NoDisplayArray'])), len(bare) >= 1, firsts(game['NoDisplayArray']))
    given = [item for item, _ in start_state.read(plain(start_state.MODULE))[0]]
    good &= check('the game\'s own new-file list gives both green tunics, the items the fix\'s rows name',
                  build_mod.KEY_ITEMS_ALWAYS == TUNICS and all(t in given for t in TUNICS), given)
    good &= check('the size rule for the table gives the game\'s entry for the game\'s file (%d)' % GAME_ENTRY,
                  sizes.rule(TABLE, old) == GAME_ENTRY, sizes.rule(TABLE, old))

    # ---- the fix
    path, fn = build_mod.TABLE_FIXES[FIX]
    new, said = fn(old)
    got = byml.loads(new).root
    good &= check('the fix adds two rows behind the stones\' three, one for each tunic, naming only the item',
                  path == TABLE and firsts(got['StoneArray']) == STONES + list(TUNICS)
                  and [dict(r) for r in got['StoneArray'][3:]] == [{'Actor': [{'ActorShort': t}]} for t in TUNICS]
                  and len(said) == 2, (firsts(got['StoneArray']), said))
    good &= check('  the stones\' rows and every other list and setting of the table are as they were',
                  got['StoneArray'][:3] == game['StoneArray']
                  and {k: v for k, v in got.items() if k != 'StoneArray'}
                  == {k: v for k, v in game.items() if k != 'StoneArray'})
    need = sizes.rule(TABLE, new)
    good &= check('  the size rule asks for more for the longer list: 1024 for each new row and each new item '
                  '(%d -> %d)' % (GAME_ENTRY, need),
                  need == GAME_ENTRY + sizes.size32(len(new)) - sizes.size32(len(old)) + 4 * 1024, need)
    twice = None
    try:
        fn(new)
    except SystemExit as e:
        twice = str(e)
    good &= check('the fix refuses a table whose StoneArray is not the game\'s three stones (here: its own output)',
                  bool(twice) and 'not as expected' in twice, twice)

    # ---- a whole build
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        said, folder = run('tab', '--fix', FIX)
        written = os.path.join(folder, *TABLE.split('/'))
        data = None
        if os.path.exists(written):
            data = open(written, 'rb').read()
        elif os.path.exists(written + '.zs'):
            data = zstd.decompress(open(written + '.zs', 'rb').read(), d)
        good &= check('a build with --fix %s writes the table, the same as the fix gives' % FIX,
                      data == new and ('fix %s' % FIX) in said, said[-300:])
        table = restbl.Restbl.read(zstd.decompress(open(os.path.join(folder, build_mod.RESTBL_PATH), 'rb').read(), d))
        good &= check('  its entry in the build\'s resource size table is what the rule asks (%d)' % need,
                      table.get(TABLE) == need, table.get(TABLE))
        _, plain_folder = run('plain', '--fix', 'bombs_without_bracelet')
        good &= check('a build without the fix does not write the table',
                      not os.path.exists(os.path.join(plain_folder, *TABLE.split('/')))
                      and not os.path.exists(os.path.join(plain_folder, *TABLE.split('/')) + '.zs'))

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
