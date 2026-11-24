"""An item's poses: where its model sits, from its animation project (skeletal animations, Model/<project>.anim.bfres)
and its model (Model/<project>.<model>.bfres).

Found in the game's files (2026-11-17, 2026-11-18):
- Items show themselves through animations of their bone `Skl_Root`: the shared `Item_Common_Animation` (the spins
  `Rotate_Obj`, `Rotate_GetDemo`, `Rotate_Stoped`) and each item's own project, whose poses set the size, turn and
  place of `Skl_Root`.
- Which pose is used is in `AS/Item_Common.root.asb`: each state names the poses it tries, in order (lists in its
  strings): on a shelf (`Rotate_Shop`, the shelf AI's idle) `Pose_Shop`, `Pose_Stoped`, `Pose_Common`,
  `Pose_GetDemo`; while the shop talk has it (`Rotate_Stoped`) `Pose_Stoped`, `Pose_Shop`, `Pose_Common`,
  `Pose_GetDemo`; held up (`Rotate_GetDemo`) `Pose_GetDemo`, `Pose_Common`; the state `Pouch`: `Pose_Pouch`,
  `Pose_GetDemo`, `Pose_Common`; anything else `Pose_Common`. (The spins work the same way: no project has a
  `Rotate_Shop`, its list goes on to `Rotate_GetDemo`.) No project has a `Pose_Stoped`.
- Six projects have a `Pose_Shop` (bomb, Deku Stick, Deku Seeds, arrow, arrow bundle, Hylian Shield): always their
  `Pose_Common` made smaller or larger (size and place times one number, the same turn), about 0.5 m tall. In
  `Pose_Common` an item stands on the point it is placed at (lowest vertex -0.03 .. +0.03 from it in every
  `Pose_Shop` and in the `Pose_Common` of the shields, bomb, stick, seeds, nut, arrows, Goron Tunic and heart); in
  `Pose_GetDemo` it is centred on it. Items the game never puts on the ground or a shelf have only a centred
  `Pose_Common` (Giant's Knife, Hover Boots, Hookshot).
- File layout used here. Animations (FSKA sections): name at +8, bone animations at +0x28, bone count at +0x4c; a
  bone animation is 0x38 bytes: name, curves, base values, flags at +0x28. Base values: scale (3 floats), rotation
  (3 angles and a 1), translation (3 floats), each only when its flag 0x8 / 0x10 / 0x20 is set. Flags 0x1000000:
  one scale for all axes, with 0x2000000: scale one (the stored scale not used); 0x4000000: no rotation;
  0x8000000: no translation. Models: skeleton (FSKL: bones at +0x10, matrix-to-bone list at +0x18, counts at
  +0x38; a bone is 0x58 bytes: name, parent at +0x22, scale / rotation / translation at +0x30 / +0x3c / +0x4c),
  shapes (FSHP, 0x60 bytes: vertices at +0x10, bone at +0x54, bones per vertex at +0x5a) and vertices (FVTX:
  attributes at +8, strides at +0x38, place in the buffer at +0x48, counts at +0x4c; the buffer starts at the
  address in the block the header names at +0xb0).
- Angles turn about X first, then Y, then Z (checked: with that order every ground pose stands on its point, and
  the Giant's Knife's box in `ActorInfo` is exactly its vertices in `Pose_Common`). A pose replaces the bone's
  place in the model (its bind pose), it is not added to it: a vertex in the model is first taken back into the
  bone, then posed. `ActorInfo`'s `ModelAabbMin` / `ModelAabbMax` is not used here: for some models it is the
  model as built, for others the model already posed.

- Where a held-up item is: the get scene (`Event/EventFlow/Dm_SY_GetInEvent`, entry `Item_Position`) shows it with
  `EventIgnitionShowItem`, `ItemPos` (0, 0, 0), `Rotate_GetDemo`: at a point the game's code works out, no file has
  it (`GameParameter/GetDemoParam` is empty). The point follows Link's age: where an item is shown to someone
  (`ShowItem`) the offsets from it for child and adult Link, taken from the raised hand (bone `Weapon_L` in
  `Evt_ShowItem`, `Evt_ShowItem_Failure`), put it 0.60 m higher for adult Link, and his raised hand in the get pose
  (`Demo_Get_Child_Loop`, `Demo_Get_Adult_Loop`) is 0.59 m higher (1.17 and 1.76 m): the same height above the
  hand at both ages. What an item has within 0.2 m of the upright line through the point is what sits over the
  hand: the Kokiri Sword, Hookshot and Poacher's Saw reach 0.25 under the point there.

A shelf copy of a project (`shelf_copy`): a game project that has exactly `Pose_Common`, `Pose_GetDemo` and
`Pose_Shop` for the bones `Root` and `Skl_Root`, with its name changed to one of the same length and the three
poses' values of `Skl_Root` set. Nothing else in the file moves.
"""
import math
import struct

