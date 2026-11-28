# NX2-ZOOTR roadmap to the public beta

Approved 2026-11-23, from the planning session: a plan of action in priority order, without dates. The decisions
it rests on are in `docs/ROADMAP_DECISIONS.md` (numbered 1-38 below as **D1**...). The sizes come from
`docs/RESEARCH_check_count.md`.

## The short version
- **Done:** phase 0, the groundwork (2026-11-15 to 2026-11-23).
- **Order:** the Forest Temple first (dungeon pieces), then the game's areas in game order, one area finished at a
  time (D23, D25). Then the generator and the app (D24). Then your own full seeds, a quiet early stage on Discord
  (D29), and the public beta on GitHub and Discord (D28).
- **Size:** 31 areas, 1,286 check spots in the maps, plus event checks (gifts, songs, boss hearts...) that the maps
  don't show. The forest, the most finished part, is 106 spots: about a twelfth.
- **Priority order:** everything essential (phases 1-6) comes first, in the order below. The "very much wanted"
  tier starts once the essentials work, then "nice to have", then the experimental item. Within a phase, what
  the rest depend on, or what is still unproven, comes first.
- **Timing:** no dates per milestone. December 24 stays the target; when the plan and the date disagree, the date
  moves (D3). We look at where we are at each milestone.

## Where things stand today (2026-11-23)
**Working and tested in game** (the base every area reuses):
- Items placed on chests, ground items, NPC gifts, song checks, Saria's bridge gift, scrubs, single shop shelves,
  pots, rocks, bushes, and Gold Skulltula tokens.
- Upgrade families (no skipped levels) on all of the above except shop shelves.
- Gossip stones: custom text and hints worded from the game's own names (one colour bug, below).
- Fixes: skippable opening, bombs without the bracelet, magic separate, bombchus without the bag, full Kokiri shop
  stock, the Kokiri circle after the dungeons.
- `run_tests.bat`: test scripts that read every change back against the game's files.

**Mapped:**
- **Kokiri Forest:** 120 logic locations in 11 regions, 155 permanent check IDs, tested in game.
- **Lost Woods (24 logic locations) and Sacred Forest Meadow (16):** region maps with logic rules exist. Missing:
  permanent check IDs (only the 4 on the bridge have one), in-game tests for the Lost Woods' regions.
  (Correction: I said earlier these two files were empty. That was wrong; I had counted the wrong field.)
- **Everything else:** not mapped. The logic has placeholders for Hyrule Field and the Temple of Time.

**Not built:** the generator, the app, every setting from D10-D18, shop families, starting as adult.

**Known bugs:** hint text stays red after the first highlight (ends with colour 1; the game uses `0xFFFF`).

## What "an area is done" means (D27)
For each area, both ages:
1. Every check spot listed from the map, plus its event checks (gifts, songs, minigames, boss heart, reward),
   each with a permanent check ID.
2. Regions and logic rules for every check, and the area's exits.
3. Each kind of check works there, with families.
4. The area's own settings and cutscenes (see the table below) built.
5. Test scripts pass, including one that builds an item onto every spot of the area and reads each one back. In
   game (changed 2026-11-24): each check kind once (in each of its forms, unless it passed in an earlier area),
   plus every unusual spot (it appears from a switch, a fight or an event, its contents can't be read from the
   files, it sits in a special room, or a cutscene gives it); samples for the rest, loose rupees and hearts
   (D35) included. Beehives are left out for now. Flat grass tufts are never checks (D30).
6. Results in CHANGELOG.md; the area is then not reopened except for bugs.

Each area's settings and cutscenes are built with the area, so nothing is left over for the end:

