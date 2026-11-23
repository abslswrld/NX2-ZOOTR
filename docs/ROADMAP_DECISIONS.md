# NX2-ZOOTR roadmap: decisions so far

Planning session started 2026-11-23. This is the running record of what's settled, so settled topics stay settled.
The roadmap built on it is `docs/ROADMAP.md` (approved 2026-11-23).

## The goal
1. **First public build = a public beta.** Anyone can download it and generate their own seeds.
2. **The whole game, beatable start to finish:** every area, every dungeon, both ages, Ganon as the goal. Logic
   without glitches (Glitched and No Logic come later).
3. **Target: 2026-12-24, but the date moves** rather than cutting the full game.
4. **A limited first build:** most of the backlog is for the final build.
5. **Testing time:** 1 to 8 hours a day, varies. Plan short daily test lists.
6. **Platform:** Longshot. Real hardware is not a concern for now.

## The app
7. **A Windows app** that, in the final build, does generation, tracking, logs and more. Suggested make-up (not
   settled): Python with HTML pages in its own window (e.g. pywebview), packed into one .exe.
8. **In the beta app:** seed generation, seed and settings sharing, saved seeds (easy switching), spoiler log,
   item tracker with its OBS overlays (exists: `C:\Design\001_FINISHED_PRODUCTS\003_STREAM_ASSETS\OOT2026\Tracker`;
   its `config.js` holds a personal OBS password and must ship blank).

## Seed settings in the beta (each its own setting)
9. **Shuffles:** classic checks; Gold Skulltulas; scrubs; shops; pots, rocks, bushes, grass and crates.
   Shop families are unproven: research early.
10. **Dungeon items** (per kind: small keys, boss keys, maps, compasses; assumed separate per kind): own dungeon /
    anywhere / start with. No vanilla choice.
11. **Dungeon rewards:** at the end of dungeons / fully randomized.
12. **Rainbow Bridge:** vanilla / all six Medallions / all Stones and Medallions / a number of Stones and Medallions.
13. **Ganon's Boss Key:** in the castle / anywhere / reward for a condition (assumed: the bridge's choices) / at
    Zelda's Light Arrow cutscene.
14. **Area access and start:** Kokiri Forest exit (closed until Deku Tree / open); Door of Time (needs Song of Time
    and Ocarina / open); Zora's Fountain (closed / open for adult / open for both); Kakariko gate (needs Zelda's
    Letter / open); Gerudo Fortress (four carpenters / one / open); starting age (child / adult / random).
15. **Cutscenes:** skippable / shortened or removed. Playing them in full is not offered.
16. **Gossip hints:** Mask of Truth needed or not; exact or vague; Way of the Hero; Temple of Time altar hints for
    the Stones and Medallions.
17. **Equipment shuffles:** Kokiri Sword, Master Sword, the Ocarinas, Gerudo Membership Card, Deku Shield, Hylian
    Shield. Trade quest items stay out.
18. **Child Zelda skipped entirely:** start with Zelda's Letter; the courtyard isn't needed; Malon and Talon aren't
    outside the castle. Assumed: Impa's Zelda's Lullaby check stays and its item is given at the start.

## Tiers (confirmed in question 21)
21. **The tiers below.**
22. "Golden tokens required" = a number of Gold Skulltula tokens as a condition for the bridge and/or Ganon's Boss Key
(a fifth choice for 12 and 13, in the "very much wanted" tier).

- **Essential (holds the release):** 1-18 above, except the Temple of Time altar hints.
- **Very much wanted in the beta:** Medallion and Spiritual Stone hints (Temple of Time altar); chest size matches
  contents; ice traps and their frequency; shop prices; golden tokens required (meaning to clarify); Navi hints
  about the randomizer; starting location; full wallets; Blue Fire Arrows; Sunlight Arrows; masks as adult; Bunny
  Hood; skip the Epona race; cosmetic randomizer; music randomizer; custom music; coloured or textured pots, grass
  and rocks.
- **Nice to have in the beta:** Song of Soaring; X/X check counter on the in-game map; challenge settings (one hit /
  double damage, Gloom); boss door hints.
