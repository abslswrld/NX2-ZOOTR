"""The cutscene list (roadmap phase 1, for decision 15): every cutscene of the game, read from its files.
Reads only; changes nothing in the game.

    python tools/cutscene_list.py "<romfs>"                      writes data/cutscenes.json and docs/CUTSCENES.md
    python tools/cutscene_list.py "<romfs>" --show Dm_Kokiri_0150   prints one entry of the list

Where each fact comes from
    the events           RSDB/EventSetting (every event of the game: its flow file and entry point, or its
                         timeline file, sub-timelines and movie; its settings list)
    what a cutscene does Event/EventFlow/<flow>.bfevfl: the steps that can run from the event's entry point
                         (flags, challenge steps, items, the next event, a change of map)
    how long it runs     the timeline file's length in frames (60 a second), or the movie file's length; a
                         flowchart has no length of its own: the frames of its wait steps are given instead
    what starts it       other events (an EventTransition step, or the BootEventName of a change of map); the
                         map files (Banc/<Area>/*.bcett.byml: an actor with the event's name in a parameter;
                         for an EventRequestActor, the logic graph of its group, Logic/*.ainb, gives the
                         condition); actor parameter files (Pack/Actor/*.pack: a boss's "die" event, a door's
                         open event, the event of a song played at an actor); the game's sequence graphs
                         (Sequence/*.ainb: the opening)
    whether it can be    the event's settings list (Event/EventSetting/EventSettingComponentList): the
    skipped              cutscene is skippable unless the list has the SkipSetting "DisableSkip"
    names                Mals/USen: LocationMsg/Location (areas), ActorMsg/PouchContent (items)
    checks               data/world/*.json: a check whose gift, cutscene or song names the flow
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from formats import zstd, sarc, byml, evfl, msbt, ainb  # noqa: E402

DATA_FILE = os.path.join(ROOT, 'data', 'cutscenes.json')
DOC_FILE = os.path.join(ROOT, 'docs', 'CUTSCENES.md')
FPS = evfl.FPS

# The order areas are listed in (roughly the order of the game); the names are the Banc folders.
AREA_ORDER = ['KokiriForest', 'InsideTheDekuTree', 'LostWood', 'SacredForestMeadow', 'ForestTemple', 'HyruleField',
              'LonLonRanch', 'Market', 'HyruleCastle', 'TimeTemple', 'KakarikoVillage', 'Graveyard',
              'BottomOfTheWell', 'ShadowTemple', 'DeathMountainTrail', 'GoronCity', 'DodongoCavern',
              'DeathMountainCrater', 'FireTemple', 'ZoraRiver', 'ZoraDomain', 'ZoraFountain', 'InsideJabuJabuBelly',
              'IceCavern', 'LakeHylia', 'WaterTemple', 'GerudoValley', 'GerudoFortress', 'GerudoTrainingGround',
              'HountedWasteland', 'DesertColossus', 'SpiritTemple', 'SageRoom', 'GanonCastle', 'InsideGanonCastle',
              'DreamWorld']
# Areas with no line in LocationMsg/Location (the game shows no title for them).
AREA_NAME_MISSING = {'SageRoom': 'Chamber of Sages (the game\'s files: SageRoom)'}
# A Dm_ name's area, used only when neither the event's settings nor a map nor its starter names one.
NAME_AREA = [('Dm_Kokiri', 'KokiriForest'), ('Dm_Deku', 'InsideTheDekuTree'), ('Dm_LostWood', 'LostWood'),
             ('Dm_SacredForest', 'SacredForestMeadow'), ('Dm_ForestTemple', 'ForestTemple'),
             ('Dm_HrlField', 'HyruleField'), ('Dm_LonLon', 'LonLonRanch'), ('Dm_HrlCastle', 'HyruleCastle'),
             ('Dm_TimeTemple', 'TimeTemple'), ('Dm_Kakariko', 'KakarikoVillage'), ('Dm_Graveyard', 'Graveyard'),
             ('Dm_ShadowTemple', 'ShadowTemple'), ('Dm_DeathMtTrail', 'DeathMountainTrail'),
             ('Dm_DeathMtCrater', 'DeathMountainCrater'), ('Dm_Goron', 'GoronCity'),
             ('Dm_DodongoCave', 'DodongoCavern'), ('Dm_FireTemple', 'FireTemple'), ('Dm_ZoraRiver', 'ZoraRiver'),
             ('Dm_ZoraFountain', 'ZoraFountain'), ('Dm_Zora', 'ZoraDomain'),
             ('Dm_InsideJabu_Jabu', 'InsideJabuJabuBelly'), ('Dm_LakeHrl', 'LakeHylia'),
             ('Dm_WaterTemple', 'WaterTemple'), ('Dm_GerudoValley', 'GerudoValley'), ('Dm_Gerudo', 'GerudoFortress'),
             ('Dm_DesertColossus', 'DesertColossus'), ('Dm_SpiritTemple', 'SpiritTemple'),
             ('Dm_SageRoom', 'SageRoom'), ('Dm_Awake', 'SageRoom'), ('Dm_InsideGanonCastle', 'InsideGanonCastle'),
             ('Dm_GanonCastle', 'GanonCastle'), ('Dm_FinalBattle', 'GanonCastle')]

# Subflows that hand an item over: the item is their ActorName parameter.
GIVE_FLOWS = {'GetPouchContent', 'Dm_SY_GetInEvent', 'Dm_SY_Get'}
# Map parameters that only say which event an actor uses for its own work (doors, chests, hints): counted, not
# listed one by one.
REQUEST_PARAMS = ('RequestEventName', 'InitEventName')
SYSTEM_PREFIXES = ('Dm_SY_', 'DmF_SY_')
# The title screen and the credits are filmed in other maps' copies: listed under no area.
NO_AREA = ('Dm_Title', 'Dm_StaffCredit', 'Dm_Ending')


def base(path):
    """'Work/Event/EventFlow/Dm_Kokiri_0150.evtm' -> 'Dm_Kokiri_0150'"""
    return os.path.basename(path or '').split('.')[0]


def plain(v):
    """an event flow parameter as plain JSON data"""
    if isinstance(v, evfl.Argument):
        return '(argument %s)' % v
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    if isinstance(v, float):
        return round(v, 4)
    return v


# ================================================================================================ the game's files
class Game:
    def __init__(self, romfs):
        self.romfs = romfs
        self.dicts = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
        self._flows, self._logic = {}, {}
        self.flow_files = self._flow_files()
        self.logic_files = {f.split('.')[0]: f for f in os.listdir(os.path.join(romfs, 'Logic')) if '.ainb' in f}

    def read(self, rel):
        data = open(os.path.join(self.romfs, rel), 'rb').read()
        return zstd.decompress(data, self.dicts) if rel.endswith('.zs') else data

    def doc(self, rel):
        return byml.loads(self.read(rel)).root

    def one(self, folder, start):
        """the file in `folder` whose name starts with `start` (the names carry a version number)"""
        hits = sorted(f for f in os.listdir(os.path.join(self.romfs, folder)) if f.startswith(start))
        if not hits:
            raise FileNotFoundError('%s/%s*' % (folder, start))
        return folder + '/' + hits[-1]

    def rsdb(self, name):
        return self.doc(self.one('RSDB', name + '.Product.'))

    def _flow_files(self):
        """flow name -> file. A flow named in EventFlowFileEntry's Versions is loaded from
        <name>.<version>.bfevfl (13 flows), as the game does."""
        folder = os.path.join(self.romfs, 'Event', 'EventFlow')
        names = os.listdir(folder)
        versions = {}
        for f in names:
            if f.startswith('EventFlowFileEntry.'):
                versions = dict(self.doc('Event/EventFlow/' + f).get('Versions') or {})
        out = {}
        for f in sorted(names):
            parts = f.split('.')
            if 'bfevfl' not in parts:
                continue
            name, version = parts[0], (parts[1] if parts[1] != 'bfevfl' else None)
            if version == versions.get(name):
                out[name] = 'Event/EventFlow/' + f
        return out

    def flow(self, name):
        if name not in self._flows:
            rel = self.flow_files.get(name)
            self._flows[name] = evfl.loads(self.read(rel)) if rel else None
        return self._flows[name]

    def logic(self, name):
        if name not in self._logic:
            f = self.logic_files.get(name)
            self._logic[name] = ainb.Ainb.read(self.read('Logic/' + f)) if f else None
        return self._logic[name]

    def texts(self):
        arc = sarc.Sarc.read(self.read(self.one('Mals', 'USen.Product.')))
        return arc.files


def movie_seconds(path):
    """length of a .webm file, from its header (the Duration and TimecodeScale elements)"""
    with open(path, 'rb') as f:
        d = f.read(4096)
    scale = 1000000
    i = d.find(b'\x2a\xd7\xb1')
    if i >= 0:
        scale = int.from_bytes(d[i + 4:i + 4 + (d[i + 3] & 0x7F)], 'big')
    i = d.find(b'\x44\x89')
    if i < 0:
        return None
    n = d[i + 2] & 0x7F
    v = struct.unpack('>f' if n == 4 else '>d', d[i + 3:i + 3 + n])[0]
    return round(v * scale / 1e9, 2)


# ================================================================================================ event flows
def walk(fc, start):
    """the events that can run from event `start`, entry points called in the same file included"""
    seen, order, todo = set(), [], [start]
    while todo:
        i = todo.pop(0)
        if i is None or i in seen:
            continue
        seen.add(i)
        order.append(i)
        e = fc.events[i]
        todo += fc.links(i)
        if e.type in ('subflow', 'callswitch') and not e.flowchart:
            try:
                todo.append(fc.entry_point(e.entry).main)
            except KeyError:
                pass
    return order


def longest(fc, start, stack=(), path=frozenset(), budget=None):
    """(frames of wait steps, message windows) on the longest way from event `start`: steps one after
    another add up, of branches run side by side or chosen between the longest counts"""
    budget = budget if budget is not None else [0]
    total, talks, seen, i = 0, 0, set(), start
    budget[0] += 1
    if budget[0] > 20000:
        return 0, 0
    while i is not None and i not in seen and i not in path:
        seen.add(i)
        e = fc.events[i]
        if e.type == 'action':
            act = fc.actors[e.actor].actions[e.action]
            frames = (e.params or {}).get('Frames')
            if act in ('EventWait', 'EventWaitFrameOrSkip') and isinstance(frames, int) \
                    and not isinstance(frames, bool):
                total += frames
            if act == 'EventTalk':
                talks += 1
            i = e.next
        elif e.type == 'join':
            i = e.next
        elif e.type == 'subflow':
            if not e.flowchart and e.entry not in stack:
                try:
                    a, b = longest(fc, fc.entry_point(e.entry).main, stack + (e.entry,), frozenset(), budget)
                    total, talks = total + a, talks + b
                except KeyError:
                    pass
            i = e.next
        else:
            ways = e.forks if e.type == 'fork' else [ev for _, ev in e.cases]
            best = max([longest(fc, w, stack, path | seen, budget) for w in ways] or [(0, 0)])
            total, talks = total + best[0], talks + best[1]
            i = e.join if e.type == 'fork' else None
    return total, talks


def flow_facts(fc, start):
    """What the steps reachable from event `start` do: flags and challenge steps set, items given, the events
    started, a change of map, and how long the waits are."""
    f = {'sets': [], 'gives': [], 'next': [], 'warps': [], 'reads': [], 'played_checks': [], 'calls': [],
         'shows': [], 'steps': 0, 'talks': 0}

    def add(key, item):
        if item not in f[key]:
            f[key].append(item)

    order = walk(fc, start)
    f['steps'] = len(order)
    for i in order:
        e = fc.events[i]
        p = e.params or {}
        if e.type == 'action':
            actor, act = fc.actors[e.actor], fc.actors[e.actor].actions[e.action]
            if act in ('EventTriggerSetGameDataBool', 'EventTriggerSetGameDataInt', 'EventTriggerSetGameDataEnum',
                       'EventTriggerSetGameDataString64', 'EventTriggerSetGameDataFloat',
                       'EventTriggerSetGameDataBoolArrayAllOnce'):
                item = {'flag': plain(p.get('GameDataName')), 'value': plain(p.get('Value'))}
                if isinstance(p.get('Index'), int) and p.get('Index') >= 0:
                    item['index'] = p['Index']
                add('sets', item)
            elif act in ('EventTriggerAddOrSubGameDataInt', 'EventTriggerAddOrSubGameDataFloat'):
                add('sets', {'flag': plain(p.get('GameDataName')), 'add': plain(p.get('Value'))})
            elif act in ('EventExecuteProgressChallengeStep', 'EventTriggerProgressChallengeStep'):
                add('sets', {'challenge': base(p.get('ChallengeName')), 'step': plain(p.get('StepName'))})
            elif act == 'EventExecuteRollbackChallengeStep':
                add('sets', {'challenge': base(p.get('ChallengeName')), 'step': plain(p.get('ChallengeStep')),
                             'rollback': True})
            elif act.startswith('EventTriggerSetEventBool'):
                add('sets', {'event_bool': act[len('EventTriggerSet'):], 'value': plain(p.get('Bool')),
                             'of': actor.name})
            elif act == 'EventTrigger_SetTime':
                add('sets', {'time': '%02d:%02d' % (p.get('TimeHour', 0), p.get('TimeMin', 0))})
            elif act == 'EventTriggerOpenLocationUI':
                add('sets', {'location_title': base(p.get('LocationName'))})
            elif act == 'EventTriggerRequestAutoSave':
                add('sets', {'autosave': True})
            elif act == 'EventTriggerAddOrRemovePouchContent':
                add('gives', {'item': plain(p.get('Actor')), 'count': plain(p.get('Num', 1)), 'by': act})
            elif act == 'EventTriggerIncreaseRupee':
                add('gives', {'rupees': plain(p.get('Value')), 'by': act})
            elif act in ('EventGetDungeonMap', 'EventGetDungeonCompass', 'EventGetDungeonBossKey',
                         'EventGetDungeonSmallKey'):
                add('gives', {'item': act[len('EventGet'):], 'by': act})
            elif act in ('EventTriggerHealLife', 'EventTriggerHealLifeMax'):
                add('gives', {'hearts_refilled': plain(p.get('Value', 'all')), 'by': act})
            elif act == 'EventTransition':
                add('next', plain(p.get('EventName')))
            elif act.startswith('EventReserveBancChange'):
                w = {'map': plain(p.get('NextBanc')), 'at': plain(p.get('NextStartPos')),
                     'then_event': plain(p.get('BootEventName'))}
                add('warps', {k: v for k, v in w.items() if v not in (None, '')} or {'map': act})
            elif act == 'EventTalk':
                f['talks'] += 1
            if actor.name.startswith(('Item_', 'Weapon_', 'Armor_')) or actor.name == 'Obj_Heart_Container':
                add('shows', actor.name)
        elif e.type == 'switch':
            q = fc.actors[e.actor].queries[e.query]
            if q in ('EventQueryIsGameDataBool', 'EventQueryIsGameDataBoolExp', 'EventQueryIsGameDataInt',
                     'EventQueryIsGameDataEnum', 'EventQueryGameDataIntBranch'):
                add('reads', plain(p.get('GameDataName') or p.get('GameDataNameBoolExp') or ''))
            elif q == 'EventQueryHavePlayedEvent':
                add('played_checks', plain(p.get('EventName') or ''))
        elif e.type in ('subflow', 'callswitch') and e.flowchart:
            if e.flowchart in GIVE_FLOWS and 'ActorName' in p:
                add('gives', {'item': plain(p['ActorName']), 'by': '%s<%s>' % (e.flowchart, e.entry)})
            add('calls', '%s<%s>' % (e.flowchart, e.entry))
    f['reads'] = sorted(x for x in f['reads'] if x)
    f['wait_frames'], f['talks_longest'] = longest(fc, start)
    return f


# ================================================================================================ logic graphs
AND_NODES = ('OperateAND', 'OperateANDPulse', 'OperateANDFixInputTrue')
OR_NODES = ('OperateOR', 'OperateORPulse', 'OperateORFixInputTrue', 'OperateORFixInputTrueWithReset.module')
NOT_NODES = ('OperateInvertBool', 'InvBool.module')


class Logic:
    """Reads conditions out of one logic graph (an AINB file). A graph can embed other graphs as modules: a
    module node's inputs are the embedded graph's Element_ModuleIF_Input nodes, its outputs the
    Element_ModuleIF_Output nodes. `parent` = (the Logic that embeds this one, its module node), so a condition
    can be followed out of the module and back in. `load` gives the graph of a file name."""

    def __init__(self, doc, load=None, parent=None, depth=0):
        self.doc, self.load, self.parent, self.depth = doc, load, parent, depth
        self._rev = None

    def node_name(self, i):
        n = self.doc.nodes[i]
        return n.name or n.type_name

    def is_module(self, i):
        return self.node_name(i).endswith('.module') and self.node_name(i) not in OR_NODES + NOT_NODES

    def child(self, i):
        """the Logic of the graph embedded by module node i (None when its file isn't there)"""
        if self.load is None or self.depth >= 3:
            return None
        doc = self.load(self.node_name(i).split('.')[0])
        return Logic(doc, self.load, (self, i), self.depth + 1) if doc is not None else None

    def value(self, i, name):
        """the fixed value of parameter `name` of node i (immediate, or an input with nothing linked)"""
        n = self.doc.nodes[i]
        for t in ainb.PARAM_TYPES:
            for x in n.immediates[t]:
                if x.name == name:
                    return x.value
            for x in n.inputs[t]:
                if x.name == name and x.node < 0 and not x.sources:
                    return x.value
        return None

    def sources(self, i, name):
        """[(node, type name, output index)] feeding input `name` of node i"""
        n = self.doc.nodes[i]
        for t in ainb.PARAM_TYPES:
            for x in n.inputs[t]:
                if x.name == name:
                    if x.sources is not None:
                        return [(s[0], t, s[1]) for s in x.sources if s[0] >= 0]
                    return [(x.node, t, x.param)] if x.node >= 0 else []
        return []

    def linked_inputs(self, i):
        n = self.doc.nodes[i]
        return [x.name for t in ainb.PARAM_TYPES for x in n.inputs[t] if x.node >= 0 or x.sources]

    def out_name(self, i, t, k):
        outs = self.doc.nodes[i].outputs[t]
        return outs[k].name if 0 <= k < len(outs) else '#%d' % k

    def inputs_all(self, i, name, depth, seen, sep):
        parts = [self.cond(n, t, k, depth + 1, seen) for n, t, k in self.sources(i, name)]
        parts = [p for j, p in enumerate(parts) if p not in parts[:j]]
        if not parts:
            return 'nothing'
        if len(parts) == 1:
            return parts[0]
        return '(' + sep.join(parts) + ')'

    def cond(self, i, t, k, depth=0, seen=()):
        """output k (of type t) of node i, as text"""
        name, out = self.node_name(i), self.out_name(i, t, k)
        key = (id(self.doc), i)
        if depth > 9 or key in seen:
            return '...'
        seen = seen + (key,)
        if name in AND_NODES or name in OR_NODES:
            s = self.inputs_all(i, 'BoolMulti' if self.sources(i, 'BoolMulti') else 'Bool', depth, seen,
                                ' AND ' if name in AND_NODES else ' OR ')
            if 'FixInputTrue' in name:
                s = 'once ' + s
            return 'NOT ' + s if out == 'False' else s
        if name in NOT_NODES:
            return 'NOT ' + self.inputs_all(i, 'BoolMulti' if self.sources(i, 'BoolMulti') else 'Bool', depth,
                                            seen, ' AND ')
        if name == 'HoldGameDataGetBoolSimple':
            return 'flag %s' % self.value(i, 'GameDataNameBool')
        if name == 'HoldGameDataGetBoolExpSimple':
            return 'flag %s' % self.value(i, 'GameDataNameBoolExp')
        if name == 'HoldGameDataGetIntSimple':
            return 'number %s' % self.value(i, 'GameDataNameInt')
        if name == 'HoldGameDataHavePlayedEvent':
            return ('%s played' if out == 'HavePlayed' else '%s not played') % self.value(i, 'EventName')
        if name == 'HoldChallengeCurrentStepCheckOrder':
            word = {'IsAfter': 'after', 'IsBefore': 'before', 'IsEqual': 'at'}.get(out, out)
            return 'challenge %s %s %s' % (base(self.value(i, 'ChallengeName')), word,
                                           self.value(i, 'ChallengeStepName'))
        if name == 'HoldIsChildhoodOrAdulthood':
            return 'adult' if out == 'Adulthood' else 'child'
        if name in ('HoldActorObserverBySensorHitInfo', 'HoldActorObserverWithInstanceNameBySensorHitInfo',
                    'HoldActorTagObserverBySensorHitInfo'):
            who = self.value(i, 'ActorName') or self.value(i, 'TagName') or 'an actor'
            who = 'Link' if who == 'Player' else who
            areas = [self.cond(n, tt, kk, depth + 1, seen) if not self.node_name(n).startswith('ActorLogic')
                     else self.actor_text(n, depth, seen) for n, tt, kk in self.sources(i, 'SensorHitInfoMulti')]
            return '%s %s %s' % (who, 'not in' if out == 'IsNotHit' else 'in', ' / '.join(areas) or 'an area')
        if name == 'HoldGeneralDelayBool':
            return '%s for %g frames' % (self.inputs_all(i, 'Bool', depth, seen, ' AND '),
                                         self.value(i, 'Frame') or 0)
        if name == 'OperateCompareInt':
            def side(n):
                src = self.sources(i, n)
                return self.cond(*src[0], depth + 1, seen) if src else str(self.value(i, n))
            sign = {'A_Bigger': '>', 'A_Smaller': '<', 'Equal': '='}.get(out, out)
            return '%s %s %s' % (side('Int_A'), sign, side('Int_B'))
        if name == 'HoldPlayerrCheckEventQueryPlayerState':
            return 'Link %s state %s' % ('in' if out == 'IsState' else 'not in',
                                         self.value(i, 'EventQueryPlayerState'))
        if name.startswith('Element_ModuleIF_Input'):
            # an input of this module: what the graph that embeds it feeds in
            if self.parent is not None:
                up, node = self.parent
                if self.value(i, 'Name') in up.linked_inputs(node):
                    return up.inputs_all(node, self.value(i, 'Name'), depth, seen, ' AND ')
                v = up.value(node, self.value(i, 'Name'))
                return 'always' if v is True else ('never' if v is False else str(v))
            return 'input "%s" of this logic module' % self.value(i, 'Name')
        if self.is_module(i):
            # an output of an embedded module: what feeds its Element_ModuleIF_Output node of that name
            ch = self.child(i)
            if ch is not None:
                for j in range(len(ch.doc.nodes)):
                    if ch.node_name(j).startswith('Element_ModuleIF_Output') and ch.value(j, 'Name') == out:
                        names = ch.linked_inputs(j)
                        if names:
                            return ch.inputs_all(j, names[0], depth, seen, ' AND ')
            return 'module %s: %s' % (name.split('.')[0], out)
        if name.startswith('ActorLogic'):
            return '%s: %s' % (self.actor_text(i, depth, seen, bare=True), out)
        vals = []
        n = self.doc.nodes[i]
        for tt in ('string', 'int', 'bool', 'float'):
            for x in list(n.immediates[tt]) + [x for x in n.inputs[tt] if x.node < 0 and not x.sources]:
                if x.name not in ('NoEventPause', 'UpdateOnce', 'GameDataArrayIndex') and x.value not in ('', None):
                    vals.append('%s=%s' % (x.name, base(x.value) if isinstance(x.value, str) else x.value))
        return '%s(%s): %s' % (name, ', '.join(vals[:4]), out)

    def actor_text(self, i, depth, seen, bare=False):
        """an actor node as text: its instance name and, when it isn't always there, when it exists"""
        text = '%s %s' % (self.node_name(i)[len('ActorLogic'):], self.value(i, 'InstanceName'))
        if not bare and depth < 6:
            if self.sources(i, 'Logic_Create'):
                text += ' [there while: %s]' % self.inputs_all(i, 'Logic_Create', depth, seen, ' AND ')
            if self.sources(i, 'Logic_Delete'):
                text += ' [gone once: %s]' % self.inputs_all(i, 'Logic_Delete', depth, seen, ' AND ')
        return text

    def rev(self):
        """{(node, type, output index): [node it feeds]}"""
        if self._rev is None:
            self._rev = {}
            for j, n in enumerate(self.doc.nodes):
                for t in ainb.PARAM_TYPES:
                    for x in n.inputs[t]:
                        srcs = x.sources if x.sources is not None else ([(x.node, x.param)] if x.node >= 0 else [])
                        for s in srcs:
                            if s[0] >= 0 and j not in self._rev.setdefault((s[0], t, s[1]), []):
                                self._rev[(s[0], t, s[1])].append(j)
        return self._rev

    def driven(self, i, k, depth=0, seen=None):
        """text of each trigger node driven by bool output k of node i, looking through AND / OR / delay
        nodes and out of the module into the graph that embeds it"""
        seen = seen if seen is not None else set()
        found = []
        if depth > 6:
            return found
        for j in self.rev().get((i, 'bool', k), []):
            if (id(self.doc), j) in seen:
                continue
            seen.add((id(self.doc), j))
            name = self.node_name(j)
            if name.startswith('Trigger'):
                found.append(self.trigger_text(j))
            elif name in AND_NODES or name in OR_NODES or name in NOT_NODES or name == 'HoldGeneralDelayBool':
                for kk in range(len(self.doc.nodes[j].outputs['bool'])):
                    found += self.driven(j, kk, depth + 1, seen)
            elif name.startswith('Element_ModuleIF_Output') and self.parent is not None:
                up, node = self.parent
                for kk, o in enumerate(up.doc.nodes[node].outputs['bool']):
                    if o.name == self.value(j, 'Name'):
                        found += up.driven(node, kk, depth + 1, seen)
        return found

    def users(self, i):
        """{output name: [what the logic does when that output of node i comes on]}"""
        out = {}
        for k, o in enumerate(self.doc.nodes[i].outputs['bool']):
            found = sorted(set(self.driven(i, k)))
            if found:
                out[o.name] = found
        return out

    def trigger_text(self, j):
        name = self.node_name(j)
        if name in ('TriggerGameDataSetBoolTrue', 'TriggerGameDataSetBoolFalse'):
            return 'flag %s = %s' % (self.value(j, 'GameDataNameBool'), 'true' if name.endswith('True') else 'false')
        if name == 'TriggerRequestAutoSave':
            return 'autosave'
        vals = []
        n = self.doc.nodes[j]
        for tt in ('string', 'int'):
            for x in list(n.immediates[tt]) + [x for x in n.inputs[tt] if x.node < 0 and not x.sources]:
                if x.name not in ('GameDataArrayIndex',) and x.value not in ('', None, -1):
                    vals.append('%s=%s' % (x.name, base(x.value) if isinstance(x.value, str) else x.value))
        return '%s(%s)' % (name, ', '.join(vals[:4]))

    def requests(self, out, played):
        """adds this graph's event request nodes to `out` {instance name: [facts]}, embedded modules included"""
        for i in range(len(self.doc.nodes)):
            nn = self.node_name(i)
            if nn in REQUEST_NODES:
                d = {}
                if self.sources(i, 'EventRequestTrigger'):
                    d['when'] = self.inputs_all(i, 'EventRequestTrigger', 0, (), ' AND ')
                if self.sources(i, 'Logic_Create'):
                    d['there'] = self.inputs_all(i, 'Logic_Create', 0, (), ' AND ')
                if self.sources(i, 'Logic_Delete'):
                    d['gone'] = self.inputs_all(i, 'Logic_Delete', 0, (), ' AND ')
                for key in ('when', 'there', 'gone'):
                    if d.get(key) in ('always', 'never', 'nothing'):
                        del d[key]
                after = self.users(i)
                if after:
                    d['after'] = after
                if self.parent is not None:
                    d['module'] = self.doc.filename.split('.')[0] if getattr(self.doc, 'filename', None) else True
                lst = out.setdefault(self.value(i, 'InstanceName'), [])
                if d not in lst:
                    lst.append(d)
            elif nn == 'HoldGameDataHavePlayedEvent':
                ev = self.value(i, 'EventName')
                if ev and ev not in played:
                    played.append(ev)
            elif self.is_module(i):
                ch = self.child(i)
                if ch is not None:
                    ch.requests(out, played)


REQUEST_NODES = ('ActorLogicEventRequestActor', 'ActorLogicEventProxyRequestActor')


def logic_requests(game, name, _cache={}):
    """({instance name: facts}, [events whose 'played' state is tested]) for logic file `name` and the modules
    it embeds. Facts: 'when' (what turns the request on), 'there' / 'gone' (when the actor exists), 'after'
    (what the logic sets when the event's outputs come on). Two copies of one module in a graph give two sets
    of facts for one name: their texts are joined with ' | or: '."""
    key = (id(game), name)
    if key in _cache:
        return _cache[key]
    doc = game.logic(name)
    found, played, out = {}, [], {}
    if doc is not None:
        Logic(doc, game.logic).requests(found, played)
    for inst, variants in found.items():
        d = dict(variants[0])
        for v in variants[1:]:
            for k in ('when', 'there', 'gone'):
                if v.get(k) and v.get(k) != d.get(k):
                    d[k] = (d[k] + ' | or: ' if d.get(k) else '') + v[k]
            for k, lst in (v.get('after') or {}).items():
                d.setdefault('after', {})
                d['after'][k] = sorted(set(d['after'].get(k, [])) | set(lst))
        out[inst] = d
    _cache[key] = (out, played)
    return _cache[key]


# ================================================================================================ the list
def map_events(game, rows):
    """Where the map files name an event: {event: [placement]} and, per parameter name, how often."""
    placements, counts, played = {}, {}, {}
    folder = os.path.join(game.romfs, 'Banc')
    for area in sorted(os.listdir(folder)):
        d = os.path.join(folder, area)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.bcett.byml.zs'):
                continue
            root = game.doc('Banc/%s/%s' % (area, fn))
            mapname = fn.split('.')[0]
            by_hash = {}
            for a in root.get('Actors') or []:
                for key, v in (a.get('Dynamic') or {}).items():
                    if isinstance(v, str) and v in rows:
                        counts[key] = counts.get(key, 0) + 1
                        p = {'area': area, 'map': mapname, 'actor': a.get('Gyaml'), 'param': key}
                        if a.get('Name'):
                            p['name'] = a['Name']
                        placements.setdefault(v, []).append(p)
                        by_hash.setdefault(a.get('Hash'), []).append(p)
            for g in root.get('AiGroups') or []:
                lname = base(g.get('Logic'))
                if not lname:
                    continue
                reqs, plays = logic_requests(game, lname)
                for ev in plays:
                    played.setdefault(ev, [])
                    if lname not in played[ev]:
                        played[ev].append(lname)
                for ref in g.get('References') or []:
                    info = reqs.get(ref.get('Id'))
                    for p in by_hash.get(ref.get('Reference'), []) if info is not None else []:
                        p['logic'] = lname
                        p.update(info)
                        if not info.get('when'):
                            p['no_trigger'] = True
    return placements, counts, played


ACTOR_PARAM_SKIP = ('FmdbName', 'UserName', 'InvalidGameData')
EVENT_PATH = re.compile(r'Work/Event/EventSetting/([A-Za-z0-9_]+)\.engine__event__EventSettingParam\.gyml$')
TOKEN = re.compile(rb'[A-Za-z0-9_]{4,}')


def actor_events(game, rows):
    """Where the actors' own parameter files (Pack/Actor/<actor>.pack) name an event:
    {event: [{'file', 'param', 'actors'}]}. A file is only opened when the event's name is in its bytes."""
    names = {r.encode() for r in rows}
    found = {}

    def walk(v, path, parent, out):
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, path + [str(k)], v, out)
        elif isinstance(v, list):
            for x in v:
                walk(x, path, parent, out)
        elif isinstance(v, str):
            m = EVENT_PATH.match(v)
            name = m.group(1) if m else v
            if name in rows and path and path[-1] not in ACTOR_PARAM_SKIP:
                key = parent.get('BBKey') if isinstance(parent, dict) and path[-1] == 'InitValConverted' else None
                out.append((key or '.'.join(path), name))

    folder = os.path.join(game.romfs, 'Pack', 'Actor')
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith('.pack.zs'):
            continue
        data = game.read('Pack/Actor/' + fn)
        if not names.intersection(TOKEN.findall(data)):
            continue
        for inner, blob in sarc.Sarc.read(data).files.items():
            if not inner.endswith(('.bgyml', '.byml')) or not names.intersection(TOKEN.findall(blob)):
                continue
            try:
                root = byml.loads(blob).root
            except Exception:
                continue
            out = []
            walk(root, [], None, out)
            kind = inner.split('/')[-2] if '/' in inner else inner
            for param, name in out:
                found.setdefault((name, kind, param), [])
                actor = fn.split('.')[0]
                if actor not in found[(name, kind, param)]:
                    found[(name, kind, param)].append(actor)
    res = {}
    for (name, kind, param), actors in sorted(found.items()):
        d = {'file': kind, 'param': param, 'actors': actors[:6]}
        if len(actors) > 6:
            d['actors_more'] = len(actors) - 6
        res.setdefault(name, []).append(d)
    return res


