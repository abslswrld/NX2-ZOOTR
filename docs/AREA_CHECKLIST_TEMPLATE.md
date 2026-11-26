# Area checklist template

The shape every area's in-game test list takes (phase 1 of `docs/ROADMAP.md`, "alongside"), so each area is
tested the same way. Claude fills it in for each test round; the user plays it and writes the answers.

- The list goes to `out\TEST_CHECKLIST.md`, the answers to `out\TEST_ANSWERS.md` (D5). Both are replaced for
  every test round; the results are kept in `CHANGELOG.md`.
- The two blocks to copy are below: **The checklist** and **The answers**. Everything in `<angle brackets>` is
  filled in; a line that does not apply is left out, not left empty.

## Before the list is written
1. **The area's every-spot build script passes** (D27, rule 5 of "an area is done"): an item on each of the
   area's spots, each read back. Then `run_tests.bat` passes as a whole.
2. **The test build is in `out\mods\NX2-ZOOTR`,** built with the standing fixes: `--fix skippable_opening
   --fix magic_is_separate --fix bombs_without_bracelet --fix bombchus_without_bag --fix
   forest_temple_bow_room_door --fix key_items_tab_open`, plus whatever the round tests.
3. **Anything sold** (a scrub, a shop shelf): `KF_SHOP_RUPEE_ITEM=Obj_Rupee_Gold` on the Kokiri Shop floor, and
   the list says where it is. Nothing sold: no gold rupee, and the list says so.
4. **What Link needs is given at the start** (`--start`, `--start-flag`) or put in the area's first check, so
   no step waits on something the round does not test. Keys for a dungeon: `--start-flag
   DungeonInfo.<dungeon>.SmallKeyNum=<n>`.

## What goes on the list (D27)
Pick in this order, and stop at what fits in one day. A longer area gets several lists, one per day, each its
own test round.

1. **Each check kind once, in each of its forms,** that the area has and that has not passed in an earlier area.
   See "Check kinds already passed in game" below. A form is what makes two checks of one kind behave
   differently (a small chest and a small chest without a baked shadow; a big chest; a gift from a person or
   from a cutscene).
2. **Every unusual spot:** a check that differs from the others of its kind because
   - it appears from a switch, a fight or an event (read from the room's logic: a `Gimmick_TreasureBoxAppear_*`
     module, or an `AiGroups` link to an `EventRequestActor`);
   - its contents can't be read from the game's files (a chest whose map entry names no item: a refill chest);
   - it sits in a special room (a grotto, a room that locks behind Link, a room with saving off);
   - a cutscene gives it (`docs/CUTSCENES.md`, the area's section).
   Each unusual spot found in the files gets a line saying what the files show, so the user knows what to
   expect.
3. **The area's own settings and cutscenes** (the table in "What an area is done means" of the roadmap): each
   one built in this area gets a section.
4. **Samples for the rest:** one or two spots of each kind already passed, picked from places not tried yet;
   loose rupees and hearts (D35) included. Beehives are left out for now; flat grass tufts are never checks.
5. **Save and reload,** last: what was opened stays opened, what was picked up stays.

Left out of every list:
- "Does it load" or "does the game start" steps.
- Spots the list does not change (the list names only what the build changed).
- Anything the every-spot build script already proves from the files alone (the right object, the right file).

How the list is written:
- **Places by the remake's names,** from the game's own text ("Sacred Forest Meadow", "Kokiri Emerald").
- **Grouped by age, then by the way through the area,** so the user walks it once. Child first when both.
- **One line per check:** where it is (how to reach it, in a few words), what Link should get, and what should
  happen. Items are named as the game names them, with the size for a family level ("the bigger bomb bag").
- **The way in:** Longshot's debug menu for a dungeon or an area reached late (D26: it leaves an area untouched
  on a new file); a new file for anything that starts from Kokiri Forest.
- A step the user may skip says so, with the reason ("the same kind as one that passed").

## The checklist

Copy from here to `out\TEST_CHECKLIST.md`:

````markdown
# In-game test: <what this round tests> (built <date>, phase <n>, <part or area, and day n of m if several>)

**Start:** close the game, run `out\Launch NX2-ZOOTR test.bat` and make a **new file**. <How to get there: "Go
to <place> with the debug menu" or "Walk from Kokiri Forest">. <Age: "Stay a child" / "Become an adult" /
"Child first, then adult">.

**What this is for:** <one or two sentences: which part of "an area is done" this round covers, and why these
checks were picked (new kinds, unusual spots, samples)>.

**What this build has**
- **<check, in a few words> holds <item>.** <Anything unusual the game's files show about it.>
- <What Link starts with, if the round gives anything: items, keys, flags.>
- <Gold rupee: "A gold rupee lies on the Kokiri Shop floor, by the counter, for buying" / "Nothing is sold, so
  there is no gold rupee.">

**Fixes in this build:** the opening can be skipped, magic items give no magic meter, bombs without the Goron
Bracelet, Bombchus without a bomb bag, the Bow room's door, the Key Items tab open<, and any other fix of this
round>.

## Child

### 1. <place> (<how to reach it>)
- [ ] <check>: <what Link should get, and what should happen>.
- [ ] <check>: ... <"Skip it if you like: the same kind as <check>, which passed.">

### 2. <next place on the way>
- [ ] ...

## Adult

### 3. <place> (<how to reach it>)
- [ ] ...