POSE, BONE, ROOT = 'Pose_Common', 'Skl_Root', 'Root'
SHELF_POSES = ('Pose_Common', 'Pose_GetDemo', 'Pose_Shop')
UNIFORM, VOLUME_ONE, NO_ROTATION, NO_TRANSLATION = 0x1000000, 0x2000000, 0x4000000, 0x8000000
SCALE_ONE = UNIFORM | VOLUME_ONE
HAS_ALL = 0x38                                # scale, rotation and translation are all stored
STILL = 0x0f000000 | HAS_ALL                  # a bone left where it is: scale one, no rotation, no translation


def model_path(project):
    return 'Model/%s.anim.bfres' % project


def _str_at(data, off):
    n = struct.unpack_from('<H', data, off)[0]
    return data[off + 2:off + 2 + n].decode('ascii')


def animations(data):
    """{animation name: {bone name: offset of its bone animation}}, in the order of the file's list of skeletal
    animations (FSKA_LIST)"""
    out = {}
    for i in fska_list(data):
        bones = struct.unpack_from('<Q', data, i + 0x28)[0]
        out[_str_at(data, struct.unpack_from('<Q', data, i + 8)[0])] = {
            _str_at(data, struct.unpack_from('<Q', data, bones + 0x38 * b)[0]): bones + 0x38 * b
            for b in range(struct.unpack_from('<H', data, i + 0x4c)[0])}
    return out


# the file header's list of skeletal animations: where it is, where its dictionary is, how many (u16)
FSKA_LIST, FSKA_DIC, FSKA_COUNT, FSKA_SIZE = 0x58, 0x60, 0xe2, 0x50


def fska_list(data):
    """the offsets of the skeletal animations (FSKA) of an animation file, as its header lists them"""
    at, n = struct.unpack_from('<Q', data, FSKA_LIST)[0], struct.unpack_from('<H', data, FSKA_COUNT)[0]
    out = [at + FSKA_SIZE * k for k in range(n)]
    if any(data[i:i + 4] != b'FSKA' for i in out):
        raise SystemExit('animation file: its list of skeletal animations is not where its header says')
    return out


def read_pose(data, anim=POSE, bone=BONE):
    """{'scale' (x, y, z), 'rot' (x, y, z radians), 'move' (x, y, z), 'flags', 'at': offset of the bone animation,
    'base': offset of its base values, 'curves': offset of its curves or 0}: the values the game uses (a flag that
    says "one" or "none" wins over what is stored)"""
    anims = animations(data)
    if anim not in anims or bone not in anims[anim]:
        raise SystemExit('animation %s with a bone %s not found' % (anim, bone))
    o = anims[anim][bone]
    _, curves, p = struct.unpack_from('<QQQ', data, o)
    flags = struct.unpack_from('<I', data, o + 0x28)[0]
    pose = {'flags': flags, 'at': o, 'base': p, 'curves': curves, 'scale': (1.0, 1.0, 1.0), 'rot': (0.0, 0.0, 0.0),
            'move': (0.0, 0.0, 0.0)}
    if flags & 8:
        if flags & SCALE_ONE != SCALE_ONE:
            pose['scale'] = struct.unpack_from('<3f', data, p)
        p += 12
    if flags & 0x10:
        if not flags & NO_ROTATION:
            pose['rot'] = struct.unpack_from('<3f', data, p)
        p += 16
    if flags & 0x20 and not flags & NO_TRANSLATION:
        pose['move'] = struct.unpack_from('<3f', data, p)
    return pose


# --- where a pose puts the model -------------------------------------------------------------------------------------
def _matrix(scale, rot, move):
    """(3x3, translation): size, then turn about X, Y, Z in that order, then place"""
    cx, sx, cy, sy, cz, sz = (f(a) for a in rot[:3] for f in (math.cos, math.sin))
    r = ((cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz),
         (cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz),
         (-sy, sx * cy, cx * cy))
    return tuple(tuple(r[i][j] * scale[j] for j in range(3)) for i in range(3)), tuple(move)


def _apply(m, v):
    a, t = m
    return tuple(a[i][0] * v[0] + a[i][1] * v[1] + a[i][2] * v[2] + t[i] for i in range(3))


def _mul(m, n):
    (a, _), (b, u) = m, n
    return (tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3)),
            _apply(m, u))


