"""Shop versions of items: an actor that stands on a shop shelf and sells item X.

Found in the game's files:
- A shop shelf item is its own actor, `Shop_<x>` (parent `Shop_Item_Base`): the item's model, animation, name
  and item settings (`PouchContentParam`), plus the shop parts (`Shop_Item_Base`: talk / buy logic, shelf
  physics) and a price: `GameParameterTable` -> `PriceParam` {BuyingPrice, SellingPrice}. Its table rows:
  `ActorInfo` with the item's model and name, `GameActorInfo` (small object), `PouchActorInfo` (the item row
  with BuyingPrice / SellingPrice).
- `Shop_Weapon_Shield_Deku` (Kokiri Shop, 40 rupees) is the shelf version of a single item that keeps the item's
  own name (`ActorName: Weapon_Shield_Deku`): the template here. Its price table also names shield-only
  settings; the new price table is built like the Deku Nut shelf's (`Shop_DekuNutBundle_01`: the shop base's
  table with its own price).
- Where a shelf is placed, the map names the actor (`Gyaml`) and its shelf number (`ShopItemIndex`); the shelf
  is changed by changing the actor, the shelf number stays.
- Shelf items come back after they are bought (`ActorGameDataSetting: AlwaysRespawn`). The game also has
  `NoRespawn` (used by the silver rupee tokens): `once=True` uses it. In game (2026-11-17) the shelf emptied
  when bought but was back after the area was reloaded: a `NoRespawn` object is remembered through the saved
  flag of its map placement (`GameData/GameDataList`, `Bool64bitKey`), and the placements of `AlwaysRespawn`
  shelves have none. The builder gives a changed shelf's placement the flag of a shop board it removes
  (`tools/build_mod.py`, `GAME_DATA`).
- With that flag the bought shelves were still back after a reload (in game, 2026-11-17), because nothing ever
  sets it. How a sold shelf works in the game's files:
  - "Sold" is the shopkeeper's count for this visit only: the shop talk (`DisplayShop`) adds one to the sold
    number (`EventTriggerAddShopItemSoldNum`) and the shopkeeper compares it with the list's `StockNum`. A
    list entry can also name a flag that makes it sold out (`Release`: `IsCheckSoldOutGameData`,
    `SoldOutGameData`; the blue fire shelf `IsGet.Item_Bottle_BlueFire`, the Market's first bomb shelf
    `Get_StoneOfFire_IsCompleted_Exp`), but that takes a named flag (a plain one, or a formula over named
    ones, `BoolExp`), and a placement's flag has no name.
  - The shelf actor never dies when it is bought. Its AI (`Shop_Item_Base.root`) asks the shopkeeper
    (`QueryShopItemIsSoldOut`, through the `ForSale` link and its `ShopItemIndex`) and only hides its model
    (`OneShotGameModelControllerSetVisible`), and tells a linked "sold out" board
    (`OneShotShopItemSendSoldOutMessage`; `Shop_Board_SoldOut`, linked from the stock-of-one shelves).
  - A placement's flag is set when the actor dies of a reason marked `IsSetRespawnFlagToFalse` (picked up,
    life depleted...: `System/CombinationDataTableData/*DeathReasonProcedures`), or by the AI node
    `OneShotActorChangeIsRespawn` (Bool false): what an item taken through an event does before it deletes
    itself (`PouchContent.event.root`, next to `OneShotPouchContentPushToPouchOwnInEvent`), and red ice, spider
    webs and falling floors in their own AI. A `NoRespawn` placement whose flag is set is not made again.
  - A shop can run with a shelf missing: the Market potion shop's bug shelf is only placed once
    `Market_Item_Bottle_TutorialEvent_Shop_Bottle_Insect_Appeared` is set, the shopkeeper always.
  So a shop version sold once gets an AI of its own (`Shop_NX2_Once.root`, `sold_for_good_ai`): the shelf's AI
  with one addition: where it hides its model because the shopkeeper says "sold out", it also runs
  `OneShotActorChangeIsRespawn` (false). After a reload the shelf is not placed: an empty shelf (to test).
  That the shopkeeper refused to sell the Giant's Knife and the Hover Boots again is most likely the game's
  buy check (Link already has them), not a memory of the sale.
- In game (2026-11-17) a sold shop version stayed away after a reload, but in the same visit its model was
  back on the shelf (not buyable). Found in the files:
  - The shelf AI has no memory: its one selector on `QueryShopItemIsSoldOut` hides the model on "sold out"
    and shows it again (`OneShotGameModelControllerSetVisible` true) whenever the answer is "not sold out";
    it is asked again in every state (idle, after every message of the shop talk).
  - The sold count is not kept for good: it is saved game data, `Shop_SoldNum.<shopkeeper>.<shelf number>`
    (the shopkeeper's `EventTriggerAddShopItemSoldNum` and `EventQueryCheckIsSoldOutSelectItem`, in
    `NpcCommon.event.root`), with a reset type of its own (2) that only one other value has, a schedule flag
    for the Sun's Song (`GraveYard_Hylia_030_AISchedule_For_SongOfSun`): the shops restock, most likely when
    the time of day changes. Once the count is back at 0 the shelf shows its model again; the flag the shop
    version set only matters when the area is loaded.
  - A model is shown from the start without any AI saying so (the Piece of Heart's AI has no such node).
  So in the shop versions' AI the "not sold out" side of that selector does nothing (the file's own
  `OneshotDoNothing`; the "sold out" board's AI has the same selector side) instead of showing the model:
  once hidden as sold, nothing in its AI shows it on the shelf again. The held-up model of the buy scene is
  shown by another node (the "get demo start" message), before the sale is counted.
- Shelves of single items name the item that goes into the pouch in their item settings (`PouchActor`: the
  Deku Shield shelf `Weapon_Shield_Deku`, the Bombchu shelves `Item_Bombchu`). A shop version has item
  settings of its own doing the same: the item's settings as parent, `PouchActor` the item.

- A shelf Link already has the item of says "Sold out" and shows no model (in game 2026-11-27: with a Bomb
  Bag from a chest, the Bomb Bag's shelf; nothing in the files says so: the shopkeeper's list had stock, and
  no flag). What a shop knows a shelf's item by is the `ActorName` of its `ActorInfo` row (the mask shelves:
  `Armor_Child_Mask_Keaton`, while their item settings name `Item_Mask_Keaton`): that name goes into
  `Shop_SelectItemName`, and it is the name the shelf's label shows. The game also has shelves named
  themselves (`Shop_DekuNutBundle_01`: row and name file its own, texts under its own name) and shelves that
  put nothing in the inventory (`Shop_Heart`: `PouchSpecialDeal: NotPushToPouch`).
  So the shelf of an upgrade family (`family=True`; tools/build_mod.py: shop_family_edit) is a shelf Link can
  never have: named itself (row, name file; its `_Name` text is the first level's, added by the builder),
  "not put in the inventory" in its item settings and its row, the row without what the item does when it
  is got. What Link gets is added by the sale flow.

A shop version of item X is built from the game's own files only: the shield shelf's pack without its item
and price files, X's model, animation and item settings (with the files they inherit from, when X's pack has
them), the shop base's price files, and two small files of its own (price table and price). The name is
`Shop_NX2_<X without "Item_">_<price>` (`_Once` added for once=True).

The text shown when Link looks at the item uses the item's own name; the shop description
(`<name>_ShopCaption` in the messages) exists only for items the game sells, so other items may show none.
"""
import copy
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml, ainb  # noqa: E402
import item_pose  # noqa: E402
from ground_items import (pack_path, ap_path, table_path, TABLES, _ref_path, pouch_param_path,  # noqa: E402,F401
                          resolved_components)

