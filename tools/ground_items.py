"""Ground versions of items: an actor Link picks up from the ground (or from a pot), for items the game only
has as the model shown when an item is received.

Found in the game's files:
- `Item_<x>` actors (parent `Item_EventObject_Base`) are only the model held up when an item is received
  (chests, NPCs). They have no pick-up collision: placed on the ground, Link can't take them.
- Ground items are `Obj_` actors (parent `Obj_Item_Base`). Only 24 exist (rupees, hearts, ammunition, the
  Piece of Heart, small keys, shields...). `Obj_Shield_Deku`, the Deku Shield lying on the ground, is a
  single equipment item built as a thin wrapper around the item: its own pack holds the ground parts
  (`Obj_Item_Base`, a body that only touches the ground, a pick-up sensor: `DropItem` / `Item_Pouch_Tgt`,
  layer `SmallObject`), and the item's model, animation and item settings (`PouchContentParam`) are copies
  of the item's own files. Its table rows: `ActorInfo` with the item's model and
  `ActorName: Weapon_Shield_Deku` (what the game shows and stores), `GameActorInfo` (small object layer),
  `PouchActorInfo` (the item row).
- Not the ground Ocarina of Time (`Obj_Ocarina_Time`, castle moat; the first template, 2026-11-16): its
  physics is the generic solid box (`ObjectDefault` -> `Box`, layer `GroundObject`) with no pick-up sensor.
  Tested in game: Link bumps into an invisible box around the item (and climbs it), and can't take it.

A ground version of item X is built the same way, from the game's own files only: the ground shield's pack
with the shield's model, animation, item settings and shield-only settings (equipment table, hookshot hold
position, effect link) taken out and X's model, animation and item settings put in (with the files they
inherit from, when X's pack has them), an actor parameter file of its own, and the three table rows taken
from the shield's (ground parts) and X's (model, name, item row). The name is `Obj_NX2_<X without "Item_">`.

No glow and no effects: the shield's effect link (only its burning effect) is left out, and its row's
`ELinkUserName` removed. Its sound link stays.

Picked up by walking into it, without pressing A: `DefaultAutoGet` in an item's settings (`PouchContentParam`)
decides that. The Bottle's has it, as does the ground shield's (its own settings inherit from `AutoPickShield`);
the Boomerang's, Bomb Bag's, Fairy Ocarina's and Hookshot's don't, and in game (2026-11-16) those showed
"Take" (A). So the ground version gets item settings of its own, built like the ground shield's: the item's
settings as `$parent`, plus `DefaultAutoGet: true`. Only the ground version's pack has them; the item itself
(chests, NPCs) is unchanged.

What goes into the pouch: every game ground item that stands for another item names it in its item settings
(`PouchActor`: the ground shield `Weapon_Shield_Deku`, the ground bomb `Item_Bomb`, the Goron Tunic
`Armor_Adult_Goron`...). Without it the ground actor itself is added. The Fairy Ocarina's own settings have
none (the game never puts it on the ground): in game (2026-11-16) the ground ocarina went into the pouch but
could not be played until a reload. The ground version's settings name the item (`PouchActor`), as the game's
ground items do (to test).

Held-up versions (`Item_NX2_<x>`, to test): what a chest shows when it gives an item. The items that show
(Boomerang, Bottle...) are item event actors (parent `Item_EventObject_Base`) with the get-demo animation
settings (`ASInfo: Item_GetDemo`, `AS/Item_Common`, the `Item_Common_Animation` animations). The ocarinas'
actors are Link's playable instrument instead (equipment: no get-demo settings); a chest giving the Fairy
Ocarina showed nothing (2026-11-16), though the ocarina could be played. A held-up version is built the same
way as a ground version, from the Boomerang's item actor (`Item_Boomerang`) instead of the ground shield:
the Boomerang's own model, animation, item settings and boomerang settings out, the item's in, and item
settings of its own naming the item (`PouchActor`). Only for items that are not item event actors already.

Gold Skulltula drops (`Obj_NX2_GS_<x>`, to test): what a Gold Skulltula drops instead of its token. Found in
the game's files (2026-11-17): a Gold Skulltula is not marked done when it dies but when its token is picked
up, and it is the token that does it. The skulltula's own AI (`Enemy_Skulltula_Gold.utility.root`) hands its
drop the saved flag of its map placement (`QueryBlackboardOverwriteParamAddNoRespawnGmdHash`, key
`GoldTokenGmdHash`, through `OneShotDropSetOverWriteParam`); the token (`Obj_Token_Gold`) has that key in its
blackboard (`Item_Token_Gold` parameter table) and its own AI (`Item_Token_Gold.root`: when it dies of reason
10, picked up, it runs `OneShotGoldTokenDeadAfter`). Dying only sets the skulltula's unsaved flag
`IsGoldSkullDead.IsGoldSkullDead_<placement hash>` (gone until the area is left). Any other item dropped has
neither the key nor that AI, so the skulltula came back after a reload (seen in game). A Gold Skulltula drop
is therefore built from the token itself: the token's pack (its AI, blackboard, death settings, physics,
lock-on) with the token's name, model, animation and item settings out and the item's in; no effect link, the
base's lift settings (the token's name a bone of the token's model).

The spin of a Gold Skulltula drop (2026-11-17: the dropped Piece of Heart lay still). Every item on the ground
spins through its AI: the ground items' AI (`DropItem.root`, and the Piece of Heart's own `Obj_Heart_Piece.root`)
plays the animation command `Rotate_Obj` (`OneShotASPlay`) when nothing is playing, and their animation
settings (`ASInfo`: `Item_Obj`) start nothing by themselves (`AutoPlayASName` empty). The token's AI
(`Item_Token_Gold.root`) plays nothing: the token spins because its own animation settings (`ASInfo`:
`Obj_Token_Gold`) start `Rotate_Obj` by themselves (`AutoPlayASName`); they are `Item_Obj` in every other
value. A drop has the token's AI, so with the item's or the shield's `Item_Obj` nothing ever started the spin.
A drop therefore keeps the token's `ASInfo`, and takes only the animation file (`ASRef`) from the item when it
is a ground item whose file knows `Rotate_Obj` (Piece of Heart: `AS/Obj_Heart_Piece`), else from the ground
shield (`AS/Item_Common`); not the token's own file, whose spin uses an animation of the token's model
(`Rotate_Obj_St`, in `Obj_Token_Gold_Animation`). The `Rotate_Obj` animation itself is in
`Item_Common_Animation`, which the items' animation settings list.

How high an item lies on the ground (2026-11-17: the Goron Bracelet and the magic blessing dropped by rocks lay
half in the ground). Found in the game's files (skeletal animations, `Model/*.anim.bfres`): the spin `Rotate_Obj`
(`Item_Common_Animation`) lifts the bone `Root` by 0.05 and the bone `Skl_Root` by 0.18, but every item's own
animation project has a pose `Pose_Common` that sets `Skl_Root` (size, turn, height) and takes its place: items
made to lie on the ground lift themselves there (the Bottle by 0.114, the Deku Shield by 0.238; the Bottle's lowest
point is then 0.05 above the ground). The bracelet's pose lifts it by -0.01 (and makes it 2.1 times bigger), the
magic blessing's sets nothing (0): their models are centred on their origin, so half of each was below the ground.
Their ground versions (and Gold Skulltula drops) get a copy of the item's animation project, renamed (`Item` ->
`NX2G`, same length) with only the pose's height of `Skl_Root` changed, so the lowest point of the model (its box,
`ModelAabbMin/Max`, sized and turned by the pose) is 0.05 above the ground, as the Bottle's. Only the items seen
too low are listed (GROUND_LIFT); the item itself (chests, shelves) keeps the game's animation.

The Silver and Gold Scales (2026-11-19: both lay partly in the ground as turning items). Each has its own model and
animation project. Their models are built standing above their origin (vertices 0.038 .. 0.433 and 0.027 .. 0.433)
with `Skl_Root` at 0.2226; `Pose_Common` puts `Skl_Root` at -0.0074 instead (size one, no turn). A pose replaces
the bone's place in the model, so the pose centres the scale on its point: lowest vertex -0.192 (Silver), -0.203
(Gold). Their box in `ActorInfo` is the model as built (lowest 0.038, 0.027), not the model in the bone: from it
the scales would seem to stand above the ground already. So their lift is measured from the model's vertices and
skeleton (tools/item_pose.py): the vertices taken into the bone, sized and turned by the pose. The bracelet and
the magic blessing stay on the box (GROUND_LIFT_BOX), as tested in game: for the magic both ways give 0.285; the
bracelet's turned box is larger than the turned model (0.130; by its vertices 0.106), so it lies 0.074 above the
ground, not 0.05.

The other items (2026-11-19). Every item the builder can put on the ground was measured the same way. The items the
game itself puts on the ground or a shelf stand on their point (lowest vertex +0.02 .. +0.06, a few up to +0.11);
those it only ever shows held up have a pose centred on their point, and lie 0.07 .. 0.28 in the ground. Listed in
GROUND_LIFT are those whose measure is sure: every vertex of the model hangs on `Skl_Root` (the pose's other bones
carry none), and the lowest vertex is more than GROUND_NEAR from GROUND_GAP. An item that lies too high is lowered
the same way (the Fire and Ice Arrows, the single arrow).

Items that share one animation project (GROUND_LIFT_AS). A lifted copy is named after the project, so a project
has one copy, whichever item is built first: the copy is always measured on the one item named there, and the
others are checked against it with their own model (GROUND_SHARED: how far from GROUND_GAP they may lie). Din's
Fire, Farore's Wind and Nayru's Love are one model in one project. The two double blessings use the magic
blessing's project: its copy (measured on the box, as tested) puts them 0.0502 and 0.0505 above the ground. The
Ice Arrow uses the Fire Arrow's project: with the Fire Arrow's copy it lies 0.057 above the ground. The single
arrow uses the large bundle's project; the large bundle is not listed and keeps the game's file.

A copy of its own for an item on a shared project (GROUND_LIFT_OWN, 2026-11-20). The Light Arrow uses the Fire
Arrow's project too, but its model needs the bone at 0.377 where the Fire Arrow's needs 0.235: on the Fire Arrow's
copy it would lie 0.092 in the ground (on the game's file 0.057 in it). It gets a second copy of that project,
measured on its own model, under a name of its own of the same length (`NX2G_ArrowLight_Animation`); the Fire
Arrow's copy (`NX2G_Arrow_Fire_Animation`, also the Ice Arrow's) is not touched. The project has a `Pose_GetDemo`,
so the copy is the project itself with only the name and the ground pose's height changed: held up it is the
game's.

Held up (2026-11-19: Din's Fire picked up from the ground was held well above Link's hands). The item Link holds up
after a pick-up is the very actor he picked up (`Dm_SY_Get` plays the animation command `Rotate_GetDemo` on it), so
it uses the lifted copy too. In `AS/Item_Common.root.asb` that command shows the pose `Pose_GetDemo`, and
`Pose_Common` when the project has none; the spin on the ground (`Rotate_Obj`) shows `Pose_Common`. Of the listed
items only the Gold Skulltula token, the Fire Arrow (and Ice Arrow) and the single arrow have a `Pose_GetDemo`: for
the others the lifted `Pose_Common` was also the held-up pose. The game's own ground items that are held up have
both poses: 13 projects have exactly `Pose_Common` (standing on its point) and `Pose_GetDemo` (centred) for the
bones `Root` and `Skl_Root` (the magic jars, the Heart Container, the ground Goron Tunic, the masks). So the lifted
copy of a project without a `Pose_GetDemo` is made of one of those (HELD_BASE, the large magic jar's) instead of
the project itself, as the shop versions' shelf copies are (tools/item_pose.py, `shelf_copy`): `Pose_Common` is the
item's pose at the lifted height, `Pose_GetDemo` the item's own `Pose_Common` as the game has it. Its name is as
long as HELD_BASE's. A project that has a `Pose_GetDemo` is copied as before; held up it was the game's already.
Lost on the way: the `Pose_Pouch` of the quivers' and the hammer's projects (the pose of the state `Pouch`), which
HELD_BASE has not; the state then shows `Pose_GetDemo`, the game's `Pose_Common`. What goes into the inventory is
the item itself (`PouchActor`), with the game's project.

Items that inherit their item settings (2026-11-20: the medium and large bags, quivers and wallets had no ground
version, "no PouchContentRef"). An actor's parameters name the actor they inherit from (`$parent`), and a setting
the actor does not name itself is its parent's. The medium bomb bag's actor (`Item_BombBag_Medium`) names its own
name, model, animation, icon and count (`GameParameterTableRef`: `ExpansionMaxNumActor`, 30) and inherits from
`Item_BombBag_Small`, whose `PouchContentRef` (`Component/PouchContentParam/BombBag`) is therefore the medium
bag's too; the large bag inherits from the medium one. The parents' parameter files and those item settings are in
the item's own pack. The same for the Deku Stick, Deku Nut and Deku Seed bags, the quivers and the wallets (their
small ones name `KeyItemDefault`): 12 items. So an item actor's item settings (`PouchContentRef`,
INHERITED_REFS) are read as the game reads them: the actor's own, else those of the actors it inherits from
(`item_components`), down to but not the base of all item actors (ITEM_BASE: its item settings are `Default`, no
item's own). Only that one setting, and only for actors built on ITEM_BASE: the 12 items name their own name,
model and animation, and nothing that built before changes (masks, Poes and others that inherit in other ways
stay refused).
What the pick-up adds stays the item itself: the ground version's own settings name it (`PouchActor`), and its
count is in the item's own actor and table row, which the ground version does not touch.
"""
import copy
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml  # noqa: E402
import item_pose  # noqa: E402

