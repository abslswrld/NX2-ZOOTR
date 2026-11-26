# NX2-ZOOTR

Step 1: file formats (below). Step 2: the region map (logic), see "Region map".

Our own readers and writers for the file formats the randomizer will need, written from the public
format documentation and checked against the game's own files. No code from any other randomizer, and
no game files are included.

## Status

| Format | Module | What it's for | Round-trip on the whole game (2026-11-15) |
|---|---|---|---|
| Zstandard `.zs` (with the game's dictionaries) | `formats/zstd.py` | every compressed file | 9,341/9,341 decompress correctly |
| SARC `.pack` / `.sarc` | `formats/sarc.py` | archives (actor packs, text) | 8,402/8,402 byte-identical |
| BYML v7, little and big endian | `formats/byml.py` | GameData, RSDB tables, map actors (`.bcett`) | 144,150/144,152 byte-identical (see below) |
| BFEVFL event flows | `formats/evfl.py` | item hand-outs, shops, cutscenes | 914/914 byte-identical (2026-11-25: the 261 timeline files of the cutscenes and the 3 files with entry point variables are read and written too, see "Timelines"). New steps can be added to a flow, not only existing ones changed (see "Adding steps to an event flow") |
| MSBT text | `formats/msbt.py` | item names, hints, dialogue | 8,640/8,640 byte-identical |
| RESTBL | `formats/restbl.py` | file-size table the game needs for changed files | 1/1 byte-identical |
| AINB v0x408 (AI, logic and sequence graphs) | `formats/ainb.py` | pot respawn rules, item pick-up logic, level logic (the rock circle) | 11,707/11,707 byte-identical (2026-11-17: 1,942 loose files in `AI`, `Logic`, `Sequence` and 9,765 inside packs; 5,036 different files) |

"Byte-identical" means: read the file, write it back without changes, and get exactly the same bytes.
Whole game = `run_tests.bat` (the Event, RSDB, Mals, GameData, Pack and System folders, archives opened:
171,450 files).

Not identical yet:
- **2 BYML system files** (`PhiveConfig.byml`, `HeapDef.byml`) come back smaller than the originals. Not
  files the randomizer edits.

`tests/edit_check.py` also changes each format (adds an event, a table row, a file, a text, a size entry,
changes a number and a string in an AI file)
and checks the result reads back correctly. `tests/evfl_add_check.py` adds new steps to every event flow
read and checks the read-back (see "Adding steps to an event flow").

AINB notes: the expression block (EXB) inside a file is kept as raw bytes, and the string pool is kept as
read (new strings go at the end); see the top of `formats/ainb.py`. `tools/ainb_dump.py` prints a file as
text. The `AI`, `Logic` and `Sequence` folders (now part of `run_tests.bat`) also hold 3 BYML node
definition tables (`NodeDefinition/Node.Product.111.aidefn.byml`) that come back smaller, like the 2 BYML
system files above.

Not covered yet: BFRES models, BNTX textures (the tunic-colour
module already has its own texture code), save files (needed for the tracker).

## Things this game does differently from the public documentation

- **GameDataList is big-endian** (`BY`), while everything else is little-endian.
- **Text is UTF-8**, not UTF-16.
- **Event flows are version 0.4**: each event is 0x30 bytes (one extra pointer), and there are two event
  types the documentation doesn't have. From the game's files:
  - type 5, `callswitch`: runs an entry point and branches on the value it returns (cases are 32-bit hashes);
  - type 6, `return`: ends an entry point returning a 32-bit hash value.
- **In event flows a yes/no question answers 0 for yes and 1 for no** (the opposite of Breath of the Wild's
  flows): a switch on `EventQueryIsGameDataBool`, `...BoolExp`, `EventQueryIsGameDataString64`,
  `EventQueryCheckIsGet`, `EventQueryPlayerIsChild`, `EventQueryHasRuppe`... has case 0 = true, case 1 =
  false. Read from the game's own flows (e.g. `DisplayShop`: "has 20 rupees" case 0 goes on to the
  transfer, case 1 to "not enough rupees"; "is child" case 0 gives the child's Deku Shield lines, case 1
  the adult's). Choice queries answer the choice's number from 0.
- Which flow files an event may call is also listed in `RSDB/GameAnalyzedEventInfo` (`SubFlowList`, per
  event), and `RSDB/EventSetting` names each event's flow file and entry point. Flow files exist only as
  loose files in `Event/EventFlow` (no copies in packs).
- The game's files list some null pointers in the event flow relocation table (empty actor action lists,
  entry point arrays, empty switch and callswitch case lists, and a flowchart's actor, event and entry
  point arrays when they are empty); the writer does the same.
