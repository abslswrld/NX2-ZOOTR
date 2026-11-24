"""Forest Temple items test: items on the temple's chests, pots and Gold Skulltulas, and the Bow room's door
(tools/build_mod.py; phase 1, part 3).

Read from the game's own files: how the temple's pots and chests name what they give (a drop table, nothing,
an item), the opening events of its chests, and how the Bow room's logic module locks its west shutter. Then
the changes: the Bow room's shutter lock (--fix forest_temple_bow_room_door, decision 39) read back against
the game's file, a pot or a chest of each form given an item, what is refused, and a whole build of the test
sample read back from the mod folder. Only reads the game; the build goes to a temporary folder that is
removed again.

    python tests/forest_temple_items_check.py "C:\\...\\romfs"
"""
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
import once_items  # noqa: E402
from formats import zstd, byml, ainb  # noqa: E402
from logic.world import World  # noqa: E402

AREA = 'ForestTemple'
MAPS = ('Banc/ForestTemple/ForestTemple_Static.bcett.byml', 'Banc/ForestTemple/ForestTemple_Dynamic.bcett.byml')
FIX = 'forest_temple_bow_room_door'
FIRST_STALFOS_ROOM = 'Logic/ForestTemple_Level_Room_06_Prefab_61dc.logic.module.ainb'
# the test build of part 3 (out/TEST_CHECKLIST.md): check -> item. The keys stay where the game puts them
SAMPLE = [
    ('FT_ENTRANCE_GS', 'Item_HeavyBoot'),                 # a Gold Skulltula
    ('FT_LOBBY_POT_01', 'Item_Hammer'),                   # a pot that names a drop table
    ('FT_LOBBY_POT_02', 'Item_HoverBoot'),                # a pot that names nothing
    ('FT_LOBBY_GS', 'Obj_Heart_Piece'),                   # a Gold Skulltula, an item that is a ground actor
    ('FT_FIRST_STALFOS_ROOM_POT_01', 'Item_GlassTruth'),  # a pot of the other map file
    ('FT_EAST_COURTYARD_CHEST', 'Item_Range_Bow'),        # the big chest of the map: the Bow moves here
    ('FT_BLOCK_ROOM_POT_01', 'Item_Shield_Mirror'),
    ('FT_BLOCK_ROOM_EYE_SWITCH_CHEST', 'Item_Arrow_Fire'),   # a small chest that appears
    ('FT_BOW_CHEST', 'Item_Arrow_Ice'),                   # the Bow's big chest: its Navi message goes
    ('FT_BOW_ROOM_POT_01', 'Item_DinFire'),               # the pot the arrow pot stands in
    ('FT_BOW_ROOM_POT_03', 'Item_FaroreWind'),
]
# the temple's chests that are not for this part: the builder takes the five key chests like any chest, and
# refuses the boss key's (its opening event has no decision yet: part 7)
KEY_CHESTS = ('FT_ENTRANCE_CHEST', 'FT_FIRST_STALFOS_ROOM_CHEST', 'FT_WELL_CHEST', 'FT_FLOORMASTER_CHEST',
              'FT_JOELLE_CHEST')
CHEST_EVENTS = {'FT_BOW_CHEST': ('ForestTemple_GetBow', 'remove'),
                'FT_EAST_COURTYARD_CHEST': ('ForesetTemple_GetMap', 'keep'),
                'FT_BETH_CHEST': ('ForesetTemple_GetCompass', 'keep')}


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def refused(fn, *args, **kw):
    try:
        fn(*args, **kw)
    except SystemExit as e:
        return str(e)
    return None


def tree(folder):
    return sorted(os.path.relpath(f, folder).replace(os.sep, '/')
                  for f in glob.glob(os.path.join(folder, '**', '*'), recursive=True) if os.path.isfile(f))


