"""Ground lift test: every item in ground_items.GROUND_LIFT gets a lifted copy of its animation project that puts
its lowest vertex 0.05 above the ground and leaves it held up as the game shows it, on the game's own files; the
items the game never gives are refused. Reads only; writes nothing.

    python tests/ground_lift_check.py "C:\\...\\romfs"
"""
import hashlib
import os
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import item_pose  # noqa: E402
import sizes  # noqa: E402
from formats import zstd, byml, sarc  # noqa: E402

VERSIONS = ('ground', 'token', 'turn')
# the copies seen lying right in game (bracelet and magic 2026-11-17, scales 2026-11-19), made of the item's own
# project then: {the item's project: (the copy's name then, its checksum)}. Their copies are now made of
# ground_items.HELD_BASE (held up as the game shows them): their ground pose must still be the one seen
TESTED = {'Item_Gauntlet_Goron_Animation':
          ('NX2G_Gauntlet_Goron_Animation', '5da73ab419a5ed5d64f67b3cf59cb94d36d1419a464bb9f3627dd9132ca334ef'),
          'Item_FairyBless_MPDouble_Animation':
          ('NX2G_FairyBless_MPDouble_Animation', 'c9192c72e16f312c34554dcb819de52cfaf07e2051dab4cbf21b6cbdd3185ddf'),
          'Item_Scale_Silver_Animation':
          ('NX2G_Scale_Silver_Animation', 'ab44960310b560938b63b2cd33fef668a17cf04fa592da9d2fac570a0faeb7ea'),
          'Item_Scale_Gold_Animation':
          ('NX2G_Scale_Gold_Animation', '29bdb58524a6b93a35081f600926409e48367063022a6af3bada60a89c0f8717')}
# projects with a held-up pose of their own (Pose_GetDemo): their copy is the project itself, as before
OWN_HELD = ('Obj_Token_Gold_Animation', 'Item_Arrow_Fire_Animation', 'Obj_ArrowBundle_Large_Animation')
# not in the randomizer for now (trade quest items), or not decided (Zelda's Letter, the masks): never lifted here
LEFT_OUT = ('Sword_Giant', 'Sword_Biggoron', 'Sword_BrokenGiant', 'BrokenSword', 'ClaimCheck', 'EyeballFrog',
            'EyeDrop', 'Prescription', 'PoacherSaw', 'OddMushroom', 'OddPowder', 'Cucco', 'PocketEgg', 'WeirdEgg',
            'ZeldaLetter', 'Mask_')
# not listed, so no copy: an item that lies right, one whose project another item's copy is made of, one with
# vertices on more bones than Skl_Root
NOT_LIFTED = ('Item_Boomerang', 'TBox_ArrowBundle_Large', 'Item_Arrow_Light', 'Item_BombBag_Small')
# the items that name no item settings (PouchContentRef) themselves: theirs are the ones of the actor they inherit
# from. {item: (the actor it inherits from, the item settings it has from the small one, its own count)}
KEY, BOMB = 'KeyItemDefault', 'BombBag'
INHERITS = {'Item_BombBag_Medium': ('Item_BombBag_Small', BOMB, 30),
            'Item_BombBag_Large': ('Item_BombBag_Medium', BOMB, 40),
            'Item_BulletBag_Medium': ('Item_BulletBag_Small', KEY, 40),
            'Item_BulletBag_Large': ('Item_BulletBag_Medium', KEY, 50),
            'Item_NutBag_Medium': ('Item_NutBag_Small', KEY, 30),
            'Item_NutBag_Large': ('Item_NutBag_Medium', KEY, 40),
            'Item_Quiver_Medium': ('Item_Quiver_Small', KEY, 40),
            'Item_Quiver_Large': ('Item_Quiver_Medium', KEY, 50),
            'Item_StickBag_Medium': ('Item_StickBag_Small', KEY, 20),
            'Item_StickBag_Large': ('Item_StickBag_Medium', KEY, 30),
            'Item_Wallet_Medium': ('Item_Wallet_Small', KEY, 500),
            'Item_Wallet_Large': ('Item_Wallet_Medium', KEY, 1000)}