- The 32-bit values of `return` events and `callswitch` cases are the **FNV-1a hash of a name** (`Yes`,
  `No`, `Complete`... match; `evfl.return_hash`).
- Each entry point of an event flow lists the subflow and callswitch events that can run from it (true of
  every entry point of the game's 653 flowchart files); the writer's helpers keep that list up to date.
- An entry point can have variables of its own with a starting value (5 entry points in 3 files:
  `LinkSleepInBed` `IsKokiriBed`, `Dm_SY_Ocarina` `IsNotNeedSensor`, `Dm_SY_Get` `Frames`): a name list and
  16 bytes per variable, written in place of the 24 empty bytes an entry point otherwise has
  (`EntryPoint.variables`).

## Timelines (cutscene files)

A cutscene file (`Dm_...`) holds either a flowchart or a **timeline**, never both (261 timeline files). The
timeline part is not in the public documentation for this version; it was worked out from the game's files
(2026-11-25) and `formats/evfl.py` reads and writes it byte for byte:

- **One `TLIN` block** (0x60 bytes): its length in frames, counts, and pointers to its actors, clips,
  triggers, sub-timelines and cuts. The actors' parameters and action names are written *before* the block,
  the clips' parameters after the cuts.
- **Times are frames, 60 a second:** 12 movie cutscenes have a timeline beside their video file
  (`Event/Movie/<name>.webm`), and for 11 of them it is as long as the video to within 2% (`Dm_Kokiri_0095`:
  7040 frames, video 117.33 s).
- **Clip** (0x18 bytes): start, length, actor, action, a track number, parameters: "this actor does this from
  frame A for N frames". Clips of one actor on one track never overlap; an actor's `cut` byte is its number
  of tracks.
- **Triggers:** every clip's start (1) and end (2), in time order; at one frame the ends come first, each by
  clip number. `evfl.timeline_triggers(tl)` gives exactly the list of all 261 files, so a changed timeline
  can be written.
- **Cuts** (0x18 bytes): the frame each camera cut starts at, and its name (`cut1`...). **Sub-timelines:**
  the names of the files run alongside (`<name>_Effect`, `<name>_Env`).
- No file has one-shot steps, timeline parameters or cut parameters; the reader takes them as the public
  documentation of the older version has them.
- **A timeline cannot set a flag or give an item:** its 94 kinds of step are camera, animation, voice, light,
  effect, rumble and weather steps (the one thing five timelines set is the time of day). What a cutscene
  sets is in the flowchart that runs it. See `docs/CUTSCENES.md`.

`tests/cutscene_list_check.py` checks all of this on every file, changes a timeline (longer, a clip and a
cut added) and reads it back, and checks that mistakes are refused.

## The cutscene list

`tools/cutscene_list.py "<romfs>"` writes **`docs/CUTSCENES.md`** (to read) and **`data/cutscenes.json`** (the
same as data): every cutscene of the game by area, for decision 15 (cutscenes skippable, shortened or
removed). It reads only. For each: the files, the kind (timeline, movie, flowchart), the length, what starts
it and when, what it sets and gives, what it runs next, whether the game lets it be skipped, who asks whether
it has been played, and its check. 319 story cutscenes (events named `Dm_...`), 217 lead-in events (they run
a story cutscene as a step and hold what it "sets"), 363 small scenes (a door opens, a chest appears), 79
system scenes (`Dm_SY_...`). Where the facts come from is at the top of the tool; how to read an entry is at
the top of the document. Both files are made by the tool: after a game update, run it again
(`tests/cutscene_list_check.py` fails when they are out of date).

## The area checklist template

**`docs/AREA_CHECKLIST_TEMPLATE.md`** is the shape of every area's in-game test list (`out\TEST_CHECKLIST.md`
and `out\TEST_ANSWERS.md`): what goes on it and in what order (decision 27), how it is written, the two blocks
to copy, what is recorded after the answers, and a table of the check kinds already passed in game.

