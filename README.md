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
| BFEVFL event flows | `formats/evfl.py` | item hand-outs, shops, cutscenes | 650/914 byte-identical; 264 not readable yet (see below) |
| MSBT text | `formats/msbt.py` | item names, hints, dialogue | 8,640/8,640 byte-identical |
| RESTBL | `formats/restbl.py` | file-size table the game needs for changed files | 1/1 byte-identical |

"Byte-identical" means: read the file, write it back without changes, and get exactly the same bytes.
Whole game = `run_tests.bat` (the Event, RSDB, Mals, GameData, Pack and System folders, archives opened:
171,450 files).

Not identical yet:
- **Event flows with timelines** (261 cutscene files, `Dm_...`) and **entry point variables** (3 files:
  `Dm_SY_Get`, `Dm_SY_Ocarina`, `LinkSleepInBed`): the reader refuses them on purpose for now.
- **2 BYML system files** (`PhiveConfig.byml`, `HeapDef.byml`) come back smaller than the originals. Not
  files the randomizer edits.

`tests/edit_check.py` also changes each format (adds an event, a table row, a file, a text, a size entry)
and checks the result reads back correctly.

Not covered yet: AINB (AI/logic files, inside packs), BFRES models, BNTX textures (the tunic-colour
module already has its own texture code), save files (needed for the tracker).

## Things this game does differently from the public documentation

- **GameDataList is big-endian** (`BY`), while everything else is little-endian.
- **Text is UTF-8**, not UTF-16.
- **Event flows are version 0.4**: each event is 0x30 bytes (one extra pointer), and there are two event
  types the documentation doesn't have. From the game's files:
  - type 5, `callswitch`: runs an entry point and branches on the value it returns (cases are 32-bit hashes);
  - type 6, `return`: ends an entry point returning a 32-bit hash value.
- The game's files list some null pointers in the event flow relocation table (empty actor action lists,
  entry point arrays, empty switch and callswitch case lists, and a flowchart's actor, event and entry
  point arrays when they are empty); the writer does the same.

## Running the tests on your PC

Needs Python 3.13 or newer. Python 3.14+ is much faster (it has zstd built in). Nothing is installed and
nothing in the game folder is changed: the tests only read.

- Double-click `run_tests.bat` (it takes the romfs folder from its first argument, the `ROMFS` environment
  variable, or a one-line `romfs_path.txt` next to it, which is not uploaded; otherwise it asks), or
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
| `tools/area_map.py` | draws an area from above with every check labelled (`maps/`) |
| `tests/logic_check.py` | situations with a known answer (closed forest, Song of Storms without an ocarina...) |

Mapped so far: **Kokiri Forest** (with the bridge to Hyrule Field, which is part of that map in the remake):
11 regions, 7 chests, 3 Gold Skulltulas, the stick-upgrade scrub, Saria's gift, 8 shop shelves, 4 pots,
24 freestanding items, 19 liftable rocks and 9 solid bushes (rocks and bushes as their own randomizer option),
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

Breakable boulders (`Obj_BrokenRock`) are listed with the rocks (kind "boulder"). Gifts from NPCs (no map
placement) carry the position of their NPC so they show on the maps.

Rules look like this: `is_adult and at_night and can_use(Hookshot)`. See `logic/rules.py` for everything a
rule can use.
