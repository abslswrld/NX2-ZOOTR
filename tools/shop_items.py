"""Shop versions of items: an actor that stands on a shop shelf and sells item X.

Found in the game's files:
- A shop shelf item is its own actor, `Shop_<x>` (parent `Shop_Item_Base`): the item's model, animation, name
  and item settings (`PouchContentParam`), plus the shop parts (`Shop_Item_Base`: talk / buy logic, shelf
  physics) and a price: `GameParameterTable` -> `PriceParam` {BuyingPrice, SellingPrice}. Its table rows:
  `ActorInfo` with the item's model and name, `GameActorInfo` (small object), `PouchActorInfo` (the item row
  with BuyingPrice / SellingPrice).
- `Shop_Weapon_Shield_Deku` (Kokiri Shop, 40 rupees) is the shelf version of a single item that keeps the item's
  own name (`ActorName: Weapon_Shield_Deku`): the template here. Its price table also names shield-only
  settings; the new price table is built like the Deku Nut shelf's (`Shop_DekuNutBundle_01`: the shop base's
  table with its own price).
- Where a shelf is placed, the map names the actor (`Gyaml`) and its shelf number (`ShopItemIndex`); the shelf
  is changed by changing the actor, the shelf number stays.
- Shelf items come back after they are bought (`ActorGameDataSetting: AlwaysRespawn`). The game also has
  `NoRespawn` (used by the silver rupee tokens): `once=True` uses it, to try "sold once" (untested).
- Shelves of single items name the item that goes into the pouch in their item settings (`PouchActor`: the
  Deku Shield shelf `Weapon_Shield_Deku`, the Bombchu shelves `Item_Bombchu`). A shop version has item
  settings of its own doing the same: the item's settings as parent, `PouchActor` the item.

A shop version of item X is built from the game's own files only: the shield shelf's pack without its item
and price files, X's model, animation and item settings (with the files they inherit from, when X's pack has
them), the shop base's price files, and two small files of its own (price table and price). The name is
`Shop_NX2_<X without "Item_">_<price>` (`_Once` added for once=True).

The text shown when Link looks at the item uses the item's own name; the shop description
(`<name>_ShopCaption` in the messages) exists only for items the game sells, so other items may show none.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml  # noqa: E402
from ground_items import pack_path, ap_path, table_path, TABLES, _ref_path, pouch_param_path  # noqa: E402,F401

TEMPLATE = 'Shop_Weapon_Shield_Deku'
PRICE_TEMPLATE = 'Shop_DekuNutBundle_01'      # its price table: the shop base's, with its own price
PREFIX = 'Shop_NX2_'
ITEM_REFS = ('ActorNameRef', 'AnimationRef', 'ModelInfoRef', 'PouchContentRef')
ROW_FROM_ITEM = ('ActorName', 'FmdbName', 'ModelAabbMax', 'ModelAabbMin', 'ModelProjectName')
NO_RESPAWN = '?Component/ActorGameDataSetting/NoRespawn.game__component__ActorGameDataSetting.bgyml'


def shop_name(item, price, once=False):
    base = item[5:] if item.startswith('Item_') else item
    return '%s%s_%d%s' % (PREFIX, base, price, '_Once' if once else '')


def gpt_path(actor):
    return 'GameParameter/GameParameterTable/%s.engine__actor__GameParameterTable.bgyml' % actor


def price_path(actor):
    return 'GameParameter/PriceParam/%s.game__pouchcontent__PriceParam.bgyml' % actor


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


def price_of(read_table_rows, shop_actor):
    """the price of a game shelf actor (its PouchActorInfo row)"""
    rows = {r['__RowId']: r for r in read_table_rows('PouchActorInfo')}
    if shop_actor not in rows or 'BuyingPrice' not in rows[shop_actor]:
        raise SystemExit('%s: no price in PouchActorInfo' % shop_actor)
    return int(rows[shop_actor]['BuyingPrice'])


def can_sell(read_pack, item):
    try:
        files = sarc.Sarc.read(read_pack(pack_path(item))).files
    except FileNotFoundError:
        return False
    if ap_path(item) not in files:
        return False
    c = byml.loads(files[ap_path(item)]).root.get('Components', {})
    return all(r in c for r in ('ActorNameRef', 'ModelInfoRef', 'PouchContentRef'))


def build(item, price, read_pack, read_table_rows, once=False):
    """the shop version of `item` at `price` rupees.
    Returns (name, pack data, {inner path: (data, similar game file)} for files new to the game, {table: row})."""
    name = shop_name(item, price, once)
    tpl = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))
    base = sarc.Sarc.read(read_pack(pack_path(PRICE_TEMPLATE)))
    itm = sarc.Sarc.read(read_pack(pack_path(item)))
    tpl_ap = byml.loads(tpl.files[ap_path(TEMPLATE)])
    tc = tpl_ap.root['Components']
    ic = byml.loads(itm.files[ap_path(item)]).root['Components']
    if not can_sell(read_pack, item):
        raise SystemExit('%s: no name, model or item settings of its own: cannot be put on a shelf' % item)

    # the shield shelf without its item and price files (files the kept parts also use stay)
    out_refs = ITEM_REFS + ('GameParameterTableRef',)
    drop = set()
    for r in out_refs:
        if r in tc:
            drop |= _reach(tpl.files, _ref_path(tc[r]))
    keep = {ap_path(TEMPLATE)}
    for r, v in tc.items():
        if r not in out_refs and isinstance(v, str) and v.startswith('?'):
            keep |= _reach(tpl.files, _ref_path(v))
    keep |= _reach(tpl.files, 'Actor/Shop_Item_Base.engine__actor__ActorParam.bgyml')
    files = {p: d for p, d in tpl.files.items() if p not in drop or p in keep}
    del files[ap_path(TEMPLATE)]

    # the item's own files
    for r in ITEM_REFS:
        if r in ic and not _ref_path(ic[r]).startswith('ActorSystem/'):
            got = _reach(itm.files, _ref_path(ic[r]))
            if _ref_path(ic[r]) not in got:
                raise SystemExit('%s: %s (%s) not in its pack' % (item, r, ic[r]))
            for p in got:
                files[p] = itm.files[p]

    # price: the Deku Nut shelf's price table (shop base table + own price), with this name and price
    bgpt_path = _ref_path(byml.loads(base.files[ap_path(PRICE_TEMPLATE)]).root['Components']['GameParameterTableRef'])
    for p in _reach(base.files, bgpt_path) - {bgpt_path, price_path(PRICE_TEMPLATE)}:
        files[p] = base.files[p]
    pdoc = byml.loads(base.files[price_path(PRICE_TEMPLATE)])
    pdoc.root = type(pdoc.root)(pdoc.root)
    pdoc.root['BuyingPrice'] = type(pdoc.root['BuyingPrice'])(price)
    gdoc = byml.loads(base.files[bgpt_path])
    gdoc.root = type(gdoc.root)(gdoc.root)
    gcomp = type(gdoc.root['Components'])(gdoc.root['Components'])
    if gcomp.get('PriceParam') != '?' + price_path(PRICE_TEMPLATE):
        raise SystemExit('price template not as expected')
    gcomp['PriceParam'] = '?' + price_path(name)
    gdoc.root['Components'] = gcomp
    new_inner = {price_path(name): (byml.dumps(pdoc), price_path(PRICE_TEMPLATE)),
                 gpt_path(name): (byml.dumps(gdoc), bgpt_path)}

    comp = type(tc)(tc)
    for r in ITEM_REFS:
        if r in ic:
            comp[r] = ic[r]
        else:
            comp.pop(r, None)
    comp['GameParameterTableRef'] = '?' + gpt_path(name)
    # item settings of its own naming the item for the pouch, as the game's shelves of single items
    tpp = _ref_path(tc['PouchContentRef'])
    pdoc = byml.loads(tpl.files[tpp])
    pdoc.root = type(pdoc.root)()
    pdoc.root['$parent'] = 'Work/' + _ref_path(ic['PouchContentRef'])[:-len('.bgyml')] + '.gyml'
    pdoc.root['PouchActor'] = 'Work/' + ap_path(item)[:-len('.bgyml')] + '.gyml'
    new_inner[pouch_param_path(name)] = (byml.dumps(pdoc), tpp)
    comp['PouchContentRef'] = '?' + pouch_param_path(name)
    if once:
        comp['ActorGameDataSetting'] = NO_RESPAWN
    doc = byml.loads(tpl.files[ap_path(TEMPLATE)])
    doc.root = type(doc.root)(doc.root)
    doc.root['Components'] = comp
    new_inner[ap_path(name)] = (byml.dumps(doc), ap_path(TEMPLATE))
    for p, (d, _) in new_inner.items():
        files[p] = d

    # every file the actor points at is in the pack (apart from names and system settings, kept outside)
    missing = [p for p in _reach(files, ap_path(name)) if p not in files]
    for p in set(_refs(byml.loads(files[ap_path(name)]).root)):
        if p not in files and not p.startswith(('ActorSystem/', 'AS/', 'AI/', 'Component/ActorGameDataSetting/',
                                                 'Component/XLink/', 'Work/', 'Logic/')):
            missing.append(p)
    if missing:
        raise SystemExit('%s: files not in the pack: %s' % (name, ', '.join(sorted(missing))))

    out = sarc.Sarc.read(read_pack(pack_path(TEMPLATE)))
    out.files = files
    out.align = {p: (tpl.align.get(p) or itm.align.get(p) or base.align.get(p) or 8) for p in files}
    pack = out.write()

    tables = {t: {r['__RowId']: r for r in read_table_rows(t)} for t in TABLES}
    if name in tables['ActorInfo']:
        raise SystemExit('%s already exists in the game' % name)
    ai_t, ai_i = tables['ActorInfo'][TEMPLATE], tables['ActorInfo'][item]
    ai = type(ai_t)(ai_t)
    for k in ROW_FROM_ITEM:
        if k in ai_i:
            ai[k] = ai_i[k]
        else:
            ai.pop(k, None)
    anim = byml.loads(files[_ref_path(comp['AnimationRef'])]).root.get('AnimationResources') \
        if 'AnimationRef' in comp else None
    if anim is not None:
        ai['AnimationResources'] = anim
    else:
        ai.pop('AnimationResources', None)
    # memory: the item's own needs on top of the shelf's, and margin
    ai['InstanceHeapSize'] = type(ai_t['InstanceHeapSize'])(
        int(ai_t['InstanceHeapSize']) + int(ai_i['InstanceHeapSize']) + 16384)
    ai['PreActorRenderInfoHeapSize'] = type(ai_t['PreActorRenderInfoHeapSize'])(
        max(int(ai_t['PreActorRenderInfoHeapSize']), int(ai_i.get('PreActorRenderInfoHeapSize', 0)) + 1024))
    ai['__RowId'] = name
    ga = type(tables['GameActorInfo'][TEMPLATE])(tables['GameActorInfo'][TEMPLATE])
    ga['__RowId'] = name
    if item not in tables['PouchActorInfo']:
        raise SystemExit('%s has no row in PouchActorInfo' % item)
    tp = tables['PouchActorInfo'][TEMPLATE]
    pa = type(tables['PouchActorInfo'][item])(tables['PouchActorInfo'][item])
    pa['BuyingPrice'] = type(tp['BuyingPrice'])(price)
    pa['SellingPrice'] = tp['SellingPrice']
    pa['__RowId'] = name
    rows = {'ActorInfo': ai, 'GameActorInfo': ga, 'PouchActorInfo': pa}

    back = sarc.Sarc.read(pack)
    if set(back.files) != set(files) or any(back.files[p] != d for p, d in files.items()):
        raise SystemExit('read-back: pack of %s differs from what was intended' % name)
    if byml.loads(back.files[ap_path(name)]).root != dict(doc.root, Components=dict(comp)):
        raise SystemExit('read-back: actor parameters of %s differ' % name)
    if int(byml.loads(back.files[price_path(name)]).root['BuyingPrice']) != price:
        raise SystemExit('read-back: price of %s differs' % name)
    return name, pack, new_inner, rows