def _inverse(m):
    ((a, b, c), (d, e, f), (g, h, i)), t = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    inv = (((e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det),
           ((f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det),
           ((d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det))
    return inv, tuple(-sum(inv[r][k] * t[k] for k in range(3)) for r in range(3))


def model_points(data, bone=BONE):
    """(every vertex of a model in the model's own space, the place of `bone` in the model, the bones' names)"""
    sk = data.find(b'FSKL')
    if sk < 0 or struct.unpack_from('<I', data, sk + 4)[0] & 0x3000 != 0x1000:
        raise SystemExit('model: no skeleton with angles (X, Y, Z)')
    bones, to_bone = struct.unpack_from('<QQ', data, sk + 0x10)
    n, smooth, rigid = struct.unpack_from('<3H', data, sk + 0x38)
    names, world = [], []
    for b in range(n):
        o = bones + 0x58 * b
        names.append(_str_at(data, struct.unpack_from('<Q', data, o)[0]))
        parent = struct.unpack_from('<h', data, o + 0x22)[0]
        local = _matrix(struct.unpack_from('<3f', data, o + 0x30), struct.unpack_from('<3f', data, o + 0x3c),
                        struct.unpack_from('<3f', data, o + 0x4c))
        if parent >= b:
            raise SystemExit('model: bone %s comes before its parent' % names[-1])
        world.append(local if parent < 0 else _mul(world[parent], local))
    if bone not in names:
        raise SystemExit('model: no bone %s' % bone)
    table = struct.unpack_from('<%dH' % (smooth + rigid), data, to_bone)
    pool = struct.unpack_from('<Q', data, struct.unpack_from('<Q', data, 0xb0)[0] + 8)[0]
    fm = data.find(b'FMDL')
    shapes = struct.unpack_from('<Q', data, fm + 0x28)[0]
    points = []
    for s in range(struct.unpack_from('<H', data, fm + 0x6a)[0]):
        o = shapes + 0x60 * s
        vtx = struct.unpack_from('<Q', data, o + 0x10)[0]
        if data[o:o + 4] != b'FSHP' or data[vtx:vtx + 4] != b'FVTX':
            raise SystemExit('model: shape %d not understood' % s)
        shape_bone, per_vertex = struct.unpack_from('<H', data, o + 0x54)[0], data[o + 0x5a]
        attrs, strides = (struct.unpack_from('<Q', data, vtx + k)[0] for k in (8, 0x38))
        at, count, n_vtx = struct.unpack_from('<IB3xI', data, vtx + 0x48)
        attr = {}
        for a in range(count):
            q = attrs + 0x10 * a
            attr[_str_at(data, struct.unpack_from('<Q', data, q)[0])] = (
                data[q + 8:q + 10].hex(), struct.unpack_from('<H', data, q + 0xc)[0],
                struct.unpack_from('<H', data, q + 0xe)[0])
        fmt, off, buf = attr['_p0']
        # positions: three floats (0518) or four half floats (0515), in the shape's first buffer; a vertex on one
        # bone names it with a byte (0302, 030b)
        if fmt not in ('0518', '0515') or buf != 0:
            raise SystemExit('model: vertices of shape %d not understood (%s)' % (s, fmt))
        if per_vertex == 1 and (attr['_i0'][0] not in ('0302', '030b') or attr['_i0'][2] != 0):
            raise SystemExit('model: vertices of shape %d not understood (%s)' % (s, attr['_i0'][0]))
        stride = struct.unpack_from('<I', data, strides)[0]
        for v in range(n_vtx):
            p = pool + at + stride * v
            pos = struct.unpack_from('<3e' if fmt == '0515' else '<3f', data, p + off)
            if per_vertex == 0:                        # the whole shape hangs on one bone: vertices in that bone
                pos = _apply(world[shape_bone], pos)
            elif per_vertex == 1:                      # each vertex on one bone
                pos = _apply(world[table[data[p + attr['_i0'][1]]]], pos)
            points.append(pos)                         # more bones per vertex: already in the model's space
    if not points:
        raise SystemExit('model: no vertices')
    return points, world[names.index(bone)], names


def extent(points, bind, scale, rot, move):
    """((lowest x, y, z), (highest x, y, z)) of a model whose bone at `bind` is posed (the other bones as built)"""
    m = _mul(_matrix(scale, rot, move), _inverse(bind))
    posed = [_apply(m, p) for p in points]
    return tuple(min(p[i] for p in posed) for i in range(3)), tuple(max(p[i] for p in posed) for i in range(3))


# --- a shelf copy --------------------------------------------------------------------------------------------------
def _still(data, pose, what):
    """the rest of a bone animation (not its name, base values, flags); it must be a still pose: every value
    stored, no curves"""
    o = pose['at']
    if pose['curves'] or pose['flags'] & 0xffff != HAS_ALL:
        raise SystemExit('%s: not a still pose with all its values stored' % what)
    return data[o + 0x18:o + 0x28] + data[o + 0x2c:o + 0x38]


def shelf_copy(base, base_project, new_project, item_anim, shop, held_lower=0.0):
    """`base` (the file of the game project `base_project`: exactly SHELF_POSES for Root and Skl_Root) renamed
    `new_project` (same length), with Pose_Common and Pose_GetDemo the Pose_Common of the item's own project
    (`item_anim`, its file) and Pose_Shop = `shop`: (scale, one for all axes; rot (x, y, z); move (x, y, z)).
    `held_lower`: Pose_GetDemo is placed that much lower (metres) than the item's Pose_Common; its size and turn
    stay."""
    if len(new_project) != len(base_project):
        raise SystemExit('%s and %s differ in length' % (base_project, new_project))
    raw = (base_project + '.anim').encode('ascii')
    pat = struct.pack('<H', len(raw)) + raw + b'\0'
    k = base.find(pat)
    if k < 0 or base.count(base_project.encode('ascii')) != 1:
        raise SystemExit('%s: its name is not in the file once' % base_project)
    theirs, mine = animations(base), animations(item_anim)
    if sorted(theirs) != sorted(SHELF_POSES) or any(sorted(b) != [ROOT, BONE] for b in theirs.values()):
        raise SystemExit('%s: not exactly %s for the bones %s and %s' % (base_project, SHELF_POSES, ROOT, BONE))
    if sorted(mine.get(POSE, ())) != [ROOT, BONE]:
        # the copy would leave the item's other bones unposed
        raise SystemExit('the item\'s %s does not pose exactly %s and %s' % (POSE, ROOT, BONE))
    src = read_pose(item_anim)
    shape = _still(item_anim, src, 'the item\'s ' + POSE)
    if read_pose(item_anim, bone=ROOT)['flags'] != STILL:
        raise SystemExit('the item\'s %s moves %s' % (POSE, ROOT))
    scale, rot, move = shop
    values = {p: (item_anim[src['base']:src['base'] + 40], src['flags']) for p in SHELF_POSES[:2]}
    held = struct.unpack('<3f', struct.pack('<3f', src['move'][0], src['move'][1] - held_lower, src['move'][2]))
    if held_lower:
        # the base values are scale (12 bytes), rotation (16), translation (12): only the translation changes
        values[SHELF_POSES[1]] = (values[SHELF_POSES[1]][0][:28] + struct.pack('<3f', *held),
                                  src['flags'] & ~NO_TRANSLATION)
    flags = (src['flags'] & ~(VOLUME_ONE | NO_TRANSLATION | NO_ROTATION)) | UNIFORM
    values[SHELF_POSES[2]] = (struct.pack('<3f4f3f', scale, scale, scale, rot[0], rot[1], rot[2], 1.0, *move),
                              flags | (0 if any(rot) else NO_ROTATION))
    out = bytearray(base)
    out[k + 2:k + 2 + len(raw)] = (new_project + '.anim').encode('ascii')
    allowed = set(range(k + 2, k + 2 + len(raw)))
    for p in SHELF_POSES:
        dst = read_pose(base, p)
        if _still(base, dst, '%s %s' % (base_project, p)) != shape or read_pose(base, p, ROOT)['flags'] != STILL:
            raise SystemExit('%s %s: not laid out like the item\'s %s' % (base_project, p, POSE))
        out[dst['base']:dst['base'] + 40] = values[p][0]
        struct.pack_into('<I', out, dst['at'] + 0x28, values[p][1])
        allowed |= set(range(dst['base'], dst['base'] + 40)) | set(range(dst['at'] + 0x28, dst['at'] + 0x2c))
    out = bytes(out)
    # read-back: only the name and the three poses' values changed, and they read as intended
    if len(out) != len(base) or not {i for i in range(len(base)) if out[i] != base[i]} <= allowed:
        raise SystemExit('%s: more than the name and the poses changed' % new_project)
    for p in SHELF_POSES[:2]:
        back = read_pose(out, p)
        lowered = bool(held_lower) and p == SHELF_POSES[1]
        if any(back[f] != src[f] for f in ('scale', 'rot')) or back['move'] != (held if lowered else src['move']) \
                or back['flags'] != (src['flags'] & ~NO_TRANSLATION if lowered else src['flags']):
            raise SystemExit('read-back: %s %s is not the item\'s %s' % (new_project, p, POSE))
    back = read_pose(out, SHELF_POSES[2])
    want = struct.unpack('<9f', struct.pack('<9f', scale, scale, scale, *rot, *move))
    if back['scale'] + back['rot'] + back['move'] != want or sorted(animations(out)) != sorted(SHELF_POSES):
        raise SystemExit('read-back: %s %s' % (new_project, SHELF_POSES[2]))
    return out


# --- a whole skeleton posed (2026-11-22) ---------------------------------------------------------------------------
# Items whose model hangs on many bones (the slingshot, bow, gauntlets, hookshot, first bomb bag) are measured with
# every bone posed. Found in the game's files: their skeletons use Maya's scale mode (FSKL flags 0x200) and nearly
# every bone below Skl_Root has "segment scale compensate" (bone flag SSC): the parent's size is undone before the
# bone's own turn and size, so a child sized 1.4 of a bone sized 1.4 is 1.4 in all, not 1.96 (without it the
# gauntlets' pose puts them 2.3 m under the ground; with it they fit in a box of 0.44 m). A bone's place: parent's
# place * its place * (1 / parent's size, with SSC) * its turn * its size. A vertex on one bone (or a whole shape on
# its bone) is stored in that bone; a vertex on several bones (up to eight: _i0/_w0, _i1/_w1) is stored in the model
# and moves with each bone, by its weight, from the bone's built place to its posed place. Checked: with no pose
# this gives exactly the box of ActorInfo for all seven models (with the shapes their visibility shows).
SSC = 0x800000
_INDEX = {'0302': 1, '0309': 2, '030b': 4}           # bone index formats: one, two, four bytes
_WEIGHT = {'0102': 1, '0109': 2, '010b': 4}           # weights: one, two or four bytes, 0..255


def skeleton(data):
    """([{'name', 'parent', 'flags', 'scale', 'rot', 'move'}] in the skeleton's order, the matrix-to-bone list) of a
    model"""
    sk = data.find(b'FSKL')
    mode = struct.unpack_from('<I', data, sk + 4)[0] & 0x3300 if sk >= 0 else None
    if mode not in (0x1100, 0x1200):
        raise SystemExit("model: no skeleton with angles (X, Y, Z) and the standard or Maya's scale mode")
    bones, to_bone = struct.unpack_from('<QQ', data, sk + 0x10)
    n, smooth, rigid = struct.unpack_from('<3H', data, sk + 0x38)
    out = []
    for b in range(n):
        o = bones + 0x58 * b
        out.append({'name': _str_at(data, struct.unpack_from('<Q', data, o)[0]),
                    'parent': struct.unpack_from('<h', data, o + 0x22)[0],
                    'flags': struct.unpack_from('<I', data, o + 0x2c)[0],
                    'scale': struct.unpack_from('<3f', data, o + 0x30), 'rot': struct.unpack_from('<3f', data, o + 0x3c),
                    'move': struct.unpack_from('<3f', data, o + 0x4c)})
        if out[-1]['parent'] >= b:
            raise SystemExit('model: bone %s comes before its parent' % out[-1]['name'])
        if mode != 0x1200 and out[-1]['flags'] & SSC:
            raise SystemExit("model: bone %s undoes its parent's size outside Maya's scale mode" % out[-1]['name'])
    return out, struct.unpack_from('<%dH' % (smooth + rigid), data, to_bone)


def _places(bones, local):
    """every bone's place in the model; local[b] = (scale, rot, move, segment scale compensate)"""
    one = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    out = []
    for b, bone in enumerate(bones):
        scale, rot, move, ssc = local[b]
        m = _matrix(scale, rot, move)
        if ssc and bone['parent'] >= 0:
            ps = local[bone['parent']][0]
            undo = (((1 / ps[0], 0.0, 0.0), (0.0, 1 / ps[1], 0.0), (0.0, 0.0, 1 / ps[2])), (0.0, 0.0, 0.0))
            m = _mul(_mul((one, tuple(move)), undo), _matrix(scale, rot, (0.0, 0.0, 0.0)))
        out.append(m if bone['parent'] < 0 else _mul(out[bone['parent']], m))
    return out


def posed_points(model, anim=None, pose=POSE, height=None, hidden=()):
    """(every vertex of a model with its whole skeleton posed by `pose` of the animation project `anim` (its file;
    None: the model as built), the names of the bones vertices hang on). Bones the pose does not name stay as
    built; `height`: the height of Skl_Root instead of the pose's own (None: the pose's). Shapes on a bone named in
    `hidden` are left out. Only still poses (no curves)."""
    bones, table = skeleton(model)
    names = [b['name'] for b in bones]
    built = _places(bones, [(b['scale'], b['rot'], b['move'], b['flags'] & SSC) for b in bones])
    named = animations(anim).get(pose) if anim is not None else {}
    if named is None:
        raise SystemExit('animation %s not found' % pose)
    local = []
    for b in bones:
        if b['name'] not in named:
            local.append((b['scale'], b['rot'], b['move'], b['flags'] & SSC))
            continue
        p = read_pose(anim, pose, b['name'])
        if p['curves']:
            raise SystemExit('%s: bone %s is not still' % (pose, b['name']))
        move = p['move'] if height is None or b['name'] != BONE else (p['move'][0], height, p['move'][2])
        local.append((p['scale'], p['rot'], move, p['flags'] & SSC))
    places = _places(bones, local)
    skin = [_mul(places[i], _inverse(built[i])) for i in range(len(bones))]
    pool = struct.unpack_from('<Q', model, struct.unpack_from('<Q', model, 0xb0)[0] + 8)[0]
    fm = model.find(b'FMDL')
    shapes = struct.unpack_from('<Q', model, fm + 0x28)[0]
    points, used = [], set()
    for s in range(struct.unpack_from('<H', model, fm + 0x6a)[0]):
        o = shapes + 0x60 * s
        vtx = struct.unpack_from('<Q', model, o + 0x10)[0]
        if model[o:o + 4] != b'FSHP' or model[vtx:vtx + 4] != b'FVTX':
            raise SystemExit('model: shape %d not understood' % s)
        shape_bone, per_vertex = struct.unpack_from('<H', model, o + 0x54)[0], model[o + 0x5a]
        if names[shape_bone] in hidden:
            continue
        attrs, strides = (struct.unpack_from('<Q', model, vtx + k)[0] for k in (8, 0x38))
        at, count, n_vtx = struct.unpack_from('<IB3xI', model, vtx + 0x48)
        attr = {}
        for a in range(count):
            q = attrs + 0x10 * a
            attr[_str_at(model, struct.unpack_from('<Q', model, q)[0])] = (
                model[q + 8:q + 10].hex(), struct.unpack_from('<H', model, q + 0xc)[0],
                struct.unpack_from('<H', model, q + 0xe)[0])
        fmt, off, buf = attr['_p0']
        sets = [k for k in '01' if '_i' + k in attr]
        ok = fmt in ('0518', '0515') and buf == 0 and all(attr['_i' + k][0] in _INDEX and attr['_i' + k][2] == 0
                                                          for k in sets)
        if per_vertex > 1:
            ok = ok and all(attr.get('_w' + k, ('', 0, 1))[0] in _WEIGHT and attr['_w' + k][2] == 0 for k in sets)
        if not ok or (per_vertex and per_vertex > sum(_INDEX[attr['_i' + k][0]] for k in sets)):
            raise SystemExit('model: vertices of shape %d not understood' % s)
        stride = struct.unpack_from('<I', model, strides)[0]
        for v in range(n_vtx):
            p = pool + at + stride * v
            pos = struct.unpack_from('<3e' if fmt == '0515' else '<3f', model, p + off)
            if per_vertex == 0:                        # the whole shape on its bone, stored in it
                used.add(shape_bone)
                points.append(_apply(places[shape_bone], pos))
                continue
            idx, wts = [], []
            for k in sets:
                f, io, _ = attr['_i' + k]
                idx += list(model[p + io:p + io + _INDEX[f]])
                if per_vertex > 1:
                    f, wo, _ = attr['_w' + k]
                    wts += [x / 255.0 for x in model[p + wo:p + wo + _WEIGHT[f]]]
            if per_vertex == 1:                        # on one bone, stored in it
                used.add(table[idx[0]])
                points.append(_apply(places[table[idx[0]]], pos))
                continue
            acc = [0.0, 0.0, 0.0]                      # on several: stored in the model
            for i, w in zip(idx[:per_vertex], wts[:per_vertex]):
                if w:
                    used.add(table[i])
                    q = _apply(skin[table[i]], pos)
                    acc = [acc[c] + w * q[c] for c in range(3)]
            points.append(tuple(acc))
    if not points:
        raise SystemExit('model: no vertices')
    return points, sorted({names[u] for u in used}, key=names.index)


def under(model, name, top=BONE):
    """whether bone `name` of a model is `top` or below it"""
    bones, _ = skeleton(model)
    names = [b['name'] for b in bones]
    i = names.index(name)
    while i >= 0 and names[i] != top:
        i = bones[i]['parent']
    return i >= 0


def bone_visibility(data, name):
    """{bone: shown (True / False), or None where a curve changes it} of the bone visibility animation `name`
    (FBVS: name at +8, curves at +0x28, the shown bits at +0x30, bone names at +0x38, counts at +0x58) of an
    animation file"""
    i = data.find(b'FBVS')
    while i >= 0:
        if _str_at(data, struct.unpack_from('<Q', data, i + 8)[0]) == name:
            n, n_curves = struct.unpack_from('<2H', data, i + 0x58)
            curves, bits, names = struct.unpack_from('<3Q', data, i + 0x28)
            shown = int.from_bytes(data[bits:bits + (n + 7) // 8], 'little')
            out = {_str_at(data, struct.unpack_from('<Q', data, names + 8 * k)[0]): bool(shown >> k & 1)
                   for k in range(n)}
            keys = list(out)
            for c in range(n_curves):                  # a curve (0x30 bytes) names its bone at +0x14
                out[keys[struct.unpack_from('<I', data, curves + 0x30 * c + 0x14)[0]]] = None
            return out
        i = data.find(b'FBVS', i + 1)
    raise SystemExit('bone visibility animation %s not found' % name)


# --- one skeletal animation more (2026-11-22) ------------------------------------------------------------------------
# The file layout (the game's animation files, all alike): the header lists the skeletal animations (FSKA_LIST,
# FSKA_DIC, FSKA_COUNT), has at +0x18 the offset of the relocation table (_RLT, at the end of the file) and at +0x1c
# the file's size. The relocation table lists every place in the file that holds an offset (made an address when
# the file is loaded): '_RLT', its own offset, the number of sections, then the sections (0x18 bytes: offset, size,
# first entry, number of entries; only the first holds anything) and the entries (8 bytes: offset, number of
# structs, offsets per struct, 8-byte words skipped after them). A dictionary (the names of a list, found by a radix
# tree over their bits) is 8 bytes (0, count) and count + 1 nodes of 16 bytes (bit, left, right, offset of the
# name), the first node with no name; formats/evfl.py builds the same tree for event flows, and it gives back the
# game's dictionaries of these files exactly. An animation's name, path and bone list are offsets: two animations
# may share them.

def relocations(data):
    """(offset of the relocation table, its sections [(offset, size, first entry, entries)], its entries
    [(offset, structs, offsets per struct, words skipped)], every place listed)"""
    r = struct.unpack_from('<I', data, 0x18)[0]
    if data[r:r + 4] != b'_RLT' or struct.unpack_from('<I', data, r + 4)[0] != r:
        raise SystemExit('animation file: no relocation table where its header says')
    n = struct.unpack_from('<I', data, r + 8)[0]
    sections = [struct.unpack_from('<8xIIII', data, r + 0x10 + 0x18 * k) for k in range(n)]
    first = r + 0x10 + 0x18 * n
    entries = [struct.unpack_from('<IHBB', data, first + 8 * k) for k in range(sum(s[3] for s in sections))]
    places = [o + s * (k + skip) * 8 + 8 * j for o, structs, k, skip in entries for s in range(structs)
              for j in range(k)]
    if first + 8 * len(entries) != len(data) or struct.unpack_from('<I', data, 0x1c)[0] != len(data):
        raise SystemExit('animation file: its relocation table does not end the file')
    return r, sections, entries, places


def dict_names(data, at):
    """the names of a dictionary, in order"""
    n = struct.unpack_from('<I', data, at + 4)[0]
    return [_str_at(data, struct.unpack_from('<Q', data, at + 8 + 16 * k + 8)[0]) for k in range(1, n + 1)]


def dict_find(data, at, name):
    """the index of `name` in a dictionary, found the way the game finds it (down its radix tree), or None"""
    raw = name.encode('ascii')

    def node(k):
        ref, left, right, key = struct.unpack_from('<iHHQ', data, at + 8 + 16 * k)
        return ref, left, right, key

    prev, k = node(0), node(0)[1]
    while prev[0] < node(k)[0]:
        prev = node(k)
        ref = prev[0]
        bit = raw[len(raw) - 1 - (ref >> 3)] >> (ref & 7) & 1 if ref >> 3 < len(raw) else 0
        k = prev[2] if bit else prev[1]
    return k - 1 if k and _str_at(data, node(k)[3]) == name else None


def _base_size(flags):
    return 12 * bool(flags & 8) + 16 * bool(flags & 0x10) + 12 * bool(flags & 0x20)


def add_pose_copy(data, src=POSE, new='Pose_GetDemo'):
    """the animation file `data` with one skeletal animation more, `new`: a copy of the still pose `src` with
    values of its own (so `src` can be changed and `new` stays the game's). Nothing in the file moves: the new
    parts are put between the strings and the relocation table, with a new list of the skeletal animations (the
    old ones, then the new one) and its dictionary; the header then names those, and the relocation table lists
    the offsets in them too. Everything else, the old list and dictionary too, stays where and what it was."""
    from formats.evfl import _dic_tree
    r, sections, entries, places = relocations(data)
    listed = set(places)
    if r % 8 or sections[0][0] != 0 or sections[0][2] != 0 or any(s[1] or s[3] for s in sections[1:]):
        raise SystemExit('animation file: relocation sections not as expected')
    old = fska_list(data)
    dic = struct.unpack_from('<Q', data, FSKA_DIC)[0]
    names = [_str_at(data, struct.unpack_from('<Q', data, i + 8)[0]) for i in old]
    if dict_names(data, dic) != names or src not in names or new in names \
            or [struct.unpack_from('<IHH', data, dic + 8 + 16 * k) for k in range(len(names) + 1)] \
            != [tuple(n[:3]) for n in _dic_tree(names)]:
        raise SystemExit('animation file: its animations are not %s, with a %s, no %s and the usual dictionary'
                         % (names, src, new))
    head = old[names.index(src)]
    bind, bones = struct.unpack_from('<QQ', data, head + 0x20)
    n_bones = struct.unpack_from('<H', data, head + 0x4c)[0]
    block, more = bytearray(), []                 # the new parts (at r), the places in them that hold offsets

    def put(raw):
        while len(block) % 8:
            block.append(0)
        at = r + len(block)
        block.extend(raw)
        return at

    def copy_struct(at, size):
        """a struct copied as it is, its offsets listed as the original's are"""
        to = put(data[at:at + size])
        more.extend(to + p - at for p in sorted(listed) if at <= p < at + size)
        return to

    raw = new.encode('ascii')
    name_at = put(struct.pack('<H', len(raw)) + raw + b'\0')
    bases = []
    for b in range(n_bones):
        o = bones + 0x38 * b
        curves, base = struct.unpack_from('<QQ', data, o + 8)
        if curves:
            raise SystemExit('%s: not a still pose' % src)
        bases.append(put(data[base:base + _base_size(struct.unpack_from('<I', data, o + 0x28)[0])]))
    bind_at = put(data[bind:bind + 2 * n_bones])
    bones_at = None
    for b in range(n_bones):
        to = copy_struct(bones + 0x38 * b, 0x38)
        bones_at = bones_at or to
        block[to - r + 0x10:to - r + 0x18] = struct.pack('<Q', bases[b])
    list_at = to = None
    for i in old + [head]:
        to = copy_struct(i, FSKA_SIZE)
        list_at = list_at or to
    block[to - r + 8:to - r + 0x10] = struct.pack('<Q', name_at)
    block[to - r + 0x20:to - r + 0x30] = struct.pack('<QQ', bind_at, bones_at)
    keys = [struct.unpack_from('<Q', data, i + 8)[0] for i in old] + [name_at]
    dic_at = put(data[dic:dic + 4] + struct.pack('<I', len(names) + 1))
    root_key = struct.unpack_from('<Q', data, dic + 0x10)[0]
    for k, (ref, left, right, _) in enumerate(_dic_tree(names + [new])):
        at = put(struct.pack('<IHHQ', ref, left, right, root_key if k == 0 else keys[k - 1]))
        more.append(at + 8)
    while len(block) % 8:
        block.append(0)
    # the relocation table: the new places as runs of offsets one after another, after the old entries
    runs = []
    for p in sorted(more):
        if runs and runs[-1][0] + 8 * runs[-1][1] == p and runs[-1][1] < 255:
            runs[-1][1] += 1
        else:
            runs.append([p, 1])
    new_r = r + len(block)
    entries2 = entries + [(p, 1, k, 0) for p, k in runs]
    rlt = bytearray(data[r:r + 0x10])
    struct.pack_into('<I', rlt, 4, new_r)
    for k in range(len(sections)):
        values = (0, new_r, 0, len(entries2)) if k == 0 else (new_r, 0, len(entries2), 0)
        rlt += data[r + 0x10 + 0x18 * k:r + 0x18 + 0x18 * k] + struct.pack('<IIII', *values)
    for e in entries2:
        rlt += struct.pack('<IHBB', *e)
    out = bytearray(data[:r] + bytes(block) + bytes(rlt))
    struct.pack_into('<II', out, 0x18, new_r, len(out))
    struct.pack_into('<QQ', out, FSKA_LIST, list_at, dic_at)
    struct.pack_into('<H', out, FSKA_COUNT, len(names) + 1)
    out = bytes(out)
    # read back: the old bytes unchanged but the header's values; every old place still listed, the new ones too,
    # each holding an offset into the file or none; the animations found by name as the game finds them; the new
    # one has the old one's values, bone for bone, in places of its own; every other animation as it was
    head_spots = set(range(0x18, 0x20)) | set(range(FSKA_LIST, FSKA_LIST + 16)) | {FSKA_COUNT, FSKA_COUNT + 1}
    _, _, _, back = relocations(out)
    if [i for i in range(r) if out[i] != data[i] and i not in head_spots] or sorted(back) != sorted(places + more) \
            or any(struct.unpack_from('<Q', out, p)[0] >= len(out) for p in more):
        raise SystemExit('read-back: %s with %s added' % (names, new))
    if dict_names(out, dic_at) != names + [new] \
            or [dict_find(out, dic_at, x) for x in names + [new]] != list(range(len(names) + 1)) \
            or dict_find(out, dic_at, new + '_') is not None:
        raise SystemExit('read-back: the dictionary of %s with %s added' % (names, new))
    mine, theirs = animations(out), animations(data)
    if list(mine) != names + [new] or list(mine[new]) != list(theirs[src]) \
            or any(list(mine[a]) != list(theirs[a]) for a in names):
        raise SystemExit('read-back: animations of %s with %s added' % (names, new))
    for a, b in [(new, src)] + [(x, x) for x in names]:
        for bone in theirs[b]:
            p, q = read_pose(out, a, bone), read_pose(data, b, bone)
            if any(p[f] != q[f] for f in ('scale', 'rot', 'move', 'flags', 'curves')) or (a != b and p['base'] < r):
                raise SystemExit('read-back: %s bone %s' % (a, bone))
    return out