## <n>. <setting or cutscene of the area, if this round builds one>
- [ ] <what to do, and what should happen>.

## <n>. Save and reload
- [ ] After saving and loading: what you opened stays open and the items are still yours.

**If it goes wrong, note:** where, what you did last, and what the game showed.
````

## The answers

Copy from here to `out\TEST_ANSWERS.md`. One line per checklist line, the same numbers and headings, the
statement to answer before the `:`.

````markdown
# Answers: test of <date> (<what this round tests>, phase <n>, <part or area>)

Fill in after each `:` with a few words. Leave a line blank if you skipped it. Tell me when it's filled in.

## 1. <place>
- <check>: <what should happen, in a few words>: 

## <n>. Save and reload
- Opened checks stay open, items kept: 

## If something didn't work
- What happened and where: 

## Anything else you noticed
- 
````

## After the answers
1. **`CHANGELOG.md`:** an entry with the date and every answer, each check by its ID, what it gave and what
   the user saw. A line that failed says what was found and what was changed.
2. **The area's data** (`data/world/<Area>.json`): each check that passed gets `"randomizable": "yes"` and a
   note `"changed in game on <date> (tools/build_mod.py): gave <item>..."`; then `python tools/build_db.py
   <Area>`, and the area's data test expects the new count.
3. **This file:** each kind or form that passed for the first time is added to "Check kinds already passed in
   game" below, so the next area does not test it again.
4. **`docs/ROADMAP.md`:** the part or area marked as passed, with the date.
5. **Failures** are fixed and tested again in the next round, never stacked with a new part (D38).

## Check kinds already passed in game
A kind or form here is not tested again in a later area (D27), only sampled. Add to it after each round.

| Kind and form | Where it passed | When |
|---|---|---|
| Small chest | Kokiri Forest (Mido's house); Forest Temple | phase 0; 2026-11-23 |
| Small chest without a baked shadow | Forest Temple | 2026-11-23 |
| Big chest | Kokiri Forest (the Kokiri Sword's chest); Forest Temple | phase 0; 2026-11-23 |
| Big chest without a shadow | Forest Temple | 2026-11-23 |
| The boss key's chest | Forest Temple | 2026-11-24 |
| A chest with an opening event made for its item (removed or kept by `CHEST_EVENTS`) | Kokiri Forest (the Kokiri Sword's chest, Mido's chests); Forest Temple (Beth's chest) | phase 0; 2026-11-25 |
| A chest that appears after a fight | Sacred Forest Meadow (the Wolfos grotto); Forest Temple (first Stalfos room, the Bow's, the Floormaster's) | phase 0; 2026-11-23 to 25 |
| A chest that appears after a Poe | Forest Temple (Joelle's, Beth's) | 2026-11-25 |
| A chest that appears from an eye switch (falls) | Forest Temple (block room) | 2026-11-23 |
| A refill chest (its map entry names no item) | Forest Temple (falling ceiling room) | 2026-11-25 |
| A grotto chest | Kokiri Forest (the Storms grotto); Sacred Forest Meadow (the Wolfos grotto) | phase 0 |
| Ground item (loose) | Kokiri Forest | phase 0 |
| Gift from a person | Kokiri Forest | phase 0 |
| Song check | the forest | phase 0 |
| Saria's bridge gift | Lost Woods (the bridge) | phase 0 |
| Scrub | the forest | phase 0 |
| Shop shelf, one item | Kokiri Shop | phase 0 |
| Pot | the forest (the boss key and a Medallion from the Know-It-All Brothers' pots, 2026-11-24); Forest Temple (a small key) | phase 0; 2026-11-23 to 24 |
| Rock | Kokiri Forest | phase 0 |
| Bush | Kokiri Forest | phase 0 |
| Gold Skulltula | Kokiri Forest; Forest Temple | phase 0; 2026-11-23 |
| Boss heart | Forest Temple | 2026-11-24 |
| A dungeon reward given by a cutscene (the Medallion) | Forest Temple (Saria's cutscene) | 2026-11-24 |
| Upgrade families (no skipped level) | every kind above except shop shelves and big chests | phase 0 |
| A dungeon's small key from a person (a gift with flow data) | Kokiri Forest (the Kokiri at the rock circle; a door of the Forest Temple opened with it) | 2026-11-25 |
| A dungeon's boss key from a Deku Scrub | Lost Woods (the scrub near the bridge) | 2026-11-25 |
| A stone on a shop shelf; a Medallion from Saria's bridge cutscene | Kokiri Shop; Lost Woods (the bridge) | 2026-11-25 |
| A first weapon alone in a pot, with its bag | Kokiri Forest (the Know-It-All Brothers' pot: the Fairy Bow) | 2026-11-25 |
| The start of a new file: items kept under another name, hearts, rupees | Kokiri Forest | 2026-11-25 |
| A dungeon's small key, boss key, map and compass on shop shelves (sold once, counted by the sale) | Kokiri Shop (a door of the Forest Temple opened with the shelf's key) | 2026-11-25 to 26 |

Not proven yet, so tested where first met: an upgrade family on a shop shelf (D9, phase 2) or in a big chest (a
big chest has no checking version).

Never asked for, because the game does not show it: **a small key count on the Map page** (the page shows the
map, the compass and the boss key; in game 2026-11-24 and 2026-11-25). A key count is seen in a dungeon: the
pop-up when a key is picked up there, or a locked door that opens.