TEMPLATE = 'Obj_Shield_Deku'
TEMPLATE_ITEM = 'Weapon_Shield_Deku'
PREFIX = 'Obj_NX2_'
# the components that make the item what it is; everything else comes from the ground shield
ITEM_REFS = ('ActorNameRef', 'AnimationRef', 'ModelInfoRef', 'PouchContentRef')
# the ground shield's own settings, left out (the item base's are used): price table (equipment), hookshot
# hold position, effect link
TEMPLATE_ONLY = ('GameParameterTableRef', 'LiftableRef', 'ELinkRef')
# of these, what an item may have from the actor it inherits from (the medium bag from the small one)
INHERITED_REFS = ('PouchContentRef',)
# the base of all item actors: its model (Dummy) and item settings (Default) are no item's own
ITEM_BASE = 'Item_EventObject_Base'
# kind of version -> (template actor, the item the template stands for, name prefix, template-only settings left
# out, picked up by walking into it, the template's own animation project)
VERSIONS = {
    'ground': (TEMPLATE, TEMPLATE_ITEM, PREFIX, TEMPLATE_ONLY, True, TEMPLATE_ITEM + '_Animation'),
    'held': ('Item_Boomerang', 'Item_Boomerang', 'Item_NX2_', ('GameParameterTableRef',), False,
             'Item_Boomerang_Animation'),
    # what a Gold Skulltula drops: the token with the item's name, model, animation and item settings
    'token': ('Obj_Token_Gold', 'Item_Token_Gold', 'Obj_NX2_GS_', ('LiftableRef', 'ELinkRef'), True,
              'Obj_Token_Gold_Animation'),
    # a level of a progressive family on the ground: the ground version under another name, which
    # tools/turn_items.py gives an AI of its own (and a drop part)
    'turn': (TEMPLATE, TEMPLATE_ITEM, 'Obj_NX2P_', TEMPLATE_ONLY, True, TEMPLATE_ITEM + '_Animation'),
}
TOKEN = 'Obj_Token_Gold'
# what marks the skulltula done when its drop is picked up: checked to be in a 'token' version (build)
TOKEN_KEEPS = {
    'AIInfoRef': '?AI/AIInfo/Item_Token_Gold.engine__actor__AIInfo.bgyml',
    'BlackboardRef': '?Component/Blackboard/BlackboardInfo/Item_Token_Gold.engine__component__BlackboardInfo.bgyml',
    'DeathRef': '?Component/DeathParam/Item_Token_Gold.game__component__DeathParam.bgyml'}
