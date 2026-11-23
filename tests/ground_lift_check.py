"""Ground lift test: every item in ground_items.GROUND_LIFT gets a lifted copy of its animation project that puts
its lowest vertex 0.05 above the ground and leaves it held up as the game shows it, on the game's own files; the
items the game never gives are refused. Reads only; writes nothing.

    python tests/ground_lift_check.py "C:\\...\\romfs"
"""
import hashlib
import json
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
# vertices on more bones than Skl_Root (the compass's needle; the first bomb bag was this one until 2026-11-22)
NOT_LIFTED = ('Item_Boomerang', 'TBox_ArrowBundle_Large', 'Item_Dungeon_Compass')
# the seven whose ground pose places many bones (2026-11-22): {item: (its project, how many bones the pose places,
# lowest vertex in the game's pose with the spin, measured with every bone posed)}. Their copy is their own project
# with Pose_GetDemo added (a copy of the game's Pose_Common) and the height of Skl_Root changed in Pose_Common
MANY = {'Item_Range_SlingShot': ('Weapon_Range_SlingShot_Animation', 19, -0.1485),
        'Item_Range_Bow': ('Weapon_Range_Bow_Animation', 10, -0.3779),
        'Item_Gauntlet_Silver': ('Armor_Adult_Gauntlet_Silver_Animation', 77, -0.1625),
        'Item_Gauntlet_Gold': ('Armor_Adult_Gauntlet_Gold_Animation', 73, -0.1626),
        'Item_BombBag_Small': ('Item_BombBag_Small_Animation', 5, -0.1427),
        'Item_Hookshot': ('Item_Hookshot_Animation', 19, -0.2004),
        'Item_Longshot': ('Item_Hookshot_Animation', 19, -0.2004)}
# their copies, as first made: {copy: checksum}
MANY_COPIES = {
    'NX2Gnd_Range_SlingShot_Animation': 'af3c4c621bd64ebfa9f3f1ac50f1616f21b05f0cae0e7324cfcc5b8adb5e62e9',
    'NX2Gnd_Range_Bow_Animation': 'ab38045c6f341aefc7140d76580b62ffe1842c596057e41fbf754dfcb210ef3d',
    'NX2GA_Adult_Gauntlet_Silver_Animation': 'b0b906184b78b7ea4fd29b260ddddbce02a85e6ab142bd80eb1f66c8dd3b09ae',
    'NX2GA_Adult_Gauntlet_Gold_Animation': 'fb9e79f5a566171fc6d33384a95eef12d9f5f3411fb69f58bbe1a2cf8b8a5947',
    'NX2G_BombBag_Small_Animation': '3ff2c34632fe4649ed4bd7cdf1f8299ebf3cbc6d4ad855dff2d471ce9cf8e405',
    'NX2G_Hookshot_Animation': 'd5d25a50521d96bf0b521dc78cdd0f65f2d9ae04d4983d1c6fad21cb28ab0b96'}
# every other item, every version (ground, token, turn, held), as ground_items.build made them before 2026-11-22
# (taken with the builder of main 68e5e89): how many built or stopped, and one checksum over them all (see
# fingerprint below). Only the seven's ground, token and turn versions differ
OTHERS = (1559, '9be0344f9860c6e77b56e0511249f836cd330cebc30e3e116d2dff450c7ff555')
# the Fire Arrow's copy (also the Ice Arrow's) as it was before the Light Arrow got a copy of its own of the same
# project (2026-11-20): its name and checksum, and the checksums of the four packs that name it
ARROW_COPY = ('NX2G_Arrow_Fire_Animation', '882e3ca4009701ff166c7fa06a43bcd906ea49792c672ae9422b4c84f3f212d7')
ARROW_PACKS = {('Item_Arrow_Fire', 'ground'): '710d4ee27bd1b9e89414cec59b673e10bcc33d75e4f1287d25edc81abe2bf9f9',
               ('Item_Arrow_Fire', 'token'): 'ac4defb0535c9620520e0abb7f8a8e865e28746eed1a08de27654465ff9e3e1b',
               ('Item_Arrow_Ice', 'ground'): '21621bdc06aa8284074b4b624409612a59b9dfcf404d7e206345489b803d44f9',
               ('Item_Arrow_Ice', 'token'): 'dba673b0ec61389b72705fbb6b5174af918eb95620c9b9bed4b94708e97db66a'}
