"""Dungeon keys test: a small key that counts for one dungeon wherever it is found (tools/dungeon_keys.py;
CHECK_ID=Item_Dungeon_SmallKey@Dungeon in tools/build_mod.py; phase 1, part 5).

Read from the game's own files: where a dungeon's key count is saved, that the game's own key nodes name no
dungeon, and the game's models for the two new steps (the Gerudo Fortress key's AI, the treasure chest game's
flow). Then the key's three versions (ground, Gold Skulltula, chest) read back, what is refused, and a whole
build of the test sample read back from the mod folder. Only reads the game; the build goes to a temporary
folder that is removed again.

    python tests/dungeon_keys_check.py "C:\\...\\romfs"
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
import ground_items  # noqa: E402
import once_items  # noqa: E402
import start_state  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, sarc, ainb, evfl, msbt  # noqa: E402
from logic.world import World  # noqa: E402

D = 'ForestTemple'
KEY = dungeon_keys.KEY_ITEM
NODE_DEFS = 'AI/NodeDefinition/Node.Product.111.aidefn.byml'
GAME_KEY_NODES = ('OneShotDungeonGetSmallKey', 'OneShotDungeonUseSmallKey', 'QueryDungeonGetSmallKeyNum',
                  'EventGetDungeonSmallKey', 'EventUseDungeonSmallKey')
# the test build of part 5 (out/TEST_CHECKLIST.md)
SAMPLE = [
    ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01', KEY + '@' + D),     # a Forest Temple key in a pot outside the temple
    ('KF_MIDO_CHEST_01', KEY + '@' + D),                      # and in a chest
    ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02', 'Obj_Dungeon_SmallKey'),   # the control: the game's own key outside
    ('FT_ENTRANCE_GS', KEY + '@' + D),                        # in the temple itself: the game's own key
    ('KF_HOUSE_OF_TWINS_CHILD_POT_01', KEY + '@' + D + '+name'),   # with the temple's name in its messages
    ('KF_MIDO_CHEST_02', KEY + '@' + D + '+name'),            # and so in a chest
    ('KF_MIDO_CHEST_03', KEY + '@WaterTemple+name'),          # a name in a colour of our own (blue)
    ('FT_ENTRANCE_CHEST', 'Item_Hammer'),                     # the chest that held the first key
]
REFUSED = [(['KF_MIDO_CHEST_01=%s@Nowhere' % KEY], 'no dungeon Nowhere'),
           (['KF_MIDO_CHEST_01=Item_Hammer@%s' % D], 'only %s@<dungeon>' % KEY),
           (['LW_SARIA_GIFT=%s@%s' % (KEY, D)], 'cannot be put on a gift yet'),
           (['LW_NEAR_BRIDGE_SCRUB=%s@%s' % (KEY, D)], 'cannot be put on a scrub yet')]


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def refused(fn, *args):
    try:
        fn(*args)
    except SystemExit as e:
        return str(e)
    return None


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
    counts = {x: data.find(dungeon_keys.flag(x)) for x in dungeon_keys.DUNGEONS}
    good &= check('the game: each of the %d dungeons has a saved key count, the number DungeonInfo.<dungeon>.'
                  'SmallKeyNum' % len(counts),
                  all(c and c[0] == 'Int' and int(c[1]['SaveFileIndex']) == 0 for c in counts.values())
                  and all((data.find(dungeon_keys.STRUCT % x) or ('',))[0] == 'Struct' for x in counts),
                  [x for x, c in counts.items() if not c])
    defs = byml.loads(plain(NODE_DEFS)).root
    good &= check('  its own key steps name no dungeon (%s): they count for the dungeon Link is in'
                  % ', '.join(GAME_KEY_NODES),
                  all(n in defs and not dict(defs[n].get('Inputs') or {}) for n in GAME_KEY_NODES))
    pouch = {str(r['__RowId']): r for r in rows('PouchActorInfo')}
    good &= check('  a new inventory item is not possible: the game\'s key has no saved count of its own in the '
                  'inventory, and the key of the treasure chest game is "not put in the inventory"',
                  data.find('PouchData.%s.StockNum' % KEY) is None
                  and pouch[dungeon_keys.NOT_PUSHED_ACTOR].get('PouchSpecialDeal') == dungeon_keys.NOT_PUSHED
                  and pouch[KEY].get('PouchSpecialDeal') == dungeon_keys.SMALL_KEY)
    shared = sarc.Sarc.read(plain(turn_items.AI_PACK)).files
    gerudo = ainb.loads(shared[dungeon_keys.STRUCT_SOURCE])
    names = [n.name for n in gerudo.nodes]
    good &= check('  the game\'s model on the ground: the Gerudo Fortress key sets a named flag of a named struct '
                  'when it is picked up (its AI)',
                  'OneShotSetGameDataBool' in names and dungeon_keys.Q_STRUCT in names
                  and once_items.Q_DEAD in names)
    add, q = dungeon_keys.templates(plain)
    good &= check('  the two nodes copied are found: %s (adds 1) and %s' % (add.name, q.name),
                  add.name == dungeon_keys.N_ADD and q.name == dungeon_keys.Q_STRUCT)
    game_flow = evfl.loads(plain(build_mod.KEY_ADD_FLOW)).flowchart
    actor, action, params = build_mod.key_add_template(game_flow)
    good &= check('  the game\'s model in a flow: the treasure chest game adds 1 to its own key count (%s.%s %s)'
                  % (actor.name, action, params.get('GameDataName')),
                  params.get('GameDataName') == 'MiniGame_SmallKeyNum' and params.get('Value') == 1)

    # ---- the key's versions
    built = {kind: dungeon_keys.build(D, kind, plain, rows, there) for kind in dungeon_keys.NAMES}
    value = dungeon_keys.not_pushed_value(plain)
    key_files = sarc.Sarc.read(plain(ground_items.pack_path(KEY))).files
    ok = True
    for kind, (name, pack, new_inner, new_rows, like) in built.items():
        files = sarc.Sarc.read(pack).files
        comp = ground_items.resolved_components(files, name)
        settings = byml.loads(files[ground_items._ref_path(comp['PouchContentRef'])]).root
        row = new_rows['PouchActorInfo']
        ok &= name == dungeon_keys.name(D, kind) and dungeon_keys.dungeon_of(name) == (D, kind) \
            and 'PouchActor' not in settings and settings['SpecialDeal'] == value \
            and row['PouchSpecialDeal'] == dungeon_keys.NOT_PUSHED and 'PouchStockable' not in row \
            and all(r['__RowId'] == name for r in new_rows.values()) \
            and comp['ActorNameRef'] == ground_items.item_components(key_files, KEY)['ActorNameRef'] \
            and comp['ModelInfoRef'] == ground_items.item_components(key_files, KEY)['ModelInfoRef']
    good &= check('the Forest Temple key\'s three versions (%s): the key\'s name and model; item settings and '
                  'table row "not put in the inventory", no inventory item named, not counted'
                  % ', '.join(b[0] for b in built.values()), ok)
    ok, said = True, []
    for kind in ('once', 'token'):
        name, pack = built[kind][:2]
        files = sarc.Sarc.read(pack).files
        ai = dungeon_keys.AI_NAMES[kind] % D
        was = once_items.mark_ai(once_items.sources(plain)['base'], once_items.sources(plain), 'x', False) \
            if kind == 'once' else files[ground_items.TOKEN_FILES[0]]
        new_doc, old_doc = ainb.loads(files['AI/%s.root.ainb' % ai]), ainb.loads(was)
        ok &= dungeon_keys.counts_of(files['AI/%s.root.ainb' % ai]) == [(dungeon_keys.STRUCT % D, 'SmallKeyNum', 1)] \
            and len(new_doc.nodes) == len(old_doc.nodes) + 2 and not dungeon_keys.counts_of(was) \
            and [n.name for n in new_doc.nodes[:len(old_doc.nodes)]] == [n.name for n in old_doc.nodes] \
            and ground_items.resolved_components(files, name)['AIInfoRef'].endswith('/%s.engine__actor__AIInfo.bgyml' % ai)
        said.append('%s: %d nodes' % (ai, len(new_doc.nodes)))
    good &= check('  on the ground and from a Gold Skulltula: its AI is the version\'s own with two nodes more; '
                  'picked up, it adds 1 to DungeonInfo.%s.SmallKeyNum (%s)' % (D, '; '.join(said)), ok)
    other = dungeon_keys.build('WaterTemple', 'once', plain, rows, there)
    good &= check('  another dungeon\'s key counts for that dungeon (%s)' % other[0],
                  dungeon_keys.counts_of(sarc.Sarc.read(other[1]).files['AI/NX2_Key_WaterTemple.root.ainb'])
                  == [('DungeonInfo.WaterTemple', 'SmallKeyNum', 1)])

    # ---- a whole build: the test sample
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        wrong = []
        for args, want in REFUSED:
            said = refused(run, 'no', *args)
            if not said or want not in said:
                wrong.append('%s -> %s' % (' '.join(args), said))
        good &= check('%d requests are refused with their reason (no such dungeon, another item, a gift, a scrub)'
                      % len(REFUSED), not wrong, wrong)
        said, folder = run('keys', *['%s=%s' % x for x in SAMPLE])
        read = lambda f: zstd.decompress(open(os.path.join(folder, *f.split('/')) + '.zs', 'rb').read(), d)   # noqa: E731
        held = {}
        for cid, _ in SAMPLE:
            r, _, loc = build_mod.find_check(w, cid)
            for scene, spot_id, p in w.placements_of(r, loc):
                for fn in p['files']:
                    acts = {str(int(a['Hash'])): a for a in byml.loads(read('Banc/%s/%s' % (scene, fn[:-3]))).root['Actors']}
                    dyn = dict(acts[p['hash']].get('Dynamic') or {})
                    held.setdefault(cid, set()).add((dyn.get('Drop__DropActor'), dyn.get(build_mod.TBOX_EVENT_KEY)))
        usual = 'KokiriForest_TreasureBox_NaviChatOff'
        event = build_mod.tbox_key_event(usual, D)
        good &= check('the sample builds; read back from the mod folder: the pot drops %s, the chest holds %s and '
                      'runs our event, the Gold Skulltula drops %s, the control pot the game\'s own key'
                      % (dungeon_keys.name(D, 'once'), dungeon_keys.name(D, 'chest'),
                         'the game\'s own key (it is in its own temple)'),
                      held['KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01'] == {(dungeon_keys.name(D, 'once'), None)}
                      and held['KF_MIDO_CHEST_01'] == {(dungeon_keys.name(D, 'chest'), event)}
                      and held['FT_ENTRANCE_GS'] == {('Obj_NX2_GS_Dungeon_SmallKey', None)}
                      and held['KF_HOUSE_OF_TWINS_CHILD_POT_01'] == {(dungeon_keys.name(D, 'once', True), None)}
                      and {x[0] for x in held['KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02']}
                      == {'Obj_NX2_GS_Obj_Dungeon_SmallKey'}, held)
        flow = build_mod.tbox_sync_read(read(build_mod.flow_path(build_mod.TBOX_KEY_FLOW)))
        steps = flow.get(event, [])
        good &= check('  our chest event: Link joins, the chest\'s usual event (%s) runs, then 1 is added to '
                      'DungeonInfo.%s.SmallKeyNum; nothing else (and one such event for the chest key of the Water Temple)' % (usual, D),
                      sorted(flow) == sorted([event, event.replace(D, 'WaterTemple')]) and len(steps) == 3
                      and steps[1][2].get('EventName') == usual
                      and steps[2][:2] == build_mod.KEY_ADD
                      and steps[2][2] == {'GameDataName': dungeon_keys.flag(D), 'Value': 1, 'Index': -1}, steps)
        settings = {str(r['__RowId']): r for r in byml.loads(read(build_mod.EVENT_SETTING)).root}
        infos = {str(r['__RowId']): r for r in byml.loads(read(build_mod.EVENT_INFO)).root}
        good &= check('  and its two table rows name the flow, the entry point and the usual event',
                      event in settings and settings[event]['EntryPointName'] == event
                      and str(settings[event]['FlowchartFileName']).endswith('/%s.evfc' % build_mod.TBOX_KEY_FLOW)
                      and [str(x) for x in infos[event]['ChildEventList']] == [usual])
        table = {str(r['__RowId']): r for r in byml.loads(read(ground_items.table_path('PouchActorInfo'))).root}
        good &= check('  the versions built are in the item table as "not put in the inventory"; the game\'s key '
                      'rows are untouched',
                      all(table[dungeon_keys.name(D, k)]['PouchSpecialDeal'] == dungeon_keys.NOT_PUSHED
                          for k in ('once', 'chest')) and dict(table[KEY]) == dict(pouch[KEY])
                      and dungeon_keys.name(D, 'token') not in table)
        info = {str(r['__RowId']): r for r in byml.loads(read(ground_items.table_path('ActorInfo'))).root}
        msg = dungeon_keys.MESSAGE_NAME % D
        texts = {}
        for lang in ('USen', 'JPja'):
            arc = sarc.Sarc.read(read('Mals/%s.Product.110.sarc' % lang))
            texts[lang] = msbt.Msbt.read(arc.files[dungeon_keys.MESSAGE_FILE]).texts
        refs = {}
        for version in (dungeon_keys.name(D, 'once', True), dungeon_keys.name(D, 'chest', True),
                        dungeon_keys.name(D, 'once'), dungeon_keys.name(D, 'chest')):
            vfiles = sarc.Sarc.read(read(ground_items.pack_path(version))).files
            refs[version] = ground_items.resolved_components(vfiles, version)['ActorNameRef']
        game_ref = ground_items.item_components(key_files, KEY)['ActorNameRef']
        good &= check('  the named key: its row and its actor file are named %s, the named chest key, which is '
                      'named itself; its three texts are in the message files with the temple\'s name (%r)'
                      % (msg, texts['USen'].get(msg + '_Name')),
                      info[dungeon_keys.name(D, 'once', True)]['ActorName'] == msg
                      and msg == dungeon_keys.name(D, 'chest', True)
                      and info[msg]['ActorName'] == msg
                      and refs[dungeon_keys.name(D, 'once', True)] == dungeon_keys.NAME_REF % msg
                      and refs[dungeon_keys.name(D, 'chest', True)] == dungeon_keys.NAME_REF % msg
                      and refs[dungeon_keys.name(D, 'once')] == game_ref
                      and refs[dungeon_keys.name(D, 'chest')] == game_ref
                      and info[dungeon_keys.name(D, 'once')]['ActorName'] == KEY
                      and texts['USen'].get(msg + '_Name') == 'Small Key (Forest Temple)\x00'
                      and all(msg + t in texts[lang] for lang in texts for t, _ in dungeon_keys.MESSAGES)
                      and texts['USen']['%s_Name' % KEY] == 'Small Key\x00')
        got = texts['USen'].get(msg + '_GetMessage', '')
        parts = msbt.tags(got, 0)
        good &= check('  the temple\'s name is in its colour in the get message (the game\'s green, number 3), '
                      'between the game\'s own colour tag and its end; a colour that does not exist and a colour '
                      'for a dungeon no key names are refused',
                      [p if isinstance(p, str) else (p[0], p[1], bytes(p[2])) for p in parts] == [
                          'You found a small key! (', (0, 3, b'\x03\x00'), 'Forest Temple',
                          (0, 3, b'\xff\xff'), ')\x00']
                      and bool(refused(run, 'no', '--key-colour', '%s=99' % D, '%s=%s+name' % (SAMPLE[0][0], SAMPLE[0][1])))
                      and bool(refused(run, 'no', '--key-colour', '%s=pink' % D, '%s=%s+name' % (SAMPLE[0][0], SAMPLE[0][1])))
                      and bool(refused(run, 'no', '--key-colour', 'FireTemple=3', '%s=%s' % SAMPLE[0])), parts)
        game_pack = sarc.Sarc.read(plain(dungeon_keys.COLOUR_PACK)).files
        built_pack = sarc.Sarc.read(read(dungeon_keys.COLOUR_PACK)).files
        game_list = byml.loads(game_pack[dungeon_keys.COLOUR_TABLE]).root[dungeon_keys.COLOUR_LIST]
        built_list = byml.loads(built_pack[dungeon_keys.COLOUR_TABLE]).root[dungeon_keys.COLOUR_LIST]
        water = msbt.tags(texts['USen'].get(dungeon_keys.MESSAGE_NAME % 'WaterTemple' + '_GetMessage', ''), 0)
        place, rgb = dungeon_keys.OUR_COLOURS['blue']
        rest = [i for i in range(len(game_list)) if i != place]
        good &= check('  a colour of our own (the Water Temple\'s blue): place %d of the game\'s %d text colours has '
                      'its three colour values changed and its name kept; the other places and every other file '
                      'of the pack are unchanged, and the name is in number %d' % (place, len(game_list), place),
                      len(game_list) == len(built_list) == dungeon_keys.GAME_COLOUR_COUNT
                      and all(built_list[i] == game_list[i] for i in rest)
                      and (built_list[place].get('Red', 0), built_list[place].get('Green', 0),
                           built_list[place].get('Blue', 0)) == rgb
                      and built_list[place].get('ColorName') == game_list[place].get('ColorName')
                      and set(built_pack) == set(game_pack)
                      and all(built_pack[k] == v for k, v in game_pack.items() if k != dungeon_keys.COLOUR_TABLE)
                      and (0, 3, bytes([place, 0])) in [(p[0], p[1], bytes(p[2])) for p in water
                                                        if not isinstance(p, str)],
                      built_list[place])
        start = ['DungeonInfo.%s.SmallKeyNum=2' % D, 'DungeonInfo.%s.IsGetMap=true' % D,
                 'DungeonInfo.%s.IsGetCompass=true' % D, 'DungeonInfo.WaterTemple.SmallKeyNum=1',
                 'IsVisitLocation.KokiriForest=true']
        _, sfolder = run('start', *[x for f in start for x in ('--start-flag', f)])
        written = open(os.path.join(sfolder, *start_state.MODULE.split('/')), 'rb').read()
        good &= check('starting with keys, the map and the compass, and a place marked as visited: the new-file '
                      'module sets the fields of the records (%s)' % ', '.join(start),
                      start_state.read_members(written) == [
                          ('DungeonInfo.%s.SmallKeyNum' % D, 2), ('DungeonInfo.%s.IsGetMap' % D, True),
                          ('DungeonInfo.%s.IsGetCompass' % D, True), ('DungeonInfo.WaterTemple.SmallKeyNum', 1),
                          ('IsVisitLocation.KokiriForest', True)]
                      and start_state.read_members(plain(start_state.MODULE)) == []
                      and len(start_state.read_members(written, 'PlayerStatus')) == 5)
        refusals = [refused(run, 'no', '--start-flag', f) for f in ('PlayerStatus.MaxLife=80', 'DungeonInfo.%s.NoSuch=1' % D)]
        good &= check('  a field of another struct, and a field that does not exist, are still refused',
                      all(refusals) and 'a field of a struct' in refusals[0] and 'no flag of this name' in refusals[1], refusals)
        good &= check('  the build says what each key does', said.count('adds 1 to %s' % dungeon_keys.flag(D)) >= 3
                      and 'key chests' in said)

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
