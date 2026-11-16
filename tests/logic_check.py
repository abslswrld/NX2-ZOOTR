"""Checks of the region map and the search on situations whose answer we know.

    python tests/logic_check.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.world import World  # noqa: E402

w = World()
failures = 0


def expect(desc, items, settings, want=(), not_want=(), age_of=None):
    global failures
    _, locs, state = w.search(items, settings)
    bad = [n for n in want if n not in locs] + ['NOT ' + n for n in not_want if n in locs]
    if age_of:
        for n, ages in age_of.items():
            if locs.get(n, set()) != set(ages):
                bad.append('%s ages %s (want %s)' % (n, sorted(locs.get(n, ())), sorted(ages)))
    print('%-62s %s' % (desc, 'OK' if not bad else 'FAILED: ' + '; '.join(bad)))
    failures += bool(bad)


print('data problems:', w.problems() or 'none')

expect('child, nothing, open forest: village checks', [], {},
       want=['KF Kokiri Sword Chest', 'KF Midos Top Left Chest', 'KF Shop Item 1', 'LW Gift from Saria', 'LW Bridge Chest'],
       not_want=['KF GS Know It All House', 'LW Deku Scrub Near Bridge', 'KF Storms Grotto Chest', 'KF GS House of Twins'])
expect('closed forest, nothing: no bridge, no Deku Tree', [], {'open_forest': False},
       want=['KF Kokiri Sword Chest'], not_want=['LW Gift from Saria', 'LW Bridge Chest'])
expect('closed forest, sword + shield + slingshot: bridge opens', ['KokiriSword', 'DekuShield', 'Slingshot'],
       {'open_forest': False}, want=['LW Gift from Saria', 'LW Deku Scrub Near Bridge', 'KF GS Know It All House'])
expect('closed forest, sword + shield only: Deku Tree not beaten', ['KokiriSword', 'DekuShield'],
       {'open_forest': False}, not_want=['LW Gift from Saria'])
expect('bottle + sword: bean patch Skulltula (child only)', ['Bottle', 'KokiriSword'], {},
       age_of={'KF GS Bean Patch': ['child']})
expect('Song of Storms without an ocarina: grotto stays shut', ['SongOfStorms'], {}, not_want=['KF Storms Grotto Chest'])
expect('Song of Storms + ocarina: grotto opens', ['SongOfStorms', 'Ocarina'], {}, want=['KF Storms Grotto Chest'])
expect('adult with hookshot (night): House of Twins Skulltula', ['MasterSword', 'Hookshot'], {},
       age_of={'KF GS House of Twins': ['adult'], 'KF Adult Rupee Circle Center': ['adult']})
expect('adult without hookshot: no House of Twins Skulltula', ['MasterSword'], {}, not_want=['KF GS House of Twins'])
expect('Kokiri Sword chest is child-only (crawlspace)', ['MasterSword'], {}, age_of={'KF Kokiri Sword Chest': ['child']})
expect('pots are one check per age (separate objects in the child and adult maps)', ['MasterSword'], {},
       age_of={'KF House of Twins Child Pot 1': ['child'], 'KF House of Twins Adult Pot 1': ['adult']})

# Lost Woods
expect('Skull Kid needs Saria\'s Song and an ocarina', ['SariasSong'], {}, not_want=['LW Skull Kid'])
expect('Skull Kid with song + ocarina (child only)', ['SariasSong', 'Ocarina'], {}, age_of={'LW Skull Kid': ['child']})
expect('shortcuts grotto needs explosives', [], {}, not_want=['LW Near Shortcuts Grotto Bush 1'])
expect('bomb bag opens both grottos', ['BombBag'], {},
       want=['LW Near Shortcuts Grotto Bush 1', 'LW Boulder Over Scrubs Grotto'])
expect('bomb bag, no bracelet, bomb fix off: no bombs', ['BombBag'],
       {'start_with_goron_bracelet': False, 'bombs_without_bracelet': False},
       not_want=['LW Near Shortcuts Grotto Bush 1'])
expect('bomb bag, no bracelet, bombs_without_bracelet fix on: bombs work', ['BombBag'],
       {'start_with_goron_bracelet': False, 'bombs_without_bracelet': True}, want=['LW Near Shortcuts Grotto Bush 1'])
expect('adult Mido blocks the back half without Saria\'s Song', ['MasterSword', 'BombBag'], {},
       age_of={'LW Boulder Near Sacred Forest Meadow': ['child']})
expect('adult past Mido with Saria\'s Song', ['MasterSword', 'BombBag', 'SariasSong', 'Ocarina'], {},
       age_of={'LW Boulder Near Sacred Forest Meadow': ['child', 'adult']})
expect('closed forest: the Lost Woods are still open to a child', ['SariasSong', 'Ocarina'], {'open_forest': False},
       want=['LW Skull Kid', 'LW Ocarina Memory Game'])

# Sacred Forest Meadow
expect('child with nothing: stuck at the Wolfos gate', [], {},
       want=['SFM Entryway Bush 1'], not_want=['SFM Bush Near Gate 1', 'Song from Saria'])
expect('child with the Kokiri Sword + letter: gate opens, Saria\'s Song', ['KokiriSword', 'ZeldasLetter'], {},
       want=['SFM Bush Near Gate 1', 'Song from Saria'], age_of={'Song from Saria': ['child']})
expect('Wolfos grotto needs the Song of Storms (remake)', ['KokiriSword', 'BombBag'], {},
       not_want=['SFM Wolfos Grotto Chest'])
expect('Wolfos grotto with storms + ocarina', ['KokiriSword', 'SongOfStorms', 'Ocarina'], {},
       age_of={'SFM Wolfos Grotto Chest': ['child']})
expect('upper grotto: bombs and the Song of Time', ['KokiriSword', 'BombBag', 'SongOfTime', 'Ocarina'], {},
       want=['SFM Upper Grotto Chest'])
expect('upper grotto without the Song of Time: chest out of reach', ['KokiriSword', 'BombBag', 'Ocarina'], {},
       not_want=['SFM Upper Grotto Chest'])
expect('adult with hookshot + Saria\'s Song: Skulltula and Sheik', ['MasterSword', 'Hookshot', 'SariasSong', 'Ocarina'],
       {}, age_of={'SFM GS': ['adult'], 'Sheik in Forest': ['adult']})
expect('adult Skulltula without the hookshot (a jump reaches it)', ['MasterSword', 'SariasSong', 'Ocarina'], {},
       age_of={'SFM GS': ['adult']})
expect('adult without Saria\'s Song: blocked by Mido', ['MasterSword', 'Hookshot'], {}, not_want=['Sheik in Forest'])

print('\n%d failed' % failures)
sys.exit(1 if failures else 0)
