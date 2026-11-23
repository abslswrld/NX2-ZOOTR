"""One-time drops: what tools/build_mod.py and tools/once_items.py make so that a rock, a bush or a pot gives its
item once (a plain item, or a level of a progressive family), and progressive families on pots. Checked on the
game's own files: the two saved flags of every rock, bush and pot check, the game nodes the new AI is copied
from, the versions that mark their dropper, the droppers' AI (read back from the files), what the rule gives
for every order of a family's checks (picked up, left behind, taken elsewhere while it lies there), and a whole
build. Only reads the game; the build it runs goes to a temporary folder that is removed again.

    python tests/one_time_check.py "C:\\...\\romfs"
"""
import contextlib
import glob
import io
import itertools
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import once_items  # noqa: E402
import shop_items  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, sarc, ainb, restbl  # noqa: E402
from logic.world import World  # noqa: E402

DROPPERS = ('Obj_LiftRock_A_01', 'Obj_Plant_Grass_A_01', 'Obj_Pot_A_01')
SCALES = ('Item_Scale_Silver', 'Item_Scale_Gold')
MAGIC = ('Item_FairyBless_MP', 'Item_FairyBless_MPDouble')
SEEDS = ('Item_Range_SlingShot', 'Item_BulletBag_Medium', 'Item_BulletBag_Large')
CORNERS = tuple('KF_CIRCLE_ADULT_ROCK_%02d' % n for n in (3, 6, 9, 12))  # the 4 adult corner rocks: never used
# the whole build: a pair on a child pot, a pair whose names start alike on an adult pot, a plain item on a pot,
# a game ground item (a rupee) on a rock, a three-level family on a bush (one check of three)
BUILD = (('KF_HOUSE_OF_TWINS_CHILD_POT_01', '>'.join(SCALES)),
         ('KF_HOUSE_OF_TWINS_ADULT_POT_02', '>'.join(MAGIC)),
         ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02', 'Item_Boomerang'),
         ('KF_WEST_OF_MIDOS_HOUSE_CHILD_ROCK_01', 'Obj_Rupee_Red'),
         ('KF_BEHIND_SHOP_CHILD_BUSH_01', '>'.join(SEEDS)))
RESTBL = build_mod.RESTBL_PATH.replace(os.sep, '/')[:-3]


