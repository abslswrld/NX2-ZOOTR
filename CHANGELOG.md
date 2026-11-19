# Changelog

Newest first. Dates are when the work was done.

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
