"""Ground versions of items: an actor Link picks up from the ground (or from a pot), for items the game only
has as the model shown when an item is received.

Found in the game's files:
- `Item_<x>` actors (parent `Item_EventObject_Base`) are only the model held up when an item is received
  (chests, NPCs). They have no pick-up collision: placed on the ground, Link can't take them.
- Ground items are `Obj_` actors (parent `Obj_Item_Base`). Only 24 exist (rupees, hearts, ammunition, the
  Piece of Heart, small keys, shields...). One of them is a major item: `Obj_Ocarina_Time`, the Ocarina of
  Time in the castle moat. It is a thin wrapper around `Item_Ocarina_Time`: its own pack holds the ground
  parts (`Obj_Item_Base`, physics, pick-up event), and the item's model, animation and item settings
  (`PouchContentParam`) are copies of the item's own files. Its table rows: `ActorInfo` with the item's
  model and `ActorName: Item_Ocarina_Time` (what the game shows and stores), `GameActorInfo` (ground object
  physics layer), `PouchActorInfo` (the item row).

A ground version of item X is built the same way, from the game's own files only: the ground ocarina's pack
with the ocarina's model, animation and item settings replaced by X's (with the files they inherit from,
when X's pack has them), an actor parameter file of its own, and the three table rows taken from the
ocarina's (ground parts) and X's (model, name, item row). The name is `Obj_NX2_<X without "Item_">`.

No glow: the ground ocarina has no effect link (the Gold Skulltula token's glow comes from its own
`ELinkRef`, user `Obj_Token_Gold`). One could be added later by pointing `ELinkRef` at an existing effect.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml  # noqa: E402

TEMPLATE = 'Obj_Ocarina_Time'
TEMPLATE_ITEM = 'Item_Ocarina_Time'
PREFIX = 'Obj_NX2_'
# the components that make the item what it is; everything else comes from the ground ocarina
ITEM_REFS = ('ActorNameRef', 'AnimationRef', 'ModelInfoRef', 'PouchContentRef')
ROW_FROM_ITEM = ('ActorName', 'FmdbName', 'ModelAabbMax', 'ModelAabbMin', 'ModelProjectName')
TABLES = ('ActorInfo', 'GameActorInfo', 'PouchActorInfo')


def table_path(t):
    return 'RSDB/%s.Product.111.rstbl.byml' % t


def pack_path(actor):
    return 'Pack/Actor/%s.pack' % actor


def ap_path(actor):
    return 'Actor/%s.engine__actor__ActorParam.bgyml' % actor


def ground_name(item):
    return PREFIX + (item[5:] if item.startswith('Item_') else item)


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
        return 'item'                                 # built like Item_Ocarina_Time (equipment: ocarinas)
    return None


def anim_param_path(actor):
    return 'Component/AnimationParam/%s.engine__component__AnimationParam.bgyml' % actor


def build(item, read_pack, read_table_rows, model_exists=lambda project: False):
    """the ground version of `item`.
    read_pack(path) -> decompressed pack; read_table_rows(table) -> list of rows; model_exists(project name)
    -> whether Model/<project>.anim.bfres exists (items with no animation file of their own: ocarinas).
    Returns (name, pack data, {inner path: data} of files new to the game, {table: new row})."""
    name = ground_name(item)
    tpl = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))
    itm = sarc.Sarc.read(read_pack(pack_path(item)))
    tpl_ap = byml.loads(tpl.files[ap_path(TEMPLATE)])
    itm_ap = byml.loads(itm.files[ap_path(item)]).root
    tc, ic = tpl_ap.root['Components'], itm_ap['Components']
    missing = [r for r in ITEM_REFS if r not in ic and r != 'AnimationRef']
    if missing:
        raise SystemExit('%s: no %s in its actor parameters: no ground version' % (item, ', '.join(missing)))

    files = dict(tpl.files)
    del files[ap_path(TEMPLATE)]
    # the ground ocarina's own item files out, the item's in (with the files they inherit from, when the item's
    # pack has them: the bomb bag's settings inherit from KeyItemDefault, in its pack)
    for r in ITEM_REFS + ('GameParameterTableRef',):
        if r in tc:
            files.pop(_ref_path(tc[r]), None)
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
        # as the ground ocarina has one for Item_Ocarina_Time (whose own actor has none): the same file with
        # the item's animation project
        tdoc = byml.loads(tpl.files[_ref_path(tc['AnimationRef'])])
        res = [dict(x) for x in tdoc.root['AnimationResources']]
        swapped = [dict(x, ModelProjectName=item + '_Animation') if x['ModelProjectName'] == TEMPLATE_ITEM + '_Animation'
                   else x for x in res]
        if swapped == res:
            raise SystemExit('template animation file not as expected')
        tdoc.root = type(tdoc.root)(tdoc.root)
        tdoc.root['AnimationResources'] = swapped
        files[anim_param_path(name)] = byml.dumps(tdoc)
        comp['AnimationRef'] = '?' + anim_param_path(name)
    comp.pop('GameParameterTableRef', None)         # as Obj_Item_Base (the ocarina's only set a menu style)
    doc = copy.copy(tpl_ap)
    doc.root = type(tpl_ap.root)(tpl_ap.root)
    doc.root['Components'] = comp
    files[ap_path(name)] = byml.dumps(doc)
    out = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))      # the ocarina pack's own layout settings
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
    # memory: the item's own needs plus what the ground parts add (as measured on the ocarina), and margin
    extra = int(ai_t['InstanceHeapSize']) - int(ai_ti['InstanceHeapSize'])
    ai['InstanceHeapSize'] = type(ai_t['InstanceHeapSize'])(
        max(int(ai_t['InstanceHeapSize']), int(ai_i['InstanceHeapSize']) + extra) + 16384)
    ai['PreActorRenderInfoHeapSize'] = type(ai_t['PreActorRenderInfoHeapSize'])(
        max(int(ai_t['PreActorRenderInfoHeapSize']), int(ai_i.get('PreActorRenderInfoHeapSize', 0)) + 1024))
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
