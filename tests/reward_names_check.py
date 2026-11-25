"""Stones' and Medallions' names in colour test (tools/build_mod.py: REWARD_TEMPLE, reward_name_lines,
change_messages; phase 1, part 7).

A placed Spiritual Stone or Medallion says its name in its temple's colour in the get window, the colours the
keys have (decision 40): Kokiri Emerald and Forest Medallion green, Goron Ruby and Fire Medallion red, Zora
Sapphire and Water Medallion blue, Spirit Medallion orange, Shadow Medallion purple (the user, 2026-11-24). The
Light Medallion has no temple and keeps its text.

Read from the game's own files: the nine items' names and get messages in every language, and where the name
stands in the message. Then the coloured texts, what is left alone, and whole builds read back from the mod
folder. Only reads the game; the builds go to a temporary folder that is removed again.

    python tests/reward_names_check.py "C:\\...\\romfs"
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
import dungeon_keys  # noqa: E402
from formats import zstd, byml, sarc, msbt  # noqa: E402

FILE = 'ActorMsg/PouchContent.msbt'
ENGLISH = 'USen.Product.110'
WANTED = {'Item_Stone_Forest': ('Kokiri Emerald', 3), 'Item_Medal_Forest': ('Forest Medallion', 3),
          'Item_Stone_Fire': ('Goron Ruby', 0), 'Item_Medal_Fire': ('Fire Medallion', 0),
          'Item_Stone_Water': ('Zora Sapphire', 'blue'), 'Item_Medal_Water': ('Water Medallion', 'blue'),
          'Item_Medal_Spirit': ('Spirit Medallion', 'orange'), 'Item_Medal_Shadow': ('Shadow Medallion', 'purple')}
LIGHT = 'Item_Medal_Light'
SAMPLE = [('KF_MIDO_CHEST_01', 'Item_Medal_Forest'), ('KF_MIDO_CHEST_02', 'Item_Stone_Fire'),
          ('KF_MIDO_CHEST_03', 'Item_Medal_Water'), ('KF_MIDO_CHEST_04', 'Item_Medal_Shadow'),
          ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01', 'Item_Medal_Spirit'), ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02', LIGHT)]
GAME_ONLY = [('KF_MIDO_CHEST_01', 'Item_Stone_Forest'), ('KF_MIDO_CHEST_02', 'Item_Medal_Fire')]   # green, red


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def coloured(name, number):
    return dungeon_keys.colour_tag(number) + name + dungeon_keys.colour_tag(dungeon_keys.COLOUR_END)


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path, root=romfs):
        p = os.path.join(root, *path.split('/'))
        if os.path.exists(p):
            return open(p, 'rb').read()
        return zstd.decompress(open(p + '.zs', 'rb').read(), d) if os.path.exists(p + '.zs') else None

    def texts_of(lang, root=romfs):
        data = plain('Mals/%s.sarc' % lang, root)
        if data is None:
            return None, None
        m = msbt.Msbt.read(sarc.Sarc.read(data).files[FILE])
        return dict(m.texts), m.encoding

    good = True
    langs = sorted(f[:-len('.sarc.zs')] for f in os.listdir(os.path.join(romfs, 'Mals')) if f.endswith('.sarc.zs'))
    numbers = {item: dungeon_keys.colour_number(c) for item, (_, c) in WANTED.items()}

    # ---- the game's files, and the choice
    good &= check('each stone and Medallion has its temple\'s colour (decision 40): green, red, blue, orange, purple; '
                  'the Light Medallion has none',
                  {i: dungeon_keys.COLOURS[t] for i, t in build_mod.REWARD_TEMPLE.items()}
                  == {i: c for i, (_, c) in WANTED.items()} and LIGHT not in build_mod.REWARD_TEMPLE
                  and LIGHT in build_mod.REWARD_ITEMS)
    en, enc = texts_of(ENGLISH)
    good &= check('the game\'s English: the remake\'s names, and "You were entrusted with the <name>!" for each',
                  all(build_mod.msg_plain(en[i + '_Name'], enc) == n
                      and en[i + '_GetMessage'] == 'You were entrusted with the %s!\x00' % n
                      for i, (n, _) in WANTED.items()), {i: en[i + '_GetMessage'] for i in WANTED})

    # ---- the coloured texts
    lines = build_mod.reward_name_lines(en, numbers, enc)
    good &= check('English: only the name is coloured, with the colour\'s number, and the text\'s own colour after it',
                  lines == {i + '_GetMessage': 'You were entrusted with the %s!\x00' % coloured(n, numbers[i])
                            for i, (n, _) in WANTED.items()}, lines)
    counts, wrong = {}, []
    for lang in langs:
        texts, encoding = texts_of(lang)
        got = build_mod.reward_name_lines(texts, numbers, encoding)
        counts[lang[:4]] = len(got)
        for label, text in got.items():
            item = label[:-len('_GetMessage')]
            before = texts[label]
            start, end = dungeon_keys.colour_tag(numbers[item]), dungeon_keys.colour_tag(dungeon_keys.COLOUR_END)
            # taking the two tags out gives the game's text; the coloured part is the item's name
            if (text.count(start) != 1 or text.replace(start, '', 1).replace(end, '', 1) != before
                    or text.split(start)[1].split(end)[0].lower()
                    != build_mod.msg_plain(texts[item + '_Name'], encoding).lower()):
                wrong.append((lang, label))
    good &= check('every language keeps its own text: the name is coloured where it stands in the message, all 8 '
                  'in %d of %d languages' % (sum(1 for c in counts.values() if c == 8), len(langs)),
                  not wrong and all(c in (0, 8) for c in counts.values()) and counts['USen'] == 8, (counts, wrong))
    ja, ja_enc = texts_of('JPja.Product.110')
    good &= check('  Japanese is left as it is: its messages have reading marks (tag 0,0) tied to the name',
                  counts.get('JPja') == 0
                  and any(not isinstance(x, str) and tuple(x[:2]) == build_mod.RUBY_TAG
                          for x in msbt.tags(ja['Item_Medal_Forest_GetMessage'], ja_enc)), counts)
    good &= check('an item with no texts is refused',
                  _refused(build_mod.reward_name_lines, en, {'Item_Nothing': 3}, enc) is not None)

    # ---- whole builds
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        said, folder = run('names', *['%s=%s' % x for x in SAMPLE])
        built, _ = texts_of(ENGLISH, folder)
        placed = [i for _, i in SAMPLE if i in WANTED]
        good &= check('a build with five of them and the Light Medallion placed: those five English messages are '
                      'coloured, the Light Medallion\'s and the other three are the game\'s',
                      built is not None
                      and all(built[i + '_GetMessage'] == lines[i + '_GetMessage'] for i in placed)
                      and all(built[i + '_GetMessage'] == en[i + '_GetMessage']
                              for i in list(WANTED) + [LIGHT] if i not in placed)
                      and {k: v for k, v in built.items() if not k.endswith('_GetMessage')}
                      == {k: v for k, v in en.items() if not k.endswith('_GetMessage')})
        table = sarc.Sarc.read(plain(dungeon_keys.COLOUR_PACK, folder)).files[dungeon_keys.COLOUR_TABLE]
        rows = byml.loads(table).root[dungeon_keys.COLOUR_LIST]
        rgb = lambda r: tuple(int(round(float(r.get(k, 0)))) for k in ('Red', 'Green', 'Blue'))   # noqa: E731
        good &= check('  the game\'s list of text colours has blue, orange and purple in their places (as for keys)',
                      all(rgb(rows[dungeon_keys.OUR_COLOURS[c][0]]) == tuple(dungeon_keys.OUR_COLOURS[c][1])
                          for c in ('blue', 'orange', 'purple')) and 'languages' in said,
                      [rgb(r) for r in rows])
        _, plain_folder = run('game', *['%s=%s' % x for x in GAME_ONLY])
        built2, _ = texts_of(ENGLISH, plain_folder)
        good &= check('a build with only green and red names changes the two messages and leaves the list of text '
                      'colours alone (both are the game\'s own colours)',
                      built2 is not None
                      and all(built2[i + '_GetMessage'] == lines[i + '_GetMessage'] for _, i in GAME_ONLY)
                      and plain(dungeon_keys.COLOUR_PACK, plain_folder) is None)
        _, none = run('none', 'KF_MIDO_CHEST_01=Item_Boomerang')
        good &= check('a build with none of them placed writes no message archive',
                      plain('Mals/%s.sarc' % ENGLISH, none) is None)

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


def _refused(fn, *args):
    try:
        fn(*args)
    except SystemExit as e:
        return str(e)
    return None


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
