"""RESTBL: the resource size table (System/Resource/ResourceSizeTable.*.rsizetable.zs).

The game sizes its memory for each file from this table. Entries are keyed by the CRC32 of the file's
path (sorted by CRC); paths whose CRC32 collides with another are listed by name instead.

Layout: 'RESTBL', u32 version, u32 name length (0xA0), u32 CRC entry count, u32 name entry count,
then (u32 crc, u32 size) entries, then (char[name length] path, u32 size) entries.
"""
import struct
import zlib


def path_crc(path):
    return zlib.crc32(path.encode('utf-8')) & 0xFFFFFFFF


class Restbl:
    def __init__(self):
        self.version = 1
        self.name_len = 0xA0
        self.crc = {}            # crc32 -> size
        self.names = {}          # path -> size (collision entries)

    @classmethod
    def read(cls, data):
        data = bytes(data)
        if data[:6] != b'RESTBL':
            raise ValueError('not a RESTBL file')
        self = cls()
        self.version, self.name_len, ncrc, nname = struct.unpack_from('<IIII', data, 6)
        pos = 22
        for _ in range(ncrc):
            c, size = struct.unpack_from('<II', data, pos)
            self.crc[c] = size
            pos += 8
        for _ in range(nname):
            raw = data[pos:pos + self.name_len]
            name = raw[:raw.index(b'\0')].decode('utf-8') if b'\0' in raw else raw.decode('utf-8')
            self.names[name] = struct.unpack_from('<I', data, pos + self.name_len)[0]
            pos += self.name_len + 4
        return self

    def get(self, path):
        if path in self.names:
            return self.names[path]
        return self.crc.get(path_crc(path))

    def set(self, path, size):
        if path in self.names:
            self.names[path] = size
        else:
            self.crc[path_crc(path)] = size

    def write(self):
        out = bytearray(b'RESTBL')
        out += struct.pack('<IIII', self.version, self.name_len, len(self.crc), len(self.names))
        for c in sorted(self.crc):
            out += struct.pack('<II', c, self.crc[c])
        for name in sorted(self.names, key=lambda n: n.encode('utf-8')):
            raw = name.encode('utf-8')
            out += raw + b'\0' * (self.name_len - len(raw))
            out += struct.pack('<I', self.names[name])
        return bytes(out)
