"""Gossip stone text: what tools/build_mod.py makes of --gossip STONE=TEXT (the text of GossipStone.msbt under the
stone's name, in every language, and a question in front of the stones' talk flow so the chosen stones speak
without the Mask of Truth), on the game's own files. Only reads the game; the whole builds it runs go to a
temporary folder that is removed again.

    python tests/gossip_check.py "C:\\...\\romfs"
"""
import contextlib
import glob
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import sizes  # noqa: E402
from formats import zstd, sarc, evfl, restbl, msbt  # noqa: E402
from logic.world import World  # noqa: E402

RESTBL = build_mod.RESTBL_PATH.replace(os.sep, '/')[:-3]
# the stones a child reaches in Kokiri Forest and at the bridge (the Lost Woods map has only the bridge stone),
# with their names in the map, and the test messages (the same as the build arguments in CHANGELOG.md)
TESTS = (
    ('KF_NEAR_LOST_WOODS_GOSSIP', 'GOSSIP_KOKIRI_FOREST_01',
     'NX2-ZOOTR test 1 of 4: this stone by the {Lost Woods} speaks without the Mask of Truth.'),
    ('KF_DEKU_TREE_GOSSIP_01', 'GOSSIP_KOKIRI_FOREST_03',
     'NX2-ZOOTR test 2 of 4: the Deku Tree stone nearer the tree.\\nThis is the second line, after a line break.'),
    ('KF_DEKU_TREE_GOSSIP_02', 'GOSSIP_KOKIRI_FOREST_04',
     'NX2-ZOOTR test 3 of 4: the Deku Tree stone farther from the tree. This message is long on purpose, so that '
     'it does not fit in one text box: the builder wraps the words into lines and carries on in a second box.'),
    ('LW_BRIDGE_GOSSIP', 'GOSSIP_LOST_WOOD_02',
     'NX2-ZOOTR test 4 of 4: the stone by the bridge to Hyrule Field.\\pThis second page was asked for with a '
     'page break.'),
)
SCRUB = 'LW_NEAR_BRIDGE_SCRUB=Item_Boomerang'     # a build that also adds scrub lines to the same archives


def check(name, ok):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args, **kw):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            f(*args, **kw)
    except SystemExit as e:
        return bool(e.code)
    return False


def shown(text):
    """what a message shows: its plain text, pages joined by ' / ', lines by ' | '"""
    out = ''
    for x in msbt.tags(text):
        if isinstance(x, str):
            out += x.replace('\x00', '').replace('\n', ' | ')
        elif x[:2] == (0, 4):
            out += ' / '
    return out


def lead(text):
    """the tags a message starts with, and the tags after each page break"""
    t = msbt.tags(text)
    heads, cur, on = [], [], True
    for x in t:
        if isinstance(x, str):
            if on:
                heads.append(cur)
            on, cur = False, []
        elif x[:2] == (0, 4):
            on, cur = True, []
        elif on:
            cur.append(x)
    return heads


