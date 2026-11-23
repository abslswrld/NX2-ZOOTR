"""Upgrade families on a song check and on a cutscene gift: what tools/build_mod.py makes of CHECK_ID=First>Second
[>Third] on Saria's song (the song cutscene Dm_MelodyGet_Saria: song_skip) and on Saria's gift on the bridge (the
cutscene Dm_Kokiri_0155: cutscene_family_edit), for every family (FAMILIES), on the game's own files. The game's
inventory question (the Deku Theater's, as gifts with a family ask it) goes in front of one get per level; for
every number of levels Link may own the cutscene must give the next one, with what the first level needs
(the seed bag, the quiver) and an ocarina's sync steps. Then whole builds. Only reads the game; the whole builds
it runs go to a temporary folder that is removed again.

    python tests/event_families_check.py "C:\\...\\romfs"
"""
import contextlib
import copy
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
from formats import zstd, evfl, byml  # noqa: E402
from logic.world import World  # noqa: E402

SONG = 'Song from Saria'
GIFT = 'LW_SARIA_GIFT'
FAMILIES = build_mod.FAMILIES


def check(name, ok):
    print('%-110s %s' % (name, 'OK' if ok else 'FAILED'))
    return bool(ok)


def refused(f, *args, **kw):
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            f(*args, **kw)
    except SystemExit as e:
        return bool(e.code)
    return False


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path):
        return zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)

    world = World()
    known = {r['__RowId']: r.get('ActorName') for r in byml.loads(plain(ground_items.table_path('ActorInfo'))).root}
    asked = lambda item: known.get(item) or item   # noqa: E731
    deals = {r['__RowId']: r.get('PouchSpecialDeal')
             for r in byml.loads(plain(ground_items.table_path('PouchActorInfo'))).root}
    sync_steps = build_mod.sync_template(evfl.loads(plain(build_mod.SYNC_FLOW)).flowchart)
    template = build_mod.gift_pair_template(evfl.loads(plain(build_mod.GIFT_PAIR_FLOW)).flowchart)
    good = True

    # ------------------------------------------------------------------------------------- where
    print('Where a family goes')
    good &= check('Saria\'s song is a song check, her bridge gift a cutscene gift: neither is a gift of the shared '
                  'get flow nor a map placement',
                  build_mod.song_pair_kind(world, SONG) and not build_mod.cutscene_pair_kind(world, SONG)
                  and build_mod.cutscene_pair_kind(world, GIFT) and not build_mod.song_pair_kind(world, GIFT)
                  and build_mod.gift_pair_kind(world, SONG) is False and build_mod.gift_pair_kind(world, GIFT) is False
                  and not build_mod.song_pair_kind(world, 'KF_MIDO_CHEST_01'))

    def simulate(fc, start, levels, give):
        """[(levels owned, the level the events reached give)] for every number of levels Link may own"""
        out = []
        for r in range(len(levels) + 1):
            i = build_mod.level_reached(fc, start, {asked(x) for x in levels[:r]}, template)
            out.append((r, give(fc.events[i])))
        return out

    def wanted(levels):
        return [(r, levels[min(r, len(levels) - 1)]) for r in range(len(levels) + 1)]

    # ------------------------------------------------------------------------------------- the song
    print('Saria\'s song (%s)' % SONG)
    song_path, (cid, _, song) = next(iter(build_mod.plan_songs(world, [(SONG, 'Item_Scale_Silver')]).items()))
    song_old = plain(song_path)
    ok_order, ok_back, ok_after, ok_names = True, True, True, True
    for name, levels in FAMILIES.items():
        ef = evfl.loads(song_old)
        sync = {x: sync_steps for x in levels if deals.get(x) == build_mod.SYNC_DEAL}
        build_mod.song_skip(ef.flowchart, SONG, levels[0], song, sync, levels, template, asked)
        new = build_mod.flow_write_checked(ef)
        back, orig = evfl.loads(new).flowchart, evfl.loads(song_old).flowchart
        try:
            build_mod.song_skip_check(orig, back, SONG, levels, sync, template, asked)
        except SystemExit as e:
            ok_back = False
            print('  read-back refused', name, e)
        ep = next(p for p in back.entry_points if p.name == 'EntryPoint0')
        got = simulate(back, back.events[ep.main].next, levels,
                       lambda e: e.params.get('ActorName') if e.type == 'subflow'
                       and (e.flowchart, e.entry) == build_mod.SONG_GET else None)
        ok_order &= got == wanted(levels)
        # what follows each get: the first level's companions, an ocarina's sync, then the end
        for r, level in wanted(levels):
            i = back.events[build_mod.level_reached(back, back.events[ep.main].next,
                                                    {asked(x) for x in levels[:r]}, template)].next
            seen = []
            while i is not None:
                e = back.events[i]
                seen.append((back.actors[e.actor].name, back.actors[e.actor].actions[e.action],
                             e.params.get('Actor') if isinstance(e.params, dict) else None))
                i = e.next
            want = [('PouchSystemActor', 'EventTriggerAddOrRemovePouchContent', c)
                    for c in (build_mod.SCRUB_COMPANIONS.get(level, []) if level == levels[0] else [])]
            want += [(a.name, act, (p or {}).get('Actor') if isinstance(p, dict) else None)
                     for a, act, p in (sync.get(level) or [])]
            ok_after &= seen == want
        # the questions ask for the names the inventory knows the levels by
        qs = [e for e in back.events[len(orig.events):] if e.type == 'switch']
        ok_names &= sorted(e.params['Actor'] for e in qs) == sorted(asked(x) for x in levels[:-1])
    good &= check('every family (%d) on the song: for every number of levels owned, the next level (all owned: '
                  'the last again)' % len(FAMILIES), ok_order)
    good &= check('  each level\'s get leads on to the first level\'s seed bag or quiver, an ocarina\'s sync steps, '
                  'then the end', ok_after)
    good &= check('  the questions ask for the names the inventory knows the levels by (Weapon_Range_SlingShot...)',
                  ok_names)
    good &= check('  the read-back (song_skip_check) passes for every family, and for a plain item and a plain '
                  'Fairy Slingshot (before 2026-11-23 the slingshot alone stopped the build)',
                  ok_back and not refused(lambda: _plain_song(song_old, song, build_mod, template, asked)))
    # read-back against tampering: a question's answers swapped, the end changed
    ef = evfl.loads(song_old)
    levels = FAMILIES['Scale'] if 'Scale' in FAMILIES else next(f for f in FAMILIES.values() if len(f) == 2)
    build_mod.song_skip(ef.flowchart, SONG, levels[0], song, {}, levels, template, asked)
    good_fc = evfl.loads(build_mod.flow_write_checked(ef)).flowchart
    swapped = copy.deepcopy(good_fc)
    q = next(e for e in swapped.events[len(evfl.loads(song_old).flowchart.events):] if e.type == 'switch')
    q.cases = [(v, c) for (v, _), (_, c) in zip(q.cases, reversed(q.cases))]
    good &= check('  the read-back refuses a question whose answers are swapped',
                  refused(build_mod.song_skip_check, evfl.loads(song_old).flowchart, swapped, SONG, levels, {},
                          template, asked))
    good &= check('  a family on a song without the question refused; a later level that needs another item with it '
                  'refused',
                  refused(build_mod.song_skip, evfl.loads(song_old).flowchart, SONG, levels[0], song, {}, levels)
                  and refused(build_mod.song_skip, evfl.loads(song_old).flowchart, SONG, 'Item_Scale_Silver', song,
                              {}, ('Item_Scale_Silver', 'Item_Range_SlingShot'), template, asked))

    # ------------------------------------------------------------------------------------- the bridge gift
    print('Saria\'s gift on the bridge (%s)' % GIFT)
    gift_path, (cid, _, g) = next(iter(build_mod.plan_cutscene_gifts(world, [(GIFT, 'Item_Scale_Silver')]).items()))
    gift_old = plain(gift_path)
    ok_w, ok_a, ok_back, ok_lead, ok_held = True, True, True, True, True
    for name, levels in FAMILIES.items():
        ef = evfl.loads(gift_old)
        fc = ef.flowchart
        show = levels[0] == g['item'] or ground_items.kind_of(plain_pack(romfs, d), levels[0]) == \
            build_mod.CUTSCENE_SHOWN_KIND
        companions = build_mod.SCRUB_COMPANIONS.get(levels[0], ())
        build_mod.cutscene_gift_edit(fc, GIFT, g, levels[0], show, companions)
        build_mod.cutscene_family_edit(fc, GIFT, g, levels, template, asked, companions)
        new = build_mod.flow_write_checked(ef)
        back, orig = evfl.loads(new).flowchart, evfl.loads(gift_old).flowchart
        try:
            build_mod.cutscene_family_check(orig, back, GIFT, g, levels, template, asked, show, companions)
        except SystemExit as e:
            ok_back = False
            print('  read-back refused', name, e)
        by = {e.name: k for k, e in enumerate(back.events)}
        into = lambda i: next(k for k, e in enumerate(back.events) if k >= len(orig.events)   # noqa: E731
                              and e.type == 'switch' and build_mod.level_reached(back, k, set(), template) == i
                              and any(x.next == k or k in x.forks for x in back.events[:len(orig.events)]))
        top_w, top_a = into(by[g['window']]), into(by[g['add']])
        ok_w &= simulate(back, top_w, levels, lambda e: e.params.get('ActorName') if e.type == 'subflow'
                         and (e.flowchart, e.entry) == build_mod.CUTSCENE_WINDOW else None) == wanted(levels)
        ok_a &= simulate(back, top_a, levels, lambda e: e.params.get('Actor') if e.type == 'action'
                         and build_mod._action_name(back, e) == build_mod.CUTSCENE_ADD[1] else None) == wanted(levels)
        lead = orig.events[[e.name for e in orig.events].index(g['add'])].next
        for r in range(1, len(levels)):
            a = back.events[build_mod.level_reached(back, top_a, {asked(x) for x in levels[:r]}, template)]
            ok_lead &= a.next == lead                      # a later level: no seed bag or quiver with it
        held = [a.name for a in back.actors if a.name in (g['item'],) + tuple(levels)]
        ok_held &= held == [levels[0] if show else g['item']]
    good &= check('every family (%d) on the bridge gift: the window names the next level, for every number owned'
                  % len(FAMILIES), ok_w)
    good &= check('  the add step adds the same level (both questions asked before anything is added)', ok_a)
    good &= check('  a later level\'s add leads on to what the add led on to (the seed bag and quiver are the first '
                  'level\'s alone)', ok_lead)
    good &= check('  Link holds one actor: the first level when it is an item actor, else Saria\'s ocarina', ok_held)
    good &= check('  the read-back (cutscene_family_check) passes for every family', ok_back)
    ef = evfl.loads(gift_old)
    levels = FAMILIES['Scale'] if 'Scale' in FAMILIES else next(f for f in FAMILIES.values() if len(f) == 2)
    build_mod.cutscene_gift_edit(ef.flowchart, GIFT, g, levels[0], False)
    build_mod.cutscene_family_edit(ef.flowchart, GIFT, g, levels, template, asked)
    good_fc = evfl.loads(build_mod.flow_write_checked(ef)).flowchart
    n = len(evfl.loads(gift_old).flowchart.events)
    bad1 = copy.deepcopy(good_fc)                     # a later level's window leads elsewhere
    w = next(e for e in bad1.events[n:] if e.type == 'subflow')
    w.next = None
    bad2 = copy.deepcopy(good_fc)                     # an original step still goes to the add itself
    add_i = [e.name for e in bad2.events].index(g['add'])
    fork = next(e for e in bad2.events[:n] if any(build_mod.level_reached(bad2, f, set(), template) == add_i
                                                   and f >= n for f in e.forks))
    fork.forks = [add_i if f >= n and build_mod.level_reached(bad2, f, set(), template) == add_i else f
                  for f in fork.forks]
    good &= check('  the read-back refuses a later level\'s window that does not lead on, and a link left on the add',
                  refused(build_mod.cutscene_family_check, evfl.loads(gift_old).flowchart, bad1, GIFT, g, levels,
                          template, asked, False)
                  and refused(build_mod.cutscene_family_check, evfl.loads(gift_old).flowchart, bad2, GIFT, g, levels,
                              template, asked, False))
    swapped = copy.deepcopy(g)
    swapped['window'], swapped['add'] = g['add'], g['window']
    fc = evfl.loads(gift_old).flowchart
    good &= check('  refused: a cutscene whose window does not come before its add (as the data would have it '
                  'swapped)', refused(build_mod.cutscene_family_edit, fc, GIFT, swapped, levels, template, asked))

    # ------------------------------------------------------------------------------------- whole builds
    print('Whole builds')
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *assign):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(assign))
            base = os.path.join(tmp, name, 'romfs')
            return base, said.getvalue(), {os.path.relpath(f, base).replace(os.sep, '/')
                                           for f in glob.glob(os.path.join(base, '**', '*'), recursive=True)
                                           if os.path.isfile(f)}

        bow = '>'.join(next(f for f in FAMILIES.values() if f[0] == 'Item_Range_Bow'))
        oca = '>'.join(next(f for f in FAMILIES.values() if f[0] == 'Item_Ocarina_Fairy'))
        base, said, files = run('ev', '%s=%s' % (SONG, oca), '%s=%s' % (GIFT, bow))
        rd = lambda path: zstd.decompress(open(os.path.join(base, *path.split('/')) + '.zs', 'rb').read(), d)  # noqa
        song_fc = evfl.loads(rd(song_path)).flowchart
        gift_fc = evfl.loads(rd(gift_path)).flowchart
        good &= check('a build with the ocarinas on the song and the bows on the bridge gift: both cutscenes in the '
                      'mod, each with its questions',
                      song_path + '.zs' in files and gift_path + '.zs' in files
                      and sum(e.type == 'switch' for e in song_fc.events) - sum(
                          e.type == 'switch' for e in evfl.loads(song_old).flowchart.events) == 1
                      and sum(e.type == 'switch' for e in gift_fc.events) - sum(
                          e.type == 'switch' for e in evfl.loads(gift_old).flowchart.events) == 4)
        good &= check('  the build says what each asks',
                      'asks Event' in said and '(the window): asks first' in said and '(the add): asks first' in said)
        good &= check('refused: a family on a gift with no flow data (a Skull Kid)',
                      refused(run, 'no1', 'LW Skull Kid=' + oca))

    print()
    print('ALL OK' if good else 'SOME CHECKS FAILED')
    return 0 if good else 1


def plain_pack(romfs, d):
    """reads a game file by its romfs path (for ground_items.kind_of)"""
    def read(path):
        p = os.path.join(romfs, *path.split('/'))
        return open(p, 'rb').read() if os.path.exists(p) else zstd.decompress(open(p + '.zs', 'rb').read(), d)
    return read


def _plain_song(song_old, song, build_mod, template, asked):
    """one plain item on the song, through song_skip and its read-back"""
    for item in ('Obj_Heart_Piece', 'Item_Range_SlingShot'):    # the slingshot: its seed bag comes with it
        ef = evfl.loads(song_old)
        build_mod.song_skip(ef.flowchart, SONG, item, song, None, None, template, asked)
        back = evfl.loads(build_mod.flow_write_checked(ef)).flowchart
        build_mod.song_skip_check(evfl.loads(song_old).flowchart, back, SONG, (item,), {}, template, asked)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
