"""Progressive families test: every upgrade family of tools/build_mod.py (FAMILIES) on every kind of check a
progressive form can be placed on: small chests, freestanding items, rocks, bushes, pots, a Deku Scrub that sells
once and a gift with flow data. Checked on the game's own files: what the game gives with a first Fairy Slingshot and
Fairy Bow, how each level is shown, the turning items of two and three levels, the three-level chests, the
questions in the gift's and the scrub's flow, and what every form gives for every order its checks are taken in
(no level skipped, none given twice). Only reads the game; the builds it runs go to a temporary folder that is
removed again.

    python tests/families_check.py "C:\\...\\romfs"
"""
import concurrent.futures
import contextlib
import glob
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import shop_items  # noqa: E402
import three_chest  # noqa: E402
import turn_items  # noqa: E402
import once_items  # noqa: E402
from formats import zstd, byml, sarc, evfl, ainb  # noqa: E402
from logic.world import World  # noqa: E402

# the user's families (2026-11-21), as they are placed, lowest level first
FAMILIES = {
    'Scale': ('Item_Scale_Silver', 'Item_Scale_Gold'),
    'Hookshot': ('Item_Hookshot', 'Item_Longshot'),
    'Ocarina': ('Item_Ocarina_Fairy', 'Item_Ocarina_Time'),
    'BombBag': ('Item_BombBag_Small', 'Item_BombBag_Medium', 'Item_BombBag_Large'),
    'BulletBag': ('Item_Range_SlingShot', 'Item_BulletBag_Medium', 'Item_BulletBag_Large'),
    'Quiver': ('Item_Range_Bow', 'Item_Quiver_Medium', 'Item_Quiver_Large'),
    'StickBag': ('Item_StickBag_Medium', 'Item_StickBag_Large'),
    'NutBag': ('Item_NutBag_Medium', 'Item_NutBag_Large'),
    'Wallet': ('Item_Wallet_Medium', 'Item_Wallet_Large'),
    'Gauntlet': ('Item_Gauntlet_Goron', 'Item_Gauntlet_Silver', 'Item_Gauntlet_Gold'),
    'Magic': ('Item_FairyBless_MP', 'Item_FairyBless_MPDouble'),
}
# what the game's chests give with a first weapon (the shared chest module), and the game's chests that give them
FIRST_GET = {'Item_Range_SlingShot': ('Weapon_Range_SlingShot', [('Item_BulletBag_Small', 1), ('Item_DekuSeed', 30)]),
             'Item_Range_Bow': ('Weapon_Range_Bow', [('Item_Quiver_Small', 1), ('Item_Arrow_Normal', 30)])}
GAME_CHESTS = {'Item_Range_SlingShot': 'InsideTheDekuTree', 'Item_Range_Bow': 'ForestTemple'}
# the names the game's own flows ask the inventory about for levels kept under another name
FLOW_NAMES = {'Item_Range_SlingShot': 'Weapon_Range_SlingShot', 'Item_Range_Bow': 'Weapon_Range_Bow',
              'Item_Gauntlet_Goron': 'Armor_Child_Gauntlet_Goron', 'Item_Gauntlet_Silver': 'Armor_Adult_Gauntlet_Silver',
              'Item_Gauntlet_Gold': 'Armor_Adult_Gauntlet_Gold'}
ASKED_BY_GAME = ('Weapon_Range_Bow', 'Armor_Child_Gauntlet_Goron', 'Armor_Adult_Gauntlet_Silver')
# levels whose ground version keeps the game's pose (no lifted copy). None since 2026-11-22: the seven on many
# bones (slingshot, bow, silver and golden gauntlets, first bomb bag, hookshot, longshot) are lifted too
NOT_LIFTED = ()
GIFT, GIFT_FLOW, GIFT_EVENT = 'KF_CIRCLE_KOKIRI_GIFT', 'Event/EventFlow/Npc_Kokiri_008_Child.bfevfl', 'Event224'
SCRUB, SCRUB_TALK, SCRUB_WAS = 'LW_NEAR_BRIDGE_SCRUB', 'Enemy_Scrub_Business_DekuStickPouch_01', 'Item_StickBag_Medium'
CHESTS = ('KF_MIDO_CHEST_01', 'KF_MIDO_CHEST_02', 'KF_MIDO_CHEST_03', 'KF_MIDO_CHEST_04', 'KF_STORMS_GROTTO_CHEST',
          'LW_BRIDGE_CHEST')
GROUND = ('KF_RUPEE_NEAR_MIDO_ITEM', 'KF_RUPEE_NEAR_FADO_ITEM_01', 'KF_RUPEE_BEHIND_MIDOS_HOUSE_ITEM',
          'KF_SARIAS_HOUSE_HEART_ITEM_01', 'KF_SARIAS_HOUSE_HEART_ITEM_03', 'KF_SARIAS_HOUSE_HEART_ITEM_05',
          'KF_SARIAS_HOUSE_HEART_ITEM_07', 'KF_SHOP_RUPEE_ITEM', 'KF_TRAINING_AREA_RUPEE_ITEM_01',
          'KF_TRAINING_AREA_RUPEE_ITEM_02', 'KF_RUPEE_NEAR_FADO_ITEM_03')
