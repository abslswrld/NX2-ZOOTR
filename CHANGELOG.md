# Changelog

Newest first. Dates are when the work was done.

## 2026-11-15

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
