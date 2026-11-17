# In-game test checklist (test mod rebuilt 2026-11-16, branch `ocarina-chus-shop`)

**Start:** run `out\Launch NX2-ZOOTR test.bat`, then make a **new file**. Skip the opening.
This round: **the Kokiri Shop only.** The child shop should now be the full shop straight away (no "low on
stock" before the Deku Tree), and the adult shop has its own shelves. You'll need some rupees: about 100
covers everything below.

## 1. Kokiri Shop as a child, before the Deku Tree
- [ ] Does the shopkeeper greet you normally (not "we're low on stock")?
- [ ] Are all 8 shelves filled (no "Coming Soon" signs)? Expected:
  - **Empty Bottle** where the Recovery Heart was, 5 rupees
  - **Boomerang** where the 30 Deku Seeds were, 15 rupees
  - **5 Bombchus** where the 5 Deku Nuts were (bottom left), 75 rupees
  - the game's own items on the other 5 shelves (Deku Nuts 10, Deku Seeds, Deku Sticks, Deku Shield, Deku
    Stick)
- [ ] Names, prices and descriptions right when you look at them? (The Bottle and Boomerang may have an
      empty description: the game has no shop text for them.)
- [ ] Buy the Boomerang, the Bottle and the Bombchus: do you get them, and do they work?
- [ ] After buying, are those shelves **empty** (sold once), also after leaving the shop and coming back,
      and after a save and reload?
- [ ] Can the game's own items still be bought again and again?

## 2. Kokiri Shop as an adult
- [ ] All 8 shelves filled, with the **Hookshot** where the 30 Deku Seeds were, 15 rupees, and the
      Recovery Heart back on its shelf?
- [ ] Buy the Hookshot: works, and the shelf stays empty afterwards?

## 3. Anything odd
- [ ] Crash entering the shop, the shopkeeper standing in the wrong place, items floating or missing.