TEMPLATE = 'Shop_Weapon_Shield_Deku'
PRICE_TEMPLATE = 'Shop_DekuNutBundle_01'      # its price table: the shop base's, with its own price
PREFIX = 'Shop_NX2_'
ITEM_REFS = ('ActorNameRef', 'AnimationRef', 'ModelInfoRef', 'PouchContentRef')
ROW_FROM_ITEM = ('ActorName', 'FmdbName', 'ModelAabbMax', 'ModelAabbMin', 'ModelProjectName')
# items the game never sells have no pose made for a shelf: their one pose (Pose_Common, tools/item_pose.py) is
# centred on the point they are placed at, where the game's shelf items stand on it (lowest point of the model
# -0.03 .. +0.03 above the shelf point, measured on the vertices of everything the game sells).
# SHELF_LIFT: how much higher the shelf is placed in the map (metres). The Hookshot stood on end, half inside the
# shelf (2026-11-17); 0.3 tested: right, a touch high; with 0.25 its lowest vertex is 0.000 above the shelf point.
# The Hover Boots' pose is centred too (lowest vertex 0.190 under the point, default size 0.44 x 0.40 x 0.43 m):
# lifted the same way. (Their pose sets 18 bones, legs and wings; no game project with a shelf pose has them, so
# they get no pose of their own, SHELF_POSE.)
# A dungeon's boss key, compass and map (phase 1, part 12; in game 2026-11-25 the boss key and the compass sat in
# the shelf): their poses are centred too, lowest vertex 0.220, 0.134 and 0.201 under the point (measured as
# the Hookshot's: item_pose.extent on the model's vertices in Pose_Common). The small key stands on its point
# (lowest vertex +0.008) and is not lifted. The names are the game's items; a version of ours is lifted as the
# item it is made of (tools/build_mod.py: on_shelf).
# The Silver and the Golden Scale (phase 2, part 1; in game 2026-11-26 the Silver Scale sat in its shelf): centred
# poses, lowest vertex 0.192 and 0.203 under the point.
# The Bomb Bag, the Fairy Bow and the Fairy Slingshot (phase 2, part 3; measured the same way before their first
# test on a shelf): centred poses, lowest vertex 0.193, 0.416 and 0.182 under the point. (The Fairy Bow stands
# 0.91 m tall and 0.63 m wide then; the shop's two rows are 0.64 m apart, so on a lower shelf it reaches the
# shelf above.)
SHELF_LIFT = {'Item_Hookshot': 0.25, 'Item_HoverBoot': 0.19,
              'Item_Dungeon_BossKey': 0.22, 'Item_Dungeon_Compass': 0.13, 'Item_Dungeon_Map': 0.20,
              'Item_Scale_Silver': 0.19, 'Item_Scale_Gold': 0.20,
              'Item_BombBag_Small': 0.19, 'Item_Range_Bow': 0.42, 'Item_Range_SlingShot': 0.18}