# actors that inherit item settings in other ways (not built on the item base): still no version of them
STILL_REFUSED = ('Armor_Child_Mask_Bunny', 'Obj_Spirit_PoeFlat', 'Armor_Adult_Default_Head')


def check(name, ok):
    print('%-98s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def vertex_bones(data):
    """{bone name (or 'several'): number of vertices that hang on it} of a model (layout: tools/item_pose.py)"""
    sk = data.find(b'FSKL')
    bones, to_bone = struct.unpack_from('<QQ', data, sk + 0x10)
    n, smooth, rigid = struct.unpack_from('<3H', data, sk + 0x38)
    names = [item_pose._str_at(data, struct.unpack_from('<Q', data, bones + 0x58 * b)[0]) for b in range(n)]
    table = struct.unpack_from('<%dH' % (smooth + rigid), data, to_bone)
    pool = struct.unpack_from('<Q', data, struct.unpack_from('<Q', data, 0xb0)[0] + 8)[0]
    fm = data.find(b'FMDL')
    shapes = struct.unpack_from('<Q', data, fm + 0x28)[0]
    out = {}
    for s in range(struct.unpack_from('<H', data, fm + 0x6a)[0]):
        o = shapes + 0x60 * s
        vtx = struct.unpack_from('<Q', data, o + 0x10)[0]
        shape_bone, per_vertex = struct.unpack_from('<H', data, o + 0x54)[0], data[o + 0x5a]
        attrs, strides = (struct.unpack_from('<Q', data, vtx + k)[0] for k in (8, 0x38))
        at, count, n_vtx = struct.unpack_from('<IB3xI', data, vtx + 0x48)
        index = None
        for a in range(count):
            q = attrs + 0x10 * a
            if item_pose._str_at(data, struct.unpack_from('<Q', data, q)[0]) == '_i0':
                index = struct.unpack_from('<H', data, q + 0xc)[0]
        stride = struct.unpack_from('<I', data, strides)[0]
        for v in range(n_vtx):
            if per_vertex == 0:
                k = names[shape_bone]
            elif per_vertex == 1:
                k = names[table[data[pool + at + stride * v + index]]]
            else:
                k = 'several'
            out[k] = out.get(k, 0) + 1
    return out


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)  # noqa: E731
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    has_model = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))  # noqa: E731
    info = {r['__RowId']: r for r in table_rows('ActorInfo')}
    out = build_mod.Output(romfs, None, d)
    lift, box, shared = ground_items.GROUND_LIFT, ground_items.GROUND_LIFT_BOX, ground_items.GROUND_LIFT_AS
    gap, spin = ground_items.GROUND_GAP, ground_items.SPIN_ROOT_LIFT
    good = True

    good &= check('the lists: no item twice; box items and shared items are listed; a shared item is measured on '
                  'a listed one', len(set(lift)) == len(lift) and set(box) <= set(lift) and set(shared) <= set(lift)
                  and all(v in lift and v not in shared for v in shared.values()))
    good &= check('no trade quest item, Zelda\'s Letter or mask is listed',
                  not [i for i in lift if any(x in i for x in LEFT_OUT)])

    copies = {}                                        # path -> (data, the game file, first item)
    built = one = names = only = poses = lows = sure = packs = entries = same = helds = bases = True
    tested, kinds = {}, {True: set(), False: set()}
    said = []
    for item in lift:
        row = info[item]
        model = plain('Model/%s.%s.bfres' % (row['ModelProjectName'], row['FmdbName']))
        versions = 0
        for version in VERSIONS:
            try:
                name, pack, _, new_rows, loose = ground_items.build(item, plain, table_rows, has_model, version)
            except SystemExit:
                continue                               # (the small seed bag and quiver have no animation
            versions += 1                              # settings: only the token version)
            one &= len(loose) == 1
            (path, (x, like, old_h, new_h, own_path)), = loose.items()
            game, made_of = plain(own_path), plain(like)
            own = own_path[len('Model/'):-len('.anim.bfres')]
            own_held = ground_items.has_held_pose(game)
            kinds[own_held].add(own)
            lifted_name = ground_items.lifted_project(own, game)
            # the copy: a name new to the game, as long as the name of the game file it is made of
            names &= path == ground_items.model_path(lifted_name) and len(path) == len(like) \
                and lifted_name.startswith('NX2G') and not os.path.exists(os.path.join(romfs, *path.split('/')) + '.zs')
            # made of the item's own project when that has a held-up pose (only the name, a flag and the height
            # differ), else of HELD_BASE (only the name and its two poses' values and flags differ)
            bases &= like == (own_path if own_held else ground_items.model_path(ground_items.HELD_BASE)) \
                and own_held == (own in OWN_HELD)
            differ = [i for i in range(len(made_of)) if i >= len(x) or x[i] != made_of[i]]
            if own_held:
                only &= len(x) == len(made_of) and len(differ) <= 12 \
                    and item_pose.animations(x).keys() == item_pose.animations(game).keys()
            else:
                spots = set()
                for anim in (ground_items.GROUND_POSE, ground_items.HELD_POSE):
                    at = item_pose.read_pose(made_of, anim)
                    spots |= set(range(at['base'], at['base'] + 40)) | set(range(at['at'] + 0x28, at['at'] + 0x2c))
                k = made_of.find(ground_items.HELD_BASE.encode())
                spots |= set(range(k, k + len(ground_items.HELD_BASE)))
                only &= len(x) == len(made_of) and set(differ) <= spots \
                    and {a: sorted(b) for a, b in item_pose.animations(x).items()} \
                    == {a: [item_pose.ROOT, item_pose.BONE] for a in (ground_items.GROUND_POSE, ground_items.HELD_POSE)}
            # held up (Rotate_GetDemo: Pose_GetDemo, else Pose_Common): exactly the pose the game shows
            was_held = item_pose.read_pose(game, ground_items.HELD_POSE if own_held else ground_items.GROUND_POSE)
            now_held = item_pose.read_pose(x, ground_items.HELD_POSE)
            helds &= all(now_held[f] == was_held[f] for f in ('scale', 'rot', 'move')) \
                and item_pose.read_pose(x, ground_items.HELD_POSE, item_pose.ROOT)['flags'] == item_pose.STILL
            if own in TESTED and own not in tested:
                # the ground pose is the one of the copy seen in game
                then = ground_items.lifted_in_place(game, own, new_h, TESTED[own][0])
                tested[own] = hashlib.sha256(then).hexdigest() == TESTED[own][1] \
                    and all(item_pose.read_pose(x)[f] == item_pose.read_pose(then)[f] for f in ('scale', 'rot', 'move'))
            pose, old_pose = item_pose.read_pose(x), item_pose.read_pose(game)
            poses &= (pose['scale'], pose['rot'], pose['move'][0], pose['move'][2]) \
                == (old_pose['scale'], old_pose['rot'], old_pose['move'][0], old_pose['move'][2]) \
                and abs(pose['move'][1] - new_h) < 1e-6 and abs(old_pose['move'][1] - old_h) < 1e-6 \
                and item_pose.read_pose(x, bone=item_pose.ROOT)['flags'] == item_pose.STILL
            # where the item lies with it, by its own model's vertices
            low = ground_items.vertex_low(x, model, None) + spin
            was = ground_items.vertex_low(game, model, None) + spin
            if item in box:
                lows &= low > gap - 1e-5                # as tested in game (the bracelet 0.074)
            elif item in shared:
                lows &= abs(low - gap) <= ground_items.GROUND_SHARED
            else:
                lows &= abs(low - gap) < 1e-5
            lows &= abs(was - gap) > ground_items.GROUND_NEAR
            # the measure is sure: every vertex hangs on Skl_Root
            sure &= list(vertex_bones(model)) == [item_pose.BONE]
            # the pack and the row name the copy
            files = sarc.Sarc.read(pack).files
            comp = ground_items.resolved_components(files, name)
            anim = byml.loads(files[ground_items._ref_path(comp['AnimationRef'])]).root['AnimationResources']
            packs &= [r['ModelProjectName'] for r in anim] == [ground_items.COMMON_ANIM, lifted_name] \
                and new_rows['ActorInfo']['AnimationResources'] == anim
            # one copy for a project, whichever item and version is built
            if path in copies:
                same &= copies[path][0] == x
            else:
                copies[path] = (x, like, item)
                out.add(path, x, like, made_of)         # the size entry, made as the build makes it
                need = sizes.rule(path, x)
                entries &= out.table.get(path) == out.table.get(like) and (need is None or out.table.get(path) >= need)
            if version == 'token':
                said.append('  %-30s height %+.4f -> %+.4f (%+.3f), lowest vertex %+.4f -> %+.4f  %s' % (
                    item, old_h, new_h, new_h - old_h, was, low,
                    'on the copy of ' + shared[item] if item in shared else 'by the box' if item in box else ''))
        built &= versions > 0
    good &= check('every listed item (%d) builds in at least one version, each with one lifted copy' % len(lift),
                  built and one)
    good &= check('the copy\'s name starts with NX2G, is as long as the game file\'s it is made of, new to the game',
                  names)
    good &= check('made of the item\'s own project when it has a %s (%d), else of %s (%d)'
                  % (ground_items.HELD_POSE, len(kinds[True]), ground_items.HELD_BASE, len(kinds[False])),
                  bases and kinds[True] == set(OWN_HELD) and len(kinds[False]) > 0)
    good &= check('only the name and the poses\' values differ from that file; the ground pose only in its height',
                  only and poses)
    good &= check('held up (%s): size, turn and place exactly the game\'s, for every copy' % ground_items.HELD_POSE,
                  helds)
    good &= check('lowest vertex %.2f above the ground (shared copies: within %.2f); it was more than %.2f off'
                  % (gap, ground_items.GROUND_SHARED, ground_items.GROUND_NEAR), lows)
    good &= check('every vertex of every listed model hangs on %s' % item_pose.BONE, sure)
    good &= check('the pack and the table row name the copy', packs)
    good &= check('one copy for a project (%d copies), the same bytes whichever item or version is built'
                  % len(copies), same)
    good &= check('each copy\'s size entry is the game file\'s (same length) and meets the rules', entries)
    good &= check('the ground pose of the copies seen right in game is as then (bracelet, magic, both scales)',
                  sorted(tested) == sorted(TESTED) and all(tested.values()))
    for item, first in sorted(shared.items()):
        good &= check('  %s lies on the copy of %s' % (item, first),
                      ground_items.own_projects(plain, item) == ground_items.own_projects(plain, first))
    none = True
    for item in NOT_LIFTED:
        for version in ('ground', 'token'):
            none &= not ground_items.build(item, plain, table_rows, has_model, version)[4]
    good &= check('items not listed get no copy (%s)' % ', '.join(NOT_LIFTED), none)

    # items whose item settings are the ones of the actor they inherit from (the medium and large bags, quivers
    # and wallets): a ground version that gives the item itself
    pouch_rows = {r['__RowId']: r for r in table_rows('PouchActorInfo')}
    ref, base = 'PouchContentRef', ground_items.ap_path(ground_items.ITEM_BASE)
    gyml = lambda path: 'Work/' + path[:-len('.bgyml')] + '.gyml'   # noqa: E731
    found, parents, counts, gives, lifted, untouched = [], True, True, True, True, True
    for item in sorted(pouch_rows):
        if not os.path.exists(os.path.join(romfs, *ground_items.pack_path(item).split('/')) + '.zs'):
            continue
        files = sarc.Sarc.read(plain(ground_items.pack_path(item))).files
        own = byml.loads(files[ground_items.ap_path(item)]).root
        if item == ground_items.ITEM_BASE or base not in files:
            continue
        if ref in own['Components']:
            # names its own: read as before
            untouched &= ground_items.item_components(files, item) == own['Components']
            continue
        found.append(item)
        if item not in INHERITS:
            continue
        parent, settings, count = INHERITS[item]
        settings_path = ground_items.pouch_param_path(settings)
        comp = ground_items.item_components(files, item)
        # the actor it inherits from is in its pack; the settings are the nearest one's that names any; everything
        # else is its own
        chain, at = [], ground_items._parent_path(own)
        while at in files and at != base:
            chain.append(at)
            at = ground_items._parent_path(byml.loads(files[at]).root)
        named = [byml.loads(files[c]).root['Components'][ref] for c in chain
                 if ref in byml.loads(files[c]).root['Components']]
        parents &= chain[0] == ground_items.ap_path(parent) and at == base and comp[ref] == named[0] \
            and comp[ref] == '?' + settings_path and settings_path in files \
            and {k: v for k, v in comp.items() if k != ref} == own['Components'] \
            and all(r in own['Components'] for r in ground_items.ITEM_REFS if r != ref)
        # its count is its own: in its own actor's files and in its own row
        table = byml.loads(files[ground_items._ref_path(own['Components']['GameParameterTableRef'])]).root
        num = byml.loads(files[ground_items._ref_path(table['Components']['ExpansionMaxNumActor'])]).root
        counts &= num['MaxNum'] == count == pouch_rows[item]['AfterExpansionMaxNum']
        for version in VERSIONS:
            name, pack, new_inner, new_rows, loose = ground_items.build(item, plain, table_rows, has_model, version)
            inner = sarc.Sarc.read(pack).files
            ap = byml.loads(inner[ground_items.ap_path(name)]).root['Components']
            mine = byml.loads(inner[ground_items._ref_path(ap[ref])]).root
            # its own item settings: the item's as parent, picked up by walking into it, and the item itself is
            # what goes into the inventory; nothing else. The item's own files are the game's, the row the item's
            gives &= ap[ref] == '?' + ground_items.pouch_param_path(name) \
                and dict(mine) == {'$parent': gyml(settings_path), 'DefaultAutoGet': True,
                                   'PouchActor': gyml(ground_items.ap_path(item))} \
                and inner[settings_path] == files[settings_path] \
                and all(inner[q] == files[q] for q in inner if q in files) \
                and not [q for q in inner if q.startswith('GameParameter/') and item[5:] in q] \
                and {k: v for k, v in new_rows['PouchActorInfo'].items() if k != '__RowId'} \
                == {k: v for k, v in pouch_rows[item].items() if k != '__RowId'} \
                and new_rows['PouchActorInfo']['AfterExpansionMaxNum'] == count \
                and new_rows['ActorInfo']['ActorName'] == item and new_rows['ActorInfo']['FmdbName'] == item \
                and ap['ActorNameRef'] == own['Components']['ActorNameRef'] \
                and ap['ModelInfoRef'] == own['Components']['ModelInfoRef']
            lifted &= item in lift and len(loose) == 1
    good &= check('item actors that name no item settings themselves: the %d medium and large bags, quivers and '
                  'wallets' % len(INHERITS), found == sorted(INHERITS))
    good &= check('  each inherits from the smaller one, in its own pack; its item settings are that one\'s (%s, %s)'
                  % (BOMB, KEY), parents)
    good &= check('  its count is its own, in its actor\'s files and its row (%s)'
                  % ', '.join('%s %d' % (k[5:], v[2]) for k, v in sorted(INHERITS.items())), counts)
    good &= check('  each builds on the ground, as a Gold Skulltula drop and as a turning item, lifted', lifted)
    good &= check('  what the pick-up adds is the item itself (PouchActor), with its own row, name and model', gives)
    good &= check('  an item that names its own item settings is read as before', untouched)
    refused = True
    for item in STILL_REFUSED + (ground_items.ITEM_BASE,):
        try:
            ground_items.build(item, plain, table_rows, has_model, 'ground')
            refused = False
        except SystemExit as e:
            refused &= ref in str(e) or 'ActorNameRef' in str(e)
    good &= check('  actors not built on %s, and it itself, get no version this way (%s)'
                  % (ground_items.ITEM_BASE, ', '.join(STILL_REFUSED)), refused)

    # items the game never gives as such (build_mod.NEVER_GIVEN): refused everywhere, not lifted
    never = build_mod.NEVER_GIVEN
    pouch = {r['__RowId']: r for r in table_rows('PouchActorInfo')}
    bag_of = {}                                        # small bag -> the rows that bring it when first got
    for r in pouch.values():
        if r.get('IsAbleToGetBagIfGet') and r.get('SmallBagActor'):
            bag_of.setdefault(r['SmallBagActor'].split('/')[-1].split('.')[0], []).append(r['__RowId'])
    good &= check('never given: %s' % ', '.join(sorted(never)),
                  sorted(never) == ['Item_NutBag_Small', 'Item_StickBag_Small', 'Item_Wallet_Small'])
    good &= check('  none of them is listed for a lift', not set(never) & set(lift))
    good &= check('  the game brings the small stick and nut bags with the first stick or nut (%s)'
                  % ', '.join('%s: %d rows' % (k[5:], len(v)) for k, v in sorted(bag_of.items())),
                  sorted(bag_of) == ['Item_NutBag_Small', 'Item_StickBag_Small']
                  and 'Item_DekuStick' in bag_of['Item_StickBag_Small'] and 'Item_DekuNut' in bag_of['Item_NutBag_Small'])
    bags = [k for k in pouch if k.startswith('Item_') and 'Bag_' in k or k.startswith('Item_Quiver_')]
    good &= check('  their rows are the only bags\' (%d) without IsItemStockMaxIfGet' % len(bags),
                  sorted(k for k in bags if not pouch[k].get('IsItemStockMaxIfGet'))
                  == ['Item_NutBag_Small', 'Item_StickBag_Small'])
    good &= check('  they cannot be held up (no animation settings); the small wallet has no actor pack',
                  not ground_items.can_hold_up(plain, 'Item_StickBag_Small')
                  and not ground_items.can_hold_up(plain, 'Item_NutBag_Small')
                  and not os.path.exists(os.path.join(romfs, 'Pack', 'Actor', 'Item_Wallet_Small.pack.zs')))
    refused = True
    with tempfile.TemporaryDirectory() as tmp:
        for item in sorted(never):
            for spot in ('KF_TRAINING_AREA_RUPEE_ITEM_01', 'NO_SUCH_CHECK'):
                for placed in (item, 'Item_Scale_Silver>' + item):
                    try:
                        build_mod.main(['--romfs', romfs, '--out', tmp, '%s=%s' % (spot, placed)])
                        refused = False
                    except SystemExit as e:
                        refused &= item in str(e) and 'never gives' in str(e) and spot in str(e)
        refused &= os.listdir(tmp) == []               # stopped before anything was written
    good &= check('  the builder refuses each of them on any spot, alone or in a pair, before it writes anything',
                  refused)
    try:
        build_mod.never_given([('A', 'Item_BulletBag_Small'), ('B', 'Item_Quiver_Small'), ('C', 'Item_StickBag_Medium'),
                               ('D', 'Item_Scale_Silver>Item_Scale_Gold')])
        others = set(build_mod.FAMILY_ALIASES) == {'Item_BulletBag_Small', 'Item_Quiver_Small'}
    except SystemExit:
        others = False
    good &= check('  the small seed bag and quiver still stand for the slingshot and the bow; other bags pass', others)
    print('\n'.join(said))

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
