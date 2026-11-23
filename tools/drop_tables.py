"""Drop tables of our own for progressive families on rocks, bushes, pots and Gold Skulltulas (to test in game).

Why (2026-11-22, in game, out/RESEARCH_drop_tables.md): a family's placement named its last level's drop
directly (`Drop__DropActor`), with rows in the game's drop rules (`DropGlobalParam`: "only dropped once Link
ever got the level before, until then the level before in its place", tools/skulltula_items.py). The rows were
never applied: every check that needed the level before dropped nothing. What the game's files show:
- a placement names either one actor (`Drop__DropActor`) or a drop table by its name (`Drop__DropTable`); the
  game's own rocks, bushes and pots mostly name a table (`DropTable_Obj_Bomb`, `DropTable_Obj_Heart`...), and a
  Gold Skulltula names nothing: it drops from the one table of its drop part (`DropTable_Token_Gold`), and that
  token still marks its skulltula;
- the replace rows belong to drop tables: every item of a game table has `IsReplace: True`, and a table can
  switch the unlock rule off for itself (`NotReplaceOnUnlockCondition`). A single actor named by a placement has
  neither;
- a table item can name one exact actor: `Type` 126134492 with `DropActorName` (Gohma's heart, the red rupees,
  `DropTable_Obj_Bomb_02`: three `Obj_Bomb`, `IsReplace: True`: bombs are in the unlock list).

So a family's placement names a drop table of ours (`Drop__DropTable`, set in the map as the game does; no AI
writes it) with one item: the last level's drop, `IsReplace: True`. The tables are listed in a drop part of our
own name, a copy of the actor's own with our tables added after the game's, which the actor's file names
(`DropRef`). A part of its own name, and tables of their own names, so that no file the game already has
changes: a game file read once from another pack could be kept as it was.

Names: `NX2_<last level>` on rocks, bushes and pots (what the droppers' hand-over looks for, tools/once_items.py:
TABLE_OURS), `NX2_GS_<last level>` on Gold Skulltulas (their table is made from the token's, which differs).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import byml  # noqa: E402
from ground_items import ap_path, resolved_components  # noqa: E402

ROCK = 'Obj_LiftRock_A_01'                       # whose drop part's tables are the shape copied when one has none
SKULLTULA = 'Enemy_Skulltula_Gold'             # the Gold Skulltula's actor
TYPE_ACTOR = 126134492                            # a table item that names one actor (DropActorName)
PREFIX = 'NX2_'
GS_PREFIX = 'NX2_GS_'
PART_PREFIX = 'NX2_'                              # the drop part of our own name: NX2_<the game's part>


def _short(item):
    return item[5:] if item.startswith('Item_') else item


def table_name(family, skulltula=False):
    return (GS_PREFIX if skulltula else PREFIX) + _short(family[-1])


def table_path(name):
    return 'Drop/DropTable/%s.game__drop__DropTable.bgyml' % name


def sub_path(name):
    return 'Drop/DropSubTable/%s.game__drop__DropSubTable.bgyml' % name


def _work(path):
    return 'Work/' + path[:-len('.bgyml')] + '.gyml'


def _unwork(ref):
    return ref[len('Work/'):-len('.gyml')] + '.bgyml'


def part_of(files, actor):
    """the drop part the actor's file names (inner path), checked to be in its pack"""
    ref = resolved_components(files, actor).get('DropRef')
    if not ref or not ref.startswith('?') or ref[1:] not in files:
        raise SystemExit('%s: no drop part in its pack (%r)' % (actor, ref))
    return ref[1:]


def own_part_path(part):
    folder, fn = part.rsplit('/', 1)
    return '%s/%s%s' % (folder, PART_PREFIX, fn)


def template(files, part, fallback=None):
    """(table path, sub-table path, the files they are in) of the first table of the part whose sub-table has
    one item naming one actor: the shape our tables copy. fallback: (files, part) to look in when the part has
    none (the insect bushes' part lists only the insects' table)"""
    for ref in byml.loads(files[part]).root.get('DropTableResourceList') or []:
        t = _unwork(ref)
        if t not in files:
            continue
        subs = byml.loads(files[t]).root.get('SubTableList') or []
        if len(subs) != 1 or _unwork(subs[0]) not in files:
            continue
        items = byml.loads(files[_unwork(subs[0])]).root.get('Items') or []
        if len(items) == 1 and int(items[0]['Type']) == TYPE_ACTOR and items[0].get('IsReplace') is True:
            return t, _unwork(subs[0]), files
    if fallback:
        return template(*fallback)
    raise SystemExit('%s: no table of one named actor to copy' % part)


