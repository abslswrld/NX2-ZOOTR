"""Edit test: change each format the way a randomizer would, write it, read it back, and check the change
is there and everything else is unchanged. Reads only; writes nothing to the romfs.
(The AINB edits are compared through the text dump of tools/ainb_dump.py: only the edited lines may differ.)

    python tests/edit_check.py "C:\\...\\romfs"
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from formats import zstd, sarc, byml, evfl, msbt, restbl, ainb  # noqa: E402
from tools import ainb_dump  # noqa: E402


def check(name, ok):
    print('%-58s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def ainb_text(doc):
    out = io.StringIO()
    ainb_dump.dump(doc, out)
    return out.getvalue().split('\n')


def changed_lines(before, after):
    """Lines that differ between two dumps of the same length (None if the line counts differ)."""
    if len(before) != len(after):
        return None
    return [(a, b) for a, b in zip(before, after) if a != b]


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda *p: zstd.decompress(open(os.path.join(romfs, *p), 'rb').read(), d)
    good = True

    # event flow: add an actor action and a new event after the first event of GetPouchContent
    raw = rd('Event', 'EventFlow', 'GetPouchContent.bfevfl.zs')
    f = evfl.loads(raw)
    fc = f.flowchart
    actor = next(i for i, a in enumerate(fc.actors) if a.name == 'GameSystemActor') if any(
        a.name == 'GameSystemActor' for a in fc.actors) else 0
    fc.actors[actor].actions.append('EventWait')
    first = fc.entry_points[0].main
    new = evfl.Event('TestWait', 'action', next=fc.events[first].next if fc.events[first].type == 'action' else None,
                     actor=actor, action=len(fc.actors[actor].actions) - 1,
                     params=evfl.Params(Frames=3, IsWaitEnd=True))
    fc.events.append(new)
    out = evfl.dumps(f)
    g = evfl.loads(out)
    e = g.flowchart.events[-1]
    good &= check('event flow: new event and action written and read back',
                  e.name == 'TestWait' and dict(e.params) == {'Frames': 3, 'IsWaitEnd': True}
                  and g.flowchart.actors[actor].actions[-1] == 'EventWait'
                  and len(g.flowchart.events) == len(evfl.loads(raw).flowchart.events) + 1)
    good &= check('event flow: rewriting the edited file is stable', evfl.dumps(g) == out)

    # BYML: change a value and add an entry in PouchActorInfo
    doc = byml.loads(rd('RSDB', 'PouchActorInfo.Product.111.rstbl.byml.zs'))
    rows = doc.root
    rows[0] = dict(rows[0])
    key = next(k for k, v in rows[0].items() if isinstance(v, str))
    rows[0][key] = rows[0][key] + '_test'
    rows.append({'__RowId': 'Test_Row', 'TestValue': byml.UInt(7)})
    back = byml.loads(byml.dumps(doc)).root
    good &= check('BYML: changed value and new row read back',
                  back[0][key].endswith('_test') and back[-1]['TestValue'] == 7 and len(back) == len(rows))

    # SARC: add a file to a pack
    pack = sarc.Sarc.read(rd('Pack', 'ResidentCommon.pack.zs'))
    pack.files['Test/hello.txt'] = b'hello'
    back = sarc.Sarc.read(pack.write())
    good &= check('SARC: added file read back, others unchanged',
                  back.files['Test/hello.txt'] == b'hello' and all(back.files[k] == v for k, v in pack.files.items()))

    # MSBT: change a text and add a label
    mals = sarc.Sarc.read(rd('Mals', 'USen.Product.110.sarc.zs'))
    m = msbt.Msbt.read(mals.files['LocationMsg/Location.msbt'])
    m.texts['KokiriForest'] = 'Randomized Forest\0'
    m.texts['TestLabel'] = 'Test text\0'
    back = msbt.Msbt.read(m.write())
    good &= check('MSBT: changed text and new label read back',
                  back.texts['KokiriForest'] == 'Randomized Forest\0' and back.texts['TestLabel'] == 'Test text\0')

    # RESTBL: set the size of a new file
    t = restbl.Restbl.read(rd('System', 'Resource', 'ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs'))
    t.set('Test/hello.txt', 1234)
    back = restbl.Restbl.read(t.write())
    good &= check('RESTBL: new entry read back', back.get('Test/hello.txt') == 1234)

    # AINB: change a number (the pot respawn logic waits 1200 frames; make it 60)
    raw = open(os.path.join(romfs, 'Logic', 'Obj_Pot_A_05_Respawn_Prefab_1c6c.logic.module.ainb'), 'rb').read()
    a = ainb.Ainb.read(raw)
    before = ainb_text(a)
    delay = next(n for n in a.nodes if n.name == 'HoldGeneralDelayBool')
    frame = next(x for x in delay.inputs['float'] if x.name == 'Frame')
    was = frame.value
    frame.value = 60.0
    out = a.write()
    b = ainb.Ainb.read(out)
    diff = changed_lines(before, ainb_text(b))
    good &= check('AINB: changed number read back, nothing else changed',
                  was == 1200.0 and diff is not None and len(diff) == 1 and 'Frame = 60' in diff[0][1]
                  and len(out) == len(raw) and sum(x != y for x, y in zip(out, raw)) <= 4)
    good &= check('AINB: rewriting the edited file is stable', b.write() == out)

    # AINB: change a string to a new one, and take one source away from an input with several
    raw = open(os.path.join(romfs, 'Logic', 'KokiriForest_Common_Level_All_01_6aaf.logic.module.ainb'), 'rb').read()
    a = ainb.Ainb.read(raw)
    before = ainb_text(a)
    setter = next(n for n in a.nodes if n.name == 'TriggerGameDataSetBoolTrue')
    name = next(x for x in setter.inputs['string'] if x.name == 'GameDataNameBool')
    old_name = name.value
    name.value = 'NX2_Test_Flag'
    both = next(n for n in a.nodes if n.name == 'OperateAND' and len(n.inputs['bool'][0].sources or ()) == 2)
    both.inputs['bool'][0].sources = both.inputs['bool'][0].sources[:1]
    out = a.write()
    b = ainb.Ainb.read(out)
    diff = changed_lines(before, ainb_text(b))
    other = next(n for n in b.nodes if n.name == 'TriggerGameDataSetBoolFalse')
    good &= check('AINB: new string, removed source; nothing else changed',
                  diff is not None and len(diff) == 2
                  and any('GameDataNameBool = "NX2_Test_Flag"' in d[1] for d in diff)
                  and any('BoolMulti' in d[1] and 'HoldGameDataGetBoolSimple' not in d[1] for d in diff)
                  and other.inputs['string'][0].value == old_name
                  and out.endswith(b'NX2_Test_Flag\0'))
    good &= check('AINB: rewriting the edited file is stable', b.write() == out)

    # zstd: compress and decompress
    blob = evfl.dumps(f)
    good &= check('zstd: written frame decompresses to the same bytes', zstd.decompress(zstd.compress(blob), d) == blob)
    return 0 if good else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