def sequence_events(game, rows):
    """{event: [{'file', 'node'}]}: the game's sequence graphs (Sequence/*.ainb) that name an event"""
    res = {}
    folder = os.path.join(game.romfs, 'Sequence')
    for fn in sorted(os.listdir(folder)):
        if '.ainb' not in fn:
            continue
        doc = ainb.Ainb.read(game.read('Sequence/' + fn))
        for n in doc.nodes:
            for x in list(n.immediates['string']) + list(n.inputs['string']):
                if isinstance(x.value, str) and x.value in rows:
                    d = {'file': fn.split('.ainb')[0], 'node': n.name or n.type_name}
                    if d not in res.setdefault(x.value, []):
                        res[x.value].append(d)
    return res


def component_lists(game):
    """{list name: {'category', 'skip_disabled'}} with each list's parent followed"""
    folder = 'Event/EventSetting/EventSettingComponentList'
    raw = {}
    for fn in os.listdir(os.path.join(game.romfs, folder)):
        raw[fn.split('.')[0]] = game.doc(folder + '/' + fn)

    def resolve(name, depth=0):
        d = raw.get(name) or {}
        up = resolve(base(d['$parent']), depth + 1) if d.get('$parent') and depth < 8 else {}
        comps = dict(up.get('components') or {})
        comps.update(d.get('Components') or {})
        return {'category': d.get('Category') or up.get('category'), 'components': comps}

    out = {}
    for name in raw:
        r = resolve(name)
        out[name] = {'category': r['category'], 'skip_disabled': 'SkipSetting' in r['components']}
    return out


