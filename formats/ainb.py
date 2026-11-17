"""AINB: the game's AI, logic and sequence node graphs (.ainb, magic 'AIB '), version 0x408, little endian.

A file is a graph of nodes. Each node has a type (0 = a named node implemented in the game's code, others
are built-in selectors, sequences, module inputs/outputs...), parameters and links to other nodes:

- immediate parameters: fixed values written in the file (name, value);
- inputs: values the node reads, either a default, the output of another node (node index + output
  index), several outputs (`sources`), or a global parameter / expression (in `flags`);
- outputs: values the node gives (name only);
- links: by link type, a list of (node index, name, extra words). Type 0 carries values (bool, float...),
  2 is the flow to child nodes, 3 a resident update, 4 string values, 5 int values;
- preconditions: nodes that must run before this one (the nodes its inputs come from).

Around the nodes: commands (the entry points), global parameters (the "blackboard", with defaults and
file references), attachments (extra parameter sets hung on nodes), embedded module names, entry
strings, a replacement table and the expression block (EXB).

Layout, in file order: header (0x74), commands (0x18 each), nodes (0x3C each), global parameters, node
bodies, attachment index, attachments and their parameters, immediate parameters, input/output
parameters, multi-parameter sources, resident updates, preconditions, EXB, embedded modules, entry
strings, two hashes, replacement table, 4 zero bytes, enum table (always empty), string pool.

Written from the game's own files (this version is newer than the public notes on 0x404/0x407):
- node bodies hold (index, count) pairs into the parameter tables instead of offsets;
- global parameters have 7 types (one more, never used, between int and float).

Kept as they are, not decoded:
- the EXB expression block (`exb`, raw bytes; it has its own header and strings);
- the string pool: read strings stay at their place, new strings are added at the end, so an unchanged
  file is written back byte for byte and string offsets inside undecoded words stay valid;
- the extra words of links (`Link.extra`), flags of parameters, and attachment/replacement fields are
  stored as numbers; `tools/ainb_dump.py` names the ones that are understood.
"""
import struct

VERSION = 0x408
PARAM_TYPES = ('int', 'bool', 'float', 'string', 'vec3f', 'userdefined')
GLOBAL_TYPES = ('string', 'int', 'type2', 'float', 'bool', 'vec3f', 'userdefined')
_GLOBAL_SIZE = {'string': 4, 'int': 4, 'type2': 4, 'float': 4, 'bool': 4, 'vec3f': 12, 'userdefined': 0}
LINK_TYPES = 10
NODE_TYPES = {
    0: 'UserDefined', 1: 'Element_S32Selector', 2: 'Element_Sequential', 3: 'Element_Simultaneous',
    4: 'Element_F32Selector', 5: 'Element_StringSelector', 6: 'Element_RandomSelector',
    7: 'Element_BoolSelector', 8: 'Element_Fork', 9: 'Element_Join', 10: 'Element_Alert',
    20: 'Element_Expression', 100: 'Element_ModuleIF_Input_S32', 101: 'Element_ModuleIF_Input_F32',
    102: 'Element_ModuleIF_Input_Vec3f', 103: 'Element_ModuleIF_Input_String',
    104: 'Element_ModuleIF_Input_Bool', 105: 'Element_ModuleIF_Input_Ptr',
    200: 'Element_ModuleIF_Output_S32', 201: 'Element_ModuleIF_Output_F32',
    202: 'Element_ModuleIF_Output_Vec3f', 203: 'Element_ModuleIF_Output_String',
    204: 'Element_ModuleIF_Output_Bool', 205: 'Element_ModuleIF_Output_Ptr',
    300: 'Element_ModuleIF_Child', 400: 'Element_StateEnd', 500: 'Element_SplitTiming',
}


class AinbError(ValueError):
    pass


def _check(ok, what):
    if not ok:
        raise AinbError(what)


class Command:
    """An entry point: a name and the node it starts (`left`; `right` is a second node index)."""
    def __init__(self, name, guid, left, right):
        self.name, self.guid, self.left, self.right = name, guid, left, right


