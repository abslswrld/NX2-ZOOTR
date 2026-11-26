"""The Forest Temple's loose ends (phase 1, part 9): what the parts before left open there.

- An upgrade family where the Medallion is given (Saria's cutscene, FT_FOREST_MEDALLION_GIFT): the cutscene
  asks the game's inventory question in front of its get and gives the next level.
- What floats down in that cutscene is what it gives, not always the Forest Medallion: the cutscene's own actor
  Item_Medal_Forest is renamed to the item, or for a family one actor per level, each run of its steps (size,
  bind to the locator, glitter) behind the same questions, as the game's Dm_LostWood_0040 shows one of two
  bags; an item the cutscene cannot show (a heart) leaves those steps out, so nothing floats down.
- An upgrade family in a big chest: the chest becomes the game's checking chest, a small chest at the same spot
  (the checking chest's AI asks for a sensor body the big chest does not have).
- A small key with the dungeon's name in its own dungeon (Item_Dungeon_SmallKey@ForestTemple, with or without
  +name): the named key, counted by our own step, instead of the game's own key (which has one text for every
  dungeon). Passed in game 2026-11-25; the user chose the name over the count on screen (decision 46).
- A big chest made small loses its kept opening event when that is only the big chest's opening (the map's
  chest played the big chest's opening in game).

Three builds, each read back from the mod folder. Only reads the game; the builds go to a temporary folder that
is removed again.

    python tests/forest_temple_loose_ends_check.py "C:\\...\\romfs"
"""
import contextlib
import io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import dungeon_keys  # noqa: E402
import ground_items  # noqa: E402
from formats import zstd, byml, sarc, evfl, restbl  # noqa: E402
from logic.world import World  # noqa: E402