| Setting or piece (decision) | Built with |
|---|---|
| Dungeon items: own dungeon / anywhere / start with (D10); boss heart; reward at end of dungeon or anywhere (D11) | Forest Temple, then every dungeon |
| Kokiri Forest exit (D14) | Forest |
| Songs anywhere (D34): every song check gives any item; songs can be on any check | Each area's song checks (Sheik, Saria, Malon, the Composer Brothers...) |
| Equipment shuffles (D17): the check each one comes from | Its area: Kokiri Sword in the forest; Ocarina of Time and Master Sword in Hyrule Field and the Temple of Time; Gerudo Card in Gerudo Fortress; shields at the shops. The generator puts them in the pool (phase 5) |
| Shop families (D9); how many shelves per shop are randomized (D37) | Forest (Kokiri Shop), then every shop |
| Door of Time (D14); starting as adult (D14) | Market and Temple of Time |
| Child Zelda skipped, start with the letter, Impa's check at the start (D18) | Hyrule Castle |
| Kakariko gate (D14) | Kakariko |
| Zora's Fountain: closed / adult / both (D14) | Zora's Domain and Fountain |
| Gerudo Fortress: four / one / open (D14) | Gerudo Fortress |
| Rainbow Bridge (D12); Ganon's Boss Key (D13); Light Arrow cutscene | Ganon's Castle (last) |
| Cutscenes skippable (D15; D48: the game's own skip is enough, nothing is shortened or removed) | Each area its own scenes, from the cutscene list: every one must be skippable |

## How a phase is worked: in parts (D38)
- **One part = one test round:** one build, one short checklist, one sitting of in-game tests.
- **One part = one PR,** so a part that breaks something can be undone on its own.
- **Never two untested parts stacked:** a part starts only after the one before it passes `run_tests.bat` and its
  in-game test.
- **Only the current phase is broken into parts.** The next phase gets its parts when we reach it, from what the
  phase before it showed.
- Research and paperwork with no game changes can run alongside, while the user tests a part.

## Phases

### Phase 0: Groundwork (done, 2026-11-15 to 2026-11-23)
Everything up to the roadmap. Details are in CHANGELOG.md and "Where things stand today" above.
- **File formats:** our own readers and writers for every format the randomizer edits (Zstandard, SARC, BYML,
  event flows, MSBT text, RESTBL, AINB), checked byte for byte against the whole game.
- **Logic:** the region map and its rules; the forest mapped (Kokiri Forest, Lost Woods, Sacred Forest Meadow).
- **Every kind of check working in game:** chests, ground items, NPC gifts, song checks, Saria's bridge gift,
  scrubs, shop shelves, pots, rocks, bushes, Gold Skulltula tokens; one-time drops; the items' poses when held.
- **Upgrade families** on all of them except shop shelves, never skipping a level.
- **Gossip stones:** custom text, then hints worded from the game's own names.
- **Fixes:** skippable opening, bombs without the bracelet, magic separate, bombchus without the bag, full Kokiri
  shop stock, the Kokiri circle after the dungeons, the ocarina fixes.
- **Tests:** `run_tests.bat` with a check script for each piece.
- **Outside the repository:** the item tracker (HTML, with OBS overlays).
- **Planning:** the roadmap, its decisions, the whole-game check count, and `CLAUDE.md`.

### Phase 1: Forest Temple, and two lists
Parts, in order:
1. **Starting state on a new file** (groundwork): one system that gives starting items and sets flags when a file
   is created. Tested in the forest: a new file that already has a chosen item and flag. Later used by "start
   with" keys, Zelda's Letter and Impa's item (D18), starting as adult, full wallets and the open options.
   Unknown settled here: can it set flags as well as items?
   **Done 2026-11-23, passed in game:** `--start ITEM` and `--start-flag NAME=VALUE` add to the game's own
   new-file list (`Sequence/SetPouchAndStatusForGameStart`), which runs before Kokiri Forest loads. Tested on a
   new file with the Boomerang and Mido's blocking flag off: both held, also after save and reload.
2. **The Forest Temple's data** (D25, D26): check IDs, regions and logic rules for its 46 spots (12 chests, 5 Gold
   Skulltulas, 28 pots, 1 loose item) plus the boss heart and the Medallion. No game changes: test scripts only.
   **Done 2026-11-23 (data and test scripts; nothing to test in game):** 47 checks with IDs (the loose item is
   the boss heart), 23 regions, 5 locked doors in a fixed order (1 to 5 keys), the boss key. Its rules are tried
   in game with part 3. Found for part 3: the Bow room traps a player who has no Bow (CHANGELOG.md, 2026-11-23).
   **Confirmed in the unchanged game the same day:** the room needs the Bow to leave (the eye switch is behind
   bars), saving is off in it, and dying puts Link back at the temple's beginning without what was picked up in
   the room. Also: the first room's Gold Skulltula does not need the Hookshot (it is grabbed by climbing the
   vines). **Decided (D39):** the randomizer reopens the Bow room's door when the chest appears; built in part 3.
3. **Items on the Forest Temple's checks:** random items in its chests, pots, Gold Skulltulas and loose item, keys
   still where the game puts them. In game: a sample in the temple. **Also here (D39):** the Bow room's west
   shutter reopens when the chest appears; then the rule out of the room no longer asks for the Bow. In game:
   walk out of the Bow room without the Bow.
   **Done 2026-11-23, passed in game:** items on the temple's chests (not the boss key's), pots and Gold
   Skulltulas (11 placements tested); `--fix forest_temple_bow_room_door` (walked out of the Bow room without
   the Bow). The loose item is the boss's Heart Container: it moves to part 7.
4. **Small keys in their own dungeon:** keys moved to other checks in the temple. In game: the locked doors open
   with keys found in new places, and the key count is right. **Also here (the user, 2026-11-24):** the Hover
   Boots' height on the ground (they lay slightly in the floor in part 3's test).
   **Done 2026-11-24, passed in game:** keys in a chest, in pots and on a Gold Skulltula (no builder change
   needed), all five counted for the temple and four locked doors opened with them; the boots raised (the Iron
   Boots had the same fault) and seen lying on the floor.
5. **Keys anywhere, and which dungeon a key belongs to:** a Forest Temple key placed in Kokiri Forest; its get
   message and the pause menu name the temple (unique key models stay after the beta). In game: pick it up
   outside, use it inside. Unknown settled here: does a key found outside count for the right dungeon?
   **Built 2026-11-24; in game the same day: the keys work.** `Item_Dungeon_SmallKey@<dungeon>` on pots, rocks,
   bushes, freestanding items, Gold Skulltulas and in chests: keys found in Kokiri Forest counted for the Forest
   Temple and opened its doors. **Unknown answered: no,** the game's own key found outside does not count for
   the dungeon. **Open:** the count shown on screen is off (it shows the count from before the key; none from a
   chest or at a door), the dungeon's name in the get message, and gifts, scrubs and shelves.
