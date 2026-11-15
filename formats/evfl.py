"""Event flows (.bfevfl): reading into plain objects, and writing back.

Written from the public BFEVFL documentation (ZeldaMods wiki), checked against the remake's files
(version 0.4.0.0, little endian, flowcharts only).

Model
    EventFlow(name, flowcharts)
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
    EntryPoint(name, subflows, main)
    Params: an ordered dict {key: value}; values are int, bool, float, str, Argument(str),
            WString(str), lists of those (IntArray/BoolArray/FloatArray/StrArray/WStrArray), ActorId(a, b),
            or a nested Params.
"""
import struct

NONE16 = 0xFFFF
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
    def __init__(self, name, main=None, subflows=None):
        self.name, self.main = name, main
        self.subflows = list(subflows or [])


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


class EventFlow:
    def __init__(self, name, flowcharts=None):
        self.name = name
        self.flowcharts = list(flowcharts or [])
        self.version = (0, 4, 0, 0)
        self.string_order = []          # pool order of the file read (kept so unchanged files rewrite identically)

    @property
    def flowchart(self):
        return self.flowcharts[0]


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
    if ntime:
        raise ValueError('timelines are not supported')
    fname = data[r.u32(0x10):data.index(b'\0', r.u32(0x10))].decode('utf-8')
    flow = EventFlow(fname)
    flow.version = tuple(data[8:12])
    arr = r.ptr(0x28)
    for i in range(nflow):
        flow.flowcharts.append(_read_flowchart(r, r.ptr(arr + 8 * i)))
    # string pool order
    pool = None
    for fc_off in (r.ptr(arr + 8 * i) for i in range(nflow)):
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


def _read_flowchart(r, p):
    if r.d[p:p + 4] != b'EVFL':
        raise ValueError('bad flowchart')
    nact, _nacts, _nq, nev, nep = (r.u16(p + 0x10 + 2 * i) for i in range(5))
    fc = Flowchart(r.pstr(r.ptr(p + 0x20)))
    ap, ep, dp, epp = r.ptr(p + 0x28), r.ptr(p + 0x30), r.ptr(p + 0x38), r.ptr(p + 0x40)
    for i in range(nact):
        a = ap + 0x38 * i
        na, nq = r.u16(a + 0x30), r.u16(a + 0x32)
        acts = [r.pstr(r.ptr(r.ptr(a + 0x18) + 8 * k)) for k in range(na)]
        qs = [r.pstr(r.ptr(r.ptr(a + 0x20) + 8 * k)) for k in range(nq)]
        epi = r.u16(a + 0x34)
        fc.actors.append(Actor(r.pstr(r.ptr(a)), r.pstr(r.ptr(a + 8)), r.pstr(r.ptr(a + 0x10)), acts, qs,
                               _read_params(r, r.ptr(a + 0x28)), None if epi == NONE16 else epi, r.u8(a + 0x36)))
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
        nsub = r.u16(e + 0x18)
        if r.u16(e + 0x1A):
            raise ValueError('entry point variables are not supported')
        main = r.u16(e + 0x1C)
        fc.entry_points.append(EntryPoint(n, None if main == NONE16 else main,
                                          [r.u16(r.ptr(e) + 2 * k) for k in range(nsub)]))
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
    fcs = flow.flowcharts
    # file header (0x48)
    o.b += b'BFEVFL\0\0' + bytes(flow.version)
    o.u16(0xFEFF)
    o.u8(3); o.u8(0)
    o.u32(0)                                  # file name, set later
    o.u16(0)
    o.u16(0)                                  # first block, set later
    o.u32(0)                                  # RELT, set later
    o.u32(0)                                  # file size, set later
    o.u16(len(fcs)); o.u16(0); o.u32(0)
    o.ptr('fc_array' if fcs else None)
    o.ptr('fc_dic')
    o.ptr(None, listed=True)
    o.ptr('tl_dic')
    if fcs:
        o.mark('fc_array')
        for i in range(len(fcs)):
            o.ptr(('fc', i))
    _write_dic(o, 'fc_dic', [fc.name for fc in fcs])
    _write_dic(o, 'tl_dic', [])
    first_block = None
    for i, fc in enumerate(fcs):
        o.align(8)
        if first_block is None:
            first_block = o.tell()
        _write_flowchart(o, ('fc', i), fc)
    # string pool
    o.align(8)
    pool = o.tell()
    for i, fc in enumerate(fcs):
        struct.pack_into('<I', o.b, o.addr[('fc', i)] + 4, pool - o.addr[('fc', i)])
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
    o.ptr((key, 'actors') if fc.actors else None)
    o.ptr((key, 'events') if fc.events else None)
    o.ptr((key, 'epdic'))
    o.ptr((key, 'eps') if fc.entry_points else None)
    # actors
    o.mark((key, 'actors'))
    for i, a in enumerate(fc.actors):
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
            o.ptr((k, 'cases') if e.cases else None)
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
        o.ptr(None); o.ptr(None, listed=True)
        o.u16(len(ep.subflows)); o.u16(0); o.u16(nx(ep.main)); o.u16(0)
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
    # actor data: parameters, then action and query name arrays
    for i, a in enumerate(fc.actors):
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
    # entry point extra data
    for i, ep in enumerate(fc.entry_points):
        k = (key, 'ep', i)
        o.align(8)
        o.mark((k, 'subs'))
        for s in ep.subflows:
            o.u16(s)
        o.align(8)
        o.b += b'\0' * 0x18
