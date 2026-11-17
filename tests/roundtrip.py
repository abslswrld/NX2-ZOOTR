"""Read-and-write test for the game's file formats.

For every file it can handle under a romfs folder, this reads the file and writes it back unchanged,
then compares the bytes. Archives (.pack, .sarc) are opened and the files inside are tested too.
It never changes anything in the romfs; it only reads.

    python tests/roundtrip.py "C:\\...\\romfs"                 everything it knows (slow on Python < 3.14)
    python tests/roundtrip.py "C:\\...\\romfs" Event RSDB      only these folders
    python tests/roundtrip.py "C:\\...\\romfs" --report out.txt

Python 3.14+ decompresses with the built-in zstd module and is much faster.
"""
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from formats import zstd, sarc, byml, evfl, msbt, restbl, ainb  # noqa: E402


def kind_of(name):
    n = name.lower()
    if n.endswith('.zs'):
        n = n[:-3]
    if n.endswith(('.byml', '.bgyml')):
        return 'byml'
    if n.endswith(('.pack', '.sarc')):
        return 'sarc'
    if n.endswith('.bfevfl'):
        return 'evfl'
    if n.endswith('.msbt'):
        return 'msbt'
    if n.endswith('.rsizetable'):
        return 'restbl'
    if n.endswith('.ainb'):
        return 'ainb'
    return None


def roundtrip(kind, data):
    if kind == 'byml':
        return byml.dumps(byml.loads(data))
    if kind == 'sarc':
        return sarc.Sarc.read(data).write()
    if kind == 'evfl':
        return evfl.dumps(evfl.loads(data))
    if kind == 'msbt':
        return msbt.Msbt.read(data).write()
    if kind == 'restbl':
        return restbl.Restbl.read(data).write()
    if kind == 'ainb':
        return ainb.Ainb.read(data).write()
    raise ValueError(kind)


class Results:
    def __init__(self):
        self.rows = []                    # (kind, path, status, detail)

    def add(self, kind, path, status, detail=''):
        self.rows.append((kind, path, status, detail))

    def summary(self):
        by = {}
        for kind, _, status, _ in self.rows:
            by.setdefault(kind, {}).setdefault(status, 0)
            by[kind][status] += 1
        return by


def test_bytes(res, kind, path, data):
    try:
        out = roundtrip(kind, data)
    except Exception as e:
        res.add(kind, path, 'error', '%s: %s' % (type(e).__name__, e))
        return
    if out == data:
        res.add(kind, path, 'identical')
    else:
        first = next((i for i in range(min(len(out), len(data))) if out[i] != data[i]), min(len(out), len(data)))
        res.add(kind, path, 'differs', 'sizes %d/%d, first difference at 0x%x' % (len(data), len(out), first))
    if kind == 'sarc':
        try:
            inner = sarc.Sarc.read(data)
        except Exception:
            return
        for name, blob in inner.files.items():
            k = kind_of(name)
            if k:
                test_bytes(res, k, path + '/' + name, blob)


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 2
    romfs = argv[0]
    report = None
    folders = []
    rest = argv[1:]
    while rest:
        a = rest.pop(0)
        if a == '--report':
            report = rest.pop(0)
        else:
            folders.append(a)
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    res = Results()
    t0 = time.time()
    roots = [os.path.join(romfs, f) for f in folders] or [romfs]
    files = []
    for root in roots:
        for dp, _, fns in os.walk(root):
            for fn in fns:
                if kind_of(fn):
                    files.append(os.path.join(dp, fn))
    files.sort()
    print('%d files to test (zstd: %s)' % (len(files), 'built-in' if zstd._std else 'pure Python'))
    for i, p in enumerate(files):
        rel = os.path.relpath(p, romfs).replace('\\', '/')
        raw = open(p, 'rb').read()
        if p.endswith('.zs'):
            try:
                data = zstd.decompress(raw, dicts)
            except Exception as e:
                res.add('zstd', rel, 'error', str(e))
                continue
            # the writer must give a frame that decompresses to the same bytes
            again = zstd.decompress(zstd.compress(data), dicts)
            res.add('zstd', rel, 'identical' if again == data else 'differs')
        else:
            data = raw
        test_bytes(res, kind_of(p), rel, data)
        if (i + 1) % 50 == 0:
            print('  %d/%d  (%.0fs)' % (i + 1, len(files), time.time() - t0))
    lines = ['Read-and-write test, %s' % time.strftime('%Y-%m-%d %H:%M'),
             'romfs: %s' % romfs, 'files: %d top-level, %d tested in all (archives opened)' % (len(files), len(res.rows)),
             'time: %.0fs, zstd: %s' % (time.time() - t0, 'built-in' if zstd._std else 'pure Python'), '']
    for kind, counts in sorted(res.summary().items()):
        lines.append('%-7s %s' % (kind, ', '.join('%d %s' % (n, s) for s, n in sorted(counts.items()))))
    problems = [r for r in res.rows if r[2] != 'identical']
    if problems:
        lines += ['', 'Not identical:']
        lines += ['  %-6s %-8s %s  %s' % r for r in problems]
    text = '\n'.join(lines)
    print(text)
    if report:
        open(report, 'w', encoding='utf-8').write(text + '\n')
    return 0 if not problems else 1


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        traceback.print_exc()
        sys.exit(3)