def check_links(root=ROOT):
    """{flow: [check]} from data/world/*.json: a location whose gift, cutscene or song data names the flow"""
    out = {}
    folder = os.path.join(root, 'data', 'world')
    for fn in sorted(os.listdir(folder)):
        if fn.startswith('_') or not fn.endswith('.json'):
            continue
        regions = json.load(open(os.path.join(folder, fn), encoding='utf-8'))
        for reg in regions if isinstance(regions, list) else []:
            for name, loc in (reg.get('locations') or {}).items():
                for key in ('gift', 'cutscene', 'song'):
                    d = loc.get(key)
                    if isinstance(d, dict) and d.get('flow'):
                        c = {'name': name}
                        if loc.get('id'):
                            c['id'] = loc['id']
                        out.setdefault(d['flow'], []).append(c)
    return out


def area_of_name(name):
    for prefix, area in NAME_AREA:
        if name.startswith(prefix):
            return area
    return None


def build(romfs, root=ROOT):
    game = Game(romfs)
    rows = {r['__RowId']: r for r in game.rsdb('EventSetting')}
    analysed = {r['__RowId']: r for r in game.rsdb('GameAnalyzedEventInfo')}
    banc_area = {r['__RowId']: r['BancMain'].split('/')[3] for r in game.rsdb('GameBancInfo')}
    base_setting = {base(r['__RowId']): base((r.get('MayaLocationParam') or {}).get('BancParamName'))
                    for r in game.rsdb('GameEventBaseSetting')}
    lists = component_lists(game)
    texts = game.texts()
    loc_names = {k: v.rstrip('\x00') for k, v in msbt.Msbt.read(texts['LocationMsg/Location.msbt']).texts.items()}
    item_names = {}
    for k, v in msbt.Msbt.read(texts['ActorMsg/PouchContent.msbt']).texts.items():
        if k.endswith('_Name'):
            item_names[k[:-5]] = ''.join(x for x in msbt.tags(v) if isinstance(x, str)).rstrip('\x00')
    message_counts = {n[len('EventFlowMsg/'):-5]: len(msbt.Msbt.read(d).texts) for n, d in texts.items()
                      if n.startswith('EventFlowMsg/')}
    checks = check_links(root)
    movies = {}
    for fn in sorted(os.listdir(os.path.join(romfs, 'Event', 'Movie'))):
        if fn.endswith('.webm'):
            movies[fn[:-5]] = movie_seconds(os.path.join(romfs, 'Event', 'Movie', fn))

    # ---- which flow and entry point each event runs
    def entry_of(row):
        name = base(row.get('FlowchartFileName'))
        flow = game.flow(name) if name else None
        if flow is None or not flow.flowcharts:
            return name or None, None
        fc = flow.flowchart
        eps = [ep.name for ep in fc.entry_points]
        for want in (row.get('EntryPointName'), row['__RowId'], 'EntryPoint0'):
            if want and want in eps:
                return name, want
        return name, (eps[0] if eps and not row.get('EntryPointName') else None)

    entries = {rid: entry_of(r) for rid, r in rows.items()}
    by_entry = {}
    for rid, (fname, ep) in entries.items():
        if ep is not None:
            by_entry.setdefault((fname, ep), []).append(rid)

    facts = {}

    def facts_of(fname, ep):
        if (fname, ep) not in facts:
            fc = game.flow(fname).flowchart
            facts[(fname, ep)] = flow_facts(fc, fc.entry_point(ep).main)
        return facts[(fname, ep)]

    # ---- what starts each event: other events, by a transition step or after a change of map
    starters = {}

    def add_starter(event, s):
        lst = starters.setdefault(event, [])
        if s not in lst:
            lst.append(s)

    played_in_flows = {}
    for fname in sorted(game.flow_files):
        flow = game.flow(fname)
        for fc in flow.flowcharts:
            covered = set()
            order = sorted(fc.entry_points, key=lambda ep: (fname, ep.name) not in by_entry)
            for ep in order:
                f = facts_of(fname, ep.name)
                owners = by_entry.get((fname, ep.name), [])
                for ev in f['played_checks']:
                    if ev:
                        lst = played_in_flows.setdefault(ev, [])
                        if fname not in lst:
                            lst.append(fname)
                for kind, names in (('transition', f['next']),
                                    ('after_warp', [w.get('then_event') for w in f['warps']])):
                    for ev in names:
                        if not isinstance(ev, str) or ev not in rows:
                            continue
                        if owners:
                            covered.add((kind, ev))
                            for o in owners:
                                if o != ev:
                                    add_starter(ev, {'event': o, 'how': kind})
                        elif (kind, ev) not in covered:
                            add_starter(ev, {'flow': fname, 'entry': ep.name, 'how': kind})

    placements, param_counts, played_in_logic = map_events(game, rows)
    in_actors = actor_events(game, rows)
    in_sequences = sequence_events(game, rows)

    # ---- which events are listed
    def klass(rid):
        if rid.startswith(SYSTEM_PREFIXES):
            return 'system'
        if rid.startswith(('Dm_', 'DmF_')):
            return 'story'
        return None

    listed = {rid: klass(rid) for rid in rows if klass(rid)}
    for rid in rows:
        if rid in listed:
            continue
        fname, ep = entries[rid]
        if ep is not None and any(listed.get(n) == 'story' for n in facts_of(fname, ep)['next']):
            listed[rid] = 'lead-in'
    for rid, ps in placements.items():
        if rid not in listed and any(p['param'] in REQUEST_PARAMS for p in ps):
            listed[rid] = 'small'

    folders = set(banc_area.values())

    def area_for(rid, seen=()):
        """(area, where it is read from). In order: a place of its own inside a bigger map, by the cutscene's
        name (Lake Hylia, Lon Lon Ranch and the Temple of Time have no map folder of their own); the map of
        the event's settings; the maps it is placed in; its name; the event that starts it; the cutscene it
        runs."""
        row = rows[rid]
        if rid.startswith(NO_AREA):
            return None, None
        named = area_of_name(rid)
        if named and named not in folders:
            return named, 'name'
        banc = base_setting.get(base(row.get('EventBaseSetting')))
        if banc and banc_area.get(banc):
            return banc_area[banc], 'event settings'
        ps = placements.get(rid)
        if ps:
            areas = sorted({p['area'] for p in ps},
                           key=lambda a: (a != named, a == 'DreamWorld', -len([p for p in ps if p['area'] == a]), a))
            return areas[0], 'map'
        if named:
            return named, 'name'
        if rid not in seen:
            for s in starters.get(rid, []):
                if s.get('event'):
                    a = area_for(s['event'], seen + (rid,))
                    if a[0]:
                        return a[0], 'starter'
            fname, ep = entries[rid]
            for n in (facts_of(fname, ep)['next'] if ep is not None else []):
                if isinstance(n, str) and n in rows and n != rid:
                    a = area_for(n, seen + (rid,))
                    if a[0]:
                        return a[0], 'the cutscene it runs'
        return None, None

    out = []
    used_files = set()
    for rid in sorted(listed):
        row = rows[rid]
        an = analysed.get(rid, {})
        fname, ep = entries[rid]
        comp = lists.get(base(row.get('EventSettingComponentList')), {})
        area, area_from = area_for(rid)
        e = {'name': rid, 'class': listed[rid], 'area': area,
             'area_name': loc_names.get(area) or AREA_NAME_MISSING.get(area), 'area_from': area_from,
             'settings': base(row.get('EventSettingComponentList')), 'can_skip': not comp.get('skip_disabled')}
        # a movie cutscene's own timeline is its TimelineFileNameSyncMovie (Dm_FinalBattle_0002 also names an
        # empty one, Dm_FinalBattle_0000, as its TimelineFileName)
        sync = base(row.get('TimelineFileNameSyncMovie'))
        tl_name = sync if sync in game.flow_files else base(row.get('TimelineFileName'))
        tl_flow = game.flow(tl_name) if tl_name else None
        files = []
        if tl_flow is not None and tl_flow.timelines:
            tl = tl_flow.timeline
            subs = [base(row.get('TimelineFileName'))] if base(row.get('TimelineFileName')) not in ('', tl_name) else []
            for s in row.get('SubTimelineNames') or []:
                subs.append(base(s))
            for s in tl.subtimelines:
                if s not in subs:
                    subs.append(s)
            files = [tl_name] + [s for s in subs if s in game.flow_files]
            missing = [s for s in subs if s not in game.flow_files]
            voices = sum(1 for c in tl.clips if tl.clip_names(c)[1] == 'EventStartVoice')
            e.update({'kind': 'timeline', 'frames': int(tl.duration), 'seconds': round(tl.duration / FPS, 1),
                      'cuts': len(tl.cuts), 'cut_starts': [int(c.start) for c in tl.cuts], 'clips': len(tl.clips),
                      'voice_lines': voices})
            # the one thing a timeline of the game sets: the time of day (5 timelines)
            for name in files:
                for c in game.flow(name).timeline.clips:
                    if game.flow(name).timeline.clip_names(c)[1] == 'EventTrigger_SetTime':
                        item = {'time': '%02d:%02d' % ((c.params or {}).get('TimeHour', 0),
                                                       (c.params or {}).get('TimeMin', 0)), 'at_frame': int(c.start)}
                        if item not in e.setdefault('sets', []):
                            e['sets'].append(item)
            if missing:
                e['sub_timelines_missing'] = missing
            shows = sorted({a.name for a in tl.actors
                            if a.name.startswith(('Item_', 'Weapon_', 'Armor_')) or a.name == 'Obj_Heart_Container'})
            if shows:
                e['shows'] = shows
            if base(row.get('TimelineFileNameSyncMovie')) and row.get('MovieFileName') in movies:
                e['kind'] = 'movie'
                e['movie'] = row['MovieFileName']
                e['movie_seconds'] = movies[row['MovieFileName']]
        elif row.get('MovieFileName') in movies and (ep is None or an.get('ExistMovie')):
            e.update({'kind': 'movie', 'movie': row['MovieFileName'], 'movie_seconds': movies[row['MovieFileName']],
                      'seconds': movies[row['MovieFileName']]})
        if ep is not None and fname != 'DefaultParentEvent' and e.get('kind') != 'timeline':
            f = facts_of(fname, ep)
            files = [fname]
            e.setdefault('kind', 'flowchart')
            e.update({'flow': fname, 'entry': ep, 'steps': f['steps'], 'wait_frames': f['wait_frames'],
                      'message_windows': f['talks_longest']})
            for key in ('sets', 'gives', 'next', 'warps', 'reads', 'shows'):
                if f[key]:
                    e[key] = f[key]
        elif 'kind' not in e:
            e['kind'] = 'unknown'
            if fname:
                e['flow'] = fname
            e['note'] = 'its flow file %s is not in the game' % fname if fname and fname not in game.flow_files \
                else 'no flow or timeline of its own (it names the flow %s and no entry point)' % fname
        for g in e.get('gives', []):
            if isinstance(g.get('item'), str) and g['item'] in item_names:
                g['name'] = item_names[g['item']]
        e['files'] = files
        used_files.update(files)
        msgs = message_counts.get(files[0]) if files and files[0].startswith(('Dm_', 'DmF_')) else None
        if msgs:
            e['text_lines'] = msgs
        st = []
        for s in starters.get(rid, []):
            st.append(dict(s))
        for p in placements.get(rid, []):
            st.append(dict(p, how='map'))
        for a in in_actors.get(rid, []):
            st.append(dict(a, how='actor'))
        for q in in_sequences.get(rid, []):
            st.append(dict(q, how='sequence'))
        if not st and (e['settings'] or '').startswith('NPC'):
            st.append({'how': 'npc', 'settings': e['settings']})
        if st:
            e['started_by'] = st
        tested = sorted(played_in_logic.get(rid, [])) + ['flow ' + x for x in sorted(played_in_flows.get(rid, []))]
        if tested:
            e['played_tested_by'] = tested
        for f2 in files[:1]:
            if f2 in checks:
                e['checks'] = checks[f2]
        out.append(e)

    dm_files = sorted(n for n in game.flow_files if n.startswith(('Dm_', 'DmF_')))
    others = []
    callers = {}
    for (fname, ep), f in facts.items():
        for c in f['calls']:
            callers.setdefault(c.split('<')[0], set()).add(fname)
    for n in dm_files:
        if n in used_files:
            continue
        flow = game.flow(n)
        o = {'file': n, 'kind': 'timeline' if flow.timelines else 'flowchart'}
        if flow.timelines:
            o['frames'] = int(flow.timeline.duration)
            parent = re.sub(r'_(Effect|Env)$', '', n)
            o['note'] = ('sub-timeline of %s, which no event row names' % parent) if parent != n \
                else 'a timeline no event row names'
        else:
            o['entry_points'] = [ep.name for ep in flow.flowchart.entry_points]
            cs = sorted(callers.get(n, ()))
            o['called_by'] = cs[:8]
            if len(cs) > 8:
                o['called_by_more'] = len(cs) - 8
            o['note'] = 'no event row of its own: run as a step of other flows' if cs \
                else 'no event row of its own and no flow calls it'
        others.append(o)

    area_names = {a: loc_names.get(a) or AREA_NAME_MISSING.get(a) for a in sorted({e['area'] for e in out if e['area']})}
    return {
        '_about': 'Every cutscene of the game, read from its files by tools/cutscene_list.py (do not edit by '
                  'hand: run the tool again). See docs/CUTSCENES.md for how to read it.',
        'frames_per_second': FPS,
        'counts': {
            'events_in_the_game': len(rows),
            'flow_files': len(game.flow_files),
            'cutscene_flow_files': len(dm_files),
            'cutscene_flow_files_in_an_entry': len([n for n in dm_files if n in used_files]),
            'story': len([e for e in out if e['class'] == 'story']),
            'system': len([e for e in out if e['class'] == 'system']),
            'lead_in': len([e for e in out if e['class'] == 'lead-in']),
            'small': len([e for e in out if e['class'] == 'small']),
            'map_event_parameters': dict(sorted(param_counts.items())),
        },
        'areas': area_names,
        'cutscenes': out,
        'other_files': others,
    }


