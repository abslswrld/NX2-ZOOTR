"""Build a Longshot mod folder that changes what some checks give, by permanent check ID.

    python tools/build_mod.py --romfs "<romfs>" --out out\\mods --name NX2-ZOOTR KF_MIDO_CHEST_01=Item_Boomerang ...

For now only chests are supported (their item is the Drop__DropActor of the chest in the map file). For
each check every placement is changed (child and adult copies, copies in other maps), the map files are
written back compressed with the same dictionary as the original, and the resource size table (RESTBL)
gets the new sizes. Output: <out>/<name>/romfs/... mirroring the game's romfs, for Longshot's HOS_MODS.

The game's own files are only read. The output contains modified game files: it must never be committed
or shared (out/ is ignored by git).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from formats import zstd, byml, restbl  # noqa: E402
from logic.world import World  # noqa: E402

RESTBL_PATH = os.path.join('System', 'Resource', 'ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs')
SUPPORTED = {'chest'}
LAUNCHER = r"""@echo off
rem NX2-ZOOTR test launcher (made by tools/build_mod.py). Starts Longshot with the mods in
rem %(mods)s and saves in %(user)s:
rem your normal saves and other mod folders are not touched, and nothing is written in the Longshot folder.
set "LONGSHOT=%(longshot)s"
set "EXE=%%LONGSHOT%%\bin\longshot.exe"
if not exist "%%EXE%%" set "EXE=%%LONGSHOT%%\longshot.exe"
if not exist "%%EXE%%" (
  echo Longshot not found in %%LONGSHOT%%
  pause
  exit /b 1
)
if not exist "%(user)s" mkdir "%(user)s"
set "HOS_MODS=%(mods)s"
cd /d "%%LONGSHOT%%"
start "" "%%EXE%%" --user "%(user)s"
"""


def find_check(world, cid):
    for r in world.regions.values():
        for name, loc in r.locations.items():
            if loc.get('id') == cid:
                return r, name, loc
    raise SystemExit('unknown check ID %s' % cid)


def plan(world, assignments):
    """{map file path in romfs: {placement hash: (check id, new item, old item)}}"""
    files = {}
    for cid, item in assignments:
        r, name, loc = find_check(world, cid)
        sps = world.spots_of(r, loc)
        if not sps:
            raise SystemExit('%s has no map placement (an event): not supported yet' % cid)
        for scene, spot_id in sps:
            spot = world.checks[scene][spot_id]
            if spot['kind'] not in SUPPORTED:
                raise SystemExit('%s is a %s: only %s supported yet' % (cid, spot['kind'], ', '.join(SUPPORTED)))
            for p in spot['placements']:
                for fn in p['files']:
                    files.setdefault('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), {})[p['hash']] = (cid, item, spot['item'])
    return files


def patch_file(data, changes):
    """change Drop__DropActor of the actors with these hashes; returns (new data, {hash: old item})"""
    doc = byml.loads(data)
    found = {}
    for a in doc.root.get('Actors', []):
        h = str(int(a['Hash']))
        if h in changes:
            dyn = a.get('Dynamic')
            if dyn is None or 'Drop__DropActor' not in dyn:
                raise SystemExit('actor %s (%s) has no Drop__DropActor' % (h, a['Gyaml']))
            found[h] = dyn['Drop__DropActor']
            # identical settings are stored once in the file and shared between actors: give this actor its
            # own copy before changing it, or every chest with the same contents would change too
            dyn = type(dyn)(dyn)
            dyn['Drop__DropActor'] = changes[h][1]
            a['Dynamic'] = dyn
    missing = set(changes) - set(found)
    if missing:
        raise SystemExit('placements not found: %s' % ', '.join(sorted(missing)))
    return byml.dumps(doc), found


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--romfs', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--name', default='NX2-ZOOTR')
    ap.add_argument('--longshot', help='Longshot folder: also write a launcher .bat next to the mods folder')
    ap.add_argument('assign', nargs='+', help='CHECK_ID=ItemActorName')
    a = ap.parse_args(argv)
    assignments = [tuple(x.split('=', 1)) for x in a.assign]
    world = World()
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(a.romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    mod_romfs = os.path.join(a.out, a.name, 'romfs')

    rraw = open(os.path.join(a.romfs, RESTBL_PATH), 'rb').read()
    table = restbl.Restbl.read(zstd.decompress(rraw, dicts))
    size_changes = []

    for path, changes in sorted(plan(world, assignments).items()):
        src = open(os.path.join(a.romfs, *(path + '.zs').split('/')), 'rb').read()
        old = zstd.decompress(src, dicts)
        new, found = patch_file(old, {h: v for h, v in changes.items()})
        for h, (cid, item, expected_old) in changes.items():
            if found[h] != expected_old:
                print('  note: %s placement %s held %s (data says %s)' % (cid, h, found[h], expected_old))
            print('%-18s %s: %s -> %s' % (cid, path.split('/')[-1], found[h], item))
        # read back: only the changed values differ
        before = {str(int(x['Hash'])): x for x in byml.loads(old).root['Actors']}
        back = byml.loads(new).root['Actors']
        if len(back) != len(before):
            raise SystemExit('read-back: actor count changed in %s' % path)
        for act in back:
            h = str(int(act['Hash']))
            want = dict(before[h])
            if h in changes:
                want['Dynamic'] = dict(want['Dynamic'], Drop__DropActor=changes[h][1])
            if act != want:
                raise SystemExit('read-back: actor %s (%s) differs from what was intended' % (h, act['Gyaml']))
        did = zstd.frame_dict_id(src)
        comp = zstd.compress(new, level=16, dictionary=dicts.get(did) if did else None)
        if zstd.decompress(comp, dicts) != new:
            raise SystemExit('compression check failed for %s' % path)
        dest = os.path.join(mod_romfs, *(path + '.zs').split('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(comp)
        entry = table.get(path)
        if entry is None:
            raise SystemExit('%s is not in the resource size table' % path)
        grown = len(new) - len(old)
        if grown > 0:
            table.set(path, entry + grown)
        size_changes.append((path, len(old), len(new), entry, table.get(path)))

    for path, o, n, e, e2 in size_changes:
        print('size %-55s %d -> %d bytes, table %d -> %d' % (path, o, n, e, e2))
    if any(e != e2 for *_, e, e2 in size_changes):
        did = zstd.frame_dict_id(rraw)
        dest = os.path.join(mod_romfs, RESTBL_PATH)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(zstd.compress(table.write(), level=16, dictionary=dicts.get(did) if did else None))
        print('resource size table written')
    print('mod folder:', os.path.join(a.out, a.name))
    if a.longshot:
        bat = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'Launch NX2-ZOOTR test.bat')
        mods = os.path.abspath(a.out)
        user = os.path.join(os.path.dirname(mods), 'user')
        with open(bat, 'w', encoding='ascii', newline='\r\n') as f:
            f.write(LAUNCHER % {'longshot': os.path.abspath(a.longshot), 'mods': mods, 'user': user})
        print('launcher:', bat)


if __name__ == '__main__':
    main(sys.argv[1:])
