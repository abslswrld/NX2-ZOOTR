"""Size rule check: the rules of tools/sizes.py against the resource size table entry of every game file they
cover (loose files and the files inside every pack). Reads only; takes several minutes (every pack is read).

    python tests/size_check.py "C:\\...\\romfs"

A rule must never give less than the game's own entry. Prints, per kind: the files checked, how many the rule
matches exactly, and the worst case either way. For the types of sizes.STRUCTS: the game's files with the same
lists must all have the same headroom.
"""
import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

from formats import zstd, sarc, restbl  # noqa: E402
import sizes  # noqa: E402

TABLE = 'System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs'
# the game files whose entry is larger than their kind's rule (an edited one keeps its own headroom:
# sizes.entry's `ref`)
LARGER = {
    'Effect/static.Nin_Ounce_NVN2.vsetb.byml': 3872,
    'RSDB/ActorInfo.Product.111.rstbl.byml': 2800,
    'Drop/DropSubTable/Drop_Test_Pot_Normal.game__drop__DropSubTable.bgyml': 4,
}


def covered(path):
    k = sizes.kind(path)
    return (k in sizes.PLAIN or k == 'ainb' or (k == 'sarc' and path.startswith('Mals/'))
            or (k == 'bntx' and path.startswith('Tex/')) or (k == 'bgyml' and sizes.bgyml_type(path) in sizes.BGYML)
            or (k == 'bgyml' and sizes.bgyml_type(path) in sizes.STRUCTS))


def main(romfs):
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    table = restbl.Restbl.read(zstd.decompress(open(os.path.join(romfs, *TABLE.split('/')), 'rb').read(), dicts))
    stats = collections.defaultdict(lambda: [0, 0, 0, 0, None, None])   # files, exact, most below, most above
    larger = {}
    structs = collections.defaultdict(lambda: collections.defaultdict(set))   # type -> lists -> headrooms
    seen = {}
    failed = []

    def check(path, data):
        if seen.get(path) == len(data) or not covered(path):
            return
        seen[path] = len(data)
        have = table.get(path)
        if have is None:
            return
        k = sizes.kind(path)
        k = k if k != 'bgyml' else sizes.bgyml_type(path)
        if k in sizes.STRUCTS:
            lists = tuple(sorted((w, n) for w, n in sizes.containers(data).items() if not w.endswith('{}')))
            structs[k][lists].add(have - sizes.size32(len(data)))
            return
        s = stats[k]
        s[0] += 1
        try:
            need = sizes.rule(path, data)
        except sizes.Unknown as e:
            failed.append(str(e))
            return
        s[1] += need == have
        if have > need:
            larger[path] = have - need
        if have - need > s[2]:
            s[2], s[4] = have - need, path
        if need - have > s[3]:
            s[3], s[5] = need - have, path

    for folder, _, names in os.walk(romfs):
        for fn in names:
            full = os.path.join(folder, fn)
            path = os.path.relpath(full, romfs).replace(os.sep, '/')
            if path.endswith('.zs'):
                path = path[:-3]
            pack = path.endswith('.pack')
            if not pack and not covered(path):
                continue
            data = open(full, 'rb').read()
            if fn.endswith('.zs'):
                data = zstd.decompress(data, dicts)
            check(path, data)
            if pack:
                for inner, d in sarc.Sarc.read(data).files.items():
                    check(inner, d)

    good = not failed and larger == LARGER
    for k, (n, exact, below, above, pb, pa) in sorted(stats.items()):
        ok = below == 0 or pb in LARGER
        good &= ok
        print('%-44s %6d files, %6d exact; rule below the game\'s entry by at most %d%s; above by at most %d%s  %s'
              % (k, n, exact, below, ' (%s)' % pb if pb else '', above, ' (%s)' % pa if pa else '',
                 'OK' if ok else 'FAILED'))
    for k, groups in sorted(structs.items()):
        differ = sum(1 for rooms in groups.values() if len(rooms) > 1)
        good &= not differ
        print('%-44s %6d different sets of lists; with files of different headroom: %d  %s'
              % (k, len(groups), differ, 'FAILED' if differ else 'OK'))
    for line in failed:
        print('FAILED', line)
    for path, d in sorted(larger.items()):
        print('%s: entry %d above the rule%s' % (path, d, '' if LARGER.get(path) == d else '  NOT EXPECTED'))
    print('size rules:', 'OK' if good else 'FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