# ================================================================================================ the document
def mmss(seconds):
    seconds = float(seconds)
    if seconds < 60:
        return '%.1f s' % seconds
    return '%d min %02d s' % divmod(round(seconds), 60)


def length_text(e):
    if e['kind'] in ('timeline', 'movie') and 'frames' in e:
        t = '%s (%d frames)' % (mmss(e['seconds']), e['frames'])
        if e['kind'] == 'movie':
            t += ', movie file %s' % mmss(e['movie_seconds'])
        return t
    if e['kind'] == 'movie':
        return '%s (movie file)' % mmss(e['movie_seconds'])
    if e['kind'] == 'flowchart':
        frames = e['wait_frames']
        t = 'waits %s' % ('none' if not frames else '%d frames' % frames if frames < 6 else mmss(frames / FPS))
        if e.get('message_windows'):
            t += ' + %d text window%s' % (e['message_windows'], '' if e['message_windows'] == 1 else 's')
        return t
    return '?'


def set_text(s):
    if 'flag' in s:
        if 'add' in s:
            return '`%s` %+g' % (s['flag'], s['add']) if isinstance(s['add'], (int, float)) \
                else '`%s` + %s' % (s['flag'], s['add'])
        v = s['value']
        v = {True: 'true', False: 'false'}.get(v, v) if isinstance(v, bool) else v
        return '`%s` = %s' % (s['flag'], v)
    if 'challenge' in s:
        return 'challenge `%s` %s `%s`' % (s['challenge'], 'back to' if s.get('rollback') else 'to', s['step'])
    if 'event_bool' in s:
        return '%s of its %s = %s' % (s['event_bool'], s['of'], str(s['value']).lower())
    if 'time' in s:
        return 'time of day %s%s' % (s['time'], ' (at frame %d)' % s['at_frame'] if 'at_frame' in s else '')
    if 'location_title' in s:
        return 'shows the title of `%s`' % s['location_title']
    if 'autosave' in s:
        return 'autosave'
    return json.dumps(s)


