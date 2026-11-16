"""Build a Longshot mod folder that changes what some checks give, by permanent check ID.

    python tools/build_mod.py --romfs "<romfs>" --out out\\mods --name NX2-ZOOTR KF_MIDO_CHEST_01=Item_Boomerang ...

For now only chests are supported (their item is the Drop__DropActor of the chest in the map file). For
each check every placement is changed (child and adult copies, copies in other maps), the map files are
written back compressed with the same dictionary as the original, and the resource size table (RESTBL)
gets the new sizes. Output: <out>/<name>/romfs/... mirroring the game's romfs, for Longshot's HOS_MODS.

Game fixes (--fix NAME, see FIXES and FILE_FIXES):
    bombs_without_bracelet   bombs from the bomb bag can be held without the Goron Bracelet: the bomb's lift
                             grade becomes the "no upgrade" grade of rocks, bushes, pots and Bombchus (bomb
                             flowers have their own copy of the setting and still need the bracelet)
    skippable_opening        the opening cutscene (Dm_Kokiri_0000) can be skipped like every other cutscene:
                             removes its "DisableSkip" setting (only the opening, the title screen and the
                             staff credits have it)

The game's own files are only read. The output contains modified game files: it must never be committed
or shared (out/ is ignored by git).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from formats import zstd, byml, restbl, sarc  # noqa: E402
from logic.world import World  # noqa: E402

RESTBL_PATH = os.path.join('System', 'Resource', 'ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs')
SUPPORTED = {'chest'}
# name -> (actor pack, file inside the pack, key, value it must have now, new value)
LIFT_GRADE_NO_UPGRADE = 3069107721      # small rocks, bushes, pots, Cuccos, Bombchus
LIFT_GRADE_BRACELET = 3655598229        # bombs and bomb flowers
FIXES = {
    'bombs_without_bracelet': ('Pack/Actor/Item_Bomb.pack',
                               'Component/LiftableParam/Item_Bomb.game__component__LiftableParam.bgyml',
                               'LiftGrade', LIFT_GRADE_BRACELET, LIFT_GRADE_NO_UPGRADE),
}
# name -> (BYML file, path of keys to the entry to remove, value it must have now)
FILE_FIXES = {
    'skippable_opening': (
        'Event/EventSetting/EventSettingComponentList/Dm_Kokiri_0000.engine__event__EventSettingComponentList.bgyml',
        ['Components', 'SkipSetting'],
        '?Event/EventSetting/EventSettingComponent/SkipSetting/DisableSkip.engine__event__SkipSetting.bgyml'),
}
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
                if not p['actor'].startswith('Obj_TBox') or p['actor'].startswith('Obj_TBoxPedestal'):
                    raise SystemExit('%s: placement %s is a %s, not a chest' % (cid, p['hash'], p['actor']))
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


def patch_pack(pack_data, inner, key, expected, value):
    """change one top-level value of a BYML file inside an actor pack; returns (new pack data, inner sizes)"""
    archive = sarc.Sarc.read(pack_data)
    if inner not in archive.files:
        raise SystemExit('%s not found in the pack' % inner)
    old_inner = archive.files[inner]
    doc = byml.loads(old_inner)
    if doc.root.get(key) != expected:
        raise SystemExit('%s: %s is %r, expected %r (game files differ from what this fix was made for)'
                         % (inner, key, doc.root.get(key), expected))
    doc.root[key] = type(doc.root[key])(value)
    new_inner = byml.dumps(doc)
    archive.files[inner] = new_inner
    new_pack = archive.write()
    # read back: only this value of this file differs
    back = sarc.Sarc.read(new_pack)
    before = sarc.Sarc.read(pack_data)
    if set(back.files) != set(before.files):
        raise SystemExit('read-back: file list of the pack changed')
    for name, data in back.files.items():
        if name != inner and data != before.files[name]:
            raise SystemExit('read-back: %s changed' % name)
    want = dict(byml.loads(old_inner).root, **{key: value})
    if byml.loads(back.files[inner]).root != want:
        raise SystemExit('read-back: %s differs from what was intended' % inner)
    return new_pack, (len(old_inner), len(new_inner))


def remove_entry(data, keys, expected):
    """remove one entry (found by its path of keys) from a BYML file; checks its current value first and that
    nothing else changed"""
    doc = byml.loads(data)
    parent = doc.root
    for k in keys[:-1]:
        parent = parent[k]
    if parent.get(keys[-1]) != expected:
        raise SystemExit('%s is %r, expected %r (game files differ from what this fix was made for)'
                         % ('/'.join(keys), parent.get(keys[-1]), expected))
    del parent[keys[-1]]
    new = byml.dumps(doc)
    want = byml.loads(data).root
    p = want
    for k in keys[:-1]:
        p = p[k]
    del p[keys[-1]]
    if byml.loads(new).root != want:
        raise SystemExit('read-back: %s differs from what was intended' % '/'.join(keys))
    return new


class Output:
    """writes changed files into the mod folder and keeps the resource size table up to date"""

    def __init__(self, romfs, mod_romfs, dicts):
        self.romfs, self.mod_romfs, self.dicts = romfs, mod_romfs, dicts
        self.rraw = open(os.path.join(romfs, RESTBL_PATH), 'rb').read()
        self.table = restbl.Restbl.read(zstd.decompress(self.rraw, dicts))
        self.sizes = []

    def read(self, path):
        """(file as stored, contents); a few game files are stored uncompressed (no .zs)"""
        plain = os.path.join(self.romfs, *path.split('/'))
        if os.path.exists(plain):
            src = open(plain, 'rb').read()
            return src, src
        src = open(os.path.join(self.romfs, *(path + '.zs').split('/')), 'rb').read()
        return src, zstd.decompress(src, self.dicts)

    def size(self, path, old_len, new_len):
        entry = self.table.get(path)
        if entry is None:
            raise SystemExit('%s is not in the resource size table' % path)
        if new_len > old_len:
            self.table.set(path, entry + new_len - old_len)
        self.sizes.append((path, old_len, new_len, entry, self.table.get(path)))

    def write(self, path, src, old, new):
        if src is old:                                   # stored uncompressed: write it the same way
            dest = os.path.join(self.mod_romfs, *path.split('/'))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'wb').write(new)
            self.size(path, len(old), len(new))
            return
        did = zstd.frame_dict_id(src)
        comp = zstd.compress(new, level=16, dictionary=self.dicts.get(did) if did else None)
        if zstd.decompress(comp, self.dicts) != new:
            raise SystemExit('compression check failed for %s' % path)
        dest = os.path.join(self.mod_romfs, *(path + '.zs').split('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(comp)
        self.size(path, len(old), len(new))

    def finish(self):
        for path, o, n, e, e2 in self.sizes:
            print('size %-70s %d -> %d bytes, table %d -> %d' % (path, o, n, e, e2))
        if any(e != e2 for *_, e, e2 in self.sizes):
            did = zstd.frame_dict_id(self.rraw)
            dest = os.path.join(self.mod_romfs, RESTBL_PATH)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'wb').write(zstd.compress(self.table.write(), level=16,
                                                 dictionary=self.dicts.get(did) if did else None))
            print('resource size table written')
        else:
            print('resource size table unchanged (not included in the mod)')


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--romfs', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--name', default='NX2-ZOOTR')
    ap.add_argument('--longshot', help='Longshot folder: also write a launcher .bat next to the mods folder')
    ap.add_argument('--fix', action='append', default=[], choices=sorted(set(FIXES) | set(FILE_FIXES)),
                    help='a game fix (see FIXES, FILE_FIXES)')
    ap.add_argument('assign', nargs='*', help='CHECK_ID=ItemActorName')
    a = ap.parse_args(argv)
    if not a.assign and not a.fix:
        ap.error('nothing to do: give CHECK_ID=Item assignments and/or --fix')
    assignments = [tuple(x.split('=', 1)) for x in a.assign]
    world = World()
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(a.romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    out = Output(a.romfs, os.path.join(a.out, a.name, 'romfs'), dicts)

    for name in a.fix:
        if name in FILE_FIXES:
            path, keys, expected = FILE_FIXES[name]
            src, old = out.read(path)
            out.write(path, src, old, remove_entry(old, keys, expected))
            print('fix %-28s %s: removed %s' % (name, path, '/'.join(keys)))
            continue
        pack, inner, key, expected, value = FIXES[name]
        src, old = out.read(pack)
        new, (old_inner, new_inner) = patch_pack(old, inner, key, expected, value)
        out.write(pack, src, old, new)
        # files inside packs have their own size table entries too
        out.size(inner, old_inner, new_inner)
        print('fix %-28s %s: %s %d -> %d' % (name, pack, key, expected, value))

    for path, changes in sorted(plan(world, assignments).items()):
        src, old = out.read(path)
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
        out.write(path, src, old, new)

    out.finish()
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