ROCKS = ('KF_WEST_OF_MIDOS_HOUSE_CHILD_ROCK_01', 'KF_WEST_OF_MIDOS_HOUSE_CHILD_ROCK_02',
         'KF_NEAR_KNOW_IT_ALL_HOUSE_CHILD_ROCK_01', 'KF_NEAR_KNOW_IT_ALL_HOUSE_CHILD_ROCK_02',
         'KF_BEHIND_SARIAS_HOUSE_CHILD_ROCK_01', 'KF_BEHIND_SARIAS_HOUSE_CHILD_ROCK_02', 'KF_CIRCLE_CHILD_ROCK_01',
         'KF_CIRCLE_CHILD_ROCK_02', 'KF_CIRCLE_CHILD_ROCK_04', 'KF_CIRCLE_CHILD_ROCK_05', 'KF_CIRCLE_CHILD_ROCK_07')
BUSHES = tuple('KF_%s_CHILD_BUSH_%02d' % (where, n) for where in ('NEAR_SARIAS_HOUSE', 'BESIDE_MIDOS_HOUSE',
                                                                   'BEHIND_SHOP') for n in (1, 2, 3))
# the eight pots of Kokiri Forest (the child's and the adult's maps place their own): a family is a turning item
# that is given once (tools/once_items.py, tests/one_time_check.py)
POTS = tuple('KF_%s_%s_POT_%02d' % (house, age, n) for age in ('CHILD', 'ADULT')
             for house in ('HOUSE_OF_TWINS', 'KNOW_IT_ALL_HOUSE') for n in (1, 2))
# a shelf takes no family yet; Saria's cutscene gift and her song take them their own way (2026-11-23:
# tests/event_families_check.py)
REFUSED = ('KF_KOKIRI_CHILD_SHOP_01', 'KF_KNOW_IT_ALL_HOUSE_GS', 'LW_SARIA_GIFT', 'Song from Saria')
BIG_CHEST = 'KF_KOKIRI_SWORD_CHEST'
CIRCLE_FIX = ['--fix', 'kokiri_circle_after_dungeons']
SCRUB_BUILDS = ('BulletBag', 'Gauntlet', 'Wallet', 'StickBag')     # the scrub's whole builds (each writes every
#                                                                    language's lines: the slow ones)
GUARDS = ['QueryDeathIsDead', 'QueryEventMemberIsEventMemberSomeReason', 'QueryIsPlayingMainEvent',
          'QueryPouchContentIsRequestingGetEvent']
TURN = [('OneShotDropSetDropValid', [True]), ('OneShotDropDrop', []), ('OneShotGenericDeleteThisActor', [])]
GONE = [('OneShotGenericDeleteThisActor', [])]


