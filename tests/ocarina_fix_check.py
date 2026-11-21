"""Ocarina fix test: an ocarina from a chest or from the ground that can be played at once. Builds a mod with
tools/build_mod.py into a temporary folder (removed afterwards) and reads it back against the game's own files:
the opening event of our own for chests that hold an ocarina, and the real ocarina named as Link's equipment by
the ground and turning versions (as the game's ground shield names his shield). Only reads the game files.

    python tests/ocarina_fix_check.py "C:\\...\\romfs"
"""
import contextlib
import hashlib
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
import sizes  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, restbl, sarc, evfl  # noqa: E402

FAIRY, TIME = 'Item_Ocarina_Fairy', 'Item_Ocarina_Time'
PAIR = '%s>%s' % (FAIRY, TIME)
SMALL, BIG, MIDO = 'Dm_SY_TreasureboxSmall', 'Dm_SY_Treasurebox', 'KokiriForest_TreasureBox_NaviChatOff'
# what the test build places: check -> item (the Ocarina of Time only as the second level of the pair)
PLACED = {
    'KF_STORMS_GROTTO_CHEST': FAIRY,               # a plain small chest (no event named in the map)
    'KF_KOKIRI_SWORD_CHEST': FAIRY,                # a big chest (its special event is removed: CHEST_EVENTS)
    'KF_MIDO_CHEST_01': PAIR,                      # one of Mido's chests, a progressive pair
    'KF_MIDO_CHEST_02': FAIRY,                     # one of Mido's chests, an ocarina alone
    'LW_BRIDGE_CHEST': PAIR,                       # a plain small chest, a progressive pair (two maps)
    'KF_MIDO_CHEST_03': 'Item_Boomerang',          # no ocarina
    'KF_MIDO_CHEST_04': 'Item_Scale_Silver>Item_Scale_Gold',    # a pair without an ocarina
    'KF_SARIAS_HOUSE_HEART_ITEM_07': FAIRY,        # on the ground
    'KF_HOUSE_OF_TWINS_CHILD_POT_01': FAIRY,       # from a pot
    'KF_RUPEE_NEAR_MIDO_ITEM': PAIR,               # a turning item
    'KF_RUPEE_NEAR_FADO_ITEM_01': 'Item_Boomerang',             # on the ground, no ocarina
}
# placement hash -> the opening event its chest must have in the build (None: none named); every other actor of
# every map must name the event it names in the game
CHESTS = {
    '14818888396401495482': SMALL,                 # KF_STORMS_GROTTO_CHEST
    '16757992849254467386': BIG,                   # KF_KOKIRI_SWORD_CHEST
    '12786193094758345086': MIDO,                  # KF_MIDO_CHEST_01
    '10831981390482426294': MIDO,                  # KF_MIDO_CHEST_02
    '4349272251343787229': SMALL,                  # LW_BRIDGE_CHEST (Kokiri Forest map)
    '17479747339356189279': SMALL,                 # LW_BRIDGE_CHEST (Lost Woods map)
}
NOT_OCARINA = ('4555665598794293658', '9725242744547055868')        # KF_MIDO_CHEST_03, _04: Mido's event stays
JOIN = ('Player_Event', 'EventTriggerParticipateEvent', None)
SYNC = [('EventSystemActor', 'EventWait', {'Frames': 1, 'IsWaitEnd': True}),
        ('UISystemActor', 'EventTriggerSyncPlayerEquipmentAndPouch', None),
        ('Player_Event', 'EventWaitCreationFinishedEquipment', {'IsWaitEnd': True})]