def route(fc, value):
    """the steps entry Talk runs when the stone's question answers `value`, up to the first step that is not
    the question: (index of that step)"""
    e = fc.events[fc.entry_point('Talk').main]
    return dict(e.cases).get(value)


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda f: zstd.decompress(open(f, 'rb').read(), d)   # noqa: E731
    plain = lambda path: rd(os.path.join(romfs, *path.split('/')) + '.zs')   # noqa: E731
    world = World()
    good = True
    mals = sorted('Mals/' + f[:-3] for f in os.listdir(os.path.join(romfs, 'Mals')) if f.endswith('.sarc.zs'))
    game_msg = {m: msbt.Msbt.read(sarc.Sarc.read(plain(m)).files[build_mod.GOSSIP_MSG_FILE]).texts for m in mals}
    en = game_msg[build_mod.GOSSIP_LANG]
    stones = [k for k in en if k.startswith(build_mod.GOSSIP_PREFIX) and 'RumorCommon' not in k]

    # ------------------------------------------------------------------------------- the game's files
    print('The game\'s files')
    good &= check('%d languages, each GossipStone.msbt with the same %d texts, %d of them one per stone' % (
        len(mals), len(en), len(stones)), len(mals) == 16 and len(stones) == 40
        and all(list(t) == list(en) for t in game_msg.values()))
    ai = sarc.Sarc.read(plain(build_mod.GOSSIP_PACK)).files[build_mod.GOSSIP_AI]
    values, other = build_mod.gossip_query_values(ai)
    good &= check('the stone\'s question (its event AI): one answer per stone, 0..39 in name order, 40 for any '
                  'other name', sorted(values) == sorted(stones) and other == 40
                  and [values[s] for s in sorted(stones)] == list(range(40)))
    flow0 = evfl.loads(plain(build_mod.GOSSIP_FLOW))
    fc0 = flow0.flowchart
    talk = fc0.entry_point('Talk').main
    e = fc0.events[talk]
    good &= check('the game\'s Talk starts by asking for the Mask of Truth (Navi talks without it)',
                  e.type == 'switch' and fc0.actors[e.actor].queries[e.query] == 'EventQueryIsExistInPouch'
                  and e.params['Actor'] == 'Armor_Child_Mask_Truth')
    t = msbt.tags(en['GOSSIP_LOST_WOOD_01'])
    page = [x for i, x in enumerate(t) if i and t[i - 1] == (0, 4, b'')][:1]
    good &= check('the builder\'s start and page tags are the game\'s own (GOSSIP_KOKIRI_FOREST_01, _LOST_WOOD_01)',
                  lead(en['GOSSIP_KOKIRI_FOREST_01'])[0] == msbt.tags(build_mod.GOSSIP_START)
                  and msbt.tags(build_mod.GOSSIP_PAGE)[1:] == lead(en['GOSSIP_LOST_WOOD_01'])[1]
                  and page == [(0, 2, b'P\x00')]
                  and all(lead(en[s])[0] in (msbt.tags(build_mod.GOSSIP_START), [msbt.tags(build_mod.GOSSIP_START)[i]
                                                                                for i in (1, 0, 2)]) for s in stones))
    longest = max(len(ln) for s in stones for x in msbt.tags(en[s]) if isinstance(x, str)
                  for ln in x.replace('\x00', '').split('\n'))
    good &= check('the line limit is the longest line of the game\'s English rumours (%d), 2 lines a page'
                  % longest, longest == build_mod.GOSSIP_WIDTH and max(
                      len(p) for s in stones for p in shown(en[s]).split(' / ')
                      for p in [p.split(' | ')]) == build_mod.GOSSIP_LINES)

    # ------------------------------------------------------------------------------- the option
    print('The option')
    specs = ['%s=%s' % (cid, text) for cid, _, text in TESTS]
    parsed = build_mod.gossip_parse(world, specs)
    good &= check('check IDs give the stones\' names in the map (the message labels)',
                  {k: v[0] for k, v in parsed.items()} == {name: cid for cid, name, _ in TESTS})
    good &= check('a stone\'s name in the map works too', list(build_mod.gossip_parse(
        world, ['GOSSIP_ZORA_RIVER_01=Hi.'])) == ['GOSSIP_ZORA_RIVER_01'])
    good &= check('refused: not a stone, no =, no text, the same stone twice (by ID and by name)',
                  refused(build_mod.gossip_parse, world, ['KF_MIDO_CHEST_01=Hi.'])
                  and refused(build_mod.gossip_parse, world, ['KF_NEAR_LOST_WOODS_GOSSIP'])
                  and refused(build_mod.gossip_parse, world, ['KF_NEAR_LOST_WOODS_GOSSIP= '])
                  and refused(build_mod.gossip_parse, world,
                              ['KF_NEAR_LOST_WOODS_GOSSIP=a', 'GOSSIP_KOKIRI_FOREST_01=b']))
    chars = build_mod.gossip_chars(plain(build_mod.GOSSIP_LANG))
    lay = lambda text: build_mod.gossip_layout(text, chars)   # noqa: E731
    want = {
        'GOSSIP_KOKIRI_FOREST_01': 'NX2-ZOOTR test 1 of 4: this stone by the Lost Woods speaks | without the Mask of '
                                   'Truth.',
        'GOSSIP_KOKIRI_FOREST_03': 'NX2-ZOOTR test 2 of 4: the Deku Tree stone nearer the tree. | This is the second '
                                   'line, after a line break.',
        'GOSSIP_KOKIRI_FOREST_04': 'NX2-ZOOTR test 3 of 4: the Deku Tree stone farther from the tree. | This message '
                                   'is long on purpose, so that it does not fit in one / text box: the builder wraps '
                                   'the words into lines and carries on | in a second box.',
        'GOSSIP_LOST_WOOD_02': 'NX2-ZOOTR test 4 of 4: the stone by the bridge to Hyrule Field. / This second page was '
                               'asked for with a page break.',
    }
    texts = {name: build_mod.gossip_message(lay(text)) for _, name, text in TESTS}
    good &= check('the four test texts: wrapped at %d characters, 2 lines a page, the line and page breaks asked '
                  'for' % build_mod.GOSSIP_WIDTH, {k: shown(v) for k, v in texts.items()} == want)
    hl = msbt.tags(texts['GOSSIP_KOKIRI_FOREST_01'])
    good &= check('highlight: colour 0 around the words, then back to the rumour\'s colour 1',
                  hl[3:7] == ['NX2-ZOOTR test 1 of 4: this stone by the ', (0, 3, b'\x00\x00'), 'Lost Woods',
                              (0, 3, b'\x01\x00')])
    p2 = msbt.tags(build_mod.gossip_message(lay('{' + ' '.join(['word'] * 30) + '} end')))
    k = p2.index((0, 4, b'')) if (0, 4, b'') in p2 else 0
    good &= check('a highlight across a page break is closed before it and started again after the page\'s colour 1',
                  p2[:4] == msbt.tags(build_mod.GOSSIP_START) + [(0, 3, b'\x00\x00')] and k
                  and p2[k - 1:] == [(0, 3, b'\x01\x00'), (0, 4, b''), (0, 2, b'P\x00'), (0, 3, b'\x01\x00'),
                                     (0, 3, b'\x00\x00'), 'word word word word', (0, 3, b'\x01\x00'), ' end\x00'])
    long_text = ' '.join(['word'] * 13 * 2 * build_mod.GOSSIP_PAGES)
    good &= check('limits: %d pages pass, more are refused' % build_mod.GOSSIP_PAGES,
                  len(lay(long_text)) == build_mod.GOSSIP_PAGES and refused(lay, long_text + ' more'))
    good &= check('refused: an unknown escape, an unclosed or stray brace, a character the English text never '
                  'uses, a word longer than a line',
                  refused(lay, 'a\\tb') and refused(lay, 'a {b') and refused(lay, 'a} b') and refused(lay, 'a @ b')
                  and refused(lay, 'a ~ b') and refused(lay, 'x' * (build_mod.GOSSIP_WIDTH + 1))
                  and not refused(lay, 'x' * build_mod.GOSSIP_WIDTH))

    # ------------------------------------------------------------------------------- the flow
    print('The flow')
    names = [name for _, name, _ in TESTS]
    flow = evfl.loads(plain(build_mod.GOSSIP_FLOW))
    fc = flow.flowchart
    said = build_mod.gossip_flow_edit(fc, values, other, names)
    back = evfl.loads(build_mod.flow_write_checked(flow)).flowchart
    n0 = len(fc0.events)
    good &= check('the game\'s %d events, actors\' other lists and other entry points are unchanged; 3 events added'
                  % n0, [vars(x) for x in back.events[:n0]] == [vars(x) for x in fc0.events]
                  and len(back.events) == n0 + 3
                  and [vars(p) for p in back.entry_points if p.name != 'Talk']
                  == [vars(p) for p in fc0.entry_points if p.name != 'Talk']
                  and [(a.name, a.actions, a.params) for a in back.actors] == [(a.name, a.actions, a.params)
                                                                              for a in fc0.actors])
    ask = back.events[back.entry_point('Talk').main]
    good &= check('Talk starts with the stone\'s question, asked of the stone talked to, one case per answer (41)',
                  ask.type == 'switch' and back.actors[ask.actor].name == build_mod.GOSSIP_TALKER
                  and back.actors[ask.actor].queries[ask.query] == build_mod.GOSSIP_QUERY
                  and sorted(v for v, _ in ask.cases) == list(range(41))
                  and [a.queries for a in back.actors if a.name != build_mod.GOSSIP_TALKER]
                  == [a.queries for a in fc0.actors if a.name != build_mod.GOSSIP_TALKER])
    init = back.events[route(back, values[names[0]])]
    say = back.events[init.next] if init.next is not None else None
    game_say = [x for x in fc0.events if x.type == 'action' and build_mod._action_name(fc0, x) == build_mod.GOSSIP_SAY]
    good &= check('the chosen stones: set-up InitTalk_GossipStone, their own text (the game\'s step copied), end',
                  all(route(back, values[n]) == route(back, values[names[0]]) for n in names)
                  and (init.type, init.flowchart, init.entry) == ('subflow',) + build_mod.GOSSIP_INIT
                  and say is not None and say.next is None and len(game_say) == 1
                  and build_mod._action_name(back, say) == build_mod.GOSSIP_SAY
                  and back.actors[say.actor].name == build_mod.GOSSIP_TALKER and say.params == game_say[0].params)
    good &= check('the other 36 stones and any other name: the game\'s first step (the mask question)',
                  all(route(back, values[s]) == talk for s in stones if s not in names) and route(back, other) == talk)
    good &= check('Talk lists the new set-up step among its subflows; the other entries\' steps are not reached',
                  route(back, values[names[0]]) in back.entry_point('Talk').subflows
                  and all(n0 not in back.reachable(p.main) for p in back.entry_points if p.name != 'Talk'))
    print('  ' + said[0][:200])

    # ------------------------------------------------------------------------------- whole builds
    print('Whole builds')
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            base = os.path.join(tmp, name, 'romfs')
            return base, out.getvalue(), {os.path.relpath(f, base).replace(os.sep, '/')
                                          for f in glob.glob(os.path.join(base, '**', '*'), recursive=True)
                                          if os.path.isfile(f)}

        mod = lambda b, path: rd(os.path.join(b, *path.split('/')) + '.zs')   # noqa: E731
        gargs = [x for s in specs for x in ('--gossip', s)]
        good &= check('the build refuses a bad --gossip before writing anything (also with a scrub): not a stone, '
                      'a shared closing line, a bad text',
                      refused(run, 'bad', '--gossip', 'KF_MIDO_CHEST_01=Hi.')
                      and refused(run, 'bad', SCRUB, '--gossip', 'GOSSIP_RumorCommon_01=Hi.')
                      and refused(run, 'bad', SCRUB, '--gossip', 'GOSSIP_KOKIRI_FOREST_01=a {b')
                      and not os.path.exists(os.path.join(tmp, 'bad', 'romfs')))
        base, said, files = run('gossip', *gargs)
        good &= check('files written: the stones\' flow, the %d message archives, the size table' % len(mals),
                      files == {f + '.zs' for f in [build_mod.GOSSIP_FLOW, RESTBL] + mals})
        ok_msg, ok_rest = True, True
        for m in mals:
            arc0, arc1 = sarc.Sarc.read(plain(m)), sarc.Sarc.read(mod(base, m))
            t1 = msbt.Msbt.read(arc1.files[build_mod.GOSSIP_MSG_FILE]).texts
            ok_msg &= list(t1) == list(game_msg[m]) and all(t1[k] == texts[k] for k in names) \
                and all(t1[k] == v for k, v in game_msg[m].items() if k not in names)
            ok_rest &= set(arc1.files) == set(arc0.files) and all(
                arc1.files[f] == v for f, v in arc0.files.items() if f != build_mod.GOSSIP_MSG_FILE)
        good &= check('every language: the four stones say the test texts (English), every other text of the file '
                      'is the game\'s', ok_msg)
        good &= check('every language: every other file of the archive is byte for byte the game\'s', ok_rest)
        built = evfl.loads(mod(base, build_mod.GOSSIP_FLOW)).flowchart
        good &= check('the flow written is the one checked above',
                      [vars(x) for x in built.events] == [vars(x) for x in back.events]
                      and [vars(p) for p in built.entry_points] == [vars(p) for p in back.entry_points])
        t0 = restbl.Restbl.read(plain(RESTBL))
        t1 = restbl.Restbl.read(mod(base, RESTBL))
        right = True
        for path in [build_mod.GOSSIP_FLOW] + mals:
            new, old = mod(base, path), plain(path)
            # as build_mod.Output.size: the game's entry plus what the file grew, and what tools/sizes.py asks
            right &= t1.get(path) == max(t0.get(path) + max(0, len(new) - len(old)),
                                         sizes.entry(path, new, t0.get(path), old)) \
                and t1.get(path) >= sizes.rule(path, new) and t1.get(path) >= t0.get(path)
        mine = {restbl.path_crc(p) for p in [build_mod.GOSSIP_FLOW] + mals}
        others = set(t1.crc) == set(t0.crc) and t1.names == t0.names \
            and all(t1.crc[k] == v for k, v in t0.crc.items() if k not in mine)
        good &= check('size table: the 17 files\' entries are what tools/sizes.py asks (never smaller than the game\'s)'
                      ', the others unchanged', right and others and t1.write() != t0.write())
        print('\n'.join('  ' + ln[:200] for ln in said.splitlines() if ln.startswith('gossip')))
        base2, _, files2 = run('both', SCRUB, *gargs)
        lines = [msbt.Msbt.read(sarc.Sarc.read(mod(base2, m)).files[f]).texts
                 for m in mals for f in (build_mod.GOSSIP_MSG_FILE, build_mod.SCRUB_MSG_FILE)]
        good &= check('with a scrub too: each archive holds both the scrub line and the stones\' texts',
                      all(lines[2 * i + 1].get(build_mod.SCRUB_LABEL) == build_mod.SCRUB_LINE
                          and all(lines[2 * i][k] == texts[k] for k in names) for i in range(len(mals))))
    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
