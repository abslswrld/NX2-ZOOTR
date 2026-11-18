"""Ground versions of items: an actor Link picks up from the ground (or from a pot), for items the game only
has as the model shown when an item is received.

Found in the game's files:
- `Item_<x>` actors (parent `Item_EventObject_Base`) are only the model held up when an item is received
  (chests, NPCs). They have no pick-up collision: placed on the ground, Link can't take them.
- Ground items are `Obj_` actors (parent `Obj_Item_Base`). Only 24 exist (rupees, hearts, ammunition, the
  Piece of Heart, small keys, shields...). `Obj_Shield_Deku`, the Deku Shield lying on the ground, is a
  single equipment item built as a thin wrapper around the item: its own pack holds the ground parts
  (`Obj_Item_Base`, a body that only touches the ground, a pick-up sensor: `DropItem` / `Item_Pouch_Tgt`,
  layer `SmallObject`), and the item's model, animation and item settings (`PouchContentParam`) are copies
  of the item's own files. Its table rows: `ActorInfo` with the item's model and
  `ActorName: Weapon_Shield_Deku` (what the game shows and stores), `GameActorInfo` (small object layer),
  `PouchActorInfo` (the item row).
- Not the ground Ocarina of Time (`Obj_Ocarina_Time`, castle moat; the first template, 2026-11-16): its
  physics is the generic solid box (`ObjectDefault` -> `Box`, layer `GroundObject`) with no pick-up sensor.
  Tested in game: Link bumps into an invisible box around the item (and climbs it), and can't take it.

A ground version of item X is built the same way, from the game's own files only: the ground shield's pack
with the shield's model, animation, item settings and shield-only settings (equipment table, hookshot hold
position, effect link) taken out and X's model, animation and item settings put in (with the files they
inherit from, when X's pack has them), an actor parameter file of its own, and the three table rows taken
from the shield's (ground parts) and X's (model, name, item row). The name is `Obj_NX2_<X without "Item_">`.

No glow and no effects: the shield's effect link (only its burning effect) is left out, and its row's
`ELinkUserName` removed. Its sound link stays.

Picked up by walking into it, without pressing A: `DefaultAutoGet` in an item's settings (`PouchContentParam`)
decides that. The Bottle's has it, as does the ground shield's (its own settings inherit from `AutoPickShield`);
the Boomerang's, Bomb Bag's, Fairy Ocarina's and Hookshot's don't, and in game (2026-11-16) those showed
"Take" (A). So the ground version gets item settings of its own, built like the ground shield's: the item's
settings as `$parent`, plus `DefaultAutoGet: true`. Only the ground version's pack has them; the item itself
(chests, NPCs) is unchanged.

What goes into the pouch: every game ground item that stands for another item names it in its item settings
(`PouchActor`: the ground shield `Weapon_Shield_Deku`, the ground bomb `Item_Bomb`, the Goron Tunic
`Armor_Adult_Goron`...). Without it the ground actor itself is added. The Fairy Ocarina's own settings have
none (the game never puts it on the ground): in game (2026-11-16) the ground ocarina went into the pouch but
could not be played until a reload. The ground version's settings name the item (`PouchActor`), as the game's
ground items do (to test).

Held-up versions (`Item_NX2_<x>`, to test): what a chest shows when it gives an item. The items that show
(Boomerang, Bottle...) are item event actors (parent `Item_EventObject_Base`) with the get-demo animation
settings (`ASInfo: Item_GetDemo`, `AS/Item_Common`, the `Item_Common_Animation` animations). The ocarinas'
actors are Link's playable instrument instead (equipment: no get-demo settings); a chest giving the Fairy
Ocarina showed nothing (2026-11-16), though the ocarina could be played. A held-up version is built the same
way as a ground version, from the Boomerang's item actor (`Item_Boomerang`) instead of the ground shield:
the Boomerang's own model, animation, item settings and boomerang settings out, the item's in, and item
settings of its own naming the item (`PouchActor`). Only for items that are not item event actors already.

Gold Skulltula drops (`Obj_NX2_GS_<x>`, to test): what a Gold Skulltula drops instead of its token. Found in
the game's files (2026-11-17): a Gold Skulltula is not marked done when it dies but when its token is picked
up, and it is the token that does it. The skulltula's own AI (`Enemy_Skulltula_Gold.utility.root`) hands its
drop the saved flag of its map placement (`QueryBlackboardOverwriteParamAddNoRespawnGmdHash`, key
`GoldTokenGmdHash`, through `OneShotDropSetOverWriteParam`); the token (`Obj_Token_Gold`) has that key in its
blackboard (`Item_Token_Gold` parameter table) and its own AI (`Item_Token_Gold.root`: when it dies of reason
10, picked up, it runs `OneShotGoldTokenDeadAfter`). Dying only sets the skulltula's unsaved flag
`IsGoldSkullDead.IsGoldSkullDead_<placement hash>` (gone until the area is left). Any other item dropped has
neither the key nor that AI, so the skulltula came back after a reload (seen in game). A Gold Skulltula drop
is therefore built from the token itself: the token's pack (its AI, blackboard, death settings, physics,
lock-on) with the token's name, model, animation and item settings out and the item's in; no effect link, the
base's lift settings (the token's name a bone of the token's model).

The spin of a Gold Skulltula drop (2026-11-17: the dropped Piece of Heart lay still). Every item on the ground
spins through its AI: the ground items' AI (`DropItem.root`, and the Piece of Heart's own `Obj_Heart_Piece.root`)
plays the animation command `Rotate_Obj` (`OneShotASPlay`) when nothing is playing, and their animation
settings (`ASInfo`: `Item_Obj`) start nothing by themselves (`AutoPlayASName` empty). The token's AI
(`Item_Token_Gold.root`) plays nothing: the token spins because its own animation settings (`ASInfo`:
`Obj_Token_Gold`) start `Rotate_Obj` by themselves (`AutoPlayASName`); they are `Item_Obj` in every other
value. A drop has the token's AI, so with the item's or the shield's `Item_Obj` nothing ever started the spin.
A drop therefore keeps the token's `ASInfo`, and takes only the animation file (`ASRef`) from the item when it
is a ground item whose file knows `Rotate_Obj` (Piece of Heart: `AS/Obj_Heart_Piece`), else from the ground
shield (`AS/Item_Common`); not the token's own file, whose spin uses an animation of the token's model
(`Rotate_Obj_St`, in `Obj_Token_Gold_Animation`). The `Rotate_Obj` animation itself is in
`Item_Common_Animation`, which the items' animation settings list.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml  # noqa: E402

TEMPLATE = 'Obj_Shield_Deku'
TEMPLATE_ITEM = 'Weapon_Shield_Deku'
PREFIX = 'Obj_NX2_'
# the components that make the item what it is; everything else comes from the ground shield
ITEM_REFS = ('ActorNameRef', 'AnimationRef', 'ModelInfoRef', 'PouchContentRef')
# the ground shield's own settings, left out (the item base's are used): price table (equipment), hookshot
# hold position, effect link
TEMPLATE_ONLY = ('GameParameterTableRef', 'LiftableRef', 'ELinkRef')
# kind of version -> (template actor, the item the template stands for, name prefix, template-only settings left
# out, picked up by walking into it, the template's own animation project)
VERSIONS = {
    'ground': (TEMPLATE, TEMPLATE_ITEM, PREFIX, TEMPLATE_ONLY, True, TEMPLATE_ITEM + '_Animation'),
    'held': ('Item_Boomerang', 'Item_Boomerang', 'Item_NX2_', ('GameParameterTableRef',), False,
             'Item_Boomerang_Animation'),
    # what a Gold Skulltula drops: the token with the item's name, model, animation and item settings
    'token': ('Obj_Token_Gold', 'Item_Token_Gold', 'Obj_NX2_GS_', ('LiftableRef', 'ELinkRef'), True,
              'Obj_Token_Gold_Animation'),
}
TOKEN = 'Obj_Token_Gold'
# what marks the skulltula done when its drop is picked up: checked to be in a 'token' version (build)
TOKEN_KEEPS = {
    'AIInfoRef': '?AI/AIInfo/Item_Token_Gold.engine__actor__AIInfo.bgyml',
    'BlackboardRef': '?Component/Blackboard/BlackboardInfo/Item_Token_Gold.engine__component__BlackboardInfo.bgyml',
    'DeathRef': '?Component/DeathParam/Item_Token_Gold.game__component__DeathParam.bgyml'}
TOKEN_FILES = ('AI/Item_Token_Gold.root.ainb',
               'Component/Blackboard/BlackboardParamTable/Item_Token_Gold.engine__component__BlackboardParamTable.bgyml')
TOKEN_KEY = 'GoldTokenGmdHash'                # the blackboard key the skulltula's flag is handed over in
SPIN = 'Rotate_Obj'                           # the animation command of an item spinning on the ground
ROW_FROM_ITEM = ('ActorName', 'FmdbName', 'ModelAabbMax', 'ModelAabbMin', 'ModelProjectName')
TABLES = ('ActorInfo', 'GameActorInfo', 'PouchActorInfo')


def table_path(t):
    return 'RSDB/%s.Product.111.rstbl.byml' % t


def pack_path(actor):
    return 'Pack/Actor/%s.pack' % actor


def ap_path(actor):
    return 'Actor/%s.engine__actor__ActorParam.bgyml' % actor


def ground_name(item, version='ground'):
    return VERSIONS[version][2] + (item[5:] if item.startswith('Item_') else item)


def template_of(name):
    """the template actor a version (by its name) was built from"""
    hits = [(len(v[2]), v[0]) for v in VERSIONS.values() if name.startswith(v[2])]
    if not hits:
        raise KeyError(name)
    return max(hits)[1]                               # the longest prefix: Obj_NX2_GS_ before Obj_NX2_


def _ref_path(ref):
    """'?Component/X.bgyml' -> 'Component/X.bgyml'"""
    return ref[1:] if ref.startswith('?') else ref


def _parent_path(doc_root):
    """'$parent': 'Work/Component/X.gyml' -> 'Component/X.bgyml' (as stored in a pack)"""
    p = doc_root.get('$parent') if isinstance(doc_root, dict) else None
    if not p:
        return None
    if p.startswith('Work/'):
        p = p[5:]
    return p[:-5] + '.bgyml' if p.endswith('.gyml') else p


def _refs(root):
    """paths a settings file points at, as stored in a pack ('?X.bgyml' values and '$parent')"""
    out = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k == '$parent' and isinstance(x, str):
                    p = x[5:] if x.startswith('Work/') else x
                    out.append(p[:-5] + '.bgyml' if p.endswith('.gyml') else p)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and v.startswith('?'):
            out.append(v[1:])
    walk(root)
    return out


def _reach(files, start):
    """start and every file of the pack it points at, directly or through other files"""
    seen, todo = set(), [start]
    while todo:
        p = todo.pop()
        if p in seen or p not in files:
            continue
        seen.add(p)
        if p.endswith('.bgyml'):
            todo.extend(_refs(byml.loads(files[p]).root))
    return seen


def kind_of(read_pack, item):
    """'ground' (already an Obj_Item_Base actor), 'item' (an Item_EventObject_Base actor: needs a ground
    version) or None (not found / something else)"""
    try:
        files = sarc.Sarc.read(read_pack(pack_path(item))).files
    except FileNotFoundError:
        return None
    if 'Actor/Obj_Item_Base.engine__actor__ActorParam.bgyml' in files:
        return 'ground'
    if 'Actor/Item_EventObject_Base.engine__actor__ActorParam.bgyml' in files:
        return 'item'
    comp = byml.loads(files.get(ap_path(item), b'')).root.get('Components', {}) if ap_path(item) in files else {}
    if 'ModelInfoRef' in comp and 'PouchContentRef' in comp:
        return 'equipment'                            # built like Item_Ocarina_Time (equipment: ocarinas)
    return None


def resolved_components(files, actor):
    """an actor's components with those of the actors it inherits from ($parent), as far as its pack has them"""
    comp, p = {}, ap_path(actor)
    while p and p in files:
        root = byml.loads(files[p]).root
        for k, v in root.get('Components', {}).items():
            comp.setdefault(k, v)
        p = _parent_path(root)
    return comp