- **Experimental:** a proof of concept of tracker waypoints on the in-game map.
- **After the beta:** dungeon entrance, boss and enemy randomizers; Jabber Nuts; "all checks reachable" logic; UI
  customization; custom models; map tracker; daily or weekly race seeds; Glitched and No Logic; keyrings, skeleton
  key, unique key models; barren and "always" hints; trade quest items.

## How it's built
23. **Area by area:** each area is finished completely (every kind of check, logic, in-game tests) before the next.
24. **The generator and the app come at the end**, once every area is mapped. Until then, areas are tested with
    hand-placed test builds, as now. Known cost: the first full-game seed, and the first real use of the generator,
    logic and app, come late.

25. **Area order:** game order, but it starts with one adult dungeon that uses keys, as a test of dungeon items
    (small keys, boss key, maps, compasses, boss, reward).

26. **The first dungeon is the Forest Temple.** Tests reach it with Longshot's debug menu.

27. **When an area counts as done (in-game tests):** every chest, gift, song, scrub, shop shelf and Gold Skulltula
    in game; for pots, grass, rocks, bushes and crates, each new kind of object in the area plus a few samples. The
    test scripts check every check's files regardless. Full seed playthroughs come at the end, with the generator.
    Forest count from the project's data: 159 check IDs (155 Kokiri Forest, 4 Lost Woods). Whole-game count
    (read-only, `docs/RESEARCH_check_count.md`): 1,286 spots, about 12 times the three forest areas; 344 of them in
    the kinds tested one by one (185 chests, 100 Gold Skulltulas, 15 scrubs, 44 shop shelves), plus event checks
    (gifts, songs, boss hearts...) that the maps don't show.

## Release
28. **Published on GitHub (Releases; the repository is already public, MIT License) and a Discord server.** Bugs are
    reported through both.

29. **A quiet early stage before the public beta:** open to anyone interested (through the Discord), with no large
    posts about it yet. Its seeds are the first wide test of the generator, logic and app.

30. **Flat grass tufts are not randomized** (`Obj_Plant_Grass_A_04`, 147 in the game: 0.2 high, no drop settings in
    any placement). "Grass" in the shuffle settings means the solid bushes, as in the forest.

## Roadmap
31. **The roadmap (`docs/ROADMAP.md`) is approved** as a plan of action in priority order, without dates per
    milestone. December 24 stays the target; the date moves when the plan and the date disagree.
32. **Groundwork added as essentials:** starting state on a new file; the item pool; which dungeon a key belongs
    to; game version check; a seed check shown in game; many seeds tested automatically; switching seeds and saves
    (research); default settings; back to the normal game. Known issues listed in the roadmap.
34. **Songs are shuffled anywhere** (not a setting): songs can be on any check, and song checks can give any item.
    Already passed in game: a song from a chest and from a shop shelf (shown as the harp), and items from song checks.
35. **Loose rupees and hearts (150) get their own shuffle setting** in the beta. **Beehives (21) are left out for
    now** (after the beta at the earliest).
36. **The beta is English only.** Other languages are a research item for after the beta.
37. **Shop shuffle setting: how many shelves in each shop are randomized** (assumed: the same number per shop, from
    none to all). The shelves not randomized keep the game's own items, so ammo stays for sale where the game sells
    it.
33. **The four settings gaps are settled:** D34-D37.
38. **Each phase is worked in parts:** one part = one test round = one PR; never two untested parts stacked;
    only the current phase is broken into parts. Phase 1's seven parts are in the roadmap.

## Flagged as unknown (research before any promise)
- Changing when the bridge appears, when the Light Arrow cutscene plays, and a "reward for a condition".
- Starting as adult; Zora's Fountain open for child; moving Malon and Talon home.
- Shortening each story cutscene (needs a list of every cutscene first).
- Mask of Truth question in front of a stone's words.
- Shop families (shelves that appear only while a flag holds).
- Music: how the remake stores it, whether tracks can be added.
- The in-game map screen (check counter, waypoints).
