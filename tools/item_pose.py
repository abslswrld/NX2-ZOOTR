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
    """{animation name: {bone name: offset of its bone animation}}"""
    out, i = {}, data.find(b'FSKA')
    while i >= 0:
        bones = struct.unpack_from('<Q', data, i + 0x28)[0]
        out[_str_at(data, struct.unpack_from('<Q', data, i + 8)[0])] = {
            _str_at(data, struct.unpack_from('<Q', data, bones + 0x38 * b)[0]): bones + 0x38 * b
            for b in range(struct.unpack_from('<H', data, i + 0x4c)[0])}
        i = data.find(b'FSKA', i + 1)
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
