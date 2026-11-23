"""Gossip stone hints: what tools/build_mod.py makes of --hint STONE=ITEM / STONE=@CHECK_ID (hint_specs): a
sentence worded from the build's own placements and the game's own English text, given to the stone as --gossip
text. Checked on the game's own files: every name a hint can use comes from the game's text (items, areas,
signboards, Gold Skulltulas, Business Scrubs) and is plain text the stones can show; every check that can hold an
item gets a wording that fits a stone; what --hint accepts and refuses; and a whole build, read back. Only reads
the game; the whole builds it runs go to a temporary folder that is removed again.

    python tests/hint_check.py "C:\\...\\romfs"
"""
import contextlib
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
from formats import zstd, sarc, byml, msbt  # noqa: E402
from logic.world import World  # noqa: E402

# items placed in tests and builds so far, beside every level of every family (build_mod.FAMILIES)
ITEMS = ('Item_Boomerang', 'Obj_Heart_Piece', 'Obj_Heart_Container', 'Obj_Rupee_Gold', 'Item_Bottle',
         'Item_Sword_Kokiri', 'Item_Hammer', 'Item_Arrow_Fire', 'Item_Arrow_Light', 'Item_Bombchu',
         'Item_Shield_Mirror', 'Item_HoverBoot', 'Item_HeavyBoot', 'Item_Mask_Truth', 'Item_GlassTruth',
         'Item_Melody_SariaSong', 'Item_Melody_StormSong', 'Item_Melody_ForestMinuet', 'Item_Sword_Biggoron')
# what the game's text is known to call some of them (read from ActorMsg/PouchContent.msbt by hand, 2026-11-23)
NAMED = {'Item_Boomerang': ('the', 'Boomerang'), 'Item_Range_SlingShot': ('the', 'Fairy Slingshot'),
         'Item_BombBag_Small': ('a', 'Bomb Bag'), 'Item_Scale_Silver': ('a', 'Silver Scale'),
         'Item_Bottle': ('an', 'Empty Bottle'), 'Obj_Heart_Piece': ('a', 'Piece of Heart'),
         'Item_Wallet_Medium': ('an', "Adult's Wallet")}
# the places as their signboards name them (read from EventFlowMsg/SignboardWood.msbt by hand, 2026-11-23: the
# first line, or the first page, before any comma)
PLACES = {'KF Links House': "Link's House", 'KF Midos House': 'Mansion of the Great Mido',
          'KF Sarias House': "Saria's House", 'KF House of Twins': 'House of the Twins',
          'KF Know It All House': 'House of the Know-It-All Brothers', 'KF Shop': 'Kokiri Shop',
          'KF Training Area': 'Training Grounds', 'Deku Theater': 'Forest Stage'}
# where some checks are, as a hint says it (the game's names: signboards, Location.msbt)
WHERE = {
    'KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02': 'in a pot in the {House of the Know-It-All Brothers} in {Kokiri Forest}',
    'KF_MIDO_CHEST_01': 'in a chest in the {Mansion of the Great Mido} in {Kokiri Forest}',
    'KF_SARIAS_HOUSE_HEART_ITEM_03': "lying on the ground in {Saria's House} in {Kokiri Forest}",
    'KF_KOKIRI_CHILD_SHOP_01': 'for sale in the {Kokiri Shop} in {Kokiri Forest}',
    'KF_TRAINING_AREA_RUPEE_ITEM_01': 'lying on the ground at the {Training Grounds} in {Kokiri Forest}',
    'KF_BEHIND_SARIAS_HOUSE_CHILD_ROCK_01': 'under a rock in {Kokiri Forest}',
    'KF_STORMS_GROTTO_CHEST': 'in a chest underground in {Kokiri Forest}',
    'LW GS Above Theater': 'on a Gold Skulltula in the {Lost Woods}',
    'LW_NEAR_BRIDGE_SCRUB': 'sold by a Business Scrub in {Kokiri Forest}',
    'Song from Saria': 'as a gift in the {Sacred Grove}',
}


def check(name, ok):
    print('%-110s %s' % (name, 'OK' if ok else 'FAILED'))
    return bool(ok)


