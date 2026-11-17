"""Draw a top-down map of an area: the game's own placements as the background, every check of the region
map on top with its name, coloured by kind. For checking names and rooms by eye.

    python tools/area_map.py "<romfs>" KokiriForest child out.png
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from formats import zstd, byml  # noqa: E402
from logic.world import World  # noqa: E402

COLOURS = {'chest': '#c0392b', 'skulltula': '#d4ac0d', 'scrub': '#7d3c98', 'shop': '#2471a3', 'pot': '#a04000',
           'freestanding': '#1e8449', 'gossip': '#5d6d7e', 'gift': '#e67e22', 'rock': '#784212', 'bush': '#52be80', 'boulder': '#4d5656'}


def main(romfs, area, age, out):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    xs, zs = [], []
    for fn in os.listdir(os.path.join(romfs, 'Banc', area)):
        if fn.startswith('%s_%s_' % (area, age.capitalize())):
            doc = byml.loads(zstd.decompress(open(os.path.join(romfs, 'Banc', area, fn), 'rb').read(), d)).root
            for a in doc.get('Actors', []):
                if a['Gyaml'].startswith(('Land_', 'Tree_')) and 'Translate' in a and 'FarView' not in a['Gyaml']:
                    xs.append(a['Translate'][0])
                    zs.append(a['Translate'][2])
    w = World()
    spots = w.checks[area]
    fig, ax = plt.subplots(figsize=(16, 13), dpi=110)
    ax.scatter(xs, zs, s=3, c='#d5d8dc', zorder=1)
    placed = []
    for r in w.regions.values():
        for name, loc in r.locations.items():
            sids = [sp for sc, sp in w.spots_of(r, loc) if sc == area]
            if not sids:
                if loc.get('pos') and r.scene == area:      # a gift: drawn where its NPC stands
                    s = {'kind': loc.get('kind', 'gift'), 'pos': loc['pos'], 'ages': [age]}
                else:
                    continue
            else:
                s = spots[sids[0]]
            if age not in s['ages'] or loc.get('age', age) != age:
                continue
            kind = s['kind']
            x, z = s['pos'][0], s['pos'][2]
            ax.scatter([x], [z], s=46, c=COLOURS.get(kind, 'k'), edgecolors='black', linewidths=0.5, zorder=3)
            placed.append((x, z, name.replace('KF ', '').replace('LW ', 'LW '), kind))
    # labels, nudged so close ones don't sit on top of each other
    used = []
    for x, z, name, kind in sorted(placed, key=lambda p: (p[1], p[0])):
        dy = 0
        while any(abs(x - ux) < 18 and abs(z + dy - uz) < 2.2 for ux, uz in used):
            dy += 2.4
        used.append((x, z + dy))
        ax.annotate(name, (x, z), (x + 1.5, z + dy), fontsize=6.5, color=COLOURS.get(kind, 'k'), zorder=4,
                    arrowprops=dict(arrowstyle='-', color='#aab7b8', lw=0.4) if dy else None)
    for kind, col in COLOURS.items():
        ax.scatter([], [], s=46, c=col, edgecolors='black', linewidths=0.5, label=kind)
    ax.legend(loc='lower left', fontsize=9)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.set_title('%s (%s) - checks from the game files, names from data/world/%s.json' % (area, age, area))
    ax.set_xlabel('x')
    ax.set_ylabel('z')
    fig.tight_layout()
    fig.savefig(out)
    print(out)


if __name__ == '__main__':
    main(*sys.argv[1:5])
