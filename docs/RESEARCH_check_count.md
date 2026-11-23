# Whole-game count of check-like objects (2026-11-23)

A read-only count from the game's map files (`romfs\Banc\<Area>\*.bcett.byml.zs`), for sizing the roadmap. **Not
mapping:** no names, IDs, regions or logic, nothing written into the project. A one-off
script (not kept in the repository) called `tools/extract_checks.py`'s own `extract()` (read only) and also tallied
crates (`Obj_BrokenBox_*`) and beehives.

**Spots:** one per place. An object that exists in both the child and adult maps is one spot. **Per age:** counts
it once per age, the way the forest's check IDs do (Kokiri Forest: 75 spots, 130 per age, 155 IDs with the shop's
24 slots and the gifts).

| Area | Chest | GS | Scrub | Shop | Loose item | Pot | Rock | Boulder | Bush | Crate | Beehive | Gossip | Spots | Per age |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kokiri Forest | 7 | 3 | 1 | 8 | 24 | 4 | 19 | 0 | 9 | 0 | 0 | 4 | 75 | 130 |
| Lost Woods | 1 | 3 | 5 | 0 | 0 | 0 | 0 | 3 | 9 | 0 | 0 | 1 | 21 | 38 |
| Sacred Forest Meadow | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 4 | 10 | 19 |
| Hyrule Field (with Lake Hylia, Lon Lon Ranch) | 7 | 11 | 4 | 0 | 28 | 9 | 10 | 3 | 23 | 14 | 0 | 6 | 109 | 152 |
| Market | 0 | 1 | 0 | 11 | 0 | 54 | 0 | 0 | 0 | 6 | 0 | 6 | 72 | 72 |
| Hyrule Castle | 0 | 2 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 2 | 0 | 3 | 10 | 10 |
| Kakariko Village | 2 | 6 | 0 | 9 | 2 | 10 | 0 | 0 | 1 | 2 | 21 | 2 | 53 | 67 |
| Graveyard | 3 | 2 | 0 | 0 | 9 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 15 | 20 |
| Death Mountain Trail | 1 | 4 | 0 | 0 | 7 | 0 | 10 | 10 | 1 | 0 | 0 | 2 | 33 | 52 |
| Goron City | 6 | 2 | 0 | 8 | 0 | 9 | 19 | 19 | 0 | 2 | 0 | 2 | 65 | 121 |
| Death Mountain Crater | 2 | 2 | 1 | 0 | 12 | 5 | 17 | 10 | 0 | 3 | 0 | 2 | 52 | 88 |
| Zora River | 1 | 4 | 0 | 0 | 22 | 4 | 10 | 3 | 3 | 0 | 0 | 4 | 47 | 89 |
| Zora's Domain | 1 | 1 | 0 | 8 | 7 | 5 | 0 | 0 | 0 | 0 | 0 | 1 | 22 | 41 |
| Zora's Fountain | 1 | 3 | 0 | 0 | 18 | 7 | 3 | 0 | 0 | 0 | 0 | 2 | 32 | 37 |
| Gerudo Valley | 5 | 4 | 0 | 0 | 0 | 4 | 8 | 9 | 0 | 0 | 0 | 1 | 30 | 46 |
| Gerudo Fortress | 2 | 2 | 0 | 0 | 0 | 15 | 0 | 0 | 0 | 13 | 0 | 0 | 32 | 32 |
| Haunted Wasteland | 1 | 1 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 8 | 14 |
| Desert Colossus | 3 | 3 | 0 | 0 | 1 | 0 | 15 | 0 | 0 | 0 | 0 | 1 | 22 | 43 |
| Ganon's Castle grounds | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| **Overworld total** | **45** | **56** | **11** | **44** | **130** | **136** | **113** | **57** | **53** | **44** | **21** | **42** | **710** | **1,073** |
| Inside the Deku Tree | 6 | 4 | 0 | 0 | 11 | 0 | 0 | 0 | 18 | 0 | 0 | 0 | 39 | 39 |
| Dodongo's Cavern | 9 | 5 | 1 | 0 | 1 | 37 | 0 | 0 | 0 | 0 | 0 | 1 | 53 | 53 |
| Jabu-Jabu's Belly | 4 | 4 | 1 | 0 | 1 | 19 | 0 | 0 | 0 | 2 | 0 | 0 | 31 | 31 |
| Forest Temple | 12 | 5 | 0 | 0 | 1 | 28 | 0 | 0 | 0 | 0 | 0 | 0 | 46 | 46 |
| Fire Temple | 16 | 5 | 0 | 0 | 3 | 18 | 0 | 3 | 0 | 4 | 0 | 0 | 49 | 49 |
| Water Temple | 9 | 5 | 0 | 0 | 1 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 39 | 39 |
| Shadow Temple | 14 | 5 | 1 | 0 | 1 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 85 | 85 |
| Spirit Temple | 15 | 5 | 0 | 0 | 1 | 27 | 0 | 0 | 0 | 0 | 0 | 0 | 48 | 48 |
| Bottom of the Well | 12 | 3 | 1 | 0 | 0 | 44 | 0 | 8 | 9 | 0 | 0 | 0 | 77 | 77 |
| Ice Cavern | 4 | 3 | 0 | 0 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 22 |
| Gerudo Training Ground | 23 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 25 |
| Inside Ganon's Castle | 16 | 0 | 0 | 0 | 0 | 40 | 4 | 0 | 0 | 0 | 0 | 0 | 60 | 60 |
| **Dungeon total** | **140** | **44** | **4** | **0** | **20** | **318** | **4** | **11** | **27** | **6** | **0** | **1** | **574** | **574** |
| **Whole game** | **185** | **100** | **15** | **44** | **150** | **454** | **117** | **68** | **80** | **52** | **21** | **43** | **1,286** | **1,649** |

