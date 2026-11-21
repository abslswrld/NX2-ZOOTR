"""Build a Longshot mod folder that changes what some checks give, by permanent check ID.

    python tools/build_mod.py --romfs "<romfs>" --out out\\mods --name NX2-ZOOTR KF_MIDO_CHEST_01=Item_Boomerang ...

Supported: chests and pots (their item is their Drop__DropActor in the map file; rocks, bushes and Gold
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

Checking chests: the game has a small chest that looks in Link's inventory (Obj_TBox_A_06, see CHECKING_CHEST).
One of the game's own that gets an item becomes the ordinary small chest, so it always gives the placed item.
Progressive pair (opt-in, a test for now): CHECK_ID=First>Second on a small chest makes it a checking chest that
gives First while Link doesn't have First, else Second; only the pairs in PROGRESSIVE_PAIRS are accepted:

    python tools/build_mod.py ... "KF_MIDO_CHEST_01=Item_Scale_Silver>Item_Scale_Gold"
(quoted: > is the shell's redirection otherwise). The pairs: Silver > Gold Scale, Hookshot > Longshot, Fairy
Ocarina > Ocarina of Time.
The same on a freestanding item (to test in game): the placement becomes First's turning item
(tools/turn_items.py): a ground item of First that, once Link owns First, drops Second's in its place and removes
itself; Second's removes itself once Link owns Second. Two freestanding items with the same pair give First then
Second in either order.
The same on a liftable rock or a solid bush (to test in game): its drop (Drop__DropActor) becomes First's turning
item, so what comes out is First while Link doesn't own it, else Second, decided where it lies and not when the
rock breaks. Not on shelves, pots or Gold Skulltulas yet.
Three-level family (to test in game): CHECK_ID=First>Second>Third on a small chest makes it a chest of our own
(tools/three_chest.py: the checking chest with a third held item and a second question) that gives Third when
Link has Second, else Second when Link has First, else First; only the families in THREE_LEVEL_FAMILIES (the
bomb bags), and only in small chests:

    python tools/build_mod.py ... "KF_MIDO_CHEST_01=Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large"

The same on a gift that has flow data (to test in game): the giver's own flow asks the inventory in front of
its call of the shared get flow, as the game's own flows do for upgrades, and gives First or Second
(gift_pair_edit). Gifts without flow data (cutscene gifts) and songs are refused.
The same on a Deku Scrub that sells one thing once (to test in game): the scrub's branch of the scrub flow asks
the inventory before the sale, as the game's own stick-bag and nut-bag scrubs do, and sells First or Second at
the scrub's price (scrub_flow_edit, point 4).

Game fixes (--fix NAME, see FIXES and FILE_FIXES):
    kokiri_shop_full_stock   the Kokiri Shop sells the same 8 shelves as a child before and after meeting the
                             Deku Tree (the "low on stock" set is removed, every shelf is open from the
                             start, the child shopkeeper greets as after the Deku Tree), and the adult
                             shopkeeper gets a shop list of its own; needed to change
                             shop shelves (each shelf's item, sold once, goes into the shopkeeper's list)
    bombchus_without_bag     Bombchus get a capacity of their own (BOMBCHU_MAX, as in the original game) and
                             no longer need the bomb bag: in the remake their maximum is the bomb bag's, so
                             without one it is 0; bomb bags stop raising and refilling them
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
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import ground_items  # noqa: E402
import harp_colors  # noqa: E402
import shop_items  # noqa: E402
import sizes  # noqa: E402
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
# Progressive pairs (opt-in, CHECK_ID=First>Second on a small chest): the chest becomes the game's checking
# chest: First while Link doesn't have First, else Second. Two chests with the same pair give First then Second
# in either opening order. Only pairs listed here are accepted, one family at a time (the chest's inventory
# question must know the family's name; three-level families can't be done this way).
# The names are the items' own names, the ones the inventory is saved under (GameData: IsGet.<name>,
# PouchData.<name>.StockNum) and the game's own flows ask about (EventQueryIsExistInPouch). The chest looks for
# First under that name (Drop__CheckActor) and holds each item as a chest gives it (in_chest: an ocarina as its
# held-up version Item_NX2_<x>, which goes into the inventory as the ocarina itself, its PouchActor).
PROGRESSIVE_PAIRS = {
    ('Item_Scale_Silver', 'Item_Scale_Gold'),      # in game 2026-11-18: both opening orders work
    # the game's own chests give these two names (Dampe's goal chest, the Water Temple). Its flows ask for the
    # Longshot and then for the Hookshot to mean "has a hookshot" (MiniGame_DampeRace, Npc_Gerudo_004), so the
    # Longshot most likely takes the Hookshot's place in the inventory: the second chest of a pair is only
    # opened once, so the order holds either way
    ('Item_Hookshot', 'Item_Longshot'),            # in game 2026-11-19: works
    # ocarinas are Link's instrument (no get-demo settings): the chest holds their held-up versions. The
    # Ocarina of Time itself teaches nothing: the Song of Time is an item of the moat cutscene (Dm_MelodyGet_Time)
    ('Item_Ocarina_Fairy', 'Item_Ocarina_Time'),   # in game 2026-11-19: works
}
# Three-level families (opt-in, CHECK_ID=First>Second>Third on a small chest): the chest becomes a chest of our
# own, Obj_TBox_NX2_<name> (tools/three_chest.py): the game's checking chest with a third held item and a second
# question. Third when Link has Second, else Second when Link has First, else First: three chests with the same
# family give the three levels in order, whatever the opening order. family -> the name of its chest.
# Every level is its own inventory item under its own name and stays owned when the next one comes
# (GameData: IsGet.<name>, PouchData.<name>.StockNum for each; the game's own flows ask "has Medium?" and then
# "has Large?": Npc_Goron_012_Child, MiniGame_BombchuBowling), so "has Second?" then "has First?" finds the next.
# A chest holds each level under its own name: all three are item event actors with the get demo (Medium and
# Large inherit the Small one's item settings, Component/PouchContentParam/BombBag, which name no other item to
# put in the inventory: each goes in as itself). The game's own chest gives Item_BombBag_Small (Dodongo's Cavern).
THREE_LEVEL_FAMILIES = {
    ('Item_BombBag_Small', 'Item_BombBag_Medium', 'Item_BombBag_Large'): 'BombBag',   # 20, 30, 40 bombs
}


def three_level_parse(world, assignments):
    """takes the three-level families (CHECK_ID=First>Second>Third) out of `assignments`: each becomes
    (CHECK_ID, First), as a pair's; returns {check id: family}. Stops the build for a family that is not in
    THREE_LEVEL_FAMILIES, and for a check that is not a chest (a big chest is refused when its map is changed:
    patch_file)"""
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
        if kinds != {'chest'}:
            raise SystemExit('%s: a three-level family (First>Second>Third) can only be put in a small chest '
                             '(this check: %s)' % (cid, ', '.join(sorted(kinds)) or 'an event, no map placement'))
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
# item, tools/turn_items.py), or a liftable rock or solid bush (its drop is the turning item: rocks, bushes and
# pots drop through the same drop part, Component/DropParam/Drop_ResourceSupply_00, whatever their placement's
# Drop__DropActor names, and a turning item made by a drop is what the second level of every pair already is).
# Not yet: shelves (the shop version has no such AI), pots (the user: not started), Gold Skulltulas (what they
# drop must carry the skulltula's flag on: no game node hands it from one drop to the next), songs (events).
# Gifts: gift_pair_kind, gift_pair_edit. Scrubs: scrub_pair_kind, scrub_flow_edit.
PAIR_KINDS = ('chest', 'freestanding', 'rock', 'bush')
TURN_KINDS = ('freestanding', 'rock', 'bush')     # the kinds whose pair is a turning item
# Two turning items of one family must not lie where Link can touch both at once: the second could be picked up
# in the frame the first's scene ends, before it has turned (it would give the first level again). Metres,
# between their map positions (for a rock or a bush: where it stands; a rock carried and thrown next to another
# item of its family is not covered).
TURN_MIN_DISTANCE = 2.0


def pair_kind(world, cid):
    """the kind of check a progressive pair is placed on (one of PAIR_KINDS); stops the build for any other
    kind, or when the check's placements are not all of one kind"""
    r, name, loc = find_check(world, cid)
    kinds = {world.checks[scene][spot_id]['kind'] for scene, spot_id, _ in world.placements_of(r, loc)}
    if len(kinds) != 1 or not kinds <= set(PAIR_KINDS):
        raise SystemExit('%s: a progressive pair (First>Second) can only be put in a chest, on a freestanding '
                         'item, or on a rock or a bush (this check: %s)'
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
    """(Drop__CheckActor, Drop__DropActor_Substitute) of a checking chest holding a progressive pair: it looks
    for First under the item's own name and holds Second as a chest gives it (in_chest), as it holds First
    (its Drop__DropActor)"""
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
         on_shelf=lambda item, shelf_actor: item, gs_drop=lambda item: item):
    """{map file path in romfs: {placement hash: (check id, new item, old item, kind)}}.
    on_ground(item): the actor to use where the item lies on the ground (freestanding items, pot drops);
    in_chest(item): the actor a chest gives (and shows held up); on_shelf(item, actor now on the shelf): the
    shelf actor that sells the item; gs_drop(item): the actor a Gold Skulltula drops"""
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