LIGHT, LIGHT_LIKE = 'Item_Arrow_Light', 'Item_Arrow_Fire'
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


def fingerprint(item, plain, table_rows, has_model, version):
    """one line for a version as ground_items.build makes it: a checksum of the pack, the files new to the game, the
    table rows and the lifted copies, or why it stopped"""
    try:
        name, pack, new_inner, rows, loose = ground_items.build(item, plain, table_rows, has_model, version)
    except SystemExit as e:
        return 'EXIT ' + str(e)[:80]
    except Exception as e:                             # noqa: BLE001 (as when the checksum was taken)
        return 'ERR ' + repr(e)[:80]
    h = hashlib.sha256(pack)
    for p in sorted(new_inner):
        h.update(p.encode())
        h.update(new_inner[p])
    h.update(json.dumps(rows, sort_keys=True, default=str).encode())
    for p in sorted(loose):
        data, like, _, _, own = loose[p]
        for x in (p.encode(), data, like.encode(), own.encode()):
            h.update(x)
    return h.hexdigest() + ' ' + ','.join(sorted(loose))


def shown(read, item, model):
    """the bones whose shapes the game hides for an item: those its model hides, as its ModelInfo's variation
    animations change them (a bone a curve changes counts as shown)"""
    files = sarc.Sarc.read(read(ground_items.pack_path(item))).files
    info = byml.loads(files[ground_items._ref_path(
        ground_items.resolved_components(files, item)['ModelInfoRef'])]).root
    bones, _ = item_pose.skeleton(model)
    hidden = {b['name'] for b in bones if not b['flags'] & 1}
    for v in info.get('ModelVariationAnims') or []:
        parts = v['Fmab'].split('/')
        if not parts[-1].endswith('.fvbb'):
            continue
        for bone, on in item_pose.bone_visibility(read('Model/%s.anim.bfres' % parts[-3]),
                                                  parts[-1][:-len('.fvbb')]).items():
            if on is False:
                hidden.add(bone)
            else:
                hidden.discard(bone)
    return hidden


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
    tested, kinds = {}, {'own': set(), 'many': set(), 'jar': set()}
    many_seen = {}                                     # item -> (copy, game project, model, low, was)
    arrow_packs, light = {}, {}
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
            many = not own_held and ground_items.many_bones(game)
            kinds['own' if own_held else 'many' if many else 'jar'].add(own)
            lifted_name = ground_items.lifted_project(own, game, item)
            # the copy: a name new to the game, as long as the name of the game file it is made of
            names &= path == ground_items.model_path(lifted_name) and len(path) == len(like) \
                and lifted_name.startswith('NX2G') and not os.path.exists(os.path.join(romfs, *path.split('/')) + '.zs')
            # made of the item's own project when that has a held-up pose (only the name, a flag and the height
            # differ) or its pose places many bones, else of HELD_BASE (only the name and its two poses' values and
            # flags differ)
            bases &= like == (own_path if own_held or many else ground_items.model_path(ground_items.HELD_BASE)) \
                and own_held == (own in OWN_HELD) and many == (item in MANY)
            differ = [i for i in range(len(made_of)) if i >= len(x) or x[i] != made_of[i]]
            if own_held:
                only &= len(x) == len(made_of) and len(differ) <= 12 \
                    and item_pose.animations(x).keys() == item_pose.animations(game).keys()
            elif many:
                # the game file's bytes up to its relocation table: only the name, Skl_Root's flag and height in
                # the ground pose, and the header's values for the list of animations, the table and the size;
                # one animation more, Pose_GetDemo
                r = item_pose.relocations(made_of)[0]
                at = item_pose.read_pose(made_of, ground_items.GROUND_POSE)
                k = made_of.find(own.encode())
                spots = set(range(k, k + len(own))) | set(range(at['at'] + 0x28, at['at'] + 0x2c)) \
                    | set(range(at['base'] + 32, at['base'] + 36)) | set(range(0x18, 0x20)) \
                    | set(range(item_pose.FSKA_LIST, item_pose.FSKA_LIST + 16)) \
                    | {item_pose.FSKA_COUNT, item_pose.FSKA_COUNT + 1}
                only &= len(x) > len(made_of) and {i for i in differ if i < r} <= spots \
                    and list(item_pose.animations(x)) == list(item_pose.animations(game)) + [ground_items.HELD_POSE]
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
            fields = ('scale', 'rot', 'move', 'flags', 'curves')
            if many:
                # every bone, held up: the game's ground pose; lying: the same but Skl_Root's height
                for bone in item_pose.animations(game)[ground_items.GROUND_POSE]:
                    was = item_pose.read_pose(game, ground_items.GROUND_POSE, bone)
                    helds &= all(item_pose.read_pose(x, ground_items.HELD_POSE, bone)[f] == was[f] for f in fields)
                    poses &= bone == item_pose.BONE or all(
                        item_pose.read_pose(x, ground_items.GROUND_POSE, bone)[f] == was[f] for f in fields)
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
            # where the item lies with it, by its own model's vertices (on many bones: every bone posed)
            measure = ground_items.skeleton_low if many else ground_items.vertex_low
            low = measure(x, model, None) + spin
            was = measure(game, model, None) + spin
            if many:
                many_seen[item] = (x, game, model, low, was)
            if item in box:
                lows &= low > gap - 1e-5                # as tested in game (the bracelet 0.074)
            elif item in shared:
                lows &= abs(low - gap) <= ground_items.GROUND_SHARED
            else:
                lows &= abs(low - gap) < 1e-5
            lows &= abs(was - gap) > ground_items.GROUND_NEAR
            # the measure is sure: every vertex hangs on Skl_Root (on many bones: on Skl_Root or below it)
            if many:
                sure &= all(item_pose.under(model, b) for b in item_pose.posed_points(model)[1])
            else:
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
                # the game file's headroom (a copy with one animation more is larger by what it adds)
                e = out.table.get(like)
                entries &= out.table.get(path) == max(e - len(made_of) + len(x),
                                                      e - sizes.size32(len(made_of)) + sizes.size32(len(x))) \
                    and (need is None or out.table.get(path) >= need)
            if (item, version) in ARROW_PACKS:
                arrow_packs[item, version] = (hashlib.sha256(pack).hexdigest(), path, hashlib.sha256(x).hexdigest())
            if item == LIGHT:
                light[version] = (path, x, game, low, was, model)
            if version == 'token':
                said.append('  %-30s height %+.4f -> %+.4f (%+.3f), lowest vertex %+.4f -> %+.4f  %s' % (
                    item, old_h, new_h, new_h - old_h, was, low,
                    'on the copy of ' + shared[item] if item in shared else 'by the box' if item in box
                    else 'on a copy of its own' if item in ground_items.GROUND_LIFT_OWN
                    else 'every bone posed' if many else ''))
        built &= versions > 0
    good &= check('every listed item (%d) builds in at least one version, each with one lifted copy' % len(lift),
                  built and one)
    good &= check('the copy\'s name starts with NX2G, is as long as the game file\'s it is made of, new to the game',
                  names)
    good &= check('made of the item\'s own project when it has a %s (%d) or places many bones (%d), else of %s (%d)'
                  % (ground_items.HELD_POSE, len(kinds['own']), len(kinds['many']), ground_items.HELD_BASE,
                     len(kinds['jar'])),
                  bases and kinds['own'] == set(OWN_HELD) and kinds['many'] == {v[0] for v in MANY.values()}
                  and len(kinds['jar']) > 0)
    good &= check('only the name and the poses\' values differ from that file (on many bones: and %s added); the '
                  'ground pose only in its height' % ground_items.HELD_POSE, only and poses)
    good &= check('held up (%s): size, turn and place exactly the game\'s, for every copy (on many bones: every '
                  'bone)' % ground_items.HELD_POSE, helds)
    good &= check('lowest vertex %.2f above the ground (shared copies: within %.2f); it was more than %.2f off'
                  % (gap, ground_items.GROUND_SHARED, ground_items.GROUND_NEAR), lows)
    good &= check('every vertex of every listed model hangs on %s (on many bones: on it or below it)'
                  % item_pose.BONE, sure)
    good &= check('the pack and the table row name the copy', packs)
    good &= check('one copy for a project (%d copies), the same bytes whichever item or version is built'
                  % len(copies), same)
    good &= check('each copy\'s size entry is the game file\'s (same length; on many bones: with its headroom) and '
                  'meets the rules', entries)
    good &= check('the ground pose of the copies seen right in game is as then (bracelet, magic, both scales)',
                  sorted(tested) == sorted(TESTED) and all(tested.values()))
    for item, first in sorted(shared.items()):
        good &= check('  %s lies on the copy of %s' % (item, first),
                      ground_items.own_projects(plain, item) == ground_items.own_projects(plain, first))
    # the Light Arrow: on the Fire Arrow's project, with a copy of its own under another name
    own_names = ground_items.GROUND_LIFT_OWN
    fire_path = ground_items.model_path(ARROW_COPY[0])
    light_path = ground_items.model_path(own_names[LIGHT])
    project = LIGHT_LIKE + '_Animation'
    good &= check('the Light Arrow (%s) uses the Fire Arrow\'s project and is the only item with a copy of its own'
                  % LIGHT, list(own_names) == [LIGHT] and LIGHT in lift and LIGHT not in shared and LIGHT not in box
                  and ground_items.own_projects(plain, LIGHT) == ground_items.own_projects(plain, LIGHT_LIKE)
                  == [project])
    good &= check('  its copy (%s): a name as long as the project\'s, no other copy\'s, new to the game'
                  % own_names[LIGHT],
                  len(own_names[LIGHT]) == len(project) and light_path != fire_path
                  and sorted(light) == sorted(VERSIONS) and {v[0] for v in light.values()} == {light_path}
                  and copies[light_path][2] == LIGHT and copies[fire_path][2] == LIGHT_LIKE
                  and len({c.lower() for c in copies}) == len(copies) and not has_model(own_names[LIGHT]))
    _, x, game, low, was, model = light['ground']
    on_fire = ground_items.vertex_low(copies[fire_path][0], model, None) + spin
    good &= check('  it lies %.2f above the ground on it (%+.4f; on the game\'s file %+.4f, on the Fire Arrow\'s '
                  'copy %+.4f)' % (gap, low, was, on_fire),
                  abs(low - gap) < 1e-5 and abs(was - gap) > 0.1 and abs(on_fire - gap) > 0.1)
    # held up: every byte but the name and the ground pose's flag and height of Skl_Root is the game's, so the
    # whole Pose_GetDemo is (both bones: values, flags and where they are)
    at = item_pose.read_pose(game, ground_items.GROUND_POSE)
    k = game.find(project.encode())
    spots = set(range(k, k + len(project))) | set(range(at['base'], at['base'] + 40)) \
        | set(range(at['at'] + 0x28, at['at'] + 0x2c))
    good &= check('  held up: its %s is the game\'s, byte for byte (only the name and the ground pose differ)'
                  % ground_items.HELD_POSE,
                  len(x) == len(game) and {i for i in range(len(game)) if x[i] != game[i]} <= spots
                  and all(item_pose.read_pose(x, ground_items.HELD_POSE, b) == item_pose.read_pose(
                      game, ground_items.HELD_POSE, b) for b in (item_pose.ROOT, item_pose.BONE))
                  and item_pose.read_pose(x, ground_items.HELD_POSE)['move']
                  != item_pose.read_pose(x, ground_items.GROUND_POSE)['move'])
    good &= check('  the Fire and Ice Arrows are as before: the same copy (%s) and the same packs, byte for byte'
                  % ARROW_COPY[0],
                  hashlib.sha256(copies[fire_path][0]).hexdigest() == ARROW_COPY[1]
                  and sorted(arrow_packs) == sorted(ARROW_PACKS)
                  and all(arrow_packs[k] == (ARROW_PACKS[k], fire_path, ARROW_COPY[1]) for k in ARROW_PACKS))
    none = True
    for item in NOT_LIFTED:
        for version in ('ground', 'token'):
            none &= not ground_items.build(item, plain, table_rows, has_model, version)[4]
    good &= check('items not listed get no copy (%s)' % ', '.join(NOT_LIFTED), none)

    # the seven whose ground pose places many bones (2026-11-22)
    good &= check('the seven on many bones are listed (%s); the Longshot lies on the Hookshot\'s copy'
                  % ', '.join(MANY), set(MANY) <= set(lift) and sorted(many_seen) == sorted(MANY)
                  and shared.get('Item_Longshot') == 'Item_Hookshot' and not set(MANY) & set(box))
    bones_ok = read_ok = shown_ok = low_ok = dic_ok = True
    lines = []
    for item, (project, n_bones, want) in sorted(MANY.items()):
        x, game, model, low, was = many_seen[item]
        row = info[item]
        pose = item_pose.animations(game)[ground_items.GROUND_POSE]
        bones_ok &= ground_items.own_projects(plain, item) == [project] and len(pose) == n_bones \
            and not ground_items.has_held_pose(game) and ground_items.many_bones(game)
        # the model read right: as built, the shapes the game shows fit exactly the box of ActorInfo
        hidden = shown(plain, item, model)
        built_pts = item_pose.posed_points(model, hidden=hidden)[0]
        box_min, box_max = row['ModelAabbMin'], row['ModelAabbMax']
        read_ok &= all(abs(min(q[i] for q in built_pts) - box_min[a]) < 1e-4
                       and abs(max(q[i] for q in built_pts) - box_max[a]) < 1e-4 for i, a in enumerate('XYZ'))
        # posed: the hidden shapes never lie lower than the shown ones, so counting them all is exact
        shown_low = min(q[1] for q in item_pose.posed_points(model, game, hidden=hidden)[0]) + spin
        shown_ok &= abs(shown_low - was) < 1e-6
        low_ok &= abs(was - want) < 5e-5 and abs(low - gap) < 1e-5
        # the game finds every animation of the copy by name, and the relocation table lists the new offsets
        r, _, _, old_places = item_pose.relocations(game)
        new_r, _, _, places = item_pose.relocations(x)
        dic = struct.unpack_from('<Q', x, item_pose.FSKA_DIC)[0]
        anims = list(item_pose.animations(x))
        dic_ok &= [item_pose.dict_find(x, dic, a) for a in anims] == list(range(len(anims))) \
            and set(old_places) <= set(places) and all(r <= p < new_r for p in set(places) - set(old_places)) \
            and item_pose.dict_find(x, dic, 'Pose_GetDemo_') is None
        lines.append('  %-22s %2d bones, %d of %d shapes\' bones hidden; lowest vertex %+.4f -> %+.4f'
                     % (item, n_bones, len(hidden), len(item_pose.skeleton(model)[0]), was, low))
    good &= check('  their projects place many bones in %s and have no %s of their own'
                  % (ground_items.GROUND_POSE, ground_items.HELD_POSE), bones_ok)
    good &= check('  their models are read right: as built, the shapes the game shows fit the box of ActorInfo', read_ok)
    good &= check('  posed, the shapes the game hides never lie lower than those it shows (every vertex counts)',
                  shown_ok)
    good &= check('  lowest vertex in the game\'s pose as measured (%s), %.2f above the ground on the copy'
                  % (', '.join('%+.3f' % v[2] for v in MANY.values()), gap), low_ok)
    good &= check('  every animation of a copy is found by name; the relocation table lists the new offsets', dic_ok)
    many_copies = {c[len('Model/'):-len('.anim.bfres')]: hashlib.sha256(d).hexdigest()
                   for c, (d, _, i) in copies.items() if i in MANY}
    good &= check('  their copies (%d), byte for byte as first made' % len(MANY_COPIES), many_copies == MANY_COPIES)
    # the new measure gives every other listed item measured by its vertices the lowest vertex it had
    agree = True
    for item in lift:
        own = ground_items.own_projects(plain, item)
        if item in MANY or item in box or not own:
            continue
        game = plain(ground_items.model_path(own[0]))
        model = plain('Model/%s.%s.bfres' % (info[item]['ModelProjectName'], info[item]['FmdbName']))
        agree &= abs(min(q[1] for q in item_pose.posed_points(model, game, height=0.0)[0])
                     - ground_items.vertex_low(game, model)) < 1e-6
    good &= check('  measured that way, every other listed item lies where its vertices on %s say' % item_pose.BONE,
                  agree)
    # nothing else changes: every other item, every version, as before
    rows_cache = {}

    def cached_rows(t):
        if t not in rows_cache:
            rows_cache[t] = table_rows(t)
        return rows_cache[t]

    others = {}                                        # 'item|version' -> fingerprint
    for item in sorted(r['__RowId'] for r in cached_rows('PouchActorInfo')):
        for version in ('ground', 'token', 'turn', 'held'):
            if item in MANY and version != 'held':
                continue
            others['%s|%s' % (item, version)] = fingerprint(item, plain, cached_rows, has_model, version)
    digest = hashlib.sha256(''.join('%s=%s\n' % (k, others[k]) for k in sorted(others)).encode()).hexdigest()
    good &= check('  every other item\'s versions (%d: the seven held up too) are built as before, byte for byte'
                  % len(others), (len(others), digest) == OTHERS)
    print('\n'.join(lines))

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
