"""Boss key, boss door, boss heart and Medallion test (tools/dungeon_items.py and tools/build_mod.py; phase 1,
part 7).

Read from the game's own files: where a dungeon's boss key, map and compass are saved; that the items
themselves are "not put in the inventory" and that it is the chests' shared opening event that sets them, for
the dungeon Link is in; the Forest Temple's boss key chest, boss door, boss heart and what brings the heart
into the room; the cutscene that hands over the Forest Medallion, and which file of it the game loads. Then
the nine versions (boss key, map, compass x ground, Gold Skulltula, chest) read back, what is refused, and a
whole build read back from the mod folder. Only reads the game; the build goes to a temporary folder that is
removed again.

    python tests/boss_check.py "C:\\...\\romfs"
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
import dungeon_items  # noqa: E402
import dungeon_keys  # noqa: E402
import ground_items  # noqa: E402
import start_state  # noqa: E402
from formats import zstd, byml, sarc, evfl, msbt  # noqa: E402
from logic.world import World  # noqa: E402

D = 'ForestTemple'
BOSS_KEY, MAP, COMPASS = 'Item_Dungeon_BossKey', 'Item_Dungeon_Map', 'Item_Dungeon_Compass'
MEDAL = 'Item_Medal_Forest'
MEDAL_FLOW, MEDAL_EVENT = 'Dm_Awake_Forest_Get', 'Event13'
BOSS_CHEST, HEART, MEDAL_CHECK = 'FT_BOSS_KEY_CHEST', 'FT_PHANTOM_GANON_HEART_CONTAINER_ITEM', 'FT_FOREST_MEDALLION_GIFT'
BOSS_ROOM_LOGIC = 'Logic/Module/ForestTemple_Level_Room_22_Prefab/ForestTemple_Level_Room_22_Prefab_c724.logic.module.ain'
SAMPLE = [
    ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01', BOSS_KEY + '@' + D),   # the boss key from a pot outside the temple
    ('KF_MIDO_CHEST_01', MAP + '@' + D),                         # the map in a chest outside
    ('FT_LOBBY_GS', COMPASS + '@' + D),                          # the compass on a Gold Skulltula in the temple
    ('FT_ENTRANCE_CHEST', BOSS_KEY + '@' + D),                   # in a chest of the temple: the game's own item
    (BOSS_CHEST, 'Item_Hammer'),                                 # another item in the boss key's chest
    (HEART, 'Item_Hookshot'),                                    # another item where the boss's heart is
    (MEDAL_CHECK, 'Item_Boomerang'),                             # another item where the Medallion is given
    ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02', MEDAL),                # and the Medallion somewhere else
]
REFUSED = [(['FT_FIRST_STALFOS_ROOM_POT_02=%s' % BOSS_KEY], 'only counts in a chest of its own dungeon'),
           (['KF_MIDO_CHEST_01=%s' % MAP], 'only counts in a chest of its own dungeon'),
           (['KF_MIDO_CHEST_01=%s@Nowhere' % BOSS_KEY], 'no dungeon Nowhere'),
           (['LW_SARIA_GIFT=%s@%s' % (BOSS_KEY, D)], 'cannot be put on a cutscene gift or a song yet')]


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def refused(fn, *args):
    try:
        fn(*args)
    except SystemExit as e:
        return str(e)
    return None


def steps_from(fc, entry):
    """[(actor, action or flow called, parameters)] of an entry point's plain line of steps"""
    out, i = [], fc.entry_point(entry).main
    while i is not None and len(out) <= len(fc.events):
        e = fc.events[i]
        if e.type == 'action':
            out.append((fc.actors[e.actor].name, build_mod._action_name(fc, e),
                        dict(e.params) if isinstance(e.params, dict) else e.params))
        else:
            out.append((e.type, getattr(e, 'flowchart', ''), None))
        i = e.next
    return out


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path):
        p = os.path.join(romfs, *path.split('/'))
        return open(p, 'rb').read() if os.path.exists(p) else zstd.decompress(open(p + '.zs', 'rb').read(), d)

    rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    there = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))   # noqa: E731
    good = True
    w = World()

    # ---- the game's files
    data = start_state.GameData(plain(start_state.GAME_DATA))
    fields = [data.find(dungeon_items.flag(item, x)) for item in dungeon_items.ITEMS for x in dungeon_keys.DUNGEONS]
    good &= check('the game: each of the %d dungeons has a saved yes/no for its boss key, map and compass '
                  '(DungeonInfo.<dungeon>.IsGetBossKey, IsGetMap, IsGetCompass)' % len(dungeon_keys.DUNGEONS),
                  all(f and f[0] == 'Bool' and int(f[1]['SaveFileIndex']) == 0 and f[1]['DefaultValue'] is False
                      for f in fields))
    pouch = {str(r['__RowId']): r for r in rows('PouchActorInfo')}
    good &= check('  the three items are "not put in the inventory": nothing happens when one is only handed over',
                  all(pouch[i].get('PouchSpecialDeal') == dungeon_items.NOT_PUSHED for i in dungeon_items.ITEMS))
    chest = evfl.loads(plain('Event/EventFlow/Dm_SY_Treasurebox.bfevfl')).flowchart
    asks = [e for e in chest.events if e.type == 'switch'
            and chest.actors[e.actor].queries[e.query] == 'EventQueryTreasureBoxIsDungeonCommonItemInside']
    acts = {build_mod._action_name(chest, e): e.params for e in chest.events if e.type == 'action'
            and chest.actors[e.actor].name == 'GameSystemActor'}
    gets = ['EventGetDungeonMap', 'EventGetDungeonCompass', 'EventGetDungeonBossKey', 'EventGetDungeonSmallKey']
    good &= check('  the chests\' shared opening event asks what dungeon item is inside and sets it itself (%s): '
                  'none of the four steps names a dungeon' % ', '.join(gets),
                  bool(asks) and all(g in acts and sorted(acts[g] or {}) == ['IsWaitEnd'] for g in gets), acts)
    banc = byml.loads(plain('Banc/%s/%s_Static.bcett.byml' % (D, D))).root
    actors = {int(a['Hash']): a for a in banc['Actors']}
    boss_chest = [a for a in actors.values() if (a.get('Dynamic') or {}).get('Drop__DropActor') == BOSS_KEY]
    gimmick = evfl.loads(plain('Event/EventFlow/ForestTemple_Gimmick.bfevfl')).flowchart
    event = str((boss_chest[0].get('Dynamic') or {}).get('GetEventName')) if boss_chest else ''
    setting = {str(r['__RowId']): r for r in byml.loads(plain(build_mod.EVENT_SETTING)).root}.get(event, {})
    steps = steps_from(gimmick, str(setting.get('EntryPointName'))) if setting else []
    good &= check('  the Forest Temple\'s boss key chest (%s) has an opening event of its own (%s): the usual '
                  'opening, then a message from Navi; the builder removes it with the boss key'
                  % (boss_chest[0]['Gyaml'] if boss_chest else '-', event),
                  len(boss_chest) == 1 and str(setting.get('FlowchartFileName', '')).endswith('/ForestTemple_Gimmick.evfc')
                  and [s[1] for s in steps] == ['EventTriggerParticipateEvent', 'EventTransition',
                                                'EventNaviRequestBallonMessage']
                  and steps[1][2].get('EventName') == 'Dm_SY_Treasurebox'
                  and build_mod.CHEST_EVENTS.get(event, ('',))[0] == 'remove', steps)
    doors = [a for a in actors.values() if a['Gyaml'] == 'Obj_DoorChainLock_A_02']
    hearts = [a for a in actors.values() if a['Gyaml'] == 'Obj_Heart_Container']
    group = [g for g in banc['AiGroups'] if str(g.get('Logic')) == BOSS_ROOM_LOGIC]
    refs = {str(r['Id']): int(r['Reference']) for g in group for r in g['References']}
    good &= check('  the temple has one boss door lock (Obj_DoorChainLock_A_02) and one Heart Container; the boss '
                  'room\'s logic brings the heart in by its place in the map, whatever lies there',
                  len(doors) == 1 and len(hearts) == 1 and len(group) == 1
                  and int(hearts[0]['Hash']) in refs.values(), refs)
    versions = build_mod.flow_versions(plain(build_mod.FLOW_VERSIONS))
    medal_file = '%s%s.%s%s' % (build_mod.FLOW_FOLDER, MEDAL_FLOW, versions.get(MEDAL_FLOW), build_mod.FLOW_EXT)
    medal_fc = evfl.loads(plain(medal_file)).flowchart
    get = {e.name: e for e in medal_fc.events}.get(MEDAL_EVENT)
    r, _, loc = build_mod.find_check(w, MEDAL_CHECK)
    good &= check('  the Forest Medallion is handed over by one step of the cutscene %s (%s: the get window and '
                  'the item), and the game loads the file %s for it (%d flows have such a version)'
                  % (MEDAL_FLOW, MEDAL_EVENT, medal_file.split('/')[-1], len(versions)),
                  get is not None and get.type == 'subflow' and (get.flowchart, get.entry) == build_mod.DIRECT_GET
                  and dict(get.params) == {'ActorName': MEDAL}
                  and loc.get('gift') == {'flow': MEDAL_FLOW, 'event': MEDAL_EVENT, 'item': MEDAL}
                  and all(os.path.exists(os.path.join(romfs, 'Event', 'EventFlow', '%s.%s.bfevfl.zs' % (n, v)))
                          for n, v in versions.items()), versions)

    # ---- the versions
    ok, said = True, []
    for item, (letter, field, word, texts) in dungeon_items.ITEMS.items():
        game = ground_items.item_components(sarc.Sarc.read(plain(ground_items.pack_path(item))).files, item)
        for kind in dungeon_items.NAMES:
            name, pack, new_inner, new_rows, like, loose = dungeon_items.build(item, D, kind, plain, rows, there)
            files = sarc.Sarc.read(pack).files
            comp = ground_items.resolved_components(files, name)
            settings = byml.loads(files[ground_items._ref_path(comp['PouchContentRef'])]).root
            msg = dungeon_items.message_name(item, D)
            ok &= name == dungeon_items.name(item, D, kind) and dungeon_items.is_ours(name) \
                and all(r['__RowId'] == name for r in new_rows.values()) \
                and new_rows['ActorInfo']['ActorName'] == msg and comp['ActorNameRef'] == dungeon_keys.NAME_REF % msg \
                and comp['ModelInfoRef'] == game['ModelInfoRef'] and 'PouchActor' not in settings \
                and new_rows['PouchActorInfo']['PouchSpecialDeal'] == dungeon_items.NOT_PUSHED
            if kind != 'chest':
                ai = dungeon_items.AI_NAMES[kind] % (word, D)
                ok &= dungeon_items.sets_of(files['AI/%s.root.ainb' % ai]) == [('DungeonInfo.' + D, field, True)]
            said.append(name)
    good &= check('the %d versions (boss key, map, compass; on the ground, from a Gold Skulltula, in a chest): the '
                  'item\'s model, its name the dungeon\'s chest version, no inventory item; on the ground its AI '
                  'sets the dungeon\'s field when it is picked up' % len(said), ok and len(said) == 9, said)
    other = dungeon_items.build(BOSS_KEY, 'WaterTemple', 'once', plain, rows, there)
    good &= check('  another dungeon\'s boss key sets that dungeon\'s field (%s)' % other[0],
                  dungeon_items.sets_of(sarc.Sarc.read(other[1]).files['AI/NX2_BossKey_WaterTemple.root.ainb'])
                  == [('DungeonInfo.WaterTemple', 'IsGetBossKey', True)])

    # ---- a whole build
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        wrong = []
        for args, want in REFUSED:
            got = refused(run, 'no', *args)
            if not got or want not in got:
                wrong.append('%s -> %s' % (' '.join(args), got))
        good &= check('%d requests are refused with their reason (the boss key on a pot and the map in a chest '
                      'outside without their dungeon named, no such dungeon, a cutscene gift)' % len(REFUSED), not wrong, wrong)
        said, folder = run('boss', *['%s=%s' % x for x in SAMPLE])
        read = lambda f: zstd.decompress(open(os.path.join(folder, *f.split('/')) + '.zs', 'rb').read(), d)   # noqa: E731
        held = {}
        for cid, _ in SAMPLE:
            r, _, loc = build_mod.find_check(w, cid)
            for scene, spot_id, p in w.placements_of(r, loc):
                for fn in p['files']:
                    acts = {str(int(a['Hash'])): a for a in byml.loads(read('Banc/%s/%s' % (scene, fn[:-3]))).root['Actors']}
                    dyn = dict(acts[p['hash']].get('Dynamic') or {})
                    held.setdefault(cid, set()).add((str(acts[p['hash']]['Gyaml']), dyn.get('Drop__DropActor'),
                                                     dyn.get(build_mod.TBOX_EVENT_KEY)))
        usual = 'KokiriForest_TreasureBox_NaviChatOff'
        event = build_mod.tbox_key_event(usual, (MAP, D))
        ours = lambda item, kind: dungeon_items.name(item, D, kind)   # noqa: E731
        good &= check('the sample builds; read back from the mod folder: the pot drops %s, the chest outside holds '
                      '%s and runs our event, the Gold Skulltula drops %s, the chest in the temple holds the '
                      'game\'s own boss key' % (ours(BOSS_KEY, 'once'), ours(MAP, 'chest'), ours(COMPASS, 'token')),
                      {x[1] for x in held['KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01']} == {ours(BOSS_KEY, 'once')}
                      and {x[1:] for x in held['KF_MIDO_CHEST_01']} == {(ours(MAP, 'chest'), event)}
                      and {x[1] for x in held['FT_LOBBY_GS']} == {ours(COMPASS, 'token')}
                      and {x[1:] for x in held['FT_ENTRANCE_CHEST']} == {(BOSS_KEY, None)}, held)
        flow = build_mod.tbox_sync_read(read(build_mod.flow_path(build_mod.TBOX_KEY_FLOW)))
        steps = flow.get(event, [])
        good &= check('  our chest event: Link joins, the chest\'s usual event (%s) runs, then %s is set; nothing '
                      'else' % (usual, dungeon_items.flag(MAP, D)),
                      list(flow) == [event] and len(steps) == 3 and steps[1][2].get('EventName') == usual
                      and steps[2][:2] == build_mod.KEY_SET
                      and steps[2][2] == {'GameDataName': dungeon_items.flag(MAP, D), 'Value': True, 'Index': -1},
                      steps)
        good &= check('  the boss key\'s chest holds the Megaton Hammer and opens like any other (its own event is '
                      'gone); where the boss\'s heart is lies the Hookshot\'s ground version, at the same place in '
                      'the map',
                      {x[1:] for x in held[BOSS_CHEST]} == {('Item_Hammer', None)}
                      and len(held[HEART]) == 1 and next(iter(held[HEART]))[0].startswith('Obj_NX2')
                      and 'Hookshot' in next(iter(held[HEART]))[0], (held[BOSS_CHEST], held[HEART]))
        medal_rel = medal_file + '.zs'
        back = evfl.loads(read(medal_file)).flowchart
        changed = [e.name for e, o in zip(back.events, medal_fc.events)
                   if (e.type, e.next, getattr(e, 'flowchart', ''), getattr(e, 'entry', ''),
                       dict(e.params) if isinstance(e.params, dict) else e.params)
                   != (o.type, o.next, getattr(o, 'flowchart', ''), getattr(o, 'entry', ''),
                       dict(o.params) if isinstance(o.params, dict) else o.params)]
        got = {e.name: e for e in back.events}[MEDAL_EVENT]
        good &= check('  the Medallion\'s cutscene hands over the Boomerang: only that step changed, in the file '
                      'the game loads (%s); the file of the plain name is not written' % medal_rel.split('/')[-1],
                      changed == [MEDAL_EVENT] and len(back.events) == len(medal_fc.events)
                      and dict(got.params) == {'ActorName': 'Item_Boomerang'}
                      and not os.path.exists(os.path.join(folder, 'Event', 'EventFlow', MEDAL_FLOW + '.bfevfl.zs')),
                      changed)
        info = {str(r['__RowId']): r for r in byml.loads(read(ground_items.table_path('ActorInfo'))).root}
        texts = msbt.Msbt.read(sarc.Sarc.read(read('Mals/USen.Product.110.sarc')).files[dungeon_keys.MESSAGE_FILE])
        msg = dungeon_items.message_name(BOSS_KEY, D)
        parts = [p if isinstance(p, str) else (p[0], p[1], bytes(p[2]))
                 for p in msbt.tags(texts.texts.get(msg + '_GetMessage', ''), 0)]
        good &= check('  the boss key from the pot is named %s, its chest version, which is built too and is named '
                      'itself; its get message names the temple in the temple\'s colour (%r)' % (msg, parts),
                      info[ours(BOSS_KEY, 'once')]['ActorName'] == msg and info[msg]['ActorName'] == msg
                      and parts == ['You found the Boss Key! (', (0, 3, b'\x03\x00'), 'Forest Temple',
                                    (0, 3, b'\xff\xff'), ')\x00']
                      and all(dungeon_items.message_name(i, D) + t in texts.texts
                              for i in dungeon_items.ITEMS for t, _ in dungeon_items.ITEMS[i][3])
                      and texts.texts['%s_Name' % BOSS_KEY] == 'Boss Key\x00', parts)
        good &= check('  the Medallion in the other pot is its one-time ground version',
                      all(str(x[1]).startswith('Obj_NX2') and 'Medal_Forest' in str(x[1])
                          for x in held['KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02']), held['KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02'])
        start = ['DungeonInfo.%s.IsGetBossKey=true' % D]
        _, sfolder = run('start', *[x for f in start for x in ('--start-flag', f)])
        written = open(os.path.join(sfolder, *start_state.MODULE.split('/')), 'rb').read()
        good &= check('starting with the boss key: the new-file module sets %s' % start[0].split('=')[0],
                      start_state.read_members(written) == [('DungeonInfo.%s.IsGetBossKey' % D, True)])

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
