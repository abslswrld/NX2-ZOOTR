# In-game test checklist (test mod built 2026-11-16, branch `chest-types`)

**Start:** run `out\Launch NX2-ZOOTR test.bat`, then make a **new file** (chests and items stay collected in
older saves). Skip the opening cutscene (it should be skippable). Play as a child.

For each item: write what you got and anything odd (wrong item, no message, crash, item not usable).
Rough notes are fine.

## 1. Kokiri Sword chest (training area, through the crawlspace)
- [ ] It gives the **Fairy Slingshot**.
- [ ] **No sword** is given or equipped afterwards (last time the sword came anyway: its special opening
      event is now removed).
- [ ] The slingshot shows in the item menu and can be used.

## 2. Magic (Mido's house, four chests)
The chests hold the **Lens of Truth**, **Magic**, **Din's Fire** and **Double Magic** (which chest is which
is not known for sure: note it). Best order if you can tell them apart: Lens and Din's Fire first.
- [ ] After the Lens of Truth: **no magic meter appears**.
- [ ] After Din's Fire: still **no magic meter**; neither item can be used.
- [ ] After **Magic**: the magic meter appears (small) and the Lens and Din's Fire work.
- [ ] After **Double Magic**: the meter doubles.
- [ ] If you got Double Magic before Magic: what happened (big meter straight away? then nothing from Magic?).

## 3. Freestanding items (Kokiri Forest, child)
- [ ] **Piece of Heart** where a blue rupee normally lies, near the path to Mido and the Deku Tree, east of
      the village centre. Does it count (4 pieces = 1 heart container)?
- [ ] **Boomerang** where a blue rupee normally lies **behind Mido's house** (the name came from its position:
      check where it really is). Can you pick it up? Does it work?
- [ ] **Red rupee** (20) where a blue rupee normally lies **inside the shop**.
- [ ] Leave Kokiri Forest (e.g. into the Lost Woods) and come back, and also save, quit and reload:
      - [ ] the **Piece of Heart** does **not** come back (should be one-time);
      - [ ] the **Boomerang** does **not** come back;
      - [ ] the red rupee: note whether it comes back (rupees normally do).

## 4. Pots
- [ ] **House of Twins**, two pots: one has a **Piece of Heart**, the other a **Bombchu bundle**.
- [ ] **Know-It-All Brothers' house**, one pot: a **red rupee**.
- [ ] Do the Bombchus show up and work (you have no bomb bag: note whether that matters)?
- [ ] Leave the house and come back (and save/reload): do the pots come back with the **Piece of Heart**
      and **Bombchus** again? (In a randomizer they must not: this tells us whether pots need extra work.)

## 5. Meadow Wolfos grotto (only if you have the Song of Storms in this file)
- [ ] The chest that appears after the Wolfos gives a **Piece of Heart**.

## 6. Things to note along the way
- [ ] The opening skipped fine and the game started normally (Navi with you, quest log OK).
- [ ] Bombs still work without the Goron Bracelet (only if you find a bomb source).
- [ ] Anything else that looks wrong.

Heart pieces in this test: up to 3 (freestanding, pot, Wolfos grotto), so you won't reach a full container
from these alone unless the game counts differently.
