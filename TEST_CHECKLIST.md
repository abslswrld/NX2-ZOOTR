# In-game test checklist (test mod rebuilt 2026-11-16 night, branch `ground-items`)

**Start:** run `out\Launch NX2-ZOOTR test.bat` (it now starts Longshot from `C:\Users\4bsol\Games\Longshot`),
then make a **new file**. Skip the opening.
This round: **automatic pickup.** Last time every ground item worked, but all except the Bottle needed A
("Take"). Now each should be picked up just by walking into it. Same items, same places.

## 0. Does it load?
- [ ] The game reaches Kokiri Forest without crashing (first run on the updated Longshot).

## 1. As a child, Kokiri Forest
- [ ] **Bomb Bag** (blue rupee spot near the path to Mido and the Deku Tree): picked up by walking into it,
      no "Take" prompt? Message and item menu still right?
- [ ] **Boomerang** (in the water, "behind Mido's house"): same question.
- [ ] **Empty Bottle** (in the shop): still picked up automatically?

## 2. House of Twins pots (child)
- [ ] **Fairy Ocarina** from one pot: picked up by walking into it?
- [ ] **Bombchus** from the other pot: still fine (they were automatic already)?

## 3. House of Twins pots (adult, if you can get there)
- [ ] **Hookshot** from the pot: picked up by walking into it?

## 4. Anything odd
- [ ] Wrong item name, wrong icon, crash, or an item that now can't be picked up at all.

Pots still refill (not built yet), so the pot items can be taken again: that's expected.
