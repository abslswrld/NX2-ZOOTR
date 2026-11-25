"""Event flows (.bfevfl): reading into plain objects, and writing back.

Written from the public BFEVFL documentation (ZeldaMods wiki), checked against the remake's files
(version 0.4.0.0, little endian). The timeline part (cutscene files) is not in the public documentation for this
version; it was worked out from the remake's 261 timeline files and is written back byte for byte.

Model
    EventFlow(name, flowcharts, timelines)      a game file holds one flowchart or one timeline, never both
    Flowchart(name, actors, events, entry_points)
    Actor(name, secondary, argument, actions, queries, params, entry_point, cut)
    Event(name, type, ...)   type: 'action' | 'switch' | 'fork' | 'join' | 'subflow' | 'callswitch' | 'return'
        action : next, actor, action, params
        switch : actor, query, params, cases [(value, event index)]
        fork   : forks [event indexes], join
        join   : next
        subflow: next, params, flowchart, entry
      Two event types that the public documentation (Breath of the Wild) doesn't have; worked out from the
      remake's own files:
        callswitch (type 5): params, flowchart, entry, cases [(32-bit hash, event index)]
                   runs entry point `entry` of `flowchart` ('' = this file) and branches on the value it returns
        return     (type 6): value (32-bit hash), ends an entry point returning that value to a callswitch
      Event links (next, cases, forks, join, entry point main event) are event indexes; None = no event.
    EntryPoint(name, subflows, main, variables)
        variables: None, or a dict {name: value} of the entry point's own variables with their starting values
                   (whole numbers and True/False; 5 entry points in 3 files have one)
    Params: an ordered dict {key: value}; values are int, bool, float, str, Argument(str),
            WString(str), lists of those (IntArray/BoolArray/FloatArray/StrArray/WStrArray), ActorId(a, b),
            or a nested Params.

    Timeline(name, duration, actors, clips, triggers, subtimelines, cuts, oneshots, params)
        A cutscene's time track. Times are in frames, 60 a second (seconds() converts).
        duration     : length of the whole cutscene, in frames
        actors       : Actor, as in a flowchart (no queries, no entry point); `cut` is here the number of
                       tracks the actor's clips are laid on
        clips        : Clip(start, duration, actor, action, params, track): `actor` does `action` from frame
                       `start` for `duration` frames; clips of one actor on one track never overlap
        triggers     : [(clip index, 1 = the clip starts | 2 = the clip ends)], in time order (kept as read;
                       timeline_triggers() works them out again for a changed timeline)
        subtimelines : names of other timeline files run alongside (<name>_Effect, <name>_Env)
        cuts         : Cut(start, name, params): camera cuts, by the frame each starts at
        oneshots     : Oneshot(time, actor, action, params); no file of the game has one
    Links (actor, action) are indexes, as in a flowchart.

Adding to a flowchart (new steps, not only changed ones)
    fc.add_actor(name, secondary, params=...)                 -> actor index
    fc.action_index(actor, 'EventX', add=True)                -> index of the action on that actor (added if new)
    fc.query_index(actor, 'EventQueryX', add=True)
    fc.add_action(actor, action, params, next)                -> event index (one helper per event type:
    fc.add_switch / add_fork / add_join / add_subflow / add_callswitch / add_return)
    fc.add_entry_point(name, main)
    fc.repoint(old, new)                                      every link to event `old` now goes to `new`
    fc.update_entry_points()                                  entry point lists of subflow events, recomputed
    fc.check()                                                names unique, every index in range
    dumps_checked(flow)                                       writes, reads back, compares with what was meant
  New events, actors, actions and queries go at the end of their lists, so every existing index stays valid.
  `actor` is an index, a name, or (name, secondary name). Links are event indexes (None = no event).
"""
import struct

NONE16 = 0xFFFF
EVENT_TYPES = ('action', 'switch', 'fork', 'join', 'subflow', 'callswitch', 'return')


def return_hash(name):
    """The 32-bit value a `return` event gives back and a `callswitch` case matches: the FNV-1a hash of a
    name (found by trying: the game's values match 'Yes', 'No', 'Complete'...). A number is kept as it is."""
    if isinstance(name, int):
        return name
    h = 0x811C9DC5
    for c in name.encode('utf-8'):
        h = ((h ^ c) * 0x01000193) & 0xFFFFFFFF
    return h


def _flat(t):
    nxt, join, cases, forks = t
    return [nxt, join] + [ev for _, ev in cases] + list(forks)


def _check_params(bad, where, v, key=None):
    """parameter values the writer can't store as meant"""
    here = where if key is None else '%s, parameter %s' % (where, key)
    if v is None and key is None:
        return
    if key is None and not isinstance(v, Params):
        bad.append('%s: parameters must be an evfl.Params' % where)
        return
    try:
        t = _item_type(v)
    except TypeError as e:
        bad.append('%s: %s' % (here, e))
        return
    if t == 1:
        for k, x in v.items():
            if not isinstance(k, str):
                bad.append('%s: key %r is not text' % (here, k))
            _check_params(bad, where, x, k if key is None else '%s.%s' % (key, k))
    elif t in (2, 7):
        for x in ([v] if t == 2 else v):
            if not isinstance(x, int) or not -2 ** 31 <= x < 2 ** 31:
                bad.append('%s: %r does not fit a signed 32-bit number' % (here, x))
    elif t == 12 and len(v) != 2:
        bad.append('%s: an ActorId is (name, secondary name)' % here)
EVENT_SIZE = 0x30          # 0x28 in Breath of the Wild; this game adds one (so far always null) pointer


class Argument(str):
    """Container value of type 0: the name of an argument passed to the entry point."""


class WString(str):
    pass


class ActorId(tuple):
    pass


class IntArray(list):
    pass


class BoolArray(list):
    pass


class FloatArray(list):
    pass


class StrArray(list):
    pass


class WStrArray(list):
    pass


class Params(dict):
    pass


class Actor:
    def __init__(self, name, secondary='', argument='', actions=None, queries=None, params=None,
                 entry_point=None, cut=1):
        self.name, self.secondary, self.argument = name, secondary, argument
        self.actions = list(actions or [])
        self.queries = list(queries or [])
        self.params, self.entry_point, self.cut = params, entry_point, cut


class Event:
    def __init__(self, name, type, **kw):
        self.name, self.type = name, type
        self.next = kw.get('next')
        self.actor = kw.get('actor')
        self.action = kw.get('action')
        self.query = kw.get('query')
        self.params = kw.get('params')
        self.cases = list(kw.get('cases') or [])
        self.forks = list(kw.get('forks') or [])
        self.join = kw.get('join')
        self.flowchart = kw.get('flowchart', '')
        self.entry = kw.get('entry', '')
        self.value = kw.get('value', 0)


class EntryPoint:
    def __init__(self, name, main=None, subflows=None, variables=None):
        self.name, self.main = name, main
        self.subflows = list(subflows or [])
        self.variables = variables