BASE_TABLE = 'GameParameter/GameParameterTable/Obj_Item_Base.engine__actor__GameParameterTable.bgyml'
# packs as the builder made them before this change (sha256), 2026-11-20: versions that must not change
UNCHANGED = {
    ('Item_Boomerang', 'ground'): '559db1535a330d78aff7e46f07c7f1d837bbef5212b4595652896ae0446926f2',
    ('Item_DinFire', 'ground'): 'cc4c1c77d27130586d2d82ddf87be129505ccb762383187d16ee35fb9d4e7aff',
    ('Item_Hookshot', 'ground'): '28069e5994bb72356bc33abb6acd654c230df1a730ed77556ddfd46ea0e52735',
    ('Item_AgonyStone', 'ground'): 'b914d2e1abe4d9aedd05aed688be6823083414fbe17e26c69e3dcf6a29693392',   # Echo Gem
    ('Item_Boomerang', 'held'): '335116612313ed3ace03035386af7a8fa16e2aa3f9f26d66b028e35785f1c1b5',
    (FAIRY, 'held'): '1d07eb872a0fcae4d78cd5878c7cd48de3397224b3ae89423a89dc9b7479dcff',
    (TIME, 'held'): '1672e43b58e3b611064d747e03c2d72bc93b440c8f3eb5a07fe3510e0b683388',
    (FAIRY, 'token'): '254a0b424e17646ece7c236ec64238495479318845c465682e07d982c70ad801',
    (TIME, 'token'): '75583414eef413e1b6f5f4ca88b314503020dc17f43a780725b3d3592a2bd78f',
}
UNCHANGED_TURN = {
    ('Item_Scale_Silver', 'Item_Scale_Gold'): ('d7b823049e389e7d20cd89006b3aa4c065d928c37903aefe24a5fec2a7321e6e',
                                               '1963632f9648f99004259c0199dcc4261770013bea548fd8d34f7da150505c13'),
    ('Item_Hookshot', 'Item_Longshot'): ('7ba3d27f3b6a251a42dd3cc08034f6008a01508139cf22917f5cefe637cbfa40',
                                         '78d8b7f71ed3d5fb148ff9f650c23f38c423eb51d194c7ba0dabdadd32e14371'),
}
# the ocarinas' ground and turning versions as they were before (contents: the names and sha256 of the pack's
# files, see contents): with the two new files and the one new setting taken out again, each must hold exactly
# those files (two files more move the others inside the pack, so the pack's own bytes differ)
SHIELD = 'Obj_Shield_Deku'
BEFORE = {
    'Obj_NX2_Ocarina_Fairy': '1387b3b309dc19f6a214ac06fc5167b597b3f16aa845312eadbcb2eb04ddc471',
    'Obj_NX2_Ocarina_Time': '19636fd420fde9cea22590effd0675ba5655f0c90a3f0b0ac97b2e6afa2c2124',
    'Obj_NX2P_Ocarina_Fairy': 'aa960465bb43f7d0f2bf017c4467ceb2ccab4bb8d15f9cb002a50ae7d8835096',
    'Obj_NX2P_Ocarina_Time': '2eca19e803fadada5116bdd7aefdc63696cef5dbb794c3834dd2bfc1ecf23c2b',
}
SHARED_FLOWS = ('Dm_SY_GetInEvent', 'Dm_SY_Get', 'GetPouchContent', 'Dm_SY_Treasurebox', 'Dm_SY_TreasureboxSmall')


def check(name, ok):
    print('%-88s %s' % (name, 'OK' if ok else 'FAILED'))
    return bool(ok)


def refused(f, *a):
    try:
        f(*a)
    except SystemExit:
        return True
    return False


def plain(v):
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    return v


def steps_of(fc, start):
    """the steps from event `start` on, as (actor, action, parameters), while they are plain actions"""
    out, i = [], start
    while i is not None and fc.events[i].type == 'action' and len(out) <= len(fc.events):
        e = fc.events[i]
        a = fc.actors[e.actor]
        out.append((a.name, a.actions[e.action], dict(e.params) if isinstance(e.params, dict) else e.params))
        i = e.next
    return out, i


def contents(files):
    """one checksum of a pack's files: their names and what is in them"""
    x = hashlib.sha256()
    for p, data in sorted(files.items()):
        x.update(p.encode() + b'\0' + hashlib.sha256(data).digest())
    return x.hexdigest()