6. **Start with:** keys, the map and the compass given at the start, through part 1. **Also here (the user,
   2026-11-24), from part 5:** the key count shown on screen for a dungeon's key (it shows the count from before
   the key; none from a chest), and the dungeon's name in the key's get message.
   **Built 2026-11-24, to test in game:** `--start-flag DungeonInfo.<dungeon>.SmallKeyNum=N`, `IsGetMap`,
   `IsGetCompass`; a key in its own dungeon is the game's own key (its count shows as the game's does); the
   name on a key as an experiment (`...@ForestTemple+name`). Outside its dungeon a key's pick-up still shows the
   count of the place Link is in.
   **First test in game, 2026-11-24:** starting with a key works (the temple showed 5 with 1 from the start);
   a key in its own temple shows the right count; no count appears at a door (the game's own behaviour). The
   name did not show (only one of an item's two names was changed), and the map and the compass could not be
   checked: the Map page was closed ("???" as a child, "Unavailable right now." in the temple).
   **Second test in game, 2026-11-24:** the map and the compass given at the start work (seen on the temple's
   map as a child); a place marked as visited (`--start-flag IsVisitLocation.<place>=true`) has its map, "???"
   is "not visited yet"; the Map page is closed for an adult made with the debug menu, which is not the
   build. The name shows on a key in a chest, not yet on a key from a pot.
   **Third test in game, 2026-11-24:** the name shows on a key from a pot too (the name is the dungeon's
   named chest key), and the get window shows a colour: the game's number 3 is green, 0 is red. The user's
   colours: Forest green, Fire red, Water blue, Shadow purple, Spirit orange.
   **Fourth test in game, 2026-11-24:** the game's list of text colours (a file in the pack the game loads
   first) cannot be made longer: colours added behind its eight all came out orange.
   **Fifth test in game, 2026-11-24:** blue and purple work as two recoloured places of the game's list that
   no text uses (2 and 7). The game's own place 6 was too dark an orange, so it is recoloured too, to a more
   yellowish orange (225, 130, 0): **that shade is not seen in game yet.** The colours are D40.
   **Rules from the user, 2026-11-24:** every key outside its dungeon says the dungeon's name (D41); with the
   opening skippable, Kokiri Forest's map is open from the start (D42).
   **The last two colours (the user, 2026-11-24; not seen in game):** Bottom of the Well gray (the game's own
   place 1), Gerudo Training Ground a darker orange (the staff roll's place 4 recoloured: 17 headings of the
   credits take that colour). Only eight places use small keys; Ganon's Castle has no colour.
   **The look at them in game, 2026-11-24:** both oranges good, the map at the start good; but the Well's
   name was purple and the Fire Temple's orange: the get window shows place 6 of the game's colour list for
   "red" (number 0) and place 7 for "gray" (number 1), so those two places are not free. **Corrected:** 6 and
   7 are the game's again; purple is one colour added behind the list, the two oranges take the staff roll's
   places 4 and 5 (those lines of the credits change colour).
   **Passed in game 2026-11-24:** all seven colours, and the game's own red is red.
   **Open:** gifts, scrubs and shelves; the dungeon's name on a key in its own dungeon (the game's own key has
   one text for all dungeons).
7. **Boss key, boss door, boss heart and the Medallion,** with the reward "at the end of the dungeon" or
   "anywhere" (D11).
   **Built 2026-11-24, to test in game:** the boss key anywhere (`Item_Dungeon_BossKey@<dungeon>`; the map and
   the compass the same way), another item in the boss key's chest, on the boss's heart and where the
   Medallion is given, the Medallion on another check.
   **Passed in game 2026-11-24:** the map and the compass from Mido's chests and the boss key from a pot in
   Kokiri Forest (each with "(Forest Temple)" in green), the boss door opened with that key, the Megaton
   Hammer in the boss key's chest (no message from Navi), the Boomerang in the Heart Container's place (the
   boss's last cutscene plays to its end), the Silver Scale from Saria, the Forest Medallion from a pot.
   **Open:** a family where the Medallion is given; in Saria's
   cutscene the Medallion still floats down whatever is given.
   **The Key Items tab (the user, 2026-11-24: "key items tab first"):** it was "???" after the Medallion from
   the pot. In game the same day: a Spiritual Stone found in a chest opens it (no cutscene needed) and the
   Medallion is then on it; a Medallion alone does not open it, whatever its age mark (third round). The
   game opens the tab when Link owns the first item of any row of the pause menu table's `StoneArray` (read
   from its program). **Passed in game 2026-11-24:** `--fix key_items_tab_open` (two rows more in that list,
   for the green tunics every file starts with): the tab is open and empty on a new file, and a Medallion or
   a stone found afterwards is on it.
   **Decision 43:** the tab is open from the start in every build.
   **Passed in game 2026-11-24:** a placed stone or Medallion turns when Link holds it up and when it lies
   on the ground (it gets the Boomerang's animation settings, as the songs' harp did). **Not known:** how the
   changed actor looks in the 11 cutscenes that show a stone or a Medallion (each with its area).
   **Passed in game 2026-11-24 (decision 44):** a placed stone or Medallion says its name in its temple's
   colour in the get window (the keys' colours); the Light Medallion's is gray.
   **Found in the same test:** with all nine owned, the Spirit and the Shadow Medallion were missing on the
   Key Items page (the two tunic rows of `key_items_tab_open` took two of the page's nine places).
   **Corrected and passed in game 2026-11-24:** the nine real rows come first in the table, the tunic rows
   behind them: all nine are shown, the cursor and "Details" work, at both ages.

8. **The Forest Temple's every-spot build script, and its unusual spots** (D27 as changed 2026-11-24): a
   test script builds an item onto every one of the temple's 47 checks and reads each back; in game only the
   unusual spots not tried yet.
   **Built 2026-11-24, passed in game 2026-11-25:** `tests/forest_temple_every_spot_check.py` (all 47 build
   and read back; no builder change needed). The falling ceiling room's chest names no contents in the map
   because it is a refill chest (it gives the supply Link is shortest of). In game: that chest (the Megaton
   Hammer), Joelle's and Beth's chests (they appear after their Poe; the Hover Boots, the Lens of Truth) and
   the Floormaster's chest (it appears after the fight; the Iron Boots) all gave their item, and stayed open
   after a save and reload. 21 of the temple's 47 checks are now changed in game, the other 26 are covered by
   the build script.

**Added 2026-11-25 (the user: "id like to finish these in Phase 1 if possible"; D45):** the open items of parts
3 to 7, in three more parts.

9. **The Forest Temple's loose ends** (one round in the temple): an upgrade family where the Medallion is given
   (the builder refuses it today); Saria's cutscene shows what is given instead of always the Forest Medallion
   (and how a changed Medallion looks in that cutscene); an upgrade family in a big chest (the game checks what
   Link owns only through the small chest; the Bow room's chest is a big one); the dungeon's name on a key in
   its own dungeon (the game's own key has one text for every dungeon; a named key may lose the count shown,
   so the round settles which is kept).
   **Built 2026-11-25, to test in game:** a family on the Medallion's check (the game's question in front of
   the cutscene's get); the cutscene shows what it gives (its Medallion actor renamed, one actor per level of a
   family, nothing for a heart); a family in a big chest makes it the game's checking chest, a small chest at
   the same spot (the game has no big one); `Item_Dungeon_SmallKey@ForestTemple+name` in the temple is the
   named key. `tests/forest_temple_loose_ends_check.py`.
   **In game 2026-11-25:** all passed: the Longshot floated down in Saria's cutscene and was given, the Bow's
   big chest gave the Gold Scale as a small chest, the map's the bigger Bomb Bag, the named key said "(Forest
   Temple)" and opened a door (no count on screen; the user kept the name: D46). **Fixed after:** the map's
   chest made small still played the big chest's opening (its kept event goes now; retest in game: good, the small chest's opening).
   **Found, for part 10:** the Fairy Bow alone in a pot came without its quiver (a first weapon alone on the
   ground, a pot, a rock, a bush or a Gold Skulltula gets no bag).