def gives_text(gives, steps=False):
    """the items of a list of gives, each once (the window and the adding are two steps of one gift)"""
    out, by = [], {}
    for g in gives:
        t = give_text(g)
        if t not in out:
            out.append(t)
        by.setdefault(t, []).append(g['by'])
    if steps:
        out = ['%s (step%s %s)' % (t, 's' if len(by[t]) > 1 else '', ', '.join('`%s`' % b for b in by[t]))
               for t in out]
    return ', '.join(out)


def give_text(g):
    if 'rupees' in g:
        return '%s rupees' % g['rupees']
    if 'hearts_refilled' in g:
        return 'refills hearts'
    t = '`%s`' % g['item']
    if g.get('name'):
        t = '%s (%s)' % (g['name'], t)
    if isinstance(g.get('count'), int) and g['count'] != 1:
        t += ' x%d' % g['count']
    return t


def starter_text(s, by_name):
    if s['how'] == 'map':
        maps = s.get('maps') or [s['map']]
        t = '%s `%s` in map%s %s' % ('entrance' if s['param'] == 'InitEventName' else 'placed', s['actor'],
                                    '' if len(maps) == 1 else 's', ', '.join('`%s`' % m for m in maps))
        if s['param'] not in REQUEST_PARAMS:
            t += ' (as its %s)' % s['param']
        if s.get('when'):
            t += '; starts when: %s' % s['when']
        if s.get('there'):
            t += '; there while: %s' % s['there']
        if s.get('gone'):
            t += '; gone once: %s' % s['gone']
        if s.get('no_trigger'):
            t += '; its logic graph gives it no trigger of its own'
        if s.get('logic'):
            t += ' (`Logic/%s`%s)' % (s['logic'], ', in its module `%s`' % s['module']
                                      if isinstance(s.get('module'), str) else '')
        for k, v in sorted((s.get('after') or {}).items()):
            t += '; on its %s the logic sets: %s' % (k, ', '.join(v))
        return t
    if s['how'] == 'actor':
        actors = ', '.join('`%s`' % a for a in s['actors']) + (' and %d more' % s['actors_more']
                                                               if s.get('actors_more') else '')
        return 'the actor%s %s (parameter `%s` of its %s)' % ('' if len(s['actors']) == 1 else 's', actors,
                                                              s['param'], s['file'])
    if s['how'] == 'sequence':
        return 'the game\'s sequence graph `Sequence/%s` (node `%s`)' % (s['file'], s['node'])
    if s['how'] == 'npc':
        return 'the NPC whose flow it is, when Link %s (settings list `%s`; the condition is in the NPC\'s ' \
               'own program)' % ('talks to it' if 'Talk' in s['settings'] else 'comes near', s['settings'])
    how = 'run by' if s['how'] == 'transition' else 'started after the change of map of'
    if s.get('event'):
        p = by_name.get(s['event'])
        where = ' (flow `%s`, entry `%s`)' % (p['flow'], p['entry']) if p and p.get('flow') else ''
        return '%s the event `%s`%s' % (how, s['event'], where)
    return '%s flow `%s`, entry `%s`' % (how, s['flow'], s['entry'])


