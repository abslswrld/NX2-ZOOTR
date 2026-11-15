"""Zstandard (.zs) reading and writing.

Uses Python's built-in ``compression.zstd`` (3.14+) when it is available. Otherwise falls back to a
pure-Python decoder written from RFC 8878, and a writer that stores data in raw (uncompressed)
blocks. Raw blocks are valid zstd frames that any decoder accepts; they just aren't smaller.

Dictionaries: the game compresses most files with dictionaries kept in Pack/ZsDic.pack.zs.
Load them with ``Dictionaries.from_pack(bytes)``; ``decompress`` then picks the right one from the
frame's dictionary ID.
"""
import struct

try:                                    # Python 3.14+
    from compression import zstd as _std
except ImportError:                     # pragma: no cover - depends on the Python version
    _std = None

FRAME_MAGIC = 0xFD2FB528
DICT_MAGIC = 0xEC30A437


class ZstdError(Exception):
    pass


# ----------------------------------------------------------------------------- bit readers
class _ForwardBits:
    """Little-endian bit reader, used for FSE table descriptions."""

    def __init__(self, data, pos=0):
        self.data, self.bit = data, pos * 8

    def peek(self, n):
        lo = self.bit >> 3
        v = int.from_bytes(self.data[lo:lo + 8], 'little') >> (self.bit & 7)
        return v & ((1 << n) - 1)

    def skip(self, n):
        self.bit += n

    def read(self, n):
        v = self.peek(n)
        self.bit += n
        return v

    def byte_pos(self):
        return (self.bit + 7) >> 3


class _BackwardBits:
    """Reader for zstd's backward bitstreams: read from the end, the highest set bit of the last
    byte marks the start. Reading past the start yields zeros; ``overflow`` tells if that happened."""

    def __init__(self, data):
        if not data or data[-1] == 0:
            raise ZstdError('bad bitstream end')
        self.data = data
        self.pos = (len(data) - 1) * 8 + data[-1].bit_length() - 1   # bits left to read

    def read(self, n):
        if n == 0:
            return 0
        lo = self.pos - n
        self.pos = lo
        if lo >= 0:
            b = lo >> 3
            v = int.from_bytes(self.data[b:b + 9], 'little') >> (lo & 7)
        else:
            v = int.from_bytes(self.data[0:9], 'little') << (-lo)
        return v & ((1 << n) - 1)

    def peek(self, n):
        save = self.pos
        v = self.read(n)
        self.pos = save
        return v

    @property
    def overflow(self):
        return self.pos < 0

    @property
    def done(self):
        return self.pos == 0


# ----------------------------------------------------------------------------- FSE
def _read_fse_description(data, pos, max_symbol, max_log):
    """Read an FSE normalized-count description. Returns (probabilities, accuracy_log, new_pos)."""
    br = _ForwardBits(data, pos)
    log = br.read(4) + 5
    if log > max_log:
        raise ZstdError('FSE accuracy log too large')
    remaining = (1 << log) + 1
    threshold = 1 << log
    nbits = log + 1
    probs = []
    while remaining > 1 and len(probs) <= max_symbol:
        maxv = (2 * threshold - 1) - remaining
        low = br.peek(nbits - 1)
        if low < maxv:
            count = low
            br.skip(nbits - 1)
        else:
            count = br.peek(nbits)
            if count >= threshold:
                count -= maxv
            br.skip(nbits)
        count -= 1
        remaining -= abs(count)
        probs.append(count)
        if count == 0:
            while True:
                rep = br.read(2)
                probs.extend([0] * rep)
                if rep != 3:
                    break
        while remaining < threshold:
            nbits -= 1
            threshold >>= 1
    if remaining != 1 or len(probs) > max_symbol + 1:
        raise ZstdError('bad FSE description')
    return probs, log, br.byte_pos()


def _build_fse(probs, log):
    """Decoding table: list of (symbol, nbits, baseline)."""
    size = 1 << log
    symbol = [0] * size
    high = size - 1
    nxt = [0] * len(probs)
    for s, p in enumerate(probs):
        if p == -1:
            symbol[high] = s
            high -= 1
            nxt[s] = 1
        else:
            nxt[s] = p
    step = (size >> 1) + (size >> 3) + 3
    mask = size - 1
    pos = 0
    for s, p in enumerate(probs):
        for _ in range(max(p, 0)):
            symbol[pos] = s
            pos = (pos + step) & mask
            while pos > high:
                pos = (pos + step) & mask
    table = []
    for st in range(size):
        s = symbol[st]
        n = nxt[s]
        nxt[s] += 1
        nb = log - (n.bit_length() - 1)
        table.append((s, nb, (n << nb) - size))
    return table, log


