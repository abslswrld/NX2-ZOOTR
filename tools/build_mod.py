"""Build a Longshot mod folder that changes what some checks give, by permanent check ID.

    python tools/build_mod.py --romfs "<romfs>" --out out\\mods --name NX2-ZOOTR KF_MIDO_CHEST_01=Item_Boomerang ...

Supported: chests and pots (their item is their Drop__DropActor in the map file; a pot that names a drop table
instead, Drop__DropTable, or nothing at all, as most pots in dungeons do, gets the item and loses the table, the
form the game's own item pots have; a chest that names nothing gets the item; rocks, bushes and Gold
Skulltulas get one added: a skulltula then drops the item instead of its token, as a version of the item built
from the token, which is what marks the skulltula done when picked up: gs_drop, tools/ground_items.py),
freestanding items
(the actor type itself is the item: it is replaced), gifts that hand their item over through the shared
event flow Dm_SY_GetInEvent (the item is that call's ActorName; the check's data names the flow, the event and
the item, "gift": {...}; an item Link can't hold up in that event, such as an ocarina or a song, is given with
the "You got ..." window instead: gift_edit), songs (the song cutscene, "song": {...} in the data, only fades in and hands over
the item: song_skip), Deku Scrubs that sell one thing once (the upgrade scrubs: their map setting
ScrubBusiness_ShopItemActorName0 becomes the item, and the shared flow Enemy_Scrub_Business_Common gets one new
branch per item, selling it at the scrub's original price with a new generic line that names the item; see
scrub_flow_edit) and shop shelves (the shelf actor is replaced by a shop
version of the item, tools/shop_items.py, at the shelf's original price, sold once: the shelf takes over the
saved flag of a shop object the build removes, shelf_flag_map_edit, and the shop version's own AI sets that
flag when the shopkeeper says "sold out", so the shelf is not placed again: shop_items.sold_for_good_ai). For
each check every placement is changed (child and adult copies, copies in other maps; a check made for one
age, "age" in its data, only has that age's), the map files are
written back compressed with the same dictionary as the original, and the resource size table (RESTBL)
gets the new sizes. Output: <out>/<name>/romfs/... mirroring the game's romfs, for Longshot's HOS_MODS.

Ocarina chests (to test in game): a chest that holds an ocarina (alone, or as a level of a progressive pair) gets
an opening event of our own, which runs the chest's usual opening event and then makes Link's ocarina, so it can
be played at once (TBOX_SYNC_FLOW: a new flow file and two table rows; the game's shared chest flows are not
changed).

Checking chests: the game has a small chest that looks in Link's inventory (Obj_TBox_A_06, see CHECKING_CHEST).
One of the game's own that gets an item becomes the ordinary small chest, so it always gives the placed item.
Progressive pair (opt-in, a test for now): CHECK_ID=First>Second on a small chest makes it a checking chest that
gives First while Link doesn't have First, else Second; only the pairs in PROGRESSIVE_PAIRS are accepted:

    python tools/build_mod.py ... "KF_MIDO_CHEST_01=Item_Scale_Silver>Item_Scale_Gold"
(quoted: > is the shell's redirection otherwise). The pairs and the three-level families are declared once, in
FAMILIES: Silver > Gold Scale, Hookshot > Longshot, Fairy Ocarina > Ocarina of Time, the medium > large Deku
Stick bag, Deku Nut bag and wallet, magic > double magic; the three bomb bags, Fairy Slingshot > medium > large
seed bag, Fairy Bow > medium > large quiver, Goron's Bracelet > Silver > Golden Gauntlets.
The same on a freestanding item (to test in game): the placement becomes First's turning item
(tools/turn_items.py): a ground item of First that, once Link owns First, drops Second's in its place and removes
itself; Second's removes itself once Link owns Second. Two freestanding items with the same pair give First then
Second in either order.
The same on a liftable rock, a solid bush, a pot or a Gold Skulltula (passed in game, 2026-11-22/23): its drop
(Drop__DropActor) names the first level's one-time turning item (tools/once_items.py). It turns into the next
level on the ground once Link owns its own, and marks what dropped it when it turns or is picked up (given
once). Not on shelves yet.
Three-level family (to test in game): CHECK_ID=First>Second>Third on a small chest makes it a chest of our own
(tools/three_chest.py: the checking chest with a third held item and a second question) that gives Third when
Link has Second, else Second when Link has First, else First; only the families in THREE_LEVEL_FAMILIES:

    python tools/build_mod.py ... "KF_MIDO_CHEST_01=Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large"

Three levels go wherever a pair goes (to test in game): on a freestanding item the turning
item has three levels (the first turns into the second, the second into the third); a gift and a Deku Scrub ask
two questions ("has Second?" then "has First?"). Not in a big chest (it has no checking version).
The first level of the seed bags and the quivers is the weapon (Item_Range_SlingShot, Item_Range_Bow). The game's
chests give the small bag and 30 seeds or arrows with it (the shared chest module, read by
turn_items.first_get); only chests do. So the first level's turning item gives the same, and a gift or a scrub
adds the small bag after it (SCRUB_COMPANIONS: the bag comes filled).

The same on a gift that has flow data (to test in game): the giver's own flow asks the inventory in front of
its call of the shared get flow, as the game's own flows do for upgrades, and gives First or Second
(gift_pair_edit). Gifts without flow data (cutscene gifts) and songs are refused.
The same on a Deku Scrub that sells one thing once (to test in game): the scrub's branch of the scrub flow asks
the inventory before the sale, as the game's own stick-bag and nut-bag scrubs do, and sells First or Second at
the scrub's price (scrub_flow_edit, point 4).

A later level of an upgrade family placed on its own (Item_Scale_Gold, Item_Longshot, a bigger bag...) stops the
build before anything is written: Link could take it before the level in front of it (UPGRADE_FAMILIES,
skip_level_guard). The message names the First>Second or First>Second>Third form to use when there is one.

A dungeon's small key anywhere (to test in game): CHECK_ID=Item_Dungeon_SmallKey@ForestTemple puts a small key
that counts for the Forest Temple on the check, in the temple or outside it (tools/dungeon_keys.py). The game
itself counts a key for the dungeon Link is in. On a pot, a rock, a bush, a freestanding item or a Gold Skulltula
the key adds to the temple's key count when it is picked up (its own AI); in a chest the chest gets an opening
event of our own around its usual one that adds to it (TBOX_KEY_FLOW). Not on gifts, scrubs or shelves yet.
On a check of its own dungeon it is the game's own small key: the game counts and shows that one itself.
...@ForestTemple+name (an experiment): the key's messages name the dungeon ("Small Key (Forest Temple)").

Gossip stone text (to test in game): --gossip STONE=TEXT (repeatable) sets what a stone says, in every language
(English text everywhere). STONE is the stone's check ID or its name in the map. In TEXT, \\n is a new line, \\p a
new page and {...} is highlighted; longer lines are wrapped and full pages continue on a new page, as the game's
rumours are laid out. The chosen stones speak without the Mask of Truth, at both ages; the others are unchanged
(see gossip_flow_edit):

    python tools/build_mod.py ... --gossip "KF_NEAR_LOST_WOODS_GOSSIP=They say {Kokiri Forest} is on the way."

Hints (to test in game): --hint STONE=ITEM or --hint STONE=@CHECK_ID (repeatable) makes the stone say where an item
of this build is, as a --gossip text worded from the placements and the game's own names (hint_specs):

    python tools/build_mod.py ... KF_KNOW_IT_ALL_HOUSE_CHILD_POT_02=Item_Boomerang
        --hint KF_NEAR_LOST_WOODS_GOSSIP=Item_Boomerang
    -> "They say the {Boomerang} can be found in a pot in the {House of the Know-It-All Brothers} in {Kokiri Forest}."

Starting state of a new file (to test in game): --start ITEM or --start ITEM=N (repeatable) puts an item in the
inventory of every new file, and --start-flag NAME=VALUE (repeatable) sets a flag on it (a Bool: true or false,
an Int: a number, a String64: text). Both are added to the game's own list of what a new file has, the sequence
module Sequence/SetPouchAndStatusForGameStart, which the new-game sequence runs once before Kokiri Forest is
loaded (tools/start_state.py). Files that already exist are not changed:

    python tools/build_mod.py ... --start Item_Boomerang --start-flag KokiriForest_Npc_Kokiri_Mido_Child_Blocker=false

Game fixes (--fix NAME, see FIXES and FILE_FIXES):
    kokiri_shop_full_stock   the Kokiri Shop sells the same 8 shelves as a child before and after meeting the
                             Deku Tree (the "low on stock" set is removed, every shelf is open from the
                             start, the child shopkeeper greets as after the Deku Tree), and the adult
                             shopkeeper gets a shop list of its own; needed to change
                             shop shelves (each shelf's item, sold once, goes into the shopkeeper's list)
    bombchus_without_bag     Bombchus get a capacity of their own (BOMBCHU_MAX, as in the original game) and
                             no longer need the bomb bag: in the remake their maximum is the bomb bag's, so
                             without one it is 0; bomb bags stop raising and refilling them
    forest_temple_bow_room_door
                             the Forest Temple's Bow room unlocks its west shutter as soon as its chest has
                             appeared (decision 39). In the game it stays locked until the eye switch behind
                             the bars is shot with an arrow, saving is off in the room, and dying loses what
                             was picked up there: without the Bow nothing found in the room could be kept
    bombs_without_bracelet   bombs from the bomb bag can be held without the Goron Bracelet: the bomb's lift
                             grade becomes the "no upgrade" grade of rocks, bushes, pots and Bombchus (bomb
                             flowers have their own copy of the setting and still need the bracelet)
    kokiri_circle_after_dungeons
                             the rock circle by Mido's house as after the dungeons, at both ages: an adult sees
                             the same ring of 8 rocks as a child (as after the Forest Temple; before, an adult
                             saw 4 other rocks), and the Kokiri (Npc_Kokiri_008_Child) no longer stands on the
                             middle rock trying to lift it, which can be lifted (as after the Kokiri Emerald);
                             needed for items on the adult circle rocks and the middle rock
    magic_is_separate        magic items (Lens of Truth, Din's Fire, Farore's Wind, Nayru's Love, magic arrows)
                             no longer give the magic meter; only the Great Fairy's blessings do
                             (Item_FairyBless_MP: magic, Item_FairyBless_MPDouble: double magic)
    skippable_opening        the opening cutscene (Dm_Kokiri_0000) can be skipped like every other cutscene:
                             removes its "DisableSkip" setting (only the opening, the title screen and the
                             staff credits have it)

The game's own files are only read. The output contains modified game files: it must never be committed
or shared (out/ is ignored by git).
"""
import argparse
import collections
import copy
import os
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import dungeon_keys  # noqa: E402
import ground_items  # noqa: E402
import harp_colors  # noqa: E402
import once_items  # noqa: E402
import shop_items  # noqa: E402
import sizes  # noqa: E402
import start_state  # noqa: E402
import three_chest  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, restbl, sarc, evfl, ainb, msbt  # noqa: E402
from logic.world import World  # noqa: E402

RESTBL_PATH = os.path.join('System', 'Resource', 'ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs')
SUPPORTED = {'chest', 'pot', 'freestanding', 'shop', 'rock', 'bush', 'skulltula', 'gift', 'scrub'}
REPLACED = ('freestanding', 'shop')      # kinds whose actor itself is replaced
# kinds whose drop is usually not set in the map: the builder adds Drop__DropActor (the game itself sets it on
# some rocks and bushes elsewhere, e.g. Obj_LiftRock_A_01 in Desert Colossus, Obj_Plant_Grass_A_01 in Hyrule Field)
DROP_ADDED = ('rock', 'bush', 'skulltula')
DROP_ON_GROUND = ('freestanding', 'pot', 'rock', 'bush', 'skulltula')   # kinds whose item lies on the ground
# name -> (actor pack, file inside the pack, key, value it must have now, new value)
LIFT_GRADE_NO_UPGRADE = 3069107721      # small rocks, bushes, pots, Cuccos, Bombchus
LIFT_GRADE_BRACELET = 3655598229        # bombs and bomb flowers
FIXES = {
    'bombs_without_bracelet': ('Pack/Actor/Item_Bomb.pack',
                               'Component/LiftableParam/Item_Bomb.game__component__LiftableParam.bgyml',
                               'LiftGrade', LIFT_GRADE_BRACELET, LIFT_GRADE_NO_UPGRADE),
}
# Some chests play a special event when opened (their GetEventName), made for their original item. When the
# item changes: 'remove' it (the chest then opens like any other) or 'keep' it. A chest with an event not
# listed here stops the build, so every one gets a decision.
CHEST_EVENTS = {
    'Get_StoneOfForest_GetSword': ('remove', 'plays Dm_Kokiri_0063, which gives and equips the Kokiri Sword '
                                             '(found in game: the sword came with any item; removed and '
                                             'retested 2026-11-16: slingshot only, no sword)'),
    'KokiriForest_TreasureBox_NaviChatOff': ('keep', 'Mido\'s chests: tested in game with four other items, harmless'),
    # the Forest Temple (read from the flows; in game 2026-11-23: the Bow's chest with the Ice Arrow gave no
    # message from Navi, the map's chest with the Fairy Bow opened as usual; the compass's not tested)
    'ForestTemple_GetBow': ('remove', 'SageOfForest / TreasureBoxDM_NaviChat_Bow: the usual opening '
                                      '(Dm_SY_Treasurebox), then Navi\'s balloon message 476 about the Bow'),
    'ForesetTemple_GetMap': ('keep', 'NaviChat / TreasureBoxDM_NaviChat_ForestTemple_Map: only the usual opening '
                                     '(subflow PlayDemo -> Dm_SY_Treasurebox), no message'),
    'ForesetTemple_GetCompass': ('keep', 'NaviChat / TreasureBoxDM_NaviChat_ForestTemple_Compass: only the usual '
                                         'opening (subflow PlayDemo -> Dm_SY_Treasurebox), no message'),
}
# The game's checking chest (Obj_TBox_A_06, 9 placements) is the ordinary small chest (its settings file has
# $parent Obj_TBox_A_01: same model, animation, physics and opening event) with its own AI, a second held actor
# (SubContent) and three more map settings: it gives Drop__DropActor while Link doesn't have Drop__CheckActor,
# else Drop__DropActor_Substitute (Graveyard: no Hylian Shield -> the shield, else a red rupee). Its AI makes
# both items when the chest is made and asks the inventory each time it is run (QueryGetPouchContentNumByActorName,
# not "only on enter"), handing the chosen holder to the shared chest module that requests the opening event.
CHECKING_CHEST = {'Obj_TBox_A_01': 'Obj_TBox_A_06', 'Obj_TBox_A_01_NoBake': 'Obj_TBox_A_06_NoBake'}
PLAIN_CHEST = {v: k for k, v in CHECKING_CHEST.items()}
CHECK_SETTINGS = ('Drop__CheckActor', 'Drop__DropActor_Substitute', 'Drop__CheckCondition')
POT_TABLE_KEY = 'Drop__DropTable'                 # a pot's drop table: removed where we place an item
# The upgrade families, declared once: name -> the levels as they are placed, lowest first (the user's list,
# 2026-11-21). Everything else is worked out from this table: the pairs (PROGRESSIVE_PAIRS), the three-level
# families and the names of their chests (THREE_LEVEL_FAMILIES) and what the skip-level guard refuses alone
# (UPGRADE_FAMILIES). The names are the items' own names, the ones a chest, the ground or a flow gives.
# A level here is always one the builder places:
# - the seed bags' and the quivers' first level is the weapon. The game gives the Fairy Slingshot and the Fairy
#   Bow from chests (the Deku Tree, the Forest Temple: Drop__DropActor Item_Range_SlingShot / Item_Range_Bow), and
#   the shared chest module then adds the small bag and 30 seeds or arrows (turn_items.first_get); the small bag
#   and quiver are no gift of their own anywhere (FAMILY_ALIASES: placed alone they mean the weapon);
# - the Deku Stick bags, Deku Nut bags and wallets start at Medium: the small ones are never given (NEVER_GIVEN:
#   the first stick or nut brings its bag, the wallet is there from the start), and the game's own flows ask
#   "has Medium?" and give Medium or Large;
# - strength is one family (the user: "1 tree for now").
# Every level is an inventory item of its own and stays owned when the next one comes (GameData: IsGet.<name>,
# PouchData.<name>.StockNum for each; the game's own flows ask "has Medium?" and then "has Large?":
# Npc_Goron_012_Child, MiniGame_BombchuBowling), so "has Second?" then "has First?" finds the next level.
FAMILIES = {
    'Scale': ('Item_Scale_Silver', 'Item_Scale_Gold'),             # in game 2026-11-18: both opening orders work
    # the game's own chests give these two names (Dampe's goal chest, the Water Temple). Its flows ask for the
    # Longshot and then for the Hookshot to mean "has a hookshot" (MiniGame_DampeRace, Npc_Gerudo_004), so the
    # Longshot most likely takes the Hookshot's place in the inventory: the second chest of a pair is only
    # opened once, so the order holds either way
    'Hookshot': ('Item_Hookshot', 'Item_Longshot'),                # in game 2026-11-19: works
    # ocarinas are Link's instrument (no get-demo settings): the chest holds their held-up versions. The
    # Ocarina of Time itself teaches nothing: the Song of Time is an item of the moat cutscene (Dm_MelodyGet_Time)
    'Ocarina': ('Item_Ocarina_Fairy', 'Item_Ocarina_Time'),        # in game 2026-11-19: works
    # 20, 30, 40 bombs. The game's own chest gives Item_BombBag_Small (Dodongo's Cavern)
    'BombBag': ('Item_BombBag_Small', 'Item_BombBag_Medium', 'Item_BombBag_Large'),
    'BulletBag': ('Item_Range_SlingShot', 'Item_BulletBag_Medium', 'Item_BulletBag_Large'),   # 30, 40, 50 seeds
    'Quiver': ('Item_Range_Bow', 'Item_Quiver_Medium', 'Item_Quiver_Large'),                  # 30, 40, 50 arrows
    'StickBag': ('Item_StickBag_Medium', 'Item_StickBag_Large'),   # 20, 30 sticks (the small one: 10)
    'NutBag': ('Item_NutBag_Medium', 'Item_NutBag_Large'),         # 30, 40 nuts (the small one: 20)
    'Wallet': ('Item_Wallet_Medium', 'Item_Wallet_Large'),         # 500, 1000 rupees (the one from the start: 200)
    'Gauntlet': ('Item_Gauntlet_Goron', 'Item_Gauntlet_Silver', 'Item_Gauntlet_Gold'),        # lift grades
    'Magic': ('Item_FairyBless_MP', 'Item_FairyBless_MPDouble'),   # the magic meter: 24, 48
}
# Progressive pairs (opt-in, CHECK_ID=First>Second): the families of two levels. In a small chest the chest
# becomes the game's checking chest: First while Link doesn't have First, else Second. Two chests with the same
# pair give First then Second in either opening order. The chest looks for First under the item's own name
# (Drop__CheckActor: the game's own checking chests name an item actor there, Item_Range_Bow, TBox_Shield_Deku)
# and holds each item as a chest gives it (in_chest: an ocarina as its held-up version Item_NX2_<x>, which goes
# into the inventory as the ocarina itself, its PouchActor).
PROGRESSIVE_PAIRS = {levels for levels in FAMILIES.values() if len(levels) == 2}
# Three-level families (opt-in, CHECK_ID=First>Second>Third): the families of three levels -> the name of their
# chest. In a small chest the chest becomes a chest of our own, Obj_TBox_NX2_<name> (tools/three_chest.py): the
# game's checking chest with a third held item and a second question. Third when Link has Second, else Second
# when Link has First, else First: three chests with the same family give the three levels in order, whatever
# the opening order. A chest holds each level under its own name: all are item event actors with the get demo.
# A chest that holds the Fairy Slingshot or the Fairy Bow gives the small bag and 30 seeds or arrows with it by
# itself: the shared chest module does, whatever chest it is in (in game: a slingshot from a chest came with 30).
THREE_LEVEL_FAMILIES = {levels: name for name, levels in FAMILIES.items() if len(levels) == 3}
if any(len(levels) not in (2, 3) for levels in FAMILIES.values()) \
        or len({x for levels in FAMILIES.values() for x in levels}) != sum(len(v) for v in FAMILIES.values()):
    raise SystemExit('FAMILIES: every family has two or three levels, and no item is in two families')
# where the progressive forms can be placed (said in messages)
PROGRESSIVE_WHERE = ('on a small chest, a freestanding item, a rock, a bush, a pot, a Gold Skulltula, a Deku Scrub '
                     'that sells once or a gift with flow data')


def three_level_parse(world, assignments):
    """takes the three-level families (CHECK_ID=First>Second>Third) in chests out of `assignments`: each becomes
    (CHECK_ID, First), as a pair's; returns {check id: family}. Stops the build for a family that is not in
    THREE_LEVEL_FAMILIES, and for a check of a kind no progressive form can be put on (a shelf). A family
    on a freestanding item, a rock, a bush, a pot, a Gold Skulltula, a scrub or a gift is left as it is: sorted out
    with the pairs (main). A big chest is refused when its map is changed (patch_file)."""
    out = {}
    for k, (cid, item) in enumerate(assignments):
        if item.count('>') != 2:
            continue
        family = tuple(item.split('>'))
        if family not in THREE_LEVEL_FAMILIES:
            raise SystemExit('%s: %s is not a three-level family the builder knows (%s)' % (cid, item, ', '.join(
                '>'.join(x) for x in sorted(THREE_LEVEL_FAMILIES))))
        r, name, loc = find_check(world, cid)
        kinds = {world.checks[scene][spot_id]['kind'] for scene, spot_id, _ in world.placements_of(r, loc)}
        if not kinds or kinds == {'scrub'} or (len(kinds) == 1 and kinds <= set(TURN_KINDS)) \
                or kinds == GS_KINDS:
            continue                                   # a gift, a scrub, a turning item: with the pairs
        if kinds != {'chest'}:
            raise SystemExit('%s: a three-level family (First>Second>Third) can only be put %s (this check: %s)'
                             % (cid, PROGRESSIVE_WHERE, ', '.join(sorted(kinds))))
        out[cid] = family
        assignments[k] = (cid, family[0])
    return out


def checking_chest(gyaml, family=None):
    """the chest that takes the place of a small chest (`gyaml`: Obj_TBox_A_01, the game's checking chest, or
    the _NoBake twin of either): the game's checking chest, or for a three-level family (its name in
    THREE_LEVEL_FAMILIES) the chest of our own"""
    plain = PLAIN_CHEST.get(gyaml, gyaml)
    if family is None or plain not in CHECKING_CHEST:
        return CHECKING_CHEST.get(plain, plain)
    return three_chest.chest_name(family, plain.endswith(three_chest.NOBAKE))


# Where a progressive pair can be placed: a small chest (the checking chest), a freestanding item (a turning
# item, tools/turn_items.py), or a liftable rock, solid bush, pot or Gold Skulltula. What a rock, a bush or a pot
# drops for us is given once (tools/once_items.py): it is the first level's one-time turning item, which turns on
# the ground and, when it turns or is picked up, sets its dropper's two saved flags as a token sets its Gold
# Skulltula's (passed in game, 2026-11-22). A Gold Skulltula drops the same one-time turning item: it hands its
# own flag to what it drops, as it does to its token (passed in game, 2026-11-23; skulltula_pair_kind).
# (The other way, the game's drop code choosing the level before anything is dropped, never put a lower level
# in place in game, 2026-11-22: its code was removed on 2026-11-23.)
# Not yet: shelves (the shop version has no such AI).
# Gifts: gift_pair_kind, gift_pair_edit. Scrubs: scrub_pair_kind, scrub_flow_edit.
GS_KINDS = {'skulltula'}
PAIR_KINDS = ('chest', 'freestanding', 'rock', 'bush', 'pot')
TURN_KINDS = ('freestanding', 'rock', 'bush', 'pot')   # the kinds whose pair is a turning item
# Two turning items of one family must not lie where Link can touch both at once: the second could be picked up
# in the frame the first's scene ends, before it has turned (it would give the first level again). Metres,
# between their map positions (for a rock or a bush: where it stands; a rock carried and thrown next to another
# item of its family is not covered).
TURN_MIN_DISTANCE = 2.0


def skulltula_pair_kind(world, cid):
    """whether a progressive form on this check is a Gold Skulltula's: every placement of the check is one"""
    r, name, loc = find_check(world, cid)
    kinds = {world.checks[scene][spot_id]['kind'] for scene, spot_id, _ in world.placements_of(r, loc)}
    return kinds == GS_KINDS


def pair_kind(world, cid):
    """the kind of check a progressive pair is placed on (one of PAIR_KINDS); stops the build for any other
    kind, or when the check's placements are not all of one kind"""
    r, name, loc = find_check(world, cid)
    kinds = {world.checks[scene][spot_id]['kind'] for scene, spot_id, _ in world.placements_of(r, loc)}
    if len(kinds) != 1 or not kinds <= set(PAIR_KINDS):
        raise SystemExit('%s: a progressive pair (First>Second) can only be put in a chest, on a freestanding '
                         'item, or on a rock, a bush or a pot (this check: %s)'
                         % (cid, ', '.join(sorted(kinds)) or 'an event, no map placement'))
    return kinds.pop()


def turn_spacing(world, turning):
    """stops the build when two turning items of one family lie within TURN_MIN_DISTANCE of each other;
    turning: {check id: family}. Returns [(check id, check id, metres)] for the pairs of one family and scene"""
    spots = []
    for cid, family in sorted(turning.items()):
        r, name, loc = find_check(world, cid)
        for scene, spot_id in world.spots_of(r, loc):
            pos = world.checks[scene][spot_id].get('pos')
            if pos is None:
                raise SystemExit('%s: no position in the data for %s: the distance to the other items of its '
                                 'family cannot be checked' % (cid, spot_id))
            spots.append((cid, family, scene, pos))
    out = []
    for i, (cid, family, scene, pos) in enumerate(spots):
        for cid2, family2, scene2, pos2 in spots[i + 1:]:
            if family2 != family or scene2 != scene or cid2 == cid:
                continue
            d = sum((a - b) ** 2 for a, b in zip(pos, pos2)) ** 0.5
            if d < TURN_MIN_DISTANCE:
                raise SystemExit('%s and %s: two items of one progressive family %.1f m apart (at least %.1f m: '
                                 'Link could touch both at once)' % (cid, cid2, d, TURN_MIN_DISTANCE))
            out.append((cid, cid2, d))
    return out


def pair_check(pair, in_chest=lambda item: item):
    """(Drop__CheckActor, Drop__DropActor_Substitute) of a checking chest holding a progressive pair (or the
    first two levels of a three-level family): it looks for First under the item's own name and holds Second as
    a chest gives it (in_chest), as it holds First (its Drop__DropActor)"""
    return pair[0], in_chest(pair[1])


# name -> (BYML file, path of keys to the entry to remove, value it must have now)
FILE_FIXES = {
    'skippable_opening': (
        'Event/EventSetting/EventSettingComponentList/Dm_Kokiri_0000.engine__event__EventSettingComponentList.bgyml',
        ['Components', 'SkipSetting'],
        '?Event/EventSetting/EventSettingComponent/SkipSetting/DisableSkip.engine__event__SkipSetting.bgyml'),
}
LAUNCHER = r"""@echo off
rem NX2-ZOOTR test launcher (made by tools/build_mod.py). Starts Longshot with the mods in
rem %(mods)s and saves in %(user)s:
rem your normal saves and other mod folders are not touched, and nothing is written in the Longshot folder.
set "LONGSHOT=%(longshot)s"
set "EXE=%%LONGSHOT%%\bin\longshot.exe"
if not exist "%%EXE%%" set "EXE=%%LONGSHOT%%\longshot.exe"
if not exist "%%EXE%%" (
  echo Longshot not found in %%LONGSHOT%%
  pause
  exit /b 1
)
if not exist "%(user)s" mkdir "%(user)s"
set "HOS_MODS=%(mods)s"
cd /d "%%LONGSHOT%%"
start "" "%%EXE%%" --user "%(user)s"
"""


def find_check(world, cid):
    """a check by its permanent ID, or by its name for areas that have no IDs yet"""
    for r in world.regions.values():
        for name, loc in r.locations.items():
            if loc.get('id') == cid:
                return r, name, loc
    for r in world.regions.values():
        for name, loc in r.locations.items():
            if name == cid:
                if loc.get('id'):
                    raise SystemExit('%r has a permanent ID: use %s' % (name, loc['id']))
                return r, name, loc
    raise SystemExit('unknown check ID or name %s' % cid)


def _right_actor(kind, actor):
    if kind == 'chest':
        return actor.startswith('Obj_TBox') and not actor.startswith('Obj_TBoxPedestal')
    if kind == 'pot':
        return actor.startswith('Obj_Pot')
    if kind == 'shop':
        return actor.startswith('Shop_')
    if kind == 'rock':
        return actor.startswith('Obj_LiftRock')
    if kind == 'bush':
        return actor.startswith('Obj_Plant_Grass')
    return True                                       # freestanding: the actor is the item


