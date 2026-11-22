"""Skip-level guard test: tools/build_mod.py refuses a later level of an upgrade family placed on its own
(UPGRADE_FAMILIES, skip_level_guard), before it writes anything; the progressive forms and the first levels
still build. The families are the ones declared once in build_mod.FAMILIES (the guard and the progressive forms
agree); their order is read again from the game's own files. Only reads the game; the builds it
runs go to a temporary folder that is removed again.

    python tests/skip_level_check.py "C:\\...\\romfs"
"""
import contextlib
import glob
import hashlib
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
from formats import zstd, byml, sarc  # noqa: E402

# the families as the game's item table (RSDB/PouchActorInfo) has them, lowest level first, and what it orders
# them by: family name (build_mod.FAMILIES) -> (the game's levels, key, values)
BAGS = lambda x: tuple('Item_%s_%s' % (x, size) for size in ('Small', 'Medium', 'Large'))   # noqa: E731
GAME = {
    'Scale': (('Item_Scale_Silver', 'Item_Scale_Gold'), 'DiveDepth', (6.0, 9.0)),
    'Ocarina': (('Item_Ocarina_Fairy', 'Item_Ocarina_Time'), 'OcarinaTypeValue', (1, 2)),
    'BombBag': (BAGS('BombBag'), 'AfterExpansionMaxNum', (20, 30, 40)),
    'BulletBag': (BAGS('BulletBag'), 'AfterExpansionMaxNum', (30, 40, 50)),
    'Quiver': (BAGS('Quiver'), 'AfterExpansionMaxNum', (30, 40, 50)),
    'StickBag': (BAGS('StickBag'), 'AfterExpansionMaxNum', (10, 20, 30)),
    'NutBag': (BAGS('NutBag'), 'AfterExpansionMaxNum', (20, 30, 40)),
    'Wallet': (BAGS('Wallet'), 'AfterExpansionMaxNum', (200, 500, 1000)),
    'Gauntlet': (('Item_Gauntlet_Goron', 'Item_Gauntlet_Silver', 'Item_Gauntlet_Gold'), 'LiftableGrade',
                 ('Low', 'Middle', 'High')),
    'Magic': (('Item_FairyBless_MP', 'Item_FairyBless_MPDouble'), 'MPMax', (24, 48)),
}
# the families as they are placed (the user's list, 2026-11-21): the game's, but for the levels never placed as
# such: the seed bags and the quivers start with the weapon (the small bag comes with it), the Deku Stick bags,
# Deku Nut bags and wallets at Medium (the small ones are never given)
PLACED = {
    'Scale': ('Item_Scale_Silver', 'Item_Scale_Gold'),
    'Hookshot': ('Item_Hookshot', 'Item_Longshot'),
    'Ocarina': ('Item_Ocarina_Fairy', 'Item_Ocarina_Time'),
    'BombBag': ('Item_BombBag_Small', 'Item_BombBag_Medium', 'Item_BombBag_Large'),
    'BulletBag': ('Item_Range_SlingShot', 'Item_BulletBag_Medium', 'Item_BulletBag_Large'),
    'Quiver': ('Item_Range_Bow', 'Item_Quiver_Medium', 'Item_Quiver_Large'),
    'StickBag': ('Item_StickBag_Medium', 'Item_StickBag_Large'),
    'NutBag': ('Item_NutBag_Medium', 'Item_NutBag_Large'),
    'Wallet': ('Item_Wallet_Medium', 'Item_Wallet_Large'),
    'Gauntlet': ('Item_Gauntlet_Goron', 'Item_Gauntlet_Silver', 'Item_Gauntlet_Gold'),
    'Magic': ('Item_FairyBless_MP', 'Item_FairyBless_MPDouble'),
}
# the hookshots are told apart by their weapon's settings: (pack, file in it, Range)
HOOKSHOTS = (('Weapon_Range_Hookshot', 'Component/HookshotParam/Weapon_Range_Hookshot.game__component__HookshotParam.bgyml', 10.0),
             ('Weapon_Range_Longshot', 'Component/HookshotParam/Weapon_Range_Longshot.game__component__HookshotParam.bgyml', 20.0))
