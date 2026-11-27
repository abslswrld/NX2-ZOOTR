# Changelog

Newest first. Dates are when the work was done.

## 2026-11-26

### Phase 2, part 2 closed: part 1's look stays, one upgrade of a family per shop (decision 51)
- **The user's decision** after the diagnostic: "keep part 1's look, but make a rule that 2 upgrades of the
  same family cannot be placed in the same shop". A family's shelf is one shelf object, the first level's
  shop version; the sale flow gives the level that is Link's turn (part 1, passed in game). Its label and
  model, and what Link holds up, are the first level's.
- **The two-object code is out again:** `shelf_twin_map_edit`, `keep_sold_counts` and their wiring are
  removed; `tools/build_mod.py` has part 1's way only. The two-shopkeeper way was not tried. What the game
  showed stays written down here and in the roadmap (the `Presence` setting, one object per shelf number,
  the sold count that can be kept).
- **The rule** (`shop_family_guard`, run before anything is planned): two shelves of one shop given levels of
  the same family stop the build, whether as pairs (`First>Second`) or one level alone. A shop is the region
  its shelves are in, so the child's and the adult's shelves of the Kokiri Shop count together. The rule is
  in `CLAUDE.md` under the randomizer rules.
- **`tests/shop_family_check.py`:** three builds it must refuse (the pair on two shelves, the pair beside its
  first level alone, one level alone on a child's and an adult's shelf).
- **Roadmap:** part 3 loses "one family on two shelves".
- **Tests:** the full run (`tests/run_all.py`): all 32 checks passed.

### Phase 2, part 2: what the diagnostic build showed
The user's answers (new file, child; the five shelves, then again with the Silver Scale from Mido's chest):

| Shelf | Arrangement | Without the Silver Scale | With the Silver Scale |
|---|---|---|---|
| 1 | a Boomerang, its sold count kept | chosen, "Boomerang", 15 rupees; bought, empty after coming back | |
| 2 | Silver Scale with `Presence` only, no twin | chosen, "Silver Scale", 20 | nothing there, cannot be chosen |
| 3 | twin linked from the shopkeeper after the shelf | **cannot be chosen** | chosen, "Golden Scale", 30; bought |
| 4 | twin linked before the shelf | chosen, "Silver Scale", 30 | **cannot be chosen** |
| 5 | twin not linked | chosen, "Silver Scale", 40 | **cannot be chosen** |

- **Found: the shop takes one object per shelf number, the one the shopkeeper's last link for that number
  points at, whether that object is there or not.** If it is absent the shelf cannot be chosen; the cursor
  goes round it.
- **What works:** the kept sold count (shelf 1); a `Presence` setting on a shelf (shelf 2); a second object
  under the same shelf number is labelled and priced as itself ("Golden Scale", 30 rupees) and sells
  (shelf 3); the switch between the two objects needs no reload of the area (the Silver Scale came from
  Mido's house, the shop was entered again).
- **What does not:** one shopkeeper serving two objects of one shelf number. Whichever is linked last is the
  only one that can ever be chosen.
- **What is left for decision 50:** two shopkeepers on one spot, one there while Link has no first level and
  one while he has, each linked to its own object for the family's shelf. It is the game's own way in this
  very shop (its two sets of shopkeeper and shelves by one flag). Limits seen already: it is one pair of
  states per shop, so two different families, or three levels, in one shop need more than two states.
  Nothing of it is built yet.

### Phase 2, part 2: the two-object shelf failed in game; a diagnostic build
- **In game (the user):** "i cannot move my cursor to either scale. and the cursor starts in the top left so
  its stuck there. i can leave the menu tho." The pair was on `KF_KOKIRI_CHILD_SHOP_01` and `_02`, the two
  shelves beside the Recovery Heart, so the cursor could go nowhere. The game did not stop.
- **Not known why.** What the build changed on those shelves: a `Presence` setting on the shelf, a second
  placement with the same shelf number, the shopkeeper's links to it (`ForSale`, `Reference`), and the sold
  count's reset type. The game's own shelves placed by a flag (the Happy Mask Shop's masks, the Kokiri
  Shop's two sets) each have a shelf number of their own under their shopkeeper.
- **A diagnostic build, to tell which of those the shop refuses** (made with a temporary change to the
  builder that is not committed; `out\TEST_CHECKLIST.md`): shelf 1 a Boomerang with its sold count kept;
  shelf 2 a Silver Scale with the `Presence` setting and no twin; shelf 3 the twin as built; shelf 4 the twin
  linked from the shopkeeper in front of the shelf; shelf 5 the twin not linked from the shopkeeper. Mido's
  first chest holds a Silver Scale, to switch the shelves over.

### Phase 2, part 2: a family shelf that looks like the level it sells (to test in game)
Branch `claude/shop-families-look`. Decision 50. Test build and checklist: `out\TEST_CHECKLIST.md`.

- **Read from the game's maps:** a placement can have a `Presence` setting, `{FlagName, IsCheckLazy,
  IsNegation}`: the object is only there while the saved flag is set (with `IsNegation`: while it is not).
  2,793 placements have one, on 424 flags. The game uses `IsGet.<item>` flags for it
  (`IsGet.Item_FairyBless_MP`). The Kokiri Shop's child map has two sets of shelves on the same spots, two
  placements per shelf number, one for each answer of `Meet_DekuTree_IsAfter_Step02_Exp` (`IsCheckLazy` true);
  the Happy Mask Shop's masks, which appear while Link is in the shop, have `IsCheckLazy` false.
- **Two shelf objects on one spot** (`shelf_twin_map_edit`, read back): for `SHELF=First>Second` the shelf's
  placement (First's shop version) gets `Presence` "not `IsGet.<First>`", and a twin of it gets
  "`IsGet.<First>`": the same placement under another hash with Second's shop version, lifted for Second's
  own model. Both are `IsCheckLazy` false. Every link to the shelf (the shopkeeper's `ForSale` and
  `Reference`) is also made to the twin, and the twin is in the shelf's groups. The twin's hash is the one the
  shelf had in the game: free, since the shelf takes over a removed shop board's hash for its saved flag.
- **One item from the two objects** (`keep_sold_counts`): both have the same shelf number
  (`ShopItemIndex`), and the shopkeeper counts a sale under that number
  (`Shop_SoldNum.<shopkeeper>.<number>`, a saved Int of its own per shelf). Once one object is sold, the other
  is "sold out" for the shopkeeper and hides. The game resets that count when the shops restock (reset type
  2); for a family shelf it now has the reset type of an ordinary saved flag (8), so the shelf stays sold.
- **Part 1's choice in the sale flow stays:** if the game only places objects when the area is loaded, a
  second shelf of the pair still shows the first level until then, and the flow gives the second level.
- **A guard of part 1 corrected:** "the game's own shelves sell Second" looked at the build's own shelf
  versions too; it looks at the game's only.
- **Not known from the files, to see in game:** whether the second object appears at once; whether the
  shopkeeper's line, label and price are right for the twin (his list names the first object for that shelf
  number).
- **`tests/shop_family_check.py`:** three more checks (the game's facts above; the two placements and the
  shopkeeper's links; the sold count's reset type).
- **Tests:** the full run (`tests/run_all.py`): all 32 checks passed.

### Phase 2, part 1: the retest passed; the look is not good enough (decision 50)
The user's answers (new file, child):
- **The scales stand on their shelves,** not in them. The lifts (0.19 m) are right.
- **The shopkeeper's line names the Golden Scale** for the second shelf: writing the name right after the shelf
  is picked works. The shelf's own label (shown while browsing) still says "Silver Scale": it is the shelf
  object's name, not the flow's.
- **"You got a golden scale!",** the price taken, the Golden Scale in the menu; both shelves still empty after
  leaving the shop and coming back.
- **The user's decision (decision 50):** it is not good enough that the shelf shows the Silver Scale's label
  and model, on the shelf and held up, when it sells the Golden Scale: "two shelf objects on one spot,
  switched by whether Link has the first level". That is phase 2's new part 2; the parts behind it move down
  by one (nine parts). Part 1's way stays in the builder: it gives the right level today, and it is the
  fallback for a second shelf of a pair bought in the same visit, should the game only switch shelf objects
  when the area is loaded.

### Phase 2, part 1: in-game results of the shelf pair, and two fixes
The user's answers (new file, child; two screenshots):
- **The method works.** The pair Silver Scale > Golden Scale on `KF_KOKIRI_CHILD_SHOP_01` and `_02`: the first
  one bought was the Silver Scale (line, window, price, menu), the second gave "You got a golden scale!" and
  the Golden Scale in the menu, the price taken. Each shelf was empty after its sale, nothing was sold twice,
  and it held after save and reload. (Leaving the shop and coming back was left blank.)
- **"Scale in shelf, needs to be raised"** (the screenshot: both scales half inside their shelves). Measured
  on the models as the other lifts were: the Silver Scale's pose is centred, its lowest vertex 0.192 m under
  the shelf point, the Golden Scale's 0.203 m. **Fixed:** `shop_items.SHELF_LIFT` gets both (0.19, 0.20 m).
- **The shopkeeper's line called the second shelf "Silver Scale".** Found: his line ("The <item>? That'll
  cost...", `Shop_01`) reads `Shop_SelectItemName` too, but it is shown before the "can Link carry it"
  question, where the name was written. The flow runs `Npc_EventStarter.EventTriggerShopItemFocus` when a
  shelf is picked (two such steps), then asks about the name and shows the line. **Fixed:** the question
  "is it First? Link has First?" and the write now stand right behind each of those two steps
  (`shop_focus_steps`), so the line, the question and everything after name Second. To see in game.
- **Link holds up the Silver Scale's model when he gets the Golden Scale** (the screenshot). As expected: the
  shelf is one object and shows its own model. Not changed: the user's decision.
- **Tests:** `tests/shop_family_check.py` (it reads the new place of the write) and
  `tests/shop_shelf_keys_check.py` pass.

### Phase 2, part 1: an upgrade pair on a shop shelf, a trial (to test in game)
Branch `claude/shop-families-trial`. Phase 2's eight parts are in the roadmap since today (decision 49). Test
build and checklist: `out\TEST_CHECKLIST.md`.

- **`SHELF=First>Second` on a shop shelf** (pairs only; three levels are refused until part 2). It was the one
  place a family could not go (decision 9: "unproven"). The earlier research (2026-11-23) saw three ways, each
  with a cost: more placements in the map, a "sold out" flag, or taking an item back after the sale. Part 12
  of phase 1 found what makes a fourth way possible: the sale is an event, and the flow keeps the picked
  item's name in the saved string `Shop_SelectItemName`.
- **How it works** (`shop_family_edit`, read back by `shop_family_check`; the shelf is First's shop version,
  sold once, as any item on a shelf):
  - In front of the flow's "can Link carry it" question: "is the item First?" -> "Link has First?" (the game's
    inventory question, `PouchSystemActor.EventQueryIsExistInPouch`) -> yes: Second's name is written into
    `Shop_SelectItemName` (`GameDataActor.EventTriggerSetGameDataString64`), two frames pass (the wait the
    scrubs' pairs need between a write and its use), then the game's question, which now asks about Second.
    From there the flow's buy line, its get window, its sound and its effects are Second's, since they all
    read that name.
  - What goes into the inventory is the shelf's own item, by one of five steps (three
    `EventTriggerGetItemAtShop`, two `EventTriggerShopItemPutInPouch`). In front of each: "is the item
    Second?" -> yes: Second is added (`PouchSystemActor.EventTriggerAddOrRemovePouchContent`, the step the
    scrubs add a bag with) and the shelf's step is passed by, so First is not added a second time.
  - A Link who has both levels is asked about by the game itself: its "can Link carry it" question then
    names Second.
- **Known before the test:** a shelf is one actor, so it shows First's model on the shelf and in Link's
  hands whichever level it sells. Only the name, the texts and what Link gets follow the level.
- **Refused:** three levels on a shelf; First alone on one shelf with its pair on another (the flow cannot
  tell the two shelves apart); a Second that one of the game's own shelves is named as (none is today).
- **A fault of part 10 found and fixed:** in `tools/build_mod.py` a name was used twice (`given`: the
  assignments as given, for `--hint`, and "handed over by a person"), so a build with a dungeon's key, boss
  key, map or compass **and** a `--hint` stopped with an error. `tests/kokiri_neighbours_check.py` now builds
  that combination.
- **`tests/shop_family_check.py`** (new; a row of `STEPS` and of `README.md`). `tests/pairs_more_check.py` and
  `tests/skulltula_prog_check.py` expected a pair on a shelf to be refused: they expect three levels refused
  instead.
- **Tests:** the full run (`tests/run_all.py`): all 32 checks passed.

### Phase 1, part 11: the Forest Temple's cutscenes are skippable, and that is enough (decision 48)
Nothing built. Phase 1 is complete with this (milestone M1).
- **Read from the game's files:** the temple has 47 scenes in the cutscene list: 18 story cutscenes (16
  flowcharts, 2 timelines: Phantom Ganon's entrance, 41.8 s, and his defeat, 1 min 32 s), 9 lead-in events,
  19 small scenes and 1 system scene. None has the "no skip" setting (`SkipSetting`: `DisableSkip`, the only
  skip setting in the game) in its settings list or the lists that one inherits from. In the whole game only
  the opening, the title screen and the staff credits have it. The 16 flowcharts have no skip steps of their
  own; the event that runs each of the two timelines asks afterwards whether it was skipped
  (`EventQueryIsEventSkipedMostRecent`) and has a branch of its own for that. No setting skips a cutscene by
  itself.
- **The user's decision (decision 48):** "If the cutscenes are already skippable then we are good to go". The
  game's own skip is enough for decision 15; nothing is shortened or removed, here or in later areas.
- **`tests/forest_temple_check.py`:** two new checks: every one of the temple's 47 scenes can be skipped (read
  from the game's settings lists, and the cutscene list says the same); only those three kinds of scene in
  the game cannot.
- **Not done:** no in-game round. What the game's skip keeps of each scene was not played through, and how
  long a flowchart cutscene really runs was not measured.

### Phase 1, part 12: the retest passed
The user's answers (new file, child):
- **The shelves' look:** the boss key and the compass stand on their shelves, not in them; the map stands on
  its shelf and does not float; the small key looks as before. The three lifts (0.22, 0.13, 0.20 m) are right.
- **A key from a shelf counts:** with only the small key bought in the Kokiri Shop, the first locked door of
  the Forest Temple opened. So the sale flow's step runs for the key as it does for the boss key, the map and
  the compass.
Part 12 has passed in game: a dungeon's small key, boss key, map and compass on a shop shelf.

## 2026-11-25

### Phase 1, part 12: in-game results; the boss key, the compass and the map lifted on the shelf
The user's answers (new file, child; one screenshot of the shop):
- **The four shelves** (`KF_KOKIRI_CHILD_SHOP_01` to `_04`) showed the Forest Temple's small key, boss key, map
  and compass, each named with "(Forest Temple)". Each was bought once with the right text ("You found the
  Boss Key! (Forest Temple)" for the boss key, the temple's name green), the shelf was empty after its sale,
  nothing was sold twice, and the shelves stayed empty after leaving the shop and after save and reload.
- **The temple's map** shows the map, the compass and the boss key: the sale flow's step sets them.
- **Not seen: the small key's count.** The line for the locked door in the temple was left blank. It is the
  same step in the same place as the three that set their fields, but only a door shows it.
- **"Boss key and compass in shelf"** (the screenshot: both models half inside the shelf). Found, measured on
  the models as the Hookshot's lift was (`item_pose.extent` on the vertices in `Pose_Common`): their poses are
  centred on the point they are placed at, the lowest vertex 0.220 m (boss key) and 0.134 m (compass) under
  it. The map's is centred too, 0.201 m under it. The small key stands on its point (+0.008). **Fixed:**
  `shop_items.SHELF_LIFT` gets the three (0.22, 0.13, 0.20 m); a version of ours is lifted as the game's item
  it is made of (`on_shelf`). `tests/shop_shelf_keys_check.py` measures the four models and checks the table
  against them. To see in game.

### Phase 1, part 12: a dungeon's key, boss key, map or compass on a shop shelf (to test in game)
Branch `claude/shop-shelf-dungeon-items`. The user chose this before part 11 ("Shop shelf first"; decision
47). Test build and checklist: `out\TEST_CHECKLIST.md`.

- **Found: a sale is an event.** Part 10 left the shelves out because the shelf's own AI could not count a
  key exactly once. The sale itself runs in the shops' shared flow, `Event/EventFlow/DisplayShop.bfevfl` (547
  events): it keeps the name of the item Link picked in the saved string `Shop_SelectItemName`, asks about
  that name itself (`GameDataActor.EventQueryIsGameDataString64`: the two tunics, the masks; 9 names), and
  counts a sale with `Npc_EventStarter.EventTriggerAddShopItemSoldNum`, once on each of its five ways through
  a sale. The name is the shelf's inventory name (`ActorInfo`: `Shop_Armor_Zora` is `Armor_Adult_Zora`).
- **The shelf** (`KEY_GIVEN_KINDS` now has `shop`): a shop version, sold once, of the version a chest holds
  (`Shop_NX2_NX2KN_ForestTemple_15_Once` for a Forest Temple key on a 15-rupee shelf). `tools/shop_items.py`
  is unchanged: the builder hands it this build's pack and table rows of that version (`shop_read`,
  `shop_rows`), since the game has none.
- **The count** (`shop_key_edit`, read back by `shop_key_check`): behind each of the five steps that count a
  sale, "is the item <that version>?" -> yes: the chests' own step (`EventTriggerAddOrSubGameDataInt` + 1 on
  `DungeonInfo.<dungeon>.SmallKeyNum`, or `EventTriggerSetGameDataBool` on the boss key's, the map's or the
  compass's field), then on as before; no: on as before. It is the step the gift and the scrub use, which
  passed in game in part 10. The shelf's AI is not touched.
- **"Can Link carry it":** before a sale the flow asks `PouchSystemActor.EventQueryCanAddToPorchByGameData`
  (yes, no, an error). Our versions are "not put in the inventory", and what the question answers for such
  an item is not known from the files, so the same name question stands in front of it and leads ours to its
  "yes".
- **`tests/shop_shelf_keys_check.py`** (new; a row of `STEPS` and of `README.md`). `tests/dungeon_keys_check.py`
  and `tests/kokiri_neighbours_check.py` no longer expect a shelf to be refused.
- **Tests:** the full run (`tests/run_all.py`): all 31 checks passed.

### Phase 1, part 10: the fourth look passed; "Boss Key" capitalised in its get text
The user's answers: the scrub's line says "Boss Key (Forest Temple)", the whole name green, on two lines
inside the box: good. After buying, the window says "You found the boss key! (Forest Temple)" with the
temple's name green: good. And: "Boss Key should be capitalized in the \"You found the Boss Key! (Forest
Temple)\" Text".
- **Changed:** the get text of a dungeon's boss key placed by the builder is "You found the Boss Key! (%s)"
  (`tools/dungeon_items.py`, `ITEMS`; `tests/boss_check.py` expects it). The game's own boss key, in a chest
  of its own dungeon, keeps the game's text ("You found the boss key!"). The small key's, the map's and the
  compass's get texts are as they were ("You found a small key!", "You found the dungeon map!", "You found
  the compass!"): not asked for.
- **Tests:** `boss_check`, `dungeon_keys_check` and `kokiri_neighbours_check` pass. The new text is not seen
  in game yet.

### Phase 1, part 10: "Boss Key" capitalised and green in the scrub's line
The user's answer to the third look: "Forest Temple" has its capital T, on two lines inside the box. And:
"\"Boss Key\" in scrub text should be capitalized, entire item name should be Green in the scrubs text box".
- **Capitals:** every capitalised word of the name of a dungeon's key, boss key, map or compass now has the
  game's "keeps its capital" tag (201, 13), the item's own words too (`dungeon_keys.proper` on the whole
  name): "Boss Key (Forest Temple)" stays as written when a talk line names it.
- **Colour:** the scrub's generic line had the item's name in the colour the game gives a name in talk (number
  0, red). For a dungeon's key, boss key, map or compass the scrub now uses a line of its own per colour
  (`scrub_line`, `scrub_label`: `Enemy_Scrub_Business_NX2_Item_Colour<n>`, named by the sale's
  `SellerMessageId`) with the name in its dungeon's colour (decision 40's colours: the Forest Temple's is
  number 3, green). Any other item's line is unchanged.
- **Tests:** `tests/kokiri_neighbours_check.py` reads the scrub's line and its colour;
  `tests/dungeon_keys_check.py` the four tags of a name. The scripts that read the scrub flow and its lines
  pass (`pairs_more_check`, `gossip_check`, `families_check`, `boss_check`, `hint_check`,
  `forest_temple_keys_check`). To see in game.

### Phase 1, part 10: the retest's results, and the capital T
The user's answers (one screenshot):
- **The scrub's line fits its box** on two lines ("Ah, the boss key (Forest temple)!" / "It's 40 rupees. Wanna
  buy it?"). The whole name is red there, as the game colours an item's name in a talk line; the dungeon's own
  colour (green) is in the get window's text.
- **A key from a person counts:** with only the Kokiri's key, the first locked door of the Forest Temple opened.
- **"Temple should have a capital T".** Found in the game's texts: a talk line that names an item in a
  sentence (the tag (201, 15) in front of the name, in the shop's and the scrubs' lines) writes the name's
  words small, and the game's own names mark each word that keeps its capital with the tag (201, 13) in front
  of it ("Deku Shield": one before each word; "Bigger Deku-Stick Bag": one before "Deku-Stick"; 57 of the 185
  item names have it). Our names for a dungeon's key, boss key, map and compass had none. **Fixed:** in the
  `_Name` text every capitalised word of the dungeon's name gets that tag (`dungeon_keys.proper`), so the line
  says "boss key (Forest Temple)". To see in game.
- **The staff roll:** "no easy way to check". The credits' colours stay with the areas, as the roadmap says for
  that case.
- **Tests:** `dungeon_keys_check` (it reads the tag now), `boss_check`, `forest_temple_keys_check`,
  `hint_check`, the two Forest Temple build scripts and `kokiri_neighbours_check` pass.

### Phase 1, part 10: in-game results and one fix
The user's answers (new file, child; two screenshots):
- **The start of a new file:** 5 hearts, 50 rupees, the Fairy Slingshot with 30 Deku Seeds (one shot: 29),
  the Goron Bracelet in the menu. All good. The Forest Temple's map opens as a child (the place is marked as
  visited); as an adult the page is still "???" (the adult made with the debug menu, as found on 2026-11-24).
- **`KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01`, the Fairy Bow alone:** the menu shows it with 30 arrows. Good: the
  first weapon alone gives its bag. **`..._POT_02`, a small key of the Spirit Temple:** "(Spirit Temple)" in
  orange. The pots did not come back after leaving the house, so neither gave its item again.
- **`KF_KOKIRI_CHILD_SHOP_01`, the Goron Ruby:** bought for 15 rupees, its name in red, on the Key Items tab;
  the shelf was empty after leaving and coming back.
- **`KF_CIRCLE_KOKIRI_GIFT`, a small key of the Forest Temple:** the Kokiri gave it, "(Forest Temple)" in
  green. **"The map shows 1 key": no key on the map.** That line of the checklist was wrong: the Map page
  shows no key count at all (found on 2026-11-24, part 6; the page has the map, the compass and the boss
  key). So whether the key counted is not seen yet: to see at a locked door of the temple.
  `docs/AREA_CHECKLIST_TEMPLATE.md` now says never to ask for a key count on the Map page.
- **`LW_NEAR_BRIDGE_SCRUB`, the Forest Temple's boss key:** sold for 40 rupees, "You found the boss key!
  (Forest Temple)", the scrub left, and the temple's map shows the boss key. Good. **Its line ran out of the
  box** (the screenshot: "Ah, the boss key (Forest temple)! It's 40 rupees. Wanna buy it?" on one line, wider
  than the box). Found: the game does not wrap a line, and the generic line (`SCRUB_LINE`) was one line.
  **Fixed:** it is two lines, as the game's own scrub lines are written ("Ah, the <item>!" / "It's <price>
  rupees. Wanna buy it?"). To see in game.
- **`LW_SARIA_GIFT`, the Fire Medallion:** Link held it up, its name in red, on the Key Items tab. Good.
- **Save and reload:** good. **The staff roll:** left blank.
- **Tests:** the scripts that read the scrub's line (`tests/pairs_more_check.py`, `tests/gossip_check.py`) and
  `tests/kokiri_neighbours_check.py` pass.

### Phase 1, part 10: Kokiri Forest and its neighbours (to test in game)
Branch `claude/kokiri-forest-neighbours`. Test build and checklist: `out\TEST_CHECKLIST.md`.

- **The starting state's leftovers** (`tools/start_state.py`, `tools/build_mod.py`):
  - **Items the inventory keeps under another name.** Read from the game: an item's inventory name is the
    `ActorName` of its row in `RSDB/ActorInfo` (`Item_Range_SlingShot` -> `Weapon_Range_SlingShot`,
    `Item_Range_Bow` -> `Weapon_Range_Bow`, `Item_Gauntlet_Goron` -> `Armor_Child_Gauntlet_Goron`), and the
    game's own new-file list pushes such a stand-in itself (`Obj_Armor_Adult_Normal`, kept as
    `Armor_Adult_Normal`). So `--start Item_Range_SlingShot`, `--start Item_Range_Bow` and `--start
    Item_Gauntlet_Goron` are now accepted and pushed as they are placed (before: refused, "under another name").
  - **A first weapon comes with its bag:** behind the weapon's push, one push each for what the game's chests
    give with it, read from the shared chest module (`turn_items.first_get`): `Item_BulletBag_Small` and 30
    `Item_DekuSeed`, or `Item_Quiver_Small` and 30 `Item_Arrow_Normal`.
  - **`--start-hearts N`** (1 to 20): the list's own two sets on `PlayerStatus`, `Life` and `MaxLife` (12
    each, 4 per heart), get the new value. **`--start-rupees N`** (0 to what the new file's wallets hold; the
    small wallet: 200): one more `SeqOneShotSetGameDataInt` node, a copy of the list's `Life` node, sets
    `PlayerStatus.CurrentRupee` (found by its name's hash among the 41 fields of `PlayerStatus`).
  - **Not possible: a chest open from the start.** A placement's saved flag is an entry of `Bool64bitKey` in
    `GameData/GameDataList` with only `Hash`, `ResetTypeValue`, `SaveFileIndex` (2,424 also `ExtraByte`): no
    default value to change, and no node of the new-file sequence sets a flag by its 64-bit number.
- **A first weapon placed alone gives its bag** (part 9's find: a Fairy Bow alone in a pot came without its
  quiver). `Item_Range_SlingShot` or `Item_Range_Bow` alone on a freestanding item, a rock, a bush, a pot or
  a Gold Skulltula is now built as its turning item of one level (`LONE_WEAPON_KINDS`;
  `tools/turn_items.py` takes a family of one level): it gives what a chest gives with the weapon when it is
  picked up, has no next level and no drop part, and removes itself once Link owns the weapon. The weapon
  alone and its family in one build is refused (the same item on two checks).
- **A dungeon's small key, boss key, map or compass from a person and from a Deku Scrub**
  (`KEY_GIVEN_KINDS`): the version a chest holds is handed over as any item, and the step the chests' own
  event runs follows the get (`GameDataActor.EventTriggerAddOrSubGameDataInt` + 1 on
  `DungeonInfo.<dungeon>.SmallKeyNum`, or `EventTriggerSetGameDataBool` on `IsGetBossKey` / `IsGetMap` /
  `IsGetCompass`): in the giver's own flow behind its call of the get (`gift_edit`, `after`), in the scrub
  flow behind a successful buy, where a first weapon's bag is added (`scrub_flow_edit`, `after`). Refused on
  a cutscene gift and a song for now.
- **Left out of this round: the same on a shop shelf.** A shelf is not an event. Its own AI would have to
  count the key, and that AI's "sold out" side runs again in every state of the shelf (it only hides the
  model and marks the placement, both harmless twice), so a count there needs a guard that holds exactly
  once; and the shop version would have to be built from an item of ours. Proposed as its own small part.
- **A stone or a Medallion from a person, a cutscene gift, a scrub and a shelf** already built (part 7's
  work); they are in this round's build to be seen in game.
- **`tests/kokiri_neighbours_check.py`** (new; a row of `STEPS` and of `README.md`): four builds read back,
  three refusals, and the facts above from the game's files. `tests/start_state_check.py`: the three items
  it expected refused are accepted now; it checks the new refusals instead.
- **Tests:** the full run (`tests/run_all.py`): 27 of 30 passed; the three that failed held expectations
  this part changes, and pass with them updated: `tests/dungeon_keys_check.py` and `tests/boss_check.py`
  (a key on a scrub is no longer refused; a cutscene gift's refusal has new words; a shelf's refusal is
  checked instead) and `tests/forest_temple_every_spot_check.py` (the Fairy Slingshot alone in a Forest
  Temple pot is now the version that gives its bag).

### Phase 1, part 9: in-game results, two fixes, and decision 46
The user's answers (new file, the debug-menu warp, adult):
- **The named key in the temple** (the first room's chest and a lobby pot): "(Forest Temple)" in green, the
  next locked door opened with it, **no key count on screen**. The user's choice: "keep name, no count".
  **Decision 46:** `Item_Dungeon_SmallKey@<dungeon>` is the named key in its own dungeon too (`+name` is still
  read and means the same); `tests/dungeon_keys_check.py`, `tests/forest_temple_every_spot_check.py` and
  `tests/forest_temple_loose_ends_check.py` expect it.
- **The Bow's big chest:** a small chest appeared in its place and gave the Gold Scale; the door opened. Good.
- **The map's big chest:** a small chest gave the bigger Bomb Bag, **but it played the big chest's opening.**
  Found: its opening event `ForesetTemple_GetMap` was kept (it is only the chest's usual opening, with no
  message), and that usual opening is the big chest's (`Dm_SY_Treasurebox`). **Fixed:** on a big chest made
  small, the events that are only the big chest's opening (`BIG_OPENING_EVENTS`: the map's and the compass's)
  go, so the small chest plays its own; any other kept event on such a chest stops the build. **Retest in game: good** (the small chest's opening,
  the bigger Bomb Bag).
- **Saria's cutscene:** the Longshot floated down (not the Medallion) and the window said Longshot. Good.
- **Save and reload:** good.
- **The Fairy Bow from a lobby pot came without its quiver.** Found: a first weapon placed alone (the Fairy Bow,
  the Fairy Slingshot) on the ground, in a pot, a rock or a bush, or on a Gold Skulltula is built as a plain
  one-time or ground version, which gives no bag; only chests (the game's own chest module), gifts and scrubs
  (`SCRUB_COMPANIONS`) and the families' turning items add it. Not part of part 9: proposed for part 10 with the
  starting state's Fairy Bow and Fairy Slingshot.
- **Tests:** the scripts the fixes touch (`forest_temple_loose_ends_check`, `forest_temple_every_spot_check`,
  `dungeon_keys_check`, `forest_temple_keys_check`, `chest_check`, `three_chest_check`, `boss_check`) pass.

### Phase 1, part 9: the Forest Temple's loose ends (to test in game)
Branch `claude/forest-temple-loose-ends`. Parts 9 to 11 were added to phase 1 today (the user: "id like to
finish these in Phase 1 if possible"; decision 45). Test build and checklist: `out\TEST_CHECKLIST.md`.

- **A family where the Medallion is given** (`FT_FOREST_MEDALLION_GIFT=First>Second[>Third]`): the builder
  refused it ("event Event13 is not the call that gives ..."): its family code for gifts only knew the shared
  get flow (`Dm_SY_GetInEvent`), and Saria's cutscene gives with the get window itself
  (`GetPouchContent<GetPouchContentByActorName>`). Now every level of such a gift is given that way, with the
  game's inventory question in front (`gift_pair_edit`).
- **What floats down in Saria's cutscene is what it gives.** Read from `Dm_Awake_Forest_Get`: the Medallion is
  an actor of the cutscene named after the item, `Item_Medal_Forest`, used by three steps before the get:
  `Event39` (its size), `Event15` (bound to the locator `Dm_Locator` that floats down) and `Event20` (its
  glitter). The game shows one of several items that way itself: `Dm_LostWood_0040` (the target practice)
  asks whether Link has the bigger seed bag and then binds one of two bag actors. So now (`reward_shown_edit`,
  read back by `reward_shown_check`):
  - one item: the actor is renamed to the item (as Saria's bridge cutscene does). A rupee shows the version a
    chest holds (`TBox_Rupee_Red`), an ocarina its held-up version;
  - a family: one actor per level, and the game's question in front of each run of those steps, so the
    Longshot floats down when the cutscene gives the Longshot;
  - an item the cutscene cannot show (a Piece of Heart or a Heart Container: no actor of that kind): the three
    steps are left out, so nothing floats down instead of the Medallion.
  Every gift whose cutscene shows its item as an actor of its own gets the same (today only the Medallion's
  in the areas with data).
- **A family in a big chest:** the game has no big checking chest, and the checking chest's AI cannot drive a
  big one: it asks for the sensor body `GeneralSensor/Sensor`, which the big chest's physics does not have (it
  has `GeneralSensor/EnemyCheck`, and its own AI, `Obj_TBox_A_02.root`). So a big chest that holds a family
  becomes the checking chest of its small twin (`BIG_CHEST`): a small chest at the same spot, which appears the
  same way (both AIs play `SpawnMagic` and `SpawnFall`). Pairs go into the game's checking chest, three levels
  into our three-level chest. `tests/chest_check.py`, `tests/families_check.py` and
  `tests/three_chest_check.py` said "refused in a big chest"; they now check the swap.
- **The dungeon's name on a key in its own dungeon:** `Item_Dungeon_SmallKey@ForestTemple+name` on a check of
  the Forest Temple is now the named key (the one every key outside its dungeon is, counted by our own step)
  instead of the game's own key. Without `+name` it is still the game's key (decision 41). The round settles
  which is kept: the named key may not show the count on screen.
- **`tests/forest_temple_loose_ends_check.py`** (new; a row of `STEPS` and of `README.md`): three builds read
  back (the round's build, a Piece of Heart and a red rupee on the Medallion's check), and from the game's
  files the cutscene's three steps, the Lost Woods pattern and the big chest's missing sensor.
- `data/world/ForestTemple.json`: the Medallion's note says what floats down now.
- **Tests:** `run_tests.bat` (all 29 scripts): 28 passed, `three_chest_check` failed on its old "refused in a
  big chest" line; changed to the swap, it passes on its own.

### The area checklist template (phase 1 "alongside"; docs only, no game changes)
- **`docs/AREA_CHECKLIST_TEMPLATE.md`** (new): the shape of every area's in-game test list, so each area is
  tested the same way.
  - **Before the list:** the area's every-spot build script and `run_tests.bat` pass; the test build carries
    the standing fixes; a gold rupee only when something is sold; what Link needs is given at the start.
  - **What goes on it, in order (D27):** each check kind and form the area has that has not passed in an
    earlier area; every unusual spot (appears from a switch, a fight or an event; names no contents; a special
    room; given by a cutscene), each with what the game's files show; the area's own settings and cutscenes;
    samples for the rest, loose rupees and hearts included; save and reload last. A longer area gets one list
    per day.
  - **How it is written:** the remake's names, grouped by age and along the way through the area, one line per
    check (where, what Link should get, what should happen), the debug-menu warp for dungeons, skippable steps
    marked. No "does it load" steps.
  - **Two blocks to copy** into `out\TEST_CHECKLIST.md` and `out\TEST_ANSWERS.md`, the shape the last rounds
    used.
  - **After the answers:** what goes into `CHANGELOG.md`, the area's data (`randomizable` and its note, then
    `tools/build_db.py`), the template's own table, and the roadmap.
  - **Check kinds already passed in game:** a table of every kind and form passed so far, where and when, so
    a later area tests only what is new; and what is not proven yet (a family on a shop shelf or in a big
    chest, a key on a gift, scrub or shelf, a stone or Medallion from a person).
- `docs/ROADMAP.md`: phase 1's "alongside" pieces are both done; the testing section points to the template
  and says the gold rupee is only for builds that sell something. `README.md`: a line for the template.

### Phase 1: the Forest Temple's unusual chests passed in game (the every-spot part)
The user's answers to the checklist of 2026-11-24 (new file, the debug-menu warp, adult): every line "good".

- **Joelle's chest** (`FT_JOELLE_CHEST`): appeared after Joelle was beaten and held the Hover Boots.
- **Beth's chest** (`FT_BETH_CHEST`): appeared after Beth was beaten and held the Lens of Truth; nothing odd
  when it was opened (the game's own opening for the compass is kept on this chest).
- **The falling ceiling room's chest** (`FT_FALLING_CEILING_ROOM_CHEST`, the refill chest that names no item):
  held the Megaton Hammer and opened like any small chest.
- **The Floormaster's chest** (`FT_FLOORMASTER_CHEST`): appeared after the Floormaster was beaten and held the
  Iron Boots.
- **Save and reload:** the opened chests stayed open and the items were kept.
- **Recorded:** the four chests are "changed in game" in `data/world/ForestTemple.json` (21 of the temple's 47
  checks now; the other 26 are covered by `tests/forest_temple_every_spot_check.py`, by decision 27), and
  `tests/forest_temple_check.py` expects 21.

### The cutscene list, and the reader takes timeline files (phase 1 "alongside"; no game changes)
Branch `claude/cutscene-list-57492a`. Nothing in the game's folder or in `out` was touched; nothing to test in
game.

- **The reader (`formats/evfl.py`) now reads and writes every event flow file: 914 of 914 byte for byte**
  (before: 650; 264 refused). The 264 were 261 timeline files and 3 files with entry point variables
  (`Dm_SY_Get`, `Dm_SY_Ocarina`, `LinkSleepInBed`).
  - **Timelines** (worked out from the files; not in the public documentation for this version): one `TLIN`
    block per file with a length in frames, actors, clips ("this actor does this from frame A for N frames",
    on a track), triggers (each clip's start and end in time order), cuts (the frame each camera cut starts
    at) and the names of its sub-timelines (`<name>_Effect`, `<name>_Env`). Details: README, "Timelines".
  - **60 frames are one second:** 12 movie cutscenes have a timeline beside their video file, and for 11 it
    is as long as the video to within 2% (`Dm_Kokiri_0095`: 7040 frames, video 117.33 s; the exception is
    `Dm_FinalBattle_0002`, 1732 frames against 33.0 s).
  - **A changed timeline can be written:** `evfl.timeline_triggers` gives exactly the trigger list of all 261
    files; `dumps_checked` and `differences` cover timelines. Not tried in game.
  - **Entry point variables** (`EntryPoint.variables`): a name list and 16 bytes per variable in place of the
    entry point's 24 empty bytes; the game has five, all read.
  - The round-trip test now shows `evfl 914 identical`. Tests that skipped "the flows the reader refuses"
    still pass (a timeline file simply has no flowchart).
- **The list: `docs/CUTSCENES.md` (to read) and `data/cutscenes.json` (the same as data),** made by the new
  `tools/cutscene_list.py` from the game's files, for the whole game, one section per area with the game's own
  area names. 12 seconds to make.
  - **319 story cutscenes** (events named `Dm_...`): 83 timelines, 25 movies, 210 flowcharts, 1 with no file.
    The timelines and movies run **117 minutes** in all (the longest: the credits 5 min 08 s, `Dm_Kokiri_0030`
    3 min 29 s, `Dm_Kokiri_0140` 3 min 28 s).
  - **217 lead-in events:** not cutscene files, they run a story cutscene as a step. **363 small scenes:**
    flowchart events placed in a map (a door opens, a chest appears). **79 system scenes** (`Dm_SY_...`).
  - For each: its files, kind, length, what starts it and when, what it sets (flags, challenge steps, time of
    day) and gives (items, with the game's names), what it runs next and where it sends Link, whether the game
    lets it be skipped, which logic graphs and flows ask whether it has been played, and its check
    (`LW_SARIA_GIFT`, `Song from Saria`, `FT Forest Medallion`...).
  - All 480 `Dm_` flow names are accounted for: 473 in an entry, 7 that have no event of their own (run as
    steps of other flows: `Dm_SY_GetInEvent`, `Dm_SY_ShopGet`, four ocarina files, `Dm_LostWood_0030`).
- **Found while building it (all in the document):**
  - **A timeline cannot set a flag or give an item.** None of the 261 files has such a step (94 kinds of step:
    camera, animation, voice, light, effect, rumble, weather; five timelines set the time of day). What a
    timeline cutscene "sets" is set by the flowchart that runs it: e.g. `KokiriForest_ArriveLostWood` runs
    `Dm_Kokiri_0150` (Saria on the bridge, 1 min 42 s), then `Dm_Kokiri_0155` (the ocarina), sets
    `HyruleField_ChangeENV` and sends Link to Hyrule Field.
  - **Where the start condition is:** an `EventRequestActor` in the map only names the event; the logic graph
    of its group (`Logic/*.ainb`, also inside nested modules) says when: e.g. Saria's Song: "Link in
    Area_0b11, which is there while `DoorOfTime_IsAfter_Step01_Exp` is set and `Dm_MelodyGet_Saria` is not
    played". The same graphs set flags when the event ends (the Forest Temple's ice: on EventFinish
    `ForestTemple_Room14_MeltedIce`). Of the 740 requests placed in the maps for listed events, 698 have their
    condition read out; 40 have a graph that gives them no trigger of their own (another actor asks for the
    event), 2 have no graph.
  - **Other starters:** actor parameter files (Link's house door names `Dm_Kokiri_0045` as its open event;
    each boss names its "die" event: Phantom Ganon's runs `Dm_ForestTemple_BossOut`) and the game's sequence
    graph (`Sequence/Opening.module` asks for the opening). What starts a story cutscene is found for 318 of
    319 (not `Dm_MelodyGet_Manegement`, which has no file).
  - **Only 8 cutscenes have the game's own skip turned off** (`DisableSkip` in their settings list): the
    opening movie `Dm_Kokiri_0000`, the title movies and one credits movie. Every other one can be skipped by
    the game itself.
  - **66 events of the list are asked about later** ("has it been played?") by a logic graph or a flow, 52 of
    them story cutscenes: removing or skipping one of those has to keep the answer true.
  - The forest: Kokiri Forest 22 story cutscenes (10 timelines and movies, 17 min 50 s), Great Deku Tree 5
    (1 min 01 s), Lost Woods 7 (1 min 22 s), Sacred Grove 3 (flowcharts), Forest Temple 18 (the boss's two
    timelines, 2 min 14 s) and 19 small scenes.
- **Not known (the files don't say):**
  - how long a flowchart cutscene runs: only the frames of its wait steps are counted ("waits", the least it
    can take), and that those are 60 a second too is assumed, not checked in game;
  - what the game's own skip keeps of a skipped cutscene (flags, items, the "played" mark): to try in game
    with the first area's cutscene work;
  - the condition of an NPC's own events (talking to it): it is in the NPC's program, not in a file read here.
- **Files:** `formats/evfl.py` (timelines, entry point variables), `tools/cutscene_list.py` (new),
  `data/cutscenes.json` and `docs/CUTSCENES.md` (new, made by the tool), `tests/cutscene_list_check.py` (new,
  35 lines of checks, in `run_tests.bat` through `tests/run_all.py`), README ("Timelines", "The cutscene
  list", the status table), `docs/ROADMAP.md` and `docs/ROADMAP_DECISIONS.md` (the list is done).
- **Tests:** `run_tests.bat` (all 28 scripts): all 27 checks passed; the round-trip report: `evfl 914
  identical` (before: 650 identical, 264 errors); the other formats as before (`byml 5 differs`).

## 2026-11-24

### Phase 1: the Forest Temple's every-spot build script, and its unusual spots (passed in game 2026-11-25)
Test build and checklist: `out\TEST_CHECKLIST.md`. Decision 27 as changed today: in game each check kind once
plus every unusual spot; a build script for every spot.

- **`tests/forest_temple_every_spot_check.py`** (new, 16 checks; a row of `STEPS` in `tests/run_all.py`): one
  build puts a different item on each of the temple's 47 checks (12 chests, 28 pots, 5 Gold Skulltulas, the
  boss's heart, the Medallion's cutscene) and every one is read back from the mod folder. Each chest holds its
  item, each pot drops the one-time version of its item and names no drop table any more, each Gold Skulltula
  drops the token-built version, the boss's heart is the ground version, the Medallion's cutscene gives its
  item in the file the game loads. The 46 objects hold 46 different things: 12 are the game's own actors, 34
  are new and each was written as a pack with its row in the actor table. The other 3,167 objects of the two
  maps are as the game has them, and every one of the build's 81 files has its entry in the resource size
  table. No builder change was needed: all 47 built at the first try.
- **Why `FT_FALLING_CEILING_ROOM_CHEST` shows no contents:** its map entry names no item, as 9 of the game's 235
  chests (the others: 3 in the Gerudo Training Ground, 4 in Ganon's Castle, 1 in the Spirit Temple). Such a
  chest gives from the chest's own drop table (`Drop/DropSubTable/Obj_TBox`, one entry of the type
  `MostDepletedResource`): the supply Link is shortest of among magic, arrows or Deku Seeds, Deku Nuts and
  bombs. The chest's default drop actor is `Obj_Rupee_Green`. So it is a refill chest, and the builder gives
  it an item like any chest.
- **Which chests only appear** (read from each room's logic module): six of the 12. After a fight: the first
  Stalfos room's, the Floormaster's (both through the module `Gimmick_TreasureBoxAppear_Any_Magic`) and the
  Bow's. After a Poe is beaten: Joelle's (`ForestTemple_DefeatJoe`, the same module as the first Stalfos
  room's) and Beth's (`ForestTemple_DefeatBeth`, through `Gimmick_TreasureBoxAppear_02_Any_Any_Magic`, which
  no other chest of the temple uses). From an eye switch: the block room's. The first Stalfos room's, the
  Bow's and the block room's passed in game in part 3.
- **Nothing unusual in the files** about the basement's chest (a small chest that names its item), the well's
  chest (a small chest whose room logic only notes that it was opened, as the first room's) and the three Gold
  Skulltulas not yet tried (all five run the same module, `Gimmick_AllDay_Skulltula`): no in-game test.
- **In game, to test** (unusual spots not tried yet): the falling ceiling room's chest (names nothing),
  Joelle's and Beth's chests (appear after a Poe), and the Floormaster's chest (appears after a fight).

### D27 changed: in game, each check kind once plus the unusual spots (no game changes)
The user: "is this excessive? Testing EVERY spot is going to take a long time. We already tested a bunch and
they all work." Decided: "each check kind once plus unusual spots in game, a build script for every spot,
samples for the rest" (`docs/ROADMAP_DECISIONS.md` D27, `docs/ROADMAP.md` "What an area is done means", rule 5).
- **In game:** each check kind once, in each of its forms (unless it passed in an earlier area), plus every
  unusual spot: one that appears from a switch, a fight or an event, whose contents can't be read from the
  game's files, that sits in a special room, or that a cutscene gives. Samples for the rest.
- **A build script for every spot:** each area's test script builds an item onto every one of its spots and
  reads each one back. It needs no play time.
- Full seeds (phase 6) touch every check; anything broken found then is a bug fix.
- **Where the Forest Temple stands:** every chest form it has passed in game (small, small without a baked
  shadow, big, big without a shadow, the boss key's), and the Gold Skulltula. Not tried: 6 of its 12 chests
  and 3 of its 5 Gold Skulltulas. The one unusual spot among them is `FT_FALLING_CEILING_ROOM_CHEST`, whose
  contents the data could not read from the game's files. Beth's and Joelle's chests may appear after their
  Poe is beaten (not checked in the remake's files). No build script for every spot yet.

### Phase 1, part 7: boss key, boss door, boss heart and the Medallion (passed in game 2026-11-24)
Test build and checklist: `out\TEST_CHECKLIST.md`.

**In game (user, 2026-11-24): every line of the checklist "good".**
- **Mido's house:** the 2nd chest "You found the dungeon map! (Forest Temple)" and the 3rd "You found the
  compass! (Forest Temple)", the name in green. In the temple as a child the Map page had the map and the
  compass in their slots and the chests marked.
- **House of the Know-It-All Brothers:** the boss key from a pot lay on the floor properly and said "You found
  the boss key! (Forest Temple)" with the name in green. The Forest Medallion from the other pot was picked up
  and shown without a freeze; **it did not spin on the floor.**
- **In the temple as an adult:** the first room's chest gave the Fairy Bow; the boss key's chest held the
  Megaton Hammer and opened without Navi's message; **the boss door opened with the boss key from the pot.**
- **The boss:** the last cutscene played to its end with the Boomerang in the Heart Container's place (the
  unknown is answered: the cutscene does not stop); the Boomerang lay there and was picked up; Saria's cutscene
  played and its window said "You got a silver scale!". After save and reload both were kept and the temple
  was done.
- **As expected, and kept:** in Saria's cutscene the Forest Medallion still floats down above Link while the
  window names the other item (the user's screenshot). It is an actor of the cutscene, not the item given.
- **Open (the user's note): the Key Items tab, the one with the stones and Medallions, was "???"** after the
  Medallion from the pot. What the files show: "???" is the pause menu's text for a tab that is not opened yet
  (`LayoutMsg/MenuOverlay_00`, label `Unopened`), and the Key Items tab is opened by the Great Deku Tree's
  cutscene when he gives the Kokiri Emerald (`Dm_Kokiri_0130`, step `Event52`:
  `UISystemActor.EventOpenPerformanceImportantMenu`; its text is "Kokiri Emerald added to Key Items"). So a
  Medallion found before that cutscene sits in a tab that is still closed. **Not found: what the game keeps in
  the save file for an opened tab.** Two candidates to try in game: the saved yes/no
  `HavePlayedEvent.Dm_Kokiri_0130` (the game keeps one for each of its 3,647 events; setting it may also skip
  the Deku Tree's cutscene), or simply owning a Spiritual Stone.

**The Key Items tab, second round in game (user, 2026-11-24; the user: "key items tab first"):** a build with
no builder change, the Forest Medallion in a pot and the Kokiri Emerald and the Goron's Ruby in Mido's chests.
- Before anything: the tab is "???". After the Forest Medallion: still "???".
- **After the Kokiri Emerald from the chest: "tab is there, emerald and medallion is there."** The chest showed
  the Kokiri Emerald as the game does. The Goron's Ruby joined them; the same after save and reload; as an
  adult (debug menu) the tab is open with the Medallion on it.
- **So: owning a Spiritual Stone opens the tab, no cutscene and no flag is needed,** and a Medallion found
  first is not lost: it shows as soon as a stone is owned. What is left: a Medallion alone does not open it.
- Read from the files meanwhile: no saved flag for the tab under any likely name (about 43,000 tried against
  the game's flag list); the game's program does not name the Deku Tree's cutscene, and does hold a list of
  the three stones and six Medallions; the pause menu's table (`UI/Pouch/PouchTable`) lists the Medallions with
  the mark `IsUsableAdult` and the stones with no mark.
- **Third round in game (user, 2026-11-24): the age mark is not it.** An experiment (`--fix medallions_try`,
  removed again): the Fire Medallion's row marked `IsUsableChild` instead of `IsUsableAdult`, the Forest
  Medallion's with no mark. After each of them the tab was still "???"; after the Kokiri Emerald it opened
  with both Medallions on it, also as an adult.
- **The user: "is there a way to force key items open without any medals/stones?"** Read from the game's
  program (`image.bin`, read only; the one place that uses the text label `Unopened`): the tab bar walks the
  rows of the pause menu table's `StoneArray` and asks, for each row, whether Link owns its first item
  (`Actor[0].ActorShort`); any one owned opens the tab. `MedalArray` is not looked at, which is why a
  Medallion alone never opens it. The page's own code asks the same of `StoneArray`.
- **Fourth round in game (user, 2026-11-24): passed. `--fix key_items_tab_open`** (`KEY_ITEMS_ALWAYS` in
  `tools/build_mod.py`): two rows more in `StoneArray`, for the two green tunics, which the game's own
  new-file list gives every file. The rows name no model and no place on the page (as the rows of
  `NoDisplayArray` name none). On a new file the tab was named "Key Items" and its page was empty, with
  nothing odd when moving the cursor; the other tabs as usual; the Forest Medallion from a chest was on the
  page in its place and could be selected, then the Kokiri Emerald with it; the same after save and reload
  and as an adult (debug menu). **Test:** `tests/key_items_tab_check.py` (new, 13 checks; a row of `STEPS` in
  `tests/run_all.py`).
- **Decision 43 (the user, 2026-11-24): the Key Items tab is open from the start in every build,** test
  builds included (`docs/ROADMAP_DECISIONS.md`).
- **Seventh round in game (user, 2026-11-24): passed, every line "good".** On a new file the Key Items tab is
  open and its page empty; the Spirit Medallion alone is shown in its place and the cursor goes to it and
  away; with all nine owned every one is shown in its own place, the cursor moves over all of them without
  getting stuck, "Details" is right on a stone and on the Medallions (Spirit and Shadow among them), the other
  tabs are as usual; the save screen shows all nine and the page is the same after loading; the same as an
  adult (debug menu). The Light Medallion's name is gray.
- **Sixth round in game (user, 2026-11-24): the colours are right; two Medallions were missing on the Key
  Items page.** All eight names had their colour (green, green, orange, purple in Mido's chests; red, red from
  the pots; blue, blue in Saria's house), the Light Medallion's was plain and it turns, and only the name was
  coloured. **Wrong:** on the Key Items page the Spirit and the Shadow Medallion were not shown; the cursor
  could go to their places and open "Details", but could not leave them without closing the menu. The save
  screen's small picture showed all nine.
  - **Why (my mistake in `key_items_tab_open`):** the page has nine places and fills them in the order of
    the table's rows, the stones' list first, then the Medallions'. The two tunic rows stood right behind the
    three stones, so they took two of the nine places and the last two Medallions of the list (Shadow, Spirit)
    got none. The fourth round had only one Medallion and one stone, so it did not show.
  - **Corrected (passed in game, above):** the nine real rows come first. The stones' list is now the three stones,
    the six Medallions' rows as the game has them, and then the two tunic rows; the Medallions' own list keeps
    a row for each Medallion that names only the item, because the game's program asks that list whether
    Link owns a Medallion.
- **The Light Medallion's name is gray** (the user, 2026-11-24: "Light Medallion can get gray i suppose since
  Yellow isnt an option"): the game's own colour number 1, as the Bottom of the Well's keys. The name on the
  Key Items page stays plain (the user: "no, leave plain").
- **The stones' and Medallions' names in their temple's colour** (the user, 2026-11-24: "id like to add the
  color of the keys to the medallions/stones names. Kokiri and Forest Green, Goron and Fire red, Zora and
  Water Blue, Spirit Orange, Shadow Purple"). Built, to test in game; decision 44. A placed stone or Medallion
  has its name coloured in the get window's message ("You were entrusted with the Forest Medallion!"), with
  the colours of decision 40: Kokiri Emerald and Forest Medallion green, Goron Ruby and Fire Medallion red,
  Zora Sapphire and Water Medallion blue, Spirit Medallion orange, Shadow Medallion purple
  (`REWARD_TEMPLE`, `reward_name_lines`, `change_messages` in `tools/build_mod.py`). The Light Medallion has no
  temple (first left plain, then gray: above). Only the message is changed: the name on the Key Items page and in hints stays
  plain. Each language keeps its own text and the name is coloured where it stands in it: 15 of the 16
  languages; Japanese is left as it is (its reading marks are tied to the name's first character).
  **Test:** `tests/reward_names_check.py` (new, 10 checks; a row of `STEPS` in `tests/run_all.py`).
- **Fifth round in game (user, 2026-11-24): the stones and Medallions turn.** The Forest Medallion and the
  Kokiri Emerald from Mido's chests turn in Link's hands and sit right; the Fire Medallion and the Goron Ruby
  from the pots turn on the floor at a good height and in Link's hands; the Zora Sapphire as a loose item in
  Saria's house too; all five on the Key Items page as before, also after save and reload. **Not tried:**
  Saria's cutscene with the changed Medallion (none of the 11 cutscenes is seen yet).
- **The user's note, fourth round: "medallions and stones still dont spin when link holds them up".** Built
  and passed in game (above). Why they stood still: the game only gives them in cutscenes, so their nine actors have no
  animation (`ASRef` names an empty placeholder, `AS/DemoDummy.root.asb`, 231 bytes with no command, and the
  stones' `AS/Dummy.root.asb` is not even a file; `AnimationRef` is an empty list; no `ASInfoRef`). Their
  models do have the two bones the game's item spin turns and lifts (`Root`, `Skl_Root`).
  **A placed stone or Medallion now gets what the Boomerang has,** as the songs' harp did: the get-demo
  animation settings (nothing plays by itself), the items' shared animation file (`AS/Item_Common.root.asb`:
  `Rotate_GetDemo` in Link's hands, `Rotate_Obj` on the ground) and a list of only the game's
  `Item_Common_Animation` (`reward_spin_pack`, `reward_spin_rows` in `tools/build_mod.py`). The actor itself
  is changed, so its versions on the ground and from a Gold Skulltula turn too. Only the ones a build places
  are changed.
  **Not known:** how the changed actor looks in the 11 cutscenes that show these actors (the five
  `Dm_Awake_*_Get`, `Dm_Kokiri_0130`, `Dm_DeathMtTrail_0025`, `Dm_InsideJabu_Jabu_0030`,
  `Dm_ZoraFountain_0030`, `Dm_SageRoom_0005`, `Dm_InsideGanonCastle_0000`). They move the actor by a locator
  and its old animation file was empty, so nothing should differ; each is to be looked at with its area. A
  stone or Medallion given as a gift is now held up like other items instead of shown in the window (not
  tested). **Test:** `tests/reward_spin_check.py` (new, 14 checks; a row of `STEPS` in `tests/run_all.py`).
- **A size rule for the pause menu's table** (`tools/sizes.py`, `game__ui__PouchTable`): the game has one file
  of the type, so the rule charges 1024 for each row of `StoneArray` and for each item of a row (far more than
  an element can cost), spreads the rest evenly, and gives the game's entry for the game's file
  (`tests/size_check.py`: OK).

- **The boss key anywhere** (`tools/dungeon_items.py`, new): `CHECK_ID=Item_Dungeon_BossKey@ForestTemple`. What
  was found: the boss key, the map and the compass are yes/no fields of the dungeon's saved record
  (`DungeonInfo.<dungeon>.IsGetBossKey`, `IsGetMap`, `IsGetCompass`); the items themselves are "not put in the
  inventory", and what sets the field is the chests' shared opening event (`Dm_SY_Treasurebox`:
  `EventGetDungeonBossKey` and its three siblings), for the dungeon Link is in. So:
  - **in a chest of its own dungeon** it is the game's own item (the builder decides by the check's map);
  - **on a pot, rock, bush, freestanding item or Gold Skulltula**, in the dungeon or outside, it is a version
    of ours whose AI sets the dungeon's field when it is picked up (`OneShotSetGameDataBool`, the step the
    Gerudo Fortress keys set their own flag with);
  - **in a chest outside its dungeon** the chest's opening event gets a step after it that sets the field
    (`GameDataActor.EventTriggerSetGameDataBool`), as a small key's chest adds 1.
  Every version says the dungeon's name in the dungeon's colour: "You found the boss key! (Forest Temple)".
- **The map and the compass the same way** (`Item_Dungeon_Map@ForestTemple`, `Item_Dungeon_Compass@...`): they
  are built exactly as the boss key is. **A flaw this closes:** the builder used to accept a boss key, a map or
  a compass on a pot, which gave an item that set nothing when picked up. Without its dungeon named, one of
  the three is now only accepted on a chest of a dungeon.
- **Another item in the boss key's chest:** its own opening event (`ForesetTemple_GetBossKey`: the usual
  opening, then a message from Navi about the boss key) is removed with the boss key, as the Bow chest's was.
- **The boss door** needs no change: its lock (`Obj_DoorChainLock_A_02`) opens with the dungeon's field. **Start
  with the boss key:** `--start-flag DungeonInfo.ForestTemple.IsGetBossKey=true` (part 6's start flags).
- **The boss's heart:** it is a placed `Obj_Heart_Container` that the boss room's logic brings in once the boss
  is beaten, by its place in the map, so another item put there is brought in the same way. The boss's last
  cutscene (`Dm_ForestTemple_BossOut`) shows the Heart Container coming down, by the actor's name; with another
  item there it plays to its end (in game, above).
- **The Medallion:** the cutscene `Dm_Awake_Forest_Get` hands it over with one step (the get window and the
  item), now in the temple's data, so `FT_FOREST_MEDALLION_GIFT=<item>` gives another item there, and
  `Item_Medal_Forest` can be put on another check. The medallion that floats down in the cutscene stays.
  A family on this check is not supported yet.
- **The file the game loads:** for 13 event flows the game loads `<name>.110.bfevfl`, not `<name>.bfevfl`
  (`Event/EventFlow/EventFlowFileEntry`: the five Medallion cutscenes, `Dm_HrlCastle_0020`, `Dm_Goron_0040` and
  six more). The builder now reads and writes the file the game loads (`Output.real`); before, a change to one
  of those 13 would have gone into a file the game never opens.
- **Tests:** `tests/boss_check.py` (new, 16 checks; in `run_tests.bat`, through `tests/run_all.py`).

### `run_tests.bat` in about 2.5 minutes instead of about 16 (every test still runs)
The user: "I think we need to change how run_tests works cause I'm losing a lot of time just waiting."

- **Timed first (main at `8dadce9`, one after another): 16.3 minutes.** The slowest: `families_check.py` 6.3 min
  (38%), `ground_lift_check.py` 1.9, `roundtrip.py` 1.7, `skulltula_prog_check.py` 1.1, `one_time_check.py`
  0.9; the other 17 together 4.3.
- **`run_tests.bat` now runs every script through the new `tests/run_all.py`, 8 at a time** (the PC has 8
  cores, 16 threads), the slowest first. The scripts don't depend on each other: each reads the game files on
  its own and builds into a temporary folder of its own. It prints a line as each one finishes, then which
  failed (with the last 40 lines of its output), the round-trip test's summary, and the total time. Each
  script's whole output is in `test_logs\` (not uploaded); the round-trip report is still `report.txt`.
  `--only NAME,...` runs a few while working; `--jobs N` sets how many at once.
- **`families_check.py` starts its 26 whole builds side by side when it begins** (`build_plan()`), each in a
  folder of its own, and its last section takes their results. Alone: 70 s instead of 6 min 16 s; its output
  is byte for byte the same as before (file counts included). The checks themselves are unchanged.
- **Result: 2 min 32 s for all 23 scripts, all 22 checks passed** (17 min of work done side by side). The
  round-trip test gave its known report (5 BYML files differ, 264 event flows with timelines not read). The two
  slowest now: `ground_lift_check.py` 2 min 32 s and the round-trip 2 min 20 s.
- **A new test script now adds its row to `STEPS` in `tests/run_all.py`** instead of to `run_tests.bat`
  (CLAUDE.md and README.md say so). A `*_check.py` that is not in the list is named when the tests run
  (`logic_check`, `db_check` and `size_check` stay out on purpose, as before).

### Phase 1, part 6: start with keys, map and compass; the key count shown; the temple's name on a key (passed in game 2026-11-24)
Test build and checklist: `out\TEST_CHECKLIST.md`.

**In game (user, 2026-11-24), all seven key colours with the corrected places: passed.**
- Mido's four chests: the Shadow Temple's name purple (the colour added behind the game's list), the Spirit
  Temple's the yellowish orange (place 4), "Gerudo Proving Grounds" the darker orange (place 5), the Fire
  Temple's red. The two pots: the Bottom of the Well gray, the Water Temple blue. All "good".
- The game's own red is red again: "when fado mentioned the great deku tree it was red".
- So one colour can be added behind the game's eight, and places 6 and 7 must stay the game's.
- **Not seen:** the credits, where the two oranges change 17 headings and 115 names.

**In game (user, 2026-11-24), the look at the last changes; and what it showed about the colour list:**
- **Good:** Kokiri Forest's map at the start (by the rule), the Spirit Temple's yellowish orange, the Training
  Ground's darker orange ("Gerudo Proving Grounds").
- **Wrong:** the Bottom of the Well's name was purple, not gray, and "fire temple became the orange from
  spirit".
- **Why: places 6 and 7 of the game's list are not unused.** In the get window the game shows place 6 for
  colour number 0 and place 7 for number 1: 6 (255, 53, 25) is that window's red and 7 (133, 125, 104) its
  gray; 0 (138, 0, 0) and 1 (80, 45, 20) are their darker versions. Every test fits: the "red" and "gray" of
  the third test were places 6 and 7. With 6 recoloured orange and 7 purple, red became orange and gray
  purple, and would have wherever the game uses that pair. No text names 6 or 7 by number, which is why they
  looked free.
- **Corrected (seen in game afterwards, see above):** places 6 and 7 are the game's again and are never changed
  (`dungeon_keys.KEPT_PLACES`: 0, 1, 3, 6, 7). The colours of our own now are: **blue** place 2 (as before,
  seen in game); **purple** one place added behind the game's eight (number 8: a number past the list shows
  the list's last colour, which the fourth test showed, so one colour can be added that way); **orange** place
  4 and the **darker orange** place 5, the staff roll's two places.
- **Side effect, larger than before:** in a build with a Spirit Temple key outside its dungeon the 17 headings
  of the credits that use place 4 are orange, and with a Training Ground key the 115 names that use place 5
  are the darker orange.
- `run_tests.bat` was not run on this change (the user: do not run another); `tests/dungeon_keys_check.py`
  passes (21 checks).

**The last two places with small keys (the user, 2026-11-24):**
- **The user:** only eight places use small keys: the Forest, Fire, Water, Shadow and Spirit Temples, the
  Gerudo Training Ground ("different orange?"), the Bottom of the Well ("gray?") and Ganon's Castle (colour not
  important). The game's maps agree: those eight have small-key doors (`Obj_DoorChainLock_A_01`; Ganon's Castle
  has one such door and one small key placed), and Gerudo Fortress has keys of its own kind.
- **Bottom of the Well: gray**, the game's own place 1 (named "Gray" in the list; it looked gray in the third
  test), unchanged.
- **Gerudo Training Ground: a second, darker orange** (`dark-orange`, 185, 85, 15). The only places left in the
  game's list are the staff roll's two, so it takes place 4 (255, 253, 198, half see-through), recoloured and
  made solid. **Side effect:** the 17 headings of the staff roll that use place 4 are that orange in a build
  with a Training Ground key outside it. Nothing else in any language uses place 4.
- The key's text uses the game's own name of the place: "Small Key (Gerudo Proving Grounds)".
- **Tests:** `tests/dungeon_keys_check.py` (21 checks): the seven places each have a colour of their own, and
  the game's places 0, 1, 3 and 5 are never changed.

**Two rules from the user (2026-11-24), built after the fifth test:**
- **Every key says its dungeon's name** (D41). `CHECK_ID=Item_Dungeon_SmallKey@ForestTemple` on a check outside
  the Forest Temple is now always the key with the temple's name in its messages; `...@ForestTemple+name`, the
  option it began as, is still read and means the same (`tools/dungeon_keys.py`: `parse`). On a check of its
  own dungeon the key is still the game's own small key, which says "You found a small key!" and shows the
  count: the game's key has one text for all dungeons.
- **Kokiri Forest's map is open from the start** (D42). A build with `--fix skippable_opening` starts a new file
  with `IsVisitLocation.KokiriForest` set (`tools/build_mod.py`: `OPENING_VISITED`), unless the build gives that
  flag itself. In the second test this flag opened the map right at the start.
- **More colours for the other dungeons** (the user's question): the game's list has eight places and cannot be
  made longer (fourth test). Three of them are used by no text and are now blue, orange and purple; the other
  five are used by the game's own texts (0 red, 1 a dark brown for Navi's thoughts, 3 green, 4 and 5 the staff
  roll's pale colours). So the other eight dungeons can share the five colours, or take the staff roll's two
  places (the credits' text would change colour with them). Not decided.
- **Tests:** `tests/dungeon_keys_check.py` (the sample's keys carry the name without `+name`),
  `tests/start_state_check.py` (the opening fix marks Kokiri Forest; a flag given for it is kept).

**In game (user, 2026-11-24), fifth test build:**
- **Blue and purple work, in the shades the user wants:** the Water Temple's name was blue (place 2 of the
  game's list recoloured) and the Shadow Temple's purple (place 7). Fire red and Forest green as before.
- **Orange:** the game's own place 6 (255, 53, 25) was "darker than last time"; the user wants "a more
  yellowish orange". So the fourth test's orange was ours (215, 110, 0): a number past the list seems to give
  the list's last colour.
- **Nothing out of place was seen** in blue or purple elsewhere ("didn't test it all").

**After the fifth test (2026-11-24):** orange is place 6 recoloured to (225, 130, 0), the same way as blue and
purple (`dungeon_keys.OUR_COLOURS`). **This shade has not been seen in game.** The test build in
`out\mods\NX2-ZOOTR` has it.

**In game (user, 2026-11-24), fourth test build:**
- **The game's list of text colours cannot be made longer.** The game started as usual, and the three names in
  the added colours (numbers 8, 9 and 10: Water, Shadow and Spirit Temple) all came out orange. The Fire
  Temple was red and both pots' Forest Temple green, as before. The user: "orange shade is fine".

**Fifth test build (2026-11-24): colours of our own in places of the game's list.**
- **Blue is place 2 and purple is place 7 of the game's list** (`tools/dungeon_keys.py`: `OUR_COLOURS`,
  `colour_table`): no text of the game in any language uses those places. Only the three colour values of the
  place change (2: from (255, 0, 254) to (30, 80, 190); 7: from (133, 125, 104) to (115, 45, 160)), its name
  stays, and only the places a named key of the build uses. **Orange is the game's own place 6** (255, 53, 25),
  unchanged. The list stays eight long.
- **Not known:** whether the game's own code uses place 2, 6 or 7 for something (their names' hashes are in
  the file; the names are not known), and whether place 6 is the orange the fourth test showed.

**In game (user, 2026-11-24), third test build:**
- **The name shows on a key from a pot.** Both pots said "You found a small key! (Forest Temple)".
- **The get window shows the colour.** Number 3 is green, number 0 is red, numbers 1, 4 and 5 look gray. All
  four chests in Mido's house showed their temple's name; nothing was broken.
- **The user's colours:** Forest Temple green, Fire Temple red, Water Temple blue, Shadow Temple purple, Spirit
  Temple orange, the last three "if we can use a custom color".

**Fourth test build (2026-11-24): colours of our own, added behind the game's (did not work, see above).**
- **The game's list of text colours is a file:** `MessageColorArray` in
  `UI/Message/MessageColorTable/MessageColorTable.game__ui__MessageColorTable.bgyml`, inside
  `Pack/Bootup.Nin_Ounce_NVN2.pack`. Eight colours (red, green, blue, alpha; a name's hash on seven of them: 1
  is "Gray", 3 is "Green"), and a text's colour number is the place in that list: 0 (138, 0, 0), 1 (80, 45,
  20), 2 (255, 0, 254), 3 (20, 152, 55), 4 and 5 (255, 253, 198) half and two thirds see-through, 6 (255, 53,
  25), 7 (133, 125, 104). It has no blue, purple or orange.
- **Three colours are added behind the game's eight** when a named key of the build uses one
  (`tools/dungeon_keys.py`: `NEW_COLOURS`, `colour_table`): blue (30, 80, 190) as number 8, purple (115, 45,
  160) as 9, orange (215, 110, 0) as 10. The game's own eight and every other file of the pack are unchanged.
  **Not known:** whether the game takes a number past its own eight.
- **The colour of each temple's name is now set** (`dungeon_keys.COLOURS`): Forest Temple 3, Fire Temple 0,
  Water Temple blue, Shadow Temple purple, Spirit Temple orange. `--key-colour DUNGEON=COLOUR` chooses another
  for a build (a number of the game's list, or blue, purple, orange). The other eight dungeons have no colour.
- **Size rule** for the colour list (`tools/sizes.py`): the game has one file of the type, so the rule charges
  everything per colour (733 each), which gives the game's entry for the game's file and can only be too much
  for a longer list.

**In game (user, 2026-11-24), second test build:**
- **The map and the compass given at the start work.** In the Forest Temple as a child the Map page showed the
  temple's map with the map and the compass in their slots and the chests marked.
- **A place marked as visited has its map.** With `IsVisitLocation.KokiriForest=true` the Map page showed the
  map of Kokiri Forest right at the start, where the first build said "???". So "???" is "not visited yet".
- **"Unavailable right now." is the adult made with the debug menu, not the build.** As an adult the Map page
  said it in the Sacred Forest Meadow (not marked) and in the temple (marked), and there was no small map on
  screen; as a child both were there. Something the game sets when Link becomes an adult is missing after the
  debug menu's change. Not looked for further (one saved flag that speaks of it: `Sequence_IsChildhood`).
- **The dungeon map shows no key count** (the user's screenshot: the temple's name and the Gold Skulltula
  count, no keys). The count is seen in the pop-up: the Gold Skulltula's key showed 6, as expected.
- **The name shows on a key in a chest:** the third chest in Mido's house said "You found a small key! (Forest
  Temple)", with no count. **It does not on a key from a pot:** both pots said "You found a small key!", with
  no count. **Why:** a key in a chest is shown as it is; for a key picked up from the ground the game holds up
  the item its name stands for, and the text is that item's. The name was the dungeon's chest key without the
  name, whose own name is the game's key.
- **Asked for (the user):** the temple's name in the temple's colour (green for the Forest Temple).
- Save and reload: as before.

**Third test build (2026-11-24):**
- **The name of a named key is now the dungeon's named chest key** (`Item_NX2KN_<dungeon>`), which is named
  itself and is built with every named key, as the game's `Obj_Dungeon_SmallKey` is named `Item_Dungeon_SmallKey`.
- **The temple's name in a colour:** `--key-colour ForestTemple=3` (`tools/dungeon_keys.py`: `messages`,
  `colour_tag`). The game's texts colour words with a numbered tag; every language uses the numbers 0, 1, 3, 4
  and 5 and no other (0: names and places in talk, 1: Navi's thoughts, 3: "uses 1 magic power", 4 and 5: the
  staff roll). No file says what colour a number is, and no get message of the game has a colour. So the build
  is a colour chart: the two pots hold Forest Temple keys in colour 3, Mido's four chests hold keys of the
  Shadow Temple (4), the Fire Temple (0), the Water Temple (1) and the Spirit Temple (5), from left to right.
  `dungeon_keys.COLOURS` (the colour of each dungeon) stays empty until the test says which number is which.

**In game (user, 2026-11-24), first test build:**
- **Starting with a key works.** The file started with 1 Forest Temple key; with the key from Mido's chest and
  the two from the pots, the Gold Skulltula's key in the temple showed **5**.
- **A key in its own temple, as the game's own key, shows the right count.** The Gold Skulltula's key in the
  first room showed the count, and the right one (5). In part 5 the same spot showed the count from before the
  key.
- **The first room's chest gave the Megaton Hammer; the first door and the lobby's west door opened.**
- **No count appears when a locked door opens.** That is the game's own key and the game's own door, so the
  game shows none there.
- **The temple's name on a key did not show.** Both pots said "You found a small key!". The pot further from
  the door showed no count, the pot nearer to the door showed "0/0". **Why (found in the game's files
  afterwards):** an item has its name in two places, the `ActorName` of its row in `ActorInfo` and the
  `ActorNameRef` of its actor file. The get message is found under the second one (the item's AI,
  `EventTriggerSetOwnNameToMessage`, writes it into the flag `UI_MessageTargetActorName`); the first build
  changed only the first. Changing the first alone is what took the count away: the get event's "is it a
  small key" goes by the row. The game's own model with both changed is the treasure chest game's key,
  `Obj_MiniGame_SmallKey` ("Door Key").
- **The map and the compass could not be checked: the Map page was closed.** As a child in Kokiri Forest it
  said "???", as an adult in the temple "Unavailable right now.", so the key count on the dungeon map was not
  read either. **What was found in the game's files:** the Map page has the states WorldMap, DungeonMap,
  FieldMap, UnopenMap ("???") and two "invisible" ones ("Unavailable right now."); the game's code picks one,
  no file says how. A place has a saved "visited" mark, `IsVisitLocation.<place>` (36 places), set when the
  place's title is shown: in the place's first cutscene (`UISystemActor.EventTriggerOpenLocationUI`:
  `Dm_Kokiri_0045` for Kokiri Forest, `Dm_ForestTemple_0000` for the Forest Temple) or from the place's
  `LocationArea`. **Not known:** whether that mark is what opens the map, and why the temple says "Unavailable
  right now." and not "???" (the temple's map is for the adult only, `LocationErasType`, and the adult was
  reached with the debug menu).

**Second test build (2026-11-24):**
- **A named key now has its name in both places** (`tools/dungeon_keys.py`): its actor file's `ActorNameRef` is
  `?ActorSystem/ActorName/Item_NX2K_<dungeon>...` too (no such file exists anywhere in the game for any item;
  the reference only carries the name). Both pots and the third chest from the left in Mido's house
  (`KF_MIDO_CHEST_02`) hold a named key; the second chest from the left holds a key without the name, as
  before.
- **A place can start as visited, to find out what opens the Map page:**
  `--start-flag IsVisitLocation.KokiriForest=true` (`tools/start_state.py`; the same way as a dungeon's
  record). The build sets it for Kokiri Forest and the Forest Temple, and not for the Sacred Forest Meadow.

**What was built for the first test build:**

- **Start with a dungeon's keys, map and compass:** `--start-flag DungeonInfo.ForestTemple.SmallKeyNum=2`,
  `--start-flag DungeonInfo.ForestTemple.IsGetMap=true`, `...IsGetCompass=true` (and `IsGetBossKey`). These are
  fields of the dungeon's saved record, which `--start-flag` refused until now. They are set the way the game's
  own new-file module sets Link's hearts: one node that finds the record by its name, and one setter per field
  (`tools/start_state.py`). Fields of other structs are still refused.
- **The key count shown on screen** (part 5's in-game result: the pop-up showed the count from before the key,
  and a chest showed none). What was found: the count on screen is the count of the dungeon Link is in, shown
  by a step of the game's own get events (`EventTriggerSetDisplaySmallKey`) after the game has counted its own
  key. So:
  - **a key placed in its own dungeon is now the game's own small key.** The builder decides by the check's
    map. The game counts and shows that one itself, as in part 4's test;
  - **a key placed outside its dungeon** stays the item of its own from part 5. Outside, the game has no count
    of that dungeon to show: a pick-up showed "0 to 0". That is not changed by this part.
- **The temple's name on a key, as an experiment:** `Item_Dungeon_SmallKey@ForestTemple+name`. The game finds
  an item's texts by the name in its `ActorInfo` row (`<name>_Name`, `_GetMessage`, `_GetCaption` in
  `ActorMsg/PouchContent.msbt`). A named key has a name of its own there, and three new texts in every
  language: "Small Key (Forest Temple)", "You found a small key! (Forest Temple)", "It opens locked doors in that
  place, wherever you found it.", with the place's name taken from the game's own list of places
  (`LocationMsg/Location.msbt`). **Not known:** what else the game looks up under that name (its icon, a saved
  flag), so this may show nothing new or go wrong; it is on one pot in the test build, tested last.
- **Tests:** `tests/dungeon_keys_check.py` (20 checks now): the key in its own dungeon, the named key's row,
  actor file and texts (on the ground and in a chest), the name's colour (one of the game's, and one of ours
  in a place of the game's list), starting with keys, map and compass and a visited place, and what is still
  refused.

### Phase 1, part 5: a dungeon's small key anywhere (in game: the keys work, the count shown is off)
A small key that counts for the Forest Temple wherever it is found: `CHECK_ID=Item_Dungeon_SmallKey@ForestTemple`
(any of the 13 dungeons with keys can be named). Test build and checklist: `out\TEST_CHECKLIST.md`.

**In game (user, 2026-11-24): the keys count and open the doors; the count the game shows is not right.**
- **Keys found in Kokiri Forest count for the Forest Temple.** With the key from the pot and the key from
  Mido's chest, the temple showed 2, and in a second run the first door opened without the Gold Skulltula's
  key. The first door, the lobby's west door and the door at the top of the block room all opened.
- **The roadmap's question is answered: no.** The game's own small key picked up in Kokiri Forest (the control
  pot) did not count for the temple: both pot keys were picked up, and the temple showed 2, not 3.
- **The chest:** the key was in the second chest from the left in Mido's house (`KF_MIDO_CHEST_01`). The game
  went on normally after it; the other three chests were as in the game.
- **What is off: the count on screen.**
  - picking up a key in Kokiri Forest showed a count going "from 0 to 0" (both the Forest Temple key and the
    game's own key);
  - the chest showed no count and no pop-up;
  - in the temple, the pop-up after the Gold Skulltula's key showed 2 where 3 were held: it shows the count
    from before the key is added;
  - no count appeared when a door was opened.
  The user: "Key count doesn't seem to accurately display, but the keys themselves seem to work"; "not end of
  world if the keys themselves work". The right count is on the dungeon map in the pause menu, inside the
  dungeon (the user; not tested in this round).
- **Not answered:** the two lines about saving and about save and reload were left blank. Which of the two pots
  held which key cannot be told (both showed the same).
- **The user's decision (2026-11-24):** the PR for this part is opened as it is; the count shown on screen and
  the dungeon's name in the get message go into the next part (part 6). Whether the game showed a count when a
  door was opened in part 4's test, with the game's own keys, the user could not say for sure ("I thought the
  key count went down by 1 when you used a key but I could be misremembering"): to look at in part 6.

- **Where the game keeps a dungeon's keys.** A saved number per dungeon, `DungeonInfo.<dungeon>.SmallKeyNum`
  (13 dungeons; the same record holds the boss key, the map and the compass: `IsGetBossKey`, `IsGetMap`,
  `IsGetCompass`). The names are stored only as hashes; they were found by trying names against the hashes.
- **The roadmap's question, from the files:** the game's own key steps name no dungeon (`OneShotDungeonGetSmallKey`,
  `EventGetDungeonSmallKey`...): they count for the dungeon Link is in. So the game's own key found outside
  cannot count for the right dungeon. The test build has one in a Kokiri Forest pot to see what it does.
- **The key of a dungeon is an item of its own** (`tools/dungeon_keys.py`), never the game's small key, so the
  game's "dungeon Link is in" step never runs for it:
  - on a pot, a rock, a bush, a freestanding item or a Gold Skulltula: the builder's version of the key for that
    kind, with two nodes more in its AI: picked up, it adds 1 to the dungeon's count. This is how the game's own
    Gerudo Fortress keys set their flag;
  - in a chest: the chest gets an opening event of our own around its usual one (as the ocarina chests have),
    with one step after it that adds 1 to the dungeon's count, as the treasure chest game's flow counts its keys;
  - it has the key's model and name; its item settings say "not put in the inventory".
- **Limits, told plainly:**
  - not on gifts, Deku Scrubs, shop shelves or songs yet (the builder refuses those);
  - the get message still says "small key", not the dungeon's name. Not done in this part;
  - no entry in the inventory: a new inventory item would need saved flags of its own, which the save file has
    no place for. The count shows where the game shows a dungeon's keys.
- **Tests:** `tests/dungeon_keys_check.py` (new, in `run_tests.bat`, 15 checks).

### Phase 1, part 4: the Forest Temple's small keys on other checks of the temple (passed in game)
The five small keys can be put on other checks of the temple: in another chest, in a pot, on a Gold Skulltula.
Test build and checklist: `out\TEST_CHECKLIST.md`.

**In game (user, 2026-11-24): passed.**
- **All five keys were counted for the temple,** each from its new place: the first room's Gold Skulltula, a
  lobby pot, a first Stalfos room pot, a block room pot and the Bow room's big chest. Picking one up showed
  "small key" and the count in a pop-up on screen. The count went 1, 0, 1, 2, 1, 2, 1, 2, 1 as keys were found
  and the four locked doors on the way (first room, lobby west, top of the block room, Bow room east) opened.
- **The two forms of the key** (the game's ground key, and the chest's key made to lie on the ground) looked
  and acted the same.
- **The chests that held keys** gave their new items: the Megaton Hammer (first room) and the Lens of Truth
  (first Stalfos room), the Lens with no magic meter.
- **The boots:** the Hover Boots and the Iron Boots lay on the floor.
- **After save and reload:** the count was still 1, the four doors open, the key pots and the Gold Skulltula
  gone.
- **Not answered:** the two lines about skipping the opening and starting with the Hookshot were left blank.
  The well's, the Floormaster room's, Joelle's and the east courtyard's chests were not on the test's way.
- **Seen, not part of this change:** the Megaton Hammer is "a little high" when Link holds it up from the
  chest. A chest holds the game's own `Item_Hammer` with the game's own pose (`Item_Hammer_Animation`,
  `Pose_Common`: no held-up pose of its own); the builder changes neither. To compare with the unchanged game
  at the Fire Temple's chest. FPS (part 3's note): the user thinks it was PC usage; not looked into.

- **No builder change was needed for the keys.** A small key is a small key by its inventory settings
  (`PouchSpecialDeal: SmallKey`, counted), and the game has it in two forms: `Item_Dungeon_SmallKey` (in a chest)
  and `Obj_Dungeon_SmallKey` (lying on the ground). The versions the builder makes for a pot and a Gold Skulltula
  keep those settings and go into the inventory as `Item_Dungeon_SmallKey`. Whether the game then counts the
  key for the temple is the in-game test.
- **The test placement is checked with the logic** (`tests/forest_temple_keys_check.py`): walked with the items
  where the placement puts them, every locked door is reached with enough keys found before it, and all 47
  checks and the boss are reached. Two placements that must get stuck do get stuck: no key in the first room
  (0 keys, 2 checks), and the fifth key behind the fifth door (4 keys, no boss).
- **Hover Boots and Iron Boots lie on the floor, not in it** (the user's note from part 3's test). Their models
  could not be measured: their vertices hang on up to seven bones, with the fifth weight stored in a byte of its
  own, which `tools/item_pose.py` did not read. Now it does, and both boots are on the builder's list of raised
  items (`GROUND_LIFT`): the Hover Boots lay 0.140 under the floor, the Iron Boots 0.147; both now lie 0.05
  above it, like every other raised item. Held up they look as before (the game's pose, copied). Every other
  version of every other item (1,553) is built byte for byte as before (`tests/ground_lift_check.py`).
- **Tests:** `tests/forest_temple_keys_check.py` (new, in `run_tests.bat`, 15 checks);
  `tests/ground_lift_check.py` knows the two boots (nine items on many bones, not seven).

## 2026-11-23

### Phase 1, part 3: items on the Forest Temple's checks, and the Bow room's door (passed in game)
The builder now places items on the temple's chests, pots and Gold Skulltulas, and a new game fix reopens the
Bow room's door when its chest appears (decision 39). The small keys and the boss key stay where the game puts
them. Test build and checklist: `out\TEST_CHECKLIST.md`.

**In game (user, 2026-11-23): passed.** A new file (it started with the Hookshot), warped to the Sacred Forest
Meadow with the debug menu, into the temple with the Hookshot.
- **All 11 placements gave their item:** the two Gold Skulltulas (Iron Boots, Piece of Heart), the six pots
  (Megaton Hammer, Hover Boots, Lens of Truth, Mirror Shield, Din's Fire, Farore's Wind) and the three chests
  (Ice Arrow in the Bow's big chest with no message from Navi, the Fairy Bow with quiver and arrows in the
  map's big chest, the Fire Arrow in the chest the eye switch drops).
- **Pots:** only the item came out of the pot that had a drop table; the other four lobby pots were as in the
  game; the two item pots stayed gone after leaving the lobby and coming back.
- **Keys:** the first room's and the first Stalfos room's chest still gave a small key. The line about the
  well's chest was left blank.
- **The Bow room without the Bow:** the door shut, three Stalfos, the chest appeared, and the west door's bars
  went up by themselves. Saving worked in the room after that. After walking out and back in the door was
  still open and the Stalfos were gone. With the Bow later, shooting the eye switch behind the bars showed the
  door and did nothing more.
- **After save and reload:** items kept, chests open, item pots gone, Gold Skulltulas gone, the door open.
- **Sides:** left, right and "furthest" in the checklist, worked out from the map's numbers, were right.
- **Seen, not part of this change:**
  - the Hover Boots lay slightly in the floor (from a pot). Not fixed yet;
  - the Lens of Truth gave the magic meter, and the opening could not be skipped: this test build was made
    without `--fix magic_is_separate` and `--fix skippable_opening`, which earlier test builds had. The fixes
    themselves are unchanged;
  - "FPS felt lower than normal?": not looked into yet.

- **Pots.** None of the temple's 28 pots names an item: 21 name a drop table (`Drop__DropTable`: hearts,
  arrows...) and 7 name nothing. The builder refused both. Now such a pot gets the item (`Drop__DropActor`) and
  loses its table, which is the form of the game's own item pots (109 in the game). The item is given once, as
  on the pots of Kokiri Forest: every one of the 28 has the two saved flags that needs.
- **Chests.** The falling ceiling room's chest names no item; it now gets one like any chest. Three chests
  have an opening event of their own, read from the event flows:
  - the Bow's (`ForestTemple_GetBow`): the usual opening, then a message from Navi about the Bow. Removed when
    the chest holds something else;
  - the map's and the compass's (`ForesetTemple_GetMap`, `ForesetTemple_GetCompass`): only the usual opening.
    Kept.
  The boss key's chest (`ForesetTemple_GetBossKey`) is still refused: part 7.
- **Gold Skulltulas:** as in the forest (the item's token version), no change needed.
- **The Bow room's door: `--fix forest_temple_bow_room_door`.** The room's logic file
  (`Logic/ForestTemple_Level_Room_06_Prefab_6b8c`) locks the west shutter until a flag is set or the eye switch's
  event has played; that event needs the eye switch on and the chest there. The fix changes one source of one
  node: the lock now ends when **the chest has appeared**. That is how the game's own first Stalfos room
  unlocks its shutter. Shooting the eye switch still works as before. The file keeps its length; one node of 36
  differs.
  - Logic: new setting `forest_temple_bow_room_door` (on by default). The way out of the Bow room asks for it
    or the Bow.
- **Not in this part:** the Heart Container. The "loose item" of the temple's count is the boss's heart, so it
  belongs to part 7 (boss key, boss door, boss heart, Medallion).
- **Found, not solved:** a big chest cannot hold a progressive family (the game's checking chest is the small
  one), and the Bow's chest is a big chest. The Bow alone can be in a big chest. To settle before the generator.
- **Tests:** `tests/forest_temple_items_check.py` (new, in `run_tests.bat`, 26 checks).

### Phase 1, part 2: the Forest Temple's data (no game changes)
The temple's checks, regions and logic rules, read from the game's files. Nothing in the game is changed and there
is nothing to test in game for this part; the rules are tried in game with part 3's build.

**In game (user, 2026-11-23, the unchanged game):**
- **The first room's Gold Skulltula does not need the Hookshot:** it is grabbed by climbing the vines.
  `FT GS Entrance` now has no item rule (it had `can_use(Hookshot)`, assumed for its height).
- **The Bow room does need the Bow to leave.** The eye switch sits behind bars, so the Hookshot does not reach it.
  **Saving is off in the room.** Dying puts Link back at the temple's beginning, and because nothing was saved,
  whatever was picked up in the room is lost. So a player without the Bow is not stuck for good, but can keep
  nothing found in the Bow room (its chest and 4 pots).
- **Decided (D39): the randomizer reopens the Bow room's door when the chest appears.** A game change, so it is
  built and tested in part 3. Until then the rules are as before (in freely, out with the Bow).

- **47 checks, each with a permanent ID** (area code `FT`, `data/ids.json`): 12 chests, 5 Gold Skulltulas, 28
  pots, the Heart Container and the Forest Medallion. The map files hold 46 spots; the "1 loose item" of the
  count is the boss's Heart Container, so the Medallion is the only check without a map object.
- **23 regions** in `data/world/ForestTemple.json`, each with the positions and flag names it was read from. The
  placeholder "Forest Temple (not mapped yet)" is gone; the Sacred Forest Meadow now leads to `FT Entrance`.
- **Small keys:** 5 locked doors (a chain lock on each side, 10 locks) and 5 small keys in chests. The doors come in
  a fixed order, so the rules ask for 1, 2, 3, 4 and 5 keys (`ForestTempleSmallKey`):
  1. first room to the lobby (**remake: this door is locked**; its key is in the first room's chest);
  2. lobby, west door, to the block room;
  3. top of the block room to the west twisted corridor;
  4. Bow room to Beth's room;
  5. east twisted corridor to the room with the frozen eye switch.
  The boss door has its own lock (`ForestTempleBossKey`).
- **What the game puts in the chests:** small keys in the first room, the first Stalfos room, the well, the
  Floormaster room and Joelle's room; the boss key in the straightened corridor; the Bow; the map (east courtyard);
  the compass (Beth's room); a purple rupee (block room eye switch); arrows (basement). The falling ceiling room's
  chest names no item in the map.
- **Read from the room logic** (`Logic/ForestTemple_Level_Room_*`):
  - The lobby's east courtyard door opens with a **floor switch**, not an eye switch. The west courtyard door has a
    Song of Time block in front of it.
  - Three eye switches cannot be pressed with the Hookshot (`isHitHookShot` false): both in the block room and the
    one in the Bow room. They need an arrow.
  - Joelle and Beth come out when their pictures are shot; Amy after her picture is shot and its blocks are put
    together; Meg appears in the lobby once the other three are beaten, and then the elevator goes down.
  - Two eye switches sit in ice that melts when an arrow reaches it through fire: the room after the east twisted
    corridor, and **the basement (not in the N64 game)**. So the boss cannot be reached without the Bow.
  - The well is drained by a floor switch on the west courtyard's upper walkway.
- **Found for part 3 (items on the temple's checks): the Bow room can trap the player.** Its west shutter opens
  again only when the eye switch is shot after the chest appears. Without the Bow the only other way out is the
  locked east door, which leads to Beth's room, a dead end without the Bow; saving and warping are off while the
  shutter is shut. In the logic the room is entered freely and left with the Bow. To settle before another item
  is put in that chest. (Settled the same day: see the in-game result and D39 above.)
- **Logic:** `logic/requirements.py` now keeps only the highest count of an item in one alternative
  (`ForestTempleSmallKey*5`, not 1+2+3+4+5 keys). `tools/extract_checks.py` leaves out pots that come back
  (`Obj_Pot_*_Respawn`: the arrow pot in the Bow room, the only one in the four areas extracted so far);
  the forest's three areas extract exactly as before.
- **Not known from the files, to check in game** (every region is `"verified": false`; each point is in the notes
  of its region or check):
  1. First room: how the chest (y 117.5) is reached. (Its Gold Skulltula: answered, no Hookshot needed.)
  2. Gold Skulltulas in the lobby, the east courtyard and the basement: Hookshot assumed. The west courtyard's is
     about 14 units from the balcony: Hookshot or Longshot?
  3. East courtyard: is the chest reachable without the Hookshot, and does the Hookshot target get Link up to the
     ledge of the falling ceiling room's door? (The logic says no: the ledge is reached from that room.)
  4. West courtyard: does the upper walkway (y 113.9) join the balcony (y 107), and can the Floormaster room be
     entered from the block room's side of the balcony? (The logic says no: only after the drop from the
     straightened corridor.)
  5. The flooded well with Iron Boots; pushing blocks without the Goron Bracelet; the ice with Din's Fire or Fire
     Arrows; Meg and Phantom Ganon without the Bow.
  6. What the falling ceiling room's chest gives.
  7. How the game hands over the Forest Medallion (its item, `Item_Medal_Forest`, is in none of the sage room's
     flows by name): part 7.
- **Tests:** `tests/forest_temple_check.py` (new, in `run_tests.bat`, 35 checks): the data against the game's
  files, and the temple walked with the items where the game puts them (all 47 checks, with or without the Song
  of Time), without the Bow (26 checks, as far as the Bow room), without the boss key (45), and with a key
  missing. `tests/logic_check.py` has 10 new situations; `tests/db_check.py` now covers the Forest Temple (167
  active IDs, 0 errors).

### Phase 1, part 1: the starting state of a new file (passed in game)
New builder options: `--start ITEM` or `--start ITEM=N` puts an item in the inventory of every new file, and
`--start-flag NAME=VALUE` sets a flag on it. Later parts reuse this for "start with" keys, maps and compasses,
Zelda's Letter, starting as adult, full wallets and the "open" options.

- **The roadmap's unknown, answered from the game's files: both. Items and flags can be set on a new file, in
  the same place.** Confirmed in game the same day (result at the end of this entry).
- **Where the game sets up a new file** (read from its own files):
  - The new-game sequence `Sequence/Opening.module.ainb` runs `Sequence/SetPouchAndStatusForGameStart.module.ainb`
    once: after the title screen's map is gone (`ChangeBanc`, `DoAfterDestroyBanc`) and before it asks for the
    event that loads Kokiri Forest (`Opening_LoadingKokiriForest`). No other sequence runs that module.
  - That module is the game's own list of what a new file has. Four `SeqOneShotPushToPouch` nodes give the small
    wallet (`Item_Wallet_Small`), the adult tunic (`Armor_Adult_Normal`) and the two green tunics
    (`Obj_Armor_Child_Normal`, `Obj_Armor_Adult_Normal`), each named by its actor file
    (`Work/Actor/<item>.engine__actor__ActorParam.gyml`) with a count (`Num`). Five `SeqOneShotSetGameDataInt`
    nodes set `PlayerStatus`: `Life` 12 and `MaxLife` 12 (three hearts), `MP`, `MPEconomy`, `MPMax` 0.
  - Everything else a new file has is the flag's default in `GameData/GameDataList`. Example: Mido's
    `KokiriForest_Npc_Kokiri_Mido_Child_Blocker` is `true` by default; the game's flows only ever set it to
    `false` (`Npc_Kokiri_Mido_Child`, twice).
  - The sequence has a setter node per flag type: `SeqOneShotSetNonStructGameDataBool`, `...Int`,
    `...String64` (also `...Float`, `...Enum`, `...Vector3`, not used yet). The game uses the first three in
    `Sequence/DestroySceneCommon.module.ainb`.
  - The opening's event flow (`OpeningEvent`: `Opening_LoadingKokiriForest`, then `Opening_Introduction`) and
    `--fix skippable_opening` are not involved: the fix only removes the opening cutscene's "DisableSkip"
    setting. The flows could also give items (`PouchSystemActor.EventTriggerAddOrRemovePouchContent`) and set
    flags (`GameDataActor.EventTriggerSetGameDataBool` / `Int` / `String64`), but the sequence module is where
    the game itself does it, and it doesn't depend on a cutscene being played or skipped: it is the one used.
- **How it is built** (`tools/start_state.py`, called by `tools/build_mod.py`):
  - A starting item is one more `SeqOneShotPushToPouch` node: a copy of the wallet's node with the item's actor
    file and count, linked under the module's group of pushes.
  - A starting flag is one more setter node: a copy of the game's own setter of that type (from
    `DestroySceneCommon`) with the flag's name and value, linked under the module's group of status sets.
  - The game's 17 nodes are not changed; the new nodes come after them. The module's size table entry follows
    the game's rule for `.ainb` files (5,916 bytes: 6,296; with one item and one flag 6,627 bytes: 7,032).
  - Read back before it is written: the game's nodes are unchanged but for the two groups' new children, every
    new node is the game's node it was copied from with only the item and count, or flag and value, different,
    and nothing else in the file changed.
- **What is accepted:**
  - An item must be an inventory item under its own name: a row in `RSDB/PouchActorInfo` and the saved pair
    `IsGet.<item>` / `PouchData.<item>.StockNum`. Three of the game's four pushes are; the fourth
    (`Obj_Armor_Adult_Normal`) has a row but no pair, so the game also pushes names that stand for another
    inventory item. That case is **not tried yet and is refused for now**: the Fairy Slingshot and Fairy Bow as
    they are placed (`Item_Range_SlingShot`, `Item_Range_Bow`) and the gauntlets (kept as armour:
    `Armor_Child_Gauntlet_Goron`...).
  - The item rules hold: nothing the game never gives as such (the small bags, the small wallet), and a later
    level of an upgrade family only with every level in front of it (`--start Item_Longshot` asks for
    `--start Item_Hookshot` too).
  - A flag must be a Bool (`true` / `false`), an Int (a number) or a String64 (text) of `GameDataList`, saved
    in the save slot (`slot_NN/progress.sav`), and not a field of a struct (`PlayerStatus.MaxLife`,
    `IsGet.<item>`: the plain setters don't take those). A `BoolExp` is worked out from other flags and cannot be
    set. A flag the game also resets at other times (reset type other than 8) is set with a printed NOTE.
  - Everything refused stops the build before anything is written, with the reason.
- **Not covered yet** (for the parts that need them): struct fields (hearts, magic, rupees: the module's own
  `SeqOneShotSetGameDataInt` on `PlayerStatus` is the pattern), Enum and Float flags, items under another
  inventory name, and the per-placement flags (`Bool64bitKey`: an opened chest, a taken heart piece), which have
  no name to set.
- **Tests:** `tests/start_state_check.py` (new, in `run_tests.bat`): where the game sets up a new file and what it
  gives and sets there, read from its files; 5 items and one flag of each type added and read back; the
  read-back stops 9 kinds of wrong file; 23 refused requests; whole builds (only the module and the size table
  are written; a refused request leaves the earlier build untouched; a build without the options doesn't
  touch the module).
- **Test build** (`out\mods\NX2-ZOOTR`, checklist `out\TEST_CHECKLIST.md`): a new file starts with the
  **Boomerang**, and Mido's blocking flag is off, so he should let Link through to the Deku Tree without the
  sword and shield. Nothing is sold, so no gold rupee. Built with:

      py -3 tools\build_mod.py --romfs "<romfs>" --out out\mods --name NX2-ZOOTR --fix skippable_opening --start Item_Boomerang --start-flag KokiriForest_Npc_Kokiri_Mido_Child_Blocker=false

  What the flag does, from the forest's logic modules: while it is true,
  `Logic/KokiriForest_Child_Level_All_02_35ae` keeps two areas in front of Mido that turn on
  `KokiriForest_Npc_Kokiri_Blocker` when Link steps in; with it false those areas are removed.
- **In-game result (2026-11-23, new file, all good):**
  - The Boomerang is in the item menu right after waking up, and it is thrown normally inside Link's house and
    outside.
  - The rest of the start is as usual: 3 hearts, no sword, no shield, 0 rupees, green tunic.
  - Mido lets Link through to the Deku Tree without the sword and shield. He stands in the middle of the path
    and says a long text box (noted by the user as "listen here my no fairy----"); it looked fine.
  - After save and reload the Boomerang is still there and the path is still open.
  - Not tested: that an older file is unchanged (the optional line).

### Roadmap to the public beta (docs only)
- `docs/ROADMAP.md`: the approved plan of action, in priority order: the Forest Temple first, then every area in
  game order, then the generator and the app, your own seeds, a quiet early stage on Discord, and the public beta.
- `docs/ROADMAP_DECISIONS.md`: the 37 decisions of the planning session.
- `docs/RESEARCH_check_count.md`: a read-only count of check-like objects in every map (1,286 spots; exactly 100
  Gold Skulltulas, which confirms every area was read). Nothing was mapped.
- `CLAUDE.md`: the project's standing working rules, read by every session (including worktrees).

### In-game results of the morning test (bombs and Boomerang retest, gossip hints, Saria's bridge family)
All three runs done, everything passed.
- **Bombs and Boomerang, retest: passed.** Run 1 (inside first): the Bomb Bag on Saria's floor and the Boomerang
  in the Know-It-All pot work inside the house, before leaving; the rock behind Saria's house then gives the
  bigger bomb bag; the House of Twins pot gives the Silver Scale. Run 2 (outside first): the rock's Bomb Bag
  and the shop bushes' Fairy Slingshot work right there; Saria's floor then gives the bigger bomb bag, usable
  inside. So last time's "unusable until a scene change" was not reproduced: most likely something in that
  build, not houses.
- **Gossip hints: the wording passed** on all four stones, word for word as built (Lost Woods entrance:
  Boomerang; the two Deku Tree stones: Bomb Bag, Silver Scale; the bridge stone: the Silver Scale gift).
  - **Colour bug:** everything after "They say the" shows red, not only the highlighted names. Cause, read
    from the game's English text: the game ends a highlight with colour `0xFFFF` (3,046 times), never with
    colour 1, which the builder used. Not fixed yet. The 2026-11-22 stone test had the same tag after
    "{Lost Woods}".
  - The user may want "progressive Bomb Bag"-style wording instead of "a Bomb Bag or an upgrade of it";
    undecided.
- **Saria's bridge family: passed.** Without the Silver Scale: window and item Silver Scale. With it: the window
  says Gold Scale and the Gold Scale is given; Link holds the Silver Scale's model, as expected (one model in
  the scene). A scale held by young Link looks oversized; accepted, a fix would be item by item.
- **Young Link's Bow:** left as it is for now (the user's choice).

### Not built: families on shop shelves, and young Link's Bow (researched, a decision first)
Both were on the overnight list. Both need a choice or in-game rounds before code, so they were researched
instead; the write-up with the measurements and the options is `out/RESEARCH_shelf_families_and_child_bow.md`.
- **Shelves:** the shop never names the item it gives in a flow we could put a question in front of. The shelf
  actor puts itself into the inventory (`EventTriggerShopItemPutInPouch` in `DisplayShop`), and which actor
  stands on a shelf is fixed in the map. The likeliest way is the game's own: a shelf placed only while a flag
  holds (the Market's bug shelf), with one placement per level. That means adding placements to a map, which
  the builder has never done: first one shelf and one pair, in game. A family on a shelf is still refused.
- **Young Link's Bow:** measured, the Bow held up is 0.86 m tall, centred on the game's show point; the items the
  game gives young Link are 0.31 to 0.59 m. It isn't held higher than other items, it's much bigger, and the
  game's chest Bow looks the same (Run 2). A fix for young Link only needs a young-Link copy of every Bow version
  (five builders, none of which knows ages today); a fix for both ages is small but changes adult Link's Bow
  too. Left as it is until one is chosen.

### Upgrade families on song checks and on Saria's bridge gift (to test in game)
`CHECK_ID=First>Second[>Third]` is now accepted on a song check (`Song from Saria`) and on the cutscene gift
on the bridge (`LW_SARIA_GIFT`). Before, both refused a family.
- **How it decides:** with the game's own inventory question, the one gifts with a family already use (the Deku
  Theater's `PouchSystemActor.EventQueryIsExistInPouch`): "has Second?" yes -> Third, no -> "has First?" yes ->
  Second, no -> First. With every level owned it gives the last again, as a gift with a family does. It asks for
  the names the inventory knows the levels by (`Weapon_Range_SlingShot`...).
- **Song check** (`song_skip`): the song cutscene still only fades in and hands over the item (passed in game
  2026-11-17), now with one get per level behind the questions. Each get leads on to what its level needs: the
  first level's seed bag or quiver, an ocarina's sync steps (so it can be played at once), then the end.
- **Saria's bridge gift** (`cutscene_family_edit`): the cutscene shows the get window (Event77) before it adds the
  item (Event68, a branch of a fork). The questions go in front of both, with a copy of the window and of the
  add per later level. Both are asked before anything is added, so both give the same level. A later level's add
  leads on to what the add led on to (the seed bag and quiver come with the first level only).
- **Known look:** Link holds one actor in the bridge cutscene, whatever the level: the first level when it is an
  item actor (the Fairy Slingshot), otherwise Saria's ocarina. The window and the item given are right.
- **Bug fixed (found by the new test, it was in main):** a Fairy Slingshot or Fairy Bow alone on a song check
  stopped the build (`no actor 'PouchSystemActor'`): the song cutscene has no inventory actor for the seed bag
  step. It is now copied from the Deku Theater's flow, as gifts do.
- **Read-backs:** the song (`song_skip_check`, new: before, a song had none) and the bridge cutscene
  (`cutscene_family_check`) are read back against the original: original events unchanged, every number of
  levels owned leads to the right window, add or get, and what follows each.
- **Still refused:** a family on a gift with no flow data (the Skull Kids, the Deku Theater), on a shelf (see
  the entry above).
- **Tests:** new `tests/event_families_check.py` (in `run_tests.bat`): all 11 families on the song and on the
  bridge gift, for every number of levels owned; what follows each get; the read-backs, and that they refuse a
  swapped question, a later window that does not lead on and a link left on the add; a cutscene whose window
  does not come first is refused; whole builds. `tests/gift_check.py`, `tests/families_check.py` and
  `tests/pairs_more_check.py` no longer expect the song and the bridge gift to refuse a family.
- **In game:** the bridge gift can be tested on a new file. Saria's song needs Zelda's letter, which a new file
  can't reach yet, so the song is only tested by the tests above.

### Gossip stone hints made from the placements (to test in game)
`--hint STONE=ITEM` (or `STONE=@CHECK_ID`, repeatable) makes a stone say where an item of the build is. The
sentence is made from the build's own placements and handed to the stone as a `--gossip` text, so it uses the
stone text and talk flow that passed in game (2026-11-22). Example:
`They say the {Boomerang} can be found in a pot in the {House of the Know-It-All Brothers} in {Kokiri Forest}.`
- **Every name is the game's own English text** (the remake's names, never the N64 game's):
  - the item: `<name>_Name` in `ActorMsg/PouchContent.msbt`, for the item or the name the inventory knows it by
    (`Weapon_Range_SlingShot` for `Item_Range_SlingShot`). Its article comes from its get message: "You found
    **the** Boomerang!" gives "the Boomerang", "You found **a** bomb bag!" gives "a Bomb Bag";
  - the area: `LocationMsg/Location.msbt`, whose labels are the maps' names: Kokiri Forest, Lost Woods, and
    **Sacred Grove** (the remake's name for the Sacred Forest Meadow);
  - a house, the shop, the training grounds and the theater: the first line of their signboard
    (`EventFlowMsg/SignboardWood.msbt`): Link's House, Mansion of the Great Mido, Saria's House, House of the
    Twins, House of the Know-It-All Brothers, Kokiri Shop, Training Grounds, Forest Stage;
  - Gold Skulltula and Business Scrub: `ActorMsg/Enemy.msbt`.
- **Our own words** are only the joins: "They say ... can be found", how it is found (in a chest, lying on the
  ground, in a pot, under a rock, under a bush, inside a boulder, on a Gold Skulltula, sold by a Business Scrub,
  for sale, as a gift), "underground" for the grottos (the game's text has no word for them), "the" in front of
  the Lost Woods and the Sacred Grove.
- **A family** is named by its first level, "or an upgrade of it" (`They say a {Silver Scale} or an upgrade of
  it can be found on a Gold Skulltula in the {Lost Woods}.`). A small seed bag placed alone is named as the
  Fairy Slingshot it gives.
- **Refused before anything is written:** an item on no check, an item or family on two or more checks (name
  the check with `@CHECK_ID` instead), a family written out in full, `@` a check given nothing, a stone that
  also has a `--gossip` text, a "stone" that is not one, `--hint` without assignments.
- **Known:** the bridge to Hyrule Field is part of the Kokiri Forest map, so its chest, Saria's gift there and
  the scrub by it are said to be "in Kokiri Forest".
- **Tests:** new `tests/hint_check.py` (in `run_tests.bat`): every level of every family and 19 other items
  have a name (with the ones read by hand), every place and area has its name, all 146 checks that can hold an
  item get a wording, the longest item name as a family fits a stone on every check (two pages at most), what
  `--hint` takes and refuses, and a whole build read back in all 16 languages. ALL OK.

### Tidy-up: the drop-table code is removed
The code for the way that never worked in game (the game's drop code choosing the level of a family before
anything is dropped, 2026-11-22) is removed. Nothing a build makes changes because of it; every family on a rock,
bush, pot or Gold Skulltula is the one-time turning item that passed in game.
- **Removed:** `tools/drop_tables.py` and `tools/skulltula_items.py` (the `Obj_NX2S_` drops, the drop code's two
  lists); in `tools/build_mod.py` `DROP_KINDS`, `gs_families`, the drop tables a placement could name
  (`patch_file`'s `tables`) and the two sections that wrote the tables, the `Obj_NX2S_` drops and the drop code's
  lists; in `tools/sizes.py` the three drop-table size rules and the `GROWTH` part (only the drop code's settings
  used it); in `tests/size_check.py` the exception for the game's test drop table.
- **The rocks', bushes' and pots' AI** (`tools/once_items.py`) loses the branch "the drop table my placement
  names starts with NX2_ -> hand my number to what I drop". No placement names such a table any more, so the
  branch never ran. The AI is now exactly the one of `claude/pots-one-time` (passed in game on 2026-11-22 with
  the Boomerang pot and the rocks).
- **Tests:** `tests/skulltula_prog_check.py` keeps its checks of the game (the token marks its skulltula, the
  skulltula hands its flag over, every skulltula placement's two flags) and its whole builds; the checks of the
  removed drops and lists are gone. Its "the drop code's settings are not in the mod" check now looks for the
  file under its real name in the mod (with `.zs`): before, it looked for a name no file has, so it could never
  fail.
- The research and the four in-game tries stay in this changelog (2026-11-22) and in
  `out/RESEARCH_drop_tables.md`.

## 2026-11-22

### Families on Gold Skulltulas are turning items too (passed in game)
The user's choice after rocks, bushes and pots passed. A family on a Gold Skulltula is now the one-time turning
item a rock drops.
- **In game (2026-11-23): everything passed.**
  - Run 1:
    - Saria's rock: the Fairy Slingshot, 30 seeds.
    - The Gold Skulltula above the Deku Theater: a slingshot that turned into the bigger seed bag (40). It
      landed where Link could reach it.
    - The shop bushes: a slingshot that turned twice, into the biggest seed bag (50).
    - The House of Twins pot: the Silver Scale.
    - The Know-It-All house Gold Skulltula, at night: a Silver Scale that turned into the Gold Scale. It
      landed where Link could reach it.
    - Done once: nothing came back after leaving the area.
  - Run 3: two slingshots lay at once (Saria's rock and the shop bushes). After Link took Saria's, the
    one at the shop bushes turned into the bigger seed bag (40).
  - No level was skipped or given twice, and no spot dropped nothing.
  - Run 2: the Fairy Bow from Mido's chest (a chest Bow, which uses the game's own pose) is **also held up
    too high** for young Link. So the high pose is the game's own Bow pose: the game never gives young Link
    the Bow, and its pose fits adult Link. It is not caused by our lifted ground pose. The user: fine to
    leave it if it can't be fixed.

How it works:
- the skulltula's placement names the first level's `Obj_NX2Q_` version (`Drop__DropActor`, as a plain item on
  a skulltula already does). The skulltula hands its flag to what it drops as it does to its token, and the item
  marks it the way the token does: when picked up, or when it turns into the next level;
- no AI is added to the skulltula (it hands its flag by itself), and the drop code's lists, the skulltula's pack
  and the `Obj_NX2S_` drops are no longer in a build. `tools/skulltula_items.py` and `tools/drop_tables.py` stay,
  but no build uses their family code now;
- the same known limit as on rocks: if Link already owns the level that comes out, it marks the skulltula as
  it turns, so a next level left lying is lost;
- not known yet: where an item falls from a skulltula high on a wall (a rock's item lands at its feet);
- tests: the whole-builds part of `tests/skulltula_prog_check.py` now checks the turning items: the
  placement, every level's version in the mod, and nothing of the drop code's way in the mod.

### Families on rocks, bushes and pots are turning items again (Run 1 passed in game)
After four in-game tries (below) the game never put a lower level in place for our drops. At the user's choice
("try 2"), rocks, bushes and pots go back to the version from before that work.
- **In game, Run 1 (2026-11-22): all passed.**
  - Saria's rock: the Fairy Slingshot, 30 seeds.
  - The shop bushes: a slingshot that turned into the bigger seed bag (40).
  - The House of Twins pot: the Silver Scale.
  - The Know-It-All rock: the Fairy Bow turned into the bigger quiver, then the biggest quiver (50).
  - Done once: no rock, bush or pot came back after leaving the area.
  - Items work indoors. The earlier problem was bombs and the Boomerang **picked up** inside a house: they did
    nothing until Link left. That is still open.
  - The 5 rupees from bushes are the game's own: the Kokiri outside Saria's house gives them as a gift for
    cutting the bushes. Not ours.
  - The Fairy Bow is still held up too high when taken (this time from the rock). Run 2 (the chest Bow) was
    not done, so it is still unknown whether that pose is ours. Run 3 (two of one family lying at once) was not
    done either. (Both were done in the next test: see above.)

How it works:
- the drop is the family's **first** level as its one-time turning item (`Obj_NX2Q_<level>`). While it lies
  there and Link owns its level, it marks the rock, bush or pot and turns into the next level, and again for a
  third level. Players can see it change;
- `TURN_KINDS` holds rocks, bushes and pots again, and `DROP_KINDS` is empty (`tools/build_mod.py`). The drop
  table code stays for Gold Skulltulas only;
- the dropper still never renames its drop (that crashed the game);
- **Gold Skulltulas are unchanged**: a family there still relies on the swap that never happens, so it drops
  nothing where a lower level is needed. They have no family in this test (changed in the next step: see
  above);
- tests: `tests/one_time_check.py` is the turning version again, and `tests/pairs_more_check.py` and
  `tests/families_check.py` check turning items on rocks, bushes and pots again. Each keeps the other
  branches' changes (pairs on Gold Skulltulas, the seven lifted poses).

### Families on rocks, bushes, pots and Gold Skulltulas drop from a drop table of ours (dropped, see above)
- **Why** (research: `out/RESEARCH_drop_tables.md`): the in-game test showed that the drop rules' fallback rows
  were never applied to an actor a placement names directly. The game's files show the rows belong to drop
  tables: every table item has `IsReplace: True`, and a table can switch the unlock rule off for itself
  (`NotReplaceOnUnlockCondition`). The game's own rocks mostly name a table (`Drop__DropTable`), and a Gold
  Skulltula drops its token from the one table of its drop part (and that token still marks the skulltula).
- **What is done** (new `tools/drop_tables.py`):
  - each family gets a drop table of ours with one item, its last level's drop (`Type` 126134492, the kind of
    item that names one actor, as Gohma's heart; `IsReplace: True`): `NX2_<last level>` on rocks, bushes and
    pots, `NX2_GS_<last level>` on Gold Skulltulas (made from the token's table);
  - the tables are listed in a drop part of our own name (a copy of the actor's, the game's tables first), and
    the rock's, bush's, pot's or skulltula's file names it (`DropRef`). No game file changes content: a game file
    read from another pack could be kept as it was;
  - the placement names the table (`Drop__DropTable`) and no actor, set in the map as the game does (no AI
    writes it);
  - the droppers' added AI also hands over its mark when its placement names a table starting with `NX2_`
    (a second copy of the skulltula's three nodes);
  - the rows, the `Obj_NX2S_` drops and both safety nets stay. Plain items keep their direct `Drop__DropActor`;
  - the insect bushes' drop part has no one-actor table to copy: the rock's is the shape copied;
  - size rules from the game's own files (`tools/sizes.py`): a drop part 5136 + 8 per table listed (65 files),
    a drop table 5112 + 8 per sub-table (102 files).
- **Not proven:** that the rows apply to a table item naming one actor; that a replacement is replaced again
  (three levels); that a Gold Skulltula draws from `Drop__DropTable`.
- **In game (first try): still no drops** where a lower level was needed (the user stopped the run). Longshot's
  log: when the area loaded, the game loaded each table's item (the last levels: `Obj_NX2S_BulletBag_Large`,
  `Quiver_Large`, `Scale_Gold`), and never loaded a lower level during the whole session.
- **Then: the lower levels are kept loaded.** Every actor the game's own rows put in place (the green rupee, the
  heart) is on the drop code's list of actors kept loaded everywhere (`SharePreLoadActorList` in
  `DropGlobalParam`). The game seems to load only what a placement or table names, plus that list, so a
  replacement had nothing loaded to drop. Each level the rows put in place is now added to that list (one each;
  `skulltula_items.preload`); the game's entries are unchanged. Size: 256 per entry (upper bound, as for the
  rows). Not proven: that this was the cause (the replacement could also not happen at all).
- **In game (second try): still nothing from Saria's rock.** Longshot's log: the game loaded only the first 16
  entries of that list. 14 are the game's own, so ours 15 and 16 (`Obj_NX2S_Quiver_Medium`, `Range_Bow`) were
  loaded, and the bigger seed bag, the Slingshot and the Silver Scale were not. So the list is no way in, and
  the preload addition is taken out again (the list is as the game has it).
- **Then: each table lists the lower levels itself, with chance 0.** A sub-table picks one item by weight (the
  game's weights add up to 100), and the game's own tables list items with weight 0 (Gohma's: the heart at 100,
  three others at 0). Our table for a family is now its last level at 100, then each lower level at 0 (and bad
  luck rate 0), highest first: `NX2_BulletBag_Large` is BulletBag_Large 100, BulletBag_Medium 0, Slingshot 0.
  They are never picked; the idea is that the area loads every actor its tables name, as it loaded the last
  levels. Size rule from the game's files: a sub-table 5336 + 136 per item (79 of its 80 files exact; one test
  table of the game's has 4 more). Not proven: that the area loads the items at chance 0.
- **In game (third try): still nothing from Saria's rock**, but the loading works: Longshot's log shows every
  level (`BulletBag_Medium`, `Range_SlingShot`, `Quiver_Medium`, `Range_Bow`, `Scale_Silver` with the last
  levels) loaded with Kokiri Forest. So loading was not the cause. Left: either the game never replaces, or
  it replaces once only. Saria's rock needs two replacements (biggest bag -> bigger bag -> Slingshot), and a
  bigger bag that comes out without the Slingshot owned deletes itself (the safety net), which also looks like
  nothing. Next: a spot with one replacement (the House of Twins pot: Gold Scale -> Silver Scale).
- **In game (fourth check, same build): the House of Twins pot dropped nothing either.** One replacement does
  not happen: the game never puts the lower level in place for our drops, though our rows are shaped like the
  game's own (a target, a condition, one replacement at 100, and an unlock entry naming an `IsGet.` flag).
  The Gold Scale that comes out is deleted by its safety net (no Silver Scale owned).
- **Tests:** `tests/skulltula_prog_check.py`, `tests/one_time_check.py`, `tests/pairs_more_check.py` check the
  map settings, the drop parts and the tables in whole builds.

### In-game results of the combined test (gossip, raised items, Gold Skulltulas, one-time drops, pots)
Run 1 only; runs 2 and 3 were skipped because of the drop problem below.
- **Gossip stones: all passed.** The three Kokiri Forest stones and the bridge stone say their test text (the
  stone speaks, not Navi; highlight, line break, two boxes and the page break all fit). A sword hit still
  tells the time.
- **Raised items:** the Bow (Fado's ledge), Silver Gauntlets, Golden Gauntlets, Bomb Bag, Hookshot and Longshot
  lie on the ground correctly. The right hook shows on each. **The Fairy Bow is held up far above Link's hands**
  (screenshot). Not yet known whether that is our lifted pose or the game's own look for the Bow.
- **Mido's chests:** bigger quiver and Goron Bracelet, correct.
- **Bombs and Boomerang unusable until a scene change:** the Bomb Bag (Saria's floor) and the Boomerang (Know-It-All
  pot) arrive in the inventory, but the button does nothing until Link leaves the house. Both were picked up
  indoors; not yet known whether the game blocks those items inside houses.
- **One-time drops:**
  - pot: Boomerang left lying, the pot is back with it after re-entering; taken, the pot stays gone, also after
    save, quit and reload. **Works.**
  - rocks: the red-rupee rock and the Know-It-All rock stay gone. But the plain witness rocks and bushes did not
    come back either, so this does not prove the rocks' mark yet.
- **Families chosen by the drop list (rocks, bushes, pots, Gold Skulltulas): only half works.**
  - Know-It-All rock, Bow family with the Bow and bigger quiver owned: the **biggest quiver came out at once**.
    This is the one case where no replacement was needed (the drop named is the right one).
  - **Every case that needed a replacement dropped nothing:** Saria's rock and the shop bushes (Slingshot family,
    nothing owned), the Gold Skulltula above the Deku Theater (same family), the House of Twins pot and the
    night Gold Skulltula (scales, nothing owned).
  - So the game did **not** replace the drop with the lower level, and the safety net removed the too-high level
    (nothing wrong was given, no level skipped). The rows are either not used for a drop a map names directly,
    or the replacement fails.
- Noted: the spot `KF_RUPEE_NEAR_MIDO_ITEM` (Silver Gauntlets) is in the water near the shop. Cutting bushes
  gives 5 rupees.
- No freeze or crash.

### Custom gossip stone text (branch `claude/gossip-text`)
A new builder option sets what a gossip stone says. It is the groundwork for hints. **Not tested in game yet.**
- **How the game picks a stone's text** (read from the game's files):
  - Every stone runs the same flow, `GossipStone`, entry `Talk`.
  - The stone's own text is one step of that flow. It shows the text of `EventFlowMsg/GossipStone.msbt` whose
    label is the stone's name in the map (for example `GOSSIP_KOKIRI_FOREST_01`). Each stone has its own text.
  - The flow only gets there when Link owns the Mask of Truth and wears it. Without it, Navi talks instead.
    The mask is a child's item, so an adult never hears a stone. The stone also says an opening line about the
    mask first, and a closing line after. Nothing depends on the time of day.
  - The stone's own AI can tell which stone it is: the question `EventQueryGossipStoneCheckInstanceName`
    answers a number per stone name (0 to 39, 40 for any other name). No game flow asks it.
- **The option:** `--gossip STONE=TEXT`, once per stone.
  - `STONE` is the stone's check ID (`KF_NEAR_LOST_WOODS_GOSSIP`) or its name in the map
    (`GOSSIP_KOKIRI_FOREST_01`). The name in the map works for stones in areas not mapped yet.
  - In `TEXT`: `\n` is a new line, `\p` a new page, `{...}` is highlighted. Quote the whole argument.
  - The same English text goes into all 16 language archives, as with the scrub lines.
  - A bad `--gossip` (not a stone, a text that breaks a limit) stops the build before anything is written.
  - It works alone or together with item placements and fixes.
- **What the builder changes:**
  - The chosen stones' texts in `GossipStone.msbt`, in every language. Every other text stays the game's.
  - The `GossipStone` flow: `Talk` now first asks the stone which stone it is. A chosen stone does the talk
    set-up the game uses with the mask, says its text, and ends. No mask needed, no opening or closing line,
    and the "first time with the mask" flag is not set. Every other stone goes to the game's own first step, so
    it behaves as before. The time-telling and the ocarina fairy are other entries and are not touched.
  - So the chosen stones speak to a child without the mask, and to an adult too.
  - The size table gets the new entries of the flow and the 16 archives (`tools/sizes.py`, through `Output`).
- **Layout, copied from the game's rumours:** every rumour starts with colour 1, size 80 % and the dialogue
  start tag. A new page repeats the size and colour (as `GOSSIP_LOST_WOOD_01` does). Lines are broken by hand.
  - A highlight is colour 0, the game's usual highlight colour. After it the text goes back to colour 1, the
    rumour's own colour. Only this one highlight colour is offered: the game's text uses few colours.
- **Limits:**
  - 65 characters a line (the longest line of the game's English rumours). Longer lines are wrapped at spaces.
    The font is proportional, so this is a guide, not exact.
  - 2 lines a page (every rumour has 1 or 2). A third line starts a new page.
  - 8 pages at most (the most any game message has).
  - Only characters the game's English text uses. `{`, `}` and `\` are never text. The build notes any
    character a language's own messages never use (its font may lack it). None of the test texts has one.
- **Test:** `tests/gossip_check.py`, in `run_tests.bat`. It reads the game's files, checks the option and the
  layout, edits the flow and reads it back, and runs whole builds into a temporary folder. It checks that the
  chosen stones say the new text in every language, that every other text and file is the game's, that other
  stones still go to the mask question, and that the size entries are right. A build with a scrub too keeps
  both the scrub line and the stone texts.
- **To test in game** (child Link, new game, no Mask of Truth). The four stones a child reaches in Kokiri
  Forest and at the bridge (the Lost Woods map has only the bridge stone):

  | Stone | Where | Message |
  |---|---|---|
  | `KF_NEAR_LOST_WOODS_GOSSIP` | Up on the ledge with the Lost Woods entrance, behind Mido's house. Reachable at once. | Test 1: one page, two lines (wrapped), "Lost Woods" highlighted. |
  | `KF_DEKU_TREE_GOSSIP_01` | Past Mido, in the Great Deku Tree's clearing: the stone nearer the tree. Needs the sword and shield. | Test 2: two lines, from a line break. |
  | `KF_DEKU_TREE_GOSSIP_02` | The same clearing: the stone farther from the tree. | Test 3: a long text over two pages. |
  | `LW_BRIDGE_GOSSIP` | Beside the bridge to Hyrule Field, past the forest exit, near where Saria waits. Needs the forest open (after the Deku Tree). | Test 4: two pages, from a page break. |

  Build arguments (from the worktree):

  ```
  py -3 tools\build_mod.py --romfs "C:\Users\4bsol\Games\Longshot\romfs" --out out\mods --name NX2-ZOOTR --gossip "KF_NEAR_LOST_WOODS_GOSSIP=NX2-ZOOTR test 1 of 4: this stone by the {Lost Woods} speaks without the Mask of Truth." --gossip "KF_DEKU_TREE_GOSSIP_01=NX2-ZOOTR test 2 of 4: the Deku Tree stone nearer the tree.\nThis is the second line, after a line break." --gossip "KF_DEKU_TREE_GOSSIP_02=NX2-ZOOTR test 3 of 4: the Deku Tree stone farther from the tree. This message is long on purpose, so that it does not fit in one text box: the builder wraps the words into lines and carries on in a second box." --gossip "LW_BRIDGE_GOSSIP=NX2-ZOOTR test 4 of 4: the stone by the bridge to Hyrule Field.\pThis second page was asked for with a page break."
  ```

  To watch for: the stone itself speaks (not Navi); the highlight colour; whether two lines of 65 characters
  fit the box; a Sacred Forest Meadow stone (not chosen) still gives Navi's lines; a sword hit still tells the
  time. If the four stones still give Navi's lines, the stone's question did not answer as read from its AI.
- **Not done:** hints themselves, other stones' places, the frozen adult Zora's Domain stone, launched stones
  that disappear (`GossipStoneDisappear.<name>`). Not built into `out/mods`.

### The last seven items lie on the ground, not in it (branch `claude/lift-seven`)
The seven levels left low on 2026-11-21 ("their models hang on several bones"). **Not yet tested in game.**
- **Why they were left.** Their models hang on many bones, and their ground pose (`Pose_Common`) places every bone:
  19 for the slingshot, 10 for the bow, 77 and 73 for the gauntlets, 5 for the first bomb bag, 19 for the hookshot.
  The lift so far only knew models on the one bone `Skl_Root`. And the copy that keeps the held-up pose (made of the
  magic jar's project) only has two bones, so it cannot hold their pose.
- **Measured, every bone posed** (`posed_points` in `tools/item_pose.py`). Every vertex, through the skeleton:
  vertices on one bone move with it, skinned vertices (on up to eight bones) move with each bone by its weight.
  Found in the game's files: these skeletons use Maya's scale mode, and almost every bone undoes its parent's
  size before its own ("segment scale compensate"). Without that the gauntlets' pose comes out 2.3 m under the
  ground; with it they fit in a 0.44 m box. The rough numbers of 2026-11-21 were taken without it, so they were
  wrong. Checks of the measure: with no pose, the shapes the game shows give exactly the box of `ActorInfo`, for
  all seven. For every other lifted item the new measure gives the same lowest vertex as before (to 0.000001).
- **Lowest vertex, while spinning, before -> after** (the lift in brackets):

  | Item | before | after |
  |---|---|---|
  | Fairy Slingshot | -0.149 | +0.050 (+0.199) |
  | Fairy Bow | -0.378 | +0.050 (+0.428) |
  | Silver Gauntlets | -0.163 | +0.050 (+0.213) |
  | Golden Gauntlets | -0.163 | +0.050 (+0.213) |
  | first Bomb Bag | -0.143 | +0.050 (+0.193) |
  | Hookshot, Longshot | -0.200 | +0.050 (+0.250) |

  The Hookshot and the Longshot are one model and one project. Their lowest vertex is on the body both show, so one
  copy is exact for both (`GROUND_LIFT_AS`). Shapes the game hides (the slingshot's two seeds, the other hook) are
  counted too; the test checks they never lie lower than the shown ones.
- **How it is lifted.** Every vertex hangs on `Skl_Root` or a bone below it, and the pose leaves `Root` alone. So
  raising the height of `Skl_Root` raises the whole model, and nothing else changes. The copy is the item's own
  project under a new name of the same length (`NX2Gnd_Range_SlingShot_Animation`, `NX2Gnd_Range_Bow_Animation`,
  `NX2GA_Adult_Gauntlet_Silver_Animation`, `NX2GA_Adult_Gauntlet_Gold_Animation`, `NX2G_BombBag_Small_Animation`,
  `NX2G_Hookshot_Animation`). One animation is added to it: `Pose_GetDemo`, a copy of the game's `Pose_Common`,
  every bone, with values of its own. Then only the height of `Skl_Root` in `Pose_Common` is changed.
  - **Held up: the game's pose.** Held up, the game shows `Pose_GetDemo` first (`AS/Item_Common`). In the copy it is
    the game's ground pose, bone for bone, so Link holds each item as now.
  - **How the animation is added** (`add_pose_copy`): nothing in the file moves. The new parts go between the
    strings and the relocation table: the new animation, its bones and values, a new list of the animations and
    its dictionary. The header then points to the new list, and the relocation table lists the new offsets. The
    dictionary is built the way the game's are: the builder gives back all 1,284 dictionaries of the game's
    animation files exactly, and finds every name the way the game walks it. The copies are 1 to 9 KB larger
    than the game's files; their size entries keep the game files' headroom.
  - Chests, shelves and the held-up versions keep the game's files. Only the ground, Gold Skulltula drop and
    turning versions of these seven use the copies.
- **To know:**
  - the bow's pose stands it upright, 0.86 m tall: it now spins standing on its tip;
  - the hookshot's model picks its hook (short or long) with a visibility animation that its model settings name
    by a path in the game's own project (`Item_Hookshot_Animation`), not in the actor's animation list. The game
    does load such animations by path for other actors (Twinrova uses Kotake's), so the right hook should still
    show. If both hooks or the wrong one show in game, this is why;
  - the copies are the first files where the builder adds to a game file's structure (before, it only changed
    values). Read back in every way known, but only the game can say it accepts them.
- **Unchanged, byte for byte:** every other item in every version (ground, Gold Skulltula drop, turning, held up),
  1,559 builds, against the builder of `main` (68e5e89); the held-up versions of these seven too. The test holds one
  checksum over them all, and the checksums of the six new copies.
- **Files:** `tools/item_pose.py` (the posed skeleton, bone visibility, the relocation table and dictionaries,
  `add_pose_copy`; the list of animations is read from the file's header now, the same for all 1,427 game files),
  `tools/ground_items.py` (the seven listed, `many_bones`, `skeleton_low`, `lifted_with_held`, the name rule for
  `Armor_` projects), `tests/ground_lift_check.py`, `tests/families_check.py` (all 26 levels are lifted now).
  Three tests held the hookshots as unlifted and were brought in line: `tests/ocarina_fix_check.py` (the ground
  Hookshot's and the turning pair's checksums, taken again; main's old ones were checked first),
  `tests/ground_prog_check.py` (measures a model on many bones with every bone posed, allows the larger copy),
  `tests/pairs_more_check.py` (3 lifted copies in its whole build, not 2).
- **Tests:** `tests/ground_lift_check.py`, 9 lines more: the seven listed, the Longshot on the Hookshot's copy;
  their poses place many bones; their models read right (the box); hidden shapes never lower; the lowest vertex as
  measured, 0.05 above the ground on the copy; held up every bone the game's; every animation found by name, every
  new offset listed; the six copies' checksums; the new measure agrees for every other lifted item; every other
  build as before. The older lines now cover the seven too. ALL OK. The whole `run_tests.bat` in the worktree:
  edit_check and evfl_add_check all OK; chest_check, ocarina_fix_check, ground_prog_check, ground_lift_check,
  three_chest_check, gift_check, saria_check, pairs_more_check, skip_level_check, families_check: ALL OK; round trip
  as before (650 event flows identical, 264 not read, 5 BYML files differ: the known ones).
- **Check build** (scratch folder, no fixes): `KF_RUPEE_NEAR_FADO_ITEM_01` Fairy Bow, `KF_SARIAS_HOUSE_HEART_ITEM_07`
  Fairy Slingshot, `_03` first Bomb Bag, `KF_TRAINING_AREA_RUPEE_ITEM_01` and `_02` Hookshot > Longshot,
  `KF_SARIAS_HOUSE_HEART_ITEM_02`, `KF_SHOP_RUPEE_ITEM` and `KF_RUPEE_NEAR_MIDO_ITEM` Goron Bracelet > Silver >
  Golden Gauntlets. Read back from the written files: each pack names its copy, each copy has the checksum the
  test holds and ends with `Pose_GetDemo`. (Saria's floor hearts are 1.5 m apart: two levels of one family cannot
  both go there.)
- **Not yet tested in game.** To look at: each of the seven lies just above the ground while it spins (not in it,
  not floating); held up, Link holds it as the game does; the hookshot and longshot show the right hook.

### Upgrade families on Gold Skulltulas (branch `claude/skulltula-progressive`)
Every upgrade family can now be placed on a Gold Skulltula, as a pair or with three levels. **Not tested in game
yet.** The details, what is not proven and the proposed test are in `out/RESEARCH_skulltula_progressive.md`.
- **How to place it:** as everywhere else, for example `KF_KNOW_IT_ALL_HOUSE_GS=Item_Scale_Silver>Item_Scale_Gold`.
  The skulltula drops the lowest level Link never got. It can be mixed with chests, rocks, gifts and the other
  kinds. The Lost Woods skulltulas have no IDs yet: use their names, in quotes
  (`"LW GS Above Theater=Item_Scale_Silver>Item_Scale_Gold"`).
- **Why the turning item could not be used.** A Gold Skulltula is marked done when its drop is picked up, not
  when it dies. The skulltula hands its saved flag to the one thing it drops. Nothing in the game can pass that
  flag on to a second item. So an item that turns into the next level would not mark the skulltula, and the
  skulltula would come back with another level.
- **What is done instead: the game's own drop rules choose the level, before anything is dropped.**
  - The game has two lists for all drops. One says "this is only dropped once something is true" (bombs once a
    scrub sells them, bugs, Deku Sticks only as a child). The other says "until then, drop this instead".
  - The game also remembers "Link ever got this item", for every item.
  - So the skulltula is told to drop the **last** level. One row in each list per level says: "only once Link
    ever got the level before; until then, drop the level before". With nothing owned, that leads down to the
    first level.
  - Only one item comes out, dropped by the skulltula itself. It carries the skulltula's flag, like every item
    from a skulltula in this mod (seen working on 2026-11-17). Picking it up marks the skulltula done, once.
  - A drop left lying is gone when the area is left. The skulltula is then back and drops the right level
    again. That is how the game treats its own tokens.
- **A safety net against skipping a level.** Each level after the first deletes itself if Link does not own the
  level before. So if the drop rules work differently than read, the worst case is a skulltula that drops
  nothing. A level is never skipped.
- **The Fairy Slingshot and the Fairy Bow come with their bag and 30 seeds or arrows**, as on rocks and bushes.
- **Not changed:** the Gold Skulltula itself, the token, the turning items, the game's shared flows. A single
  item on a skulltula is built as before. The game's drop-rule file only gets new rows about our own items; the
  game's rows stay as they are. A build with no family on a skulltula does not touch that file.
- **Not proven (only the game can show):** that the drop rules are used for an item a map names on a skulltula;
  that the item put in place still carries the skulltula's flag; for three levels, that the rules are checked
  twice (last level, then second, then first); that "Link ever got this" is set however he got it; that the
  item put in place loads in time; the bag on a slingshot from a skulltula; the memory size given to the
  drop-rule file.
- **To watch for in game:** a skulltula that drops nothing; a skulltula that is back after its drop was picked
  up; the first level again although Link has it; a slingshot with 0 seeds.
- **Files:** new `tools/skulltula_items.py`; `tools/build_mod.py`; `tools/sizes.py`; new
  `tests/skulltula_prog_check.py` (in `run_tests.bat`); one check each in `tests/families_check.py`,
  `tests/three_chest_check.py` and `tests/pairs_more_check.py` (they expected a family on a skulltula to be
  refused).
- **Tests:** the new `tests/skulltula_prog_check.py` has 29 checks. It reads from the game how a skulltula is
  marked, the two drop lists and the "ever got" flag of every level. It builds every level's item for all 11
  families. From the rows it works out, for everything Link can own, that the skulltula drops the lowest level
  he never got, every level once and in order, and that nothing wrong can be picked up if the drop rules do
  less than read. Then whole builds of all 11 families on Gold Skulltulas. The full `run_tests.bat`: all 13
  checks OK, 0 failed; the round-trip as before. logic_check: 0 failed; db_check: 0 errors; size_check: OK.

### Rocks, bushes and pots drop their item once; families on pots (branch `claude/pots-one-time`)
**Not tested in game yet.** The research, what is not proven and the proposed test are in
`out/RESEARCH_pots_one_time.md`.
- **The problem.** A rock, a bush or a pot comes back when the area is loaded again. It then dropped its item
  again. With a family it gave the next level, so one check gave two levels.
- **What is done: the Gold Skulltula's own way of being done once.**
  - A Gold Skulltula hands its saved flag to what it drops. When that item is picked up, it sets the skulltula's
    two saved flags (read in the game's code). The skulltula then stays gone.
  - Every rock, bush and pot check has the same two saved flags: one that is reset, and a second one that is
    never reset (checked for all of them).
  - Now every randomized rock, bush and pot hands its flag to its drop, as the skulltula does. Its drop is a
    version of the item with the token's "picked up" step: `Obj_NX2O_<item>` for a plain item,
    `Obj_NX2Q_<level>` for a level of a family, and the Gold Skulltula version for a rupee or a heart.
  - The rock, bush or pot gets an AI of its own name: the game's AI, unchanged, plus one branch that only acts
    when its drop is one of ours. Game rocks, bushes and pots take the other side, which does nothing.
  - Left lying and not picked up: nothing is marked. When the rock is back, it drops the item again.
- **Not proven, and the key point of the test:** that a rock, a bush or a pot whose second flag is set is not
  made again. That is what keeps a Gold Skulltula away, but its first flag is never reset either, so the files
  do not tell which flag does it. If the rock comes back, it drops its item again, as before.
- **Found and dropped:** the "done already?" question of the game's cow skulls and hanging signs does not work
  for rocks, bushes and pots (it needs a setting they do not have, and it reads a named flag they do not have).
  It is not used.
- **Families on pots.** Every family (pairs and three levels) can now be put on a pot, as on a rock or a bush:
  `KF_HOUSE_OF_TWINS_CHILD_POT_01=Item_Scale_Silver>Item_Scale_Gold`. The Fairy Slingshot and the Fairy Bow
  bring their bag, the pick-up guard is the turning item's, and the drop is given once.
- **Crash fixed (in-game test, 2026-11-22):** the game crashed near the Know-It-All rocks once Link had the Fairy
  Bow. The rock's AI tried to rename its drop to the next level, and the game crashes when an AI writes that
  setting (it comes from the map). The rocks, bushes and pots no longer rename their drop. A test now checks
  that nothing we build writes such a setting.
- **Families on rocks, bushes and pots now work like Gold Skulltulas (after the crash, at the user's request).**
  The first fix let the item come out as placed and turn into the next level on the ground; the user did not
  want players to see a level they already have. Now:
  - the rock's drop names the family's last level, and the game's drop list drops the lowest level Link never
    got in its place, before anything comes out (`tools/skulltula_items.py`, the same rows as the skulltulas);
  - what comes out is the same actor a Gold Skulltula drops (`Obj_NX2S_<level>`, built from the token), so it
    marks the rock when picked up exactly as it marks a skulltula. No turning item, no `Obj_NX2Q_` version;
  - **new safety net on every family drop (skulltulas too):** a level Link already owns removes itself without
    marking anything (two drops of one family lying at once, or the level got elsewhere while it lay there).
    The rock or skulltula comes back later with the next level. The old net stays: a level whose level before
    Link does not own removes itself;
  - every level, the first included, is now an `Obj_NX2S_` actor (the first level used to be the plain token
    version), so the first level has the safety net too;
  - two family drops on rocks, bushes or pots closer than 2 m are refused, as two turning items are.
- **Not proven (shared with the skulltulas):** that the game uses the drop list for a drop a map names
  directly. If not, the drop removes itself: nothing comes out, never a wrong level.
- **Files:** new `tools/once_items.py`; `tools/build_mod.py` (pots in `PAIR_KINDS`, `DROP_KINDS` for rocks,
  bushes and pots, the one-time versions and droppers, the flag check); `tools/skulltula_items.py` (every level
  its own actor, the owned-level safety net); small changes in `tools/turn_items.py` and `tools/ground_items.py`;
  new `tests/one_time_check.py` (in `run_tests.bat`); pots added to `tests/families_check.py`; pots no longer
  refused in `tests/gift_check.py`, `tests/ground_prog_check.py`, `tests/pairs_more_check.py` and
  `tests/three_chest_check.py`.
- **Tests:** the whole `run_tests.bat` passes (all checks OK; the round-trip shows only the known differences).
  `tests/one_time_check.py`, 22 lines: the two saved flags of every rock, bush and pot check; that no game
  placement names one of our drops; the game nodes copied; every version with the mark (and, with the mark
  taken out, node for node the turning item); the droppers' AI read back from the files; every order of a
  family's checks, picked up or left behind; a whole build. `tests/families_check.py` now builds all 11
  families on the 8 pots of Kokiri Forest. `logic_check` and `db_check` pass.

## 2026-11-21

### Progressive upgrade families, everywhere a pair can go (branch `claude/progressive-families`)
The user's list of upgrade families is now in the builder. Every family can be placed in its progressive form on
every kind of check that pairs already worked on. **Nothing new here is tested in game yet.** The details and the
proposed test are in `out/RESEARCH_families.md`.
- **The families** (the user's list; declared once, `FAMILIES` in `tools/build_mod.py`):

  | Family | Levels, lowest first (the game's names) | Written as |
  |---|---|---|
  | Seed bags | Fairy Slingshot (with its Deku-Seed Bag) > Bigger Deku-Seed Bag > Biggest Deku-Seed Bag | `Item_Range_SlingShot>Item_BulletBag_Medium>Item_BulletBag_Large` |
  | Quivers | Fairy Bow (with its Quiver) > Bigger Quiver > Biggest Quiver | `Item_Range_Bow>Item_Quiver_Medium>Item_Quiver_Large` |
  | Strength | Goron Bracelet > Silver Gauntlets > Golden Gauntlets | `Item_Gauntlet_Goron>Item_Gauntlet_Silver>Item_Gauntlet_Gold` |
  | Bomb bags | Bomb Bag > Bigger Bomb Bag > Biggest Bomb Bag (as before) | `Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large` |
  | Deku Stick bags | Bigger Deku-Stick Bag > Biggest Deku-Stick Bag | `Item_StickBag_Medium>Item_StickBag_Large` |
  | Deku Nut bags | Bigger Deku-Nut Bag > Biggest Deku-Nut Bag | `Item_NutBag_Medium>Item_NutBag_Large` |
  | Wallets | Adult's Wallet (500) > Giant's Wallet (1000) | `Item_Wallet_Medium>Item_Wallet_Large` |
  | Magic | the magic meter (the game's name: "Gift of Improved Spin") > Gift of Doubled Magic | `Item_FairyBless_MP>Item_FairyBless_MPDouble` |
  | Scales, hookshots, ocarinas | as before | `Item_Scale_Silver>Item_Scale_Gold`, `Item_Hookshot>Item_Longshot`, `Item_Ocarina_Fairy>Item_Ocarina_Time` |

  - Deku Sticks and Deku Nuts themselves are not placed (the user: they come from enemies and shops). Their first
    bags and the Kokiri Wallet (the one from the start) are still refused everywhere (`NEVER_GIVEN`).
  - The names of the gauntlets and of the two magic items were checked in the game's item table: they are the
    ones above. Strength is one family, as asked.
- **How to place a family:** put the same text on as many checks as the family has levels, for example three
  checks with `Item_Range_SlingShot>Item_BulletBag_Medium>Item_BulletBag_Large`. Each check gives the lowest level
  Link does not have yet. The checks can be of different kinds.
- **Where a family can go** (pairs and three levels alike):

  | Kind of check | Two levels | Three levels |
  |---|---|---|
  | Small chest | the game's checking chest (as before) | a chest of our own per family (was: bomb bags only) |
  | Freestanding item | turning item (as before) | turning item with three levels: **new** |
  | Liftable rock | turning item as its drop (as before) | the same with three levels: **new** |
  | Solid bush | turning item as its drop (as before) | the same with three levels: **new** |
  | Deku Scrub that sells once | one question in its branch (as before) | two questions: **new** |
  | Gift with flow data | one question in the giver's flow (as before) | two questions: **new** |

  All eleven families build on all six kinds. The bomb bags now work on all six too.
- **Still refused, with a message:** a big chest (it has no checking version), shop shelves, pots (not started,
  the user's call), Gold Skulltulas, cutscene gifts (Saria's ocarina) and songs. The reasons are the ones found on
  2026-11-20. Nothing new was found for them.
- **The Fairy Slingshot and the Fairy Bow as first levels.** Found in the game's files:
  - the game gives both from chests only (the Deku Tree, the Forest Temple). None of its 914 event flows names
    them;
  - the first Deku-Seed Bag and the first Quiver ("small" in the files) are separate items. No chest, map or flow
    gives them. The shared chest AI adds them: when a chest is opened and Link never had the weapon in it, the
    chest adds the bag and 30 seeds (or the quiver and 30 arrows) without showing them (`TreasureBox.module`, the
    small module inside it). That is why a slingshot from a chest came with 30 seeds and one from a scrub with 0;
  - the bag fills itself when it is added, so adding the bag alone also gives 30.
  - **So the first level is the weapon, and the builder makes sure the bag comes with it on every kind:**
    - chest: the game's own chest AI does it, as for the Deku Tree chest. Nothing is added;
    - freestanding item, rock, bush: the weapon's turning item does what the chest does. It uses copies of the
      chest's own two steps (add the bag, add 30 seeds), read from the game's file by the weapon's name. It does
      so when Link touches it, and again as soon as Link owns the weapon, both only while Link has no bag. So the
      bag is given once;
    - gift and scrub: the bag is added silently right after the weapon, as scrubs already did
      (`SCRUB_COMPANIONS`). Gifts did not do this before. Now they do, also for a weapon placed alone on a gift.
  - A weapon placed **alone** on the ground or in a pot still comes without its bag. The build now says so and
    names the family form to use.
- **Three levels on the ground.** The turning item has one actor per level. Level 1 turns into level 2 once Link
  owns level 1, and level 2 into level 3 once Link owns level 2. The last one deletes itself once owned. Every
  level keeps the pick-up guard of 2026-11-20 (it does not turn while Link is picking it up). The two-level
  turning items are byte for byte what they were.
- **Three levels on a gift and at a scrub.** One more question of the same kind in front of the first: "has the
  second level?" Yes: give the third. No: the old question, "has the first level?". The questions use the names
  the game's own flows ask about: the weapons and the gauntlets are kept in the inventory under another name
  (`Weapon_Range_Bow`, `Armor_Child_Gauntlet_Goron`, `Armor_Adult_Gauntlet_Silver`...), read from the game's
  table. The game's shared flows are only called, as before.
- **Deku-Stick and Deku-Nut bags at a scrub.** The game's own scrubs already sell these two pairs, so they were
  refused there before ("another scrub would sell it too"). Now the pair is accepted when the game's own branch
  sells exactly the same two bags at the same price (it does: 40 rupees). One difference: the game's stick-bag
  scrub sells the Bigger Deku-Stick Bag to anyone who never had a Deku Stick, even if he has that bag already.
  Ours asks the inventory only, so no bag is sold twice. The scrub then says our general sales line, not the
  game's own.
- **The skip-level guard is part of this branch** (it was the unmerged `claude/skip-level-guard`; its own section
  is below, under 2026-11-20). Changed here: its families are now the one list above, so the guard and the
  progressive forms cannot disagree. Every later level placed alone is refused, and the message always names the
  form to use (before, seven families had none). First levels placed alone still build.
- **How the levels look.** Every level of every family has a ground version, a turning version and a held-up
  pose for chests (26 levels checked). 19 of them lie on a lifted copy of their pose. **Seven keep the game's own
  pose and may sit partly in the ground:** Fairy Slingshot, Fairy Bow, Silver Gauntlets, Golden Gauntlets, the
  first Bomb Bag, and (as before) Hookshot and Longshot. Their models hang on several bones, or their pose places
  several bones, so the lift cannot be measured or made the way it is for the others. Measured roughly: slingshot
  about 0.17 m low, bow about 0.24 m, the first Bomb Bag about 0.14 m. The gauntlets could not be measured. Held
  up, all seven are as the game shows them.
- **Not changed:** the game's shared flows (`Dm_SY_GetInEvent`, `Dm_SY_Get`, `GetPouchContent`,
  `Dm_SY_Treasurebox`, `Dm_SY_TreasureboxSmall`), the game's chest AI, Link's real items, pots. Every item goes
  into the inventory as itself, so capacity, refill and the menu are the game's own.
- **Files:** `tools/build_mod.py` (the families, the guard, three levels on gifts and scrubs, the bag on gifts),
  `tools/turn_items.py` (three levels, what a chest gives with a weapon), `run_tests.bat`; new
  `tests/families_check.py` and `tests/skip_level_check.py`; small changes in `tests/chest_check.py`,
  `tests/three_chest_check.py`, `tests/gift_check.py`, `tests/ground_prog_check.py` (they keep looking at their
  own three pairs or the bomb bags; the new test looks at every family).
- **Tests:** new `tests/families_check.py` (in `run_tests.bat`), 39 lines. For every family: the list is the
  user's; what the game's chests give with the two weapons, read from the game; every level's ground, turning and
  held-up version; the turning items (each level asks for itself and turns into the next, the two weapons give
  what a chest gives); the three-level chests; the questions on the gift and at the scrub. Then, worked out from
  the built files: the checks of a family give its levels in order whatever kind they are, and one check more
  gives nothing. Then whole builds: every family in small chests, on freestanding items, on rocks, on bushes and
  on the gift, and four families at the scrub. `tests/skip_level_check.py` (20 lines): the guard against the same
  list.
  Both ALL OK. The whole `run_tests.bat` was run in the worktree: edit_check and evfl_add_check all OK;
  chest_check, ocarina_fix_check, ground_prog_check, ground_lift_check, three_chest_check, gift_check,
  saria_check, pairs_more_check, skip_level_check, families_check: ALL OK; round trip as before (650 event
  flows identical, 264 not read, 5 BYML files differ: the known ones); `logic_check`: 0 failed; `db_check`:
  0 errors.
- **Check build** (scratch folder, the six usual fixes): the proposed in-game test, 20 checks in Kokiri
  Forest with eight families on chests, rocks, bushes, freestanding items, the gift and the scrub, wrote 74
  files without complaint. Not built into `out/mods`.
- **Not yet tested in game.** To watch for:
  - a slingshot or bow from the ground with 0 seeds or arrows (the bag step did not run);
  - a level given twice or skipped when the checks of one family are of different kinds;
  - the third level coming out of a rock or bush when Link has the first two (the item turns twice in a row);
  - the Goron Bracelet question (the chest and the turning item ask under the item's name, as the game's chests
    do for the bow; not seen in game for the gauntlets);
  - the scrub's line naming the right level with three levels.
- **Limits:** the mapped areas have one gift and one scrub of the right kind, so three levels on a gift or at a
  scrub can each be tested with one family per build. A rock or bush that comes back gives the next level, as
  before. Seven levels are not lifted (above).
- **In game (2026-11-22, two runs, child Link; placements as proposed above):**
  - **Order and counts: right in both runs.** Every family gave its levels in order, whichever kind came first:
    stick and nut bags from rocks, bushes and the shop floor; the Fairy Slingshot with 30 seeds from a rock and
    from the rock-circle Kokiri's gift; the Fairy Bow with 30 arrows from the ground and from a chest; bigger
    and biggest seed bags and quivers from chests, rocks, bushes, the gift and the ground (the item near Mido
    already lay there as the biggest quiver); the Goron Bracelet from a rock and from the scrub, the Silver
    Gauntlets from a chest, the Golden Gauntlets from a rock; both wallets from bushes and Fado's ledge; the bomb
    bags from rocks and bushes; the magic meter from Mido's chest.
  - **The scrub's line named the right level both times** (Goron Bracelet first, Golden Gauntlets last). The
    Golden Gauntlets were not bought in run 1: not enough rupees.
  - **Two spots were never reached: `KF_SARIAS_HOUSE_HEART_ITEM_01` and `_05` are not in the house.** In the
    map they stand about 6 m above the house floor (y 117.5 against 111.75 for `_02`, `_03`, `_04`, `_07`), on
    Saria's roof, with `_06`. Only the four floor hearts were seen, so the magic upgrade and the biggest bomb
    bag stayed where they were. Progression still held: the next spot gave the next level (Mido's chest gave
    the magic meter, the beside-Mido bush the bigger bomb bag).
  - **The Fairy Slingshot sits in the ground** (one of the seven items not lifted yet), as expected.
  - Not filled in: run 2's Mido's chests, the menu at the end of run 1, and run 3.

## 2026-11-20

### An ocarina from a chest or from the ground can be played at once (branch `claude/ocarina-fix`)
The problem: an ocarina from a chest, a pot or the ground went into the inventory, but Link could not play it
until the area was loaded again. Two fixes, one for chests and one for the ground. **Neither is tested in game
yet.** The reasons and the other options are in `out/RESEARCH_ocarina_chest.md`.
- **Chests: an opening event of our own.**
  - A chest that holds an ocarina now names an opening event of ours (`GetEventName` in the map). Our event
    does five steps: Link joins, the chest's usual opening event runs to its end, one frame passes, the game
    matches Link's equipment to his inventory, and the game waits until his equipment is made.
  - This is how the game itself wraps 36 of its chests (`SubEvent_GetIceArrow_OpenTBox` is the one copied). The
    last three steps are the game's own, from the Dream world's boss fights. They already ran without harm
    after the rock-circle Kokiri's ocarina.
  - The usual event is read from the game, not assumed: the event the chest's placement names, else the one in
    the chest's own files. Small chests: `Dm_SY_TreasureboxSmall`. Big chests: `Dm_SY_Treasurebox`. Mido's
    chests: `KokiriForest_TreasureBox_NaviChatOff`. There is one event of ours per usual event used.
  - It covers an ocarina alone, and a Fairy Ocarina > Ocarina of Time pair (the checking chest). A pair's chest
    runs our event whichever ocarina it gives.
  - New in the mod: one flow file (`Event/EventFlow/NX2_TBoxSync`), and one row per event in two tables
    (`RSDB/EventSetting`, `RSDB/GameAnalyzedEventInfo`). The rows are copies of the Ice Arrow chest's rows with
    our names.
  - **Not changed:** the game's shared flows (`Dm_SY_Treasurebox`, `Dm_SY_TreasureboxSmall`, `GetPouchContent`,
    `Dm_SY_Get`, `Dm_SY_GetInEvent`). Chests without an ocarina are as before.
  - Refused for now: a usual event that itself runs other events, and the three-level chest (no family with
    an ocarina exists).
- **Ground: the ocarina's own settings on our ground versions (an experiment).**
  - A pick-up from the ground has no event of its own to add steps to, so the chest fix cannot be used there.
  - In the game, every actor that stands for an ocarina and makes it playable carries the ocarina's settings
    (`OcarinaParam`, in its parameter table). The menu's `Pouch_Ocarina_Fairy` does. Ours did not.
  - Now the ground version (`Obj_NX2_Ocarina_Fairy`, `_Time`) and the turning version used by pairs
    (`Obj_NX2P_Ocarina_Fairy`, `_Time`) get a parameter table of their own. It inherits the ground item base's
    table and names the ocarina's own settings file (the Fairy Ocarina's or the Ocarina of Time's). That file
    is copied into the pack from the ocarina's own pack, as the menu's version has it.
  - It lives in the shared builders (`tools/ground_items.py`, used by `tools/turn_items.py`), so it also covers
    an ocarina from a pot, and pairs on rocks and bushes once that branch is merged.
  - Whether this is what makes the ocarina playable is a guess: that part is in the game's code.
  - **Not changed:** every other ground and turning item (byte for byte), the held-up versions a chest shows,
    and what a Gold Skulltula drops.
- **Tests:** new `tests/ocarina_fix_check.py` (in `run_tests.bat`), 28 lines. It builds a mod into a temporary
  folder and reads it back: the flow has the five steps for each usual event and nothing else; both tables
  have our rows, sorted, and every other row as it was; the size table has the new files; only the chests
  that hold an ocarina name our event (plain small, big, Mido's, pairs), every other actor of the maps names
  what it named; the ground and turning ocarinas carry the settings, and without them every file of their
  packs is as before; other ground items, turning items, held-up versions and Gold Skulltula drops have the
  same checksums as before. ALL OK, and the rest of `run_tests.bat` passes.
- **To test in game:** a Fairy Ocarina in one of Mido's chests, and one on the ground or from a rock. Play it
  straight after each, before any door.
- **Risks to watch for:** a chest with an ocarina that does not open, or the game stopping at it (a wrong
  row or flow); the game treating the ocarina on the ground as one in Link's hands (odd looks or a crash when
  the item appears).
- **In game (2026-11-20, combined test of the pairs, ocarina fix, Light Arrow and bigger bags branches together):**
  - **Chest (option 1): works.** Mido's chest gave the Ocarina of Time after the rock's Fairy Ocarina (run 1), and
    the Fairy Ocarina first (run 2); both played straight away, inside the house, before any door;
  - **Ground (option 3): does not work.** The Fairy Ocarina from the rock could not be played straight away (run 1).
    In run 2 the Ocarina of Time from the rock went into the inventory and the menu, but Link still played the Fairy
    Ocarina, even after a change of scene.
- **Ground, second try: the real ocarina named as Link's equipment** (replaces the first try, which is taken out).
  - Why the first try failed (read in the game's code, `out/RESEARCH_ocarina_ground.md`): when an ocarina is
    added, the game saves it as the one Link plays, and asks Link to make his ocarina under the name of the item
    it was handed. Ours handed over the ground item's own name, which is not a piece of equipment, so nothing
    was made. The ocarina's settings (the first try) are never read there.
  - The game's own ground Deku Shield has the same problem and solves it in two places: its row in
    `PouchActorInfo` names Link's shield (`AdultEquipment`, `ChildEquipment`), and its parameter table names it
    too (`PlayerEquipmentActor`, a small file in its pack).
  - Now the ground and turning ocarinas do the same, naming the real ocarina (the Fairy Ocarina or the Ocarina
    of Time). Their parameter table is the ground shield's with the names changed. The ocarina settings file
    and the first try's table are gone.
  - Chests are not changed: they keep the opening event, which works.
  - **Not yet tested in game.** If it fails, it should fail as before (the ocarina only plays after a load).
  - Tests: `tests/ocarina_fix_check.py` now checks the table, the equipment file, the two row fields, that the
    ground shield names Link's shield the same way, and that nothing else in the packs changed. ALL OK.
- **In game (2026-11-20, retest of the second try, same build with the pairs branch and the Longshot guard):**
  - **Ground: works.** Rock first: the Fairy Ocarina played straight away, before any door. Chest first, then
    the rock: Link played the Ocarina of Time straight away (the case that failed before).
  - **Chest while Link already has a working ocarina: works.** After the rock's Fairy Ocarina, Mido's chest gave
    the Ocarina of Time, and Link played the Ocarina of Time straight away, inside the house.
- **Merged after the pairs branch:** `tests/ocarina_fix_check.py` takes the turning items' checksums as main now
  builds them (the pick-up guard changed their AI), and the whole-build check of `tests/pairs_more_check.py`
  also expects the ocarina chest event's flow and two tables.

### Progressive pairs on rocks, bushes and Deku Scrubs (branch `claude/pairs-more-places`)
`CHECK_ID=First>Second` (`PROGRESSIVE_PAIRS`) is now also accepted on a liftable rock, a solid bush and a Deku
Scrub that sells one thing once. Looked at kind by kind: rocks and bushes, Gold Skulltulas (the drop and the
rewards), scrubs, shop shelves. Pots were not started (the user's call) and stay refused.
- **Rocks and bushes: the turning item as their drop. Found** (all in the game's files):
  - rocks, bushes and pots drop through one drop part, `Component/DropParam/Drop_ResourceSupply_00` (the same
    file in `Obj_LiftRock_A_01`, `Obj_Plant_Grass_A_01` and `Obj_Pot_A_01`), on the base `DropParam/Default`,
    whose table (`BlackboardParamTable/Drop`) holds the placement's `Drop__DropActor`. The game names a drop on
    its own rocks and bushes (`Obj_LiftRock_A_01` with rupees in Desert Colossus, 14 placements;
    `Obj_Plant_Grass_A_01` with a blue rupee in Hyrule Field, Deku Seeds in the Deku Tree);
  - the turning item's own drop part stands on the same base and table, and a turning item made by a drop is
    what the second level of every pair already is (seen working in game on freestanding pairs).
- **Built:** the rock's or bush's `Drop__DropActor` becomes First's turning item (`Obj_NX2P_<first>`,
  `tools/turn_items.py`), the same actor a freestanding pair uses. No new actor, AI or table. What comes out is
  First while Link doesn't own it; once he does, it drops Second's in its place and removes itself; with both
  owned nothing is left. Decided where the item lies, not when the rock breaks. `PAIR_KINDS` has `rock` and
  `bush`; `TURN_KINDS` are the kinds whose pair is a turning item. The 2 m rule between two items of one family
  holds for where rocks and bushes stand (two rocks of the circle's ring, 1.9 m apart, are refused).
- **Deku Scrubs: the question in the scrub's own branch. Found** (`Enemy_Scrub_Business_Common`):
  - the game's own upgrade scrubs are a pair already: the stick-bag scrub's map setting is
    `Item_StickBag_Medium`, and its branch asks `PouchSystemActor.EventQueryIsExistInPouch {Num: 1, Actor:
    Item_StickBag_Medium}` (`Event319`): 0 (Link has it) -> the one-time sale of `Item_StickBag_Large`, 1 -> of
    `Item_StickBag_Medium`, same price and line. The nut-bag scrub the same (`Event323`);
  - what keeps a one-time scrub gone is its talk entry (it sets the scrub's sold flag after a buy), whatever
    was sold;
  - the flow writes scrub item names (`EventTriggerSetGameDataString64` on `Scrub_Business_TempItemName_02`)
    and waits (`EventSystemActor.EventWait`, 1 frame) before the step that reads them.
- **Built** (`scrub_flow_edit`, point 4; `scrub_pair_kind`, `scrub_pair_template`, `scrub_pair_read`,
  `scrub_pair_check`): the scrub's map setting names First, and the builder's branch for First asks the game's
  question in front of the sale: Link has no First -> the one-time sale of First, as before; else First's name
  in `Scrub_Business_TempItemName_00` is written over with Second's, the flow waits 2 frames
  (`SCRUB_WRITE_WAIT`), and the same sale runs with Second, at the scrub's price. The name is written because
  the generic line names the item from it and an item Link can't hold up (an ocarina) is sorted out by it in
  front of the pay-and-get call. Six new steps; no new actor, action or question (the flow has all three); the
  shared flows `Dm_SY_GetInEvent` / `Dm_SY_Get` are only called, as before. Refused: a pair on a scrub that
  sells again and again, a second scrub selling First alone or Second beside the pair, a pair with an item that
  needs a companion.
- **Not built, and why** (the full reasons, with the designs in order of safety, are in the research file):
  - **Gold Skulltula drops.** The drop must carry the skulltula's saved flag (what marks it done). The game has
    no node that hands it from one drop to the next: `QueryBlackboardOverwriteParamAddNoRespawnGmdHash` (the
    skulltula, the Gohma egg) hands over a placed actor's own flag, and nothing reads a 64-bit value from an
    actor's own table. The plain turning item would never mark the skulltula (it would come back and give both
    levels); a token-built one would lose the flag when it turns. Next step: one small test of a skulltula
    whose placement names a drop table with two entries (both levels dropped at once, each deciding for itself).
  - **Gold Skulltula rewards** (the House of Skulltula): gifts with a flow (`GatheringTokenGold` calls
    `Dm_SY_GetInEvent`), so the gift's question fits; Kakariko is not in the check data yet.
  - **Shop shelves.** The shopkeeper's list names one actor per shelf and the game's code gives that actor's
    own item; a choice could only be made in `DisplayShop`, shared by every shop. A lock (Second's shelf
    released by `IsGet.<first>`) is possible with settings alone, but it is not a pair.
- **Known limits of what was built:**
  - a rock or bush that comes back (their saved flag is reset, type 88) gives the next level, as it gives a
    plain item again today: no level is skipped or given twice, but "one level per check" holds only while
    rocks stay gone;
  - a rock carried and thrown onto another item of its family is not covered by the 2 m rule;
  - the first level made by a drop has not been seen in game (placed in the map it has; the second level made
    by a drop has).
- **Tests:** new `tests/pairs_more_check.py` (in `run_tests.bat`), 31 lines: the kinds accepted and refused; the
  drop part shared by rocks, bushes and pots and the turning item's on the same base; the game's own rocks and
  bushes with a drop; the two map edits (only `Drop__DropActor` added); the spacing rule; the game's question
  in the scrub flow (`Event319`), its name write and wait; the scrub branch for the scales (six new steps, the
  question, the two sales alike but for the item, the write and the wait, every step of the game's flow as it
  was, the entry points) and for the ocarinas (each given with the get window under its own name); the
  refusals; the read-back noticing swapped answers, a missing wait and a wrong name; one whole build (two
  rocks, two bushes, the scrub and a chest, three pairs) read back against a build of the fixes alone. ALL OK.
  `tests/ground_prog_check.py` and `tests/gift_check.py`: their "refused on a rock, a bush, a scrub" lines
  follow. Every test of `run_tests.bat` run: edit_check, evfl_add_check, chest_check, ground_prog_check,
  ground_lift_check, three_chest_check, gift_check, saria_check, pairs_more_check: all OK; round trip as
  before; logic_check: 0 failed; db_check: 0 errors.
- **Check builds** (scratch folder, the six usual fixes each; read back from the written files, nothing
  unexpected):
  - rocks: `KF_BEHIND_SARIAS_HOUSE_CHILD_ROCK_01` and `KF_WEST_OF_MIDOS_HOUSE_CHILD_ROCK_01` Silver > Gold
    Scale; `KF_NEAR_KNOW_IT_ALL_HOUSE_CHILD_ROCK_01` and Mido's chest `KF_MIDO_CHEST_01` Fairy Ocarina >
    Ocarina of Time (a rock and a chest of one pair);
  - bushes: `KF_NEAR_SARIAS_HOUSE_CHILD_BUSH_01` and `KF_BEHIND_SHOP_CHILD_BUSH_01` Hookshot > Longshot;
    `KF_BESIDE_MIDOS_HOUSE_CHILD_BUSH_01` and the freestanding `KF_RUPEE_NEAR_FADO_ITEM_01` Silver > Gold Scale;
  - scrub: `LW_NEAR_BRIDGE_SCRUB` (by the bridge out of the forest, 40 rupees) and `KF_MIDO_CHEST_01` Silver >
    Gold Scale;
  - all three kinds in one: `KF_BEHIND_SARIAS_HOUSE_CHILD_ROCK_01` and `KF_MIDO_CHEST_01` the ocarinas, the two
    bushes above the hookshots, `LW_NEAR_BRIDGE_SCRUB` and `KF_WEST_OF_MIDOS_HOUSE_CHILD_ROCK_01` the scales.
  None of them uses the 4 adult corner rocks of the circle.
- **Not yet tested in game.** Open there: the first level coming out of a rock and a bush and turning when
  owned; the scrub's line naming the item sold; an ocarina pair on a scrub (after the scales); whether and when
  rocks and bushes come back.
- **In game (2026-11-20, combined test of the pairs, ocarina fix, Light Arrow and bigger bags branches together):**
  - rocks: the scales (rocks behind Saria's house) and the ocarinas (Know-It-All rocks, with Mido's chest) came out at
    the right level in both orders;
  - bushes: run 1 (Saria's bushes, then the shop's) gave the Hookshot, then the Longshot, both fine. Run 2 (the shop's
    first) gave the Hookshot, then **the Longshot from the bushes beside Saria's house left Link stuck in place**
    after the pick-up: camera and menu worked, but he could not move. Looked into below;
  - scrub: its line named the item, and it sold the Silver Scale first and the Gold Scale second, in both orders.
- **The stuck Longshot: most likely cause, and a guard for it** (not proven: seen once, not yet repeated; the full
  account is in `out/RESEARCH_longshot_freeze.md`).
  - **Compared:** the two bushes are the same in the built map (`Obj_Plant_Grass_A_01`, only `Drop__DropActor:
    Obj_NX2P_Hookshot` added, one link to the cut bush), the two turning items are the same files, and the
    Longshot came out of the shop's bush fine in run 1. Nothing in the data is different for Saria's bush. What
    is different there is the place: a Kokiri (`Npc_Kokiri_005_Child`) stands 0.9 m from the bush, between it
    and the other two, so where Link stands to cut it is not the same; and by chance, how close he was.
  - **Most likely:** when Link already owns the Hookshot, what the bush drops is the Hookshot's turning item
    for a few frames, until it has turned (dropped the Longshot's and deleted itself). On a rock that is thrown,
    or an item lying in the map, Link is never there in those frames; next to a bush cut with the sword he can
    be. Touching it asks for its pick-up scene; the scene has not begun, so none of the three guards holds yet,
    and the item turns: it deletes itself with its scene on its way. Link is left waiting for a scene that
    never plays (no scene running, so camera and menu work), and the Longshot dropped beside him is picked up
    normally, which is what was seen.
  - **The game guards against exactly this:** its one item that ends itself, the Poe soul, asks "is my pick-up
    asked for" (`QueryPouchContentIsRequestingGetEvent`) at the very root of its AI (`Obj_Spirit_Poe.root`: asked
    for -> nothing, in front of its vanishing). Only the Poe souls' AI files ask it. The turning items did not.
  - **Built** (`tools/turn_items.py`): the same question, copied from the Poe soul's AI, asked last before
    "Link owns this level": asked for -> no turning and no delete. The scene then plays (Link holds up the
    Hookshot he already has), and so that the Longshot is not lost, a level with a next level switches its drop
    on when it is asked for while owned: the scene ends the item with the death ground items drop on (reason
    10), which drops the next level. 3 more nodes in the last level's AI (16), 6 in the first's (28), each a
    copy of a game node. An item touched while Link doesn't own it does nothing new.
  - **Not known:** whether the question answers in those frames as the Poe soul's use suggests, and whether the
    death that ends the scene drops (read from the death table, never seen: the drop was always off). If it
    does not, that bush's Longshot is not given until the bush comes back; no freeze either way.
  - **Also looked at, and why not:** the weeding Kokiri (the three bushes beside Saria's house are his: all
    three cut sets `KokiriForest_Npc_Kokiri_005_Child_Talk_01`, `Logic/KokiriForest_Common_Level_All_01_b11a`)
    changes his lines only; his reward is given when Link talks to him, his "near" event is a balloon
    (`NPCNear`: a sub event), and all of it happened in run 1 as well. The Longshot in a child's hands: fine at
    the shop. Two items at once: the other bushes there have no drop. The pick-up scene's short form (no
    hold-up, taken when the camera has no room): not ruled out; the new question covers it if it is true
    through the scene.
  - **Tests:** `tests/ground_prog_check.py`, two new lines (the Poe soul's root asks the question and does
    nothing when asked for; the turning items ask it last, stay, and the first level switches its drop on) and
    the node counts; `run_tests.bat`: all OK, round trip as before; logic_check 0 failed, db_check 0 errors. A
    check build of the two bushes (scratch folder) wrote without complaint.
  - **In game (2026-11-20, retest with the guard):** shop bushes first, then Saria's item bush cut standing
    right against it: no freeze, Hookshot and Longshot both in the menu. The other order: Hookshot, then
    Longshot, Link moves after. Which of the guard's outcomes happened (plain Longshot, or the Hookshot held up
    again and then the Longshot) was not noted, so whether the guard itself was needed is still not proven.

### The bigger bags, quivers and wallets lie on the ground (branch `claude/big-bags-ground`)
- **Why they had no ground version** ("no PouchContentRef in its actor parameters"). Found in the game's files:
  - an actor's parameters (`Actor/<name>.engine__actor__ActorParam`) name the actor they inherit from (`$parent`)
    and list only the settings that differ. The medium bomb bag's (`Item_BombBag_Medium`) inherit from
    `Item_BombBag_Small` and name their own name, model, animation, icon and count (`ActorNameRef`, `ModelInfoRef`,
    `AnimationRef`, `CaptureRef`, `GameParameterTableRef`) but no item settings (`PouchContentRef`): those are the
    small bag's, `Component/PouchContentParam/BombBag`. The large bag inherits from the medium one, and so from
    the small one. The parents' parameter files and the item settings are in the item's own pack;
  - the same for the Deku Stick, Deku Nut and Deku Seed bags, the quivers and the wallets; their small ones name
    `Component/PouchContentParam/KeyItemDefault`. That makes **12 items**, and no other: every other item actor
    (built on `Item_EventObject_Base`, with a row in `PouchActorInfo`) names its own item settings;
  - the builder read only the item's own list (`tools/ground_items.py`, `build`), found no `PouchContentRef` and
    stopped. Their Gold Skulltula drops built already: that version reads the inherited settings too;
  - what makes a medium bag a medium bag is not in those shared settings: its count is in its own
    `GameParameter/ExpansionMaxNumActor/<item>` (`MaxNum`) and in its own row of `PouchActorInfo`
    (`AfterExpansionMaxNum`), e.g. bomb bags 20 / 30 / 40, wallets 500 / 1000.
- **Fix** (`item_components` in `tools/ground_items.py`): an item actor's item settings are read as the game reads
  them, its own, else those of the nearest actor it inherits from, in its pack. Only `PouchContentRef`
  (`INHERITED_REFS`), only for actors built on `Item_EventObject_Base`, and nothing from that base itself (its
  item settings are `Default`, no item's own). The ground version is then built as every other one: item
  settings of its own with the inherited ones as `$parent`, `DefaultAutoGet`, and `PouchActor` naming the item;
  the item's row; the item's name and model.
- **Items now possible on the ground** (freestanding spots, drops of rocks and bushes, turning items; all were in
  `GROUND_LIFT` already, so all are lifted to 0.05 and held up at the game's height): `Item_BombBag_Medium`,
  `Item_BombBag_Large`, `Item_BulletBag_Medium`, `Item_BulletBag_Large`, `Item_NutBag_Medium`,
  `Item_NutBag_Large`, `Item_Quiver_Medium`, `Item_Quiver_Large`, `Item_StickBag_Medium`, `Item_StickBag_Large`,
  `Item_Wallet_Medium`, `Item_Wallet_Large`. Still refused: `Item_StickBag_Small`, `Item_NutBag_Small`,
  `Item_Wallet_Small` (`NEVER_GIVEN`); the small seed bag and quiver still stand for their weapons.
- **What the pick-up adds is the item itself.** Read from the built packs: the ground version's own settings are
  exactly `$parent` (`BombBag` or `KeyItemDefault`), `DefaultAutoGet: true` and
  `PouchActor: Work/Actor/<item>...` (as the game's `Obj_Shield_Deku` names `Weapon_Shield_Deku`, and as every
  other ground version of ours names its item, the ones tested in game too). The item's own actor, with its
  count, is the game's file, untouched and not in the mod; the ground version's row is the item's row
  (`AfterExpansionMaxNum` the item's own); nothing of the count is in the ground version's pack.
- **Nothing else changes:** `ground_items.build` for every actor with a row in `PouchActorInfo` (393) in the four
  versions, before and after: the 1,395 that built give the same bytes; of those that stopped, only these 12
  items' ground, turn and held-up versions build now (their Gold Skulltula drops built before, unchanged). Masks,
  Poes and other actors that inherit item settings in other ways (not built on the item base) stay refused.
- **Tests:** `tests/ground_lift_check.py`, 7 lines more (33): the item actors that name no item settings are
  exactly these 12; each inherits from the smaller one, in its own pack, and its settings are that one's; its
  count is its own, in its actor's files and its row; each builds on the ground, as a Gold Skulltula drop and as
  a turning item, with one lifted copy (so the older lines now also measure their ground and turn versions);
  the built settings are exactly parent, `DefaultAutoGet` and `PouchActor` = the item, the row the item's, the
  name and model the item's, every game file in the pack unchanged; an item that names its own settings is read
  as before; actors not built on the item base, and the base, are still refused. ALL OK. edit_check,
  evfl_add_check, chest_check, ground_prog_check, three_chest_check, gift_check, saria_check: all OK;
  logic_check: 0 failed; db_check: 0 errors; size_check: OK; round trip as before (evfl 650 of 914 identical).
- **Check build** (scratch folder, the six usual fixes, 31 files; a build of the fixes alone: 11):
  `KF_RUPEE_NEAR_FADO_ITEM_01` medium bomb bag, `KF_SHOP_RUPEE_ITEM` large wallet,
  `KF_TRAINING_AREA_RUPEE_ITEM_01` large quiver, `_02` medium Deku Stick bag, `KF_SARIAS_HOUSE_HEART_ITEM_02`
  medium Deku Nut bag, `_03` large seed bag, `_04` medium wallet, `_07` large bomb bag. Read back from the written
  files: 8 of 3,639 actors changed in `KokiriForest_Child_Dynamic` and 5 of 3,674 in `KokiriForest_Adult_Dynamic`
  (`Gyaml` only); 8 rows added to each of the three tables, no other row changed; 8 packs and 8 copies new. Each
  pack names the item as `PouchActor`, its row has the item's count (30, 1000, 50, 20, 30, 50, 500, 40), the
  lowest vertex is 0.050 above the ground (the game's pose: 0.11 .. 0.26 in it), and `Pose_GetDemo` is the game's
  held-up pose.
- **To know for the test:** a medium or large bag placed alone skips a level (the medium bomb bag without the
  small one, the large wallet before the medium one): fine for a look test, not for a seed. And nothing stops a
  smaller one taken after a bigger one: what the count is then (the medium wallet after the large one, the medium
  bomb bag after the large one) is not known; take the medium one first.
- **Not yet tested in game.** Open there: each lies on the ground and is held up at the game's height; the
  inventory shows the bag itself and the new count (bombs 30 then 40, rupees up to 500 then 1000, sticks 20,
  nuts 30; seeds 50 and arrows 50 only show with the slingshot and the bow); whether taking a bag fills it
  (`IsItemStockMaxIfGet`, not on the wallets).
- **In game (2026-11-20, combined test of the pairs, ocarina fix, Light Arrow and bigger bags branches together):**
  all eight (medium Stick, Nut and Bomb bags, large Bullet and Bomb bags, large Quiver, medium and large Wallet) lie
  right on the ground, are held up normally and named in the window. **Works.** The medium Deku Stick bag, taken before
  any stick, carries 20. As placed (each bag alone, no guard), bags could be taken out of order, as expected.

### The Light Arrow lies on the ground, not in it (branch `claude/light-arrow-lift`)
The one item left low on 2026-11-19 ("it needs a copy of its own under another name").
- **Cause, confirmed** (the game's files): `Item_Arrow_Light` has no animation project of its own. Its pack names
  `Item_Arrow_Fire_Animation`, as the Fire and Ice Arrows' do. That project's `Pose_Common` puts `Skl_Root` at
  0.270. The three models are not built alike: with it the Fire Arrow's lowest vertex is +0.085, the Ice Arrow's
  +0.092, the Light Arrow's -0.057 (0.107 too low). To lie 0.05 above the ground the Fire Arrow needs the bone at
  0.235, the Light Arrow at 0.377. A lifted copy was named after the project, so the project had one copy, the
  Fire Arrow's; on that one the Light Arrow would lie lower still (-0.092). So it was not listed and kept the
  game's file.
- **Fix** (`tools/ground_items.py`): a new table `GROUND_LIFT_OWN` = {item: the name of a copy of its own}, for an
  item that shares a project but needs another height: `Item_Arrow_Light` -> `NX2G_ArrowLight_Animation` (25
  letters, as `Item_Arrow_Fire_Animation`; the Fire Arrow's copy is `NX2G_Arrow_Fire_Animation`). The Light Arrow
  is now in `GROUND_LIFT`, measured on its own model (every vertex on `Skl_Root`); `lifted_project` and
  `lifted_animation` take the item and give its copy that name. The copy is made as the Fire Arrow's: the
  project's own file with the name, one flag and the height of `Skl_Root` in `Pose_Common` changed (12 bytes of
  1,800), 0.270 -> 0.377. Lowest vertex -0.057 -> +0.050.
  - **Held up: the game's.** The project has a `Pose_GetDemo` (`Skl_Root` at -0.0225) and the copy keeps it byte
    for byte, so no jar-based copy (`HELD_BASE`) is needed.
  - The builder stops when such a name is not as long as the project's, is the shared copy's name, is used twice,
    when the project has no `Pose_GetDemo`, or when the item is also listed in `GROUND_LIFT_AS`.
- **Unchanged, byte for byte:** the Fire Arrow's copy (also the Ice Arrow's) and the ground and Gold Skulltula
  drop packs of both (the test holds their five checksums, taken from the builder as it was before this change).
  `Dm_SY_GetInEvent` and `Dm_SY_Get` are not touched.
- **Tests:** `tests/ground_lift_check.py`, five lines more: the Light Arrow uses the Fire Arrow's project and is
  the only item with a copy of its own; the copy's name (as long as the project's, no other copy's, new to the
  game); lowest vertex +0.0500 on it (-0.0574 on the game's file, -0.0925 on the Fire Arrow's copy); its
  `Pose_GetDemo` the game's, only the name and the ground pose differ; the Fire and Ice Arrows as before. The
  Light Arrow now also runs through every line for listed items (36 items, 31 copies) and is out of the "not
  listed, no copy" line. ALL OK. The other tests of `run_tests.bat`, run one by one: edit_check,
  evfl_add_check, chest_check, ground_prog_check, three_chest_check, gift_check, saria_check: all OK;
  round-trip: the same report as before (evfl 650 identical, 264 errors; byml 5 differ).
- **Check build** (scratch folder, the six usual fixes, 18 files): `KF_RUPEE_NEAR_FADO_ITEM_01` Light Arrow
  (Fado's ledge), `KF_TRAINING_AREA_RUPEE_ITEM_02` Fire Arrow (behind the crawl hole). Read back against a build
  of the fixes alone (11 files): two actors changed in `KokiriForest_Child_Dynamic` (`Gyaml` only), 2 rows added
  to each of the three tables, 2 packs and 2 copies new. `Obj_NX2_Arrow_Light` names `NX2G_ArrowLight_Animation`
  in its pack and its row; with the written copy its lowest vertex is +0.0500. `Obj_NX2_Arrow_Fire` names
  `NX2G_Arrow_Fire_Animation`, the written copy has the checksum held by the test (+0.0500). Both copies'
  `Pose_GetDemo` are the game's.
- **Not yet tested in game.** To look at: the Light Arrow on Fado's ledge lies just above the ground (not in it,
  not floating), as the Fire Arrow behind the crawl hole; picked up, each is held at Link's hands as the game
  holds it.
- **In game (2026-11-20, combined test of the pairs, ocarina fix, Light Arrow and bigger bags branches together):**
  on the ground right, held up normally, named in the window. **Works.**

### A later level of an upgrade family is never placed on its own (branch `claude/skip-level-guard`)
- Background: the user's rule, progressive upgrades must never skip a level. Every level of a family is its own
  inventory item (`IsGet.<name>`), so a later level placed alone can be taken before the earlier one. Seen in
  game (below, the ground lift's test): `Item_Scale_Gold` placed alone was taken before the Silver Scale, and
  nothing in the builder stopped it.
- **The families, from the game's own files** (new table `UPGRADE_FAMILIES` in `tools/build_mod.py`, one row per
  family, lowest level first). The order is the item table's own value (`RSDB/PouchActorInfo`), except the
  hookshots':

  | Family | Levels | The game's order |
  |---|---|---|
  | Scales | `Item_Scale_Silver` > `Item_Scale_Gold` | `DiveDepth` 6, 9 |
  | Hookshots | `Item_Hookshot` > `Item_Longshot` | the weapons' `Component/HookshotParam`: `Range` 10, 20; the Longshot's settings have the Hookshot's as `$parent` |
  | Ocarinas | `Item_Ocarina_Fairy` > `Item_Ocarina_Time` | `OcarinaTypeValue` 1, 2 |
  | Bomb bags | `Item_BombBag_Small` > `_Medium` > `_Large` | `AfterExpansionMaxNum` 20, 30, 40 (`MaxNumGameData: Bomb`) |
  | Seed bags | `Item_BulletBag_Small` > `_Medium` > `_Large` | 30, 40, 50 (`DekuSeed`) |
  | Quivers | `Item_Quiver_Small` > `_Medium` > `_Large` | 30, 40, 50 (`Arrow`) |
  | Deku Stick bags | `Item_StickBag_Small` > `_Medium` > `_Large` | 10, 20, 30 (`DekuStick`) |
  | Deku Nut bags | `Item_NutBag_Small` > `_Medium` > `_Large` | 20, 30, 40 (`DekuNut`) |
  | Wallets | `Item_Wallet_Small` > `_Medium` > `_Large` | 200, 500, 1000 (`Rupee`) |
  | Strength | `Item_Gauntlet_Goron` > `Item_Gauntlet_Silver` > `Item_Gauntlet_Gold` | `ExpansionAvility: LiftGradeUP`, `LiftableGrade` Low, Middle, High |
  | Magic meter | `Item_FairyBless_MP` > `Item_FairyBless_MPDouble` | `MPMax` 24, 48 |

  No other `Item_` row of the table has one of those values (27 rows, the 29 levels less the two hookshots).
  Not families: the double defence blessing (one level, `Item_FairyBless_DefenseDouble`); the swords (the Kokiri
  and Master Sword are a child's and an adult's sword, `EquipmentPerformance` 1 and 2, and the Master Sword is no
  item of a check; the Giant's Knife and Biggoron's Sword are trade quest items, out); the shields and tunics
  (each a different thing: `WeaponSubType`, `ArmorEffectType`, no value that orders them); the magic items (all
  `MPMax` 24, the same meter: `--fix magic_is_separate`).
- **Which level is the first:** a level that is never placed (`NEVER_GIVEN`: the small stick bag, nut bag and
  wallet) cannot be skipped, so the Medium one is the first of those three families. The game's own flows say
  the same: they ask "has Medium?" and give Medium or Large (the Deku Theater for the stick and nut bags, the
  scrubs' sales, `Dm_LostWood_0040` and `MiniGame_HitTarget` for the seed bag, `MiniGame_HitTarget` and
  `Minigame_HorsebackArchery` for the quiver), the Gold Skulltula rewards are the Medium and the Large wallet
  (`GatheringTokenGold`), and no flow names `Item_StickBag_Small` at all. The small seed bag and quiver are first levels: placed alone they still become
  the slingshot and the bow (`FAMILY_ALIASES`), so their Medium ones are later levels.
- **The guard** (`skip_level_guard`, run right after `never_given`, before the check is looked up and before
  anything is written): a later level placed on its own stops the build, on any kind of spot. The message names
  the check, the item, the family, the level it would skip, and the form to use when the builder has one:

      KF_MIDO_CHEST_01: Item_Scale_Gold cannot be placed on its own: it is the second level of the upgrade
      family Item_Scale_Silver > Item_Scale_Gold and could be taken before Item_Scale_Silver, skipping a level.
      Use KF_MIDO_CHEST_01=Item_Scale_Silver>Item_Scale_Gold (on a chest, a freestanding item or a gift with
      flow data).

      KF_MIDO_CHEST_01: Item_BombBag_Large cannot be placed on its own: it is the third level of the upgrade
      family Item_BombBag_Small > Item_BombBag_Medium > Item_BombBag_Large and could be taken before
      Item_BombBag_Medium, skipping a level. Use
      KF_MIDO_CHEST_01=Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large (on a small chest).

      KF_MIDO_CHEST_01: Item_Quiver_Medium cannot be placed on its own: it is the second level of the upgrade
      family Item_Quiver_Small > Item_Quiver_Medium > Item_Quiver_Large and could be taken before
      Item_Quiver_Small, which comes with Item_Range_Bow, skipping a level. The builder has no progressive form
      for this family yet: it cannot be placed for now.

  - Refused alone, 15 levels: `Item_Scale_Gold`, `Item_Longshot`, `Item_Ocarina_Time` (their pair is named);
    `Item_BombBag_Medium`, `Item_BombBag_Large` (the triple is named); and with no form yet, so not placeable for
    now: `Item_BulletBag_Medium` / `_Large`, `Item_Quiver_Medium` / `_Large`, `Item_StickBag_Large`,
    `Item_NutBag_Large`, `Item_Wallet_Large`, `Item_Gauntlet_Silver`, `Item_Gauntlet_Gold`,
    `Item_FairyBless_MPDouble`. Also under their other names in the item table: the inventory's twin
    `Pouch_<x>`, the gauntlets' `Armor_...`, `Obj_Ocarina_Time` (`UPGRADE_OTHER_NAMES`).
  - Still placed alone, 11 first levels: `Item_Scale_Silver`, `Item_Hookshot`, `Item_Ocarina_Fairy`,
    `Item_BombBag_Small`, `Item_BulletBag_Small` (the slingshot), `Item_Quiver_Small` (the bow),
    `Item_StickBag_Medium`, `Item_NutBag_Medium`, `Item_Wallet_Medium`, `Item_Gauntlet_Goron`,
    `Item_FairyBless_MP`.
  - Unchanged: `NEVER_GIVEN` and its message, `FAMILY_ALIASES`, the scrubs' companions, gifts, songs, the pairs
    and the triple and where they can go. The guard does not look at `First>Second` forms: only the known ones
    pass, as before. A later level is refused also when its earlier level is on another check of the same
    build (either could be reached first).
  - To add a family: one row in `UPGRADE_FAMILIES`; a form for it goes into `PROGRESSIVE_PAIRS` or
    `THREE_LEVEL_FAMILIES`, and the message names it by itself.
- **Tests:** new `tests/skip_level_check.py` (in `run_tests.bat`), 17 lines: the table against the game's files
  (every level a row of the item table; the order values above; the hookshots' `Range`; no other item with a
  level; every form a run of one family); each of the 15 later levels alone refused on 13 spots (small and big
  chest, freestanding item, shelf, pot, rock, bush, Gold Skulltula, two gifts, a scrub, a song, a name that is
  no check) with the message and nothing written; the same under the other names and with the earlier level
  elsewhere in the build; the never-given items and unknown pairs and triples refused as before; whole builds
  of the three pairs in chests, the triple, a pair on a freestanding item and on a gift; whole builds of first
  levels alone in chests, on the ground, on a gift and at a scrub (the small seed bag gives the slingshot, the
  small quiver the bow with its quiver); a refused build leaves an earlier build of the same name untouched
  byte for byte. ALL OK. No existing test placed a later level alone: none changed. edit_check,
  evfl_add_check: all OK; chest_check, ground_prog_check, ground_lift_check, three_chest_check, gift_check,
  saria_check: ALL OK; round trip as before.
- **Check build** (scratch folder): `KF_SARIAS_HOUSE_HEART_ITEM_02=Item_Scale_Silver` with
  `KF_SARIAS_HOUSE_HEART_ITEM_07=Item_Scale_Gold` (the placement seen in game) stops with the message and writes
  nothing; the pair on `KF_RUPEE_NEAR_MIDO_ITEM` and `KF_RUPEE_NEAR_FADO_ITEM_01` with a Hookshot alone in
  `KF_MIDO_CHEST_01` builds (10 files).
- **Unsure:** whether the Medium stick or nut bag taken before any stick or nut (so before the Small bag, which
  the first stick or nut then brings) keeps its size: the game sells and gives the Medium ones without asking
  for the Small one, so it is allowed here; not tried in game. The bigger seed bags, quivers, wallet, stick and
  nut bags, the gauntlets and the double magic need a form (or a rule that the earlier level is always reached
  first) before they can be placed again. Nothing to test in game: the guard only stops builds.
- **In game (2026-11-20, combined test of the pairs, ocarina fix, Light Arrow and bigger bags branches together):**
  the medium Deku Stick bag taken before any stick carries 20 (its own count, not less). The guard itself was not in
  the build: the bomb bags placed alone could be taken out of order, which is what it refuses.

## 2026-11-19

### More items lie on the ground, not in it (branch `claude/ground-lift-all`)
- **Measured:** every item the builder can put on the ground, the way the scales were (below): the model's
  vertices taken into the bone `Skl_Root`, then sized, turned and placed by the item's `Pose_Common`, plus the
  spin's 0.05 (`tools/item_pose.py`). Items the game itself puts on the ground or a shelf come out standing on
  their point (lowest vertex +0.02 .. +0.06, a few up to +0.11). Items it only ever shows held up have a pose
  centred on their point: 0.07 .. 0.28 in the ground.
- **Lifted** (`GROUND_LIFT` in `tools/ground_items.py`, 33 items more): those whose measure is sure, meaning every
  vertex of the model hangs on `Skl_Root` (checked per vertex, not only by the number of bones), and whose lowest
  vertex is more than 0.02 from the 0.05 wanted. As before: the ground, token and turn versions get a copy of the
  animation project under a new name of the same length, with only the pose's height changed; chests, shelves and
  the held-up item keep the game's file. Lowest vertex before -> after, and the change of height:

  | Item | before | after | height |
  |---|---|---|---|
  | Din's Fire, Farore's Wind, Nayru's Love (one model, one project) | -0.283 | +0.050 | +0.333 |
  | Quiver small / medium / large | -0.227 / -0.250 / -0.262 | +0.050 | +0.277 / +0.300 / +0.312 |
  | Deku Stick bag small / medium / large | -0.181 / -0.222 / -0.261 | +0.050 | +0.231 / +0.272 / +0.311 |
  | Bomb bag medium / large | -0.184 / -0.205 | +0.050 | +0.234 / +0.255 |
  | Bullet bag small / medium / large | -0.094 / -0.115 / -0.196 | +0.050 | +0.144 / +0.165 / +0.246 |
  | Deku Nut bag small / medium / large | -0.096 / -0.111 / -0.179 | +0.050 | +0.146 / +0.161 / +0.229 |
  | Megaton Hammer | -0.243 | +0.050 | +0.293 |
  | Kokiri Sword | -0.204 | +0.050 | +0.254 |
  | Wallet medium / large | -0.162 / -0.194 | +0.050 | +0.212 / +0.244 |
  | Boss key | -0.170 | +0.050 | +0.220 |
  | Dungeon map | -0.151 | +0.050 | +0.201 |
  | Gold Skulltula token (`Item_Token_Gold`) | -0.143 | +0.050 | +0.193 |
  | Magic Bean | -0.114 | +0.050 | +0.164 |
  | Fairy Ocarina / Ocarina of Time | -0.090 / -0.086 | +0.050 | +0.140 / +0.136 |
  | Stone of Agony | -0.074 | +0.050 | +0.124 |
  | Double magic / double defence blessing | -0.235 / -0.235 | +0.0502 / +0.0505 | +0.285 (the magic's copy) |
  | Fire Arrow | +0.085 | +0.050 | -0.035 |
  | Ice Arrow | +0.092 | +0.057 | -0.035 (the Fire Arrow's copy) |
  | Single arrow (`TBox_ArrowBundle_Small`) | +0.106 | +0.050 | -0.056 |

  The last three were too high and are lowered (`lifted_animation` now moves a pose either way, and refuses a
  change of 0.02 or less). To know: the game's own ground versions of two of them, `Obj_Arrow_Fire` and
  `Obj_ArrowBundle_Small`, use the same models and poses and lie at the same +0.085 and +0.106. Lowering ours is
  a choice, not a repair; taking the three out of the list undoes it.
- **Unchanged, byte for byte:** the bracelet's, the magic blessing's and both scales' copies (the test holds their
  checksums); a build of the four gives the same packs, rows and files as before.
- **Shared projects: one copy each** (`GROUND_LIFT_AS`). A copy is named after the project, so a project can have
  only one. It is now always measured on one named item, whichever item is built first, and the others are
  checked against it with their own model (within 0.01, or the build stops). A build that would write two
  different copies under one name stops too.
  - Din's Fire, Farore's Wind, Nayru's Love: the same model and project, one copy, exact for all three.
  - The double blessings use the magic blessing's project. They reuse its copy as it is (measured on the box, as
    tested in game): by their own vertices they lie 0.0502 and 0.0505 above the ground.
  - The Ice Arrow uses the Fire Arrow's project: on the Fire Arrow's copy it lies 0.057 above the ground.
  - The **Light Arrow** uses that project too, and its measure is as sure (all vertices on `Skl_Root`), but its
    model needs the bone at 0.377 where the Fire Arrow needs 0.235. One copy cannot be right for both. Left as
    it is (0.107 too low); it needs a copy of its own under another name.
  - The single arrow uses the large bundle's project (`Obj_ArrowBundle_Large_Animation`). The large bundle lies
    right (+0.042), is not listed and keeps the game's file, so the copy only serves the single arrow.
  - Names: a copy's name is the project's with its first letters changed, `Item` -> `NX2G`, `Weapon` -> `NX2Gnd`
    (Kokiri Sword), `Obj_` -> `NX2G` (token, single arrow).
- **Left out:**
  - trade quest items (the user's rule: not in the randomizer for now): Giant's Knife, Biggoron's Sword, both
    broken swords, Claim Check, Eyeball Frog, Eye Drops, Prescription, Poacher's Saw, Odd Mushroom, Odd Powder,
    Cojiro, Pocket Egg, Pocket Cucco, Weird Egg, the alarm Cucco; and Zelda's Letter and the masks, not decided;
  - vertices on more bones than `Skl_Root`, so the pose of one bone does not say where the model is, for later:
    Fairy Bow, Slingshot, Iron and Hover Boots, Hookshot and Longshot, Fishing Rod, Silver and Golden
    Gauntlets, Lens of Truth, Gerudo token, compass (its needle), small bomb bag (its two bombs), the bomb
    (`Item_Bomb`), Hylian Shield (+0.017);
  - within 0.02 of the 0.05 wanted: bottles, Boomerang, Deku Sticks, Deku Nuts, Bombchus, medium and large
    arrow bundles, large magic jar, rupees, small key, Deku and Mirror Shields, and the Deku Seed bundle (+0.070,
    just on the limit, and where the game's own `Obj_DekuSeed` lies). The Deku Scrub's seed
    (`Item_ScrubBusinessSeed`) is 0.022 low, as the game's own ground version of it: left;
  - no pose of their own, so no number that can be trusted: the spiritual stones, medallions, songs,
    `Item_Arrow_Normal`.
- **Found on the way:** the medium and large quivers, bags and wallets cannot get a ground version yet: their
  actor inherits its item settings from the smaller one's (`no PouchContentRef`), and the builder stops. Their
  Gold Skulltula drops build, and are lifted. Not changed here.
- **Tests:** new `tests/ground_lift_check.py` (in `run_tests.bat`), 17 lines, for every listed item in every
  version that builds: one copy; its name; only the name, one flag and the height differ from the game's file;
  lowest vertex 0.05 above the ground by the item's own model (shared copies within 0.01); every vertex on
  `Skl_Root`; the pack and the row name the copy; one copy per project with the same bytes whichever item is
  built (32 copies for 37 items); the size entry is the game file's; the four tested copies' checksums; no trade
  item or mask listed; items not listed get no copy. ALL OK. ground_prog_check (now also the lifted ocarinas as
  turning items), edit_check, evfl_add_check, chest_check: all OK; logic_check: 0 failed; db_check: 0 errors.
  A check build in the scratchpad (23 placements: 18 ground versions, 2 pairs, 3 Gold Skulltula drops) read
  back: 20 copies, each 7 or 8 bytes from the game's file, every actor that names one with its lowest vertex as
  above, every file with a size entry.
- **Test build** (`out/mods/NX2-ZOOTR`, the six usual fixes, 31 files), eight items on child spots in Kokiri
  Forest, each once: `KF_RUPEE_NEAR_FADO_ITEM_01` Din's Fire (Fado's ledge), `KF_SHOP_RUPEE_ITEM` Megaton Hammer
  (the shop floor), `KF_TRAINING_AREA_RUPEE_ITEM_01` small Deku Stick bag and `_02` Fire Arrow (behind the crawl
  hole), `KF_SARIAS_HOUSE_HEART_ITEM_02` Magic Bean, `_03` Stone of Agony, `_04` Gold Skulltula token, `_07`
  Fairy Ocarina (Saria's house, the four hearts at floor height). Read back against a build of the fixes alone:
  only those placements changed (8 of 3,639 actors in `KokiriForest_Child_Dynamic`, and the same checks' adult
  placements, 5 of 3,674 in `KokiriForest_Adult_Dynamic`: `Gyaml` only), 8 rows added to each of the three
  tables, 8 packs and 8 copies new. Not placed: the Kokiri Sword (its chest still gives it) and a large quiver
  or bag (no ground version, above).
- **Not yet tested in game.** Open there: whether each sits right; the six spots other than Fado's ledge and the
  shop have not been changed in game before.
- **In game (2026-11-19, combined test with the three-level chest, the progressive gift and Saria's gift):**
  - **On the ground: right.** Din's Fire, the Megaton Hammer, the Fire Arrow, the Magic Bean, the Stone of Agony,
    the Gold Skulltula token and the Fairy Ocarina all sit right. Of the bean the user wrote "maybe invis double
    check" (not yet clear what to check). The Stone of Agony is called the **Echo Gem** in this game (the user:
    there is no Shard of Agony here).
  - **Held up: too high.** Picking up Din's Fire, Link holds it well above his hands (screenshot); the user: "some
    holdup animations are too high", and wants the game's own height when held up. Cause, most likely: the item
    held up after a pick-up is the ground actor itself (as found for the turning items), so it uses the lifted
    copy too. The scales' small lift (+0.1) was not noticed; Din's Fire's +0.333 is.
  - **The small Deku Stick bag soft-locks** when picked up. The user: the game never gives the small stick bag;
    the first stick picked up unlocks the sticks. So it must not be placed. Not checked yet: the small Deku Nut
    bag, very likely the same.

### Lifted items are held up as in the game; items the game never gives are refused (2026-11-19, branch `claude/ground-lift-all`)
Two bugs of the in-game test above.
- **Held up too high. Found** (all in the game's files):
  - picking an item up runs `Dm_SY_Get`, which plays the animation command `Rotate_GetDemo` on the actor picked
    up: the item Link holds up is the ground actor itself, with its own animation project, so with the lifted copy;
  - in `AS/Item_Common.root.asb` (the animation file of every ground version) that command shows the pose
    `Pose_GetDemo`, and `Pose_Common` when the project has none. The spin on the ground (`Rotate_Obj`) shows
    `Pose_Common`;
  - of the listed items' projects only three have a `Pose_GetDemo`: the Gold Skulltula token's, the Fire Arrow's
    (also the Ice Arrow's) and the large arrow bundle's (the single arrow). The other 27 have `Pose_Common` alone
    (the quivers' and the hammer's also a `Pose_Pouch`): held up, the game shows them in `Pose_Common`, the pose
    the lift raised. So Din's Fire was held 0.333 too high, the hammer 0.293, the bean 0.164, the Echo Gem 0.124,
    the Fairy Ocarina 0.140, and the scales 0.19 and 0.20, the bracelet 0.14, the magic blessing 0.285 (not
    noticed then). The token and the Fire Arrow were held up right already: "some" in the user's words;
  - the game's own items that both lie on the ground and are held up have the two poses: 13 projects have exactly
    `Pose_Common` (standing on its point) and `Pose_GetDemo` (centred) for the bones `Root` and `Skl_Root`: the
    magic jars, the Heart Container, the ground Goron Tunic, the Deku Scrub's seed, the masks.
- **Fix** (`lifted_animation` in `tools/ground_items.py`): the lifted copy of a project without a `Pose_GetDemo`
  is no longer made of the project itself but of one of those 13, the large magic jar's
  (`Obj_MagicJar_Large_Animation`, `HELD_BASE`), the way the shop versions' shelf copies are made (the Giant's
  Knife, seen right in game): its `Pose_Common` is the item's pose at the lifted height, its `Pose_GetDemo` the
  item's own `Pose_Common` exactly as the game has it (size, turn, place, flags). Only the name and the two
  poses' values change in the jar's file. On the ground nothing changes: every item lies exactly where it did.
  The three projects that have a `Pose_GetDemo` are copied as before, byte for byte.
  - Names: such a copy is as long as the jar's name (28 letters): `NX2G_`, the project's own part, filled with
    `_`, e.g. `NX2G_DinFire________________`, `NX2G_Sword_Kokiri___________`. The three others keep theirs
    (`NX2GToken_Gold_Animation`).
  - **The bytes of the four copies tested before change** (bracelet, magic blessing, both scales): new names, 1,216
    bytes instead of 880 / 888, made of the jar's file. Their `Pose_Common` is the one seen right in game (the
    test builds the old copy, checks its checksum and compares the poses); held up they are now the game's.
  - Lost: the `Pose_Pouch` of the quivers' and the hammer's projects (the pose of the animation state `Pouch`),
    which the jar's project has not; that state then shows `Pose_GetDemo`, the game's `Pose_Common`. The item in
    the inventory is the item itself (`PouchActor`) with the game's project, so this should never show. Not
    known: what uses the state `Pouch`.
- **The small Deku Stick bag soft-locks. Found:**
  - the game never gives it. No map, chest or event flow names `Item_StickBag_Small` at all (every file of the
    game searched, but models, textures and sound). Its actor has no animation settings (`ASRef`, `ASInfoRef`,
    `AnimationRef`): it cannot be shown held up;
  - the first Deku Stick brings it by itself: in `PouchActorInfo` the sticks' rows (`Item_DekuStick`,
    `Obj_DekuStick`, `Pouch_`, `Shop_`, `Weapon_DekuStick`) have `IsAbleToGetBagIfGet` and
    `SmallBagActor: Item_StickBag_Small`. The Deku Nut is the same (`Item_DekuNut`, the scrub's nut:
    `SmallBagActor: Item_NutBag_Small`); `Item_NutBag_Small` is named by one flow only, which asks whether Link
    has it (a scrub's nut sale, `NecessaryActor`). The two bags' own rows are the only ones of the 15 bags and
    quivers without `IsItemStockMaxIfGet`;
  - the small wallet (`Item_Wallet_Small`) is in the inventory from the start
    (`Sequence/SetPouchAndStatusForGameStart`) and has no actor pack at all;
  - the small seed bag and the small quiver are not given by any map, chest or flow either: flows only ask for
    them (`IsGet.Item_BulletBag_Small`, `IsGet.Item_Quiver_Small` in `DisplayShop`, `NecessaryActor` in the
    scrubs' sales), their actors have no animation settings, and seeds and arrows name them as `SmallBagActor`
    without `IsAbleToGetBagIfGet` (the bag has to be there first). The builder already never places them: placed
    alone they mean the slingshot and the bow (`FAMILY_ALIASES`), and scrubs give them with the weapon
    (`SCRUB_COMPANIONS`). Left as it is;
  - given as such: the small bomb bag (the Dodongo's Cavern chest), every medium and large bag, quiver and wallet
    (mini games, Gorons, scrubs, the Forest Stage, the Gold Skulltula rewards).
- **Fix:** `NEVER_GIVEN` in `tools/build_mod.py`: `Item_StickBag_Small`, `Item_NutBag_Small` and
  `Item_Wallet_Small` are refused on every kind of spot, alone or in a pair, before anything is written
  ("... cannot be placed anywhere: the game never gives it as an item (the first Deku Stick Link gets brings
  it)"). The two small bags are out of `GROUND_LIFT`: 35 items, 30 copies (27 made of the jar's project, 3 of
  their own).
- **Tests:** `tests/ground_lift_check.py`, now 26 lines: as before, and for every copy: made of the item's own
  project when that has a `Pose_GetDemo`, else of the jar's; only the name and the poses' values differ from that
  file; held up, size, turn and place are exactly the game's; the ground pose of the four tested copies is as
  then; the three items are refused whatever the check, alone and in a pair, with nothing written; the evidence above read from `PouchActorInfo` and the packs; the small seed bag
  and quiver still stand for their weapons. ALL OK. `tests/ground_prog_check.py` (changed for the new copies):
  ALL OK. edit_check, evfl_add_check, chest_check: all OK; logic_check: 0 failed; db_check: 0 errors; round trip
  as before (evfl 650 of 914 identical).
- **Check build** (scratch folder, the six usual fixes, 29 files): `KF_RUPEE_NEAR_FADO_ITEM_01` Din's Fire,
  `KF_SHOP_RUPEE_ITEM` Megaton Hammer, `KF_TRAINING_AREA_RUPEE_ITEM_02` Fire Arrow,
  `KF_SARIAS_HOUSE_HEART_ITEM_02` Magic Bean, `_03` Echo Gem, `_04` Gold Skulltula token, `_07` Fairy Ocarina.
  Read back from the written files: each of the seven packs and rows names its copy; with it the lowest vertex
  is 0.050 above the ground, as in the build tested in game; `Pose_GetDemo` is the game's held-up pose for all
  seven (Din's Fire at height 0.000 instead of 0.333). A build with
  `KF_TRAINING_AREA_RUPEE_ITEM_01=Item_StickBag_Small` stops with the message and writes nothing.
- **Not yet tested in game.** Open there: the five items made of the jar's project held up (Din's Fire, the
  hammer, the bean, the Echo Gem, the Fairy Ocarina) and still lying right; the scales, bracelet and magic
  blessing again, as their files changed.
- **In game (2026-11-20): works.** Nine items in Kokiri Forest (Din's Fire on Fado's ledge, the hammer on the
  shop floor, the Silver and Gold Scale behind the crawl hole, the magic blessing near Mido, the bean, the Echo
  Gem, the Goron Bracelet and the Fairy Ocarina in Saria's house): each lies on the ground and is held up at the
  game's height. The hammer seemed a little high but fine; the user: don't change it any more for now. Found
  along the way: the two scales were placed as two plain items (not as the pair), so the Gold Scale could be taken
  before the Silver one. That is the test's placement, not the lift; but nothing in the builder stops it.

### Progressive upgrades, step 4: a chest with three outcomes, the bomb bags (branch `claude/three-level-chest`)
- `CHECK_ID=First>Second>Third` on a **small chest** makes it a chest of our own, `Obj_TBox_NX2_<family>`, that
  gives Third when Link has Second, else Second when Link has First, else First. Only the families in the new
  table `THREE_LEVEL_FAMILIES` (`tools/build_mod.py`), for now one:
  `Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large`. Plan: `out/RESEARCH_progressive.md`, question A.
  Two-level pairs stay on the game's checking chest. **Not yet tested in game.**
- **Found** (all in the game's files):
  - the checking chest (`Obj_TBox_A_06`) is the small chest (`$parent` `Obj_TBox_A_01`) with four parts of its
    own: its AI, its held actors (the small chest's, plus the slot `SubContent`), its drop settings and
    `AffiliationRef`. Its AI (101 nodes) makes both items when the chest is made and hands the name of one
    slot (`HolderKey`) to the shared chest module, chosen by "0 < the number Link has";
  - a slot's name is free: `ActorHoldSettings` is a table of names (`Content`, `SubContent`, `ContentDisplay`,
    `ShopHolder`, `Obj_Bomb`...), and the code has no slot name of its own (its one `SubContent` is a parameter
    of an error node). The chest module only allows opening when the slot it is handed holds an actor;
  - the names: each bag is an inventory item under its own name, saved under it (`IsGet.<name>`,
    `PouchData.<name>.StockNum`), 20 / 30 / 40 bombs, filled when received (`RSDB/PouchActorInfo`). The game's
    own chest gives `Item_BombBag_Small` (Dodongo's Cavern), and a small chest of Mido's gave it in game on
    2026-11-15;
  - Medium and Large inherit the Small one's item settings (`Component/PouchContentParam/BombBag`). For a
    chest that changes nothing: those settings name no other item to put in the inventory, so each bag goes in
    as itself, and all three are item event actors with the get demo (a chest holds them as they are);
  - a chest is lit by a light on its bone, given to it **by actor name** in
    `System/GameGraphics/LocationalLightRigGroupSetting/Gimmick0` (one entry per chest actor). Without an entry
    a chest of ours would not be lit as the others;
  - the game's tag table (`RSDB/Tag`) has a row per chest: `Graphics`, `HasLightRigBone`, `MapIcon_Treasure`.
    The code reads `HasLightRigBone` from `RSDB/GameActorInfo` (its only uses are the table's columns). The
    table's layout: one bit per actor and tag, and per tag a running count every 32 actors (`RankTable`); made
    again from the bits it comes out byte for byte.
- **Design, one change from the plan:** the plan had two more map settings read with
  `QueryBlackboardGetString`. Instead the level-2 question and level 3 are **fixed in the chest's AI**, one
  chest actor per family, as a turning item's names are. Why: the game asks the inventory with a fixed name
  (`Enemy_Tentacle_Red`: `Item_Boomerang`) and makes a held item from a fixed name (the chests' own default
  `TBox_Rupee_Green`), and the turning items' fixed-name question was seen working in game; the only game use of
  `QueryBlackboardGetString` on an actor's own settings reads one no placement can set (`BalloonMessageId`). So the
  game's drop settings and settings table are used as they are, and only the third slot is new to the game.
- **The chest** (`tools/three_chest.py`, new): `Obj_TBox_NX2_BombBag` (and `_NoBake` for a `_NoBake` small
  chest): the checking chest's pack with four files of our own in place of its four:
  - the actor file: the small chest with the checking chest's four parts, the AI and the held actors ours;
  - the held actors: the checking chest's, plus the slot `ThirdContent`, a copy of `SubContent`'s settings;
  - the AI `Obj_TBox_NX2_BombBag.root`: the checking chest's 101 nodes with their numbers and four more, each a
    copy of a game node of the same type: make `Item_BombBag_Large` in `ThirdContent` (the chest's own node for
    its default item), "how many `Item_BombBag_Medium` has Link" (the tentacle's), "0 < that" (the chest's
    own), and "yes: `ThirdContent`, no: the checking chest's answer" (the chest's local module's). Two game
    nodes change: the node that makes the held items gets one child more, and the chest module takes its slot
    name from the new choice;
  - level 1 and 2 are the placement's settings, as for a pair (`Drop__DropActor`, `Drop__CheckActor`,
    `Drop__DropActor_Substitute`);
  - two table rows, the checking chest's under our name (`ActorInfo`, `GameActorInfo`). Memory: the checking
    chest has 9,344 more than the small chest; ours gets as much again (197,392);
  - an entry in the game's list of chest lights, a copy of the checking chest's, added at the end (25 -> 26).
- **Not done:** no row in the tag table. In a dungeon a chest of ours would most likely not be drawn on the
  dungeon map. Mido's house is not one.
- **Builder:** `three_level_parse` (only the table's families; only chests, a big chest is refused when its map
  is changed), `checking_chest` (which chest takes a small chest's place), `patch_file` takes the family's
  chest. A family on a number of checks other than three prints a note.
- **Sizes:** two new rules in `tools/sizes.py`, both exact for every game file of the kind
  (`tests/size_check.py`): held actors (`ActorHolderParam`, 99 files): 5,128 + 224 a slot + 104 a bound bone;
  light lists (`LocationalLightRigGroupSetting`, 17 files): 5,096 + 160 an entry. The slots of
  `ActorHoldSettings` have free names, so a rule can now write `*` for an entry's name (`FREE_KEYS`).
- New test `tests/three_chest_check.py` (in `run_tests.bat`), 26 lines: the names, the syntax, the refusals
  (a family not in the table; a freestanding item, shelf, pot, rock, bush, Gold Skulltula, gift, scrub; a big
  chest), Mido's three chests in both maps with nothing else changed, the `_NoBake` twin, the pack file by
  file, the rows, the light entry, a size entry for every new file, the AI read back byte for byte (99 of the
  101 game nodes untouched, every new node the copy of a game node), and what the chest gives **worked out from
  the file's nodes**: the game's checking chest first (it comes out as seen in game: the first item, then the
  second), then ours for all 8 inventories and all six opening orders (Small, Medium, Large each time). ALL OK.
  edit_check, evfl_add_check, chest_check, ground_prog_check: all OK; logic_check: 0 failed; db_check: 0
  errors; size_check: OK.
- **Check build** (scratchpad only, the six usual fixes; `KF_MIDO_CHEST_01`, `_02`, `_03` = the bomb bag
  family): 17 files. Read back against a build of the fixes alone: `KokiriForest_Child_Dynamic` (3 of 3,639
  actors) and `KokiriForest_Adult_Dynamic` (3 of 3,674): `Obj_TBox_A_01` -> `Obj_TBox_NX2_BombBag` with the
  three settings, the opening event kept, nothing else of them; `ActorInfo` and `GameActorInfo` one row more
  each; the light list one entry more; the pack new; 10 size entries differ. `KokiriForest_Child_Dynamic`
  510,884 -> 511,004 bytes (entry 511,176 -> 511,296), `KokiriForest_Adult_Dynamic` 516,036 -> 516,156
  (516,328 -> 516,448). The pack: 98,596 bytes (entry 98,936), 64 files, 4 new. The AI: 105 nodes, 33,787 bytes
  (entry 34,206; the game's 32,549 and 32,968). Held actors 440 bytes (entry 6,024), actor file 556 (5,912), AI
  settings 108 (5,224), light list 4,872 -> 5,004 (13,992 -> 14,280).
- Known: once Link has the second level, every chest of the family left gives the third (a fourth chest, or
  three chests after a first bag from elsewhere, give the biggest bag again). The game itself adds the small
  bag on the first bomb picked up without one.
- Open, in game only: the engine accepts a third slot and three held items in one chest; the third item is
  made in time; the light entry lights the chest; a chest shown = given for all three levels.
- **In game (2026-11-19, combined test with the ground lift, the progressive gift and Saria's gift): works.**
  Run 1 (no leaving the house): bomb bag, bigger, biggest, each held up and named alike, 20 / 30 / 40 bombs. Run 2
  (reverse order): 20 / 30 / 40 in order. More orders: "tried a handful, all seemed fine". So the third slot,
  the third item and the fixed-name question all work. Not answered: whether the three chests are lit like the
  fourth, leaving and coming back (run 3, and the chests staying open).

### Progressive upgrades: a pair on a gift, decided in the giver's own flow (branch `claude/progressive-gift`)
- `CHECK_ID=First>Second` is now also accepted on a **gift that has flow data** (today: the rock-circle Kokiri,
  `KF_CIRCLE_KOKIRI_GIFT`). The giver's own flow asks the inventory in front of its call of the shared get flow:
  First if Link doesn't have First, else Second. Plan: `out/RESEARCH_progressive.md`, question B1. The shared
  get flows (`Dm_SY_GetInEvent`, `Dm_SY_Get`, `GetPouchContent`) are only called, not changed.
- **Found** (all in the game's files):
  - the game's own example of exactly this is the Deku Theater, `LostWood_ScrubForestStageElder_SkullMaskFirst`:
    `Event30`, a switch on `PouchSystemActor.EventQueryIsExistInPouch {Num: 1, Actor: Item_StickBag_Medium}`,
    case 0 (has it) -> `Event32`, case 1 (has not) -> `Event29`. Both are calls of
    `Dm_SY_GetInEvent<GetInEvent_NotTurn>` that differ only in `ActorName` (`Item_StickBag_Large` /
    `_Medium`), and both lead on to the same step (`Event0`). The Kokiri's gift is a call of the same entry;
  - the question has one shape in the whole game: 153 switches in the flows read, parameters `Num: 1` and
    `Actor` only, cases 0 and 1. `PouchSystemActor` has the same actor entry in all 110 flows that have one
    (no secondary name, the six usual settings);
  - the game's flows ask about each pair's first item under its own name: `Item_Scale_Silver` (6 times),
    `Item_Hookshot` (12), `Item_Ocarina_Fairy` (4);
  - the Kokiri's gift (`Npc_Kokiri_008_Child`, `Event224`) is the head of one branch of a fork (`Event219`) and
    ends that branch. The game has forks whose branch starts with a two-way switch between two calls that end
    the branch (6, e.g. `Common_Dungeon_OpenShutterMove` `Event210` -> `Event194`);
  - `Dm_SY_GetInEvent` makes the held-up model, the window and the inventory entry from the one `ActorName` it
    is called with, so each branch shows what it gives;
  - no table lists a flow's actors (`RSDB/EventSetting`, `GameAnalyzedEventInfo`: only the flow files an event
    may run, and none is added here).
- **Changed** (`tools/build_mod.py`, a section of its own: `gift_pair_kind`, `gift_pair_template`,
  `gift_pair_edit`, `gift_pair_read_back`; `gift_edit` and `pair_kind` are untouched):
  - the gift is first set to First as any gift (`gift_edit`). Then, in the same flow: a new call that is a copy
    of the gift's call naming Second, with the same next step; a new switch with the game's question about
    First, 0 -> Second's call, 1 -> the gift's own call; every link to the gift moved to the switch
    (`repoint`). The question's parameters, its case values and the `PouchSystemActor` entry are read from the
    Deku Theater's flow at build time, found by what they are;
  - for the Kokiri: 2 new events (`Event241` the Gold Scale's call, `Event242` the question), 1 new actor
    (`PouchSystemActor`, 9 instead of 8), 1 link moved (the fork `Event219`: branch `Event224` -> `Event242`),
    and the two entry points that list the gift's call list the second call too. The other 236 events are as
    in the game. 134,144 -> 135,408 bytes, size entry 134,416 -> 135,696 (length rounded up to 32, plus 272);
  - items Link can't hold up (the ocarinas) keep their way: both branches are the get window call
    (`GetPouchContent`) and lead to the same sync steps. A pair with one item held up and the other not is
    refused;
  - **refused:** a pair on a gift with no flow data (Saria's cutscene gift `LW_SARIA_GIFT`, the Skull Kids, the
    Deku Theater: no step of the giver's flow to put the question in front of), on a song, and as before on
    scrubs, shelves, pots, rocks, bushes and Gold Skulltulas; pairs not in `PROGRESSIVE_PAIRS`.
- New test `tests/gift_check.py` (in `run_tests.bat`), 29 lines: the game's pattern (the Deku Theater's switch,
  the 110 actor entries, the 153 questions, the fork shape); where a pair is accepted and refused; the Kokiri's
  flow read back (the two steps, the actor, the question's parameters, the branch naming the right items, both
  calls ending where the gift ended, every other step and entry point as in the game, the size entry); the
  builder's own read-back stops a branch the wrong way round; hookshots and ocarinas; one whole build in a
  temporary folder against a build of the fixes alone. ALL OK. edit_check, evfl_add_check, chest_check,
  ground_prog_check: all OK; logic_check: 0 failed; db_check: 0 errors.
- **Check build** (scratch folder only, the six usual fixes; `KF_CIRCLE_KOKIRI_GIFT` and `KF_MIDO_CHEST_04` =
  `Item_Scale_Silver>Item_Scale_Gold`): 14 files. Against a build of the fixes alone: only
  `Npc_Kokiri_008_Child.bfevfl` (as above), `KokiriForest_Child_Dynamic` and `KokiriForest_Adult_Dynamic` (one
  actor each: Mido's bottom right chest `Obj_TBox_A_01` -> `Obj_TBox_A_06` with the pair's three settings) and
  three entries of the size table differ.
- **Not yet tested in game.** To see: the Kokiri hands the Silver Scale when Link has none and the Gold Scale
  after the chest's Silver one, held up and named alike; no freeze at the hand-over (a flow gaining
  `PouchSystemActor` and a switch at the head of a fork branch is new for the builder).
- **In game (2026-11-19, combined test with the ground lift, the three-level chest and Saria's gift): works.**
  Gift first: the Kokiri gives the Silver Scale, his last line plays, the bottom right chest then gives the Gold
  Scale, both in the inventory. Chest first: the chest gives the Silver Scale, the Kokiri the Gold Scale, his last
  line plays, talking to him again gives nothing. Held up and named alike every time; no freeze.

### An item on Saria's gift (`LW_SARIA_GIFT`, branch `claude/saria-gift`)
- `LW_SARIA_GIFT=<item>` is accepted now: Saria's cutscene on the bridge gives that item. Research and evidence:
  `out/RESEARCH_saria_gift.md`. **Not yet tested in game.**
- **Found** (all in the game's files):
  - the cutscene that gives the ocarina, `Dm_Kokiri_0155`, has no timeline: `formats/evfl.py` already reads it
    and writes it back byte for byte. The timeline file is the cutscene before it, `Dm_Kokiri_0150` (Saria's
    goodbye), which gives nothing. No format work: `formats/` is unchanged;
  - walking onto the bridge starts `KokiriForest_ArriveLostWood` (flow `Goto_HyruleCastle`): `Dm_Kokiri_0150`,
    then `Dm_Kokiri_0155`, then Link is sent to Hyrule Field. The trigger area is there until `Dm_Kokiri_0150`
    has been played (`Logic/KokiriForest_Child_Level_All_02_ddcd`): "played", not owning the ocarina;
  - in `Dm_Kokiri_0155` Link holds a cutscene actor named `Item_Ocarina_Fairy`, bound to his left hand
    (`Event93`, `EventTriggerModelBind`, `Weapon_L`); `Event77` shows the get window (`GetPouchContent`, entry
    `DisplayGetByActorName`: the window alone, the text is the item's own); `Event68` adds the item
    (`PouchSystemActor.EventTriggerAddOrRemovePouchContent`). No flag, no song, no talk step, and nobody plays
    the ocarina there;
  - the game's cutscenes bind other item actors to a hand the same way (`Item_Gauntlet_Goron`,
    `Item_ZeldaLetter`, `Item_Sword_Giant`, `Item_Bottle_Letter`, `Item_BulletBag_Medium`), all built on
    `Item_EventObject_Base`;
  - none of the 262 files with a timeline gives an item: every cutscene gift (the Ocarina of Time, the stones,
    the medallions, the Light Arrow) is in a file the reader handles. None of those was changed.
- **Builder** (`tools/build_mod.py`): a check with `"cutscene": {flow, add, window, item}` in its data
  (`plan_cutscene_gifts`). `cutscene_gift_edit` sets the item of the add step and of the window, and renames the
  actor Link holds to the item when the item is built on `Item_EventObject_Base`; for anything else (a rupee, a
  heart, equipment) Link keeps the ocarina in his hand and the build says so. A slingshot or bow gets its small
  bag added right after it. `cutscene_gift_check` reads the written file back against the game's: nothing else
  may differ. The data is checked against the file first (the add step, the window, one held actor).
- Left as they are: the Zelda Notes screenshot step (`Event58`, still names the Fairy Ocarina) and
  `Dm_Kokiri_0150`, where Saria still holds out an ocarina.
- **Sizes**: no new rule. `Dm_Kokiri_0155.bfevfl` 45,216 -> 45,208 bytes with the Boomerang, entry 45,488 ->
  45,488 (size rounded up to 32, plus 272).
- `tools/build_db.py`: the original contents of a check with `cutscene` data; `data/db/KokiriForest.json`
  rebuilt (`LW_SARIA_GIFT`: `Item_Ocarina_Fairy`, from `Dm_Kokiri_0155`, `Event68`).
- New test `tests/saria_check.py` (in `run_tests.bat`), 15 lines: the data against the game's file; the cutscene
  byte for byte through the reader; the Boomerang given, named and held, nothing else changed; the size entry;
  the ocarina placed on its own check gives the game's file; a rupee keeps the ocarina in the hand; the
  slingshot's seed bag; wrong data and a progressive pair refused; the read-back notices a change elsewhere.
  ALL OK. edit_check, evfl_add_check, chest_check, ground_prog_check: all OK; logic_check: 0 failed; db_check: 0
  errors. Round-trip: the same report as before the change (evfl 650 identical, 264 errors).
- Check build (the six usual fixes, `LW_SARIA_GIFT=Item_Boomerang`), read back: `Event68` adds `Item_Boomerang`,
  `Event77` names it, the held actor is `Item_Boomerang` with its three steps (join, bind to `Weapon_L`, leave).
- Open, in game only: how the item sits in Link's hand (no offset, turned as the ocarina was); that an item actor
  other than the ones the game binds behaves as a held prop there; what skipping the cutscene does to the gift
  (the game's own behaviour, not changed).
- **In game (2026-11-19, combined test with the ground lift, the three-level chest and the progressive gift):
  works.** Saria's goodbye plays as usual; in the second scene Link holds the Boomerang, the window names it, the
  scene goes on to Hyrule Field; the Boomerang is in the inventory and throws, no Fairy Ocarina; the scenes don't
  play again. Skipping Saria's scene by hand: the Boomerang still arrives. Looks: the Boomerang doesn't spin
  there, and is slightly too big in his hands (screenshot); the user: a unique pose, "not a big deal".

### Progressive upgrades, step 3: pairs on freestanding items, the "turning item" (branch `claude/ground-progressive`)
- `CHECK_ID=First>Second` is now also accepted on a **freestanding item**: the placement gets First's *turning
  item*. Plan and evidence: `out/RESEARCH_ground_progressive.md`. Still refused on shelves, pots, rocks, bushes
  and Gold Skulltulas (and on gifts, songs and scrubs), and only the pairs in `PROGRESSIVE_PAIRS`.
- **Found** (all in the game's files):
  - a ground item decides nothing: what goes into the inventory, the model on the ground and the model Link
    holds up all come from the one actor picked up. So the actor lying there has to be the right level's;
  - a ground item's AI (`DropItem.root`, 13 nodes: spin, bounce, a layer change while carried) is named in its
    own parameter files (`AIInfoRef`), so a copy under another name can replace it, as the shop versions'
    `Shop_NX2_Once`;
  - an object's AI can ask the inventory every frame: `Enemy_Tentacle_Red.utility.root` asks
    `QueryGetPouchContentNumByActorName` for `Item_Boomerang` into a "when 0 / otherwise" selector. It is the
    checking chest's question;
  - the game has an actor that turns into another through a drop table of its own: `Animal_ButterflyToFairy`
    (`DropRef` -> `Component/DropParam` -> `Drop/DropTable` -> `Drop/DropSubTable`, one item). Its three files
    are only in its own pack: no table (`RSDB`) and no file under `GameParameter` names them;
  - an AI can drop without dying (`OneShotDropDrop`: trees, the Gerudo cow bone), switch its drop on and off
    (`OneShotDropSetDropValid`: chests) and remove its actor without marking its placement
    (`OneShotGenericDeleteThisActor`, `IsFade` false: the silver rupee counter);
  - **death reason 10 is not "picked up"**: the code's list of reasons makes 4 `PickedUp` and 10 `LifeDepleted`
    (the numbers in the game's AI files agree: pots breaking 10, the silver rupee taking itself 4). The pick-up
    scene (`Dm_SY_Get`) ends the item with 10, and the ground items' death table drops on that reason
    (`IsDropItem`). An item with a drop part would drop its next level when picked up, so its drop is switched
    off as soon as it is made;
  - the ground items' death table ignores reason 0 (`AI`: `IsIgnoreThisDeathReason`), the reason the butterfly
    turns with: turning by dying would need a death table of our own (a loose file). Not used;
  - no game AI drops and deletes itself in one step. Pots and the butterfly are gone as soon as they have
    dropped (through their death), and in game a pot's drop of one of our ground versions appeared
    (2026-11-16): a drop outlives its dropper there. Whether it does after a delete can only be seen in game.
- **The turning item** (`tools/turn_items.py`, new): one actor per level, `Obj_NX2P_<level>`: the ordinary ground
  version of that level (`tools/ground_items.py`, version `turn`) with a root AI of its own,
  `NX2_Turn_<level>.root`: `DropItem.root` with one more branch under its root. Every frame: dead? in an event?
  a main event playing? then nothing. Else, once Link owns this level: switch the drop on, drop the next
  level's actor, delete itself, in one step (the last level only deletes itself). The first level also deletes
  itself when Link owns the second but not the first (a second level that takes the first one's place in the
  inventory, as the Longshot most likely does). On entering, a level with a next level switches its drop off.
  - The first level has a drop part: copies of the butterfly's three files under its own name, the sub-table
    naming the second level's actor, with the two game files they inherit from as they are.
  - Every new node is a copy of a game node of the same type, found by what it is and checked before use:
    the yes/no selector and the "do nothing" of `DropItem.root` itself; the inventory question and the "dead"
    question of `Enemy_Tentacle_Red.utility.root`; "in an event" of `Obj_TBox_A_01.root`; "main event" and the
    enter/update split of `Door.root`; the number selector, the one-step sequence and the delete of
    `Obj_silverRupeeCounter.root`; the drop switch of `TreasureBox.event.root`; the drop of the cow bone's AI.
    The 13 nodes of the game's file keep their numbers and contents (the root gets one child more).
  - Three guards instead of the plan's two. Which question is true through the whole pick-up scene is not in a
    file, so all three the game's own item AIs use are asked: `QueryDeathIsDead` (Piece of Heart),
    `QueryEventMemberIsEventMemberSomeReason` (Ruto's letter, same event settings; chests) and
    `QueryIsPlayingMainEvent` (a Poe soul does not end itself while one plays). The cost: an item turns after
    another one's scene, not during it.
  - Memory: the ground version's `InstanceHeapSize` plus what a drop part, an actor holder and more AI add to the
    game's butterfly (`Animal_ButterflyToFairy` over `Animal_Butterfly`: 34,208).
- **Builder** (`tools/build_mod.py`): `pair_kind` (chest: the checking chest as before; freestanding: the
  turning item; anything else stops the build); `turn_spacing` refuses two items of one family less than 2 m
  apart (Link could touch both at once; the second could be taken before it has turned); both levels' packs and
  rows are made for each family placed. Families of three levels are refused (`turn_items.build`).
- **Sizes**: no new rule. The AI, the AI settings, the actor file, the item settings and the pack have rules
  (`tools/sizes.py`). The three drop kinds have none: each new file keeps the headroom of the butterfly's file it
  is a copy of (`Output.add`), and its list is as long. The entries come out at what the research fitted on the
  game's files of each kind (size rounded up to 32, plus 5,144 / 5,120 / 5,472).
- New test `tests/ground_prog_check.py` (in `run_tests.bat`), 16 lines: where a pair is accepted and refused
  (shelf, pot, rock, bush, Gold Skulltula, gift, scrub; three levels; two items too close); the two placements
  in the map, nothing else changed; for all three pairs: names, the AI read back with `formats/ainb.py` (the 13
  game nodes untouched, every new node the copy of a game node, the branch followed link by link, no node
  unreached), the pack's settings, the drop files naming the second level, the three rows, a size entry for
  every file. ALL OK. edit_check, evfl_add_check, chest_check: all OK; logic_check: 0 failed; db_check: 0 errors.
- **Test build** (`out/mods/NX2-ZOOTR`, the six usual fixes; `KF_RUPEE_NEAR_MIDO_ITEM` and
  `KF_RUPEE_NEAR_FADO_ITEM_01` = `Item_Scale_Silver>Item_Scale_Gold`): 16 files. Read back against a build of the
  fixes alone: only `KokiriForest_Child_Dynamic` (2 of 3,639 actors: `Obj_Rupee_Blue` -> `Obj_NX2P_Scale_Silver`,
  nothing else of them), the three tables (2 rows each) and the size table (16 entries) differ, and the two
  packs are new. `KokiriForest_Child_Dynamic` 510,884 -> 510,912 bytes, entry 511,176 -> 511,204.
  `Obj_NX2P_Scale_Silver`: pack 51,636 bytes (entry 51,960), 51 files, 7 new; AI 35 nodes, 10,860 bytes (entry
  11,256). `Obj_NX2P_Scale_Gold`: pack 47,260 bytes (entry 47,576), 46 files, 4 new; AI 26 nodes, 8,292 bytes
  (entry 8,696). No entry below its rule or below the game's.
- **The two spots** (child, both blue rupees in the game, 40.2 m apart): `KF_RUPEE_NEAR_FADO_ITEM_01` lies 1.2 m
  from Fado, on her ledge (y 116.1, about 6 m above the ground below). `KF_RUPEE_NEAR_MIDO_ITEM` (the spot where a
  Piece of Heart was taken on 2026-11-16) is at y 107.6 under the pond's water plane (`Land_Kokiri_WaterPlane_A_01`,
  y 109.7), by the waterfall: 2.1 m under the surface. Taken while swimming, an item may go through
  `Dm_SY_Get_WithoutPlayer` (no hold-up, and the item is not ended by the scene's own step), a path the guards
  were not read for: the checklist takes Fado's first.
- Known limits (from the research): a placement whose item turned and was then taken is not marked collected, so
  on a later visit its first level is made, turns, and the second removes itself in the first frames (maybe
  visible for a moment); the item that appears is dropped (a short hop).
- Open, in game only: an item actor accepts a drop part; the drop still happens when the actor deletes itself
  in the same step; one of the guards is true from the start of the item's own pick-up to its death, and none
  stays true for good; the inventory answers for a name asked by an item as it does for the chest.
- **In game (2026-11-19):** the user: "both scales worked as intended" (the turn, the pick-ups, the checklist's
  runs). But both scales lie partly in the ground (seen on Fado's ledge): the scales are not in `GROUND_LIFT`.
- **Scales no longer in the ground:** each scale has its own model and animation
  project. The models are built standing above their origin (`Skl_Root` at 0.223), and `Pose_Common` puts
  `Skl_Root` at -0.007 instead, which centres the scale on its point: with the spin's 0.05, the lowest vertex was
  0.142 (Silver) and 0.153 (Gold) under the ground. The box in `ActorInfo` is no measure here: it is the model as
  built (lowest 0.038, 0.027), and by it the scales would need no lift. So both are in `GROUND_LIFT` now, measured
  from the model's vertices and skeleton (`tools/item_pose.py`): their ground, token and turn versions get
  `NX2G_Scale_Silver_Animation` / `NX2G_Scale_Gold_Animation` with only the pose's height changed, -0.007 -> 0.184
  and -0.007 -> 0.196, lowest vertex 0.05 above the ground. Chests, shelves and held-up keep the game's animation.
  The bracelet and the magic stay on the box (`GROUND_LIFT_BOX`), as tested: their files come out byte for byte
  the same as before (by its vertices the bracelet lies 0.074 above the ground, the magic 0.05).
  `tests/ground_prog_check.py` checks the lifted copies.
- **In game (2026-11-19, second test):** the user: "it worked correctly": the scales sit on the ground, and the
  turn still works.

### Progressive upgrades, step 2: Hookshot > Longshot, Fairy Ocarina > Ocarina of Time (branch `claude/progressive-pairs`)
- Two more two-level pairs for the game's checking chest (`CHECK_ID=First>Second` on a small chest, step 1
  below): `Item_Hookshot>Item_Longshot` and `Item_Ocarina_Fairy>Item_Ocarina_Time`.
- **The names** (all from the game's files):
  - the game's own chests give `Item_Hookshot` (Dampe's goal chest, `Graveyard_Adult_Static`) and
    `Item_Longshot` (Water Temple); its flows ask the inventory about the same names
    (`EventQueryIsExistInPouch`: `MiniGame_DampeRace`, `Npc_Gerudo_004`, `Npc_Gerudo_009`), and about
    `Item_Ocarina_Fairy` (`Npc_Kokiri_005_Child`, `Npc_Kokiri_007_Child`);
  - the inventory is saved under an item's own name: `GameData/GameDataList` has `IsGet.<name>` and
    `PouchData.<name>.StockNum` for `Item_Hookshot`, `Item_Longshot`, `Item_Ocarina_Fairy`, `Item_Ocarina_Time`
    and both scales (names found by their hash, MurmurHash3). Each level has its own pair;
  - the names the game's own checking chests look for (`TBox_Shield_Deku`, `TBox_Shield_Hylian`,
    `Item_Range_Bow`) have no saved entry: they are the actor the chest gives, and the inventory question finds
    the item that actor stands for (`ActorName` in `RSDB/ActorInfo`: `Weapon_Shield_Deku`, `Weapon_Range_Bow`;
    the shield's item settings also name it, `PouchActor`). A flow does the same with the ground Ocarina of
    Time (`Dm_MelodyGet_Epona` asks for `Obj_Ocarina_Time`, which stands for `Item_Ocarina_Time`). So a
    check may name the item itself (the scales in step 1, seen working) or an actor that stands for it.
- **Does the inventory keep the first item?**
  - the inventory screen's table (`UI/Pouch/PouchTable`) has **one slot** for the hookshots
    (`ItemArray[7]`: `Item_Longshot`, then `Item_Hookshot`) and one for the scales (`CollectArray[7]`: Gold, then
    Silver); the ocarinas have two entries (`OcarinaArray[0]` Fairy, `[1]` Time). The same table marks the
    Hookshot and the Longshot **adult only** (`IsUsableAdult`), the Fairy Ocarina child only, the Ocarina of
    Time and the scales both ages;
  - whether the Hookshot leaves the inventory when the Longshot comes is not in a file. The game's flows ask
    "Longshot? if not, Hookshot?" for the same answer (`MiniGame_DampeRace` events 18 -> 0 and 262 -> 260,
    `Npc_Gerudo_004` 210 -> 158), which they would not need if the Hookshot stayed: most likely it is replaced.
    The saved "ever got it" flag stays (`IsGet.Item_Hookshot`, asked by `SageOfSpirit_RescueCarpenter`);
  - for two chests it makes no difference: the chest that gives the second item is only opened once;
  - **when the chest asks:** its AI's inventory question (`QueryGetPouchContentNumByActorName`) and the choice
    of the item (`QuerySelectStringByBool`) are not marked "only on enter" and feed the shared chest module
    while the chest waits, so the answer is the one at opening, not at room load. The scales in game
    (2026-11-18) agree: both orders worked in one room.
- **Ocarinas in a checking chest.** `Drop__DropActor` and `Drop__DropActor_Substitute` name the held-up
  versions (`Item_NX2_Ocarina_Fairy`, `Item_NX2_Ocarina_Time`: the builder's `in_chest`, as for any chest
  ocarina), `Drop__CheckActor` names the ocarina itself (`Item_Ocarina_Fairy`). A held-up version has no saved
  entry of its own (no `IsGet.Item_NX2_...`): it names the ocarina (`ActorName` in its `ActorInfo` row and
  `PouchActor` in its item settings), so what the inventory holds is `Item_Ocarina_Fairy`, the name the
  game's flows ask for. (The opening event is handed the held actor's file name, `Item_NX2_Ocarina_Fairy`:
  `QueryGenericGetActorName.ActorFileName` in `TreasureBox.module`, as for the game's `TBox_Shield_Deku`.)
- **A held-up version as a checking chest's item.** The checking chest makes both items the way the ordinary
  chest makes its one (`OneShotActorHolderTryRequestCreateActorWithActorFileName`, by actor name, into the
  slots `Content` and `SubContent`, which have the same settings). A held-up version is an item event actor
  like the Boomerang's with the get-demo command, which is what a chest holds; `Item_NX2_Ocarina_Fairy` was
  held by an ordinary chest in game (2026-11-17). Its files are the kinds the size rules already cover (actor
  file, animation list, item settings, pack, three table rows): no new rule.
- **The Ocarina of Time from a chest teaches nothing and needs nothing.** In the game the moat object
  (`Obj_Ocarina_Time_A_01`, a thing to look at, not an item) starts `DoorOfTime_GetOcarinaOfTime`, which plays
  the cutscene `Dm_MelodyGet_Time`. The cutscene adds the ocarina (`EventTriggerAddOrRemovePouchContent`
  `Item_Ocarina_Time`), shows its window, and gives the Song of Time as an item of its own
  (`GetPouchContent<GetPouchContentByActorName>` `Item_Melody_TimeSong`). No logic file names the ocarina.
- **Changed:** `PROGRESSIVE_PAIRS` has the two pairs; new `pair_check` (the check name and the second item of
  a pair's chest, used by the build and the test). Nothing else in the builder: the chest already gets the
  first item as a chest gives it.
- `tests/chest_check.py` now also checks: the three pairs; every item of a pair is an inventory item under
  its own name and saved under it; the game's own check names are stand-ins; the game's own Hookshot and
  Longshot chests; ocarinas become held-up versions that are item event actors with the get demo and stand for
  the ocarina; the hookshots in Mido's top chests and the ocarinas in the bottom ones at both ages, nothing
  else changed. 16 lines, ALL OK. edit_check, evfl_add_check: all OK; logic_check: 0 failed; db_check: 0
  errors.
- **Test build** (`out/mods/NX2-ZOOTR`, the six usual fixes; `KF_MIDO_CHEST_01` and `_02` =
  `Item_Hookshot>Item_Longshot`, `KF_MIDO_CHEST_03` and `_04` = `Item_Ocarina_Fairy>Item_Ocarina_Time`): 17
  files. Read back: the four placements at both ages are `Obj_TBox_A_06` with the three settings and
  `GetEventName: KokiriForest_TreasureBox_NaviChatOff`; the other 3,635 (child) and 3,670 (adult) actors are
  identical. `KokiriForest_Child_Dynamic` 510,884 -> 511,056 bytes, entry 511,176 -> 511,348 (rule: 511,336);
  `KokiriForest_Adult_Dynamic` 516,036 -> 516,208, entry 516,328 -> 516,500 (rule: 516,488). Held-up versions:
  `Item_NX2_Ocarina_Fairy` (pack 4,244 bytes, entry 4,568) and `Item_NX2_Ocarina_Time` (4,212, entry 4,536),
  two rows added to each of `ActorInfo`, `GameActorInfo`, `PouchActorInfo`. Size table: 15 entries new or
  changed, all for files the mod holds; none below its rule or below the game's (187 files with those inside
  the packs).
- Known and not changed here: a child can't use the Hookshot or the Longshot (the table above), so their reach
  can't be tried on a new file; a chest ocarina plays only after a save and reload (2026-11-17); Saria still
  gives her Fairy Ocarina on the bridge (`LW_SARIA_GIFT`: her cutscene `Dm_Kokiri_0155` adds it directly, and
  the builder has no data for that gift yet, so nothing could be placed there for this test).
- Open: whether the second ocarina chest finds a Fairy Ocarina that came from a held-up version before any
  reload (the files say the inventory holds the ocarina itself); what the Ocarina of Time's held-up version
  looks like (never seen in game). **Not yet tested in game.**
- **In game (2026-11-19):** the user: "it all worked properly". Both pairs gave the first item, then the second,
  as the checklist asked (both opening orders, the second ocarina chest also straight after the first, without
  a reload).

## 2026-11-18

### Size table entries from the file's contents (branch `claude/size-floors`)
- **What was found.** The crash of the songs' spin (below) was one case of a general fault: the builder gave a
  changed file its old entry plus what it grew in bytes, and a new file the headroom of a similar game file.
  The game's entries are not made that way. Fitted on the game's own files (every loose file and every file
  inside the 8,384 packs; `size32` is the size rounded up to 32):
  - `.bfevfl`, `.baev`: size32 + 272 (914 and 916 files, all exact); `.pack` and `Mals/*.sarc`: size32 + 312
    (8,384 and 16, all exact); `.bntx` in `Tex/`: size32 + 264 (20,667, all exact);
  - `.byml` (maps, RSDB tables, GameData): size32 + 264, `Sound/*.casset.byml` + 520 (1,814 of 1,816 exact; two
    have more: `RSDB/ActorInfo` + 2,800, `Effect/static...vsetb.byml` + 3,872). The number of rows or actors
    does not count;
  - `.ainb`: size32 + 376, and with an expression block + 16 + four times its number of signatures rounded up
    to 8 (5,036 files, all exact). The number of nodes does not count;
  - `.bgyml`: size32 + a constant per type + a cost per element of each list and per entry of each table with
    free keys; the members of a struct cost nothing. Actor files (`ActorParam`): 5,144 + 48 per component
    (8,374 files, all exact); `GameParameterTable` and `EventSettingComponentList`: 5,128 + 48 per component;
    `AnimationParam`: 5,096 + 88 per animation resource; `ModelInfo`: 5,192 + 80 per variation animation + 104
    per sub-model; `BlackboardInfo`: 5,096 + 8 per table; `AIInfo` 5,088, `PouchContentParam` 5,216,
    `PriceParam` 5,064 (constants). 532 of the 691 types have one constant for all their files;
  - message files (`.msbt`) have no entry of their own (only their archive); `.bfres`, `.asb` and the others
    were not fitted (the builder only copies them at the same size).
- **The fix.** New `tools/sizes.py` holds these rules. `Output.size` and `Output.add` (`tools/build_mod.py`)
  now take the files' contents and give the largest of: what they gave before, the rule for the new contents,
  the headroom of the original (or similar) file counted in steps of 32, and `floor` (kept; the songs' spin
  still passes the Boomerang's entry). Every call site passes contents (`patch_pack` and `song_spin_pack`
  return them). A `.bgyml` of a type without a rule keeps its headroom as long as none of its lists or tables
  has more elements than the game file it comes from; if one has, the build stops and names it (a rule has to
  be added). For `AIScheduleParam` and `ShopParam`, whose tables are all structs (the game's files with the
  same lists all have the same headroom: 502 and 11 files), only the lists have to stay.
- **Entries that were too small** (two test builds, 141 and 146 changed files; before -> now):
  - by a component or more: the adult shopkeeper's actor file, which gains `ShopRef`
    (`Actor/Npc_Kokiri_001_Shop_Adult...ActorParam.bgyml`, 5,584 -> 5,624), and every shop version's actor
    file, which has one component more than the shelf it is made from (`Actor/Shop_NX2_*_Once`, e.g.
    7,248 -> 7,304; 44 to 72 short). The songs' actor files, 120 short before the floor, need 6,168 by the
    rule (the floor gives 6,344);
  - by less than 32 (the rounding): the new item settings of every ground, token and shop version
    (`PouchContentParam`, 4 to 24 short), their packs and actor files (4 to 24), `Shop_NX2_Once`'s AI and its
    info (5 and 4), the songs' animation list (12), the six message archives the scrub lines grow (16), the
    song packs (8), `Npc_Kokiri_008_Child.bfevfl` (16), `RSDB/ActorInfo` (4), a shop version's
    `GameParameterTable` (16).
  Ground and shop versions have worked in game with those entries, so a few bytes short does not always crash;
  where the limit lies is not known.
- New `tests/size_check.py` checks the rules against every game file they cover (several minutes, not in
  `run_tests.bat`): OK. Both test builds: no entry below its rule, none smaller than the game's, no entry
  changed for a file the mod doesn't hold. edit_check, evfl_add_check, logic_check, db_check: as before
  (0 failed). Not yet tested in game.
- **In game (2026-11-18, evening; combined test with the shelf rework and the progressive chests):** no crash,
  everything works as before.

### Progressive upgrades, step 1: the game's checking chest (branch `claude/progressive-chests`)
- Background: an upgrade family must never skip a level and one item must never be on two checks. The first
  attempt decided inside the shared get flow and was rolled back. The game has a chest that decides by itself:
  the checking chest `Obj_TBox_A_06` (9 placements: Graveyard at both ages, Dodongo's Cavern twice, Spirit Temple,
  Bottom of the Well, Gerudo Training Ground three times). Its map placement names `Drop__CheckActor` (the item
  to look for in Link's inventory), `Drop__DropActor` (given without it) and `Drop__DropActor_Substitute` (given
  with it). No event flow is involved.
- What the files say about it: its settings file has the ordinary small chest as parent (`Obj_TBox_A_01`) and
  replaces three parts: the AI, the held actors (a second slot `SubContent`) and the drop settings table (the
  three settings above and `Drop__CheckCondition`, default true). Model, animation, physics and opening event
  are the small chest's, so it looks and opens like Mido's chests (which are `Obj_TBox_A_01`). Its AI makes both
  items when the chest is made (an empty setting becomes a green rupee) and asks the inventory
  (`QueryGetPouchContentNumByActorName`, not marked "only on enter") for the slot it hands to the shared chest
  module; an empty `Drop__CheckActor` asks for the default drop `Obj_Rupee_Green`.
- **Leftover fixed:** the builder changed `Drop__DropActor` on a game checking chest and left the other two
  settings (shown on Dodongo's Cavern: `Item_Boomerang` placed, `Drop__CheckActor: TBox_Shield_Deku` and
  `Drop__DropActor_Substitute: TBox_Rupee_Blue` still there, so with a Deku Shield the chest would give the blue
  rupee; the Training Ground chest that sets no first item stopped the build). A game checking chest that gets
  an item now becomes the ordinary chest (`Obj_TBox_A_06` -> `Obj_TBox_A_01`, `_NoBake` likewise) and its
  check settings are removed: the result is a placement shaped like the game's other small chests (the same
  settings 35 + 51 + 13 times in the game's maps), rather than a checking chest with empty settings, which the
  game never has. None of the nine is in the three areas with check IDs yet, so no build so far was affected.
- **Progressive pair (opt-in):** `CHECK_ID=First>Second` on a small chest makes it a checking chest: `First`
  while Link doesn't have `First`, else `Second`. Two chests with the same pair give `First` then `Second` in
  either opening order. Only pairs in `PROGRESSIVE_PAIRS` are accepted (now: `Item_Scale_Silver>Item_Scale_Gold`);
  refused on a big chest and on anything that isn't a chest. The names are the scales' own item names: the game's
  chests check `TBox_Shield_Deku` and `Item_Range_Bow`, which are the actors the chest gives (their settings name
  the inventory item), and the scales are their own inventory items (the game's flows ask for `Item_Scale_Silver`).
  The chest's own opening event setting stays.
- **Map size entries:** all 160 map files have the entry "length rounded up to 32, plus 264", whatever they
  hold. A changed map now gets at least that for its new length (`map_entry`), in every build (adding only the
  bytes it grew can fall short by up to 31).
- Test build (`KF_MIDO_CHEST_01` and `_02` = `Item_Scale_Silver>Item_Scale_Gold`, with all six fixes): both
  placements at both ages read back as `Obj_TBox_A_06` with the three settings and
  `GetEventName: KokiriForest_TreasureBox_NaviChatOff`; the other two Mido chests and all other actors unchanged;
  `KokiriForest_Child_Dynamic` 510,884 -> 510,992 bytes, entry 511,176 -> 511,284 (rule: 511,272);
  `KokiriForest_Adult_Dynamic` 516,036 -> 516,144, entry 516,328 -> 516,436 (rule: 516,424). No pack, table or
  flow is added for it.
- New `tests/chest_check.py` (in `run_tests.bat`): the map size rule, the nine checking chests given an item,
  the pair in Mido's chests, the refusal on a big chest. logic_check: 0 failed; db_check: 0 errors.
- Open: whether the chest chooses when opened or when the room loads (the files suggest when opened), and
  whether the Gold Scale after the Silver sets the deeper dive. **Not yet tested in game.**
- **In game (2026-11-18, evening; combined test with the shelf rework and the size rules):** the user: apart from
  the Giant's Knife's height, "everything else seems to work as intended" (the checklist had both opening orders
  and the Gold Scale's dive).

## 2026-11-17

### Goron Bracelet and magic blessing no longer half in the ground (branch `claude/ground-heights`)
- **Bug (in game):** dropped by rocks, the Goron Bracelet and the magic blessing lay half in the ground.
- **Found in the game's files** (skeletal animations; details in `tools/ground_items.py`): on the ground the spin
  `Rotate_Obj` lifts the bone `Root` by 0.05, and each item's own pose `Pose_Common` sets the height of the bone
  `Skl_Root`. Items made to lie on the ground lift themselves there (Bottle 0.114, Deku Shield 0.238; the
  Bottle's lowest point is 0.05 above the ground). The bracelet's pose lifts it by -0.01 (at 2.1 times its size),
  the magic blessing's by nothing; both models are centred on their origin.
- **Fix:** their ground versions and Gold Skulltula drops (`GROUND_LIFT`, only these two items) get a copy of the
  item's animation project (`NX2G_Gauntlet_Goron_Animation`, `NX2G_FairyBless_MPDouble_Animation`: same-length
  names) with only the pose's height changed, so the model's lowest point (its box, sized and turned by the
  pose) is 0.05 above the ground: bracelet -0.010 -> 0.130, magic 0 -> 0.285. Chests and shelves keep the
  game's animation. Check build: both files read back as intended.
- **In game (2026-11-18, built together with the shelf fix on main): works.** Under the rocks behind Saria's
  house, the bracelet and the magic now lie on the ground, not in it.

### Harp cloth in the song's colour (branch `claude/harp-colors`)
- New `tools/harp_colors.py`: the harp model (one material, one colour texture
  `Tex/Mt_Harp_Sheik_Item_Harp_Sheik_Alb.bntx`, BC1 sRGB 768 x 768, 10 mip levels, frame and cloth together)
  gets one variant per coloured song: the model file copied with three names changed to same-length names (model
  `Item_HrpX_Sheik`, file, colour texture; nothing else moves), and the colour texture copied, renamed, and its
  navy cloth recoloured on each BC1 block's two end colours (hue 190-275 degrees, saturated -> the song's hue and
  saturation, brightness scaled); a block whose end-colour order flips is swapped and its indices remapped. Each
  new name is checked in its file's dictionary. The approach is the user's own, from their earlier project
  (read only).
- The builder makes the variant for each placed song in `harp_colors.SONG_COLORS` (new files
  `Model/Item_Harp_Sheik.Item_HrpX_Sheik.bfres`, `Tex/Mt_Harp_Sheik_Item_HrpX_Sheik_Alb.bntx`, with size-table
  entries) and points the song's model settings and ActorInfo row at it.
- First test: Saria's Song with a provisional green (5,972 blocks recoloured), the Sun's Song plain. The 12
  songbook colours are still to be read (the song icons are ASTC in `UI/Layout2Archive/Common...bntx`; installing
  a decoder wasn't allowed: the user's screenshot instead).
- **In game:** the green harp worked (green cloth, gold frame unchanged); the plain harp stayed navy. Held up,
  the harp still sat low into Link's head and didn't spin.
- **The songbook colours** (from the user's songbook screenshot: the average of each icon's most coloured
  pixels): the six songs with white icons (Zelda's Lullaby, Epona's Song, Saria's Song, Sun's Song, Song of Time,
  Song of Storms) share one white harp, as the user asked (cream, 244/240/214); the warp songs take their icon's
  colour: Minuet green, Bolero red, Serenade blue, Requiem orange, Nocturne purple, Prelude yellow. One variant
  per colour (letter W, G, R, B, O, P, Y), shared by the songs of that colour. A light colour is darkened just
  enough that the cloth keeps its shading (the cloth's brightest 1 % stays at most full brightness).
- **Spin and height** (found in the game's files; details in `tools/harp_colors.py`): items held up spin
  through three components the songs lack (`ASInfoRef` Item_GetDemo, `ASRef` AS/Item_Common, `AnimationRef`).
  The command `Rotate_GetDemo` (`Item_Common_Animation`) turns the bone `Root` and lifts the bone `Skl_Root` by
  0.18; the harp has both bones but is 0.50 tall, centred. The songs now get the three components (the
  Boomerang's settings file, an animation list of their own), with an animation project of their own: a copy
  of `Item_Common_Animation` named `Item_HarpNX_Animation`, whose three lifts (held up, on the ground, still)
  are 0.31 instead of 0.18. Gifts and song cutscenes still give songs with the get window (unchanged).
- Test build: Mido's four chests and the Kokiri Sword chest hold five songs (white, green, red, purple, blue).
  logic_check: 0 failed; db_check: 0 errors. Not yet tested in game.
- **In game (2026-11-18): crash** right after the first cutscene, when Kokiri Forest loads. Longshot's log: the
  five song packs load, then the game crashes creating an actor (`Actor/Item_Melod...` in the crash registers),
  before any harp model loads. The packs themselves matched the Boomerang's. The difference was in their
  ActorInfo rows: every item that spins lists its animation projects there (`AnimationResources`) and reserves
  more memory (the Boomerang 114,848 bytes, the songs 68,848). The songs' rows now list `Item_HarpNX_Animation`
  and take at least the Boomerang's heaps (instance 114,848, render info 29,192). The ground and shelf fix
  branches already set their rows' lists from the item's own animation settings. Rebuilt, not yet tested in game.
- **In game: the same crash** (same place, same registers), so the rows were not the cause. The crash is a write
  through a null pointer (fault at the guest address 0) while creating the song, before its model or animation
  file is asked for. The cause found in the files: `AS/Item_Common` plays the item's resting pose `Pose_Common`,
  which comes from the item's own animation project (the one listed after Item_Common_Animation). All 297 items
  that list Item_Common_Animation have one; the songs listed only the harp's spin. The songs now also list Din's
  Fire's project (`Item_DinFire_Animation`, used as it is: only `Pose_Common`, leaving `Root` and `Skl_Root` as
  they are; Farore's Wind and Nayru's Love use it too), in their animation list and their rows. Uncertain: if the
  pose sets the height of `Skl_Root` itself, the harp's lift (0.31) is lost and it sits as before. Not yet tested.
- **In game: the same crash a third time.** As the user asked, the spin is off (`harp_colors.SPIN = False`; its
  code is kept): the songs are built as before the spin, with only the five colours (no animation components,
  files or row changes). Test build: the same five songs. Not yet tested in game.
- **In game (2026-11-18): no crash**; the colours work (Serenade blue, Bolero red seen held up, the gold frame
  unchanged). So the crash came from the spin. Held up, the harp still clips into Link's head a little.
- **The spin again, with the game's own animation.** Without a spin animation the harp doesn't even get the
  game's lift of held-up items. What differed from what the game does: the harp listed a renamed copy of
  `Item_Common_Animation` (`Item_HarpNX_Animation`, for a higher lift). Every crash had that copy, and items with
  a single unrenamed project work, so the copy is the likely cause (the resting-pose theory was wrong: an item
  doesn't need `Pose_Common`). The songs now list the game's `Item_Common_Animation` alone, unchanged
  (`harp_colors.SPIN_PROJECTS`), in their animation list and rows; no new animation file, no Din's Fire pose. The
  three components and the heaps (the Boomerang's) as before. The lift is the game's 0.18; if the harp still
  clips, more height has to come another way than a renamed animation. Not yet tested in game.
- **In game: the same crash a fourth time**, so not the renamed copy either. **Cause found in the game's code**
  (`.longshot_exefs/main`, loaded at 0x80020000; read with a small decoder in the scratchpad): the crash is in the
  code that loads an actor's settings file and merges its `Components` with its parent's
  (`Item_EventObject_Base`). It puts the keys in a table whose room is allocated first, from the memory given for
  that file. If that allocation fails, the table has no room, and the first key is written through a null pointer
  (`str x8, [x19]` with x19 = 0 at 0x80688f50). That memory comes from the file's size table entry. The songs'
  settings file grew from 484 to 732 bytes (3 components added) and the builder added only those 248 bytes to its
  entry (5,800 -> 6,048). A game file of exactly the same shape (`Item_BombBundle_Small`: 732 bytes, the same 6
  components, the same parent) has 6,168: loading takes more memory per component than the component's bytes.
  Every spin build had this, so the rows, the pose and the renamed copy were never the cause. Fix: a size entry
  can now be given a floor (`Output.size(..., floor=)`); the songs' settings file gets at least the Boomerang's
  entry (6,344, 7 components). Lesson for later: adding entries to a game file can need more size table room than
  the bytes it grew (compare with a game file of the same shape).
- **In game (2026-11-18): works.** No crash; held up, the harps spin and sit clear above Link's head (the game's
  own lift is enough: no higher lift needed); colours right (Saria white, Bolero red, Serenade blue seen).

### Giant's Knife and Hover Boots placed to fit their shelves (branch `claude/shelf-positions`, not yet tested in game)
- **Bug (in game):** on the Kokiri Shop's shelves the Giant's Knife and the Hover Boots "need repositioning".
- **Found in the game's files** (new `tools/item_pose.py`): a shelf shows an item in its own pose `Pose_Common`
  (size, turn and height of the bone `Skl_Root`). The Giant's Knife's pose stands it 1.36 m tall, centred on
  the shelf point: through its shelf and into the one above (shelves are 0.65 m apart, items 0.5 m apart). The
  Hover Boots' pose lifts them 0.72 m above it.
- **Fix:** their shop versions (`SHELF_POSE` in `tools/shop_items.py`) get a posed copy of the item's animation
  project (`NX2Son_Sword_Biggoron_Animation`, `NX2Sr_Adult_HoverBoot_Animation`: same-length names), made
  smaller when taller than 0.5 m and lifted so the model's box starts 0.08 above the shelf point (about where the
  Hookshot's box starts with its tuned lift). Giant's Knife: size 0.8 -> 0.295 (about 0.45 m long), height
  0 -> 0.334; Hover Boots: height 0.716 -> 0.08. The turn stays the game's; chests and the items themselves keep
  the game's animation. Check build: both files read back as intended.
- `tools/item_pose.py` reads poses the same way as the ground-height fix (branch `claude/ground-heights`, in
  `tools/ground_items.py`); when both are merged, the ground fix should use `item_pose` too.
- **In game (2026-11-18): not right.** The knife on the shelf was much too small and too high (the user: it
  should be only slightly smaller than its default); the Hover Boots were invisible on their shelf. Bought and
  held up, the knife was invisible (it wasn't before) and the boots were inside Link.
- **Why (found in the files):** both items' own animation projects hold only `Pose_Common`, and the game uses
  it for the shelf, for holding up and for the ground. Items that look different on a shelf have a `Pose_Shop`
  too (the bomb, the Deku Stick). So the posed copy also changed how the bought item is held up: the boots'
  0.716 lift was right held up, and the knife held up became tiny and off to one side.

### Shelf fix reworked: only the shelf changes (2026-11-18, branch `claude/shelf-positions`, not yet tested in game)
- **Found in the game's files:**
  - Which pose an item shows is in `AS/Item_Common.root.asb`: each state lists the poses it tries, in order. On
    a shelf (`Rotate_Shop`, what the shelf AI plays): `Pose_Shop`, `Pose_Stoped`, `Pose_Common`, `Pose_GetDemo`.
    Held up (`Rotate_GetDemo`): `Pose_GetDemo`, `Pose_Common`. During the shop talk (`Rotate_Stoped`):
    `Pose_Stoped`, `Pose_Shop`, `Pose_Common`, `Pose_GetDemo`. The spins have such lists too, and they are
    needed: no animation project has a `Rotate_Shop` or a `Pose_Stoped`.
  - Six projects have a `Pose_Shop` (bomb, Deku Stick, Deku Seeds, arrow, arrow bundle, Hylian Shield). It is
    always their `Pose_Common` times one number (0.5 to 1.15), which makes them at most about 0.5 m tall.
  - Measured on the models' vertices: in `Pose_Common` and `Pose_Shop` an item stands on the point it is placed
    at (lowest vertex -0.03 to +0.03), in `Pose_GetDemo` it is centred on it. The Giant's Knife, Hover Boots
    and Hookshot have only a centred `Pose_Common`: on a shelf their lower half is inside it. The Hookshot's
    lift tuned in game (0.25) puts its lowest vertex exactly 0.000 above the shelf point.
  - The first fix measured wrongly. It turned the item's box from `ActorInfo`, but for the knife that box is
    the model already posed; and a pose replaces the bone's place in the model instead of adding to it (the
    boots' bone sits at 0.906 in the model, so their pose 0.716 lowers them). The order of the angles (X, Y,
    Z) was right. In its own pose the knife lies nearly flat: 1.53 m wide, 0.50 m tall, 0.56 m deep, from 0.26
    under the shelf point to 0.24 above. The boots are 0.44 x 0.40 x 0.43 m, from 0.19 under it to 0.21 above.
- **Fix, Giant's Knife** (`SHELF_POSE` in `tools/shop_items.py`): its shop version's animation project is a
  copy of the game's `Item_DekuSeed_Animation` (exactly `Pose_Common`, `Pose_GetDemo`, `Pose_Shop` for the bones
  `Root` and `Skl_Root`, all the knife's model has) named `NX2S_Sword_Giant_______` (same length). `Pose_Common`
  and `Pose_GetDemo` are the knife's own `Pose_Common`, byte for byte (size 0.8, turn -1.9315 / 0.4259 /
  -1.4437, place 0.012 / 0 / 0): held up it is as in the game. `Pose_Shop` is that pose times 0.8 (size 0.64,
  the same turn), lifted 0.2093 so its lowest vertex is on the shelf point: 1.22 m wide, 0.40 m tall, 0.45 m
  deep. Nothing in the file moves; its size entry is the Deku Seeds project's (8232).
- **Fix, Hover Boots:** no game project with a `Pose_Shop` has their bones (their pose sets 18: legs, wings), so
  they keep their own animation and their shelf is placed 0.19 m higher in the map, as the Hookshot's
  (`SHELF_LIFT`): lowest vertex on the shelf point, default size, held up as in the game.
- `tools/item_pose.py` now reads a model's vertices and bones and works out where a pose puts them.
- Check build (knife on the Kokiri Shop's heart shelf, boots on shelf 2): the new project reads back with the
  three poses as above and differs from the Deku Seeds project only in its name and the three poses' values;
  the boots' pack names their own animation project; their shelf is 0.19 higher.
- **Not known:** at 0.64 the knife is wider than a shelf slot (items are 0.5 m apart), so its ends reach into the
  slots next to it. A shop item is also in its `Pose_Shop` while the shop talk has it (looked at, chosen).
- **In game (2026-11-18, evening; combined test with the size rules and the progressive chests):** works, except
  that the Giant's Knife held up by child Link is a little too high (it floats well above his hands). The knife
  on its shelf, the Hover Boots on theirs, the boots held up and the empty shelves after buying: as intended.
- **The bought Giant's Knife held up 0.11 m lower: tried and taken out again.**
  - **Found in the game's files:** the get scene (`Dm_SY_GetInEvent`, entry `Item_Position`) shows the item with
    `EventIgnitionShowItem`, `ItemPos` (0, 0, 0): at a point the game's code works out. No file has that point
    (`GameParameter/GetDemoParam` is empty, the player's settings have nothing for it). It follows Link's age:
    where Link shows an item to someone (`ShowItem`), the offsets from that point for child and adult, taken
    from the raised hand (bone `Weapon_L` in `Evt_ShowItem` and `Evt_ShowItem_Failure`), put it 0.60 m higher for
    adult Link both times, and in the get pose (`Demo_Get_Child_Loop`, `Demo_Get_Adult_Loop`: one hand raised) that
    hand is 0.59 m higher for adult Link (1.17 and 1.76 m). So an item is the same height above the raised hand
    at both ages. Worked out, not read: the point is about 1.4 to 1.5 m up for child Link (the cameras of the
    scene show up to 1.83 m there).
  - Every held-up pose is centred on that point, whoever gets the item (Kokiri Sword -0.25 .. +0.25, Bow -0.42 ..
    +0.50, Megaton Hammer -0.29 .. +0.42, Hover Boots -0.19 .. +0.21); the game tunes no height for an age. The
    Fishing Rod, the game's other long item for both ages, hangs lower (-0.55 .. +0.22).
  - The knife's pose is not too high for a child in particular: it lays the knife's 1.68 m nearly flat (15
    degrees), its middle on the point, the hilt 0.37 to 0.77 m out to one side. Over the hand (within 0.2 m of the
    upright line through the point) its underside is 0.143 under the point, where the Kokiri Sword, the Hookshot
    and the Poacher's Saw reach 0.25 under it: it floats 0.11 higher above the hand than they do, at both ages.
    Next to child Link (1.17 m tall) that shows more; the game's own two scenes for it (Medigoron, Biggoron)
    also pull the camera back (2.24 m away instead of 1.75 to 2.05).
  - **Fix** (`HELD_LOWER` in `tools/shop_items.py`, `shelf_copy` in `tools/item_pose.py`): in the shop version's
    project `NX2S_Sword_Giant_______`, `Pose_GetDemo` is placed 0.11 lower: place 0.012 / 0 / 0 -> 0.012 / -0.11 /
    0, size 0.8 and the turn as the game's. `Pose_Common` stays the knife's own, byte for byte; `Pose_Shop` is
    unchanged. Held up the knife is now -0.372 .. +0.129 from the point, its underside over the hand 0.253 under
    it (as the Kokiri Sword's), the hilt 0.21 to 0.32 under it out to the side. The same for adult Link.
  - Check build (knife on the first Kokiri Shop shelf of both ages): the project reads back with `Pose_GetDemo`
    differing from `Pose_Common` in the height only (4 bytes), same length as the Deku Seeds project, size entry
    8232 as before.
  - **Not known:** whether 0.11 is enough to the eye (one number, `HELD_LOWER`), and whether the hilt, now about
    level with the raised hand as it turns, comes near Link's head.
  - **Not covered:** a Giant's Knife from a chest, a gift, the ground or a Gold Skulltula is held up through the
    item itself (`Item_Sword_Giant`) with the game's `Weapon_Sword_Biggoron_Animation` (only `Pose_Common`; the
    Biggoron's Sword and the game's own `Shop_Sword_Giant` use it too): still at the game's height.
  - **In game (2026-11-19):** still felt a bit high to the user, who preferred the game's own height ("it was
    just the shelves that were wrong"). The build before (2026-11-18, evening) already held it exactly as the game
    does: its `Pose_GetDemo` was the knife's `Pose_Common` byte for byte (read back from the built file). So
    `HELD_LOWER` is now empty: held up, the knife is the game's again; only its shelf pose differs.

### In-game result: bought shelf items vanish
- **Confirmed in game:** the Giant's Knife, Hover Boots and Song of Storms disappeared from their shelves right
  after buying and stayed gone (shop screen, leaving and coming back, day/night change, reload).

### A sold shelf's model no longer comes back in the same visit (not yet tested in game)
- **Bug (in game):** a bought changed shelf stayed empty after a reload, but in the same visit its model was
  back on the shelf (not buyable).
- **Found in the game's files:**
  - The shelf AI (`Shop_Item_Base.root`, and our copy `Shop_NX2_Once.root`) has no memory. Its one selector
    on `QueryShopItemIsSoldOut` hides the model on "sold out" and **shows it again** on "not sold out"
    (`OneShotGameModelControllerSetVisible` true), and it is asked in every state: idle, and after every
    message of the shop talk but "hide" and "get demo start" (message numbers matched with the shopkeeper's
    `NpcCommon.event.root`: focus, select, hide, get demo start / end, show, put in pouch).
  - The sold count is saved game data, not the shopkeeper's memory: `Shop_SoldNum.<shopkeeper>.<shelf 0-7>`
    (`EventTriggerAddShopItemSoldNum` adds 1; `EventQueryCheckIsSoldOutSelectItem` compares it with the
    list's `StockNum`). In `GameData/GameDataList` those 104 numbers (13 shopkeepers x 8) are saved and have
    a reset type of their own, 2, that only one other value has: `GraveYard_Hylia_030_AISchedule_For_SongOfSun`.
    So the game restocks its shops by itself, most likely when the time of day changes (a guess from that
    one name; the earlier test build had the Sun's Song in a chest). `DisplayShop` has no "refresh shelves" step and
    `EventTriggerInitializeBuyShop` only clears the selected shelf.
  - So: once the count is back at 0 the shelf shows its model again. The flag our shop version set
    (`OneShotActorChangeIsRespawn`) only matters when the area is loaded; the shopkeeper's refusal is the buy
    check (Link already has the item). The game's own stock-of-one shelves (the "low on stock" Kokiri Shop)
    are meant to come back the same way.
- **Fix** (`shop_items.sold_for_good_ai`, one more link changed in `Shop_NX2_Once.root`): the selector's
  "not sold out" side leads to the file's own `OneshotDoNothing` instead of the "show" node (the "sold out"
  board's AI has the same selector side). No node added. A model is shown from the start without any AI
  saying so (the Piece of Heart's AI has no such node), and the model held up in the buy scene is shown by
  another node ("get demo start", sent before the sale is counted): checked by the builder. Once hidden as
  sold, nothing in the shelf's AI shows it again. Read back: the selector's two links, nothing else.
- **Guessed:** when the game resets the count (it was not seen happening), and that the shelf's query reads
  that same count (it is in the game's code, not in a file); that nothing outside the AI shows
  the model (then this would not be enough); that the "show" node left without a link is harmless.
- **Limit:** the hidden shelf can still be pointed at in the buy screen. After a restock the shopkeeper would
  offer it again: refused for an item Link can hold once, but an item he can hold several of could be bought
  again from the empty shelf until the area is reloaded (then the shelf is gone for good).
- **To test:** buy the Giant's Knife, the Hover Boots and the Song of Storms: each is on its shelf before,
  held up in the buy scene, and gone at once after; still gone after leaving the buy screen, after walking
  out of the shop and back in, after day / night changes (Sun's Song) while staying in the forest, and after
  a reload. The other shelves sell as before.

### In-game results of the kept fixes
- **Sold shelves stay empty after a reload** (Giant's Knife, Hover Boots, Song of Storms): confirmed. But in the
  same visit, after buying, the item's model is shown again (not buyable). Wanted: the model gone at once after
  buying and never back.
- Confirmed: Sun's Song from a chest and Song of Storms on a shelf as the harp, Saria's Song as a harp on the
  ground, the slingshot from a chest with 30 seeds, the ocarina gift, the skulltula's heart piece spinning.
- The bridge scrub wasn't tested. Rule from the user: never place the same item twice (that build had the
  slingshot in a chest and at the scrub).

### Progressive upgrades taken out again
- The progressive-upgrade work below (the shared get `GetPouchContent<GetPouchContent>` choosing the level, the
  chest flows `Dm_SY_Treasurebox` / `Dm_SY_TreasureboxSmall` handing over owned levels, the waits, the scrub
  level choice, chests holding the first level, the refusals on the ground / shelves / skulltulas) is **removed**
  from `tools/build_mod.py`: those rounds piled untested changes onto the game's shared flows (the user's call).
  The game's own get and chest flows are no longer in the mod. Kept: the slingshot first (`FAMILY_ALIASES`: a
  small seed bag or quiver placed alone becomes its weapon, the bag comes with it; scrubs add it,
  `SCRUB_COMPANIONS`), the ocarina gift, sold shelves vanishing, the skulltula's item spinning, the harp model.
- To redo later, one piece at a time, each tested alone (chests first). What was learned stays below: the
  pouch query `EventQueryIsExistInPouch`, the `Armor_*` / `Weapon_*` inventory names, the game reading written
  data a frame or two later (wait after writing), chests showing only the window for an owned item.

### Progressive gets mixed up items: the game reads written data a frame later
- **In game (combined test):** the chests gave items depending on the order they were opened (the slingshot
  chest, holding up the slingshot, said "You got a giant's wallet!"), the rock-circle Kokiri gave a giant's
  wallet and no ocarina, and a chest held up the biggest bomb bag while giving the first one.
- **Cause:** the shared get wrote the item name into `Scrub_Business_TempItemName_02` and compared it at once;
  a value written into the game data is read back only a frame or two later, so it compared the **previous**
  item's name. The game's own flows wait after writing (`Enemy_Scrub_Business_Seed`: String64 -> `EventWait` 1
  frame -> use; `MelodyGet_Sun_SubEvent`: flag -> `EventWait` 2 frames -> read). (The user's French randomizer
  notes the same and waits there too; read only.) Now a wait of 2 frames (`WRITE_WAIT_FRAMES`) after every
  name written: in the shared get and in the scrub branch (the level written for its line).
- **Chests and owned items:** a chest whose item Link already owns only shows the window and adds nothing
  (`Dm_SY_Treasurebox` Event25 / `Dm_SY_TreasureboxSmall` Event17: `EventQueryCanAddToPorch` case 2 ->
  `GetPouchContent<DisplayGetByActorName>`). A chest now holds its family's **first** level (the slingshot, as
  the user wants shown, not a bag), and for a level of a placed family case 2 goes to the hand-over too, where
  the shared get gives the next level (`chest_owned_edit`, same write + wait + compare). The first chest of a
  family holds up the right model; later ones hold up the first level's model while the window names the level
  given.
- **Harp songs:** shown on the shelf and held up as the harp; it doesn't spin held up and clips Link's face a
  little (the harp's model is centred, the rupee's sat on its base). Not fixed yet.
- Rebuilt; not yet tested in game.

### In-game results of the first bug fixes, and the slingshot first
- **Ocarina gift: fixed.** The rock-circle Kokiri gave the Fairy Ocarina with the window, no freeze, and it
  played straight away (not held up: it has no held-up animation).
- **Scrub selling the small seed bag alone: froze again** (sound and world running, no control). It should never
  be given alone: the slingshot comes with its bag, then the bigger bag, then the biggest (the user's rule). A
  small seed bag or quiver placed alone now becomes its weapon at the start of the build (`FAMILY_ALIASES`): the
  check shows and gives the slingshot / bow, the small bag comes with it (`SCRUB_COMPANIONS` now also gives the
  bow its small quiver at scrubs). Not yet tested in game.
- **Changed shelves after a reload:** the Giant's Knife and Hover Boots were back on their shelves, but the
  shopkeeper refused to sell them again. Wanted: sold out for good, the item not shown. (Fixed again below.)
- **Gold Skulltula:** the Piece of Heart dropped and was taken without pressing A; once collected the
  skulltula stayed gone; left lying, the skulltula came back with its item. Correct. But the heart piece didn't
  spin. (Fixed below.)

### Sold shelves stay empty, Gold Skulltula drops spin (branch `claude/item-fixes`; not yet tested in game)
Two bugs seen in game on 2026-11-17 with the fixes below. Both are in the builder (`tools/shop_items.py`,
`tools/ground_items.py`, a few lines of `tools/build_mod.py`); nothing here has been tried in game yet.

**1. Bought changed shelves were back after a reload (but could not be bought again).**
- What "sold" is in the game's files:
  - The shop talk (`DisplayShop`) adds one to the shopkeeper's sold number
    (`EventTriggerAddShopItemSoldNum`), which the shopkeeper compares with the list's `StockNum`
    (`EventQueryCheckIsSoldOutSelectItem`). That count lives for one visit: nothing saves it.
  - The shelf actor never dies. Its AI (`Shop_Item_Base.root`, in every shelf's pack) asks the shopkeeper
    through its `ForSale` link and its shelf number (`QueryShopItemIsSoldOut`) and hides or shows its model
    (`OneShotGameModelControllerSetVisible`); it also tells a linked "sold out" board
    (`OneShotShopItemSendSoldOutMessage`). `Shop_Board_SoldOut` boards are placed by hand in the maps and
    linked from the shelves that can sell out (the two stock-of-one shelves of the "low on stock" Kokiri
    Shop, the masks, the blue fire, the Market's first bomb shelf).
  - A list entry can name a flag that makes it sold out (`Release`: `IsCheckSoldOutGameData`,
    `SoldOutGameData`: `IsGet.Item_Bottle_BlueFire`, `Get_StoneOfFire_IsCompleted_Exp`). It takes a named
    flag (a plain one, or a formula `BoolExp`, whose steps only read named flags, numbers and lists); the
    flag of a map placement (`Bool64bitKey`) has no name, and the `IsGet.` flags are one per item (under its
    inventory name: `IsGet.Weapon_Sword_Giant`, `IsGet.Armor_Adult_HoverBoot`), not one per shelf: they
    would count an item found anywhere else, and a second Piece of Heart on a shelf would be sold out
    from the start. Not used.
- Cause: the flag the shelf took over (previous fix) is never set. A placement's flag is set when its actor
  dies of a reason marked `IsSetRespawnFlagToFalse` (`System/CombinationDataTableData/*DeathReasonProcedures`:
  picked up, life depleted, burned...), or by the AI node `OneShotActorChangeIsRespawn` with Bool false. A
  bought shelf does neither, so after a reload it was placed again, and the shopkeeper's count was back at 0.
  That the shopkeeper would not sell the Giant's Knife and the Hover Boots a second time is most likely the
  game's buy check (`EventQueryCheckBuyResult`: Link already has them), not a memory of the sale: an item Link
  can hold several of could probably have been bought again.
- Fix: shop versions (`Shop_NX2_*_Once`) get an AI of their own, `Shop_NX2_Once.root`
  (`shop_items.sold_for_good_ai`): the shelf's AI with one addition. Its one selector on "sold out" led to
  "hide the model"; it now leads to both at once (`Element_Simultaneous`, copied from the file) of the same
  hide node and `OneShotActorChangeIsRespawn` (false), copied from the AI of an item taken through an event
  (`PouchContent.event.root` in `Pack/AI.Global`, where it runs next to the node that puts the item in the
  pouch; red ice, spider webs and falling floors use it in their own AI). The two new nodes come after the
  file's 54, so no node number changes. The pack also gets the small file naming that AI (`AI/AIInfo/
  Shop_NX2_Once`), and the actor's `AIInfoRef` points at it. The game's own shelves keep their AI.
  - Result expected: buying sets the placement's flag (reset type 24 since the previous fix: never reset),
    and a `NoRespawn` placement whose flag is set is not made again: after a reload the shelf is **empty**,
    for good, at both ages. No "sold out" board: the game shows one only where a board is placed and linked,
    and with the shelf not placed nothing would tell the board.
  - A shop with a shelf missing is something the game does itself: the Market potion shop's bug shelf is
    only placed once `Market_Item_Bottle_TutorialEvent_Shop_Bottle_Insect_Appeared` is set, its shopkeeper
    always (the mask shelves likewise).
  - Read back: every node of the shelf AI is as it was but for that one link; the two files are the same in
    every shop version's pack (one resource size entry each).
- Limits, unchanged: a shelf for which no flag is free (the printed NOTE) still comes back; a game shelf
  actor (`Shop_...`) put on another shelf is as the game made it.
- To test: buy the Giant's Knife (`KF_KOKIRI_CHILD_SHOP_08`) and the Hover Boots (`KF_KOKIRI_CHILD_SHOP_02`),
  leave the shop and come back, and again after saving and restarting: both shelves empty, the cursor skips
  them or stays usable, the other six shelves sell as before. Also on a new visit before buying: both items
  are on their shelves (the shelf must not mark itself sold when it is made).
- Uncertain until tested: that the game runs an AI file under a new name from the actor's pack (every game
  actor with an AI of its own has it there, but all our earlier AI edits changed existing files); that the
  two numbers at the end of an AI file (`hashes`, kept as they were) are not checked against its contents;
  that the shopkeeper never answers "sold out" for a shelf that is just being made (it would mark an unsold
  shelf); how the buy screen's cursor treats the empty place.

**2. The Piece of Heart dropped by a Gold Skulltula did not spin.**
- Cause, from the game's files: items on the ground are spun by their AI. The ground items' AI
  (`DropItem.root`) and the Piece of Heart's own (`Obj_Heart_Piece.root`) play the animation command
  `Rotate_Obj` (`OneShotASPlay`) whenever nothing is playing, and their animation settings (`ASInfo`:
  `Item_Obj`) start nothing by themselves (`AutoPlayASName` empty). The token's AI (`Item_Token_Gold.root`)
  plays nothing: the token spins because its own settings (`ASInfo`: `Obj_Token_Gold`) start `Rotate_Obj` by
  themselves; they are `Item_Obj` in every other value. A Gold Skulltula drop has the token's AI (it is what
  marks the skulltula done) but was given the item's or the ground shield's `Item_Obj`: nothing ever started
  the spin.
- Fix (`ground_items.build`, version `token`): a drop keeps the token's `ASInfo`, and takes only the animation
  file (`ASRef`) from the item when it is a ground item whose file knows `Rotate_Obj` (Piece of Heart:
  `AS/Obj_Heart_Piece`; rupees: `AS/Item_Rupee_Green`), else from the ground shield (`AS/Item_Common`). Not
  the token's own file: its spin uses an animation of the token's model (`Rotate_Obj_St`). The `Rotate_Obj`
  animation itself is in `Item_Common_Animation`, which the items' animation settings list. Everything that
  worked is as it was (the token's AI, blackboard, death settings, physics; picked up by walking into it).
- To test: `KF_KNOW_IT_ALL_HOUSE_GS=Obj_Heart_Piece`: the dropped Piece of Heart spins; it is still taken by
  walking into it, the skulltula stays gone once it is taken and is back with its item when it isn't.
- Uncertain: how the spin looks on items that only exist as the model held up (Boomerang...): they get the
  same command from `AS/Item_Common` (every item on the ground spins with it), not tried.
- Test build: `KF_KOKIRI_CHILD_SHOP_08=Item_Sword_Giant KF_KOKIRI_CHILD_SHOP_02=Item_HoverBoot
  KF_KNOW_IT_ALL_HOUSE_GS=Obj_Heart_Piece` with the usual fixes and the gold rupee; `tests/logic_check.py`
  and `tests/db_check.py` pass.

### Progressive upgrades (branch `claude/item-fixes`)
- A check given any level of an upgrade family now gives the **next level Link doesn't have** (never skipping
  one). Families, from the game's tables: wallet 500 -> 1000 (200 is the start), bomb bag 20 -> 30 -> 40,
  slingshot -> seed bag 40 -> 50, bow -> quiver 40 -> 50 (the small bag and quiver come with the weapon), stick
  bag 20 -> 30, nut bag 30 -> 40, Goron Bracelet -> Silver -> Gold Gauntlets, Silver -> Gold Scale, Hookshot ->
  Longshot, Magic -> Double Magic, Fairy Ocarina -> Ocarina of Time (`PROGRESSIVE` in `tools/build_mod.py`).
- How: the level is chosen with the game's own "is it in the pouch?" query
  (`PouchSystemActor.EventQueryIsExistInPouch`, 0 = yes, as in `DisplayShop`), from the top level down. The
  idea of asking the pouch comes from the user's progression fix for the French randomizer (read only).
  The inventory name differs for some items: the gauntlets are kept as `Armor_Child_Gauntlet_Goron` /
  `Armor_Adult_Gauntlet_*`, the bow and slingshot as `Weapon_Range_*` (only those have `IsGet.` flags).
  - Chests, NPC gifts and song skips all end in `GetPouchContent<GetPouchContent>`: its first step now keeps
    the item name (`Scrub_Business_TempItemName_02`, an unsaved text game data only written when a scrub's talk
    starts) and, for a level of a family (or a chest's held-up version of one), gives the chosen level with a
    copy of the entry's own window and add steps (`progressive_get_edit`). Ocarinas get the sync steps.
  - Scrubs choose the level in their own branch and set `Scrub_Business_TempItemName_00` to it, so the
    generic line names the level actually sold.
  - Items on the ground, on shelves and dropped by Gold Skulltulas are given by the game's own code (no flow to
    choose the level): progressive items are refused there for now.
- A chest's held-up model / the gift's held-up model still shows the level placed, the window names the level
  given. Not yet tested in game.
- **Songs show Sheik's harp** (the user's choice) instead of the green rupee: the song items borrow the rupee
  model (`Obj_Rupee`) and the game has no note model. For every song placed, its model settings (`ModelInfo`
  in its pack) and its `RSDB/ActorInfo` row (model, size, the larger heaps) take those of the cutscene harp
  `Dm_Item_Sheik_Harp` (model `Item_Harp_Sheik`), before any ground, shelf or token version copies the model
  (checked: the versions have the harp too). Not yet tested in game.

### Fixes for the three bugs of the item type test (branch `claude/item-fixes`; not yet tested in game)
All three are in the builder (`tools/build_mod.py`, `tools/ground_items.py`); nothing here has been tried in
game yet.

**1. Ocarina gift froze the game (gifts and scrubs).**
- Cause, from the game's files: the shared get event `Dm_SY_GetInEvent` shows the item in Link's hands. It makes
  the item's own actor (`Player_Event.EventCreateShowItemFromActorFileName`) and plays its animation command
  `Rotate_GetDemo`, waiting for it to end (`EventIgnitionShowItem`: `IsAsPlay`, `IsWaitEnd`). All 40 actors the
  game's own flows give through that event have an animation file (`ASRef`, a loose `AS/*.asb`) that knows that
  command. The ocarinas (Link's instrument, no `ASRef` at all), the songs, the small seed, stick and nut bags
  and the small quiver (no `ASRef`), the three stones (`AS/Dummy`) and the six medallions (`AS/DemoDummy`) don't:
  the wait never ends. That is the freeze with the Fairy Ocarina, and the earlier one with the seed bag from a
  scrub (`Item_BulletBag_Small`: no `ASRef`). Chests never run that event, which is why a chest ocarina only
  showed nothing.
- Also found: why a song cutscene calling `Dm_SY_GetInEvent` gave nothing (2026-11-17, song skip).
  `RSDB/GameAnalyzedEventInfo` lists for each event the flow files it may run (`SubFlowList`); `Dm_MelodyGet_Saria`
  lists `GetPouchContent` but not `Dm_SY_GetInEvent`. All 113 events that list `Dm_SY_GetInEvent` also list
  `GetPouchContent` (the first runs the second).
- Fix: `ground_items.can_hold_up(item)` reads the item's animation file for `Rotate_GetDemo`. An item without
  it is given the way the game's cutscenes give ocarinas and songs: `GetPouchContent<GetPouchContentByActorName>`
  (the "You got ..." window and the item, nothing held up; what the song skip already uses, confirmed in game
  there).
  - Gifts (`gift_edit`): the gift's call of `Dm_SY_GetInEvent` becomes that call. Items Link can hold up are
    edited as before (same bytes as before for the gold rupee gift).
  - Scrubs (`scrub_flow_edit`, point 3): the one-time sale pays and hands over inside
    `Dm_SY_GetInEvent<GetInEvent_NotTurn_2DShop>`. In front of that call, one new check per such item
    (`Scrub_Business_TempItemName_00 == item`): the price is taken the same way
    (`EventTriggerAddGameDataIntToRupee` on `SimpleShop_Price`, `EventWaitStableNumDisplay`), the item given with
    the get window, then on as after the game's call.
  - The builder checks the `SubFlowList` rule above before using the window (`direct_get_allowed`).
- Playable straight away: after an ocarina (items whose `PouchSpecialDeal` is `Ocarina`) given in a flow, the
  three steps the game runs after changing Link's inventory behind his back (Dream world boss fights:
  `SubEvent_AllBossBattle`, `DreamBossStage`, `Npc_Dream`): one frame's wait,
  `UISystemActor.EventTriggerSyncPlayerEquipmentAndPouch`, `Player_Event.EventWaitCreationFinishedEquipment`.
  Copied from `SubEvent_AllBossBattle` with their actors (`sync_template`, `sync_steps`); also after an ocarina
  given by a song cutscene. Not done for chest and ground ocarinas (their get is not an event flow of ours).
- To test: the rock-circle Kokiri gives the Fairy Ocarina (window, no freeze, playable at once); a scrub selling
  an item of that kind (seed bag, a song, an ocarina): price taken once, item given, scrub leaves.

**2. Changed shop shelves came back after a reload.**
- How the game remembers that a map object is gone: `GameData/GameDataList` has one saved flag per map
  placement that can be gone (`Bool64bitKey`, keyed by the placement's hash). Which placements have one, and its
  reset type, follow the actor's `ActorGameDataSetting`: `NoRespawn` 24 (never reset: heart pieces, Gold
  Skulltulas, silver rupee tokens), `BancReset` 25 (fairies, scrub leaves, the shops' boards and their bottle,
  bomb, Bombchu, tunic and mask shelves), `SupplyObject` 88 (pots, rocks, grass), `BancResetNoItemWarp` 280
  (enemies, Business Scrubs), `AlwaysRespawn`: no flag (every other shelf, all of the Kokiri Shop's). The setting
  files themselves are not in the game's files (only their names). The game has no shelf that stays sold for good
  by itself: its stock-of-one shelves are `AlwaysRespawn` (the "low on stock" nuts and stick) or released by named
  flags (masks).
- Cause: our shop versions ask for `NoRespawn`, but the shelf placements have no flag in the list, so nothing
  was saved. A flag can't be added without changing the save file's layout (every flag has a place in it).
- Fix (`shelf_flag_map_edit`, `keep_flags`, and the step after the count boards in `main`): a changed shelf takes over the flag
  of a shop object the build removes anyway: its own count board ("x5"), else one of the boards of the "before
  the Deku Tree" shop set that `kokiri_shop_full_stock` removes. The shelf's placement gets that board's hash
  (its `Hash`, its physics placement ID, the shopkeeper's two links to it, the map's group lists; stale mentions
  of the removed board in those lists are dropped first), and the flag's reset type in `GameDataList` goes from
  25 to 24. One byte per shelf changes in `GameDataList`; its size and the save layout stay the same. The
  shelf hashes appear nowhere else in the Kokiri Forest maps, the shared map resources or `Logic` (checked).
- Limits: only shop versions (`Shop_NX2_*_Once`); a game shelf actor put on another shelf is still
  `AlwaysRespawn`. A shelf with no count board of its own needs a board from the removed set: the Kokiri Shop
  has 3 of those and 6 shelves without boards (3 per age), so with more than 3 of them changed the rest get a
  printed NOTE and still come back. (10 "sold out" boards that only exist before the Deku Tree are in the two
  Dynamic maps and could be removed for more flags: not done, the shop fix is tested as it is.)
- Uncertain until tested: that buying sets the shelf's flag at all (the game's own flagged shelves suggest it),
  and that the reset type in the list alone decides when a flag is reset.
- Seen on the way, not changed: the Business Scrubs' flags are type 280, the same as ordinary enemies. A scrub
  made one-time by the builder "stayed gone" in the 2026-11-17 test; if that was checked without leaving the
  area, it may be worth checking again after leaving it.

**3. A Gold Skulltula dropping an item came back after a reload.**
- How the game marks a skulltula done: not when it dies, but when its token is picked up, and the token does
  it. Dying only sets an unsaved flag, `IsGoldSkullDead.IsGoldSkullDead_<placement hash>` (100 of them, reset
  type 25, not in the save; set by `Enemy_Skulltula_Gold.action.root`). The skulltula's saved flag is the one of
  its placement (`NoRespawn`, type 24). Its AI (`Enemy_Skulltula_Gold.utility.root`) hands that flag's hash to
  whatever it drops (`QueryBlackboardOverwriteParamAddNoRespawnGmdHash`, key `GoldTokenGmdHash`, through
  `OneShotDropSetOverWriteParam`). The token (`Obj_Token_Gold`) has that key in its blackboard and its own AI
  (`Item_Token_Gold.root`): when it dies of reason 10 (picked up) it runs `OneShotGoldTokenDeadAfter`.
- Cause: the item dropped instead (the item itself or its ground version) has neither the key nor that AI.
- Fix: what a Gold Skulltula drops is now a version of the item built from the token itself
  (`Obj_NX2_GS_<item>`, version `token` in `tools/ground_items.py`; `gs_drop` in the builder): the token's pack
  with its AI, blackboard, death settings, physics and lock-on kept, and the token's name, model, animation and
  item settings replaced by the item's. Animation settings are the ground shield's, as for every ground version
  (the token's make the token's model spin), or the item's own when it is a ground item already (Piece of
  Heart, rupees); no effect link; the base's lift settings. Its own token (`Obj_Token_Gold`) is left as it is.
- To test: the Know-It-All House skulltula drops the Piece of Heart, it can be picked up, and after leaving and
  reloading the skulltula is gone. Also that a skulltula killed but whose item was not taken is back after a
  reload (as the game does with tokens), and how the item hangs where the skulltula died (token physics).
- Uncertain: that the hash is handed over when the drop comes from `Drop__DropActor` rather than the drop
  table, and what else `OneShotGoldTokenDeadAfter` does (game code).

### In-game test: item types (20 kinds of item on Kokiri Forest checks; test build only)
Placed by a planning agent with the builder as it is (no code changed). Results:
- **Mido's chests** (left to right: Boss Key `Item_Dungeon_BossKey`, Sun's Song `Item_Melody_SunSong`, Map
  `Item_Dungeon_Map`, adult wallet `Item_Wallet_Medium`): all given correctly. The song shows a **green rupee**
  as its model when held up ("You learned the Sun's Song!").
- **Shelves** (Giant's Knife `Item_Sword_Giant`, Hover Boots `Item_HoverBoot`, Kokiri Emerald
  `Item_Stone_Forest`, Song of Storms `Item_Melody_StormSong`): all bought and in the menus; the shop does not
  refuse a song (unlike a bottle). The song shows the green rupee on the shelf; the sword and the boots need
  repositioning on the shelf. **After reloading the area the changed shelves were back** (the "sold once" shop
  versions are not remembered).
- **Ground items** (heart container, small key, Goron Tunic, Hylian Shield): all worked. The small key's
  count stayed 0 (no keyed door here): keys, maps, compasses and boss keys will have to be bound to their
  dungeon.
- **Rocks and bushes**: all dropped the right item (token, Goron Bracelet, magic blessing; compass, bottle);
  the bracelet and the blessing lie too low (half in the ground). Rocks and bushes did not come back.
- **Gold Skulltula** (Know-It-All House) dropped Saria's Song (green rupee model), but **came back after a
  reload**: with an item instead of its token it must still count as done.
- **Gift**: the rock-circle Kokiri giving `Item_Ocarina_Fairy` (`Dm_SY_GetInEvent`) **froze the game
  completely**.
- **Scrub**: the bigger bomb bag (`Item_BombBag_Medium`) worked. But progressive items must never skip a level
  (the wallet and bomb bag were given as the second level directly).
- **Songs** all played (with the ocarina from Saria; the gift one froze).
- Item tables (notes from the planning agent): one generic map, compass, boss key and small key for every
  dungeon (`Item_Dungeon_*`, `Obj_Dungeon_SmallKey`; Gerudo Fortress keys have their own actors); some dungeon
  chests have special opening events (`BottomOfTheWell_GetCompass`, `ForesetTemple_GetBossKey`, the boots
  chests). Bigger wallets and bags have no ground model (`no PouchContentRef`): chests, gifts, scrubs only.
  Wallets 200/500/1000; bags fill up when received (`IsItemStockMaxIfGet`). Rewards (`Item_Stone_*`,
  `Item_Medal_*`) are plain key items.

### Songs: an item instead of the song, without the lesson (branch `claude/song-skip`)
- How Saria's Song is started: an `EventRequestActor` in the child Sacred Forest Meadow map requests
  `SacredForestMeadow_Field_MelodyGet_Saria` (flow `SacredForestMeadow`): fade out, then
  `EventSystemActor.EventTransition` to the cutscene event `Dm_MelodyGet_Saria`, then Saria sits, a challenge
  step (`Get_StoneOfFire_MelodyGet_Saria`), Saria marked as talked to. Its trigger area
  (`Logic/SacredForestMeadow_Child_Prefab_bbc3`) exists while `DoorOfTime_IsAfter_Step01_Exp` (Zelda's letter)
  is set **and the cutscene `Dm_MelodyGet_Saria` has not been played**: what stops it repeating is "played", not
  owning the song. Saria herself is created on the same letter flag (`..._Prefab_3265`). The cutscene sets no
  flags of its own; it only gives the song (`GetPouchContent<GetPouchContentByActorName>`). There is no flow
  action that marks an event as played.
- `tools/build_mod.py`: a check with `"song": {"flow", "item"}` in its data (first: "Song from Saria" in the
  Sacred Forest Meadow). The cutscene is still started, so the game records it as played, but its
  `EntryPoint0` now only fades in, hands over the item through `Dm_SY_GetInEvent<GetInEvent_NotTurn_NotNpc>`
  (as the Skull Kid hands over his heart piece) and ends: no lesson, no song (`song_skip`).
- Test build (`out/mods`): Saria's Song -> Piece of Heart, plus a test-only change (not in the builder) so a new
  file can reach it: Saria and her trigger no longer need Zelda's letter (Saria was there, on her stump).
  **In game: the screen faded out and in, nothing was given, and it happened again every time** (not counted
  as played). Most likely the cutscene event stopped at the call of `Dm_SY_GetInEvent`, which no song cutscene
  uses. Changed to the step the cutscene itself gives the song with, `GetPouchContent<GetPouchContentByActorName>`
  ("You got ..." window, then the item; the Song of Time cutscene shows the Ocarina of Time with the same
  flow), plus the item's companions (slingshot -> seed bag). **Confirmed in game:** fade out and in, the Piece
  of Heart window, the heart piece given, no Saria's Song, and the trigger did not come back.

### Correction: song cutscenes are ordinary event flows (first look at timelines)
- **Correction:** an earlier note here said the songs are in cutscene flows with timelines that
  `formats/evfl.py` can't read. Wrong: all 12 `Dm_MelodyGet_*` song flows (and `GetPouchContent`) are plain
  flowcharts and round-trip byte for byte. Each gives its song with one call of the shared flow
  `GetPouchContent`, entry `GetPouchContentByActorName`, parameter `ActorName` (Saria event 20, Forest 11,
  Epona 50, Fire 208, Shadow 15, Light (`Shine`) 249, Spirit (`Spilit`) 11, Storm 21, Sun in `Dm_MelodyGet_Sun_03`
  30, Time 93, Water 120, Zelda 66; `Dm_MelodyGet_Time` event 255 also shows the Ocarina of Time). Inside,
  that entry ends in `PouchSystemActor.EventTriggerAddOrRemovePouchContent`, as for other gifts. The lesson
  (notes shown and played) is separate (`Dm_SY_Ocarina`, `MelodyType`). Changing a song's item: not tried in
  game yet; open questions: does the game skip/replay a song cutscene by checking the song is owned, how the
  get window looks mid-cutscene.
- The 264 unreadable flows: 261 are pure timelines (cinematic tracks `Dm_<Area>_<nnnn>` and their `_Effect`,
  `_Env` companions: camera, animation, light, sound; none gives an item or sets a flag) and 3 use entry point
  variables (`Dm_SY_Ocarina`, `Dm_SY_Get`, `LinkSleepInBed`). Timelines are laid out much as in the public
  Breath of the Wild documentation (a read-only scratch parser reads all 261; one clip field is of unknown
  use). Entry point variables are a small addition (5 entry points use them) and would make `Dm_SY_Ocarina`
  editable, needed only to change or skip song lessons.

### Deku Scrubs in the builder (branch `claude/scrubs-in-builder`, on top of the event flow tool branch)
- `tools/build_mod.py` now changes what a Deku Scrub sells, for the scrubs that sell one thing once (their talk
  runs `SimpleShopRoot_Enemy_Scrub_Business_Pouch`: the stick and nut upgrade scrubs, the Death Mountain heart
  piece scrub):
  - map: the scrub's `ScrubBusiness_ShopItemActorName0` becomes the item (every copy and age; read back);
  - flow `Enemy_Scrub_Business_Common`: in front of the root's first item comparison, one new branch per item
    (`Scrub_Business_TempItemName_00 == item` -> `SimpleShopSub_Scrub_Business_OneTime` with the item, the
    price the game's own calls ask for the scrub's original item, and the generic line), made with the event
    flow tool's `add_switch`, `add_subflow`, `repoint`;
  - text: the generic line `Enemy_Scrub_Business_NX2_Item` in every language (as confirmed in game).
- Refused for now: the other scrubs (potions, seeds, bugs, the Dream scrubs: several items each), and items
  the game's own branches already sell (Piece of Heart, stick bag, nut bag): a new branch for one would also
  catch the game's other scrubs selling it (the Death Mountain heart-piece scrub would sell at 40, not 100).
- Every scrub in the game (all maps): 4 stick-bag, 2 nut-bag, 3 heart-piece (`Heart_01` x2, `Heart_02`),
  consumable sellers, 25 Dream scrubs (`Enemy_Scrub_Business_Dream*`).
- Areas without IDs: the builder takes the check's name (`"LW Deku Scrub Grotto Nut Upgrade=Item"`).
- Test build (`out/mods`): `LW_NEAR_BRIDGE_SCRUB` = Bomb Bag: **confirmed in game** (made by the builder).
  The grotto nut scrub was given `Item_BulletBag_Small`, thought to be the slingshot: it is the **seed bag**;
  bought, then the game froze while Link held it up (nothing gives that item alone in the game). The slingshot
  is `Item_Range_SlingShot` (what the Deku Tree chest gives). Retest: **the slingshot was given, without the
  seed bag (0/0 seeds)**. Nothing in the game files gives the bag with the slingshot (the Deku Tree chest's
  special event `InsideTheDekuTree_GetSlingShot` only plays a Navi line; the item tables don't link them).
- So a scrub selling an item also gives what it needs (`SCRUB_COMPANIONS`: slingshot -> `Item_BulletBag_Small`),
  silently (`PouchSystemActor.EventTriggerAddOrRemovePouchContent`, `IsGetEvent` false) and only after a
  successful buy (`ScrubBusiness_BuySuccess`, as the game's own callers check it). Not yet tested.
- The grotto seed scrub then sold seeds to the slingshot without a bag ("pretty full, buy anyway?") and buying
  gave the seed bag. Its offer checks `IsGet.Weapon_Range_SlingShot`, not the bag. When any check gives the
  slingshot, the builder now puts a check in front of both seed sales of `Enemy_Scrub_Business_Common`
  (`IsGet.Item_BulletBag_Small`): without the bag the scrub says a new line `Enemy_Scrub_Business_NX2_NoSeedBag`
  ("Squee... On second thought, you've got nothing to carry these in!") and the sale ends as not bought, like
  the game's "not enough rupees" refusal. Not yet tested. Not done yet: the seed sales of the Dream scrubs and
  the wandering seed scrub (their own flow files).
- **Confirmed in game:** the grotto scrub sold the slingshot **and** the seed bag (30/30). A slingshot from a
  chest (Kokiri Sword chest) also comes with 30/30 by itself: only the scrubs' way of giving
  (`Dm_SY_GetInEvent`) needs the companion; gifts use the same flow, so probably they do too (not tested).
  The seed scrub refusal wasn't seen (the bag-less slingshot was no longer reachable in that test).
- Seen: a seed scrub sells seeds again and again. In the randomizer a scrub must sell its item once.
  How the game keeps a one-time scrub gone: the scrub sits in a prefab (`Enemy_Scrub_Business_Set_01_d7f2`)
  that a logic module per scrub (`Logic/Enemy_Scrub_Business_DekuStickPouch_300c`, `..._DekuNutsPouch_a676`,
  `..._Heart_Piece_86ac`, ...) creates only while the scrub's sold flag (e.g.
  `LostWood_Enemy_Scrub_Business_DekuStickPouch_01`, set by the talk entry after a buy) is off. The repeat
  sellers (seeds, potions, bugs) have no flag and no such module. Making one sell once needs a sold flag of its
  own: the game's flag list (`GameData/GameDataList`, 11,292 bools, by hash, each with a place in the save) has
  no free one, so it would mean adding flags, not tried yet. Also every talk name is registered in
  `RSDB/EventSetting`.
- **Flags looked into.** `GameData/GameDataList`: a flag's key is MurmurHash3 (32-bit, seed 0) of its name
  (checked on `LostWood_Enemy_Scrub_Business_DekuStickPouch_01`, `ScrubBusiness_BuySuccess`,
  `Npc_SkullKid_Child_IsGetHeartPiece`); each has `DefaultValue`, `ResetTypeValue`, `SaveFileIndex`, and
  `MetaData` gives each save file's size and offsets (`progress.sav` 703,884 bytes), so adding saved flags
  would also mean changing the save layout. Not needed for scrubs: the 11,657 `Bool64bitKey` flags are keyed
  by **map placement hash** (287 placements in Kokiri Forest and the Lost Woods: rocks, bushes, enemies, ...),
  and **every Business Scrub placement has one** (reset type 280), repeat sellers included. Most likely the
  "gone" state that the one-time sale's `EventTriggerRequestDeath` records.
- So the builder now makes **any** scrub sell once (`scrub_flow_edit`): a scrub whose talk doesn't run the
  one-time root (seeds, arrows, potions) gets at the start of its talk the root's own first step
  (`EventScrubBusinessWriteGameDataBancItemName`, which copies the map setting into
  `Scrub_Business_TempItemName_00`) and a check: its item -> the one-time root (the new branch sells it once,
  the scrub leaves), anything else -> the game's talk as before (other scrubs with the same talk are not
  changed). The price is what the game asks for the scrub's original item (copies may differ: the first's).
  Still refused: scrubs with nothing set in the map (the bug seller), the Dream scrubs (other flow files).
- Test build: the Lost Woods grotto seed scrub (child seeds / adult arrows) sells a gold rupee once.
  **Confirmed in game:** it sold the gold rupee and stayed gone. No new flags needed.
- The other grotto scrub (seeds, unchanged) offers nothing without a slingshot; talking to it a second time
  and choosing "see ya later" froze the game. Its talk never reaches the changed root or the new steps, and
  the flow's entry point lists are the game's apart from the root's: most likely the original game (not yet
  checked unmodded).
- Event flow tool PR merged (#10).

### Gold Skulltulas, gifts and Deku Scrubs: how the game gives their items (research, test build only)
None of the three can be changed by the builder yet. Read from the game's own files:
- **Gold Skulltula** (`Enemy_Skulltula_Gold`): its token comes from a drop table in its pack
  (`DropTable_Token_Gold` -> `Obj_Token_Gold`), and it has the same `Drop__DropActor` instance setting as pots
  and rocks. So the builder's map edit for rocks (add `Drop__DropActor` to the placement) may work for it too.
- **Gifts**: most hand their item over through the shared flow `Dm_SY_GetInEvent` (entries `GetInEvent`,
  `GetInEvent_NotTurn`, ...) with the item as its `ActorName` setting: the Skull Kids' heart pieces, the Lost
  Woods target prize, the Deku Theater upgrades, Fado. A few cutscenes add the item directly
  (`PouchSystemActor.EventTriggerAddOrRemovePouchContent`, `Actor`): Saria's ocarina (`Dm_Kokiri_0155`), the
  Ocarina of Time. Songs are in cutscene flows with timelines, which `formats/evfl.py` can't read yet.
- **New check found**: the rock-circle Kokiri (`Npc_Kokiri_008_Child`) gives a blue rupee once all the circle
  rocks are lifted (`Event224`, after `..._LiftRock_AllBroken_Talk_Event166`). Not in the data yet.
- **Deku Scrubs** (`Enemy_Scrub_Business`): the map placement names what it sells
  (`ScrubBusiness_ShopItemActorName0..2`); the shared flow `Enemy_Scrub_Business_Common` matches that name and
  calls a sell step with the item as a setting. The one-time upgrades (stick bag, nut bag, heart piece) use
  `SimpleShopSub_Scrub_Business_OneTime` (`ActorName`, `Price`), which pays and gives through `Dm_SY_GetInEvent`.
  The flow is shared by every scrub, so per-scrub items will need a branch per scrub.
- Test build (`out/mods-kinds-test`, nothing in the builder): the Know-It-All House skulltula drops a Piece of
  Heart (rock-style map edit), the rock-circle Kokiri's gift is a gold rupee, the Lost Woods stick-bag scrub
  sells a Bomb Bag. **Confirmed in game, all three:** the skulltula dropped the Piece of Heart, the Kokiri gave
  the gold rupee (also with the rock circle fix moving him), the scrub sold a Bomb Bag (held up, 40 rupees).
  The scrub's lines still talk about the Deku Stick bag (its `SellerMessageId`).
- **Builder: Gold Skulltulas and gifts.** `tools/build_mod.py` now changes:
  - Gold Skulltulas: `Drop__DropActor` added to the placement, as for rocks (`DROP_ADDED`); the item lies on
    the ground (`DROP_ON_GROUND`).
  - gifts with `"gift": {"flow", "event", "item"}` in their data: the `ActorName` of that event's call of
    `Dm_SY_GetInEvent` (checked: it is such a call and gives the expected item; read back, only those values
    change). Gifts that add their item directly (Saria's ocarina) have no such data yet and are still refused.
  With the test's assignments the builder writes the map and the flow byte for byte as tested.
- New check `KF_CIRCLE_KOKIRI_GIFT` ("KF Rock Circle Kokiri Gift", kind gift, child): the Kokiri's blue rupee
  for lifting all the circle rocks. Refused without `--fix kokiri_circle_after_dungeons` (tested only with it).
  `KF_KNOW_IT_ALL_HOUSE_GS` randomizable "yes". `tools/build_db.py` gives a gift's original item from its data.
  Kokiri Forest: 120 checks; db_check 0 errors, logic tests pass.
- **Generic scrub sales line** (test build only, `out/mods-scrub-test`): a new label
  `Enemy_Scrub_Business_NX2_Item` in `EventFlowMsg/Enemy_Event.msbt` (all 16 languages, English text; the
  file has no attribute section, so a new label is only a label and a text): "Ah, the <item>! It's <price>
  rupees. Wanna buy it?". The item name is the shop's item-name tag (2,3) reading
  `Scrub_Business_TempItemName_00`, which the scrub fills from its map setting `ScrubBusiness_ShopItemActorName0`;
  the price is the scrub lines' own tag. The stick-bag scrub: map setting -> `Item_BombBag_Small`, the flow's
  name check (`Event315`) and its three sell calls follow, with the new line. **Confirmed in game:** "Ah, the
  bomb bag! It's 40 rupees." and the sale worked.
- **One test launcher.** Test builds now go into `out/mods/NX2-ZOOTR` and are started with
  `Launch NX2-ZOOTR test.bat` (plus `Launch 100 save (unmodded).bat`); the per-test launchers were deleted.
  `tools/build_mod.py` removes its earlier output (`<out>/<name>/romfs`) before building, so no file of an older
  build stays in the mod. `tools/evfl_test_mod.py` no longer writes a launcher (`--longshot` removed).
- Scrubs are not in the builder yet: the Lost Woods isn't classified (no check IDs), each scrub needs its own
  branch in the shared flow, and the sales lines name the original item (no line names the item from a
  variable).

### Shopkeeper greeting back in, rock circle after the dungeons, Bottle shelf retest
- `--fix kokiri_shop_full_stock` again makes the child shopkeeper greet as after the Deku Tree, now wired
  the right way round (case 0 = yes = the "after" side). Same edit as the confirmed event flow test: the
  file it writes is byte for byte the tested one. `tools/evfl_test_mod.py` now uses the builder's edit.
  **Confirmed in game.**
- New `--fix kokiri_circle_after_dungeons`: the rock circle by Mido's house as after the dungeons, at both ages.
  - `Logic/KokiriForest_Common_Level_All_01_6aaf`: the AND node (adult, and `SageOfForest_IsBefore_Step08`)
    that swaps the ring of 8 for 4 other rocks takes "is child" instead of the flag, so it is never true: an
    adult sees the ring of 8 like a child. One link changed, nothing else in the file. **Confirmed in game.**
  - `Component/AIScheduleParam/Npc_Kokiri_008_Child`: the Kokiri who tries to lift the middle rock does that
    in his default schedule; his schedule after the Kokiri Emerald (`Get_StoneOfForest_IsCompleted_Exp`)
    becomes the default, so he isn't on the rock from the start. **Confirmed in game** (moved).
  - The middle rock still couldn't be lifted: it is two rocks in one place, a prop with no lift setting
    (`Obj_LiftRock_A_02`, the one he acts out lifting) and a liftable `Obj_LiftRock_A_01`.
    `Logic/KokiriForest_Child_Level_All_02_6960` swaps them after the Kokiri Emerald; the fix now gives both
    fixed values (prop never, liftable rock always). **Confirmed in game:** all the circle rocks lift
    (child), each dropping its own green rupee.
  - Check data: the adult ring of 8 has no rule any more, the 4 other adult rocks are never there
    (rule False, not randomizable), the middle rock is "is_child". The builder refuses an item on the adult
    circle rocks or the middle rock without this fix. Logic tests updated.
- Event flow tool branch (`claude/evfl-add-events-b2737c`): `example_shop_bottle` wired for 0 = yes.
- Bottle shelf retest (test build only, `out/mods-bottle-test`, nothing in the builder). The earlier refusals
  said nothing, as their branches were wired backwards.
  - Test 1: `DisplayShop` sold the Bottle itself when `Shop_SelectItemName` is the shelf's name. **In game:
    1 Empty Bottle, works, shelf empty after** (so the selection holds the shelf's name, `Shop_NX2_...`).
    But no price question and no held-up get, as those steps were skipped.
  - Found where the refusal is: after "I'll buy!", `Event27` sorts the item by kind and `Event77`
    (`PouchSystemActor.EventQueryCanAddToPorchByGameData`) checks pouch room; "no" leads to the "never mind"
    lines. Test 2: only that sorting is skipped for the bottle shelf (straight to `Event6`, where the game's
    own pay and held-up get start). **In game: refused again** before any price question, with
    "The empty bottle? Wait... Hold on a second." (`Shop_01_02_1`).
  - That line is one of 3 picked at random by `NotAvailableTalk` ("Oh, wait. Actually..." is another), so
    the earlier refusals may have come from there too. `NotAvailableTalk` is run by `SelectItem_CheckAvailable`,
    which `NormalFlow` calls (`Event121`) **before** the price question. It sorts the item by kind; for
    bottled items (kind 5) it asks `PouchSystemActor.EventQueryIsAnyBottleEmpty`, and with no empty bottle
    it refuses. The Bottle is most likely sorted there. Test 3 also starts `SelectItem_CheckAvailable` with a
    branch: the bottle shelf goes straight to its "OK" return (`Event124`), every other item to the
    game's check (`Event318`). From "OK" to the price question are only the camera, focus and talk steps.
    Test 2's skip after "I'll buy!" stays. **In game: still refused.**
  - **Decision:** if bottles go on shelves, they use test 1's way (the flow sells the bottle itself: no price
    question, no held-up get, but it works). That is `example_shop_bottle` on the event flow tool branch.
    Whether bottles go in shops at all is left for later, so the builder still refuses a bottle on a shelf.

### Why event flow edits showed nothing: yes and no were the wrong way round (branch `claude/evfl-in-game-0d5942`)
Looked into offline (game, Longshot and its logs only read). **Confirmed in game (2026-11-17):** with the test mod, the
 child shopkeeper greeted normally before the Deku Tree and the goodbye line was replaced. Event flow edits work.

- **Likely cause: in this game's flows a yes/no question answers 0 for yes and 1 for no.** Both edits
  assumed the opposite (1 = yes, as in Breath of the Wild). Read from the game's own flows, four ways:
  - `DisplayShop`: "has Link 20 rupees" (`EventQueryHasRuppe`): case 0 -> "You wanna transfer 20 rupees?",
    case 1 -> "it doesn't look like you have enough rupees";
  - `DisplayShop`: "is child" (`EventQueryPlayerIsChild`): case 0 -> the child's Deku Shield lines, case 1 ->
    the adult's ("They're just for kids, you know");
  - `DisplayShop`: "selected item is `Weapon_Shield_Deku`" (`EventQueryIsGameDataString64`): case 0 -> the
    Deku Shield lines, case 1 -> the checks for the other shields and tunics;
  - `Npc_Kokiri_001_Shop_Child`: after buying, "has the Deku Shield" case 0 and "tutorial already given"
    case 1 -> the Deku Shield tutorial talk, then the flag is set.
  And the game itself: on a new file the shopkeeper says the "low on stock" lines, which are on case 1 of
  the switch on `Meet_DekuTree_IsAfter_Step02_Exp`.
- **What the two edits really did:**
  - Shopkeeper greeting: both cases were sent to case 1's step, which is the "low on stock" side. So the
    edit forced the greeting the game already gave. (The line removed from `build_mod.py` took
    `dict(e.cases).get(1)` as the "after" side.)
  - `DisplayShop` branches: "name matches" was wired as case 1, so a matching item went straight on to the
    game's buy check, and a non-matching item went to the rupee test and then (having the rupees = 0) on to
    the game's check too. The new steps could only run for an item that did NOT match while Link had fewer
    than 5 rupees. So that test said nothing about what `Shop_SelectItemName` holds: still open.
    The same mistake is in `tests/evfl_add_check.py` (`example_shop_bottle`) on
    `claude/evfl-add-events-b2737c`: to fix there before any further use.
- **The game does read our flow files.** Longshot's logs (`logs/longshot_log*.txt`) print a line each time
  the game opens a file from the mod folder (`mods: <path> <- <mod file>`). The two test sessions with flows
  show `Event/EventFlow/Npc_Kokiri_001_Shop_Child.bfevfl.zs` and `Event/EventFlow/DisplayShop.bfevfl.zs`
  opened from our folder, like the map, table and pack files. No error or rejection lines about them.
  Longshot also merges its own button prompt sizes into the mod's resource size table (harmless).
- **No other copy of the flows.** Searched 14,921 files outside `Event/EventFlow` (every folder except
  textures, models, sound, shaders, terrain, physics, animation and effects), packs opened (three levels
  deep): no BFEVFL file anywhere else, in no pack. What names flows: `RSDB/EventSetting` (2,380 rows: an
  event's flow file `Work/Event/EventFlow/<name>.evfc`, its entry point, its settings),
  `RSDB/GameAnalyzedEventInfo` (2,379 rows: per event, `SubFlowList`, the other flow files it calls; a
  custom event that calls a flow file not in its list may need its row changed: not tested),
  the actor packs (the flow an actor starts) and the address table (2 mentions of the folder).
- **Our written files are sound.** Both flows round-trip byte for byte. The edited files have the same
  header fields as the game's (magic, version 0.4.0.0, byte order, alignment, file size field = real size,
  one flowchart, relocation table at its place with its own offset) and the same `.zs` frame (single
  segment, dictionary 1, content size present and right, no checksum). The shopkeeper file differed from
  the game's by one byte (the case's event index).
- **Test mod** (`tools/evfl_test_mod.py`, new; output in `out/mods-evfl-test`, launcher
  `out/Launch evfl test.bat`, checklist `out/EVFL_TEST_CHECKLIST.md`; `out/mods` untouched). One flow,
  `Npc_Kokiri_001_Shop_Child`, two independent edits: the greeting switch with both cases to the normal
  greeting (the fix: case 0 is the "after" side; the Talk entry point's list is recomputed), and the three
  goodbye lines replaced by the "not enough rupees" line (control: shows that the flow is read whatever
  yes/no means). Plus the skippable opening, to get there fast.
- README: the yes/no rule and where flows are named, under "Things this game does differently".

### Shopkeeper greeting edit removed
- `--fix kokiri_shop_full_stock` no longer edits the child shopkeeper's talk
  (`Event/EventFlow/Npc_Kokiri_001_Shop_Child.bfevfl`): tested, it changed nothing (he still greets with
  "low on stock" before the Deku Tree), so the mod no longer carries that file. The rest of the fix (one shop
  set, every shelf open, the adult's own list) is unchanged and tested. No event flow file is edited by the
  builder now; the greeting can come back once event flow edits are shown to work in game.

### In-game test of the two new tools (scratch build; branches `claude/ainb-format-aa01ca`, `claude/evfl-add-events-b2737c` not merged)
- **AINB tool: works in game.** The rock circle module (`Logic/KokiriForest_Common_Level_All_01_6aaf`)
  with the "is adult" input taken out of its switch (node 32, `OperateAND`): a child on a new file saw the 4
  corner rocks instead of the ring of 8, so the game ran our edited AI file.
- **Wanted (the user, 2026-11-17):** the rock circle as it is after the dungeons, at both ages: the ring of
  8 rocks, and the Kokiri (`Npc_Kokiri_008_Child`) away from the middle rock. Needs the circle module
  changed so the 8 are never deleted and the 4 never created, and finding what keeps the Kokiri there.
- **Event flow tool: the shop Bottle still can't be bought** (same "take it back" line). The new branch was
  added to `DisplayShop` twice (selected item `Shop_NX2_Bottle_5_Once`, then `Item_Bottle`), in front of the
  only call of the game's buy check (`NormalFlow`: sold out? -> callswitch `SelectItem_CheckAvailable`);
  the other two callers of the take-back talk are for the Hylian Shield and the tunics only. So either the
  selected item's name is stored as something else, or the game doesn't read our copy of `DisplayShop`.
  Next: a test that tells the two apart.
- **Disguised Bottle shelf** (test build): the shelf kept the Bottle's look and name, but its item row and
  item settings said one Deku Nut (as the game's own Deku Nut shelves); `DisplayShop` got three branches
  (shelf name and `Item_Bottle` -> give the Bottle, `Item_DekuNut` -> give the Hookshot as a marker). Result:
  still couldn't be bought. Decided (the user, 2026-11-17): **no bottles in shops** (the builder already
  refuses them); bottles go anywhere else.
- **Open question, bigger than bottles:** no edit to an event flow (`.bfevfl`) has shown any effect in game
  yet: the shopkeeper's greeting branch (`Npc_Kokiri_001_Shop_Child`), and every `DisplayShop` branch, even
  for an item the buy code accepts. Edits to maps, tables, packs and AI files all worked. Possibly the game
  doesn't use our edited event flows (read from elsewhere, or skipped). To find out before relying on event
  flow edits (ground ocarina, custom events).
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

### Event flows: new steps can be added (branch `claude/evfl-add-events-b2737c`)
- `formats/evfl.py` could change existing events; it can now add to a flowchart: events of every type
  (`add_action`, `add_switch`, `add_fork`, `add_join`, `add_subflow`, and the game's two extra types
  `add_callswitch`, `add_return`), actors (`add_actor`), actions and queries on an existing or new actor
  (added by name when an action or switch uses one the actor doesn't have yet), entry points
  (`add_entry_point`), all with parameters; and `repoint(old, new)` sends every link to an old event to a
  new one. New things go at the end of their lists, so existing indexes never move. Names must be unique
  (events, actors by name + secondary name, entry points): a second one is refused.
- `evfl.dumps_checked(flow)` is the writer for edited flows: checks the flow (`fc.check()`: names, every
  index in range, a fork's join is a join, parameters the file can hold), writes it, reads it back and
  compares every event, actor, action, query, parameter (with its type) and entry point with what was meant
  (`evfl.differences`). `evfl.dumps` itself is unchanged.
- Two things found in the game's files on the way:
  - the 32-bit values of `return` events and `callswitch` cases are the FNV-1a hash of a name (`Yes`, `No`,
    `Complete` match), so both take a name now (`evfl.return_hash`);
  - an entry point's list is the subflow and callswitch events that can run from it (all 5,465 entry points
    of the 650 files read). `fc.update_entry_points()` works it out again after an edit (`dumps_checked`
    does it).
- New test `tests/evfl_add_check.py` (in `run_tests.bat`), on the real game flows, read only:
  - unchanged: 650/650 pass the checks and `dumps_checked` gives the game's bytes back;
  - one event of every type, a new actor, a new action and a new query added and linked in front of the
    first entry point: 650/650 read back as meant (old parts untouched, new parts as written);
  - 11 kinds of mistake refused (name used twice, link to an event that isn't there, parameter too big...).
  - Round trip unchanged: 650/914 byte-identical (`tests/roundtrip.py`, Event folder); `tests/edit_check.py`
    passes.
- Two worked examples kept in that test. **Examples only: not used by the builder, not tried in the game.**
  - `example_item_get`: what an "item get" needs, read from `Dm_Kokiri_0155` (Fairy Ocarina) and
    `GetPouchContent`: action `PouchSystemActor.EventTriggerAddOrRemovePouchContent` `{Num, IsEquipDIrect,
    IsSetMessageTargetActorName: True, Actor, IsGetEvent: False}` (into the pouch), then subflow
    `GetPouchContent` entry `DisplayGetByActorName` `{ActorName}` (the window: `EventTriggerSetForGetWindow`
    + `OpenGetWindow`). Or one subflow for everything, as chests do: `GetPouchContent` entry
    `GetPouchContentByActorName` `{ActorName}` (window, rupee counter, pouch, autosave).
  - `example_shop_bottle`: in `DisplayShop`, a branch in front of the callswitch that runs the game's buy
    check (`SelectItem_CheckAvailable`, in `NormalFlow`): for one selected item with enough rupees, pay
    (`EventTriggerPayItemPriceAtShop`), give `Item_Bottle` with the two steps above, mark the shelf sold
    (`EventTriggerAddShopItemSoldNum`, shop board message, shelf refresh), return to the shelves
    (`Buy_ReturnStart_NoDofReset`). 10 new events, one new action name on `PouchSystemActor`, one link moved;
    every other event, actor and entry point reads back unchanged.
  - To find in game before using it: whether `Shop_SelectItemName` holds the shelf's name
    (`Shop_NX2_Bottle_5_Once`) or the pouch item's (`Item_Bottle`; the game compares it with
    `Weapon_Shield_Deku`, whose shelf is `Shop_Weapon_Shield_Deku`, so probably the item's); whether the
    branch needs the shopkeeper's price talk first; whether the shelf empties as after a normal buy.
- Still refused, as before: the 264 flows with timelines or entry point variables.

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
