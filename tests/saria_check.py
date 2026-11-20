"""Cutscene gift test: what tools/build_mod.py makes of an item placed on Saria's gift (LW_SARIA_GIFT, the
cutscene Dm_Kokiri_0155), on the game's own file. Reads only; writes nothing.

    python tests/saria_check.py "C:\\...\\romfs"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import sizes  # noqa: E402
from formats import zstd, evfl  # noqa: E402
from logic.world import World  # noqa: E402

CID = 'LW_SARIA_GIFT'
ITEM = 'Item_Boomerang'                     # an item actor (Item_EventObject_Base): shown in Link's hand
PICKUP = 'Obj_Rupee_Blue'                   # an actor Link picks up by touching it: not put in his hand
WEAPON = 'Item_Range_SlingShot'             # comes with its small seed bag
# item actors the game's own cutscenes bind to a hand: (cutscene, actor)
GAME_BOUND = (('Dm_Goron_0030', 'Item_Gauntlet_Goron'), ('Dm_Kakariko_0010', 'Item_ZeldaLetter'),
              ('Npc_Goron_Biggoron_Adult', 'Item_Sword_Giant'))


def check(name, ok):
    print('%-78s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *a):
    try:
        f(*a)
    except SystemExit:
        return True
    return False


def state(fc):
    return ([dict(vars(a)) for a in fc.actors], [dict(vars(e)) for e in fc.events],
            [dict(vars(p)) for p in fc.entry_points])


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *(path + '.zs').split('/')), 'rb').read(), d)  # noqa: E731
    world = World()
    good = True

    planned = build_mod.plan_cutscene_gifts(world, [(CID, ITEM)])
    good &= check('the data: one cutscene, not a map placement, not a gift of the shared get flow',
                  len(planned) == 1 and not build_mod.plan(world, [(CID, ITEM)])
                  and not build_mod.plan_gifts(world, [(CID, ITEM)])
                  and not build_mod.plan_songs(world, [(CID, ITEM)]))
    (path, (cid, item, g)), = planned.items()
    old = plain(path)
    orig = evfl.loads(old)
    fc = orig.flowchart
    good &= check('the cutscene is read and written back byte for byte (no timeline in it)',
                  evfl.dumps(orig) == old and len(orig.flowcharts) == 1)

    # the game's file is what the data says
    by_name = {e.name: e for e in fc.events}
    add, win = by_name[g['add']], by_name[g['window']]
    held = [a for a in fc.actors if a.name == g['item']]
    binds = [e for e in fc.events if e.type == 'action' and fc.actors[e.actor].name == g['item']
             and build_mod._action_name(fc, e) == build_mod.CUTSCENE_BIND]
    good &= check('game file: %s adds one %s, %s is its get window' % (g['add'], g['item'], g['window']),
                  (fc.actors[add.actor].name, build_mod._action_name(fc, add)) == build_mod.CUTSCENE_ADD
                  and add.params['Actor'] == g['item'] and add.params['Num'] == 1
                  and (win.flowchart, win.entry) == build_mod.CUTSCENE_WINDOW
                  and win.params['ActorName'] == g['item'])
    good &= check('game file: one actor %s, made for the cutscene and bound to Link\'s hand' % g['item'],
                  len(held) == 1 and held[0].params['EventMemberCreateMethod'] == 1 and len(binds) == 1
                  and binds[0].params['ActorName'] == 'Player_Event' and binds[0].params['BoneName'] == 'Weapon_L')
    # the game binds other item actors of the same kind the same way
    same = True
    for flow, actor in GAME_BOUND:
        f2 = evfl.loads(plain('Event/EventFlow/%s.bfevfl' % flow)).flowchart
        a2 = [a for a in f2.actors if a.name == actor]
        same &= len(a2) == 1 and build_mod.CUTSCENE_BIND in a2[0].actions \
            and a2[0].params['EventMemberCreateMethod'] == 1 \
            and ground_items.kind_of(plain, actor) == build_mod.CUTSCENE_SHOWN_KIND
    good &= check('game: its cutscenes bind item actors of the same kind as %s (%s)'
                  % (ITEM, ', '.join(a for _, a in GAME_BOUND)),
                  same and ground_items.kind_of(plain, ITEM) == build_mod.CUTSCENE_SHOWN_KIND
                  and ground_items.kind_of(plain, PICKUP) != build_mod.CUTSCENE_SHOWN_KIND)

    def edited(item, show, companions=()):
        ef = evfl.loads(old)
        said, added = build_mod.cutscene_gift_edit(ef.flowchart, CID, g, item, show, companions)
        new = build_mod.flow_write_checked(ef)
        back = evfl.loads(new)
        build_mod.cutscene_gift_check(evfl.loads(old).flowchart, back.flowchart, CID, g, item, show, added)
        return new, back.flowchart, added

    def only_differs(back, item, shown, extra=0):
        """against the game's file: the add's item, the window's item, the held actor's name; nothing else"""
        a0, e0, p0 = state(fc)
        a1, e1, p1 = state(back)
        diff = []
        for x, y in zip(a0, a1):
            diff += [('actor', x['name'], k, y[k]) for k in x if x[k] != y[k]]
        for x, y in zip(e0, e1[:len(e0)]):
            for k in x:
                if k == 'params' and isinstance(x[k], dict) and isinstance(y[k], dict):
                    diff += [('event', x['name'], pk, y[k].get(pk)) for pk in x[k] if x[k][pk] != y[k].get(pk)]
                    diff += [('event', x['name'], pk, 'new') for pk in y[k] if pk not in x[k]]
                elif x[k] != y[k]:
                    diff.append(('event', x['name'], k, y[k]))
        want = [('event', g['add'], 'Actor', item), ('event', g['window'], 'ActorName', item)]
        if shown != g['item']:
            want.append(('actor', g['item'], 'name', shown))
        if extra:
            want.append(('event', g['add'], 'next', len(e0)))
        return sorted(diff, key=str) == sorted(want, key=str) and p0 == p1 \
            and len(a0) == len(a1) and len(e1) == len(e0) + extra

    # the Boomerang: given, named and shown
    new, back, added = edited(ITEM, True)
    b = {e.name: e for e in back.events}
    good &= check('%s: %s adds it, %s names it, Link holds it; nothing else differs' % (ITEM, g['add'], g['window']),
                  b[g['add']].params['Actor'] == ITEM and b[g['window']].params['ActorName'] == ITEM
                  and [a.name for a in back.actors].count(ITEM) == 1 and not added
                  and not any(a.name == g['item'] for a in back.actors) and only_differs(back, ITEM, ITEM))
    hold = [e for e in back.events if e.type == 'action' and back.actors[e.actor].name == ITEM]
    good &= check('%s: the held actor keeps its three steps (join the cutscene, bind to the hand, leave)' % ITEM,
                  sorted(build_mod._action_name(back, e) for e in hold)
                  == ['EventGoOffstageForUser', 'EventTriggerModelBind', 'EventTriggerParticipateEvent'])
    good &= check('%s: the written file reads back and writes the same again' % ITEM,
                  evfl.dumps(evfl.loads(new)) == new)
    # its size entry
    out = build_mod.Output(romfs, None, d)
    was = out.table.get(path)
    out.size(path, old, new)
    now = out.table.get(path)
    good &= check('size entry: %d bytes -> entry %d (rule %d, the game\'s %d for %d bytes)'
                  % (len(new), now, sizes.rule(path, new), was, len(old)),
                  now >= sizes.rule(path, new) and now >= was and was == sizes.rule(path, old))

    # the ocarina placed on its own check: the game's file
    new0, back0, _ = edited(g['item'], True)
    good &= check('%s placed here: the game\'s file byte for byte' % g['item'], new0 == old)

    # a pickup: given and named, the cutscene's own actor stays in Link's hand
    _, back, added = edited(PICKUP, False)
    b = {e.name: e for e in back.events}
    good &= check('%s (picked up by touch): given and named, Link still holds %s' % (PICKUP, g['item']),
                  b[g['add']].params['Actor'] == PICKUP and b[g['window']].params['ActorName'] == PICKUP
                  and not any(a.name == PICKUP for a in back.actors) and only_differs(back, PICKUP, g['item']))

    # a weapon that needs its bag: the bag is added right after it
    comp = build_mod.SCRUB_COMPANIONS[WEAPON]
    _, back, added = edited(WEAPON, True, comp)
    b = {e.name: e for e in back.events}
    nxt = back.events[b[g['add']].next]
    good &= check('%s: %s is added right after it, silently' % (WEAPON, comp[0]),
                  len(added) == 1 and nxt.name == added[0] and nxt.next == by_name[g['add']].next
                  and nxt.params['Actor'] == comp[0] and nxt.params['Num'] == 1
                  and nxt.params['IsSetMessageTargetActorName'] is False
                  and back.actors[nxt.actor].name == 'PouchSystemActor' and only_differs(back, WEAPON, WEAPON, 1))

    # refused: data that is not what the file has; a progressive pair on the gift
    wrong = [dict(g, item='Item_Ocarina_Time'), dict(g, add=g['window']), dict(g, window='Event0'),
             dict(g, add='EventNone')]
    good &= check('refused: data that does not match the cutscene (item, add step, window)',
                  all(refused(build_mod.cutscene_gift_edit, evfl.loads(old).flowchart, CID, w, ITEM, True)
                      for w in wrong))
    good &= check('refused: a progressive pair on the gift', refused(build_mod.pair_kind, world, CID))
    tampered = evfl.loads(new)
    tampered.flowchart.events[0].next = 1
    good &= check('the read-back check notices a change elsewhere in the cutscene',
                  refused(build_mod.cutscene_gift_check, fc, tampered.flowchart, CID, g, ITEM, True))

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
