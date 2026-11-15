"""SARC archives (.pack, .sarc), little endian.

Layout: SARC header, SFAT (one node per file, sorted by name hash), SFNT (names), then file data.
Each file's alignment is remembered on read so an unchanged archive is written back byte for byte.
"""
import struct

HASH_KEY = 0x65


def name_hash(name, key=HASH_KEY):
    h = 0
    for c in name.encode('utf-8'):
        if c >= 0x80:
            c -= 0x100                                   # the game hashes signed chars
        h = (h * key + c) & 0xFFFFFFFF
    return h


def _align(n, a):
    return (n + a - 1) & -a


class Sarc:
    def __init__(self, files=None):
        self.files = dict(files or {})                   # name -> bytes
        self.align = {}                                  # name -> alignment used for its data
        self.data_align = 0x100
        self.version = 0x0100
        self.hash_key = HASH_KEY

    @classmethod
    def read(cls, data):
        data = bytes(data)
        if data[:4] != b'SARC':
            raise ValueError('not a SARC archive')
        hsize, bom = struct.unpack_from('<HH', data, 4)
        if bom != 0xFEFF:
            raise ValueError('big-endian SARC not supported')
        fsize, doff, version = struct.unpack_from('<IIH', data, 8)
        pos = hsize
        if data[pos:pos + 4] != b'SFAT':
            raise ValueError('missing SFAT')
        sfat_hsize, count, key = struct.unpack_from('<HHI', data, pos + 4)
        pos += sfat_hsize
        nodes = [struct.unpack_from('<IIII', data, pos + 16 * i) for i in range(count)]
        pos += 16 * count
        if data[pos:pos + 4] != b'SFNT':
            raise ValueError('missing SFNT')
        names_at = pos + struct.unpack_from('<H', data, pos + 4)[0]
        self = cls()
        self.version, self.hash_key = version, key
        self.data_align = _largest_pow2(doff)
        for h, attr, start, end in nodes:
            if not attr >> 24:
                raise ValueError('unnamed SARC entries are not supported')
            noff = names_at + (attr & 0xFFFFFF) * 4
            name = data[noff:data.index(b'\0', noff)].decode('utf-8')
            self.files[name] = data[doff + start:doff + end]
            self.align[name] = _largest_pow2(doff + start) if start else self.data_align
        return self

    def write(self):
        names = sorted(self.files, key=lambda n: name_hash(n, self.hash_key))
        sfnt = bytearray()
        name_off = {}
        for n in names:
            name_off[n] = len(sfnt) // 4
            sfnt += n.encode('utf-8') + b'\0'
            sfnt += b'\0' * (_align(len(sfnt), 4) - len(sfnt))
        head = 0x14 + 0xC + 16 * len(names) + 8 + len(sfnt)
        doff = _align(head, self.data_align)
        body = bytearray()
        spans = []
        for n in names:
            a = self.align.get(n, 8)
            start = _align(doff + len(body), a) - doff
            body += b'\0' * (start - len(body))
            body += self.files[n]
            spans.append((start, len(body)))
        out = bytearray()
        out += b'SARC' + struct.pack('<HHIIHH', 0x14, 0xFEFF, doff + len(body), doff, self.version, 0)
        out += b'SFAT' + struct.pack('<HHI', 0xC, len(names), self.hash_key)
        for n, (s, e) in zip(names, spans):
            out += struct.pack('<IIII', name_hash(n, self.hash_key), 0x01000000 | name_off[n], s, e)
        out += b'SFNT' + struct.pack('<HH', 8, 0) + sfnt
        out += b'\0' * (doff - len(out))
        out += body
        return bytes(out)


def _largest_pow2(n, cap=0x2000):
    if n == 0:
        return cap
    a = n & -n
    return min(a, cap)
