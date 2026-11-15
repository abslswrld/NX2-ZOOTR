"""BYML (binary YAML), versions 2 to 7, little or big endian.

Values come back as plain Python objects, with small wrapper types where the file distinguishes
types that Python doesn't:
    dict            0xC1 string-keyed dictionary (key order kept)
    HashDict        0x20 dictionary keyed by 32-bit hashes
    ValueHashDict   0x21 dictionary keyed by 32-bit hashes, with an extra 32-bit field per entry
    list            0xC0 array
    str             0xA0 string
    Binary          0xA1 binary data;  File  0xA2 file data (with alignment)
    bool, int (0xD1 signed 32), float (0xD2), None (0xFF)
    UInt (0xD3), Int64 (0xD4), UInt64 (0xD5), Double (0xD6)
``write`` lays the file out the way the game's files are laid out (keys, strings, 64-bit values,
then containers depth first, sharing identical containers and values) so an unchanged file comes
back byte for byte.
"""
import struct


class UInt(int):
    pass


class Int64(int):
    pass


class UInt64(int):
    pass


class Double(float):
    pass


class Binary(bytes):
    pass


class File(bytes):
    align = 0x1000


class HashDict(dict):
    """0x20: {hash: value}"""


class ValueHashDict(dict):
    """0x21: {hash: value}; ``extra[hash]`` keeps the per-entry 32-bit field."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.extra = {}


class Document:
    def __init__(self, root, version=7, big_endian=False):
        self.root, self.version, self.big_endian = root, version, big_endian
        # id(container) -> child positions in the order the original file stored them; used by dumps so
        # that an unchanged file is rewritten byte for byte (new or edited containers fall back to key order)
        self.layout = {}


_CONTAINERS = (0xC0, 0xC1, 0x20, 0x21)


def loads(data):
    """Parse a BYML file. Returns a Document (``.root`` is the data)."""
    data = bytes(data)
    if data[:2] == b'YB':
        e = '<'
    elif data[:2] == b'BY':
        e = '>'
    else:
        raise ValueError('not a BYML file')
    version, hk_off, st_off, root_off = struct.unpack_from(e + 'HIII', data, 2)

    def u24(off):
        b = data[off:off + 3]
        return int.from_bytes(b, 'little' if e == '<' else 'big')

    def table(off):
        if not off:
            return []
        n = u24(off + 1)
        offs = struct.unpack_from(e + '%dI' % (n + 1), data, off + 4)
        return [data[off + offs[i]:data.index(b'\0', off + offs[i])].decode('utf-8') for i in range(n)]

    keys, strings = table(hk_off), table(st_off)
    cache = {}

    def value(t, raw):
        if t == 0xA0:
            return strings[raw]
        if t in _CONTAINERS:
            if raw not in cache:
                cache[raw] = container(raw)
            return cache[raw]
        if t == 0xD0:
            return bool(raw)
        if t == 0xD1:
            return struct.unpack(e + 'i', struct.pack(e + 'I', raw))[0]
        if t == 0xD2:
            return struct.unpack(e + 'f', struct.pack(e + 'I', raw))[0]
        if t == 0xD3:
            return UInt(raw)
        if t == 0xD4:
            return Int64(struct.unpack_from(e + 'q', data, raw)[0])
        if t == 0xD5:
            return UInt64(struct.unpack_from(e + 'Q', data, raw)[0])
        if t == 0xD6:
            return Double(struct.unpack_from(e + 'd', data, raw)[0])
        if t == 0xA1:
            n = struct.unpack_from(e + 'I', data, raw)[0]
            return Binary(data[raw + 4:raw + 4 + n])
        if t == 0xA2:
            n, a = struct.unpack_from(e + 'II', data, raw)
            f = File(data[raw + 8:raw + 8 + n])
            f.align = a
            return f
        if t == 0xFF:
            return None
        raise ValueError('unknown BYML node type 0x%02X' % t)

    layout = {}

    def remember(obj, kids):
        """kids: [(position, type, raw)]; keep the order child containers sit in the file"""
        offs = sorted((raw, i) for i, ty, raw in kids if ty in _CONTAINERS)
        layout[id(obj)] = (obj, [i for _, i in offs])

    def container(off):
        t, n = data[off], u24(off + 1)
        if t == 0xC0:
            types = data[off + 4:off + 4 + n]
            vals = struct.unpack_from(e + '%dI' % n, data, off + 4 + ((n + 3) & ~3))
            out = [value(ty, v) for ty, v in zip(types, vals)]
            remember(out, [(i, ty, v) for i, (ty, v) in enumerate(zip(types, vals))])
            return out
        if t == 0xC1:
            out = {}
            kids = []
            for i in range(n):
                p = off + 4 + 8 * i
                k = u24(p)
                ty = data[p + 3]
                raw = struct.unpack_from(e + 'I', data, p + 4)[0]
                out[keys[k]] = value(ty, raw)
                kids.append((i, ty, raw))
            remember(out, kids)
            return out
        if t == 0x20:
            out = HashDict()
            types = data[off + 4 + 8 * n:off + 4 + 9 * n]
            kids = []
            for i in range(n):
                h, v = struct.unpack_from(e + 'II', data, off + 4 + 8 * i)
                out[h] = value(types[i], v)
                kids.append((i, types[i], v))
            remember(out, kids)
            return out
        if t == 0x21:
            out = ValueHashDict()
            types = data[off + 4 + 12 * n:off + 4 + 13 * n]
            kids = []
            for i in range(n):
                v, h, x = struct.unpack_from(e + 'III', data, off + 4 + 12 * i)
                out[h] = value(types[i], v)
                out.extra[h] = x
                kids.append((i, types[i], v))
            remember(out, kids)
            return out
        raise ValueError('bad container type 0x%02X' % t)

    root = container(root_off) if root_off else None
    doc = Document(root, version, e == '>')
    doc.layout = layout
    return doc


# ----------------------------------------------------------------------------- writing
def _type_of(v):
    if isinstance(v, bool):
        return 0xD0
    if isinstance(v, (HashDict,)):
        return 0x20
    if isinstance(v, ValueHashDict):
        return 0x21
    if isinstance(v, dict):
        return 0xC1
    if isinstance(v, list):
        return 0xC0
    if isinstance(v, str):
        return 0xA0
    if isinstance(v, File):
        return 0xA2
    if isinstance(v, Binary):
        return 0xA1
    if isinstance(v, UInt64):
        return 0xD5
    if isinstance(v, Int64):
        return 0xD4
    if isinstance(v, UInt):
        return 0xD3
    if isinstance(v, Double):
        return 0xD6
    if isinstance(v, int):
        return 0xD1
    if isinstance(v, float):
        return 0xD2
    if v is None:
        return 0xFF
    raise TypeError('cannot store %r in BYML' % type(v))


def _freeze(v):
    """Hashable identity of a value, type included (used to share identical nodes)."""
    t = _type_of(v)
    if t == 0xC0:
        return (t, tuple(_freeze(x) for x in v))
    if t == 0xC1:
        return (t, tuple((k, _freeze(x)) for k, x in v.items()))
    if t == 0x20:
        return (t, tuple((k, _freeze(x)) for k, x in v.items()))
    if t == 0x21:
        return (t, tuple((k, v.extra.get(k, 0), _freeze(x)) for k, x in v.items()))
    if t == 0xD2:
        return (t, struct.pack('<f', v))
    if t == 0xD6:
        return (t, struct.pack('<d', v))
    if t == 0xA2:
        return (t, bytes(v), v.align)
    return (t, v)


def _same_shape(v, values, order):
    """the remembered order still points at exactly this container's child containers"""
    idx = [i for i, x in enumerate(values) if _type_of(x) in _CONTAINERS]
    return sorted(order) == idx