(Spots and per age leave gossip stones out: they are hint spots, not checks. Two crates in `DreamWorld`, a set of
boss and enemy stages, are left out of the area rows but in the whole-game row.)

## Cross-checks
- **Gold Skulltulas: exactly 100**, as in the game. So every area's map was read, and Lake Hylia, Lon Lon Ranch and
  the houses and grottos sit inside the area maps (as Kokiri Forest's houses do).
- **Kokiri Forest: 75 spots** (79 with the gossip stones), the same as `data/checks/KokiriForest.json`.

## What the count can't see, or may have wrong
- **Not map objects, so not counted:** NPC gifts, songs, boss heart containers, dungeon rewards, minigames, the House
  of Skulltula rewards, Great Fairies, frogs and other event checks. They sit in event flows. They have to be listed
  area by area during mapping.
- **Scrubs (15) and shop shelves (44) look low** next to the N64 game (about 35 scrubs; the Market and Kakariko have
  more shops there). They may use other actor names, sit in other files, or be different in the remake. Unknown
  until those areas are mapped.
- **"Loose item" (150)** is every rupee and heart lying in the open (`Obj_Rupee_*`, `Obj_Heart*`). Kokiri Forest
  made its 24 checks; whether all 150 should be is a settings question.
- **Grass:** flat grass tufts (`Obj_Plant_Grass_A_04`, 147) are left out as foliage, as in the forest. "Bush" is the
  solid bushes (`Obj_Plant_Grass_A_01`/`_A_03`).
- **Not counted at all:** flying pots (`Enemy_FlyingPot_*`, 23), silver rupees (85), the Treasure Chest Game's chests
  (`Obj_HrlCity_Shop_TBox_*`, 12), 22 respawning bushes (`Obj_Plant_Grass_A_01_Respawn`).

## For the roadmap
- **Kinds tested one by one in game (question 26):** 185 chests + 100 Gold Skulltulas + 15 scrubs + 44 shop shelves =
  **344**, plus the event checks above.
- **Kinds tested by sample:** 454 pots, 117 rocks, 68 boulders, 80 bushes, 52 crates, 21 beehives, 150 loose items.
- **Size against the forest:** the three forest areas are 106 spots. The whole game is 1,286, about **12 times the
  forest**; 1,180 still to map.