def without_ocarina(pack, name):
    """the files of a pack with the ocarina's parameter table, the equipment file it names and the actor's mention
    of the table taken out again"""
    arc = sarc.Sarc.read(pack)
    table = ground_items.table_param_path(name)
    param = ground_items._ref_path(byml.loads(arc.files[table]).root['Components'][ground_items.EQUIP_COMPONENT])
    doc = byml.loads(arc.files[ground_items.ap_path(name)])
    doc.root = type(doc.root)(doc.root)
    comp = type(doc.root['Components'])(doc.root['Components'])
    del comp['GameParameterTableRef']
    doc.root['Components'] = comp
    files = dict(arc.files)
    del files[table], files[param]
    files[ground_items.ap_path(name)] = byml.dumps(doc)
    return files


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    game = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)  # noqa: E731
    rows = lambda t: byml.loads(game(ground_items.table_path(t))).root   # noqa: E731
    model = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))  # noqa: E731
    sha = lambda data: hashlib.sha256(data).hexdigest()   # noqa: E731
    good = True

    # ---- what the game has
    good &= check("a chest's usual opening event: small chests (plain, checking, _NoBake) %s, big chests %s"
                  % (SMALL, BIG),
                  [build_mod.chest_usual_event(game, c) for c in (
                      'Obj_TBox_A_01', 'Obj_TBox_A_01_NoBake', 'Obj_TBox_A_06', 'Obj_TBox_A_06_NoBake',
                      'Obj_TBox_A_02', 'Obj_TBox_A_02_NoBake', 'Obj_TBox_A_03')] == [SMALL] * 4 + [BIG] * 3)
    good &= check('  a chest actor that is not in the game is refused',
                  refused(build_mod.chest_usual_event, game, 'Obj_TBox_NX2_Nothing'))
    ice = evfl.loads(game(build_mod.flow_path(build_mod.TBOX_SYNC_LIKE_FLOW))).flowchart
    ice_steps, _ = steps_of(ice, {p.name: p.main for p in ice.entry_points}[build_mod.TBOX_SYNC_LIKE])
    run_params = {'IsWaitEnd': True, 'SpecialEventActionType': 1, 'FadeInTypeEventEnd': 0}
    good &= check("the game's own chest event %s: Link joins, then %s is run and waited for"
                  % (build_mod.TBOX_SYNC_LIKE, BIG),
                  ice_steps[:2] == [JOIN, ('EventSystemActor', 'EventTransition', dict(run_params, EventName=BIG))])
    boss = evfl.loads(game(build_mod.SYNC_FLOW)).flowchart
    found = False
    for i, e in enumerate(boss.events):
        if e.type == 'action' and boss.actors[e.actor].actions[e.action] == 'EventWait':
            found |= steps_of(boss, i)[0][:3] == SYNC
    good &= check("the game's own sync: a one-frame wait, the sync, the wait for Link's equipment", found)
    setting = {r['__RowId']: r for r in byml.loads(game(build_mod.EVENT_SETTING)).root}
    info = {r['__RowId']: r for r in byml.loads(game(build_mod.EVENT_INFO)).root}
    good &= check('the three usual events are events of the game that run no other event',
                  all(u in setting and u in info and not info[u].get('ChildEventList') for u in (SMALL, BIG, MIDO)))
    good &= check('  an event that runs other events itself is refused as a usual event',
                  refused(build_mod.tbox_sync_rows, list(setting.values()), list(info.values()),
                          ['MiniGame_DampeRace_OpenGoalTBox']))
    pouch = {r['__RowId']: r for r in rows('PouchActorInfo')}
    good &= check('the ocarinas are the items whose special deal is %s' % build_mod.SYNC_DEAL,
                  sorted(n for n, r in pouch.items() if r.get('PouchSpecialDeal') == build_mod.SYNC_DEAL
                         and n.startswith('Item_')) == [FAIRY, TIME])

    # ---- the build
    with tempfile.TemporaryDirectory() as tmp:
        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log):
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', 'T']
                               + ['%s=%s' % x for x in PLACED.items()])
        except SystemExit as e:
            print(log.getvalue()[-2000:])
            print('the build stopped: %s' % e)
            return 1
        mod = os.path.join(tmp, 'T', 'romfs')
        built = lambda path: zstd.decompress(open(os.path.join(mod, *path.split('/')) + '.zs', 'rb').read(), d)  # noqa: E731
        made = sorted(os.path.relpath(os.path.join(dp, f), mod).replace(os.sep, '/')[:-3]
                      for dp, _, fs in os.walk(mod) for f in fs)
        table = restbl.Restbl.read(built(build_mod.RESTBL_PATH.replace(os.sep, '/')[:-3]))
        game_table = restbl.Restbl.read(game(build_mod.RESTBL_PATH.replace(os.sep, '/')[:-3]))
        flow_file = build_mod.flow_path(build_mod.TBOX_SYNC_FLOW)
        events = {u: build_mod.tbox_sync_event(u) for u in (SMALL, BIG, MIDO)}

        # the flow
        good &= check('the only event flow in the mod is ours (%s); no shared flow is changed' % flow_file,
                      [p for p in made if p.startswith('Event/')] == [flow_file]
                      and not any(build_mod.flow_path(f) in made for f in SHARED_FLOWS)
                      and not os.path.exists(os.path.join(romfs, *flow_file.split('/')) + '.zs'))
        data = built(flow_file)
        ef = evfl.loads(data)
        fc = ef.flowchart
        good &= check('the flow: one entry point per usual event used, named as its event',
                      sorted(p.name for p in fc.entry_points) == sorted(events.values())
                      and fc.name == build_mod.TBOX_SYNC_FLOW and ef.version == evfl.loads(game(
                          build_mod.flow_path(build_mod.TBOX_SYNC_LIKE_FLOW))).version)
        ok = len(fc.events) == 5 * len(events)
        for usual, name in events.items():
            got, end = steps_of(fc, {p.name: p.main for p in fc.entry_points}[name])
            ok &= end is None and got == [JOIN, ('EventSystemActor', 'EventTransition',
                                                 dict(run_params, EventName=usual))] + SYNC
            ok &= got[:2] == [ice_steps[0], (ice_steps[1][0], ice_steps[1][1], dict(ice_steps[1][2], EventName=usual))]
        good &= check('  each: Link joins, the usual event (waited for), a frame, the sync, the wait; nothing else',
                      ok)
        theirs = {a.name: a for f in (ice, boss) for a in f.actors if not a.secondary}
        good &= check("  its three actors are the game's own, with the game's settings",
                      sorted(a.name for a in fc.actors) == ['EventSystemActor', 'Player_Event', 'UISystemActor']
                      and all(not a.secondary and not a.argument and a.entry_point is None
                              and a.cut == theirs[a.name].cut and plain(a.params) == plain(theirs[a.name].params)
                              for a in fc.actors))
        good &= check('  it rewrites byte for byte, and every entry point lists no other flow',
                      evfl.dumps(evfl.loads(data)) == data and not any(
                          e.type in ('subflow', 'callswitch', 'switch', 'fork', 'join') for e in fc.events))

        # the two table rows
        for path, key in ((build_mod.EVENT_SETTING, 'EventSetting'), (build_mod.EVENT_INFO, 'GameAnalyzedEventInfo')):
            old, new = byml.loads(game(path)).root, byml.loads(built(path)).root
            ids = [r['__RowId'] for r in new]
            mine = [r for r in new if r['__RowId'] in events.values()]
            like = {r['__RowId']: r for r in old}[build_mod.TBOX_SYNC_LIKE]
            ok = ids == sorted(ids) and len(ids) == len(set(ids)) and len(mine) == len(events) \
                and [r for r in new if r['__RowId'] not in events.values()] == list(old)
            for usual, name in events.items():
                row = plain({r['__RowId']: r for r in new}.get(name, {}))
                if key == 'EventSetting':
                    want = dict(plain(like), __RowId=name, EntryPointName=name,
                                FlowchartFileName='Work/Event/EventFlow/%s.evfc' % build_mod.TBOX_SYNC_FLOW)
                else:
                    want = dict(plain(like), __RowId=name, ChildEventList=[usual])
                    want.pop('SubFlowList', None)
                ok &= row == want
            good &= check('%s: three rows of ours, sorted in; each the game\'s %s row with our names; the '
                          'other %d rows as they were' % (key, build_mod.TBOX_SYNC_LIKE, len(old)), ok)

        # the size table
        in_mod = [n for n in BEFORE if ground_items.pack_path(n) in made]
        per_actor = (ground_items.table_param_path, ground_items.equip_param_path)
        shield_files = sarc.Sarc.read(game(ground_items.pack_path(SHIELD))).files

        def need(path, data):
            # as the builder: the headroom of the ground shield's file of the same kind, at least what the rules ask
            like = ground_items.new_file_like(path, SHIELD)
            e = game_table.get(like)
            return max(e - len(shield_files[like]) + len(data), sizes.entry(path, data, e, shield_files[like]))

        new_files = [flow_file] + [f(n) for n in in_mod for f in per_actor]
        good &= check('size table: the flow, the three parameter tables and their equipment files are new entries, '
                      'at least what the rules ask',
                      in_mod == ['Obj_NX2_Ocarina_Fairy', 'Obj_NX2P_Ocarina_Fairy', 'Obj_NX2P_Ocarina_Time']
                      and all(game_table.get(p) is None for p in new_files)
                      and table.get(flow_file) >= sizes.rule(flow_file, data)
                      and all(table.get(f(n)) >= need(f(n), sarc.Sarc.read(built(ground_items.pack_path(n))).files[f(n)])
                              for n in in_mod for f in per_actor))
        good &= check('  the changed tables and maps have entries for their new sizes',
                      all(table.get(p) >= sizes.rule(p, built(p)) and table.get(p) >= game_table.get(p)
                          for p in made if p.startswith(('RSDB/', 'Banc/'))))
        ok = True
        for p in made:
            if p.startswith('Pack/Actor/'):
                ok &= table.get(p) is not None and all(table.get(i) is not None
                                                       for i in sarc.Sarc.read(built(p)).files)
        good &= check('  every new pack and every file in it has an entry', ok)

        # the maps: only the chests that hold an ocarina name our event
        ok, seen, kept = True, set(), set()
        for p in made:
            if not p.startswith('Banc/'):
                continue
            before = {str(int(a['Hash'])): a for a in byml.loads(game(p)).root['Actors']}
            for a in byml.loads(built(p)).root['Actors']:
                h = str(int(a['Hash']))
                was = (before[h].get('Dynamic') or {}).get(build_mod.TBOX_EVENT_KEY)
                now = (a.get('Dynamic') or {}).get(build_mod.TBOX_EVENT_KEY)
                if h in CHESTS:
                    seen.add(h)
                    ok &= now == events[CHESTS[h]]
                else:
                    ok &= now == was
                    if h in NOT_OCARINA:
                        kept.add(h)
                        ok &= now == MIDO and a['Dynamic']['Drop__DropActor'] in ('Item_Boomerang', 'Item_Scale_Silver')
        good &= check('maps: the chests that hold an ocarina name our event around their usual one (plain small, '
                      'big, Mido\'s, pairs)', ok and seen == set(CHESTS))
        good &= check('  every other actor names the event it names in the game (the Boomerang chest and the '
                      'scales pair: Mido\'s)', ok and kept == set(NOT_OCARINA))
        actors = {str(int(a['Hash'])): a for p in made if p.startswith('Banc/')
                  for a in byml.loads(built(p)).root['Actors']}
        good &= check('  the ground, pot and turning spots hold the ocarina\'s ground and turning versions',
                      sorted(n for n in in_mod if any(
                          a['Gyaml'] == n or (a.get('Dynamic') or {}).get('Drop__DropActor') == n
                          for a in actors.values())) == ['Obj_NX2P_Ocarina_Fairy', 'Obj_NX2_Ocarina_Fairy'])
        good &= check('  the pairs are checking chests: Fairy Ocarina while Link has none, then Ocarina of Time',
                      all(actors[h]['Gyaml'] == 'Obj_TBox_A_06' and plain(actors[h]['Dynamic']) == {
                          'Drop__DropActor': 'Item_NX2_Ocarina_Fairy', 'Drop__CheckActor': FAIRY,
                          'Drop__DropActor_Substitute': 'Item_NX2_Ocarina_Time',
                          'GetEventName': events[CHESTS[h]]}
                          for h in ('12786193094758345086', '4349272251343787229', '17479747339356189279')))

        # the ground and turning ocarinas in the mod (the ground Ocarina of Time, not placed: built here)
        shield = sarc.Sarc.read(game(ground_items.pack_path(SHIELD))).files
        shield_table = plain(byml.loads(shield[ground_items.table_param_path(SHIELD)]).root)
        pouch_mod = {r['__RowId']: r for r in byml.loads(built(ground_items.table_path('PouchActorInfo'))).root}
        ok = ok_rows = ok_rest = True
        for name in BEFORE:
            item = TIME if name.endswith('Time') else FAIRY
            equipment = 'Work/Actor/%s.engine__actor__ActorParam.gyml' % item
            if name in in_mod:
                pack, row = built(ground_items.pack_path(name)), pouch_mod.get(name, {})
            else:
                _, pack, _, new_rows, _ = ground_items.build(item, game, rows, model, 'ground')
                row = new_rows['PouchActorInfo']
            files = sarc.Sarc.read(pack).files
            comp = ground_items.resolved_components(files, name)
            ok &= comp.get('GameParameterTableRef') == '?' + ground_items.table_param_path(name)
            ok &= plain(byml.loads(files[ground_items.table_param_path(name)]).root) == dict(
                shield_table, Components={'PlayerEquipmentActor': '?' + ground_items.equip_param_path(name)})
            ok &= plain(byml.loads(files[ground_items.equip_param_path(name)]).root) == {'Adult': equipment,
                                                                                       'Child': equipment}
            ok &= ground_items.equipment_of(files, name) == (equipment, equipment) and BASE_TABLE in files
            ok &= not any(p.startswith('Game/OcarinaParam/') for p in files)
            ok_rows &= plain(row) == dict(plain(pouch[item]), __RowId=name, AdultEquipment=equipment,
                                          ChildEquipment=equipment)
            ok_rest &= contents(without_ocarina(pack, name)) == BEFORE[name]
        good &= check('ground and turning ocarinas: a parameter table of their own (the ground shield\'s, over the '
                      'item base\'s) naming the real ocarina as Link\'s equipment, in a file of their pack', ok)
        good &= check('  their PouchActorInfo rows: the ocarina\'s, with AdultEquipment and ChildEquipment naming it',
                      ok_rows)
        good &= check('  nothing else in them changed: without the table every file of each pack is as before; '
                      'no ocarina settings file (the earlier try) left', ok and ok_rest)
        good &= check('  the ground Boomerang in the mod is byte for byte as before',
                      sha(built(ground_items.pack_path('Obj_NX2_Boomerang'))) == UNCHANGED[('Item_Boomerang', 'ground')])

    # ---- the way the game carries it, and the versions that must not change
    shield = sarc.Sarc.read(game(ground_items.pack_path(SHIELD))).files
    deku = 'Work/Actor/Weapon_Shield_Deku.engine__actor__ActorParam.gyml'
    good &= check("the game's ground shield names Link's shield the same way: the component in its table, and both "
                  "row fields",
                  ground_items.equipment_of(shield, SHIELD) == (deku, deku)
                  and all(pouch[SHIELD].get(k) == deku for k in ground_items.EQUIP_ROW))
    good &= check('  the ocarinas are known by their own settings; an item that is not an ocarina has none',
                  all(ground_items.ocarina_param(sarc.Sarc.read(game(ground_items.pack_path(i))).files, i)
                      for i in (FAIRY, TIME))
                  and all(ground_items.ocarina_param(sarc.Sarc.read(game(ground_items.pack_path(i))).files, i) is None
                          for i in ('Item_Boomerang', 'Item_Hookshot', 'Weapon_Shield_Deku')))
    good &= check("  the game's ocarinas name no equipment in their rows (so an add of the real ocarina makes it)",
                  not any(k in pouch[i] for i in (FAIRY, TIME) for k in ground_items.EQUIP_ROW))
    ok = True
    for (item, version), digest in UNCHANGED.items():
        ok &= sha(ground_items.build(item, game, rows, model, version)[1]) == digest
    good &= check('unchanged, byte for byte: ground Boomerang, Din\'s Fire, Hookshot, Echo Gem; held-up Boomerang '
                  'and ocarinas; the ocarinas as Gold Skulltula drops', ok)
    ok = True
    for family, digests in UNCHANGED_TURN.items():
        for level, digest in enumerate(digests):
            ok &= sha(turn_items.build(family, level, game, rows, model)[1]) == digest
    good &= check('unchanged, byte for byte: the turning scales and hookshots', ok)

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