def song_skip(fc, cid, item, song, sync=None):
    """the song cutscene (Dm_MelodyGet_*) is still started as before, so the game records it as played (that
    is what keeps its trigger from coming back, e.g. SacredForestMeadow_Child_Prefab_bbc3: "Dm_MelodyGet_Saria"
    not played), but its first entry point now only fades in, hands over the item the way the cutscene hands
    over the song (GetPouchContent<GetPouchContentByActorName>: "You got ..." window, then the item; plus what the
    item needs, SCRUB_COMPANIONS) and ends: no lesson, no song. sync: the sync steps (sync_template) to run
    after the get, for an ocarina. Returns lines saying what was changed."""
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
    nxt = sync_steps(fc, sync) if sync else None
    for companion in reversed(SCRUB_COMPANIONS.get(item, [])):
        nxt = fc.add_action('PouchSystemActor', 'EventTriggerAddOrRemovePouchContent',
                            evfl.Params(Num=1, Actor=companion, IsGetEvent=False,
                                        IsSetMessageTargetActorName=False, IsEquipDIrect=False), next=nxt)
    get = fc.add_subflow(SONG_GET[0], SONG_GET[1], evfl.Params(ActorName=item), next=nxt)
    first = fc.add_action(fade.actor, 'EventEventFadeIn', params, next=get)
    was = fc.events[ep.main].name
    ep.main = first
    fc.update_entry_points()
    return ['%-18s cutscene starts with the get of %s instead of the song lesson (%s; was %s)'
            % (cid, item, fc.events[first].name, was)]


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
    from the root: {'first', 'second' (None when the branch is a plain sale), 'ask' (the question's
    parameters), 'steps' (what Second's branch does before its sale, in order: actor, action, parameters),
    'sells' ((First's sale's parameters, Second's))}. Raises SystemExit when the branch is not one
    scrub_flow_edit makes"""
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
    a = fc.actors[e.actor] if e.type == 'switch' else None
    if a is None or (a.name, a.secondary or '', a.queries[e.query]) != (GIFT_PAIR_ACTOR, '', SCRUB_PAIR_QUERY) \
            or sorted(v for v, _ in e.cases) != [0, 1]:
        raise SystemExit('%s: the branch for %s is neither a sale nor the inventory question' % (SCRUB_ROOT, first))
    cases = dict(e.cases)
    steps, k = [], by[cases[0]]
    while k.type == 'action':
        steps.append((fc.actors[k.actor].name, _action_name(fc, k), dict(k.params)))
        if k.next is None:
            raise SystemExit('%s: the branch for %s ends before a sale' % (SCRUB_ROOT, first))
        k = by[k.next]
    one, two = by[cases[1]], k
    if any(s.type != 'subflow' or s.flowchart != '' or s.entry != SCRUB_SELL or s.next is not None
           for s in (one, two)):
        raise SystemExit('%s: the branch for %s does not end in two one-time sales' % (SCRUB_ROOT, first))
    return {'first': first, 'second': two.params.get('ActorName'), 'ask': dict(e.params), 'steps': steps,
            'sells': (dict(one.params), dict(two.params))}


def scrub_pair_check(fc, first, second):
    """read-back of a pair's branch: the question asks for First; "has not" sells First; "has" writes Second's
    name where the line and the hold-up check read it, waits, and sells Second; the two sales differ in the
    item only"""
    got = scrub_pair_read(fc, first)
    one, two = got['sells']
    if got['second'] != second or got.get('ask') != {'Num': 1, 'Actor': first} \
            or one.get('ActorName') != first or {k: v for k, v in one.items() if k != 'ActorName'} \
            != {k: v for k, v in two.items() if k != 'ActorName'} \
            or got['steps'] != [('GameDataActor', SCRUB_NAME_WRITE,
                                 {'Index': -1, 'GameDataName': SCRUB_VAR, 'Value': second}),
                                ('EventSystemActor', 'EventWait', {'Frames': SCRUB_WRITE_WAIT, 'IsWaitEnd': True})]:
        raise SystemExit('read-back: %s: the branch for %s>%s is not as intended: %r'
                         % (SCRUB_FLOW, first, second, got))
    return got


def scrub_flow_edit(fc, sales, direct=(), sync=None, pairs=None):
    """sales: [(check id, new item, [(talk event, original item)])]. Every changed scrub sells its item once.
    direct: the items Link can't hold up (ground_items.can_hold_up); sync {item: sync steps}: see point 3.
    pairs: {check id: (first, second)} for the scrubs that hold a progressive pair (their item in `sales` is
    First): see point 4.
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
    The price is what the game's own calls ask for the scrub's original item (the first copy's). Returns lines
    saying what was changed."""
    pairs = pairs or {}
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
    second_of = {}                                     # First -> Second, or None for an item sold alone
    for cid, item, copies in sales:
        second = pairs[cid][1] if cid in pairs else None
        if cid in pairs and pairs[cid][0] != item:
            raise SystemExit('%s: sells %s, not the first level of its pair %s' % (cid, item, '>'.join(pairs[cid])))
        for x in (item, second):
            if x in known:
                raise SystemExit('%s: %s is sold by the game\'s own scrub branches (other scrubs would sell it '
                                 'at this price too): not supported yet' % (cid, x))
        if second_of.setdefault(item, second) != second:
            raise SystemExit('%s: %s is sold alone by one scrub and as the first level of a pair by another: '
                             'one branch cannot do both' % (cid, item))
        if second and (SCRUB_COMPANIONS.get(item) or SCRUB_COMPANIONS.get(second)):
            raise SystemExit('%s: %s>%s: a pair with an item that needs another one given with it is not '
                             'supported on a scrub' % (cid, item, second))
        asked = []
        for talk, old in copies:
            start = eps.get(talk)
            if start is None:
                raise SystemExit('%s: its talk %s is not in %s: not supported yet' % (cid, talk, SCRUB_FLOW))
            if not (by[start].type == 'subflow' and by[start].entry == SCRUB_ROOT):
                if second:
                    raise SystemExit('%s: a progressive pair can only be put on a scrub that sells one thing '
                                     'once (its talk %s sells again and again: nothing would keep it from '
                                     'selling both levels)' % (cid, talk))
                repeat.setdefault(talk, []).append(item)
            asked += sorted({e.params.get('Price') for e in calls if e.params.get(SCRUB_PRICE_KEYS[e.entry]) == old})
        if not asked:
            raise SystemExit('%s: price of %s not found' % (cid, [o for _, o in copies]))
        price = asked[0]
        if len(set(asked)) > 1:
            said.append('%s: its copies cost %s; sells at %s' % (cid, sorted(set(asked)), price))
        if prices.get(item, (price,))[0] != price:
            raise SystemExit('%s: %s is also sold by %s at %s rupees, here %s'
                             % (cid, item, prices[item][1], prices[item][0], price))
        prices[item] = (price, cid)
    both = list(second_of) + [s for s in second_of.values() if s]
    if len(set(both)) != len(both):
        raise SystemExit('%s: an item would be sold by two branches: %s' % (SCRUB_FLOW, sorted(
            x for x in set(both) if both.count(x) > 1)))
    template = next(e for e in calls if e.entry == SCRUB_SELL)
    pair_tpl = scrub_pair_template(fc) if any(second_of.values()) else None
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
        target, second = sell, second_of[item]
        if second:
            (q_actor, q_params, has, has_not), (w_params, wait_actor, wait_params) = pair_tpl
            params2 = evfl.Params(params)
            params2['ActorName'] = second
            sell2 = fc.add_subflow('', SCRUB_SELL, params2)
            wait_params = evfl.Params(wait_params)
            wait_params['Frames'] = SCRUB_WRITE_WAIT
            wait = fc.add_action(wait_actor, 'EventWait', wait_params, next=sell2)
            w_params = evfl.Params(w_params)
            w_params['GameDataName'], w_params['Value'] = SCRUB_VAR, second
            write = fc.add_action('GameDataActor', SCRUB_NAME_WRITE, w_params, next=wait)
            ask = evfl.Params(q_params)
            ask['Actor'] = item
            target = fc.add_switch(q_actor, SCRUB_PAIR_QUERY, [(has, write), (has_not, sell)], ask)
        sw = fc.add_switch('GameDataActor', 'EventQueryIsGameDataString64', [(0, target), (1, head)],
                           evfl.Params(GameDataName=SCRUB_VAR, Index=-1, Value=item))
        if fc.repoint(head, sw, keep=(sw,)) < 1:
            raise SystemExit('%s: nothing led to %s' % (SCRUB_ROOT, by[head].name))
        head = sw
        said.append('%s sells %s at %s rupees, once (new branch %s)%s' % (cid, item, price, fc.events[sw].name,
                    ', with %s' % ', '.join(extra) if extra else ''))
        if second:
            said.append('%s: a progressive pair: asks first (%s: %s.%s %s): Link has no %s -> %s sells %s, else '
                        '%s is written into %s, %d frames pass and %s sells %s at the same price'
                        % (cid, fc.events[target].name, GIFT_PAIR_ACTOR, SCRUB_PAIR_QUERY, dict(ask), item,
                           fc.events[sell].name, item, second, SCRUB_VAR, SCRUB_WRITE_WAIT,
                           fc.events[sell2].name, second))
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
    for first, second in sorted(second_of.items()):
        if second:
            scrub_pair_check(fc, first, second)
    return said


def scrub_messages(out, romfs, lines):
    """new scrub lines {label: text} in every language's message archive"""
    for fn in sorted(os.listdir(os.path.join(romfs, 'Mals'))):
        if not fn.endswith('.sarc.zs'):
            continue
        path = 'Mals/' + fn[:-3]
        src, old = out.read(path)
        arc = sarc.Sarc.read(old)
        m = msbt.Msbt.read(arc.files[SCRUB_MSG_FILE])
        if m.write() != arc.files[SCRUB_MSG_FILE] or set(lines) & set(m.texts):
            raise SystemExit('%s: %s does not round-trip or already has %s' % (path, SCRUB_MSG_FILE, sorted(lines)))
        m.texts.update(lines)
        new_msg = m.write()
        if msbt.Msbt.read(new_msg).texts != m.texts:
            raise SystemExit('read-back: %s in %s' % (SCRUB_MSG_FILE, path))
        arc.files[SCRUB_MSG_FILE] = new_msg
        new = arc.write()
        back = sarc.Sarc.read(new)
        if set(back.files) != set(arc.files) or any(back.files[k] != v for k, v in arc.files.items()):
            raise SystemExit('read-back: %s differs from what was intended' % path)
        out.write(path, src, old, new)


def patch_file(data, changes, checking=None, three=None):
    """change what the actors with these hashes give: chests and pots through their Drop__DropActor (chests'
    special opening events handled by CHEST_EVENTS), freestanding items by their actor type (Gyaml);
    checking: {hash: (item to look for, item given when Link has it)}: that small chest becomes the game's
    checking chest (CHECKING_CHEST). A game checking chest that is not in `checking` becomes the ordinary chest
    (PLAIN_CHEST) without its check settings, so it always gives the placed item;
    three: {hash: name of a three-level family}: that chest (one of `checking`) becomes the family's own chest
    instead (checking_chest), with the same settings;
    returns (new data, {hash: old item}, {hash: new Dynamic as intended})"""
    checking = checking or {}
    three = three or {}
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
    data (the flow and the event that hand the item over). Gifts without that data (cutscene gifts: the builder
    has no flow step to put the question in front of) and songs stop the build"""
    r, name, loc = find_check(world, cid)
    if world.spots_of(r, loc):
        return False
    if loc.get('song') or not loc.get('gift'):
        raise SystemExit('%s: a progressive pair (First>Second) cannot be put on this gift: the builder has no '
                         'flow data for it ("gift": flow, event, item), so there is no step of the giver\'s own '
                         'flow to put the inventory question in front of' % cid)
    return True


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


def gift_pair_edit(fc, events, template, direct=()):
    """a progressive pair on gift events. events: {event name: (check id, (first, second))}; each event already
    gives First (gift_edit: a call of Dm_SY_GetInEvent, or of GetPouchContent for an item in `direct`, one Link
    can't hold up). In front of it goes the game's question "does Link have First?" (template:
    gift_pair_template; the PouchSystemActor entry is added as the game's flow has it when this flow has none):
    no -> the event as it is (First), yes -> a new copy of that call naming Second, leading on to the same step.
    Every link to the gift event (a step before it, a branch, a fork, an entry point) now goes to the question.
    Returns (lines saying what was changed, {event name: (question's name, Second's call's name)})."""
    actor, params, has, has_not = template
    said, made = [], {}
    for ev, (cid, (first, second)) in sorted(events.items()):
        i = next((k for k, e in enumerate(fc.events) if e.name == ev), None)
        if i is None:
            raise SystemExit('%s: event %s not in the flow' % (cid, ev))
        e = fc.events[i]
        how = DIRECT_GET[0] if first in direct else GIFT_FLOW
        if e.type != 'subflow' or e.flowchart != how or not isinstance(e.params, dict) \
                or e.params.get('ActorName') != first:
            raise SystemExit('%s: event %s is not the call that gives %s' % (cid, ev, first))
        if (first in direct) != (second in direct):
            raise SystemExit('%s: %s and %s are not given the same way (one is held up, the other only has the '
                             'get window): not as a pair on a gift' % (cid, first, second))
        give = evfl.Params(e.params)
        give['ActorName'] = second
        yes = fc.add_subflow(e.flowchart, e.entry, give, next=e.next)
        ask = evfl.Params(params)
        ask['Actor'] = first
        q = fc.add_switch(flow_copy_actor(fc, actor), GIFT_PAIR_QUERY, [(has, yes), (has_not, i)], ask)
        moved = fc.repoint(i, q, keep=(q,))
        if not moved:
            raise SystemExit('%s: nothing leads to event %s' % (cid, ev))
        made[ev] = (fc.events[q].name, fc.events[yes].name)
        said.append('%-18s %s: asks first (%s: %s.%s %s): Link has no %s -> %s gives %s, else %s gives %s '
                    '(%s<%s>); %d link%s moved to the question'
                    % (cid, ev, fc.events[q].name, GIFT_PAIR_ACTOR, GIFT_PAIR_QUERY, dict(ask), first, ev, first,
                       fc.events[yes].name, second, e.flowchart, e.entry, moved, '' if moved == 1 else 's'))
    fc.update_entry_points()
    return said, made


def gift_pair_read_back(path, before, after, events, made, template):
    """the flow written (after) against the flow before the pair went in: the same events, actors and entry
    points, but: two new events per gift (the question and Second's call, as intended), the links to the gift
    now on the question, PouchSystemActor (added when the flow had none) with the query, and the entry points'
    lists of calls with Second's call added where the gift's is"""
    bad = lambda what: SystemExit('read-back: %s: %s' % (path, what))   # noqa: E731
    actor, params, has, has_not = template
    old = {e.name: e for e in before.events}
    new = {e.name: e for e in after.events}
    added = {n for pair in made.values() for n in pair}
    if set(new) != set(old) | added or set(old) & added or len(added) != 2 * len(events):
        raise bad('events differ from what was intended')
    name_of = lambda fc, i: None if i is None else fc.events[i].name   # noqa: E731
    to_q = {ev: q for ev, (q, _) in made.items()}

    def shape(fc, e, moved=False):
        sw = (lambda n: to_q.get(n, n)) if moved else (lambda n: n)   # noqa: E731
        a = fc.actors[e.actor] if e.type in ('action', 'switch') else None
        return (e.type, (a.name, a.secondary) if a else None,
                a.actions[e.action] if e.type == 'action' else None,
                a.queries[e.query] if e.type == 'switch' else None,
                e.params, e.flowchart, e.entry, e.value, sw(name_of(fc, e.next)), sw(name_of(fc, e.join)),
                [(v, sw(name_of(fc, c))) for v, c in e.cases], [sw(name_of(fc, f)) for f in e.forks])

    for name, o in old.items():
        if shape(after, new[name]) != shape(before, o, moved=True):
            raise bad('%s differs from what was intended' % name)
    for ev, (cid, (first, second)) in events.items():
        q, yes, gift = new[made[ev][0]], new[made[ev][1]], new[ev]
        qa = after.actors[q.actor] if q.type == 'switch' else None
        if qa is None or (qa.name, qa.secondary, qa.queries[q.query]) != (GIFT_PAIR_ACTOR, '', GIFT_PAIR_QUERY) \
                or list(q.params.items()) != [(k, first if k == 'Actor' else v) for k, v in params.items()] \
                or [(v, name_of(after, c)) for v, c in q.cases] != [(has, yes.name), (has_not, ev)]:
            raise bad('the question in front of %s is not as intended' % ev)
        want = evfl.Params(gift.params)
        want['ActorName'] = second
        if gift.params.get('ActorName') != first or yes.type != 'subflow' \
                or (yes.flowchart, yes.entry, yes.next) != (gift.flowchart, gift.entry, gift.next) \
                or list(yes.params.items()) != list(want.items()):
            raise bad('the two calls behind the question of %s are not as intended' % ev)
    was = [(a.name, a.secondary, a.argument, a.actions, a.queries, a.params, a.entry_point, a.cut)
           for a in before.actors]
    now = [(a.name, a.secondary, a.argument, a.actions, a.queries, a.params, a.entry_point, a.cut)
           for a in after.actors]
    k = next((n for n, a in enumerate(before.actors) if a.name == GIFT_PAIR_ACTOR and not a.secondary), None)
    if k is None:
        was.append((actor.name, '', '', [], [GIFT_PAIR_QUERY], actor.params, None, actor.cut))
    elif GIFT_PAIR_QUERY not in was[k][4]:
        was[k] = was[k][:4] + (was[k][4] + [GIFT_PAIR_QUERY],) + was[k][5:]
    if now != was:
        raise bad('actors differ from what was intended')
    if [p.name for p in after.entry_points] != [p.name for p in before.entry_points]:
        raise bad('entry points differ')
    for p, o in zip(after.entry_points, before.entry_points):
        calls = [name_of(before, i) for i in o.subflows]
        extra = [made[n][1] for n in calls if n in made]
        if to_q.get(name_of(before, o.main), name_of(before, o.main)) != name_of(after, p.main) \
                or [name_of(after, i) for i in p.subflows] != calls + extra:
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
                                   | {'kokiri_shop_full_stock', 'kokiri_circle_after_dungeons'}),
                    help='a game fix (see FIXES, FILE_FIXES, TABLE_FIXES)')
    ap.add_argument('assign', nargs='*', help='CHECK_ID=ItemActorName')
    a = ap.parse_args(argv)
    if not a.assign and not a.fix:
        ap.error('nothing to do: give CHECK_ID=Item assignments and/or --fix')
    assignments = [tuple(x.split('=', 1)) for x in a.assign]
    never_given(assignments)
    # CHECK_ID=First>Second: a progressive pair (PROGRESSIVE_PAIRS). In a small chest: planned as First, the
    # chest made a checking chest further down. On a freestanding item, a rock or a bush: planned as First's
    # turning item (tools/turn_items.py; the rock's or bush's drop). On a gift with flow data: planned as First,
    # the question added further down (gift_pair_kind). On a scrub: planned as First, the question added in
    # the scrub's branch of the scrub flow (scrub_pair_kind). Nowhere else yet (pair_kind).
    steps = {}                                         # check id -> (first, second): chests
    turning = {}                                       # check id -> (first, second): turning items (TURN_KINDS)
    gift_pairs = {}                                    # check id -> (first, second): gifts (gift_pair_edit)
    scrub_pairs = {}                                   # check id -> (first, second): scrubs (scrub_flow_edit)
    world = World()
    # CHECK_ID=First>Second>Third: a three-level family (THREE_LEVEL_FAMILIES), small chests only: planned as
    # First, the chest made the family's own chest further down (tools/three_chest.py)
    triples = three_level_parse(world, assignments)    # check id -> (first, second, third)
    for family in sorted(set(triples.values())):
        n = sum(1 for f in triples.values() if f == family)
        if n != len(family):
            print('  note: %s is on %d checks, not %d: %s' % ('>'.join(family), n, len(family), (
                'the last level cannot be reached' if n < len(family) else 'the last level is given more than once')))
    for k, (cid, item) in enumerate(assignments):
        if '>' in item:
            pair = tuple(item.split('>'))
            if pair not in PROGRESSIVE_PAIRS:
                raise SystemExit('%s: %s is not a progressive pair the builder knows (%s)' % (cid, item, ', '.join(
                    '>'.join(x) for x in sorted(PROGRESSIVE_PAIRS))))
            if gift_pair_kind(world, cid):
                gift_pairs[cid] = pair             # planned as First; the question is added further down
                assignments[k] = (cid, pair[0])
            elif scrub_pair_kind(world, cid):
                scrub_pairs[cid] = pair            # planned as First; the question goes in the scrub's branch
                assignments[k] = (cid, pair[0])
            elif pair_kind(world, cid) == 'chest':
                steps[cid] = pair
                assignments[k] = (cid, pair[0])
            else:
                turning[cid] = pair
                assignments[k] = (cid, turn_items.turn_name(pair[0]))
    for cid, cid2, d in turn_spacing(world, turning):
        print('%-18s and %s: the same progressive family, %.1f m apart' % (cid, cid2, d))
    # a small seed bag or quiver placed alone means its weapon: the check shows and gives the slingshot / bow,
    # and the small bag comes with it (the user's rule: never the bag first)
    for k, (cid, item) in enumerate(assignments):
        if item in FAMILY_ALIASES:
            print('%-18s %s placed: gives %s with it instead (the weapon first)' % (cid, item, FAMILY_ALIASES[item]))
            assignments[k] = (cid, FAMILY_ALIASES[item])
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(a.romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    mod_romfs = os.path.join(a.out, a.name, 'romfs')
    if os.path.isdir(mod_romfs):
        # files of an earlier build would stay in the mod otherwise (only this build's output folder is removed)
        shutil.rmtree(mod_romfs)
        print('earlier build removed:', mod_romfs)
    out = Output(a.romfs, mod_romfs, dicts)

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

    def on_ground(item):
        if item.startswith(turn_items.PREFIX):
            return item                                # a turning item (a progressive pair): built further down
        kind = ground_items.kind_of(plain, item)
        if kind == 'ground':
            return item
        if kind in ('item', 'equipment'):
            return grounds.setdefault((item, 'ground'), ground_items.ground_name(item))
        raise SystemExit('%s: not something that can lie on the ground, and no ground version can be made' % item)

    def in_chest(item):
        if ground_items.kind_of(plain, item) == 'equipment':
            return grounds.setdefault((item, 'held'), ground_items.ground_name(item, 'held'))
        return item

    def gs_drop(item):
        if item == ground_items.TOKEN:
            return item                                # its own token
        if ground_items.kind_of(plain, item) in ('ground', 'item', 'equipment'):
            return grounds.setdefault((item, 'token'), ground_items.ground_name(item, 'token'))
        raise SystemExit('%s: not something a Gold Skulltula can drop (no version of it can be made from the '
                         'token)' % item)

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

    planned = plan(world, assignments, on_ground, in_chest, on_shelf, gs_drop)
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

    # progressive pairs: in chests (the chest itself chooses) and on freestanding items, rocks and bushes (a
    # turning item), as sorted out above (pair_kind); checked again on what was planned
    stepped = {cid for changes in planned.values() for cid, _, _, kind in changes.values() if kind == 'chest'}
    for cid in sorted(set(steps) - stepped):
        raise SystemExit('%s: a progressive pair (First>Second) can only be put in a chest, on a freestanding '
                         'item, or on a rock or a bush' % cid)
    for cid in sorted(set(triples) - stepped):
        raise SystemExit('%s: a three-level family (First>Second>Third) can only be put in a small chest' % cid)
    three_used = {}                                    # (family name, _NoBake twin) -> (second, third as held)
    for changes in planned.values():
        for cid, item, _, kind in changes.values():
            if (cid in turning) != item.startswith(turn_items.PREFIX) or (cid in turning and kind not in TURN_KINDS):
                raise SystemExit('%s: a turning item (%s) planned on a %s: only freestanding items, rocks and '
                                 'bushes yet' % (cid, item, kind))

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
        new, found, _ = patch_file(old, {h: v for h, v in changes.items()}, checking, three)
        for h, (cid, item, expected_old, kind) in changes.items():
            if found[h] != expected_old:
                print('  note: %s placement %s held %s (data says %s)' % (cid, h, found[h], expected_old))
            print('%-18s %s: %s -> %s' % (cid, path.split('/')[-1], found[h], item))
            if cid in turning:
                print('%-18s   a turning item%s: %s on the ground while Link has no %s, then %s'
                      % (cid, '' if kind == 'freestanding' else ' as the %s\'s drop' % kind, turning[cid][0],
                         turning[cid][0], turning[cid][1]))
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
                want['Dynamic'] = dyn
            if act != want:
                raise SystemExit('read-back: actor %s (%s) differs from what was intended' % (h, act['Gyaml']))
        out.write(path, src, old, new)

    # songs: the cutscene only hands over the item
    for path, (cid, item, song) in sorted(plan_songs(world, assignments).items()):
        src, old = out.read(path)
        ef = evfl.loads(old)
        said = song_skip(ef.flowchart, cid, item, song, get_plan([item])[1].get(item))
        out.write(path, src, old, flow_write_checked(ef))
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
    for path, events in sorted(plan_gifts(world, [(c, i) for c, i in assignments if c in gift_pairs]).items()):
        src, old = out.read(path)
        ef = evfl.loads(old)
        pairs = {ev: (cid, gift_pairs[cid]) for ev, (cid, _, _) in events.items()}
        template = gift_pair_template(evfl.loads(plain(GIFT_PAIR_FLOW)).flowchart)
        direct, _ = get_plan(sorted({x for _, pair in pairs.values() for x in pair}))
        said, made = gift_pair_edit(ef.flowchart, pairs, template, direct)
        new = flow_write_checked(ef)
        gift_pair_read_back(path, evfl.loads(old).flowchart, evfl.loads(new).flowchart, pairs, made, template)
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
        said, added = cutscene_gift_edit(ef.flowchart, cid, g, item, show, SCRUB_COMPANIONS.get(item, ()))
        new = flow_write_checked(ef)
        cutscene_gift_check(evfl.loads(old).flowchart, evfl.loads(new).flowchart, cid, g, item, show, added)
        out.write(path, src, old, new)
        for line in said:
            print(line, '(%s)' % path.split('/')[-1])

    # scrubs: their map setting, one branch each in the shared flow, the generic line
    scrubs = plan_scrubs(world, assignments)
    # a slingshot given anywhere may come without its seed bag: the scrubs' seed sales then refuse
    guard = any(item == 'Item_Range_SlingShot' for _, item in assignments)
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
        direct, sync = get_plan(sorted({i for _, i, _ in scrubs} | {p[1] for p in scrub_pairs.values()}))
        said = scrub_flow_edit(ef.flowchart, [(c, i, [(t, w) for _, _, t, w in rows]) for c, i, rows in scrubs],
                               direct, sync, scrub_pairs) if scrubs else []
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
            like = (ground_items.anim_param_path(tpl_name) if 'AnimationParam' in inner
                    else ground_items.pouch_param_path(tpl_name) if 'PouchContentParam' in inner
                    else ground_items.ap_path(tpl_name))
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
    for family in sorted(set(turning.values())):
        for level, item in enumerate(family):
            got, pack, new_inner, rows, loose = turn_items.build(
                family, level, plain, table_rows,
                lambda project: os.path.exists(os.path.join(a.romfs, 'Model', project + '.anim.bfres.zs')))
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
            print('turn   version %-22s for %s (%d bytes); its AI %s (%d nodes more than %s): %s'
                  % (name, item, len(pack), turn_items.ai_name(item), what['new'], turn_items.BASE_AI,
                     'once Link owns %s it drops %s and deletes itself'
                     % (item, turn_items.turn_name(family[level + 1])) if what['drops']
                     else 'once Link owns %s it deletes itself' % item))
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