class Flowchart:
    def __init__(self, name, actors=None, events=None, entry_points=None):
        self.name = name
        self.actors = list(actors or [])
        self.events = list(events or [])
        self.entry_points = list(entry_points or [])

    def event_index(self, name):
        for i, e in enumerate(self.events):
            if e.name == name:
                return i
        raise KeyError(name)

    # ------------------------------------------------------------------ adding
    def actor_index(self, actor):
        """index of an actor given as an index, a name, or (name, secondary name)"""
        if isinstance(actor, int):
            if not 0 <= actor < len(self.actors):
                raise IndexError('no actor %d' % actor)
            return actor
        name, secondary = (actor, None) if isinstance(actor, str) else actor
        hits = [i for i, a in enumerate(self.actors)
                if a.name == name and (secondary is None or (a.secondary or '') == secondary)]
        if not hits:
            raise KeyError('no actor %r' % (actor,))
        if len(hits) > 1:
            raise KeyError('%d actors named %r: give (name, secondary name)' % (len(hits), name))
        return hits[0]

    def add_actor(self, name, secondary='', argument='', params=None, actions=(), queries=(), entry_point=None,
                  cut=1):
        """a new actor, at the end; (name, secondary name) must be new. Returns its index."""
        if any(a.name == name and (a.secondary or '') == secondary for a in self.actors):
            raise ValueError('actor %r / %r is already in %s' % (name, secondary, self.name))
        self.actors.append(Actor(name, secondary, argument, actions, queries, params, entry_point, cut))
        return len(self.actors) - 1

    def _slot(self, actor, kind, name, add):
        a = self.actors[self.actor_index(actor)]
        names = getattr(a, kind)
        if name in names:
            return names.index(name)
        if not add:
            raise KeyError('actor %r has no %r in its %s' % (a.name, name, kind))
        names.append(name)
        return len(names) - 1

    def action_index(self, actor, action, add=False):
        """index of an action in the actor's list; add=True adds it at the end when it isn't there"""
        return self._slot(actor, 'actions', action, add)

    def query_index(self, actor, query, add=False):
        return self._slot(actor, 'queries', query, add)

    def new_event_name(self, prefix='Event'):
        """a name no event has yet: prefix + the first free number (the game's own are Event0, Event1...)"""
        used = {e.name for e in self.events}
        n = len(self.events)
        while '%s%d' % (prefix, n) in used:
            n += 1
        return '%s%d' % (prefix, n)

    def add_event(self, event):
        """a ready-made Event, at the end; its name must be new (None: one is made up). Returns its index."""
        if event.name is None:
            event.name = self.new_event_name()
        if any(e.name == event.name for e in self.events):
            raise ValueError('event %r is already in %s' % (event.name, self.name))
        if len(self.events) >= NONE16:
            raise ValueError('too many events')
        self.events.append(event)
        return len(self.events) - 1

    def add_action(self, actor, action, params=None, next=None, name=None):
        """`actor` does `action` (added to the actor when new), then goes to `next`"""
        a = self.actor_index(actor)
        return self.add_event(Event(name, 'action', actor=a, action=self.action_index(a, action, add=True),
                                    params=params, next=next))

    def add_switch(self, actor, query, cases, params=None, name=None):
        """asks `actor` the `query` (added when new) and goes to the event of the matching (value, event) case"""
        a = self.actor_index(actor)
        return self.add_event(Event(name, 'switch', actor=a, query=self.query_index(a, query, add=True),
                                    params=params, cases=cases))

    def add_fork(self, forks, join, name=None):
        """runs the branches starting at the `forks` events side by side; all end at the join event `join`"""
        return self.add_event(Event(name, 'fork', forks=forks, join=join))

    def add_join(self, next=None, name=None):
        return self.add_event(Event(name, 'join', next=next))

    def add_subflow(self, flowchart, entry, params=None, next=None, name=None):
        """runs entry point `entry` of `flowchart` ('' = this file), then goes to `next`"""
        return self.add_event(Event(name, 'subflow', flowchart=flowchart, entry=entry, params=params, next=next))

    def add_callswitch(self, flowchart, entry, cases, params=None, name=None):
        """runs entry point `entry` of `flowchart` ('' = this file) and branches on what it returns;
        case values are 32-bit hashes or names (hashed with return_hash)"""
        return self.add_event(Event(name, 'callswitch', flowchart=flowchart, entry=entry, params=params,
                                    cases=[(return_hash(v), ev) for v, ev in cases]))

    def add_return(self, value, name=None):
        """ends the entry point, returning `value` (a 32-bit hash, or a name) to the callswitch that ran it"""
        return self.add_event(Event(name, 'return', value=return_hash(value)))

    def entry_point(self, name):
        for ep in self.entry_points:
            if ep.name == name:
                return ep
        raise KeyError(name)

    def add_entry_point(self, name, main, subflows=None):
        """a new entry point starting at event `main`; its list of subflow events is worked out when not given"""
        if any(ep.name == name for ep in self.entry_points):
            raise ValueError('entry point %r is already in %s' % (name, self.name))
        ep = EntryPoint(name, main, subflows)
        self.entry_points.append(ep)
        if subflows is None:
            ep.subflows = self._subflows_from(main)
        return ep

    def links(self, i):
        """every event index event `i` points at"""
        e = self.events[i]
        return [x for x in _flat((e.next, e.join, e.cases, e.forks)) if x is not None]

    def links_to(self, i):
        """indexes of the events pointing at event `i`"""
        return [k for k in range(len(self.events)) if i in self.links(k)]

    def repoint(self, old, new, keep=()):
        """every link to event `old` (next, cases, forks, join, entry point start) now goes to `new`, but
        for the events whose indexes are in `keep` (the new steps that must still reach `old`).
        Returns how many links changed."""
        n = 0
        sw = lambda v: new if v == old else v
        for i, e in enumerate(self.events):
            if i in keep:
                continue
            before = _flat((e.next, e.join, e.cases, e.forks))
            e.next, e.join = sw(e.next), sw(e.join)
            e.forks = [sw(f) for f in e.forks]
            e.cases = [(v, sw(ev)) for v, ev in e.cases]
            n += sum(1 for a, b in zip(before, _flat((e.next, e.join, e.cases, e.forks))) if a != b)
        for ep in self.entry_points:
            if ep.main == old:
                ep.main = new
                n += 1
        return n

    def reachable(self, start):
        """indexes of the events that can run from event `start`, in the order found"""
        seen, mark = [], set()
        todo = [] if start is None else [start]
        while todo:
            i = todo.pop(0)
            if i in mark:
                continue
            mark.add(i)
            seen.append(i)
            todo += self.links(i)
        return seen

    def _subflows_from(self, main):
        return [i for i in self.reachable(main) if self.events[i].type in ('subflow', 'callswitch')]

    def update_entry_points(self):
        """Each entry point lists the subflow and callswitch events that can run from it (true of every
        entry point in the game's files). After adding or repointing events: the lists are worked out again,
        keeping the order they had and putting newly reached events at the end."""
        for ep in self.entry_points:
            want = self._subflows_from(ep.main)
            keep = [i for i in ep.subflows if i in want]
            ep.subflows = keep + [i for i in want if i not in keep]

    def check(self):
        """raises ValueError when the flowchart can't be written as meant: names not unique, an index out of
        range, a fork without a join..."""
        bad = []
        ne = len(self.events)

        def dup(what, names):
            seen = set()
            for n in names:
                if n in seen:
                    bad.append('%s %r is there twice' % (what, n))
                seen.add(n)

        dup('event', [e.name for e in self.events])
        dup('actor', [(a.name, a.secondary or '') for a in self.actors])
        dup('entry point', [ep.name for ep in self.entry_points])
        for a in self.actors:
            dup('action of %s' % a.name, a.actions)
            dup('query of %s' % a.name, a.queries)
            if a.entry_point is not None and not 0 <= a.entry_point < len(self.entry_points):
                bad.append('actor %s: no entry point %r' % (a.name, a.entry_point))
            _check_params(bad, 'actor %s' % a.name, a.params)

        def link(e, what, v, none_ok=True):
            if v is None:
                if not none_ok:
                    bad.append('event %s: %s is missing' % (e.name, what))
            elif not isinstance(v, int) or isinstance(v, bool) or not 0 <= v < ne:
                bad.append('event %s: %s points at event %r, there are %d' % (e.name, what, v, ne))

        for e in self.events:
            if not isinstance(e.name, str) or not e.name:
                bad.append('an event has no name')
            if e.type not in EVENT_TYPES:
                bad.append('event %s: unknown type %r' % (e.name, e.type))
                continue
            if e.type in ('action', 'switch'):
                kind, idx = ('actions', e.action) if e.type == 'action' else ('queries', e.query)
                if not isinstance(e.actor, int) or not 0 <= e.actor < len(self.actors):
                    bad.append('event %s: no actor %r' % (e.name, e.actor))
                elif not isinstance(idx, int) or not 0 <= idx < len(getattr(self.actors[e.actor], kind)):
                    bad.append('event %s: actor %s has no %s number %r'
                               % (e.name, self.actors[e.actor].name, kind, idx))
            if e.type in ('action', 'join', 'subflow'):
                link(e, 'next', e.next)
            if e.type in ('switch', 'callswitch'):
                for v, ev in e.cases:
                    link(e, 'case %r' % (v,), ev, none_ok=False)
                    if not isinstance(v, int) or not 0 <= v <= 0xFFFFFFFF:
                        bad.append('event %s: case value %r is not a 32-bit number' % (e.name, v))
            if e.type == 'fork':
                for f in e.forks:
                    link(e, 'fork', f, none_ok=False)
                link(e, 'join', e.join, none_ok=False)
                if isinstance(e.join, int) and 0 <= e.join < ne and self.events[e.join].type != 'join':
                    bad.append('event %s: its join, event %s, is not a join' % (e.name, self.events[e.join].name))
            if e.type == 'return' and not (isinstance(e.value, int) and 0 <= e.value <= 0xFFFFFFFF):
                bad.append('event %s: return value %r is not a 32-bit number' % (e.name, e.value))
            if e.type in ('action', 'switch', 'subflow', 'callswitch'):
                _check_params(bad, 'event %s' % e.name, e.params)
        for ep in self.entry_points:
            for what, v in [('start', ep.main)] + [('subflow list', s) for s in ep.subflows]:
                if v is not None and not (isinstance(v, int) and 0 <= v < ne):
                    bad.append('entry point %s: %s points at event %r, there are %d' % (ep.name, what, v, ne))
            for vn, v in (ep.variables or {}).items():
                if not isinstance(v, int) or not -2 ** 31 <= v < 2 ** 31:
                    bad.append('entry point %s: variable %s must be a whole number or True/False' % (ep.name, vn))
        if bad:
            raise ValueError('%s: %s' % (self.name, '; '.join(bad[:10])
                                         + ('; and %d more' % (len(bad) - 10) if len(bad) > 10 else '')))