GET_DEMO = b'Rotate_GetDemo'


def can_hold_up(read, item):
    """whether Link can hold `item` up in the shared get event (Dm_SY_GetInEvent). That event makes the actor
    itself as the item shown in Link's hands (Player_Event.EventCreateShowItemFromActorFileName) and plays its
    animation command Rotate_GetDemo, waiting for it to end (EventIgnitionShowItem: IsAsPlay, IsWaitEnd). All 40
    actors the game's own flows give that way have an animation file (ASRef, a loose AS/*.asb file) that knows
    that command; the ocarinas (Link's instrument), the songs, the small bags, the stones and the medallions
    have no animation file or one without it, so the wait never ends (the Fairy Ocarina and the seed bag froze
    the game there). read(path) -> file contents (FileNotFoundError when it isn't there)."""
    try:
        files = sarc.Sarc.read(read(pack_path(item))).files
    except FileNotFoundError:
        raise SystemExit('%s: no such actor (no %s)' % (item, pack_path(item)))
    ref = resolved_components(files, item).get('ASRef')
    if not ref:
        return False
    path = _ref_path(ref)
    try:
        data = files[path] if path in files else read(path)
    except FileNotFoundError:
        return False
    return GET_DEMO in data


def pouch_param_path(actor):
    return 'Component/PouchContentParam/%s.game__component__PouchContentParam.bgyml' % actor