# SHELF_POSE: items that get a shelf pose (Pose_Shop) of their own, as the game's own shelf items have (bomb, Deku
# Stick, arrows, Hylian Shield: their Pose_Common times one number): how many times its Pose_Common the item is on
# the shelf. The Giant's Knife's pose lays it nearly flat, 1.53 m wide (0.50 m tall, 0.56 m deep), centred on the
# shelf point: half inside the shelf and across its neighbours (shelves are 0.65 m apart, items 0.5 m apart).
# The shop version's animation project is a copy of SHELF_BASE (a game project with exactly Pose_Common,
# Pose_GetDemo and Pose_Shop for the bones Root and Skl_Root, what the knife's model has) under a name of the same
# length (shelf_project): Pose_Common and Pose_GetDemo are the item's own Pose_Common (held up, looked at in the
# menu: as in the game), Pose_Shop is that pose times the number, lifted so that the model's lowest vertex is
# SHELF_GAP above the shelf point. The turn stays the game's.
SHELF_POSE = {'Item_Sword_Giant': 0.8}       # 0.37 (2026-11-18, in game): much too small
SHELF_GAP = 0.0
# HELD_LOWER: how much lower than the item's own pose the shop version is held up (Pose_GetDemo; metres; size and
# turn stay the game's). Empty: held up, every item is exactly as in the game. Tried in game (2026-11-18): the
# Giant's Knife 0.11 lower; the user preferred the game's own height.
HELD_LOWER = {}
SHELF_BASE = 'Item_DekuSeed_Animation'
COMMON_ANIM = 'Item_Common_Animation'
NO_RESPAWN = '?Component/ActorGameDataSetting/NoRespawn.game__component__ActorGameDataSetting.bgyml'
# a family's shelf (family=True): a shelf Link can never have
NAME_REF = '?ActorSystem/ActorName/%s.engine__actor__ActorName.bgyml'    # an actor file's ActorNameRef
NOT_PUSHED_SHELF = 'Shop_Heart'                    # a shelf of the game that puts nothing in the inventory
NOT_PUSHED = 'NotPushToPouch'                      # PouchSpecialDeal (PouchActorInfo)
# what a family shelf's row keeps of the item's row: where it is listed and how it is got, nothing it does
FAMILY_ROW = ('__RowId', 'BundleActorNum', 'BuyingPrice', 'SellingPrice', 'IsAutoSaveAfterGet', 'PouchCategory',
              'PouchGetType', 'PouchSpecialDeal', 'PouchTabCategory')
# sold once, for good: the AI of the shop versions (the shelf's own with one addition, sold_for_good_ai)
BASE_AI = 'Shop_Item_Base'                    # the AI of every shelf
ONCE_AI = 'Shop_NX2_Once'
AI_PACK = 'Pack/AI.Global.Product.111.pack'
PICKUP_AI = 'AI/PouchContent.event.root.ainb'   # an item taken through an event: where the node is copied from
SOLD_QUERY = 'QueryShopItemIsSoldOut'
SHOW_NODE = 'OneShotGameModelControllerSetVisible'
GONE_NODE = 'OneShotActorChangeIsRespawn'
IDLE_NODE = 'OneshotDoNothing'                # what the "not sold out" side leads to in the shop versions
BOOL_SELECTOR, SIMULTANEOUS = 7, 3            # node types (formats/ainb.py NODE_TYPES)
FLOW = 2                                      # link type: flow to child nodes


def shop_name(item, price, once=False, family=False):
    base = item[5:] if item.startswith('Item_') else item
    return '%s%s_%d%s' % (PREFIX, base, price, '_Family' if family else '_Once' if once else '')


def not_pushed_value(read_pack):
    """the item settings' SpecialDeal value "not put in the inventory", read from the game's own heart shelf"""
    files = sarc.Sarc.read(read_pack(pack_path(NOT_PUSHED_SHELF))).files
    comp = resolved_components(files, NOT_PUSHED_SHELF)
    root = byml.loads(files[_ref_path(comp['PouchContentRef'])]).root
    if 'SpecialDeal' not in root:
        raise SystemExit('%s: its item settings name no SpecialDeal as expected' % NOT_PUSHED_SHELF)
    return root['SpecialDeal']


def gpt_path(actor):
    return 'GameParameter/GameParameterTable/%s.engine__actor__GameParameterTable.bgyml' % actor


def price_path(actor):
    return 'GameParameter/PriceParam/%s.game__pouchcontent__PriceParam.bgyml' % actor


def ai_path(name):
    return 'AI/%s.root.ainb' % name


def ai_info_path(name):
    return 'AI/AIInfo/%s.engine__actor__AIInfo.bgyml' % name


def _node_state(n):
    """everything a node holds, to compare two nodes"""
    return (n.type, n.name, n.flags, n.name_hash, bytes(n.guid), n.exb_count, n.exb_size, list(n.attachments),
            list(n.preconditions),
            [[sorted(vars(p).items()) for p in getattr(n, kind)[t]]
             for kind in ('immediates', 'inputs', 'outputs') for t in ainb.PARAM_TYPES],
            [[(l.node, l.name, tuple(l.extra)) for l in links] for links in n.links])