class Immediate:
    """A fixed value. `flags`: 0 = plain value; 0x8000nnnn = taken from global parameter nnnn of the same
    type; 0xC200nnnn = result of expression nnnn of the EXB block. A userdefined parameter has a class
    name (`cls`) and no value."""
    def __init__(self, name, value, flags=0, cls=None):
        self.name, self.value, self.flags, self.cls = name, value, flags, cls


class Input:
    """A value read by a node. `node`/`param` point at another node's output (-1 = none, `value` is then
    the default). `sources` lists several (node, param, flags) when the input takes more than one.
    `flags`: as for Immediate (0x8000nnnn global parameter, 0xC200nnnn expression; 0x8400/0x8800/0x8C00
    seem to pick one component of a vec3f global), or 0x0080/0x0180 on inputs with nothing linked."""
    def __init__(self, name, value, node=-1, param=0, flags=0, cls=None, sources=None):
        self.name, self.value, self.node, self.param, self.flags, self.cls = name, value, node, param, flags, cls
        self.sources = sources


class Output:
    def __init__(self, name, flag=False, cls=None):
        self.name, self.flag, self.cls = name, flag, cls


class Link:
    """A link to another node. `extra` is a tuple of 32-bit words whose meaning depends on the node and
    link type (selector conditions, string offsets into the pool...). For link type 3 (resident update)
    `name` is None and `extra` holds the index into `Ainb.resident`."""
    def __init__(self, node, name, extra=()):
        self.node, self.name, self.extra = node, name, tuple(extra)


class Node:
    def __init__(self, type=0, name=''):
        self.type = type
        self.name = name
        self.flags = 0
        self.name_hash = 0
        self.guid = b'\0' * 16
        self.exb_count = 0
        self.exb_size = 0
        self.attachments = []                            # indices into Ainb.attachments
        self.preconditions = []                          # node indices
        self.precondition_slot = None                    # where its block sits in the file's table (kept
                                                         # as read; None = after the others)
        self.immediates = {t: [] for t in PARAM_TYPES}
        self.inputs = {t: [] for t in PARAM_TYPES}
        self.outputs = {t: [] for t in PARAM_TYPES}
        self.links = [[] for _ in range(LINK_TYPES)]

    @property
    def type_name(self):
        return NODE_TYPES.get(self.type, 'Type%d' % self.type)


class GlobalParam:
    """A global ("blackboard") parameter. `flags`: 2 low bits kept from the file. `file`: index into
    `Ainb.global_files` or None."""
    def __init__(self, name, default, notes='', flags=2, file=None):
        self.name, self.default, self.notes, self.flags, self.file = name, default, notes, flags, file


class Attachment:
    """A parameter set hung on nodes: a name and immediate parameters. `head` and `tail` are undecoded
    words kept as read (always 0 in the game's files)."""
    def __init__(self, name):
        self.name = name
        self.name_hash = 0
        self.exb_count = 0
        self.exb_size = 0
        self.head = 0
        self.tail = (0,) * 6
        self.immediates = {t: [] for t in PARAM_TYPES}