def merged_starters(st):
    """map placements that differ only in the map (child and adult) as one, with the maps listed"""
    out = []
    for s in st:
        if s['how'] == 'map':
            key = {k: v for k, v in s.items() if k not in ('map', 'area', 'name')}
            for o in out:
                if o.get('_key') == key:
                    if s['map'] not in o['maps']:
                        o['maps'].append(s['map'])
                    break
            else:
                out.append(dict(s, maps=[s['map']], _key=key))
        else:
            out.append(s)
    return out


def cut_text(t, n):
    return t if len(t) <= n else t[:n] + ' ... (the rest: data/cutscenes.json)'


def md_escape(t):
    return str(t).replace('|', '\\|')


def render(data):
    cs = data['cutscenes']
    by_name = {e['name']: e for e in cs}
    c = data['counts']
    L = []
    w = L.append
    w('# The cutscene list')
    w('')
    w('Every cutscene of the game, read from its files by `tools/cutscene_list.py` (roadmap phase 1, for decision')
    w('15: cutscenes skippable, shortened or removed). **Made by the tool: do not edit this file by hand,** run')
    w('`python tools/cutscene_list.py "<romfs>"` again. The same list as data is `data/cutscenes.json`.')
    w('`tests/cutscene_list_check.py` reads the game\'s files again and fails when either file is out of date.')
    w('')
    w('## What is in it')
    w('')
    w('| | |')
    w('|---|---|')
    w('| Events in the game (`RSDB/EventSetting`) | %d |' % c['events_in_the_game'])
    w('| Event flow files (`Event/EventFlow`) | %d, %d of them cutscene files (`Dm_...`, `DmF_...`) |'
      % (c['flow_files'], c['cutscene_flow_files']))
    w('| **Story cutscenes** (events named `Dm_...`) | **%d** |' % c['story'])
    w('| Lead-in events (not `Dm_`, they run a story cutscene as a step) | %d |' % c['lead_in'])
    w('| Small scenes (not `Dm_`, placed in a map: a door opens, a chest appears, Navi speaks) | %d |' % c['small'])
    w('| System scenes (`Dm_SY_...`: getting an item, opening a chest, the ocarina, changing map) | %d |' % c['system'])
    w('| Cutscene files that belong to one of these events | %d of %d (the rest: "Cutscene files without an event" below) |'
      % (c['cutscene_flow_files_in_an_entry'], c['cutscene_flow_files']))
    w('')
    w('## How to read an entry')
    w('')
    w('- **Kind.** *timeline*: a fixed film (camera, animations, voices on a time track; files `<name>`,')
    w('  `<name>_Effect`, `<name>_Env`). *movie*: a video file (`Event/Movie/<name>.webm`), with a timeline beside it')
    w('  for sound. *flowchart*: a list of steps (walk here, say this, wait, give that).')
    w('- **Length.** A timeline\'s length is in its file, in frames; **60 frames are one second** (12 movie')
    w('  cutscenes have a timeline beside their video file, and for 11 of them it is as long as the video to')
    w('  within 2%: e.g. `Dm_Kokiri_0095`, 7040 frames, video 117.33 s; the exception is `Dm_FinalBattle_0002`,')
    w('  1732 frames, video 33.0 s). A flowchart has no length: "waits" is the time of its wait steps on its longest')
    w('  path, **at 60 frames a second, which is not checked in game for flowcharts**; animations, camera moves and')
    w('  the player reading text come on top. So for a flowchart it is the least it can take, not its length.')
    w('- **Sets / gives.** Only a flowchart can set a flag or give an item: no timeline in the game has a step')
    w('  that does (the 261 timeline files hold camera, animation, sound, light and effect steps; the one thing')
    w('  a few of them set is the time of day). What a timeline cutscene "sets" is set by the event that runs it,')
    w('  listed under **Started by** and under the area\'s lead-in events. Flags are GameData names; "challenge"')
    w('  is the game\'s quest step (`RSDB/Challenge`). "On its EventFinish the logic sets" = the map\'s logic')
    w('  graph sets it when the event ends, not the event itself.')
    w('- **Played.** The game also remembers for every event that it has been played (`HavePlayedEvent.<event>`).')
    w('  "Played is tested by" names the logic graphs and flows that ask for it: removing or skipping such a')
    w('  cutscene has to keep that answer true.')
    w('- **Can be skipped.** "no" = the event\'s settings list has `DisableSkip`. Everything else can be skipped')
    w('  by the game\'s own skip (not tried for each one in game).')
    w('- **Started by.** Another event (a transition step), or an actor in a map. For an `EventRequestActor`')
    w('  the condition is read from the logic graph of its group; `Area_xxxx`, `EventRequestActor_xxxx` are the')
    w('  names of that graph\'s actors.')
    w('')
    areas = [a for a in AREA_ORDER if a in data['areas']] + sorted(a for a in data['areas'] if a not in AREA_ORDER)

    def area_title(a):
        if a is None:
            return 'No single area (title screen, credits, Great Fairies, the Sun\'s Song)'
        name = data['areas'].get(a)
        return '%s (`%s`)' % (name, a) if name else '`%s`' % a

    # ---- by area
    w('## Overview by area')
    w('')
    w('| Area | Story cutscenes | of them timelines and movies, total length | Lead-in events | Small scenes |')
    w('|---|---|---|---|---|')
    by_area = {}
    for e in cs:
        if e['class'] != 'system':
            by_area.setdefault(e['area'], {}).setdefault(e['class'], []).append(e)
    order = [a for a in areas + [None] if a in by_area]
    for a in order:
        g = by_area[a]
        st = g.get('story', [])
        tls = [e for e in st if e['kind'] in ('timeline', 'movie')]
        w('| %s | %d | %d, %s | %d | %d |' % (area_title(a), len(st), len(tls),
                                           mmss(sum(e['seconds'] for e in tls)) if tls else '0',
                                           len(g.get('lead-in', [])), len(g.get('small', []))))
    tls = [e for e in cs if e['class'] == 'story' and e['kind'] in ('timeline', 'movie')]
    w('| **All** | **%d** | **%d, %s** | **%d** | **%d** |' % (c['story'], len(tls), mmss(sum(e['seconds'] for e in tls)),
                                                            c['lead_in'], c['small']))
    w('')
    for a in order:
        g = by_area[a]
        w('## %s' % area_title(a))
        w('')
        es = g.get('story', [])
        if es:
            w('### Story cutscenes (%d)' % len(es))
            w('')
            w('| Cutscene | Kind | Length | Text lines | Can be skipped | Gives | Check |')
            w('|---|---|---|---|---|---|---|')
            for e in es:
                w('| `%s` | %s | %s | %s | %s | %s | %s |' % (
                    e['name'], e['kind'], length_text(e), e.get('text_lines', ''),
                    'yes' if e['can_skip'] else '**no**', md_escape(gives_text(e.get('gives', []))),
                    md_escape(', '.join(x.get('id') or x['name'] for x in e.get('checks', [])))))
            w('')
            for e in es:
                lines = detail_lines(e, by_name)
                if lines:
                    w('**`%s`**' % e['name'])
                    for l in lines:
                        w('- ' + l)
                    w('')
        es = g.get('lead-in', [])
        if es:
            w('### Lead-in events (%d)' % len(es))
            w('')
            w('Not cutscene files themselves: they run a story cutscene as one of their steps. What they set before')
            w('and after it is what the cutscene "sets".')
            w('')
            for e in es:
                w('**`%s`** (flow `%s`, entry `%s`; %s)' % (e['name'], e.get('flow'), e.get('entry'), length_text(e)))
                for l in detail_lines(e, by_name):
                    w('- ' + l)
                w('')
        es = g.get('small', [])
        if es:
            w('### Small scenes (%d)' % len(es))
            w('')
            w('Flowchart events placed in the map that are not `Dm_` files: the camera shows a door opening or a')
            w('chest appearing, Navi says a line, a room\'s enemies appear.')
            w('')
            w('| Scene | Flow, entry | Length | Sets / gives | Starts when |')
            w('|---|---|---|---|---|')
            for e in es:
                sets = [set_text(x) for x in e.get('sets', []) if 'event_bool' not in x]
                if e.get('gives'):
                    sets.append('gives ' + gives_text(e['gives']))
                sets += ['then `%s`' % n for n in e.get('next', [])]
                whens = []
                for x in e.get('started_by', []):
                    if x['how'] == 'map':
                        for k, v in sorted((x.get('after') or {}).items()):
                            t = 'on its %s the logic sets: %s' % (k, ', '.join(v))
                            if t not in sets:
                                sets.append(t)
                        if x.get('when') and x['when'] not in whens:
                            whens.append(x['when'])
                when = ' // '.join(whens)
                w('| `%s` | `%s`, `%s` | %s | %s | %s |' % (
                    e['name'], e.get('flow'), e.get('entry'), length_text(e), md_escape('; '.join(sets)),
                    md_escape(cut_text(when, 500))))
            w('')

    # ---- system
    w('## System scenes')
    w('')
    w('`Dm_SY_...` events: the game\'s own pieces for getting an item, opening a chest, the ocarina, changing map,')
    w('game over. They are run as steps of other events, not placed in maps.')
    w('')
    w('| Scene | Kind | Flow, entry | Length | Sets / gives |')
    w('|---|---|---|---|---|')
    for e in cs:
        if e['class'] != 'system':
            continue
        sets = [set_text(x) for x in e.get('sets', [])]
        if e.get('gives'):
            sets.append('gives ' + gives_text(e['gives']))
        w('| `%s` | %s | `%s`, `%s` | %s | %s |' % (e['name'], e['kind'], e.get('flow', ''), e.get('entry', ''),
                                                 length_text(e),
                                                 md_escape(cut_text('; '.join(sets), 300))))
    w('')

    # ---- other files
    w('## Cutscene files without an event')
    w('')
    w('`Dm_...` flow files that no row of `RSDB/EventSetting` names as its flow or timeline.')
    w('')
    w('| File | Kind | Note |')
    w('|---|---|---|')
    for o in data['other_files']:
        note = o['note']
        if o.get('called_by'):
            note += ': ' + ', '.join('`%s`' % x for x in o['called_by'])
            if o.get('called_by_more'):
                note += ' and %d more' % o['called_by_more']
        if 'frames' in o:
            note += ' (%d frames)' % o['frames']
        w('| `%s` | %s | %s |' % (o['file'], o['kind'], note))
    w('')
    w('## Event names on other map actors')
    w('')
    w('Besides `RequestEventName` and `InitEventName` (the scenes above), map actors name events in these')
    w('parameters for their own work (a door\'s opening, a chest\'s get scene, a Navi hint, a scrub\'s talk).')
    w('They are not listed one by one.')
    w('')
    w('| Parameter | Times used in the maps |')
    w('|---|---|')
    for k, v in sorted(c['map_event_parameters'].items(), key=lambda x: -x[1]):
        w('| `%s` | %d |' % (k, v))
    w('')
    return '\n'.join(L)