def _doc_state(doc):
    """everything an AI file holds around its nodes"""
    return ([(c.name, bytes(c.guid), c.left, c.right) for c in doc.commands],
            {t: [sorted(vars(g).items()) for g in doc.globals[t]] for t in ainb.GLOBAL_TYPES},
            list(doc.global_files), len(doc.attachments), list(doc.resident), bytes(doc.exb), list(doc.modules),
            list(doc.entry_strings), tuple(doc.hashes), tuple(doc.replace_head), list(doc.replacements),
            doc.output_count, doc.category, doc.category_id, doc.version)


def sold_for_good_ai(base, pickup, name=ONCE_AI):
    """the shelf AI (`base`: Shop_Item_Base.root) under the name `name`, with two changes: where the shelf hides
    its model because the shopkeeper answers "sold out", it also marks its placement as not to be made again;
    and where it showed its model because the answer is "not sold out", it does nothing.

    Found in the shelf AI: one selector on QueryShopItemIsSoldOut (asked of the shopkeeper through the ForSale
    link, with the shelf's ShopItemIndex) leads to OneShotGameModelControllerSetVisible false (sold out) or
    true; every state of the shelf goes through it (on entering, while idle, after each message of the shop
    talk). The addition: its "sold out" side becomes "both at once" (Element_Simultaneous, a copy of one of
    the file's own) of the same hide node and OneShotActorChangeIsRespawn with Bool false, copied from the AI of
    an item taken through an event (`pickup`: PouchContent.event.root, where it runs next to the node that puts
    the item in the pouch). Both new nodes are added after the file's own, so no node number changes.
    The second change (in game 2026-11-17: a sold shelf's model was back in the same visit): the selector's
    "not sold out" side led to OneShotGameModelControllerSetVisible true, which showed a sold shelf again as
    soon as the shopkeeper's sold count was reset (saved game data that the game resets, see the top of this
    file). It now leads to the file's own OneshotDoNothing (one link changed, no node added): the model is
    shown from the start anyway, and the model held up in the buy scene is shown by another node (the "get
    demo start" message, checked here: it doesn't go through the selector).
    Read back: every node of the shelf AI is as it was but for the selector's two links."""
    doc = ainb.loads(base)
    if doc.filename != BASE_AI + '.root':
        raise SystemExit('%s: not the shelf AI expected (%s)' % (ai_path(BASE_AI), doc.filename))
    n0 = len(doc.nodes)

    def shows(i, visible):
        n = doc.nodes[i]
        return n.name == SHOW_NODE and [(x.name, x.value, x.node) for x in n.inputs['bool']] == [
            ('IsVisible', visible, -1)]

    hits = []
    for i, n in enumerate(doc.nodes):
        if n.type != BOOL_SELECTOR:
            continue
        inp = n.inputs['bool']
        if len(inp) != 1 or inp[0].node < 0 or doc.nodes[inp[0].node].name != SOLD_QUERY:
            continue
        flow = {l.name: l for l in n.links[FLOW]}
        if set(flow) != {'True', 'False'} or len(n.links[FLOW]) != 2 \
                or not shows(flow['True'].node, False) or not shows(flow['False'].node, True):
            raise SystemExit('%s: the "sold out" selector (node %d) is not as expected' % (ai_path(BASE_AI), i))
        hits.append((i, flow['True'], flow['False']))
    if len(hits) != 1:
        raise SystemExit('%s: %d "sold out" selectors, expected 1' % (ai_path(BASE_AI), len(hits)))
    sel, link, show_link = hits[0]
    hide, show = link.node, show_link.node

    # "not sold out" leads to a node that does nothing: the file's own, plain (no values but its own switch,
    # no links). The shown state never depended on that side alone: the "get demo start" message shows the
    # held-up model through a node of its own, which must not be the one given up here.
    idle = [i for i, n in enumerate(doc.nodes) if n.name == IDLE_NODE and not n.preconditions
            and not n.attachments and not any(n.links)
            and not any(n.inputs[t] or n.outputs[t] for t in ainb.PARAM_TYPES)
            and [(t, x.name, x.value) for t in ainb.PARAM_TYPES for x in n.immediates[t]]
            == [('bool', 'ExecuteEveryFrame', False)]]
    if len(idle) != 1:
        raise SystemExit('%s: %d plain %s nodes, expected 1' % (ai_path(BASE_AI), len(idle), IDLE_NODE))
    idle = idle[0]
    users = [i for i, n in enumerate(doc.nodes) for l in n.links[FLOW] if l.node == show]
    if users != [sel]:
        raise SystemExit('%s: the "show the model" node %d of the "sold out" selector is also used elsewhere'
                         % (ai_path(BASE_AI), show))
    others = [l.node for n in doc.nodes for l in n.links[FLOW] if l.node != show and shows(l.node, True)]
    if len(set(others)) != 1:
        raise SystemExit('%s: %d other "show the model" nodes, expected 1 (the held-up model of the buy scene)'
                         % (ai_path(BASE_AI), len(set(others))))

    both = next((n for n in doc.nodes if n.type == SIMULTANEOUS and n.flags == 0 and not n.preconditions
                 and not n.attachments and not any(n.inputs[t] or n.outputs[t] for t in ainb.PARAM_TYPES)
                 and all(l.name == '' and not l.extra for l in n.links[FLOW])
                 and not any(links for t, links in enumerate(n.links) if t != FLOW)), None)
    if both is None:
        raise SystemExit('%s: no plain Element_Simultaneous to copy' % ai_path(BASE_AI))
    gone = [n for n in ainb.loads(pickup).nodes if n.name == GONE_NODE]
    if not gone or any([(x.name, x.value, x.node) for x in n.inputs['bool']] != [('Bool', False, -1)]
                       or n.preconditions or n.attachments or any(n.links)
                       or any(n.outputs[t] for t in ainb.PARAM_TYPES)
                       or any(n.inputs[t] for t in ainb.PARAM_TYPES if t != 'bool') for n in gone):
        raise SystemExit('%s: %s not found as expected' % (PICKUP_AI, GONE_NODE))

    def new_node(template, what):
        n = copy.deepcopy(template)
        n.guid = hashlib.md5(('NX2-ZOOTR %s %s' % (name, what)).encode()).digest()
        n.precondition_slot = None
        if any(bytes(x.guid) == n.guid for x in doc.nodes):
            raise SystemExit('%s: node id already used' % name)
        return n

    mark = new_node(gone[0], 'gone')
    wrap = new_node(both, 'both')
    wrap.links[FLOW] = [ainb.Link(hide, ''), ainb.Link(n0 + 1, '')]
    doc.nodes += [wrap, mark]
    link.node = n0
    show_link.node = idle
    doc.filename = name + '.root'
    new = doc.write()

    back, orig = ainb.loads(new), ainb.loads(base)
    if back.write() != new or back.filename != name + '.root' or len(back.nodes) != n0 + 2 \
            or _doc_state(back) != _doc_state(orig):
        raise SystemExit('read-back: %s differs from what was intended' % ai_path(name))
    for i, (o, b) in enumerate(zip(orig.nodes, back.nodes)):
        if i == sel:
            for l in o.links[FLOW]:
                if l.name == 'True':
                    l.node = n0
                elif l.name == 'False':
                    l.node = idle
        if _node_state(o) != _node_state(b):
            raise SystemExit('read-back: node %d of %s differs from what was intended' % (i, ai_path(name)))
    b_wrap, b_mark = back.nodes[n0], back.nodes[n0 + 1]
    if _node_state(b_mark) != _node_state(mark) or _node_state(b_wrap) != _node_state(wrap) \
            or [(l.node, l.name) for l in b_wrap.links[FLOW]] != [(hide, ''), (n0 + 1, '')] \
            or b_mark.name != GONE_NODE or [(x.name, x.value) for x in b_mark.inputs['bool']] != [('Bool', False)]:
        raise SystemExit('read-back: the new nodes of %s differ from what was intended' % ai_path(name))
    b_flow = {l.name: l.node for l in back.nodes[sel].links[FLOW]}
    if b_flow != {'True': n0, 'False': idle} or back.nodes[idle].name != IDLE_NODE             or any(l.node == show for n in back.nodes for l in n.links[FLOW]):
        raise SystemExit('read-back: the "sold out" selector of %s differs from what was intended' % ai_path(name))
    return new


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


