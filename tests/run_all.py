"""Runs every test script of run_tests.bat, several at a time, and says which passed.

The scripts don't depend on each other: each reads the game files on its own and builds into a temporary folder
of its own, so they can run side by side. The slowest ones start first. Each script's whole output goes to
test_logs/<script>.txt (not uploaded); a failing script's last lines are shown at the end.

    python tests/run_all.py "<romfs folder>" [--jobs N] [--only NAME,NAME...]

--jobs   how many scripts run at once (default: the number of CPU cores, at most 8)
--only   run only these scripts (names without .py, e.g. families_check,roundtrip), for a quick check while
         working; run_tests.bat always runs them all

A script passes when it ends with exit code 0. The round-trip test is a report, not a pass or fail: it always
lists the same known differences (5 BYML files), so its summary is shown
instead; the full report is in report.txt, as before.
"""
import concurrent.futures
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, 'test_logs')

ROUNDTRIP_ARGS = ['Event', 'RSDB', 'Mals', 'GameData', 'Pack', 'System', 'AI', 'Logic', 'Sequence',
                  '--report', 'report.txt']

# (script, title), in the order run_tests.bat listed them. A new test script adds its row here.
STEPS = [
    ('edit_check', 'Edit check'),
    ('evfl_add_check', 'Event flow add check'),
    ('chest_check', 'Checking chest check'),
    ('ocarina_fix_check', 'Ocarina fix check'),
    ('ground_prog_check', 'Turning items check'),
    ('ground_lift_check', 'Ground lift check'),
    ('three_chest_check', 'Three-level chest check'),
    ('gift_check', 'Progressive gift check'),
    ('event_families_check', 'Families on songs and the bridge gift check'),
    ('saria_check', 'Cutscene gift check'),
    ('pairs_more_check', 'Pairs on rocks, bushes and scrubs check'),
    ('skip_level_check', 'Skip-level guard check'),
    ('families_check', 'Progressive families check'),
    ('gossip_check', 'Gossip stone text check'),
    ('hint_check', 'Gossip stone hints check'),
    ('skulltula_prog_check', 'Progressive families on Gold Skulltulas check'),
    ('one_time_check', 'One-time drops (rocks, bushes, pots) check'),
    ('forest_temple_check', 'Forest Temple data check'),
    ('forest_temple_items_check', 'Forest Temple items check'),
    ('forest_temple_keys_check', 'Forest Temple keys check'),
    ('dungeon_keys_check', 'Dungeon keys check'),
    ('start_state_check', 'Starting state of a new file check'),
    ('boss_check', 'Boss key, boss door, boss heart and Medallion check'),
    ('key_items_tab_check', 'Key Items tab open from the start check'),
    ('reward_spin_check', 'Stones and Medallions turn check'),
    ('reward_names_check', 'Stones\' and Medallions\' names in colour check'),
    ('forest_temple_every_spot_check', 'Forest Temple, every spot check'),
    ('cutscene_list_check', 'Timeline reader and cutscene list check'),
    ('roundtrip', 'Round-trip test (Event, RSDB, Mals, GameData, Pack, System, AI, Logic, Sequence)'),
]

# test scripts that run_tests.bat leaves out on purpose (run by hand: README.md)
NOT_HERE = {'logic_check', 'db_check', 'size_check'}

# Seconds each took when run one after another (2026-11-24; families_check since its builds run side by side),
# so the slowest start first. A script not listed starts after these.
SECONDS = {'ground_lift_check': 114, 'roundtrip': 103, 'families_check': 70, 'skulltula_prog_check': 63,
           'one_time_check': 54, 'skip_level_check': 47, 'hint_check': 35, 'gossip_check': 34,
           'pairs_more_check': 31, 'evfl_add_check': 31, 'cutscene_list_check': 30,
           'forest_temple_items_check': 26, 'ocarina_fix_check': 19,
           'start_state_check': 10, 'chest_check': 8, 'three_chest_check': 7, 'forest_temple_keys_check': 6,
           'gift_check': 6, 'ground_prog_check': 5}