def check(name, ok):
    print('%-112s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args, **kw):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            f(*args, **kw)
    except SystemExit as e:
        return bool(e.code)
    return False


# ---- the rule, as the files say it works (a model to try every order on) ----

class Spot:
    """a rock, a bush or a pot with one of our drops, and Link. `steps`: what its AI renames (dropper_of);
    `turns`: {version: whether it marks its dropper when it turns} (marks_of); `first`: what its placement names.
    The rule (once_items): a version picked up marks the dropper (its two saved flags, as a token marks its
    Gold Skulltula), and a marked dropper is not made again (TO BE SEEN IN GAME: the model takes it as for the
    Gold Skulltula); else it drops what its placement names, after its steps; a version that lies there while
    Link owns its level marks it and turns into the next level's ordinary turning item (the last level deletes
    itself); an ordinary turning item marks nothing; a drop left lying is gone with the area, and the dropper
    is back then."""

    def __init__(self, family, steps, turns, first):
        self.family, self.steps, self.turns, self.first = family, steps, turns, first
        self.marked, self.lying, self.broken = False, None, False
        self.once = {once_items.once_name(x): k for k, x in enumerate(family)}
        self.plain = {turn_items.turn_name(x): k for k, x in enumerate(family)}

    def name(self, owned):
        """the drop named once the dropper's AI has run (one write per frame; two different writes in one frame
        would be a fault)"""
        named = self.first
        for _ in range(len(self.family) + 1):
            writes = {to for frm, item, to in self.steps if named.startswith(frm) and item in owned}
            if len(writes) > 1:
                raise AssertionError('two names written in one frame: %s' % writes)
            if not writes or writes == {named}:
                return named
            named = writes.pop()
        raise AssertionError('the names do not settle')

    def brk(self, owned):
        if self.broken:
            return
        self.broken = True
        self.lying = None if self.marked else self.name(owned)
        self.frame(owned)

    def frame(self, owned):
        """what lies there does what its AI does while Link owns its level"""
        while self.lying is not None:
            if self.lying in self.once:
                k = self.once[self.lying]
                if self.family[k] not in owned:
                    return
                if self.turns[self.lying]:
                    self.marked = True
                    self.lying = turn_items.turn_name(self.family[k + 1])
                else:
                    self.lying = None
            elif self.lying in self.plain:
                k = self.plain[self.lying]
                if self.family[k] not in owned:
                    return
                self.lying = turn_items.turn_name(self.family[k + 1]) if k + 1 < len(self.family) else None
            else:
                return

    def pick(self, owned):
        x, self.lying = self.lying, None
        if x is None:
            return None
        if x in self.once:
            self.marked = True
            return self.family[self.once[x]]
        return self.family[self.plain[x]]

    def leave(self):
        self.lying, self.broken = None, False


def play(spot, family, script):
    """runs a script of moves: 'b' break the rock, 'p' pick up what lies there, 'l' leave the area and come
    back, 'c' take another check of the family (a checking chest: the lowest level not owned). Returns (what was
    given in order, whether a level was given twice or skipped)"""
    owned, given, bad = set(), [], False
    for m in script:
        got = None
        if m == 'b':
            spot.brk(owned)
        elif m == 'p':
            got = spot.pick(owned)
        elif m == 'l':
            spot.leave()
        elif m == 'c':
            got = next((x for x in family if x not in owned), None)
        if got is not None:
            bad |= got in owned or any(x not in owned for x in family[:family.index(got)])
            owned.add(got)
            given.append(got)
        spot.frame(owned)
    return given, bad


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda f: zstd.decompress(open(f, 'rb').read(), d)   # noqa: E731
    plain = lambda path: rd(os.path.join(romfs, *path.split('/')) + '.zs')   # noqa: E731
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    model = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))  # noqa: E731
    pack = lambda actor: sarc.Sarc.read(plain(ground_items.pack_path(actor))).files   # noqa: E731
    world = World()
    good = True

    # ------------------------------------------------------------------------------------- the game's files
    print('The game')
    flags = build_mod.placement_flags(plain(build_mod.GAME_DATA))
    spots, no_drop, missing = [], set(), []
    drops = {}
    for r in world.regions.values():
        for name, loc in r.locations.items():
            for scene, sid, p in world.placements_of(r, loc):
                if world.checks[scene][sid]['kind'] not in once_items.KINDS:
                    continue
                if p['actor'] not in drops:
                    drops[p['actor']] = once_items.has_drop(pack(p['actor']), p['actor'])
                if not drops[p['actor']]:
                    no_drop.add(p['actor'])
                    continue
                spots.append((loc.get('id') or name, p['hash']))
                if flags.get(p['hash']) != once_items.FLAG_RESET \
                        or flags.get(str(int(p['hash']) ^ 2)) != build_mod.FLAG_KEPT:
                    missing.append(loc.get('id') or name)
    good &= check('every rock, bush and pot check that drops something (%d placements) has its two saved flags: '
                  'its own (reset) and hash ^ 2 (never reset)' % len(spots), spots and not missing)
    good &= check('  the ones that drop nothing are props with no drop part: %s' % ', '.join(sorted(no_drop)),
                  all(not once_items.has_drop(pack(a), a) for a in no_drop))
    bancs = glob.glob(os.path.join(romfs, 'Banc', '**', '*.bcett.byml.zs'), recursive=True)
    ours = set()
    for f in bancs:
        for a in byml.loads(rd(f)).root.get('Actors') or []:
            x = (a.get('Dynamic') or {}).get(once_items.DROP_KEY)
            if isinstance(x, str) and x.startswith(once_items.OURS):
                ours.add(x)
    good &= check('no placement of the game (%d maps) names a drop that starts with %s: every game rock, bush and '
                  'pot takes the side that does nothing' % (len(bancs), once_items.OURS), not ours)
    keys = True
    for a in DROPPERS:
        files = pack(a)
        table = byml.loads(files[turn_items.DROP_SHARED[1]]).root
        entry = [x for x in table['BlackboardParamStringArray'] if x['BBKey'] == once_items.DROP_KEY]
        keys &= len(entry) == 1 and entry[0]['IsInstanceParam'] and entry[0]['StringParamType'] == 'String128'
    good &= check('the drop a placement names is a text of 128 characters at most in the actor\'s own blackboard '
                  '(%s): what the AI reads and writes' % once_items.DROP_KEY, keys)
    every = {}
    instance, writes = set(), []                       # every instance parameter; every write to an actor's own
    for f in os.listdir(os.path.join(romfs, 'Pack', 'Actor')):
        if f.endswith('.pack.zs'):
            files = sarc.Sarc.read(rd(os.path.join(romfs, 'Pack', 'Actor', f))).files
            instance |= once_items.instance_keys(files)
            for inner, data in files.items():
                if inner.startswith('Actor/'):
                    every.setdefault(inner, set()).add(f[:-len('.pack.zs')])
                elif inner.endswith('.ainb'):
                    writes += once_items.actor_writes(data)
    for inner, data in sarc.Sarc.read(plain(once_items.AI_PACK)).files.items():
        if inner.endswith('.ainb'):
            writes += once_items.actor_writes(data)
    # the in-game crash of 2026-11-22: the droppers' AI wrote Drop__DropActor, an instance parameter
    good &= check('no AI of the game writes an instance parameter of its actor\'s blackboard (%d writes to an '
                  'actor\'s own, none to any of the %d instance parameters): writing one stops the game'
                  % (len(writes), len(instance)),
                  writes and once_items.DROP_KEY in instance and not {k for _, k in writes} & instance)
    held = True
    for a in sorted(drops):
        if drops[a]:
            found = {x for x in once_items.holders(romfs, a) if ground_items.ap_path(a) in pack(x)}
            held &= found == every[ground_items.ap_path(a)]
    good &= check('the packs that hold a dropper\'s own file are found among the packs of its kind (every pack of '
                  'the game looked through)', held)

    src = once_items.sources(plain)
    t = once_items._templates(src)
    token = ainb.loads(src['token'])
    group, _ = once_items._picked_up(token)
    good &= check('the game nodes copied are found: the token\'s "picked up" branch (%d nodes, with %s), %s, %s, '
                  '%s' % (len(group), once_items.N_MARK, once_items.Q_NAMED, once_items.Q_STARTS, once_items.N_WRITE),
                  len(group) == 7 and all(k in t for k in ('mark', 'named', 'starts', 'write', 'all')))
    # what the game reads as an object's "done already?" (QueryInstanceGameDataGetBool) needs a setting that no
    # rock, bush or pot has, and is not the hash ^ 2 flag (once_items' notes): it is not used
    tables = True
    for a in DROPPERS:
        files = pack(a)
        tables &= not any('InstanceGameParameter' in k for k in files) and not any(
            b'InstanceGameParameterSetting' in v for k, v in files.items() if 'GameParameterTable/' in k)
    good &= check('  no rock, bush or pot has an InstanceGameParameterSetting (the hanging signs\' "done already?" '
                  'would always say no for them): not used', tables)

    # ------------------------------------------------------------------------------------- the versions
    print('The versions that mark their dropper')
    name, ppack, new_inner, rows, _ = once_items.build_plain('Item_Boomerang', plain, table_rows, model, src)
    files = sarc.Sarc.read(ppack).files
    got = once_items.marks_of(files[shop_items.ai_path(once_items.PLAIN_AI)])
    number = byml.loads(files[once_items.TABLE]).root['BlackboardParamU64Array']
    good &= check('plain: %s marks its dropper when picked up (the token\'s branch), the token\'s 64-bit number '
                  'in its blackboard' % name,
                  name == once_items.plain_name('Item_Boomerang') and got['picked_up'] and got['turns'] == 0
                  and [x['BBKey'] for x in number] == [once_items.KEY] and set(rows) == set(ground_items.TABLES))
    turns, ok, same = {}, True, True
    known_as = {r['__RowId']: r.get('ActorName') for r in table_rows('ActorInfo')}   # as build_mod's flow_name
    for family in (SCALES, SEEDS):
        for k, x in enumerate(family):
            bundle_for = known_as.get(x) or x if k == 0 and x in build_mod.SCRUB_COMPANIONS else None
            name, vpack, _, _, _ = once_items.build(family, k, plain, table_rows, model, bundle_for, src)
            vfiles = sarc.Sarc.read(vpack).files
            data = vfiles[shop_items.ai_path(once_items.ai_name(x))]
            got = once_items.marks_of(data)
            _, tpack, _, _, _ = turn_items.build(family, k, plain, table_rows, model, bundle_for,
                                                 version=once_items.TURN, ai=once_items.ai_name(x))
            u = ainb.loads(once_items.unmarked(data))
            w = ainb.loads(sarc.Sarc.read(tpack).files[shop_items.ai_path(once_items.ai_name(x))])
            same &= len(u.nodes) == len(w.nodes) and shop_items._doc_state(u) == shop_items._doc_state(w) and all(
                shop_items._node_state(a) == shop_items._node_state(b) for a, b in zip(u.nodes, w.nodes)) \
                and bool(turn_items.describe(once_items.unmarked(data))['bundle']) == bool(bundle_for)
            last = k == len(family) - 1
            turns[name] = bool(got['turns_marked'])
            ok &= name == once_items.once_name(x) and got['picked_up'] and got['turns'] == got['turns_marked'] \
                and (got['turns'] == 0) == last
            if not last:
                sub = byml.loads(vfiles[turn_items.drop_sub_path(name)]).root
                ok &= [i['DropActorName'] for i in sub['Items']] == [
                    turn_items._work(ground_items.ap_path(turn_items.turn_name(family[k + 1])))]
    good &= check('turning: every level of a pair and of a three-level family marks its dropper when picked up, '
                  'and (not the last) when it turns into the next level\'s turning item', ok)
    good &= check('  with the mark taken out, each is the turning item tools/turn_items.py makes (the Fairy '
                  'Slingshot with its bag step), node for node', same)

    # ------------------------------------------------------------------------------------- the droppers
    print('The rocks, bushes and pots')
    fams = [f for f in build_mod.FAMILIES.values()]
    steps = [(once_items.once_name(f[i]), f[i], once_items.once_name(f[i + 1])) for f in fams
             for i in range(len(f) - 1)]
    ok, sizes, refused_steps = True, [], True
    for a in DROPPERS:
        files = pack(a)
        root, new, changed = once_items.dropper_files(files, a, src)
        out = new[shop_items.ai_path(once_items.dropper_ai_name(root))][0]
        got = once_items.dropper_of(out)
        game = ainb.loads(files[shop_items.ai_path(root)])
        back = ainb.loads(out)
        diff = [i for i, (o, b) in enumerate(zip(game.nodes, back.nodes))
                if shop_items._node_state(o) != shop_items._node_state(b)]
        ok &= got['ours'] == once_items.OURS and got['key'] == once_items.KEY and got['steps'] == [] \
            and once_items.dropper_of(files[shop_items.ai_path(root)]) is None and len(diff) == 1 \
            and byml.loads(changed[2]).root['Components']['AIInfoRef'] == '?' + shop_items.ai_info_path(
                once_items.dropper_ai_name(root)) \
            and not {k for _, k in once_items.actor_writes(out)} & once_items.instance_keys(files)
        sizes.append('%s +%d' % (root, len(back.nodes) - len(game.nodes)))
        refused_steps &= refused(once_items.dropper_files, files, a, src, steps)
    good &= check('each dropper\'s AI, read back from the file: for a drop of ours it hands its placement\'s number '
                  'over, and writes nothing of its blackboard (%s)' % ', '.join(sizes), ok)
    good &= check('  naming the next level\'s version (writing %s, an instance parameter: the crash of '
                  '2026-11-22) is refused for every dropper' % once_items.DROP_KEY, refused_steps)
    steps = []                                         # what the droppers' AI renames: nothing

    # ------------------------------------------------------------------------------------- the rule
    print('What the rule gives (from the steps and marks read above)')
    ok, lost, cases = True, [], 0
    for family in (SCALES, SEEDS):
        st = [s for s in steps if s[1] in family]
        n = len(family)
        for at in range(n):
            # the rock taken at place `at` among the family's checks: picked up at once; then back: nothing
            for left in (False, True):
                spot = Spot(family, st, turns, once_items.once_name(family[0]))
                script = 'c' * at + ('blb' if left else 'b') + 'p' + 'c' * (n - 1 - at) + 'lbp' + 'lbp'
                given, bad_ = play(spot, family, script)
                cases += 1
                if left and at:                        # Link owned the first level: it turned as it came out
                    ok &= not bad_ and list(given) == list(family[:-1])
                    lost.append(family[at])
                else:
                    ok &= list(given) == list(family) and not bad_
            # broken, and another check taken while it lies there: it turns; picked up, or left behind
            for pick in (True, False):
                spot = Spot(family, st, turns, once_items.once_name(family[0]))
                script = 'c' * at + 'b' + ('c' if at < n - 1 else '') + ('p' if pick else 'l') \
                    + 'c' * max(0, n - 2 - at) + 'lbp'
                given, bad_ = play(spot, family, script)
                cases += 1
                if pick:
                    ok &= list(given) == list(family) and not bad_
                else:                                  # the family cannot be finished: its last level is missing
                    ok &= not bad_ and list(given) == list(family[:-1])
                    lost.append(family[min(at + 1, n - 1)])   # (the last place: it turned as it came out)
    good &= check('for every place of a rock among its family\'s checks (%d cases): each level once, in order; '
                  'the first level left behind is there again when the rock is back; once picked up, the rock '
                  'gives nothing' % cases, ok)
    good &= check('  the known limit: Link owns the level it drops (before it is broken, or taken elsewhere while '
                  'it lies there), it turns into the next level; left behind then, that level is lost (%d cases)'
                  % len(lost), bool(lost))
    spot = Spot(('Item_Boomerang',), [], {}, once_items.plain_name('Item_Boomerang'))
    spot.once = {once_items.plain_name('Item_Boomerang'): 0}
    spot.turns = {once_items.plain_name('Item_Boomerang'): False}
    given, bad_ = play(spot, ('Item_Boomerang',), 'blbplbplbp')
    good &= check('plain: left behind, it is there again when the rock is back; picked up, never again',
                  given == ['Item_Boomerang'] and not bad_)

    # ------------------------------------------------------------------------------------- a whole build
    print('A whole build')
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *assign):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(assign))
            base = os.path.join(tmp, name, 'romfs')
            return base, said.getvalue(), {os.path.relpath(f, base).replace(os.sep, '/')
                                           for f in glob.glob(os.path.join(base, '**', '*'), recursive=True)
                                           if os.path.isfile(f)}

        mod = lambda b, path: rd(os.path.join(b, *path.split('/')) + '.zs')   # noqa: E731
        base, said, files = run('once', *['%s=%s' % x for x in BUILD])
        want = {'KF_HOUSE_OF_TWINS_CHILD_POT_01': once_items.once_name(SCALES[0]),
                'KF_HOUSE_OF_TWINS_ADULT_POT_02': once_items.once_name(MAGIC[0]),
                'KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02': once_items.plain_name('Item_Boomerang'),
                'KF_WEST_OF_MIDOS_HOUSE_CHILD_ROCK_01': ground_items.ground_name('Obj_Rupee_Red', 'token'),
                'KF_BEHIND_SHOP_CHILD_BUSH_01': once_items.once_name(SEEDS[0])}
        lines = said.splitlines()
        ok = all(any(l.startswith(c + ' ') and l.endswith('-> ' + n) for l in lines) for c, n in want.items()) \
            and all(any(l.startswith(c) and 'given once: picked up, it marks this' in l for l in lines) for c in want)
        good &= check('the maps name the versions that mark their dropper, and the build says each is given once',
                      ok)
        t1 = restbl.Restbl.read(mod(base, RESTBL))
        ok = True
        versions = [once_items.once_name(x) for x in SCALES + MAGIC + SEEDS] + [once_items.plain_name('Item_Boomerang')]
        for f in (SCALES, MAGIC, SEEDS):
            for k in range(len(f)):
                n, vpack, _, _, _ = once_items.build(f, k, plain, table_rows, model,
                                                     known_as.get(f[0]) or f[0] if k == 0 and f[0]
                                                     in build_mod.SCRUB_COMPANIONS else None, src)
                ok &= mod(base, ground_items.pack_path(n)) == vpack
        n, vpack, _, _, _ = once_items.build_plain('Item_Boomerang', plain, table_rows, model, src)
        ok &= mod(base, ground_items.pack_path(n)) == vpack
        ok &= all(t1.get(ground_items.pack_path(n)) for n in versions)
        good &= check('  the %d versions are the ones tools/once_items.py makes, each with a size entry'
                      % len(versions), ok)
        ok, packs_seen = True, 0
        for a in ('Obj_Pot_A_01', 'Obj_LiftRock_A_01', 'Obj_Plant_Grass_A_01'):
            root, new, changed = once_items.dropper_files(pack(a), a, src)
            for h in once_items.holders(romfs, a):
                if ground_items.ap_path(a) not in pack(h):
                    continue
                packs_seen += 1
                game = pack(h)
                got = sarc.Sarc.read(mod(base, ground_items.pack_path(h))).files
                ok &= got[changed[0]] == changed[2] and all(got[p] == x for p, (x, _) in new.items()) \
                    and set(got) == set(game) | set(new) \
                    and all(got[p] == game[p] for p in game if p != changed[0])
            ok &= all(t1.get(p) for p in new) and bool(t1.get(changed[0]))
        good &= check('  the pot, the rock and the bush: in each of the %d packs that hold their own file, that '
                      'file names our AI, the AI is added, nothing else differs; size entries' % packs_seen, ok)
        bad_writes, ais = set(), 0
        for f in files:
            if f.startswith('Pack/') and f.endswith('.pack.zs'):
                for inner, data in sarc.Sarc.read(mod(base, f[:-len('.zs')])).files.items():
                    if inner.endswith('.ainb'):
                        ais += 1
                        bad_writes |= {(f, inner, k) for _, k in once_items.actor_writes(data) if k in instance}
        good &= check('  no AI in the build (%d files in its packs) writes an instance parameter of its actor\'s '
                      'blackboard (the crash of 2026-11-22: a rock with the Fairy Bow owned)%s'
                      % (ais, ''.join(' %s %s %s' % x for x in sorted(bad_writes))), ais and not bad_writes)
        good &= check('  the 4 adult corner rocks of the circle are used by no build here',
                      not set(CORNERS) & {c for c, _ in BUILD})
        print('\n'.join('  ' + l[:200] for l in lines if l.startswith('once   Obj_')))

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