def plan(world, assignments, on_ground=lambda item: item, in_chest=lambda item: item,
         on_shelf=lambda item, shelf_actor: item, gs_drop=lambda item: item, once_drop=None):
    """{map file path in romfs: {placement hash: (check id, new item, old item, kind)}}.
    on_ground(item): the actor to use where the item lies on the ground (freestanding items, pot drops);
    in_chest(item): the actor a chest gives (and shows held up); on_shelf(item, actor now on the shelf): the
    shelf actor that sells the item; gs_drop(item): the actor a Gold Skulltula drops; once_drop(item): the
    actor a rock, a bush or a pot drops once (once_items.KINDS; without it: as on_ground)"""
    files = {}
    for cid, item_given in assignments:
        r, name, loc = find_check(world, cid)
        sps = world.spots_of(r, loc)
        if not sps and (loc.get('gift') or loc.get('song') or loc.get('cutscene')):
            continue                                  # an event: plan_gifts
        if not sps:
            raise SystemExit('%s has no map placement (an event): not supported yet' % cid)
        for scene, spot_id, p in world.placements_of(r, loc):
            spot = world.checks[scene][spot_id]
            if spot['kind'] not in SUPPORTED:
                raise SystemExit('%s is a %s: only %s supported yet' % (cid, spot['kind'], ', '.join(sorted(SUPPORTED))))
            if spot['kind'] == 'skulltula':
                item = gs_drop(item_given)
            elif spot['kind'] in once_items.KINDS and once_drop is not None:
                item = once_drop(item_given)
            elif spot['kind'] in DROP_ON_GROUND:
                item = on_ground(item_given)
            elif spot['kind'] == 'chest':
                item = in_chest(item_given)
            elif spot['kind'] == 'shop':
                item = on_shelf(item_given, p['actor'])
            else:
                item = item_given
            if spot['kind'] == 'scrub':
                continue                              # plan_scrubs
            if not _right_actor(spot['kind'], p['actor']):
                raise SystemExit('%s: placement %s is a %s, not a %s' % (cid, p['hash'], p['actor'], spot['kind']))
            old = 'Shop_' + spot['item'] if spot['kind'] == 'shop' else spot['item']   # shelf data drops 'Shop_'
            for fn in p['files']:
                files.setdefault('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), {})[p['hash']] = \
                    (cid, item, old, spot['kind'])
    return files


GIFT_FLOW = 'Dm_SY_GetInEvent'                    # the shared flow most gifts hand their item over with
# Dm_SY_GetInEvent shows the item in Link's hands: it makes the item's actor (Player_Event.
# EventCreateShowItemFromActorFileName) and plays its animation command Rotate_GetDemo, waiting for the end
# (EventIgnitionShowItem). An actor without that command (ocarinas, songs, the small bags, stones, medallions:
# ground_items.can_hold_up) never ends it: the Fairy Ocarina froze the game there, as the seed bag did from a
# scrub (seen in game). Such an item is given the way the game's own cutscenes give ocarinas and songs: the
# "You got ..." window and the item, nothing held up (GetPouchContent, as song_skip; every event that may run
# Dm_SY_GetInEvent may also run GetPouchContent: direct_get_allowed).
DIRECT_GET = ('GetPouchContent', 'GetPouchContentByActorName')
EVENT_INFO = 'RSDB/GameAnalyzedEventInfo.Product.111.rstbl.byml'
# After changing Link's inventory behind his back (the Dream world's boss fights), the game's own flows wait one
# frame, run UISystemActor.EventTriggerSyncPlayerEquipmentAndPouch and wait for Link's equipment
# (Player_Event.EventWaitCreationFinishedEquipment): Npc_Dream, DreamBossStage, SubEvent_AllBossBattle. The
# ocarina in Link's hands is equipment: one added to the inventory by our own get was only playable after a
# reload (seen in game with the chest and pot versions). The same three steps follow an ocarina we give in a
# flow (items whose PouchSpecialDeal is Ocarina), copied from SubEvent_AllBossBattle with their actors.
SYNC_FLOW = 'Event/EventFlow/SubEvent_AllBossBattle.bfevfl'
SYNC_ACTION = 'EventTriggerSyncPlayerEquipmentAndPouch'
SYNC_DEAL = 'Ocarina'


def _action_name(fc, e):
    return fc.actors[e.actor].actions[e.action] if e.type == 'action' else None


def sync_template(fc):
    """the three steps (one frame's wait, sync, wait for the equipment) as SubEvent_AllBossBattle has them:
    [(actor, action name, parameters)]"""
    for i, e in enumerate(fc.events):
        if _action_name(fc, e) != SYNC_ACTION or e.next is None:
            continue
        after = fc.events[e.next]
        before = [b for b in fc.events if b.next == i and _action_name(fc, b) == 'EventWait'
                  and isinstance(b.params, dict) and b.params.get('Frames') == 1]
        if before and _action_name(fc, after) == 'EventWaitCreationFinishedEquipment':
            return [(fc.actors[x.actor], _action_name(fc, x), x.params) for x in (before[0], e, after)]
    raise SystemExit('%s: wait, %s, wait for the equipment not found as expected (game files differ from what '
                     'this was made for)' % (SYNC_FLOW, SYNC_ACTION))


def flow_copy_actor(fc, actor):
    """index in `fc` of the actor with this name (and no secondary name); added as the other flow has it when
    `fc` has none"""
    for i, a in enumerate(fc.actors):
        if a.name == actor.name and not a.secondary:
            return i
    if actor.secondary or actor.argument or actor.entry_point is not None:
        raise SystemExit('actor %s of the flow copied from is not a plain one' % actor.name)
    return fc.add_actor(actor.name, params=evfl.Params(actor.params) if actor.params is not None else None,
                        cut=actor.cut)


def sync_steps(fc, template, next=None):
    """adds the sync steps (sync_template) in front of event `next`; returns the first one's index"""
    for actor, action, params in reversed(template):
        next = fc.add_action(flow_copy_actor(fc, actor), action,
                             evfl.Params(params) if params is not None else None, next=next)
    return next


# An ocarina from a chest (to test in game). A chest gives its item with the same inventory step as the game's
# own ocarina cutscenes, but it hands that step the held-up version (Item_NX2_Ocarina_*): the inventory gets
# the ocarina, Link's own ocarina (equipment) is only made at the next map load (in game 2026-11-19;
# out/RESEARCH_ocarina_chest.md). The shared chest flows are not touched. A chest that holds an ocarina gets an
# opening event of our own instead (its map setting GetEventName), the way the game itself wraps 36 chests:
# SubEvent_GetIceArrow_OpenTBox is a flow of one entry point: Player_Event.EventTriggerParticipateEvent, then
# EventSystemActor.EventTransition {EventName: Dm_SY_Treasurebox, IsWaitEnd: True, ...}, then its own steps.
# Ours: the same two steps with the chest's usual event as EventName, then the three sync steps above. One
# event (one entry point of one new flow file, two table rows) per usual event used:
#   Event/EventFlow/NX2_TBoxSync.bfevfl                  entry point NX2_TBoxSync_<usual event>
#   RSDB/EventSetting            row NX2_TBoxSync_<usual event>: the flow file and the entry point
#   RSDB/GameAnalyzedEventInfo   row NX2_TBoxSync_<usual event>: ChildEventList [<usual event>]
# both rows copied from SubEvent_GetIceArrow_OpenTBox's. A chest's usual event is its GetEventName, else the
# default of its actor's blackboard (chest_usual_event). A checking chest (a progressive pair) runs the event
# whichever level it gives: the sync then also follows the other level (it only matches Link's equipment to
# the inventory).
TBOX_SYNC_FLOW = 'NX2_TBoxSync'
TBOX_SYNC_LIKE = 'SubEvent_GetIceArrow_OpenTBox'       # the game's event ours are copies of
TBOX_SYNC_LIKE_FLOW = 'SubEvent_GetIceArrow'           # its flow file
TBOX_SYNC_JOIN = ('Player_Event', 'EventTriggerParticipateEvent')
TBOX_SYNC_RUN = ('EventSystemActor', 'EventTransition')
TBOX_EVENT_KEY = 'GetEventName'
EVENT_SETTING = 'RSDB/EventSetting.Product.111.rstbl.byml'


def flow_path(name):
    return 'Event/EventFlow/%s.bfevfl' % name


def tbox_sync_event(usual):
    """the name of our opening event (and of its entry point) around the chest's usual event"""
    return '%s_%s' % (TBOX_SYNC_FLOW, usual)


def chest_usual_event(read, gyaml):
    """the opening event a chest actor runs when its map placement names none: the GetEventName of its
    blackboard (the first table that has it, the actor's own before those it inherits). read(path) -> file"""
    try:
        files = sarc.Sarc.read(read(ground_items.pack_path(gyaml))).files
    except FileNotFoundError:
        raise SystemExit('%s: no such chest actor in the game: its usual opening event is not known' % gyaml)
    ref = ground_items.resolved_components(files, gyaml).get('BlackboardRef')
    info = ground_items._ref_path(ref) if ref else None
    while info and info in files:
        root = byml.loads(files[info]).root
        for t in root.get('BlackboardParamTables', []):
            table = ground_items._parent_path({'$parent': str(t)})
            if table not in files:
                continue
            for x in byml.loads(files[table]).root.get('BlackboardParamStringArray', []):
                if x.get('BBKey') == TBOX_EVENT_KEY and x.get('InitValConverted'):
                    return str(x['InitValConverted'])
        info = ground_items._parent_path(root)
    raise SystemExit('%s: no %s in its blackboard: its usual opening event is not known' % (gyaml, TBOX_EVENT_KEY))


def tbox_sync_template(fc):
    """the two steps the game's own wrapper starts with (TBOX_SYNC_LIKE): Link joins the event, then the chest's
    usual event is run and waited for: [(actor, action name, parameters)]"""
    start = {p.name: p.main for p in fc.entry_points}.get(TBOX_SYNC_LIKE)
    join = fc.events[start] if start is not None else None
    run = fc.events[join.next] if join is not None and join.next is not None else None
    steps = [(fc.actors[e.actor], _action_name(fc, e), e.params) for e in (join, run)
             if e is not None and e.type == 'action']
    if [(a.name, n) for a, n, _ in steps] != [TBOX_SYNC_JOIN, TBOX_SYNC_RUN] or steps[0][2] is not None \
            or not isinstance(steps[1][2], dict) or steps[1][2].get('IsWaitEnd') is not True \
            or not isinstance(steps[1][2].get('EventName'), str):
        raise SystemExit('%s: does not start by joining Link and running a chest event as expected (game files '
                         'differ from what this was made for)' % TBOX_SYNC_LIKE)
    return steps


def tbox_sync_flow(template, sync, usuals, version):
    """our flow: for each usual event one entry point: join, run the usual event and wait for its end
    (`template`: tbox_sync_template), then the sync steps (`sync`: sync_template)"""
    fc = evfl.Flowchart(TBOX_SYNC_FLOW)
    ef = evfl.EventFlow(TBOX_SYNC_FLOW, [fc])
    ef.version = version
    (join_actor, join, _), (run_actor, run, run_params) = template
    for usual in sorted(usuals):
        nxt = sync_steps(fc, sync)
        params = evfl.Params(run_params)
        params['EventName'] = usual
        nxt = fc.add_action(flow_copy_actor(fc, run_actor), run, params, next=nxt)
        nxt = fc.add_action(flow_copy_actor(fc, join_actor), join, None, next=nxt)
        fc.add_entry_point(tbox_sync_event(usual), nxt)
    return ef


# A dungeon's key in a chest (tools/dungeon_keys.py): the same kind of opening event of our own, with one step
# after the chest's usual event: GameDataActor.EventTriggerAddOrSubGameDataInt adds 1 to the dungeon's key count
# (DungeonInfo.<dungeon>.SmallKeyNum), as the treasure chest game's flow adds to its own key count
# (MiniGame_SequentialChoiceTreasure: MiniGame_SmallKeyNum + 1). One event per (usual event, dungeon):
#   Event/EventFlow/NX2_TBoxKey.bfevfl                   entry point NX2_TBoxKey_<dungeon>_<usual event>
TBOX_KEY_FLOW = 'NX2_TBoxKey'
KEY_ADD_FLOW = 'Event/EventFlow/MiniGame_SequentialChoiceTreasure.bfevfl'
KEY_ADD = ('GameDataActor', 'EventTriggerAddOrSubGameDataInt')


def tbox_key_event(usual, dungeon):
    return '%s_%s_%s' % (TBOX_KEY_FLOW, dungeon, usual)


def key_add_template(fc):
    """the game's own "add 1 to a saved number" step: (actor, action name, parameters)"""
    for e in fc.events:
        if e.type == 'action' and fc.actors[e.actor].name == KEY_ADD[0] and _action_name(fc, e) == KEY_ADD[1] \
                and isinstance(e.params, dict) and sorted(e.params) == ['GameDataName', 'Index', 'Value'] \
                and e.params['Value'] == 1 and e.params['Index'] == -1 and not fc.actors[e.actor].secondary:
            return fc.actors[e.actor], KEY_ADD[1], e.params
    raise SystemExit('%s: no step that adds 1 to a saved number found as expected (game files differ from what '
                     'this was made for)' % KEY_ADD_FLOW)


def key_add_step(add, dungeon):
    actor, action, params = add
    p = evfl.Params(params)
    p['GameDataName'] = dungeon_keys.flag(dungeon)
    return actor, action, p


def tbox_key_flow(template, add, events, version):
    """our flow: for each (usual event, dungeon) one entry point: join, run the usual event and wait for its
    end (`template`: tbox_sync_template), then one key more for the dungeon (`add`: key_add_template)"""
    fc = evfl.Flowchart(TBOX_KEY_FLOW)
    ef = evfl.EventFlow(TBOX_KEY_FLOW, [fc])
    ef.version = version
    (join_actor, join, _), (run_actor, run, run_params) = template
    for (usual, dungeon), name in sorted(events.items()):
        nxt = sync_steps(fc, [key_add_step(add, dungeon)])
        params = evfl.Params(run_params)
        params['EventName'] = usual
        nxt = fc.add_action(flow_copy_actor(fc, run_actor), run, params, next=nxt)
        nxt = fc.add_action(flow_copy_actor(fc, join_actor), join, None, next=nxt)
        fc.add_entry_point(name, nxt)
    return ef


def tbox_key_steps(template, add, usual, dungeon):
    """what an entry point of our flow must read back as (tbox_sync_read)"""
    (join_actor, join, _), (run_actor, run, run_params) = template
    actor, action, params = key_add_step(add, dungeon)
    return [(join_actor.name, join, None), (run_actor.name, run, dict(run_params, EventName=usual)),
            (actor.name, action, dict(params))]


def tbox_sync_read(data):
    """{entry point: [(actor, action, parameters)]} of our flow as written: each entry point's steps in order"""
    fc = evfl.loads(data).flowchart
    out = {}
    for p in fc.entry_points:
        steps, i = [], p.main
        while i is not None:
            e = fc.events[i]
            if e.type != 'action' or len(steps) > len(fc.events):
                raise SystemExit('read-back: %s: %s is not a plain line of steps' % (TBOX_SYNC_FLOW, p.name))
            steps.append((fc.actors[e.actor].name, _action_name(fc, e),
                          dict(e.params) if isinstance(e.params, dict) else e.params))
            i = e.next
        out[p.name] = steps
    return out


def tbox_sync_steps(template, sync, usual):
    """what an entry point of our flow must read back as (tbox_sync_read) for this usual event"""
    (join_actor, join, _), (run_actor, run, run_params) = template
    return [(join_actor.name, join, None), (run_actor.name, run, dict(run_params, EventName=usual))] \
        + [(a.name, n, dict(p) if isinstance(p, dict) else p) for a, n, p in sync]


def tbox_sync_rows(settings, infos, usuals, events=None, flow_name=None):
    """the two table rows of each of our events, copied from the game's wrapper's (TBOX_SYNC_LIKE):
    {'EventSetting': [rows], 'GameAnalyzedEventInfo': [rows]}. The usual event must be an event that runs no
    other event itself (no ChildEventList: the plain chest events)."""
    setting = {r['__RowId']: r for r in settings}
    info = {r['__RowId']: r for r in infos}
    like_s, like_i = setting.get(TBOX_SYNC_LIKE), info.get(TBOX_SYNC_LIKE)
    flow = lambda name: 'Work/Event/EventFlow/%s.evfc' % name   # noqa: E731
    if like_s is None or like_i is None or like_s.get('EntryPointName') != TBOX_SYNC_LIKE \
            or like_s.get('FlowchartFileName') != flow(TBOX_SYNC_LIKE_FLOW) \
            or not isinstance(like_i.get('ChildEventList'), list) or len(like_i['ChildEventList']) != 1:
        raise SystemExit('%s: its rows in EventSetting and GameAnalyzedEventInfo are not as expected (game files '
                         'differ from what this was made for)' % TBOX_SYNC_LIKE)
    rows = {'EventSetting': [], 'GameAnalyzedEventInfo': []}
    # events: [(usual event, the name of ours around it)] of another flow of ours (flow_name: a dungeon's keys)
    for usual, name in (events if events is not None else [(u, tbox_sync_event(u)) for u in sorted(usuals)]):
        if usual not in setting or usual not in info:
            raise SystemExit('%s: not an event of the game (no row in EventSetting or GameAnalyzedEventInfo)' % usual)
        if info[usual].get('ChildEventList'):
            raise SystemExit('%s: runs other events itself (%s): an opening event of our own around it is not '
                             'supported yet' % (usual, ', '.join(str(x) for x in info[usual]['ChildEventList'])))
        if name in setting or name in info:
            raise SystemExit('%s already exists in the game' % name)
        s = type(like_s)(like_s)
        s['__RowId'] = s['EntryPointName'] = name
        s['FlowchartFileName'] = flow(flow_name or TBOX_SYNC_FLOW)
        i = type(like_i)(like_i)
        i['__RowId'] = name
        i['ChildEventList'] = type(like_i['ChildEventList'])([usual])
        i.pop('SubFlowList', None)                      # ours runs no other flow file
        rows['EventSetting'].append(s)
        rows['GameAnalyzedEventInfo'].append(i)
    return rows


def direct_get_allowed(rows):
    """RSDB/GameAnalyzedEventInfo lists for each event the other flow files it may run (SubFlowList). A flow
    not in an event's list didn't run (Dm_SY_GetInEvent called from a song cutscene gave nothing: seen in game;
    Dm_MelodyGet_Saria lists GetPouchContent, not Dm_SY_GetInEvent). Dm_SY_GetInEvent itself runs
    GetPouchContent, so every event listing the one must list the other: checked here."""
    listing = [r for r in rows if GIFT_FLOW in [str(x) for x in r.get('SubFlowList', [])]]
    bad = [r['__RowId'] for r in listing if DIRECT_GET[0] not in [str(x) for x in r['SubFlowList']]]
    if not listing or bad:
        raise SystemExit('%s: %d events list %s; without %s: %s (game files differ from what this was made for)'
                         % (EVENT_INFO, len(listing), GIFT_FLOW, DIRECT_GET[0], ', '.join(bad[:5]) or '-'))


def plan_gifts(world, assignments):
    """{flow path in romfs: {event name: (check id, new item, old item)}} for the gifts among the assignments.
    A gift's data: "gift": {"flow": flow name, "event": the event calling Dm_SY_GetInEvent, "item": what it gives}"""
    flows = {}
    for cid, item in assignments:
        r, name, loc = find_check(world, cid)
        if world.spots_of(r, loc):
            continue
        if loc.get('song'):
            continue                                  # plan_songs
        if loc.get('cutscene'):
            continue                                  # plan_cutscene_gifts
        g = loc.get('gift')
        if not g:
            raise SystemExit('%s has no map placement (an event) and no "gift" data: not supported yet' % cid)
        events = flows.setdefault('Event/EventFlow/%s.bfevfl' % g['flow'], {})
        if g['event'] in events:
            raise SystemExit('%s: %s %s is also %s' % (cid, g['flow'], g['event'], events[g['event']][0]))
        events[g['event']] = (cid, item, g['item'])
    return flows


# what the song cutscenes themselves give the song with: "You got ..." window, then the item (Dm_SY_GetInEvent
# called from the cutscene gave nothing and the cutscene didn't count as played: seen in game)
SONG_GET = ('GetPouchContent', 'GetPouchContentByActorName')


def plan_songs(world, assignments):
    """{song cutscene flow path: (check id, new item, song)} for the song checks among the assignments.
    A song's data: "song": {"flow": its cutscene (Dm_MelodyGet_*), "item": the song it gives}"""
    out = {}
    for cid, item in assignments:
        r, name, loc = find_check(world, cid)
        sg = loc.get('song')
        if not sg:
            continue
        path = 'Event/EventFlow/%s.bfevfl' % sg['flow']
        if path in out:
            raise SystemExit('%s: %s is also %s' % (cid, sg['flow'], out[path][0]))
        out[path] = (cid, item, sg['item'])
    return out


def song_skip(fc, cid, item, song, sync=None, levels=None, template=None, asked=None):
    """the song cutscene (Dm_MelodyGet_*) is still started as before, so the game records it as played (that
    is what keeps its trigger from coming back, e.g. SacredForestMeadow_Child_Prefab_bbc3: "Dm_MelodyGet_Saria"
    not played), but its first entry point now only fades in, hands over the item the way the cutscene hands
    over the song (GetPouchContent<GetPouchContentByActorName>: "You got ..." window, then the item; plus what the
    item needs, SCRUB_COMPANIONS) and ends: no lesson, no song. sync: {item: the sync steps (sync_template) to run
    after its get}, for an ocarina (a list alone: for `item`).
    levels: a family (First, Second[, Third]; `item` is First): one get per level, with the game's inventory
    questions in front of them (level_switch; template: gift_pair_template, asked: the name the inventory knows
    an item by), as a gift with a family asks them. Returns lines saying what was changed."""
    levels = tuple(levels or (item,))
    if levels[0] != item:
        raise SystemExit('%s: the family %s does not start with %s' % (cid, '>'.join(levels), item))
    if not isinstance(sync, dict):
        sync = {item: sync} if sync else {}
    gives = [e for e in fc.events if e.type == 'subflow' and e.flowchart == 'GetPouchContent'
             and isinstance(e.params, dict) and e.params.get('ActorName') == song]
    if len(gives) != 1:
        raise SystemExit('%s: %d events give %s in the cutscene, expected 1' % (cid, len(gives), song))
    ep = next((p for p in fc.entry_points if p.name == 'EntryPoint0'), None)
    if ep is None:
        raise SystemExit('%s: the cutscene has no EntryPoint0' % cid)
    fade = next((e for e in fc.events if e.type == 'action'
                 and fc.actors[e.actor].actions[e.action] == 'EventEventFadeIn'), None)
    if fade is None:
        raise SystemExit('%s: no fade-in found in the cutscene' % cid)
    params = evfl.Params(fade.params)
    params['IsWaitEnd'] = True
    gets = []
    for k, level in enumerate(levels):
        if k and SCRUB_COMPANIONS.get(level):
            raise SystemExit('%s: %s: a later level that needs another item given with it is not supported on a '
                             'song' % (cid, '>'.join(levels)))
        nxt = sync_steps(fc, sync[level]) if sync.get(level) else None
        for companion in (reversed(SCRUB_COMPANIONS.get(level, [])) if k == 0 else ()):
            # the song cutscenes have no PouchSystemActor of their own (Dm_MelodyGet_Saria): it is added as the
            # Deku Theater's flow has it (template), as gift_pair_edit adds it (found 2026-11-23: a slingshot
            # alone on a song stopped the build with "no actor 'PouchSystemActor'")
            if template is None:
                raise SystemExit('%s: %s comes with %s: the song needs the PouchSystemActor (template)'
                                 % (cid, companion, level))
            nxt = fc.add_action(flow_copy_actor(fc, template[0]), CUTSCENE_ADD[1],
                                evfl.Params(Num=1, Actor=companion, IsGetEvent=False,
                                            IsSetMessageTargetActorName=False, IsEquipDIrect=False), next=nxt)
        gets.append(fc.add_subflow(SONG_GET[0], SONG_GET[1], evfl.Params(ActorName=level), next=nxt))
    if len(levels) > 1 and template is None:
        raise SystemExit('%s: a family on a song needs the game\'s inventory question (template)' % cid)
    top, questions = level_switch(fc, levels, gets, template, asked or (lambda x: x)) if len(levels) > 1 \
        else (gets[0], [])
    first = fc.add_action(fade.actor, 'EventEventFadeIn', params, next=top)
    was = fc.events[ep.main].name
    ep.main = first
    fc.update_entry_points()
    said = ['%-18s cutscene starts with the get of %s instead of the song lesson (%s; was %s)'
            % (cid, item if len(levels) == 1 else ' or '.join(levels), fc.events[first].name, was)]
    for k, q in enumerate(questions, 1):
        said.append('%-18s   asks %s (%s.%s %s): yes -> %s gives %s, no -> %s'
                    % (cid, fc.events[q].name, GIFT_PAIR_ACTOR, GIFT_PAIR_QUERY, dict(fc.events[q].params),
                       fc.events[gets[k]].name, levels[k], fc.events[dict(fc.events[q].cases)[template[3]]].name))
    return said


def song_skip_check(orig, back, cid, levels, sync, template=None, asked=None):
    """read-back of song_skip: every event, actor entry point of the original cutscene is as it was but for
    EntryPoint0's start (and the entry points' lists of calls); the new start fades in, then for every number of
    levels Link may own the game's questions lead to the get of the next level (all owned: the last again), which
    leads on to its companions (first level), its sync steps (an ocarina) and the end. Stops the build otherwise."""
    def bad(what):
        raise SystemExit('read-back: %s: %s' % (cid, what))

    asked = asked or (lambda x: x)
    n = len(orig.events)
    if len(back.events) < n or len(back.actors) < len(orig.actors):
        bad('events or actors are missing')
    for o, e in zip(orig.events, back.events):
        if vars(o) != vars(e):
            bad('event %s differs from the original' % o.name)
    for a, b in zip(orig.actors, back.actors):
        va, vb = dict(vars(a)), dict(vars(b))
        if vb['actions'][:len(va['actions'])] != va['actions'] or vb['queries'][:len(va['queries'])] != va['queries']:
            bad('actor %s lost an action or a query' % a.name)
        va.pop('actions'), va.pop('queries'), vb.pop('actions'), vb.pop('queries')
        if va != vb:
            bad('actor %s differs from the original' % a.name)
    if [p.name for p in orig.entry_points] != [p.name for p in back.entry_points]:
        bad('entry points differ')
    for o, p in zip(orig.entry_points, back.entry_points):
        if p.name != 'EntryPoint0' and p.main != o.main:
            bad('entry point %s starts elsewhere' % p.name)
    ep = next(p for p in back.entry_points if p.name == 'EntryPoint0')
    fade = back.events[ep.main]
    if ep.main < n or fade.type != 'action' or back.actors[fade.actor].actions[fade.action] != 'EventEventFadeIn':
        bad('EntryPoint0 does not start with a new fade-in')
    if len(levels) > 1 and template is None:
        bad('no question template for a family')
    for r in range(len(levels) + 1):
        owned = {asked(x) for x in levels[:r]}
        i = level_reached(back, fade.next, owned, template) if template else fade.next
        want = levels[min(r, len(levels) - 1)]
        g = back.events[i]
        if i < n or g.type != 'subflow' or (g.flowchart, g.entry) != SONG_GET or dict(g.params) != {'ActorName': want}:
            bad('owning %s, the cutscene does not give %s' % (', '.join(levels[:r]) or 'nothing', want))
        steps = [(CUTSCENE_ADD[0], CUTSCENE_ADD[1], {'Num': 1, 'Actor': c, 'IsGetEvent': False,
                                                     'IsSetMessageTargetActorName': False, 'IsEquipDIrect': False})
                 for c in (SCRUB_COMPANIONS.get(want, []) if want == levels[0] else [])]
        steps += [(a.name, act, dict(p) if p is not None else None) for a, act, p in (sync.get(want) or [])]
        j = g.next
        for actor, action, params in steps:
            x = back.events[j] if j is not None else None
            if x is None or j < n or x.type != 'action' or back.actors[x.actor].name != actor \
                    or back.actors[x.actor].actions[x.action] != action \
                    or (dict(x.params) if x.params is not None else None) != params:
                bad('after the get of %s: not %s.%s as intended' % (want, actor, action))
            j = x.next
        if j is not None:
            bad('after the get of %s the cutscene does not end' % want)


def gift_edit(fc, events, direct=(), sync=None):
    """set the item of each gift event (a call of Dm_SY_GetInEvent). An item in `direct` (Link can't hold it up
    in that event: ground_items.can_hold_up) is given by a call of GetPouchContent<GetPouchContentByActorName>
    in its place (the "You got ..." window and the item, as the game's cutscenes give ocarinas and songs);
    sync {item: sync steps (sync_template)}: steps to run after it (an ocarina). Returns (lines saying what was
    changed, {event name: (flow file called, entry point, parameters, name of the next event)} as intended,
    names of the new events)."""
    said, want = [], {}
    first_new = len(fc.events)
    by_name = {e.name: e for e in fc.events}
    for ev, (cid, item, old) in sorted(events.items()):
        e = by_name.get(ev)
        if e is None:
            raise SystemExit('%s: event %s not in the flow' % (cid, ev))
        if e.type != 'subflow' or e.flowchart != GIFT_FLOW or not isinstance(e.params, dict):
            raise SystemExit('%s: event %s is not a call of %s' % (cid, ev, GIFT_FLOW))
        if e.params.get('ActorName') != old:
            raise SystemExit('%s: event %s gives %r, the data says %s' % (cid, ev, e.params.get('ActorName'), old))
        if item not in direct:
            e.params['ActorName'] = item
            said.append('%-18s %s: %s -> %s' % (cid, ev, old, item))
        else:
            was = '%s<%s>' % (e.flowchart, e.entry)
            e.flowchart, e.entry = DIRECT_GET
            e.params = evfl.Params(ActorName=item)
            steps = (sync or {}).get(item)
            if steps:
                e.next = sync_steps(fc, steps, e.next)
            said.append('%-18s %s: %s -> %s, given with the get window (%s<%s> instead of %s: Link can\'t hold '
                        'it up)%s' % (cid, ev, old, item, DIRECT_GET[0], DIRECT_GET[1], was,
                                      ', then Link\'s equipment is brought in line (%s)' % fc.events[e.next].name
                                      if steps else ''))
        want[ev] = (e.flowchart, e.entry, dict(e.params), None if e.next is None else fc.events[e.next].name)
    return said, want, [x.name for x in fc.events[first_new:]]


# Gifts a cutscene gives by itself (Saria's Fairy Ocarina on the bridge, Dm_Kokiri_0155): the cutscene shows the
# "You got ..." window (a call of GetPouchContent<DisplayGetByActorName>, the window alone: what the chests'
# Dm_SY_Treasurebox calls with whatever the chest holds) and adds the item with a step of its own
# (PouchSystemActor.EventTriggerAddOrRemovePouchContent, the step and parameters GetPouchContent itself adds any
# item with). Link holds the item's actor meanwhile: an actor of the cutscene, made for it and bound to his
# hand (EventTriggerModelBind). The game's cutscenes bind item actors built on Item_EventObject_Base that way
# (Item_Gauntlet_Goron, Item_ZeldaLetter, Item_Sword_Giant, Item_BulletBag_Medium...), so another item of that
# kind takes the cutscene actor's place; for anything else (a rupee, a heart: actors Link picks up by touching
# them; equipment) the cutscene keeps the actor it has, and only the window and the inventory change.
CUTSCENE_WINDOW = ('GetPouchContent', 'DisplayGetByActorName')
CUTSCENE_ADD = ('PouchSystemActor', 'EventTriggerAddOrRemovePouchContent')
CUTSCENE_BIND = 'EventTriggerModelBind'
CUTSCENE_SHOWN_KIND = 'item'                       # ground_items.kind_of: built on Item_EventObject_Base


def plan_cutscene_gifts(world, assignments):
    """{cutscene flow path: (check id, new item, the check's data)} for the cutscene gifts among the assignments.
    A cutscene gift's data: "cutscene": {"flow": the cutscene, "add": the event adding the item, "window": the
    event showing the get window, "item": what it gives (also the name of the cutscene actor Link holds)}"""
    out = {}
    for cid, item in assignments:
        r, name, loc = find_check(world, cid)
        g = loc.get('cutscene')
        if not g or world.spots_of(r, loc):
            continue
        path = 'Event/EventFlow/%s.bfevfl' % g['flow']
        if path in out:
            raise SystemExit('%s: %s is also %s' % (cid, g['flow'], out[path][0]))
        out[path] = (cid, item, g)
    return out


def cutscene_gift_edit(fc, cid, g, item, show, companions=()):
    """the cutscene gives `item` instead of g['item']: the item its add step adds and the one its get window
    names; show: the cutscene actor Link holds becomes the item's too. companions: what the item needs to be
    usable (SCRUB_COMPANIONS), added silently right after it. Nothing else of the cutscene changes.
    Returns (lines saying what was changed, names of the new events)."""
    old = g['item']
    by_name = {e.name: e for e in fc.events}
    add, win = by_name.get(g['add']), by_name.get(g['window'])
    if add is None or win is None:
        raise SystemExit('%s: event %s or %s not in the cutscene' % (cid, g['add'], g['window']))
    if add.type != 'action' or (fc.actors[add.actor].name, _action_name(fc, add)) != CUTSCENE_ADD \
            or not isinstance(add.params, dict) or add.params.get('Actor') != old or add.params.get('Num') != 1:
        raise SystemExit('%s: event %s does not add one %s' % (cid, g['add'], old))
    if win.type != 'subflow' or (win.flowchart, win.entry) != CUTSCENE_WINDOW \
            or not isinstance(win.params, dict) or win.params.get('ActorName') != old:
        raise SystemExit('%s: event %s is not the get window of %s' % (cid, g['window'], old))
    others = [e.name for e in fc.events if e is not add and e is not win and (
        (e.type == 'action' and (fc.actors[e.actor].name, _action_name(fc, e)) == CUTSCENE_ADD)
        or (e.type == 'subflow' and e.flowchart == CUTSCENE_WINDOW[0]))]
    if others:
        raise SystemExit('%s: the cutscene gives or shows more than the data says (%s)' % (cid, ', '.join(others)))
    held = [a for a in fc.actors if a.name == old]
    if len(held) != 1 or held[0].secondary or CUTSCENE_BIND not in held[0].actions:
        raise SystemExit('%s: the cutscene does not have one actor %s bound to someone' % (cid, old))
    said = []
    first_new = len(fc.events)
    add.params['Actor'] = item
    win.params['ActorName'] = item
    said.append('%-18s %s adds %s, %s names it in the get window (was %s)' % (cid, g['add'], item, g['window'], old))
    if show:
        if item != old and any(a.name == item for a in fc.actors):
            raise SystemExit('%s: the cutscene already has an actor %s' % (cid, item))
        held[0].name = item
        if item != old:
            said.append('%-18s Link holds %s in the cutscene (the cutscene actor %s renamed)' % (cid, item, old))
    else:
        said.append('%-18s Link still holds %s in the cutscene: %s is not an item actor of the kind the '
                    'game binds to a hand' % (cid, old, item))
    nxt = add.next
    for companion in reversed(list(companions)):
        nxt = fc.add_action(add.actor, CUTSCENE_ADD[1],
                            evfl.Params(Num=1, Actor=companion, IsGetEvent=False,
                                        IsSetMessageTargetActorName=False, IsEquipDIrect=False), next=nxt)
        said.append('%-18s %s comes with it (%s)' % (cid, companion, fc.events[nxt].name))
    add.next = nxt
    return said, [e.name for e in fc.events[first_new:]]


def cutscene_family_edit(fc, cid, g, levels, template, asked, companions=()):
    """a family (First, Second[, Third]) on a cutscene gift whose get window comes before its add step (Saria's
    bridge cutscene: Event77 shows the window, then a fork's branch runs Event68, the add). After
    cutscene_gift_edit has made both give First (and chained First's companions after the add), the game's
    inventory questions (level_switch) go in front of each, with a copy of the window and of the add per later
    level. A window copy leads on as the window does; an add copy leads on to what the add led on to before
    First's companions (they are First's alone). Both questions are asked before anything is added, so both get
    the same answers. Every link to the window or the add (a step, a fork's branch) goes to its first question.
    Link holds one actor in the cutscene whatever the level (cutscene_gift_edit). Returns lines saying what was
    changed."""
    by_name = {e.name: k for k, e in enumerate(fc.events)}
    win_i, add_i = by_name[g['window']], by_name[g['add']]
    if add_i not in fc.reachable(win_i) or win_i in fc.reachable(add_i):
        raise SystemExit('%s: the get window does not come before the add step: a family cannot be put here'
                         % cid)
    win, add = fc.events[win_i], fc.events[add_i]
    if win.params.get('ActorName') != levels[0] or add.params.get('Actor') != levels[0]:
        raise SystemExit('%s: the cutscene does not give %s (cutscene_gift_edit first)' % (cid, levels[0]))
    for level in levels[1:]:
        if SCRUB_COMPANIONS.get(level):
            raise SystemExit('%s: %s: a later level that needs another item given with it is not supported on a '
                             'cutscene gift' % (cid, '>'.join(levels)))
    lead = add.next                                    # past First's companions: what the add led on to
    for _ in companions:
        lead = fc.events[lead].next
    said = []
    for what, i, key, nxt in (('window', win_i, 'ActorName', win.next), ('add', add_i, 'Actor', lead)):
        e = fc.events[i]
        copies = []
        for level in levels[1:]:
            p = evfl.Params(e.params)
            p[key] = level
            if e.type == 'subflow':
                copies.append(fc.add_subflow(e.flowchart, e.entry, p, next=nxt))
            else:
                copies.append(fc.add_action(e.actor, CUTSCENE_ADD[1], p, next=nxt))
        top, questions = level_switch(fc, levels, [i] + copies, template, asked)
        moved = fc.repoint(i, top, keep=questions)
        if not moved:
            raise SystemExit('%s: nothing leads to %s' % (cid, e.name))
        said.append('%-18s %s (the %s): asks first %s; %s; %d link%s moved to the questions'
                    % (cid, e.name, what, ', then '.join('%s (has %s?)' % (fc.events[q].name, fc.events[q].params['Actor'])
                                                         for q in reversed(questions)),
                       ', '.join('%s gives %s' % (fc.events[c].name, lv) for c, lv in zip([i] + copies, levels)),
                       moved, '' if moved == 1 else 's'))
    fc.update_entry_points()
    return said


def cutscene_family_check(orig, back, cid, g, levels, template, asked, show, companions=()):
    """read-back of a family on a cutscene gift (cutscene_family_edit): no original event links to the window or
    the add any more but through one question each; for every number of levels Link may own, the questions lead
    to the window and the add of the same level (all owned: the last again); a later level's window leads on as
    the window does, its add to what the add led on to. With the questions and the later levels taken out again,
    the cutscene is what cutscene_gift_check wants for First. Stops the build otherwise."""
    def bad(what):
        raise SystemExit('read-back: %s: %s' % (cid, what))

    n = len(orig.events)
    by_name = {e.name: k for k, e in enumerate(back.events)}
    win_i, add_i = by_name[g['window']], by_name[g['add']]
    lead = orig.events[[e.name for e in orig.events].index(g['add'])].next
    tops = {}
    for what, i in (('window', win_i), ('add', add_i)):
        into = [k for k, e in enumerate(back.events[:n]) if e.next == i or i in e.forks or i in [c for _, c in e.cases]
                or e.join == i] + [p.name for p in back.entry_points if p.main == i]
        firsts = [k for k in range(n, len(back.events)) if back.events[k].type == 'switch'
                  and (any(e.next == k or k in e.forks or k in [c for _, c in e.cases] for e in back.events[:n])
                       or any(p.main == k for p in back.entry_points))]
        tops[what] = [k for k in firsts if level_reached(back, k, set(), template) == i]
        if len(tops[what]) != 1 or into:
            bad('the links to the %s do not all go to one question in front of it' % what)
    adds = set()
    for r in range(len(levels) + 1):
        owned = {asked(x) for x in levels[:r]}
        want = levels[min(r, len(levels) - 1)]
        wi = level_reached(back, tops['window'][0], owned, template)
        ai = level_reached(back, tops['add'][0], owned, template)
        w, a = back.events[wi], back.events[ai]
        if w.type != 'subflow' or (w.flowchart, w.entry) != CUTSCENE_WINDOW \
                or dict(w.params) != dict(back.events[win_i].params, ActorName=want) or w.next != back.events[win_i].next:
            bad('owning %s, the window does not name %s as intended' % (', '.join(levels[:r]) or 'nothing', want))
        if a.type != 'action' or (back.actors[a.actor].name, _action_name(back, a)) != CUTSCENE_ADD \
                or dict(a.params) != dict(back.events[add_i].params, Actor=want) \
                or (ai != add_i and a.next != lead):
            bad('owning %s, the cutscene does not add %s as intended' % (', '.join(levels[:r]) or 'nothing', want))
        if (wi == win_i) != (want == levels[0]) or (ai == add_i) != (want == levels[0]):
            bad('the first level is not given by the original window and add')
        adds.add(ai)
    # the questions and the later levels taken out again: what cutscene_gift_check wants for First
    flat = copy.deepcopy(back)
    to = {tops['window'][0]: win_i, tops['add'][0]: add_i}
    for e in flat.events[:n]:
        e.next, e.join = to.get(e.next, e.next), to.get(e.join, e.join)
        e.forks = [to.get(f, f) for f in e.forks]
        e.cases = [(v, to.get(c, c)) for v, c in e.cases]
    for p in flat.entry_points:
        p.main = to.get(p.main, p.main)
    first_new = [k for k in range(n, len(back.events)) if back.events[k].type == 'action' and k not in adds]
    if first_new != list(range(n, n + len(companions))):
        bad('the companions are not the first new events')
    flat.events = flat.events[:n + len(companions)]
    for p, o in zip(flat.entry_points, orig.entry_points):
        p.subflows = list(o.subflows)
    for a, o in zip(flat.actors, orig.actors):
        extra = a.queries[len(o.queries):]
        if a.queries[:len(o.queries)] == o.queries and set(extra) <= {GIFT_PAIR_QUERY}:
            a.queries = list(o.queries)
    flat.actors = flat.actors[:len(orig.actors)]
    cutscene_gift_check(orig, flat, cid, g, levels[0], show, [back.events[k].name for k in first_new])


def cutscene_gift_check(orig, back, cid, g, item, show, added=()):
    """read-back of a cutscene gift: against the original cutscene, only the add step's item, the window's item
    and (show) the held actor's name differ; the new events are the companions' adds, chained after the add
    step and leading on as it did. Stops the build otherwise."""
    def bad(what):
        raise SystemExit('read-back: %s: %s' % (cid, what))

    old = g['item']
    if len(back.actors) != len(orig.actors) or len(back.events) != len(orig.events) + len(added):
        bad('actors or events differ in number from what was intended')
    for a, b in zip(orig.actors, back.actors):
        va, vb = dict(vars(a)), dict(vars(b))
        if a.name == old:
            if vb['name'] != (item if show else old):
                bad('the held actor is %s' % vb['name'])
            vb['name'] = old
        if va != vb:
            bad('actor %s differs from the original' % a.name)
    if [vars(p) for p in orig.entry_points] != [vars(p) for p in back.entry_points]:
        bad('entry points differ from the original')
    chain = lead = None
    for o, e in zip(orig.events, back.events):
        vo, ve = dict(vars(o)), dict(vars(e))
        if o.name == g['add']:
            if ve['params'].get('Actor') != item:
                bad('%s adds %s' % (o.name, ve['params'].get('Actor')))
            ve['params'] = evfl.Params(ve['params'])
            ve['params']['Actor'] = old
            chain, lead = ve['next'], vo['next']
            ve['next'] = lead
        elif o.name == g['window']:
            if ve['params'].get('ActorName') != item:
                bad('%s names %s' % (o.name, ve['params'].get('ActorName')))
            ve['params'] = evfl.Params(ve['params'])
            ve['params']['ActorName'] = old
        if vo != ve:
            bad('event %s differs from the original' % o.name)
    for _ in added:
        if chain is None or chain < len(orig.events):
            bad('the companions do not follow the add step')
        e = back.events[chain]
        if e.type != 'action' or (back.actors[e.actor].name, _action_name(back, e)) != CUTSCENE_ADD:
            bad('%s is not an add step' % e.name)
        chain = e.next
    if chain != lead:
        bad('what follows the add step is not what followed it')


# Deku Scrubs. When Link talks to one, the game copies its map setting ScrubBusiness_ShopItemActorName0 into
# the game data string Scrub_Business_TempItemName_00 and runs the entry point named by its TalkEventName in
# Enemy_Scrub_Business_Common. The scrubs that sell one thing once (stick and nut upgrades) run
# SimpleShopRoot_Enemy_Scrub_Business_Pouch, which compares that string with the items it knows and calls
# SimpleShopSub_Scrub_Business_OneTime (ActorName, Price, SellerMessageId): talk, pay, held-up get, the scrub
# leaves. Each sales line there is written for one item, so a new one names the item from the string.
SCRUB_FLOW = 'Event/EventFlow/Enemy_Scrub_Business_Common.bfevfl'
SCRUB_ROOT = 'SimpleShopRoot_Enemy_Scrub_Business_Pouch'
SCRUB_SELL = 'SimpleShopSub_Scrub_Business_OneTime'
SCRUB_VAR = 'Scrub_Business_TempItemName_00'
SCRUB_SETTING = 'ScrubBusiness_ShopItemActorName0'
SCRUB_MSG_FILE = 'EventFlowMsg/Enemy_Event.msbt'
SCRUB_LABEL = 'Enemy_Scrub_Business_NX2_Item'


def _msg_tag(group, kind, params=b''):
    return (b'\x0e' + struct.pack('<HHH', group, kind, len(params)) + params).decode('utf-8', 'surrogateescape')


def _msg_name(name):
    raw = name.encode('ascii')
    return struct.pack('<H', len(raw)) + raw + b'\xff\xff'


# "Ah, the <item>! It's <price> rupees. Wanna buy it?" (English, in every language), built from the game's own
# tags: the scrub lines' start (3,0) and price (2,12), the shop's item-name tag (2,3) with the (201,15) it has
# before it (Npc_Kokiri_001_Shop_Child Shop_01), colour on/off (0,3), the pause (5,0). Confirmed in game.
SCRUB_LINE = (_msg_tag(3, 0, b'\x0f\x00\x00') + 'Ah, the ' + _msg_tag(0, 3, b'\x00\x00') + _msg_tag(201, 15)
              + _msg_tag(2, 3, _msg_name(SCRUB_VAR)) + _msg_tag(0, 3, b'\xff\xff') + "! It's "
              + _msg_tag(0, 3, b'\x00\x00') + _msg_tag(2, 12, _msg_name('SimpleShop_Price')) + ' rupees'
              + _msg_tag(0, 3, b'\xff\xff') + '.' + _msg_tag(5, 0) + ' Wanna buy it?\x00')


# what an item needs to be usable, given with it when a scrub sells it (silently, after a successful buy: held up
# alone the seed bag froze the game). The slingshot sold alone came with no seed bag: 0/0 seeds (seen in game).
SCRUB_COMPANIONS = {'Item_Range_SlingShot': ['Item_BulletBag_Small'], 'Item_Range_Bow': ['Item_Quiver_Small']}
SEED_BAG = 'Item_BulletBag_Small'
SEED_SELL = 'SimpleShopSub_Scrub_Business_Seed_Consume'
SCRUB_NOBAG_LABEL = 'Enemy_Scrub_Business_NX2_NoSeedBag'
# "Squee... On second thought, you've got nothing to carry these in!" (built like the game's refusal lines,
# e.g. Enemy_Scrub_Business_Seed_10: start (3,0) 0x11, pause (5,1))
SCRUB_NOBAG_LINE = (_msg_tag(3, 0, b'\x11\x00\x00') + 'Squee... On second thought, ' + _msg_tag(5, 1)
                    + "you've got nothing to carry these in!\x00")


def seed_bag_guard(fc):
    """the seed sales of Enemy_Scrub_Business_Common (SimpleShopSub_Scrub_Business_Seed_Consume with
    NecessaryActor Item_BulletBag_Small) sell to a slingshot without the bag ("pretty full, buy anyway?", and
    buying gave the bag: seen in game). In front of each, a new check:
        IsGet.Item_BulletBag_Small?   yes (0) -> the game's sale
                                      no  (1) -> the scrub says the new refusal line; not bought (as the game's
                                                 own "not enough rupees" refusal ends)
    Returns lines saying what was changed."""
    by = fc.events
    sales = [i for i, e in enumerate(by) if e.type == 'subflow' and e.flowchart == '' and e.entry == SEED_SELL
             and isinstance(e.params, dict) and e.params.get('NecessaryActor') == SEED_BAG]
    if not sales:
        raise SystemExit('no seed sales found in the scrub flow')
    talk = next(e for e in by if e.type == 'action' and isinstance(e.params, dict)
                and e.params.get('MessageId') == 'EventFlowMsg/Enemy_Event:Enemy_Scrub_Business_Seed_10')
    scrub = fc.actor_index(('Enemy_Scrub_Business', ''))
    said = []
    for i in sales:
        if by[i].next is not None:
            raise SystemExit('seed sale %s is not the end of its branch' % by[i].name)
        params = evfl.Params(talk.params)
        params['MessageId'] = 'EventFlowMsg/Enemy_Event:' + SCRUB_NOBAG_LABEL
        not_bought = fc.add_action('GameDataActor', 'EventTriggerSetGameDataBool',
                                   evfl.Params(GameDataName='ScrubBusiness_BuySuccess', Value=False, Index=-1))
        refuse = fc.add_action(scrub, 'EventTalk', params, next=not_bought)
        sw = fc.add_switch('GameDataActor', 'EventQueryIsGameDataBool', [(0, i), (1, refuse)],
                           evfl.Params(GameDataName='IsGet.' + SEED_BAG, Index=-1))
        if fc.repoint(i, sw, keep=(sw,)) < 1:
            raise SystemExit('nothing led to seed sale %s' % by[i].name)
        said.append('seed sale %s (%s): refused without the seed bag (new check %s)'
                    % (by[i].name, by[i].params.get('Actor'), by[sw].name))
    return said


# the small seed bag and quiver are never given alone: they come with the slingshot and the bow (a scrub selling
# the small seed bag alone froze the game, seen in game). Placed alone, they become their weapon (main), and the
# bag comes with it (a chest's slingshot brings 30 seeds by itself; scrubs add it, SCRUB_COMPANIONS).
FAMILY_ALIASES = {'Item_BulletBag_Small': 'Item_Range_SlingShot', 'Item_Quiver_Small': 'Item_Range_Bow'}
# items the game never gives as such: no map, chest or event flow of the game gives them, and they are refused
# everywhere (the small Deku Stick bag picked up from the ground froze the game, 2026-11-19). Found in the game's
# files: the first Deku Stick or Deku Nut Link gets brings its small bag by itself (PouchActorInfo: the sticks'
# and nuts' rows have IsAbleToGetBagIfGet, and SmallBagActor names the bag; the two bags' own rows are the only
# bags' without IsItemStockMaxIfGet), and their actors have no animation settings at all (they cannot be held
# up). The small wallet is in the inventory from the start (Sequence/SetPouchAndStatusForGameStart) and has no
# actor pack. (The small seed bag and quiver are never given alone either: FAMILY_ALIASES.)
NEVER_GIVEN = {
    'Item_StickBag_Small': 'the first Deku Stick Link gets brings it',
    'Item_NutBag_Small': 'the first Deku Nut Link gets brings it',
    'Item_Wallet_Small': 'Link has it from the start',
}


def never_given(assignments):
    """stops the build when an item the game never gives as such is placed (NEVER_GIVEN); assignments:
    [(check id, item or First>Second)]"""
    for cid, item in assignments:
        for x in item.split('>'):
            if x in NEVER_GIVEN:
                raise SystemExit('%s: %s cannot be placed anywhere: the game never gives it as an item (%s)'
                                 % (cid, x, NEVER_GIVEN[x]))


# Upgrade families: every level of a family is an inventory item of its own (GameData: IsGet.<name>), so a later
# level placed on its own can be taken before the earlier one, and the level is skipped (seen in game,
# 2026-11-20: Item_Scale_Gold on the ground, taken before the Silver Scale). The user's rule: a progressive
# upgrade never skips a level. So a later level is only placed as a later part of First>Second (PROGRESSIVE_PAIRS)
# or First>Second>Third (THREE_LEVEL_FAMILIES); placed alone it stops the build: skip_level_guard.
# The families are the ones declared in FAMILIES, as they are placed, so the guard and the progressive forms
# always agree: every later level of a family has a form that names it. The levels' order is the game's own
# (tests/skip_level_check.py reads it from the game's files: RSDB/PouchActorInfo, DiveDepth 6 and 9,
# OcarinaTypeValue 1 and 2, AfterExpansionMaxNum of the bags, quivers and wallets, LiftableGrade Low, Middle and
# High, MPMax 24 and 48; the hookshots by their weapons' Range, 10 and 20).
# What the game's table has below a family's first level is never placed as such, so it is no level that can be
# skipped: the small Deku Stick bag, Deku Nut bag and wallet (NEVER_GIVEN: refused everywhere) and the small
# seed bag and quiver (FAMILY_ALIASES: placed alone they become the weapon, the family's first level).
# To add a family: one row in FAMILIES.
UPGRADE_FAMILIES = tuple(FAMILIES.values())
# other names the same levels have in the item table: the inventory's twin Pouch_<x> of every Item_<x>, and these
UPGRADE_OTHER_NAMES = {
    'Armor_Child_Gauntlet_Goron': 'Item_Gauntlet_Goron', 'Armor_Adult_Gauntlet_Silver': 'Item_Gauntlet_Silver',
    'Armor_Adult_Gauntlet_Gold': 'Item_Gauntlet_Gold', 'Obj_Ocarina_Time': 'Item_Ocarina_Time',
}
PAIR_WHERE = TRIPLE_WHERE = PROGRESSIVE_WHERE
LEVEL_WORDS = ('first', 'second', 'third')


def upgrade_level(item):
    """(family, index of the level) of an item of UPGRADE_FAMILIES, under any of its names; None for any other
    item"""
    name = UPGRADE_OTHER_NAMES.get(item, 'Item_' + item[len('Pouch_'):] if item.startswith('Pouch_') else item)
    for family in UPGRADE_FAMILIES:
        if name in family:
            return family, family.index(name)
    return None


def skipped_level(item):
    """the level a check would skip when `item` is placed on its own: (family, level of the item, the level
    before it that Link might not have yet); None when the item is no later level of an upgrade family. Levels
    that are never placed (NEVER_GIVEN) cannot be skipped"""
    found = upgrade_level(item)
    if not found:
        return None
    family, level = found
    before = [x for x in family[:level] if x not in NEVER_GIVEN]
    return (family, level, before[-1]) if before else None


def progressive_form(family, level):
    """the form a level of an upgrade family can be placed with: ('First>Second' or 'First>Second>Third', where
    it can be put), or None when the builder has none for it yet"""
    name = family[level]
    for pair in sorted(PROGRESSIVE_PAIRS):
        if pair[1] == name:
            return '>'.join(pair), PAIR_WHERE
    for triple in sorted(THREE_LEVEL_FAMILIES):
        if name in triple[1:]:
            return '>'.join(triple), TRIPLE_WHERE
    return None


def skip_level_guard(assignments):
    """stops the build when a later level of an upgrade family (UPGRADE_FAMILIES) is placed on its own: Link
    could take it before the level in front of it. assignments: [(check id, item or First>Second(>Third))]; the
    progressive forms are not looked at here (only the known pairs and triples pass, further down)"""
    for cid, item in assignments:
        found = None if '>' in item else skipped_level(item)
        if not found:
            continue
        family, level, before = found
        form = progressive_form(family, level)
        if form:
            how = 'Use %s=%s (%s).' % (cid, form[0], form[1])
        else:
            how = 'The builder has no progressive form for this family yet: it cannot be placed for now.'
        raise SystemExit('%s: %s cannot be placed on its own: it is the %s level of the upgrade family %s and '
                         'could be taken before %s, skipping a level. %s'
                         % (cid, item, LEVEL_WORDS[level], ' > '.join(family), before, how))


def plan_scrubs(world, assignments):
    """[(check id, new item, [(map path, placement hash, talk event, original item)])] for the scrubs among the
    assignments (the copies of one check may differ: e.g. seeds as a child, arrows as an adult)"""
    out = []
    for cid, item in assignments:
        r, name, loc = find_check(world, cid)
        places = [(sc, sp, p) for sc, sp, p in world.placements_of(r, loc)
                  if world.checks[sc][sp]['kind'] == 'scrub']
        if not places:
            continue
        rows = []
        for sc, _, p in places:
            prm = p.get('params', {})
            if not prm.get('TalkEventName') or not prm.get(SCRUB_SETTING):
                raise SystemExit('%s: scrub %s has no %s/TalkEventName (it sells nothing set in the map): '
                                 'not supported yet' % (cid, p['hash'], SCRUB_SETTING))
            for fn in p['files']:
                rows.append(('Banc/%s/%s' % (sc, fn[:-3] if fn.endswith('.zs') else fn), p['hash'],
                             prm['TalkEventName'], prm[SCRUB_SETTING]))
        out.append((cid, item, rows))
    return out


def scrub_map_edit(data, changes):
    """{placement hash: (check id, new item, original item)}: the scrub's ScrubBusiness_ShopItemActorName0;
    read back: nothing else changes"""
    doc = byml.loads(data)
    done = set()
    for a in doc.root.get('Actors', []):
        h = str(int(a['Hash']))
        if h not in changes:
            continue
        cid, item, old = changes[h]
        dyn = a.get('Dynamic')
        if a['Gyaml'] != 'Enemy_Scrub_Business' or dyn is None or dyn.get(SCRUB_SETTING) != old:
            raise SystemExit('%s: placement %s is not a scrub selling %s' % (cid, h, old))
        dyn = type(dyn)(dyn)                          # its own copy: identical settings are shared in the file
        dyn[SCRUB_SETTING] = item
        a['Dynamic'] = dyn
        done.add(h)
    if done != set(changes):
        raise SystemExit('placements not found: %s' % ', '.join(sorted(set(changes) - done)))
    new = byml.dumps(doc)
    before = {str(int(x['Hash'])): x for x in byml.loads(data).root['Actors']}
    back = byml.loads(new).root['Actors']
    if len(back) != len(before):
        raise SystemExit('read-back: actor count changed')
    for x in back:
        h = str(int(x['Hash']))
        want = dict(before[h])
        if h in changes:
            want['Dynamic'] = dict(want['Dynamic'], **{SCRUB_SETTING: changes[h][1]})
        if x != want:
            raise SystemExit('read-back: scrub %s differs from what was intended' % h)
    return new


SCRUB_PRICE_KEYS = {SCRUB_SELL: 'ActorName', SEED_SELL: 'Actor',
                    'SimpleShopSub_Scrub_Business_Seed_Bottle': 'DisplayActor'}
SCRUB_ONE_TIME_TALK = 'Enemy_Scrub_Business_DekuStickPouch_01'   # its call of the root: the greetings to copy
# A progressive pair on a scrub (CHECK_ID=First>Second, PROGRESSIVE_PAIRS): the scrub's map setting names First,
# and the builder's own branch for First in Enemy_Scrub_Business_Common asks the inventory before the sale, the
# way the game's own upgrade scrubs do in that very flow: the stick-bag scrub's map setting is
# Item_StickBag_Medium, and its branch asks PouchSystemActor.EventQueryIsExistInPouch {Num: 1, Actor:
# Item_StickBag_Medium} (Event319): 0 (Link has it) -> the one-time sale of Item_StickBag_Large, 1 -> of
# Item_StickBag_Medium; the nut-bag scrub the same (Event323). The question is copied from there. The generic
# line names the item from Scrub_Business_TempItemName_00 (the map setting: First), and an item Link can't hold
# up is sorted out by that name too (scrub_flow_edit, point 3), so before Second's sale the name is written
# over with Second's and the flow waits, as the game's own flows do after writing a name they use
# (Enemy_Scrub_Business_Potion: EventTriggerSetGameDataString64 on Scrub_Business_TempItemName_02 and _03, a
# call that writes _00, then EventWait of 1 frame before the step that reads them; a value written is read back
# a frame or two later, seen in game 2026-11-18).
SCRUB_PAIR_QUERY = 'EventQueryIsExistInPouch'
SCRUB_NAME_WRITE = 'EventTriggerSetGameDataString64'
SCRUB_WRITE_WAIT = 2                               # frames between writing the name and the sale that uses it


def scrub_pair_kind(world, cid):
    """True for a check whose placements are all Deku Scrubs: a progressive pair on it is decided in the
    scrub's own branch of the scrub flow (scrub_flow_edit)"""
    r, name, loc = find_check(world, cid)
    kinds = {world.checks[scene][spot_id]['kind'] for scene, spot_id, _ in world.placements_of(r, loc)}
    return kinds == {'scrub'}


def scrub_pair_template(fc):
    """the game's own question as the upgrade scrubs' branches have it: (the actor's index, the query's
    parameters, the case value for "has it", the case value for "doesn't"), and the steps the game writes a
    name and waits with: (the write's parameters, the wait's actor index, the wait's parameters). Found by what
    they are"""
    ask = None
    for e in fc.events:
        if e.type != 'switch' or fc.actors[e.actor].name != GIFT_PAIR_ACTOR or fc.actors[e.actor].secondary \
                or fc.actors[e.actor].queries[e.query] != SCRUB_PAIR_QUERY or not isinstance(e.params, dict):
            continue
        sells = {v: fc.events[c] for v, c in e.cases}
        if sorted(sells) != [0, 1] or any(s.type != 'subflow' or s.flowchart != '' or s.entry != SCRUB_SELL
                                          or not isinstance(s.params, dict) for s in sells.values()):
            continue
        asked = e.params.get('Actor')
        if list(e.params) == ['Num', 'Actor'] and e.params['Num'] == 1 and isinstance(asked, str) \
                and sells[1].params.get('ActorName') == asked and sells[0].params.get('ActorName') != asked:
            ask = (e.actor, evfl.Params(e.params), 0, 1)
            break
    if ask is None:
        raise SystemExit('%s: no %s.%s switch between two one-time sales found (game files differ from what '
                         'this was made for)' % (SCRUB_FLOW, GIFT_PAIR_ACTOR, SCRUB_PAIR_QUERY))
    write = next((e for e in fc.events if e.type == 'action' and _action_name(fc, e) == SCRUB_NAME_WRITE
                  and isinstance(e.params, dict) and sorted(e.params) == ['GameDataName', 'Index', 'Value']
                  and e.params['Index'] == -1 and isinstance(e.params['Value'], str)
                  and str(e.params['GameDataName']).startswith('Scrub_Business_TempItemName_')
                  and fc.actors[e.actor].name == 'GameDataActor' and not fc.actors[e.actor].secondary), None)
    wait = next((e for e in fc.events if e.type == 'action' and _action_name(fc, e) == 'EventWait'
                 and isinstance(e.params, dict) and sorted(e.params) == ['Frames', 'IsWaitEnd']
                 and e.params['IsWaitEnd'] is True and fc.actors[e.actor].name == 'EventSystemActor'
                 and not fc.actors[e.actor].secondary), None)
    if write is None or wait is None:
        raise SystemExit('%s: no name written, or no wait, found as expected (game files differ from what this '
                         'was made for)' % SCRUB_FLOW)
    return ask, (evfl.Params(write.params), wait.actor, evfl.Params(wait.params))


def scrub_pair_read(fc, first):
    """what the flow does for a scrub whose map setting is `first`, read from the flow by following its links
    from the root: {'first', 'second' (None when the branch is a plain sale), 'ask' (the parameters of the
    question about First), 'steps' (what Second's branch does before its sale, in order: actor, action,
    parameters), 'sells' ((First's sale's parameters, Second's)), 'levels' (every level sold, lowest first),
    'chain' (every question from the one asked first to the one about First: (its parameters, the steps of its
    "has" branch, that branch's sale's parameters)), 'with' (what is added after First's sale: its
    companions)}. Raises SystemExit when the branch is not one scrub_flow_edit makes"""
    by = fc.events
    eps = {p.name: p.main for p in fc.entry_points}
    sw = next((by[i] for i in flow_reachable(fc, eps[SCRUB_ROOT]) if by[i].type == 'switch'
               and isinstance(by[i].params, dict) and by[i].params.get('GameDataName') == SCRUB_VAR
               and by[i].params.get('Value') == first), None)
    if sw is None:
        raise SystemExit('%s: no branch for %s' % (SCRUB_ROOT, first))
    e = by[dict(sw.cases)[0]]
    if e.type == 'subflow':
        return {'first': first, 'second': None, 'sells': (dict(e.params), None)}
    chain = []
    while e.type != 'subflow':
        a = fc.actors[e.actor] if e.type == 'switch' else None
        if a is None or (a.name, a.secondary or '', a.queries[e.query]) != (GIFT_PAIR_ACTOR, '', SCRUB_PAIR_QUERY) \
                or sorted(v for v, _ in e.cases) != [0, 1] or len(chain) >= 2:
            raise SystemExit('%s: the branch for %s is neither a sale nor the inventory question'
                             % (SCRUB_ROOT, first))
        cases = dict(e.cases)
        steps, k = [], by[cases[0]]
        while k.type == 'action':
            steps.append((fc.actors[k.actor].name, _action_name(fc, k), dict(k.params)))
            if k.next is None:
                raise SystemExit('%s: the branch for %s ends before a sale' % (SCRUB_ROOT, first))
            k = by[k.next]
        if k.type != 'subflow' or k.flowchart != '' or k.entry != SCRUB_SELL or k.next is not None:
            raise SystemExit('%s: the branch for %s does not end in one-time sales' % (SCRUB_ROOT, first))
        chain.append((dict(e.params), steps, dict(k.params)))
        e = by[cases[1]]
    one, comes = e, []
    if one.flowchart != '' or one.entry != SCRUB_SELL:
        raise SystemExit('%s: the branch for %s does not end in one-time sales' % (SCRUB_ROOT, first))
    if one.next is not None:                           # what First needs, added after a successful buy
        g = by[one.next]
        if g.type != 'switch' or not isinstance(g.params, dict) \
                or g.params.get('GameDataName') != 'ScrubBusiness_BuySuccess' or [v for v, _ in g.cases] != [0]:
            raise SystemExit('%s: the first sale of the branch for %s leads on to something else than its '
                             'companions' % (SCRUB_ROOT, first))
        k = by[g.cases[0][1]]
        while True:
            if k.type != 'action' or (fc.actors[k.actor].name, _action_name(fc, k)) != CUTSCENE_ADD:
                raise SystemExit('%s: the branch for %s adds its companions with other steps' % (SCRUB_ROOT, first))
            comes.append(k.params.get('Actor'))
            if k.next is None:
                break
            k = by[k.next]
    return {'first': first, 'second': chain[-1][2].get('ActorName'), 'ask': chain[-1][0], 'steps': chain[-1][1],
            'sells': (dict(one.params), chain[-1][2]), 'chain': chain, 'with': comes,
            'levels': [first] + [c[2].get('ActorName') for c in reversed(chain)]}


def scrub_pair_check(fc, first, second, third=None, asked=None):
    """read-back of a pair's or a three-level family's branch: every question asks for the level before the one
    its "has" branch sells (under the name the inventory knows it by: asked(item)); "has not" of the question
    about First sells First; each "has" branch writes its level's name where the line and the hold-up check
    read it, waits, and sells that level; the sales differ in the item only"""
    asked = asked or (lambda item: item)
    levels = [first, second] + ([third] if third else [])
    got = scrub_pair_read(fc, first)
    one = got['sells'][0]
    rest = lambda sale: {k: v for k, v in sale.items() if k != 'ActorName'}   # noqa: E731
    ok = got.get('levels') == levels and one.get('ActorName') == first \
        and got['with'] == SCRUB_COMPANIONS.get(first, [])
    for k, (ask, steps, sale) in enumerate(reversed(got.get('chain', ())), 1):
        ok = ok and k < len(levels) and ask == {'Num': 1, 'Actor': asked(levels[k - 1])} \
            and sale.get('ActorName') == levels[k] and rest(sale) == rest(one) \
            and steps == [('GameDataActor', SCRUB_NAME_WRITE,
                           {'Index': -1, 'GameDataName': SCRUB_VAR, 'Value': levels[k]}),
                          ('EventSystemActor', 'EventWait', {'Frames': SCRUB_WRITE_WAIT, 'IsWaitEnd': True})]
    if not ok:
        raise SystemExit('read-back: %s: the branch for %s is not as intended: %r'
                         % (SCRUB_FLOW, '>'.join(levels), got))
    return got


def scrub_flow_edit(fc, sales, direct=(), sync=None, pairs=None, asked=None):
    """sales: [(check id, new item, [(talk event, original item)])]. Every changed scrub sells its item once.
    direct: the items Link can't hold up (ground_items.can_hold_up); sync {item: sync steps}: see point 3.
    pairs: {check id: (first, second) or (first, second, third)} for the scrubs that hold a progressive pair or
    a three-level family (their item in `sales` is First): see point 4. asked(item): the name the inventory
    knows an item by, the one the game's flows ask about (ActorInfo: ActorName; default: the item's own).
    1. In front of the first item comparison of SimpleShopRoot_Enemy_Scrub_Business_Pouch, one branch per item:
           Scrub_Business_TempItemName_00 == item?   yes (0) -> SimpleShopSub_Scrub_Business_OneTime with the
                                                                item, the scrub's price, the generic line (and
                                                                what the item needs, SCRUB_COMPANIONS)
                                                     no  (1) -> the next branch, at the end the game's own checks
       The one-time sale ends with the scrub leaving (EventTriggerRequestDeath).
    2. A scrub that normally sells again and again (its talk doesn't run that root: seeds, arrows, potions) gets,
       at the start of its talk, the root's own first step (EventScrubBusinessWriteGameDataBancItemName: copies
       the map setting into Scrub_Business_TempItemName_00), then
           Scrub_Business_TempItemName_00 == item?   yes (0) -> the root, so the branch above
                                                     no  (1) -> the game's talk, as before
    3. The one-time sale pays and hands over inside Dm_SY_GetInEvent<GetInEvent_NotTurn_2DShop> (the price
       taken, then the item held up). For an item Link can't hold up (the seed bag froze the game there), in
       front of that call:
           Scrub_Business_TempItemName_00 == item?   yes (0) -> the price taken the same way
                                                                (EventTriggerAddGameDataIntToRupee,
                                                                EventWaitStableNumDisplay), the item given with
                                                                the get window (GetPouchContent), for an
                                                                ocarina the sync steps, then on as after the
                                                                game's call
                                                     no  (1) -> the game's call
    4. A progressive pair: the branch of point 1 for First does not sell at once but asks first, as the game's
       own upgrade scrubs do (scrub_pair_template):
           PouchSystemActor.EventQueryIsExistInPouch {Num: 1, Actor: First}
               1 (Link has no First) -> the one-time sale of First, as point 1
               0 (Link has First)    -> Scrub_Business_TempItemName_00 = Second, a wait of SCRUB_WRITE_WAIT
                                        frames, then the same one-time sale with Second (the line names Second,
                                        and point 3 sorts Second out by its own name)
       Only for a scrub whose talk runs the one-time root itself (the upgrade scrubs: their talk marks them
       sold for good after a buy), so a scrub gives one level.
       Three levels: one more question in front of that one, of the same kind:
           PouchSystemActor.EventQueryIsExistInPouch {Num: 1, Actor: Second}
               1 (Link has no Second) -> the question about First, above
               0 (Link has Second)    -> Scrub_Business_TempItemName_00 = Third, the wait, the sale of Third
       What First needs (SCRUB_COMPANIONS: the Fairy Slingshot's small seed bag) follows First's sale only.
       A pair whose First the game's own branches already sell (the stick bags, the nut bags: the game's own
       upgrade scrubs) is accepted when that branch sells nothing but the pair's levels, at the scrub's price:
       the new branch then stands in front of it for every scrub with that map setting, and sells them the
       same levels at the same price (with the generic line). The game's stick-bag branch first asks "ever had
       a Deku Stick?" and sells Medium when not, also to a Link who has Medium from another check: the new
       branch asks the inventory only, so no level is sold twice.
    The price is what the game's own calls ask for the scrub's original item (the first copy's). Returns lines
    saying what was changed."""
    pairs = pairs or {}
    asked = asked or (lambda item: item)
    eps = {p.name: p.main for p in fc.entry_points}
    by = fc.events
    root = eps.get(SCRUB_ROOT)
    head = next((i for i in flow_reachable(fc, root) if by[i].type == 'switch' and isinstance(by[i].params, dict)
                 and by[i].params.get('GameDataName') == SCRUB_VAR), None)
    if head is None:
        raise SystemExit('%s: no comparison of %s found' % (SCRUB_ROOT, SCRUB_VAR))
    calls = [e for e in by if e.type == 'subflow' and e.flowchart == '' and e.entry in SCRUB_PRICE_KEYS
             and isinstance(e.params, dict)]
    # items the game's own branches already sell: a new branch for one would also catch the game's other
    # scrubs selling it (e.g. the Death Mountain heart-piece scrub, 100 rupees), so they are refused for now
    known = {by[i].params.get('Value') for i in flow_reachable(fc, root) if by[i].type == 'switch'
             and isinstance(by[i].params, dict) and by[i].params.get('GameDataName') == SCRUB_VAR}
    prices, repeat, said = {}, {}, []
    later_of = {}                                      # First -> the levels after it, () for an item sold alone

    def games_sales(first):
        """what the game's own branch for a scrub whose map setting is `first` sells once: {(item, price)}"""
        sw = next(by[i] for i in flow_reachable(fc, root) if by[i].type == 'switch'
                  and isinstance(by[i].params, dict) and by[i].params.get('GameDataName') == SCRUB_VAR
                  and by[i].params.get('Value') == first)
        return {(by[i].params.get('ActorName'), by[i].params.get('Price'))
                for i in flow_reachable(fc, dict(sw.cases)[0])
                if by[i].type == 'subflow' and by[i].flowchart == '' and by[i].entry == SCRUB_SELL}

    for cid, item, copies in sales:
        later = tuple(pairs[cid][1:]) if cid in pairs else ()
        if cid in pairs and pairs[cid][0] != item:
            raise SystemExit('%s: sells %s, not the first level of its pair %s' % (cid, item, '>'.join(pairs[cid])))
        if later_of.setdefault(item, later) != later:
            raise SystemExit('%s: %s is sold alone by one scrub and as the first level of a pair by another: '
                             'one branch cannot do both' % (cid, item))
        if any(SCRUB_COMPANIONS.get(x) for x in later):
            raise SystemExit('%s: %s: a later level that needs another item given with it is not supported '
                             'on a scrub' % (cid, '>'.join((item,) + later)))
        costs = []
        for talk, old in copies:
            start = eps.get(talk)
            if start is None:
                raise SystemExit('%s: its talk %s is not in %s: not supported yet' % (cid, talk, SCRUB_FLOW))
            if not (by[start].type == 'subflow' and by[start].entry == SCRUB_ROOT):
                if later:
                    raise SystemExit('%s: a progressive pair can only be put on a scrub that sells one thing '
                                     'once (its talk %s sells again and again: nothing would keep it from '
                                     'selling both levels)' % (cid, talk))
                repeat.setdefault(talk, []).append(item)
            costs += sorted({e.params.get('Price') for e in calls if e.params.get(SCRUB_PRICE_KEYS[e.entry]) == old})
        if not costs:
            raise SystemExit('%s: price of %s not found' % (cid, [o for _, o in copies]))
        price = costs[0]
        for x in (item,) + later:
            if x not in known:
                continue
            # the game's own branch for it sells nothing but this pair's levels at this price: the new branch
            # in front of it gives the game's other scrubs of that kind the same
            sold = games_sales(x)
            if not later or x != item or not sold or any(i not in (item,) + later or c != price for i, c in sold):
                raise SystemExit('%s: %s is sold by the game\'s own scrub branches (other scrubs would sell it '
                                 'at this price too): not supported yet' % (cid, x))
            said.append('%s: the game\'s own branch for %s sells %s at %s rupees: the new branch in front of it '
                        'sells every scrub of that kind the same levels at the same price'
                        % (cid, item, ' and '.join(sorted({i for i, _ in sold})), price))
        if len(set(costs)) > 1:
            said.append('%s: its copies cost %s; sells at %s' % (cid, sorted(set(costs)), price))
        if prices.get(item, (price,))[0] != price:
            raise SystemExit('%s: %s is also sold by %s at %s rupees, here %s'
                             % (cid, item, prices[item][1], prices[item][0], price))
        prices[item] = (price, cid)
    both = list(later_of) + [x for later in later_of.values() for x in later]
    if len(set(both)) != len(both):
        raise SystemExit('%s: an item would be sold by two branches: %s' % (SCRUB_FLOW, sorted(
            x for x in set(both) if both.count(x) > 1)))
    template = next(e for e in calls if e.entry == SCRUB_SELL)
    pair_tpl = scrub_pair_template(fc) if any(later_of.values()) else None
    first_new = len(by)
    for item, (price, cid) in prices.items():
        params = evfl.Params(template.params)
        params['ActorName'] = item
        params['Price'] = price
        params['SellerMessageId'] = 'EventFlowMsg/Enemy_Event:' + SCRUB_LABEL
        sell = fc.add_subflow('', SCRUB_SELL, params)
        extra = SCRUB_COMPANIONS.get(item, [])
        if extra:
            # after a successful buy only (ScrubBusiness_BuySuccess, as the game's own callers check it)
            nxt = None
            for companion in reversed(extra):
                nxt = fc.add_action('PouchSystemActor', 'EventTriggerAddOrRemovePouchContent',
                                    evfl.Params(Num=1, Actor=companion, IsGetEvent=False,
                                                IsSetMessageTargetActorName=False, IsEquipDIrect=False), next=nxt)
            fc.events[sell].next = fc.add_switch('GameDataActor', 'EventQueryIsGameDataBool', [(0, nxt)],
                                                 evfl.Params(GameDataName='ScrubBusiness_BuySuccess', Index=-1))
        target, levels, lines = sell, (item,) + later_of[item], []
        for k in range(1, len(levels)):
            # "has the level before?" -> yes: this level's name written, the wait, its sale; no: what was there
            (q_actor, q_params, has, has_not), (w_params, wait_actor, wait_params) = pair_tpl
            params2 = evfl.Params(params)
            params2['ActorName'] = levels[k]
            sell2 = fc.add_subflow('', SCRUB_SELL, params2)
            wait_params = evfl.Params(wait_params)
            wait_params['Frames'] = SCRUB_WRITE_WAIT
            wait = fc.add_action(wait_actor, 'EventWait', wait_params, next=sell2)
            w_params = evfl.Params(w_params)
            w_params['GameDataName'], w_params['Value'] = SCRUB_VAR, levels[k]
            write = fc.add_action('GameDataActor', SCRUB_NAME_WRITE, w_params, next=wait)
            ask = evfl.Params(q_params)
            ask['Actor'] = asked(levels[k - 1])
            below = target
            target = fc.add_switch(q_actor, SCRUB_PAIR_QUERY, [(has, write), (has_not, below)], ask)
            if k == 1:
                lines.append('%s: a progressive pair: asks first (%s: %s.%s %s): Link has no %s -> %s sells %s, '
                             'else %s is written into %s, %d frames pass and %s sells %s at the same price'
                             % (cid, fc.events[target].name, GIFT_PAIR_ACTOR, SCRUB_PAIR_QUERY, dict(ask), item,
                                fc.events[sell].name, item, levels[k], SCRUB_VAR, SCRUB_WRITE_WAIT,
                                fc.events[sell2].name, levels[k]))
            else:
                lines.append('%s: three levels: asks before that (%s: %s.%s %s): Link has no %s -> the question '
                             'above (%s), else %s is written into %s, %d frames pass and %s sells %s at the same '
                             'price' % (cid, fc.events[target].name, GIFT_PAIR_ACTOR, SCRUB_PAIR_QUERY, dict(ask),
                                        levels[k - 1], fc.events[below].name, levels[k], SCRUB_VAR,
                                        SCRUB_WRITE_WAIT, fc.events[sell2].name, levels[k]))
        sw = fc.add_switch('GameDataActor', 'EventQueryIsGameDataString64', [(0, target), (1, head)],
                           evfl.Params(GameDataName=SCRUB_VAR, Index=-1, Value=item))
        if fc.repoint(head, sw, keep=(sw,)) < 1:
            raise SystemExit('%s: nothing led to %s' % (SCRUB_ROOT, by[head].name))
        head = sw
        said.append('%s sells %s at %s rupees, once (new branch %s)%s' % (cid, item, price, fc.events[sw].name,
                    ', with %s' % ', '.join(extra) if extra else ''))
        said += lines
    hard = sorted(i for i in both if i in direct)
    if hard:
        shown = [i for i in flow_reachable(fc, eps[SCRUB_SELL]) if by[i].type == 'subflow'
                 and by[i].flowchart == GIFT_FLOW]
        if len(shown) != 1 or by[shown[0]].entry != 'GetInEvent_NotTurn_2DShop' \
                or not isinstance(by[shown[0]].params, dict) \
                or by[shown[0]].params.get('PriceGameData') != 'SimpleShop_Price' \
                or by[shown[0]].params.get('ActorName') != 'ActorName':
            raise SystemExit('%s: its pay-and-get call of %s not found as expected' % (SCRUB_SELL, GIFT_FLOW))
        get = first = shown[0]
        for item in hard:
            nxt = by[get].next
            steps = (sync or {}).get(item)
            if steps:
                nxt = sync_steps(fc, steps, nxt)
            give = fc.add_subflow(DIRECT_GET[0], DIRECT_GET[1], evfl.Params(ActorName=item), next=nxt)
            # as the first two steps of GetInEvent_NotTurn_2DShop (its PriceGameData is SimpleShop_Price here)
            settle = fc.add_action('UISystemActor', 'EventWaitStableNumDisplay', evfl.Params(IsWaitEnd=True),
                                   next=give)
            pay = fc.add_action('PouchSystemActor', 'EventTriggerAddGameDataIntToRupee',
                                evfl.Params(IsSignInverse=True, GameDataName='SimpleShop_Price'), next=settle)
            sw = fc.add_switch('GameDataActor', 'EventQueryIsGameDataString64', [(0, pay), (1, first)],
                               evfl.Params(GameDataName=SCRUB_VAR, Index=-1, Value=item))
            if fc.repoint(first, sw, keep=(sw,)) < 1:
                raise SystemExit('%s: nothing led to its call of %s' % (SCRUB_SELL, GIFT_FLOW))
            first = sw
            said.append('%s: Link can\'t hold it up: paid and given with the get window (new check %s in %s)%s'
                        % (item, by[sw].name, SCRUB_SELL,
                           ', then Link\'s equipment is brought in line' if steps else ''))
    if repeat:
        write = next(i for i in flow_reachable(fc, root) if by[i].type == 'action'
                     and fc.actors[by[i].actor].actions[by[i].action] == 'EventScrubBusinessWriteGameDataBancItemName')
        root_call = by[eps[SCRUB_ONE_TIME_TALK]]
        assert root_call.type == 'subflow' and root_call.entry == SCRUB_ROOT
        for talk, items in sorted(repeat.items()):
            start = eps[talk]
            new = []
            nxt = start
            for item in sorted(set(items)):
                call = fc.add_subflow('', SCRUB_ROOT, evfl.Params(root_call.params))
                nxt = fc.add_switch('GameDataActor', 'EventQueryIsGameDataString64', [(0, call), (1, nxt)],
                                    evfl.Params(GameDataName=SCRUB_VAR, Index=-1, Value=item))
                new += [call, nxt]
            first = fc.add_action(by[write].actor, 'EventScrubBusinessWriteGameDataBancItemName',
                                  evfl.Params(by[write].params), next=nxt)
            new.append(first)
            if fc.repoint(start, first, keep=set(new)) < 1:
                raise SystemExit('%s: nothing led to the start of %s' % (SCRUB_FLOW, talk))
            said.append('talk %s: sells %s once through the one-time root (new start %s)'
                        % (talk, ', '.join(sorted(set(items))), fc.events[first].name))
    reached = set()
    for p in fc.entry_points:
        reached |= set(flow_reachable(fc, p.main))
    missing = [i for i in range(first_new, len(fc.events)) if i not in reached]
    if missing:
        raise SystemExit('%s: new steps not reached: %s' % (SCRUB_FLOW, [fc.events[i].name for i in missing]))
    fc.update_entry_points()
    for first, later in sorted(later_of.items()):
        if later:
            scrub_pair_check(fc, first, *later, asked=asked)
    return said


def scrub_messages(out, romfs, lines, msg_file=None):
    """new lines {label: text} in every language's message archive (the scrubs' file, or `msg_file`); `lines`
    may be a function of the language's archive that gives them (texts made from that language's own)"""
    msg_file = msg_file or SCRUB_MSG_FILE
    lines_for = lines if callable(lines) else (lambda arc: lines)
    for fn in sorted(os.listdir(os.path.join(romfs, 'Mals'))):
        if not fn.endswith('.sarc.zs'):
            continue
        path = 'Mals/' + fn[:-3]
        src, old = out.read(path)
        arc = sarc.Sarc.read(old)
        lines = lines_for(arc)
        m = msbt.Msbt.read(arc.files[msg_file])
        if m.write() != arc.files[msg_file] or set(lines) & set(m.texts):
            raise SystemExit('%s: %s does not round-trip or already has %s' % (path, msg_file, sorted(lines)))
        m.texts.update(lines)
        new_msg = m.write()
        if msbt.Msbt.read(new_msg).texts != m.texts:
            raise SystemExit('read-back: %s in %s' % (msg_file, path))
        arc.files[msg_file] = new_msg
        new = arc.write()
        back = sarc.Sarc.read(new)
        if set(back.files) != set(arc.files) or any(back.files[k] != v for k, v in arc.files.items()):
            raise SystemExit('read-back: %s differs from what was intended' % path)
        out.write(path, src, old, new)


# ---------------------------------------------------------------------------------------------- gossip stones
# --gossip STONE=TEXT: what a gossip stone says (a test of the groundwork for hints). From the game's files:
# - every stone runs the flow GossipStone, entry Talk. The stone's own rumour is one step: Npc_EventStarter (the
#   stone talked to) EventTalkWithInstanceNameLabel {MstxtName: GossipStone}: the text of
#   EventFlowMsg/GossipStone.msbt whose label is the stone's name in the map (GOSSIP_KOKIRI_FOREST_01...). So
#   a stone's text is changed by changing that one text, in every language's archive (English everywhere, as
#   the scrub lines);
# - the rumour is only reached with the Mask of Truth owned and worn (two questions at the start of Talk;
#   without it Navi talks instead), the mask is a child's, and the stone first says an opening line about the
#   mask. Nothing depends on the time of day. The stone's own event AI answers a question no game flow asks,
#   EventQueryGossipStoneCheckInstanceName: a number per stone name (GOSSIP_DEATH_MOUNTAIN_CRATER_01 = 0 ...
#   GOSSIP_ZORA_RIVER_03 = 39, any other name 40; read from the AI by gossip_query_values). The builder puts that
#   question in front of Talk: a chosen stone goes to the talk set-up the stone uses with the mask
#   (InitTalk_GossipStone), its text, and the end (no mask questions, no opening or closing line, no "first
#   time" flag); every other answer goes to the game's own first step, so other stones are unchanged.
GOSSIP_FLOW = 'Event/EventFlow/GossipStone.bfevfl'
GOSSIP_ENTRY = 'Talk'
GOSSIP_MSG_FILE = 'EventFlowMsg/GossipStone.msbt'
GOSSIP_PACK = 'Pack/Actor/Obj_GossipStone_A_01.pack'
GOSSIP_AI = 'AI/GossipStone.event.root.ainb'
GOSSIP_QUERY = 'EventQueryGossipStoneCheckInstanceName'
GOSSIP_TALKER = 'Npc_EventStarter'
GOSSIP_SAY = 'EventTalkWithInstanceNameLabel'
GOSSIP_INIT = ('InitTalk', 'InitTalk_GossipStone')
GOSSIP_PREFIX = 'GOSSIP_'
# Layout, as the game's rumours (every one of the 40, every language): colour 1 and size 80 % for the whole text,
# then the dialogue start tag; a new page is (0,4) followed by the size and colour again (GOSSIP_LOST_WOOD_01,
# the one rumour with pages); lines are broken by hand ('\n'). A highlighted word is colour 0, the colour the
# game uses for highlights (about 3,000 times), switched back to colour 1 after it (not to the default, 0xffff,
# which would end the rumour's colour).
GOSSIP_START = _msg_tag(0, 3, b'\x01\x00') + _msg_tag(0, 2, b'\x50\x00') + _msg_tag(3, 0, b'\x0f\x00\x00')
GOSSIP_PAGE = _msg_tag(0, 4) + _msg_tag(0, 2, b'\x50\x00') + _msg_tag(0, 3, b'\x01\x00')
GOSSIP_HIGHLIGHT, GOSSIP_NORMAL = _msg_tag(0, 3, b'\x00\x00'), _msg_tag(0, 3, b'\x01\x00')
GOSSIP_WIDTH = 65         # characters per line: the longest line of the game's English rumours (65)
GOSSIP_LINES = 2          # lines per page: every rumour of the game has 1 or 2
GOSSIP_PAGES = 8          # pages: the most any message of the game has (8)
GOSSIP_LANG = 'Mals/USen.Product.110.sarc'   # the text's characters must be ones the game's English text uses


def gossip_parse(world, specs):
    """--gossip STONE=TEXT -> {stone name in the map (= its message label): (what was given, text)}. STONE is the
    stone's check ID (KF_NEAR_LOST_WOODS_GOSSIP) or its name in the map (GOSSIP_KOKIRI_FOREST_01)"""
    out = {}
    for spec in specs:
        stone, sep, text = spec.partition('=')
        if not sep or not stone or not text.strip():
            raise SystemExit('--gossip %r: write STONE=TEXT (a check ID or the stone\'s name in the map)' % spec)
        if stone.startswith(GOSSIP_PREFIX):
            names = {stone}
        else:
            r, _, loc = find_check(world, stone)
            ps = list(world.placements_of(r, loc))
            kinds = {world.checks[sc][sp]['kind'] for sc, sp, _ in ps}
            if kinds != {'gossip'}:
                raise SystemExit('--gossip %s: not a gossip stone (%s)'
                                 % (stone, ', '.join(sorted(kinds)) or 'no placement'))
            names = {p.get('name_in_map') for _, _, p in ps}
            if len(names) != 1 or None in names:
                raise SystemExit('--gossip %s: its placements do not have one name in the map (%s)' % (stone, names))
        name, = names
        if name in out:
            raise SystemExit('--gossip: %s (%s) is given twice' % (stone, name))
        out[name] = (stone, text)
    return out


def gossip_layout(text, chars):
    """the user's text -> pages of lines of (character, highlighted). '\\n' (backslash n, or a real line feed):
    a line break; '\\p': a new page; {...}: highlighted. Lines longer than GOSSIP_WIDTH are wrapped at spaces,
    pages with more than GOSSIP_LINES lines continue on a new page. chars: the characters allowed"""
    pages, lines, line, hl, i = [], [], [], False, 0
    while i < len(text):
        c = text[i]
        if c == '\\':
            k = text[i + 1:i + 2]
            if k not in ('n', 'p'):
                raise SystemExit('--gossip: unknown escape \\%s (\\n: new line, \\p: new page)' % k)
            lines.append(line)
            line = []
            if k == 'p':
                pages.append(lines)
                lines = []
            i += 2
            continue
        if c == '\n':
            lines.append(line)
            line = []
        elif c == '{' and not hl:
            hl = True
        elif c == '}' and hl:
            hl = False
        elif c in '{}':
            raise SystemExit('--gossip: %r: braces must come in pairs, {highlighted}' % text)
        elif c not in chars:
            raise SystemExit('--gossip: %r: the character %r is not used anywhere in the game\'s English text'
                             % (text, c))
        else:
            line.append((c, hl))
        i += 1
    if hl:
        raise SystemExit('--gossip: %r: a { is not closed' % text)
    lines.append(line)
    pages.append(lines)
    out = []
    for given in pages:
        wrapped = []
        for ln in given:
            words, w = [], []
            for c in ln:
                if c[0] == ' ':
                    if w:
                        words.append(w)
                    w = []
                else:
                    w.append(c)
            if w:
                words.append(w)
            cur = []
            for w in words:
                if len(w) > GOSSIP_WIDTH:
                    raise SystemExit('--gossip: the word %r is longer than a line (%d characters)'
                                     % (''.join(c for c, _ in w), GOSSIP_WIDTH))
                if cur and len(cur) + 1 + len(w) > GOSSIP_WIDTH:
                    wrapped.append(cur)
                    cur = []
                if cur:
                    # the space takes the highlight of the words on both sides of it, else none
                    cur.append((' ', cur[-1][1] and w[0][1]))
                cur += w
            wrapped.append(cur)
        while len(wrapped) > 1 and not wrapped[-1]:
            wrapped.pop()                               # a line break at the end of a page
        out += [wrapped[k:k + GOSSIP_LINES] for k in range(0, len(wrapped), GOSSIP_LINES)]
    if not any(c for page in out for ln in page for c in ln):
        raise SystemExit('--gossip: %r: no text' % text)
    if len(out) > GOSSIP_PAGES:
        raise SystemExit('--gossip: %r takes %d pages (at most %d, %d lines of %d characters each)'
                         % (text, len(out), GOSSIP_PAGES, GOSSIP_LINES, GOSSIP_WIDTH))
    return out


def gossip_message(pages):
    """pages of lines of (character, highlighted) -> the message, with the game's tags (GOSSIP_START...)"""
    msg = GOSSIP_START
    for n, page in enumerate(pages):
        if n:
            msg += GOSSIP_PAGE
        hl = False
        for k, ln in enumerate(page):
            if k:
                msg += '\n'
            for c, h in ln:
                if h != hl:
                    msg += GOSSIP_HIGHLIGHT if h else GOSSIP_NORMAL
                    hl = h
                msg += c
        if hl:
            msg += GOSSIP_NORMAL
    return msg + '\x00'


def gossip_chars(arc_data):
    """the characters the game's messages in a language archive use (plain text, not tags or line feeds)"""
    chars = set()
    for f, data in sarc.Sarc.read(arc_data).files.items():
        if f.endswith('.msbt'):
            m = msbt.Msbt.read(data)
            for t in m.texts.values():
                chars.update(c for x in msbt.tags(t, m.encoding) if isinstance(x, str) for c in x)
    return chars - set('\n\x00\\{}')


def gossip_query_values(ai_data):
    """what EventQueryGossipStoneCheckInstanceName answers, from the stone's event AI: ({stone name: number},
    the number for any other name). The question runs a string selector on the stone's own name in the map,
    each case setting the answer (ExecuteEventSetQueryValue)"""
    a = ainb.Ainb.read(ai_data)
    cmd = [c for c in a.commands if c.name == GOSSIP_QUERY]
    if len(cmd) != 1:
        raise SystemExit('%s: no command %s' % (GOSSIP_AI, GOSSIP_QUERY))
    start = a.nodes[cmd[0].left]
    sel = [a.nodes[x.node] for x in start.links[2]]
    if len(sel) != 1 or sel[0].type_name != 'Element_StringSelector':
        raise SystemExit('%s: %s does not run one string selector' % (GOSSIP_AI, GOSSIP_QUERY))
    names, other = {}, []
    for x in sel[0].links[2]:
        node = a.nodes[x.node]
        ins = {i.name: i for t in ('int', 'string') for i in node.inputs[t]}
        if node.name != 'ExecuteEventSetQueryValue' or 'Value' not in ins or ins['Value'].node != -1:
            raise SystemExit('%s: a case of %s does not set a fixed answer' % (GOSSIP_AI, GOSSIP_QUERY))
        case = a.string_at(x.extra[1]) if len(x.extra) > 1 else ''
        if case.startswith(GOSSIP_PREFIX):
            if ins['Label'].value != case or case in names:
                raise SystemExit('%s: %s: case %s not as expected' % (GOSSIP_AI, GOSSIP_QUERY, case))
            names[case] = ins['Value'].value
        else:
            other.append(ins['Value'].value)
    if len(other) != 1 or len(set(names.values()) | set(other)) != len(names) + 1:
        raise SystemExit('%s: %s: the answers are not one per stone and one for any other name'
                         % (GOSSIP_AI, GOSSIP_QUERY))
    return names, other[0]


def gossip_flow_edit(fc, values, other, stones):
    """GossipStone, entry Talk (flowchart, edited in place): first ask the stone its number (GOSSIP_QUERY, on the
    stone talked to): for the chosen stones (names), the talk set-up (subflow InitTalk_GossipStone, as with the
    mask), the stone's text (a copy of the game's step), end; for every other answer the game's own first step.
    Returns lines saying what changed"""
    ep = fc.entry_point(GOSSIP_ENTRY)
    first = ep.main
    reach = fc.reachable(first)
    inits = [i for i in reach if fc.events[i].type == 'subflow'
             and (fc.events[i].flowchart, fc.events[i].entry) == GOSSIP_INIT]
    says = [i for i in reach if fc.events[i].type == 'action' and fc.actors[fc.events[i].actor].name == GOSSIP_TALKER
            and _action_name(fc, fc.events[i]) == GOSSIP_SAY]
    if len(inits) != 1 or len(says) != 1 or (fc.events[says[0]].params or {}).get('MstxtName') != 'GossipStone':
        raise SystemExit('%s: entry %s: not one %s step and one %s step as expected'
                         % (GOSSIP_FLOW, GOSSIP_ENTRY, '/'.join(GOSSIP_INIT), GOSSIP_SAY))
    unknown = sorted(set(stones) - set(values))
    if unknown:
        raise SystemExit('%s: the stone\'s question %s has no answer for %s'
                         % (GOSSIP_FLOW, GOSSIP_QUERY, ', '.join(unknown)))
    say = fc.add_action(GOSSIP_TALKER, GOSSIP_SAY, copy.deepcopy(fc.events[says[0]].params), next=None)
    init = fc.add_subflow(GOSSIP_INIT[0], GOSSIP_INIT[1], copy.deepcopy(fc.events[inits[0]].params), next=say)
    chosen = {values[s] for s in stones}
    cases = [(v, init if v in chosen else first) for v in sorted(set(values.values()) | {other})]
    ask = fc.add_switch(GOSSIP_TALKER, GOSSIP_QUERY, cases)
    ep.main = ask
    fc.update_entry_points()
    return ['entry %s starts with %s (event %d, %d answers): %s -> set-up %s (event %d), the stone\'s text (event '
            '%d, a copy of %s), end; every other answer -> the game\'s first step (event %d)'
            % (GOSSIP_ENTRY, GOSSIP_QUERY, ask, len(cases),
               ', '.join('%s (%d)' % (s, values[s]) for s in sorted(stones)), GOSSIP_INIT[1], init, say,
               fc.events[says[0]].name, first)]


def gossip_messages(out, romfs, texts):
    """replace the texts {label: message} of GossipStone.msbt in every language's message archive; every
    other text stays as it is. Returns {archive: characters of the text its own messages never use}"""
    unseen = {}
    for fn in sorted(os.listdir(os.path.join(romfs, 'Mals'))):
        if not fn.endswith('.sarc.zs'):
            continue
        path = 'Mals/' + fn[:-3]
        src, old = out.read(path)
        arc = sarc.Sarc.read(old)
        m = msbt.Msbt.read(arc.files[GOSSIP_MSG_FILE])
        if m.write() != arc.files[GOSSIP_MSG_FILE] or not set(texts) <= set(m.texts):
            raise SystemExit('%s: %s does not round-trip or has no text %s'
                             % (path, GOSSIP_MSG_FILE, sorted(set(texts) - set(m.texts))))
        before = dict(m.texts)
        m.texts.update(texts)
        new_msg = m.write()
        back = msbt.Msbt.read(new_msg).texts
        if back != m.texts or list(back) != list(before) \
                or any(back[k] != v for k, v in before.items() if k not in texts):
            raise SystemExit('read-back: %s in %s' % (GOSSIP_MSG_FILE, path))
        arc.files[GOSSIP_MSG_FILE] = new_msg
        new = arc.write()
        back = sarc.Sarc.read(new)
        if set(back.files) != set(arc.files) or any(back.files[k] != v for k, v in arc.files.items()):
            raise SystemExit('read-back: %s differs from what was intended' % path)
        out.write(path, src, old, new)
        used = {c for t in texts.values() for x in msbt.tags(t) if isinstance(x, str) for c in x} - set('\n\x00')
        missing = used - gossip_chars(old)
        if missing:
            unseen[path] = ''.join(sorted(missing))
    return unseen


def gossip_plan(out, world, specs):
    """--gossip, worked out before anything is written: (stones {name: (given, text)}, their messages, their
    layouts, the stone's question's answers {name: number}, the answer for any other name)"""
    stones = gossip_parse(world, specs)
    chars = gossip_chars(out.read(GOSSIP_LANG)[1])
    texts, layouts = {}, {}
    for name, (given, text) in stones.items():
        layouts[name] = gossip_layout(text, chars)
        texts[name] = gossip_message(layouts[name])
    values, other = gossip_query_values(sarc.Sarc.read(out.read(GOSSIP_PACK)[1]).files[GOSSIP_AI])
    unknown = sorted(set(stones) - set(values))
    if unknown:
        raise SystemExit('--gossip: %s: not a stone the game knows (%s answers no number for it)'
                         % (', '.join(unknown), GOSSIP_QUERY))
    return stones, texts, layouts, values, other


def gossip_build(out, romfs, plan):
    """--gossip: the texts in every language and the stones' talk flow (see GOSSIP_FLOW); plan: gossip_plan"""
    stones, texts, layouts, values, other = plan
    src, old = out.read(GOSSIP_FLOW)
    ef = evfl.loads(old)
    said = gossip_flow_edit(ef.flowchart, values, other, sorted(stones))
    out.write(GOSSIP_FLOW, src, old, flow_write_checked(ef))
    for line in said:
        print('gossip flow        %s' % line)
    unseen = gossip_messages(out, romfs, texts)
    for name, (given, text) in sorted(stones.items()):
        pages = layouts[name]
        shown = ' / '.join(' | '.join(''.join(c for c, _ in ln) for ln in page) for page in pages)
        print('gossip             %s (%s): %d page%s: %s' % (given, name, len(pages), 's' * (len(pages) > 1), shown))
    print('gossip lines       %s replaced in %s (every language, English text)'
          % (', '.join(sorted(texts)), GOSSIP_MSG_FILE))
    for path, missing in sorted(unseen.items()):
        print('  note: %s: its own messages never use %r (check that its font shows them)' % (path, missing))


# ----------------------------------------------------------------------------------------------- hints
# --hint STONE=ITEM or STONE=@CHECK_ID: the stone says where an item of this build is, worded from the build's own
# placements, as a --gossip text (the stone's text and talk flow above, passed in game):
#     They say {the Boomerang} can be found in a pot in the {House of the Know-It-All Brothers} in {Kokiri Forest}.
# Every name is the game's own English text (the remake's names, never the N64 game's): the item's name and its
# article from ActorMsg/PouchContent.msbt (<name>_Name; the article as its get message has it, "You found the
# Boomerang!"); the area from LocationMsg/Location.msbt (the label is the map's name); a house or a shop from the
# first line of its signboard (EventFlowMsg/SignboardWood.msbt, HINT_PLACES); Gold Skulltulas and Business Scrubs
# from ActorMsg/Enemy.msbt. Only the joining words are ours (HINT_KINDS, "They say ... can be found").
HINT_NAMES = 'ActorMsg/PouchContent.msbt'
HINT_AREAS = 'LocationMsg/Location.msbt'
HINT_SIGNS = 'EventFlowMsg/SignboardWood.msbt'
HINT_ENEMIES = 'ActorMsg/Enemy.msbt'
# region -> (signboard label, the words in front of it): the place inside the area, named by its sign (the first line,
# before any comma). Regions without a sign of their own are named by their area alone.
HINT_PLACES = {
    'KF Links House': ('KokiriForest_005', 'in'),                # Link's House
    'KF Midos House': ('KokiriForest_010', 'in the'),            # Mansion of the Great Mido
    'KF Sarias House': ('KokiriForest_013', 'in'),               # Saria's House
    'KF House of Twins': ('KokiriForest_012', 'in the'),         # House of the Twins
    'KF Know It All House': ('KokiriForest_011', 'in the'),      # House of the Know-It-All Brothers
    'KF Shop': ('KokiriForest_004', 'in the'),                   # Kokiri Shop
    'KF Training Area': ('KokiriForest_001', 'at the'),          # Training Grounds
    'Deku Theater': ('LostWood_001', 'at the'),                  # Forest Stage
}
# regions under the ground (a hole leads down to them; the game's text has no word for them): "underground"
HINT_UNDERGROUND = {'KF Storms Grotto', 'LW Scrubs Grotto', 'SFM Wolfos Grotto', 'SFM Upper Grotto'}
# area (map) -> the article English puts in front of its name ("in the Lost Woods")
HINT_AREA_ARTICLE = {'LostWood': 'the', 'SacredForestMeadow': 'the'}
# kind of check -> how the item is found there; {gs} and {scrub} are the game's names for them
HINT_KINDS = {
    'chest': 'in a chest',
    'freestanding': 'lying on the ground',
    'pot': 'in a pot',
    'rock': 'under a rock',
    'bush': 'under a bush',
    'boulder': 'inside a boulder',
    'skulltula': 'on a {gs}',
    'scrub': 'sold by a {scrub}',
    'shop': 'for sale',
    'gift': 'as a gift',
    'song': 'as a gift',
}
HINT_GS, HINT_SCRUB = 'Enemy_Skulltula_Gold_Name', 'Enemy_Scrub_Business_Name'
HINT_GET = re.compile(r'^You [^!]*?\b(the|a|an) ')                   # the article of a get message


def msg_plain(text, encoding=0):
    """a message's text without its tags and its end; a new page (tag 0,4) is a line break"""
    return ''.join(x if isinstance(x, str) else '\n' if tuple(x[:2]) == (0, 4) else ''
                   for x in msbt.tags(text, encoding)).rstrip('\x00')


def hint_texts(lang_arc):
    """{msbt file: {label: plain text}} of the files hints read, from a language archive (its data)"""
    files = sarc.Sarc.read(lang_arc).files
    out = {}
    for f in (HINT_NAMES, HINT_AREAS, HINT_SIGNS, HINT_ENEMIES):
        m = msbt.Msbt.read(files[f])
        out[f] = {k: msg_plain(v, m.encoding) for k, v in m.texts.items()}
    return out


def hint_item_name(item, texts, known_as):
    """(article, name) of an item as the game's English text names it: <name>_Name in PouchContent.msbt, for the
    item itself or the name the inventory knows it by (ActorInfo ActorName: Weapon_Range_SlingShot for
    Item_Range_SlingShot); the article from its get message ('' when it has none)"""
    names = texts[HINT_NAMES]
    for label in (item, known_as(item)):
        if label and label + '_Name' in names:
            name = names[label + '_Name'].strip()
            m = HINT_GET.match(names.get(label + '_GetMessage', ''))
            return (m.group(1) if m else ''), name
    raise SystemExit('--hint: %s has no name in the game\'s text (%s)' % (item, HINT_NAMES))


def hint_sign(texts, label):
    """a place's name: its signboard's first line, before any comma"""
    t = texts[HINT_SIGNS].get(label)
    if not t:
        raise SystemExit('--hint: no signboard text %s in %s' % (label, HINT_SIGNS))
    return t.replace('　', ' ').split('\n')[0].split(',')[0].strip()


def check_kind(world, cid):
    """the kind of a check: its map placements' (one kind), or an event's (gift, song)"""
    r, name, loc = find_check(world, cid)
    kinds = {world.checks[sc][sp]['kind'] for sc, sp, _ in world.placements_of(r, loc)}
    if len(kinds) > 1:
        raise SystemExit('%s: placements of more than one kind (%s)' % (cid, ', '.join(sorted(kinds))))
    if kinds:
        return kinds.pop()
    if loc.get('song'):
        return 'song'
    if loc.get('gift') or loc.get('cutscene'):
        return 'gift'
    raise SystemExit('%s: neither a map placement nor an event' % cid)


def hint_where(world, cid, texts):
    """how and where the item of a check is found, as hint text: 'in a pot in the {House of the Know-It-All
    Brothers} in {Kokiri Forest}'"""
    r, name, loc = find_check(world, cid)
    kind = check_kind(world, cid)
    if kind not in HINT_KINDS:
        raise SystemExit('--hint: %s is a %s: no hint wording for it' % (cid, kind))
    enemies = texts[HINT_ENEMIES]
    how = HINT_KINDS[kind].format(gs=enemies[HINT_GS].strip(), scrub=' '.join(enemies[HINT_SCRUB].split()))
    area = texts[HINT_AREAS].get(r.scene)
    if not area:
        raise SystemExit('--hint: %s: its area %s has no name in %s' % (cid, r.scene, HINT_AREAS))
    where = how + (' underground' if r.name in HINT_UNDERGROUND else '')
    if r.name in HINT_PLACES:
        label, prep = HINT_PLACES[r.name]
        where += ' %s {%s}' % (prep, hint_sign(texts, label))
    article = HINT_AREA_ARTICLE.get(r.scene)
    return where + ' in %s{%s}' % (article + ' ' if article else '', area)


def hint_specs(world, specs, assignments, texts, known_as):
    """--hint STONE=ITEM or STONE=@CHECK_ID -> ([STONE=TEXT, as --gossip takes it], lines saying what each
    stone hints). assignments: the build's (check id, item as given: an item, or a family First>Second...). ITEM
    is an item as given in an assignment, or the first level of a family: it must be placed on exactly one check
    (else name the check: @CHECK_ID). A family is named by its first level, "or an upgrade of it"."""
    placed = {}                                        # item or first level -> [(check id, family or None)]
    by_check = {}
    for cid, given in assignments:
        levels = given.split('>')
        item = FAMILY_ALIASES.get(levels[0], levels[0]) if len(levels) == 1 else levels[0]
        fam = tuple(levels) if len(levels) > 1 else None
        placed.setdefault(item, []).append((cid, fam))
        if len(levels) == 1 and levels[0] != item:
            placed.setdefault(levels[0], []).append((cid, fam))
        by_check[cid] = (item, fam)
    out, said = [], []
    for spec in specs:
        stone, sep, what = spec.partition('=')
        if not sep or not stone or not what:
            raise SystemExit('--hint %r: write STONE=ITEM or STONE=@CHECK_ID' % spec)
        if what.startswith('@'):
            cid = what[1:]
            find_check(world, cid)
            if cid not in by_check:
                raise SystemExit('--hint %s: %s is given nothing in this build' % (stone, cid))
            item, fam = by_check[cid]
        else:
            if '>' in what:
                raise SystemExit('--hint %s: name a family by its first level (%s)' % (stone, what.split('>')[0]))
            spots = placed.get(what, [])
            if len(spots) != 1:
                raise SystemExit('--hint %s: %s is on %s in this build: name the check instead (%s=@CHECK_ID)'
                                 % (stone, what, '%d checks (%s)' % (len(spots), ', '.join(c for c, _ in spots))
                                    if spots else 'no check', stone))
            cid, fam = spots[0]
            item = by_check[cid][0]                    # a small seed bag or quiver alone: its weapon
        article, name = hint_item_name(item, texts, known_as)
        thing = '%s{%s}' % (article + ' ' if article else '', name)
        if fam:
            thing += ' or an upgrade of it'
        text = 'They say %s can be found %s.' % (thing, hint_where(world, cid, texts))
        out.append('%s=%s' % (stone, text))
        said.append('hint               %s -> %s (%s): %s' % (stone, cid, '>'.join(fam) if fam else item,
                                                              text.replace('{', '').replace('}', '')))
    return out, said


def patch_file(data, changes, checking=None, three=None, wrap=None):
    """change what the actors with these hashes give: chests and pots through their Drop__DropActor (chests'
    special opening events handled by CHEST_EVENTS), freestanding items by their actor type (Gyaml);
    checking: {hash: (item to look for, item given when Link has it)}: that small chest becomes the game's
    checking chest (CHECKING_CHEST). A game checking chest that is not in `checking` becomes the ordinary chest
    (PLAIN_CHEST) without its check settings, so it always gives the placed item;
    three: {hash: name of a three-level family}: that chest (one of `checking`) becomes the family's own chest
    instead (checking_chest), with the same settings;
    wrap: {hash: f}: that chest gets an opening event of our own, GetEventName = f(the chest's actor, the event
    its placement names or None): for chests that hold an ocarina (tbox_sync_event);
    returns (new data, {hash: old item}, {hash: new Dynamic as intended})"""
    checking = checking or {}
    three = three or {}
    wrap = wrap or {}
    doc = byml.loads(data)
    found, intended = {}, {}
    for a in doc.root.get('Actors', []):
        h = str(int(a['Hash']))
        if h in changes and changes[h][3] in REPLACED:
            found[h] = a['Gyaml']
            a['Gyaml'] = changes[h][1]
            continue
        if h in changes:
            dyn = a.get('Dynamic')
            if h in checking and a['Gyaml'] not in CHECKING_CHEST and a['Gyaml'] not in PLAIN_CHEST:
                raise SystemExit('%s: placement %s is a %s: only the small chest (%s) has a checking version'
                                 % (changes[h][0], h, a['Gyaml'], ', '.join(sorted(CHECKING_CHEST))))
            if a['Gyaml'] in PLAIN_CHEST and (dyn is None or 'Drop__DropActor' not in dyn):
                # a game checking chest with nothing set as its first item (Gerudo Training Ground: a green
                # rupee by default): set like any chest's
                dyn = type(dyn)(dyn) if dyn is not None else {}
                dyn['Drop__DropActor'] = None             # nothing set: found below as None
            if changes[h][3] == 'pot' and (dyn is None or 'Drop__DropActor' not in dyn
                                           or POT_TABLE_KEY in dyn):
                # a pot that drops from a table (DropTable_Obj_Heart...) or names nothing (most pots in
                # dungeons): it gets the item and loses the table, the form of the game's own item pots
                # (Drop__DropActor alone: 109 pots). The game's code reads Drop__DropActor before
                # Drop__DropTable (out/RESEARCH_drop_tables.md); two pots in Dodongo's Cavern name both, and
                # whether the table still drops there too is not known, so the table goes
                dyn = type(dyn)(dyn) if dyn is not None else {}
                dyn.setdefault('Drop__DropActor', None)   # nothing set: found below as None
                dyn.pop(POT_TABLE_KEY, None)
            if changes[h][3] == 'chest' and a['Gyaml'] in CHECKING_CHEST \
                    and (dyn is None or 'Drop__DropActor' not in dyn):
                # an ordinary small chest with nothing set (the Forest Temple's falling ceiling room): set
                # like any chest's
                dyn = type(dyn)(dyn) if dyn is not None else {}
                dyn['Drop__DropActor'] = None             # nothing set: found below as None
            if changes[h][3] in DROP_ADDED and (dyn is None or 'Drop__DropActor' not in dyn):
                if dyn is not None and 'Drop__DropTable' in dyn:
                    raise SystemExit('actor %s (%s) drops from a drop table (%s): not supported yet'
                                     % (h, a['Gyaml'], dyn['Drop__DropTable']))
                dyn = type(dyn)(dyn) if dyn is not None else {}
                dyn['Drop__DropActor'] = None             # nothing set: found below as None
            if dyn is None or 'Drop__DropActor' not in dyn:
                raise SystemExit('actor %s (%s) has no Drop__DropActor' % (h, a['Gyaml']))
            found[h] = dyn['Drop__DropActor']
            # identical settings are stored once in the file and shared between actors: give this actor its
            # own copy before changing it, or every chest with the same contents would change too
            dyn = type(dyn)(dyn)
            dyn['Drop__DropActor'] = changes[h][1]
            event = dyn.get('GetEventName')
            if event is not None and changes[h][1] != found[h]:
                what = CHEST_EVENTS.get(event)
                if what is None:
                    raise SystemExit('%s: chest %s has the special opening event %r, not in CHEST_EVENTS yet: '
                                     'decide what to do with it first' % (changes[h][0], h, event))
                if what[0] == 'remove':
                    del dyn['GetEventName']
            if h in checking:
                a['Gyaml'] = checking_chest(a['Gyaml'], three.get(h))
                for k in CHECK_SETTINGS:
                    dyn.pop(k, None)
                dyn['Drop__CheckActor'], dyn['Drop__DropActor_Substitute'] = checking[h]
            elif a['Gyaml'] in PLAIN_CHEST:
                a['Gyaml'] = PLAIN_CHEST[a['Gyaml']]
                for k in CHECK_SETTINGS:
                    dyn.pop(k, None)
            if h in wrap:
                dyn[TBOX_EVENT_KEY] = wrap[h](a['Gyaml'], dyn.get(TBOX_EVENT_KEY))
            a['Dynamic'] = dyn
            intended[h] = dict(dyn)
    missing = set(changes) - set(found)
    if missing:
        raise SystemExit('placements not found: %s' % ', '.join(sorted(missing)))
    return byml.dumps(doc), found, intended


def patch_pack(pack_data, inner, key, expected, value):
    """change one top-level value of a BYML file inside an actor pack; returns (new pack data, (the inner file
    before, after))"""
    archive = sarc.Sarc.read(pack_data)
    if inner not in archive.files:
        raise SystemExit('%s not found in the pack' % inner)
    old_inner = archive.files[inner]
    doc = byml.loads(old_inner)
    if doc.root.get(key) != expected:
        raise SystemExit('%s: %s is %r, expected %r (game files differ from what this fix was made for)'
                         % (inner, key, doc.root.get(key), expected))
    doc.root[key] = type(doc.root[key])(value)
    new_inner = byml.dumps(doc)
    archive.files[inner] = new_inner
    new_pack = archive.write()
    # read back: only this value of this file differs
    back = sarc.Sarc.read(new_pack)
    before = sarc.Sarc.read(pack_data)
    if set(back.files) != set(before.files):
        raise SystemExit('read-back: file list of the pack changed')
    for name, data in back.files.items():
        if name != inner and data != before.files[name]:
            raise SystemExit('read-back: %s changed' % name)
    want = dict(byml.loads(old_inner).root, **{key: value})
    if byml.loads(back.files[inner]).root != want:
        raise SystemExit('read-back: %s differs from what was intended' % inner)
    return new_pack, (old_inner, new_inner)


# A progressive pair on a gift (CHECK_ID=First>Second, PROGRESSIVE_PAIRS): the gift decides in the NPC's own
# flow, the way the game's own flows hand out upgrades: a switch on PouchSystemActor.EventQueryIsExistInPouch
# {Num: 1, Actor: <item>} (0 = Link has it, 1 = he doesn't), then one call of Dm_SY_GetInEvent per answer, each
# with a fixed ActorName, both leading on to the same step. The Deku Theater does exactly this for the stick
# bags (LostWood_ScrubForestStageElder_SkullMaskFirst, Event30: has Item_StickBag_Medium -> Event32 gives
# Item_StickBag_Large, else Event29 gives Item_StickBag_Medium, both GetInEvent_NotTurn, both on to Event0), as
# do the shooting galleries, Bombchu Bowling and the bomb bag Goron. The question, its parameters, its two case
# values and the PouchSystemActor entry are copied from that flow. Nothing is written and the shared get flow
# is only called, with the name of the item given: it makes the held-up model, the window and the inventory
# entry from that one name (its ActorName), so shown = given. The game's flows ask about the three pairs' first
# items under these very names (Item_Scale_Silver, Item_Hookshot, Item_Ocarina_Fairy).
GIFT_PAIR_FLOW = 'Event/EventFlow/LostWood_ScrubForestStageElder_SkullMaskFirst.bfevfl'
GIFT_PAIR_ACTOR = 'PouchSystemActor'
GIFT_PAIR_QUERY = 'EventQueryIsExistInPouch'


def gift_pair_kind(world, cid):
    """True for a check a progressive pair can be placed on as a gift: an event (no map placement) with "gift"
    data (the flow and the event that hand the item over). Songs and cutscene gifts are not (song_pair_kind,
    cutscene_pair_kind); an event with none of that data (the Skull Kids, the Deku Theater: no step of the
    giver's own flow to put the inventory question in front of) stops the build"""
    r, name, loc = find_check(world, cid)
    if world.spots_of(r, loc) or loc.get('song') or loc.get('cutscene'):
        return False
    if not loc.get('gift'):
        raise SystemExit('%s: a progressive pair (First>Second) cannot be put on this gift: the builder has no '
                         'flow data for it ("gift": flow, event, item), so there is no step of the giver\'s own '
                         'flow to put the inventory question in front of' % cid)
    return True


def song_pair_kind(world, cid):
    """True for a song check (an event with "song" data): a family there is given by the song cutscene's own get,
    with the inventory questions in front of it (song_skip)"""
    r, name, loc = find_check(world, cid)
    return not world.spots_of(r, loc) and bool(loc.get('song'))


def cutscene_pair_kind(world, cid):
    """True for a cutscene gift (an event with "cutscene" data): a family there is asked about in front of the
    cutscene's get window and its add step (cutscene_family_edit)"""
    r, name, loc = find_check(world, cid)
    return not world.spots_of(r, loc) and bool(loc.get('cutscene'))


def gift_pair_template(fc):
    """the game's own question as the Deku Theater's flow has it: (the PouchSystemActor entry, the query's
    parameters, the case value for "has it", the case value for "doesn't"). Found by what it is: a switch on
    EventQueryIsExistInPouch whose two cases are calls of Dm_SY_GetInEvent leading on to the same event"""
    for e in fc.events:
        if e.type != 'switch' or fc.actors[e.actor].name != GIFT_PAIR_ACTOR \
                or fc.actors[e.actor].queries[e.query] != GIFT_PAIR_QUERY:
            continue
        gives = {v: fc.events[c] for v, c in e.cases}
        if sorted(gives) != [0, 1] or any(g.type != 'subflow' or g.flowchart != GIFT_FLOW
                                          or not isinstance(g.params, dict) for g in gives.values()):
            continue
        asked = e.params.get('Actor') if isinstance(e.params, dict) else None
        # "doesn't have it" gives the item asked about, "has it" another one, and both lead on to the same step
        if list(e.params) == ['Num', 'Actor'] and e.params['Num'] == 1 and isinstance(asked, str) \
                and gives[1].params.get('ActorName') == asked and gives[0].params.get('ActorName') != asked \
                and gives[0].next == gives[1].next and gives[0].entry == gives[1].entry:
            return fc.actors[e.actor], evfl.Params(e.params), 0, 1
    raise SystemExit('%s: no %s.%s switch between two calls of %s found (game files differ from what this was '
                     'made for)' % (GIFT_PAIR_FLOW, GIFT_PAIR_ACTOR, GIFT_PAIR_QUERY, GIFT_FLOW))


def level_switch(fc, levels, gives, template, asked):
    """the game's inventory questions (template: gift_pair_template) in front of one event per level of a family,
    gives[k] giving levels[k], asked as gift_pair_edit asks them: "has Second?" yes -> Third's event, no -> "has
    First?" yes -> Second's, no -> First's. asked(item): the name the inventory knows it by. Returns (the question
    asked first, or gives[0] for one level; the questions, the lowest level's first)"""
    actor, params, has, has_not = template
    top, questions = gives[0], []
    for k in range(1, len(levels)):
        ask = evfl.Params(params)
        ask['Actor'] = asked(levels[k - 1])
        top = fc.add_switch(flow_copy_actor(fc, actor), GIFT_PAIR_QUERY, [(has, gives[k]), (has_not, top)], ask)
        questions.append(top)
    return top, questions


def level_reached(fc, start, owned, template):
    """the event the game's inventory questions from `start` lead to while Link owns `owned` (the names the
    inventory knows the items by): follows every PouchSystemActor.EventQueryIsExistInPouch switch it meets"""
    _, _, has, has_not = template
    i, seen = start, set()
    while i is not None and fc.events[i].type == 'switch' \
            and fc.actors[fc.events[i].actor].name == GIFT_PAIR_ACTOR \
            and fc.actors[fc.events[i].actor].queries[fc.events[i].query] == GIFT_PAIR_QUERY:
        if i in seen:
            raise SystemExit('the questions from event %s go round in a circle' % fc.events[start].name)
        seen.add(i)
        e = fc.events[i]
        i = dict(e.cases)[has if e.params.get('Actor') in owned else has_not]
    return i


def gift_pair_edit(fc, events, template, direct=(), asked=None):
    """a progressive pair or a three-level family on gift events. events: {event name: (check id, levels)},
    levels: (first, second) or (first, second, third); each event already gives First (gift_edit: a call of
    Dm_SY_GetInEvent, or of GetPouchContent for an item in `direct`, one Link can't hold up). In front of it goes
    the game's question "does Link have First?" (template: gift_pair_template; the PouchSystemActor entry is
    added as the game's flow has it when this flow has none): no -> the event as it is (First), yes -> a new
    copy of that call naming Second, leading on to the same step. Three levels: in front of that question one
    more, "does Link have Second?": no -> the question about First, yes -> a copy of the call naming Third.
    Every link to the gift event (a step before it, a branch, a fork, an entry point) now goes to the question
    asked first. asked(item): the name the inventory knows an item by, the one the game's flows ask about
    (ActorInfo: ActorName; default: the item's own).
    What First needs to be usable (SCRUB_COMPANIONS: the small seed bag of the Fairy Slingshot, the small quiver
    of the Fairy Bow; the game's chests add them, this event doesn't) is added silently right after First's
    call, as the scrubs' sales do; also for a gift of one level, levels (first,), which gets no question.
    Returns (lines saying what was changed, {event name: the names of its new events: for each later level the
    question and the call, lowest level first, then the companions' adds}))."""
    actor, params, has, has_not = template
    asked = asked or (lambda item: item)
    said, made = [], {}
    for ev, (cid, levels) in sorted(events.items()):
        first = levels[0]
        i = next((k for k, e in enumerate(fc.events) if e.name == ev), None)
        if i is None:
            raise SystemExit('%s: event %s not in the flow' % (cid, ev))
        e = fc.events[i]
        how = DIRECT_GET[0] if first in direct else GIFT_FLOW
        if e.type != 'subflow' or e.flowchart != how or not isinstance(e.params, dict) \
                or e.params.get('ActorName') != first:
            raise SystemExit('%s: event %s is not the call that gives %s' % (cid, ev, first))
        for later in levels[1:]:
            if (first in direct) != (later in direct):
                raise SystemExit('%s: %s and %s are not given the same way (one is held up, the other only has '
                                 'the get window): not as a pair on a gift' % (cid, first, later))
            if SCRUB_COMPANIONS.get(later):
                raise SystemExit('%s: %s: a later level that needs another item given with it is not supported '
                                 'on a gift' % (cid, '>'.join(levels)))
        lead = e.next                                  # where every level's call leads on to
        names, questions, top = [], [], i
        for k in range(1, len(levels)):
            give = evfl.Params(e.params)
            give['ActorName'] = levels[k]
            yes = fc.add_subflow(e.flowchart, e.entry, give, next=lead)
            ask = evfl.Params(params)
            ask['Actor'] = asked(levels[k - 1])
            below = top
            top = fc.add_switch(flow_copy_actor(fc, actor), GIFT_PAIR_QUERY, [(has, yes), (has_not, below)], ask)
            questions.append((top, yes, below, dict(ask)))
            names += [fc.events[top].name, fc.events[yes].name]
        moved = 0
        if questions:
            moved = fc.repoint(i, top, keep=[q for q, _, _, _ in questions])
            if not moved:
                raise SystemExit('%s: nothing leads to event %s' % (cid, ev))
        for k, (q, yes, below, ask) in enumerate(questions, 1):
            if k == 1:
                said.append('%-18s %s: asks first (%s: %s.%s %s): Link has no %s -> %s gives %s, else %s gives %s '
                            '(%s<%s>)%s'
                            % (cid, ev, fc.events[q].name, GIFT_PAIR_ACTOR, GIFT_PAIR_QUERY, ask, first, ev, first,
                               fc.events[yes].name, levels[k], e.flowchart, e.entry,
                               '; %d link%s moved to the question' % (moved, '' if moved == 1 else 's')
                               if len(questions) == 1 else ''))
            else:
                said.append('%-18s %s: three levels: asks before that (%s: %s.%s %s): Link has no %s -> the '
                            'question above (%s), else %s gives %s; %d link%s moved to this question'
                            % (cid, ev, fc.events[q].name, GIFT_PAIR_ACTOR, GIFT_PAIR_QUERY, ask, levels[k - 1],
                               fc.events[below].name, fc.events[yes].name, levels[k], moved,
                               '' if moved == 1 else 's'))
        comes, nxt = [], lead
        for companion in reversed(SCRUB_COMPANIONS.get(first, [])):
            nxt = fc.add_action(flow_copy_actor(fc, actor), CUTSCENE_ADD[1],
                                evfl.Params(Num=1, Actor=companion, IsGetEvent=False,
                                            IsSetMessageTargetActorName=False, IsEquipDIrect=False), next=nxt)
            comes.insert(0, fc.events[nxt].name)
            said.append('%-18s %s: %s comes with %s, added right after it (%s)'
                        % (cid, ev, companion, first, fc.events[nxt].name))
        e.next = nxt
        made[ev] = tuple(names) + tuple(comes)
    fc.update_entry_points()
    return said, made


def gift_pair_read_back(path, before, after, events, made, template, asked=None):
    """the flow written (after) against the flow before the pair went in: the same events, actors and entry
    points, but: two new events per later level of each gift (the question and that level's call, as intended),
    the links to the gift now on the question asked first, the companions' adds between First's call and what
    it led on to, PouchSystemActor (added when the flow had none) with the query and the add, and the entry
    points' lists of calls with the new calls added"""
    bad = lambda what: SystemExit('read-back: %s: %s' % (path, what))   # noqa: E731
    actor, params, has, has_not = template
    asked = asked or (lambda item: item)
    old = {e.name: e for e in before.events}
    new = {e.name: e for e in after.events}
    added = [n for names in made.values() for n in names]
    n_asks = {ev: len(levels) - 1 for ev, (_, levels) in events.items()}
    comes_of = {ev: list(made[ev][2 * n_asks[ev]:]) for ev in events}
    if set(new) != set(old) | set(added) or set(old) & set(added) or len(set(added)) != len(added) \
            or set(made) != set(events) \
            or any(len(comes_of[ev]) != len(SCRUB_COMPANIONS.get(levels[0], [])) or len(made[ev]) < 2 * n_asks[ev]
                   for ev, (_, levels) in events.items()):
        raise bad('events differ from what was intended')
    name_of = lambda fc, i: None if i is None else fc.events[i].name   # noqa: E731
    to_q = {ev: made[ev][2 * n_asks[ev] - 2] for ev in events if n_asks[ev]}   # the question asked first

    def shape(fc, e, moved=False):
        sw = (lambda n: to_q.get(n, n)) if moved else (lambda n: n)   # noqa: E731
        a = fc.actors[e.actor] if e.type in ('action', 'switch') else None
        return (e.type, (a.name, a.secondary) if a else None,
                a.actions[e.action] if e.type == 'action' else None,
                a.queries[e.query] if e.type == 'switch' else None,
                e.params, e.flowchart, e.entry, e.value, sw(name_of(fc, e.next)), sw(name_of(fc, e.join)),
                [(v, sw(name_of(fc, c))) for v, c in e.cases], [sw(name_of(fc, f)) for f in e.forks])

    for name, o in old.items():
        got, want = shape(after, new[name]), shape(before, o, moved=True)
        if comes_of.get(name):                         # the gift's call leads on to its companions first
            if got[8] != comes_of[name][0]:
                raise bad('%s does not lead on to what comes with its item' % name)
            got = got[:8] + (want[8],) + got[9:]
        if got != want:
            raise bad('%s differs from what was intended' % name)
    for ev, (cid, levels) in events.items():
        gift = new[ev]
        lead = shape(before, old[ev], moved=True)[8]   # what the gift led on to
        below = ev
        for k in range(1, len(levels)):
            q, yes = new[made[ev][2 * k - 2]], new[made[ev][2 * k - 1]]
            qa = after.actors[q.actor] if q.type == 'switch' else None
            if qa is None or (qa.name, qa.secondary, qa.queries[q.query]) != (GIFT_PAIR_ACTOR, '', GIFT_PAIR_QUERY) \
                    or list(q.params.items()) != [(key, asked(levels[k - 1]) if key == 'Actor' else v)
                                                  for key, v in params.items()] \
                    or [(v, name_of(after, c)) for v, c in q.cases] != [(has, yes.name), (has_not, below)]:
                raise bad('the question in front of %s is not as intended' % ev)
            want = evfl.Params(gift.params)
            want['ActorName'] = levels[k]
            if yes.type != 'subflow' or (yes.flowchart, yes.entry) != (gift.flowchart, gift.entry) \
                    or name_of(after, yes.next) != lead or list(yes.params.items()) != list(want.items()):
                raise bad('the calls behind the questions of %s are not as intended' % ev)
            below = q.name
        if gift.params.get('ActorName') != levels[0]:
            raise bad('%s does not give %s' % (ev, levels[0]))
        at = gift
        for companion, name in zip(SCRUB_COMPANIONS.get(levels[0], []), comes_of[ev]):
            x = new[name]
            if name_of(after, at.next) != name or x.type != 'action' \
                    or (after.actors[x.actor].name, after.actors[x.actor].secondary, _action_name(after, x)) \
                    != (CUTSCENE_ADD[0], '', CUTSCENE_ADD[1]) \
                    or dict(x.params) != {'Num': 1, 'Actor': companion, 'IsGetEvent': False,
                                          'IsSetMessageTargetActorName': False, 'IsEquipDIrect': False}:
                raise bad('what comes with the item of %s is not added as intended' % ev)
            at = x
        if name_of(after, at.next) != lead:
            raise bad('%s does not lead on as it did' % ev)
    was = [(a.name, a.secondary, a.argument, a.actions, a.queries, a.params, a.entry_point, a.cut)
           for a in before.actors]
    now = [(a.name, a.secondary, a.argument, a.actions, a.queries, a.params, a.entry_point, a.cut)
           for a in after.actors]
    k = next((n for n, a in enumerate(before.actors) if a.name == GIFT_PAIR_ACTOR and not a.secondary), None)
    if k is None:
        was.append((actor.name, '', '', [], [], actor.params, None, actor.cut))
        k = len(was) - 1
    actions, queries = list(was[k][3]), list(was[k][4])
    if any(n_asks.values()) and GIFT_PAIR_QUERY not in queries:
        queries.append(GIFT_PAIR_QUERY)
    if any(comes_of.values()) and CUTSCENE_ADD[1] not in actions:
        actions.append(CUTSCENE_ADD[1])
    was[k] = was[k][:3] + (actions, queries) + was[k][5:]
    if now != was:
        raise bad('actors differ from what was intended')
    if [p.name for p in after.entry_points] != [p.name for p in before.entry_points]:
        raise bad('entry points differ')
    for p, o in zip(after.entry_points, before.entry_points):
        calls = [name_of(before, i) for i in o.subflows]
        extra = [made[n][2 * k - 1] for n in calls if n in made for k in range(1, n_asks[n] + 1)]
        got = [name_of(after, i) for i in p.subflows]
        if to_q.get(name_of(before, o.main), name_of(before, o.main)) != name_of(after, p.main) \
                or got[:len(calls)] != calls or sorted(got[len(calls):]) != sorted(extra):
            raise bad('entry point %s differs from what was intended' % p.name)


# Songs as items: their actors (Item_Melody_*) borrow the rupee model (Obj_Rupee), so a song held up, on a
# shelf or on the ground showed a green rupee (seen in game). The game has no note model; they take Sheik's
# harp instead (model project Item_Harp_Sheik, as the cutscene actor Dm_Item_Sheik_Harp has it; the user's
# choice): the song's model settings and its ActorInfo row (model, size, the larger of the two heaps).
SONG_PREFIX = 'Item_Melody_'
HARP_ACTOR, HARP_MODEL = 'Dm_Item_Sheik_Harp', 'Item_Harp_Sheik'
# the item whose animation components the songs take for the spin (harp_colors); its row also gives them the
# animation list and the heaps such an item needs (2026-11-18: without them the game crashed creating the songs)
SPIN_LIKE = 'Item_Boomerang'
ACTOR_INFO = 'RSDB/ActorInfo.Product.111.rstbl.byml'


def song_harp_rows(data, songs, models=None, anim_projects=()):
    """ActorInfo rows of `songs` take the harp's model, size and (the larger) heaps; models {song: model name}:
    a song with a harp variant of its own (tools/harp_colors.py) takes that model name; anim_projects: the songs'
    animation projects (the spin, the resting pose), listed in their rows as SPIN_LIKE lists its own, with the
    heaps at least SPIN_LIKE's; read back"""
    doc = byml.loads(data)
    rows = {str(r['__RowId']): r for r in doc.root}
    harp = rows.get(HARP_ACTOR)
    if harp is None or harp.get('ModelProjectName') != HARP_MODEL:
        raise SystemExit('%s: no %s row with the model %s' % (ACTOR_INFO, HARP_ACTOR, HARP_MODEL))
    like = rows.get(SPIN_LIKE)
    if anim_projects and (like is None or not like.get('AnimationResources')):
        raise SystemExit('%s: no %s row with an animation list' % (ACTOR_INFO, SPIN_LIKE))
    want = {}
    for i, r in enumerate(doc.root):
        name = str(r['__RowId'])
        if name not in songs:
            continue
        if r.get('ModelProjectName') != 'Obj_Rupee':
            raise SystemExit('%s: %s has the model %r, expected Obj_Rupee' % (ACTOR_INFO, name, r.get('ModelProjectName')))
        new = type(r)(r)
        for k in ('FmdbName', 'ModelProjectName', 'ModelAabbMax', 'ModelAabbMin'):
            new[k] = harp[k]
        if name in (models or {}):
            new['FmdbName'] = type(harp['FmdbName'])(models[name])
        for k in ('InstanceHeapSize', 'PreActorRenderInfoHeapSize'):
            new[k] = type(r[k])(max(int(r[k]), int(harp[k]), int(like[k]) if anim_projects else 0))
        if anim_projects:
            if 'AnimationResources' in r:
                raise SystemExit('%s: %s already has an animation list' % (ACTOR_INFO, name))
            res = like['AnimationResources']
            entries = []
            for project in anim_projects:
                entry = type(res[0])(res[0])
                entry['ModelProjectName'] = type(res[0]['ModelProjectName'])(project)
                entries.append(entry)
            new['AnimationResources'] = type(res)(entries)
        doc.root[i] = new
        want[name] = dict(new)
    if set(want) != set(songs):
        raise SystemExit('%s: rows not found: %s' % (ACTOR_INFO, ', '.join(sorted(set(songs) - set(want)))))
    out = byml.dumps(doc)
    back = {str(r['__RowId']): r for r in byml.loads(out).root}
    before = {str(r['__RowId']): r for r in byml.loads(data).root}
    if set(back) != set(before) or any(back[n] != (want.get(n) or before[n]) for n in back):
        raise SystemExit('read-back: %s differs from what was intended' % ACTOR_INFO)
    return out


MAGIC_BLESSINGS = ('Item_FairyBless_MP', 'Pouch_FairyBless_MP', 'Item_FairyBless_MPDouble', 'Pouch_FairyBless_MPDouble')


def song_spin_files(boomerang_pack):
    """the files a song's pack gets for the spin (harp_colors): the Boomerang's animation settings file (ASInfo
    Item_GetDemo) as it is, and an animation list of the songs' own (from the Boomerang's: only
    harp_colors.SPIN_PROJECTS, the game's Item_Common_Animation)"""
    files = sarc.Sarc.read(boomerang_pack).files
    doc = byml.loads(files[harp_colors.ANIM_PARAM_LIKE])
    res = doc.root['AnimationResources']
    if [str(r['ModelProjectName']) for r in res][:1] != [harp_colors.ANIM_PROJECT]:
        raise SystemExit('%s: animations %r, expected %s first' % (harp_colors.ANIM_PARAM_LIKE, res,
                                                                    harp_colors.ANIM_PROJECT))
    first = res[0]
    res[:] = []
    for project in harp_colors.SPIN_PROJECTS:
        entry = type(first)(first)
        entry['ModelProjectName'] = type(first['ModelProjectName'])(project)
        res.append(entry)
    out = byml.dumps(doc)
    if [str(r['ModelProjectName']) for r in byml.loads(out).root['AnimationResources']] != list(
            harp_colors.SPIN_PROJECTS):
        raise SystemExit('read-back: the animation list of the songs')
    return {harp_colors.AS_INFO: files[harp_colors.AS_INFO], harp_colors.ANIM_PARAM: out}


def song_spin_pack(pack_data, song, spin):
    """a song's pack with the animation components (ASInfoRef, ASRef, AnimationRef) and their files (spin:
    song_spin_files); returns (new pack, (actor file's path, its contents before, after)); read back"""
    archive = sarc.Sarc.read(pack_data)
    inner = 'Actor/%s.engine__actor__ActorParam.bgyml' % song
    if inner not in archive.files or set(spin) & set(archive.files):
        raise SystemExit('%s: pack not as expected (no %s, or the spin files already there)' % (song, inner))
    old_inner = archive.files[inner]
    doc = byml.loads(old_inner)
    comps = doc.root['Components']
    add = {'ASInfoRef': '?' + harp_colors.AS_INFO, 'ASRef': '?' + harp_colors.AS_REF,
           'AnimationRef': '?' + harp_colors.ANIM_PARAM}
    if set(add) & set(comps):
        raise SystemExit('%s: already has %s' % (song, sorted(set(add) & set(comps))))
    kind = type(comps['ModelInfoRef'])
    for k, v in add.items():
        comps[k] = kind(v)
    new_inner = byml.dumps(doc)
    archive.files[inner] = new_inner
    archive.files.update(spin)
    new_pack = archive.write()
    back, before = sarc.Sarc.read(new_pack).files, sarc.Sarc.read(pack_data).files
    if set(back) != set(before) | set(spin) or any(back[n] != before[n] for n in before if n != inner) or             any(back[n] != spin[n] for n in spin):
        raise SystemExit('read-back: %s pack' % song)
    want = byml.loads(old_inner).root
    want['Components'].update(add)
    if byml.loads(back[inner]).root != want:
        raise SystemExit('read-back: %s differs from what was intended' % inner)
    return new_pack, (inner, old_inner, new_inner)


def magic_is_separate(data):
    """item table (RSDB/PouchActorInfo): every item that raises the magic meter (ExpansionAvility MPMaxUP:
    Lens of Truth, Din's Fire, Farore's Wind, Nayru's Love, magic arrows) stops doing so, except the Great
    Fairy's magic blessings, which become the magic items of their own"""
    doc = byml.loads(data)
    changed = []
    for i, row in enumerate(doc.root):
        if row.get('ExpansionAvility') == 'MPMaxUP' and row['__RowId'] not in MAGIC_BLESSINGS:
            row = type(row)(row)                      # own copy (shared nodes)
            del row['ExpansionAvility']
            row.pop('MPMax', None)
            doc.root[i] = row
            changed.append(row['__RowId'])
    blessings = [r['__RowId'] for r in doc.root if r['__RowId'] in MAGIC_BLESSINGS and r.get('ExpansionAvility') == 'MPMaxUP']
    if sorted(blessings) != sorted(MAGIC_BLESSINGS):
        raise SystemExit('magic blessings not found as expected: %s' % blessings)
    new = byml.dumps(doc)
    # read back: only those rows lost those two keys
    old_rows = byml.loads(data).root
    new_rows = byml.loads(new).root
    if len(old_rows) != len(new_rows):
        raise SystemExit('read-back: row count changed')
    for o, n in zip(old_rows, new_rows):
        want = dict(o)
        if o['__RowId'] in changed:
            del want['ExpansionAvility']
            want.pop('MPMax', None)
        if n != want:
            raise SystemExit('read-back: row %s differs from what was intended' % o['__RowId'])
    return new, changed


BOMBCHU_MAX = 50
BOMBCHU_ROW = 'Item_Bombchu'                     # the Bombchu itself; bundles and shelves give it (BundleActor)
BOMBCHU_ACTOR = 'Work/Actor/Item_Bombchu.engine__actor__ActorParam.gyml'


def bombchus_without_bag(data):
    """item table (RSDB/PouchActorInfo): Bombchus' maximum stops being the bomb bag's (MaxNumGameData: Bomb,
    SmallBagActor: the small bomb bag) and becomes a fixed number (FixedMaxNum, as the Magic Beans' 10 and the
    Gold Skulltula tokens' 100); the bomb bags stop raising (ExpansionMaxNumActor) and refilling
    (ActorFullOnlyIfIsGetWhenGetBag) Bombchus. Rows that give one Bombchu with the bag's maximum
    (Item_Bombchu, the 1-Bombchu shelf Shop_BombchuBundle_03) change the same way."""
    doc = byml.loads(data)
    rows = {r['__RowId']: r for r in doc.root}
    fixed_type = type(rows['Item_MagicBean']['FixedMaxNum'])
    want = {}
    for i, row in enumerate(doc.root):
        rid, new = row['__RowId'], None
        if 'Bombchu' in rid and row.get('MaxNumGameData') == 'Bomb':
            new = type(row)(row)
            del new['MaxNumGameData']
            new.pop('SmallBagActor', None)
            new['FixedMaxNum'] = fixed_type(BOMBCHU_MAX)
        elif (BOMBCHU_ACTOR in str(row.get('ExpansionMaxNumActor', ''))
              or row.get('ActorFullOnlyIfIsGetWhenGetBag') == BOMBCHU_ACTOR):
            new = type(row)(row)
            if 'ExpansionMaxNumActor' in new:
                kept = [x for x in str(new['ExpansionMaxNumActor']).split(',') if x != BOMBCHU_ACTOR]
                new['ExpansionMaxNumActor'] = type(row['ExpansionMaxNumActor'])(','.join(kept))
            if new.get('ActorFullOnlyIfIsGetWhenGetBag') == BOMBCHU_ACTOR:
                del new['ActorFullOnlyIfIsGetWhenGetBag']
        if new is not None:
            doc.root[i] = new
            want[rid] = dict(new)
    if BOMBCHU_ROW not in want:
        raise SystemExit('bombchus_without_bag: %s not as expected' % BOMBCHU_ROW)
    new_data = byml.dumps(doc)
    for o, n in zip(byml.loads(data).root, byml.loads(new_data).root):
        if n != want.get(o['__RowId'], dict(o)):
            raise SystemExit('read-back: row %s differs from what was intended' % o['__RowId'])
    return new_data, sorted(want)


# name -> (file, function(data) -> (new data, list of what changed))
TABLE_FIXES = {
    'bombchus_without_bag': ('RSDB/PouchActorInfo.Product.111.rstbl.byml', bombchus_without_bag),
    'magic_is_separate': ('RSDB/PouchActorInfo.Product.111.rstbl.byml', magic_is_separate),
}


# The rock circle by Mido's house (--fix kokiri_circle_after_dungeons). Its level logic module shows the ring of
# 8 rocks, and to an adult before the Forest Temple 4 other rocks instead: one AND node (adult, and the flag
# SageOfForest_IsBefore_Step08) deletes the 8 and creates the 4. Its flag input becomes "is child": an adult
# is never a child, so the AND is never true and both ages get the 8. The Kokiri who tries to lift the middle
# rock does so in his default schedule; after the Kokiri Emerald (Get_StoneOfForest_IsCompleted_Exp) his
# schedule sends him elsewhere. That schedule becomes his default. The middle rock is two rocks in one place:
# a prop with no lift setting (Obj_LiftRock_A_02, the one he acts out lifting) and a liftable one; a child
# level logic swaps the prop for the liftable rock after the Kokiri Emerald. Both get fixed values: prop
# never there, liftable rock always there.
CIRCLE_MIDDLE = 'Logic/KokiriForest_Child_Level_All_02_6960.logic.module.ainb'
CIRCLE_MIDDLE_ROCKS = {'Obj_LiftRock_A_02_2143': False, 'Obj_LiftRock_A_01_0de2': True}   # instance -> there
CIRCLE_NEEDS_FIX = ('KF_CIRCLE_ADULT_ROCK_', 'KF_CIRCLE_CENTER_ROCK', 'KF_CIRCLE_KOKIRI_GIFT')
CIRCLE_LOGIC = 'Logic/KokiriForest_Common_Level_All_01_6aaf.logic.module.ainb'
CIRCLE_FLAG = 'SageOfForest_IsBefore_Step08'
CIRCLE_KOKIRI = 'Component/AIScheduleParam/Npc_Kokiri_008_Child.game__component__AIScheduleParam.bgyml'
CIRCLE_KOKIRI_FLAG = 'Get_StoneOfForest_IsCompleted_Exp'


def circle_logic(data):
    """the AND node's flag input becomes the "is child" output of the same age node"""
    a = ainb.Ainb.read(data)
    hits = []
    for i, n in enumerate(a.nodes):
        if n.name != 'OperateAND' or not n.inputs['bool'] or n.inputs['bool'][0].sources is None:
            continue
        src = n.inputs['bool'][0].sources
        names = [a.nodes[s[0]].name for s in src]
        if names == ['HoldIsChildhoodOrAdulthood', 'HoldGameDataGetBoolSimple'] and                 a.nodes[src[1][0]].inputs['string'][0].value == CIRCLE_FLAG:
            hits.append(i)
    if len(hits) != 1:
        raise SystemExit('%s: %d AND nodes on age and %s, expected 1' % (CIRCLE_LOGIC, len(hits), CIRCLE_FLAG))
    inp = a.nodes[hits[0]].inputs['bool'][0]
    age, (flag_node, _, flags) = inp.sources[0], inp.sources[1]
    outs = [o.name for o in a.nodes[age[0]].outputs['bool']]
    if outs != ['Adulthood', 'Childhood'] or age[1] != 0:
        raise SystemExit('%s: age node not as expected: %r' % (CIRCLE_LOGIC, outs))
    inp.sources = [age, (age[0], outs.index('Childhood'), flags)]
    new = a.write()
    b = ainb.Ainb.read(new)
    if b.nodes[hits[0]].inputs['bool'][0].sources != inp.sources or len(new) != len(data)             or sum(x != y for x, y in zip(new, data)) > 4 or b.write() != new:
        raise SystemExit('read-back: %s differs from what was intended' % CIRCLE_LOGIC)
    return new, 'node %d (%s): source %d (%s) -> %d.Childhood' % (hits[0], a.nodes[hits[0]].name, flag_node,
                                                                 CIRCLE_FLAG, age[0])


def circle_middle(data):
    """the middle rock's two actors: created / deleted by fixed values instead of by the Kokiri Emerald"""
    a = ainb.Ainb.read(data)
    done = []
    for n in a.nodes:
        if n.name != 'ActorLogicLiftableActor':
            continue
        inst = next(x.value for x in n.immediates['string'] if x.name == 'InstanceName')
        if inst not in CIRCLE_MIDDLE_ROCKS:
            continue
        there = CIRCLE_MIDDLE_ROCKS[inst]
        flag = [x for x in n.inputs['bool'] if x.name in ('Logic_Create', 'Logic_Delete')]
        if len(flag) != 2 or any(x.node < 0 or x.sources is not None for x in flag) or                 {a.nodes[x.node].name for x in flag} != {'OperateAND'}:
            raise SystemExit('%s: %s not as expected' % (CIRCLE_MIDDLE, inst))
        for x in flag:
            x.node, x.param, x.flags = -1, 0, 0x1800000         # as the game's own fixed inputs
            x.value = there if x.name == 'Logic_Create' else not there
        n.links[0] = [l for l in n.links[0] if l.name not in ('Logic_Create', 'Logic_Delete')]
        n.preconditions = []
        done.append(inst)
    if sorted(done) != sorted(CIRCLE_MIDDLE_ROCKS):
        raise SystemExit('%s: middle rocks found: %r' % (CIRCLE_MIDDLE, done))
    new = ainb.Ainb.read(a.write()).write()
    b = ainb.Ainb.read(new)
    for n in b.nodes:
        inst = next((x.value for x in n.immediates['string'] if x.name == 'InstanceName'), None)
        if inst in CIRCLE_MIDDLE_ROCKS:
            got = {x.name: (x.node, x.value) for x in n.inputs['bool']}
            if got['Logic_Create'] != (-1, CIRCLE_MIDDLE_ROCKS[inst]) or                     got['Logic_Delete'] != (-1, not CIRCLE_MIDDLE_ROCKS[inst]) or n.links[0] or n.preconditions:
                raise SystemExit('read-back: %s differs from what was intended' % CIRCLE_MIDDLE)
    return new


def circle_kokiri(data):
    """the Kokiri's schedule after the Kokiri Emerald becomes his default one"""
    doc = byml.loads(data)
    hits = [c for c in doc.root['ConditionalSchedule'] if c.get('ConditionFlag') == CIRCLE_KOKIRI_FLAG]
    if len(hits) != 1 or 'Act_Lift_Rock' not in repr(doc.root['DefaultSchedule']):
        raise SystemExit('%s: schedule not as expected' % CIRCLE_KOKIRI)
    after = {k: v for k, v in hits[0].items() if k != 'ConditionFlag'}
    if sorted(after) != sorted(doc.root['DefaultSchedule']):
        raise SystemExit('%s: the schedules have different keys' % CIRCLE_KOKIRI)
    doc.root['DefaultSchedule'] = after
    new = byml.dumps(doc)
    want = byml.loads(data).root
    want['DefaultSchedule'] = {k: v for k, v in want['ConditionalSchedule'][doc.root['ConditionalSchedule'].index(
        hits[0])].items() if k != 'ConditionFlag'}
    if byml.loads(new).root != want:
        raise SystemExit('read-back: %s differs from what was intended' % CIRCLE_KOKIRI)
    return new


# The Forest Temple's Bow room (--fix forest_temple_bow_room_door, decision 39). Its level logic module locks
# the west shutter (DungeonSwitchShutterWithLockSet, input LockMinusZ) while an OR node is false: the flag
# Gimmick_DefeatEnemy_Open_ForestTemple_03, or the "focus on gimmick" event that sets it. That event plays when
# the eye switch is on and the chest has appeared, and the eye switch is behind bars: an arrow only. The OR's
# second source becomes "the chest has appeared" (the module's own OR of the flag
# ForestTemple_After_Appearance_TreasureChest and the chest module's EventFinish), so the shutter unlocks with
# the chest, as the first Stalfos room's does (ForestTemple_Level_Room_06_Prefab_61dc: LockMinusZ from an OR of
# its chest module's event and its flag). Shooting the eye switch still plays its event and sets its flag.
BOW_ROOM_LOGIC = 'Logic/ForestTemple_Level_Room_06_Prefab_6b8c.logic.module.ainb'
BOW_ROOM_OPEN_FLAG = 'Gimmick_DefeatEnemy_Open_ForestTemple_03'
BOW_ROOM_CHEST_FLAG = 'ForestTemple_After_Appearance_TreasureChest'


def _flag_of(node):
    """the flag a HoldGameDataGetBoolSimple node reads, or None"""
    if node.name != 'HoldGameDataGetBoolSimple' or not node.inputs['string']:
        return None
    return node.inputs['string'][0].value


def bow_room_parts(a):
    """(the OR node the shutter's lock hangs on, the "chest has appeared" node, its True output) of the Bow
    room's logic module, each found by what it is"""
    def one(what, found):
        if len(found) != 1:
            raise SystemExit('%s: %d %s, expected 1' % (BOW_ROOM_LOGIC, len(found), what))
        return found[0]
    shutter = one('shutter modules', [n for n in a.nodes if n.name.startswith('DungeonSwitchShutterWithLockSet')])
    lock = one('LockMinusZ inputs', [x for x in shutter.inputs['bool'] if x.name == 'LockMinusZ'])
    if lock.node < 0 or lock.sources is not None or a.nodes[lock.node].name != 'OperateORFixInputTrue' \
            or [o.name for o in a.nodes[lock.node].outputs['bool']][lock.param] != 'False':
        raise SystemExit('%s: the shutter\'s lock is not the False output of an OR node' % BOW_ROOM_LOGIC)
    appeared = one('"chest has appeared" nodes', [
        i for i, n in enumerate(a.nodes)
        if n.name == 'OperateOR' and n.inputs['bool'] and n.inputs['bool'][0].sources is not None
        and len(n.inputs['bool'][0].sources) == 2
        and _flag_of(a.nodes[n.inputs['bool'][0].sources[0][0]]) == BOW_ROOM_CHEST_FLAG
        and a.nodes[n.inputs['bool'][0].sources[1][0]].name.startswith('Gimmick_TreasureBoxAppear')
        and [o.name for o in a.nodes[n.inputs['bool'][0].sources[1][0]].outputs['bool']][
            n.inputs['bool'][0].sources[1][1]] == 'EventFinish'])
    return lock.node, appeared, [o.name for o in a.nodes[appeared].outputs['bool']].index('True')


def bow_room_door(data):
    """the shutter's lock: "the flag, or the eye switch's event" becomes "the flag, or the chest has appeared";
    returns (new data, what was done)"""
    a = ainb.Ainb.read(data)
    lock, appeared, true = bow_room_parts(a)
    n = a.nodes[lock]
    inp = n.inputs['bool'][0]
    if inp.name != 'BoolMulti' or inp.sources is None or len(inp.sources) != 2 \
            or _flag_of(a.nodes[inp.sources[0][0]]) != BOW_ROOM_OPEN_FLAG \
            or not a.nodes[inp.sources[1][0]].name.startswith('Gimmick_FocusOnGimmick') \
            or len(n.links[0]) != 1 or n.links[0][0].node != inp.sources[1][0] \
            or sorted(n.preconditions) != sorted(s[0] for s in inp.sources):
        raise SystemExit('%s: the lock\'s OR node is not "the flag %s, or the focus event"'
                         % (BOW_ROOM_LOGIC, BOW_ROOM_OPEN_FLAG))
    flag, (event, _, flags) = inp.sources
    inp.sources = [flag, (appeared, true, flags)]
    n.links[0][0].node = appeared
    n.preconditions = [appeared if p == event else p for p in n.preconditions]
    new = a.write()
    b = ainb.Ainb.read(new)
    m = b.nodes[lock]
    if m.inputs['bool'][0].sources != inp.sources or m.links[0][0].node != appeared \
            or m.preconditions != n.preconditions or len(new) != len(data) or b.write() != new \
            or len(b.nodes) != len(a.nodes) \
            or sum(x != y for x, y in zip(new, data)) > 8:
        raise SystemExit('read-back: %s differs from what was intended' % BOW_ROOM_LOGIC)
    return new, 'node %d (%s): source %d (%s) -> %d.True (the chest has appeared)' % (
        lock, n.name, event, a.nodes[event].name, appeared)


def remove_entry(data, keys, expected):
    """remove one entry (found by its path of keys) from a BYML file; checks its current value first and that
    nothing else changed"""
    doc = byml.loads(data)
    parent = doc.root
    for k in keys[:-1]:
        parent = parent[k]
    if parent.get(keys[-1]) != expected:
        raise SystemExit('%s is %r, expected %r (game files differ from what this fix was made for)'
                         % ('/'.join(keys), parent.get(keys[-1]), expected))
    del parent[keys[-1]]
    new = byml.dumps(doc)
    want = byml.loads(data).root
    p = want
    for k in keys[:-1]:
        p = p[k]
    del p[keys[-1]]
    if byml.loads(new).root != want:
        raise SystemExit('read-back: %s differs from what was intended' % '/'.join(keys))
    return new


# Kokiri Shop with one set of shelves per age (--fix kokiri_shop_full_stock). What a shop sells is decided by
# its shopkeeper: its shop list (ShopParam GoodsList) has one entry per shelf, in ShopItemIndex order (the
# Recovery Heart, with no index, is 0), naming the shelf actor sold (its price), a release flag and a stock
# (-1 unlimited, 1 once). The child map has two sets of shopkeeper, shelves and boards: before meeting the
# Deku Tree (the "low on stock" shopkeeper, its own short list, two "sold out" boards) and after; the adult
# shopkeeper has no list of its own and uses the child one (a copy of the same file in its pack).
SHOP_FLAG = 'Meet_DekuTree_IsAfter_Step02_Exp'
SHOP_MAP = 'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml'
SHOP_KEEPERS = {'child': 'Npc_Kokiri_001_Shop_Child', 'adult': 'Npc_Kokiri_001_Shop_Adult'}
SHOP_LIST = 'Component/ShopParam/Npc_Kokiri_001_Shop_Child.game__component__ShopParam.bgyml'
SHOP_LIST_ADULT = 'Component/ShopParam/Npc_Kokiri_001_Shop_Adult.game__component__ShopParam.bgyml'
SHOP_STOCK_ONCE = 1
SHOP_FLOW = 'Event/EventFlow/Npc_Kokiri_001_Shop_Child.bfevfl'   # the child shopkeeper's talk
SHOP_GREETING = 'Npc_Kokiri_001_Shop_Child_Talk_Arrival'          # the switch that picks the normal greeting
FLOW_YES, FLOW_NO = 0, 1      # what a yes/no query answers in this game's event flows (0 = yes)


def _flow_links(e):
    return [x for x in [e.next, e.join] + [ev for _, ev in e.cases] + list(e.forks) if x is not None]


def flow_reachable(fc, start):
    seen, todo = [], [start]
    while todo:
        i = todo.pop(0)
        if i not in seen:
            seen.append(i)
            todo += _flow_links(fc.events[i])
    return seen


def flow_drop_unreached_subflows(fc):
    """each entry point lists the subflow / callswitch steps that can run from it: drop those no longer
    reached; returns lines saying what changed"""
    said = []
    for ep in fc.entry_points:
        can = flow_reachable(fc, ep.main)
        keep = [i for i in ep.subflows if i in can]
        if keep != ep.subflows:
            said.append('entry point %s: list %r -> %r' % (ep.name, ep.subflows, keep))
            ep.subflows = keep
    return said


def shop_greeting_edit(fc):
    """the child shopkeeper's talk (flowchart, edited in place): its one switch on meeting the Deku Tree takes
    the "after" side's normal greeting in both cases (case 1, NO, was the "low on stock / Mido" side). Skips
    only the "lost your Deku Shield?" hand-out between the switch and the greeting. Confirmed in game
    2026-11-17 (tools/evfl_test_mod.py). Returns lines saying what changed."""
    hits = [i for i, e in enumerate(fc.events)
            if e.type == 'switch' and isinstance(e.params, dict) and e.params.get('GameDataName') == SHOP_FLAG]
    if len(hits) != 1:
        raise SystemExit('%s: %d switches on %s, expected 1' % (SHOP_FLOW, len(hits), SHOP_FLAG))
    sw = fc.events[hits[0]]
    cases = dict(sw.cases)
    if sorted(cases) != [FLOW_YES, FLOW_NO]:
        raise SystemExit('%s: switch on %s: cases %r not as expected' % (SHOP_FLOW, SHOP_FLAG, sw.cases))
    hand_out = fc.events[cases[FLOW_YES]]
    if hand_out.type != 'callswitch' or hand_out.entry != 'present_DekuSheld':
        raise SystemExit('%s: the "after" side is not the Deku Shield hand-out' % SHOP_FLOW)
    greet = [ev for _, ev in hand_out.cases
             if fc.events[ev].type == 'switch' and (fc.events[ev].params or {}).get('GameDataName') == SHOP_GREETING]
    if len(greet) != 1:
        raise SystemExit('%s: normal greeting not found after the hand-out' % SHOP_FLOW)
    said = ['greeting: switch %s (%s) cases %r -> both %d' % (sw.name, SHOP_FLAG, sorted(cases.items()), greet[0])]
    sw.cases = [(FLOW_YES, greet[0]), (FLOW_NO, greet[0])]
    return said + flow_drop_unreached_subflows(fc)


def flow_write_checked(ef):
    """write an edited event flow and read it back: must be the same flow as intended"""
    fc = ef.flowchart
    new = evfl.dumps(ef)
    back = evfl.loads(new).flowchart
    if [vars(e) for e in back.events] != [vars(e) for e in fc.events]             or [vars(p) for p in back.entry_points] != [vars(p) for p in fc.entry_points]             or [vars(x) for x in back.actors] != [vars(x) for x in fc.actors]:
        raise SystemExit('read-back of an edited event flow differs from what was intended')
    return new


def _is_shop_actor(actor):
    return actor['Gyaml'].startswith(('Shop_', 'Npc_Kokiri_001_Shop'))


def shop_full_stock_map(data):
    """child map: the shop set placed before meeting the Deku Tree is removed and the set placed after it is
    always there. Returns (new data, removed hashes, hashes now always there)."""
    doc = byml.loads(data)
    keep, removed, always = [], set(), set()
    for act in doc.root['Actors']:
        pres = act.get('Presence')
        if _is_shop_actor(act) and pres is not None and pres.get('FlagName') == SHOP_FLAG:
            h = str(int(act['Hash']))
            if pres.get('IsNegation'):
                removed.add(h)
                continue
            act = type(act)(act)                      # own copy (shared nodes)
            del act['Presence']
            always.add(h)
        keep.append(act)
    if not removed or not always:
        raise SystemExit('kokiri_shop_full_stock: the two shop sets were not found as expected')
    for act in keep:                                  # nothing left may point at a removed object
        for link in act.get('Links') or []:
            if str(int(link['Dst'])) in removed:
                raise SystemExit('kokiri_shop_full_stock: %s links to a removed shop object' % act['Gyaml'])
    doc.root = type(doc.root)(doc.root)
    doc.root['Actors'] = keep
    new = byml.dumps(doc)
    want = []
    for act in byml.loads(data).root['Actors']:
        h = str(int(act['Hash']))
        if h in removed:
            continue
        want.append({k: v for k, v in act.items() if not (h in always and k == 'Presence')})
    if [dict(x) for x in byml.loads(new).root['Actors']] != want:
        raise SystemExit('read-back: %s differs from what was intended' % SHOP_MAP)
    return new, removed, always


SHOP_BOARD = 'Shop_Board_Bundle_%02d'                 # count boards: 03 05 08 10 15 20 30 50 in the game


def shop_boards(data, shelves, board_exists):
    """count boards ("x5", separate objects a shelf links to, made for its original bundle) for changed
    shelves: shelves {shelf hash: number of items it now sells}. A single item gets no board (the board and
    every link to it removed); a bundle gets the board with its own count (board_exists(name)), or none if
    the game has no such board. Returns (new data, [what changed], {shelf hash: hash of its removed board})."""
    doc = byml.loads(data)
    acts = doc.root['Actors']
    by_hash = {str(int(a['Hash'])): a for a in acts}
    linked_from = {}
    for a in acts:
        for link in a.get('Links') or []:
            linked_from.setdefault(str(int(link['Dst'])), []).append(a)
    remove, rename, done, board_of = set(), {}, [], {}
    for sh, count in shelves.items():
        for link in by_hash[sh].get('Links') or []:
            b = str(int(link['Dst']))
            board = by_hash.get(b)
            if board is None or not board['Gyaml'].startswith('Shop_Board_Bundle_'):
                continue
            shelf_links = [a for a in linked_from[b] if a['Gyaml'].startswith('Shop_') and str(int(a['Hash'])) != sh]
            if shelf_links:
                raise SystemExit('count board %s is shared with another shelf' % b)
            want = SHOP_BOARD % count if count > 1 and board_exists(SHOP_BOARD % count) else None
            if want is None:
                remove.add(b)
                board_of[sh] = b
                done.append('%s board %s removed' % (by_hash[sh]['Gyaml'], board['Gyaml']))
            elif want != board['Gyaml']:
                rename[b] = want
                done.append('%s board %s -> %s' % (by_hash[sh]['Gyaml'], board['Gyaml'], want))
    new_acts = []
    for a in acts:
        h = str(int(a['Hash']))
        if h in remove:
            continue
        links = a.get('Links') or []
        if h in rename or any(str(int(l['Dst'])) in remove for l in links):
            a = type(a)(a)
            if h in rename:
                a['Gyaml'] = type(a['Gyaml'])(rename[h])
            if any(str(int(l['Dst'])) in remove for l in links):
                a['Links'] = [l for l in links if str(int(l['Dst'])) not in remove]
        new_acts.append(a)
    doc.root = type(doc.root)(doc.root)
    doc.root['Actors'] = new_acts
    new = byml.dumps(doc)
    want = []
    for a in byml.loads(data).root['Actors']:
        h = str(int(a['Hash']))
        if h in remove:
            continue
        a = dict(a)
        if h in rename:
            a['Gyaml'] = rename[h]
        if 'Links' in a:
            a['Links'] = [l for l in a['Links'] if str(int(l['Dst'])) not in remove]
        want.append(a)
    if [dict(x) for x in byml.loads(new).root['Actors']] != want:
        raise SystemExit('read-back: count boards differ from what was intended')
    return new, done, board_of


# Shelves sold once. How the game remembers that a map object is gone: GameData/GameDataList has one saved flag
# per map placement that can be (Bool64bitKey: the key is the placement's hash), made for the placements of
# actors whose ActorGameDataSetting asks for one, with a reset type that follows that setting:
#     NoRespawn (heart pieces, Gold Skulltulas, silver rupee tokens...)   24: never reset
#     BancReset (fairies, scrubs' leaves, the shops' boards and their bottle, bomb, Bombchu, tunic and mask
#                shelves)                                                 25: until the area is left
#     SupplyObject (pots, rocks, grass) 88, BancResetNoItemWarp (enemies, Business Scrubs) 280
#     AlwaysRespawn (every other shelf, the Kokiri Shop's included): no flag at all.
# The game has no shelf that stays sold for good by itself (the Happy Mask Shop's are released by named flags).
# Our shop versions ask for NoRespawn, but their placements were made for AlwaysRespawn shelves: no flag, so the
# shelf was back after a reload (seen in game). A flag can't be added without changing the layout of the save
# file, so a changed shelf takes over the flag of a shop object this build removes anyway: its own count board
# ("x5"), else a board of the shop set removed by kokiri_shop_full_stock. The shelf's placement gets that
# object's hash (with every link to it), and the flag's reset type becomes NoRespawn's. The child and the adult
# copy of one shelf share one flag, as the game's own objects that exist at both ages share one hash (a chest,
# a hole cover in Kokiri Forest).
# Who sets the flag (2026-11-17, in game: with the flag alone the bought shelves were still back after a
# reload): not the game. A bought shelf doesn't die, its AI only hides its model while the shopkeeper counts it
# as sold, and that count starts again with every visit. A placement's flag is set by a death marked
# IsSetRespawnFlagToFalse or by the AI node OneShotActorChangeIsRespawn; the shop versions have an AI of their
# own that runs that node when the shopkeeper says "sold out" (shop_items.sold_for_good_ai). A NoRespawn
# placement whose flag is set is not made again: the shelf stays empty, which the game's shops allow (the
# Market potion shop's bug shelf is placed later than its shopkeeper).
GAME_DATA = 'GameData/GameDataList.Product.110.byml'
FLAG_KEPT, FLAG_UNTIL_LEFT = 24, 25


def placement_flags(data):
    """{placement hash: reset type} of the saved per-placement flags"""
    return {str(int(e['Hash'])): int(e['ResetTypeValue']) for e in byml.loads(data).root['Data']['Bool64bitKey']}


def keep_flags(data, hashes):
    """the per-placement flags with these hashes are never reset (reset type 24, as NoRespawn placements');
    read back: nothing else changes. Returns (new data, {hash: reset type it had})."""
    doc = byml.loads(data)
    root = type(doc.root)(doc.root)
    table = type(root['Data'])(root['Data'])
    flags = list(table['Bool64bitKey'])
    was = {}
    for i, e in enumerate(flags):
        h = str(int(e['Hash']))
        if h not in hashes:
            continue
        was[h] = int(e['ResetTypeValue'])
        if was[h] not in (FLAG_KEPT, FLAG_UNTIL_LEFT):
            raise SystemExit('%s: flag %s has reset type %d, expected %d or %d'
                             % (GAME_DATA, h, was[h], FLAG_KEPT, FLAG_UNTIL_LEFT))
        e = type(e)(e)                                # own copy (shared nodes)
        e['ResetTypeValue'] = type(e['ResetTypeValue'])(FLAG_KEPT)
        flags[i] = e
    if set(was) != set(hashes):
        raise SystemExit('%s: flags not found: %s' % (GAME_DATA, ', '.join(sorted(set(hashes) - set(was)))))
    table['Bool64bitKey'] = flags
    root['Data'] = table
    doc.root = root
    new = byml.dumps(doc)
    before, after = byml.loads(data).root, byml.loads(new).root
    if list(before) != list(after) or list(before['Data']) != list(after['Data']) \
            or any(after[k] != before[k] for k in before if k != 'Data') \
            or any(after['Data'][k] != before['Data'][k] for k in before['Data'] if k != 'Bool64bitKey') \
            or len(after['Data']['Bool64bitKey']) != len(before['Data']['Bool64bitKey']):
        raise SystemExit('read-back: %s differs from what was intended' % GAME_DATA)
    for o, n in zip(before['Data']['Bool64bitKey'], after['Data']['Bool64bitKey']):
        want = dict(o)
        if str(int(o['Hash'])) in hashes:
            want['ResetTypeValue'] = FLAG_KEPT
        if dict(n) != want:
            raise SystemExit('read-back: flag %d of %s differs from what was intended' % (int(o['Hash']), GAME_DATA))
    return new, was


def _swap_hashes(v, table, count):
    """a copy of a map value with the 64-bit hashes in `table` {old: new} replaced (count: how many of each)"""
    if isinstance(v, dict):
        new = [(k, _swap_hashes(x, table, count)) for k, x in v.items()]
        if all(x is y for (_, x), y in zip(new, v.values())):
            return v
        out = type(v)(v)
        for k, x in new:
            out[k] = x
        return out
    if isinstance(v, list):
        new = [_swap_hashes(x, table, count) for x in v]
        return v if all(x is y for x, y in zip(new, v)) else type(v)(new)
    if isinstance(v, byml.UInt64) and int(v) in table:
        count[int(v)] += 1
        return type(v)(table[int(v)])
    return v


GROUP_LISTS = ('FarDeleteGroups', 'SimultaneousGroups')   # lists of placement hashes at the top of a map file


def _take_over(root, table):
    """a copy of a map's contents where each placement in `table` {its hash: the hash it takes over} has the
    new hash wherever it is mentioned. The object that had that hash is gone from the map (removed by this
    build), but the map's group lists still name it: those stale mentions go first, or the shelf would be in
    that object's group as well as its own. Returns (new contents, {old hash: mentions changed})."""
    gone = set(table.values())
    root = type(root)(root)
    for key in GROUP_LISTS:
        if key in root:
            root[key] = [g if not any(int(h) in gone for h in g) else type(g)(h for h in g if int(h) not in gone)
                         for g in root[key]]
    left = collections.Counter()
    _swap_hashes(root, {h: h for h in gone}, left)
    if left:
        raise SystemExit('hash %s (to be taken over by a shelf) is still used in this map'
                         % ', '.join(str(h) for h in sorted(left)))
    count = collections.Counter()
    return _swap_hashes(root, table, count), count


def shelf_flag_map_edit(data, moves):
    """moves {placement hash: hash it takes over}: the placement's Hash and every mention of it in the map (its
    physics placement ID, the shopkeeper's link to the shelf, the shelf's own links, the group lists) change;
    the hash taken over must be gone from this map (but for stale mentions in the group lists, dropped). Read
    back: nothing else changes. Returns (new data, {old hash: mentions changed})."""
    table = {int(k): int(v) for k, v in moves.items()}
    if len(set(table.values())) != len(table):
        raise SystemExit('two shelves of one map would take over the same flag')
    doc = byml.loads(data)
    here = collections.Counter(int(a['Hash']) for a in doc.root['Actors'])
    for old, new in table.items():
        if here[old] != 1:
            raise SystemExit('placement %d is %d times in the map, expected once' % (old, here[old]))
        if here[new]:
            raise SystemExit('hash %d (to be taken over by shelf %d) is still a placement of this map' % (new, old))
    doc.root, count = _take_over(doc.root, table)
    out = byml.dumps(doc)
    if any(struct.pack('<Q', old) in out for old in table):
        raise SystemExit('read-back: a replaced hash is still in the map')
    want, _ = _take_over(byml.loads(data).root, table)
    back = byml.loads(out).root
    if back != want or collections.Counter(int(a['Hash']) for a in back['Actors']) != collections.Counter(
            table.get(h, h) for h in here.elements()):
        raise SystemExit('read-back: the map differs from what was intended')
    return out, {str(k): count[k] for k in table}


def lift_shelves(data, lifts):
    """raise shelf actors: lifts {hash: metres}; returns new data"""
    doc = byml.loads(data)
    acts = list(doc.root['Actors'])
    for i, act in enumerate(acts):
        h = str(int(act['Hash']))
        if h in lifts:
            act = type(act)(act)
            t = list(act['Translate'])
            t[1] = type(t[1])(float(t[1]) + lifts[h])
            act['Translate'] = t
            acts[i] = act
    doc.root = type(doc.root)(doc.root)
    doc.root['Actors'] = acts
    new = byml.dumps(doc)
    for o, n in zip(byml.loads(data).root['Actors'], byml.loads(new).root['Actors']):
        h = str(int(o['Hash']))
        want = dict(o)
        if h in lifts:
            want['Translate'] = [o['Translate'][0], float(o['Translate'][1]) + lifts[h], o['Translate'][2]]
        got = dict(n)
        if h in lifts:
            got['Translate'] = [float(x) for x in n['Translate']]
            want['Translate'] = [float(x) for x in want['Translate']]
            if any(abs(a - b) > 1e-4 for a, b in zip(got['Translate'], want['Translate'])):
                raise SystemExit('read-back: shelf %s not lifted as intended' % h)
            got['Translate'] = want['Translate']
        if got != want:
            raise SystemExit('read-back: actor %s differs from what was intended' % h)
    return new


def open_shop_list(data, goods):
    """a shop list (ShopParam) with every shelf open from the start (no release flag); goods {shelf index:
    shelf actor} replaces what those shelves sell, sold once"""
    doc = byml.loads(data)
    root = type(doc.root)(doc.root)
    entries = list(root['GoodsList'])
    if goods and max(goods) >= len(entries):
        raise SystemExit('shop list has %d shelves, shelf %d asked for' % (len(entries), max(goods)))
    stock_type = next((type(e['StockNum']) for e in entries if 'StockNum' in e), int)
    new_entries = []
    for i, e in enumerate(entries):
        e = type(e)(e)
        if 'Release' in e:
            r = type(e['Release'])(e['Release'])
            r['IsCheckReleaseGameData'] = False
            r['ReleaseGameData'] = type(r['ReleaseGameData'])('')
            e['Release'] = r
        if i in goods:
            e['Actor'] = type(e['Actor'])('Work/Actor/%s.engine__actor__ActorParam.gyml' % goods[i])
            e['StockNum'] = stock_type(SHOP_STOCK_ONCE)
        new_entries.append(e)
    root['GoodsList'] = new_entries
    doc.root = root
    new = byml.dumps(doc)
    back = byml.loads(new).root['GoodsList']
    for i, e in enumerate(back):
        if 'Release' in e and e['Release']['IsCheckReleaseGameData']:
            raise SystemExit('read-back: shop shelf %d still has a release flag' % i)
        if i in goods and (not e['Actor'].endswith('/%s.engine__actor__ActorParam.gyml' % goods[i])
                           or int(e['StockNum']) != SHOP_STOCK_ONCE):
            raise SystemExit('read-back: shop shelf %d differs from what was intended' % i)
    return new


MAP_SUFFIX = '.bcett.byml'


def map_entry(length):
    """the size table entry the game has for a map file (Banc/.../*.bcett.byml) of this many bytes: the length
    rounded up to 32, plus 264 (true of every map in the game)"""
    return (length + 31) // 32 * 32 + 264


class Output:
    """writes changed files into the mod folder and keeps the resource size table up to date"""

    def __init__(self, romfs, mod_romfs, dicts):
        self.romfs, self.mod_romfs, self.dicts = romfs, mod_romfs, dicts
        self.rraw = open(os.path.join(romfs, RESTBL_PATH), 'rb').read()
        self.table = restbl.Restbl.read(zstd.decompress(self.rraw, dicts))
        self.sizes = {}          # path -> (original length, new length, original entry, new entry)
        self.orig = {}           # path -> the game's file (what its original entry was made for)
        self.written = {}        # path -> (file as stored in the game, contents written): edited twice = read back

    def read(self, path):
        """(file as stored, contents); a few game files are stored uncompressed (no .zs); a file this build
        already changed is read back as changed"""
        if path in self.written:
            return self.written[path]
        plain = os.path.join(self.romfs, *path.split('/'))
        if os.path.exists(plain):
            src = open(plain, 'rb').read()
            return None, src                             # None: stored uncompressed
        src = open(os.path.join(self.romfs, *(path + '.zs').split('/')), 'rb').read()
        return src, zstd.decompress(src, self.dicts)

    def size(self, path, old, new, floor=0):
        """the entry of a changed game file; old, new: its contents before and after. At least: the entry's
        headroom over the original file plus what the file grew (never shrink); what the contents need by the
        rules of tools/sizes.py (loading a file takes more memory than its bytes, and a parameter file more per
        element of its lists and tables: adding elements needs more than what the file grew); and `floor`.
        A length instead of contents is accepted too: then only the growth counts."""
        new_len = new if isinstance(new, int) else len(new)
        if path in self.sizes:
            old_len, _, entry, _ = self.sizes[path]
        else:
            entry = self.table.get(path)
            if entry is None:
                raise SystemExit('%s is not in the resource size table' % path)
            old_len = old if isinstance(old, int) else len(old)
            self.orig[path] = None if isinstance(old, int) else old
        need = entry + max(0, new_len - old_len)
        if not isinstance(new, int) and self.orig[path] is not None:
            try:
                need = max(need, sizes.entry(path, new, entry, self.orig[path]))
            except sizes.Unknown as e:
                raise SystemExit('size table: %s' % e)
        self.table.set(path, max(need, floor))
        self.sizes[path] = (old_len, new_len, entry, self.table.get(path))

    def add(self, path, new, like, like_data):
        """entry for a file new to the game (contents `new`): the headroom of a similar game file (`like`,
        contents `like_data`), and at least what the contents need by the rules of tools/sizes.py (the new file
        may hold more elements than the similar one)"""
        if self.table.get(path) is not None:
            raise SystemExit('%s is already in the resource size table' % path)
        e = self.table.get(like)
        if e is None:
            raise SystemExit('%s is not in the resource size table' % like)
        try:
            need = max(e - len(like_data) + len(new), sizes.entry(path, new, e, like_data))
        except sizes.Unknown as x:
            raise SystemExit('size table: %s' % x)
        self.table.set(path, need)
        self.sizes[path] = (0, len(new), 0, self.table.get(path))

    def write_new(self, path, data, like):
        """write a file new to the game, compressed like the game file `like`"""
        src = open(os.path.join(self.romfs, *(like + '.zs').split('/')), 'rb').read()
        did = zstd.frame_dict_id(src)
        comp = zstd.compress(data, level=16, dictionary=self.dicts.get(did) if did else None)
        if zstd.decompress(comp, self.dicts) != data:
            raise SystemExit('compression check failed for %s' % path)
        dest = os.path.join(self.mod_romfs, *(path + '.zs').split('/'))
        if os.path.exists(os.path.join(self.romfs, *(path + '.zs').split('/'))):
            raise SystemExit('%s already exists in the game' % path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(comp)

    def write(self, path, src, old, new):
        self.written[path] = (src, new)
        if src is None:                                  # stored uncompressed: write it the same way
            dest = os.path.join(self.mod_romfs, *path.split('/'))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'wb').write(new)
            self.size(path, old, new)
            return
        did = zstd.frame_dict_id(src)
        comp = zstd.compress(new, level=16, dictionary=self.dicts.get(did) if did else None)
        if zstd.decompress(comp, self.dicts) != new:
            raise SystemExit('compression check failed for %s' % path)
        dest = os.path.join(self.mod_romfs, *(path + '.zs').split('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(comp)
        self.size(path, old, new)

    def finish(self):
        for path, (o, n, e, e2) in sorted(self.sizes.items()):
            print('size %-70s %d -> %d bytes, table %d -> %d' % (path, o, n, e, e2))
        if any(e != e2 for o, n, e, e2 in self.sizes.values()):
            did = zstd.frame_dict_id(self.rraw)
            dest = os.path.join(self.mod_romfs, RESTBL_PATH)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'wb').write(zstd.compress(self.table.write(), level=16,
                                                 dictionary=self.dicts.get(did) if did else None))
            print('resource size table written')
        else:
            print('resource size table unchanged (not included in the mod)')


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--romfs', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--name', default='NX2-ZOOTR')
    ap.add_argument('--longshot', help='Longshot folder: also write a launcher .bat next to the mods folder')
    ap.add_argument('--fix', action='append', default=[],
                    choices=sorted(set(FIXES) | set(FILE_FIXES) | set(TABLE_FIXES)
                                   | {'kokiri_shop_full_stock', 'kokiri_circle_after_dungeons',
                                      'forest_temple_bow_room_door'}),
                    help='a game fix (see FIXES, FILE_FIXES, TABLE_FIXES)')
    ap.add_argument('--gossip', action='append', default=[], metavar='STONE=TEXT',
                    help='what a gossip stone says (STONE: its check ID or its name in the map; in TEXT \\n is a '
                         'new line, \\p a new page, {...} highlighted); see gossip_parse')
    ap.add_argument('--hint', action='append', default=[], metavar='STONE=ITEM',
                    help='a gossip stone says where an item of this build is (ITEM: an item as assigned, or a '
                         'family\'s first level; or @CHECK_ID for the item of that check); see hint_specs')
    ap.add_argument('--start', action='append', default=[], metavar='ITEM[=N]',
                    help='an item every new file has from the start (N: how many); see tools/start_state.py')
    ap.add_argument('--start-flag', action='append', default=[], metavar='NAME=VALUE',
                    help='a flag set on every new file (a Bool: true or false, an Int: a number, a String64: '
                         'text); see tools/start_state.py')
    ap.add_argument('--key-colour', action='append', default=[], metavar='DUNGEON=N',
                    help='the colour number of the dungeon\'s name in its named keys\' get message '
                         '(Item_Dungeon_SmallKey@DUNGEON+name); see tools/dungeon_keys.py')
    ap.add_argument('assign', nargs='*', help='CHECK_ID=ItemActorName')
    a = ap.parse_args(argv)
    if not a.assign and not a.fix and not a.gossip and not a.start and not a.start_flag:
        ap.error('nothing to do: give CHECK_ID=Item assignments, --fix, --gossip, --start and/or --start-flag')
    start_items, start_flags = start_state.parse_items(a.start), start_state.parse_flags(a.start_flag)
    if a.hint and not a.assign:
        ap.error('--hint: nothing is placed to hint at (give CHECK_ID=Item assignments)')
    assignments = [tuple(x.split('=', 1)) for x in a.assign]
    given = list(assignments)                          # as given, for --hint
    never_given(assignments)
    skip_level_guard(assignments)                      # a later level of an upgrade family, alone
    # CHECK_ID=First>Second: a progressive pair (PROGRESSIVE_PAIRS). In a small chest: planned as First, the
    # chest made a checking chest further down. On a freestanding item: planned as First's turning item
    # (tools/turn_items.py). On a rock, a bush, a pot or a Gold Skulltula: planned as First's one-time turning
    # item, its drop (tools/once_items.py). On a gift with flow data: planned as First,
    # the question added further down (gift_pair_kind). On a song: planned as First, the questions in front of
    # the song cutscene's get (song_pair_kind). On a cutscene gift: planned as First, the questions in front of
    # its window and its add step (cutscene_pair_kind). On a scrub: planned as First, the question added in
    # the scrub's branch of the scrub flow (scrub_pair_kind). Nowhere else yet (pair_kind).
    # (first, second) below is (first, second, third) for a three-level family on anything but a chest
    steps = {}                                         # check id -> (first, second): chests
    turning = {}                                       # check id -> (first, second): turning items (TURN_KINDS)
    once_turning = {}                                  # those of `turning` dropped: rocks, bushes, pots, skulltulas
    gift_pairs = {}                                    # check id -> (first, second): gifts (gift_pair_edit)
    song_pairs = {}                                    # check id -> (first, second): song checks (song_skip)
    cutscene_pairs = {}                                # check id -> (first, second): cutscene gifts
    scrub_pairs = {}                                   # check id -> (first, second): scrubs (scrub_flow_edit)
    world = World()
    # CHECK_ID=First>Second>Third: a three-level family (THREE_LEVEL_FAMILIES). In a small chest: planned as
    # First, the chest made the family's own chest further down (tools/three_chest.py). Anywhere else a pair can
    # go: as a pair, with one level more (the loop below)
    triples = three_level_parse(world, assignments)    # check id -> (first, second, third): chests
    for k, (cid, item) in enumerate(assignments):
        if '>' in item:
            pair = tuple(item.split('>'))
            if pair not in PROGRESSIVE_PAIRS and pair not in THREE_LEVEL_FAMILIES:
                raise SystemExit('%s: %s is not a progressive pair the builder knows (%s)' % (cid, item, ', '.join(
                    '>'.join(x) for x in sorted(PROGRESSIVE_PAIRS))))
            if song_pair_kind(world, cid):
                song_pairs[cid] = pair             # planned as First; the questions go in the song cutscene
                assignments[k] = (cid, pair[0])
            elif cutscene_pair_kind(world, cid):
                cutscene_pairs[cid] = pair         # planned as First; the questions go in the cutscene
                assignments[k] = (cid, pair[0])
            elif gift_pair_kind(world, cid):
                gift_pairs[cid] = pair             # planned as First; the question is added further down
                assignments[k] = (cid, pair[0])
            elif scrub_pair_kind(world, cid):
                scrub_pairs[cid] = pair            # planned as First; the question goes in the scrub's branch
                assignments[k] = (cid, pair[0])
            elif skulltula_pair_kind(world, cid):
                # the one-time turning item a rock drops (tools/once_items.py): the skulltula hands its flag to
                # what it drops as it does to its token, and the item marks it as the token does. It comes out
                # as the first level and turns into the next one on the ground once Link owns it
                turning[cid] = pair
                once_turning[cid] = pair
                assignments[k] = (cid, once_items.once_name(pair[0]))
            elif pair_kind(world, cid) == 'chest':
                steps[cid] = pair
                assignments[k] = (cid, pair[0])
            elif pair_kind(world, cid) in once_items.KINDS:
                # a turning item that marks the rock, bush or pot it came from: it comes out as the first
                # level and turns into the next one on the ground once Link owns it (tools/once_items.py)
                turning[cid] = pair
                once_turning[cid] = pair
                assignments[k] = (cid, once_items.once_name(pair[0]))
            else:
                turning[cid] = pair
                assignments[k] = (cid, turn_items.turn_name(pair[0]))
    placed = collections.Counter(list(triples.values()) + [f for forms in (turning, gift_pairs, scrub_pairs,
                                                                         song_pairs, cutscene_pairs)
                                                           for f in forms.values() if len(f) == 3])
    for family, n in sorted(placed.items()):
        if n != len(family):
            print('  note: %s is on %d checks, not %d: %s' % ('>'.join(family), n, len(family), (
                'the last level cannot be reached' if n < len(family) else 'the last level is given more than once')))
    # (and two drops of one family on rocks, bushes or pots: the second could be picked up in the frame the
    # first's scene ends, before it has removed itself)
    for cid, cid2, d in turn_spacing(world, turning):
        print('%-18s and %s: the same progressive family, %.1f m apart' % (cid, cid2, d))
    # a small seed bag or quiver placed alone means its weapon: the check shows and gives the slingshot / bow,
    # and the small bag comes with it (the user's rule: never the bag first)
    for k, (cid, item) in enumerate(assignments):
        if item in FAMILY_ALIASES:
            print('%-18s %s placed: gives %s with it instead (the weapon first)' % (cid, item, FAMILY_ALIASES[item]))
            assignments[k] = (cid, FAMILY_ALIASES[item])
    # CHECK_ID=Item_Dungeon_SmallKey@Dungeon: a key that counts for that dungeon wherever it is found
    # (tools/dungeon_keys.py): planned as the key's own version for the kind of check
    key_versions = {}                                  # (dungeon, kind of version, named) -> name
    key_colours = dict(dungeon_keys.COLOURS)           # dungeon -> the colour number of its name
    key_colour_asked = set()
    for spec in a.key_colour:
        dungeon, _, number = spec.partition('=')
        if dungeon not in dungeon_keys.DUNGEONS or not number.isdigit() \
                or int(number) not in dungeon_keys.GAME_COLOURS:
            raise SystemExit('--key-colour %s: give DUNGEON=N, a dungeon with keys (%s) and one of the game\'s '
                             'colour numbers (%s)' % (spec, ', '.join(dungeon_keys.DUNGEONS),
                                                      ', '.join(map(str, dungeon_keys.GAME_COLOURS))))
        key_colours[dungeon] = int(number)
        key_colour_asked.add(dungeon)
    key_chests = {}                                    # check id -> dungeon: chests that hold a dungeon's key
    for k, (cid, item) in enumerate(assignments):
        parsed = dungeon_keys.parse(item)
        if parsed is None:
            continue
        dungeon, named = parsed
        kind = dungeon_keys.kind_for(check_kind(world, cid), cid)
        r, _, loc = find_check(world, cid)
        if {scene for scene, _, _ in world.placements_of(r, loc)} == {dungeon}:
            # in its own dungeon: the game's own key, which the game counts and shows itself
            print('%-18s a key of %s in %s itself: the game\'s own small key' % (cid, dungeon, dungeon))
            assignments[k] = (cid, dungeon_keys.KEY_ITEM)
            continue
        assignments[k] = (cid, key_versions.setdefault((dungeon, kind, named),
                                                       dungeon_keys.name(dungeon, kind, named)))
        if named:                                      # the item its name stands for: the named chest key
            key_versions.setdefault((dungeon, 'chest', True), dungeon_keys.name(dungeon, 'chest', True))
        if kind == 'chest':
            key_chests[cid] = dungeon
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(a.romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    if start_items or start_flags:                     # the starting state: refused here, with nothing touched
        game_file = lambda path: zstd.decompress(                                        # noqa: E731
            open(os.path.join(a.romfs, *(path + '.zs').split('/')), 'rb').read(), dicts)
        start_data = start_state.GameData(game_file(start_state.GAME_DATA))
        start_state.check_items(start_items, start_data,
                                {r['__RowId'] for r in byml.loads(game_file(start_state.ITEM_TABLE)).root},
                                NEVER_GIVEN, UPGRADE_FAMILIES)
        start_flags = start_state.check_flags(start_flags, start_data)
    mod_romfs = os.path.join(a.out, a.name, 'romfs')
    if os.path.isdir(mod_romfs):
        # files of an earlier build would stay in the mod otherwise (only this build's output folder is removed)
        shutil.rmtree(mod_romfs)
        print('earlier build removed:', mod_romfs)
    out = Output(a.romfs, mod_romfs, dicts)
    if a.hint:                                         # hints become gossip texts (hint_specs)
        hint_known = {r['__RowId']: r.get('ActorName') for r in byml.loads(
            out.read(ground_items.table_path('ActorInfo'))[1]).root}
        hinted, hint_said = hint_specs(world, a.hint, given, hint_texts(out.read(GOSSIP_LANG)[1]),
                                       lambda item: hint_known.get(item))
        a.gossip = a.gossip + hinted
        for line in hint_said:
            print(line)
    gossip = gossip_plan(out, world, a.gossip) if a.gossip else None    # refused here, before anything is written

    shop_fix = 'kokiri_shop_full_stock' in a.fix
    for cid, _ in assignments:
        if cid.startswith(CIRCLE_NEEDS_FIX) and 'kokiri_circle_after_dungeons' not in a.fix:
            raise SystemExit('%s: needs --fix kokiri_circle_after_dungeons' % cid)
    shop_removed = set()
    for name in a.fix:
        if name == 'kokiri_shop_full_stock':
            src, old = out.read(SHOP_MAP)
            new, shop_removed, always = shop_full_stock_map(old)
            out.write(SHOP_MAP, src, old, new)
            print('fix %-28s %s: %d shop objects removed (before the Deku Tree), %d always there'
                  % (name, SHOP_MAP, len(shop_removed), len(always)))
            src, old = out.read(SHOP_FLOW)
            ef = evfl.loads(old)
            shop_greeting_edit(ef.flowchart)
            out.write(SHOP_FLOW, src, old, flow_write_checked(ef))
            print('fix %-28s %s: greeting always as after the Deku Tree' % (name, SHOP_FLOW))
            continue
        if name == 'kokiri_circle_after_dungeons':
            src, old = out.read(CIRCLE_LOGIC)
            new, said = circle_logic(old)
            out.write(CIRCLE_LOGIC, src, old, new)
            print('fix %-28s %s: %s' % (name, CIRCLE_LOGIC, said))
            src, old = out.read(CIRCLE_KOKIRI)
            out.write(CIRCLE_KOKIRI, src, old, circle_kokiri(old))
            print('fix %-28s %s: schedule after the Kokiri Emerald is the default' % (name, CIRCLE_KOKIRI))
            src, old = out.read(CIRCLE_MIDDLE)
            out.write(CIRCLE_MIDDLE, src, old, circle_middle(old))
            print('fix %-28s %s: middle rock: prop never, liftable rock always' % (name, CIRCLE_MIDDLE))
            continue
        if name == 'forest_temple_bow_room_door':
            src, old = out.read(BOW_ROOM_LOGIC)
            new, said = bow_room_door(old)
            out.write(BOW_ROOM_LOGIC, src, old, new)
            print('fix %-28s %s: %s' % (name, BOW_ROOM_LOGIC, said))
            continue
        if name in TABLE_FIXES:
            path, fn = TABLE_FIXES[name]
            src, old = out.read(path)
            new, changed = fn(old)
            out.write(path, src, old, new)
            print('fix %-28s %s: %d rows changed (%s)' % (name, path, len(changed), ', '.join(changed)))
            continue
        if name in FILE_FIXES:
            path, keys, expected = FILE_FIXES[name]
            src, old = out.read(path)
            out.write(path, src, old, remove_entry(old, keys, expected))
            print('fix %-28s %s: removed %s' % (name, path, '/'.join(keys)))
            continue
        pack, inner, key, expected, value = FIXES[name]
        src, old = out.read(pack)
        new, (old_inner, new_inner) = patch_pack(old, inner, key, expected, value)
        out.write(pack, src, old, new)
        # files inside packs have their own size table entries too
        out.size(inner, old_inner, new_inner)
        print('fix %-28s %s: %s %d -> %d' % (name, pack, key, expected, value))

    # songs show Sheik's harp (before any ground, shelf or token version copies their model)
    songs = sorted({item for _, item in assignments if item.startswith(SONG_PREFIX)})
    if songs:
        # each colour the songs use (harp_colors.SONG_COLORS) gets a harp variant: a model copy and a recoloured
        # copy of its colour texture, new files next to the original harp's; songs of one colour share it
        models = {}
        for tag in sorted({harp_colors.SONG_COLORS[song] for song in songs if song in harp_colors.SONG_COLORS}):
            src, old = out.read(harp_colors.MODEL)
            new = harp_colors.model_variant(old, tag)
            out.write_new(harp_colors.model_path(tag), new, harp_colors.MODEL)
            out.add(harp_colors.model_path(tag), new, harp_colors.MODEL, old)
            src, old = out.read(harp_colors.ALB)
            new, changed = harp_colors.texture_variant(old, tag, harp_colors.COLORS[tag])
            out.write_new(harp_colors.alb_path(tag), new, harp_colors.ALB)
            out.add(harp_colors.alb_path(tag), new, harp_colors.ALB, old)
            users = [song for song in songs if harp_colors.SONG_COLORS.get(song) == tag]
            for song in users:
                models[song] = harp_colors.variant_name(tag)
            print('%-18s %s: harp %s, cloth %s (%d texture blocks recoloured)'
                  % ('songs', ', '.join(users), harp_colors.variant_name(tag), harp_colors.COLORS[tag], changed))
        # held up, the harp spins and is lifted above the hands (harp_colors): its own animation project, and the
        # animation components the Boomerang has; off (harp_colors.SPIN)
        if harp_colors.SPIN:
            boomerang = out.read(ground_items.pack_path('Item_Boomerang'))[1]
            spin = song_spin_files(boomerang)
            spin_floor = out.table.get('Actor/%s.engine__actor__ActorParam.bgyml' % SPIN_LIKE)
            if spin_floor is None:
                raise SystemExit('%s: no size entry for its actor file' % SPIN_LIKE)
            out.add(harp_colors.ANIM_PARAM, spin[harp_colors.ANIM_PARAM], harp_colors.ANIM_PARAM_LIKE,
                    sarc.Sarc.read(boomerang).files[harp_colors.ANIM_PARAM_LIKE])
        for song in songs:
            pack = ground_items.pack_path(song)
            inner = 'Component/ModelInfo/%s.engine__component__ModelInfo.bgyml' % song
            for key in ('FmdbName', 'ModelProjectName'):
                src, old = out.read(pack)
                value = models.get(song, HARP_MODEL) if key == 'FmdbName' else HARP_MODEL
                new, (old_inner, new_inner) = patch_pack(old, inner, key, 'Obj_Rupee', value)
                out.write(pack, src, old, new)
                out.size(inner, old_inner, new_inner)
            if harp_colors.SPIN:
                src, old = out.read(pack)
                new, (inner, old_inner, new_inner) = song_spin_pack(old, song, spin)
                out.write(pack, src, old, new)
                # at least the size entry of SPIN_LIKE's actor file (2026-11-18: with only the growth added, the
                # game crashed creating the songs: its table of the actor's components could not be allocated)
                out.size(inner, old_inner, new_inner, floor=spin_floor)
        if harp_colors.SPIN:
            print('%-18s %s: spin and lift when held up (animations %s)'
                  % ('songs', ', '.join(songs), ', '.join(harp_colors.SPIN_PROJECTS)))
        src, old = out.read(ACTOR_INFO)
        out.write(ACTOR_INFO, src, old, song_harp_rows(
            old, set(songs), models,
            harp_colors.SPIN_PROJECTS if harp_colors.SPIN else ()))
        print('%-18s %s: model %s (Sheik\'s harp) instead of the rupee' % ('songs', ', '.join(songs), HARP_MODEL))

    # items that lie on the ground (freestanding, pot drops) and only exist as the model shown when received
    # get a ground version; items a chest gives that have no get-demo settings (ocarinas: Link's instrument)
    # get a held-up version; what a Gold Skulltula drops is a version built from its token, which marks the
    # skulltula done when picked up (tools/ground_items.py)
    grounds = {}                                       # (item, version) -> name

    def plain(path):
        return out.read(path)[1]

    once_plain = {}                                    # item -> its ground version with the one-time mark

    def once_drop(item):
        """what a rock, a bush or a pot drops once: a version of the item that marks it when picked up"""
        if item.startswith(once_items.PREFIX) or item == ground_items.TOKEN or dungeon_keys.is_ours(item):
            return item                                # a family's level (built further down); a real token
        kind = ground_items.kind_of(plain, item)
        if kind in ('item', 'equipment'):
            return once_plain.setdefault(item, once_items.plain_name(item))
        return gs_drop(item)                           # a ground actor of the game: its token-built version

    def on_ground(item):
        if item.startswith((turn_items.PREFIX, once_items.PREFIX)) or dungeon_keys.is_ours(item):
            return item                                # a turning item (a progressive pair): built further down
        kind = ground_items.kind_of(plain, item)
        if kind == 'ground':
            return item
        if kind in ('item', 'equipment'):
            return grounds.setdefault((item, 'ground'), ground_items.ground_name(item))
        raise SystemExit('%s: not something that can lie on the ground, and no ground version can be made' % item)

    def in_chest(item):
        if dungeon_keys.is_ours(item):
            return item                                # a dungeon's key: built further down
        if ground_items.kind_of(plain, item) == 'equipment':
            return grounds.setdefault((item, 'held'), ground_items.ground_name(item, 'held'))
        return item

    def gs_drop(item):
        if item == ground_items.TOKEN:
            return item                                # its own token
        if item.startswith(once_items.PREFIX) or dungeon_keys.is_ours(item):
            return item                                # a level of a family (a progressive form): built further down
        if ground_items.kind_of(plain, item) in ('ground', 'item', 'equipment'):
            return grounds.setdefault((item, 'token'), ground_items.ground_name(item, 'token'))
        raise SystemExit('%s: not something a Gold Skulltula can drop (no version of it can be made from the '
                         'token)' % item)

    # chests that hold an ocarina (alone or as a level of a pair): an opening event of our own around the
    # chest's usual one, which makes Link's ocarina after it (TBOX_SYNC_FLOW)
    tbox_usuals = {}                                   # usual opening event -> our event around it
    tbox_deals = {}                                    # item -> PouchSpecialDeal (read once)

    def holds_ocarina(cid):
        if not tbox_deals:
            tbox_deals.update({r['__RowId']: r.get('PouchSpecialDeal') for r in byml.loads(plain(
                ground_items.table_path('PouchActorInfo'))).root})
        levels = steps.get(cid) or triples.get(cid) or tuple(i for c, i in assignments if c == cid)
        return any(tbox_deals.get(x) == SYNC_DEAL for x in levels)

    def tbox_event(gyaml, event):
        usual = event if event is not None else chest_usual_event(plain, gyaml)
        return tbox_usuals.setdefault(usual, tbox_sync_event(usual))

    # chests that hold a dungeon's key: an opening event of our own around the usual one, which adds the key
    key_events = {}                                    # (usual opening event, dungeon) -> our event around it

    def key_event(dungeon):
        def event_for(gyaml, event):
            usual = event if event is not None else chest_usual_event(plain, gyaml)
            return key_events.setdefault((usual, dungeon), tbox_key_event(usual, dungeon))
        return event_for

    def get_plan(items):
        """how gifts, scrubs and song cutscenes give these items: (the items Link can't hold up in
        Dm_SY_GetInEvent: given with the get window, {ocarina: the sync steps to run after its get})"""
        deals = {r['__RowId']: r.get('PouchSpecialDeal') for r in byml.loads(plain(
            ground_items.table_path('PouchActorInfo'))).root}
        for item in items:
            if item not in deals:
                raise SystemExit('%s has no row in PouchActorInfo: not an item' % item)
        direct = {item for item in items if not ground_items.can_hold_up(plain, item)}
        if direct:
            direct_get_allowed(byml.loads(plain(EVENT_INFO)).root)
        sync = {}
        if any(deals[item] == SYNC_DEAL for item in items):
            steps = sync_template(evfl.loads(plain(SYNC_FLOW)).flowchart)
            sync = {item: steps for item in items if deals[item] == SYNC_DEAL}
        return direct, sync

    # shelves: a game shelf actor (Shop_...) is used as it is; any other item gets a shop version at the price
    # of what the shelf sold, sold once (tools/shop_items.py)
    shops = {}                                         # (item, price) -> name
    shelf_lift = {}                                    # shop version name -> metres higher on the shelf
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root  # noqa: E731
    known_as = {}                                      # item -> the name the inventory knows it by (read once)

    def flow_name(item):
        """the name the inventory knows an item by (ActorInfo: ActorName): what the game's own flows ask about
        (EventQueryIsExistInPouch: Weapon_Range_Bow, Armor_Child_Gauntlet_Goron, Armor_Adult_Gauntlet_Silver;
        for most items it is the item's own name)"""
        if not known_as:
            known_as.update({r['__RowId']: r.get('ActorName') for r in table_rows('ActorInfo')})
        return known_as.get(item) or item

    def on_shelf(item, shelf_actor):
        if item.startswith('Shop_'):
            return item
        if not shop_items.can_sell(plain, item):
            raise SystemExit('%s: cannot be put on a shop shelf' % item)
        why = shop_items.refusal(item, table_rows)
        if why:
            raise SystemExit('%s cannot be put on a shop shelf: %s' % (item, why))
        price = shop_items.price_of(table_rows, shelf_actor)
        name = shops.setdefault((item, price), shop_items.shop_name(item, price, once=True))
        if item in shop_items.SHELF_LIFT:
            shelf_lift[name] = shop_items.SHELF_LIFT[item]
        return name

    planned = plan(world, assignments, on_ground, in_chest, on_shelf, gs_drop, once_drop)
    # a weapon placed alone where it lies on the ground: nothing there gives its small bag (only chests do, and
    # the first level of its family's turning item; a gift, a scrub and a cutscene add it)
    for cid, item, kind in sorted({(c, i, k) for changes in planned.values() for c, i, _, k in changes.values()}):
        alone = next((x for x in SCRUB_COMPANIONS if kind in DROP_ON_GROUND and item in (
            x, ground_items.ground_name(x), ground_items.ground_name(x, 'token'), once_items.plain_name(x))), None)
        if alone:
            print('  NOTE: %s: %s alone on a %s comes without %s (only a chest gives it with the weapon)%s'
                  % (cid, alone, kind, ', '.join(SCRUB_COMPANIONS[alone]),
                     ': place its family there instead (%s=%s)' % (cid, '>'.join(next(
                         f for f in FAMILIES.values() if f[0] == alone)))
                     if kind in TURN_KINDS or kind in GS_KINDS else ''))
    # shelves: which shelf (ShopItemIndex; the Heart has none: 0) and age each placement is, for the lists
    shelf_of = {p['hash']: (p['ages'], int(p.get('params', {}).get('ShopItemIndex', 0)))
                for spots in world.checks.values() for sp in spots.values() if sp['kind'] == 'shop'
                for p in sp['placements']}
    goods = {'child': {}, 'adult': {}}
    for path in list(planned):
        for h, (cid, item, _, kind) in list(planned[path].items()):
            if kind != 'shop':
                continue
            if not shop_fix:
                raise SystemExit('%s: shop shelves need --fix kokiri_shop_full_stock' % cid)
            if h in shop_removed:
                del planned[path][h]
                print('%-18s placement %s: removed by kokiri_shop_full_stock (before the Deku Tree)' % (cid, h))
                continue
            ages, idx = shelf_of[h]
            for age in ages:
                if goods[age].get(idx, item) != item:
                    raise SystemExit('%s: shelf %d (%s) given two items' % (cid, idx, age))
                goods[age][idx] = item
        if not planned[path]:
            del planned[path]

    # what rocks, bushes and pots drop is given once (tools/once_items.py): the placements it is for. Each must
    # have the two saved flags the token's node sets: the one that is reset (its hash) and hash ^ 2 (never
    # reset), and its actor must have a drop part (the prop rock of the rock circle has none)
    once_spots = {}                                    # placement hash -> (check id, the drop, its actor)
    actor_of = {p['hash']: p['actor'] for spots in world.checks.values() for sp in spots.values()
                for p in sp['placements']}
    once_no_drop = {}                                  # actor -> whether it has no drop part (read once)
    for path, changes in sorted(planned.items()):
        for h, (cid, item, _, kind) in sorted(changes.items()):
            if kind not in once_items.KINDS:
                continue
            actor = actor_of[h]
            if actor not in once_no_drop:
                once_no_drop[actor] = not once_items.has_drop(
                    sarc.Sarc.read(plain(ground_items.pack_path(actor))).files, actor)
            if once_no_drop[actor]:
                continue                               # it drops nothing, whatever its placement names
            if not item.startswith(once_items.OURS):
                print('  NOTE: %s: %s on a %s is not given once (it comes out again when the %s is back)'
                      % (cid, item, kind, kind))
                continue
            once_spots[h] = (cid, item, actor)
    if once_spots:
        flags = placement_flags(plain(GAME_DATA))
        for h, (cid, item, actor) in sorted(once_spots.items()):
            if flags.get(h) != once_items.FLAG_RESET or flags.get(str(int(h) ^ 2)) != FLAG_KEPT:
                raise SystemExit('%s: placement %s (%s) does not have the two saved flags a one-time drop needs '
                                 '(%s and %s)' % (cid, h, actor, flags.get(h), flags.get(str(int(h) ^ 2))))

    # progressive pairs: in chests (the chest itself chooses) and on freestanding items, rocks and bushes (a
    # turning item), as sorted out above (pair_kind); checked again on what was planned
    stepped = {cid for changes in planned.values() for cid, _, _, kind in changes.values() if kind == 'chest'}
    for cid in sorted(set(steps) - stepped):
        raise SystemExit('%s: a progressive pair (First>Second) can only be put in a chest, on a freestanding '
                         'item, or on a rock or a bush' % cid)
    for cid in sorted(set(triples) - stepped):
        raise SystemExit('%s: a three-level family (First>Second>Third) can only be put %s' % (cid, PROGRESSIVE_WHERE))
    three_used = {}                                    # (family name, _NoBake twin) -> (second, third as held)
    for changes in planned.values():
        for cid, item, _, kind in changes.values():
            if (cid in turning) != item.startswith((turn_items.PREFIX, once_items.PREFIX)) \
                    or (cid in turning and kind not in TURN_KINDS + tuple(GS_KINDS)) \
                    or (cid in once_turning) != item.startswith(once_items.PREFIX) \
                    or (cid in once_turning and kind not in once_items.KINDS + tuple(GS_KINDS)):
                raise SystemExit('%s: a turning item (%s) planned on a %s: only freestanding items, rocks, '
                                 'bushes, pots and Gold Skulltulas' % (cid, item, kind))

    for path, changes in sorted(planned.items()):
        src, old = out.read(path)
        # (item to look for in the inventory: the item's own name; item given when Link has it: as a chest
        # gives it)
        checking = {h: pair_check(steps[cid], in_chest) for h, (cid, _, _, kind) in changes.items()
                    if cid in steps}
        # three-level families: the first two levels as a pair's settings; the family's own chest knows the
        # second level's name and holds the third as a chest gives it
        three = {h: THREE_LEVEL_FAMILIES[triples[cid]] for h, (cid, _, _, kind) in changes.items()
                 if cid in triples}
        checking.update({h: pair_check(triples[cid][:2], in_chest) for h, (cid, _, _, kind) in changes.items()
                         if cid in triples})
        wrap = {h: tbox_event for h, (cid, _, _, kind) in changes.items() if kind == 'chest' and holds_ocarina(cid)}
        wrap.update({h: key_event(key_chests[cid]) for h, (cid, _, _, kind) in changes.items()
                     if kind == 'chest' and cid in key_chests})
        new, found, _ = patch_file(old, {h: v for h, v in changes.items()}, checking, three, wrap)
        for h, (cid, item, expected_old, kind) in changes.items():
            if found[h] != expected_old:
                print('  note: %s placement %s held %s (data says %s)' % (cid, h, found[h], expected_old))
            print('%-18s %s: %s -> %s' % (cid, path.split('/')[-1], found[h], item))
            if cid in turning:
                print('%-18s   a turning item%s: %s on the ground while Link has no %s, then %s'
                      % (cid, '' if kind == 'freestanding' else ' as the %s\'s drop' % kind, turning[cid][0],
                         turning[cid][0], turning[cid][1]))
            if h in once_spots:
                print('%-18s   given once: picked up, it marks this %s as the token marks its Gold Skulltula'
                      % (cid, kind))
        # read back: only the changed values differ (worked out again here from the original, not from
        # what patch_file did)
        before = {str(int(x['Hash'])): x for x in byml.loads(old).root['Actors']}
        back = byml.loads(new).root['Actors']
        if len(back) != len(before):
            raise SystemExit('read-back: actor count changed in %s' % path)
        for act in back:
            h = str(int(act['Hash']))
            want = dict(before[h])
            if h in changes and changes[h][3] in REPLACED:
                want['Gyaml'] = changes[h][1]
            elif h in changes:
                dyn = dict(want.get('Dynamic') or {}, Drop__DropActor=changes[h][1])
                if changes[h][3] == 'pot' and POT_TABLE_KEY in dyn:
                    print('%-18s   the pot\'s drop table %s removed' % (changes[h][0], dyn.pop(POT_TABLE_KEY)))
                ev = dyn.get('GetEventName')
                if ev is not None and changes[h][1] != found[h] and CHEST_EVENTS[ev][0] == 'remove':
                    del dyn['GetEventName']
                    print('%-18s   special opening event %s removed' % (changes[h][0], ev))
                was = want['Gyaml']
                if h in checking or was in PLAIN_CHEST:
                    # the chest's check settings: a progressive pair's, or none left (an ordinary chest)
                    dyn = {k: v for k, v in dyn.items() if k not in CHECK_SETTINGS}
                    if h in checking:
                        want['Gyaml'] = CHECKING_CHEST.get(was, was)
                        if h in three:
                            twin = PLAIN_CHEST.get(was, was) != three_chest.PLAIN
                            want['Gyaml'] = three_chest.chest_name(three[h], twin)
                        dyn.update(Drop__CheckActor=checking[h][0], Drop__DropActor_Substitute=checking[h][1])
                        print('%-18s   %s -> %s: gives %s while Link has no %s, then %s'
                              % (changes[h][0], was, want['Gyaml'], changes[h][1], checking[h][0], checking[h][1]))
                        if h in three:
                            family = triples[changes[h][0]]
                            names = three_used.setdefault((three[h], twin), (family[1], in_chest(family[2])))
                            print('%-18s   a three-level chest: once Link has %s it gives %s'
                                  % (changes[h][0], names[0], names[1]))
                    else:
                        want['Gyaml'] = PLAIN_CHEST[was]
                        print('%-18s   %s -> %s: a checking chest of the game made an ordinary chest (its check '
                              'for %s removed: it always gives the placed item)'
                              % (changes[h][0], was, want['Gyaml'],
                                 (before[h].get('Dynamic') or {}).get('Drop__CheckActor')))
                if h in wrap:
                    # an ocarina chest: our opening event around the one the chest would run
                    usual = dyn.get(TBOX_EVENT_KEY) or chest_usual_event(plain, want['Gyaml'])
                    if changes[h][0] in key_chests:
                        dyn[TBOX_EVENT_KEY] = tbox_key_event(usual, key_chests[changes[h][0]])
                        print('%-18s   holds a key of %s: opening event %s (runs %s, then adds 1 to %s)'
                              % (changes[h][0], key_chests[changes[h][0]], dyn[TBOX_EVENT_KEY], usual,
                                 dungeon_keys.flag(key_chests[changes[h][0]])))
                    else:
                        dyn[TBOX_EVENT_KEY] = tbox_sync_event(usual)
                        print('%-18s   holds an ocarina: opening event %s (runs %s, then makes Link\'s ocarina)'
                              % (changes[h][0], dyn[TBOX_EVENT_KEY], usual))
                want['Dynamic'] = dyn
            if act != want:
                raise SystemExit('read-back: actor %s (%s) differs from what was intended' % (h, act['Gyaml']))
        out.write(path, src, old, new)

    # ocarina chests: the flow of our opening events (one entry point per usual event used) and their two table
    # rows each; read back: every entry point is join, the usual event, the three sync steps, nothing else
    if tbox_usuals:
        like = flow_path(TBOX_SYNC_LIKE_FLOW)
        like_data = plain(like)
        like_ef = evfl.loads(like_data)
        template = tbox_sync_template(like_ef.flowchart)
        sync = sync_template(evfl.loads(plain(SYNC_FLOW)).flowchart)
        try:
            data = evfl.dumps_checked(tbox_sync_flow(template, sync, tbox_usuals, like_ef.version))
        except ValueError as e:
            raise SystemExit(str(e))
        if tbox_sync_read(data) != {name: tbox_sync_steps(template, sync, usual)
                                    for usual, name in tbox_usuals.items()}:
            raise SystemExit('read-back: %s differs from what was intended' % flow_path(TBOX_SYNC_FLOW))
        out.write_new(flow_path(TBOX_SYNC_FLOW), data, like)
        out.add(flow_path(TBOX_SYNC_FLOW), data, like, like_data)
        rows = tbox_sync_rows(byml.loads(plain(EVENT_SETTING)).root, byml.loads(plain(EVENT_INFO)).root,
                              tbox_usuals)
        for t, path in (('EventSetting', EVENT_SETTING), ('GameAnalyzedEventInfo', EVENT_INFO)):
            src, old = out.read(path)
            out.write(path, src, old, ground_items.add_rows(old, rows[t]))
        for usual, name in sorted(tbox_usuals.items()):
            said = ' -> '.join('%s.%s%s' % (a, n, ' ' + usual if n == TBOX_SYNC_RUN[1] else '')
                               for a, n, _ in tbox_sync_steps(template, sync, usual))
            print('%-18s %s: entry point and event %s: %s' % ('ocarina chests', flow_path(TBOX_SYNC_FLOW), name, said))
        print('%-18s %d rows added to %s and %s' % ('ocarina chests', len(tbox_usuals), EVENT_SETTING, EVENT_INFO))

    # chests that hold a dungeon's key: the flow of our opening events and their two table rows each; read back:
    # every entry point is join, the usual event, one key more for its dungeon, nothing else
    if key_events:
        like = flow_path(TBOX_SYNC_LIKE_FLOW)
        like_data = plain(like)
        like_ef = evfl.loads(like_data)
        template = tbox_sync_template(like_ef.flowchart)
        add = key_add_template(evfl.loads(plain(KEY_ADD_FLOW)).flowchart)
        try:
            data = evfl.dumps_checked(tbox_key_flow(template, add, key_events, like_ef.version))
        except ValueError as e:
            raise SystemExit(str(e))
        if tbox_sync_read(data) != {name: tbox_key_steps(template, add, usual, dungeon)
                                    for (usual, dungeon), name in key_events.items()}:
            raise SystemExit('read-back: %s differs from what was intended' % flow_path(TBOX_KEY_FLOW))
        out.write_new(flow_path(TBOX_KEY_FLOW), data, like)
        out.add(flow_path(TBOX_KEY_FLOW), data, like, like_data)
        rows = tbox_sync_rows(byml.loads(out.read(EVENT_SETTING)[1]).root, byml.loads(out.read(EVENT_INFO)[1]).root,
                              (), [(usual, name) for (usual, _), name in sorted(key_events.items())], TBOX_KEY_FLOW)
        for t, path in (('EventSetting', EVENT_SETTING), ('GameAnalyzedEventInfo', EVENT_INFO)):
            src, old = out.read(path)
            out.write(path, src, old, ground_items.add_rows(old, rows[t]))
        for (usual, dungeon), name in sorted(key_events.items()):
            print('%-18s %s: entry point and event %s: %s, then %s + 1'
                  % ('key chests', flow_path(TBOX_KEY_FLOW), name, usual, dungeon_keys.flag(dungeon)))

    # songs: the cutscene only hands over the item (a family: the inventory questions in front of one get per
    # level); read back against the original
    for path, (cid, item, song) in sorted(plan_songs(world, assignments).items()):
        src, old = out.read(path)
        ef = evfl.loads(old)
        levels = song_pairs.get(cid, (item,))
        sync = get_plan(list(levels))[1]
        template = gift_pair_template(evfl.loads(plain(GIFT_PAIR_FLOW)).flowchart)
        said = song_skip(ef.flowchart, cid, item, song, sync, levels, template, flow_name)
        new = flow_write_checked(ef)
        song_skip_check(evfl.loads(old).flowchart, evfl.loads(new).flowchart, cid, levels, sync, template, flow_name)
        out.write(path, src, old, new)
        for line in said:
            print(line, '(%s)' % path.split('/')[-1])

    # gifts: the item of their call of Dm_SY_GetInEvent, or for an item Link can't hold up a call of
    # GetPouchContent in its place (read back, worked out again from the original: only the gift events change,
    # as intended; the only new events are the sync steps after an ocarina)
    for path, events in sorted(plan_gifts(world, assignments).items()):
        src, old = out.read(path)
        ef = evfl.loads(old)
        direct, sync = get_plan(sorted({item for _, item, _ in events.values()}))
        said, intended, added = gift_edit(ef.flowchart, events, direct, sync)
        new = flow_write_checked(ef)
        back_fc, orig_fc = evfl.loads(new).flowchart, evfl.loads(old).flowchart
        back = {e.name: e for e in back_fc.events}
        orig = {e.name: e for e in orig_fc.events}

        def call(fc, e):
            return (e.flowchart, e.entry, dict(e.params) if isinstance(e.params, dict) else e.params,
                    None if e.next is None else fc.events[e.next].name)

        if set(back) != set(orig) | set(added) or set(orig) & set(added) \
                or any(back[n].type != 'action' for n in added):
            raise SystemExit('read-back: %s: events differ from what was intended' % path)
        for name, o in orig.items():
            e, want = back[name], call(orig_fc, o)
            if name in events:
                item = events[name][1]
                if item in direct:
                    after = e                          # the sync steps, if any, lead to what followed the gift
                    for _ in range(len(sync.get(item, ()))):
                        after = back_fc.events[after.next]
                        if after.name not in added:
                            raise SystemExit('read-back: %s %s: sync steps not as intended' % (path, name))
                    want = (DIRECT_GET[0], DIRECT_GET[1], {'ActorName': item},
                            want[3] if not sync.get(item) else back_fc.events[e.next].name)
                    if call(back_fc, after)[3] != call(orig_fc, o)[3]:
                        raise SystemExit('read-back: %s %s does not lead on as the gift did' % (path, name))
                else:
                    want = (want[0], want[1], dict(want[2], ActorName=item), want[3])
                if intended[name] != want:
                    raise SystemExit('read-back: %s %s was not edited as intended' % (path, name))
            if call(back_fc, e) != want or e.type != o.type or e.cases != o.cases or e.forks != o.forks:
                raise SystemExit('read-back: %s %s differs from what was intended' % (path, name))
        out.write(path, src, old, new)
        for line in said:
            print(line, '(%s)' % path.split('/')[-1])

    # progressive pairs on gifts: each such gift now gives First (above); the inventory question goes in front
    # of it in the giver's own flow, with a second call for Second (gift_pair_edit), read back against the flow
    # as it was before the question
    # (three levels: two questions; a first level that needs its small bag, alone or in a family: the bag is
    # added after its call)
    for path, events in sorted(plan_gifts(world, [(c, i) for c, i in assignments
                                                  if c in gift_pairs or i in SCRUB_COMPANIONS]).items()):
        src, old = out.read(path)
        ef = evfl.loads(old)
        pairs = {ev: (cid, gift_pairs.get(cid, (item,))) for ev, (cid, item, _) in events.items()}
        template = gift_pair_template(evfl.loads(plain(GIFT_PAIR_FLOW)).flowchart)
        direct, _ = get_plan(sorted({x for _, pair in pairs.values() for x in pair}))
        said, made = gift_pair_edit(ef.flowchart, pairs, template, direct, flow_name)
        new = flow_write_checked(ef)
        gift_pair_read_back(path, evfl.loads(old).flowchart, evfl.loads(new).flowchart, pairs, made, template,
                            flow_name)
        out.write(path, src, old, new)
        for line in said:
            print(line, '(%s)' % path.split('/')[-1])

    # cutscene gifts: the item the cutscene adds, names in its window and puts in Link's hand (read back and
    # compared with the original: nothing else differs)
    for path, (cid, item, g) in sorted(plan_cutscene_gifts(world, assignments).items()):
        src, old = out.read(path)
        ef = evfl.loads(old)
        if item not in {r['__RowId'] for r in byml.loads(plain(ground_items.table_path('PouchActorInfo'))).root}:
            raise SystemExit('%s has no row in PouchActorInfo: not an item' % item)
        show = item == g['item'] or ground_items.kind_of(plain, item) == CUTSCENE_SHOWN_KIND
        companions = SCRUB_COMPANIONS.get(item, ())
        said, added = cutscene_gift_edit(ef.flowchart, cid, g, item, show, companions)
        levels = cutscene_pairs.get(cid)
        if levels:                                     # a family: the questions in front of the window and the add
            template = gift_pair_template(evfl.loads(plain(GIFT_PAIR_FLOW)).flowchart)
            said += cutscene_family_edit(ef.flowchart, cid, g, levels, template, flow_name, companions)
            new = flow_write_checked(ef)
            cutscene_family_check(evfl.loads(old).flowchart, evfl.loads(new).flowchart, cid, g, levels, template,
                                  flow_name, show, companions)
            if show:
                said.append('%-18s   Link holds %s in the cutscene whichever level is given (one actor)'
                            % (cid, item))
        else:
            new = flow_write_checked(ef)
            cutscene_gift_check(evfl.loads(old).flowchart, evfl.loads(new).flowchart, cid, g, item, show, added)
        out.write(path, src, old, new)
        for line in said:
            print(line, '(%s)' % path.split('/')[-1])

    # scrubs: their map setting, one branch each in the shared flow, the generic line
    scrubs = plan_scrubs(world, assignments)
    # a slingshot given anywhere may come without its seed bag: the scrubs' seed sales then refuse
    guard = any(item in ('Item_Range_SlingShot', turn_items.turn_name('Item_Range_SlingShot'),
                         once_items.once_name('Item_Range_SlingShot'))
                for _, item in assignments)
    if scrubs or guard:
        maps = {}
        for cid, item, rows in scrubs:
            for path, h, talk, was in rows:
                maps.setdefault(path, {})[h] = (cid, item, was)
        for path, changes in sorted(maps.items()):
            src, old = out.read(path)
            out.write(path, src, old, scrub_map_edit(old, changes))
            for h, (cid, item, was) in sorted(changes.items()):
                print('%-18s %s: scrub %s sells %s instead of %s' % (cid, path.split('/')[-1], h, item, was))
        src, old = out.read(SCRUB_FLOW)
        ef = evfl.loads(old)
        direct, sync = get_plan(sorted({i for _, i, _ in scrubs} | {x for p in scrub_pairs.values() for x in p}))
        said = scrub_flow_edit(ef.flowchart, [(c, i, [(t, w) for _, _, t, w in rows]) for c, i, rows in scrubs],
                               direct, sync, scrub_pairs, flow_name) if scrubs else []
        lines = {SCRUB_LABEL: SCRUB_LINE} if scrubs else {}
        if guard:
            said += seed_bag_guard(ef.flowchart)
            lines[SCRUB_NOBAG_LABEL] = SCRUB_NOBAG_LINE
        ef.flowchart.update_entry_points()
        out.write(SCRUB_FLOW, src, old, flow_write_checked(ef))
        for line in said:
            print('scrub flow         %s' % line)
        scrub_messages(out, a.romfs, lines)
        print('scrub lines        %s added to %s (every language)' % (', '.join(lines), SCRUB_MSG_FILE))

    # count boards of changed shelves: none for a single item, the right count for a bundle
    pouch_rows = {r['__RowId']: r for r in table_rows('PouchActorInfo')}

    def bundle_count(actor):
        if actor.startswith(shop_items.PREFIX):
            return 1                                   # shop versions sell one item
        return int(pouch_rows[actor].get('BundleActorNum', 1))

    removed_boards = {}                                # (map path, shelf hash) -> its removed count board
    for path, changes in sorted(planned.items()):
        shelves = {h: bundle_count(v[1]) for h, v in changes.items() if v[3] == 'shop'}
        if not shelves:
            continue
        src, old = out.read(path)
        new, done, board_of = shop_boards(old, shelves, lambda n: os.path.exists(
            os.path.join(a.romfs, *ground_items.pack_path(n).split('/')) + '.zs'))
        removed_boards.update({(path, sh): b for sh, b in board_of.items()})
        if done:
            out.write(path, src, old, new)
            for d in done:
                print('%-18s %s: %s' % ('count board', path.split('/')[-1], d))
        lifts = {h: shelf_lift[v[1]] for h, v in changes.items() if v[3] == 'shop' and v[1] in shelf_lift}
        if lifts:
            src, old = out.read(path)
            out.write(path, src, old, lift_shelves(old, lifts))
            for h in lifts:
                print('%-18s %s: %s %.2f m higher' % ('shelf lift', path.split('/')[-1], changes[h][1], lifts[h]))

    # shelves sold once stay sold: each takes over the saved flag of a shop object this build removed (see
    # GAME_DATA); the shop version's AI sets it when the shelf is sold. Last of the map edits: everything above
    # finds the shelves by their own hashes.
    once = {}                                          # check id -> [(map path, shelf hash)]
    for path, changes in sorted(planned.items()):
        for h, (cid, item, _, kind) in sorted(changes.items()):
            if kind == 'shop' and item.startswith(shop_items.PREFIX):
                once.setdefault(cid, []).append((path, h))
    if once:
        src_g, old_g = out.read(GAME_DATA)
        flags = placement_flags(old_g)
        free = lambda h: flags.get(h) in (FLAG_KEPT, FLAG_UNTIL_LEFT)   # noqa: E731
        pool = sorted(h for h in shop_removed if free(h))
        moves, kept = {}, {}
        for cid, places in sorted(once.items()):
            if len({p for p, _ in places}) != len(places):
                raise SystemExit('%s: two shelves in one map: they can\'t share one saved flag' % cid)
            own = sorted(removed_boards[x] for x in places if free(removed_boards.get(x)))
            donor = own[0] if own else pool.pop(0) if pool else None
            if donor is None:
                print('  NOTE: %s: no saved flag is free for this shelf (no count board of its own, no removed '
                      'shop object left): it will be on sale again after the area is reloaded' % cid)
                continue
            for p, h in places:
                moves.setdefault(p, {})[h] = donor
            kept[donor] = cid
        for path, mv in sorted(moves.items()):
            src, old = out.read(path)
            new, mentions = shelf_flag_map_edit(old, mv)
            out.write(path, src, old, new)
            for h, donor in sorted(mv.items()):
                print('%-18s %s: shelf %s is now placement %s (%d mentions changed): the saved flag of a removed '
                      'shop board' % (planned[path][h][0], path.split('/')[-1], h, donor, mentions[h]))
        if kept:
            new_g, was = keep_flags(old_g, set(kept))
            out.write(GAME_DATA, src_g, old_g, new_g)
            for donor, cid in sorted(kept.items(), key=lambda x: x[1]):
                print('%-18s %s: flag %s reset type %d -> %d (never reset: set by the shelf when sold, it stays sold)'
                      % (cid, GAME_DATA.split('/')[-1], donor, was[donor], FLAG_KEPT))

    if shop_fix:
        # the child shopkeeper's list (also copied in the adult shopkeeper's pack: kept identical), and a list
        # of the adult shopkeeper's own
        child_pack = ground_items.pack_path(SHOP_KEEPERS['child'])
        child_list = sarc.Sarc.read(plain(child_pack)).files[SHOP_LIST]
        new_child = open_shop_list(child_list, goods['child'])
        new_adult = open_shop_list(child_list, goods['adult'])
        for keeper in ('child', 'adult'):
            pack_path = ground_items.pack_path(SHOP_KEEPERS[keeper])
            src, old = out.read(pack_path)
            arc = sarc.Sarc.read(old)
            if arc.files[SHOP_LIST] != child_list:
                raise SystemExit('%s: its copy of the child shop list differs' % SHOP_KEEPERS[keeper])
            arc.files[SHOP_LIST] = new_child
            out.size(SHOP_LIST, child_list, new_child)
            if keeper == 'adult':
                ap = ground_items.ap_path(SHOP_KEEPERS['adult'])
                adoc = byml.loads(arc.files[ap])
                adoc.root = type(adoc.root)(adoc.root)
                comp = type(adoc.root.get('Components', {}))(adoc.root.get('Components', {}))
                if 'ShopRef' in comp:
                    raise SystemExit('%s already has a shop list of its own' % SHOP_KEEPERS['adult'])
                comp['ShopRef'] = '?' + SHOP_LIST_ADULT
                adoc.root['Components'] = comp
                new_ap = byml.dumps(adoc)
                out.size(ap, arc.files[ap], new_ap)
                arc.files[ap] = new_ap
                arc.files[SHOP_LIST_ADULT] = new_adult
                arc.align[SHOP_LIST_ADULT] = arc.align.get(SHOP_LIST, 8)
                out.add(SHOP_LIST_ADULT, new_adult, SHOP_LIST, child_list)
            new_pack = arc.write()
            back = sarc.Sarc.read(new_pack)
            if set(back.files) != set(arc.files) or any(back.files[k] != v for k, v in arc.files.items()):
                raise SystemExit('read-back: %s differs from what was intended' % pack_path)
            out.write(pack_path, src, old, new_pack)
            print('shop list %-36s %s' % (SHOP_KEEPERS[keeper], ', '.join(
                'shelf %d: %s' % (i, n) for i, n in sorted(goods[keeper].items())) or 'all shelves open'))

    new_rows = {}
    loose_done = {}                                    # lifted animations shared by an item's versions, and by
    #                                                    the items that share an animation project: one copy each

    def lifted_before(path, data):
        if path not in loose_done:
            loose_done[path] = data
            return False
        if loose_done[path] != data:
            raise SystemExit('%s: two different lifted copies in one build' % path)
        return True

    for (item, version), name in sorted(grounds.items()):
        tpl_name = ground_items.template_of(name)
        tpl_pack_path = ground_items.pack_path(tpl_name)
        tpl_pack = plain(tpl_pack_path)
        got, pack, new_inner, rows, loose = ground_items.build(
            item, plain, lambda t: byml.loads(plain(ground_items.table_path(t))).root,
            lambda project: os.path.exists(os.path.join(a.romfs, 'Model', project + '.anim.bfres.zs')), version)
        assert got == name
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=tpl_pack_path)
        out.add(path, pack, tpl_pack_path, tpl_pack)
        tpl_files = sarc.Sarc.read(tpl_pack).files
        for inner, data in new_inner.items():
            like = ground_items.new_file_like(inner, tpl_name)
            out.add(inner, data, like, tpl_files[like])
        for inner in sarc.Sarc.read(pack).files:          # every file of the pack has a size entry
            if out.table.get(inner) is None:
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        for path, (data, like, old_h, new_h, _) in sorted(loose.items()):
            if lifted_before(path, data):
                continue
            out.write_new(path, data, like)
            out.add(path, data, like, plain(like))
            print('%-6s %s: lies %.3f %s on the ground (pose height %.3f -> %.3f, %s)'
                  % (version, item, abs(new_h - old_h), 'higher' if new_h > old_h else 'lower', old_h, new_h, path))
        print('%-6s version %-22s for %s (%d bytes)%s' % (version, name, item, len(pack), {
            'token': ': dropped by a Gold Skulltula, marks it done when picked up (the token\'s AI and blackboard), '
                     'spins as the token does (the token\'s animation settings start %s)' % ground_items.SPIN
        }.get(version, '')))
    # turning items: every level of each family placed on a freestanding item, a rock or a bush
    # (tools/turn_items.py)
    # (a family only on rocks, bushes and pots: its first level lies there only as its one-time version, which
    # turns into the second level's turning item; the first level's turning item is not made)
    ground_families = {f for cid, f in turning.items() if cid not in once_turning}
    for family in sorted(set(turning.values())):
        for level, item in enumerate(family):
            if level == 0 and family not in ground_families:
                continue
            # a first level the game's chests give more with (the weapons: SCRUB_COMPANIONS) gives the same
            bundle_for = flow_name(item) if level == 0 and item in SCRUB_COMPANIONS else None
            got, pack, new_inner, rows, loose = turn_items.build(
                family, level, plain, table_rows,
                lambda project: os.path.exists(os.path.join(a.romfs, 'Model', project + '.anim.bfres.zs')),
                bundle_for)
            name = turn_items.turn_name(item)
            assert got == name
            tpl_pack_path = ground_items.pack_path(ground_items.template_of(name))
            path = ground_items.pack_path(name)
            out.write_new(path, pack, like=tpl_pack_path)
            out.add(path, pack, tpl_pack_path, plain(tpl_pack_path))
            like_files = dict(sarc.Sarc.read(plain(turn_items.AI_PACK)).files)
            for actor in (ground_items.template_of(name), turn_items.DROP_TEMPLATE):
                like_files.update(sarc.Sarc.read(plain(ground_items.pack_path(actor))).files)
            for inner, (data, like) in new_inner.items():
                out.add(inner, data, like, like_files[like])
            for inner in sarc.Sarc.read(pack).files:      # every file of the pack has a size entry
                if out.table.get(inner) is None:
                    raise SystemExit('%s: %s has no resource size entry' % (name, inner))
            for t, row in rows.items():
                new_rows.setdefault(t, []).append(row)
            for path, (data, like, old_h, new_h, _) in sorted(loose.items()):
                if lifted_before(path, data):
                    continue
                out.write_new(path, data, like)
                out.add(path, data, like, plain(like))
                print('%-6s %s: lies %.3f %s on the ground (pose height %.3f -> %.3f, %s)'
                      % ('turn', item, abs(new_h - old_h), 'higher' if new_h > old_h else 'lower', old_h, new_h,
                         path))
            what = turn_items.describe(sarc.Sarc.read(pack).files[shop_items.ai_path(turn_items.ai_name(item))])
            if bundle_for:
                # what the game's chests give with it starts with what the flows add with it (the small bag)
                gives = [(turn_items._actor_of(x), n) for x, n in what['bundle']['gives']]
                if [x for x, _ in gives][:len(SCRUB_COMPANIONS[item])] != SCRUB_COMPANIONS[item] \
                        or what['bundle']['bag'] != SCRUB_COMPANIONS[item][0]:
                    raise SystemExit('%s: the game\'s chests give %r with %s, not %s first as expected'
                                     % (name, gives, bundle_for, SCRUB_COMPANIONS[item]))
            print('turn   version %-22s for %s (%d bytes); its AI %s (%d nodes more than %s): %s%s'
                  % (name, item, len(pack), turn_items.ai_name(item), what['new'], turn_items.BASE_AI,
                     'once Link owns %s it drops %s and deletes itself'
                     % (item, turn_items.turn_name(family[level + 1])) if what['drops']
                     else 'once Link owns %s it deletes itself' % item,
                     '; while Link has no %s it gives what a chest gives with %s (%s) when it is picked up'
                     % (what['bundle']['bag'], bundle_for, ', '.join('%d %s' % (n, x) for x, n in gives))
                     if bundle_for else ''))
    # one-time drops (tools/once_items.py): the versions with the mark, then the rocks, bushes and pots
    once_src = once_items.sources(plain) if once_spots else None
    once_shared = {}                                   # new files that are the same in every pack of these
    model_there = lambda project: os.path.exists(os.path.join(a.romfs, 'Model', project + '.anim.bfres.zs'))  # noqa

    def once_write(name, pack, new_inner, rows, loose, item, said):
        tpl_pack_path = ground_items.pack_path(ground_items.template_of(name))
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=tpl_pack_path)
        out.add(path, pack, tpl_pack_path, plain(tpl_pack_path))
        like_files = dict(sarc.Sarc.read(plain(turn_items.AI_PACK)).files)
        for actor in (ground_items.template_of(name), turn_items.DROP_TEMPLATE, once_items.HEART):
            like_files.update(sarc.Sarc.read(plain(ground_items.pack_path(actor))).files)
        for inner, (data, like) in new_inner.items():
            if inner in once_shared:                   # the same file in every such pack (the number's table)
                if once_shared[inner] != data:
                    raise SystemExit('%s: %s differs from the one in another one-time version' % (name, inner))
                continue
            if not inner.split('/')[-1].startswith((name + '.', once_items.ai_name(item) + '.')):
                once_shared[inner] = data
            out.add(inner, data, like, like_files[like])
        for inner in sarc.Sarc.read(pack).files:          # every file of the pack has a size entry
            if out.table.get(inner) is None:
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        for path, (data, like, old_h, new_h, _) in sorted(loose.items()):
            if lifted_before(path, data):
                continue
            out.write_new(path, data, like)
            out.add(path, data, like, plain(like))
            print('%-6s %s: lies %.3f %s on the ground (pose height %.3f -> %.3f, %s)'
                  % ('once', item, abs(new_h - old_h), 'higher' if new_h > old_h else 'lower', old_h, new_h, path))
        print('once   version %-22s for %s (%d bytes): %s' % (name, item, len(pack), said))

    for item, name in sorted(once_plain.items()):
        got, pack, new_inner, rows, loose = once_items.build_plain(item, plain, table_rows, model_there, once_src)
        assert got == name
        once_write(name, pack, new_inner, rows, loose, item,
                   'its ground version with the AI %s: picked up, it marks what dropped it' % once_items.PLAIN_AI)
    for family in sorted(set(once_turning.values())):
        for level, item in enumerate(family):
            bundle_for = flow_name(item) if level == 0 and item in SCRUB_COMPANIONS else None
            name, pack, new_inner, rows, loose = once_items.build(
                family, level, plain, table_rows, model_there, bundle_for, once_src)
            ai_data = sarc.Sarc.read(pack).files[shop_items.ai_path(once_items.ai_name(item))]
            what = once_items.marks_of(ai_data)
            bundle = turn_items.describe(once_items.unmarked(ai_data))['bundle'] if bundle_for else None
            if bundle_for and (not bundle or bundle['bag'] != SCRUB_COMPANIONS[item][0]):
                raise SystemExit('%s: does not give %s with itself as expected' % (name, SCRUB_COMPANIONS[item][0]))
            once_write(name, pack, new_inner, rows, loose, item,
                       'its turning item with the AI %s: it marks what dropped it when it is picked up%s%s'
                       % (once_items.ai_name(item), ' and when it turns into %s' % turn_items.turn_name(
                           family[level + 1]) if what['turns'] else '',
                          '; while Link has no %s it gives what a chest gives with %s (%s) when it is picked up'
                          % (bundle['bag'], bundle_for, ', '.join('%d %s' % (n, turn_items._actor_of(x))
                                                                  for x, n in bundle['gives']))
                          if bundle_for else ''))
    # a dungeon's keys (tools/dungeon_keys.py): the key's version for each kind of check it is on
    for (dungeon, kind, named), name in sorted(key_versions.items()):
        got, pack, new_inner, rows, like_pack = dungeon_keys.build(dungeon, kind, plain, table_rows, model_there,
                                                                   once_src, named)
        assert got == name
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=like_pack)
        out.add(path, pack, like_pack, plain(like_pack))
        for inner, (data, like, like_data) in sorted(new_inner.items()):
            if inner in once_shared:                   # the same file as in the one-time versions' packs
                if once_shared[inner] != data:
                    raise SystemExit('%s: %s differs from the one in another version' % (name, inner))
                continue
            if not inner.split('/')[-1].startswith(name + '.'):
                once_shared[inner] = data              # also the key's AI: the same in a named key's pack
            out.add(inner, data, like, like_data)
        for inner in sarc.Sarc.read(pack).files:          # every file of the pack has a size entry
            if out.table.get(inner) is None:
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        if named:
            print('key    version %-22s its messages are found under %s (the dungeon\'s name in them)'
                  % (name, dungeon_keys.MESSAGE_NAME % dungeon))
        print('key    version %-22s a small key of %s (%d bytes): %s' % (name, dungeon, len(pack), {
            'once': 'picked up, it adds 1 to %s and marks what dropped it' % dungeon_keys.flag(dungeon),
            'token': 'dropped by a Gold Skulltula: picked up, it adds 1 to %s and marks the skulltula done'
                     % dungeon_keys.flag(dungeon),
            'chest': 'what a chest holds; the chest\'s opening event adds 1 to %s' % dungeon_keys.flag(dungeon),
        }[kind]))

    # named keys: their three texts in every language's message archive, with the dungeon's name as that
    # language's own text has it
    named_keys = sorted({dungeon for dungeon, _, named in key_versions if named})
    if named_keys:
        def key_lines(arc):
            places = msbt.Msbt.read(arc.files[dungeon_keys.LOCATION_FILE]).texts
            lines = {}
            for dungeon in named_keys:
                if dungeon not in places:
                    raise SystemExit('%s: no name for it in %s' % (dungeon, dungeon_keys.LOCATION_FILE))
                lines.update(dungeon_keys.messages(dungeon, msg_plain(places[dungeon]), key_colours.get(dungeon)))
            return lines
        scrub_messages(out, a.romfs, key_lines, dungeon_keys.MESSAGE_FILE)
        print('%-18s %s: the texts of the named keys of %s added in every language'
              % ('key names', dungeon_keys.MESSAGE_FILE, ', '.join(
                  '%s (its name in colour %d)' % (x, key_colours[x]) if x in key_colours else x
                  for x in named_keys)))
    for dungeon in sorted(set(key_colours) - set(named_keys)):
        if dungeon in key_colour_asked:
            raise SystemExit('--key-colour %s: no key of this build names %s (%s@%s%s)'
                             % (dungeon, dungeon, dungeon_keys.KEY_ITEM, dungeon, dungeon_keys.NAMED))

    # the rocks, bushes and pots themselves: an AI of our own name for each actor that drops for us. It only
    # hands its placement's number to its drop: it does not name another level's version (Drop__DropActor is
    # an instance parameter, and writing one stops the game: tools/once_items.py, seen 2026-11-22)
    once_actors = {}                                   # actor -> the game's AI it runs
    for h, (cid, item, actor) in sorted(once_spots.items()):
        if actor not in once_actors:
            once_actors[actor] = once_items.root_ai_of(
                sarc.Sarc.read(plain(ground_items.pack_path(actor))).files, actor)[0]
    for actor, root in sorted(once_actors.items()):
        ap = ground_items.ap_path(actor)
        own_files = sarc.Sarc.read(plain(ground_items.pack_path(actor))).files
        _, new, changed = once_items.dropper_files(own_files, actor, once_src)
        held = [x for x in once_items.holders(a.romfs, actor)
                if ap in sarc.Sarc.read(plain(ground_items.pack_path(x))).files]
        if actor not in held:
            raise SystemExit('%s: its own pack is not among the packs that hold its file' % actor)
        for holder in held:
            path = ground_items.pack_path(holder)
            src, old = out.read(path)
            out.write(path, src, old, once_items.patch_pack(old, new, changed))
        out.size(changed[0], changed[1], changed[2])
        for inner, (data, like) in sorted(new.items()):
            if inner in once_shared:
                if once_shared[inner] != data:
                    raise SystemExit('%s: %s differs from the one made for another actor' % (actor, inner))
                continue
            once_shared[inner] = data
            out.add(inner, data, like, own_files[like])
        what = once_items.dropper_of(new[shop_items.ai_path(once_items.dropper_ai_name(root))][0])
        written = [k for _, k in once_items.actor_writes(new[shop_items.ai_path(once_items.dropper_ai_name(root))][0])
                   if k in once_items.instance_keys(own_files)]
        if what['steps'] or written:
            raise SystemExit('%s: its AI writes an instance parameter of its blackboard (%s): that stops the game'
                             % (actor, ', '.join(written) or once_items.DROP_KEY))
        print('once   %-22s runs the AI %s (%d nodes more than %s): for a drop of ours it hands its placement\'s '
              'number to it (%s)%s; in %d pack%s: %s'
              % (actor, what['name'], what['new'], root, what['key'],
                 ''.join('; Link owns %s: %s instead of %s' % (i, to, frm) for frm, i, to in what['steps']),
                 len(held), '' if len(held) == 1 else 's', ', '.join(held)))
    # three-level chests: one actor per family placed, and its _NoBake twin where a placement is one
    # (tools/three_chest.py); the twin's pack holds the same new files
    three_shared = {}
    if three_used:
        # the light on a chest's bone is given to it by name: an entry in the game's list for each of ours
        lit = [three_chest.chest_name(family, twin) for family, twin in sorted(three_used)]
        src, old = out.read(three_chest.LIGHT_RIGS)
        out.write(three_chest.LIGHT_RIGS, src, old, three_chest.light_rigs(old, lit))
        print('chest lights       %s: %s added, as the checking chest\'s' % (
            three_chest.LIGHT_RIGS.split('/')[-1], ', '.join(lit)))
    for (family, twin), (second, third) in sorted(three_used.items()):
        name, pack, new_inner, rows = three_chest.build(family, second, third, plain, table_rows, twin)
        base_pack = ground_items.pack_path(three_chest.BASE + (three_chest.NOBAKE if twin else ''))
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=base_pack)
        out.add(path, pack, base_pack, plain(base_pack))
        like_files = sarc.Sarc.read(plain(base_pack)).files
        for inner, (data, like) in new_inner.items():
            if inner in three_shared:
                if three_shared[inner] != data:
                    raise SystemExit('%s: %s differs from the one in its twin' % (name, inner))
                continue
            three_shared[inner] = data
            out.add(inner, data, like, like_files[like])
        for inner in sarc.Sarc.read(pack).files:          # every file of the pack has a size entry, but for
            if out.table.get(inner) is None and inner not in like_files:   # the game's own without one (debug)
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        what = three_chest.describe(sarc.Sarc.read(pack).files[shop_items.ai_path(three_chest.chest_name(family))])
        print('chest  %-22s (%d bytes): %s with a third held item (%s); its AI %s (%d nodes more than %s): Link '
              'has %s -> %s, else the checking chest\'s own answer'
              % (name, len(pack), three_chest.BASE + (three_chest.NOBAKE if twin else ''), what['key'],
                 what['name'], what['new'], three_chest.BASE, what['second'], what['third']))
    shop_shared = {}                                   # new files that are the same in every shop version
    for (item, price), name in sorted(shops.items()):
        tpl_pack_path = ground_items.pack_path(shop_items.TEMPLATE)
        tpl_pack = plain(tpl_pack_path)
        got, pack, new_inner, rows, loose = shop_items.build(item, price, plain, table_rows, once=True)
        assert got == name
        path = ground_items.pack_path(name)
        out.write_new(path, pack, like=tpl_pack_path)
        out.add(path, pack, tpl_pack_path, tpl_pack)
        like_files = {}
        for actor in (shop_items.TEMPLATE, shop_items.PRICE_TEMPLATE):
            like_files.update(sarc.Sarc.read(plain(ground_items.pack_path(actor))).files)
        for inner, (data, like) in new_inner.items():
            if inner in shop_shared:                   # the same file in every shop version's pack (their AI)
                if shop_shared[inner] != data:
                    raise SystemExit('%s: %s differs from the one in another shop version' % (name, inner))
                continue
            if not inner.split('/')[-1].startswith(name + '.'):
                shop_shared[inner] = data
            out.add(inner, data, like, like_files[like])
        for inner in sarc.Sarc.read(pack).files:
            if out.table.get(inner) is None:
                raise SystemExit('%s: %s has no resource size entry' % (name, inner))
        for t, row in rows.items():
            new_rows.setdefault(t, []).append(row)
        for path, (data, like, info) in sorted(loose.items()):
            if path in shop_shared:                    # one animation project for every shop version of the item
                continue
            shop_shared[path] = data
            out.write_new(path, data, like)
            out.add(path, data, like, plain(like))
            vec = lambda v: '(%s)' % ', '.join('%.4f' % x for x in v)  # noqa: E731
            print('shelf pose %s: %s, a copy of %s; Pose_Common: the item\'s Pose_Common (scale %.3f, turn %s, at '
                  '%s); Pose_GetDemo (held up): the same at %s, the model y %.3f .. %.3f from the point it is held '
                  'at; Pose_Shop: scale %.3f, turn %s, at %s; on the shelf the model is x %.3f .. '
                  '%.3f, y %.3f .. %.3f, z %.3f .. %.3f from the shelf point'
                  % ((item, path, like.split('/')[-1]) + tuple(x for x in (info['common'][0], vec(info['common'][1]),
                                                                           vec(info['common'][2])))
                     + (vec(info['held'][2]), info['held_lo'][1], info['held_hi'][1])
                     + tuple(x for x in (info['shop'][0], vec(info['shop'][1]), vec(info['shop'][2])))
                     + tuple(x for i in range(3) for x in (info['lo'][i], info['hi'][i]))))
        print('shop   version %-22s for %s, %d rupees, sold once (%d bytes); its AI %s marks the shelf\'s '
              'placement as not to be made again once sold and never shows the model again'
              % (name, item, price, len(pack), shop_items.ONCE_AI))
    for t, rws in sorted(new_rows.items()):
        path = ground_items.table_path(t)
        src, old = out.read(path)
        out.write(path, src, old, ground_items.add_rows(old, rws))
        print('table %-16s %d rows added' % (t, len(rws)))

    if a.gossip:
        gossip_build(out, a.romfs, gossip)

    # The starting state of a new file: one more push per item and one more setter per flag in the game's own
    # new-game module (tools/start_state.py: read back against the game's files before it is written)
    if start_items or start_flags:
        src, old = out.read(start_state.MODULE)
        new, said = start_state.edit(old, out.read(start_state.SETTER_SOURCE)[1], start_items, start_flags)
        out.write(start_state.MODULE, src, old, new)
        for line in said:
            print('%s (%s)' % (line, start_state.MODULE))
        for name, _, _, note in start_flags:
            if note:
                print('NOTE start flag %s: %s' % (name, note))
    out.finish()
    print('mod folder:', os.path.join(a.out, a.name))
    if a.longshot:
        bat = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'Launch NX2-ZOOTR test.bat')
        mods = os.path.abspath(a.out)
        user = os.path.join(os.path.dirname(mods), 'user')
        with open(bat, 'w', encoding='ascii', newline='\r\n') as f:
            f.write(LAUNCHER % {'longshot': os.path.abspath(a.longshot), 'mods': mods, 'user': user})
        print('launcher:', bat)


if __name__ == '__main__':
    main(sys.argv[1:])