def dumps(doc):
    """Write a Document (or a bare root value, as v7 little endian)."""
    if not isinstance(doc, Document):
        doc = Document(doc)
    e = '>' if doc.big_endian else '<'
    order = 'big' if doc.big_endian else 'little'
    root = doc.root

    keys, strings = set(), set()
    specials = []                                   # 64-bit values and binary data, first-seen order
    seen_special = set()

    def collect(v):
        t = _type_of(v)
        if t == 0xC1:
            for k, x in v.items():
                keys.add(k)
                collect(x)
        elif t in (0xC0,):
            for x in v:
                collect(x)
        elif t in (0x20, 0x21):
            for x in v.values():
                collect(x)
        elif t == 0xA0:
            strings.add(v)
        elif t in (0xA1, 0xA2, 0xD4, 0xD5, 0xD6):
            f = _freeze(v)
            if f not in seen_special:
                seen_special.add(f)
                specials.append(v)

    if root is not None:
        collect(root)
    keys = sorted(keys, key=lambda s: s.encode('utf-8'))
    strings = sorted(strings, key=lambda s: s.encode('utf-8'))
    key_idx = {k: i for i, k in enumerate(keys)}
    str_idx = {s: i for i, s in enumerate(strings)}

    out = bytearray(16)

    def align4():
        out.extend(b'\0' * (-len(out) & 3))

    def u24(n):
        return n.to_bytes(3, order)

    def write_table(items):
        start = len(out)
        enc = [s.encode('utf-8') + b'\0' for s in items]
        offs = []
        pos = 4 + 4 * (len(items) + 1)
        for s in enc:
            offs.append(pos)
            pos += len(s)
        offs.append(pos)
        out.append(0xC2)
        out.extend(u24(len(items)))
        out.extend(struct.pack(e + '%dI' % len(offs), *offs))
        for s in enc:
            out.extend(s)
        align4()
        return start

    hk_off = write_table(keys) if keys else 0
    st_off = write_table(strings) if strings else 0

    special_off = {}
    for v in specials:
        t = _type_of(v)
        f = _freeze(v)
        if t == 0xA2:
            # the data itself is aligned; the 8-byte size/alignment header sits just before it
            target = len(out) + 8
            pad = -target & (v.align - 1)
            out.extend(b'\0' * pad)
            special_off[f] = len(out)
            out.extend(struct.pack(e + 'II', len(v), v.align))
            out.extend(v)
            align4()
            continue
        special_off[f] = len(out)
        if t == 0xA1:
            out.extend(struct.pack(e + 'I', len(v)))
            out.extend(v)
        elif t == 0xD4:
            out.extend(struct.pack(e + 'q', v))
        elif t == 0xD5:
            out.extend(struct.pack(e + 'Q', v))
        else:
            out.extend(struct.pack(e + 'd', v))

    container_off = {}

    def inline(v):
        t = _type_of(v)
        if t == 0xA0:
            return str_idx[v]
        if t == 0xD0:
            return int(v)
        if t == 0xD1:
            return struct.unpack(e + 'I', struct.pack(e + 'i', v))[0]
        if t == 0xD2:
            return struct.unpack(e + 'I', struct.pack(e + 'f', v))[0]
        if t == 0xD3:
            return int(v)
        if t == 0xFF:
            return 0
        if t in _CONTAINERS:
            return container_off[_freeze(v)]
        return special_off[_freeze(v)]

    def write_container(v):
        """Write v and, depth first, the containers below it that aren't written yet."""
        f = _freeze(v)
        if f in container_off:
            return
        align4()
        start = len(out)
        container_off[f] = start
        t = _type_of(v)
        if t == 0xC0:
            items = list(v)
            size = 4 + ((len(items) + 3) & ~3) + 4 * len(items)
        elif t == 0xC1:
            items = sorted(v.items(), key=lambda kv: kv[0].encode('utf-8'))
            size = 4 + 8 * len(items)
        elif t == 0x20:
            items = sorted(v.items())
            size = 4 + 8 * len(items) + ((len(items) + 3) & ~3)
        else:
            items = sorted(v.items())
            size = 4 + 12 * len(items) + ((len(items) + 3) & ~3)
        out.extend(b'\0' * size)
        values = items if t == 0xC0 else [x for _, x in items]
        kept = doc.layout.get(id(v))
        if kept is not None and kept[0] is v and _same_shape(v, values, kept[1]):
            children = [values[i] for i in kept[1]]
        else:
            children = [x for x in values if _type_of(x) in _CONTAINERS]
        for c in children:
            write_container(c)
        # fill in the node now that every child has an offset
        node = bytearray([t]) + u24(len(items))
        if t == 0xC0:
            node += bytes(_type_of(x) for x in items)
            node += b'\0' * (-len(node) & 3)
            node += b''.join(struct.pack(e + 'I', inline(x)) for x in items)
        elif t == 0xC1:
            for k, x in items:
                node += key_idx[k].to_bytes(3, order) + bytes([_type_of(x)]) + struct.pack(e + 'I', inline(x))
        elif t == 0x20:
            for h, x in items:
                node += struct.pack(e + 'II', h, inline(x))
            node += bytes(_type_of(x) for _, x in items)
            node += b'\0' * (-len(node) & 3)
        else:
            for h, x in items:
                node += struct.pack(e + 'III', inline(x), h, v.extra.get(h, 0))
            node += bytes(_type_of(x) for _, x in items)
            node += b'\0' * (-len(node) & 3)
        out[start:start + size] = node

    root_off = 0
    if root is not None:
        write_container(root)
        root_off = container_off[_freeze(root)]
    align4()
    out[0:16] = (b'BY' if doc.big_endian else b'YB') + struct.pack(e + 'HIII', doc.version, hk_off, st_off, root_off)
    return bytes(out)
