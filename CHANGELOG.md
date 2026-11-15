# Changelog

Newest first. Dates are when the work was done.

## 2026-11-15

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
