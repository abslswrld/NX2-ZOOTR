"""MSBT message files (inside Mals/*.sarc.zs): labels and their text.

Layout: 'MsgStdBn' header (0x20 bytes), then sections, each '<4cc>' + u32 size + 8 bytes padding, data,
padded with 0xAB to 16 bytes. LBL1 maps label -> text index through a hash table; TXT2 holds the texts
(UTF-8 in this game, UTF-16 in others; control tags start with 0x0E). ATR1 and any other section are kept
as they are.

``Msbt.texts`` is an ordered {label: text}; text is a str (decoded losslessly: control tags and their binary
parameters are kept as-is, see ``tags``). Editing a text and writing gives a valid file; an unchanged file comes back byte for byte.
"""
import struct


_CODECS = {0: ('utf-8', 'surrogateescape'), 1: ('utf-16-le', 'surrogatepass')}


def _decode(raw, encoding):
    codec, errors = _CODECS[encoding]
    return raw.decode(codec, errors)


def _encode(text, encoding):
    codec, errors = _CODECS[encoding]
    return text.encode(codec, errors)


def label_hash(label, groups):
    h = 0
    for c in label.encode('utf-8'):
        h = (h * 0x492 + c) & 0xFFFFFFFF
    return h % groups


class Msbt:
    def __init__(self):
        self.texts = {}              # label -> text, in text-index order
        self.sections = []           # [(magic, raw bytes or None for LBL1/TXT2)]
        self.groups = 101
        self.label_order = []        # labels in the order the hash table listed them
        self.version = 3
        self.encoding = 1
        self.header_pad = b'\0' * 10

    @classmethod
    def read(cls, data):
        data = bytes(data)
        if data[:8] != b'MsgStdBn':
            raise ValueError('not an MSBT file')
        bom = struct.unpack_from('<H', data, 8)[0]
        if bom != 0xFEFF:
            raise ValueError('big-endian MSBT not supported')
        self = cls()
        self.encoding, self.version = data[0xC], data[0xD]
        if self.encoding not in _CODECS:
            raise ValueError('MSBT encoding %d is not supported' % self.encoding)
        nsec = struct.unpack_from('<H', data, 0xE)[0]
        self.header_pad = data[0x16:0x20]
        pos = 0x20
        labels = {}
        texts = []
        for _ in range(nsec):
            magic = data[pos:pos + 4].decode('ascii')
            size = struct.unpack_from('<I', data, pos + 4)[0]
            body = data[pos + 0x10:pos + 0x10 + size]
            if magic == 'LBL1':
                self.groups = struct.unpack_from('<I', body, 0)[0]
                for g in range(self.groups):
                    count, off = struct.unpack_from('<II', body, 4 + 8 * g)
                    p = off
                    for _ in range(count):
                        n = body[p]
                        name = body[p + 1:p + 1 + n].decode('utf-8')
                        labels[name] = struct.unpack_from('<I', body, p + 1 + n)[0]
                        self.label_order.append(name)
                        p += 1 + n + 4
                self.sections.append((magic, None))
            elif magic == 'TXT2':
                count = struct.unpack_from('<I', body, 0)[0]
                offs = list(struct.unpack_from('<%dI' % count, body, 4)) + [len(body)]
                for i in range(count):
                    texts.append(_decode(body[offs[i]:offs[i + 1]], self.encoding))
                self.sections.append((magic, None))
            else:
                self.sections.append((magic, body))
            pos += 0x10 + size
            pos += -pos & 15
        by_index = sorted(labels.items(), key=lambda kv: kv[1])
        if [i for _, i in by_index] != list(range(len(texts))):
            raise ValueError('labels and texts do not line up')
        self.texts = {name: texts[i] for name, i in by_index}
        return self

    def write(self):
        names = list(self.texts)
        index = {n: i for i, n in enumerate(names)}
        out = bytearray()
        for magic, raw in self.sections:
            if magic == 'LBL1':
                order = [n for n in self.label_order if n in index] + [n for n in names if n not in set(self.label_order)]
                buckets = [[] for _ in range(self.groups)]
                for n in order:
                    buckets[label_hash(n, self.groups)].append(n)
                body = bytearray(struct.pack('<I', self.groups))
                p = 4 + 8 * self.groups
                for b in buckets:
                    body += struct.pack('<II', len(b), p)
                    p += sum(1 + len(n.encode('utf-8')) + 4 for n in b)
                for b in buckets:
                    for n in b:
                        raw_n = n.encode('utf-8')
                        body += bytes([len(raw_n)]) + raw_n + struct.pack('<I', index[n])
            elif magic == 'TXT2':
                enc = [_encode(self.texts[n], self.encoding) for n in names]
                body = bytearray(struct.pack('<I', len(enc)))
                p = 4 + 4 * len(enc)
                for t in enc:
                    body += struct.pack('<I', p)
                    p += len(t)
                for t in enc:
                    body += t
            else:
                body = raw
            out += magic.encode('ascii') + struct.pack('<I', len(body)) + b'\0' * 8 + body
            out += b'\xab' * (-len(out) & 15)
        head = b'MsgStdBn' + struct.pack('<HHBBHHI', 0xFEFF, 0, self.encoding, self.version, len(self.sections), 0,
                                         0x20 + len(out)) + self.header_pad
        return head + bytes(out)


def tags(text, encoding=0):
    """Split a text into plain strings and control tags (group, tag, parameter bytes).
    Tag layout: 0x0E, then u16 group, u16 tag, u16 parameter size, parameters (in code units of the encoding)."""
    if encoding == 1:
        raw, unit = text.encode('utf-16-le', 'surrogatepass'), 2
    else:
        raw, unit = text.encode('utf-8', 'surrogateescape'), 1
    out, buf, i = [], bytearray(), 0
    while i < len(raw):
        if raw[i] == 0x0E and (unit == 1 or raw[i + 1] == 0):
            if buf:
                out.append(_decode(bytes(buf), encoding))
                buf = bytearray()
            p = i + unit
            group, tag, size = struct.unpack_from('<HHH', raw, p)
            out.append((group, tag, raw[p + 6:p + 6 + size]))
            i = p + 6 + size
        else:
            buf += raw[i:i + unit]
            i += unit
    if buf:
        out.append(_decode(bytes(buf), encoding))
    return out