TOKEN_FILES = ('AI/Item_Token_Gold.root.ainb',
               'Component/Blackboard/BlackboardParamTable/Item_Token_Gold.engine__component__BlackboardParamTable.bgyml')
TOKEN_KEY = 'GoldTokenGmdHash'                # the blackboard key the skulltula's flag is handed over in
SPIN = 'Rotate_Obj'                           # the animation command of an item spinning on the ground
ROW_FROM_ITEM = ('ActorName', 'FmdbName', 'ModelAabbMax', 'ModelAabbMin', 'ModelProjectName')
TABLES = ('ActorInfo', 'GameActorInfo', 'PouchActorInfo')


def table_path(t):
    return 'RSDB/%s.Product.111.rstbl.byml' % t


def pack_path(actor):
    return 'Pack/Actor/%s.pack' % actor


def ap_path(actor):
    return 'Actor/%s.engine__actor__ActorParam.bgyml' % actor


def ground_name(item, version='ground'):
    return VERSIONS[version][2] + (item[5:] if item.startswith('Item_') else item)


def template_of(name):
    """the template actor a version (by its name) was built from"""
    hits = [(len(v[2]), v[0]) for v in VERSIONS.values() if name.startswith(v[2])]
    if not hits:
        raise KeyError(name)
    return max(hits)[1]                               # the longest prefix: Obj_NX2_GS_ before Obj_NX2_


def _ref_path(ref):
    """'?Component/X.bgyml' -> 'Component/X.bgyml'"""
    return ref[1:] if ref.startswith('?') else ref


def _parent_path(doc_root):
    """'$parent': 'Work/Component/X.gyml' -> 'Component/X.bgyml' (as stored in a pack)"""
    p = doc_root.get('$parent') if isinstance(doc_root, dict) else None
    if not p:
        return None
    if p.startswith('Work/'):
        p = p[5:]
    return p[:-5] + '.bgyml' if p.endswith('.gyml') else p


def _refs(root):
    """paths a settings file points at, as stored in a pack ('?X.bgyml' values and '$parent')"""
    out = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k == '$parent' and isinstance(x, str):
                    p = x[5:] if x.startswith('Work/') else x
                    out.append(p[:-5] + '.bgyml' if p.endswith('.gyml') else p)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and v.startswith('?'):
            out.append(v[1:])
    walk(root)
    return out


def _reach(files, start):
    """start and every file of the pack it points at, directly or through other files"""
    seen, todo = set(), [start]
    while todo:
        p = todo.pop()
        if p in seen or p not in files:
            continue
        seen.add(p)
        if p.endswith('.bgyml'):
            todo.extend(_refs(byml.loads(files[p]).root))
    return seen


def kind_of(read_pack, item):
    """'ground' (already an Obj_Item_Base actor), 'item' (an Item_EventObject_Base actor: needs a ground
    version) or None (not found / something else)"""
    try:
        files = sarc.Sarc.read(read_pack(pack_path(item))).files
    except FileNotFoundError:
        return None
    if 'Actor/Obj_Item_Base.engine__actor__ActorParam.bgyml' in files:
        return 'ground'
    if 'Actor/Item_EventObject_Base.engine__actor__ActorParam.bgyml' in files:
        return 'item'
    comp = byml.loads(files.get(ap_path(item), b'')).root.get('Components', {}) if ap_path(item) in files else {}
    if 'ModelInfoRef' in comp and 'PouchContentRef' in comp:
        return 'equipment'                            # built like Item_Ocarina_Time (equipment: ocarinas)
    return None


def resolved_components(files, actor):
    """an actor's components with those of the actors it inherits from ($parent), as far as its pack has them"""
    comp, p = {}, ap_path(actor)
    while p and p in files:
        root = byml.loads(files[p]).root
        for k, v in root.get('Components', {}).items():
            comp.setdefault(k, v)
        p = _parent_path(root)
    return comp