FPS = 60.0


def seconds(frames):
    """timeline frames as seconds: the timelines count 60 frames a second (the game's movie cutscenes have a
    timeline as long as their video file: Dm_Kokiri_0095 is 7040 frames, its video 117.33 s)"""
    return frames / FPS


class Clip:
    def __init__(self, start, duration, actor, action, params=None, track=0):
        self.start, self.duration, self.actor, self.action = start, duration, actor, action
        self.params, self.track = params, track

    @property
    def end(self):
        return self.start + self.duration


class Oneshot:
    def __init__(self, time, actor, action, params=None):
        self.time, self.actor, self.action, self.params = time, actor, action, params


class Cut:
    def __init__(self, start, name, params=None):
        self.start, self.name, self.params = start, name, params


class Timeline:
    def __init__(self, name, duration=0.0, actors=None, clips=None, triggers=None, subtimelines=None,
                 cuts=None, oneshots=None, params=None):
        self.name, self.duration, self.params = name, duration, params
        self.actors = list(actors or [])
        self.clips = list(clips or [])
        self.triggers = list(triggers or [])
        self.subtimelines = list(subtimelines or [])
        self.cuts = list(cuts or [])
        self.oneshots = list(oneshots or [])

    def clip_names(self, clip):
        """(actor name, action name) of a clip"""
        a = self.actors[clip.actor]
        return a.name, a.actions[clip.action]

    def check(self):
        """raises ValueError when the timeline can't be written as meant"""
        bad = []
        for i, c in enumerate(list(self.clips) + list(self.oneshots)):
            if not isinstance(c.actor, int) or not 0 <= c.actor < len(self.actors):
                bad.append('clip %d: no actor %r' % (i, c.actor))
            elif not isinstance(c.action, int) or not 0 <= c.action < len(self.actors[c.actor].actions):
                bad.append('clip %d: actor %s has no action number %r' % (i, self.actors[c.actor].name, c.action))
            _check_params(bad, 'clip %d' % i, c.params)
        for a in self.actors:
            _check_params(bad, 'actor %s' % a.name, a.params)
        for c, t in self.triggers:
            if not 0 <= c < len(self.clips) or t not in (1, 2):
                bad.append('trigger (%r, %r)' % (c, t))
        if bad:
            raise ValueError('%s: %s' % (self.name, '; '.join(bad[:10])))


def timeline_triggers(tl):
    """The trigger list of a timeline, worked out from its clips: every clip's start (1) and end (2) in time
    order; at the same frame the ends come before the starts, each by clip number. (This gives the list of
    every one of the game's 261 timeline files.)"""
    out = [(c.start, 1, i, 1) for i, c in enumerate(tl.clips)] + [(c.end, 0, i, 2) for i, c in enumerate(tl.clips)]
    return [(i, t) for _, _, i, t in sorted(out)]


class EventFlow:
    def __init__(self, name, flowcharts=None, timelines=None):
        self.name = name
        self.flowcharts = list(flowcharts or [])
        self.timelines = list(timelines or [])
        self.version = (0, 4, 0, 0)
        self.string_order = []          # pool order of the file read (kept so unchanged files rewrite identically)

    @property
    def flowchart(self):
        return self.flowcharts[0]

    @property
    def timeline(self):
        return self.timelines[0]


