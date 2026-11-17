# Changelog

Newest first. Dates are when the work was done.

## 2026-11-17

### AINB: reader and writer for the game's AI and logic files (branch `claude/ainb-format-aa01ca`)
- **New `formats/ainb.py`**: reads an `.ainb` file (magic `AIB `, version 0x408) into Python objects and
  writes it back: commands (entry points), nodes with their fixed values, inputs, outputs, links,
  preconditions and attachments, global parameters with their defaults and file references, embedded
  module names, entry strings, the replacement table. Written from the game's own files: no public
  description of this version was reachable, and it differs from what I knew of the older 0x404/0x407
  (node bodies hold index+count pairs instead of offsets; 7 global parameter types instead of 6).
- **Round trip: 11,707/11,707 byte-identical** (1,942 loose files in `AI`, `Logic`, `Sequence`, 9,765
  inside packs; 5,036 different files). In `tests/roundtrip.py`; `run_tests.bat` now also covers the
  `AI`, `Logic` and `Sequence` folders.
- **Kept as they are, not decoded:** the expression block (EXB: small formulas some nodes use; 1,079 of
  the 5,036 files have one) is raw bytes; the string pool is kept as read and new strings go at the end;
  the extra words of links, parameter flags and the replacement table are numbers (the dump tool names
  the ones understood: selector conditions, "value comes from global parameter N / expression N").
  Not possible yet: adding or changing an expression. Adding nodes is possible in the object model but
  not tested in game.
- **Edit test** (`tests/edit_check.py`): changes a number (the pot respawn delay, 1200 -> 60 frames), a
  string (a flag name, new in the pool) and removes one source of an input with several; each result
  reads back with only those lines changed in the text dump, and writing it again gives the same bytes.
- **New `tools/ainb_dump.py`** (read only): prints an AINB as text, from a file or from a path in the
  romfs that may go through a pack; `--find <text>` lists where AINB files with that name are.
- Found on the way: the `AI`, `Logic` and `Sequence` folders hold 3 BYML node definition tables
  (`NodeDefinition/Node.Product.111.aidefn.byml`) that the BYML writer gives back smaller (not AINB;
  same kind as the 2 known BYML system files). Not fixed here.

What the three files do (analysis only, nothing changed in the builder; all from the dumps):

- **Rock circle** (`Logic/KokiriForest_Common_Level_All_01_6aaf.logic.module.ainb`, 38 nodes). Two sets
  of liftable rocks. The 8 (`Obj_LiftRock_A_01_4079`, `_4151`, `_6b1c`, `_79ff`, `_ab49`, `_b129`,
  `_e464`, `_f107`) are always created and are deleted when "adult AND the flag
  `SageOfForest_IsBefore_Step08`" is true. The 4 (`_1345`, `_39ec`, `_b2db`, `_f726`) are created only
  when that same condition is true. So: child = the 8; adult while `SageOfForest_IsBefore_Step08` = the 4;
  adult after = the 8 again. This matches what was seen in game, and names the exact flag (a step of the
  Forest Sage's story, not "Forest Temple completed" as such). When all 8 are broken it sets
  `KokiriForest_Npc_Kokiri_008_Child_LiftRock_AllBroken` to true (false otherwise). 8 trigger areas, one
  per rock of the 8, watch for the player: player inside one -> `Npc_Kokiri_008_Child_AttentionFlag`
  false, otherwise true; each area is deleted when its rock is lifted or broken, or when
  `Get_StoneOfForest_IsCompleted_Exp` (by its name: the Kokiri Emerald is obtained) is true. The middle rock is not in this
  module. To make the circle the same at every age, the one node to change is the "adult AND flag" node
  (or the flag name it reads).
- **Ground item pick-up** (`AI/PouchContent.event.root.ainb` in `Pack/AI.Global.Product.111.pack.zs`, 380
  nodes, 60 entry points). It is the list of things an event flow can ask of or tell an item actor
  (`EventQuery...`, `EventTrigger...`); each query answers with a number the event flow switches on.
  - `EventTriggerAddOwnToPouch` (the push to the pouch) runs two game-code nodes at once:
    `OneShotPouchContentPushToPouchOwnInEvent` and `OneShotActorChangeIsRespawn(false)` (the picked-up
    object will not come back). Nothing else: what the push does (equip, count, refresh the ocarina
    button) is inside the game's code, not in this file.
  - `SpecialDeal` is read by `QueryPouchContentGetSpecialDeal` in two entry points with the same graph:
    `EventQueryOwnIsMaxLifeUpPouchContent` and `EventQueryOwnIsNotPushPouchContent`. Both answer 0 ("yes")
    when SpecialDeal is 3 and 1 ("no") for anything else. So in this file SpecialDeal 3 means "heart
    container kind: don't put it in the pouch"; no other value is looked at here.
  - `EventQueryGetRequestedTargetProcess`: 0 put in the pouch, 1 equip, 2 heal (also the default).
    `EventQueryCanAddToPorchSelf` asks the pouch manager (`QueryPouchMgrIsEnablePushToPouch`, by actor
    name): 0 can be taken, 1 cannot. `EventTriggerReserveNotPushToPouchProcess` /
    `EventQueryIsNotPushToPouchInEvent`: an event can reserve "don't push this one".
    `EventQueryCheckOwnPouchContentCategory`: 0 weapon, 1 bow, 2 arrow, 3 shield, 4 armour, 5 material,
    6 important item, 7 rupee, 8 healing item, 9 head gear, 10 boots, 11 other.
    `EventQueryCheckTagOnPouchActor`: actor tags `LetterBottle` 0, `Obj_Fire_Arrow` 1, `BiggoronSword` 2,
    `Token_Gold` 3, other 4. `EventQueryIsAutoSavePouchContent`: save after the get scene or not.
  - For the Fairy Ocarina that can't be played until a reload: this file gives no handle on it (the push
    is one game-code node). The place to compare next is the event flow that calls these entry points
    for the Ocarina of Time in the moat against the one used for our ground ocarina.