10. **Kokiri Forest and its neighbours** (one round on a new file, child): a small key, the boss key, the map
   or the compass on a person's gift, a scrub and a shop shelf; a stone or a Medallion given by a person; the
   starting state's leftovers (hearts and rupees, items the game files under another name: Fairy Slingshot,
   Fairy Bow, the gauntlets; a chest open from the start). If Longshot's debug menu can start the staff roll,
   one line for the credits' colours (decision 40). Proposed from part 9: the Fairy Bow or Fairy Slingshot
   placed alone on the ground, in a pot, a rock or a bush, or on a Gold Skulltula, given with its bag.
   **Built 2026-11-25, to test in game** (`tests/kokiri_neighbours_check.py`):
   - the starting state: `--start Item_Range_SlingShot`, `Item_Range_Bow` (each with the small bag and the 30
     seeds or arrows a chest gives with it) and `Item_Gauntlet_Goron` are pushed as they are placed (the game's
     own new-file list pushes such a stand-in itself, `Obj_Armor_Adult_Normal`); `--start-hearts N` changes the
     list's own `Life` and `MaxLife`; `--start-rupees N` adds one set of `PlayerStatus.CurrentRupee`;
   - a first weapon placed alone on a freestanding item, a rock, a bush, a pot or a Gold Skulltula is its
     turning item of one level, which gives the bag and the 30 as a chest does;
   - a dungeon's small key, boss key, map or compass from a person (a gift with flow data) and from a Deku
     Scrub: the version a chest holds, and the chests' count step right after the get;
   - a stone or a Medallion from a person, a cutscene gift, a scrub and a shelf already built: in the round.
   **Not possible (found in the game's files):** a chest open from the start. A placement's saved flag
   (`Bool64bitKey` in `GameData/GameDataList`) has no default value to change, and no node of the new-file
   sequence sets a flag by its 64-bit number.
   **Left out of this round, proposed as its own small part:** a dungeon's key, boss key, map or compass on a
   **shop shelf**. A shelf is not an event: its own AI would have to count the key, and the AI's "sold out"
   side runs again in every state of the shelf, so the count needs a guard that holds exactly once; and a shop
   version would have to be built from an item of ours instead of a game item.
   **In game 2026-11-25:** passed: 5 hearts, 50 rupees, the Fairy Slingshot with 30 seeds, the Goron Bracelet
   from the start; the Fairy Bow alone in a pot came with 30 arrows; the pots did not come back; the Goron
   Ruby from the shelf; the Kokiri's small key "(Forest Temple)" in green; the scrub's boss key, shown on the
   temple's map; Saria's Fire Medallion; save and reload. **Not seen:** that the Kokiri's key counts (the Map
   page shows no key count, as found on 2026-11-24: the checklist should not have asked for it there): to see
   at a door of the temple. **Fixed after:** the scrub's line ran out of its box with a long name; it is on
   two lines now (to see once more). The staff roll's line was left blank.
   **Retest in game 2026-11-25:** the scrub's line fits its box; with only the Kokiri's key a locked door of the
   Forest Temple opened, so a key from a person counts. The user: "Temple should have a capital T" (the line
   said "boss key (Forest temple)"): the dungeon's name in an item's name now has the game's own "keeps its
   capital" tag (to see once more). The staff roll: "no easy way to check", so the credits' colours stay
   with "left with their areas" below.
   **Third look in game 2026-11-25:** "Forest Temple" has its capital T. The user: "Boss Key" should be
   capitalised too, and the whole item name green in the scrub's box. Done: every capitalised word of such a
   name has the tag, and the scrub's line colours the name of a dungeon's key, boss key, map or compass in
   its dungeon's colour (D40's colours; any other item's name stays in the game's colour for names in talk).
   To see once more.
   **Fourth look in game 2026-11-25: passed.** The scrub's line says "Boss Key (Forest Temple)", the whole
   name green, on two lines inside the box; the get window after buying is right. The user: "Boss Key" should
   be capitalised in the get window's text too: it says "You found the Boss Key! (Forest Temple)" now (the
   game's own text for its boss key is "You found the boss key!"; not seen in game after the change).
   **Merged 2026-11-25 (PR 44).**
