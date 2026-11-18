"""Sheik's harp with a cloth colour per song (songs as items show the harp, tools/build_mod.py).

Found in the game's files:
- The harp model `Model/Item_Harp_Sheik.Item_Harp_Sheik.bfres` (model project and model both Item_Harp_Sheik) has
  one material, Mt_Harp_Sheik, whose colour texture is `Tex/Mt_Harp_Sheik_Item_Harp_Sheik_Alb.bntx`: BC1 (sRGB),
  768 x 768, 10 mip levels, one texture for the gold frame and the cloth.
- The cloth is navy: the end colours of its BC1 blocks have hues of 210-240 degrees (saturated); the frame's are
  30-90 degrees, a few grey parts are unsaturated.

A colour = one model variant + one texture copy, as the game itself does for variants of a model (same project,
model of its own: file Model/<project>.<model>.bfres):
- the model file copied with three names changed to names of the same length (so nothing else in the file moves):
  the model `Item_Harp_Sheik` -> `Item_HrpX_Sheik`, the file `Item_Harp_Sheik.Item_Harp_Sheik` ->
  `Item_Harp_Sheik.Item_HrpX_Sheik`, the colour texture `..._Item_Harp_Sheik_Alb` -> `..._Item_HrpX_Sheik_Alb`
  (X: one letter per song). The other textures stay the original harp's.
- the colour texture copied with its name changed the same way, and its cloth recoloured: every 8-byte BC1 block
  stores two end colours (RGB565) and 2-bit indices; an end colour in the navy range takes the song's hue and
  saturation, its brightness scaled from the navy's to the song colour's. The block order on the Switch (swizzled)
  doesn't matter: each block is changed on its own. When the change flips which end colour is larger (that decides
  the block's mode in BC1), the two are swapped and the indices remapped, so the block decodes the same way.
- names are found in the files' string tables (a 2-byte length, the text, a 0); both files look names up in a
  dictionary (a Patricia tree on the names' bits): the new name is looked up after the change to check it is found.
The idea (variant per colour, recolouring BC1 end colours) is the user's own, from their earlier project.

Held up, the harp didn't spin and sat low, into Link's head (seen in game, 2026-11-17). Found in the game's files:
- The items Link holds up spin through their animation settings: the actor's components `ASInfoRef`
  (`Item_GetDemo`), `ASRef` (`AS/Item_Common.root.asb`, which plays the command `Rotate_GetDemo`) and
  `AnimationRef` (the animation projects, `Item_Common_Animation` first). The songs (`Item_Melody_*`) have none
  of the three: a song held up from a chest stood still.
- `Rotate_GetDemo` (`Model/Item_Common_Animation.anim.bfres`, skeletal animation) turns the bone `Root` once
  around and lifts the bone `Skl_Root` by 0.18 above the hand point. Item models are centred on their origin
  (the bottle is 0.18 tall), so the lift puts them just above the hands. The harp is 0.50 tall (its bones `Root`
  and `Skl_Root` too, so the animation works on it): lifted by 0.18 its lower 0.07 would still be below the
  hand point. Its `Rotate_Obj` and `Rotate_Stoped` (on the ground, still) lift by the same 0.18.
- So the songs get the three components, with an animation project of their own: a copy of
  `Item_Common_Animation` named `Item_HarpNX_Animation` (same length), whose three lifts are 0.31 instead of 0.18
  (the harp's lower edge then as far above the hand point as a bottle's). Nothing else of the animation changes.
"""
import colorsys
import struct

PROJECT = 'Item_Harp_Sheik'
MODEL = 'Model/Item_Harp_Sheik.Item_Harp_Sheik.bfres'
ALB_NAME = 'Mt_Harp_Sheik_Item_Harp_Sheik_Alb'
ALB = 'Tex/%s.bntx' % ALB_NAME
NAVY_HUE = (190 / 360, 275 / 360)      # the cloth's end colours (hue range, saturation from NAVY_SAT)
NAVY_SAT = 0.25


def variant_name(tag):
    """the model name of colour `tag` (one letter), as long as the original"""
    return 'Item_Hrp%s_Sheik' % tag


def model_path(tag):
    return 'Model/%s.%s.bfres' % (PROJECT, variant_name(tag))