class Ainb:
    def __init__(self):
        self.version = VERSION
        self.filename = ''
        self.category = 'AI'
        self.category_id = 0
        self.commands = []
        self.nodes = []
        self.globals = {t: [] for t in GLOBAL_TYPES}
        self.global_files = []                           # (name, hash, hash, hash)
        self.attachments = []
        self.resident = []                               # (flags,) or (flags, string offset)
        self.exb = b''
        self.modules = []                                # (path, category, count)
        self.entry_strings = []                          # (node index, string, string)
        self.hashes = (0, 0)
        self.replace_head = (0, 0, 0, -1)                # u8, u8, s16 node count, s16 attachment count
        self.replacements = []                           # tuples of four 16-bit words
        self.output_count = 0                            # header word 0x1C, kept as read (in most files
                                                         # the number of module output nodes, 200-205)
        self.strings = b''                               # the string pool, kept as read
        self._str_index = None

    # ---- strings ----
    def _str(self, off):
        end = self.strings.find(b'\0', off)
        _check(0 <= off < len(self.strings) and end >= 0, 'string offset 0x%x outside the pool' % off)
        return self.strings[off:end].decode('utf-8')

    def _off(self, s):
        """Offset of a string in the pool; added at the end if it isn't there."""
        if self._str_index is None:
            self._str_index = {}
            pos = 0
            for part in self.strings.split(b'\0')[:-1]:
                self._str_index.setdefault(part, pos)
                pos += len(part) + 1
        raw = s.encode('utf-8')
        off = self._str_index.get(raw)
        if off is None:
            off = self._str_index[raw] = len(self.strings)
            self.strings += raw + b'\0'
        return off

    def string_at(self, off):
        """The pool string at an offset (for words of `Link.extra` that are strings)."""
        return self._str(off)

    # ---- reading ----
    @classmethod
    def read(cls, data):
        data = bytes(data)
        _check(data[:4] == b'AIB ', 'not an AINB file')
        h = struct.unpack_from('<28I', data, 4)
        (version, fname, ncmd, nnode, nprec, natt, nout, o_glob, o_str, o_enum, o_imm, o_resid, o_io,
         o_multi, o_att, o_attidx, o_exb, o_repl, o_prec, o_x50, x54, x58, o_embed, catname, cat,
         o_entry, o_x6c, o_hash) = h
        _check(version == VERSION, 'AINB version 0x%x not supported' % version)
        _check(x54 == 0 and x58 == 0 and o_x50 == o_resid, 'unexpected header words')
        self = cls()
        self.strings = data[o_str:]
        _check(self.strings.endswith(b'\0'), 'string pool not terminated')
        u32 = lambda o: struct.unpack_from('<I', data, o)[0]
        S = self._str
        self.filename, self.category, self.category_id = S(fname), S(catname), cat
        self.output_count = nout

        pos = 0x74
        for _ in range(ncmd):
            name, guid, left, right = struct.unpack_from('<I16sHH', data, pos)
            self.commands.append(Command(S(name), guid, left, right))
            pos += 0x18

        # node table
        raw_nodes = []
        for i in range(nnode):
            (ntype, idx, n_att, flags, name, nhash, z10, body, exb_count, exb_size, n_multi, z1e,
             att_base, prec_base, n_prec, z28, guid) = struct.unpack_from('<HHHHIIIIHHHHIHHI16s', data, pos)
            _check(idx == i and z10 == 0 and z1e == 0 and z28 == 0, 'unexpected node header')
            n = Node(ntype, S(name))
            n.flags, n.name_hash, n.guid, n.exb_count, n.exb_size = flags, nhash, guid, exb_count, exb_size
            raw_nodes.append((n, body, n_att, att_base, prec_base, n_prec, n_multi))
            self.nodes.append(n)
            pos += 0x3C
        _check(pos == o_glob, 'global parameters not after the nodes')

        # global parameters
        heads = [struct.unpack_from('<HHHH', data, pos + 8 * t) for t in range(7)]
        total = sum(c for c, _, _, _ in heads)
        entries = pos + 0x38
        values = entries + 8 * total
        run = size = 0
        max_file = -1
        for t, (count, index, off, pad) in zip(GLOBAL_TYPES, heads):
            _check(index == run and off == size and pad == 0, 'unexpected global parameter header')
            for k in range(count):
                e, notes = struct.unpack_from('<II', data, entries + 8 * (run + k))
                at = values + size + _GLOBAL_SIZE[t] * k
                if t == 'string':
                    default = S(u32(at))
                elif t == 'float':
                    default = struct.unpack_from('<f', data, at)[0]
                elif t == 'vec3f':
                    default = struct.unpack_from('<3f', data, at)
                elif t == 'bool':
                    default = _bool(u32(at))
                elif t == 'userdefined':
                    default = None
                else:
                    default = struct.unpack_from('<i', data, at)[0]
                file = (e >> 24) & 0x7F if e >> 31 else None
                _check(e >> 31 or not (e >> 24), 'unexpected global parameter flags')
                if file is not None:
                    max_file = max(max_file, file)
                self.globals[t].append(GlobalParam(S(e & 0x3FFFFF), default, S(notes), (e >> 22) & 3, file))
            run += count
            size += _GLOBAL_SIZE[t] * count
        pos = values + size
        for _ in range(max_file + 1):
            name, h1, h2, h3 = struct.unpack_from('<IIII', data, pos)
            self.global_files.append((S(name), h1, h2, h3))
            pos += 16
        bodies_end = min(o_attidx, o_att, o_imm)
        _check(pos == (raw_nodes[0][1] if raw_nodes else bodies_end), 'global parameters end at 0x%x' % pos)

        # node bodies: (index, count) pairs and links
        counts = []                                      # per node or attachment: 18 (index, count) pairs
        att_run = prec_run = 0
        n_att_idx = sum(r[2] for r in raw_nodes)
        att_idx = struct.unpack_from('<%dI' % n_att_idx, data, o_attidx)
        n_prec_all = sum(r[5] for r in raw_nodes)
        _check(o_prec + 4 * n_prec_all == (o_exb or o_embed), 'precondition table size')
        prec = struct.unpack_from('<%dH' % (2 * n_prec_all), data, o_prec)
        _check(not any(prec[1::2]), 'unexpected precondition entry')
        _check(sum(1 for r in raw_nodes if r[0].flags & 1) == nprec, 'precondition node count in the header')
        for i, (n, body, n_att, att_base, prec_base, n_prec, n_multi) in enumerate(raw_nodes):
            _check(body == pos, 'node body %d not where expected' % i)
            counts.append(struct.unpack_from('<36I', data, pos))
            pos += 0x90
            lc = struct.unpack_from('<20B', data, pos)
            pos += 0x14
            total = sum(lc[0::2])
            offs = struct.unpack_from('<%dI' % total, data, pos) if total else ()
            pos += 4 * total
            end = raw_nodes[i + 1][1] if i + 1 < nnode else bodies_end
            bounds = offs + (end,)
            run = 0
            for lt in range(LINK_TYPES):
                _check(lc[2 * lt + 1] == run, 'unexpected link index')
                for j in range(run, run + lc[2 * lt]):
                    _check(bounds[j] == pos and bounds[j + 1] - pos >= 8 and (bounds[j + 1] - pos) % 4 == 0,
                           'unexpected link entry')
                    w = struct.unpack_from('<%dI' % ((bounds[j + 1] - pos) // 4), data, pos)
                    if lt == 3:
                        n.links[lt].append(Link(w[0], None, w[1:]))
                    else:
                        n.links[lt].append(Link(w[0], S(w[1]), w[2:]))
                    pos = bounds[j + 1]
                run += lc[2 * lt]
            _check(pos == end, 'node body %d size' % i)
            _check(att_base == att_run, 'unexpected attachment index')
            n.attachments = list(att_idx[att_run:att_run + n_att])
            att_run += n_att
            _check(prec_base + n_prec <= n_prec_all and (n_prec or prec_base == 0), 'unexpected precondition index')
            n.preconditions = list(prec[2 * prec_base:2 * (prec_base + n_prec):2])
            n.precondition_slot = prec_base if n_prec else None

        # attachments
        _check(o_attidx + 4 * n_att_idx == o_att, 'attachment index size')
        pos = o_att + 16 * natt
        for k in range(natt):
            name, off, exb_count, exb_size, nhash = struct.unpack_from('<IIHHI', data, o_att + 16 * k)
            _check(off == pos, 'attachment parameters not where expected')
            a = Attachment(S(name))
            a.name_hash, a.exb_count, a.exb_size = nhash, exb_count, exb_size
            w = struct.unpack_from('<25I', data, pos)
            a.head = w[0]
            counts.append(w[1:13])
            _check(all(x == pos + 100 for x in w[14::2]), 'unexpected attachment words')
            a.tail = w[13::2]
            self.attachments.append(a)
            pos += 100
        _check(pos == o_imm, 'attachment section size')

        # immediate parameters
        owners = [r[0] for r in raw_nodes] + self.attachments
        starts = struct.unpack_from('<6I', data, o_imm)
        pos = o_imm + 24
        for t, tname in enumerate(PARAM_TYPES):
            _check(starts[t] == pos, 'immediate table %s not where expected' % tname)
            n_all = sum(c[2 * t + 1] for c in counts)
            end = starts[t + 1] if t < 5 else o_io
            size = 20 if t == 4 else 12
            _check(end - pos == size * n_all, 'immediate table %s size' % tname)
            run = 0
            for owner, c in zip(owners, counts):
                _check(c[2 * t] == run, 'unexpected immediate index (%s)' % tname)
                for _ in range(c[2 * t + 1]):
                    if t == 5:
                        name, cname, flags = struct.unpack_from('<III', data, pos)
                        owner.immediates[tname].append(Immediate(S(name), None, flags, S(cname)))
                    else:
                        name, flags = struct.unpack_from('<II', data, pos)
                        owner.immediates[tname].append(Immediate(S(name), self._value(data, pos + 8, t), flags))
                    pos += size
                run += c[2 * t + 1]

        # multi-parameter sources
        n_multi_all = (o_resid - o_multi) // 8
        _check(o_multi + 8 * n_multi_all == o_resid, 'multi-parameter table size')
        multi = [struct.unpack_from('<hhI', data, o_multi + 8 * k) for k in range(n_multi_all)]
        multi_run = 0

        # inputs and outputs
        starts = struct.unpack_from('<12I', data, o_io)
        pos = o_io + 48
        node_multi = [0] * nnode
        for t, tname in enumerate(PARAM_TYPES):
            # inputs
            _check(starts[2 * t] == pos, 'input table %s not where expected' % tname)
            size = {4: 24, 5: 20}.get(t, 16)
            n_all = sum(c[12 + 4 * t + 1] for c in counts[:nnode])
            _check(starts[2 * t + 1] - pos == size * n_all, 'input table %s size' % tname)
            run = 0
            for i, (owner, c) in enumerate(zip(self.nodes, counts)):
                _check(c[12 + 4 * t] == run, 'unexpected input index (%s)' % tname)
                for _ in range(c[12 + 4 * t + 1]):
                    if t == 5:
                        name, cname, node, param, flags, value = struct.unpack_from('<IIhhII', data, pos)
                        inp = Input(S(name), value, node, param, flags, S(cname))
                    else:
                        name, node, param, flags = struct.unpack_from('<IhhI', data, pos)
                        inp = Input(S(name), self._value(data, pos + 12, t), node, param, flags)
                    if node <= -100:                     # several sources, numbered in table order
                        _check(-100 - node == multi_run, 'unexpected multi-parameter index')
                        inp.sources = multi[multi_run:multi_run + param]
                        multi_run += param
                        node_multi[i] += param
                        inp.node, inp.param = -1, 0
                    owner.inputs[tname].append(inp)
                    pos += size
                run += c[12 + 4 * t + 1]
            # outputs
            _check(starts[2 * t + 1] == pos, 'output table %s not where expected' % tname)
            size = 8 if t == 5 else 4
            n_all = sum(c[14 + 4 * t + 1] for c in counts[:nnode])
            end = starts[2 * t + 2] if t < 5 else o_multi
            _check(end - pos == size * n_all, 'output table %s size' % tname)
            run = 0
            for owner, c in zip(self.nodes, counts):
                _check(c[14 + 4 * t] == run, 'unexpected output index (%s)' % tname)
                for _ in range(c[14 + 4 * t + 1]):
                    name = u32(pos)
                    owner.outputs[tname].append(Output(S(name & 0x7FFFFFFF), bool(name >> 31),
                                                       S(u32(pos + 4)) if t == 5 else None))
                    pos += size
                run += c[14 + 4 * t + 1]
        _check(multi_run == n_multi_all, 'unused multi-parameter sources')
        for i, r in enumerate(raw_nodes):
            _check(node_multi[i] == r[6], 'multi-parameter count of node %d' % i)

        # resident updates
        pos = o_resid
        if o_prec > o_resid:
            n_res = (u32(o_resid) - o_resid) // 4
            offs = struct.unpack_from('<%dI' % n_res, data, o_resid) + (o_prec,)
            pos += 4 * n_res
            for k in range(n_res):
                _check(offs[k] == pos and offs[k + 1] > pos, 'unexpected resident update entry')
                self.resident.append(struct.unpack_from('<%dI' % ((offs[k + 1] - pos) // 4), data, pos))
                pos = offs[k + 1]
        _check(pos == o_prec, 'resident update section size')

        if o_exb:
            _check(data[o_exb:o_exb + 4] == b'EXB ', 'EXB block not where expected')
            self.exb = data[o_exb:o_embed]

        pos = o_embed
        for k in range(u32(pos)):
            path, mcat, count = struct.unpack_from('<III', data, pos + 4 + 12 * k)
            self.modules.append((S(path), S(mcat), count))
        pos += 4 + 12 * len(self.modules)
        _check(pos == o_entry, 'embedded module section size')
        for k in range(u32(pos)):
            node, s1, s2 = struct.unpack_from('<III', data, pos + 4 + 12 * k)
            self.entry_strings.append((node, S(s1), S(s2)))
        pos += 4 + 12 * len(self.entry_strings)
        _check(pos == o_hash and o_repl == pos + 8, 'entry string section size')
        self.hashes = struct.unpack_from('<II', data, pos)
        b0, b1, count, n_nodes, n_atts = struct.unpack_from('<BBHhh', data, o_repl)
        self.replace_head = (b0, b1, n_nodes, n_atts)
        self.replacements = [struct.unpack_from('<4H', data, o_repl + 8 + 8 * k) for k in range(count)]
        _check(o_repl + 8 + 8 * count == o_x6c and o_enum == o_x6c + 4 and o_str == o_enum + 4
               and u32(o_x6c) == 0 and u32(o_enum) == 0, 'unexpected end sections')
        return self

    def _value(self, data, pos, t):
        if t == 2:
            return struct.unpack_from('<f', data, pos)[0]
        if t == 3:
            return self._str(struct.unpack_from('<I', data, pos)[0])
        if t == 4:
            return struct.unpack_from('<3f', data, pos)
        if t == 1:
            return _bool(struct.unpack_from('<I', data, pos)[0])
        return struct.unpack_from('<i', data, pos)[0]

    def _pack_value(self, value, t):
        if t == 2:
            return struct.pack('<f', value)
        if t == 3:
            return struct.pack('<I', self._off(value))
        if t == 4:
            return struct.pack('<3f', *value)
        if t == 1:
            return struct.pack('<I', int(value))
        return struct.pack('<i', value)

    # ---- writing ----
    def write(self):
        O = self._off
        owners = self.nodes + self.attachments
        nnode, natt = len(self.nodes), len(self.attachments)

        # global parameters
        heads, entries, values = bytearray(), bytearray(), bytearray()
        run = 0
        for t in GLOBAL_TYPES:
            params = self.globals[t]
            heads += struct.pack('<HHHH', len(params), run, len(values), 0)
            run += len(params)
            for p in params:
                e = O(p.name) | (p.flags & 3) << 22
                if p.file is not None:
                    e |= 0x80000000 | p.file << 24
                entries += struct.pack('<II', e, O(p.notes))
                if t == 'string':
                    values += struct.pack('<I', O(p.default))
                elif t == 'float':
                    values += struct.pack('<f', p.default)
                elif t == 'vec3f':
                    values += struct.pack('<3f', *p.default)
                elif t == 'bool':
                    values += struct.pack('<I', int(p.default))
                elif t != 'userdefined':
                    values += struct.pack('<i', p.default)
        glob = heads + entries + values
        for name, h1, h2, h3 in self.global_files:
            glob += struct.pack('<IIII', O(name), h1, h2, h3)

        # parameter tables and the (index, count) pairs of every node and attachment
        imm = [bytearray() for _ in PARAM_TYPES]
        inp = [bytearray() for _ in PARAM_TYPES]
        out = [bytearray() for _ in PARAM_TYPES]
        n_imm = [0] * 6
        multi = bytearray()
        pairs = []
        for owner in owners:
            p = []
            for t, tname in enumerate(PARAM_TYPES):
                params = owner.immediates[tname]
                p += [n_imm[t], len(params)]
                n_imm[t] += len(params)
                for x in params:
                    if t == 5:
                        imm[t] += struct.pack('<III', O(x.name), O(x.cls or ''), x.flags)
                    else:
                        imm[t] += struct.pack('<II', O(x.name), x.flags) + self._pack_value(x.value, t)
            pairs.append(p)
        node_multi = [0] * nnode
        for t, tname in enumerate(PARAM_TYPES):
            n_in = n_out = 0
            for i, n in enumerate(self.nodes):
                pairs[i] += [n_in, len(n.inputs[tname]), n_out, len(n.outputs[tname])]
                n_in += len(n.inputs[tname])
                n_out += len(n.outputs[tname])
                for x in n.inputs[tname]:
                    node, param = x.node, x.param
                    if x.sources is not None:
                        node, param = -100 - len(multi) // 8, len(x.sources)
                        node_multi[i] += param
                        for s in x.sources:
                            multi += struct.pack('<hhI', *s)
                    if t == 5:
                        inp[t] += struct.pack('<IIhhII', O(x.name), O(x.cls or ''), node, param, x.flags, x.value)
                    else:
                        inp[t] += struct.pack('<IhhI', O(x.name), node, param, x.flags) + self._pack_value(x.value, t)
                for x in n.outputs[tname]:
                    out[t] += struct.pack('<I', O(x.name) | (0x80000000 if x.flag else 0))
                    if t == 5:
                        out[t] += struct.pack('<I', O(x.cls or ''))

        # node bodies
        o_cmd = 0x74
        o_nodes = o_cmd + 0x18 * len(self.commands)
        o_glob = o_nodes + 0x3C * nnode
        pos = o_glob + len(glob)
        bodies = bytearray()
        body_at = []
        for i, n in enumerate(self.nodes):
            body_at.append(pos + len(bodies))
            b = bytearray(struct.pack('<36I', *pairs[i]))
            run = 0
            for links in n.links:
                b += struct.pack('<BB', len(links), run)
                run += len(links)
            at = body_at[-1] + len(b) + 4 * run
            ent = bytearray()
            for lt, links in enumerate(n.links):
                for ln in links:
                    b += struct.pack('<I', at + len(ent))
                    if lt == 3:
                        ent += struct.pack('<%dI' % (1 + len(ln.extra)), ln.node, *ln.extra)
                    else:
                        ent += struct.pack('<II%dI' % len(ln.extra), ln.node, O(ln.name), *ln.extra)
            bodies += b + ent
        o_attidx = pos + len(bodies)
        attidx = b''.join(struct.pack('<I', a) for n in self.nodes for a in n.attachments)
        o_att = o_attidx + len(attidx)
        o_imm = o_att + 116 * natt
        att = bytearray()
        for k, a in enumerate(self.attachments):
            att += struct.pack('<IIHHI', O(a.name), o_att + 16 * natt + 100 * k, a.exb_count, a.exb_size, a.name_hash)
        for k, a in enumerate(self.attachments):
            att += struct.pack('<13I', a.head, *pairs[nnode + k])
            for x in a.tail:
                att += struct.pack('<II', x, o_att + 16 * natt + 100 * (k + 1))

        imm_sec = bytearray()
        at = o_imm + 24
        for t in range(6):
            imm_sec += struct.pack('<I', at)
            at += len(imm[t])
        imm_sec += b''.join(imm)
        o_io = o_imm + len(imm_sec)
        io_sec = bytearray()
        at = o_io + 48
        for t in range(6):
            io_sec += struct.pack('<I', at)
            at += len(inp[t])
            io_sec += struct.pack('<I', at)
            at += len(out[t])
        for t in range(6):
            io_sec += inp[t] + out[t]
        o_multi = o_io + len(io_sec)
        o_resid = o_multi + len(multi)
        resid = bytearray()
        at = o_resid + 4 * len(self.resident)
        for w in self.resident:
            resid += struct.pack('<I', at)
            at += 4 * len(w)
        for w in self.resident:
            resid += struct.pack('<%dI' % len(w), *w)
        o_prec = o_resid + len(resid)
        order = sorted((i for i, n in enumerate(self.nodes) if n.preconditions),
                       key=lambda i: (self.nodes[i].precondition_slot is None, self.nodes[i].precondition_slot or 0, i))
        prec = bytearray()
        prec_base = {}
        for i in order:
            prec_base[i] = len(prec) // 4
            for p in self.nodes[i].preconditions:
                prec += struct.pack('<HH', p, 0)
        o_exb = o_prec + len(prec)
        o_embed = o_exb + len(self.exb)
        embed = struct.pack('<I', len(self.modules))
        for path, mcat, count in self.modules:
            embed += struct.pack('<III', O(path), O(mcat), count)
        o_entry = o_embed + len(embed)
        entry = struct.pack('<I', len(self.entry_strings))
        for node, s1, s2 in self.entry_strings:
            entry += struct.pack('<III', node, O(s1), O(s2))
        o_hash = o_entry + len(entry)
        o_repl = o_hash + 8
        b0, b1, n_nodes, n_atts = self.replace_head
        repl = struct.pack('<BBHhh', b0, b1, len(self.replacements), n_nodes, n_atts)
        for r in self.replacements:
            repl += struct.pack('<4H', *r)
        o_x6c = o_repl + len(repl)
        o_enum = o_x6c + 4
        o_str = o_enum + 4

        # commands and node table (after everything else, so every string is in the pool)
        cmds = b''.join(struct.pack('<I16sHH', O(c.name), c.guid, c.left, c.right) for c in self.commands)
        table = bytearray()
        att_run = 0
        for i, n in enumerate(self.nodes):
            table += struct.pack('<HHHHIIIIHHHHIHHI16s', n.type, i, len(n.attachments), n.flags, O(n.name),
                                 n.name_hash, 0, body_at[i], n.exb_count, n.exb_size, node_multi[i], 0,
                                 att_run, prec_base.get(i, 0),
                                 len(n.preconditions), 0, n.guid)
            att_run += len(n.attachments)
        header = b'AIB ' + struct.pack(
            '<28I', self.version, O(self.filename), len(self.commands), nnode, sum(1 for n in self.nodes if n.flags & 1), natt,
            self.output_count, o_glob, o_str, o_enum, o_imm, o_resid, o_io, o_multi, o_att, o_attidx,
            o_exb if self.exb else 0, o_repl, o_prec, o_resid, 0, 0, o_embed, O(self.category),
            self.category_id, o_entry, o_x6c, o_hash)
        return b''.join((header, cmds, table, glob, bodies, attidx, att, imm_sec, io_sec, multi, resid, prec,
                         self.exb, embed, entry, struct.pack('<II', *self.hashes), repl, b'\0' * 8,
                         self.strings))


def _bool(v):
    return bool(v) if v in (0, 1) else v


def loads(data):
    return Ainb.read(data)


def dumps(doc):
    return doc.write()