- **Pots.** The pot's own AI (`AI/Obj_Pot.root.ainb`, in every pot, rock and grass pack, 40 nodes) only
  decides when it breaks: thrown or fallen and then touching something, thrown and hitting an actor
  (unless that actor has the tag `UnbreakHitPotAttack`), or damaged by a Wallmaster; each ends in
  `OneShotDeathRequestDeath`. Other ways of breaking (a sword hit) are not in this file. Nothing in it
  brings a pot back or remembers it. What brings a broken pot back is outside the AI:
  - ordinary pots (`Obj_Pot_A_01`...) use the actor setting `ActorGameDataSetting/SupplyObject` and the
    saved per-object flag found earlier (reset when the area reloads);
  - the `..._Respawn` pots use `ActorGameDataSetting/AlwaysRespawn` and a death procedure
    `Default_AlwaysRespawn`, and are driven by a logic module, e.g.
    `Logic/Obj_Pot_A_05_Respawn_Prefab_1c6c.logic.module.ainb` (16 nodes): the pot is re-created
    (`RespawnTrigger`) when all of these hold: the pot has been gone for 1200 frames, the player has a
    bomb bag but no bombs and no Bombchus, no bomb (`Obj_Bomb`) is in the object area and the player is
    not in the player area around it, it is not on camera, and a condition given by the map that uses
    the module is true. A supply pot that refills when you are out of bombs. (The module also writes an
    auto-generated saved flag when the pot dies and uses it to decide whether to create the pot.)
  So a one-time rule for pots is not an AI change: the lead is the `SupplyObject` game data setting
  (and the reset type of the flag), to look at with the BYML tools.

### Rock circle corrected (branch `rock-circle`)
- **Correction:** the circle by Mido's house has **8** rocks as a child, not 12 (earlier notes said 12).
  The map places 12 rock objects; the level logic shows 8 to a child, and to an adult 4 before the Forest
  Temple and the 8 others after (seen in game and in a 100% save). Assumed: the child's 8 are the same as
  the adult's 8 after the Forest Temple, so `KF_CIRCLE_CHILD_ROCK_03`, `_06`, `_09`, `_12` never appear: rule
  `False`, `randomizable: no`.
- **The middle rock** (`KF_CIRCLE_CENTER_ROCK`): in a 100% save the Kokiri lifting it is gone and it can be
  lifted. Rule now `is_child and 'Deku Tree Clear'` (assumed: the level logic checks the Kokiri Emerald flag;
  not tested at which point exactly).
- Not done (decided 2026-11-17): setting the Deku Tree or Forest Temple story flags at the start to change
  the rocks. They drive much more (the Deku Tree's death, Saria, Mido, the Forest Sage's story); the
  rocks' conditions are in the logic instead. Changing the circle's own logic module would need our own AI
  file editor.
- Two logic tests added (`tests/logic_check.py`).
- Why those 4: in the map, the level logic's group of 8 lies in a ring 2-2.7 m around the middle rock (as in
  a child screenshot), the group of 4 at the diagonals (as in the adult one), each ~0.3 m from one of the 8.
  To confirm in game (test mod): the 8 child rocks of the ring drop a red rupee, the 4 others a gold rupee.
- **Confirmed in game:** all 8 rocks a child sees gave red rupees, so the child's 8 are the ring and
  `KF_CIRCLE_CHILD_ROCK_03`, `_06`, `_09`, `_12` are rightly marked as never there.
- **Seen in game (unmodded, a 100% save):** as an adult after the Forest Temple, the circle is the same ring
  of 8 rocks, evenly spaced, with a Kokiri in the middle and no middle rock (the group of 4 sits in a
  square, so the two can't be confused).

### Rocks and bushes: one check per age
- Each liftable rock and solid bush in Kokiri Forest is now two checks, a child one and an adult one (like
  the pots: separate objects per age, each giving its own item, tested in game). New IDs like
  `KF_CIRCLE_CHILD_ROCK_01` / `KF_CIRCLE_ADULT_ROCK_01`, `KF_BEHIND_SHOP_CHILD_BUSH_01`; the 27 old IDs
  retired. The rock in the middle of the circle stays one child-only check (`KF_CIRCLE_CENTER_ROCK`).
  Kokiri Forest: 119 checks.
- **Adult rock circle:** 4 rocks before the Forest Temple is completed, 8 others after (seen in game, and
  in a 100% save). The 8 have the rule `'Forest Temple Clear'`, a new event of the Forest Temple
  placeholder (rule for now: reaching the temple; the real one when it's mapped). The 4 are marked
  `missable` ("gone once the Forest Temple is completed: never place anything required here"); the field
  goes into the database (`tools/build_db.py`). Two new tests in `tests/logic_check.py`.

### In-game results of the rocks and bushes test
- **Rocks work:** the 12 circle rocks each dropped a red rupee (20) as a child. As an adult, the 4 circle
  rocks there dropped red rupees too.
- **The rock in the middle of the circle** can't be lifted as a child: a Kokiri is trying to lift it (an
  NPC scene). Maybe it can be lifted later in the game; to look at before it becomes a check.
- **Bushes work:** the 3 bushes beside Mido's house each dropped a Piece of Heart, as a child and again as
  an adult. The Piece of Heart needs A to pick up (the game's own ground Piece of Heart does; may be
  changed later).
- **Separate objects per age:** the adult rocks and bushes gave their items again after the child ones, so
  like the pots, rocks and bushes need one check per age.
- **Adult circle rocks:** only 4 are there as an adult (screenshot), though the adult map places all 12 at
  the same spots as the child ones, the same way (same rock, no `Presence`, nothing linked to them; some
  are only ~0.3 m apart). The unmodded game shows 4 too.
- Found: the circle is run by a level logic module (`Logic/KokiriForest_Common_Level_All_01_6aaf`, the map's
  `AiGroups` entry referencing the 12 rocks and 8 trigger areas). From its text: it creates and deletes
  rocks (`Logic_Create` / `Logic_Delete`) in two sets (8 and 4), checks the age and story flags
  (`Get_StoneOfForest_IsCompleted_Exp`, `SageOfForest_IsBefore_Step08`), and sets
  `KokiriForest_Npc_Kokiri_008_Child_LiftRock_AllBroken` when all are broken: it belongs to the scene of
  the Kokiri lifting the middle rock (`Npc_Kokiri_008_Child`). As an adult (in our test) only the set of 4
  is there: `KF_CIRCLE_ROCK_03`, `_06`, `_09`, `_12`. The exact conditions need an AI file reader (not
  built yet): the other 8 may appear as an adult at another point of the story.
- **Respawn:** after going to the Lost Woods and back, the bushes had **not** come back (pots do come back
  when the area reloads). What makes them come back is not known yet.

### Rocks and bushes in the builder (branch `rocks-bushes`, to test)
- Liftable rocks (`Obj_LiftRock_*`) and solid bushes (`Obj_Plant_Grass_*`) can be given an item: the builder
  adds `Drop__DropActor` to them (in Kokiri Forest none has a drop set; the game itself sets it on some
  rocks and bushes elsewhere, e.g. `Obj_LiftRock_A_01` with a red rupee in Desert Colossus,
  `Obj_Plant_Grass_A_01` with a blue rupee in Hyrule Field). A rock or bush that drops from a drop table
  (`Drop__DropTable`) is refused for now. Boulders are not included.
- Like the pots, each rock and bush is a separate object in the child and the adult map; if they work,
  they will probably need one check per age (decided after the test).
- Test mod: the 12 circle rocks near Mido's house: red rupee each; the rock in the middle of the circle
  (child only): Boomerang (ground version); the 3 bushes beside Mido's house: Piece of Heart each.

### Tidy before merging `ocarina-chus-shop`
- Removed the test-only Empty Bottle shelf variants and the shop Bottle's special-deal workaround (bottles
  never reach a shelf now). Results stay above.
