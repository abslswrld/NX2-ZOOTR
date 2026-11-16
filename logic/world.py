"""The region map: loads data/world/*.json, data/helpers.json and data/checks/*.json, and works out what
is reachable with a given set of items and settings, for child and adult separately (like the N64
randomizer's logic).

World file format (one per area), a list of regions:
    {
      "region": "KF Main",                 unique name
      "scene": "KokiriForest",             the game's map (Banc folder)
      "time_passes": true,                 day and night happen here (for at_night)
      "verified": false,                   rules checked in game yet?
      "notes": "...",
      "locations": {                       checks in this region
          "KF Kokiri Sword Chest": {"spot": "chest@-82.5,33.0", "rule": "is_child"}
      },
      "events": {"Showed Mido Sword and Shield": "is_child and KokiriSword and DekuShield"},
      "exits": {"KF Outside Deku Tree": "is_adult or open_forest or 'Showed Mido Sword and Shield'"}
    }
A location's "rule" may be left out (= True). A gift (no map placement) may give "pos": where its NPC
stands, for maps and the tracker. A check that the game places in two maps (the remake models
some edges twice, e.g. the bridge to Hyrule Field in both Kokiri Forest and the Lost Woods) lists the
other copies in "also": [{"scene": "LostWood", "spot": "chest@-49.5,72.0"}]; both get the same item. An exit to a region that isn't mapped yet points at
"<Area> (not mapped yet)" regions declared in data/world/_unmapped.json.
"""
import collections
import json
import os

from . import rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')


class Region:
    def __init__(self, d, source):
        self.name = d['region']
        self.scene = d.get('scene')
        self.time_passes = d.get('time_passes', False)
        self.verified = d.get('verified', False)
        self.unmapped = d.get('unmapped', False)
        self.notes = d.get('notes', '')
        self.source = source
        self.locations = {}
        self.events = {}
        self.exits = {}
        for name, loc in (d.get('locations') or {}).items():
            if isinstance(loc, str):
                loc = {'rule': loc}
            rule = loc.get('rule', True)
            if loc.get('age') in ('child', 'adult'):
                # a check for one age's object only (the child and adult maps place separate objects)
                rule = 'is_%s' % loc['age'] if rule is True else 'is_%s and (%s)' % (loc['age'], rule)
                loc = dict(loc, rule=rule)
            self.locations[name] = dict(loc, rule_fn=rules.compile_rule(rule, name))
        for name, r in (d.get('events') or {}).items():
            self.events[name] = (r, rules.compile_rule(r, name))
        for target, r in (d.get('exits') or {}).items():
            self.exits[target] = (r, rules.compile_rule(r, '%s -> %s' % (self.name, target)))


class State:
    def __init__(self, items=(), settings=None):
        self.items = collections.Counter(items)
        self.settings = dict(settings or {})

    def count(self, name):
        return self.items.get(name, 0)

    def copy(self):
        s = State(settings=self.settings)
        s.items = collections.Counter(self.items)
        return s


