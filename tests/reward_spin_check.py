"""Stones and Medallions turn test (tools/build_mod.py: reward_spin_pack, reward_spin_rows; phase 1, part 7).

The Spiritual Stones and the Medallions stood still in Link's hands and on the ground (in game 2026-11-24): the
game only gives them in cutscenes, so their actors have no animation. A placed one gets the animation settings
the Boomerang has, as the songs do.

Read from the game's own files: the nine actors' empty animation components, the two bones of their models
that the game's item spin turns and lifts, the Boomerang's settings (nothing plays by itself) and the shared
animation file's commands. Then the change read back on every one of the nine, their table rows, what is
refused, and a whole build read back from the mod folder (a chest, a pot and a loose item; one not placed is
left alone). Only reads the game; the build goes to a temporary folder that is removed again.

    python tests/reward_spin_check.py "C:\\...\\romfs"
"""
import contextlib
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import harp_colors  # noqa: E402
from formats import zstd, byml, sarc  # noqa: E402

STONES = ['Item_Stone_Forest', 'Item_Stone_Fire', 'Item_Stone_Water']
MEDALS = ['Item_Medal_Light', 'Item_Medal_Forest', 'Item_Medal_Fire', 'Item_Medal_Water', 'Item_Medal_Shadow',
          'Item_Medal_Spirit']
NINE = STONES + MEDALS
LIKE = 'Item_Boomerang'
COMMON = 'Item_Common_Animation'
AS_INFO = 'Component/ASInfo/Item_GetDemo.engine__component__ASInfo.bgyml'
AS_FILE = 'AS/Item_Common.root.asb'
EMPTY_AS = 'AS/DemoDummy.root.asb'
EMPTY_ANIM = 'Component/AnimationParam/Dummy.engine__component__AnimationParam.bgyml'
SPIN_ANIM = build_mod.REWARD_ANIM_PARAM
SPUN = {'ASInfoRef': '?' + AS_INFO, 'ASRef': '?' + AS_FILE, 'AnimationRef': '?' + SPIN_ANIM}
SAMPLE = [('KF_MIDO_CHEST_01', 'Item_Medal_Forest'),                      # a Medallion in a chest
          ('KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01', 'Item_Stone_Fire'),       # a stone from a pot
          ('KF_SARIAS_HOUSE_HEART_ITEM_02', 'Item_Medal_Water')]          # a Medallion as a loose item
PLACED = sorted(item for _, item in SAMPLE)
VERSIONS = {'Item_Stone_Fire': 'Obj_NX2O_Stone_Fire', 'Item_Medal_Water': 'Obj_NX2_Medal_Water'}


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def refused(fn, *args):
    try:
        fn(*args)
    except SystemExit as e:
        return str(e)
    return None


def components(pack, actor):
    files = sarc.Sarc.read(pack).files
    return {k: str(v) for k, v in byml.loads(files[ground_items.ap_path(actor)]).root['Components'].items()}, files