def anim_param_path(actor):
    return 'Component/AnimationParam/%s.engine__component__AnimationParam.bgyml' % actor


def build(item, read_pack, read_table_rows, model_exists=lambda project: False, version='ground'):
    """the ground version (version='ground') or held-up version (version='held') of `item`.
    read_pack(path) -> decompressed pack; read_table_rows(table) -> list of rows; model_exists(project name)
    -> whether Model/<project>.anim.bfres exists (items with no animation file of their own: ocarinas).
    Returns (name, pack data, {inner path: data} of files new to the game, {table: new row})."""
    TEMPLATE, TEMPLATE_ITEM, _, TEMPLATE_ONLY, auto_get, tpl_anim = VERSIONS[version]
    name = ground_name(item, version)
    tpl = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))
    itm = sarc.Sarc.read(read_pack(pack_path(item)))
    tpl_ap = byml.loads(tpl.files[ap_path(TEMPLATE)])
    itm_ap = byml.loads(itm.files[ap_path(item)]).root
    tc, ic = tpl_ap.root['Components'], itm_ap['Components']
    if version == 'token':
        # ground items may inherit their parts (the blue rupee from the green one)
        ic = resolved_components(itm.files, item)
        for r, v in TOKEN_KEEPS.items():
            if tc.get(r) != v or _ref_path(v) not in tpl.files:
                raise SystemExit('%s: %s is %r, expected %s (game files differ from what this was made for)'
                                 % (TEMPLATE, r, tc.get(r), v))
        if any(p not in tpl.files for p in TOKEN_FILES) or TOKEN_KEY.encode() not in tpl.files[TOKEN_FILES[1]]:
            raise SystemExit('%s: its AI or its %s blackboard key not found as expected' % (TEMPLATE, TOKEN_KEY))
    missing = [r for r in ITEM_REFS if r not in ic and r != 'AnimationRef']
    if missing:
        raise SystemExit('%s: no %s in its actor parameters: no ground version' % (item, ', '.join(missing)))

    # the ground shield's own item files and shield-only files out (with the files only they point at), the
    # item's in (with the files they inherit from, when the item's pack has them: the bomb bag's settings
    # inherit from KeyItemDefault, in its pack)
    out_refs = ITEM_REFS + TEMPLATE_ONLY
    drop = set()
    for r in out_refs:
        if r in tc:
            drop |= _reach(tpl.files, _ref_path(tc[r]))
    keep = _reach(tpl.files, _parent_path(tpl_ap.root))      # the item base (Obj_Item_Base) and what it uses
    for r, v in tc.items():
        if r not in out_refs and isinstance(v, str) and v.startswith('?'):
            keep |= _reach(tpl.files, _ref_path(v))
    files = {p: d for p, d in tpl.files.items() if p not in drop or p in keep}
    del files[ap_path(TEMPLATE)]
    for r in ITEM_REFS:
        if r not in ic:
            continue
        path = _ref_path(ic[r])
        if path.startswith('ActorSystem/'):          # names live outside the packs
            continue
        while path and path in itm.files:
            files[path] = itm.files[path]
            path = _parent_path(byml.loads(itm.files[path]).root)
        if _ref_path(ic[r]) not in files:
            raise SystemExit('%s: %s (%s) not in its pack' % (item, r, ic[r]))

    comp = type(tc)(tc)
    for r in ITEM_REFS:
        if r in ic:
            comp[r] = ic[r]
        else:
            comp.pop(r, None)
    if 'AnimationRef' not in ic and model_exists(item + '_Animation'):
        # as the ground ocarina has one for Item_Ocarina_Time (whose own actor has none): the ground shield's
        # file with the item's animation project
        tdoc = byml.loads(tpl.files[_ref_path(tc['AnimationRef'])])
        res = [dict(x) for x in tdoc.root['AnimationResources']]
        swapped = [dict(x, ModelProjectName=item + '_Animation') if x['ModelProjectName'] == tpl_anim
                   else x for x in res]
        if swapped == res:
            raise SystemExit('template animation file not as expected')
        tdoc.root = type(tdoc.root)(tdoc.root)
        tdoc.root['AnimationResources'] = swapped
        files[anim_param_path(name)] = byml.dumps(tdoc)
        comp['AnimationRef'] = '?' + anim_param_path(name)
    # picked up by walking into it: item settings of its own (the item's as parent, DefaultAutoGet on), as
    # the ground shield's own settings over AutoPickShield
    pdoc = byml.loads(tpl.files[_ref_path(tc['PouchContentRef'])])
    pdoc.root = type(pdoc.root)()
    pdoc.root['$parent'] = 'Work/' + _ref_path(ic['PouchContentRef'])[:-len('.bgyml')] + '.gyml'
    if auto_get:
        pdoc.root['DefaultAutoGet'] = True
    stands_for, pp = None, _ref_path(ic['PouchContentRef'])
    while pp and pp in itm.files and stands_for is None:   # a ground item may name another item already
        proot = byml.loads(itm.files[pp]).root
        stands_for, pp = proot.get('PouchActor') or None, _parent_path(proot)
    if not (version == 'token' and stands_for and kind_of(read_pack, item) == 'ground'):
        pdoc.root['PouchActor'] = 'Work/' + ap_path(item)[:-len('.bgyml')] + '.gyml'
    files[pouch_param_path(name)] = byml.dumps(pdoc)
    comp['PouchContentRef'] = '?' + pouch_param_path(name)
    if _parent_path(byml.loads(files[pouch_param_path(name)]).root) != _ref_path(ic['PouchContentRef']):
        raise SystemExit('read-back: item settings parent of %s' % name)
    for r in TEMPLATE_ONLY:                         # as Obj_Item_Base
        comp.pop(r, None)
    if version == 'token':
        # the spin: the token's AI plays no animation, its animation settings (ASInfo) start Rotate_Obj by
        # themselves; ground items are spun by their AI instead (DropItem / Obj_Heart_Piece: OneShotASPlay
        # Rotate_Obj) and their settings start nothing. So the token's settings stay, and only the animation
        # file comes from the item (a ground item whose file knows the command: the Piece of Heart), else from
        # the ground shield (Item_Common); the token's own file spins with an animation of the token's model
        info = _ref_path(tc['ASInfoRef'])
        if info not in files or byml.loads(files[info]).root.get('AutoPlayASName') != SPIN:
            raise SystemExit('%s: its animation settings (%s) do not start %s by themselves as expected'
                             % (TEMPLATE, info, SPIN))

        def knows_spin(pack, ref):
            path = _ref_path(ref)
            try:
                return SPIN.encode() in (pack.files[path] if path in pack.files else read_pack(path))
            except FileNotFoundError:
                return False

        sc = ic
        if 'ASRef' not in ic or kind_of(read_pack, item) != 'ground' or not knows_spin(itm, ic['ASRef']):
            src = sarc.Sarc.read(read_pack(pack_path(VERSIONS['ground'][0])))
            sc = resolved_components(src.files, VERSIONS['ground'][0])
            if 'ASRef' not in sc or not knows_spin(src, sc['ASRef']):
                raise SystemExit('%s: its animation file does not know %s as expected' % (VERSIONS['ground'][0], SPIN))
        comp['ASRef'] = sc['ASRef']
        if comp['ASRef'] == tc['ASRef'] or comp.get('ASInfoRef') != tc['ASInfoRef']:
            raise SystemExit('%s: animation settings not as intended' % name)
        for r, v in TOKEN_KEEPS.items():
            if comp.get(r) != v or _ref_path(v) not in files:
                raise SystemExit("%s: lost the token's %s" % (name, r))
        if any(p not in files for p in TOKEN_FILES):
            raise SystemExit("%s: lost the token's AI or blackboard table" % name)
    doc = copy.copy(tpl_ap)
    doc.root = type(tpl_ap.root)(tpl_ap.root)
    doc.root['Components'] = comp
    files[ap_path(name)] = byml.dumps(doc)
    out = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))      # the shield pack's own layout settings
    out.files = files
    out.align = {p: (tpl.align.get(p) or itm.align.get(p) or 8) for p in files}
    pack = out.write()

    rows = {}
    tables = {t: {r['__RowId']: r for r in read_table_rows(t)} for t in TABLES}
    if name in tables['ActorInfo']:
        raise SystemExit('%s already exists in the game' % name)
    ai_t, ai_ti, ai_i = (tables['ActorInfo'][n] for n in (TEMPLATE, TEMPLATE_ITEM, item))
    ai = type(ai_t)(ai_t)
    for k in ROW_FROM_ITEM:
        if k in ai_i:
            ai[k] = ai_i[k]
        else:
            ai.pop(k, None)
    anim = None
    if 'AnimationRef' in comp:
        anim = byml.loads(files[_ref_path(comp['AnimationRef'])]).root.get('AnimationResources')
    if anim is not None:
        ai['AnimationResources'] = anim
    else:
        ai.pop('AnimationResources', None)
    # memory: the item's own needs plus what the ground parts add (as measured on the shield), and margin
    extra = int(ai_t['InstanceHeapSize']) - int(ai_ti['InstanceHeapSize'])
    ai['InstanceHeapSize'] = type(ai_t['InstanceHeapSize'])(
        max(int(ai_t['InstanceHeapSize']), int(ai_i['InstanceHeapSize']) + extra) + 16384)
    ai['PreActorRenderInfoHeapSize'] = type(ai_t['PreActorRenderInfoHeapSize'])(
        max(int(ai_t['PreActorRenderInfoHeapSize']), int(ai_i.get('PreActorRenderInfoHeapSize', 0)) + 1024))
    ai.pop('ELinkUserName', None)                   # no effects (the shield's effect link is left out)
    ai['__RowId'] = name
    rows['ActorInfo'] = ai
    ga = type(tables['GameActorInfo'][TEMPLATE])(tables['GameActorInfo'][TEMPLATE])
    ga['__RowId'] = name
    rows['GameActorInfo'] = ga
    if item not in tables['PouchActorInfo']:
        raise SystemExit('%s has no row in PouchActorInfo' % item)
    pa = type(tables['PouchActorInfo'][item])(tables['PouchActorInfo'][item])
    pa['__RowId'] = name
    rows['PouchActorInfo'] = pa

    new_inner = {p: d for p, d in files.items() if p not in tpl.files and p not in itm.files}
    # read back
    back = sarc.Sarc.read(pack)
    if set(back.files) != set(files) or any(back.files[p] != d for p, d in files.items()):
        raise SystemExit('read-back: pack of %s differs from what was intended' % name)
    want_ap = dict(tpl_ap.root, Components=dict(comp))
    if byml.loads(back.files[ap_path(name)]).root != want_ap:
        raise SystemExit('read-back: actor parameters of %s differ' % name)
    return name, pack, new_inner, rows


def add_rows(data, new_rows):
    """insert rows into an RSDB table (kept sorted by __RowId, as the game's are); checks that nothing else
    changed"""
    doc = byml.loads(data)
    ids = [r['__RowId'] for r in doc.root]
    if ids != sorted(ids):
        raise SystemExit('table not sorted as expected')
    for row in new_rows:
        if row['__RowId'] in ids:
            raise SystemExit('row %s already exists' % row['__RowId'])
    rows = list(doc.root) + list(new_rows)
    rows.sort(key=lambda r: r['__RowId'])
    doc.root[:] = rows if isinstance(doc.root, list) else rows
    new = byml.dumps(doc)
    back = byml.loads(new).root
    old = byml.loads(data).root
    added = {r['__RowId'] for r in new_rows}
    if [r for r in back if r['__RowId'] not in added] != list(old):
        raise SystemExit('read-back: existing rows changed')
    if [r for r in back if r['__RowId'] in added] != sorted(new_rows, key=lambda r: r['__RowId']):
        raise SystemExit('read-back: new rows differ')
    return new