class World:
    def __init__(self, data_dir=DATA):
        self.regions = {}
        self.checks = {}             # scene -> {spot id -> spot}
        helpers_src = json.load(open(os.path.join(data_dir, 'helpers.json'), encoding='utf-8'))
        self.helper_text = {k: v['rule'] if isinstance(v, dict) else v for k, v in helpers_src.items()
                            if not k.startswith('_')}
        self.helpers = {k: rules.compile_rule(v, 'helper ' + k) for k, v in self.helper_text.items()}
        wdir = os.path.join(data_dir, 'world')
        for fn in sorted(os.listdir(wdir)):
            if fn.endswith('.json'):
                for d in json.load(open(os.path.join(wdir, fn), encoding='utf-8')):
                    if d['region'] in self.regions:
                        raise ValueError('region %r defined twice' % d['region'])
                    self.regions[d['region']] = Region(d, fn)
        cdir = os.path.join(data_dir, 'checks')
        if os.path.isdir(cdir):
            for fn in sorted(os.listdir(cdir)):
                if fn.endswith('.json'):
                    self.checks[fn[:-5]] = json.load(open(os.path.join(cdir, fn), encoding='utf-8'))
        self.settings_defaults = json.load(open(os.path.join(data_dir, 'settings.json'), encoding='utf-8'))

    # ------------------------------------------------------------------ checking the data
    def problems(self):
        """Mistakes in the data files: unknown exits, spots that don't exist, names nobody defines."""
        out = []
        known_events = {e for r in self.regions.values() for e in r.events}
        items = set(json.load(open(os.path.join(DATA, 'items.json'), encoding='utf-8')))
        builtins = {'is_child', 'is_adult', 'at_night', 'True', 'False'}
        settings = set(self.settings_defaults)

        def check_names(text, where):
            for n in rules.names_in(text):
                if n in builtins or n in self.helpers or n in settings or n in items or n in known_events:
                    continue
                out.append('%s: unknown name %r' % (where, n))

        for k, t in self.helper_text.items():
            check_names(t, 'helper ' + k)
        for r in self.regions.values():
            for t, (txt, _) in r.exits.items():
                if t not in self.regions:
                    out.append('%s: exit to unknown region %r' % (r.name, t))
                check_names(txt, '%s -> %s' % (r.name, t))
            for n, (txt, _) in r.events.items():
                check_names(txt, '%s event %s' % (r.name, n))
            for n, loc in r.locations.items():
                check_names(loc.get('rule', True), '%s: %s' % (r.name, n))
                if 'age' in loc and loc['age'] not in ('child', 'adult'):
                    out.append('%s: %s has age %r (child or adult)' % (r.name, n, loc['age']))
                for scene, spot in self.spots_of(r, loc):
                    if spot not in self.checks.get(scene, {}):
                        out.append('%s: %s points at unknown spot %s %r' % (r.name, n, scene, spot))
                    elif loc.get('age') and not any(loc['age'] in p['ages']
                                                    for p in self.checks[scene][spot]['placements']):
                        out.append('%s: %s: spot %s has no %s object' % (r.name, n, spot, loc['age']))
        # every object (placement) belongs to at most one location
        placed = collections.Counter((sc, sp, p['hash']) for r in self.regions.values()
                                     for l in r.locations.values() for sc, sp, p in self.placements_of(r, l))
        for (scene, spot, h), n in placed.items():
            if n > 1:
                out.append('%s: spot %s object %s used by %d locations' % (scene, spot, h, n))
        return out

    @staticmethod
    def spots_of(region, loc):
        """(scene, spot id) of every map placement of a location"""
        out = []
        if loc.get('spot') and region.scene:
            out.append((region.scene, loc['spot']))
        for a in loc.get('also', []):
            out.append((a['scene'], a['spot']))
        return out

    def placements_of(self, region, loc):
        """(scene, spot id, placement) of every map object of a location; a location with an 'age' has only
        that age's objects"""
        out = []
        for sc, sp in self.spots_of(region, loc):
            for p in self.checks.get(sc, {}).get(sp, {}).get('placements', []):
                if not loc.get('age') or loc['age'] in p['ages']:
                    out.append((sc, sp, p))
        return out

    def unplaced_spots(self, scene, kinds=None):
        used = {sp for r in self.regions.values() for l in r.locations.values()
                for sc, sp in self.spots_of(r, l) if sc == scene}
        return [sid for sid, s in self.checks.get(scene, {}).items()
                if sid not in used and (kinds is None or s['kind'] in kinds)]

    # ------------------------------------------------------------------ search
    def search(self, items=(), settings=None):
        """Everything reachable: returns (regions reached {age: set}, locations {name: set of ages}, state).
        Events found along the way are added to the state's items and the search goes again until nothing
        changes."""
        s = dict(self.settings_defaults)
        s.update(settings or {})
        state = State(items, s)
        while True:
            reached = {age: self._explore(state, age) for age in ('child', 'adult')}
            new_events = []
            for age, regs in reached.items():
                for rn in regs:
                    r = self.regions[rn]
                    for ev, (_, fn) in r.events.items():
                        if not state.count(ev) and fn(rules.Context(state, age, r, self.helpers)):
                            new_events.append(ev)
            if not new_events:
                break
            for ev in set(new_events):
                state.items[ev] += 1
        locs = collections.defaultdict(set)
        for age, regs in reached.items():
            for rn in regs:
                r = self.regions[rn]
                for ln, loc in r.locations.items():
                    if loc['rule_fn'](rules.Context(state, age, r, self.helpers)):
                        locs[ln].add(age)
        return reached, dict(locs), state

    def _explore(self, state, age):
        start = 'Root'
        seen = {start}
        todo = [start]
        while todo:
            r = self.regions[todo.pop()]
            ctx = rules.Context(state, age, r, self.helpers)
            for target, (_, fn) in r.exits.items():
                if target not in seen and fn(ctx):
                    seen.add(target)
                    todo.append(target)
        return seen