def item_components(files, actor):
    """an item actor's components as build() needs them: its own, and the item settings it does not name itself
    (INHERITED_REFS) from the actors it inherits from ($parent, in its pack), the nearest first. Only for an actor
    built on ITEM_BASE, and nothing from ITEM_BASE itself; any other actor: its own components alone, as before.
    The medium and large bags, quivers and wallets name no PouchContentRef: theirs is the small one's."""
    root = byml.loads(files[ap_path(actor)]).root
    own, found, p = root['Components'], {}, _parent_path(root)
    while p and p in files and p != ap_path(ITEM_BASE):
        root = byml.loads(files[p]).root
        for r in INHERITED_REFS:
            if r in root.get('Components', {}):
                found.setdefault(r, root['Components'][r])
        p = _parent_path(root)
    if p != ap_path(ITEM_BASE) or p not in files:
        return own
    return dict(found, **own)


GET_DEMO = b'Rotate_GetDemo'

# items whose own pose leaves them in the ground (seen in game, 2026-11-17; the scales 2026-11-19) or above it.
# Not the small Deku Stick and Deku Nut bags: the game never gives them as items, and the builder refuses them
# (NEVER_GIVEN in tools/build_mod.py)
GROUND_LIFT = ('Item_Gauntlet_Goron', 'Item_FairyBless_MP', 'Item_Scale_Silver', 'Item_Scale_Gold',
               # measured 2026-11-19 (see the notes at the top); not yet seen in game
               'Item_DinFire', 'Item_FaroreWind', 'Item_NayruLove',
               'Item_Quiver_Small', 'Item_Quiver_Medium', 'Item_Quiver_Large',
               'Item_StickBag_Medium', 'Item_StickBag_Large',
               'Item_BombBag_Medium', 'Item_BombBag_Large',
               'Item_BulletBag_Small', 'Item_BulletBag_Medium', 'Item_BulletBag_Large',
               'Item_NutBag_Medium', 'Item_NutBag_Large',
               'Item_Hammer', 'Item_Sword_Kokiri', 'Item_Wallet_Medium', 'Item_Wallet_Large',
               'Item_Dungeon_BossKey', 'Item_Dungeon_Map', 'Item_Token_Gold',
               'Item_MagicBean', 'Item_Ocarina_Fairy', 'Item_Ocarina_Time', 'Item_AgonyStone',
               'Item_FairyBless_MPDouble', 'Item_FairyBless_DefenseDouble',
               # these lie too high: lowered
               'Item_Arrow_Fire', 'Item_Arrow_Ice', 'TBox_ArrowBundle_Small',
               # on the Fire Arrow's project, but its model needs another height: a copy of its own (2026-11-20)
               'Item_Arrow_Light')
# items that share an animation project with another listed item: the one copy is measured on that item
GROUND_LIFT_AS = {'Item_FairyBless_MPDouble': 'Item_FairyBless_MP',
                  'Item_FairyBless_DefenseDouble': 'Item_FairyBless_MP',
                  'Item_FaroreWind': 'Item_DinFire', 'Item_NayruLove': 'Item_DinFire',
                  'Item_Arrow_Ice': 'Item_Arrow_Fire'}
# items that share an animation project with another listed item but need another height than its copy gives:
# a copy of their own, measured on their own model, under this name (as long as the project's, new to the game).
# Only for a project with a held-up pose of its own (the copy is the project itself)
GROUND_LIFT_OWN = {'Item_Arrow_Light': 'NX2G_ArrowLight_Animation'}
# measured with the box of ActorInfo (their models are built in the bone, so the box is right for them), as
# tested in game; the others with the model's vertices (tools/item_pose.py)
GROUND_LIFT_BOX = ('Item_Gauntlet_Goron', 'Item_FairyBless_MP')
GROUND_POSE, POSE_BONE = 'Pose_Common', 'Skl_Root'
SPIN_ROOT_LIFT = 0.05                        # Rotate_Obj's lift of the bone Root
GROUND_GAP = 0.05                            # the lowest point above the ground, as the Bottle's
GROUND_NEAR = 0.02                           # an item this near GROUND_GAP already is left as it is
GROUND_SHARED = 0.01                         # how far from GROUND_GAP an item on another item's copy may lie
# the lifted copy's name: the project's with its first letters changed (same length)
LIFTED_NAMES = (('Item', 'NX2G'), ('Weapon', 'NX2Gnd'), ('Obj_', 'NX2G'))
COMMON_ANIM = 'Item_Common_Animation'
# held up, an item is shown in its Pose_GetDemo, and in its Pose_Common only when its project has none (see "Held
# up" in the notes at the top). A project without one gets its lifted copy made of HELD_BASE instead of itself: a
# game project with exactly Pose_Common and Pose_GetDemo for the bones Root and Skl_Root (the ground magic jar's)
HELD_POSE = 'Pose_GetDemo'
HELD_BASE = 'Obj_MagicJar_Large_Animation'
HELD_NAME = 'NX2G_'                          # such a copy's name: this, the project's own part, '_' to the length


def model_path(project):
    return 'Model/%s.anim.bfres' % project


def has_held_pose(anim):
    """whether an animation project (its file) has a pose of its own for being held up (HELD_POSE)"""
    return HELD_POSE in item_pose.animations(anim)


def lifted_project(project, anim, item=None):
    """the name of the lifted copy of an item's animation project (`anim`: its file). A project with a held-up
    pose of its own is copied as it is: its name with its first letters changed (same length). One without is
    made of HELD_BASE: HELD_NAME, the project's name without its first word and '_Animation', filled with '_' to
    the length of HELD_BASE's name. `item`: the item the copy is for; one in GROUND_LIFT_OWN has a copy of its
    own, under the name given there."""
    if item in GROUND_LIFT_OWN:
        name = GROUND_LIFT_OWN[item]
        shared = [n for o, n in LIFTED_NAMES if project.startswith(o)]
        if not has_held_pose(anim) or len(name) != len(project) or not shared \
                or name == shared[0] + project[len(shared[0]):] \
                or list(GROUND_LIFT_OWN.values()).count(name) != 1:
            raise SystemExit('%s: %s cannot be the name of its own lifted copy of %s (a project with a %s; a '
                             'name as long, not the name of the shared copy, used once)'
                             % (item, name, project, HELD_POSE))
        return name
    if has_held_pose(anim):
        for old, new in LIFTED_NAMES:
            if project.startswith(old):
                return new + project[len(old):]
        raise SystemExit('%s: no lifted name for it (expected %s...)'
                         % (project, ', '.join(o for o, _ in LIFTED_NAMES)))
    tail = '_Animation'
    if '_' not in project or not project.endswith(tail):
        raise SystemExit('%s: no lifted name for it (expected <word>_<name>%s)' % (project, tail))
    name = (HELD_NAME + project.split('_', 1)[1][:-len(tail)]).ljust(len(HELD_BASE), '_')
    if len(name) != len(HELD_BASE):
        raise SystemExit('%s: no lifted name of %d letters for it' % (project, len(HELD_BASE)))
    return name


def _str_at(data, off):
    n = struct.unpack_from('<H', data, off)[0]
    return data[off + 2:off + 2 + n].decode('ascii')


