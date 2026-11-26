"""Progressive families on Gold Skulltulas test: every upgrade family of tools/build_mod.py (FAMILIES) on a Gold
Skulltula check. A family there is the one-time turning item a rock drops (tools/once_items.py): the skulltula
hands its saved flag to what it drops, as it does to its token, and the item marks it the way the token does
(passed in game, 2026-11-23). Checked on the game's own files: how a skulltula is marked done (its token's AI and
the flag it is handed); then whole builds.
(The other way, the game's drop code choosing the level, never put a lower level in place in game; its code and
its checks were removed on 2026-11-23.)
Only reads the game; the builds it runs go to a temporary folder that is removed again.

    python tests/skulltula_prog_check.py "C:\\...\\romfs"
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
import ground_items  # noqa: E402
import once_items  # noqa: E402
from formats import zstd, byml, sarc, ainb  # noqa: E402
from logic.world import World  # noqa: E402

FAMILIES = build_mod.FAMILIES
# the Gold Skulltula checks of the mapped areas (the Lost Woods and the Meadow have no IDs yet: by name)
SKULLTULAS = ('KF_KNOW_IT_ALL_HOUSE_GS', 'KF_BEAN_PATCH_GS', 'KF_HOUSE_OF_TWINS_GS', 'LW GS Bean Patch Near Bridge',
              'LW GS Bean Patch Near Theater', 'LW GS Above Theater', 'SFM GS')
SKULLTULA = 'Enemy_Skulltula_Gold'
MARK = 'OneShotGoldTokenDeadAfter'
HAND_OVER = 'QueryBlackboardOverwriteParamAddNoRespawnGmdHash'
TOKEN_AI = 'AI/Item_Token_Gold.root.ainb'
SKULLTULA_AI = 'AI/Enemy_Skulltula_Gold.utility.root.ainb'
FLOW = 2
TOKEN_NODES = 12                                   # the token's AI: its nodes, as the game has them
# the drop code's global settings: no build changes them (the drop code's way was removed)
DROP_GLOBAL = 'GameParameter/DropGlobalParam/Default.game__drop__DropGlobalParam.bgyml.zs'


def check(name, ok):
    print('%-118s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args, **kw):
    try:
        f(*args, **kw)
    except SystemExit:
        return True
    return False


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda p: zstd.decompress(open(p, 'rb').read(), d)   # noqa: E731

    def plain(path):
        p = os.path.join(romfs, *path.split('/'))
        return open(p, 'rb').read() if os.path.exists(p) else rd(p + '.zs')

    world = World()
    good = True

    # ------------------------------------------------------------------------------ what the game's files show
    print('The game')
    token = sarc.Sarc.read(plain(ground_items.pack_path(ground_items.TOKEN))).files
    doc = ainb.loads(token[TOKEN_AI])
    root = doc.nodes[doc.commands[0].left]
    dead = doc.nodes[root.links[FLOW][0].node]                       # dead? -> by reason
    by_reason = doc.nodes[dict((l.name, l.node) for l in dead.links[FLOW])['True']]
    ten = [doc.nodes[l.node] for l in by_reason.links[FLOW] if tuple(l.extra) == (0, 10)]
    marks = [doc.nodes[l.node].name for n in ten for l in n.links[FLOW]]
    good &= check('the token marks its skulltula when it is picked up: its AI, dead with reason 10 -> %s' % MARK,
                  len(doc.nodes) == TOKEN_NODES and MARK in marks
                  and doc.nodes[dead.inputs['bool'][0].node].name == 'QueryDeathIsDead')
    gs = sarc.Sarc.read(plain(ground_items.pack_path(SKULLTULA))).files
    hand = [n for n in ainb.loads(gs[SKULLTULA_AI]).nodes if n.name == HAND_OVER]
    table = byml.loads(token[ground_items.TOKEN_FILES[1]]).root
    keys = {e['BBKey']: e['InitVal'] for e in table.get('BlackboardParamU64Array', [])}
    good &= check('the skulltula hands its flag to its drop under the key the token has (%s)' % ground_items.TOKEN_KEY,
                  len(hand) == 1 and {x.name: x.value for x in hand[0].immediates['string']}.get('Key')
                  == ground_items.TOKEN_KEY and list(keys) == [ground_items.TOKEN_KEY])
    good &= check('  a table can only start that key with a 32-bit number (the game\'s is 0, stored as 32 bits): '
                  'the flag (64 bits) cannot be written into a second drop\'s table',
                  type(keys[ground_items.TOKEN_KEY]) is byml.UInt and keys[ground_items.TOKEN_KEY] == 0)
    flags = {int(e['Hash']): int(e['ResetTypeValue'])
             for e in byml.loads(plain(build_mod.GAME_DATA)).root['Data']['Bool64bitKey']}
    hashes = []
    for p in glob.glob(os.path.join(romfs, 'Banc', '**', '*.bcett.byml.zs'), recursive=True):
        hashes += [int(a['Hash']) for a in byml.loads(rd(p)).root.get('Actors', []) if a.get('Gyaml') == SKULLTULA]
    good &= check('every Gold Skulltula placement (%d) has its two saved flags, never reset (the two the token sets)'
                  % len(set(hashes)), len(set(hashes)) >= 100
                  and all(flags.get(h) == build_mod.FLAG_KEPT and flags.get(h ^ 2) == build_mod.FLAG_KEPT
                          for h in hashes))

    # ------------------------------------------------------------------------------------- whole builds
    print('Whole builds')
    good &= check('a family on a Gold Skulltula is planned as a Gold Skulltula\'s (not as a chest\'s or a '
                  'freestanding item\'s)',
                  all(build_mod.skulltula_pair_kind(world, c) for c in SKULLTULAS)
                  and not build_mod.skulltula_pair_kind(world, 'KF_MIDO_CHEST_01')
                  and refused(build_mod.pair_kind, world, SKULLTULAS[0]))
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *assign):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(assign))
            base = os.path.join(tmp, name, 'romfs')
            return base, said.getvalue(), {os.path.relpath(f, base).replace(os.sep, '/')
                                           for f in glob.glob(os.path.join(base, '**', '*'), recursive=True)
                                           if os.path.isfile(f)}

        fams = list(FAMILIES.items())
        ok, maps_ok, packs_ok, other_ok, untouched_ok = True, True, True, True, True
        for part, some in enumerate((fams[:6], fams[6:])):
            placed = dict(zip(SKULLTULAS, some))
            extra = ['KF_MIDO_CHEST_01=Item_Boomerang'] + (['%s=Item_Bottle' % SKULLTULAS[6]] if part else [])
            base, said, files = run('gs%d' % part, *(['%s=%s' % (c, '>'.join(f)) for c, (n, f) in placed.items()]
                                                    + extra))
            changed = {p['hash'] for c in list(placed) + ([SKULLTULAS[6]] if part else [])
                       for _, _, p in world.placements_of(*build_mod.find_check(world, c)[::2])}
            for c, (n, f) in placed.items():
                r, _, loc = build_mod.find_check(world, c)
                for scene, spot_id, p in world.placements_of(r, loc):
                    for fn in p['files']:
                        path = os.path.join(base, 'Banc', scene, fn)
                        acts = {str(int(a['Hash'])): a for a in byml.loads(rd(path)).root['Actors']}
                        orig = {str(int(a['Hash'])): a for a in byml.loads(
                            rd(os.path.join(romfs, 'Banc', scene, fn))).root['Actors']}
                        a = acts[p['hash']]
                        maps_ok &= a['Gyaml'] == SKULLTULA \
                            and a['Dynamic'].get('Drop__DropActor') == once_items.once_name(f[0]) \
                            and {k: v for k, v in a['Dynamic'].items() if k != 'Drop__DropActor'} \
                            == {k: v for k, v in dict(orig[p['hash']].get('Dynamic') or {}).items()
                                if k != 'Drop__DropActor'} \
                            and all(acts[h] == o for h, o in orig.items() if h not in changed and o['Gyaml'] == SKULLTULA)
                ok &= ('a turning item as the skulltula\'s drop: %s on the ground while Link has no %s, then %s'
                       % (f[0], f[0], f[1])) in said
                packs_ok &= all(('Pack/Actor/%s.pack.zs' % once_items.once_name(x)) in files
                                and ('once   version %-22s for %s' % (once_items.once_name(x), x)) in said for x in f)
            info = {r['__RowId'] for r in byml.loads(rd(os.path.join(
                base, *ground_items.table_path('ActorInfo').split('/')) + '.zs')).root}
            packs_ok &= all(once_items.once_name(x) in info for c, (n, f) in placed.items() for x in f)
            # nothing of the drop code's way (removed): its lists, the skulltula's own pack, Obj_NX2S_ drops
            untouched_ok &= DROP_GLOBAL not in files \
                and (ground_items.pack_path(SKULLTULA) + '.zs') not in files \
                and not any('/Obj_NX2S_' in x for x in files)
            if part:                                    # a plain item on a skulltula beside them: as before
                other_ok &= 'Pack/Actor/Obj_NX2_GS_Bottle.pack.zs' in files
        good &= check('all %d families build on Gold Skulltulas (two builds): each is a turning item as the '
                      'skulltula\'s drop' % len(fams), ok)
        good &= check('  the skulltula\'s placement names the first level\'s one-time turning item (Drop__DropActor); '
                      'nothing else of it, and no other skulltula, changes', maps_ok)
        good &= check('  every level\'s one-time turning item is in the mod (pack and table row)', packs_ok)
        good &= check('  the drop code\'s lists, the skulltula\'s own pack and the Obj_NX2S_ drops are not in the mod',
                      untouched_ok)
        good &= check('  a plain item on another skulltula is the plain token version', other_ok)
        base, said, files = run('none', 'KF_MIDO_CHEST_01=Item_Scale_Silver>Item_Scale_Gold',
                                '%s=Item_Scale_Silver' % SKULLTULAS[0])
        good &= check('a build without a family on a skulltula: its plain item is the token version, no turning item',
                      DROP_GLOBAL not in files and 'Pack/Actor/Obj_NX2_GS_Scale_Silver.pack.zs' in files
                      and not any('/Obj_NX2S_' in f or '/Obj_NX2Q_' in f for f in files))
        # (a family on a pot builds since 2026-11-22: tests/one_time_check.py)
        good &= check('still refused: a later level alone on a skulltula, a family that is none, three levels on a '
                      'shelf',
                      refused(run, 'no1', '%s=Item_Scale_Gold' % SKULLTULAS[0])
                      and refused(run, 'no2', '%s=Item_Scale_Gold>Item_Scale_Silver' % SKULLTULAS[0])
                      and refused(run, 'no4', '--fix', 'kokiri_shop_full_stock', 'KF_KOKIRI_CHILD_SHOP_01=Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large'))

    print()
    print('ALL OK' if good else 'SOME CHECKS FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