def detail_lines(e, by_name):
    lines = []
    if e['kind'] in ('timeline', 'movie') and 'frames' in e:
        t = 'Files: ' + ', '.join('`%s`' % f for f in e['files'])
        t += '; %d cuts, %d steps on the time track, %d voice lines' % (e['cuts'], e['clips'], e['voice_lines'])
        if e.get('sub_timelines_missing'):
            t += '; named but not in the game: ' + ', '.join('`%s`' % f for f in e['sub_timelines_missing'])
        lines.append(t)
    elif e['kind'] == 'flowchart' and e['class'] == 'story':
        lines.append('Flow `%s`, entry `%s`: %d steps' % (e['flow'], e['entry'], e['steps']))
    if e.get('note'):
        lines.append('Note: ' + e['note'])
    if e.get('shows'):
        lines.append('Shows the item actors: ' + ', '.join('`%s`' % s for s in e['shows']))
    st = merged_starters(e.get('started_by', []))
    if st:
        shown = [starter_text(s, by_name) for s in st[:6]]
        lines.append('Started by: ' + ' // '.join(shown) + (' // and %d more' % (len(st) - 6) if len(st) > 6 else ''))
    elif e['class'] in ('story', 'lead-in'):
        lines.append('Started by: **not found** in the flows, the maps, the actors\' parameter files or the '
                     'sequence graphs (most likely the game\'s program)')
    sets = [set_text(s) for s in e.get('sets', [])]
    if sets:
        lines.append('Sets: ' + '; '.join(sets))
    elif e['kind'] in ('timeline', 'movie'):
        lead = [s['event'] for s in st if s.get('event') and by_name.get(s['event'], {}).get('sets')]
        if lead:
            lines.append('Sets: nothing itself; see ' + ', '.join('`%s`' % x for x in lead))
    if e.get('gives'):
        lines.append('Gives: ' + gives_text(e['gives'], steps=True))
    if e.get('next'):
        lines.append('Then runs: ' + ', '.join('`%s`' % n for n in e['next']))
    for wp in e.get('warps', []):
        t = 'Then changes map' + (' to `%s`' % wp['map'] if wp.get('map') else '')
        if wp.get('at'):
            t += ' at `%s`' % wp['at']
        if wp.get('then_event'):
            t += ', where `%s` starts' % wp['then_event']
        lines.append(t)
    if e.get('played_tested_by'):
        p = e['played_tested_by']
        lines.append('Played is tested by: ' + ', '.join('`%s`' % x for x in p[:8])
                     + (' and %d more' % (len(p) - 8) if len(p) > 8 else ''))
    if e.get('checks'):
        lines.append('Check: ' + ', '.join('%s%s' % (x['name'], ' (`%s`)' % x['id'] if x.get('id') else '')
                                           for x in e['checks']))
    return lines


def dump_json(data):
    return json.dumps(data, indent=1, ensure_ascii=False) + '\n'


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 2
    romfs = argv[0]
    data = build(romfs)
    if len(argv) >= 3 and argv[1] == '--show':
        for e in data['cutscenes']:
            if e['name'] == argv[2]:
                print(json.dumps(e, indent=1, ensure_ascii=False))
        return 0
    with open(DATA_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(dump_json(data))
    with open(DOC_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(render(data) + '\n')
    print(json.dumps(data['counts'], indent=1))
    print('wrote %s and %s' % (os.path.relpath(DATA_FILE, ROOT), os.path.relpath(DOC_FILE, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