- Kept as it is for now (decided 2026-11-17): a chest giving the Fairy Ocarina gives the held-up version
  (`Item_NX2_Ocarina_Fairy`): visible when held up, playable after a save and reload or a change of
  scene, not straight away. The pot / ground ocarina behaves the same.

### No bottles on shop shelves (for now)
- The builder refuses any item with the "Bottle" special deal on a shop shelf (the Empty Bottle, potions,
  fish, Ruto's letter... `REFUSED_SPECIAL_DEALS` / `refusal()` in `tools/shop_items.py`), with a message
  saying why and where it can go instead (chest, pot, ground, NPC). The game's own bottle shelves
  (`Shop_Bottle_*`, special deal `NotPushToPouch`: poured into a bottle Link owns) are still allowed.

### In-game results of the Empty Bottle variants
- Neither variant can be bought: for both, the shopkeeper goes through his "on second thought" lines.
  With the special deal, the item settings' `PouchActor` and the row's bottle slot each ruled out, the
  refusal is in the game's buy code itself. Conclusion: an Empty Bottle can't be sold on a shelf (the game
  never sells one). It works everywhere else (chest, pot, freestanding, NPC).

### Empty Bottle on a shelf: two test variants (to test)
- The game's buy code refuses the shop Empty Bottle. Two test-only variants (`shop_items.VARIANTS`, given on
  the builder's command line as `CHECK=Item_Bottle~A` / `~B`), one guess each:
  - **A** (Recovery Heart shelf, 5 rupees): no `PouchActor`, so the shop version itself goes into the
    pouch, as the first ground Bottle did (which worked as a bottle).
  - **B** (Deku Nuts 10 shelf, 30 rupees): the row without its item-button slot (`AssignableItem:
    BottleA`) and bottle action guide, in case the buy code treats anything with a bottle slot as bottle
    contents; `Item_Bottle` still goes into the pouch.

### In-game results of the Kokiri Shop fixes
- **Count boards:** right. No board under single items (no "x10" under the Hookshot), "x3" under the
  3 Bombchus, which give 3. Bought shelves stay empty.
- **Hookshot on the shelf:** 0.3 m higher looks right, maybe a touch high: now 0.25 m.
- **Greeting:** still "low on stock" as a child before the Deku Tree, so the branch changed in
  `Npc_Kokiri_001_Shop_Child` is not where that line comes from. Left for later.
- **Empty Bottle:** still cannot be bought, so the special deal (row and item settings) is not the cause
  either. The shopkeeper says "That'll cost 5 rupees ... oh, wait, actually..." (`Shop_01_02_*`, played by
  `DisplayShop`'s `NotAvailableTalk`). Every route to it in `DisplayShop` goes through the engine's own
  buy check (`EventQueryCheckBuyResult`) answering "failed"; for bottle-kind items the flow asks about a
  free empty bottle first and then makes the same check. So the game's buy code refuses it. The game never
  sells an empty bottle (shops only sell bottle contents, poured into one you own), so the buy code most
  likely has no way to add a new bottle. Not something the files decide, as far as found.

### Kokiri Shop fixes after the first full-shop test (to test)
- **Greeting:** the child shopkeeper's talk (`Event/EventFlow/Npc_Kokiri_001_Shop_Child.bfevfl`) has one
  branch on meeting the Deku Tree (before: "Mido is blocking the way, can't restock"). Part of
  `kokiri_shop_full_stock` now: both sides of that branch go to the "after" greeting. The file is read and
  written by our event flow writer (byte-identical round trip checked).
- **Count boards ("x5"):** the builder now handles the boards of changed shelves: a single item gets none
  (the board and the links to it are removed), a bundle gets the board with its own count when the game
  has one (03 05 08 10 15 20 30 50), e.g. 3 Bombchus on the Deku Nuts 10 shelf: "x10" -> "x3".
- **Empty Bottle not for sale:** the shop flow (`DisplayShop`) sorts the selected item by kind; the
  "bottled goods" kind (potions, fish) is only sold when an empty bottle is free. The Empty Bottle's
  "Bottle" special deal most likely puts it in that kind. The shop version of an item with the "Bottle"
  special deal now has none (item table row and item settings); what goes into the pouch is still
  `Item_Bottle` (`PouchActor`).
- **Hookshot inside the shelf:** shelves stand an item in a pose made for it (the Deku Stick's long side,
  Z, stands up); the game never sells the Hookshot, and it stood on end, half inside the shelf. Items like
  that are placed higher (`SHELF_LIFT` in `tools/shop_items.py`, Hookshot 0.3 m to start, to tune).
- Test mod adds 3 Bombchus (the game's shelf, 45 rupees) on the Deku Nuts 10 shelf (child).

### In-game results of the full Kokiri Shop test
- Child: all 8 shelves are there before the Deku Tree. The **Boomerang** can be bought and works. The
  **5 Bombchus** can be bought without a bomb bag and work. The game's own items can still be bought again
  and again.
- Child: the **Empty Bottle** (on the Recovery Heart's shelf) could not be bought.
- Child: the shopkeeper still says Mido is blocking the way and he can't restock (the greeting of the
  set before the Deku Tree), though all 8 shelves are there.
- Some single items show an "x5" count board (the boards are separate objects linked to the shelf, made
  for the original bundle). Wanted: no count board on single items.
- Adult: the **Hookshot** shows, but partly inside the shelf. Bought, works, and the shelf stays empty
  afterwards (sold once works).

## 2026-11-16

### Kokiri Shop: one full shop per age (to test)
- New `--fix kokiri_shop_full_stock` (needed to change shop shelves):
  - Child map: the shop set placed before meeting the Deku Tree (the "low on stock" shopkeeper
    `Npc_Kokiri_001_Shop_Child_ShortStock`, its 8 shelves, 2 "sold out" boards and a bundle board: 12
    objects) is removed, and the set placed after it is always there (its `Presence` removed). Nothing
    else links to the removed objects (checked by the build).
  - The child shopkeeper's list: every shelf open from the start (release flags off).
  - The adult shopkeeper gets a list of its own (`Npc_Kokiri_001_Shop_Adult` ShopParam, its actor's
    `ShopRef`), same shelves, all open. The copy of the child list in its pack is kept identical to the
    child shopkeeper's.
  - A changed shelf: the map's shelf actor shows the item, and the shopkeeper's list entry names the same
    actor (what is sold, and its price), with stock 1 (sold once, as the game's "low on stock" list).
    Shop versions also keep `NoRespawn`.
- The data keeps both child placements of each shelf (as in the game files); with the fix on, the builder
  skips the ones the fix removes.
- Side effect: the vanilla items are on sale from the start as a child too (Deku Seeds before the
  Slingshot, the Recovery Heart).
- Test mod (shop only, plus `bombchus_without_bag`): child shelf 1 Boomerang (15), shelf 2 the game's
  5 Bombchus, Heart shelf Empty Bottle (5); adult shelf 1 Hookshot (15). The freestanding rupee in the
  shop (`KF_SHOP_RUPEE_ITEM`) is a gold rupee (`Obj_Rupee_Gold`), to have rupees for the test.

### In-game results of the held-up ocarina, Bombchus and shop test
- **Chest ocarina (held-up version):** now visible above Link's head, but **not playable** (the plain
  `Item_Ocarina_Fairy` from the same chest was playable). So naming the item (`PouchActor`) is not enough:
  what goes into the pouch is still our own actor, and only the real `Item_Ocarina_Fairy` is playable.
- **Pot ocarina (ground version, with `PouchActor`):** picked up and held up, still not playable until a
  reload. `PouchActor` did not fix it.
- **Bombchus without a bomb bag:** work. They go into the item menu (not 0/0) and can be used.
- **Kokiri Shop, child before the Deku Tree:** only 3 items show (Bombchus x5 on shelf 2, Deku Shield, Deku
  Stick); the other slots show only a sign. No Boomerang. The Bombchus cost **20** rupees, not the 75 of the
  game's 5-Bombchu shelf; buying them works.
- **Kokiri Shop, adult:** the same 3 slots show (Deku Nuts x5, Deku Shield, Deku Stick); the others say
  "Coming Soon". No Hookshot.
- So: the price comes from the shop slot, not from the shelf actor, and our shop versions don't appear at
  all.
- Found (game files): the **shopkeeper** decides what is sold. Its shop list (`ShopParam` -> `GoodsList`)
  has one entry per slot, in `ShopItemIndex` order (0 Heart, 1 Deku Seeds 30, 2 Deku Nuts 5, 3 Deku Nuts
  10, 4 Deku Seeds ..., 5 Deku Sticks bundle, 6 Deku Shield, 7 Deku Stick). Each entry names the shelf
  actor that is sold (its price), a release flag (`Release`: most slots only after meeting the Deku Tree)
  and a stock (`StockNum`: -1 unlimited, 1 = once, as the "low on stock" list before the Deku Tree). The
  shelf actor in the map only shows the item. Kokiri shopkeepers: `Npc_Kokiri_001_Shop_Child` (after the
  Deku Tree), `..._Child_ShortStock` (before: its own list over the child one), `..._Shop_Adult`, which
  has no list of its own: it uses the child one (same file, a copy in each pack).

### Held-up ocarina, Bombchus without a bomb bag, shop shelves (branch `ocarina-chus-shop`, to test)
- **What goes into the pouch:** every game ground item and shelf that stands for another item names it in its
  item settings (`PouchActor`: ground bomb `Item_Bomb`, ground Deku Shield and its shelf `Weapon_Shield_Deku`,
  Bombchu shelves `Item_Bombchu`...). Ours didn't, so the ground version itself went into the pouch. That is
  the likely cause of the ground ocarina only playing after a reload. Ground versions, held-up versions and
  shop versions now name the item.
- **Chest ocarina invisible:** the items a chest shows (Boomerang, Bottle...) are item event actors with
  get-demo animation settings (`ASInfo: Item_GetDemo`, `AS/Item_Common`, `Item_Common_Animation`). The
  ocarinas' actors are Link's playable instrument instead, with none of that. New **held-up versions**
  (`Item_NX2_<x>`, in `tools/ground_items.py`): the Boomerang's item actor with the item's model, animation
  (`Item_Common_Animation` + `<item>_Animation`) and item settings. A chest uses one only for items that are
  not item event actors already (the ocarinas). Link's real ocarina is not touched.
- **`--fix bombchus_without_bag`:** in the remake Bombchus have no maximum of their own (the bomb bag's:
  `MaxNumGameData: Bomb`), so without a bag it is 0. The fix gives them a fixed maximum of 50, as in the
  original game (`FixedMaxNum`, as the Magic Beans' 10 and the Gold Skulltula tokens' 100), and the bomb
  bags stop raising and refilling them (`ExpansionMaxNumActor`, `ActorFullOnlyIfIsGetWhenGetBag`). Rows
  changed: `Item_Bombchu`, the 1-Bombchu shelf `Shop_BombchuBundle_03`, the six bomb bag rows.
- **Shop shelves, one check per age:** the 8 Kokiri Shop shelves become 16 checks
  (`KF_KOKIRI_CHILD_SHOP_01`-`08`, `KF_KOKIRI_ADULT_SHOP_01`-`08`; the child check covers both child
  shelves, before and after meeting the Deku Tree). `KF_KOKIRI_SHOP_01`-`08` retired. Kokiri Forest: 92
  checks.
- **Shop shelves in the builder:** a shelf is changed by replacing its actor (the shelf number stays). A
  game shelf actor (`Shop_...`) is used as it is; any other item gets a **shop version**
  (`tools/shop_items.py`, `Shop_NX2_<item>_<price>_Once`): the game's Deku Shield shelf with the item's
  model, animation and item settings, the price of what the shelf sold, and **sold once** (`NoRespawn`, as
  the silver rupee tokens; untested).
- Test mod: Fairy Ocarina in Mido's chest (held-up version) and in the House of Twins child pot (ground
  version); Bombchus in the other child pot and the Bomb Bag on the ground near Mido, with
  `bombchus_without_bag`; Kokiri Shop shelf 1: Boomerang (child) and Hookshot (adult), 15 rupees, sold once;
  shelf 2 (child): the game's 5-Bombchu shelf.

### Special deal change undone
- The ground versions keep the item's special deal again (`tools/ground_items.py` as before the test): the
  change fixed neither the Bottle nor the ocarina. Test mod rebuilt (same items, Fairy Ocarina still in
  Mido's chest).

### In-game results of the special deal test
- Ground **Bottle** with no special deal: still no hold-up ("You got an empty bottle!" with Link standing).
  The special deal is not the cause.
- Ground **Fairy Ocarina** (pot) with no special deal: held up, but still not playable until a reload. The
  special deal is not the cause here either.
- **Fairy Ocarina from Mido's chest**: playable straight away, but **invisible** when held up (the message
  shows, Link's hands are empty). So the chest's get flow does whatever makes the ocarina playable, and the
  ground pickup doesn't. Invisible probably because `Item_Ocarina_Fairy` has no animation file of its own
  (its ground version needed one made, from `Item_Ocarina_Fairy_Animation`); not confirmed.

### Ground Bottle and ground ocarina: no "special deal" (to test)
- A ground version whose item has a special deal (`SpecialDeal` in its settings: the Bottle's `Bottle`, the
  ocarinas' `Ocarina`) now sets it to "None" in its own settings, so the ground pick-up logic skips its
  special steps. The item table row keeps the special deal. Only the ground Bottle and ground Fairy Ocarina
  change; the other ground items had none.
- Test mod adds a **Fairy Ocarina in Mido's chest** (`KF_MIDO_CHEST_01`): is a chest ocarina playable
  straight away? (Tells whether the bug is only in the ground pickup.)

### In-game results of the automatic pickup test
- Passed: every ground item is picked up by walking into it. The game loads on the updated Longshot.
- Bug: the **Bottle** is picked up without Link holding it above his head (the other items have that).
- Bug: the **Fairy Ocarina** from the pot can't be played after pickup until the game is saved, quit and
  reloaded (switching to adult also fixes it). Probably there since the first ground ocarina; the French
  randomizer has the same bug.
- Lead (not confirmed): these are the only two test items with a "special deal" in the game's item table
  (`PouchSpecialDeal`: `Bottle`, `Ocarina`), handled apart from ordinary items when received.
- Looked at (game files only):
  - The ground pick-up logic (`AI/PouchContent.event.root.ainb`, in `AI.Global`) reads the item's special
    deal (`QueryPouchContentGetSpecialDeal`) and has bottle-only steps (taking a bottle out, a bottle
    message, the bottle's position): a bottle picked up from the ground is handled like catching something
    in a bottle, not with the hold-up. The special deal it reads is in the item's settings
    (`PouchContentParam` `SpecialDeal`; the hash `3069107721` is "None", as in `KeyItemDefault`).
  - The game never lets Link pick a Fairy Ocarina up from the ground: Saria gives it in a cutscene
    (`Dm_Kokiri_0155`: add to the pouch, then the shared `GetPouchContent` get window), during which Link
    goes offstage and comes back. The shared get flow has nothing ocarina-specific. The ocarina reaching
    the pouch but only becoming playable after a reload or an age change suggests Link's ocarina is set up
    when Link himself is (re)loaded, which a cutscene does and a ground pickup doesn't (not confirmed).
  - The Ocarina of Time on the ground in the vanilla game is also followed straight away by an event
    (`DoorOfTime_GetOcarinaOfTime`, the Song of Time lesson).

### Ground items picked up by walking into them (to test)
- Each ground version (`Obj_NX2_*`) now has item settings of its own (`PouchContentParam`), built like the
  ground shield's: the item's own settings as parent, plus `DefaultAutoGet: true`. Only the ground versions
  change; the items from chests and NPCs keep their own settings.
- Test mod rebuilt with the same items in the same places, now from Longshot's new single folder
  (`romfs_path.txt` and the launcher point at it).

### In-game results of the ground items test, second try (Deku Shield template)
- Passed. The game loaded. The Bomb Bag, Boomerang and Empty Bottle were picked up, went into the item
  menu and work. The Fairy Ocarina (child pot), Bombchus (child pot, after the Bomb Bag) and Hookshot
  (adult pot) were picked up and work too.
- Every item except the Bottle needed **A ("Take")** to pick up. Wanted: picked up automatically, by
  walking into it, like the Bottle.
- Found: the item's own pick-up settings (`PouchContentParam`, copied into the ground version) decide
  this. The Bottle's has `DefaultAutoGet: true`, and so does the shield template's (`AutoPickShield`). The
  Boomerang, Bomb Bag, Fairy Ocarina and Hookshot have no `DefaultAutoGet`, so the game shows "Take". Not
  changed yet.

### Ground items rebuilt from the ground Deku Shield (to test)
- `tools/ground_items.py` now copies the game's ground Deku Shield (`Obj_Shield_Deku`) instead of the ground
  ocarina. It is a single equipment item lying on the ground, with the pick-up collision of ordinary ground
  items: a body that only touches the ground (`DropItem`, `HitOnlyGroundAndObject`), a pick-up sensor
  (`Item_Pouch_Tgt`, `SensorHitGetObject`), layer `SmallObject`.
- The shield's own settings are left out: its model, animation and item settings (replaced by the item's),
  its equipment table, its hookshot hold position and its effect link (only its burning effect; the row's
  `ELinkUserName` is removed too). No glow, no effects. Its sound link stays.
- Same test mod as before (same items, same places), rebuilt.

### In-game results of the ground items test
- The game loaded, and every ground item appeared in the right place (Bomb Bag, Boomerang in the water,
  Bottle in the shop, Fairy Ocarina from the child pot, Hookshot from the adult pot).
- None could be picked up: an invisible box around each item kept Link away, and he could climb onto it.
- Found: the ground ocarina used as the template has the generic solid box for physics (`ObjectDefault` ->
  `Box`, layer `GroundObject`) and no pick-up sensor, unlike every ground item that works. Fixed above.
- Bombchus not tested (no Bomb Bag). Wanted: Bombchus usable without a bomb bag (to look at separately).

### Ground versions of items (branch `ground-items`, to test)
- New `tools/ground_items.py`: makes a ground version of an item that only exists as the model shown when an
  item is received (`Item_...`), so it can lie on the ground or drop from a pot. Built like the game's own
  ground ocarina (`Obj_Ocarina_Time`, the Ocarina of Time in the castle moat): its pack with the ocarina's
  model, animation and item settings swapped for the item's, an actor parameter file of its own, and rows
  in `RSDB/ActorInfo` (the item's model and `ActorName`, the ocarina's ground settings), `GameActorInfo` and
  `PouchActorInfo` (the item's row). Named `Obj_NX2_<item>`. Items built like the ocarinas (equipment, no
  animation file) get one made the way the ground ocarina has one.
- `tools/build_mod.py`: a freestanding item or pot holding an item that can't lie on the ground gets its
  ground version automatically. The builder can now write files new to the game (size table entries with
  the headroom of a similar game file), add rows to tables, and edit a file twice in one build (the size
  entry is always worked out from the original file).
- Found: the Gold Skulltula token's glow comes from its effect link (`ELinkRef`, user `Obj_Token_Gold`); the
  ground ocarina has none, so our ground items don't glow (no glow wanted).
- The French randomizer (OOT26RandoBeta) was read for how it handles pots, at the user's request; facts
  credited to its author: shuffled pots behave like Gold Skulltulas (death no longer sets the pot's flag,
  the pot's AI hands its flag to the drop, picking the drop up sets it), and real items drop as clones of
  the Gold Skulltula token. No code or data was copied.
- Test mod: Bomb Bag, Boomerang and Empty Bottle as freestanding items; Fairy Ocarina and Bombchus from the
  child House of Twins pots, Hookshot from an adult one. Checklist in `TEST_CHECKLIST.md`.

### In-game results of the per-age pots test
- House of Twins: the child pot gave the Piece of Heart, the adult pot at the same spot gave the red
  rupee. One check per age works.
- Bombchus (`Obj_Bombchu`) could be picked up this time, but showed 0/0 and never reached the inventory.
- Found: Bombchus have no capacity of their own. Their maximum is the bomb bag's (`MaxNumGameData: Bomb` on
  `Item_Bombchu` in `RSDB/PouchActorInfo`), and each bomb bag raises both bombs and Bombchus
  (`ExpansionMaxNumActor`). Without a bomb bag the maximum is 0. Bombchus need the bomb bag, as in the
  remake itself; with a bomb bag they are not tested yet.

### Pots: one check per age (to test)
- Kokiri Forest's pots are separate objects in the child and adult maps, so each pot is now two checks,
  with its own item per age. A check can name one age (`"age": "child"` / `"adult"` in the world data): it
  covers only that age's object (builder, database, maps), and the logic counts it only at that age.
- IDs: `KF_HOUSE_OF_TWINS_POT_01/02` and `KF_KNOW_IT_ALL_HOUSE_POT_01/02` are retired; they are replaced
  by `..._CHILD_POT_01/02` and `..._ADULT_POT_01/02` (8 checks).
- `tests/db_check.py` checks coverage per object (each child and adult object needs a check), not per
  spot. New logic test: the child pot only as a child, the adult pot only as an adult.
- Test mod: House of Twins child pots hold a Piece of Heart and Bombchus (`Obj_Bombchu`, the ground
  version), adult pots a red rupee and Bombchus. The Boomerang test is left out (needs a ground version).
- Still to do: pots still refill. Found while looking: the game sets a named flag when a pot breaks only
  through small logic files linked to the pot in the map (Ice Cavern does it for two pots). Flag names are
  hashed with MurmurHash3 in `GameDataList`. Nothing in the game remembers whether an item dropped from a
  pot was picked up; the Gold Skulltula (`RespawnGmdHash`) is the only thing with that behaviour.
- Same situation, not split yet: Kokiri Forest's rock circle, other rocks, bushes, Saria's house hearts and
  the shop shelves also have separate child and adult objects.

### In-game results of the pots and freestanding test
- Kokiri Sword chest: gave the Fairy Slingshot, no sword, no cutscene. The special event removal works.
- Magic: no meter after the Lens of Truth or Din's Fire; after Magic both work. Double Magic before Magic
  gives the big meter at once (to handle with progressive items later).
- Freestanding: the Piece of Heart and the red rupee worked. The Boomerang appeared but could not be
  picked up. The spot named "behind Mido's house" is in the water.
- Pots: the Piece of Heart and the red rupee worked; the Bombchus appeared but could not be picked up.
  Both pots came back with their items when returning (as an adult), so the items could be taken again.
- Found (Boomerang, Bombchus): `Item_` actors are only the model shown when an item is received (parent
  `Item_EventObject_Base`, no pick-up collision). Ground items are `Obj_` actors (parent `Obj_Item_Base`).
  Only 24 exist (rupees, hearts, Piece of Heart, Bombchus as `Obj_Bombchu`, small keys, shields, ...); most
  major items have none. `Obj_Ocarina_Time` (the ocarina in the moat) is a thin wrapper around
  `Item_Ocarina_Time`'s model and item data, so the same can be built for other items. The earlier note
  about an `Item_` actor placed freestanding was wrong as a general rule.
- Found (pots refilling): the game keeps one saved flag per placed object, keyed by its placement hash
  (`GameData/GameDataList`, `Bool64bitKey`). Its `ResetTypeValue` decides when it resets: 24 = never
  (chests, heart pieces, freestanding rupees, tokens), 88 = when the area reloads (pots, rocks, grass),
  280 = enemies, 25 = shops and fairies. Kokiri Forest's pots are two objects each, one in the child map
  and one in the adult map, each with its own flag. No pot in the base game holds a one-time item.
- Data: Kokiri Sword chest, Storms grotto chest, the freestanding rupee near Mido and the shop rupee are
  now randomizable "yes"; the other tested pots and items stay "untested" with what was found.

### Pots and freestanding items in the builder (to test)
- Found: pots name their item like chests (`Drop__DropActor`); freestanding items have no settings, the
  actor type itself is the item (`Obj_Rupee_Blue`, `Obj_Heart`). Freestanding heart pieces elsewhere in the
  game are placed with no settings and no condition either, so the "already collected" memory comes with
  the actor type. The game also places an `Item_` actor freestanding (a bottle of milk in Hyrule Field).
- `tools/build_mod.py` now changes pots (their `Drop__DropActor`) and freestanding items (their actor type).
- Test mod adds: Piece of Heart and Boomerang as freestanding items, a red rupee in the shop; Piece of
  Heart and Bombchus in the House of Twins pots, a red rupee in a Know-It-All house pot. The Storms
  grotto chest is back to normal (no duplicate Lens of Truth).
- `TEST_CHECKLIST.md`: what to check in game for this test mod.

### Chest special events, magic as its own item (to test)
- In-game result of the chest-types test: the big chest (Kokiri Sword chest), the Kokiri Forest Storms
  grotto chest and the meadow's Wolfos grotto chest all gave their new item. But the Kokiri Sword chest
  still gave and equipped the sword, and the Lens of Truth gave the magic meter.
- Found: about 30 chests have a special opening event made for their original item (`GetEventName`). The
  Kokiri Sword chest's (`Get_StoneOfForest_GetSword`) plays `Dm_Kokiri_0063`, which gives and equips the
  sword. Others are presentation only (dungeon maps), and some carry story (Ruto's chests, Nabooru, the
  Serenade of Water after the Iron Boots).
- `tools/build_mod.py`: new `CHEST_EVENTS` table, deciding per event whether it is removed or kept when a
  chest's item changes; a chest with an event not in the table stops the build. The sword's is removed;
  Mido's chests' "Navi stays quiet" event is kept (tested harmless).
- Found: in the item table (`RSDB/PouchActorInfo`) every magic item raises the magic meter
  (`ExpansionAvility: MPMaxUP`, `MPMax: 24`). The Great Fairy's blessings exist as items of their own:
  `Item_FairyBless_MP` (magic, 24) and `Item_FairyBless_MPDouble` (48); also `Item_FairyBless_DefenseDouble`.
- `--fix magic_is_separate`: the magic items (21 rows: Lens, Din's, Farore's, Nayru's, magic arrows) stop
  raising the meter; only the blessings do.

### Other chest types (branch `chest-types`, to test)
- `tools/build_mod.py` also accepts a check's name, for areas without permanent IDs yet (it refuses a name
  when the check has an ID).
- Test mod adds: Kokiri Sword chest (big chest) -> Fairy Slingshot, Kokiri Forest Storms grotto chest ->
  Lens of Truth, Sacred Forest Meadow Wolfos grotto chest (appears after the Wolfos) -> Piece of Heart.

## 2026-11-15

### In-game results: skippable opening and bombs without the bracelet both work
- The opening cutscene could be skipped with `--fix skippable_opening`.
- Bombs could be held, thrown and exploded without the Goron Bracelet with `--fix bombs_without_bracelet`.
  The `bombs_without_bracelet` setting is now on by default (the logic counts a bomb bag alone as
  explosives); the logic test for the no-fix case switches it off explicitly.

### Skippable opening cutscene (to test)
- Found in the game files: the intro is `OpeningEvent` (two cutscenes, `Dm_Kokiri_0000` then
  `Dm_Kokiri_0030`). Only three cutscenes in the whole game block skipping: the opening
  (`Dm_Kokiri_0000`), the title screen and the staff credits (setting `SkipSetting: DisableSkip`).
  `Dm_Kokiri_0030` has no block (should already be skippable).
- `tools/build_mod.py --fix skippable_opening` removes that setting from the opening, so it can be skipped
  like any other cutscene; the game still runs every step of the opening. The builder can now also edit
  uncompressed game files and remove entries from BYML files.

### Bombs without the Goron Bracelet (to test), chest pedestals
- Found in the game files: every liftable object has a lift grade. Small rocks, bushes, pots, Cuccos and
  Bombchus share the "no upgrade" grade; bombs (and bomb flowers, in their own files) use the Goron
  Bracelet grade; the big rocks use the Silver and Golden Gauntlets grades. That is why a bomb vanishes
  without the bracelet.
- `tools/build_mod.py --fix bombs_without_bracelet`: sets the bomb's lift grade (in `Item_Bomb.pack`) to
  the "no upgrade" grade. Changes exactly 4 bytes of the pack; same sizes, so no size-table change for
  it. Bomb flowers keep needing the bracelet. The builder can now edit values inside actor packs.
- New setting `bombs_without_bracelet` (off until confirmed in game); `has_explosives` counts it.
  New logic test (28 in all, all pass).
- Fixed: the extractor counted chest pedestals (`Obj_TBoxPedestal_A_01`, in the Sacred Forest Meadow
  Wolfos grotto) as part of the chest. Re-extracted: only those two entries removed. The builder also
  refuses to change anything that isn't a real chest.

### Mod builder and the first in-game item test (branch `chest-test`)
- New `tools/build_mod.py`: changes what checks give, by check ID (chests only for now). Edits every
  placement of the check, writes the map files back compressed with the game's dictionary, updates the
  resource size table (keeping each entry's headroom and adding what the file grew), checks every actor of
  each file against what was intended, and can write a launcher `.bat`. Output goes to `out/` (ignored by
  git: it holds modified game files).
- Found while building: identical actor settings are stored once and shared in the map files, so changing
  one chest changed every chest with the same contents. The builder now gives each changed actor its own
  copy.
- Test mod: the four chests in Mido's house get a Boomerang, a Piece of Heart, a Hylian Shield and a bomb
  bag. **Result: all four gave the new item and it worked, no issues.** `KF_MIDO_CHEST_01`-`04` are now
  `randomizable: "yes"`; the other Kokiri Forest chests stay `untested` (different chest models).

### Full requirements for every check
- New `logic/requirements.py`: for each check, the smallest sets of items and settings that get it from
  the start of the game, for a child and an adult, following every route through the region map (exits,
  check rules, events, helpers, can_play / can_use). Stops with an error on a rule it can't handle (`not`,
  comparisons) instead of guessing.
- Database (`data/db/KokiriForest.json`): `requirements` is now this full answer (`[[]]` = nothing needed,
  `null` = impossible at that age); the check's own rule moves to `check_rule`; `requirements_note` flags
  answers that still go through placeholder regions.
- `tests/db_check.py`: every answer of all 120 checks (both ages, 430 alternatives) is tried against the
  search; 0 errors. The longest list today is 12 alternatives, so no shortening is needed yet.

### Check database and permanent check IDs (Kokiri Forest)
- New ID convention (README, "Check IDs"): `<AREA>_<SUBJECT>_<TYPE>`, with `_NN` only for groups; IDs are
  written once, never computed again, never reused; retired IDs stay listed.
- `data/world/KokiriForest.json`: every check (80) gets `"id"`, `"randomizable"` and `"randomizable_note"`.
  Nothing else changed (checked against the previous version: 0 of 80 checks and 0 of 11 regions changed).
- New `data/ids.json` (80 active IDs, area codes `KF` and `LW`, type codes).
- New `tools/build_db.py` and `data/db/KokiriForest.json` (generated): one row per check with region, name,
  type, the game's placement hashes, original contents, randomizable, requirements, verification status.
- Rocks and bushes with no drop table: original contents noted as "probably a random drop (rupees,
  hearts...), not confirmed in game".
- New `tests/db_check.py`: validation and totals (0 errors). Tried with deliberately broken data: it caught
  all 13 planted errors.

### Sacred Forest Meadow checked in game
- All 5 SFM regions now `"verified": true`. Confirmed in game: the child Wolfos gate (the slingshot is
  enough), the Song of Storms grotto and its Wolfos chest, Saria's Song needs Zelda's letter, the bomb
  grotto and its Song of Time blocks, the adult gate already open, Sheik's Minuet on the first adult visit,
  the hookshot for the Forest Temple entrance, and the Skulltula there in the daytime.
- `SFM GS`: rule changed from `can_use(Hookshot)` to `is_adult` (a jump reaches it).
- `tests/logic_check.py`: 1 new case (27 in all, all pass).
- Not tested: whether bombs also open the Song of Storms grotto (the game files say no), and the Song of
  Time tutorial (the test save was reached with cheats).

### Event flow writer: relocation table matches the game's files
- The first run of `run_tests.bat` on the whole game showed 32 event flows written back with one byte wrong
  in the relocation table (the list of pointers the game fixes up on loading). The game's files also list
  null pointers for a flowchart's empty actor, event and entry point arrays, and for a callswitch with no
  cases; `formats/evfl.py` now does the same. All 32 now come back identical (650 identical in all).
- README: the status table now gives the whole-game results, and what isn't identical yet (264 event flows
  with timelines or entry point variables, 2 BYML system files).

### No personal path in the repository
- `run_tests.bat` no longer has a built-in game path: it takes the romfs folder from its argument, the
  `ROMFS` environment variable, or a local `romfs_path.txt` (ignored by git), and asks otherwise.
- `.gitignore`: `romfs_path.txt`, `report.txt`, `__pycache__/`.

### Sacred Forest Meadow mapped
- `data/checks/SacredForestMeadow.json` extracted from the game's map files: 14 spots (2 chests, 1 Gold
  Skulltula, 4 gossip stones, 7 solid bushes).
- `data/world/SacredForestMeadow.json`: 5 regions (SFM Entryway, SFM Meadow, SFM Upper, SFM Wolfos Grotto,
  SFM Upper Grotto), every spot placed, plus Song from Saria and Sheik in Forest as gifts. All
  `"verified": false`.
- Found in the game files (differs from the N64 game): the entryway grotto has a Song of Storms cover and
  the upper grotto a bomb cover (swapped); the upper grotto has a chest behind Song of Time blocks and a
  gossip stone instead of two Deku Scrubs; the Skulltula is not night-only.
- New helper `can_defeat_wolfos` (the child gate and the grotto chest).
- Lost Woods now leads to `SFM Entryway`; the meadow placeholder in `_unmapped.json` is replaced by a
  `Forest Temple (not mapped yet)` placeholder.
- `tests/logic_check.py`: 8 new cases (26 in all, all pass).
- `maps/SacredForestMeadow_child.png`, `maps/SacredForestMeadow_adult.png`.
- README: Sacred Forest Meadow section.

### Earlier work (summary, before this changelog)
- `formats/`: zstd, SARC, BYML, BFEVFL, MSBT, RESTBL readers/writers, byte-identical on 1,177 game files.
- Region map and search (`logic/`), Kokiri Forest (11 regions) and Lost Woods (5 regions) mapped.