def check(name, ok):
    print('%-118s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args, **kw):
    try:
        f(*args, **kw)
    except SystemExit:
        return True
    return False


def taken(give, levels, extra=False):
    """what the checks of a family give when they are taken one after the other: give(owned set) -> the level a
    check gives now (None: nothing). With `extra`, one check more than the family has levels"""
    owned, out = set(), []
    for _ in range(len(levels) + (1 if extra else 0)):
        x = give(owned)
        out.append(x)
        if x is not None:
            owned.add(x)
    return out


def build_plan():
    """The whole builds of the last section, (name, arguments) in the order it asks for them. They are started at
    once, side by side, when the test begins (each in a folder of its own: a build clears its folder first, so
    this gives the same files as one folder used over and over); the last section then takes their results. A
    build asked for that is not in this list runs there and then, as before."""
    text = {n: '>'.join(f) for n, f in FAMILIES.items()}
    names = list(FAMILIES)
    plan = []
    for part in (names[:6], names[6:]):
        plan.append(('chests', tuple('%s=%s' % (c, text[n]) for c, n in zip(CHESTS, part))))
    for spots, parts in ((GROUND, (names,)), (ROCKS, (names,)), (BUSHES, (names[:9], names[9:])),
                         (POTS, (names[:8], names[8:]))):
        for part in parts:
            plan.append(('turn', tuple(['%s=%s' % (c, text[n]) for c, n in zip(spots, part)] + CIRCLE_FIX)))
    for n in FAMILIES:
        plan.append(('gift', ('%s=%s' % (GIFT, text[n]), *CIRCLE_FIX)))
    for n in SCRUB_BUILDS:
        plan.append(('scrub', ('%s=%s' % (SCRUB, text[n]),)))
    plan.append(('mix', ('%s=%s' % (CHESTS[0], text['BulletBag']), '%s=%s' % (ROCKS[0], text['BulletBag']),
                         '%s=%s' % (GIFT, text['BulletBag']), *CIRCLE_FIX)))
    plan.append(('mix', ('%s=%s' % (CHESTS[0], text['BulletBag']), '%s=%s' % (ROCKS[0], text['BulletBag']))))
    return plan


def build(romfs, out, name, assign):
    """One whole build into out/<name>: what it said, and the files it wrote (relative to out/<name>)."""
    with contextlib.redirect_stdout(io.StringIO()) as said:
        build_mod.main(['--romfs', romfs, '--out', out, '--name', name] + list(assign))
    folder = os.path.join(out, name)
    return said.getvalue(), {os.path.relpath(f, folder).replace(os.sep, '/')
                             for f in glob.glob(os.path.join(folder, '**', '*'), recursive=True) if os.path.isfile(f)}


def main(romfs):
    with tempfile.TemporaryDirectory() as tmp, \
            concurrent.futures.ProcessPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as pool:
        builds = {(name, assign): pool.submit(build, romfs, os.path.join(tmp, 'b%02d' % i), name, assign)
                  for i, (name, assign) in enumerate(build_plan())}
        return checks(romfs, builds)


def checks(romfs, builds):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)  # noqa: E731
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    model = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))  # noqa: E731
    rows = {t: {r['__RowId']: r for r in table_rows(t)} for t in ground_items.TABLES}
    flow_name = lambda item: rows['ActorInfo'][item].get('ActorName') or item   # noqa: E731
    world = World()
    families = build_mod.FAMILIES
    levels_all = [x for f in families.values() for x in f]
    good = True

    def in_chest(item):                                # as build_mod.main's in_chest
        if ground_items.kind_of(plain, item) == 'equipment':
            return ground_items.ground_name(item, 'held')
        return item

    # ------------------------------------------------------------------------------------------ the families
    good &= check('the families are the user\'s list: %d families, %d pairs, %d of three levels, %d levels'
                  % (len(FAMILIES), len(build_mod.PROGRESSIVE_PAIRS), len(build_mod.THREE_LEVEL_FAMILIES),
                     len(levels_all)),
                  families == FAMILIES and len(set(levels_all)) == len(levels_all) == 26
                  and build_mod.PROGRESSIVE_PAIRS == {f for f in FAMILIES.values() if len(f) == 2}
                  and build_mod.THREE_LEVEL_FAMILIES == {f: n for n, f in FAMILIES.items() if len(f) == 3}
                  and tuple(build_mod.UPGRADE_FAMILIES) == tuple(FAMILIES.values()))
    good &= check('  never placed: the small Deku Stick bag, Deku Nut bag and wallet; the small seed bag and quiver '
                  'stand for their weapons, which are the first levels',
                  not set(build_mod.NEVER_GIVEN) & set(levels_all)
                  and build_mod.FAMILY_ALIASES == {'Item_BulletBag_Small': FAMILIES['BulletBag'][0],
                                                   'Item_Quiver_Small': FAMILIES['Quiver'][0]}
                  and not set(build_mod.FAMILY_ALIASES) & set(levels_all))
    good &= check('  every level is an item of the game (PouchActorInfo, ActorInfo); the inventory keeps the two '
                  'weapons and the three gauntlets under another name (Weapon_..., Armor_...), the rest under their own',
                  all(x in rows['PouchActorInfo'] and x in rows['ActorInfo'] for x in levels_all)
                  and all(flow_name(x) == FLOW_NAMES.get(x, x) for x in levels_all))

    # ------------------------------------------------------------ the first Fairy Slingshot and Fairy Bow
    shared = sarc.Sarc.read(plain(turn_items.AI_PACK)).files
    ok = True
    gets = {}
    for item, (name, gives) in FIRST_GET.items():
        nodes, got = turn_items.first_get(shared, name)
        gets[item] = (nodes, got)
        ok &= got == gives and flow_name(item) == name and build_mod.SCRUB_COMPANIONS[item] == [gives[0][0]]
    owners = [p for p, x in shared.items() if p.endswith('.ainb')
              and any(m[0].startswith('_LocalModule_') and b'Item_BulletBag_Small' in shared.get('AI/' + m[0], b'')
                      for m in ainb.loads(x).modules)]
    good &= check('the game\'s chests give with a first Fairy Slingshot: the small seed bag and 30 Deku Seeds; with '
                  'a first Fairy Bow: the small quiver and 30 arrows', ok and set(build_mod.SCRUB_COMPANIONS) == set(FIRST_GET))
    good &= check('  only the shared chest module runs that (%s)' % ', '.join(owners),
                  owners == [turn_items.FIRST_GET_OWNER]
                  and refused(turn_items.first_get, shared, 'Item_Hookshot'))
    ok = True
    for item, (name, gives) in FIRST_GET.items():
        bag, ammo = rows['PouchActorInfo'][gives[0][0]], rows['PouchActorInfo'][gives[1][0]]
        ok &= bag.get('IsItemStockMaxIfGet') is True and int(bag['AfterExpansionMaxNum']) == gives[1][1] \
            and bag.get('MaxNumGameData') == ammo.get('MaxNumGameData') \
            and not ground_items.can_hold_up(plain, gives[0][0])
    good &= check('  the small bag and quiver fill themselves when added (30), so the bag alone leaves the same; '
                  'neither can be held up (never a gift of its own)', ok)
    found = {}
    for path in glob.glob(os.path.join(romfs, 'Banc', '*', '*.bcett.byml.zs')):
        scene = os.path.basename(os.path.dirname(path))
        if scene not in GAME_CHESTS.values():
            continue
        for a in byml.loads(zstd.decompress(open(path, 'rb').read(), d)).root.get('Actors', []):
            item = (a.get('Dynamic') or {}).get('Drop__DropActor')
            if item in GAME_CHESTS and a['Gyaml'].startswith('Obj_TBox'):
                found.setdefault(item, set()).add(scene)
    flows = {}
    for path in glob.glob(os.path.join(romfs, 'Event', 'EventFlow', '*.bfevfl.zs')):
        flows[os.path.basename(path)[:-len('.bfevfl.zs')]] = zstd.decompress(open(path, 'rb').read(), d)
    named = [n for n, x in flows.items() if any(k.encode() in x for k in GAME_CHESTS)]
    good &= check('  the game gives the two weapons from chests (the Deku Tree, the Forest Temple); none of its %d '
                  'event flows names them' % len(flows),
                  found == {k: {v} for k, v in GAME_CHESTS.items()} and not named and len(flows) > 900)
    asked = set()
    for x in flows.values():
        try:
            fc = evfl.loads(x).flowchart
        except Exception:                              # timeline files have no flowchart
            continue
        for e in fc.events:
            if e.type == 'switch' and fc.actors[e.actor].queries[e.query] == build_mod.GIFT_PAIR_QUERY \
                    and isinstance(e.params, dict):
                asked.add(str(e.params.get('Actor')))
    good &= check('  the game\'s own flows ask the inventory under the kept names (%s)' % ', '.join(ASKED_BY_GAME),
                  set(ASKED_BY_GAME) <= asked and not {'Item_Range_Bow', 'Item_Gauntlet_Goron',
                                                       'Item_Gauntlet_Silver'} & asked)

    # ------------------------------------------------------------------------------ how each level is shown
    ok = lift_ok = True
    for x in levels_all:
        kind = ground_items.kind_of(plain, x)
        ok &= kind in ('item', 'equipment') and (ground_items.can_hold_up(plain, x) == (kind == 'item'))
        built = {}
        for version in ('ground', 'turn', 'held'):
            name, pack, _, _, loose = ground_items.build(x, plain, table_rows, model, version)
            built[version] = loose
            ok &= name == ground_items.ground_name(x, version) and len(pack) > 1000
        lift_ok &= (len(built['ground']) == 1) == (len(built['turn']) == 1) == (x not in NOT_LIFTED) \
            and not built['held'] and (x in ground_items.GROUND_LIFT) == (x not in NOT_LIFTED)
        ok &= in_chest(x) == (x if kind == 'item' else ground_items.ground_name(x, 'held'))
    good &= check('every level has a ground version, a turning version and a way a chest holds it up (itself; the '
                  'ocarinas as held-up versions)', ok)
    good &= check('  %d levels lie on a lifted copy of their pose; %d keep the game\'s pose (%s)'
                  % (len(levels_all) - len(NOT_LIFTED), len(NOT_LIFTED), ', '.join(NOT_LIFTED) or 'none'), lift_ok)

    # ------------------------------------------------------------------------------------ the turning items
    sources = [ainb.loads(shared[shop_items.ai_path(turn_items.BASE_AI)])] \
        + [ainb.loads(shared[p]) for p in turn_items.SOURCES.values()] \
        + [ainb.loads(sarc.Sarc.read(plain(ground_items.pack_path(a))).files[f])
           for a, f in ((turn_items.DROP_ACTOR, turn_items.DROP_AI), (turn_items.REQUEST_ACTOR, turn_items.REQUEST_AI))] \
        + [ainb.loads(shared['AI/' + m[0]]) for m in ainb.loads(shared[turn_items.FIRST_GET_OWNER]).modules]
    game_nodes = {(n.type, n.name) for s in sources for n in s.nodes}
    turn_ok = copies = chain_ok = bundle_ok = sizes = True
    describes = {}
    for fam_name, family in families.items():
        for level, item in enumerate(family):
            last = level == len(family) - 1
            bundle_for = flow_name(item) if level == 0 and item in FIRST_GET else None
            name, pack, new_inner, new_rows, loose = turn_items.build(family, level, plain, table_rows, model,
                                                                     bundle_for)
            files = sarc.Sarc.read(pack).files
            data = files[shop_items.ai_path(turn_items.ai_name(item))]
            doc = ainb.loads(data)
            what = describes[item] = turn_items.describe(data)
            between = list(family[level + 1:-1]) if not last else []
            turn_ok &= name == turn_items.turn_name(item) and what['own'] == item and what['guards'] == GUARDS \
                and what['drops'] == (not last) and what['later'] == list(family[level + 1:]) \
                and what['later_turns'] == between and what['turn'] == (GONE if last else TURN) \
                and what['enter'] == ([] if last else [('OneShotDropSetDropValid', [False])]) \
                and what['asked'] == ([] if last else [('OneShotDropSetDropValid', [True])]) \
                and what['new'] == (16 if last else 28) + 6 * len(between) + (14 if bundle_for else 0)
            copies &= all((n.type, n.name) in game_nodes for n in doc.nodes[turn_items.BASE_NODES:]) \
                and len({bytes(n.guid) for n in doc.nodes}) == len(doc.nodes) and doc.write() == data
            if bundle_for:
                bundle_ok &= what['bundle'] == {'bag': FIRST_GET[item][1][0][0], 'gives': [
                    ('Work/Actor/%s.engine__actor__ActorParam.gyml' % x, n) for x, n in FIRST_GET[item][1]]}
            else:
                bundle_ok &= what['bundle'] is None
            if not last:
                sub = byml.loads(files[turn_items.drop_sub_path(name)]).root
                chain_ok &= [x['DropActorName'] for x in sub['Items']] == [
                    'Work/' + ground_items.ap_path(turn_items.turn_name(family[level + 1]))[:-len('.bgyml')] + '.gyml']
            else:
                chain_ok &= not [p for p in files if 'Drop/' in p or '/DropParam/' in p]
            pouch = byml.loads(files[ground_items.pouch_param_path(name)]).root
            chain_ok &= pouch.get('PouchActor') == 'Work/' + ground_items.ap_path(item)[:-len('.bgyml')] + '.gyml' \
                and dict(new_rows['PouchActorInfo'], __RowId=item) == dict(
                    rows['PouchActorInfo'][item], **({k: 'Work/Actor/%s.engine__actor__ActorParam.gyml' % item
                                                      for k in ground_items.EQUIP_ROW}
                                                     if ground_items.kind_of(plain, item) == 'equipment' else {}))
            sizes &= int(new_rows['ActorInfo']['InstanceHeapSize']) > int(
                rows['ActorInfo'][ground_items.TEMPLATE]['InstanceHeapSize'])
    good &= check('turning items: one actor per level of every family (%d); each asks for its own level, turns into '
                  'the next one (the last deletes itself), and stays while its pick-up is asked for'
                  % len(describes), turn_ok)
    good &= check('  three levels: the first turns into the second, the second into the third; a first level whose '
                  'second is owned without it turns too',
                  all(describes[f[0]]['later_turns'] == [f[1]] and describes[f[1]]['later_turns'] == []
                      for f in build_mod.THREE_LEVEL_FAMILIES))
    good &= check('  every new node is a copy of a game node of that kind; the files read back', copies)
    good &= check('  each level drops the next level\'s turning item, gives the item itself (PouchActor) and has the '
                  'item\'s own row; more memory than the ground item', chain_ok and sizes)
    good &= check('  the first Fairy Slingshot and Fairy Bow give what a chest gives with them while Link has no '
                  'small bag (asked for, or owned); no other level gives more', bundle_ok)

    def lies(family):
        """what a turning check of the family shows for what Link owns: the level whose actor stays"""
        def give(owned):
            k = 0
            while k is not None and k < len(family):
                w = describes[family[k]]
                if w['own'] in owned:
                    k = k + 1 if w['drops'] else None
                    continue
                hit = next((x for x in w['later'] if x in owned), None)
                if hit is None:
                    return family[k]
                k = k + 1 if hit in w['later_turns'] else None
            return None
        return give

    good &= check('  taken one after the other, the checks of a family give its levels in order, and a check more '
                  'gives nothing (every family)',
                  all(taken(lies(f), f, extra=True) == list(f) + [None] for f in families.values()))
    odd = FAMILIES['Gauntlet']
    good &= check('  a later level owned without the ones before it (these checks cannot do that): a check then '
                  'offers the level after the highest one owned, or nothing; never a level Link owns',
                  lies(odd)({odd[1]}) == odd[2] and lies(odd)({odd[2]}) is None
                  and lies(odd)({odd[0], odd[2]}) is None and lies(odd)({odd[1], odd[2]}) is None)

    # ----------------------------------------------------------------------------------------- the chests
    ok = True
    for family, tag in build_mod.THREE_LEVEL_FAMILIES.items():
        name, pack, _, _ = three_chest.build(tag, family[1], in_chest(family[2]), plain, table_rows)
        what = three_chest.describe(sarc.Sarc.read(pack).files[shop_items.ai_path(three_chest.chest_name(tag))])
        ok &= name == 'Obj_TBox_NX2_' + tag and tag == [n for n, f in FAMILIES.items() if f == family][0] \
            and what['second'] == family[1] and what['third'] == in_chest(family[2]) and what['new'] == 4 \
            and build_mod.pair_check(family[:2], in_chest) == (family[0], in_chest(family[1]))
    good &= check('three-level chests: one per family of three (%s): the first two levels as a pair\'s settings, '
                  '"has Second?" and Third in its own AI' % ', '.join(
                      'Obj_TBox_NX2_' + t for t in build_mod.THREE_LEVEL_FAMILIES.values()), ok)

    def chest(family):
        def give(owned):
            if len(family) == 3 and family[1] in owned:
                return family[2]
            return family[1] if family[0] in owned else family[0]
        return give

    good &= check('  taken one after the other, the chests of a family give its levels in order (every family)',
                  all(taken(chest(f), f) == list(f) for f in families.values()))

    # ------------------------------------------------------------------------------------------ the gift
    template = build_mod.gift_pair_template(evfl.loads(plain(build_mod.GIFT_PAIR_FLOW)).flowchart)
    old_gift = plain(GIFT_FLOW)
    sync_steps = build_mod.sync_template(evfl.loads(plain(build_mod.SYNC_FLOW)).flowchart)

    def gift(family):
        direct = {x for x in family if not ground_items.can_hold_up(plain, x)}
        ef = evfl.loads(old_gift)
        build_mod.gift_edit(ef.flowchart, {GIFT_EVENT: (GIFT, family[0], 'Obj_Rupee_Blue')}, direct,
                            {x: sync_steps for x in direct})
        before = build_mod.flow_write_checked(ef)
        ef = evfl.loads(before)
        events = {GIFT_EVENT: (GIFT, family)}
        said, made = build_mod.gift_pair_edit(ef.flowchart, events, template, direct, flow_name)
        new = build_mod.flow_write_checked(ef)
        build_mod.gift_pair_read_back(GIFT_FLOW, evfl.loads(before).flowchart, evfl.loads(new).flowchart, events,
                                      made, template, flow_name)
        return evfl.loads(new).flowchart, made[GIFT_EVENT], evfl.loads(before).flowchart

    def walk(fc, start, owned, sells=None):
        """follow a flow from event `start` for what Link owns: the first call that gives an item, and the items
        added silently after it"""
        names = {flow_name(x) for x in owned}
        e, seen = fc.events[start], 0
        while seen < 50:
            seen += 1
            if e.type == 'switch' and fc.actors[e.actor].queries[e.query] == build_mod.GIFT_PAIR_QUERY:
                e = fc.events[dict(e.cases)[0 if e.params['Actor'] in names else 1]]
            elif e.type == 'action':
                e = fc.events[e.next]
            elif e.type == 'subflow' and (sells is None or e.entry == sells):
                more, k = [], e.next
                while k is not None and sells is None:
                    x = fc.events[k]
                    if x.type != 'action' or build_mod._action_name(fc, x) != build_mod.CUTSCENE_ADD[1]:
                        break
                    more.append(x.params['Actor'])
                    k = x.next
                if sells is not None and e.next is not None:      # a scrub: its companions behind "bought?"
                    g = fc.events[e.next]
                    k = g.cases[0][1]
                    while k is not None:
                        more.append(fc.events[k].params['Actor'])
                        k = fc.events[k].next
                return e.params['ActorName'], more
            else:
                break
        raise SystemExit('flow not followed to a call that gives an item')

    gift_ok = shape_ok = comes_ok = True
    for fam_name, family in families.items():
        fc, made, before = gift(family)
        top = next(i for i, e in enumerate(fc.events) if e.name == (made[2 * (len(family) - 1) - 2]))
        give = lambda owned: walk(fc, top, owned)[0]   # noqa: E731
        gift_ok &= taken(give, family) == list(family)
        with_first = build_mod.SCRUB_COMPANIONS.get(family[0], [])
        comes_ok &= walk(fc, top, set())[1] == with_first \
            and all(walk(fc, top, set(family[:k]))[1] == [] for k in range(1, len(family)))
        asks = [fc.events[i] for i, e in enumerate(fc.events) if e.name in made[0:2 * (len(family) - 1):2]]
        shape_ok &= len(fc.events) == len(before.events) + 2 * (len(family) - 1) + len(with_first) \
            and [e.params['Actor'] for e in asks] == [flow_name(x) for x in family[:-1]] \
            and all(list(e.params) == ['Num', 'Actor'] and e.params['Num'] == 1 for e in asks)
    good &= check('gift (the rock-circle Kokiri): every family: one question per later level, asked under the name '
                  'the inventory keeps the level before it', shape_ok)
    good &= check('  given one after the other, the gifts of a family give its levels in order (every family)', gift_ok)
    good &= check('  the small seed bag / quiver is added right after the first Fairy Slingshot / Fairy Bow, and '
                  'after nothing else', comes_ok)
    fc, made, before = gift(FAMILIES['Quiver'][:1])
    good &= check('  the same for a Fairy Bow placed alone on the gift: no question, the quiver after it',
                  len(made) == 1 and len(fc.events) == len(before.events) + 1
                  and walk(fc, next(i for i, e in enumerate(fc.events) if e.name == GIFT_EVENT), set())
                  == ('Item_Range_Bow', ['Item_Quiver_Small']))
    good &= check('  refused: a family whose later level would need a companion; levels not given the same way',
                  refused(gift, ('Item_Scale_Silver', 'Item_Range_Bow'))
                  and refused(gift, ('Item_Scale_Silver', 'Item_Ocarina_Time')))

    # ------------------------------------------------------------------------------------------ the scrub
    old_scrub = plain(build_mod.SCRUB_FLOW)

    def scrub(family):
        direct = {x for x in family if not ground_items.can_hold_up(plain, x)}
        ef = evfl.loads(old_scrub)
        said = build_mod.scrub_flow_edit(ef.flowchart, [(SCRUB, family[0], [(SCRUB_TALK, SCRUB_WAS)])], direct,
                                         {x: sync_steps for x in direct}, {SCRUB: family}, flow_name)
        fc = evfl.loads(build_mod.flow_write_checked(ef)).flowchart
        build_mod.scrub_pair_check(fc, *family, asked=flow_name)
        return fc, said

    scrub_ok = shape_ok = comes_ok = True
    for fam_name, family in families.items():
        fc, said = scrub(family)
        got = build_mod.scrub_pair_read(fc, family[0])
        eps = {p.name: p.main for p in fc.entry_points}
        sw = next(i for i in build_mod.flow_reachable(fc, eps[build_mod.SCRUB_ROOT])
                  if fc.events[i].type == 'switch' and isinstance(fc.events[i].params, dict)
                  and fc.events[i].params.get('GameDataName') == build_mod.SCRUB_VAR
                  and fc.events[i].params.get('Value') == family[0])
        start = dict(fc.events[sw].cases)[0]
        give = lambda owned: walk(fc, start, owned, build_mod.SCRUB_SELL)[0]   # noqa: E731
        scrub_ok &= taken(give, family) == list(family)
        with_first = build_mod.SCRUB_COMPANIONS.get(family[0], [])
        comes_ok &= walk(fc, start, set(), build_mod.SCRUB_SELL)[1] == with_first == got['with'] \
            and all(walk(fc, start, set(family[:k]), build_mod.SCRUB_SELL)[1] == [] for k in range(1, len(family)))
        shape_ok &= got['levels'] == list(family) and len(got['chain']) == len(family) - 1 \
            and [c[0] for c in reversed(got['chain'])] == [{'Num': 1, 'Actor': flow_name(x)} for x in family[:-1]] \
            and all(c[1][0][2]['Value'] == c[2]['ActorName'] and c[1][1][2]['Frames'] == build_mod.SCRUB_WRITE_WAIT
                    for c in got['chain']) \
            and len({(c[2]['Price'], c[2]['SellerMessageId']) for c in got['chain']}
                    | {(got['sells'][0]['Price'], got['sells'][0]['SellerMessageId'])}) == 1
    good &= check('scrub (by the bridge): every family: one question per later level in its own branch, each later '
                  'level\'s name written and waited for before its sale, one price and one line', shape_ok)
    good &= check('  bought one after the other, the scrubs of a family sell its levels in order (every family)',
                  scrub_ok)
    good &= check('  the small seed bag / quiver follows the first Fairy Slingshot / Fairy Bow after a buy, and '
                  'nothing else', comes_ok)
    sticks, nuts = FAMILIES['StickBag'], FAMILIES['NutBag']
    said = scrub(sticks)[1] + scrub(nuts)[1]
    good &= check('  the stick-bag and nut-bag pairs: the game\'s own branch sells the same two levels at the same '
                  'price, so the new branch may stand in front of it; alone, or mixed, they stay refused',
                  sum('the game\'s own branch for' in x for x in said) == 2
                  and refused(scrub, sticks[:1]) and refused(scrub, (sticks[0], nuts[1]))
                  and refused(scrub, ('Item_Scale_Silver', sticks[0])))

    # --------------------------------------------------------------------------------------- where it goes
    text = {n: '>'.join(f) for n, f in FAMILIES.items()}
    ok = True
    for n, f in FAMILIES.items():
        for c in REFUSED[:2]:
            asked_ = [(c, text[n])]
            # (a Gold Skulltula takes the families in a form of its own since 2026-11-22: no turning item there,
            # tests/skulltula_prog_check.py)
            ok &= (refused(build_mod.three_level_parse, world, asked_) != build_mod.skulltula_pair_kind(world, c)) \
                if len(f) == 3 else refused(build_mod.pair_kind, world, c)
        ok &= build_mod.cutscene_pair_kind(world, REFUSED[2]) and build_mod.song_pair_kind(world, REFUSED[3]) \
            and build_mod.gift_pair_kind(world, REFUSED[2]) is False and build_mod.gift_pair_kind(world, REFUSED[3]) is False
        ok &= (build_mod.pair_kind(world, POTS[0]) == 'pot' if len(f) == 2
               else build_mod.three_level_parse(world, [(POTS[0], text[n])]) == {})
    good &= check('refused for every family: a shelf; no turning item on a Gold Skulltula; a pot takes it; a '
                  'cutscene gift and a song take it their own way', ok)

    # ------------------------------------------------------------------------------------- whole builds
    names = list(FAMILIES)
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *assign):
            started = builds.get((name, assign))       # started side by side at the beginning (build_plan)
            return started.result() if started else build(romfs, tmp, name, assign)

        def packs(files):
            return {f.split('/')[-1][:-len('.pack.zs')] for f in files if '/Pack/Actor/' in '/' + f}

        def turn_actors(used):
            return {turn_items.turn_name(x) for n in used for x in FAMILIES[n]}

        # chests: every family in a small chest (two builds of the six small chests)
        ok, lines = True, 0
        for part in (names[:6], names[6:]):
            said, files = run('chests', *['%s=%s' % (c, text[n]) for c, n in zip(CHESTS, part)])
            for n in part:
                f = FAMILIES[n]
                gives = ': gives %s while Link has no %s, then %s' % (in_chest(f[0]), f[0], in_chest(f[1]))
                if len(f) == 3:
                    # (a chest without a baked shadow, the grotto's, becomes the family's chest of that kind)
                    ok &= any('Obj_TBox_A_01%s -> Obj_TBox_NX2_%s%s%s' % (twin, n, twin, gives) in said
                              and 'Obj_TBox_NX2_' + n + twin in packs(files) for twin in ('', '_NoBake')) \
                        and 'once Link has %s it gives %s' % (f[1], in_chest(f[2])) in said
                else:
                    ok &= any('Obj_TBox_A_01%s -> Obj_TBox_A_06%s%s' % (twin, twin, gives) in said
                              for twin in ('', '_NoBake'))
            lines += len(files)
        good &= check('built: every family in a small chest (%d files in two builds): the pairs in the game\'s '
                      'checking chest, the three-level families in a chest of their own' % lines, ok)
        good &= check('  refused: a three-level family in a big chest (it has no checking version)',
                      refused(run, 'no', '%s=%s' % (BIG_CHEST, text['Quiver'])))

        # freestanding items, rocks, bushes, pots: every family as a turning item (on a rock, a bush or a pot:
        # its version that is given once, which turns into the next level's turning item)
        for kind, spots, parts in (('freestanding items', GROUND, (names,)), ('rocks', ROCKS, (names,)),
                                   ('bushes', BUSHES, (names[:9], names[9:])),
                                   ('pots', POTS, (names[:8], names[8:]))):
            ok, count = True, 0
            for part in parts:
                said, files = run('turn', *(['%s=%s' % (c, text[n]) for c, n in zip(spots, part)] + CIRCLE_FIX))
                free = kind.startswith('free')
                # on a rock, a bush or a pot the first level lies there only as its one-time version: no first-level
                # turning item is made
                firsts = set() if free else {turn_items.turn_name(FAMILIES[n][0]) for n in part}
                ok &= turn_actors(part) - firsts <= packs(files) and not firsts & packs(files)
                if not free:
                    ok &= {once_items.once_name(x) for n in part for x in FAMILIES[n]} <= packs(files)
                for n in part:
                    f = FAMILIES[n]
                    ok &= 'a turning item%s: %s on the ground while Link has no %s, then %s' % (
                        '' if kind.startswith('free') else ' as the %s\'s drop' % kind[:-1].replace('bushe', 'bush'),
                        f[0], f[0], f[1]) in said
                    for k, x in enumerate(f):
                        if k == 0 and not free:
                            continue
                        ok &= ('once Link owns %s it drops %s and deletes itself' % (x, turn_items.turn_name(f[k + 1]))
                               if k + 1 < len(f) else 'once Link owns %s it deletes itself' % x) in said
                    if not kind.startswith('free'):
                        for k, x in enumerate(f):
                            ok &= 'once   version %-22s for %s' % (once_items.once_name(x), x) in said
                        # the dropper names no other level (writing its Drop__DropActor stops the game, 2026-11-22)
                        ok &= ' instead of Obj_NX2Q_' not in said
                        ok &= 'given once: picked up, it marks this %s' % kind[:-1].replace('bushe', 'bush') in said
                    if f[0] in FIRST_GET:
                        ok &= 'it gives what a chest gives with %s (%s) when it is picked up' % (
                            FIRST_GET[f[0]][0], ', '.join('%d %s' % (c, x) for x, c in FIRST_GET[f[0]][1])) in said
                count += len(files)
            good &= check('built: every family on %s (%d files): the first level\'s turning item placed, every '
                          'level\'s actor in the mod' % (kind, count), ok)

        # the gift: every family
        ok = True
        for n, f in FAMILIES.items():
            said, files = run('gift', '%s=%s' % (GIFT, text[n]), *CIRCLE_FIX)
            ok &= any(x.endswith('Npc_Kokiri_008_Child.bfevfl.zs') for x in files) \
                and all('gives %s' % x in said for x in f) \
                and said.count('EventQueryIsExistInPouch') == len(f) - 1 \
                and (' comes with %s' % f[0] in said) == (f[0] in FIRST_GET)
        good &= check('built: every family on the gift (%d builds)' % len(FAMILIES), ok)

        # the scrub: one family of each shape
        ok = True
        for n in SCRUB_BUILDS:
            f = FAMILIES[n]
            said, files = run('scrub', '%s=%s' % (SCRUB, text[n]))
            ok &= any(x.endswith('Enemy_Scrub_Business_Common.bfevfl.zs') for x in files) \
                and all('sells %s at' % x in said for x in f) \
                and said.count('.EventQueryIsExistInPouch') == len(f) - 1 \
                and (', with Item_' in said) == (f[0] in FIRST_GET) \
                and ('refused without the seed bag' in said) == (f[0] == 'Item_Range_SlingShot')
        good &= check('built: the scrub with %s (the other families: the flow edits above)'
                      % ', '.join(text[n] for n in SCRUB_BUILDS), ok)

        # one family across the kinds, as a seed would place it
        f = FAMILIES['BulletBag']
        said, files = run('mix', '%s=%s' % (CHESTS[0], text['BulletBag']), '%s=%s' % (ROCKS[0], text['BulletBag']),
                          '%s=%s' % (GIFT, text['BulletBag']), *CIRCLE_FIX)
        good &= check('built: the slingshot\'s family on a chest, a rock and the gift of one build: no note about '
                      'the number of checks',
                      'note:' not in said and 'Obj_TBox_NX2_BulletBag' in packs(files)
                      and turn_actors(['BulletBag']) - {turn_items.turn_name(f[0])} <= packs(files)
                      and once_items.once_name(f[0]) in packs(files))
        said, _ = run('mix', '%s=%s' % (CHESTS[0], text['BulletBag']), '%s=%s' % (ROCKS[0], text['BulletBag']))
        good &= check('  on two checks only, the build says that the last level cannot be reached',
                      'is on 2 checks, not 3: the last level cannot be reached' in said)

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