# every later level, with the level it would skip and the form the message must name: its whole family
WHERE = build_mod.PROGRESSIVE_WHERE
LATER = {levels[k]: (levels[k - 1], '>'.join(levels), WHERE) for levels in PLACED.values()
         for k in range(1, len(levels))}
BOMB_BAGS = '>'.join(PLACED['BombBag'])
# the levels that can be placed on their own: each family's first one
FIRST = tuple(levels[0] for levels in PLACED.values())
# what the game's table has below a family's first level: never placed as such
ALIASED = ('Item_BulletBag_Small', 'Item_Quiver_Small')         # placed alone they become the weapon
# other names of a later level (the inventory's twin, the armour the gauntlets are kept as)
OTHER_NAMES = {'Pouch_Scale_Gold': 'Item_Scale_Silver', 'Pouch_Longshot': 'Item_Hookshot',
               'Pouch_Wallet_Large': 'Item_Wallet_Medium', 'Armor_Adult_Gauntlet_Silver': 'Item_Gauntlet_Goron',
               'Armor_Adult_Gauntlet_Gold': 'Item_Gauntlet_Silver', 'Obj_Ocarina_Time': 'Item_Ocarina_Fairy'}
# items of no family, a song among them, and the small seed bag and quiver (they stand for their weapons)
PLAIN = ('Item_Boomerang', 'Item_Melody_SariaSong', 'Item_AgonyStone', 'Item_FairyBless_DefenseDouble',
         'Item_Sword_Kokiri', 'Weapon_Shield_Deku', 'Item_Arrow_Fire') + ALIASED
# one check of each kind, a song, and a name that is no check: the guard stops the build before it looks
SPOTS = ('KF_MIDO_CHEST_01', 'KF_KOKIRI_SWORD_CHEST', 'KF_RUPEE_NEAR_MIDO_ITEM', 'KF_KOKIRI_CHILD_SHOP_01',
         'KF_HOUSE_OF_TWINS_CHILD_POT_01', 'KF_CIRCLE_CENTER_ROCK', 'KF_NEAR_SARIAS_HOUSE_CHILD_BUSH_01',
         'KF_KNOW_IT_ALL_HOUSE_GS', 'KF_CIRCLE_KOKIRI_GIFT', 'LW_SARIA_GIFT', 'LW_NEAR_BRIDGE_SCRUB',
         'Song from Saria', 'NO_SUCH_CHECK')
CHESTS = ('KF_MIDO_CHEST_01', 'KF_MIDO_CHEST_02', 'KF_MIDO_CHEST_03', 'KF_MIDO_CHEST_04')
GROUND = ('KF_RUPEE_NEAR_MIDO_ITEM', 'KF_RUPEE_NEAR_FADO_ITEM_01')
GIFT, SCRUB = 'KF_CIRCLE_KOKIRI_GIFT', 'LW_NEAR_BRIDGE_SCRUB'
CIRCLE_FIX = ['--fix', 'kokiri_circle_after_dungeons']