# ============================================================================ reading
class _Reader:
    def __init__(self, data):
        self.d = data

    def u8(self, o):
        return self.d[o]

    def u16(self, o):
        return struct.unpack_from('<H', self.d, o)[0]

    def u32(self, o):
        return struct.unpack_from('<I', self.d, o)[0]

    def s32(self, o):
        return struct.unpack_from('<i', self.d, o)[0]

    def ptr(self, o):
        return struct.unpack_from('<Q', self.d, o)[0]

    def pstr(self, p):
        if not p:
            return None
        n = self.u16(p)
        return self.d[p + 2:p + 2 + n].decode('utf-8')

    def dic_names(self, p):
        """names of a DIC, in entry order (entry 1..count)"""
        n = self.u32(p + 4)
        return [self.pstr(self.ptr(p + 0x18 + 0x10 * i + 8)) for i in range(n)]


def _read_params(r, p):
    if not p:
        return None
    t, n = r.u8(p), r.u16(p + 2)
    if t != 1:
        raise ValueError('parameter root is not a container')
    return _read_item(r, p)


def _read_item(r, p):
    t, n = r.u8(p), r.u16(p + 2)
    v = p + 0x10
    if t == 0:
        return Argument(r.pstr(r.ptr(v)))
    if t == 1:
        keys = r.dic_names(r.ptr(p + 8))
        out = Params()
        for i, k in enumerate(keys):
            out[k] = _read_item(r, r.ptr(v + 8 * i))
        return out
    if t == 2:
        return r.s32(v)
    if t == 3:
        return r.u32(v) == 0x80000001
    if t == 4:
        return struct.unpack_from('<f', r.d, v)[0]
    if t == 5:
        return r.pstr(r.ptr(v))
    if t == 6:
        return WString(_read_wstr(r, r.ptr(v)))
    if t == 7:
        return IntArray(struct.unpack_from('<%di' % n, r.d, v))
    if t == 8:
        return BoolArray(r.u32(v + 4 * i) == 0x80000001 for i in range(n))
    if t == 9:
        return FloatArray(struct.unpack_from('<%df' % n, r.d, v))
    if t == 10:
        return StrArray(r.pstr(r.ptr(v + 8 * i)) for i in range(n))
    if t == 11:
        return WStrArray(_read_wstr(r, r.ptr(v + 8 * i)) for i in range(n))
    if t == 12:
        return ActorId((r.pstr(r.ptr(v)), r.pstr(r.ptr(v + 8))))
    raise ValueError('unknown container type %d' % t)


def _read_wstr(r, p):
    n = r.u16(p)
    return r.d[p + 2:p + 2 + 4 * n].decode('utf-32-le')


def loads(data):
    data = bytes(data)
    if data[:8] != b'BFEVFL\0\0':
        raise ValueError('not a BFEVFL file')
    r = _Reader(data)
    nflow, ntime = r.u16(0x20), r.u16(0x22)
    fname = data[r.u32(0x10):data.index(b'\0', r.u32(0x10))].decode('utf-8')
    flow = EventFlow(fname)
    flow.version = tuple(data[8:12])
    arr = r.ptr(0x28)
    for i in range(nflow):
        flow.flowcharts.append(_read_flowchart(r, r.ptr(arr + 8 * i)))
    tarr = r.ptr(0x38)
    for i in range(ntime):
        flow.timelines.append(_read_timeline(r, r.ptr(tarr + 8 * i)))
    # string pool order
    pool = None
    for fc_off in [r.ptr(arr + 8 * i) for i in range(nflow)] + [r.ptr(tarr + 8 * i) for i in range(ntime)]:
        pool = fc_off + r.u32(fc_off + 4)
    if pool is not None and data[pool:pool + 4] == b'STR ':
        count = r.u32(pool + 0x10) + 1          # the count leaves out the empty string that starts the pool
        p = pool + 0x14
        for _ in range(count):
            n = r.u16(p)
            flow.string_order.append(data[p + 2:p + 2 + n].decode('utf-8'))
            p += 2 + n + 1
            p += p & 1
    return flow


def _read_actors(r, ap, nact):
    out = []
    for i in range(nact):
        a = ap + 0x38 * i
        na, nq = r.u16(a + 0x30), r.u16(a + 0x32)
        acts = [r.pstr(r.ptr(r.ptr(a + 0x18) + 8 * k)) for k in range(na)]
        qs = [r.pstr(r.ptr(r.ptr(a + 0x20) + 8 * k)) for k in range(nq)]
        epi = r.u16(a + 0x34)
        out.append(Actor(r.pstr(r.ptr(a)), r.pstr(r.ptr(a + 8)), r.pstr(r.ptr(a + 0x10)), acts, qs,
                         _read_params(r, r.ptr(a + 0x28)), None if epi == NONE16 else epi, r.u8(a + 0x36)))
    return out


def _read_timeline(r, p):
    """TLIN block (0x60 bytes): 'TLIN', u32 offset to the string pool, 8 zero bytes, float duration, u16 counts
    (actors, actions, clips, oneshots, subtimelines, cuts), then 8 pointers: name, actors, clips, oneshots,
    triggers, subtimelines, cuts, parameters."""
    if r.d[p:p + 4] != b'TLIN':
        raise ValueError('bad timeline')
    f32 = lambda o: struct.unpack_from('<f', r.d, o)[0]
    nact, _nacts, nclip, nos, nsub, ncut = (r.u16(p + 0x14 + 2 * i) for i in range(6))
    name, ap, cp, op, tp, sp, kp, pp = (r.ptr(p + 0x20 + 8 * i) for i in range(8))
    tl = Timeline(r.pstr(name), f32(p + 0x10), params=_read_params(r, pp))
    tl.actors = _read_actors(r, ap, nact)
    for i in range(nclip):                      # 0x18: float start, float duration, u16 actor, u16 action,
        c = cp + 0x18 * i                       #       u8 track, 3 zero bytes, pointer to parameters
        if r.d[c + 0xD:c + 0x10] != bytes(3):
            raise ValueError('clip %d: unknown bytes' % i)
        tl.clips.append(Clip(f32(c), f32(c + 4), r.u16(c + 8), r.u16(c + 0xA), _read_params(r, r.ptr(c + 0x10)),
                             r.u8(c + 0xC)))
    for i in range(nos):                        # 0x10 (as in the public documentation; no file has one)
        c = op + 0x10 * i
        tl.oneshots.append(Oneshot(f32(c), r.u16(c + 4), r.u16(c + 6), _read_params(r, r.ptr(c + 8))))
    for i in range(2 * nclip if tp else 0):     # 4: u16 clip, u8 type (1 start, 2 end), u8 zero
        t = tp + 4 * i
        if r.u8(t + 3):
            raise ValueError('trigger %d: unknown byte' % i)
        tl.triggers.append((r.u16(t), r.u8(t + 2)))
    tl.subtimelines = [r.pstr(r.ptr(sp + 8 * i)) for i in range(nsub)]
    for i in range(ncut):                       # 0x18: float start, u32 zero, name, parameters
        c = kp + 0x18 * i
        if r.u32(c + 4):
            raise ValueError('cut %d: unknown bytes' % i)
        tl.cuts.append(Cut(f32(c), r.pstr(r.ptr(c + 8)), _read_params(r, r.ptr(c + 0x10))))
    return tl