def pose_bone(data, anim, bone):
    """(offset of the bone animation, flags, base offset) of `bone` in skeletal animation `anim` (FSKA sections:
    name at +8, bone animations at +0x28, bone count at +0x4c; a bone animation is 0x38 bytes: name, curves,
    base values, flags at +0x28; base values: scale 3 floats, rotation 4, translation 3, each only when its flag
    0x8 / 0x10 / 0x20 is set)"""
    i = 0
    while True:
        i = data.find(b'FSKA', i + 1)
        if i < 0:
            raise SystemExit('animation %s not found' % anim)
        if _str_at(data, struct.unpack_from('<Q', data, i + 8)[0]) != anim:
            continue
        bones = struct.unpack_from('<Q', data, i + 0x28)[0]
        for b in range(struct.unpack_from('<H', data, i + 0x4c)[0]):
            o = bones + 0x38 * b
            name, _, base = struct.unpack_from('<QQQ', data, o)
            if _str_at(data, name) == bone:
                return o, struct.unpack_from('<I', data, o + 0x28)[0], base
        raise SystemExit('animation %s: no bone %s' % (anim, bone))


def _pose(data, base, flags):
    """(scale, rotation (x, y, z radians), offset of the translation) of a bone animation's base values"""
    p, scale, rot = base, 1.0, (0.0, 0.0, 0.0)
    if flags & 8:
        scale = struct.unpack_from('<f', data, p)[0]
        p += 12
    if flags & 0x10:
        rot = struct.unpack_from('<3f', data, p)
        p += 16
    if not flags & 0x20:
        raise SystemExit('pose has no height to change')
    return scale, rot, p


def lowest_point(aabb_min, aabb_max, scale, rot):
    """the lowest Y of a model's box, sized and turned (X, then Y, then Z) by a pose"""
    rx, ry, rz = rot
    low = None
    for x0 in (aabb_min['X'], aabb_max['X']):
        for y0 in (aabb_min['Y'], aabb_max['Y']):
            for z0 in (aabb_min['Z'], aabb_max['Z']):
                x, y, z = x0, y0, z0
                y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
                x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
                x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
                low = y * scale if low is None else min(low, y * scale)
    return low


def box_low(data, aabb_min, aabb_max):
    """the lowest point of a model's box (ActorInfo) in the ground pose at height 0"""
    _, flags, base = pose_bone(data, GROUND_POSE, POSE_BONE)
    scale, rot, _ = _pose(data, base, flags)
    return lowest_point(aabb_min, aabb_max, scale, rot)


def vertex_low(data, model, height=0.0):
    """the lowest vertex of a model (its file) in the ground pose (of the animation project `data`) with
    Skl_Root at `height` (None: the pose's own): the vertices taken into the bone, then sized, turned and placed
    by the pose (tools/item_pose.py)"""
    pose = item_pose.read_pose(data, GROUND_POSE, POSE_BONE)
    if item_pose.read_pose(data, GROUND_POSE, item_pose.ROOT)['flags'] != item_pose.STILL:
        raise SystemExit('the ground pose moves the bone %s' % item_pose.ROOT)
    points, bind, _ = item_pose.model_points(model, POSE_BONE)
    move = pose['move'] if height is None else (pose['move'][0], height, pose['move'][2])
    return item_pose.extent(points, bind, pose['scale'], pose['rot'], move)[0][1]


def lifted_animation(data, project, low, read_base=None, item=None):
    """the lifted copy of an item's animation project (`data`: its file): the ground pose's height of Skl_Root set
    so the model's lowest point is GROUND_GAP above the ground (higher, or lower for an item that lies too high);
    `low`: the model's lowest point in that pose at height 0 (box_low, vertex_low). Held up, the item stays as the
    game shows it:
    - a project with a held-up pose of its own (HELD_POSE): the project itself renamed (lifted_project), only the
      ground pose's height changed;
    - one without (held up, the game shows its ground pose): HELD_BASE renamed, with the lifted pose as its ground
      pose and the item's own, untouched ground pose as its held-up pose. `read_base(path)` reads HELD_BASE.
    `item`: the item the copy is for, when it has a copy of its own (GROUND_LIFT_OWN: its own name).
    Returns (new data, old height, new height, the game file the copy is made of)"""
    o, flags, base = pose_bone(data, GROUND_POSE, POSE_BONE)
    scale, rot, t = _pose(data, base, flags)
    old = struct.unpack_from('<f', data, t + 4)[0]
    if flags & 0x8000000:                     # "no translation": the stored height was not used
        old = 0.0
    new_h = GROUND_GAP - SPIN_ROOT_LIFT - low
    if abs(new_h - old) <= GROUND_NEAR:
        raise SystemExit('%s: its pose already puts it where it should be (%.3f, wanted %.3f)'
                         % (project, old, new_h))
    if has_held_pose(data):
        new_project = lifted_project(project, data, item)
        return lifted_in_place(data, project, new_h, new_project), old, new_h, model_path(project)
    if item in GROUND_LIFT_OWN:
        raise SystemExit('%s: a copy of its own only of a project with a %s' % (item, HELD_POSE))
    if read_base is None:
        raise SystemExit('%s: no %s of its own, and no way to read %s' % (project, HELD_POSE, HELD_BASE))
    return lifted_on_base(read_base(model_path(HELD_BASE)), data, project, new_h), old, new_h, model_path(HELD_BASE)


def lifted_in_place(data, project, new_h, new_project=None):
    """the project's own file renamed (same length), the ground pose's height of Skl_Root set to `new_h`; nothing
    else. Every other pose, the held-up one too, stays the game's."""
    new_project = new_project or lifted_project(project, data)
    o, flags, base = pose_bone(data, GROUND_POSE, POSE_BONE)
    t = _pose(data, base, flags)[2]
    raw = (project + '.anim').encode('ascii')
    pat = struct.pack('<H', len(raw)) + raw + b'\0'
    k = data.find(pat)
    if k < 0 or data.find(pat, k + 1) >= 0 or len(new_project) != len(project):
        raise SystemExit('%s: its name is not in the file once, or %s is not as long' % (project, new_project))
    out = bytearray(data)
    out[k + 2:k + 2 + len(raw)] = (new_project + '.anim').encode('ascii')
    struct.pack_into('<I', out, o + 0x28, flags & ~0x8000000)
    struct.pack_into('<f', out, t + 4, new_h)
    out = bytes(out)
    if len(out) != len(data) or sum(a != b for a, b in zip(out, data)) > 4 + 4 + 4:
        raise SystemExit('%s: more than the name, the flag and the height changed' % project)
    o2, f2, b2 = pose_bone(out, GROUND_POSE, POSE_BONE)
    if abs(struct.unpack_from('<f', out, _pose(out, b2, f2)[2] + 4)[0] - new_h) > 1e-6 or f2 & 0x8000000:
        raise SystemExit('read-back: %s lifted pose' % project)
    return out