def _rle_fse(symbol):
    return [(symbol, 0, 0)], 0


# ----------------------------------------------------------------------------- Huffman
def _read_huffman_description(data, pos):
    """Returns (table, max_bits, new_pos). table: list of (symbol, nbits), size 1 << max_bits."""
    hb = data[pos]
    pos += 1
    if hb < 128:
        stream = data[pos:pos + hb]
        probs, log, used = _read_fse_description(stream, 0, 255, 6)
        table, _ = _build_fse(probs, log)
        bits = _BackwardBits(stream[used:])
        weights = []
        s1 = bits.read(log)
        s2 = bits.read(log)
        while True:
            sym, nb, base = table[s1]
            weights.append(sym)
            s1 = base + bits.read(nb)
            if bits.overflow:
                weights.append(table[s2][0])
                break
            sym, nb, base = table[s2]
            weights.append(sym)
            s2 = base + bits.read(nb)
            if bits.overflow:
                weights.append(table[s1][0])
                break
        pos += hb
    else:
        n = hb - 127
        nbytes = (n + 1) // 2
        weights = []
        for i in range(n):
            b = data[pos + i // 2]
            weights.append(b >> 4 if i % 2 == 0 else b & 15)
        pos += nbytes
    total = sum(1 << (w - 1) for w in weights if w)
    max_bits = total.bit_length()
    if max_bits > 11:
        raise ZstdError('Huffman table too deep')
    left = (1 << max_bits) - total
    if left & (left - 1):
        raise ZstdError('bad Huffman weights')
    weights.append(left.bit_length())
    rank = [0] * (max_bits + 2)
    start = 0
    for w in range(1, max_bits + 1):
        rank[w] = start
        start += sum(1 for x in weights if x == w) << (w - 1)
    table = [None] * (1 << max_bits)
    for s, w in enumerate(weights):
        if not w:
            continue
        ln = 1 << (w - 1)
        nb = max_bits + 1 - w
        for i in range(rank[w], rank[w] + ln):
            table[i] = (s, nb)
        rank[w] += ln
    return (table, max_bits), pos


def _huffman_stream(stream, huf, count):
    table, max_bits = huf
    bits = _BackwardBits(stream)
    out = bytearray(count)
    for i in range(count):
        s, nb = table[bits.peek(max_bits)]
        out[i] = s
        bits.read(nb)
    if bits.pos != 0:
        raise ZstdError('Huffman stream not fully used')
    return out


# ----------------------------------------------------------------------------- sequences
_LL_BASE = list(range(16)) + [16, 18, 20, 22, 24, 28, 32, 40, 48, 64, 128, 256, 512, 1024, 2048, 4096,
                              8192, 16384, 32768, 65536]
_LL_BITS = [0] * 16 + [1, 1, 1, 1, 2, 2, 3, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
_ML_BASE = [i + 3 for i in range(32)] + [35, 37, 39, 41, 43, 47, 51, 59, 67, 83, 99, 131, 259, 515, 1027,
                                         2051, 4099, 8195, 16387, 32771, 65539]
_ML_BITS = [0] * 32 + [1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
_LL_DEFAULT = _build_fse([4, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 1,
                          1, 1, 1, 1, -1, -1, -1, -1], 6)
_ML_DEFAULT = _build_fse([1, 4, 3, 2, 2, 2, 2, 2, 2] + [1] * 37 + [-1] * 7, 6)
_OF_DEFAULT = _build_fse([1, 1, 1, 1, 1, 1, 2, 2, 2] + [1] * 15 + [-1] * 5, 5)


class _State:
    """What carries over between blocks (and comes from a dictionary)."""

    def __init__(self):
        self.huf = None
        self.ll = self.of = self.ml = None
        self.rep = [1, 4, 8]


def _read_table(data, pos, mode, default, max_symbol, max_log, previous):
    if mode == 0:
        return default, pos
    if mode == 1:
        return _rle_fse(data[pos]), pos + 1
    if mode == 2:
        probs, log, used = _read_fse_description(data, pos, max_symbol, max_log)
        return _build_fse(probs, log), used
    if previous is None:
        raise ZstdError('repeat mode with no previous table')
    return previous, pos


def _decode_block(block, out, st):
    # literals
    b0 = block[0]
    ltype, sf = b0 & 3, (b0 >> 2) & 3
    if ltype in (0, 1):
        if sf in (0, 2):
            size, pos = b0 >> 3, 1
        elif sf == 1:
            size, pos = (b0 >> 4) + (block[1] << 4), 2
        else:
            size, pos = (b0 >> 4) + (block[1] << 4) + (block[2] << 12), 3
        if ltype == 0:
            literals = block[pos:pos + size]
            pos += size
        else:
            literals = bytes([block[pos]]) * size
            pos += 1
    else:
        nhead, nbits = {0: (3, 10), 1: (3, 10), 2: (4, 14), 3: (5, 18)}[sf]
        h = int.from_bytes(block[:nhead], 'little')
        regen = (h >> 4) & ((1 << nbits) - 1)
        comp = (h >> (4 + nbits)) & ((1 << nbits) - 1)
        pos = nhead
        end = pos + comp
        if ltype == 2:
            st.huf, pos = _read_huffman_description(block, pos)
        elif st.huf is None:
            raise ZstdError('treeless literals with no table')
        if sf == 0:
            literals = _huffman_stream(block[pos:end], st.huf, regen)
        else:
            s1, s2, s3 = struct.unpack_from('<3H', block, pos)
            pos += 6
            each = (regen + 3) // 4
            sizes = [each, each, each, regen - 3 * each]
            parts = []
            for ln, cnt in zip((s1, s2, s3, end - pos - s1 - s2 - s3), sizes):
                parts.append(_huffman_stream(block[pos:pos + ln], st.huf, cnt))
                pos += ln
            literals = b''.join(parts)
        pos = end
    # sequences
    n = block[pos]
    pos += 1
    if n == 0:
        out += literals
        return
    if n == 255:
        n = block[pos] + (block[pos + 1] << 8) + 0x7F00
        pos += 2
    elif n >= 128:
        n = ((n - 128) << 8) + block[pos]
        pos += 1
    modes = block[pos]
    pos += 1
    st.ll, pos = _read_table(block, pos, modes >> 6, _LL_DEFAULT, 35, 9, st.ll)
    st.of, pos = _read_table(block, pos, (modes >> 4) & 3, _OF_DEFAULT, 31, 8, st.of)
    st.ml, pos = _read_table(block, pos, (modes >> 2) & 3, _ML_DEFAULT, 52, 9, st.ml)
    bits = _BackwardBits(block[pos:])
    (llt, lllog), (oft, oflog), (mlt, mllog) = st.ll, st.of, st.ml
    sll = bits.read(lllog)
    sof = bits.read(oflog)
    sml = bits.read(mllog)
    rep = st.rep
    lit = 0
    for i in range(n):
        ofc = oft[sof][0]
        mlc = mlt[sml][0]
        llc = llt[sll][0]
        ofv = (1 << ofc) + bits.read(ofc)
        ml = _ML_BASE[mlc] + bits.read(_ML_BITS[mlc])
        ll = _LL_BASE[llc] + bits.read(_LL_BITS[llc])
        if i != n - 1:
            _, nb, base = llt[sll]
            sll = base + bits.read(nb)
            _, nb, base = mlt[sml]
            sml = base + bits.read(nb)
            _, nb, base = oft[sof]
            sof = base + bits.read(nb)
        if ofv > 3:
            off = ofv - 3
            rep[2], rep[1], rep[0] = rep[1], rep[0], off
        else:
            idx = ofv - 1 + (ll == 0)
            if idx == 0:
                off = rep[0]
            elif idx == 1:
                off = rep[1]
                rep[1], rep[0] = rep[0], off
            elif idx == 2:
                off = rep[2]
                rep[2], rep[1], rep[0] = rep[1], rep[0], off
            else:
                off = rep[0] - 1
                rep[2], rep[1], rep[0] = rep[1], rep[0], off
        out += literals[lit:lit + ll]
        lit += ll
        start = len(out) - off
        if start < 0 or off == 0:
            raise ZstdError('match offset out of range')
        if off >= ml:
            out += out[start:start + ml]
        else:
            for k in range(ml):
                out.append(out[start + k])
    if not bits.done:
        raise ZstdError('sequence stream not fully used')
    out += literals[lit:]


# ----------------------------------------------------------------------------- dictionaries
class Dictionary:
    def __init__(self, data):
        if struct.unpack_from('<I', data, 0)[0] != DICT_MAGIC:       # raw content dictionary
            self.id, self.content, self.state = 0, bytes(data), _State()
            self.raw = bytes(data)
            return
        self.raw = bytes(data)
        self.id = struct.unpack_from('<I', data, 4)[0]
        st = _State()
        st.huf, pos = _read_huffman_description(data, 8)
        probs, log, pos = _read_fse_description(data, pos, 31, 8)
        st.of = _build_fse(probs, log)
        probs, log, pos = _read_fse_description(data, pos, 52, 9)
        st.ml = _build_fse(probs, log)
        probs, log, pos = _read_fse_description(data, pos, 35, 9)
        st.ll = _build_fse(probs, log)
        st.rep = list(struct.unpack_from('<3I', data, pos))
        self.content = bytes(data[pos + 12:])
        self.state = st

    def fresh_state(self):
        s = _State()
        s.huf, s.ll, s.of, s.ml, s.rep = self.state.huf, self.state.ll, self.state.of, self.state.ml, list(self.state.rep)
        return s


class Dictionaries:
    """The game's dictionaries, by ID."""

    def __init__(self, dicts=()):
        self.by_id = {d.id: d for d in dicts}

    @classmethod
    def from_pack(cls, pack_zs):
        from . import sarc
        archive = sarc.Sarc.read(decompress(pack_zs))
        return cls(Dictionary(data) for name, data in archive.files.items() if name.endswith('.zsdic'))

    def get(self, did):
        return self.by_id.get(did)

    def names(self):
        return sorted(self.by_id)


# ----------------------------------------------------------------------------- frames
def frame_dict_id(data):
    """Dictionary ID named in a frame header (0 if none)."""
    if struct.unpack_from('<I', data, 0)[0] != FRAME_MAGIC:
        raise ZstdError('not a zstd frame')
    fhd = data[4]
    size = (0, 1, 2, 4)[fhd & 3]
    pos = 5 + (0 if fhd & 0x20 else 1)
    return int.from_bytes(data[pos:pos + size], 'little')


def _py_decompress(data, dicts):
    out_all = bytearray()
    pos = 0
    while pos < len(data):
        magic = struct.unpack_from('<I', data, pos)[0]
        if magic & 0xFFFFFFF0 == 0x184D2A50:                       # skippable frame
            pos += 8 + struct.unpack_from('<I', data, pos + 4)[0]
            continue
        if magic != FRAME_MAGIC:
            raise ZstdError('not a zstd frame')
        fhd = data[pos + 4]
        pos += 5
        single = fhd & 0x20
        if not single:
            pos += 1                                              # window descriptor
        did_size = (0, 1, 2, 4)[fhd & 3]
        did = int.from_bytes(data[pos:pos + did_size], 'little')
        pos += did_size
        fcs_flag = fhd >> 6
        fcs_size = (1 if single else 0, 2, 4, 8)[fcs_flag]
        fcs = int.from_bytes(data[pos:pos + fcs_size], 'little') + (256 if fcs_size == 2 else 0) if fcs_size else None
        pos += fcs_size
        checksum = fhd & 4
        d = None
        if did:
            d = dicts.get(did) if dicts else None
            if d is None:
                raise ZstdError('dictionary %d needed' % did)
        st = d.fresh_state() if d else _State()
        prefix = d.content if d else b''
        out = bytearray(prefix)
        while True:
            h = int.from_bytes(data[pos:pos + 3], 'little')
            pos += 3
            last, btype, bsize = h & 1, (h >> 1) & 3, h >> 3
            if btype == 0:
                out += data[pos:pos + bsize]
                pos += bsize
            elif btype == 1:
                out += bytes([data[pos]]) * bsize
                pos += 1
            elif btype == 2:
                _decode_block(data[pos:pos + bsize], out, st)
                pos += bsize
            else:
                raise ZstdError('reserved block type')
            if last:
                break
        if checksum:
            pos += 4
        if fcs is not None and len(out) - len(prefix) != fcs:
            raise ZstdError('content size mismatch')
        out_all += out[len(prefix):]
    return bytes(out_all)


def decompress(data, dicts=None):
    """Decompress a .zs file. ``dicts`` is a Dictionaries (needed for most game files)."""
    data = bytes(data)
    if _std is not None:
        did = frame_dict_id(data)
        zd = None
        if did:
            d = dicts.get(did) if dicts else None
            if d is None:
                raise ZstdError('dictionary %d needed' % did)
            zd = _std.ZstdDict(d.raw)
        return _std.decompress(data, zstd_dict=zd)
    return _py_decompress(data, dicts)


def compress(data, level=9, dictionary=None):
    """Compress to a zstd frame. With Python 3.14+ this really compresses (with the dictionary if
    given); otherwise it writes raw blocks, which any zstd decoder (and the game) reads."""
    data = bytes(data)
    if _std is not None:
        zd = _std.ZstdDict(dictionary.raw) if dictionary is not None else None
        return _std.compress(data, level=level, zstd_dict=zd)
    out = bytearray(struct.pack('<I', FRAME_MAGIC))
    out.append(0xE0)                                  # single segment, 8-byte content size, no dict
    out += struct.pack('<Q', len(data))
    if not data:
        out += (1).to_bytes(3, 'little')              # last, raw, size 0
        return bytes(out)
    block = 128 * 1024
    for i in range(0, len(data), block):
        chunk = data[i:i + block]
        last = 1 if i + block >= len(data) else 0
        out += (last | (len(chunk) << 3)).to_bytes(3, 'little')
        out += chunk
    return bytes(out)