11. **The Forest Temple's own cutscenes** (D15; rule 4 of "an area is done"): skippable or shortened, from the
   cutscene list; in game, what the game's own skip keeps and how long a flowchart cutscene really runs.
   **Done 2026-11-26, with nothing built (D48).** Read from the game's files: every one of the temple's 47
   scenes in the cutscene list (18 story cutscenes, 9 lead-in events, 19 small scenes, 1 system scene) can be
   skipped with the game's own skip; none has the "no skip" setting. The user: "If the cutscenes are already
   skippable then we are good to go". `tests/forest_temple_check.py` now fails if one of them ever gets that
   setting. **Not done, by that decision:** shortening or removing a scene, and the in-game round (what the
   skip keeps of each scene was not played through; how long a flowchart cutscene runs was not measured).
12. **A dungeon's small key, boss key, map or compass on a shop shelf** (left out of part 10; done before
   part 11: the user, 2026-11-25, "Shop shelf first"; D47).
   **Built 2026-11-25, to test in game** (`tests/shop_shelf_keys_check.py`). A sale turned out to be an event
   after all: the shops' shared flow `DisplayShop` keeps the picked item's name in the saved string
   `Shop_SelectItemName` (it asks about the tunics and the masks by it) and counts a sale with
   `EventTriggerAddShopItemSoldNum`, in five places. So the shelf is a shop version, sold once, of the version
   a chest holds, and behind each of those five steps stands "is it <that version>?" -> the chests' count step
   (the one the gift and the scrub use, passed in game). The shelf's AI is not touched, so no guard is needed.
   In front of the flow's "can Link carry it" question the same name question leads ours to "yes" (what that
   question answers for an item that is not put in the inventory is not known).
   **In game 2026-11-25:** the four shelves sold the Forest Temple's small key, boss key, map and compass,
   each once, with the right texts; the temple's map shows the map, the compass and the boss key; the shelves
   stay empty after coming back and after save and reload. **Not seen:** that the shop's key counts (the door
   in the temple was left blank). **Fixed after:** the boss key and the compass sat in the shelf. Their poses
   are centred on the shelf point, and so is the map's: lifted 0.22, 0.13 and 0.20 m (`SHELF_LIFT`, measured
   on the models as the Hookshot's was). To see once more.
   **Retest in game 2026-11-26: passed.** The boss key, the compass and the map stand on their shelves, the
   small key as before; with only the key from the shop the first locked door of the Forest Temple opened.

Left with their areas: the other 10 cutscenes that show a stone or a Medallion (each plays after its own
dungeon's boss), and the credits if the debug menu cannot start them.

Alongside (no game changes): the **cutscene list** (every story cutscene, how long, what it sets and gives;
needed by D15 in every area) and the **area checklist template**, so each area's test list has the same shape.
**The cutscene list is done (2026-11-25): `docs/CUTSCENES.md`** (the same as data: `data/cutscenes.json`), made
by `tools/cutscene_list.py` from the game's files for the whole game, one section per area: 319 story
cutscenes, the 217 events that run them, 363 small scenes. The reader now takes the cutscenes' timeline files
(`formats/evfl.py`: all 914 event flow files, byte for byte). Not in it, because the files don't say: how long
a flowchart cutscene runs (only its wait steps), and what the game's own skip keeps of a cutscene (to try in
game with the first area's D15 work).
**The area checklist template is done (2026-11-25): `docs/AREA_CHECKLIST_TEMPLATE.md`.** What goes on an
area's list and in what order (new check kinds and forms, every unusual spot, the area's settings and
cutscenes, samples, save and reload), how it is written (by age, along the way through the area, the remake's
names, the debug-menu warp), the two blocks to copy into `out\TEST_CHECKLIST.md` and `out\TEST_ANSWERS.md`,
what is recorded after the answers, and a table of the check kinds already passed in game, so a later area
tests only what is new.

(The debug-menu warp was checked on 2026-11-23: it leaves the temple untouched.)

- **Milestone M1:** the Forest Temple is done, and the dungeon-item settings work in one dungeon.
  **Reached 2026-11-26:** parts 1 to 12 are done.

### Phase 2: Finish the forest, and the Deku Tree
- **Shop families** (D9, the one unproven method), first: one shelf, one pair, in game. If it fails, it comes back
  to you as a decision.
- Lost Woods and Sacred Forest Meadow: check IDs, in-game tests.
- Kokiri Forest exit setting.
- Inside the Deku Tree (39 spots, 18 of them bushes) with Gohma's heart and the reward.
- **Milestone M2:** the forest region and the Deku Tree are done.