def lifted_on_base(base, data, project, new_h):
    """HELD_BASE (`base`: its file) renamed, its ground pose the item's own (`data`: the item's project) at height
    `new_h`, its held-up pose the item's own ground pose as it is; nothing else"""
    new_project = lifted_project(project, data)
    raw = (HELD_BASE + '.anim').encode('ascii')
    pat = struct.pack('<H', len(raw)) + raw + b'\0'
    k = base.find(pat)
    if k < 0 or base.count(HELD_BASE.encode('ascii')) != 1:
        raise SystemExit('%s: its name is not in the file once' % HELD_BASE)
    bones = sorted((item_pose.ROOT, POSE_BONE))
    theirs, mine = item_pose.animations(base), item_pose.animations(data)
    if sorted(theirs) != sorted((GROUND_POSE, HELD_POSE)) or any(sorted(b) != bones for b in theirs.values()):
        raise SystemExit('%s: not exactly %s and %s for the bones %s and %s'
                         % (HELD_BASE, GROUND_POSE, HELD_POSE, item_pose.ROOT, POSE_BONE))
    if sorted(mine.get(GROUND_POSE, ())) != bones:
        raise SystemExit('%s: its %s does not pose exactly %s and %s'
                         % (project, GROUND_POSE, item_pose.ROOT, POSE_BONE))
    src = item_pose.read_pose(data, GROUND_POSE)
    shape = item_pose._still(data, src, '%s %s' % (project, GROUND_POSE))
    if item_pose.read_pose(data, GROUND_POSE, item_pose.ROOT)['flags'] != item_pose.STILL:
        raise SystemExit('%s: its %s moves %s' % (project, GROUND_POSE, item_pose.ROOT))
    # a still pose's values: scale (12 bytes), rotation (16), translation (12)
    own = data[src['base']:src['base'] + 40]
    lying = own[:32] + struct.pack('<f', new_h) + own[36:]
    values = {GROUND_POSE: (lying, src['flags'] & ~item_pose.NO_TRANSLATION), HELD_POSE: (own, src['flags'])}
    out = bytearray(base)
    out[k + 2:k + 2 + len(raw)] = (new_project + '.anim').encode('ascii')
    allowed = set(range(k + 2, k + 2 + len(raw)))
    for p, (vals, flags) in values.items():
        dst = item_pose.read_pose(base, p)
        if item_pose._still(base, dst, '%s %s' % (HELD_BASE, p)) != shape \
                or item_pose.read_pose(base, p, item_pose.ROOT)['flags'] != item_pose.STILL:
            raise SystemExit('%s %s: not laid out like the %s of %s' % (HELD_BASE, p, GROUND_POSE, project))
        out[dst['base']:dst['base'] + 40] = vals
        struct.pack_into('<I', out, dst['at'] + 0x28, flags)
        allowed |= set(range(dst['base'], dst['base'] + 40)) | set(range(dst['at'] + 0x28, dst['at'] + 0x2c))
    out = bytes(out)
    # read-back: only the name and the two poses' values changed; held up it is the game's pose, lying the same
    # pose at the new height
    if len(out) != len(base) or not {i for i in range(len(base)) if out[i] != base[i]} <= allowed:
        raise SystemExit('%s: more than the name and the two poses changed' % new_project)
    held, lies = item_pose.read_pose(out, HELD_POSE), item_pose.read_pose(out, GROUND_POSE)
    if any(held[f] != src[f] for f in ('scale', 'rot', 'move', 'flags')):
        raise SystemExit('read-back: %s held up is not the %s of %s' % (new_project, GROUND_POSE, project))
    want = struct.unpack('<3f', struct.pack('<3f', src['move'][0], new_h, src['move'][2]))
    if any(lies[f] != src[f] for f in ('scale', 'rot')) or lies['move'] != want \
            or sorted(item_pose.animations(out)) != sorted(values):
        raise SystemExit('read-back: %s lifted pose' % new_project)
    return out


def own_projects(read_pack, item):
    """the animation projects of an item's own pack, apart from the shared one (COMMON_ANIM)"""
    files = sarc.Sarc.read(read_pack(pack_path(item))).files
    comp = byml.loads(files[ap_path(item)]).root['Components']
    if 'AnimationRef' not in comp or _ref_path(comp['AnimationRef']) not in files:
        return []
    res = byml.loads(files[_ref_path(comp['AnimationRef'])]).root['AnimationResources']
    return [x['ModelProjectName'] for x in res if x['ModelProjectName'] != COMMON_ANIM]


def can_hold_up(read, item):
    """whether Link can hold `item` up in the shared get event (Dm_SY_GetInEvent). That event makes the actor
    itself as the item shown in Link's hands (Player_Event.EventCreateShowItemFromActorFileName) and plays its
    animation command Rotate_GetDemo, waiting for it to end (EventIgnitionShowItem: IsAsPlay, IsWaitEnd). All 40
    actors the game's own flows give that way have an animation file (ASRef, a loose AS/*.asb file) that knows
    that command; the ocarinas (Link's instrument), the songs, the small bags, the stones and the medallions
    have no animation file or one without it, so the wait never ends (the Fairy Ocarina and the seed bag froze
    the game there). read(path) -> file contents (FileNotFoundError when it isn't there)."""
    try:
        files = sarc.Sarc.read(read(pack_path(item))).files
    except FileNotFoundError:
        raise SystemExit('%s: no such actor (no %s)' % (item, pack_path(item)))
    ref = resolved_components(files, item).get('ASRef')
    if not ref:
        return False
    path = _ref_path(ref)
    try:
        data = files[path] if path in files else read(path)
    except FileNotFoundError:
        return False
    return GET_DEMO in data


def pouch_param_path(actor):
    return 'Component/PouchContentParam/%s.game__component__PouchContentParam.bgyml' % actor


def anim_param_path(actor):
    return 'Component/AnimationParam/%s.engine__component__AnimationParam.bgyml' % actor


