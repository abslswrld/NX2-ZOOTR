"""Forest Temple data test: the temple's checks, regions and rules (data/world/ForestTemple.json) against the
game's own files. Only reads the game; changes nothing.

From the game's map files (Banc/ForestTemple) and room logic (Logic/ForestTemple_Level_Room_*): the 46 spots
and what the game puts in them, the five locked doors and the boss lock, the eye switches the Hookshot cannot
press, the two blocks of ice an arrow has to melt, the lobby's floor switch, and the pot that comes back in
the Bow room. From the project's data: every spot has one check with a permanent ID, the five locked doors
are the five key rules (1 to 5 keys, in the order the temple is walked), and the temple can be finished with
the items where the game itself puts them, and cannot without the Bow, the boss key or with a key missing.

    python tests/forest_temple_check.py "C:\\...\\romfs"
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_db  # noqa: E402
import extract_checks  # noqa: E402
from formats import zstd, byml, ainb  # noqa: E402
from logic.world import World  # noqa: E402

AREA = 'ForestTemple'
KEY, BOSS_KEY = 'ForestTempleSmallKey', 'ForestTempleBossKey'
SPOTS = {'chest': 12, 'skulltula': 5, 'pot': 28, 'freestanding': 1}
# what the game puts in the chests (map data), by check ID
GAME_CHESTS = {
    'FT_ENTRANCE_CHEST': 'Item_Dungeon_SmallKey', 'FT_FIRST_STALFOS_ROOM_CHEST': 'Item_Dungeon_SmallKey',
    'FT_WELL_CHEST': 'Item_Dungeon_SmallKey', 'FT_FLOORMASTER_CHEST': 'Item_Dungeon_SmallKey',
    'FT_JOELLE_CHEST': 'Item_Dungeon_SmallKey', 'FT_BOSS_KEY_CHEST': 'Item_Dungeon_BossKey',
    'FT_BOW_CHEST': 'Item_Range_Bow', 'FT_BETH_CHEST': 'Item_Dungeon_Compass',
    'FT_EAST_COURTYARD_CHEST': 'Item_Dungeon_Map', 'FT_BLOCK_ROOM_EYE_SWITCH_CHEST': 'TBox_Rupee_Purple',
    'FT_BASEMENT_CHEST': 'TBox_ArrowBundle_Large', 'FT_FALLING_CEILING_ROOM_CHEST': None,
}
# the game's items that the temple's own rules ask for, under the names the rules use
LOGIC_NAME = {'Item_Dungeon_SmallKey': KEY, 'Item_Dungeon_BossKey': BOSS_KEY, 'Item_Range_Bow': 'Bow'}
# the locked doors (x, z of the door), in the order the temple is walked, and the exit each one is
LOCKED_DOORS = [((0.7, 44.5), 'FT Entrance', 'FT Lobby'), ((-26.0, -0.7), 'FT Lobby', 'FT Block Room'),
                ((-55.8, -11.4), 'FT Block Room', 'FT West Twisted Corridor'),
                ((14.5, -58.8), 'FT Bow Room', 'FT Beth Room'),
                ((57.2, -11.5), 'FT East Twisted Corridor', 'FT Frozen Eye Switch Room')]
# what an adult brings to the temple's door (the way there: Mido in the Lost Woods, the Hookshot at the entrance)
ARRIVE = ['MasterSword', 'Hookshot', 'SariasSong', 'Ocarina']

results = []


def check(desc, ok, detail=''):
    results.append(ok)
    print('%-88s %s' % (desc, 'OK' if ok else 'FAILED' + (': ' + str(detail) if detail else '')))


def near(a, b, tol=0.6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def main(romfs):
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    actors = []
    for fn in sorted(os.listdir(os.path.join(romfs, 'Banc', AREA))):
        doc = byml.loads(zstd.decompress(open(os.path.join(romfs, 'Banc', AREA, fn), 'rb').read(), dicts)).root
        actors += list(doc['Actors'])
    by_hash = {int(a['Hash']): a for a in actors}
    w = World()
    spots = w.checks[AREA]
    world_file = json.load(open(os.path.join(ROOT, 'data', 'world', AREA + '.json'), encoding='utf-8'))
    db = json.load(open(os.path.join(ROOT, 'data', 'db', AREA + '.json'), encoding='utf-8'))
    ids = json.load(open(os.path.join(ROOT, 'data', 'ids.json'), encoding='utf-8'))
    regions = {r.name: r for r in w.regions.values() if r.scene == AREA}
    locs = {loc['id']: (r, name, loc) for r in regions.values() for name, loc in r.locations.items()}

    # ---- the spots, straight from the map files
    fresh = json.loads(json.dumps(extract_checks.extract(romfs, AREA, dicts)))
    check('data/checks/ForestTemple.json is what the map files hold today', fresh == spots)
    kinds = collections.Counter(s['kind'] for s in spots.values())
    check('46 spots: 12 chests, 5 Gold Skulltulas, 28 pots, 1 loose item', dict(kinds) == SPOTS, dict(kinds))
    check('every spot is one object (one map, no child and adult copies)',
          all(len(s['placements']) == 1 for s in spots.values()))
    respawn = [a for a in actors if a['Gyaml'].startswith('Obj_Pot') and a['Gyaml'].endswith('_Respawn')]
    pot1 = spots[locs['FT_BOW_ROOM_POT_01'][2]['spot']]
    check('one pot comes back (arrows, Bow room): not a check, and it stands where Bow Room Pot 1 is',
          len(respawn) == 1 and near(respawn[0]['Translate'], pot1['pos'], 0.11)
          and not any('Respawn' in p['actor'] for s in spots.values() for p in s['placements']))
    check('the loose item is the Heart Container, in the boss room',
          [s['item'] for s in spots.values() if s['kind'] == 'freestanding'] == ['Obj_Heart_Container'])

    # ---- one check per spot, permanent IDs
    check('47 checks: one per spot, plus the Forest Medallion (an event)',
          len(locs) == 47 and len(db) == 47 and sum(1 for _, _, l in locs.values() if 'spot' in l) == 46
          and {l['spot'] for _, _, l in locs.values() if 'spot' in l} == set(spots))
    check('data/db/ForestTemple.json is up to date (tools/build_db.py ForestTemple)',
          json.loads(json.dumps(build_db.build(w, AREA))) == db)
    registered = {k for k, v in ids['ids'].items() if k.startswith('FT_') and v['status'] == 'active'}
    check('the 47 IDs are registered under area code FT, none retired',
          ids['areas'].get('FT') == 'Forest Temple' and registered == set(locs)
          and all(ids['ids'][k]['check'] == locs[k][1] for k in locs))
    got = {cid: spots[l['spot']]['item'] for cid, (_, _, l) in locs.items() if cid in GAME_CHESTS}
    check('the 12 chests hold what the map files say (5 small keys, boss key, Bow, map, compass...)',
          got == GAME_CHESTS, {k: v for k, v in got.items() if GAME_CHESTS.get(k) != v})
    check('the database gives the same contents, and a Gold Skulltula token for each Skulltula',
          all(r['vanilla_contents']['value'] == GAME_CHESTS[r['unique_check_id']] for r in db
              if r['unique_check_id'] in GAME_CHESTS)
          and [r['vanilla_contents']['value'] for r in db if r['check_type'] == 'skulltula']
          == ['GoldSkulltulaToken'] * 5)
    check('every region of the temple is still "not verified in game", every check "untested"',
          not any(r.verified for r in regions.values())
          and all(l.get('randomizable') == 'untested' for _, _, l in locs.values()))

    # ---- locked doors: the map against the rules
    locks = [a for a in actors if a['Gyaml'] == 'Obj_DoorChainLock_A_01']
    doors = [a for a in actors if a['Gyaml'] == 'Obj_ForestTemple_Door_A_01']
    locked = sorted((a for a in doors if sum(by_hash.get(int(l['Dst']), {}).get('Gyaml') == 'Obj_DoorChainLock_A_01'
                                             for l in a.get('Links', [])) == 2),
                    key=lambda a: [i for i, d in enumerate(LOCKED_DOORS)
                                   if near((a['Translate'][0], a['Translate'][2]), d[0])] or [99])
    check('5 doors have chain locks, one on each side (10 locks): 5 small keys are needed',
          len(locks) == 10 and len(locked) == 5 and len(doors) == 13)
    check('they are the five doors the rules lock',
          [near((a['Translate'][0], a['Translate'][2]), d[0]) for a, d in zip(locked, LOCKED_DOORS)] == [True] * 5)
    key_rules = {}
    for r in regions.values():
        for target, (txt, _) in r.exits.items():
            if KEY in str(txt):
                key_rules[(r.name, target)] = str(txt)
    want = {(a, b): (KEY if n == 1 else 'has(%s, %d)' % (KEY, n)) for n, (_, a, b) in enumerate(LOCKED_DOORS, 1)}
    check('the rules ask for 1, 2, 3, 4 and 5 keys at those doors, in the order the temple is walked',
          key_rules == want, key_rules)
    check('the game puts exactly 5 small keys in the temple, as many as it has locked doors',
          list(GAME_CHESTS.values()).count('Item_Dungeon_SmallKey') == 5
          and sum(1 for s in spots.values() if s['item'] == 'Item_Dungeon_SmallKey') == 5)
    boss_lock = [a for a in actors if a['Gyaml'] == 'Obj_DoorChainLock_A_02']
    check('one boss lock, on the basement shutter in front of Phantom Ganon; the rule asks for the boss key',
          len(boss_lock) == 1 and near(boss_lock[0]['Translate'], (0.0, 59.5, -40.9))
          and BOSS_KEY in regions['FT Basement'].exits['FT Phantom Ganon Room'][0])

    # ---- switches, ice, the lobby, from the map and the room logic
    eyes = [a for a in actors if a['Gyaml'].startswith('Obj_EyeSwitch')]
    no_hook = [a for a in eyes if dict(a.get('Dynamic') or {}).get('isHitHookShot') is False]
    check('5 eye switches; the map says of 3 that the Hookshot does not press them (block room x2, Bow room)',
          len(eyes) == 5 and len(no_hook) == 3, (len(eyes), len(no_hook)))

    def logic(name):
        return ainb.loads(open(os.path.join(romfs, 'Logic', name + '.logic.module.ainb'), 'rb').read())

    def strings(doc):
        return {x.value for n in doc.nodes for group in (n.immediates, n.inputs) for lst in group.values()
                for x in lst if isinstance(x.value, str)}

    def source_outputs(doc):
        """the names of the outputs that other nodes of the module read"""
        out = set()
        for n in doc.nodes:
            for t, lst in n.inputs.items():
                for inp in lst:
                    for s in (inp.sources or ([(inp.node, inp.param, 0)] if inp.node >= 0 else [])):
                        outs = doc.nodes[s[0]].outputs.get(t, [])
                        if s[1] < len(outs):
                            out.add((doc.nodes[s[0]].name, outs[s[1]].name))
        return out

    ice = [a for a in actors if a['Gyaml'] == 'Obj_Ice_A_01']
    melt = {'ForestTemple_Level_Room_26_Prefab_2a87': 'ForestTemple_Room14_MeltedIce',
            'ForestTemple_Level_Room_17_Prefab_7ee5': 'ForestTemple_Room27_MeltedIce'}
    ok = len(ice) == 2
    for name, flag in melt.items():
        doc = logic(name)
        ok = ok and flag in strings(doc) and ('ActorLogicIce', 'isArrow') in source_outputs(doc)
    check('2 blocks of ice over eye switches (east corridor room, basement): melted by an arrow (isArrow)', ok)
    doc = logic('ForestTemple_Level_Room_02_Prefab_f080')
    names = [n.name for n in doc.nodes]
    check('lobby: a floor switch opens the shutter to the east courtyard (no eye switch, unlike its flag name)',
          'ActorLogicBootUpActorIsFirstOn' in names and 'ActorLogicShutter' in names
          and any(s.startswith('Obj_StepSwitch') for s in strings(doc))
          and 'ForestTemple_Room02_GoldEyeSwitch_On' in strings(doc))
    block = [a for a in actors if a['Gyaml'] == 'Obj_SongOfTimeBlock_A_01']
    check('lobby: one Song of Time block, in front of the west courtyard door; the rule asks for the song',
          len(block) == 1 and near(block[0]['Translate'], (-19.0, 100.0, -19.1))
          and regions['FT Lobby'].exits['FT West Courtyard'][0] == 'can_play(SongOfTime)')
    doc = logic('ForestTemple_Level_Room_06_Prefab_6b8c')
    check('Bow room: its west shutter waits for the eye switch (logic module), and the rule back out asks for the Bow',
          {'ForestTemple_Level_Room_06_PressedEyeball', 'ForestTemple_Room06_GetBow'} <= strings(doc)
          and regions['FT Bow Room'].exits['FT Joelle Room'][0] == 'can_use(Bow)'
          and regions['FT Joelle Room'].exits['FT Bow Room'][0] == 'True')
    check('first room: its Gold Skulltula asks for no item (in game 2026-11-23: no Hookshot needed)',
          regions['FT Entrance'].locations['FT GS Entrance'].get('rule', True) is True)
    sisters = {'Enemy_Poe_Joelle', 'Enemy_Poe_Beth', 'Enemy_Poe_Amy', 'Enemy_MiddleBoss_Poe_Meg'}
    check('the four Poe sisters and Phantom Ganon are in the map; Meg needs the other three beaten',
          sisters <= {a['Gyaml'] for a in actors} and 'Enemy_DungeonBoss_PhantomGanon' in {a['Gyaml'] for a in actors}
          and all(("'FT %s Defeated'" % n) in regions['FT Lobby'].events['FT Meg Defeated'][0]
                  for n in ('Joelle', 'Beth', 'Amy')))

    # ---- the search: the temple with the items where the game puts them
    check('data problems: none', not w.problems(), w.problems())
    check('SFM Upper leads to FT Entrance (adult, Hookshot); no "not mapped yet" Forest Temple region is left',
          w.regions['SFM Upper'].exits['FT Entrance'][0] == 'is_adult and can_use(Hookshot)'
          and not any('Forest Temple' in n and 'not mapped' in n for n in w.regions))
    game_item = {l['id']: LOGIC_NAME.get(spots[l['spot']]['item']) for _, _, l in locs.values() if 'spot' in l}
    name_to_id = {name: cid for cid, (_, name, _) in locs.items()}

    def walk(start, without=()):
        """collect the temple's checks in rounds, taking what the game puts in each; returns (checks got, state)"""
        items, got = list(start), set()
        while True:
            _, reach, state = w.search(items)
            new = {name_to_id[n] for n in reach if n in name_to_id} - got
            if not new:
                return got, state
            for cid in sorted(new):
                got.add(cid)
                if game_item.get(cid) and cid not in without:
                    items.append(game_item[cid])

    got, state = walk(ARRIVE + ['SongOfTime'])
    check('with the game\'s own items: all 47 checks, Phantom Ganon beaten',
          len(got) == 47 and state.count('Forest Temple Clear') and state.count(KEY) == 5 and state.count('Bow') == 1,
          (len(got), state.count(KEY)))
    got, state = walk(ARRIVE)
    check('the same without the Song of Time (the well is drained by way of the block room)',
          len(got) == 47 and state.count('Forest Temple Clear'))
    got, state = walk(ARRIVE, without={'FT_BOW_CHEST'})
    check('without the Bow: no Poe sister, no basement, no boss; 26 checks are left (3 keys, as far as the Bow room)',
          not state.count('Forest Temple Clear') and not state.count('FT Joelle Defeated')
          and 'FT_BASEMENT_CHEST' not in got and 'FT_BOW_CHEST' in got and state.count(KEY) == 3
          and len(got) == 26, len(got))
    got, state = walk(ARRIVE, without={'FT_BOSS_KEY_CHEST'})
    check('without the boss key: everything but the boss room (45 checks)',
          not state.count('Forest Temple Clear') and len(got) == 45, len(got))
    got, state = walk(ARRIVE, without={'FT_JOELLE_CHEST'})
    check('with Joelle\'s key missing (4 keys): the last locked door stays shut, no boss',
          not state.count('Forest Temple Clear') and 'FT_FROZEN_EYE_SWITCH_ROOM_POT_01' not in got
          and 'FT_BETH_CHEST' in got and state.count(KEY) == 4)
    got, state = walk(ARRIVE, without={'FT_WELL_CHEST'})
    check('with the well\'s key missing: stuck at the third locked door (2 keys), before the Bow',
          not state.count('Bow') and state.count(KEY) == 2 and 'FT_BLOCK_ROOM_POT_01' in got
          and 'FT_BOW_CHEST' not in got)
    got, state = walk(['MasterSword', 'SariasSong', 'Ocarina'])
    check('without the Hookshot the temple is not entered at all', not got)
    _, reach, _ = w.search(ARRIVE + [KEY] * 5 + [BOSS_KEY, 'Bow'])
    check('the temple is adult only (a child cannot reach its door)',
          all(reach.get(name) == {'adult'} for _, name, _ in locs.values()))
    req = {r['unique_check_id']: r['requirements'] for r in db}
    check('database requirements count keys once: the Heart Container needs "ForestTempleSmallKey*5", not 1+2+3+4+5',
          all(sum(1 for n in alt if n.startswith(KEY)) == 1 and KEY + '*5' in alt and BOSS_KEY in alt and 'Bow' in alt
              for alt in req['FT_PHANTOM_GANON_HEART_CONTAINER_ITEM']['adult'])
          and req['FT_PHANTOM_GANON_HEART_CONTAINER_ITEM']['child'] is None)
    check('the first chest needs no key; the lobby needs one',
          all(not any(n.startswith(KEY) for n in alt) for alt in req['FT_ENTRANCE_CHEST']['adult'])
          and all(KEY in alt for alt in req['FT_LOBBY_POT_01']['adult']))

    print('\n%s' % ('ALL OK' if all(results) else '%d FAILED' % results.count(False)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