Parts, in order (added 2026-11-26, the user: "Yes"; D49; nine since part 2 was added the same day, D50). Where the forest stood that day: Kokiri Forest 120
checks, all with IDs, no every-spot build script; Lost Woods 22 map spots (9 bushes, 5 scrubs, 3 Gold
Skulltulas, 3 boulders, 1 chest, 1 gossip stone) and 5 event checks, none with an ID; Sacred Grove
(`SacredForestMeadow`) 14 map spots (7 bushes, 4 gossip stones, 2 chests, 1 Gold Skulltula) and 2 event
checks, none with an ID; Inside the Deku Tree no data yet.
1. **Shop families, a trial:** one Kokiri Shop shelf, one pair (Silver Scale > Gold Scale), in game. Part 12
   of phase 1 found that a sale runs through the shops' shared flow (`DisplayShop`), so the level can be
   chosen there. If it fails, it comes back to the user as a decision.
   **Built 2026-11-26, to test in game** (`tests/shop_family_check.py`): `SHELF=First>Second` (pairs only).
   The shelf is First's shop version, sold once. The sale flow keeps the picked item's name in
   `Shop_SelectItemName` and uses it for its "can Link carry it" question, the buy line, the get window and
   the sound; so when Link has First, Second's name is written there before that question (two frames' wait,
   as the scrubs' pairs do), and in front of each of the five steps that put the shelf's item in the inventory
   Second is added in its place. **Known before the test:** the shelf itself is one actor, so it shows First's
   model on the shelf and held up, whichever level it sells. The test build has the pair on two shelves, so
   one file sees both levels.
   **In game 2026-11-26: the method works.** The first shelf bought gave the Silver Scale, the second the
   Golden Scale ("You got a golden scale!", in the menu); both shelves empty after, also after save and
   reload. Three things seen: the scale sat in its shelf (**fixed:** lifted 0.19 m, measured on the model);
   the shopkeeper's line still named the Silver Scale for the second shelf (**fixed:** the line comes before
   the point the name was written at, so it is written right after the shelf is picked now; to see once
   more); Link holds up the Silver Scale's model when he gets the Golden one (the shelf is one object: the
   user's decision whether that is good enough).
   **Retest in game 2026-11-26: passed.** The scales stand on their shelves; the shopkeeper's line names the
   Golden Scale for the second shelf; "You got a golden scale!" and the Golden Scale in the menu; both shelves
   still empty after leaving and coming back. The shelf's own label still says "Silver Scale", and Link still
   holds up the Silver Scale's model. **The user's decision (D50): not good enough;** two shelf objects on
   one spot, switched by whether Link has the first level: part 2.
2. **Shop families with the right look** (added 2026-11-26, D50): two shelf objects on one spot, one per
   level, each shown only while it is that level's turn (Link has the level before it and not this one), so
   the shelf's label, its model and what Link holds up are the level's own. The Kokiri Shop itself swaps a
   set of shelves by a flag (its "low on stock" set), so the game has the mechanism. To find out first: whether
   such a condition is looked at while Link is in the shop or only when the area is loaded. Part 1's name
   swap in the sale flow stays for the case it is only on load (a second shelf of the pair bought in the same
   visit).
   **Built 2026-11-26, to test in game** (`tests/shop_family_check.py`). Read from the game's maps: a
   placement can have a `Presence` setting (`FlagName`, `IsCheckLazy`, `IsNegation`): it is only there while
   the saved flag holds. 2,793 placements have one; the game uses `IsGet.<item>` flags for it, and the Kokiri
   Shop has two placements of one shelf number on one spot. So the shelf (First's shop version) gets "not
   `IsGet.<First>`", and a twin of it (Second's shop version, under the hash the shelf had in the game) gets
   "`IsGet.<First>`", both `IsCheckLazy` false, as the Happy Mask Shop's masks, which appear while Link is in
   the shop. The shopkeeper links to both. **So that the two objects sell one item:** both have the same
   shelf number, the shopkeeper counts a sale under that number, and the count (a saved number of its own,
   `Shop_SoldNum.<shopkeeper>.<number>`) is no longer reset when the shops restock. **Not known from the
   files:** whether the second object appears at once or only when the area is loaded again; whether the
   shopkeeper names and prices the twin right (his list names the first object for that shelf).
   **In game 2026-11-26: failed.** With the pair on two shelves the shop's cursor would not go onto either of
   them, and since they are the two shelves next to the Recovery Heart it could not leave the top left; the
   shop could be left. Why is not in the game's files. **A diagnostic build** (not a candidate; built with
   a temporary change that is not in the repository) has one arrangement per shelf: an ordinary item with the
   sold count kept; a shelf with the `Presence` setting and no twin; the twin as built; the twin linked from
   the shopkeeper before the shelf; the twin not linked from the shopkeeper. A Silver Scale in Mido's first
   chest switches them over.
   **The diagnostic in game, 2026-11-26: the shop takes one object per shelf number, the one its last link
   for that number points at, whether that object is there or not.** Without the Silver Scale: the ordinary
   item worked (the kept sold count is fine), the shelf with only the `Presence` setting worked, the twin
   linked last could not be chosen (the last link pointed at the absent twin), the twin linked first and the
   twin not linked worked (the shelf was the last link). With the Silver Scale it turned round: only the twin
   linked last could be chosen, and it was right: "Golden Scale", 30 rupees, bought. So `Presence` works on a
   shelf, a second object is labelled and priced right, and the switch needs no reload, but **one
   shopkeeper cannot serve two objects of one shelf number**. What is left: two shopkeepers on one spot, one
   per state, each linked to its own object (the game's own way in this shop: its two sets); to try next.
   **Closed 2026-11-26 by the user's decision (D51): "keep part 1's look, but make a rule that 2 upgrades of
   the same family cannot be placed in the same shop".** The two-object code is taken out again (nothing of
   it is in the builder), the two-shopkeeper way was not tried, and the builder now stops a build with levels
   of one family on two shelves of one shop (`shop_family_guard`; `tests/shop_family_check.py`). No in-game
   round: the rule only refuses builds, and part 1's way passed in game.