def alb_name(tag):
    return 'Mt_Harp_Sheik_%s_Alb' % variant_name(tag)


def alb_path(tag):
    return 'Tex/%s.bntx' % alb_name(tag)


# ------------------------------------------------------------------ names in NintendoWare files
def _string_entry(data, text):
    """offset of the string-table entry holding exactly `text` (2-byte length, text, 0); must be unique"""
    raw = text.encode('ascii')
    pat = struct.pack('<H', len(raw)) + raw + b'\0'
    i = data.find(pat)
    if i < 0 or data.find(pat, i + 1) >= 0:
        raise SystemExit('harp: name %r found %s times' % (text, 0 if i < 0 else 'several'))
    return i


def rename(data, old, new):
    """`old` -> `new` (same length) in the string table; returns the new data"""
    if len(old) != len(new):
        raise SystemExit('harp: %r and %r differ in length' % (old, new))
    out = bytearray(data)
    i = _string_entry(data, old)
    out[i + 2:i + 2 + len(new)] = new.encode('ascii')
    return bytes(out)


def _bit(key, n):
    """bit n of a dictionary key: counted from the last byte's lowest bit"""
    byte = n >> 3
    return 0 if byte >= len(key) else (key[len(key) - 1 - byte] >> (n & 7)) & 1


def dict_find(data, dict_off, key):
    """index of `key` in the NintendoWare dictionary at dict_off ('_DIC'), or None"""
    count = struct.unpack_from('<I', data, dict_off + 4)[0]
    nodes = [struct.unpack_from('<iHHQ', data, dict_off + 8 + 16 * k) for k in range(count + 1)]

    def name(k):
        off = nodes[k][3]
        n = struct.unpack_from('<H', data, off)[0]
        return data[off + 2:off + 2 + n]
    parent, node = 0, nodes[0][1]
    while nodes[parent][0] < nodes[node][0]:
        parent = node
        node = nodes[node][2] if _bit(key, nodes[node][0]) else nodes[node][1]
    return node if node and name(node) == key else None


def model_variant(data, tag):
    """the harp model file with its model, file and colour texture names changed for colour `tag`"""
    new = rename(data, PROJECT, variant_name(tag))
    new = rename(new, '%s.%s' % (PROJECT, PROJECT), '%s.%s' % (PROJECT, variant_name(tag)))
    new = rename(new, ALB_NAME, alb_name(tag))
    if len(new) != len(data) or sum(a != b for a, b in zip(new, data)) > 9:
        raise SystemExit('harp model: more than the three names changed')   # 'Harp' -> 'HrpX': 3 letters each
    model_dict = struct.unpack_from('<Q', new, 0x30)[0]       # the file's model dictionary
    if dict_find(new, model_dict, variant_name(tag).encode()) is None:
        raise SystemExit('harp model: %s not found in its model dictionary after the change' % variant_name(tag))
    return new


# ------------------------------------------------------------------ the texture
def _from565(v):
    return ((v >> 11) & 31) / 31, ((v >> 5) & 63) / 63, (v & 31) / 31


def _to565(r, g, b):
    q = lambda x, m: max(0, min(m, int(round(x * m))))  # noqa: E731
    return (q(r, 31) << 11) | (q(g, 63) << 5) | q(b, 31)


def _is_cloth(rgb):
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    return NAVY_HUE[0] <= h <= NAVY_HUE[1] and s >= NAVY_SAT and v > 0.02


def _data_block(data):
    """(start, end) of the texture data (BRTD block) of a one-texture BNTX file"""
    i = data.find(b'BRTD')
    if i < 0 or data.find(b'BRTD', i + 1) >= 0:
        raise SystemExit('harp texture: not one BRTD block')
    size = struct.unpack_from('<Q', data, i + 8)[0]
    return i + 16, i + size