def build(files, actor, actor_data, tables, fallback=None, loaded=None):
    """the actor's file (`actor_data`: as it is, or as already changed) naming a drop part of our own that lists
    `tables` ({table name: the actor it drops}) after the game's; returns (new actor data, {inner path: (data,
    the game file it is made from, that file's data)}). fallback: see template.
    loaded: {table name: [actors]} listed after the dropped one with chance 0 (DropProbability 0, as the game's
    own tables list items it never picks: Gohma's heart table). They are never picked: they are there so the
    area loads them with the table. Why (2026-11-22, in game): the area loads the actors its tables name; the
    lower levels the drop code's rows put in place were never loaded, and nothing came out. The drop code's
    list of actors kept loaded everywhere (SharePreLoadActorList) did not help: the game loaded its first 16
    entries only, and 14 are the game's own"""
    loaded = loaded or {}
    part = part_of(files, actor)
    t_tpl, s_tpl, tf = template(files, part, fallback)
    new = {}
    pdoc = byml.loads(files[part])
    pdoc.root = type(pdoc.root)(pdoc.root)
    listed = list(pdoc.root.get('DropTableResourceList') or [])
    for name, drop in sorted(tables.items()):
        tdoc, sdoc = byml.loads(tf[t_tpl]), byml.loads(tf[s_tpl])
        tdoc.root = type(tdoc.root)(tdoc.root)
        tdoc.root['DropTableName'] = name
        tdoc.root['SubTableList'] = [_work(sub_path(name))]
        sdoc.root = type(sdoc.root)(sdoc.root)
        item = type(sdoc.root['Items'][0])(sdoc.root['Items'][0])
        item['DropActorName'] = 'Work/Actor/%s.engine__actor__ActorParam.gyml' % drop
        item['DropCreateCount'] = type(item['DropCreateCount'])(1)
        item['DropProbability'] = type(item['DropProbability'])(100)
        kept = []
        for lower in loaded.get(name, ()):
            k = type(item)(item)
            k['DropActorName'] = 'Work/Actor/%s.engine__actor__ActorParam.gyml' % lower
            k['DropProbability'] = type(item['DropProbability'])(0)
            k['BadLuckValueRate'] = type(item['BadLuckValueRate'])(0)
            kept.append(k)
        sdoc.root['Items'] = [item] + kept
        new[table_path(name)] = (byml.dumps(tdoc), t_tpl, tf[t_tpl])
        new[sub_path(name)] = (byml.dumps(sdoc), s_tpl, tf[s_tpl])
        listed.append(_work(table_path(name)))
    pdoc.root['DropTableResourceList'] = listed
    own = own_part_path(part)
    new[own] = (byml.dumps(pdoc), part, files[part])
    adoc = byml.loads(actor_data)
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    comp['DropRef'] = '?' + own
    adoc.root['Components'] = comp
    out = byml.dumps(adoc)
    # read back
    back = byml.loads(out).root
    if dict(back, Components=None) != dict(byml.loads(actor_data).root, Components=None) \
            or dict(back['Components'], DropRef=None) != dict(byml.loads(actor_data).root['Components'], DropRef=None):
        raise SystemExit('read-back: %s: more than its drop part changed' % actor)
    got = tables_of(dict(files, **{p: d for p, (d, _, _) in new.items()}), own)
    if {n: a for n, a in got.items() if n in tables} != tables \
            or {n: x for n, x in loaded_of(dict(files, **{p: d for p, (d, _, _) in new.items()}), own).items()
                if n in tables} != {n: list(loaded.get(n, ())) for n in tables} \
            or byml.loads(new[own][0]).root['DropTableResourceList'][:-len(tables) or None] \
            != list(byml.loads(files[part]).root.get('DropTableResourceList') or []):
        raise SystemExit('read-back: %s: the drop tables are not as intended' % actor)
    return out, new


def _items_of(files, part):
    """(table name, items) for the tables of a drop part that drop one actor: one item naming an actor with
    chance 100 or the only one, any others naming actors with chance 0 (see build: loaded)"""
    for ref in byml.loads(files[part]).root.get('DropTableResourceList') or []:
        t = _unwork(ref)
        if t not in files:
            continue
        root = byml.loads(files[t]).root
        subs = root.get('SubTableList') or []
        if len(subs) != 1 or _unwork(subs[0]) not in files:
            continue
        items = byml.loads(files[_unwork(subs[0])]).root.get('Items') or []
        if items and all(int(i['Type']) == TYPE_ACTOR and i.get('DropActorName') for i in items) \
                and (len(items) == 1 or all(int(i['DropProbability']) == 0 for i in items[1:])):
            yield root.get('DropTableName', ''), [i['DropActorName'][len('Work/Actor/'):-len(
                '.engine__actor__ActorParam.gyml')] for i in items]


def loaded_of(files, part):
    """{table name: the actors listed with chance 0 after the one it drops} (see build: loaded)"""
    return {n: a[1:] for n, a in _items_of(files, part)}


def tables_of(files, part):
    """{table name: the one actor it drops} for the tables of a drop part that drop one actor"""
    return {n: a[0] for n, a in _items_of(files, part)}