def build(item, read_pack, read_table_rows, model_exists=lambda project: False, version='ground'):
    """the ground version (version='ground'; 'turn': the same under the turning items' name, see
    tools/turn_items.py) or held-up version (version='held') of `item`.
    read_pack(path) -> decompressed pack; read_table_rows(table) -> list of rows; model_exists(project name)
    -> whether Model/<project>.anim.bfres exists (items with no animation file of their own: ocarinas).
    Returns (name, pack data, {inner path: data} of files new to the game, {table: new row}, {loose file new to
    the game: (data, the game file it is a copy of, old height, new height, the file of the item's own animation
    project)}: a lifted animation, GROUND_LIFT)."""
    TEMPLATE, TEMPLATE_ITEM, _, TEMPLATE_ONLY, auto_get, tpl_anim = VERSIONS[version]
    name = ground_name(item, version)
    tpl = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))
    itm = sarc.Sarc.read(read_pack(pack_path(item)))
    tpl_ap = byml.loads(tpl.files[ap_path(TEMPLATE)])
    itm_ap = byml.loads(itm.files[ap_path(item)]).root
    # the item's settings as the game reads them: its own, else those of the actor it inherits from
    tc, ic = tpl_ap.root['Components'], item_components(itm.files, item)
    if version == 'token':
        # ground items may inherit their parts (the blue rupee from the green one)
        ic = resolved_components(itm.files, item)
        for r, v in TOKEN_KEEPS.items():
            if tc.get(r) != v or _ref_path(v) not in tpl.files:
                raise SystemExit('%s: %s is %r, expected %s (game files differ from what this was made for)'
                                 % (TEMPLATE, r, tc.get(r), v))
        if any(p not in tpl.files for p in TOKEN_FILES) or TOKEN_KEY.encode() not in tpl.files[TOKEN_FILES[1]]:
            raise SystemExit('%s: its AI or its %s blackboard key not found as expected' % (TEMPLATE, TOKEN_KEY))
    missing = [r for r in ITEM_REFS if r not in ic and r != 'AnimationRef']
    if missing:
        raise SystemExit('%s: no %s in its actor parameters: no ground version' % (item, ', '.join(missing)))

    # the ground shield's own item files and shield-only files out (with the files only they point at), the
    # item's in (with the files they inherit from, when the item's pack has them: the bomb bag's settings
    # inherit from KeyItemDefault, in its pack)
    out_refs = ITEM_REFS + TEMPLATE_ONLY
    drop = set()
    for r in out_refs:
        if r in tc:
            drop |= _reach(tpl.files, _ref_path(tc[r]))
    keep = _reach(tpl.files, _parent_path(tpl_ap.root))      # the item base (Obj_Item_Base) and what it uses
    for r, v in tc.items():
        if r not in out_refs and isinstance(v, str) and v.startswith('?'):
            keep |= _reach(tpl.files, _ref_path(v))
    files = {p: d for p, d in tpl.files.items() if p not in drop or p in keep}
    del files[ap_path(TEMPLATE)]
    for r in ITEM_REFS:
        if r not in ic:
            continue
        path = _ref_path(ic[r])
        if path.startswith('ActorSystem/'):          # names live outside the packs
            continue
        while path and path in itm.files:
            files[path] = itm.files[path]
            path = _parent_path(byml.loads(itm.files[path]).root)
        if _ref_path(ic[r]) not in files:
            raise SystemExit('%s: %s (%s) not in its pack' % (item, r, ic[r]))

    comp = type(tc)(tc)
    for r in ITEM_REFS:
        if r in ic:
            comp[r] = ic[r]
        else:
            comp.pop(r, None)
    if 'AnimationRef' not in ic and model_exists(item + '_Animation'):
        # as the ground ocarina has one for Item_Ocarina_Time (whose own actor has none): the ground shield's
        # file with the item's animation project
        tdoc = byml.loads(tpl.files[_ref_path(tc['AnimationRef'])])
        res = [dict(x) for x in tdoc.root['AnimationResources']]
        swapped = [dict(x, ModelProjectName=item + '_Animation') if x['ModelProjectName'] == tpl_anim
                   else x for x in res]
        if swapped == res:
            raise SystemExit('template animation file not as expected')
        tdoc.root = type(tdoc.root)(tdoc.root)
        tdoc.root['AnimationResources'] = swapped
        files[anim_param_path(name)] = byml.dumps(tdoc)
        comp['AnimationRef'] = '?' + anim_param_path(name)
    loose = {}
    if item in GROUND_LIFT and version in ('ground', 'token', 'turn'):
        # lies too low: its own animation project replaced by a lifted copy (see the notes at the top)
        adoc = byml.loads(files[_ref_path(comp['AnimationRef'])])
        res = [dict(x) for x in adoc.root['AnimationResources']]
        own = [x['ModelProjectName'] for x in res if x['ModelProjectName'] != COMMON_ANIM]
        if len(own) != 1:
            raise SystemExit('%s: animation projects %r, expected %s and one of its own' % (item, res, COMMON_ANIM))
        info = {r['__RowId']: r for r in read_table_rows('ActorInfo')}
        row = info[item]
        src = read_pack(model_path(own[0]))
        # a project has one copy: measured on `first`, whichever of the items that share it is built
        first = GROUND_LIFT_AS.get(item, item)
        if item in GROUND_LIFT_OWN and item in GROUND_LIFT_AS:
            raise SystemExit('%s: listed both for another item\'s copy and for one of its own' % item)
        if first != item and (first not in GROUND_LIFT or first in GROUND_LIFT_AS
                              or own_projects(read_pack, first) != own):
            raise SystemExit('%s: %s is not a lifted item with the same animation project' % (item, first))

        def model_of(r):
            return read_pack('Model/%s.%s.bfres' % (r['ModelProjectName'], r['FmdbName']))

        if first in GROUND_LIFT_BOX:
            low = box_low(src, info[first]['ModelAabbMin'], info[first]['ModelAabbMax'])
        else:
            low = vertex_low(src, model_of(info[first]))
        data, old_h, new_h, like = lifted_animation(src, own[0], low, read_pack, item)
        new_project = lifted_project(own[0], src, item)
        if item not in GROUND_LIFT_BOX:
            # on its own copy: exactly; on another item's: near enough
            off = vertex_low(data, model_of(row), None) + SPIN_ROOT_LIFT - GROUND_GAP
            if abs(off) > (1e-5 if first == item else GROUND_SHARED):
                raise SystemExit('read-back: %s does not lie %.2f above the ground (%+.4f)' % (item, GROUND_GAP, off))
        loose[model_path(new_project)] = (data, like, old_h, new_h, model_path(own[0]))
        adoc.root = type(adoc.root)(adoc.root)
        adoc.root['AnimationResources'] = [dict(x, ModelProjectName=new_project)
                                           if x['ModelProjectName'] == own[0] else x for x in res]
        files[anim_param_path(name)] = byml.dumps(adoc)
        comp['AnimationRef'] = '?' + anim_param_path(name)
    # picked up by walking into it: item settings of its own (the item's as parent, DefaultAutoGet on), as
    # the ground shield's own settings over AutoPickShield
    pdoc = byml.loads(tpl.files[_ref_path(tc['PouchContentRef'])])
    pdoc.root = type(pdoc.root)()
    pdoc.root['$parent'] = 'Work/' + _ref_path(ic['PouchContentRef'])[:-len('.bgyml')] + '.gyml'
    if auto_get:
        pdoc.root['DefaultAutoGet'] = True
    stands_for, pp = None, _ref_path(ic['PouchContentRef'])
    while pp and pp in itm.files and stands_for is None:   # a ground item may name another item already
        proot = byml.loads(itm.files[pp]).root
        stands_for, pp = proot.get('PouchActor') or None, _parent_path(proot)
    if not (version == 'token' and stands_for and kind_of(read_pack, item) == 'ground'):
        pdoc.root['PouchActor'] = 'Work/' + ap_path(item)[:-len('.bgyml')] + '.gyml'
    files[pouch_param_path(name)] = byml.dumps(pdoc)
    comp['PouchContentRef'] = '?' + pouch_param_path(name)
    if _parent_path(byml.loads(files[pouch_param_path(name)]).root) != _ref_path(ic['PouchContentRef']):
        raise SystemExit('read-back: item settings parent of %s' % name)
    for r in TEMPLATE_ONLY:                         # as Obj_Item_Base
        comp.pop(r, None)
    if version == 'token':
        # the spin: the token's AI plays no animation, its animation settings (ASInfo) start Rotate_Obj by
        # themselves; ground items are spun by their AI instead (DropItem / Obj_Heart_Piece: OneShotASPlay
        # Rotate_Obj) and their settings start nothing. So the token's settings stay, and only the animation
        # file comes from the item (a ground item whose file knows the command: the Piece of Heart), else from
        # the ground shield (Item_Common); the token's own file spins with an animation of the token's model
        info = _ref_path(tc['ASInfoRef'])
        if info not in files or byml.loads(files[info]).root.get('AutoPlayASName') != SPIN:
            raise SystemExit('%s: its animation settings (%s) do not start %s by themselves as expected'
                             % (TEMPLATE, info, SPIN))

        def knows_spin(pack, ref):
            path = _ref_path(ref)
            try:
                return SPIN.encode() in (pack.files[path] if path in pack.files else read_pack(path))
            except FileNotFoundError:
                return False

        sc = ic
        if 'ASRef' not in ic or kind_of(read_pack, item) != 'ground' or not knows_spin(itm, ic['ASRef']):
            src = sarc.Sarc.read(read_pack(pack_path(VERSIONS['ground'][0])))
            sc = resolved_components(src.files, VERSIONS['ground'][0])
            if 'ASRef' not in sc or not knows_spin(src, sc['ASRef']):
                raise SystemExit('%s: its animation file does not know %s as expected' % (VERSIONS['ground'][0], SPIN))
        comp['ASRef'] = sc['ASRef']
        if comp['ASRef'] == tc['ASRef'] or comp.get('ASInfoRef') != tc['ASInfoRef']:
            raise SystemExit('%s: animation settings not as intended' % name)
        for r, v in TOKEN_KEEPS.items():
            if comp.get(r) != v or _ref_path(v) not in files:
                raise SystemExit("%s: lost the token's %s" % (name, r))
        if any(p not in files for p in TOKEN_FILES):
            raise SystemExit("%s: lost the token's AI or blackboard table" % name)
    doc = copy.copy(tpl_ap)
    doc.root = type(tpl_ap.root)(tpl_ap.root)
    doc.root['Components'] = comp
    files[ap_path(name)] = byml.dumps(doc)
    out = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))      # the shield pack's own layout settings
    out.files = files
    out.align = {p: (tpl.align.get(p) or itm.align.get(p) or 8) for p in files}
    pack = out.write()

    rows = {}
    tables = {t: {r['__RowId']: r for r in read_table_rows(t)} for t in TABLES}
    if name in tables['ActorInfo']:
        raise SystemExit('%s already exists in the game' % name)
    ai_t, ai_ti, ai_i = (tables['ActorInfo'][n] for n in (TEMPLATE, TEMPLATE_ITEM, item))
    ai = type(ai_t)(ai_t)
    for k in ROW_FROM_ITEM:
        if k in ai_i:
            ai[k] = ai_i[k]
        else:
            ai.pop(k, None)
    anim = None
    if 'AnimationRef' in comp:
        anim = byml.loads(files[_ref_path(comp['AnimationRef'])]).root.get('AnimationResources')
    if anim is not None:
        ai['AnimationResources'] = anim
    else:
        ai.pop('AnimationResources', None)
    # memory: the item's own needs plus what the ground parts add (as measured on the shield), and margin
    extra = int(ai_t['InstanceHeapSize']) - int(ai_ti['InstanceHeapSize'])
    ai['InstanceHeapSize'] = type(ai_t['InstanceHeapSize'])(
        max(int(ai_t['InstanceHeapSize']), int(ai_i['InstanceHeapSize']) + extra) + 16384)
    ai['PreActorRenderInfoHeapSize'] = type(ai_t['PreActorRenderInfoHeapSize'])(
        max(int(ai_t['PreActorRenderInfoHeapSize']), int(ai_i.get('PreActorRenderInfoHeapSize', 0)) + 1024))
    ai.pop('ELinkUserName', None)                   # no effects (the shield's effect link is left out)
    ai['__RowId'] = name
    rows['ActorInfo'] = ai
    ga = type(tables['GameActorInfo'][TEMPLATE])(tables['GameActorInfo'][TEMPLATE])
    ga['__RowId'] = name
    rows['GameActorInfo'] = ga
    if item not in tables['PouchActorInfo']:
        raise SystemExit('%s has no row in PouchActorInfo' % item)
    pa = type(tables['PouchActorInfo'][item])(tables['PouchActorInfo'][item])
    pa['__RowId'] = name
    rows['PouchActorInfo'] = pa

    new_inner = {p: d for p, d in files.items() if p not in tpl.files and p not in itm.files}
    # read back
    back = sarc.Sarc.read(pack)
    if set(back.files) != set(files) or any(back.files[p] != d for p, d in files.items()):
        raise SystemExit('read-back: pack of %s differs from what was intended' % name)
    want_ap = dict(tpl_ap.root, Components=dict(comp))
    if byml.loads(back.files[ap_path(name)]).root != want_ap:
        raise SystemExit('read-back: actor parameters of %s differ' % name)
    return name, pack, new_inner, rows, loose


def add_rows(data, new_rows):
    """insert rows into an RSDB table (kept sorted by __RowId, as the game's are); checks that nothing else
    changed"""
    doc = byml.loads(data)
    ids = [r['__RowId'] for r in doc.root]
    if ids != sorted(ids):
        raise SystemExit('table not sorted as expected')
    for row in new_rows:
        if row['__RowId'] in ids:
            raise SystemExit('row %s already exists' % row['__RowId'])
    rows = list(doc.root) + list(new_rows)
    rows.sort(key=lambda r: r['__RowId'])
    doc.root[:] = rows if isinstance(doc.root, list) else rows
    new = byml.dumps(doc)
    back = byml.loads(new).root
    old = byml.loads(data).root
    added = {r['__RowId'] for r in new_rows}
    if [r for r in back if r['__RowId'] not in added] != list(old):
        raise SystemExit('read-back: existing rows changed')
    if [r for r in back if r['__RowId'] in added] != sorted(new_rows, key=lambda r: r['__RowId']):
        raise SystemExit('read-back: new rows differ')
    return new
