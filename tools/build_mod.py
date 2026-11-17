"""Build a Longshot mod folder that changes what some checks give, by permanent check ID.

    python tools/build_mod.py --romfs "<romfs>" --out out\\mods --name NX2-ZOOTR KF_MIDO_CHEST_01=Item_Boomerang ...

Supported: chests and pots (their item is their Drop__DropActor in the map file) and freestanding items
(the actor type itself is the item: it is replaced). For
each check every placement is changed (child and adult copies, copies in other maps; a check made for one
age, "age" in its data, only has that age's), the map files are
written back compressed with the same dictionary as the original, and the resource size table (RESTBL)
gets the new sizes. Output: <out>/<name>/romfs/... mirroring the game's romfs, for Longshot's HOS_MODS.

Game fixes (--fix NAME, see FIXES and FILE_FIXES):
    bombs_without_bracelet   bombs from the bomb bag can be held without the Goron Bracelet: the bomb's lift
                             grade becomes the "no upgrade" grade of rocks, bushes, pots and Bombchus (bomb
                             flowers have their own copy of the setting and still need the bracelet)
    magic_is_separate        magic items (Lens of Truth, Din's Fire, Farore's Wind, Nayru's Love, magic arrows)
                             no longer give the magic meter; only the Great Fairy's blessings do
                             (Item_FairyBless_MP: magic, Item_FairyBless_MPDouble: double magic)
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

import ground_items  # noqa: E402
from formats import zstd, byml, restbl, sarc  # noqa: E402
from logic.world import World  # noqa: E402

RESTBL_PATH = os.path.join('System', 'Resource', 'ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs')
SUPPORTED = {'chest', 'pot', 'freestanding'}
# name -> (actor pack, file inside the pack, key, value it must have now, new value)
LIFT_GRADE_NO_UPGRADE = 3069107721      # small rocks, bushes, pots, Cuccos, Bombchus
LIFT_GRADE_BRACELET = 3655598229        # bombs and bomb flowers
FIXES = {
    'bombs_without_bracelet': ('Pack/Actor/Item_Bomb.pack',
                               'Component/LiftableParam/Item_Bomb.game__component__LiftableParam.bgyml',
                               'LiftGrade', LIFT_GRADE_BRACELET, LIFT_GRADE_NO_UPGRADE),
}
# Some chests play a special event when opened (their GetEventName), made for their original item. When the
# item changes: 'remove' it (the chest then opens like any other) or 'keep' it. A chest with an event not
# listed here stops the build, so every one gets a decision.
CHEST_EVENTS = {
    'Get_StoneOfForest_GetSword': ('remove', 'plays Dm_Kokiri_0063, which gives and equips the Kokiri Sword '
                                             '(found in game: the sword came with any item; removed and '
                                             'retested 2026-11-16: slingshot only, no sword)'),
    'KokiriForest_TreasureBox_NaviChatOff': ('keep', 'Mido\'s chests: tested in game with four other items, harmless'),
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
    """a check by its permanent ID, or by its name for areas that have no IDs yet"""
    for r in world.regions.values():
        for name, loc in r.locations.items():
            if loc.get('id') == cid:
                return r, name, loc
    for r in world.regions.values():
        for name, loc in r.locations.items():
            if name == cid:
                if loc.get('id'):
                    raise SystemExit('%r has a permanent ID: use %s' % (name, loc['id']))
                return r, name, loc
    raise SystemExit('unknown check ID or name %s' % cid)


def _right_actor(kind, actor):
    if kind == 'chest':
        return actor.startswith('Obj_TBox') and not actor.startswith('Obj_TBoxPedestal')
    if kind == 'pot':
        return actor.startswith('Obj_Pot')
    return True                                       # freestanding: the actor is the item


def plan(world, assignments, on_ground=lambda item: item):
    """{map file path in romfs: {placement hash: (check id, new item, old item, kind)}}.
    on_ground(item): the actor to use where the item lies on the ground (freestanding items, pot drops)"""
    files = {}
    for cid, item_given in assignments:
        r, name, loc = find_check(world, cid)
        sps = world.spots_of(r, loc)
        if not sps:
            raise SystemExit('%s has no map placement (an event): not supported yet' % cid)
        for scene, spot_id, p in world.placements_of(r, loc):
            spot = world.checks[scene][spot_id]
            if spot['kind'] not in SUPPORTED:
                raise SystemExit('%s is a %s: only %s supported yet' % (cid, spot['kind'], ', '.join(sorted(SUPPORTED))))
            item = on_ground(item_given) if spot['kind'] in ('freestanding', 'pot') else item_given
            if not _right_actor(spot['kind'], p['actor']):
                raise SystemExit('%s: placement %s is a %s, not a %s' % (cid, p['hash'], p['actor'], spot['kind']))
            for fn in p['files']:
                files.setdefault('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), {})[p['hash']] = \
                    (cid, item, spot['item'], spot['kind'])
    return files


def patch_file(data, changes):
    """change what the actors with these hashes give: chests and pots through their Drop__DropActor (chests'
    special opening events handled by CHEST_EVENTS), freestanding items by their actor type (Gyaml);
    returns (new data, {hash: old item}, {hash: new Dynamic as intended})"""
    doc = byml.loads(data)
    found, intended = {}, {}
    for a in doc.root.get('Actors', []):
        h = str(int(a['Hash']))
        if h in changes and changes[h][3] == 'freestanding':
            found[h] = a['Gyaml']
            a['Gyaml'] = changes[h][1]
            continue
        if h in changes:
            dyn = a.get('Dynamic')
            if dyn is None or 'Drop__DropActor' not in dyn:
                raise SystemExit('actor %s (%s) has no Drop__DropActor' % (h, a['Gyaml']))
            found[h] = dyn['Drop__DropActor']
            # identical settings are stored once in the file and shared between actors: give this actor its
            # own copy before changing it, or every chest with the same contents would change too
            dyn = type(dyn)(dyn)
            dyn['Drop__DropActor'] = changes[h][1]
            event = dyn.get('GetEventName')
            if event is not None and changes[h][1] != found[h]:
                what = CHEST_EVENTS.get(event)
                if what is None:
                    raise SystemExit('%s: chest %s has the special opening event %r, not in CHEST_EVENTS yet: '
                                     'decide what to do with it first' % (changes[h][0], h, event))
                if what[0] == 'remove':
                    del dyn['GetEventName']
            a['Dynamic'] = dyn
            intended[h] = dict(dyn)
    missing = set(changes) - set(found)
    if missing:
        raise SystemExit('placements not found: %s' % ', '.join(sorted(missing)))
    return byml.dumps(doc), found, intended


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


MAGIC_BLESSINGS = ('Item_FairyBless_MP', 'Pouch_FairyBless_MP', 'Item_FairyBless_MPDouble', 'Pouch_FairyBless_MPDouble')


def magic_is_separate(data):
    """item table (RSDB/PouchActorInfo): every item that raises the magic meter (ExpansionAvility MPMaxUP:
    Lens of Truth, Din's Fire, Farore's Wind, Nayru's Love, magic arrows) stops doing so, except the Great
    Fairy's magic blessings, which become the magic items of their own"""
    doc = byml.loads(data)
    changed = []
    for i, row in enumerate(doc.root):
        if row.get('ExpansionAvility') == 'MPMaxUP' and row['__RowId'] not in MAGIC_BLESSINGS:
            row = type(row)(row)                      # own copy (shared nodes)
            del row['ExpansionAvility']
            row.pop('MPMax', None)
            doc.root[i] = row
            changed.append(row['__RowId'])
    blessings = [r['__RowId'] for r in doc.root if r['__RowId'] in MAGIC_BLESSINGS and r.get('ExpansionAvility') == 'MPMaxUP']
    if sorted(blessings) != sorted(MAGIC_BLESSINGS):
        raise SystemExit('magic blessings not found as expected: %s' % blessings)
    new = byml.dumps(doc)
    # read back: only those rows lost those two keys
    old_rows = byml.loads(data).root
    new_rows = byml.loads(new).root
    if len(old_rows) != len(new_rows):
        raise SystemExit('read-back: row count changed')
    for o, n in zip(old_rows, new_rows):
        want = dict(o)
        if o['__RowId'] in changed:
            del want['ExpansionAvility']
            want.pop('MPMax', None)
        if n != want:
            raise SystemExit('read-back: row %s differs from what was intended' % o['__RowId'])
    return new, changed


# name -> (file, function(data) -> (new data, list of what changed))
TABLE_FIXES = {
    'magic_is_separate': ('RSDB/PouchActorInfo.Product.111.rstbl.byml', magic_is_separate),
}


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
        self.sizes = {}          # path -> (original length, new length, original entry, new entry)
        self.written = {}        # path -> (file as stored in the game, contents written): edited twice = read back

    def read(self, path):
        """(file as stored, contents); a few game files are stored uncompressed (no .zs); a file this build
        already changed is read back as changed"""
        if path in self.written:
            return self.written[path]
        plain = os.path.join(self.romfs, *path.split('/'))
        if os.path.exists(plain):
            src = open(plain, 'rb').read()
            return None, src                             # None: stored uncompressed
        src = open(os.path.join(self.romfs, *(path + '.zs').split('/')), 'rb').read()
        return src, zstd.decompress(src, self.dicts)

    def size(self, path, old_len, new_len):
        """keep the entry's headroom over the original file and add only what the file grew (never shrink)"""
        if path in self.sizes:
            old_len, _, entry, _ = self.sizes[path]
        else:
            entry = self.table.get(path)
            if entry is None:
                raise SystemExit('%s is not in the resource size table' % path)
        self.table.set(path, entry + max(0, new_len - old_len))
        self.sizes[path] = (old_len, new_len, entry, self.table.get(path))

    def add(self, path, new_len, like, like_len):
        """entry for a file new to the game: the headroom of a similar game file (`like`, `like_len` bytes)"""
        if self.table.get(path) is not None:
            raise SystemExit('%s is already in the resource size table' % path)
        e = self.table.get(like)
        if e is None:
            raise SystemExit('%s is not in the resource size table' % like)
        self.table.set(path, e - like_len + new_len)
        self.sizes[path] = (0, new_len, 0, self.table.get(path))

    def write_new(self, path, data, like):
        """write a file new to the game, compressed like the game file `like`"""
        src = open(os.path.join(self.romfs, *(like + '.zs').split('/')), 'rb').read()
        did = zstd.frame_dict_id(src)
        comp = zstd.compress(data, level=16, dictionary=self.dicts.get(did) if did else None)
        if zstd.decompress(comp, self.dicts) != data:
            raise SystemExit('compression check failed for %s' % path)
        dest = os.path.join(self.mod_romfs, *(path + '.zs').split('/'))
        if os.path.exists(os.path.join(self.romfs, *(path + '.zs').split('/'))):
            raise SystemExit('%s already exists in the game' % path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(comp)

    def write(self, path, src, old, new):
        self.written[path] = (src, new)
        if src is None:                                  # stored uncompressed: write it the same way
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
        for path, (o, n, e, e2) in sorted(self.sizes.items()):
            print('size %-70s %d -> %d bytes, table %d -> %d' % (path, o, n, e, e2))
        if any(e != e2 for o, n, e, e2 in self.sizes.values()):
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
    ap.add_argument('--fix', action='append', default=[],
                    choices=sorted(set(FIXES) | set(FILE_FIXES) | set(TABLE_FIXES)),
                    help='a game fix (see FIXES, FILE_FIXES, TABLE_FIXES)')
    ap.add_argument('assign', nargs='*', help='CHECK_ID=ItemActorName')
    a = ap.parse_args(argv)
    if not a.assign and not a.fix:
        ap.error('nothing to do: give CHECK_ID=Item assignments and/or --fix')
    assignments = [tuple(x.split('=', 1)) for x in a.assign]
    world = World()
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(a.romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    out = Output(a.romfs, os.path.join(a.out, a.name, 'romfs'), dicts)

    for name in a.fix:
        if name in TABLE_FIXES:
            path, fn = TABLE_FIXES[name]
            src, old = out.read(path)
            new, changed = fn(old)
            out.write(path, src, old, new)
            print('fix %-28s %s: %d rows changed (%s)' % (name, path, len(changed), ', '.join(changed)))
            continue
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

    # items that lie on the ground (freestanding, pot drops) and only exist as the model shown when received
    # get a ground version (tools/ground_items.py)
    grounds = {}

    def plain(path):
        return out.read(path)[1]

    def on_ground(item):
        kind = ground_items.kind_of(plain, item)
        if kind == 'ground':
            return item
        if kind == 'item':
            return grounds.setdefault(item, ground_items.ground_name(item))
        raise SystemExit('%s: not something that can lie on the ground, and no ground version can be made' % item)

    for path, changes in sorted(plan(world, assignments, on_ground).items()):
        src, old = out.read(path)
        new, found, _ = patch_file(old, {h: v for h, v in changes.items()})
        for h, (cid, item, expected_old, kind) in changes.items():
            if found[h] != expected_old:
                print('  note: %s placement %s held %s (data says %s)' % (cid, h, found[h], expected_old))
            print('%-18s %s: %s -> %s' % (cid, path.split('/')[-1], found[h], item))
        # read back: only the changed values differ (worked out again here from the original, not from
        # what patch_file did)
        before = {str(int(x['Hash'])): x for x in byml.loads(old).root['Actors']}
        back = byml.loads(new).root['Actors']
        if len(back) != len(before):
            raise SystemExit('read-back: actor count changed in %s' % path)
        for act in back:
            h = str(int(act['Hash']))
            want = dict(before[h])
            if h in changes and changes[h][3] == 'freestanding':
                want['Gyaml'] = changes[h][1]
            elif h in changes:
                dyn = dict(want['Dynamic'], Drop__DropActor=changes[h][1])
                ev = dyn.get('GetEventName')
                if ev is not None and changes[h][1] != found[h] and CHEST_EVENTS[ev][0] == 'remove':
                    del dyn['GetEventName']
                    print('%-18s   special opening event %s removed' % (changes[h][0], ev))
                want['Dynamic'] = dyn
            if act != want:
                raise SystemExit('read-back: actor %s (%s) differs from what was intended' % (h, act['Gyaml']))
        out.write(path, src, old, new)

    new_rows = {}
    tpl_pack_path = ground_items.pack_path(ground_items.TEMPLATE)
    tpl_pack = plain(tpl_pack_path)
    tpl_ap = sarc.Sarc.read(tpl_pack).files[ground_items.ap_path(ground_items.TEMPLATE)]
    for item, name in sorted(grounds.items()):
        got, pack, new_inner, rows = ground_items.build(
            item, plain, lambda t: byml.loads(plain(ground_items.table_path(t))).root,
            lambda project: os.path.exists(os.path.join(a.romfs, 'Model', project + '.anim.bfres.zs')))
        assert got == name
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=tpl_pack_path)
        out.add(path, len(pack), tpl_pack_path, len(tpl_pack))
        tpl_files = sarc.Sarc.read(tpl_pack).files
        for inner, data in new_inner.items():
            like = (ground_items.anim_param_path(ground_items.TEMPLATE) if 'AnimationParam' in inner
                    else ground_items.pouch_param_path(ground_items.TEMPLATE) if 'PouchContentParam' in inner
                    else ground_items.ap_path(ground_items.TEMPLATE))
            out.add(inner, len(data), like, len(tpl_files[like]))
        for inner in sarc.Sarc.read(pack).files:          # every file of the pack has a size entry
            if out.table.get(inner) is None:
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        print('ground version %-22s for %s (%d bytes)' % (name, item, len(pack)))
    for t, rws in sorted(new_rows.items()):
        path = ground_items.table_path(t)
        src, old = out.read(path)
        out.write(path, src, old, ground_items.add_rows(old, rws))
        print('table %-16s %d rows added' % (t, len(rws)))

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