def _navy_value(data, start, end):
    """the brightness of the cloth's end colours: (average, 99th percentile)"""
    vs = []
    for k in range(start, end - 7, 8):
        for c in struct.unpack_from('<HH', data, k):
            rgb = _from565(c)
            if _is_cloth(rgb):
                vs.append(colorsys.rgb_to_hsv(*rgb)[2])
    if not vs:
        raise SystemExit('harp texture: no navy cloth found')
    vs.sort()
    return sum(vs) / len(vs), vs[len(vs) * 99 // 100]


def recolor(data, color):
    """the harp's colour texture (BNTX) with the cloth in `color` (r, g, b 0-255); returns (new data, blocks changed)"""
    start, end = _data_block(data)
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in color))
    # the cloth's average takes the colour's brightness; a light colour (the white) is darkened just enough that
    # the cloth's lighter parts keep their shading (the 99th percentile stays at most full brightness)
    avg, high = _navy_value(data, start, end)
    scale = min(tv / avg, 1.0 / high)
    out = bytearray(data)
    changed = 0
    for k in range(start, end - 7, 8):
        c0, c1, idx = struct.unpack_from('<HHI', data, k)
        new = []
        for c in (c0, c1):
            rgb = _from565(c)
            if _is_cloth(rgb):
                v = colorsys.rgb_to_hsv(*rgb)[2]
                new.append(_to565(*colorsys.hsv_to_rgb(th, ts, min(1.0, v * scale))))
            else:
                new.append(c)
        n0, n1 = new
        if (n0, n1) == (c0, c1):
            continue
        four = c0 > c1                        # BC1: c0 > c1 -> 4 colours, else 3 colours + transparent
        if four and n0 <= n1:
            if n0 == n1:
                n0 = min(0xFFFF, n0 + 1) if n0 < 0xFFFF else n0
                if n0 == n1:
                    n1 -= 1
            else:                             # swap: index 0<->1, 2<->3
                n0, n1 = n1, n0
                idx = sum(([1, 0, 3, 2][(idx >> (2 * p)) & 3]) << (2 * p) for p in range(16))
        elif not four and n0 > n1:            # swap: index 0<->1 (2 is the middle, 3 transparent)
            n0, n1 = n1, n0
            idx = sum(([1, 0, 2, 3][(idx >> (2 * p)) & 3]) << (2 * p) for p in range(16))
        struct.pack_into('<HHI', out, k, n0, n1, idx)
        changed += 1
    return bytes(out), changed


def texture_variant(data, tag, color):
    """the harp's colour texture renamed for colour `tag`, its cloth recoloured; returns (data, blocks changed)"""
    new, changed = recolor(data, color)
    new = rename(new, ALB_NAME, alb_name(tag))
    dics = [i for i in range(0, len(new) - 3, 4) if new[i:i + 4] == b'_DIC']
    if len(dics) != 1 or dict_find(new, dics[0], alb_name(tag).encode()) is None:
        raise SystemExit('harp texture: %s not found in its dictionary after the change' % alb_name(tag))
    return new, changed


# the cloth colours, taken from the song icons of the songbook (a screenshot from the user, 2026-11-17: the
# average of each icon's most coloured pixels; sRGB 0-255), one letter each (the variant names). The six songs
# with white icons share the white harp; the six warp songs have their icon's colour.
COLORS = {
    'W': (244, 240, 214),    # white (cream) icons: Zelda's Lullaby, Epona, Saria, Sun, Time, Storms
    'G': (107, 177, 83),     # Minuet of Forest
    'R': (204, 82, 74),      # Bolero of Fire
    'B': (89, 122, 222),     # Serenade of Water
    'O': (205, 129, 60),     # Requiem of Spirit
    'P': (139, 92, 229),     # Nocturne of Shadow
    'Y': (214, 205, 91),     # Prelude of Light
}
SONG_COLORS = {
    'Item_Melody_ZeldaLullaby': 'W', 'Item_Melody_EponaSong': 'W', 'Item_Melody_SariaSong': 'W',
    'Item_Melody_SunSong': 'W', 'Item_Melody_TimeSong': 'W', 'Item_Melody_StormSong': 'W',
    'Item_Melody_ForestMinuet': 'G', 'Item_Melody_FireBolero': 'R', 'Item_Melody_WaterSerenade': 'B',
    'Item_Melody_SpiritRequiem': 'O', 'Item_Melody_ShadowNocturne': 'P', 'Item_Melody_LightPrelude': 'Y',
}


