# Working rules for NX2-ZOOTR

NX2-ZOOTR is a randomizer for the Nintendo Switch 2 remake of Ocarina of Time, played in the Longshot emulator.
These are the project owner's standing rules. Every session follows them, in this checkout and in any worktree.

## What we work on
- **The plan is `docs/ROADMAP.md`**, in its priority order. The decisions in `docs/ROADMAP_DECISIONS.md` are
  settled: don't reopen them unless the user does. Keep both files up to date when a decision is made or a
  phase moves on.
- **Work in parts:** one part of a phase = one test round = one PR. Never start a part before the one before it
  has passed `run_tests.bat` and the user's in-game test.
- **Don't make changes the user didn't ask for.** Suggest them instead.
- **Ask before anything hard to undo, and before any change in the game's folder** (the romfs, the Longshot
  folder). Builds write only to the project's `out` folder.

## Sources
- **Ship no game files.** Use only the remake's own files, never the N64 game's.
- **Other randomizers' code and folders on this PC are reference only:** never copy from them, never credit them.
- **Use the remake's names** for items, places and people (e.g. "Sacred Grove"), taken from the game's own text.

## Randomizer rules
- **Upgrade families never skip a level.** Never put the same item on two checks, except levels of one family.
- **Families** (the user's design): Slingshot (with its first seed bag) > bigger > biggest; Bow (with its first
  quiver) > bigger > biggest; Bomb Bag > bigger > biggest; bigger Deku Nut bag > biggest; bigger Deku Stick bag >
  biggest; Adult's Wallet > Giant's Wallet; Goron Bracelet > Silver Gauntlets > Golden Gauntlets; half magic > full
  magic; Silver Scale > Gold Scale; Hookshot > Longshot; Fairy Ocarina > Ocarina of Time.
- **Never placed:** Deku Nuts and Deku Sticks themselves, the small bags, the small wallet, and trade quest items
  (both chains: Weird Egg, Cucco, Pocket Egg ... Biggoron's Sword, Giant's Knife, Claim Check, Eyeball Frog...).
- **Never use the four adult corner rocks** of Kokiri Forest's rock circle.
- **Flat grass tufts (`Obj_Plant_Grass_A_04`) are never checks.** Beehives are left out for now.

## Building and testing
- **Test builds go to `C:\Emulation\Mods\NX2-ZOOTR\out\mods\NX2-ZOOTR`** (the main checkout's `out`, even when
  working in a worktree). The user starts them with `out\Launch NX2-ZOOTR test.bat`. **Make no new .bat files.**
- **The game's romfs path** is in `romfs_path.txt` in the main checkout (not in git).
- **Every test build that sells anything** (a scrub, a shop shelf) has a gold rupee: `KF_SHOP_RUPEE_ITEM=Obj_Rupee_Gold`
  on the Kokiri Shop floor, and the checklist says where it is. (`KF_SARIAS_HOUSE_HEART_ITEM_01`, `_05` and `_06`
  are on Saria's roof; `_02`, `_03`, `_04`, `_07` are inside.)
- **One checklist, `out\TEST_CHECKLIST.md`, plus `out\TEST_ANSWERS.md`** for the user's answers. Short lists the
  user can do in a day; no "does it load" steps. Dungeons are reached with Longshot's debug menu (it leaves an
  area untouched on a new file).
- **Run `run_tests.bat`** (all test scripts) before saying a change works. New work adds its own test script and
  a row in README.md.
- **In-game results go into CHANGELOG.md.**

## Git
- **Keep CHANGELOG.md** for every change, newest first.
- **Plain commits for small things; a branch and a PR for big work.** Push or merge only after the user approves.
- End commit messages with the `Co-Authored-By` line the session is given.

## Talking to the user
- **Answer in English, plainly and specifically.** The user dislikes vague explanations: name the file, the
  spot, the item, the number.
- **Give exact PowerShell commands** for anything the user has to run.
- **The user often follows over Remote Control:** put questions in the closing message, not only in app boxes.
- **Fable is kept for big research and builds;** small fixes and follow-ups run on the normal model.
