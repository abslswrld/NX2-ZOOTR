# Changelog

Newest first. Dates are when the work was done.

## 2026-11-17

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