AREA = 'ForestTemple'
MAPS = ('Banc/ForestTemple/ForestTemple_Static.bcett.byml', 'Banc/ForestTemple/ForestTemple_Dynamic.bcett.byml')
GIFT = 'FT_FOREST_MEDALLION_GIFT'
FLOW = 'Event/EventFlow/Dm_Awake_Forest_Get.110.bfevfl'     # the file the game loads (EventFlowFileEntry)
MEDAL = 'Item_Medal_Forest'
# the cutscene's steps of the Medallion actor, as the game has them: (the step before, the run, what follows)
LOCATOR = 'Dm_Locator'
LOD_RUN = ('Event16', ['Event39', 'Event15'], None)          # Dm_Locator's warp -> size -> bind to the locator
GLITTER_FORK, GLITTER_RUN = 'Event17', ('Event20', 'Event21')  # a branch of the fork: glitter, then the shaft's
NAMED_KEY = 'Item_Dungeon_SmallKey@%s+name' % AREA
BUILDS = {
    # the round's build (the in-game test)
    'round': {GIFT: 'Item_Hookshot>Item_Longshot',
              'FT_BOW_CHEST': 'Item_Scale_Silver>Item_Scale_Gold',
              'FT_EAST_COURTYARD_CHEST': 'Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large',
              'FT_LOBBY_POT_01': NAMED_KEY, 'FT_WELL_CHEST': NAMED_KEY,
              'FT_ENTRANCE_CHEST': 'Item_Dungeon_SmallKey@' + AREA},
    'heart': {GIFT: 'Obj_Heart_Piece'},                      # nothing the cutscene can show
    'rupee': {GIFT: 'Obj_Rupee_Red'},                        # one item: the chest's rupee shown
}
BIG = {'FT_BOW_CHEST': ('Obj_TBox_A_02_NoBake', 'Obj_TBox_A_06_NoBake'),
       'FT_EAST_COURTYARD_CHEST': ('Obj_TBox_A_02', 'Obj_TBox_NX2_BombBag')}


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def dyn(actor):
    return dict(actor.get('Dynamic') or {})


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path, root=romfs):
        p = os.path.join(root, *path.split('/'))
        if os.path.exists(p):
            return open(p, 'rb').read()
        return zstd.decompress(open(p + '.zs', 'rb').read(), d) if os.path.exists(p + '.zs') else None

    good = True
    w = World()
    template = build_mod.gift_pair_template(evfl.loads(plain(build_mod.GIFT_PAIR_FLOW)).flowchart)
    game_fc = evfl.loads(plain(FLOW)).flowchart
    gift = build_mod.find_check(w, GIFT)[2]['gift']
    names = {e.name: k for k, e in enumerate(game_fc.events)}
    before_get, = [e.name for e in game_fc.events if e.next == names[gift['event']]]

    def act(fc, i):
        e = fc.events[i]
        return (fc.actors[e.actor].name, fc.actors[e.actor].actions[e.action]) if e.type == 'action' else None

    # ---- the game's files
    lod, glit = [names[n] for n in LOD_RUN[1]], names[GLITTER_RUN[0]]
    good &= check('the game\'s Medallion cutscene shows %s as an actor of its own: %s, %s (bind to %s), %s '
                  '(glitter), all before its get %s' % (MEDAL, LOD_RUN[1][0], LOD_RUN[1][1], LOCATOR,
                                                        GLITTER_RUN[0], gift['event']),
                  [act(game_fc, i) for i in lod + [glit]] == [(MEDAL, 'EventTriggerSetModelLodManual'),
                                                            (MEDAL, build_mod.CUTSCENE_BIND),
                                                            (MEDAL, 'EventTriggerEmitXLink')]
                  and game_fc.events[names[LOD_RUN[0]]].next == lod[0] and game_fc.events[lod[1]].next is None
                  and game_fc.events[lod[1]].params.get('ActorName') == LOCATOR
                  and not set(lod + [glit]) & set(game_fc.reachable(names[gift['event']])))
    lw = evfl.loads(plain('Event/EventFlow/Dm_LostWood_0040.bfevfl')).flowchart
    binds = {lw.actors[e.actor].name for e in lw.events if act(lw, lw.events.index(e)) is not None
             and act(lw, lw.events.index(e))[1] == build_mod.CUTSCENE_BIND}
    asks = [e for e in lw.events if e.type == 'switch' and lw.actors[e.actor].queries[e.query]
            == build_mod.GIFT_PAIR_QUERY and e.params.get('Actor') == 'Item_BulletBag_Medium']
    good &= check('  the game shows one of two items that way itself: Dm_LostWood_0040 asks whether Link has the '
                  'bigger seed bag, then binds one of two bag actors to the locator',
                  binds == {'Item_BulletBag_Medium', 'Item_BulletBag_Large'} and len(asks) >= 1)
    ctl = lambda n: sarc.Sarc.read(plain(ground_items.pack_path(n))).files   # noqa: E731
    big_set = ctl('Obj_TBox_A_02')['Phive/ControllerSetParam/Obj_TBox_A_02.phive__ControllerSetParam.bgyml']
    small_set = ctl('Obj_TBox_A_01')['Phive/ControllerSetParam/Obj_TBox_A_01.phive__ControllerSetParam.bgyml']
    check_ai = ctl('Obj_TBox_A_06')['AI/Obj_TBox_A_06.root.ainb']
    good &= check('the game has no big checking chest: the checking chest\'s AI asks for the sensor body "Sensor", '
                  'the small chest has it, the big one has "EnemyCheck" instead',
                  b'Sensor\0' in check_ai and re.search(rb'\bSensor\b', small_set) is not None
                  and re.search(rb'\bSensor\b', big_set) is None and b'EnemyCheck' in big_set
                  and not any(n.startswith('Obj_TBox_A_02') for n in build_mod.CHECKING_CHEST.values()))

    builds = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, plan in BUILDS.items():
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + ['%s=%s' % x for x in sorted(plan.items())])
            folder = os.path.join(tmp, name, 'romfs')
            files = sorted(os.path.relpath(os.path.join(dp, f), folder).replace(os.sep, '/')
                           for dp, _, fn in os.walk(folder) for f in fn)
            builds[name] = (out.getvalue(), folder, files)
            good &= check('build "%s" (%s): %d files written' % (name, ', '.join('%s=%s' % x for x in sorted(plan.items()))
                                                                [:60] + '...', len(files)),
                          FLOW + '.zs' in files)

        def flow_of(name):
            return evfl.loads(plain(FLOW, builds[name][1])).flowchart

        # ---- the round: a family on the Medallion's check, shown level by level
        fc = flow_of('round')
        ix = {e.name: k for k, e in enumerate(fc.events)}
        levels = ('Item_Hookshot', 'Item_Longshot')
        gets, runs, glits = [], [], []
        for k in range(len(levels)):
            owned = set(levels[:k])
            g = build_mod.level_reached(fc, fc.events[ix[before_get]].next, owned, template)
            gets.append(dict(fc.events[g].params).get('ActorName'))
            r = build_mod.level_reached(fc, fc.events[ix[LOD_RUN[0]]].next, owned, template)
            runs.append([act(fc, r), act(fc, fc.events[r].next) if fc.events[r].next is not None else None,
                         fc.events[fc.events[r].next].params.get('ActorName') if fc.events[r].next is not None
                         else None])
            branch = fc.events[ix[GLITTER_FORK]].forks[game_fc.events[names[GLITTER_FORK]].forks.index(glit)]
            x = build_mod.level_reached(fc, branch, owned, template)
            glits.append((act(fc, x), fc.events[fc.events[x].next].name if fc.events[x].next is not None else None))
        good &= check('the round: Saria\'s cutscene gives %s, or %s when Link has the Hookshot (the game\'s question '
                      'in front of its get %s)' % (levels[0], levels[1], gift['event']), gets == list(levels), gets)
        good &= check('  and shows what it gives: %s > %s run with the Hookshot\'s actor or the Longshot\'s, bound '
                      'to %s, behind the same question' % (LOD_RUN[1][0], LOD_RUN[1][1], LOCATOR),
                      runs == [[(lv, 'EventTriggerSetModelLodManual'), (lv, build_mod.CUTSCENE_BIND), LOCATOR]
                               for lv in levels], runs)
        good &= check('  its glitter too (%s with the level\'s actor, then %s as before)' % GLITTER_RUN,
                      glits == [((lv, 'EventTriggerEmitXLink'), GLITTER_RUN[1]) for lv in levels], glits)
        good &= check('  the cutscene has no %s actor left, and one actor for each level'
                      % MEDAL, not any(a.name == MEDAL for a in fc.actors)
                      and all(sum(1 for a in fc.actors if a.name == lv) == 1 for lv in levels))

        # ---- the round: families in the big chests, named keys in the temple
        said, folder, files = builds['round']
        back = {m: {str(int(a['Hash'])): a for a in byml.loads(plain(m, folder) or plain(m)).root['Actors']}
                for m in MAPS}
        game = {m: {str(int(a['Hash'])): a for a in byml.loads(plain(m)).root['Actors']} for m in MAPS}

        def spot(cid):
            reg, _, loc = build_mod.find_check(w, cid)
            (scene, _, p), = list(w.placements_of(reg, loc))
            m = 'Banc/%s/%s' % (scene, p['files'][0][:-3])
            return game[m][p['hash']], back[m][p['hash']]

        got = {}
        for cid, (was, now) in BIG.items():
            g, b = spot(cid)
            got[cid] = (g['Gyaml'], b['Gyaml'], dyn(b).get('Drop__DropActor'), dyn(b).get('Drop__CheckActor'),
                        dyn(b).get('Drop__DropActor_Substitute'))
        good &= check('the round: the Bow\'s big chest holds Silver > Gold Scale as the game\'s checking chest, a '
                      'small one (%s -> %s)' % BIG['FT_BOW_CHEST'],
                      got['FT_BOW_CHEST'] == BIG['FT_BOW_CHEST'] + ('Item_Scale_Silver', 'Item_Scale_Silver',
                                                                    'Item_Scale_Gold'), got['FT_BOW_CHEST'])
        info = {str(r['__RowId']) for r in byml.loads(plain(build_mod.ACTOR_INFO, folder)).root}
        good &= check('  the map\'s big chest holds the three bomb bags as our three-level chest (%s -> %s), '
                      'written with its row' % BIG['FT_EAST_COURTYARD_CHEST'],
                      got['FT_EAST_COURTYARD_CHEST'] == BIG['FT_EAST_COURTYARD_CHEST']
                      + ('Item_BombBag_Small', 'Item_BombBag_Small', 'Item_BombBag_Medium')
                      and BIG['FT_EAST_COURTYARD_CHEST'][1] in info
                      and ground_items.pack_path(BIG['FT_EAST_COURTYARD_CHEST'][1]) + '.zs' in files,
                      got['FT_EAST_COURTYARD_CHEST'])
        pot, well, entrance = spot('FT_LOBBY_POT_01')[1], spot('FT_WELL_CHEST')[1], spot('FT_ENTRANCE_CHEST')[1]
        once = dungeon_keys.name(AREA, 'once', True)
        chest = dungeon_keys.name(AREA, 'chest', True)
        good &= check('  a key asked for with its name in its own temple is the named key: %s in a pot, %s in a '
                      'chest with the opening event that counts it' % (once, chest),
                      dyn(pot).get('Drop__DropActor') == once and dyn(well).get('Drop__DropActor') == chest
                      and str(dyn(well).get(build_mod.TBOX_EVENT_KEY, '')).startswith('NX2_TBoxKey_' + AREA)
                      and once in info and chest in info, (dyn(pot), dyn(well)))
        good &= check('  without +name too (decision 46): the named key with its opening event',
                      dyn(entrance).get('Drop__DropActor') == chest
                      and str(dyn(entrance).get(build_mod.TBOX_EVENT_KEY, '')).startswith('NX2_TBoxKey_' + AREA),
                      dyn(entrance))
        good &= check('  the map\'s chest made small loses ForesetTemple_GetMap (the big chest\'s opening), the Bow\'s '
                      'its ForestTemple_GetBow (as before)',
                      spot('FT_EAST_COURTYARD_CHEST')[0].get('Dynamic', {}).get('GetEventName') == 'ForesetTemple_GetMap'
                      and 'GetEventName' not in dyn(spot('FT_EAST_COURTYARD_CHEST')[1])
                      and 'GetEventName' not in dyn(spot('FT_BOW_CHEST')[1]))

        # ---- one item, and an item the cutscene cannot show
        fc = flow_of('rupee')
        ix = {e.name: k for k, e in enumerate(fc.events)}
        r = fc.events[ix[LOD_RUN[0]]].next
        good &= check('build "rupee": the cutscene gives the red rupee and shows the chest\'s red rupee '
                      '(TBox_Rupee_Red: the actor %s renamed, nothing else changed)' % MEDAL,
                      dict(fc.events[ix[gift['event']]].params).get('ActorName') == 'Obj_Rupee_Red'
                      and act(fc, r) == ('TBox_Rupee_Red', 'EventTriggerSetModelLodManual')
                      and len(fc.events) == len(game_fc.events) and len(fc.actors) == len(game_fc.actors))
        fc = flow_of('heart')
        ix = {e.name: k for k, e in enumerate(fc.events)}
        branch = fc.events[ix[GLITTER_FORK]].forks[game_fc.events[names[GLITTER_FORK]].forks.index(glit)]
        reach = set()
        for p in fc.entry_points:
            reach |= set(fc.reachable(p.main))
        good &= check('build "heart": the cutscene gives the Piece of Heart and nothing floats down (no step of %s '
                      'runs; the glitter branch starts at %s)' % (MEDAL, GLITTER_RUN[1]),
                      dict(fc.events[ix[gift['event']]].params).get('ActorName') == 'Obj_Heart_Piece'
                      and fc.events[ix[LOD_RUN[0]]].next is None and fc.events[branch].name == GLITTER_RUN[1]
                      and not any(act(fc, i) and act(fc, i)[0] == MEDAL for i in reach))

        # ---- every file has its size
        short = []
        for name, (_, folder, files) in builds.items():
            written = os.path.join(folder, build_mod.RESTBL_PATH)   # not written when every file still fits
            table = restbl.Restbl.read(zstd.decompress(open(written if os.path.exists(written) else os.path.join(
                romfs, build_mod.RESTBL_PATH), 'rb').read(), d))
            rest = build_mod.RESTBL_PATH.replace(os.sep, '/')
            for f in files:
                path = f[:-3] if f.endswith('.zs') else f
                if f != rest and (table.get(path) is None or table.get(path) < len(plain(path, folder))):
                    short.append((name, path))
        good &= check('every file of the three builds has an entry in the resource size table, at least its own '
                      'size', not short, short[:5])

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