def price_of(read_table_rows, shop_actor):
    """the price of a game shelf actor (its PouchActorInfo row)"""
    rows = {r['__RowId']: r for r in read_table_rows('PouchActorInfo')}
    if shop_actor not in rows or 'BuyingPrice' not in rows[shop_actor]:
        raise SystemExit('%s: no price in PouchActorInfo' % shop_actor)
    return int(rows[shop_actor]['BuyingPrice'])


# Items a shelf can't sell (for now): bottles. Every bottle item (empty, potions, fish, Ruto's letter...) has
# the "Bottle" special deal; the game's buy code refuses them on a shelf: tested 2026-11-17 with the Empty
# Bottle three ways (special deal removed, PouchActor removed, bottle button slot removed), each time the
# shopkeeper takes it back. The game never sells a bottle: its bottle shelves (Shop_Bottle_*, special deal
# NotPushToPouch) pour their contents into a bottle Link already owns.
# A flow branch that sells the bottle itself works (no price question, no held-up get; tested 2026-11-17,
# see CHANGELOG and example_shop_bottle on the event flow tool branch). Not used until bottles in shops are decided.
REFUSED_SPECIAL_DEALS = ('Bottle',)


def refusal(item, read_table_rows):
    """why `item` can't be sold on a shelf, or None"""
    for r in read_table_rows('PouchActorInfo'):
        if r['__RowId'] == item and r.get('PouchSpecialDeal') in REFUSED_SPECIAL_DEALS:
            return ("a bottle (special deal %s): the game's buy code refuses bottles on a shelf (tested "
                    '2026-11-17); put it in a chest, a pot, on the ground or with an NPC instead'
                    % r['PouchSpecialDeal'])
    return None


def can_sell(read_pack, item):
    try:
        files = sarc.Sarc.read(read_pack(pack_path(item))).files
    except FileNotFoundError:
        return False
    if ap_path(item) not in files:
        return False
    c = byml.loads(files[ap_path(item)]).root.get('Components', {})
    return all(r in c for r in ('ActorNameRef', 'ModelInfoRef', 'PouchContentRef'))


def shelf_project(item):
    """the name of the animation project of an item's shop version (SHELF_POSE): as long as SHELF_BASE"""
    name = ('NX2S_' + item.split('_', 1)[1]).ljust(len(SHELF_BASE), '_')
    if len(name) != len(SHELF_BASE):
        raise SystemExit('%s: no animation project name of %d letters' % (item, len(SHELF_BASE)))
    return name


