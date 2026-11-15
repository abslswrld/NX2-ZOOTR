"""Rule expressions for the region map.

A rule is a small Python-like expression, written in the data files, e.g.
    is_child and (Slingshot or Boomerang)
    is_adult and at_night and can_use(Hookshot)
    open_forest or 'Showed Mido Sword and Shield'
    has(Bottle, 2)

Names:
    True / False
    is_child, is_adult           the age being checked
    at_night                     night can be reached here (the region lets time pass, or Sun's Song)
    a helper name                another rule, defined in data/helpers.json
    a setting name               value of that setting (settings are given to the search)
    anything else                an item or event: true if owned (CamelCase or 'quoted text')
Functions:
    has(X, n)                    at least n of item X
    can_play(Song)               the song is learned and Link has an ocarina
    can_use(Item)                owned and usable at this age (some items are child-only or adult-only)
    setting(name)                value of a setting (same as the bare name)
Operators: and, or, not, ==, !=, <, <=, >, >=, parentheses, numbers, 'strings'.
Rules are parsed once and checked against a State; nothing is ever passed to eval().
"""
import ast

ADULT_ONLY = {'Hookshot', 'Longshot', 'Bow', 'Hammer', 'IronBoots', 'HoverBoots', 'GoronTunic', 'ZoraTunic',
              'MirrorShield', 'MasterSword', 'BiggoronSword', 'FireArrows', 'IceArrows', 'LightArrows',
              'SilverGauntlets', 'GoldGauntlets', 'Scarecrow', 'DistantScarecrow'}
CHILD_ONLY = {'Slingshot', 'Boomerang', 'KokiriSword', 'DekuShield'}


class RuleError(Exception):
    pass


class Context:
    """What a rule is checked against: the items/events owned, the settings, the age and the region."""

    def __init__(self, state, age, region=None, helpers=None):
        self.state, self.age, self.region = state, age, region
        self.helpers = helpers if helpers is not None else {}


def compile_rule(text, where=''):
    """Parse a rule; returns a function(ctx) -> bool-ish value."""
    if text is True or text is None:
        return lambda ctx: True
    if text is False:
        return lambda ctx: False
    try:
        tree = ast.parse(str(text), mode='eval').body
    except SyntaxError as e:
        raise RuleError('%s: bad rule %r (%s)' % (where, text, e))
    return _build(tree, '%s: %r' % (where, text))


def _name_value(name, ctx):
    if name == 'is_child':
        return ctx.age == 'child'
    if name == 'is_adult':
        return ctx.age == 'adult'
    if name == 'at_night':
        r = ctx.region
        return bool(r is not None and r.time_passes) or _can_play('SunsSong', ctx)
    if name in ctx.helpers:
        return ctx.helpers[name](ctx)
    if name in ctx.state.settings:
        return ctx.state.settings[name]
    return ctx.state.count(name)


def _can_play(song, ctx):
    return ctx.state.count(song) > 0 and (ctx.state.count('Ocarina') > 0 or ctx.state.count('OcarinaOfTime') > 0)


def _can_use(item, ctx):
    if not ctx.state.count(item):
        return False
    if item in ADULT_ONLY:
        return ctx.age == 'adult'
    if item in CHILD_ONLY:
        return ctx.age == 'child'
    return True


def _arg_name(node, where):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise RuleError('%s: expected a name' % where)


def _build(node, where):
    if isinstance(node, ast.BoolOp):
        parts = [_build(v, where) for v in node.values]
        if isinstance(node.op, ast.And):
            return lambda ctx: all(p(ctx) for p in parts)
        return lambda ctx: any(p(ctx) for p in parts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        inner = _build(node.operand, where)
        return lambda ctx: not inner(ctx)
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, str):                       # 'Event name' as a condition
            return lambda ctx: ctx.state.count(v)
        return lambda ctx: v
    if isinstance(node, ast.Name):
        n = node.id
        return lambda ctx: _name_value(n, ctx)
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left = _value(node.left, where)
        right = _value(node.comparators[0], where)
        op = node.ops[0]
        ops = {ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b, ast.Lt: lambda a, b: a < b,
               ast.LtE: lambda a, b: a <= b, ast.Gt: lambda a, b: a > b, ast.GtE: lambda a, b: a >= b}
        f = ops.get(type(op))
        if not f:
            raise RuleError('%s: unsupported comparison' % where)
        return lambda ctx: f(left(ctx), right(ctx))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn, args = node.func.id, node.args
        if fn == 'has':
            item = _arg_name(args[0], where)
            n = args[1].value if len(args) > 1 else 1
            return lambda ctx: ctx.state.count(item) >= n
        if fn == 'can_play':
            song = _arg_name(args[0], where)
            return lambda ctx: _can_play(song, ctx)
        if fn == 'can_use':
            item = _arg_name(args[0], where)
            return lambda ctx: _can_use(item, ctx)
        if fn == 'setting':
            name = _arg_name(args[0], where)
            return lambda ctx: ctx.state.settings.get(name)
        raise RuleError('%s: unknown function %s()' % (where, fn))
    raise RuleError('%s: unsupported expression %s' % (where, type(node).__name__))


def _value(node, where):
    """the value side of a comparison: a setting / count / number / string"""
    if isinstance(node, ast.Constant):
        v = node.value
        return lambda ctx: v
    if isinstance(node, ast.Name):
        n = node.id
        return lambda ctx: _name_value(n, ctx)
    return _build(node, where)


def names_in(text):
    """every bare name and quoted event in a rule (for checking the data files)"""
    if text in (True, False, None):
        return set()
    out = set()
    tree = ast.parse(str(text), mode='eval')
    funcs = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and id(n) not in funcs:
            out.add(n.id)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
    return out
