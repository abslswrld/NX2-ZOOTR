"""Print an AINB (AI / logic / sequence graph) as readable text. Reads only.

    python tools/ainb_dump.py <file.ainb>
    python tools/ainb_dump.py <romfs> Logic/KokiriForest_Common_Level_All_01_6aaf.logic.module.ainb
    python tools/ainb_dump.py <romfs> Pack/AI.Global.Product.111.pack.zs/AI/PouchContent.event.root.ainb
    python tools/ainb_dump.py <romfs> --find Shop_Item_Base      list the packs holding files with that name

A path may go through packs (`<pack>.pack.zs/<file inside>`); `.zs` files are decompressed.
For each node: its parameters (imm = fixed value, in = input, out = output) and its links.
`<- [n].Name` means the value comes from that output of node n; `global`, `expression` say where a value
comes from instead of the file.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from formats import zstd, sarc, ainb  # noqa: E402

LINK_NAMES = {0: 'value', 2: 'flow', 3: 'resident', 4: 'string', 5: 'int'}
GLOBAL_OF = {'int': 'int', 'bool': 'bool', 'float': 'float', 'string': 'string', 'vec3f': 'vec3f',
             'userdefined': 'userdefined'}


def open_path(romfs, rel):
    """Bytes of a romfs file; `rel` may continue inside packs."""
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    parts = rel.replace('\\', '/').split('/')
    for i in range(len(parts), 0, -1):
        p = os.path.join(romfs, *parts[:i])
        if os.path.isfile(p):
            data = open(p, 'rb').read()
            if p.endswith('.zs'):
                data = zstd.decompress(data, dicts)
            inner = '/'.join(parts[i:])
            if inner:
                data = sarc.Sarc.read(data).files[inner]
                if inner.endswith('.zs'):
                    data = zstd.decompress(data, dicts)
            return data
    raise FileNotFoundError(rel)


def find(romfs, text):
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    for dp, _, fns in os.walk(romfs):
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, romfs).replace('\\', '/')
            if fn.endswith(('.ainb', '.ainb.zs')):
                if text in fn:
                    print(rel)
            elif '.pack' in fn or '.sarc' in fn:
                raw = open(p, 'rb').read()
                if fn.endswith('.zs'):
                    raw = zstd.decompress(raw, dicts)
                try:
                    names = sarc.Sarc.read(raw).files
                except ValueError:
                    continue
                for n in names:
                    if text in n and '.ainb' in n:
                        print(rel + '/' + n)


def _source(doc, tname, flags):
    hi, lo = flags >> 16, flags & 0xFFFF
    if hi & 0xFF00 == 0xC200:
        return 'expression %d' % lo
    if hi & 0x8000:
        part = {0x8400: '.x', 0x8800: '.y', 0x8C00: '.z'}.get(hi & 0xFC00, '')
        gt = 'vec3f' if part else GLOBAL_OF[tname]
        params = doc.globals[gt]
        return 'global %s%s' % (params[lo].name if lo < len(params) else '#%d' % lo, part)
    return None


def _fmt(v):
    if isinstance(v, str):
        return '"%s"' % v
    if isinstance(v, float):
        return '%g' % v
    if isinstance(v, tuple):
        return '(' + ', '.join('%g' % x for x in v) + ')'
    return str(v)


def _out_name(doc, tname, node, param):
    if 0 <= node < len(doc.nodes):
        outs = doc.nodes[node].outputs[tname]
        n = doc.nodes[node]
        return '[%d].%s (%s)' % (node, outs[param].name if 0 <= param < len(outs) else '#%d' % param,
                                 n.name or n.type_name)
    return '[%d].#%d' % (node, param)


def _extra(doc, node, lt, extra, last=False):
    """The extra words of a link, with the ones known to be strings or numbers shown as such."""
    if not extra:
        return ''
    t = node.type
    if lt == 2 and t == 5 or lt == 4:                    # string selector condition, string value
        return '  ' + ' '.join(['%d' % extra[0]] + ['"%s"' % doc.string_at(w) for w in extra[1:]])
    if lt == 2 and t in (4, 6):                          # float selector range, random weight
        return '  ' + ' '.join('%g' % struct.unpack('<f', struct.pack('<I', w))[0] if w else '0' for w in extra)
    if lt == 2 and t == 1:                               # int selector condition
        if last:                                         # the last child of an int selector is the default
            return '  otherwise'
        return '  when %d' % struct.unpack('<i', struct.pack('<I', extra[1]))[0]
    return '  ' + ' '.join('%d' % w if w < 0x10000 else '0x%x' % w for w in extra)


def dump(doc, out=sys.stdout):
    w = lambda s='': out.write(s + '\n')
    w('%s  (%s, version 0x%x)' % (doc.filename, doc.category, doc.version))
    w('%d commands, %d nodes, %d attachments, %d embedded modules, EXB %d bytes'
      % (len(doc.commands), len(doc.nodes), len(doc.attachments), len(doc.modules), len(doc.exb)))
    if doc.commands:
        w()
        w('Commands (entry points):')
        for c in doc.commands:
            w('  %-40s -> node %d%s' % (c.name, c.left, '' if c.right in (0, 0xFFFF) else ', %d' % c.right))
    if any(doc.globals.values()):
        w()
        w('Global parameters:')
        for t in ainb.GLOBAL_TYPES:
            for i, g in enumerate(doc.globals[t]):
                file = '  (file %s)' % doc.global_files[g.file][0] if g.file is not None else ''
                d = '' if t == 'userdefined' else ' = ' + _fmt(g.default)
                w('  %-11s %d %s%s%s%s' % (t, i, g.name, d, file, '  // ' + g.notes if g.notes else ''))
    if doc.modules:
        w()
        w('Embedded modules:')
        for path, cat, count in doc.modules:
            w('  %s (%s) x%d' % (path, cat, count))
    if doc.entry_strings:
        w()
        w('Entry strings:')
        for node, s1, s2 in doc.entry_strings:
            w('  node %d: %s / %s' % (node, s1, s2))
    if doc.attachments:
        w()
        w('Attachments:')
        for i, a in enumerate(doc.attachments):
            w('  {%d} %s' % (i, a.name))
            for t in ainb.PARAM_TYPES:
                for x in a.immediates[t]:
                    w('      imm  %-6s %s = %s' % (t, x.name, _source(doc, t, x.flags) or _fmt(x.value)))
    w()
    w('Nodes:')
    for i, n in enumerate(doc.nodes):
        flags = [name for bit, name in ((1, 'precondition'), (2, 'flag2'), (4, 'flag4'), (8, 'flag8')) if n.flags & bit]
        w('[%d] %s%s%s' % (i, n.name or n.type_name, '  (%s)' % n.type_name if n.name and n.type else '',
                           '  {%s}' % ', '.join(flags) if flags else ''))
        if n.attachments:
            w('    attachments: ' + ', '.join('{%d} %s' % (a, doc.attachments[a].name) for a in n.attachments))
        for t in ainb.PARAM_TYPES:
            for x in n.immediates[t]:
                v = _source(doc, t, x.flags) or (x.cls if t == 'userdefined' else _fmt(x.value))
                w('    imm  %-6s %s = %s' % (t[:6], x.name, v))
        for t in ainb.PARAM_TYPES:
            for x in n.inputs[t]:
                src = _source(doc, t, x.flags)
                if x.sources is not None:
                    v = '<- ' + ', '.join(_out_name(doc, t, s[0], s[1]) if s[0] >= 0 else '?' for s in x.sources)
                elif x.node >= 0:
                    v = '<- ' + _out_name(doc, t, x.node, x.param) + (' / ' + src if src else '')
                elif src:
                    v = '<- ' + src
                else:
                    v = '= ' + (x.cls if t == 'userdefined' else _fmt(x.value))
                w('    in   %-6s %s %s' % (t[:6], x.name, v))
        for t in ainb.PARAM_TYPES:
            for x in n.outputs[t]:
                w('    out  %-6s %s%s' % (t[:6], x.name, '  (%s)' % x.cls if x.cls else ''))
        for lt, links in enumerate(n.links):
            for k, ln in enumerate(links):
                target = doc.nodes[ln.node] if ln.node < len(doc.nodes) else None
                tn = (target.name or target.type_name) if target else '?'
                if lt == 3:
                    r = doc.resident[ln.extra[0]] if ln.extra and ln.extra[0] < len(doc.resident) else ()
                    info = ' '.join(['0x%x' % r[0]] + ['"%s"' % doc.string_at(x) for x in r[1:]]) if r else ''
                    w('    link %-8s -> [%d] %s  %s' % ('resident', ln.node, tn, info))
                else:
                    w('    link %-8s %s -> [%d] %s%s' % (LINK_NAMES.get(lt, 'type%d' % lt), ln.name or '""', ln.node, tn,
                                                         _extra(doc, n, lt, ln.extra, k == len(links) - 1)))
        if n.preconditions:
            w('    after: ' + ', '.join('[%d]' % p for p in n.preconditions))
    if doc.replacements:
        w()
        w('Replacement table: %d entries (type, node, index, replacement): %s'
          % (len(doc.replacements), ' '.join(str(tuple(r)) for r in doc.replacements)))


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 2
    if len(argv) >= 3 and argv[1] == '--find':
        find(argv[0], argv[2])
        return 0
    if len(argv) == 1:
        data = open(argv[0], 'rb').read()
    else:
        data = open_path(argv[0], argv[1])
    sys.stdout.reconfigure(encoding='utf-8')
    dump(ainb.Ainb.read(data))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
