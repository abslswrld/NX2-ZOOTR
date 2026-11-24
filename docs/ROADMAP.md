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
5. Test scripts pass. In game: every chest, gift, song, scrub, shop shelf and Gold Skulltula; for pots, rocks,
   bushes, crates and loose rupees and hearts (D35), each new kind plus samples. Beehives are left out for now. Flat grass tufts are never checks (D30).
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
| Cutscenes skippable / shortened (D15) | Each area its own scenes, from the cutscene list (phase 1) |

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
   with keys found in new places, and the key count is right.
5. **Keys anywhere, and which dungeon a key belongs to:** a Forest Temple key placed in Kokiri Forest; its get
   message and the pause menu name the temple (unique key models stay after the beta). In game: pick it up
   outside, use it inside. Unknown settled here: does a key found outside count for the right dungeon?
6. **Start with:** keys, the map and the compass given at the start, through part 1.
7. **Boss key, boss door, boss heart and the Medallion,** with the reward "at the end of the dungeon" or
   "anywhere" (D11).

Alongside (no game changes): the **cutscene list** (every story cutscene, how long, what it sets and gives;
needed by D15 in every area) and the **area checklist template**, so each area's test list has the same shape.

(The debug-menu warp was checked on 2026-11-23: it leaves the temple untouched.)

- **Milestone M1:** the Forest Temple is done, and the dungeon-item settings work in one dungeon.

### Phase 2: Finish the forest, and the Deku Tree
- **Shop families** (D9, the one unproven method), first: one shelf, one pair, in game. If it fails, it comes back
  to you as a decision.
- Lost Woods and Sacred Forest Meadow: check IDs, in-game tests.
- Kokiri Forest exit setting.
- Inside the Deku Tree (39 spots, 18 of them bushes) with Gohma's heart and the reward.
- **Milestone M2:** the forest region and the Deku Tree are done.

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
  several. Each test build has the gold rupee on the Kokiri Shop floor.
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
| Starting state: setting flags as well as items on a new file | **Answered 2026-11-23: both**, read from the game's files and confirmed in game (part 1's test). The game's own new-file list (`Sequence/SetPouchAndStatusForGameStart`) takes one more item push per item and one more setter per flag (Bool, Int, String64). Not covered yet: struct fields (hearts, rupees), items kept under another inventory name (Fairy Slingshot, Fairy Bow, gauntlets), per-placement flags (an opened chest) |
| Keys placed outside their dungeon; "start with" keys | 1 |
| Debug-menu warp leaves areas untouched | **Settled 2026-11-23:** a new file warped into the Forest Temple keeps its doors locked and 0 small keys |
| Shortening each cutscene and keeping what it sets | 1 (list), then every area |
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
