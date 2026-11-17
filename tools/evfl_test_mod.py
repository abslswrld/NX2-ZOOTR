"""Build the small test mod that tells whether event flow (.bfevfl) edits work in game.

    python tools/evfl_test_mod.py --romfs "<romfs>" --out out\\mods-evfl-test --longshot "<Longshot folder>"

One event flow is edited, `Event/EventFlow/Npc_Kokiri_001_Shop_Child.bfevfl` (the child Kokiri shopkeeper's
talk), in two independent ways:

  1. GREETING (the fix under test). The flow's one switch on `Meet_DekuTree_IsAfter_Step02_Exp` has two
     cases. In this game's flows a yes/no question answers 0 for YES and 1 for NO (see CHANGELOG, 2026-11-17,
     "Why event flow edits showed nothing"), so case 0 is the "after" side and case 1 the "low on stock"
     side. Both cases now go to where the "after" side ends up (the step that picks the normal greeting),
     skipping only the "you lost your Deku Shield" hand-out that sits in between.
  2. GOODBYE (the control, needs no understanding of yes/no). The three goodbye lines ("Come agaaain!",
     "Please come back sooon!", "Until next tiiiime!") are replaced by the shop's "not enough rupees" line.

Also in the mod: the skippable opening (a BYML edit already seen to work), only to get to the shop faster.

Output: <out>/NX2-ZOOTR-evfl-test/romfs/..., and with --longshot a launcher "Launch evfl test.bat" next to
<out>, using the same test save folder as the main launcher (<out>/../user). `out/` is ignored by git.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import build_mod  # noqa: E402
from formats import zstd, evfl  # noqa: E402

FLOW = 'Event/EventFlow/Npc_Kokiri_001_Shop_Child.bfevfl'
FLAG = 'Meet_DekuTree_IsAfter_Step02_Exp'
MSG = 'EventFlowMsg/Npc_Kokiri_001_Shop_Child:'
GOODBYES = (MSG + 'Talk_0002', MSG + 'Talk_0007', MSG + 'Talk_0008')
MARKER = MSG + 'Shop_02'            # "You don't have enough rupees. Sorry, but I don't haggle."
ARRIVAL = 'Npc_Kokiri_001_Shop_Child_Talk_Arrival'
YES, NO = 0, 1                      # what a yes/no query answers in this game's flows


def links(e):
    return [x for x in [e.next, e.join] + [ev for _, ev in e.cases] + list(e.forks) if x is not None]


def reachable(fc, start):
    seen, todo = [], [start]
    while todo:
        i = todo.pop(0)
        if i not in seen:
            seen.append(i)
            todo += links(fc.events[i])
    return seen


def edit(data):
    """returns (new file, lines saying what was changed)"""
    ef = evfl.loads(data)
    fc = ef.flowchart
    said = []

    # 1. greeting
    hits = [i for i, e in enumerate(fc.events)
            if e.type == 'switch' and isinstance(e.params, dict) and e.params.get('GameDataName') == FLAG]
    if len(hits) != 1:
        raise SystemExit('%d switches on %s, expected 1' % (len(hits), FLAG))
    sw = fc.events[hits[0]]
    cases = dict(sw.cases)
    if sorted(cases) != [YES, NO]:
        raise SystemExit('switch on %s: cases %r not as expected' % (FLAG, sw.cases))
    hand_out = fc.events[cases[YES]]              # the "lost your Deku Shield?" call; both its results...
    if hand_out.type != 'callswitch' or hand_out.entry != 'present_DekuSheld':
        raise SystemExit('the "after" side is not the Deku Shield hand-out: %r' % vars(hand_out))
    greet = [ev for _, ev in hand_out.cases       # ...lead to the normal greeting; take the direct one
             if fc.events[ev].type == 'switch' and (fc.events[ev].params or {}).get('GameDataName') == ARRIVAL]
    if len(greet) != 1:
        raise SystemExit('normal greeting not found after the hand-out: %r' % hand_out.cases)
    sw.cases = [(YES, greet[0]), (NO, greet[0])]
    said.append('greeting: switch %s (%s) cases %r -> %r' % (sw.name, FLAG, sorted(cases.items()), sw.cases))

    # the entry points list the subflow / callswitch steps that can run from them: drop those no longer reached
    for ep in fc.entry_points:
        can = reachable(fc, ep.main)
        keep = [i for i in ep.subflows if i in can]
        if keep != ep.subflows:
            said.append('entry point %s: list %r -> %r' % (ep.name, ep.subflows, keep))
            ep.subflows = keep

    # 2. goodbye
    n = 0
    for e in fc.events:
        if e.type == 'action' and isinstance(e.params, dict) and e.params.get('MessageId') in GOODBYES:
            said.append('goodbye: %s says %s instead of %s' % (e.name, MARKER, e.params['MessageId']))
            e.params['MessageId'] = MARKER
            n += 1
    if n != 3:
        raise SystemExit('%d goodbye lines found, expected 3' % n)

    new = evfl.dumps(ef)
    # read back: the same flow as intended
    back = evfl.loads(new).flowchart
    if [vars(e) for e in back.events] != [vars(e) for e in fc.events] \
            or [vars(p) for p in back.entry_points] != [vars(p) for p in fc.entry_points] \
            or [vars(a) for a in back.actors] != [vars(a) for a in fc.actors]:
        raise SystemExit('read-back differs from what was intended')
    return new, said


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--romfs', required=True)
    ap.add_argument('--out', required=True, help='mods folder for this test only (not out\\mods)')
    ap.add_argument('--name', default='NX2-ZOOTR-evfl-test')
    ap.add_argument('--longshot', help='Longshot folder: also write "Launch evfl test.bat" next to --out')
    a = ap.parse_args(argv)
    mods = os.path.abspath(a.out)
    if os.path.basename(mods).lower() == 'mods':
        raise SystemExit('--out must not be the main mods folder')
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(a.romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    out = build_mod.Output(a.romfs, os.path.join(mods, a.name, 'romfs'), dicts)

    src, old = out.read(FLOW)
    if evfl.dumps(evfl.loads(old)) != old:
        raise SystemExit('%s does not round-trip byte for byte' % FLOW)
    new, said = edit(old)
    out.write(FLOW, src, old, new)
    for line in said:
        print(line)

    path, keys, expected = build_mod.FILE_FIXES['skippable_opening']
    src, old = out.read(path)
    out.write(path, src, old, build_mod.remove_entry(old, keys, expected))
    print('skippable opening: %s' % path)

    out.finish()
    print('mod folder:', os.path.join(mods, a.name))
    if a.longshot:
        bat = os.path.join(os.path.dirname(mods), 'Launch evfl test.bat')
        user = os.path.join(os.path.dirname(mods), 'user')
        with open(bat, 'w', encoding='ascii', newline='\r\n') as f:
            f.write(build_mod.LAUNCHER.replace('NX2-ZOOTR test launcher (made by tools/build_mod.py)',
                                               'NX2-ZOOTR event flow test launcher (made by tools/evfl_test_mod.py)') % {'longshot': os.path.abspath(a.longshot), 'mods': mods, 'user': user})
        print('launcher:', bat)


if __name__ == '__main__':
    main(sys.argv[1:])