3. **Shop families, the rest:** a three-level family on a shelf, and the setting for how many shelves per shop
   are randomized (D37). (One family on two shelves of a shop is ruled out by D51.)
   **Done 2026-11-28, passed in game** (third build; `tests/shop_family_check.py`). The Kokiri Shop's shelf
   order confirmed by the user (D52). What was built, and the two rounds before it:
   - **three levels on a shelf** (`SHELF=First>Second>Third`): the sale flow asks "has Second?" and then "has
     First?" right after the shelf is picked and writes the next level's name; in front of each giving step
     the second or the third level is added in the shelf item's place;
   - **a first weapon on a shelf comes with its small bag** (found here: a Fairy Slingshot or Fairy Bow on a
     shelf, alone or as its family's first level, came with no bag, since a shelf gives nothing but its own
     item): the bag is added in the sale flow in front of each giving step;
   - **the shelf-count setting (D37)** needs nothing in the game's files (a build already changes only the
     shelves it is given). What it needs is the order in which a shop's shelves are randomized as the number
     goes up: each shop shelf has a `shelf_rank` in `data/world`, and `World.shop_shelves(n)` names the shelves
     for a setting of n. **The Kokiri Shop's order (proposed, then confirmed):** Deku Seeds x30, Deku
     Nuts x10, Deku Sticks x5, the Recovery Heart, Deku Seeds x10, Deku Nuts x5, the Deku Stick, the Deku
     Shield (last): **confirmed by the user 2026-11-28 (D52).** The generator that will use it is phase 5.
   - **in game 2026-11-27:** the Fairy Bow on a shelf: good (stands right, 30 arrows). With a Bomb Bag from
     a chest the bomb bag shelf said "Sold out" (a shop does not sell an item Link has). **Fixed, to retest:**
     a family's shelf is a shelf of its own that Link can never have (`Shop_NX2_<First>_<price>_Family`: named
     itself, the first level's look and name, never in the inventory), and the sale flow writes the name of
     the level Link gets next and adds that level, the first one included;
   - **in game 2026-11-27, second build:** that shelf was "Sold out" on a new file, so "Link has it" was not
     the cause. The bomb bags' item settings are the only ones with `IsPlayGetEventPouchMax: False`, and the
     shelf inherited it; a family's shelf says True now, and "can Link carry it" is not asked about a
     family's level. **Passed in game 2026-11-28** (with a Silver Scale > Golden Scale shelf beside it): all
     three levels sold from the shelf (20, 30 and the biggest bag's bombs), the scale shelf too, the shelves
     empty after leaving and after save and reload. The shelf keeps the first level's model (D51: "fine for
     now", the user);
   - shelf lifts for the Bomb Bag (0.19 m), the Fairy Bow (0.42 m) and the Fairy Slingshot (0.18 m), measured
     as the scales'. The Fairy Bow is 0.91 m tall on a shelf (the shop's rows are 0.64 m apart): its look is
     part of the test.
4. **Kokiri Forest closed out:** its every-spot build script, the Kokiri Forest exit setting (D14: closed until
   the Deku Tree / open), and the check that its cutscenes can be skipped (D48).
5. **Lost Woods, the map spots:** check IDs, regions and rules for the 22 spots, the every-spot script, an
   in-game round. A boulder is a kind the builder does not place an item in yet.
6. **Lost Woods, the five event checks** (the Skull Kid, the ocarina memory game, the target practice, the Deku
   Theater twice): each one's hand-over found in the game's flows, then in game. The target practice gives a
   seed bag upgrade (the family rule). May be played in one round with part 5.
7. **Sacred Grove:** check IDs, regions and rules for the 14 spots, Saria's song and Sheik's song, the
   every-spot script, an in-game round.