def _read_flowchart(r, p):
    if r.d[p:p + 4] != b'EVFL':
        raise ValueError('bad flowchart')
    nact, _nacts, _nq, nev, nep = (r.u16(p + 0x10 + 2 * i) for i in range(5))
    fc = Flowchart(r.pstr(r.ptr(p + 0x20)))
    ap, ep, dp, epp = r.ptr(p + 0x28), r.ptr(p + 0x30), r.ptr(p + 0x38), r.ptr(p + 0x40)
    fc.actors = _read_actors(r, ap, nact)
    for i in range(nev):
        e = ep + EVENT_SIZE * i
        name, t = r.pstr(r.ptr(e)), r.u8(e + 8)
        f0a, f0c, f0e = r.u16(e + 0xA), r.u16(e + 0xC), r.u16(e + 0xE)
        p10, p18, p20 = r.ptr(e + 0x10), r.ptr(e + 0x18), r.ptr(e + 0x20)
        nx = lambda v: None if v == NONE16 else v
        if t == 0:
            ev = Event(name, 'action', next=nx(f0a), actor=f0c, action=f0e, params=_read_params(r, p10))
        elif t == 1:
            cases = [(r.u32(p18 + 8 * k), r.u16(p18 + 8 * k + 4)) for k in range(f0a)]
            ev = Event(name, 'switch', actor=f0c, query=f0e, params=_read_params(r, p10), cases=cases)
        elif t == 2:
            ev = Event(name, 'fork', join=f0c, forks=[r.u16(p10 + 2 * k) for k in range(f0a)])
        elif t == 3:
            ev = Event(name, 'join', next=nx(f0a))
        elif t == 4:
            ev = Event(name, 'subflow', next=nx(f0a), params=_read_params(r, p10),
                       flowchart=r.pstr(p18) or '', entry=r.pstr(p20) or '')
        elif t == 5:
            cases = [(r.u32(p18 + 8 * k), r.u16(p18 + 8 * k + 4)) for k in range(f0a)]
            ev = Event(name, 'callswitch', params=_read_params(r, p10), cases=cases,
                       flowchart=r.pstr(p20) or '', entry=r.pstr(r.ptr(e + 0x28)) or '')
        elif t == 6:
            ev = Event(name, 'return', value=r.u32(e + 0xC))
        else:
            raise ValueError('unknown event type %d' % t)
        fc.events.append(ev)
    names = r.dic_names(dp)
    for i, n in enumerate(names):
        e = epp + 0x20 * i
        nsub, nvar = r.u16(e + 0x18), r.u16(e + 0x1A)
        variables = None
        if nvar:
            # a DIC of names and, per variable, 0x10 bytes: value (8 bytes), u16 count (1), u16 type
            # (2 number, 3 true/false, stored as 1 / 0), u32 zero
            variables = {}
            vd = r.ptr(e + 0x10)
            for k, vn in enumerate(r.dic_names(r.ptr(e + 8))):
                v = vd + 0x10 * k
                count, t = r.u16(v + 8), r.u16(v + 0xA)
                if count != 1 or t not in (2, 3) or r.u32(v + 4) or r.u32(v + 0xC) or (t == 3 and r.u32(v) > 1):
                    raise ValueError('entry point %s: unknown kind of variable %r' % (n, vn))
                variables[vn] = r.s32(v) if t == 2 else bool(r.u32(v))
        main = r.u16(e + 0x1C)
        fc.entry_points.append(EntryPoint(n, None if main == NONE16 else main,
                                          [r.u16(r.ptr(e) + 2 * k) for k in range(nsub)], variables))
    return fc


# ============================================================================ writing
def _dic_bit(name, n):
    b = name.encode('utf-8')
    i = n >> 3
    if i >= len(b):
        return 0
    return (b[len(b) - 1 - i] >> (n & 7)) & 1


def _dic_tree(names):
    """Radix tree entries for a DIC: [(bit index, left, right, name)], root first."""
    nodes = [[0xFFFFFFFF, 0, 0, '']]

    def ref(i):
        r = nodes[i][0]
        return -1 if r == 0xFFFFFFFF else r

    def child(i, name):
        if i == 0:
            return nodes[0][1]
        return nodes[i][2] if _dic_bit(name, nodes[i][0]) else nodes[i][1]

    for name in names:
        idx = len(nodes)
        p, n = 0, nodes[0][1]
        while ref(n) > ref(p):
            p, n = n, child(n, name)
        other = nodes[n][3]
        maxbits = max(len(name.encode('utf-8')), len(other.encode('utf-8'))) * 8
        diff = next((i for i in range(maxbits) if _dic_bit(name, i) != _dic_bit(other, i)), None)
        if diff is None:
            raise ValueError('duplicate name in dictionary: %r' % name)
        p, n = 0, nodes[0][1]
        while ref(n) > ref(p) and ref(n) < diff:
            p, n = n, child(n, name)
        new = [diff, 0, 0, name]
        if _dic_bit(name, diff):
            new[1], new[2] = n, idx
        else:
            new[1], new[2] = idx, n
        nodes.append(new)
        if p == 0:
            nodes[0][1] = idx
        elif _dic_bit(name, nodes[p][0]):
            nodes[p][2] = idx
        else:
            nodes[p][1] = idx
    return nodes


class _Out:
    """Output buffer with 64-bit pointer slots resolved at the end (and listed for the RELT)."""

    def __init__(self):
        self.b = bytearray()
        self.fix = []                 # (slot offset, target key)
        self.addr = {}                # key -> address
        self.str_slots = []           # (slot offset, string, +2 if it must point at the characters)
        self.null_slots = []          # null pointers the game's files still list in the RELT

    def tell(self):
        return len(self.b)

    def align(self, a):
        self.b += b'\0' * (-len(self.b) & (a - 1))

    def u8(self, v):
        self.b += struct.pack('<B', v)

    def u16(self, v):
        self.b += struct.pack('<H', v)

    def u32(self, v):
        self.b += struct.pack('<I', v)

    def ptr(self, key, listed=False):
        """pointer to an object written later (key) or None for null; listed: a null pointer that still
        goes in the relocation table (as in the game's files)"""
        if key is not None:
            self.fix.append((len(self.b), key))
        elif listed:
            self.null_slots.append(len(self.b))
        self.b += b'\0' * 8

    def sptr(self, s):
        """pointer to a pooled string"""
        if s is None:
            self.b += b'\0' * 8
            return
        self.str_slots.append((len(self.b), s))
        self.b += b'\0' * 8

    def mark(self, key):
        self.addr[key] = len(self.b)