def mmss(s):
    return '%dm %02ds' % divmod(round(s), 60) if s >= 60 else '%ds' % round(s)


def run_one(romfs, script):
    args = [sys.executable, os.path.join(HERE, script + '.py'), romfs]
    if script == 'roundtrip':
        args += ROUNDTRIP_ARGS
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    log = os.path.join(LOGS, script + '.txt')
    t0 = time.perf_counter()
    with open(log, 'w', encoding='utf-8') as f:
        rc = subprocess.call(args, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env)
    return rc, time.perf_counter() - t0


def tail(script, n):
    with open(os.path.join(LOGS, script + '.txt'), encoding='utf-8', errors='replace') as f:
        return f.read().splitlines()[-n:]


def roundtrip_summary(script='roundtrip'):
    lines = tail(script, 100000)
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith('Read-and-write test'))
    except StopIteration:
        return tail(script, 15)
    out = []
    for l in lines[start + 5:]:
        if not l.strip():
            break
        out.append(l)
    return out


def main(argv):
    if not argv or argv[0].startswith('-'):
        sys.exit(__doc__)
    romfs, jobs, only = argv[0], min(os.cpu_count() or 4, 8), None
    rest = argv[1:]
    while rest:
        opt = rest.pop(0)
        if opt == '--jobs' and rest:
            jobs = max(1, int(rest.pop(0)))
        elif opt == '--only' and rest:
            only = [x.strip().removesuffix('.py') for x in rest.pop(0).split(',') if x.strip()]
        else:
            sys.exit('Unknown option: %s\n%s' % (opt, __doc__))
    titles = dict(STEPS)
    if only:
        unknown = [x for x in only if x not in titles]
        if unknown:
            sys.exit('No such test script in the list: %s' % ', '.join(unknown))
    steps = [s for s, _ in STEPS if not only or s in only]
    missing = [s for s in steps if not os.path.exists(os.path.join(HERE, s + '.py'))]
    if missing:
        sys.exit('Missing test scripts: %s' % ', '.join(missing))

    os.makedirs(LOGS, exist_ok=True)
    for name in os.listdir(LOGS):
        if name.endswith('.txt'):
            os.remove(os.path.join(LOGS, name))
    order = sorted(steps, key=lambda s: -SECONDS.get(s, 0))
    print('%d test scripts, %d at a time. Each one\'s output: test_logs\\<script>.txt' % (len(steps), jobs))
    forgotten = sorted(f[:-3] for f in os.listdir(HERE)
                       if f.endswith('_check.py') and f[:-3] not in titles and f[:-3] not in NOT_HERE)
    if forgotten:
        print('NOTE: not in the list of tests/run_all.py, so not run: %s' % ', '.join(forgotten))
    print()
    t_all = time.perf_counter()
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(run_one, romfs, s): s for s in order}
        for fut in concurrent.futures.as_completed(futures):
            s = futures[fut]
            rc, dt = fut.result()
            results[s] = (rc, dt)
            word = 'done' if s == 'roundtrip' else ('OK' if rc == 0 else 'FAILED')
            print('  %-6s %-48s %8s   (%d of %d finished)' % (word, titles[s][:48], mmss(dt), len(results), len(steps)),
                  flush=True)
    total = time.perf_counter() - t_all

    checks = [s for s in steps if s != 'roundtrip']
    failed = [s for s in checks if results[s][0] != 0]
    print()
    for s in failed:
        print('=== FAILED: %s (exit code %d), last lines of test_logs\\%s.txt ===' % (titles[s], results[s][0], s))
        for l in tail(s, 40):
            print('  ' + l)
        print()
    if 'roundtrip' in steps:
        print('Round-trip test (a report; the full list is in report.txt):')
        for l in roundtrip_summary():
            print('  ' + l)
        print()
    if failed:
        print('%d of %d checks FAILED: %s' % (len(failed), len(checks), ', '.join(failed)))
    else:
        print('All %d checks passed.' % len(checks))
    print('Time: %s (one after another it would be %s)' % (mmss(total), mmss(sum(dt for _, dt in results.values()))))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
