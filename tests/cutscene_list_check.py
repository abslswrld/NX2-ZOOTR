"""Cutscene list test: the timeline reader (formats/evfl.py) and the cutscene list (tools/cutscene_list.py),
on the game's own files. Reads only; writes nothing.

    python tests/cutscene_list_check.py "C:\\...\\romfs"

1. The reader: every event flow file is read and written back byte for byte (the 261 timeline files and the 3
   files with entry point variables included); what the reader says about a timeline holds for every file;
   a changed timeline is written and read back as meant; a mistake is refused.
2. The list: data/cutscenes.json and docs/CUTSCENES.md are what the tool makes of the game's files now; every
   cutscene file is in the list; facts that were checked in game or by hand earlier are in it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import cutscene_list  # noqa: E402
from formats import zstd, evfl  # noqa: E402

FLAG_WORDS = ('GameData', 'Pouch', 'Challenge', 'EventBool', 'Rupee', 'Save')
# the five entry point variables of the game: (flow, entry point, variable, value)
VARIABLES = [('LinkSleepInBed', 'EntryPoint0', 'IsKokiriBed', True), ('LinkSleepInBed', 'CommonBed', 'IsKokiriBed', False),
             ('Dm_SY_Ocarina', 'PlayOcarinaSequence_NpcBeginningTalk', 'IsNotNeedSensor', False),
             ('Dm_SY_Ocarina', 'PlayOcarinaSequence_NpcBeginningTalk_NotCreateSensor', 'IsNotNeedSensor', True),
             ('Dm_SY_Get', 'Dm_SY_Get', 'Frames', 0)]
EDIT_FLOW = 'Dm_Kokiri_0150'


def check(name, ok):
    print('%-100s %s' % (name, 'OK' if ok else 'FAILED'))
    return bool(ok)


def refused(f, *a):
    try:
        f(*a)
    except ValueError:
        return True
    return False


def reader_checks(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    folder = os.path.join(romfs, 'Event', 'EventFlow')
    files = sorted(f for f in os.listdir(folder) if f.endswith('.bfevfl.zs'))
    good = True
    read = same = checked = 0
    timelines = {}
    problems = []
    one_of_each = True
    for fn in files:
        raw = zstd.decompress(open(os.path.join(folder, fn), 'rb').read(), d)
        try:
            flow = evfl.loads(raw)
            read += 1
            same += evfl.dumps(flow) == raw
            checked += evfl.dumps_checked(flow, update_entry_points=False) == raw
        except Exception as e:                          # noqa: BLE001  (a test: report, go on)
            problems.append('%s: %s: %s' % (fn, type(e).__name__, e))
            continue
        one_of_each &= (len(flow.flowcharts), len(flow.timelines)) in ((1, 0), (0, 1))
        if flow.timelines:
            timelines[fn.split('.')[0]] = (flow, raw)
    for p in problems[:10]:
        print('   ' + p)
    good &= check('every event flow file is read (%d of %d)' % (read, len(files)), read == len(files) >= 914)
    good &= check('  and written back byte for byte (%d), also by dumps_checked (%d)' % (same, checked),
                  same == checked == len(files))
    good &= check('  a file holds one flowchart or one timeline, never both; %d hold a timeline' % len(timelines),
                  one_of_each and len(timelines) == 261)

    # ---- what the reader's notes say about timelines, on every file
    rule = whole = cuts_ok = tracks = plain = flag_free = 0
    actions = set()
    for name, (flow, raw) in timelines.items():
        tl = flow.timeline
        rule += evfl.timeline_triggers(tl) == tl.triggers
        whole += tl.duration == int(tl.duration) and all(c.start == int(c.start) and c.duration == int(c.duration)
                                                         for c in tl.clips)
        starts = [c.start for c in tl.cuts]
        cuts_ok += bool(starts) and starts[0] == 0 and starts == sorted(starts) and starts[-1] < tl.duration
        lanes = {}
        for c in tl.clips:
            lanes.setdefault((c.actor, c.track), []).append((c.start, c.end))
        tracks += all(a[1] <= b[0] for lane in lanes.values() for a, b in zip(sorted(lane), sorted(lane)[1:]))
        plain += not tl.oneshots and tl.params is None and all(c.params is None for c in tl.cuts) \
            and all(not a.queries and a.entry_point is None for a in tl.actors)
        acts = {tl.clip_names(c)[1] for c in tl.clips}
        actions |= acts
        flag_free += not any(w in a for a in acts for w in FLAG_WORDS)
    n = len(timelines)
    good &= check('timelines: the trigger list is every clip\'s start and end in time order, ends first (%d/%d)'
                  % (rule, n), rule == n)
    good &= check('timelines: lengths and times are whole frames (%d/%d)' % (whole, n), whole == n)
    good &= check('timelines: cuts start at frame 0, in order, inside the length (%d/%d)' % (cuts_ok, n), cuts_ok == n)
    good &= check('timelines: clips of one actor on one track don\'t overlap (%d/%d; one file is the exception)'
                  % (tracks, n), tracks >= n - 1)
    good &= check('timelines: no one-shot steps, no parameters on a timeline or a cut, no queries (%d/%d)'
                  % (plain, n), plain == n)
    good &= check('timelines: no step sets a flag, a challenge step or gives an item (%d/%d; %d kinds of step)'
                  % (flag_free, n, len(actions)), flag_free == n and 'EventTrigger_SetTime' in actions)

    # ---- entry point variables
    var_ok = True
    for fname, ep, var, value in VARIABLES:
        raw = zstd.decompress(open(os.path.join(folder, fname + '.bfevfl.zs'), 'rb').read(), d)
        got = evfl.loads(raw).flowchart.entry_point(ep).variables
        var_ok &= got == {var: value} and type(got[var]) is type(value)
    good &= check('entry point variables: the game\'s five are read with their values', var_ok)

    # ---- a changed timeline
    flow, raw = timelines[EDIT_FLOW]
    orig = evfl.loads(raw)
    tl = flow.timeline
    tl.duration += 120
    tl.clips[0].duration += 30
    tl.clips.append(evfl.Clip(tl.duration - 60, 60, tl.clips[0].actor, tl.clips[0].action,
                              evfl.Params(tl.clips[0].params or {}), tl.clips[0].track))
    tl.cuts.append(evfl.Cut(tl.duration - 60, 'cut%d' % (len(tl.cuts) + 1)))
    tl.triggers = evfl.timeline_triggers(tl)
    out = evfl.dumps_checked(flow)
    back = evfl.loads(out).timeline
    good &= check('a changed timeline (longer, a clip longer, a clip and a cut added) is written and read back as '
                  'meant',
                  back.duration == orig.timeline.duration + 120 and len(back.clips) == len(orig.timeline.clips) + 1
                  and back.clips[0].duration == orig.timeline.clips[0].duration + 30
                  and back.clips[-1].start == back.duration - 60 and back.cuts[-1].start == back.duration - 60
                  and len(back.triggers) == 2 * len(back.clips) and not evfl.differences(flow, evfl.loads(out))
                  and len(evfl.differences(orig, flow)) >= 4 and evfl.dumps(evfl.loads(out)) == out)
    bad1, bad2 = evfl.loads(raw), evfl.loads(raw)
    bad1.timeline.clips[0].actor = len(bad1.timeline.actors)
    bad2.timeline.triggers[0] = (len(bad2.timeline.clips), 1)
    good &= check('mistakes are refused: a clip of an actor that isn\'t there, a trigger of a clip that isn\'t there',
                  refused(evfl.dumps_checked, bad1) and refused(evfl.dumps_checked, bad2))
    return good


def list_checks(romfs):
    good = True
    data = json.loads(cutscene_list.dump_json(cutscene_list.build(romfs)))
    with open(cutscene_list.DATA_FILE, encoding='utf-8') as f:
        on_disk = json.load(f)
    with open(cutscene_list.DOC_FILE, encoding='utf-8') as f:
        doc = f.read()
    good &= check('data/cutscenes.json is what the tool reads from the game now', on_disk == data)
    good &= check('docs/CUTSCENES.md is what the tool writes for it', doc == cutscene_list.render(data) + '\n')
    cs = data['cutscenes']
    by = {e['name']: e for e in cs}
    c = data['counts']
    good &= check('the list: %d story cutscenes, %d lead-in events, %d small scenes, %d system scenes'
                  % (c['story'], c['lead_in'], c['small'], c['system']),
                  c['story'] >= 300 and c['lead_in'] >= 150 and c['small'] >= 300 and c['system'] >= 70
                  and len(by) == len(cs))

    # ---- every cutscene file is in the list
    folder = os.path.join(romfs, 'Event', 'EventFlow')
    dm = sorted({f.split('.')[0] for f in os.listdir(folder) if f.endswith('.bfevfl.zs') and f.startswith(('Dm_', 'DmF_'))})
    in_entries = {f for e in cs for f in e['files']}
    others = {o['file'] for o in data['other_files']}
    good &= check('every cutscene flow file (%d names) is in an entry (%d) or in "files without an event" (%d)'
                  % (len(dm), len(in_entries & set(dm)), len(others)),
                  set(dm) == (in_entries & set(dm)) | others and not (in_entries & others) and len(dm) >= 480)

    # ---- every entry is complete
    story = [e for e in cs if e['class'] == 'story']
    kinds = {}
    for e in story:
        kinds[e['kind']] = kinds.get(e['kind'], 0) + 1
    good &= check('story cutscenes: %s' % ', '.join('%d %s' % (v, k) for k, v in sorted(kinds.items())),
                  kinds.get('unknown', 0) <= 1 and kinds.get('timeline', 0) >= 80 and kinds.get('movie', 0) >= 20)
    tls = [e for e in cs if 'frames' in e]
    good &= check('timeline cutscenes (%d): a length in frames and in seconds at 60 a second, their cuts, their files'
                  % len(tls),
                  all(e['frames'] > 0 and abs(e['seconds'] - e['frames'] / 60) < 0.06 and e['cuts'] == len(e['cut_starts'])
                      and e['files'] and e['files'][0] in in_entries for e in tls))
    synced = [e for e in cs if e['kind'] == 'movie' and 'frames' in e]
    off = [e['name'] for e in synced if abs(e['frames'] / 60 - e['movie_seconds']) > 0.02 * e['movie_seconds']]
    good &= check('60 frames a second: %d movie cutscenes have a timeline as long as their video file to within 2%% '
                  '(not: %s)' % (len(synced) - len(off), ', '.join(off) or 'none'),
                  len(synced) >= 12 and off == ['Dm_FinalBattle_0002'])
    flows = [e for e in cs if e['kind'] == 'flowchart']
    good &= check('flowchart events (%d): a flow, an entry point, steps, the frames of their waits' % len(flows),
                  all(e.get('flow') and e.get('entry') and e['steps'] > 0 and e['wait_frames'] >= 0 for e in flows))
    no_area = [e['name'] for e in story if not e['area']]
    good &= check('story cutscenes have an area, but the title, the credits, the Great Fairies and the Sun\'s Song '
                  '(%d)' % len(no_area),
                  all(n.startswith(('Dm_Title', 'Dm_StaffCredit', 'Dm_Ending', 'Dm_FairyFountain', 'Dm_MelodyGet_'))
                      for n in no_area))
    no_start = [e['name'] for e in story if not e.get('started_by')]
    good &= check('what starts a story cutscene is found for all but %s' % (', '.join(no_start) or 'none'),
                  no_start in ([], ['Dm_MelodyGet_Manegement']))
    names = data['areas']
    good &= check('area names are the game\'s own text: Sacred Grove, Lost Woods, Hyrule Castle Town',
                  names.get('SacredForestMeadow') == 'Sacred Grove' and names.get('LostWood') == 'Lost Woods'
                  and names.get('Market') == 'Hyrule Castle Town')

    # ---- facts found earlier (in game or by hand)
    def starters(name, how):
        return [s for s in by[name].get('started_by', []) if s['how'] == how]

    def gives(name):
        return {(g.get('item'), g.get('name')) for g in by[name].get('gives', [])}

    e = by['Dm_Kokiri_0150']
    lead = by['KokiriForest_ArriveLostWood']
    where = starters('KokiriForest_ArriveLostWood', 'map')
    good &= check('Saria on the bridge: Dm_Kokiri_0150 is a timeline of 6108 frames (1 min 42 s) with two '
                  'sub-timelines',
                  e['kind'] == 'timeline' and e['frames'] == 6108 and e['seconds'] == 101.8
                  and e['files'] == ['Dm_Kokiri_0150', 'Dm_Kokiri_0150_Effect', 'Dm_Kokiri_0150_Env']
                  and 'sets' not in e and 'gives' not in e)
    good &= check('  run by KokiriForest_ArriveLostWood, then Dm_Kokiri_0155, a flag, then Hyrule Field',
                  [s['event'] for s in starters('Dm_Kokiri_0150', 'transition')] == ['KokiriForest_ArriveLostWood']
                  and lead['class'] == 'lead-in' and lead['next'] == ['Dm_Kokiri_0150', 'Dm_Kokiri_0155']
                  and {'flag': 'HyruleField_ChangeENV', 'value': True} in lead['sets']
                  and lead['warps'][0]['map'] == 'HyruleField_Child')
    good &= check('  which starts when Link is in an area that is gone once Dm_Kokiri_0150 has been played',
                  len(where) == 1 and where[0]['map'] == 'KokiriForest_Child_Static'
                  and where[0]['when'] == 'Link in AreaActor Area_aaaa [gone once: Dm_Kokiri_0150 played]'
                  and 'KokiriForest_Child_Level_All_02_ddcd' in by['Dm_Kokiri_0150']['played_tested_by'])
    good &= check('  Dm_Kokiri_0155 gives the Fairy Ocarina and is the cutscene of the check LW_SARIA_GIFT',
                  gives('Dm_Kokiri_0155') == {('Item_Ocarina_Fairy', 'Fairy Ocarina')}
                  and [x.get('id') for x in by['Dm_Kokiri_0155']['checks']] == ['LW_SARIA_GIFT']
                  and by['Dm_Kokiri_0155']['shows'] == ['Item_Ocarina_Fairy'])
    song = starters('SacredForestMeadow_Field_MelodyGet_Saria', 'map')
    good &= check('Saria\'s Song: started in an area that is there while the letter flag is set and the cutscene '
                  'is not played',
                  gives('Dm_MelodyGet_Saria') == {('Item_Melody_SariaSong', 'Saria\'s Song')} and len(song) == 1
                  and song[0]['when'] == 'Link in AreaActor Area_0b11 [there while: (flag DoorOfTime_IsAfter_Step01_Exp '
                                         'AND Dm_MelodyGet_Saria not played)]'
                  and by['Dm_MelodyGet_Saria']['checks'][0]['name'] == 'Song from Saria')
    good &= check('the opening: Dm_Kokiri_0000 is a movie that can\'t be skipped, started by the sequence graph',
                  by['Dm_Kokiri_0000']['kind'] == 'movie' and by['Dm_Kokiri_0000']['can_skip'] is False
                  and by['Dm_Kokiri_0030']['can_skip'] is True
                  and starters('Opening_LoadingKokiriForest', 'sequence')[0]['file'] == 'Opening.module')
    door = starters('Dm_Kokiri_0045', 'actor')
    good &= check('Link\'s house: Dm_Kokiri_0045 is the door\'s open event',
                  len(door) == 1 and door[0]['actors'] == ['Obj_Kokiri_Door_A_01'] and door[0]['param'] == 'OpenEventName')
    good &= check('the Kokiri Emerald: Dm_Kokiri_0130 gives it, after the Deku Tree\'s warp',
                  gives('Dm_Kokiri_0130') == {('Item_Stone_Forest', 'Kokiri Emerald')}
                  and 'KokiriForest_WarpFromInsideTheDekuTree' in [s.get('event') for s in by['Dm_Kokiri_0130']['started_by']])
    e = by['Dm_ForestTemple_0000']
    good &= check('Forest Temple: Dm_ForestTemple_0000 shows the title and moves the challenge to Step05',
                  {'location_title': 'ForestTemple'} in e['sets']
                  and {'challenge': 'SageOfForest', 'step': 'Step05'} in e['sets'] and e['area'] == 'ForestTemple'
                  and e['area_name'] == 'Forest Temple')
    boss = starters('ForestTemple_SageOfForest_PhantomGanonDefeat', 'actor')
    e = by['Dm_ForestTemple_BossOut']
    good &= check('  the boss: his "die" event runs Dm_ForestTemple_BossOut, a timeline that shows the Heart '
                  'Container',
                  len(boss) == 1 and boss[0]['actors'] == ['Enemy_DungeonBoss_PhantomGanon']
                  and by['ForestTemple_SageOfForest_PhantomGanonDefeat']['next'] == ['Dm_ForestTemple_BossOut']
                  and e['kind'] == 'timeline' and e['shows'] == ['Obj_Heart_Container'] and e['frames'] == 5528)
    good &= check('  the Medallion: Dm_Awake_Forest_Get gives it (the check FT Forest Medallion), in the Chamber of '
                  'Sages',
                  ('Item_Medal_Forest', 'Forest Medallion') in gives('Dm_Awake_Forest_Get')
                  and by['Dm_Awake_Forest_Get']['checks'][0]['name'] == 'FT Forest Medallion'
                  and by['Dm_Awake_Forest_Get']['area'] == 'SageRoom')
    ice = starters('ForestTemple_Room22_IceMelts', 'map')
    good &= check('  a small scene inside a logic module: the ice melts on an arrow, then the logic sets its flag',
                  by['ForestTemple_Room22_IceMelts']['class'] == 'small' and len(ice) == 1
                  and ice[0]['when'] == 'Ice Obj_Ice_A_01_c729: isArrow'
                  and ice[0]['after'] == {'EventFinish': ['flag ForestTemple_Room14_MeltedIce = true']})
    return good


def main(romfs):
    good = reader_checks(romfs)
    good &= list_checks(romfs)
    print()
    print('All checks passed.' if good else 'SOME CHECKS FAILED.')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