def refused(f, *args, **kw):
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            f(*args, **kw)
    except SystemExit as e:
        return bool(e.code)
    return False


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path):
        return zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)

    lang = plain(build_mod.GOSSIP_LANG)
    texts = build_mod.hint_texts(lang)
    chars = build_mod.gossip_chars(lang)
    known = {r['__RowId']: r.get('ActorName') for r in byml.loads(plain(ground_items.table_path('ActorInfo'))).root}
    known_as = known.get
    world = World()
    good = True

    # ------------------------------------------------------------------------------------- names
    print('Names (the game\'s English text)')
    items = sorted({x for f in build_mod.FAMILIES.values() for x in f} | set(ITEMS))
    names, ok = {}, True
    for item in items:
        try:
            names[item] = build_mod.hint_item_name(item, texts, known_as)
        except SystemExit:
            ok = False
            print('  no name:', item)
    good &= check('every level of every family and %d other items has a name in %s' % (len(ITEMS), build_mod.HINT_NAMES),
                  ok and len(names) == len(items))
    good &= check('  each with an article from its get message (the, a, an or none) and plain text a stone can show',
                  all(a in ('', 'a', 'an', 'the') and n and n == n.strip() and '\n' not in n and set(n) <= chars
                      and '{' not in n and '}' not in n for a, n in names.values()))
    good &= check('  the ones read by hand: %s' % ', '.join('%s %s' % v for v in NAMED.values()),
                  all(names.get(i) == v for i, v in NAMED.items()))
    good &= check('  an item with no name in the game\'s text is refused',
                  refused(build_mod.hint_item_name, 'Item_NX2_None', texts, known_as))
    signs = {r: build_mod.hint_sign(texts, label) for r, (label, _) in build_mod.HINT_PLACES.items()}
    good &= check('every place named in hints is a region of the world data, named by its signboard: %s'
                  % ', '.join(sorted(signs.values())),
                  set(build_mod.HINT_PLACES) <= set(world.regions)
                  and set(build_mod.HINT_UNDERGROUND) <= set(world.regions)
                  and all(s and set(s) <= chars for s in signs.values()) and signs == PLACES)
    areas = {r.scene for r in world.regions.values() if not r.unmapped and r.scene}
    good &= check('every mapped area has its name in %s: %s' % (
        build_mod.HINT_AREAS, ', '.join(sorted(texts[build_mod.HINT_AREAS][a] for a in areas))),
        all(texts[build_mod.HINT_AREAS].get(a) for a in areas))

    # ------------------------------------------------------------------------------------- where
    print('Where')
    longest = max((n for n in names.values()), key=lambda x: len(x[0]) + len(x[1]))
    worded, refused_ids, fits = {}, [], True
    for r in world.regions.values():
        for name, loc in r.locations.items():
            cid = loc.get('id') or name
            try:
                kind = build_mod.check_kind(world, cid)
            except SystemExit:
                refused_ids.append(cid)                # an event with no data (Sheik, the Skull Kid...)
                continue
            if kind == 'gossip':
                continue
            worded[cid] = build_mod.hint_where(world, cid, texts)
            # the longest item name there, as a family ("or an upgrade of it"): it must fit a stone
            text = 'They say %s {%s} or an upgrade of it can be found %s.' % (longest[0], longest[1], worded[cid])
            try:
                pages = build_mod.gossip_layout(text, chars)
            except SystemExit:
                fits = False
                print('  does not fit:', cid)
                continue
            fits &= len(pages) <= 2
    good &= check('every check that is not a gossip stone gets a wording (%d checks); %d events without data '
                  'are not checks yet' % (len(worded), len(refused_ids)),
                  len(worded) > 100 and all(worded.values()))
    good &= check('  with the longest item name as a family, every hint fits a stone in one or two pages', fits)
    good &= check('  the ones read by hand (houses, the shop, the training grounds, underground, a scrub, a song)',
                  all(worded.get(c) == w for c, w in WHERE.items()))
    good &= check('  a gossip stone itself has no wording (a hint cannot point at a stone)',
                  refused(build_mod.hint_where, world, 'LW_BRIDGE_GOSSIP', texts))

    # ------------------------------------------------------------------------------------- what --hint takes
    print('What --hint takes')
    given = [('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02', 'Item_Boomerang'),
             ('KF_BEHIND_SARIAS_HOUSE_CHILD_ROCK_01', 'Item_Range_SlingShot>Item_BulletBag_Medium>Item_BulletBag_Large'),
             ('KF_BEHIND_SHOP_CHILD_BUSH_01', 'Item_Range_SlingShot>Item_BulletBag_Medium>Item_BulletBag_Large'),
             ('KF_MIDO_CHEST_01', 'Obj_Rupee_Gold'), ('KF_MIDO_CHEST_02', 'Obj_Rupee_Gold'),
             ('KF_MIDO_CHEST_03', 'Item_BulletBag_Small'),
             ('LW GS Above Theater', 'Item_Scale_Silver>Item_Scale_Gold')]

    def specs(*hints):
        return build_mod.hint_specs(world, list(hints), given, texts, known_as)[0]

    one = specs('KF_NEAR_LOST_WOODS_GOSSIP=Item_Boomerang')
    good &= check('an item placed once: "They say {the Boomerang} can be found <where>." as --gossip text',
                  one == ['KF_NEAR_LOST_WOODS_GOSSIP=They say the {Boomerang} can be found '
                          + WHERE['KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02'] + '.'])
    fam = specs('KF_DEKU_TREE_GOSSIP_01=Item_Scale_Silver')
    good &= check('  a family, named by its first level: "... or an upgrade of it"',
                  fam == ['KF_DEKU_TREE_GOSSIP_01=They say a {Silver Scale} or an upgrade of it can be found '
                          + WHERE['LW GS Above Theater'] + '.'])
    at = specs('LW_BRIDGE_GOSSIP=@KF_BEHIND_SHOP_CHILD_BUSH_01', 'KF_DEKU_TREE_GOSSIP_02=@KF_MIDO_CHEST_02')
    good &= check('  @CHECK_ID: the item of that check (a family on two checks, an item on two checks)',
                  at == ['LW_BRIDGE_GOSSIP=They say the {Fairy Slingshot} or an upgrade of it can be found under a '
                         'bush in {Kokiri Forest}.',
                         'KF_DEKU_TREE_GOSSIP_02=They say a {Gold Rupee} can be found in a chest in the {Mansion of '
                         'the Great Mido} in {Kokiri Forest}.'])
    alias = specs('KF_NEAR_LOST_WOODS_GOSSIP=Item_BulletBag_Small')
    good &= check('  a small seed bag placed alone is the slingshot it gives (FAMILY_ALIASES), by either name',
                  alias == specs('KF_NEAR_LOST_WOODS_GOSSIP=@KF_MIDO_CHEST_03')
                  and 'Fairy Slingshot}' in alias[0] and 'or an upgrade' not in alias[0])
    good &= check('refused: an item on no check, on two checks (a family on two, an item on two), a family written '
                  'out, @ a check given nothing, a malformed spec',
                  refused(specs, 'KF_NEAR_LOST_WOODS_GOSSIP=Item_Hookshot')
                  and refused(specs, 'KF_NEAR_LOST_WOODS_GOSSIP=Item_Range_SlingShot')
                  and refused(specs, 'KF_NEAR_LOST_WOODS_GOSSIP=Obj_Rupee_Gold')
                  and refused(specs, 'KF_NEAR_LOST_WOODS_GOSSIP=Item_Scale_Silver>Item_Scale_Gold')
                  and refused(specs, 'KF_NEAR_LOST_WOODS_GOSSIP=@KF_MIDO_CHEST_04')
                  and refused(specs, 'KF_NEAR_LOST_WOODS_GOSSIP')
                  and refused(specs, '=Item_Boomerang'))

    # ------------------------------------------------------------------------------------- whole builds
    print('Whole builds')
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return os.path.join(tmp, name, 'romfs'), said.getvalue()

        assign = ['%s=%s' % x for x in given if x[0] != 'KF_MIDO_CHEST_03']
        base, said = run('h', *(assign + ['--hint', 'KF_NEAR_LOST_WOODS_GOSSIP=Item_Boomerang',
                                          '--hint', 'LW_BRIDGE_GOSSIP=@LW GS Above Theater',
                                          '--gossip', 'KF_DEKU_TREE_GOSSIP_01=A {plain} text beside the hints.']))
        want = {'GOSSIP_KOKIRI_FOREST_01': one[0].split('=', 1)[1],
                'GOSSIP_LOST_WOOD_02': 'They say a {Silver Scale} or an upgrade of it can be found '
                                       + WHERE['LW GS Above Theater'] + '.',
                'GOSSIP_KOKIRI_FOREST_03': 'A {plain} text beside the hints.'}
        ok, langs = True, 0
        for fn in sorted(os.listdir(os.path.join(romfs, 'Mals'))):
            if not fn.endswith('.sarc.zs'):
                continue
            langs += 1
            got = msbt.Msbt.read(sarc.Sarc.read(zstd.decompress(open(os.path.join(base, 'Mals', fn), 'rb').read(),
                                                                d)).files[build_mod.GOSSIP_MSG_FILE]).texts
            game = msbt.Msbt.read(sarc.Sarc.read(plain('Mals/' + fn[:-3])).files[build_mod.GOSSIP_MSG_FILE]).texts
            ok &= all(got[k] == build_mod.gossip_message(build_mod.gossip_layout(t, chars)) for k, t in want.items())
            ok &= all(got[k] == v for k, v in game.items() if k not in want) and list(got) == list(game)
        good &= check('a build with two hints and a --gossip text: in all %d languages the three stones say exactly '
                      'that, laid out as --gossip lays out, every other text as the game has it' % langs, ok and langs > 0)
        good &= check('  the build says what each stone hints, and where',
                      'hint               KF_NEAR_LOST_WOODS_GOSSIP -> KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02 '
                      '(Item_Boomerang): They say the Boomerang can be found in a pot in the House of the Know-It-All '
                      'Brothers in Kokiri Forest.' in said
                      and 'LW_BRIDGE_GOSSIP -> LW GS Above Theater (Item_Scale_Silver>Item_Scale_Gold)' in said)
        good &= check('refused before anything is written: a hint and a --gossip text on one stone, a hint on a stone '
                      'that is not one, a hint without assignments',
                      refused(run, 'n1', *(assign + ['--hint', 'KF_NEAR_LOST_WOODS_GOSSIP=Item_Boomerang',
                                                     '--gossip', 'KF_NEAR_LOST_WOODS_GOSSIP=two texts']))
                      and refused(run, 'n2', *(assign + ['--hint', 'KF_MIDO_CHEST_04=Item_Boomerang']))
                      and refused(run, 'n3', '--fix', 'skippable_opening', '--hint',
                                  'KF_NEAR_LOST_WOODS_GOSSIP=Item_Boomerang')
                      and not os.path.exists(os.path.join(tmp, 'n1')) and not os.path.exists(os.path.join(tmp, 'n2')))

    print()
    print('ALL OK' if good else 'SOME CHECKS FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