def shelf_pose(item, project, row, read_pack):
    """the animation project of the shop version of `item` (SHELF_POSE; `project`: the item's own, `row`: its
    ActorInfo row). Returns (data, {'common': the item's pose, 'shop': the shelf pose, 'held': the held-up pose
    (HELD_LOWER), each (scale, rot, move); 'lo', 'hi': the model's lowest and highest x, y, z on the shelf;
    'held_lo', 'held_hi': the same held up, from the point it is held at})."""
    anim = read_pack(item_pose.model_path(project))
    own = item_pose.read_pose(anim)
    if len(set(own['scale'])) != 1:
        raise SystemExit('%s: its pose has a scale per axis' % item)
    points, bind, _ = item_pose.model_points(read_pack('Model/%s.%s.bfres' % (row['ModelProjectName'],
                                                                              row['FmdbName'])))
    k = SHELF_POSE[item]
    scale = own['scale'][0] * k
    flat = (own['move'][0] * k, 0.0, own['move'][2] * k)
    lo, _ = item_pose.extent(points, bind, (scale,) * 3, own['rot'], flat)
    move = (flat[0], SHELF_GAP - lo[1], flat[2])
    data = item_pose.shelf_copy(read_pack(item_pose.model_path(SHELF_BASE)), SHELF_BASE, shelf_project(item), anim,
                                (scale, own['rot'], move), HELD_LOWER.get(item, 0.0))
    back = item_pose.read_pose(data, item_pose.SHELF_POSES[2])
    lo, hi = item_pose.extent(points, bind, back['scale'], back['rot'], back['move'])
    if abs(lo[1] - SHELF_GAP) > 1e-4:
        raise SystemExit('read-back: %s does not stand %.2f above the shelf point' % (item, SHELF_GAP))
    held = item_pose.read_pose(data, item_pose.SHELF_POSES[1])
    held_lo, held_hi = item_pose.extent(points, bind, held['scale'], held['rot'], held['move'])
    own_lo, _ = item_pose.extent(points, bind, own['scale'], own['rot'], own['move'])
    if abs(own_lo[1] - held_lo[1] - HELD_LOWER.get(item, 0.0)) > 1e-4:
        raise SystemExit('read-back: %s is not held up %.2f lower' % (item, HELD_LOWER.get(item, 0.0)))
    return data, {'common': (own['scale'][0], own['rot'], own['move']), 'shop': (scale, own['rot'], move),
                  'held': (held['scale'][0], held['rot'], held['move']), 'lo': lo, 'hi': hi,
                  'held_lo': held_lo, 'held_hi': held_hi}


