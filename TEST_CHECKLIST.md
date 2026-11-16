# In-game test checklist (test mod built 2026-11-16, branch `ground-items`)

**Start:** run `out\Launch NX2-ZOOTR test.bat`, then make a **new file**. Skip the opening.
This round: **ground versions of items** (new objects made from the game's own ground ocarina). They are
new to the game, so a crash or an invisible object is possible: note exactly where it happens.

## 0. Does it load?
- [ ] The game reaches Kokiri Forest without crashing. (If it crashes when entering the forest or a house,
      note which: that points at one of the new objects.)

## 1. As a child, Kokiri Forest
- [ ] **Bomb Bag** where a blue rupee lies near the path to Mido and the Deku Tree (where the Piece of
      Heart was last time). Can Link pick it up? Does the "you got the Bomb Bag" message appear? Bombs in
      the item menu, and usable?
- [ ] **Boomerang** in the water (the spot named "behind Mido's house", where it couldn't be picked up last
      time). Can Link take it now? Does it work?
- [ ] **Empty Bottle** inside the shop (where the red rupee was). Picked up? Shows in the item menu?
- [ ] For each: does it look right (model, size, sits on the ground or floats)? Any glow or sparkle?
- [ ] Leave the forest and come back, and save/reload: they should **not** come back once taken.

## 2. House of Twins pots (child)
- [ ] One pot drops the **Fairy Ocarina** (a ground version dropped from a pot). Can Link pick it up? Does
      it show and play?
- [ ] The other pot drops **Bombchus**. With the Bomb Bag from step 1, do they go into the item menu this
      time (not 0/0)? Usable?

## 3. House of Twins pots (adult, if you can get there)
- [ ] One pot drops the **Hookshot**. Picked up, usable?

## 4. Anything odd
- [ ] Wrong item name in the message, wrong icon, crash, items in the wrong place.

Pots still refill (not built yet), so the pot items can be taken again: that's expected.