8. **Inside the Deku Tree, the spots:** check IDs, regions and rules for the 39 spots, the every-spot script,
   an in-game round (the debug menu's warp).
9. **Inside the Deku Tree, the end:** Gohma's heart, the Kokiri Emerald as the reward, the map and compass
   settings in a second dungeon, and the check that its cutscenes can be skipped (D48).

### Phase 3: The child-era world, in game order
Each overworld area is done for both ages when first reached.
- Hyrule Field with Lake Hylia and Lon Lon Ranch (109 spots, 11 Gold Skulltulas; the biggest overworld area).
- Market and Temple of Time (72 spots, 54 pots, 11 shop shelves); Door of Time; starting-as-adult research.
- Hyrule Castle (child Zelda skipped).
- Kakariko Village and Graveyard (68 spots, 21 beehives, 9 shop shelves); Kakariko gate.
- Death Mountain Trail, Goron City (8 shop shelves), Death Mountain Crater.
- Dodongo's Cavern.
- Zora River, Zora's Domain, Zora's Fountain; the fountain setting.
- Jabu-Jabu's Belly.
- **Milestone M3:** every child-era area and the three child dungeons done.

### Phase 4: The adult dungeons and the west
- Fire Temple; Ice Cavern; Water Temple; Bottom of the Well; Shadow Temple.
- Gerudo Valley, Gerudo Fortress (its setting), Gerudo Training Ground, Haunted Wasteland, Desert Colossus,
  Spirit Temple.
- Ganon's Castle, outside and inside: Rainbow Bridge, Ganon's Boss Key, the Light Arrow cutscene (research first:
  unproven in the remake).
- **Milestone M4:** every area done. The whole game is mapped, with logic, and tested.

### Phase 5: Generator and app
The largest single piece of new code; a Fable job.
- **Switching seeds and saves** (research, first): how Longshot keeps saves when the mod changes, so a save from
  one seed is never loaded with another seed's mod. The app's saved seeds (D8) are built on the answer.
- **The item pool:** every item in a seed and how many (heart pieces and containers, bottles with Ruto's Letter,
  ammo, rupees, filler), and what fills the slots of items removed or given at the start.
- **Generator:** fill with logic for every D-setting; seeds always beatable (D2); the required-items list (for the
  spoiler log and "Way of the Hero").
- **Hints** (D16): exact or vague, Way of the Hero, Mask of Truth needed or not; the colour bug fixed here.
- **Spoiler log; seed and settings string; saved seeds** (D8).
- **The Windows app** (D7): Python with HTML pages (pywebview suggested), one .exe, reading the player's own game
  files (we ship none). Your tracker inside it with its OBS overlays; `config.js` ships blank.
- **Game version check:** the app refuses game files of a version we didn't build for.
- **Seed check in game:** a short code shown in game (for example on the file select screen), so a player sees
  the right mod is loaded and two players can confirm they're on the same seed.
- **Back to the normal game:** the app removes the mod cleanly.
- **Many seeds tested automatically:** hundreds of seeds generated and checked (beatable, no duplicate items, every
  setting combination) on every change to the generator or logic.
- **Milestone M5:** the app makes a beatable full-game seed from settings.

### Phase 6: Your full seeds
- You play complete seeds with different settings. Every bug found is fixed and the seed replayed.
- GitHub issue form (seed string, settings, spoiler log), Discord channels, install guide, known issues, settings
  list.
- The app and the install guide say the beta is English only (D36).
- **Default settings,** and maybe a few presets: what a new player gets with no changes.
- **Milestone M6:** you've finished a few seeds without blocking bugs.

### Phase 7: Quiet early stage
- Anyone interested, through the Discord; no big posts (D29). Releases on GitHub as 0.x versions.
- Bugs come in through both (D28) and are fixed in small releases.
- Work starts on the "very much wanted" tier (below), never holding a fix back.
- **Milestone M7:** no known blocking bugs for a week.

### Phase 8: Public beta
- The larger posts. The "very much wanted" items that are ready go in; the rest follow in updates.

## After the essentials, in priority order
None of these holds the release (D21).

**1. Very much wanted in the beta** (from phase 7, or earlier when an area makes one cheap):
- With the generator: chest size matches contents; ice traps and their frequency; shop prices; Gold Skulltula
  tokens for the bridge or Ganon's key (D22); Navi hints; Temple of Time altar hints; full wallets; starting
  location.
- Items: Blue Fire Arrows, Sunlight Arrows, masks as adult, Bunny Hood.
- Skip the Epona race (Lon Lon Ranch, phase 3, if cheap there).
- Cosmetics, outside the seed: cosmetic randomizer, music randomizer, custom music (unknown: how the remake stores
  music), coloured or textured pots, rocks and bushes.

**2. Nice to have** (only with time left): Song of Soaring; the X/X counter on the map; one hit / double damage,
Gloom; boss door hints.

**3. Experimental:** a proof of concept of waypoints on the in-game map (needs the map screen researched first).

**4. After the beta:** entrance, boss and enemy randomizers; Jabber Nuts; "all checks reachable"; UI customization;
custom models; beehives (D35); other languages, after research (D36); the map tracker; daily or weekly seeds; Glitched and No Logic; keyrings, skeleton key, unique key
models; barren and "always" hints; trade quest items.

## Testing
- **Daily test lists**, short, in `out\TEST_CHECKLIST.md` with `out\TEST_ANSWERS.md` (D5); a long day takes
  several. Each area's list has the shape of `docs/AREA_CHECKLIST_TEMPLATE.md`. A test build that sells
  anything has the gold rupee on the Kokiri Shop floor.
- **Platform:** Longshot only (D6).
- **Saves:** Longshot's debug menu to reach areas (D26); first check that the warp leaves an area untouched.
- **Test scripts** on every build; every area adds its own.
- **Full seeds** only from phase 5 on (D24), then the quiet stage's players.

## Known issues carried forward
| Issue | Fixed in |
|---|---|
| Hint text stays red after the first highlight (ends with colour 1; the game uses `0xFFFF`) | Phase 5, with the hints |
| Saria's bridge scene: Link holds the first level's model, whatever level he gets | Not planned (the window and item are right) |
| Young Link's Bow held up looks oversized (0.86 m; child items are 0.31-0.59 m) | Left as it is (your choice, 2026-11-23) |

## Unknowns (each settled in the phase named; each failure comes back to you as a decision)
| Unknown | Phase |
|---|---|
| Starting state: setting flags as well as items on a new file | **Answered 2026-11-23: both**, read from the game's files and confirmed in game (part 1's test). The game's own new-file list (`Sequence/SetPouchAndStatusForGameStart`) takes one more item push per item and one more setter per flag (Bool, Int, String64). Built 2026-11-25 (part 10, to test in game): hearts and rupees (`--start-hearts`, `--start-rupees`), items kept under another inventory name (Fairy Slingshot and Fairy Bow with their bag, the Goron Bracelet). Not possible: per-placement flags (an opened chest): those flags have no default value and no sequence node sets one |
| Keys placed outside their dungeon; "start with" keys | 1 |
| Debug-menu warp leaves areas untouched | **Settled 2026-11-23:** a new file warped into the Forest Temple keeps its doors locked and 0 small keys |
| Shortening each cutscene and keeping what it sets | **List done 2026-11-25** (`docs/CUTSCENES.md`: what each one sets, gives and who asks whether it was played; timelines can be read and written). The change itself: every area. Still open: what the game's own skip keeps, and a flowchart cutscene's real length |
| Shop families: shelves that appear only while a flag holds | 2 |
| Scrubs (15) and shop shelves (44) look low next to the N64 game | 2-3, as those areas are mapped |
| Starting as adult | 3 |
| Master Sword shuffled: the pedestal giving another item; becoming adult without it | 3 |
| Moving Malon and Talon home; Impa's check at the start | 3 |
| Zora's Fountain open for child | 3 |
| Rainbow Bridge, Ganon's Boss Key condition, Light Arrow cutscene | 4 |
| Mask of Truth question in front of a stone | 5 |
| How Longshot keeps saves per mod (switching seeds) | 5 |
| Which game version the files are (`Product.110`: 1.1.0?) | 5 |
| Music storage (custom music) | 7 |
| The in-game map screen (counter, waypoints) | After phase 7 |