def check(name, ok):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def tree(folder):
    """every file under `folder` with a checksum of its bytes"""
    return {os.path.relpath(f, folder): hashlib.sha256(open(f, 'rb').read()).hexdigest()
            for f in glob.glob(os.path.join(folder, '**', '*'), recursive=True) if os.path.isfile(f)}


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)   # noqa: E731
    pouch = {r['__RowId']: r for r in byml.loads(plain(ground_items.table_path('PouchActorInfo'))).root}
    families = build_mod.UPGRADE_FAMILIES
    good = True

    # one declaration: the guard's families are the builder's, and every progressive form is one of them
    names = [x for f in families for x in f]
    forms = set(build_mod.PROGRESSIVE_PAIRS) | set(build_mod.THREE_LEVEL_FAMILIES)
    good &= check('the families are declared once (FAMILIES): the guard\'s rows, the pairs and the three-level '
                  'families are the same %d' % len(families),
                  build_mod.FAMILIES == PLACED and tuple(families) == tuple(build_mod.FAMILIES.values())
                  and forms == set(families) and len(forms) == len(families)
                  and build_mod.PROGRESSIVE_PAIRS == {f for f in families if len(f) == 2}
                  and build_mod.THREE_LEVEL_FAMILIES == {f: n for n, f in build_mod.FAMILIES.items() if len(f) == 3})

    # the table against the game's own files
    good &= check('%d families, %d levels: every level is an item of the game (a row in PouchActorInfo), once'
                  % (len(families), len(names)),
                  len(set(names)) == len(names) and all(x in pouch for x in names)
                  and all(k in pouch and v in names for k, v in build_mod.UPGRADE_OTHER_NAMES.items()))
    ok = set(GAME) | {'Hookshot'} == set(build_mod.FAMILIES)
    for name, (levels, key, values) in GAME.items():
        ok &= tuple(pouch[x].get(key) for x in levels) == values and list(values) == sorted(values, key=lambda v: (
            ('Low', 'Middle', 'High').index(v) if isinstance(v, str) else v))
    good &= check("  the levels' order is the game's: dive depth, ocarina type, bag and wallet size, lift grade, "
                  'magic meter', ok)
    ranges = []
    for pack, inner, _ in HOOKSHOTS:
        files = sarc.Sarc.read(plain(ground_items.pack_path(pack))).files
        ranges.append(byml.loads(bytes(dict(files)[inner])).root)
    good &= check('  Hookshot > Longshot: the weapons\' Range is 10 and 20, the Longshot\'s settings build on the '
                  'Hookshot\'s',
                  [r.get('Range') for r in ranges] == [h[2] for h in HOOKSHOTS]
                  and ranges[1].get('$parent', '').endswith('Weapon_Range_Hookshot.game__component__HookshotParam.gyml')
                  and ('Item_Hookshot', 'Item_Longshot') in families)
    # no family of the item table is missing: every Item_ row with one of those values is in the table
    game_names = {x for levels, _, _ in GAME.values() for x in levels}
    level_keys = {k for _, k, _ in GAME.values()} - {'LiftableGrade', 'MPMax'}
    marked = {k for k, r in pouch.items() if k.startswith('Item_') and (
        level_keys & set(r) or r.get('ExpansionAvility') == 'LiftGradeUP'
        or str(r.get('PouchSpecialDeal', '')).startswith('FairyBlessMP'))}
    good &= check('  no other item of the table has a level (%d rows with a depth, type, size, grade or meter '
                  'blessing)' % len(marked), marked == game_names)
    # a family as it is placed: the game's levels without the ones never given, the small seed bag and quiver
    # as their weapons
    as_placed = {name: tuple(build_mod.FAMILY_ALIASES.get(x, x) for x in levels if x not in build_mod.NEVER_GIVEN)
                 for name, (levels, _, _) in GAME.items()}
    good &= check('  a family is placed as the game has it, but: the small Deku Stick bag, Deku Nut bag and wallet '
                  'left out (never given), the small seed bag and quiver as their weapon',
                  all(build_mod.FAMILIES[name] == levels for name, levels in as_placed.items())
                  and set(build_mod.NEVER_GIVEN) | set(ALIASED) == game_names - set(names)
                  and set(build_mod.FAMILY_ALIASES) == set(ALIASED))
    later = {x for f in families for x in f if build_mod.skipped_level(x)}
    good &= check('  %d later levels are refused alone, %d levels pass alone (each family\'s first), %d are never '
                  'placed, %d stand for their weapon' % (len(LATER), len(FIRST), len(build_mod.NEVER_GIVEN),
                                                        len(ALIASED)),
                  later == set(LATER) and set(names) - later == set(FIRST)
                  and all(build_mod.skipped_level(x)[2] == LATER[x][0] for x in LATER)
                  and not any(build_mod.skipped_level(x) for x in ALIASED + tuple(build_mod.NEVER_GIVEN)))
    good &= check('  every later level has a form that names it: its whole family, lowest level first',
                  all(build_mod.progressive_form(*build_mod.upgrade_level(x)) == (LATER[x][1], WHERE)
                      for x in LATER))

    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *assign):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(assign))
            return said.getvalue(), tree(os.path.join(tmp, name))

        def message(name, *assign):
            try:
                run(name, *assign)
            except SystemExit as e:
                return str(e) if e.code else None
            return None

        # each later level alone, on every kind of spot
        ok, shown = True, []
        for item, (before, form, where) in sorted(LATER.items()):
            for spot in SPOTS:
                said = message('no', '%s=%s' % (spot, item), *CIRCLE_FIX) or ''
                ok &= said.startswith('%s: %s cannot be placed on its own' % (spot, item)) \
                    and 'could be taken before %s, skipping a level' % before in said \
                    and said.endswith('Use %s=%s (%s).' % (spot, form, where))
                if spot == SPOTS[0] and item in ('Item_Scale_Gold', 'Item_BombBag_Large', 'Item_Quiver_Medium'):
                    shown.append(said)
        ok &= os.listdir(tmp) == []
        good &= check('each of the %d later levels alone is refused on %d spots of every kind, with nothing written; '
                      'the message is as below' % (len(LATER), len(SPOTS)), ok)
        ok = all('could be taken before %s,' % before in (message('no', '%s=%s' % (CHESTS[0], item)) or '')
                 for item, before in OTHER_NAMES.items()) and os.listdir(tmp) == []
        good &= check('  the same under the levels\' other names (Pouch_..., the gauntlets\' armour, '
                      'Obj_Ocarina_Time)', ok)
        ok = all(message('no', '%s=%s' % (CHESTS[0], 'Item_Scale_Silver'), '%s=%s' % (CHESTS[1], item))
                 for item in ('Item_Scale_Gold', 'Item_BombBag_Medium')) and os.listdir(tmp) == []
        good &= check('  also when the level before it is on another check of the same build', ok)

        # what was refused before still is, with its own message
        never = [message('no', '%s=%s' % (CHESTS[0], x)) or '' for x in sorted(build_mod.NEVER_GIVEN)]
        wrong = [message('no', '%s=%s' % (CHESTS[0], x)) or '' for x in (
            'Item_Scale_Gold>Item_Scale_Silver', 'Item_Scale_Silver>Item_Longshot',
            'Item_BombBag_Small>Item_BombBag_Medium', 'Item_BombBag_Medium>Item_BombBag_Large',
            'Item_BombBag_Large>Item_BombBag_Medium>Item_BombBag_Small',
            'Item_Quiver_Small>Item_Quiver_Medium>Item_Quiver_Large', 'Item_Quiver_Medium>Item_Quiver_Large',
            'Item_Gauntlet_Goron>Item_Gauntlet_Silver', 'Item_Wallet_Small>Item_Wallet_Medium>Item_Wallet_Large',
            'Item_Range_SlingShot>Item_Quiver_Medium>Item_Quiver_Large')]
        good &= check('still refused: the items the game never gives (their own message); a pair or triple the '
                      'builder doesn\'t know',
                      all('never gives' in x for x in never) and len(never) == 3
                      and all('the builder knows' in x or 'never gives' in x for x in wrong)
                      and os.listdir(tmp) == [])

        # the guard itself lets everything else through
        try:
            build_mod.skip_level_guard([('A', x) for x in FIRST + PLAIN]
                                       + [('B', '>'.join(p)) for p in sorted(build_mod.PROGRESSIVE_PAIRS)]
                                       + [('C', '>'.join(t)) for t in sorted(build_mod.THREE_LEVEL_FAMILIES)])
            ok = True
        except SystemExit:
            ok = False
        good &= check('the guard passes: the %d first levels, items of no family (a song, the Echo Gem, the '
                      'small seed bag and quiver), every pair and triple' % len(FIRST), ok)
        good &= check('  the small seed bag and quiver still stand for their weapons; the scrubs\' companions '
                      'are as before',
                      build_mod.FAMILY_ALIASES == {'Item_BulletBag_Small': 'Item_Range_SlingShot',
                                                   'Item_Quiver_Small': 'Item_Range_Bow'}
                      and build_mod.SCRUB_COMPANIONS == {'Item_Range_SlingShot': ['Item_BulletBag_Small'],
                                                         'Item_Range_Bow': ['Item_Quiver_Small']})

        # whole builds: the progressive forms
        pairs = ['>'.join(p) for p in (('Item_Scale_Silver', 'Item_Scale_Gold'), ('Item_Hookshot', 'Item_Longshot'),
                                       ('Item_Ocarina_Fairy', 'Item_Ocarina_Time'))]
        said, files = run('forms', CHESTS[0] + '=' + pairs[0], CHESTS[1] + '=' + pairs[1], CHESTS[2] + '=' + pairs[2],
                          CHESTS[3] + '=' + BOMB_BAGS, GROUND[0] + '=' + pairs[0], GIFT + '=' + pairs[1], *CIRCLE_FIX)
        good &= check('built: the three pairs in small chests, the bomb bags\' triple in a small chest, a pair on '
                      'a freestanding item and on a gift (%d files)' % len(files),
                      len(files) > 4 and all(x in said for x in (
                          'then Item_Scale_Gold', 'then Item_Longshot', 'Obj_TBox_NX2_BombBag',
                          'NX2_Turn_Scale_Gold', 'else Event241 gives Item_Longshot'))
                      and said.count('Obj_TBox_A_01 -> Obj_TBox_A_06') == 6)

        # whole builds: the new forms, one of each shape on each way of placing it
        sling, gauntlets = '>'.join(PLACED['BulletBag']), '>'.join(PLACED['Gauntlet'])
        wallets, magic = '>'.join(PLACED['Wallet']), '>'.join(PLACED['Magic'])
        said, files = run('more', CHESTS[0] + '=' + sling, CHESTS[1] + '=' + wallets, GROUND[0] + '=' + gauntlets,
                          GROUND[1] + '=' + magic, GIFT + '=' + sling, SCRUB + '=' + gauntlets, *CIRCLE_FIX)
        good &= check('built: the slingshot\'s family in a small chest and on a gift, the wallets in a small chest, '
                      'the gauntlets on a freestanding item and at a scrub, the magic on a freestanding item '
                      '(%d files)' % len(files),
                      len(files) > 8 and all(x in said for x in (
                          'Obj_TBox_NX2_BulletBag', 'then Item_Wallet_Large', 'NX2_Turn_Gauntlet_Gold',
                          'NX2_Turn_FairyBless_MPDouble', 'gives Item_BulletBag_Large',
                          'sells Item_Gauntlet_Gold at the same price',
                          'Item_BulletBag_Small comes with Item_Range_SlingShot')))

        # whole builds: first levels alone
        said, files = run('first', CHESTS[0] + '=Item_Scale_Silver', CHESTS[1] + '=Item_Hookshot',
                          CHESTS[2] + '=Item_BombBag_Small', CHESTS[3] + '=Item_BulletBag_Small',
                          GROUND[0] + '=Item_Ocarina_Fairy', GROUND[1] + '=Item_Gauntlet_Goron',
                          GIFT + '=Item_FairyBless_MP', SCRUB + '=Item_Quiver_Small', *CIRCLE_FIX)
        good &= check('built: first levels alone in chests, on the ground, on a gift and at a scrub (%d files)'
                      % len(files),
                      len(files) > 4 and all(x in said for x in (
                          '-> Item_Scale_Silver', '-> Item_Hookshot', '-> Item_BombBag_Small', 'Item_FairyBless_MP'))
                      and 'Obj_TBox_A_06' not in said)
        good &= check('  the small seed bag in a chest gives the slingshot; the small quiver at a scrub the bow '
                      'and its quiver with it',
                      '%-18s Item_BulletBag_Small placed: gives Item_Range_SlingShot' % CHESTS[3] in said
                      and '-> Item_Range_SlingShot' in said
                      and '%-18s Item_Quiver_Small placed: gives Item_Range_Bow' % SCRUB in said
                      and 'Item_Quiver_Small' in said.split('placed: gives Item_Range_Bow', 1)[1])
        said2, files2 = run('first2', CHESTS[0] + '=Item_StickBag_Medium', CHESTS[1] + '=Item_NutBag_Medium',
                            CHESTS[2] + '=Item_Wallet_Medium', CHESTS[3] + '=Item_Quiver_Small', *CIRCLE_FIX)
        good &= check('built: the Medium stick bag, nut bag and wallet alone (their Small ones are never placed), '
                      'the small quiver as the bow',
                      len(files2) > 2 and all(x in said2 for x in (
                          '-> Item_StickBag_Medium', '-> Item_NutBag_Medium', '-> Item_Wallet_Medium',
                          '-> Item_Range_Bow')))

        # a refused build leaves an earlier build of the same name as it was
        ok = bool(message('first', CHESTS[0] + '=Item_Scale_Gold')) and tree(os.path.join(tmp, 'first')) == files \
            and sorted(os.listdir(tmp)) == ['first', 'first2', 'forms', 'more']
        good &= check('a refused build leaves the earlier build of the same name untouched, byte for byte', ok)

    print()
    print('\n'.join(shown))
    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
