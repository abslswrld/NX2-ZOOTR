"""Full requirements of every check, from the start of the game: the smallest sets of items (and settings)
that let a child or an adult get it.

Unlike a check's own rule (which only says what is needed once in its region), this follows every route
through the region map: the exits' rules, the check's rule, events ('Deku Tree Clear'...), helpers and
can_play / can_use, the same way the search in world.py does.

A requirement is a list of alternatives, any one of which is enough; each alternative is a sorted list of
names (items, settings that must be on, 'Item*n' for n copies):
    [[]]                       nothing needed
    [['KokiriSword'], ['Slingshot']]   the Kokiri Sword, or the slingshot
    [['Bow', 'ForestTempleSmallKey*3']]   the Bow and three small keys (a route through three locked doors
                               needs has(Key, 1), has(Key, 2), has(Key, 3): only the highest count is kept)
    None                       impossible at this age (with everything mapped so far)
Only alternatives that are not covered by a smaller one are kept.

    from logic.world import World
    from logic.requirements import requirements
    req = requirements(World())          # {check name: {'child': ..., 'adult': ...}}

Rules may use: and, or, True/False, is_child, is_adult, at_night, helpers, settings, items, 'events',
has(X, n), can_play(X), can_use(X), setting(x). Anything else (not, comparisons) stops with an error rather
than giving a wrong answer.
"""
import ast

from . import rules

TRUE = frozenset([frozenset()])
FALSE = frozenset()
AGES = ('child', 'adult')


class RequirementError(Exception):
    pass


def _split(name):
    """'Item*3' -> ('Item', 3); 'Item' -> ('Item', 1)"""
    item, star, count = name.partition('*')
    return (item, int(count)) if star and count.isdigit() else (name, 1)


def _highest(s):
    """the same set with one name per item: of 'Key', 'Key*2' and 'Key*3' only 'Key*3' stays"""
    top = {}
    for name in s:
        item, n = _split(name)
        top[item] = max(top.get(item, 0), n)
    return frozenset(item if n == 1 else '%s*%d' % (item, n) for item, n in top.items())


def _covers(small, big):
    """everything `small` asks for is in `big`, counts included ('Key*2' is covered by 'Key*3')"""
    have = dict(_split(name) for name in big)
    return all(have.get(item, 0) >= n for item, n in map(_split, small))


def _minimal(sets):
    out = []
    for s in sorted({_highest(s) for s in sets}, key=lambda s: (len(s), sorted(s))):
        if not any(_covers(o, s) for o in out):
            out.append(s)
    return frozenset(out)


def _or(*fs):
    return _minimal(s for f in fs for s in f)


def _and(*fs):
    acc = TRUE
    for f in fs:
        acc = _minimal(a | b for a in acc for b in f)
        if not acc:
            return FALSE
    return acc


def _atom(name):
    return frozenset([frozenset([name])])


class _Solver:
    def __init__(self, world, skip_unmapped=False):
        self.w = world
        self.settings = set(world.settings_defaults)
        self.trees = {}
        self.skip_unmapped = skip_unmapped
        self.events = {}           # event name -> formula
        self.access = {}           # (region, age) -> formula

    def tree(self, text):
        if text is True or text is None or text == 'True':
            return ast.Constant(True)
        if text is False or text == 'False':
            return ast.Constant(False)
        if text not in self.trees:
            self.trees[text] = ast.parse(str(text), mode='eval').body
        return self.trees[text]

    def ev(self, node, age, region, stack=()):
        if isinstance(node, ast.BoolOp):
            parts = [self.ev(v, age, region, stack) for v in node.values]
            return _and(*parts) if isinstance(node.op, ast.And) else _or(*parts)
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, bool):
                return TRUE if v else FALSE
            if isinstance(v, str):
                return self.events.get(v, FALSE)
            raise RequirementError('number %r outside a function' % v)
        if isinstance(node, ast.Name):
            return self.name(node.id, age, region, stack)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn, args = node.func.id, node.args
            arg = args[0].id if isinstance(args[0], ast.Name) else args[0].value
            if fn == 'can_play':
                return _and(_atom(arg), _or(_atom('Ocarina'), _atom('OcarinaOfTime')))
            if fn == 'can_use':
                if (arg in rules.ADULT_ONLY and age != 'adult') or (arg in rules.CHILD_ONLY and age != 'child'):
                    return FALSE
                return _atom(arg)
            if fn == 'has':
                n = args[1].value if len(args) > 1 else 1
                return _atom(arg if n == 1 else '%s*%d' % (arg, n))
            if fn == 'setting':
                return _atom(arg)
        raise RequirementError('cannot work out requirements for %s' % ast.dump(node))

    def name(self, n, age, region, stack):
        if n == 'is_child':
            return TRUE if age == 'child' else FALSE
        if n == 'is_adult':
            return TRUE if age == 'adult' else FALSE
        if n == 'at_night':
            if region is not None and region.time_passes:
                return TRUE
            return _and(_atom('SunsSong'), _or(_atom('Ocarina'), _atom('OcarinaOfTime')))
        if n in self.w.helper_text:
            if n in stack:
                raise RequirementError('helper %s refers to itself' % n)
            return self.ev(self.tree(self.w.helper_text[n]), age, region, stack + (n,))
        if n in self.events:
            return self.events[n]
        if n in self.event_names:
            return FALSE                      # an event not reached yet (this pass)
        return _atom(n)                       # an item or a setting

    def solve(self):
        w = self.w
        self.event_names = {e for r in w.regions.values() for e in r.events}
        for e in self.event_names:
            self.events[e] = FALSE
        for rn in w.regions:
            for a in AGES:
                self.access[(rn, a)] = FALSE
        for a in AGES:
            self.access[('Root', a)] = TRUE
        changed = True
        while changed:
            changed = False
            for rn, r in w.regions.items():
                if self.skip_unmapped and r.unmapped:
                    continue
                for a in AGES:
                    here = self.access[(rn, a)]
                    if not here:
                        continue
                    for target, (txt, _) in r.exits.items():
                        if self.skip_unmapped and w.regions[target].unmapped:
                            continue
                        f = _or(self.access[(target, a)], _and(here, self.ev(self.tree(txt), a, r)))
                        if f != self.access[(target, a)]:
                            self.access[(target, a)] = f
                            changed = True
                    for e, (txt, _) in r.events.items():
                        f = _or(self.events[e], _and(here, self.ev(self.tree(txt), a, r)))
                        if f != self.events[e]:
                            self.events[e] = f
                            changed = True
        out = {}
        for rn, r in w.regions.items():
            for ln, loc in r.locations.items():
                out[ln] = {}
                for a in AGES:
                    f = _and(self.access[(rn, a)], self.ev(self.tree(loc.get('rule', True)), a, r))
                    out[ln][a] = f
        return out


def _plain(f):
    if not f:
        return None
    return [sorted(s) for s in sorted(f, key=lambda s: (len(s), sorted(s)))]


def requirements(world):
    """{check name: {'child': requirement, 'adult': requirement}} (see the module notes)"""
    return {n: {a: _plain(f) for a, f in v.items()} for n, v in _Solver(world).solve().items()}


def placeholder_ages(world):
    """{check name: [ages]} for the checks whose requirements at that age change when the 'not mapped yet'
    placeholder regions are left out (their answer still relies on a placeholder)"""
    full = _Solver(world).solve()
    real = _Solver(world, skip_unmapped=True).solve()
    return {n: [a for a in AGES if full[n][a] != real[n][a]] for n in full
            if any(full[n][a] != real[n][a] for a in AGES)}