def build(item, price, read_pack, read_table_rows, once=False, family=False):
    """the shop version of `item` at `price` rupees. family: the shelf of an upgrade family whose first level is
    `item`: sold once, named itself, never in the inventory (the sale flow adds the level Link gets).
    Returns (name, pack data, {inner path: (data, similar game file)} for files new to the game, {table: row},
    {loose file new to the game: (data, the game file it is a copy of, what shelf_pose says about it)}: the
    animation project of an item with a shelf pose of its own, SHELF_POSE)."""
    once = once or family
    name = shop_name(item, price, once, family)
    tpl = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))
    base = sarc.Sarc.read(read_pack(pack_path(PRICE_TEMPLATE)))
    itm = sarc.Sarc.read(read_pack(pack_path(item)))
    tpl_ap = byml.loads(tpl.files[ap_path(TEMPLATE)])
    tc = tpl_ap.root['Components']
    ic = byml.loads(itm.files[ap_path(item)]).root['Components']
    if not can_sell(read_pack, item):
        raise SystemExit('%s: no name, model or item settings of its own: cannot be put on a shelf' % item)

    # the shield shelf without its item and price files (files the kept parts also use stay)
    out_refs = ITEM_REFS + ('GameParameterTableRef',)
    drop = set()
    for r in out_refs:
        if r in tc:
            drop |= _reach(tpl.files, _ref_path(tc[r]))
    keep = {ap_path(TEMPLATE)}
    for r, v in tc.items():
        if r not in out_refs and isinstance(v, str) and v.startswith('?'):
            keep |= _reach(tpl.files, _ref_path(v))
    keep |= _reach(tpl.files, 'Actor/Shop_Item_Base.engine__actor__ActorParam.bgyml')
    files = {p: d for p, d in tpl.files.items() if p not in drop or p in keep}
    del files[ap_path(TEMPLATE)]

    # the item's own files
    for r in ITEM_REFS:
        if r in ic and not _ref_path(ic[r]).startswith('ActorSystem/'):
            got = _reach(itm.files, _ref_path(ic[r]))
            if _ref_path(ic[r]) not in got:
                raise SystemExit('%s: %s (%s) not in its pack' % (item, r, ic[r]))
            for p in got:
                files[p] = itm.files[p]

    # price: the Deku Nut shelf's price table (shop base table + own price), with this name and price
    bgpt_path = _ref_path(byml.loads(base.files[ap_path(PRICE_TEMPLATE)]).root['Components']['GameParameterTableRef'])
    for p in _reach(base.files, bgpt_path) - {bgpt_path, price_path(PRICE_TEMPLATE)}:
        files[p] = base.files[p]
    pdoc = byml.loads(base.files[price_path(PRICE_TEMPLATE)])
    pdoc.root = type(pdoc.root)(pdoc.root)
    pdoc.root['BuyingPrice'] = type(pdoc.root['BuyingPrice'])(price)
    gdoc = byml.loads(base.files[bgpt_path])
    gdoc.root = type(gdoc.root)(gdoc.root)
    gcomp = type(gdoc.root['Components'])(gdoc.root['Components'])
    if gcomp.get('PriceParam') != '?' + price_path(PRICE_TEMPLATE):
        raise SystemExit('price template not as expected')
    gcomp['PriceParam'] = '?' + price_path(name)
    gdoc.root['Components'] = gcomp
    new_inner = {price_path(name): (byml.dumps(pdoc), price_path(PRICE_TEMPLATE)),
                 gpt_path(name): (byml.dumps(gdoc), bgpt_path)}

    comp = type(tc)(tc)
    for r in ITEM_REFS:
        if r in ic:
            comp[r] = ic[r]
        else:
            comp.pop(r, None)
    comp['GameParameterTableRef'] = '?' + gpt_path(name)
    loose = {}
    if item in SHELF_POSE:
        # no pose made for a shelf: its animation project replaced by one with a shelf pose (SHELF_POSE)
        adoc = byml.loads(files[_ref_path(ic['AnimationRef'])])
        res = [dict(x) for x in adoc.root['AnimationResources']]
        own = [x['ModelProjectName'] for x in res if x['ModelProjectName'] != COMMON_ANIM]
        if len(own) != 1:
            raise SystemExit('%s: animation projects %r, expected %s and one of its own' % (item, res, COMMON_ANIM))
        row = {r['__RowId']: r for r in read_table_rows('ActorInfo')}[item]
        data, info = shelf_pose(item, own[0], row, read_pack)
        loose[item_pose.model_path(shelf_project(item))] = (data, item_pose.model_path(SHELF_BASE), info)
        adoc.root = type(adoc.root)(adoc.root)
        adoc.root['AnimationResources'] = [dict(x, ModelProjectName=shelf_project(item))
                                           if x['ModelProjectName'] == own[0] else x for x in res]
        anim_path = 'Component/AnimationParam/%s.engine__component__AnimationParam.bgyml' % name
        new_inner[anim_path] = (byml.dumps(adoc), _ref_path(tc['AnimationRef']))
        comp['AnimationRef'] = '?' + anim_path
    # item settings of its own naming the item for the pouch, as the game's shelves of single items
    tpp = _ref_path(tc['PouchContentRef'])
    pdoc = byml.loads(tpl.files[tpp])
    pdoc.root = type(pdoc.root)()
    pdoc.root['$parent'] = 'Work/' + _ref_path(ic['PouchContentRef'])[:-len('.bgyml')] + '.gyml'
    if family:
        # never in the inventory, and named itself (the name file is not in a pack, as the game's own)
        pdoc.root['SpecialDeal'] = not_pushed_value(read_pack)
        comp['ActorNameRef'] = NAME_REF % name
    else:
        pdoc.root['PouchActor'] = 'Work/' + ap_path(item)[:-len('.bgyml')] + '.gyml'
    new_inner[pouch_param_path(name)] = (byml.dumps(pdoc), tpp)
    comp['PouchContentRef'] = '?' + pouch_param_path(name)
    if once:
        comp['ActorGameDataSetting'] = NO_RESPAWN
        # an AI of its own, which marks the placement as not to be made again once sold (sold_for_good_ai),
        # with the file that names it, as every actor with an AI of its own has in its pack
        base_info = ai_info_path(BASE_AI)
        if resolved_components(tpl.files, TEMPLATE).get('AIInfoRef') != '?' + base_info \
                or base_info not in tpl.files or ai_path(BASE_AI) not in tpl.files:
            raise SystemExit('%s: its AI is not %s as expected' % (TEMPLATE, BASE_AI))
        idoc = byml.loads(tpl.files[base_info])
        if dict(idoc.root) != {'RootAIRef': 'Work/AI/Root/%s.root.ain' % BASE_AI}:
            raise SystemExit('%s not as expected' % base_info)
        idoc.root = type(idoc.root)(idoc.root)
        idoc.root['RootAIRef'] = type(idoc.root['RootAIRef'])('Work/AI/Root/%s.root.ain' % ONCE_AI)
        pickup = sarc.Sarc.read(read_pack(AI_PACK)).files[PICKUP_AI]
        new_inner[ai_info_path(ONCE_AI)] = (byml.dumps(idoc), base_info)
        new_inner[ai_path(ONCE_AI)] = (sold_for_good_ai(tpl.files[ai_path(BASE_AI)], pickup), ai_path(BASE_AI))
        comp['AIInfoRef'] = '?' + ai_info_path(ONCE_AI)
    doc = byml.loads(tpl.files[ap_path(TEMPLATE)])
    doc.root = type(doc.root)(doc.root)
    doc.root['Components'] = comp
    new_inner[ap_path(name)] = (byml.dumps(doc), ap_path(TEMPLATE))
    for p, (d, _) in new_inner.items():
        files[p] = d

    # every file the actor points at is in the pack (apart from names and system settings, kept outside)
    missing = [p for p in _reach(files, ap_path(name)) if p not in files]
    for p in set(_refs(byml.loads(files[ap_path(name)]).root)):
        if p not in files and not p.startswith(('ActorSystem/', 'AS/', 'AI/', 'Component/ActorGameDataSetting/',
                                                 'Component/XLink/', 'Work/', 'Logic/')):
            missing.append(p)
    if missing:
        raise SystemExit('%s: files not in the pack: %s' % (name, ', '.join(sorted(missing))))

    out = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))
    out.files = files
    out.align = {p: (tpl.align.get(p) or itm.align.get(p) or base.align.get(p) or 8) for p in files}
    for p in (ai_path(ONCE_AI), ai_info_path(ONCE_AI)):          # placed in the pack as the files they come from
        if p in new_inner:
            out.align[p] = tpl.align.get(new_inner[p][1]) or 8
    pack = out.write()

    tables = {t: {r['__RowId']: r for r in read_table_rows(t)} for t in TABLES}
    if name in tables['ActorInfo']:
        raise SystemExit('%s already exists in the game' % name)
    ai_t, ai_i = tables['ActorInfo'][TEMPLATE], tables['ActorInfo'][item]
    ai = type(ai_t)(ai_t)
    for k in ROW_FROM_ITEM:
        if k in ai_i:
            ai[k] = ai_i[k]
        else:
            ai.pop(k, None)
    anim = byml.loads(files[_ref_path(comp['AnimationRef'])]).root.get('AnimationResources') \
        if 'AnimationRef' in comp else None
    if anim is not None:
        ai['AnimationResources'] = anim
    else:
        ai.pop('AnimationResources', None)
    # memory: the item's own needs on top of the shelf's, and margin
    ai['InstanceHeapSize'] = type(ai_t['InstanceHeapSize'])(
        int(ai_t['InstanceHeapSize']) + int(ai_i['InstanceHeapSize']) + 16384)
    ai['PreActorRenderInfoHeapSize'] = type(ai_t['PreActorRenderInfoHeapSize'])(
        max(int(ai_t['PreActorRenderInfoHeapSize']), int(ai_i.get('PreActorRenderInfoHeapSize', 0)) + 1024))
    ai['__RowId'] = name
    ga = type(tables['GameActorInfo'][TEMPLATE])(tables['GameActorInfo'][TEMPLATE])
    ga['__RowId'] = name
    if item not in tables['PouchActorInfo']:
        raise SystemExit('%s has no row in PouchActorInfo' % item)
    tp = tables['PouchActorInfo'][TEMPLATE]
    pa = type(tables['PouchActorInfo'][item])(tables['PouchActorInfo'][item])
    pa['BuyingPrice'] = type(tp['BuyingPrice'])(price)
    pa['SellingPrice'] = tp['SellingPrice']
    pa['__RowId'] = name
    if family:
        heart = tables['PouchActorInfo'][NOT_PUSHED_SHELF]
        if heart.get('PouchSpecialDeal') != NOT_PUSHED or 'PouchSpecialDeal' not in pa:
            raise SystemExit('%s: its row is not "%s" as expected' % (NOT_PUSHED_SHELF, NOT_PUSHED))
        pa['PouchSpecialDeal'] = type(heart['PouchSpecialDeal'])(NOT_PUSHED)
        for k in [k for k in pa if k not in FAMILY_ROW]:
            del pa[k]
        ai['ActorName'] = type(ai_t['ActorName'])(name)
    rows = {'ActorInfo': ai, 'GameActorInfo': ga, 'PouchActorInfo': pa}

    back = sarc.Sarc.read(pack)
    if set(back.files) != set(files) or any(back.files[p] != d for p, d in files.items()):
        raise SystemExit('read-back: pack of %s differs from what was intended' % name)
    if byml.loads(back.files[ap_path(name)]).root != dict(doc.root, Components=dict(comp)):
        raise SystemExit('read-back: actor parameters of %s differ' % name)
    if int(byml.loads(back.files[price_path(name)]).root['BuyingPrice']) != price:
        raise SystemExit('read-back: price of %s differs' % name)
    if once:
        got = resolved_components(back.files, name)
        if got.get('AIInfoRef') != '?' + ai_info_path(ONCE_AI) or got.get('ActorGameDataSetting') != NO_RESPAWN \
                or byml.loads(back.files[ai_info_path(ONCE_AI)]).root['RootAIRef'] \
                != 'Work/AI/Root/%s.root.ain' % ONCE_AI \
                or ainb.loads(back.files[ai_path(ONCE_AI)]).filename != ONCE_AI + '.root':
            raise SystemExit('read-back: the sold-once AI of %s differs' % name)
    if family:
        got = resolved_components(back.files, name)
        sroot = byml.loads(back.files[_ref_path(got['PouchContentRef'])]).root
        if got.get('ActorNameRef') != NAME_REF % name or 'PouchActor' in sroot \
                or sroot.get('SpecialDeal') != not_pushed_value(read_pack) or ai.get('ActorName') != name \
                or pa.get('PouchSpecialDeal') != NOT_PUSHED or set(pa) - set(FAMILY_ROW):
            raise SystemExit('read-back: the family shelf %s is not named itself and out of the inventory' % name)
    return name, pack, new_inner, rows, loose