def _write_dic(o, key, names):
    o.align(8)
    o.mark(key)
    nodes = _dic_tree(names)
    o.b += b'DIC '
    o.u32(len(names))
    for ref, left, right, name in nodes:
        o.u32(ref)
        o.u16(left)
        o.u16(right)
        o.sptr(name)


_TYPE_ID = {Argument: 0, Params: 1, WString: 6, IntArray: 7, BoolArray: 8, FloatArray: 9, StrArray: 10,
            WStrArray: 11, ActorId: 12}


def _item_type(v):
    for cls, t in _TYPE_ID.items():
        if isinstance(v, cls):
            return t
    if isinstance(v, bool):
        return 3
    if isinstance(v, int):
        return 2
    if isinstance(v, float):
        return 4
    if isinstance(v, str):
        return 5
    raise TypeError('cannot store %r in event flow parameters' % type(v))


def _inline_str(o, s, wide=False):
    """an inline (unpooled) string right here: u16 length, characters, terminator"""
    if wide:
        o.u16(len(s))
        o.b += s.encode('utf-32-le') + b'\0' * 4
    else:
        raw = s.encode('utf-8')
        o.u16(len(raw))
        o.b += raw + b'\0'


def _write_item(o, key, v):
    t = _item_type(v)
    o.align(8)
    o.mark(key)
    if t == 1:
        keys = list(v.keys())
        o.u8(1); o.u8(0); o.u16(len(keys)); o.u32(0)
        o.ptr((key, 'dic'))
        for i in range(len(keys)):
            o.ptr((key, i))
        _write_dic(o, (key, 'dic'), keys)
        for i, k in enumerate(keys):
            _write_item(o, (key, i), v[k])
        return
    n = len(v) if t in (7, 8, 9, 10, 11) else (2 if t == 12 else 1)
    o.u8(t); o.u8(0); o.u16(n); o.u32(0)
    o.ptr(None)
    if t == 2:
        o.b += struct.pack('<i', v)
    elif t == 3:
        o.u32(0x80000001 if v else 0)
    elif t == 4:
        o.b += struct.pack('<f', v)
    elif t == 7:
        o.b += struct.pack('<%di' % n, *v)
    elif t == 8:
        for x in v:
            o.u32(0x80000001 if x else 0)
    elif t == 9:
        o.b += struct.pack('<%df' % n, *v)
    elif t in (0, 5, 6):
        o.ptr((key, 's'))
        o.mark((key, 's'))
        _inline_str(o, v, t == 6)
    elif t in (10, 11, 12):
        vals = list(v)
        for i in range(len(vals)):
            o.ptr((key, 's', i))
        for i, x in enumerate(vals):
            o.align(2)
            o.mark((key, 's', i))
            _inline_str(o, x, t == 11)


def _write_params(o, key, params):
    if params is not None:
        _write_item(o, key, params)


