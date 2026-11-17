"""Build a Longshot mod folder that changes what some checks give, by permanent check ID.

    python tools/build_mod.py --romfs "<romfs>" --out out\\mods --name NX2-ZOOTR KF_MIDO_CHEST_01=Item_Boomerang ...

Supported: chests and pots (their item is their Drop__DropActor in the map file; rocks and bushes get one
added), freestanding items
(the actor type itself is the item: it is replaced) and shop shelves (the shelf actor is replaced by a shop
version of the item, tools/shop_items.py, at the shelf's original price, sold once). For
each check every placement is changed (child and adult copies, copies in other maps; a check made for one
age, "age" in its data, only has that age's), the map files are
written back compressed with the same dictionary as the original, and the resource size table (RESTBL)
gets the new sizes. Output: <out>/<name>/romfs/... mirroring the game's romfs, for Longshot's HOS_MODS.

Game fixes (--fix NAME, see FIXES and FILE_FIXES):
    kokiri_shop_full_stock   the Kokiri Shop sells the same 8 shelves as a child before and after meeting the
                             Deku Tree (the "low on stock" set is removed, every shelf is open from the
                             start, the child shopkeeper greets as after the Deku Tree), and the adult
                             shopkeeper gets a shop list of its own; needed to change
                             shop shelves (each shelf's item, sold once, goes into the shopkeeper's list)
    bombchus_without_bag     Bombchus get a capacity of their own (BOMBCHU_MAX, as in the original game) and
                             no longer need the bomb bag: in the remake their maximum is the bomb bag's, so
                             without one it is 0; bomb bags stop raising and refilling them
    bombs_without_bracelet   bombs from the bomb bag can be held without the Goron Bracelet: the bomb's lift
                             grade becomes the "no upgrade" grade of rocks, bushes, pots and Bombchus (bomb
                             flowers have their own copy of the setting and still need the bracelet)
    kokiri_circle_after_dungeons
                             the rock circle by Mido's house as after the dungeons, at both ages: an adult sees
                             the same ring of 8 rocks as a child (as after the Forest Temple; before, an adult
                             saw 4 other rocks), and the Kokiri (Npc_Kokiri_008_Child) no longer stands on the
                             middle rock trying to lift it, which can be lifted (as after the Kokiri Emerald);
                             needed for items on the adult circle rocks and the middle rock
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
import shop_items  # noqa: E402
from formats import zstd, byml, restbl, sarc, evfl, ainb  # noqa: E402
from logic.world import World  # noqa: E402

RESTBL_PATH = os.path.join('System', 'Resource', 'ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs')
SUPPORTED = {'chest', 'pot', 'freestanding', 'shop', 'rock', 'bush'}
REPLACED = ('freestanding', 'shop')      # kinds whose actor itself is replaced
# kinds whose drop is usually not set in the map: the builder adds Drop__DropActor (the game itself sets it on
# some rocks and bushes elsewhere, e.g. Obj_LiftRock_A_01 in Desert Colossus, Obj_Plant_Grass_A_01 in Hyrule Field)
DROP_ADDED = ('rock', 'bush')
DROP_ON_GROUND = ('freestanding', 'pot', 'rock', 'bush')   # kinds whose item lies on the ground
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
    if kind == 'shop':
        return actor.startswith('Shop_')
    if kind == 'rock':
        return actor.startswith('Obj_LiftRock')
    if kind == 'bush':
        return actor.startswith('Obj_Plant_Grass')
    return True                                       # freestanding: the actor is the item


def plan(world, assignments, on_ground=lambda item: item, in_chest=lambda item: item,
         on_shelf=lambda item, shelf_actor: item):
    """{map file path in romfs: {placement hash: (check id, new item, old item, kind)}}.
    on_ground(item): the actor to use where the item lies on the ground (freestanding items, pot drops);
    in_chest(item): the actor a chest gives (and shows held up); on_shelf(item, actor now on the shelf): the
    shelf actor that sells the item"""
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
            if spot['kind'] in DROP_ON_GROUND:
                item = on_ground(item_given)
            elif spot['kind'] == 'chest':
                item = in_chest(item_given)
            elif spot['kind'] == 'shop':
                item = on_shelf(item_given, p['actor'])
            else:
                item = item_given
            if not _right_actor(spot['kind'], p['actor']):
                raise SystemExit('%s: placement %s is a %s, not a %s' % (cid, p['hash'], p['actor'], spot['kind']))
            old = 'Shop_' + spot['item'] if spot['kind'] == 'shop' else spot['item']   # shelf data drops 'Shop_'
            for fn in p['files']:
                files.setdefault('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), {})[p['hash']] = \
                    (cid, item, old, spot['kind'])
    return files


def patch_file(data, changes):
    """change what the actors with these hashes give: chests and pots through their Drop__DropActor (chests'
    special opening events handled by CHEST_EVENTS), freestanding items by their actor type (Gyaml);
    returns (new data, {hash: old item}, {hash: new Dynamic as intended})"""
    doc = byml.loads(data)
    found, intended = {}, {}
    for a in doc.root.get('Actors', []):
        h = str(int(a['Hash']))
        if h in changes and changes[h][3] in REPLACED:
            found[h] = a['Gyaml']
            a['Gyaml'] = changes[h][1]
            continue
        if h in changes:
            dyn = a.get('Dynamic')
            if changes[h][3] in DROP_ADDED and (dyn is None or 'Drop__DropActor' not in dyn):
                if dyn is not None and 'Drop__DropTable' in dyn:
                    raise SystemExit('actor %s (%s) drops from a drop table (%s): not supported yet'
                                     % (h, a['Gyaml'], dyn['Drop__DropTable']))
                dyn = type(dyn)(dyn) if dyn is not None else {}
                dyn['Drop__DropActor'] = None             # nothing set: found below as None
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


BOMBCHU_MAX = 50
BOMBCHU_ROW = 'Item_Bombchu'                     # the Bombchu itself; bundles and shelves give it (BundleActor)
BOMBCHU_ACTOR = 'Work/Actor/Item_Bombchu.engine__actor__ActorParam.gyml'


def bombchus_without_bag(data):
    """item table (RSDB/PouchActorInfo): Bombchus' maximum stops being the bomb bag's (MaxNumGameData: Bomb,
    SmallBagActor: the small bomb bag) and becomes a fixed number (FixedMaxNum, as the Magic Beans' 10 and the
    Gold Skulltula tokens' 100); the bomb bags stop raising (ExpansionMaxNumActor) and refilling
    (ActorFullOnlyIfIsGetWhenGetBag) Bombchus. Rows that give one Bombchu with the bag's maximum
    (Item_Bombchu, the 1-Bombchu shelf Shop_BombchuBundle_03) change the same way."""
    doc = byml.loads(data)
    rows = {r['__RowId']: r for r in doc.root}
    fixed_type = type(rows['Item_MagicBean']['FixedMaxNum'])
    want = {}
    for i, row in enumerate(doc.root):
        rid, new = row['__RowId'], None
        if 'Bombchu' in rid and row.get('MaxNumGameData') == 'Bomb':
            new = type(row)(row)
            del new['MaxNumGameData']
            new.pop('SmallBagActor', None)
            new['FixedMaxNum'] = fixed_type(BOMBCHU_MAX)
        elif (BOMBCHU_ACTOR in str(row.get('ExpansionMaxNumActor', ''))
              or row.get('ActorFullOnlyIfIsGetWhenGetBag') == BOMBCHU_ACTOR):
            new = type(row)(row)
            if 'ExpansionMaxNumActor' in new:
                kept = [x for x in str(new['ExpansionMaxNumActor']).split(',') if x != BOMBCHU_ACTOR]
                new['ExpansionMaxNumActor'] = type(row['ExpansionMaxNumActor'])(','.join(kept))
            if new.get('ActorFullOnlyIfIsGetWhenGetBag') == BOMBCHU_ACTOR:
                del new['ActorFullOnlyIfIsGetWhenGetBag']
        if new is not None:
            doc.root[i] = new
            want[rid] = dict(new)
    if BOMBCHU_ROW not in want:
        raise SystemExit('bombchus_without_bag: %s not as expected' % BOMBCHU_ROW)
    new_data = byml.dumps(doc)
    for o, n in zip(byml.loads(data).root, byml.loads(new_data).root):
        if n != want.get(o['__RowId'], dict(o)):
            raise SystemExit('read-back: row %s differs from what was intended' % o['__RowId'])
    return new_data, sorted(want)


# name -> (file, function(data) -> (new data, list of what changed))
TABLE_FIXES = {
    'bombchus_without_bag': ('RSDB/PouchActorInfo.Product.111.rstbl.byml', bombchus_without_bag),
    'magic_is_separate': ('RSDB/PouchActorInfo.Product.111.rstbl.byml', magic_is_separate),
}


# The rock circle by Mido's house (--fix kokiri_circle_after_dungeons). Its level logic module shows the ring of
# 8 rocks, and to an adult before the Forest Temple 4 other rocks instead: one AND node (adult, and the flag
# SageOfForest_IsBefore_Step08) deletes the 8 and creates the 4. Its flag input becomes "is child": an adult
# is never a child, so the AND is never true and both ages get the 8. The Kokiri who tries to lift the middle
# rock does so in his default schedule; after the Kokiri Emerald (Get_StoneOfForest_IsCompleted_Exp) his
# schedule sends him elsewhere. That schedule becomes his default. The middle rock is two rocks in one place:
# a prop with no lift setting (Obj_LiftRock_A_02, the one he acts out lifting) and a liftable one; a child
# level logic swaps the prop for the liftable rock after the Kokiri Emerald. Both get fixed values: prop
# never there, liftable rock always there.
CIRCLE_MIDDLE = 'Logic/KokiriForest_Child_Level_All_02_6960.logic.module.ainb'
CIRCLE_MIDDLE_ROCKS = {'Obj_LiftRock_A_02_2143': False, 'Obj_LiftRock_A_01_0de2': True}   # instance -> there
CIRCLE_NEEDS_FIX = ('KF_CIRCLE_ADULT_ROCK_', 'KF_CIRCLE_CENTER_ROCK')
CIRCLE_LOGIC = 'Logic/KokiriForest_Common_Level_All_01_6aaf.logic.module.ainb'
CIRCLE_FLAG = 'SageOfForest_IsBefore_Step08'
CIRCLE_KOKIRI = 'Component/AIScheduleParam/Npc_Kokiri_008_Child.game__component__AIScheduleParam.bgyml'
CIRCLE_KOKIRI_FLAG = 'Get_StoneOfForest_IsCompleted_Exp'


def circle_logic(data):
    """the AND node's flag input becomes the "is child" output of the same age node"""
    a = ainb.Ainb.read(data)
    hits = []
    for i, n in enumerate(a.nodes):
        if n.name != 'OperateAND' or not n.inputs['bool'] or n.inputs['bool'][0].sources is None:
            continue
        src = n.inputs['bool'][0].sources
        names = [a.nodes[s[0]].name for s in src]
        if names == ['HoldIsChildhoodOrAdulthood', 'HoldGameDataGetBoolSimple'] and                 a.nodes[src[1][0]].inputs['string'][0].value == CIRCLE_FLAG:
            hits.append(i)
    if len(hits) != 1:
        raise SystemExit('%s: %d AND nodes on age and %s, expected 1' % (CIRCLE_LOGIC, len(hits), CIRCLE_FLAG))
    inp = a.nodes[hits[0]].inputs['bool'][0]
    age, (flag_node, _, flags) = inp.sources[0], inp.sources[1]
    outs = [o.name for o in a.nodes[age[0]].outputs['bool']]
    if outs != ['Adulthood', 'Childhood'] or age[1] != 0:
        raise SystemExit('%s: age node not as expected: %r' % (CIRCLE_LOGIC, outs))
    inp.sources = [age, (age[0], outs.index('Childhood'), flags)]
    new = a.write()
    b = ainb.Ainb.read(new)
    if b.nodes[hits[0]].inputs['bool'][0].sources != inp.sources or len(new) != len(data)             or sum(x != y for x, y in zip(new, data)) > 4 or b.write() != new:
        raise SystemExit('read-back: %s differs from what was intended' % CIRCLE_LOGIC)
    return new, 'node %d (%s): source %d (%s) -> %d.Childhood' % (hits[0], a.nodes[hits[0]].name, flag_node,
                                                                 CIRCLE_FLAG, age[0])


def circle_middle(data):
    """the middle rock's two actors: created / deleted by fixed values instead of by the Kokiri Emerald"""
    a = ainb.Ainb.read(data)
    done = []
    for n in a.nodes:
        if n.name != 'ActorLogicLiftableActor':
            continue
        inst = next(x.value for x in n.immediates['string'] if x.name == 'InstanceName')
        if inst not in CIRCLE_MIDDLE_ROCKS:
            continue
        there = CIRCLE_MIDDLE_ROCKS[inst]
        flag = [x for x in n.inputs['bool'] if x.name in ('Logic_Create', 'Logic_Delete')]
        if len(flag) != 2 or any(x.node < 0 or x.sources is not None for x in flag) or                 {a.nodes[x.node].name for x in flag} != {'OperateAND'}:
            raise SystemExit('%s: %s not as expected' % (CIRCLE_MIDDLE, inst))
        for x in flag:
            x.node, x.param, x.flags = -1, 0, 0x1800000         # as the game's own fixed inputs
            x.value = there if x.name == 'Logic_Create' else not there
        n.links[0] = [l for l in n.links[0] if l.name not in ('Logic_Create', 'Logic_Delete')]
        n.preconditions = []
        done.append(inst)
    if sorted(done) != sorted(CIRCLE_MIDDLE_ROCKS):
        raise SystemExit('%s: middle rocks found: %r' % (CIRCLE_MIDDLE, done))
    new = ainb.Ainb.read(a.write()).write()
    b = ainb.Ainb.read(new)
    for n in b.nodes:
        inst = next((x.value for x in n.immediates['string'] if x.name == 'InstanceName'), None)
        if inst in CIRCLE_MIDDLE_ROCKS:
            got = {x.name: (x.node, x.value) for x in n.inputs['bool']}
            if got['Logic_Create'] != (-1, CIRCLE_MIDDLE_ROCKS[inst]) or                     got['Logic_Delete'] != (-1, not CIRCLE_MIDDLE_ROCKS[inst]) or n.links[0] or n.preconditions:
                raise SystemExit('read-back: %s differs from what was intended' % CIRCLE_MIDDLE)
    return new


def circle_kokiri(data):
    """the Kokiri's schedule after the Kokiri Emerald becomes his default one"""
    doc = byml.loads(data)
    hits = [c for c in doc.root['ConditionalSchedule'] if c.get('ConditionFlag') == CIRCLE_KOKIRI_FLAG]
    if len(hits) != 1 or 'Act_Lift_Rock' not in repr(doc.root['DefaultSchedule']):
        raise SystemExit('%s: schedule not as expected' % CIRCLE_KOKIRI)
    after = {k: v for k, v in hits[0].items() if k != 'ConditionFlag'}
    if sorted(after) != sorted(doc.root['DefaultSchedule']):
        raise SystemExit('%s: the schedules have different keys' % CIRCLE_KOKIRI)
    doc.root['DefaultSchedule'] = after
    new = byml.dumps(doc)
    want = byml.loads(data).root
    want['DefaultSchedule'] = {k: v for k, v in want['ConditionalSchedule'][doc.root['ConditionalSchedule'].index(
        hits[0])].items() if k != 'ConditionFlag'}
    if byml.loads(new).root != want:
        raise SystemExit('read-back: %s differs from what was intended' % CIRCLE_KOKIRI)
    return new


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


# Kokiri Shop with one set of shelves per age (--fix kokiri_shop_full_stock). What a shop sells is decided by
# its shopkeeper: its shop list (ShopParam GoodsList) has one entry per shelf, in ShopItemIndex order (the
# Recovery Heart, with no index, is 0), naming the shelf actor sold (its price), a release flag and a stock
# (-1 unlimited, 1 once). The child map has two sets of shopkeeper, shelves and boards: before meeting the
# Deku Tree (the "low on stock" shopkeeper, its own short list, two "sold out" boards) and after; the adult
# shopkeeper has no list of its own and uses the child one (a copy of the same file in its pack).
SHOP_FLAG = 'Meet_DekuTree_IsAfter_Step02_Exp'
SHOP_MAP = 'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml'
SHOP_KEEPERS = {'child': 'Npc_Kokiri_001_Shop_Child', 'adult': 'Npc_Kokiri_001_Shop_Adult'}
SHOP_LIST = 'Component/ShopParam/Npc_Kokiri_001_Shop_Child.game__component__ShopParam.bgyml'
SHOP_LIST_ADULT = 'Component/ShopParam/Npc_Kokiri_001_Shop_Adult.game__component__ShopParam.bgyml'
SHOP_STOCK_ONCE = 1
SHOP_FLOW = 'Event/EventFlow/Npc_Kokiri_001_Shop_Child.bfevfl'   # the child shopkeeper's talk
SHOP_GREETING = 'Npc_Kokiri_001_Shop_Child_Talk_Arrival'          # the switch that picks the normal greeting
FLOW_YES, FLOW_NO = 0, 1      # what a yes/no query answers in this game's event flows (0 = yes)


def _flow_links(e):
    return [x for x in [e.next, e.join] + [ev for _, ev in e.cases] + list(e.forks) if x is not None]


def flow_reachable(fc, start):
    seen, todo = [], [start]
    while todo:
        i = todo.pop(0)
        if i not in seen:
            seen.append(i)
            todo += _flow_links(fc.events[i])
    return seen


def flow_drop_unreached_subflows(fc):
    """each entry point lists the subflow / callswitch steps that can run from it: drop those no longer
    reached; returns lines saying what changed"""
    said = []
    for ep in fc.entry_points:
        can = flow_reachable(fc, ep.main)
        keep = [i for i in ep.subflows if i in can]
        if keep != ep.subflows:
            said.append('entry point %s: list %r -> %r' % (ep.name, ep.subflows, keep))
            ep.subflows = keep
    return said


def shop_greeting_edit(fc):
    """the child shopkeeper's talk (flowchart, edited in place): its one switch on meeting the Deku Tree takes
    the "after" side's normal greeting in both cases (case 1, NO, was the "low on stock / Mido" side). Skips
    only the "lost your Deku Shield?" hand-out between the switch and the greeting. Confirmed in game
    2026-11-17 (tools/evfl_test_mod.py). Returns lines saying what changed."""
    hits = [i for i, e in enumerate(fc.events)
            if e.type == 'switch' and isinstance(e.params, dict) and e.params.get('GameDataName') == SHOP_FLAG]
    if len(hits) != 1:
        raise SystemExit('%s: %d switches on %s, expected 1' % (SHOP_FLOW, len(hits), SHOP_FLAG))
    sw = fc.events[hits[0]]
    cases = dict(sw.cases)
    if sorted(cases) != [FLOW_YES, FLOW_NO]:
        raise SystemExit('%s: switch on %s: cases %r not as expected' % (SHOP_FLOW, SHOP_FLAG, sw.cases))
    hand_out = fc.events[cases[FLOW_YES]]
    if hand_out.type != 'callswitch' or hand_out.entry != 'present_DekuSheld':
        raise SystemExit('%s: the "after" side is not the Deku Shield hand-out' % SHOP_FLOW)
    greet = [ev for _, ev in hand_out.cases
             if fc.events[ev].type == 'switch' and (fc.events[ev].params or {}).get('GameDataName') == SHOP_GREETING]
    if len(greet) != 1:
        raise SystemExit('%s: normal greeting not found after the hand-out' % SHOP_FLOW)
    said = ['greeting: switch %s (%s) cases %r -> both %d' % (sw.name, SHOP_FLAG, sorted(cases.items()), greet[0])]
    sw.cases = [(FLOW_YES, greet[0]), (FLOW_NO, greet[0])]
    return said + flow_drop_unreached_subflows(fc)


def flow_write_checked(ef):
    """write an edited event flow and read it back: must be the same flow as intended"""
    fc = ef.flowchart
    new = evfl.dumps(ef)
    back = evfl.loads(new).flowchart
    if [vars(e) for e in back.events] != [vars(e) for e in fc.events]             or [vars(p) for p in back.entry_points] != [vars(p) for p in fc.entry_points]             or [vars(x) for x in back.actors] != [vars(x) for x in fc.actors]:
        raise SystemExit('read-back of an edited event flow differs from what was intended')
    return new


def _is_shop_actor(actor):
    return actor['Gyaml'].startswith(('Shop_', 'Npc_Kokiri_001_Shop'))


def shop_full_stock_map(data):
    """child map: the shop set placed before meeting the Deku Tree is removed and the set placed after it is
    always there. Returns (new data, removed hashes, hashes now always there)."""
    doc = byml.loads(data)
    keep, removed, always = [], set(), set()
    for act in doc.root['Actors']:
        pres = act.get('Presence')
        if _is_shop_actor(act) and pres is not None and pres.get('FlagName') == SHOP_FLAG:
            h = str(int(act['Hash']))
            if pres.get('IsNegation'):
                removed.add(h)
                continue
            act = type(act)(act)                      # own copy (shared nodes)
            del act['Presence']
            always.add(h)
        keep.append(act)
    if not removed or not always:
        raise SystemExit('kokiri_shop_full_stock: the two shop sets were not found as expected')
    for act in keep:                                  # nothing left may point at a removed object
        for link in act.get('Links') or []:
            if str(int(link['Dst'])) in removed:
                raise SystemExit('kokiri_shop_full_stock: %s links to a removed shop object' % act['Gyaml'])
    doc.root = type(doc.root)(doc.root)
    doc.root['Actors'] = keep
    new = byml.dumps(doc)
    want = []
    for act in byml.loads(data).root['Actors']:
        h = str(int(act['Hash']))
        if h in removed:
            continue
        want.append({k: v for k, v in act.items() if not (h in always and k == 'Presence')})
    if [dict(x) for x in byml.loads(new).root['Actors']] != want:
        raise SystemExit('read-back: %s differs from what was intended' % SHOP_MAP)
    return new, removed, always


SHOP_BOARD = 'Shop_Board_Bundle_%02d'                 # count boards: 03 05 08 10 15 20 30 50 in the game


def shop_boards(data, shelves, board_exists):
    """count boards ("x5", separate objects a shelf links to, made for its original bundle) for changed
    shelves: shelves {shelf hash: number of items it now sells}. A single item gets no board (the board and
    every link to it removed); a bundle gets the board with its own count (board_exists(name)), or none if
    the game has no such board. Returns (new data, [what changed])."""
    doc = byml.loads(data)
    acts = doc.root['Actors']
    by_hash = {str(int(a['Hash'])): a for a in acts}
    linked_from = {}
    for a in acts:
        for link in a.get('Links') or []:
            linked_from.setdefault(str(int(link['Dst'])), []).append(a)
    remove, rename, done = set(), {}, []
    for sh, count in shelves.items():
        for link in by_hash[sh].get('Links') or []:
            b = str(int(link['Dst']))
            board = by_hash.get(b)
            if board is None or not board['Gyaml'].startswith('Shop_Board_Bundle_'):
                continue
            shelf_links = [a for a in linked_from[b] if a['Gyaml'].startswith('Shop_') and str(int(a['Hash'])) != sh]
            if shelf_links:
                raise SystemExit('count board %s is shared with another shelf' % b)
            want = SHOP_BOARD % count if count > 1 and board_exists(SHOP_BOARD % count) else None
            if want is None:
                remove.add(b)
                done.append('%s board %s removed' % (by_hash[sh]['Gyaml'], board['Gyaml']))
            elif want != board['Gyaml']:
                rename[b] = want
                done.append('%s board %s -> %s' % (by_hash[sh]['Gyaml'], board['Gyaml'], want))
    new_acts = []
    for a in acts:
        h = str(int(a['Hash']))
        if h in remove:
            continue
        links = a.get('Links') or []
        if h in rename or any(str(int(l['Dst'])) in remove for l in links):
            a = type(a)(a)
            if h in rename:
                a['Gyaml'] = type(a['Gyaml'])(rename[h])
            if any(str(int(l['Dst'])) in remove for l in links):
                a['Links'] = [l for l in links if str(int(l['Dst'])) not in remove]
        new_acts.append(a)
    doc.root = type(doc.root)(doc.root)
    doc.root['Actors'] = new_acts
    new = byml.dumps(doc)
    want = []
    for a in byml.loads(data).root['Actors']:
        h = str(int(a['Hash']))
        if h in remove:
            continue
        a = dict(a)
        if h in rename:
            a['Gyaml'] = rename[h]
        if 'Links' in a:
            a['Links'] = [l for l in a['Links'] if str(int(l['Dst'])) not in remove]
        want.append(a)
    if [dict(x) for x in byml.loads(new).root['Actors']] != want:
        raise SystemExit('read-back: count boards differ from what was intended')
    return new, done


def lift_shelves(data, lifts):
    """raise shelf actors: lifts {hash: metres}; returns new data"""
    doc = byml.loads(data)
    acts = list(doc.root['Actors'])
    for i, act in enumerate(acts):
        h = str(int(act['Hash']))
        if h in lifts:
            act = type(act)(act)
            t = list(act['Translate'])
            t[1] = type(t[1])(float(t[1]) + lifts[h])
            act['Translate'] = t
            acts[i] = act
    doc.root = type(doc.root)(doc.root)
    doc.root['Actors'] = acts
    new = byml.dumps(doc)
    for o, n in zip(byml.loads(data).root['Actors'], byml.loads(new).root['Actors']):
        h = str(int(o['Hash']))
        want = dict(o)
        if h in lifts:
            want['Translate'] = [o['Translate'][0], float(o['Translate'][1]) + lifts[h], o['Translate'][2]]
        got = dict(n)
        if h in lifts:
            got['Translate'] = [float(x) for x in n['Translate']]
            want['Translate'] = [float(x) for x in want['Translate']]
            if any(abs(a - b) > 1e-4 for a, b in zip(got['Translate'], want['Translate'])):
                raise SystemExit('read-back: shelf %s not lifted as intended' % h)
            got['Translate'] = want['Translate']
        if got != want:
            raise SystemExit('read-back: actor %s differs from what was intended' % h)
    return new


def open_shop_list(data, goods):
    """a shop list (ShopParam) with every shelf open from the start (no release flag); goods {shelf index:
    shelf actor} replaces what those shelves sell, sold once"""
    doc = byml.loads(data)
    root = type(doc.root)(doc.root)
    entries = list(root['GoodsList'])
    if goods and max(goods) >= len(entries):
        raise SystemExit('shop list has %d shelves, shelf %d asked for' % (len(entries), max(goods)))
    stock_type = next((type(e['StockNum']) for e in entries if 'StockNum' in e), int)
    new_entries = []
    for i, e in enumerate(entries):
        e = type(e)(e)
        if 'Release' in e:
            r = type(e['Release'])(e['Release'])
            r['IsCheckReleaseGameData'] = False
            r['ReleaseGameData'] = type(r['ReleaseGameData'])('')
            e['Release'] = r
        if i in goods:
            e['Actor'] = type(e['Actor'])('Work/Actor/%s.engine__actor__ActorParam.gyml' % goods[i])
            e['StockNum'] = stock_type(SHOP_STOCK_ONCE)
        new_entries.append(e)
    root['GoodsList'] = new_entries
    doc.root = root
    new = byml.dumps(doc)
    back = byml.loads(new).root['GoodsList']
    for i, e in enumerate(back):
        if 'Release' in e and e['Release']['IsCheckReleaseGameData']:
            raise SystemExit('read-back: shop shelf %d still has a release flag' % i)
        if i in goods and (not e['Actor'].endswith('/%s.engine__actor__ActorParam.gyml' % goods[i])
                           or int(e['StockNum']) != SHOP_STOCK_ONCE):
            raise SystemExit('read-back: shop shelf %d differs from what was intended' % i)
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
                    choices=sorted(set(FIXES) | set(FILE_FIXES) | set(TABLE_FIXES)
                                   | {'kokiri_shop_full_stock', 'kokiri_circle_after_dungeons'}),
                    help='a game fix (see FIXES, FILE_FIXES, TABLE_FIXES)')
    ap.add_argument('assign', nargs='*', help='CHECK_ID=ItemActorName')
    a = ap.parse_args(argv)
    if not a.assign and not a.fix:
        ap.error('nothing to do: give CHECK_ID=Item assignments and/or --fix')
    assignments = [tuple(x.split('=', 1)) for x in a.assign]
    world = World()
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(a.romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    out = Output(a.romfs, os.path.join(a.out, a.name, 'romfs'), dicts)

    shop_fix = 'kokiri_shop_full_stock' in a.fix
    for cid, _ in assignments:
        if cid.startswith(CIRCLE_NEEDS_FIX) and 'kokiri_circle_after_dungeons' not in a.fix:
            raise SystemExit('%s: needs --fix kokiri_circle_after_dungeons' % cid)
    shop_removed = set()
    for name in a.fix:
        if name == 'kokiri_shop_full_stock':
            src, old = out.read(SHOP_MAP)
            new, shop_removed, always = shop_full_stock_map(old)
            out.write(SHOP_MAP, src, old, new)
            print('fix %-28s %s: %d shop objects removed (before the Deku Tree), %d always there'
                  % (name, SHOP_MAP, len(shop_removed), len(always)))
            src, old = out.read(SHOP_FLOW)
            ef = evfl.loads(old)
            shop_greeting_edit(ef.flowchart)
            out.write(SHOP_FLOW, src, old, flow_write_checked(ef))
            print('fix %-28s %s: greeting always as after the Deku Tree' % (name, SHOP_FLOW))
            continue
        if name == 'kokiri_circle_after_dungeons':
            src, old = out.read(CIRCLE_LOGIC)
            new, said = circle_logic(old)
            out.write(CIRCLE_LOGIC, src, old, new)
            print('fix %-28s %s: %s' % (name, CIRCLE_LOGIC, said))
            src, old = out.read(CIRCLE_KOKIRI)
            out.write(CIRCLE_KOKIRI, src, old, circle_kokiri(old))
            print('fix %-28s %s: schedule after the Kokiri Emerald is the default' % (name, CIRCLE_KOKIRI))
            src, old = out.read(CIRCLE_MIDDLE)
            out.write(CIRCLE_MIDDLE, src, old, circle_middle(old))
            print('fix %-28s %s: middle rock: prop never, liftable rock always' % (name, CIRCLE_MIDDLE))
            continue
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
    # get a ground version; items a chest gives that have no get-demo settings (ocarinas: Link's instrument)
    # get a held-up version (tools/ground_items.py)
    grounds = {}                                       # (item, version) -> name

    def plain(path):
        return out.read(path)[1]

    def on_ground(item):
        kind = ground_items.kind_of(plain, item)
        if kind == 'ground':
            return item
        if kind in ('item', 'equipment'):
            return grounds.setdefault((item, 'ground'), ground_items.ground_name(item))
        raise SystemExit('%s: not something that can lie on the ground, and no ground version can be made' % item)

    def in_chest(item):
        if ground_items.kind_of(plain, item) == 'equipment':
            return grounds.setdefault((item, 'held'), ground_items.ground_name(item, 'held'))
        return item

    # shelves: a game shelf actor (Shop_...) is used as it is; any other item gets a shop version at the price
    # of what the shelf sold, sold once (tools/shop_items.py)
    shops = {}                                         # (item, price) -> name
    shelf_lift = {}                                    # shop version name -> metres higher on the shelf
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root  # noqa: E731

    def on_shelf(item, shelf_actor):
        if item.startswith('Shop_'):
            return item
        if not shop_items.can_sell(plain, item):
            raise SystemExit('%s: cannot be put on a shop shelf' % item)
        why = shop_items.refusal(item, table_rows)
        if why:
            raise SystemExit('%s cannot be put on a shop shelf: %s' % (item, why))
        price = shop_items.price_of(table_rows, shelf_actor)
        name = shops.setdefault((item, price), shop_items.shop_name(item, price, once=True))
        if item in shop_items.SHELF_LIFT:
            shelf_lift[name] = shop_items.SHELF_LIFT[item]
        return name

    planned = plan(world, assignments, on_ground, in_chest, on_shelf)
    # shelves: which shelf (ShopItemIndex; the Heart has none: 0) and age each placement is, for the lists
    shelf_of = {p['hash']: (p['ages'], int(p.get('params', {}).get('ShopItemIndex', 0)))
                for spots in world.checks.values() for sp in spots.values() if sp['kind'] == 'shop'
                for p in sp['placements']}
    goods = {'child': {}, 'adult': {}}
    for path in list(planned):
        for h, (cid, item, _, kind) in list(planned[path].items()):
            if kind != 'shop':
                continue
            if not shop_fix:
                raise SystemExit('%s: shop shelves need --fix kokiri_shop_full_stock' % cid)
            if h in shop_removed:
                del planned[path][h]
                print('%-18s placement %s: removed by kokiri_shop_full_stock (before the Deku Tree)' % (cid, h))
                continue
            ages, idx = shelf_of[h]
            for age in ages:
                if goods[age].get(idx, item) != item:
                    raise SystemExit('%s: shelf %d (%s) given two items' % (cid, idx, age))
                goods[age][idx] = item
        if not planned[path]:
            del planned[path]

    for path, changes in sorted(planned.items()):
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
            if h in changes and changes[h][3] in REPLACED:
                want['Gyaml'] = changes[h][1]
            elif h in changes:
                dyn = dict(want.get('Dynamic') or {}, Drop__DropActor=changes[h][1])
                ev = dyn.get('GetEventName')
                if ev is not None and changes[h][1] != found[h] and CHEST_EVENTS[ev][0] == 'remove':
                    del dyn['GetEventName']
                    print('%-18s   special opening event %s removed' % (changes[h][0], ev))
                want['Dynamic'] = dyn
            if act != want:
                raise SystemExit('read-back: actor %s (%s) differs from what was intended' % (h, act['Gyaml']))
        out.write(path, src, old, new)

    # count boards of changed shelves: none for a single item, the right count for a bundle
    pouch_rows = {r['__RowId']: r for r in table_rows('PouchActorInfo')}

    def bundle_count(actor):
        if actor.startswith(shop_items.PREFIX):
            return 1                                   # shop versions sell one item
        return int(pouch_rows[actor].get('BundleActorNum', 1))

    for path, changes in sorted(planned.items()):
        shelves = {h: bundle_count(v[1]) for h, v in changes.items() if v[3] == 'shop'}
        if not shelves:
            continue
        src, old = out.read(path)
        new, done = shop_boards(old, shelves, lambda n: os.path.exists(
            os.path.join(a.romfs, *ground_items.pack_path(n).split('/')) + '.zs'))
        if done:
            out.write(path, src, old, new)
            for d in done:
                print('%-18s %s: %s' % ('count board', path.split('/')[-1], d))
        lifts = {h: shelf_lift[v[1]] for h, v in changes.items() if v[3] == 'shop' and v[1] in shelf_lift}
        if lifts:
            src, old = out.read(path)
            out.write(path, src, old, lift_shelves(old, lifts))
            for h in lifts:
                print('%-18s %s: %s %.2f m higher' % ('shelf lift', path.split('/')[-1], changes[h][1], lifts[h]))

    if shop_fix:
        # the child shopkeeper's list (also copied in the adult shopkeeper's pack: kept identical), and a list
        # of the adult shopkeeper's own
        child_pack = ground_items.pack_path(SHOP_KEEPERS['child'])
        child_list = sarc.Sarc.read(plain(child_pack)).files[SHOP_LIST]
        new_child = open_shop_list(child_list, goods['child'])
        new_adult = open_shop_list(child_list, goods['adult'])
        for keeper in ('child', 'adult'):
            pack_path = ground_items.pack_path(SHOP_KEEPERS[keeper])
            src, old = out.read(pack_path)
            arc = sarc.Sarc.read(old)
            if arc.files[SHOP_LIST] != child_list:
                raise SystemExit('%s: its copy of the child shop list differs' % SHOP_KEEPERS[keeper])
            arc.files[SHOP_LIST] = new_child
            out.size(SHOP_LIST, len(child_list), len(new_child))
            if keeper == 'adult':
                ap = ground_items.ap_path(SHOP_KEEPERS['adult'])
                adoc = byml.loads(arc.files[ap])
                adoc.root = type(adoc.root)(adoc.root)
                comp = type(adoc.root.get('Components', {}))(adoc.root.get('Components', {}))
                if 'ShopRef' in comp:
                    raise SystemExit('%s already has a shop list of its own' % SHOP_KEEPERS['adult'])
                comp['ShopRef'] = '?' + SHOP_LIST_ADULT
                adoc.root['Components'] = comp
                new_ap = byml.dumps(adoc)
                out.size(ap, len(arc.files[ap]), len(new_ap))
                arc.files[ap] = new_ap
                arc.files[SHOP_LIST_ADULT] = new_adult
                arc.align[SHOP_LIST_ADULT] = arc.align.get(SHOP_LIST, 8)
                out.add(SHOP_LIST_ADULT, len(new_adult), SHOP_LIST, len(child_list))
            new_pack = arc.write()
            back = sarc.Sarc.read(new_pack)
            if set(back.files) != set(arc.files) or any(back.files[k] != v for k, v in arc.files.items()):
                raise SystemExit('read-back: %s differs from what was intended' % pack_path)
            out.write(pack_path, src, old, new_pack)
            print('shop list %-36s %s' % (SHOP_KEEPERS[keeper], ', '.join(
                'shelf %d: %s' % (i, n) for i, n in sorted(goods[keeper].items())) or 'all shelves open'))

    new_rows = {}
    for (item, version), name in sorted(grounds.items()):
        tpl_name = ground_items.template_of(name)
        tpl_pack_path = ground_items.pack_path(tpl_name)
        tpl_pack = plain(tpl_pack_path)
        got, pack, new_inner, rows = ground_items.build(
            item, plain, lambda t: byml.loads(plain(ground_items.table_path(t))).root,
            lambda project: os.path.exists(os.path.join(a.romfs, 'Model', project + '.anim.bfres.zs')), version)
        assert got == name
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=tpl_pack_path)
        out.add(path, len(pack), tpl_pack_path, len(tpl_pack))
        tpl_files = sarc.Sarc.read(tpl_pack).files
        for inner, data in new_inner.items():
            like = (ground_items.anim_param_path(tpl_name) if 'AnimationParam' in inner
                    else ground_items.pouch_param_path(tpl_name) if 'PouchContentParam' in inner
                    else ground_items.ap_path(tpl_name))
            out.add(inner, len(data), like, len(tpl_files[like]))
        for inner in sarc.Sarc.read(pack).files:          # every file of the pack has a size entry
            if out.table.get(inner) is None:
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        print('%-6s version %-22s for %s (%d bytes)' % (version, name, item, len(pack)))
    for (item, price), name in sorted(shops.items()):
        tpl_pack_path = ground_items.pack_path(shop_items.TEMPLATE)
        tpl_pack = plain(tpl_pack_path)
        got, pack, new_inner, rows = shop_items.build(item, price, plain, table_rows, once=True)
        assert got == name
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=tpl_pack_path)
        out.add(path, len(pack), tpl_pack_path, len(tpl_pack))
        like_files = {}
        for actor in (shop_items.TEMPLATE, shop_items.PRICE_TEMPLATE):
            like_files.update(sarc.Sarc.read(plain(ground_items.pack_path(actor))).files)
        for inner, (data, like) in new_inner.items():
            out.add(inner, len(data), like, len(like_files[like]))
        for inner in sarc.Sarc.read(pack).files:
            if out.table.get(inner) is None:
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        print('shop   version %-22s for %s, %d rupees, sold once (%d bytes)' % (name, item, price, len(pack)))
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