## Adding steps to an event flow

`formats/evfl.py` can add to a flowchart as well as change it (2026-11-17):

| Call | What it adds |
|---|---|
| `fc.add_action(actor, action, params, next)` | a step where an actor does something (the action is added to the actor when it's new) |
| `fc.add_switch(actor, query, cases, params)` | a branch on an actor's answer (the query is added when new) |
| `fc.add_fork(forks, join)`, `fc.add_join(next)` | branches run side by side, and where they meet |
| `fc.add_subflow(flowchart, entry, params, next)` | runs an entry point of this or another flow |
| `fc.add_callswitch(flowchart, entry, cases, params)`, `fc.add_return(value)` | the game's two extra types: run an entry point and branch on what it returns; return a value (a name or a number) |
| `fc.add_actor(name, secondary, params=...)` | a new actor |
| `fc.add_entry_point(name, main)` | a new entry point |
| `fc.repoint(old, new, keep=())` | every link to event `old` now goes to `new` (to put new steps in front of an old one) |
| `evfl.dumps_checked(flow)` | brings the entry point lists up to date, checks the flow (names unique, every index in range), writes it, reads it back and compares every event, actor, action, query, parameter and entry point with what was meant |

Everything new goes at the end of its list, so every existing index stays valid. `actor` is an index, a name
or (name, secondary name). `tests/evfl_add_check.py` adds one of everything to each of the 653 flowchart files and
checks the read-back, and keeps two worked examples (examples only: the builder doesn't use them and they
haven't been tried in the game):

- **Giving an item with its get window** (`example_item_get`), as `Dm_Kokiri_0155` gives the Fairy Ocarina:
  1. action `PouchSystemActor.EventTriggerAddOrRemovePouchContent` `{Num: 1, IsEquipDIrect: False,
     IsSetMessageTargetActorName: True, Actor: <item>, IsGetEvent: False}`: into the pouch;
  2. subflow `GetPouchContent` entry `DisplayGetByActorName` `{ActorName: <item>}`: the window
     (`EventTriggerSetForGetWindow`, then `OpenGetWindow`, which picks the window by kind of item).

  One subflow does both and more, as chests and pick-ups do: `GetPouchContent` entry
  `GetPouchContentByActorName` `{ActorName: <item>}` (window, rupee counter, pouch, autosave).
- **Selling an Empty Bottle on a shelf** (`example_shop_bottle`), in `DisplayShop`, the flow every shop
  shares. Its `NormalFlow` runs when an item is chosen: sold out? then callswitch `SelectItem_CheckAvailable`
  (holds the game's buy check, `EventQueryCheckBuyResult`, which refuses a new bottle), then the talk, pay
  and get steps. The example puts a branch in front of that callswitch: if `Shop_SelectItemName` is the named
  item (`GameDataActor.EventQueryIsGameDataString64`) and Link has the price
  (`PouchSystemActor.EventQueryHasRuppe`): pay (`Npc_EventStarter.EventTriggerPayItemPriceAtShop`), the two
  item get steps above, mark the shelf sold (`EventTriggerAddShopItemSoldNum`,
  `EventTriggerSendMessageToShopBoard`, a one-frame wait, `EventTriggerVisibleItemAtShop`: what the game does
  after a "sold out" buy), back to the shelves (subflow `Buy_ReturnStart_NoDofReset`). Otherwise the game's
  own steps, untouched. 10 new events, 1 new action name, 1 link moved.

## Running the tests on your PC

Needs Python 3.13 or newer. Python 3.14+ is much faster (it has zstd built in). Nothing is installed and
nothing in the game folder is changed: the tests only read.

- Double-click `run_tests.bat` (it takes the romfs folder from its first argument, the `ROMFS` environment
  variable, or a one-line `romfs_path.txt` next to it, which is not uploaded; otherwise it asks). It runs every
  test script through `tests/run_all.py`, 8 at a time, slowest first: about 2.5 minutes for all of them
  (about 17 one after another). It says which passed; each script's whole output is in `test_logs\` (not
  uploaded) and a failing script's last lines are shown at the end. A quick check of a few while working:
  `python tests/run_all.py "<romfs folder>" --only families_check,hint_check`, or
- `python tests/roundtrip.py "<romfs folder>" [folders...] --report report.txt`
- `python tests/edit_check.py "<romfs folder>"`

On the whole game with Python 3.13 the round-trip test can take a long time; give it a few folders first,
e.g. `Event RSDB Mals GameData`.

## Licence

Not chosen yet (see the research notes: GPL lets us use community libraries; writing our own, as here,
keeps every option open). Everything in this folder was written for this project.

## Region map (logic)

Built like the N64 randomizer's logic: the world is split into regions (rooms or parts of rooms), joined by
exits with rules; each check sits in a region with its own rule; child and adult are worked out separately;
events (Mido shown the sword and shield, the Deku Tree beaten...) unlock more as they're reached.

| Folder / file | What it is |
|---|---|
| `data/checks/<Area>.json` | made by `tools/extract_checks.py` from the game's map files: every chest, Skulltula, scrub, shop shelf, pot, freestanding item, liftable rock, solid bush and gossip stone, with the game's own placement ID, position, original item, ages and flags |
| `data/world/<Area>.json` | written by hand: the area's regions, exits, checks and their rules |
| `data/world/_unmapped.json` | where the search starts, and stand-ins for areas not mapped yet |
| `data/helpers.json` | shared rule shortcuts (`can_child_attack`, `has_explosives`, `can_leave_forest`...) |
| `data/items.json`, `data/settings.json` | the item names rules can use, and the settings with their defaults |
| `logic/rules.py`, `logic/world.py` | the rule language and the search |
| `logic/requirements.py` | the full requirements of every check from the start of the game, for a child and an adult (the smallest sets of items and settings that work) |
| `tools/area_map.py` | draws an area from above with every check labelled (`maps/`) |
| `tests/logic_check.py` | situations with a known answer (closed forest, Song of Storms without an ocarina...) |
| `data/ids.json` | every permanent check ID ever issued (active or retired), the area codes and the type codes |
| `tools/build_db.py`, `data/db/<Area>.json` | the check database of an area, built from the files above (generated: never edit it by hand) |
| `tests/db_check.py` | checks the database and the IDs, and prints totals |
| `tools/dungeon_keys.py` | a small key of one dungeon (`Item_Dungeon_SmallKey@<dungeon>`): the key's own version for a pot, rock, bush or freestanding item, for a Gold Skulltula and for a chest, which adds 1 to that dungeon's saved key count (`DungeonInfo.<dungeon>.SmallKeyNum`) wherever it is found; on a check of its own dungeon the builder uses the game's own key instead; outside it the key's messages name the dungeon, in the dungeon's colour (`COLOURS`; blue and purple take two places of the game's list of text colours that no text uses; `build_mod.py --key-colour <dungeon>=<colour>` chooses another); used by `tools/build_mod.py` |
| `tools/build_mod.py` | builds a Longshot mod folder: changes what chests, pots, freestanding items, shop shelves, liftable rocks, solid bushes, Gold Skulltulas, gifts (those handed over through the shared `Dm_SY_GetInEvent` flow) and Deku Scrubs that sell one thing once (with a generic sales line naming the item) give, by check ID, applies game fixes (`--fix bombs_without_bracelet`, `--fix skippable_opening`, `--fix magic_is_separate`, `--fix bombchus_without_bag`, `--fix kokiri_shop_full_stock`: one full shop per age, needed for shelves, `--fix kokiri_circle_after_dungeons`: the rock circle as after the dungeons at both ages), updates the resource size table, and can write a test launcher; output in `out/` (never committed) |
| `tools/evfl_test_mod.py` | builds the small test mod (own folder and launcher) that shows whether event flow edits work in game: the child Kokiri shopkeeper's greeting and goodbye |
| `tools/ground_items.py` | makes ground versions (`Obj_NX2_<item>`) of items that only exist as the model shown when received, from the game's own ground Deku Shield, so they can lie on the ground or drop from a pot and are picked up by walking into them; also held-up versions (`Item_NX2_<item>`) for chests giving items with no get-demo setup of their own (ocarinas), from the Boomerang's item actor (used by `build_mod.py`) |
| `tools/shop_items.py` | makes shop versions (`Shop_NX2_<item>_<price>_Once`) of items for shop shelves, from the game's own Deku Shield shelf, sold once (used by `build_mod.py`) |
| `tools/sizes.py` | what a file's entry in the resource size table has to be, from its contents: the rules per kind of file, fitted on the game's own files (used by `build_mod.py` for every file it changes or adds) |
| `tests/event_families_check.py` | upgrade families on a song check and on Saria's bridge gift: every family, every number of levels owned, what follows each get, the read-backs, whole builds (in `run_tests.bat`) |
| `tests/hint_check.py` | gossip stone hints (`build_mod.py --hint STONE=ITEM` or `STONE=@CHECK_ID`): every name a hint uses is the game's own English text, every check gets a wording that fits a stone, what `--hint` takes and refuses, and a whole build read back (in `run_tests.bat`) |
| `tools/start_state.py` | the starting state of a new file: adds starting items and starting flags to the game's own list of what a new file has, the sequence module `Sequence/SetPouchAndStatusForGameStart` (used by `build_mod.py --start ITEM[=N]` and `--start-flag NAME=VALUE`; a flag can also be a field of a dungeon's record, `DungeonInfo.<dungeon>.SmallKeyNum` / `IsGetMap` / `IsGetCompass`, or a place's visited mark, `IsVisitLocation.<place>`) |
| `tests/start_state_check.py` | the starting state: where the game sets up a new file and what it gives and sets there, read from its own files; items and flags of each type added and read back; what is refused; whole builds (in `run_tests.bat`) |
| `tests/forest_temple_check.py` | the Forest Temple's data against the game's files: its 46 spots and what the game puts in them, one check and one permanent ID per spot, the five locked doors as the five key rules, the boss lock, the eye switches and the ice, and the temple walked with the items where the game puts them (and without the Bow, the boss key or a key); every one of the temple's 47 scenes in the cutscene list can be skipped with the game's own skip (decision 48) (in `run_tests.bat`) |
| `tests/forest_temple_items_check.py` | items on the Forest Temple's chests, pots and Gold Skulltulas, and the Bow room's door: how the temple's pots and chests name what they give, a pot or chest of each form given an item and read back, the chests' opening events, the Bow room's shutter lock before and after `--fix forest_temple_bow_room_door` (one node differs), and a whole build of the test sample read back from the mod folder (in `run_tests.bat`) |
| `tests/forest_temple_keys_check.py` | the Forest Temple's small keys on other checks of the temple: what makes an item a small key in the game, the key versions the builder makes for a pot and a Gold Skulltula (the same inventory settings, given as the key itself), the test placement walked with the logic (every locked door reached with enough keys), placements that must get stuck, and a whole build read back from the mod folder (in `run_tests.bat`) |
| `tools/dungeon_items.py` | a dungeon's boss key, map or compass wherever it is found (`Item_Dungeon_BossKey@<dungeon>`, `Item_Dungeon_Map@...`, `Item_Dungeon_Compass@...`): the item's version for a pot, rock, bush or freestanding item, for a Gold Skulltula and for a chest outside the dungeon, which sets the dungeon's saved yes/no (`DungeonInfo.<dungeon>.IsGetBossKey` / `IsGetMap` / `IsGetCompass`); in a chest of its own dungeon the builder uses the game's own item; used by `tools/build_mod.py` |
| `tests/key_items_tab_check.py` | the pause menu's Key Items tab open from the start (`--fix key_items_tab_open`): the game's table of stones and Medallions, the rows that show nothing, the two green tunics in the game's own new-file list, the fix read back, its size table entry, and a whole build read back from the mod folder (in `run_tests.bat`) |
| `tests/reward_spin_check.py` | the Spiritual Stones and the Medallions turn when held up and on the ground: the nine actors' empty animation settings and their models' two bones in the game's files, the Boomerang's settings they get, the change read back on all nine and on their table rows, what is refused, and a whole build read back (a chest, a pot, a loose item; one not placed is left alone) (in `run_tests.bat`) |
| `tests/forest_temple_every_spot_check.py` | the Forest Temple's every-spot build (decision 27): one build with a different item on each of the temple's 47 checks, every check read back from the mod folder (the right object holds the right thing, every new actor written with its table row, nothing else of the two maps changed, every file with its size table entry); and from the game's files, which of its chests names no contents and which only appear (in `run_tests.bat`) |
| `tests/reward_names_check.py` | the Spiritual Stones' and Medallions' names in their temple's colour in the get window: the nine items' names and messages in every language of the game, the coloured texts (each language's own, Japanese left alone, the Light Medallion left alone), and whole builds read back, with the list of text colours (in `run_tests.bat`) |
| `tests/boss_check.py` | the boss key, boss door, boss heart and Medallion of the Forest Temple: where the game saves a dungeon's boss key, map and compass and what sets them, the boss key chest's own event, the boss room's logic, the Medallion's cutscene and the file of it the game loads; the nine versions read back, what is refused, and a whole build read back from the mod folder (in `run_tests.bat`) |
| `tests/dungeon_keys_check.py` | a small key that counts for one dungeon wherever it is found (`CHECK_ID=Item_Dungeon_SmallKey@ForestTemple`): where the game saves a dungeon's key count, that its own key steps name no dungeon, the game's models for the two new steps, the key's three versions (ground, Gold Skulltula, chest) read back, what is refused, and a whole build read back from the mod folder (in `run_tests.bat`) |
| `tools/cutscene_list.py` | the cutscene list: writes `docs/CUTSCENES.md` and `data/cutscenes.json` from the game's files (events, flows, timelines, maps, logic graphs, actor parameters, the game's text); `--show <event>` prints one entry. Reads only |
| `tests/shop_shelf_keys_check.py` | phase 1, part 12: a dungeon's small key, boss key, map or compass on a shop shelf. From the game's files: a sale is an event of the shops' shared flow `DisplayShop`, which keeps the picked item's name (`Shop_SelectItemName`) and counts a sale in five places. A build with three such shelves read back: each is a shop version, sold once, of the version a chest holds; behind every step that counts a sale the name question leads ours to the chests' count step; nothing else of the flow changed. A build with an ordinary shelf item does not touch the flow (in `run_tests.bat`) |
| `tests/kokiri_neighbours_check.py` | phase 1, part 10: the starting state's leftovers (an item the inventory keeps under another name pushed as it is placed, a first weapon with the bag and the 30 seeds or arrows a chest gives with it, `--start-hearts`, `--start-rupees`; from the game's files: a placement's saved flag has no default value); a first weapon placed alone on a pot, a Gold Skulltula or a freestanding item gives its bag; a dungeon's small key, boss key, map or compass from a person and from a Deku Scrub (the chests' count step right after the get), refused on a cutscene gift and on a shelf; a stone or a Medallion from a person, a cutscene, a scrub and a shelf. Four builds read back (in `run_tests.bat`) |
| `tests/forest_temple_loose_ends_check.py` | phase 1, part 9: a family where the Medallion is given (the game's question in front of the cutscene's get); what floats down in Saria's cutscene is what it gives (the Medallion actor renamed, one actor per level of a family behind the same question, nothing for an item the cutscene cannot show); a family in a big chest (it becomes the game's checking chest, a small one); a key asked for with its name in its own dungeon is the named key. Three builds read back (in `run_tests.bat`) |
| `tests/cutscene_list_check.py` | the timeline reader and the cutscene list: all 914 event flow files read and written back byte for byte; the timeline rules on all 261 timeline files (trigger order, tracks, cuts, no step that sets a flag); the five entry point variables; a changed timeline read back, mistakes refused; the two list files are what the tool makes of the game now; every `Dm_` file is in the list; 60 frames a second against the movie files; facts found earlier (Saria on the bridge, Saria's Song, the opening, Link's door, the Forest Temple's boss and Medallion) |
| `tests/run_all.py` | runs every test script of `run_tests.bat` side by side (`--jobs N` at once, default 8; `--only NAME,...` for a few) and says which passed; the round-trip test is shown as its summary (it always lists the same known differences). A new test script adds its row to `STEPS` there; a `*_check.py` left out is named when it runs |
| `tests/size_check.py` | checks those rules against the entry of every game file they cover (reads every pack: several minutes; not part of `run_tests.bat`) |

Mapped so far: **Kokiri Forest** (with the bridge to Hyrule Field, which is part of that map in the remake):
11 regions, 7 chests, 3 Gold Skulltulas, the stick-upgrade scrub, Saria's gift, 8 shop shelves (one check per age, like the pots: 16), 4 pots,
24 freestanding items, 19 liftable rocks and 9 solid bushes (rocks and bushes as their own randomizer option;
one check per age, like the pots; the adult rock circle changes after the Forest Temple),
all taken from the game files. The 4 gossip stones are listed too (kind "gossip"): they give no item, they're
kept for hints. Every region is marked `"verified": false` until its
rules have been checked in game; anything uncertain has a `note`.

**Lost Woods**: 5 regions (front half, back half past adult Mido, Deku Theater, and the two grottos under
breakable boulders): Skull Kid and the Skull Kid ocarina game (heart pieces), the slingshot target, the Deku
Theater masks, 3 Gold Skulltulas, 4 scrubs (nut upgrade, seeds/arrows, bugs, potions), 9 bug bushes,
3 breakable boulders, exits to Goron City, Zora's River and the Sacred Forest Meadow. The bridge chest,
scrub and gossip stone are in both the Kokiri Forest and Lost Woods maps (separate IDs): one check each,
both copies get the same item (`"also"` in the data).

**Sacred Forest Meadow**: 5 regions (entryway, maze, upper plateau, and two grottos): the child Wolfos
gate, Saria's Song and Sheik's Minuet, the Gold Skulltula, 2 grotto chests, 4 gossip stones, 7 solid bushes,
and the exit to the Forest Temple (adult with the hookshot). The remake swaps the two grottos from the N64
game: the entryway grotto (two Wolfos, chest) opens with the Song of Storms, the upper grotto with
explosives, and the upper grotto holds a chest behind Song of Time blocks instead of two Deku Scrubs (all
from the grotto covers' own actor files: `Land_HidingHoleCover_DisappearSrom_Base` vs
`Land_HidingHoleCover_BrokenBomb_Base`). That finishes the forest outside the temples.

**Forest Temple** (one map for both ages; entered as an adult with the Hookshot): 23 regions, 12 chests, 5 Gold
Skulltulas, 28 pots, the Heart Container and the Forest Medallion (47 checks, all with IDs, area code `FT`).
Five locked doors in a fixed order, so the rules ask for 1 to 5 small keys (`ForestTempleSmallKey`), and the
boss door asks for `ForestTempleBossKey`. Remake differences found in the files: the first door is locked
(its key is in the first room's chest), the east courtyard opens with a floor switch, the basement has ice
over an eye switch, and there is no chest on a raised island (12 chests, not 13). Nothing here is checked in
game yet: every region is `"verified": false`, and the open questions are in CHANGELOG.md (2026-11-23).
Items can be placed on its chests (the boss key's too), pots and Gold Skulltulas, on the boss's heart and
where the Medallion is given (passed in game 2026-11-23 and 2026-11-24). The
Bow room reopens its door when its chest appears (`--fix forest_temple_bow_room_door`, setting
`forest_temple_bow_room_door`, on by default: decision 39), so the room needs no Bow to leave (passed in
game 2026-11-23).

Breakable boulders (`Obj_BrokenRock`) are listed with the rocks (kind "boulder"). Gifts from NPCs (no map
placement) carry the position of their NPC so they show on the maps.

Rules look like this: `is_adult and at_night and can_use(Hookshot)`. See `logic/rules.py` for everything a
rule can use.

## Check IDs

Every check has a permanent ID, written in `data/world/<Area>.json` next to the check (`"id"`) and listed in
`data/ids.json`. The game's own placement hashes are kept separately (`object_id` in the database); the two
are never mixed.

**Format:** `<AREA>_<SUBJECT>_<TYPE>`, or `<AREA>_<SUBJECT>_<TYPE>_<NN>` for a group. Capital letters,
digits and `_` only.

- `AREA`: a code from `data/ids.json` (`KF`, `LW`...), the one in the check's name when the ID is issued.
  Codes are unique across the game (Goron City and Ganon's Castle can't both be `GC`).
- `SUBJECT`: words from the check's name when the ID is issued, without the area and the type word.
- `TYPE`: `CHEST GS SCRUB SHOP POT ITEM ROCK BOULDER BUSH GIFT SONG GOSSIP`.
- `NN`: only for groups of checks with the same subject and type, `01`, `02`... A single check has no
  number (`KF_KOKIRI_SWORD_CHEST`). Words that aren't certain yet (left/right, top/bottom before they are
  checked in game) are left out of IDs: `KF_MIDO_CHEST_01` to `_04`.

**Rules**

- One ID per check (one item handed out), not per object: a check the game places several times (child
  and adult copies, the bridge chest in two maps) has one ID listing every placement; an NPC that gives two
  things has two IDs.
- Except when the child and adult objects are separate objects that each give their item (pots, rocks, bushes: each has
  its own "broken" memory, so one shared check could be collected once per age). Then there is one check
  per age, with `"age": "child"` or `"adult"` in its data and `CHILD`/`ADULT` in its ID and name:
  `KF_HOUSE_OF_TWINS_CHILD_POT_01`, `KF_HOUSE_OF_TWINS_ADULT_POT_01`. Such a check covers only that age's
  object, and the logic only counts it at that age.
- IDs are written once and never computed again: renaming a check, moving it to another region or
  extracting the map again doesn't change its ID.
- IDs are never reused. A check that goes away is marked `"retired"` in `data/ids.json` with the date and
  the reason. A new check gets a new ID. If a single check later gets a sibling with the same subject and
  type, the existing ID stays as it is and the new check gets a different subject word (no `_02` without an
  `_01`).
- `tests/db_check.py` fails on a duplicate, an unregistered or reused ID, a wrong area or type code, a
  number gap, a group mixing numbered and unnumbered IDs, an object with no check, or an out-of-date
  `data/db/` file.

**Requirements in the database:** `requirements` is what it takes to get the check from the start of the
game, worked out from every route through the region map (`logic/requirements.py`): for `child` and
`adult`, a list of alternatives (any one is enough), each a list of items and settings that must be on.
`[[]]` means nothing is needed, `null` means impossible at that age. `check_rule` keeps the check's own
rule (only what is needed once in its region). `requirements_note` says when an answer still goes through
a "not mapped yet" placeholder region, so it will change as the world is mapped. Nothing here is written
by hand: rebuilding the database updates every answer, and `tests/db_check.py` tries each one against the
search (every listed set reaches the check, every set minus any one item doesn't, and "impossible" really
is impossible).

**Classified so far:** Kokiri Forest (120 checks), Forest Temple (47 checks). `randomizable` is `"untested"` for every check that may
hold an item, until changing it has been tried in game; gossip stones are `"no"`.