def dumps(flow):
    o = _Out()
    fcs, tls = flow.flowcharts, flow.timelines
    # file header (0x48)
    o.b += b'BFEVFL\0\0' + bytes(flow.version)
    o.u16(0xFEFF)
    o.u8(3); o.u8(0)
    o.u32(0)                                  # file name, set later
    o.u16(0)
    o.u16(0)                                  # first block, set later
    o.u32(0)                                  # RELT, set later
    o.u32(0)                                  # file size, set later
    o.u16(len(fcs)); o.u16(len(tls)); o.u32(0)
    o.ptr('fc_array' if fcs else None, listed=True)
    o.ptr('fc_dic')
    o.ptr('tl_array' if tls else None, listed=True)
    o.ptr('tl_dic')
    if fcs:
        o.mark('fc_array')
        for i in range(len(fcs)):
            o.ptr(('fc', i))
    _write_dic(o, 'fc_dic', [fc.name for fc in fcs])
    if tls:
        o.mark('tl_array')
        for i in range(len(tls)):
            o.ptr(('tl', i))
    _write_dic(o, 'tl_dic', [tl.name for tl in tls])
    first_block = None
    for i, fc in enumerate(fcs):
        o.align(8)
        if first_block is None:
            first_block = o.tell()
        _write_flowchart(o, ('fc', i), fc)
    for i, tl in enumerate(tls):
        _write_actor_data(o, ('tl', i), tl.actors)        # a timeline's actor data comes before its block
        o.align(8)
        if first_block is None:
            first_block = o.tell()
        _write_timeline(o, ('tl', i), tl)
    # string pool
    o.align(8)
    pool = o.tell()
    for key in [('fc', i) for i in range(len(fcs))] + [('tl', i) for i in range(len(tls))]:
        struct.pack_into('<I', o.b, o.addr[key] + 4, pool - o.addr[key])
    o.b += b'STR ' + b'\0' * 12
    used = []
    seen = set()
    for _, s in o.str_slots:
        if s not in seen:
            seen.add(s)
            used.append(s)
    seen.add('')
    order = [s for s in flow.string_order if s in seen]
    known = set(order)
    order += [s for s in used if s not in known]
    if order[0] != '':
        order.remove('')
        order.insert(0, '')
    o.u32(len(order) - 1)
    saddr = {}
    for s in order:
        o.align(2)
        saddr[s] = o.tell()
        _inline_str(o, s)
    o.align(2)
    data_end = o.tell()
    # resolve pointers
    slots = list(o.null_slots)
    for off, key in o.fix:
        struct.pack_into('<Q', o.b, off, o.addr[key])
        slots.append(off)
    for off, s in o.str_slots:
        struct.pack_into('<Q', o.b, off, saddr[s])
        slots.append(off)
    # relocation table
    o.align(8)
    rt = o.tell()
    slots.sort()
    entries = []
    i = 0
    while i < len(slots):
        base = slots[i]
        mask = 0
        while i < len(slots) and slots[i] < base + 32 * 8:
            mask |= 1 << ((slots[i] - base) // 8)
            i += 1
        entries.append((base, mask))
    o.b += b'RELT'
    o.u32(rt)
    o.u32(1)
    o.u32(0)
    o.b += b'\0' * 8
    o.u32(0)
    o.u32(data_end)
    o.u32(0)
    o.u32(len(entries))
    for base, mask in entries:
        o.u32(base)
        o.u32(mask)
    size = o.tell()
    name_addr = saddr[flow.name] + 2 if flow.name in saddr else 0
    struct.pack_into('<IHHII', o.b, 0x10, name_addr, 0, first_block or 0, rt, size)
    return bytes(o.b)


def _write_actors(o, key, actors):
    o.mark((key, 'actors'))
    for i, a in enumerate(actors):
        k = (key, 'actor', i)
        o.sptr(a.name)
        o.sptr(a.secondary)
        o.sptr(a.argument)
        o.ptr((k, 'actions') if a.actions else None, listed=True)
        o.ptr((k, 'queries') if a.queries else None, listed=True)
        o.ptr((k, 'params') if a.params is not None else None)
        o.u16(len(a.actions)); o.u16(len(a.queries))
        o.u16(NONE16 if a.entry_point is None else a.entry_point)
        o.u8(a.cut); o.u8(0)


def _write_actor_data(o, key, actors):
    """actor data: parameters, then action and query name arrays"""
    for i, a in enumerate(actors):
        k = (key, 'actor', i)
        _write_params(o, (k, 'params'), a.params)
        if a.actions:
            o.align(8)
            o.mark((k, 'actions'))
            for n in a.actions:
                o.sptr(n)
        if a.queries:
            o.align(8)
            o.mark((k, 'queries'))
            for n in a.queries:
                o.sptr(n)


def _write_timeline(o, key, tl):
    o.mark(key)
    o.b += b'TLIN'
    o.u32(0)                                  # string pool offset, set later
    o.u32(0); o.u32(0)
    o.b += struct.pack('<f', tl.duration)
    for v in (len(tl.actors), sum(len(a.actions) for a in tl.actors), len(tl.clips), len(tl.oneshots),
              len(tl.subtimelines), len(tl.cuts)):
        o.u16(v)
    o.sptr(tl.name)
    # empty arrays: the null pointer is still listed in the RELT (as in the game's files)
    o.ptr((key, 'actors') if tl.actors else None, listed=True)
    o.ptr((key, 'clips') if tl.clips else None, listed=True)
    o.ptr((key, 'oneshots') if tl.oneshots else None, listed=True)
    o.ptr((key, 'triggers') if tl.triggers else None, listed=True)
    o.ptr((key, 'subs') if tl.subtimelines else None, listed=True)
    o.ptr((key, 'cuts') if tl.cuts else None, listed=True)
    o.ptr((key, 'params') if tl.params is not None else None)
    _write_actors(o, key, tl.actors)
    o.mark((key, 'clips'))
    for i, c in enumerate(tl.clips):
        o.b += struct.pack('<ffHHBxxx', c.start, c.duration, c.actor, c.action, c.track)
        o.ptr((key, 'clip', i) if c.params is not None else None)
    o.mark((key, 'oneshots'))
    for i, c in enumerate(tl.oneshots):
        o.b += struct.pack('<fHH', c.time, c.actor, c.action)
        o.ptr((key, 'oneshot', i) if c.params is not None else None)
    o.mark((key, 'subs'))
    for n in tl.subtimelines:
        o.sptr(n)
    o.mark((key, 'triggers'))
    for c, t in tl.triggers:
        o.b += struct.pack('<HBx', c, t)
    o.align(8)
    o.mark((key, 'cuts'))
    for i, c in enumerate(tl.cuts):
        o.b += struct.pack('<fI', c.start, 0)
        o.sptr(c.name)
        o.ptr((key, 'cut', i) if c.params is not None else None)
    for i, c in enumerate(tl.clips):
        _write_params(o, (key, 'clip', i), c.params)
    for i, c in enumerate(tl.oneshots):
        _write_params(o, (key, 'oneshot', i), c.params)
    for i, c in enumerate(tl.cuts):
        _write_params(o, (key, 'cut', i), c.params)
    _write_params(o, (key, 'params'), tl.params)


def _write_flowchart(o, key, fc):
    o.mark(key)
    nacts = sum(len(a.actions) for a in fc.actors)
    nq = sum(len(a.queries) for a in fc.actors)
    o.b += b'EVFL'
    o.u32(0)                                  # string pool offset, set later
    o.u32(0); o.u32(0)
    for v in (len(fc.actors), nacts, nq, len(fc.events), len(fc.entry_points), 0, 0, 0):
        o.u16(v)
    o.sptr(fc.name)
    # empty arrays: the null pointer is still listed in the RELT (as in the game's files)
    o.ptr((key, 'actors') if fc.actors else None, listed=True)
    o.ptr((key, 'events') if fc.events else None, listed=True)
    o.ptr((key, 'epdic'))
    o.ptr((key, 'eps') if fc.entry_points else None, listed=True)
    _write_actors(o, key, fc.actors)
    # events
    nx = lambda v: NONE16 if v is None else v
    o.mark((key, 'events'))
    for i, e in enumerate(fc.events):
        k = (key, 'event', i)
        o.sptr(e.name)
        t = e.type
        if t == 'action':
            o.u8(0); o.u8(0); o.u16(nx(e.next)); o.u16(e.actor); o.u16(e.action)
            o.ptr((k, 'params') if e.params is not None else None); o.ptr(None); o.ptr(None); o.ptr(None)
        elif t == 'switch':
            o.u8(1); o.u8(0); o.u16(len(e.cases)); o.u16(e.actor); o.u16(e.query)
            o.ptr((k, 'params') if e.params is not None else None)
            o.ptr((k, 'cases') if e.cases else None, listed=True); o.ptr(None); o.ptr(None)
        elif t == 'fork':
            o.u8(2); o.u8(0); o.u16(len(e.forks)); o.u16(e.join); o.u16(0)
            o.ptr((k, 'forks')); o.ptr(None); o.ptr(None); o.ptr(None)
        elif t == 'join':
            o.u8(3); o.u8(0); o.u16(nx(e.next)); o.u16(0); o.u16(0)
            o.ptr(None); o.ptr(None); o.ptr(None); o.ptr(None)
        elif t == 'subflow':
            o.u8(4); o.u8(0); o.u16(nx(e.next)); o.u16(0); o.u16(0)
            o.ptr((k, 'params') if e.params is not None else None)
            o.sptr(e.flowchart); o.sptr(e.entry); o.ptr(None)
        elif t == 'callswitch':
            o.u8(5); o.u8(0); o.u16(len(e.cases)); o.u16(0); o.u16(0)
            o.ptr((k, 'params') if e.params is not None else None)
            o.ptr((k, 'cases') if e.cases else None, listed=True)
            o.sptr(e.flowchart); o.sptr(e.entry)
        elif t == 'return':
            o.u8(6); o.u8(0); o.u16(0); o.u32(e.value)
            o.ptr(None); o.ptr(None); o.ptr(None); o.ptr(None)
        else:
            raise ValueError('unknown event type %r' % t)
    # entry points
    _write_dic(o, (key, 'epdic'), [ep.name for ep in fc.entry_points])
    o.mark((key, 'eps'))
    for i, ep in enumerate(fc.entry_points):
        k = (key, 'ep', i)
        o.ptr((k, 'subs') if ep.subflows else None, listed=True)
        o.ptr((k, 'vdic') if ep.variables else None)
        o.ptr((k, 'vdefs') if ep.variables else None, listed=True)
        o.u16(len(ep.subflows)); o.u16(len(ep.variables or ())); o.u16(nx(ep.main)); o.u16(0)
    # event data: cases / forks, then parameters
    for i, e in enumerate(fc.events):
        k = (key, 'event', i)
        if e.type in ('switch', 'callswitch') and e.cases:
            o.align(8)
            o.mark((k, 'cases'))
            for v, ev in e.cases:
                o.u32(v); o.u16(ev); o.u16(0)
        if e.type == 'fork':
            o.align(8)
            o.mark((k, 'forks'))
            for f in e.forks:
                o.u16(f)
        _write_params(o, (k, 'params'), e.params)
    _write_actor_data(o, key, fc.actors)
    # entry point extra data
    for i, ep in enumerate(fc.entry_points):
        k = (key, 'ep', i)
        o.align(8)
        o.mark((k, 'subs'))
        for s in ep.subflows:
            o.u16(s)
        if ep.variables:                      # in place of the 0x18 empty bytes
            _write_dic(o, (k, 'vdic'), list(ep.variables))
            o.mark((k, 'vdefs'))
            for v in ep.variables.values():
                o.b += struct.pack('<iIHHI', int(v), 0, 1, 3 if isinstance(v, bool) else 2, 0)
            continue
        o.align(8)
        o.b += b'\0' * 0x18


# ============================================================================ checking what was written
def _f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def _norm(v):
    """a parameter value as (type, value), so that 1 / True / 1.0 and text / Argument don't compare equal;
    floats as the 32-bit value the file can hold"""
    if v is None:
        return None
    t = _item_type(v)
    if t == 1:
        return (1, [(k, _norm(x)) for k, x in v.items()])
    if t == 4:
        return (4, _f32(v))
    if t == 9:
        return (9, [_f32(x) for x in v])
    if t in (7, 8, 10, 11, 12):
        return (t, list(v))
    return (t, str(v) if t in (0, 5, 6) else v)


def _event_fields(e):
    d = {'name': e.name, 'type': e.type}
    if e.type in ('action', 'join', 'subflow'):
        d['next'] = e.next
    if e.type in ('action', 'switch'):
        d['actor'] = e.actor
        d['action' if e.type == 'action' else 'query'] = e.action if e.type == 'action' else e.query
    if e.type in ('action', 'switch', 'subflow', 'callswitch'):
        d['params'] = _norm(e.params)
    if e.type in ('switch', 'callswitch'):
        d['cases'] = [tuple(c) for c in e.cases]
    if e.type == 'fork':
        d['forks'], d['join'] = list(e.forks), e.join
    if e.type in ('subflow', 'callswitch'):
        d['flowchart'], d['entry'] = e.flowchart or '', e.entry or ''
    if e.type == 'return':
        d['value'] = e.value
    return d


def _actor_fields(a):
    return {'name': a.name, 'secondary': a.secondary or '', 'argument': a.argument or '',
            'actions': list(a.actions), 'queries': list(a.queries), 'params': _norm(a.params),
            'entry_point': a.entry_point, 'cut': a.cut}


def _entry_fields(ep):
    return {'name': ep.name, 'main': ep.main, 'subflows': list(ep.subflows),
            'variables': [(k, type(v).__name__, v) for k, v in (ep.variables or {}).items()]}


def _clip_fields(c):
    return {'start': _f32(c.start), 'duration': _f32(c.duration), 'actor': c.actor, 'action': c.action,
            'track': c.track, 'params': _norm(c.params)}


def _timeline_differences(out, ta, tb):
    w = ta.name
    for k in ('name', 'duration', 'triggers', 'subtimelines'):
        if getattr(ta, k) != getattr(tb, k):
            out.append('%s: %s: %r / %r' % (w, k, getattr(ta, k), getattr(tb, k)))
    if _norm(ta.params) != _norm(tb.params):
        out.append('%s: parameters differ' % w)
    lists = (('actor', ta.actors, tb.actors, _actor_fields, lambda x: x.name),
             ('clip', ta.clips, tb.clips, _clip_fields, lambda x: 'frame %g' % x.start),
             ('oneshot', ta.oneshots, tb.oneshots,
              lambda c: {'time': _f32(c.time), 'actor': c.actor, 'action': c.action, 'params': _norm(c.params)},
              lambda x: 'frame %g' % x.time),
             ('cut', ta.cuts, tb.cuts,
              lambda c: {'start': _f32(c.start), 'name': c.name, 'params': _norm(c.params)}, lambda x: x.name))
    for what, la, lb, fields, label in lists:
        if len(la) != len(lb):
            out.append('%s: %d %ss / %d' % (w, len(la), what, len(lb)))
        for i, (x, y) in enumerate(zip(la, lb)):
            dx, dy = fields(x), fields(y)
            for k in sorted(dx.keys() | dy.keys()):
                if dx.get(k) != dy.get(k):
                    out.append('%s: %s %d (%s) %s: %r / %r' % (w, what, i, label(x), k, dx.get(k), dy.get(k)))


def differences(a, b):
    """What differs between two event flows, as a list of lines (empty = the same): every flowchart, actor,
    action, query, event, link, parameter (with its type) and entry point is compared; of a timeline, its
    length, actors, clips, triggers, cuts and sub-timelines."""
    out = []
    if a.name != b.name:
        out.append('file name: %r / %r' % (a.name, b.name))
    if tuple(a.version) != tuple(b.version):
        out.append('version: %r / %r' % (a.version, b.version))
    if len(a.flowcharts) != len(b.flowcharts):
        out.append('flowcharts: %d / %d' % (len(a.flowcharts), len(b.flowcharts)))
    if len(a.timelines) != len(b.timelines):
        out.append('timelines: %d / %d' % (len(a.timelines), len(b.timelines)))
    for ta, tb in zip(a.timelines, b.timelines):
        _timeline_differences(out, ta, tb)
    for fa, fb in zip(a.flowcharts, b.flowcharts):
        w = fa.name
        if fa.name != fb.name:
            out.append('flowchart name: %r / %r' % (fa.name, fb.name))
        for what, la, lb, fields in (('actor', fa.actors, fb.actors, _actor_fields),
                                     ('event', fa.events, fb.events, _event_fields),
                                     ('entry point', fa.entry_points, fb.entry_points, _entry_fields)):
            if len(la) != len(lb):
                out.append('%s: %d %ss / %d' % (w, len(la), what, len(lb)))
            for i, (x, y) in enumerate(zip(la, lb)):
                dx, dy = fields(x), fields(y)
                for k in sorted(dx.keys() | dy.keys()):
                    if (k in dx) != (k in dy) or dx.get(k) != dy.get(k):
                        out.append('%s: %s %d (%s) %s: %r / %r' % (w, what, i, x.name, k, dx.get(k), dy.get(k)))
    return out


def dumps_checked(flow, update_entry_points=True):
    """dumps() for an edited flow: brings the entry points' subflow lists up to date, checks the flow, writes
    it, reads the result back and compares it with what was meant (every event, actor, action, query,
    parameter, entry point). Raises ValueError when anything is wrong or differs."""
    for fc in flow.flowcharts:
        if update_entry_points:
            fc.update_entry_points()
        fc.check()
    for tl in flow.timelines:
        tl.check()
    data = dumps(flow)
    diff = differences(flow, loads(data))
    if diff:
        raise ValueError('%s: what was written does not read back as meant: %s' % (flow.name, '; '.join(diff[:10])))
    if dumps(loads(data)) != data:
        raise ValueError('%s: the written file does not rewrite identically' % flow.name)
    return data