def shape(doc):
    """every node of a logic file as plain values, to compare two files node by node"""
    out = []
    for n in doc.nodes:
        out.append((n.name, n.type, n.flags, list(n.preconditions),
                    [(t, x.name, x.value, x.node, x.param, x.flags, x.sources)
                     for t in ainb.PARAM_TYPES for x in n.inputs[t]],
                    [(t, x.name, x.value) for t in ainb.PARAM_TYPES for x in n.immediates[t]],
                    [(t, x.name) for t in ainb.PARAM_TYPES for x in n.outputs[t]],
                    [[(l.node, l.name, l.extra) for l in kind] for kind in n.links]))
    return out


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)   # noqa: E731
    loose = lambda path: open(os.path.join(romfs, *path.split('/')), 'rb').read()   # noqa: E731
    w = World()
    good = True
    locs = {l['id']: (r, name, l) for r in w.regions.values() if r.scene == AREA
            for name, l in r.locations.items() if l.get('id')}
    spots = w.checks[AREA]
    maps = {m: plain(m) for m in MAPS}
    actors = {str(int(a['Hash'])): (m, a) for m in MAPS for a in byml.loads(maps[m]).root['Actors']}

    def place(cid):
        """(map file, placement hash, the actor as the game has it) of a check with one placement"""
        p, = spots[locs[cid][2]['spot']]['placements']
        return actors[p['hash']][0], p['hash'], actors[p['hash']][1]

    def dyn(actor):
        return dict(actor.get('Dynamic') or {})

    # ---- the game's files: how the temple's pots and chests name what they give
    pots = sorted(cid for cid, (_, _, l) in locs.items() if spots.get(l.get('spot'), {}).get('kind') == 'pot')
    forms = {'table': [], 'nothing': [], 'item': []}
    for cid in pots:
        dy = dyn(place(cid)[2])
        forms['item' if 'Drop__DropActor' in dy else 'table' if build_mod.POT_TABLE_KEY in dy else 'nothing'].append(cid)
    good &= check('the temple\'s 28 pots: 21 name a drop table, 7 name nothing, none names an item',
                  (len(forms['table']), len(forms['nothing']), len(forms['item'])) == (21, 7, 0),
                  {k: len(v) for k, v in forms.items()})
    flags = build_mod.placement_flags(plain(build_mod.GAME_DATA))
    two = [cid for cid in pots if flags.get(place(cid)[1]) == once_items.FLAG_RESET
           and flags.get(str(int(place(cid)[1]) ^ 2)) == build_mod.FLAG_KEPT]
    good &= check('  every one has the two saved flags a one-time drop needs (its own, reset; and the kept one)',
                  two == pots, sorted(set(pots) - set(two)))
    chests = sorted(cid for cid, (_, _, l) in locs.items() if spots.get(l.get('spot'), {}).get('kind') == 'chest')
    bare = [cid for cid in chests if 'Drop__DropActor' not in dyn(place(cid)[2])]
    good &= check('the temple\'s 12 chests: one names no item (the falling ceiling room\'s, an ordinary small chest)',
                  len(chests) == 12 and bare == ['FT_FALLING_CEILING_ROOM_CHEST']
                  and place(bare[0])[2]['Gyaml'] in build_mod.CHECKING_CHEST, bare)
    events = {cid: dyn(place(cid)[2]).get(build_mod.TBOX_EVENT_KEY) for cid in chests}
    good &= check('  four have an opening event of their own: the Bow\'s, the map\'s, the compass\'s (each with a '
                  'decision in CHEST_EVENTS) and the boss key\'s (none yet: part 7)',
                  {c: e for c, e in events.items() if e} == dict(
                      {c: e for c, (e, _) in CHEST_EVENTS.items()}, FT_BOSS_KEY_CHEST='ForesetTemple_GetBossKey')
                  and all(build_mod.CHEST_EVENTS[e][0] == what for e, what in CHEST_EVENTS.values())
                  and 'ForesetTemple_GetBossKey' not in build_mod.CHEST_EVENTS)

    # ---- one pot or chest of each form given an item
    def patched(cid, item, kind):
        path, h, _ = place(cid)
        new, found, _ = build_mod.patch_file(maps[path], {h: (cid, item, None, kind)})
        back = {str(int(a['Hash'])): a for a in byml.loads(new).root['Actors']}
        others = all(a == actors[k][1] for k, a in back.items() if k != h and actors[k][0] == path)
        return back[h], found[h], others and len(back) == sum(1 for m, _ in actors.values() if m == path)

    def as_intended(cid, item, kind, gone=()):
        got, found, others = patched(cid, item, kind)
        want = dict(dyn(place(cid)[2]), Drop__DropActor=item)
        for k in gone:
            want.pop(k)
        return dict(got.get('Dynamic') or {}) == want and got['Gyaml'] == place(cid)[2]['Gyaml'] and others \
            and found == dyn(place(cid)[2]).get('Drop__DropActor')

    good &= check('a pot that names a drop table: it names the item, the table is gone, nothing else changes',
                  all(as_intended(cid, 'Obj_NX2O_Test', 'pot', gone=[build_mod.POT_TABLE_KEY])
                      for cid in forms['table']))
    good &= check('a pot that names nothing: it names the item, nothing else changes',
                  all(as_intended(cid, 'Obj_NX2O_Test', 'pot') for cid in forms['nothing']))
    good &= check('the chest that names no item: it names the item, nothing else changes',
                  as_intended(bare[0], 'Item_Hammer', 'chest'))
    good &= check('the Bow\'s chest with another item: its opening event (Navi\'s message about the Bow) is '
                  'removed; with the Bow itself it stays',
                  as_intended('FT_BOW_CHEST', 'Item_Hammer', 'chest', gone=[build_mod.TBOX_EVENT_KEY])
                  and as_intended('FT_BOW_CHEST', 'Item_Range_Bow', 'chest'))
    good &= check('the map\'s and the compass\'s chest with another item: the opening event stays (it is only '
                  'the usual opening)',
                  as_intended('FT_EAST_COURTYARD_CHEST', 'Item_Hammer', 'chest')
                  and as_intended('FT_BETH_CHEST', 'Item_Hammer', 'chest'))
    said = refused(patched, 'FT_BOSS_KEY_CHEST', 'Item_Hammer', 'chest')
    good &= check('the boss key\'s chest with another item is refused (its opening event has no decision yet)',
                  bool(said) and 'ForesetTemple_GetBossKey' in said and 'CHEST_EVENTS' in said, said)
    good &= check('the five small key chests are ordinary chests (an item of their own, no opening event)',
                  all(dyn(place(cid)[2]).get('Drop__DropActor') == 'Item_Dungeon_SmallKey'
                      and not events[cid] for cid in KEY_CHESTS))

    # ---- the Bow room's door
    game = loose(build_mod.BOW_ROOM_LOGIC)
    doc = ainb.Ainb.read(game)
    lock, appeared, true = build_mod.bow_room_parts(doc)
    src = doc.nodes[lock].inputs['bool'][0].sources
    names = lambda i: [o.name for o in doc.nodes[i].outputs['bool']]   # noqa: E731
    focus = doc.nodes[src[1][0]]
    play = next(x for x in focus.inputs['bool'] if x.name == 'play')
    wait = doc.nodes[play.node].inputs['bool'][0].sources or []
    good &= check('the game: the Bow room\'s west shutter is locked until the flag %s is set, or its "focus" '
                  'event has played' % build_mod.BOW_ROOM_OPEN_FLAG,
                  build_mod._flag_of(doc.nodes[src[0][0]]) == build_mod.BOW_ROOM_OPEN_FLAG
                  and focus.name.startswith('Gimmick_FocusOnGimmick') and len(src) == 2)
    good &= check('  that event plays when the eye switch is on AND the chest has appeared (so: an arrow)',
                  doc.nodes[play.node].name == 'OperateAND' and names(play.node)[play.param] == 'True'
                  and len(wait) == 2
                  and doc.nodes[wait[0][0]].name == 'ActorLogicBootUpActorIsFirstOnEventTrigger'
                  and names(wait[0][0])[wait[0][1]] == 'OnState' and wait[1][:2] == (appeared, true))
    new, said = build_mod.bow_room_door(game)
    after = ainb.Ainb.read(new)
    a, b = shape(doc), shape(after)
    differ = [i for i in range(len(a)) if a[i] != b[i]]
    got = after.nodes[lock]
    good &= check('the fix: the lock\'s second source is "the chest has appeared"; only that node differs '
                  '(%d of %d), the file is as long as before' % (len(differ), len(a)),
                  len(a) == len(b) and differ == [lock] and len(new) == len(game)
                  and got.inputs['bool'][0].sources == [src[0], (appeared, true, src[1][2])]
                  and got.links[0][0].node == appeared and sorted(got.preconditions) == sorted([src[0][0], appeared])
                  and after.write() == new, differ)
    good &= check('  the eye switch and its event are as before (shooting it still sets its flag)',
                  a[play.node] == b[play.node] and a[src[1][0]] == b[src[1][0]] and a[wait[0][0]] == b[wait[0][0]])
    good &= check('  a file that already has the fix is refused', bool(refused(build_mod.bow_room_door, new)))
    first = ainb.Ainb.read(loose(FIRST_STALFOS_ROOM))
    shutter, = [n for n in first.nodes if n.name.startswith('DungeonSwitchShutterWithLockSet')]
    flock = next(x for x in shutter.inputs['bool'] if x.name == 'LockMinusZ')
    fsrc = first.nodes[flock.node].inputs['bool'][0].sources or []
    good &= check('the game\'s own model: the first Stalfos room unlocks its shutter with "its chest\'s event, '
                  'or its flag" (no switch)',
                  first.nodes[flock.node].name == 'OperateORFixInputTrue' and len(fsrc) == 2
                  and first.nodes[fsrc[0][0]].name.startswith('Gimmick_TreasureBoxAppear')
                  and build_mod._flag_of(first.nodes[fsrc[1][0]]) == 'Gimmick_DefeatEnemy_Open_ForestTemple_01')
    rule = w.regions['FT Bow Room'].exits['FT Joelle Room'][0]
    good &= check('the logic: the setting %s is on by default, and the way out of the Bow room asks for it or '
                  'the Bow' % FIX,
                  w.settings_defaults.get(FIX) is True and rule == '%s or can_use(Bow)' % FIX, rule)

    # ---- a whole build: the test sample
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        said = refused(run, 'no', 'FT_BOSS_KEY_CHEST=Item_Hammer')
        good &= check('a build with the boss key\'s chest changed is refused and nothing is written',
                      bool(said) and 'CHEST_EVENTS' in said and not os.path.isdir(os.path.join(tmp, 'no', 'romfs', 'Banc')),
                      said)
        said, folder = run('ft', '--fix', FIX, *['%s=%s' % x for x in SAMPLE])
        files = tree(folder)
        read = lambda f: open(os.path.join(folder, *f.split('/')), 'rb').read()   # noqa: E731
        good &= check('the sample builds: %d placements and the door fix (%d files)' % (len(SAMPLE), len(files)),
                      all(m + '.zs' in files for m in MAPS) and build_mod.BOW_ROOM_LOGIC in files
                      and 'Pack/Actor/Obj_Pot_A_02.pack.zs' in files, files)
        good &= check('  the Bow room\'s logic file in the mod folder is the fixed one, stored as the game '
                      'stores it (not compressed)', build_mod.BOW_ROOM_LOGIC in files
                      and read(build_mod.BOW_ROOM_LOGIC) == new)
        back = {str(int(a['Hash'])): a for m in MAPS if m + '.zs' in files
                for a in byml.loads(zstd.decompress(read(m + '.zs'), d)).root['Actors']}
        held, changed = {}, set()
        for cid, item in SAMPLE:
            _, h, _ = place(cid)
            changed.add(h)
            held[cid] = dyn(back.get(h, {})).get('Drop__DropActor')
        kinds = {cid: spots[locs[cid][2]['spot']]['kind'] for cid, _ in SAMPLE}
        good &= check('  read back from the mod folder: each chest holds its item; each pot drops its one-time '
                      'version (Obj_NX2O_...) and each Gold Skulltula its token version (Obj_NX2_GS_...)',
                      all(held[cid] == item for cid, item in SAMPLE if kinds[cid] == 'chest')
                      and all((held[cid] or '').startswith('Obj_NX2') for cid, _ in SAMPLE if kinds[cid] != 'chest')
                      and len(set(held.values())) == len(SAMPLE), held)
        good &= check('  no pot of the sample still names a drop table; every other object of both maps is as '
                      'the game has it (%d objects)' % len(back),
                      len(back) == len(actors)
                      and not any(build_mod.POT_TABLE_KEY in dyn(back[place(cid)[1]]) for cid, _ in SAMPLE)
                      and all(back[h] == actors[h][1] for h in back if h not in changed))
        good &= check('  the five small key chests and the boss key\'s chest still hold their keys',
                      all(dyn(back[place(cid)[1]]).get('Drop__DropActor') == 'Item_Dungeon_SmallKey'
                          for cid in KEY_CHESTS)
                      and dyn(back[place('FT_BOSS_KEY_CHEST')[1]]).get('Drop__DropActor') == 'Item_Dungeon_BossKey')
        good &= check('  the build says what it did: the door fix, the Bow\'s opening event removed, the pots\' '
                      'drop tables removed',
                      'fix %s' % FIX in said and 'special opening event ForestTemple_GetBow removed' in said
                      and said.count('drop table') >= 3, said[:300])
        _, plain_folder = run('nofix', *['%s=%s' % x for x in SAMPLE])
        good &= check('  without --fix %s the logic file is not written' % FIX,
                      build_mod.BOW_ROOM_LOGIC not in tree(plain_folder))

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