# ------------------------------------------------------------------ held up: spin and height
# 2026-11-18: with the harp's own copy of the spin animation (HARP_ANIM_PROJECT, below) the game crashed three times
# creating the songs (Kokiri Forest loading after the first cutscene: a write through a null pointer, before the
# harp model or that copy was asked for), whatever else was tried (the rows' animation list and heaps, a resting
# pose); without the spin it did not crash. The songs now list the game's own Item_Common_Animation, unchanged and
# alone (SPIN_PROJECTS): the spin and the game's lift (GAME_LIFT), nothing renamed and no new animation file.
# The copy with the higher lift (animation_copy) is not used.
SPIN = True
ANIM_PROJECT = 'Item_Common_Animation'
SPIN_PROJECTS = (ANIM_PROJECT,)
ANIM = 'Model/%s.anim.bfres' % ANIM_PROJECT
HARP_ANIM_PROJECT = 'Item_HarpNX_Animation'          # as long as the original (not used: see above)
HARP_ANIM = 'Model/%s.anim.bfres' % HARP_ANIM_PROJECT
LIFT_BONE = 'Skl_Root'
GAME_LIFT, HARP_LIFT = 0.18, 0.31
LIFTED = ('Rotate_GetDemo', 'Rotate_Obj', 'Rotate_Stoped')
# the songs' new components (what the Boomerang, an item that is held up, has; AnimationRef: the songs' own file)
AS_INFO = 'Component/ASInfo/Item_GetDemo.engine__component__ASInfo.bgyml'
AS_REF = 'AS/Item_Common.root.asb'
ANIM_PARAM = 'Component/AnimationParam/Item_Melody_Harp.engine__component__AnimationParam.bgyml'
ANIM_PARAM_LIKE = 'Component/AnimationParam/Item_Boomerang.engine__component__AnimationParam.bgyml'


def _name_at(data, off):
    n = struct.unpack_from('<H', data, off)[0]
    return data[off + 2:off + 2 + n].decode('ascii')


def lift_points(data):
    """{animation name: offset of the Y lift of bone Skl_Root} in a skeletal animation file (FSKA sections: name
    at +8, bone animations at +0x28, bone count at +0x4c; a bone animation is 0x38 bytes: name, curves, base
    values (scale 3 floats, rotation 4, translation 3, each only when its flag 0x8 / 0x10 / 0x20 is set),
    flags at +0x28)"""
    points = {}
    i = 0
    while True:
        i = data.find(b'FSKA', i + 1)
        if i < 0:
            return points
        name = _name_at(data, struct.unpack_from('<Q', data, i + 8)[0])
        bones = struct.unpack_from('<Q', data, i + 0x28)[0]
        for b in range(struct.unpack_from('<H', data, i + 0x4c)[0]):
            o = bones + 0x38 * b
            bone, _, base = struct.unpack_from('<QQQ', data, o)
            flags = struct.unpack_from('<I', data, o + 0x28)[0]
            if _name_at(data, bone) != LIFT_BONE or not flags & 0x20:
                continue
            points[name] = base + (12 if flags & 8 else 0) + (16 if flags & 0x10 else 0) + 4


def animation_copy(data):
    """Item_Common_Animation as the harp's own animation project: renamed, the three lifts raised"""
    new = bytearray(rename(data, ANIM_PROJECT + '.anim', HARP_ANIM_PROJECT + '.anim'))
    points = lift_points(data)
    if set(points) != set(LIFTED):
        raise SystemExit('harp animation: lifts found in %s, expected %s' % (sorted(points), LIFTED))
    for name, off in points.items():
        y = struct.unpack_from('<f', data, off)[0]
        if abs(y - GAME_LIFT) > 1e-4:
            raise SystemExit('harp animation: %s lifts by %.4f, expected %.2f' % (name, y, GAME_LIFT))
        struct.pack_into('<f', new, off, HARP_LIFT)
    new = bytes(new)
    if len(new) != len(data) or sum(a != b for a, b in zip(new, data)) > 6 + 4 * len(LIFTED):
        raise SystemExit('harp animation: more than the name and the lifts changed')
    back = lift_points(new)
    if any(abs(struct.unpack_from('<f', new, back[n])[0] - HARP_LIFT) > 1e-6 for n in LIFTED):
        raise SystemExit('read-back: harp animation lifts')
    return new