def projects(data):
    return [str(r['ModelProjectName']) for r in byml.loads(data).root['AnimationResources']]


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path):
        p = os.path.join(romfs, *path.split('/'))
        return open(p, 'rb').read() if os.path.exists(p) else zstd.decompress(open(p + '.zs', 'rb').read(), d)

    good = True

    # ---- the game's files
    packs = {n: plain(ground_items.pack_path(n)) for n in NINE + [LIKE]}
    comps = {n: components(packs[n], n) for n in packs}
    good &= check('the builder knows the three Spiritual Stones and the six Medallions',
                  sorted(build_mod.REWARD_ITEMS) == sorted(NINE))
    good &= check('  none of the nine has animation settings (ASInfoRef), and each names an empty animation list',
                  all('ASInfoRef' not in comps[n][0] and comps[n][0].get('AnimationRef') == '?' + EMPTY_ANIM
                      and projects(comps[n][1][EMPTY_ANIM]) == [] for n in NINE))
    no_file = [n for n in NINE if not os.path.exists(os.path.join(romfs, *comps[n][0]['ASRef'][1:].split('/')) + '.zs')
               and not os.path.exists(os.path.join(romfs, *comps[n][0]['ASRef'][1:].split('/')))]
    empty = plain(EMPTY_AS)
    good &= check('  their animation file is a placeholder: the Medallions\' has no command (%d bytes), the stones\' '
                  'is not a file of the game' % len(empty),
                  all(comps[n][0]['ASRef'] == '?' + EMPTY_AS for n in MEDALS) and b'Rotate' not in empty
                  and len(empty) < 400 and all(comps[n][0]['ASRef'] in build_mod.REWARD_NO_AS for n in NINE)
                  and no_file == STONES, (no_file, len(empty)))
    bones = {n: [b for b in (b'Root', b'Skl_Root') if b + b'\0' in plain('Model/%s.%s.bfres' % (n, n))] for n in NINE}
    good &= check('  every one of the nine models has the two bones the item spin turns and lifts (Root, Skl_Root)',
                  all(len(b) == 2 for b in bones.values()), {n: b for n, b in bones.items() if len(b) != 2})
    like_c, like_f = comps[LIKE]
    info = byml.loads(like_f[AS_INFO]).root
    shared = plain(AS_FILE)
    good &= check('the Boomerang, which Link holds up, has the three: settings that play nothing by themselves, the '
                  'shared animation file with the hands\' and the ground\'s spin, and the game\'s common animations',
                  like_c.get('ASInfoRef') == '?' + AS_INFO and like_c.get('ASRef') == '?' + AS_FILE
                  and not info.get('AutoPlayASName') and not list(info.get('AutoPlayASCommands') or [])
                  and b'Rotate_GetDemo' in shared and b'Rotate_Obj' in shared
                  and projects(like_f[like_c['AnimationRef'][1:]])[0] == COMMON == harp_colors.ANIM_PROJECT)
    good &= check('  before the change the builder would not let Link hold one of the nine up; the Boomerang it does',
                  not any(ground_items.can_hold_up(plain, n) for n in NINE) and ground_items.can_hold_up(plain, LIKE))

    # ---- the change
    spin = build_mod.reward_spin_files(packs[LIKE])
    good &= check('the spin\'s two files: the Boomerang\'s settings as they are, and a list of only %s' % COMMON,
                  sorted(spin) == sorted([AS_INFO, SPIN_ANIM]) and spin[AS_INFO] == like_f[AS_INFO]
                  and projects(spin[SPIN_ANIM]) == [COMMON])
    wrong = []
    done = {}
    for n in NINE:
        new, (inner, old_inner, new_inner) = build_mod.reward_spin_pack(packs[n], n, spin)
        got, files = components(new, n)
        before, was = comps[n]
        if ({k: got.get(k) for k in SPUN} != SPUN
                or {k: v for k, v in got.items() if k not in SPUN} != {k: v for k, v in before.items() if k not in SPUN}
                or set(files) != set(was) | set(spin) or any(files[p] != was[p] for p in was if p != inner)
                or inner != ground_items.ap_path(n) or files[inner] != new_inner or was[inner] != old_inner):
            wrong.append(n)
        done[n] = new
    good &= check('each of the nine packs gets the three components and the two files; nothing else of it changes',
                  not wrong, wrong)
    again = refused(build_mod.reward_spin_pack, done[NINE[0]], NINE[0], spin)
    other = refused(build_mod.reward_spin_pack, packs[LIKE], LIKE, spin)
    good &= check('a pack that already has the spin, or an item that is not one of the empty ones, is refused',
                  bool(again) and bool(other) and 'not as expected' in again + other, (again, other))
    table = plain(build_mod.ACTOR_INFO)
    rows = {str(r['__RowId']): r for r in byml.loads(table).root}
    new_rows = {str(r['__RowId']): r for r in byml.loads(build_mod.reward_spin_rows(table, set(NINE))).root}
    heaps = ('InstanceHeapSize', 'PreActorRenderInfoHeapSize')
    good &= check('their nine table rows get the animation list and heaps at least the Boomerang\'s; every other '
                  'row is as it was',
                  not any('AnimationResources' in rows[n] for n in NINE)
                  and all([str(x['ModelProjectName']) for x in new_rows[n]['AnimationResources']] == [COMMON]
                          and all(int(new_rows[n][k]) == max(int(rows[n][k]), int(rows[LIKE][k])) for k in heaps)
                          and {k: v for k, v in new_rows[n].items() if k not in heaps + ('AnimationResources',)}
                          == {k: v for k, v in rows[n].items() if k not in heaps}
                          for n in NINE)
                  and all(new_rows[n] == rows[n] for n in rows if n not in NINE) and set(new_rows) == set(rows))

    # ---- a whole build
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        said, folder = run('spin', *['%s=%s' % x for x in SAMPLE])

        def read(path):
            p = os.path.join(folder, *path.split('/'))
            if os.path.exists(p):
                return open(p, 'rb').read()
            return zstd.decompress(open(p + '.zs', 'rb').read(), d) if os.path.exists(p + '.zs') else None

        built = {n: read(ground_items.pack_path(n)) for n in NINE}
        good &= check('a build with three of them placed (a chest, a pot, a loose item) writes those three packs '
                      'with the spin and leaves the other six alone',
                      sorted(n for n in NINE if built[n]) == PLACED
                      and all(built[n] == done[n] for n in PLACED) and 'turn when held up' in said,
                      sorted(n for n in NINE if built[n]))
        wrong = []
        for item, version in VERSIONS.items():
            pack = read(ground_items.pack_path(version))
            got, files = components(pack, version) if pack else ({}, {})
            if (got.get('AnimationRef') != '?' + SPIN_ANIM or SPIN_ANIM not in files
                    or projects(files[SPIN_ANIM]) != [COMMON] or got.get('ASRef') != '?' + AS_FILE):
                wrong.append((version, got.get('AnimationRef'), got.get('ASRef')))
        good &= check('  the versions that lie on the ground (%s) carry the same animation list and the shared '
                      'animation file, so they turn there' % ', '.join(VERSIONS.values()), not wrong, wrong)
        out_rows = {str(r['__RowId']): r for r in byml.loads(read(build_mod.ACTOR_INFO)).root}
        good &= check('  the table rows of the three, and of their ground versions, list the animation',
                      all([str(x['ModelProjectName']) for x in out_rows[n].get('AnimationResources', [])] == [COMMON]
                          for n in PLACED + list(VERSIONS.values()))
                      and not any('AnimationResources' in out_rows[n] for n in NINE if n not in PLACED))
        _, none = run('none', 'KF_MIDO_CHEST_01=Item_Boomerang')
        good &= check('a build with none of them placed writes none of the nine packs',
                      not any(os.path.exists(os.path.join(none, *ground_items.pack_path(n).split('/')) + '.zs')
                              for n in NINE))

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
