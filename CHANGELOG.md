# Changelog

Newest first. Dates are when the work was done.

## 2026-11-16

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
  ground ocarina has none, so our ground items don't glow. A glow could be added later by pointing
  `ELinkRef` at an existing effect.
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
