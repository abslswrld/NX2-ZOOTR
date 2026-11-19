"""Checking chest test: what tools/build_mod.py does with the game's checking chests (Obj_TBox_A_06) and with a
progressive pair, on the game's own map files. Reads only; writes nothing.

    python tests/chest_check.py "C:\\...\\romfs"
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
from formats import zstd, byml, restbl  # noqa: E402

MIDO = 'Banc/KokiriForest/KokiriForest_Child_Dynamic.bcett.byml'
MIDO_CHESTS = ('12786193094758345086', '10831981390482426294')      # KF_MIDO_CHEST_01, _02
PAIR = ('Item_Scale_Silver', 'Item_Scale_Gold')


def check(name, ok):
    print('%-74s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda path: zstd.decompress(open(path, 'rb').read(), d)   # noqa: E731
    table = restbl.Restbl.read(rd(os.path.join(romfs, build_mod.RESTBL_PATH)))
    good = True

    # every game map: the size rule, and its checking chests given an item
    rule, chests, plain = True, 0, 0
    for f in sorted(glob.glob(os.path.join(romfs, 'Banc', '**', '*.bcett.byml.zs'), recursive=True)):
        rel = os.path.relpath(f, romfs).replace(os.sep, '/')[:-3]
        old = rd(f)
        rule &= table.get(rel) == build_mod.map_entry(len(old))
        before = {str(int(a['Hash'])): a for a in byml.loads(old).root.get('Actors', [])}
        mine = [h for h, a in before.items() if a['Gyaml'] in build_mod.PLAIN_CHEST]
        if not mine:
            continue
        chests += len(mine)
        new, found, _ = build_mod.patch_file(old, {h: ('TEST', 'Item_Boomerang', None, 'chest') for h in mine})
        for a in byml.loads(new).root['Actors']:
            h = str(int(a['Hash']))
            want = dict(before[h])
            if h in mine:
                want['Gyaml'] = build_mod.PLAIN_CHEST[want['Gyaml']]
                want['Dynamic'] = dict({k: v for k, v in want['Dynamic'].items()
                                        if k not in build_mod.CHECK_SETTINGS}, Drop__DropActor='Item_Boomerang')
                plain += a == want
            elif a != want:
                plain = -1000
    good &= check('map files: every size entry is the length rounded up to 32, plus 264', rule)
    good &= check('the game has 9 checking chests', chests == 9)
    good &= check('given an item, each becomes an ordinary chest without its check; nothing else changes',
                  plain == chests)

    # a progressive pair in two of Mido's chests
    old = rd(os.path.join(romfs, *MIDO.split('/')) + '.zs')
    before = {str(int(a['Hash'])): a for a in byml.loads(old).root['Actors']}
    new, found, _ = build_mod.patch_file(
        old, {h: ('TEST', PAIR[0], None, 'chest') for h in MIDO_CHESTS}, {h: PAIR for h in MIDO_CHESTS})
    ok = True
    for a in byml.loads(new).root['Actors']:
        h = str(int(a['Hash']))
        want = dict(before[h])
        if h in MIDO_CHESTS:
            want['Gyaml'] = 'Obj_TBox_A_06'
            want['Dynamic'] = dict(want['Dynamic'], Drop__DropActor=PAIR[0], Drop__CheckActor=PAIR[0],
                                   Drop__DropActor_Substitute=PAIR[1])
        ok &= a == want
    good &= check('progressive pair: two of Mido\'s chests become checking chests; nothing else changes', ok)
    good &= check('progressive pair: the same settings as the game\'s own checking chests',
                  all(set(a['Dynamic']) - {'GetEventName'} == {'Drop__CheckActor', 'Drop__DropActor',
                                                               'Drop__DropActor_Substitute'}
                      for a in byml.loads(new).root['Actors'] if str(int(a['Hash'])) in MIDO_CHESTS))
    try:
        build_mod.patch_file(old, {'16757992849254467386': ('TEST', PAIR[0], None, 'chest')},
                             {'16757992849254467386': PAIR})
        refused = False
    except SystemExit:
        refused = True
    good &= check('progressive pair: refused in a big chest (the Kokiri Sword chest)', refused)

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
