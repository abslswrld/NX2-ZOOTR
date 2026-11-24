"""What a file's entry in the resource size table has to be, from the file's contents.

The game allocates each file's memory from its entry. The entry is not the file's size plus a fixed margin:
it is the file's size rounded up to 32, plus what the loaded form of that kind of file takes, and for the
parameter files (.bgyml) more for each element of their lists and tables. A file that gains elements and only
has its growth in bytes added runs out of memory while loading (2026-11-18: the songs' actor files, three
components added, crashed the game: the table of components could not be allocated).

The rules below were fitted on the game's own files and are exact for every game file of each kind, except
where noted (tests/size_check.py checks them against every file of the game):

    kind                         entry
    .bfevfl, .baev               size32 + 272
    .pack, Mals/*.sarc           size32 + 312
    .byml                        size32 + 264     (Sound/*.casset.byml: + 520; two files have more, see
                                 tests/size_check.py: an edited file keeps its own headroom, `ref`)
    .bntx in Tex/                size32 + 264     (those in UI/ have more: no rule)
    .ainb                        size32 + 376, and with an expression block (EXB): + 16 + its number of
                                 signatures * 4 rounded up to 8
    .bgyml                       size32 + a constant per type + a cost per element of each list and per
                                 entry of each table with free keys (a struct's members cost nothing):
                                 BGYML below for the types the builder adds elements to; STRUCTS for types
                                 where only the lists count

`size32` is the size rounded up to a multiple of 32. Files of other kinds (.bfres, .asb, ...) have no rule
here: they keep the headroom of a game file (`ref`).
"""
import struct

from formats import byml


class Unknown(Exception):
    """the entry can't be worked out safely"""


def size32(n):
    return (n + 31) // 32 * 32


# .bgyml: type (the part of the name before .bgyml) -> (constant, {container: cost per element}).
# A container is named by its place in the file: /Key for a member, [] for the elements of a list, <Type>
# for a struct that names its type ($type), and a closing {} or [] for what is counted: the members of a
# table/struct or the elements of a list (a <Type> alone counts the structs of that type). Every container
# the game's files of that type have is listed, a cost of 0 included (structs); a file with any other
# container is refused.
BGYML = {
    'engine__actor__ActorParam': (5144, {'{}': 0, '/Components{}': 48}),
    'engine__actor__GameParameterTable': (5128, {'{}': 0, '/Components{}': 48}),
    'engine__event__EventSettingComponentList': (5128, {'{}': 0, '/Components{}': 48}),
    'engine__component__AnimationParam': (5096, {'{}': 0, '/AnimationResources[]': 88,
                                                 '/AnimationResources[]{}': 0}),
    'engine__component__ModelInfo': (5192, {'{}': 0, '/DebugModelScale{}': 0, '/ModelVariationAnims[]': 80,
                                            '/ModelVariationAnims[]{}': 0, '/SubModels[]': 104,
                                            '/SubModels[]{}': 0}),
    'engine__component__BlackboardInfo': (5096, {'{}': 0, '/BlackboardParamTables[]': 8}),
    'engine__actor__AIInfo': (5088, {'{}': 0}),
    'game__component__PouchContentParam': (5216, {'{}': 0, '/GetDemoOffsetPos{}': 0}),
    'game__pouchcontent__PriceParam': (5064, {'{}': 0}),
    # the actors an actor holds: 224 per slot, 104 per bone a slot is bound to (exact for the game's 98 files)
    'game__component__ActorHolderParam': (5128, {
        '{}': 0, '/ActorHoldSettings{}': 224, '/ActorHoldSettings/*{}': 0,
        '/ActorHoldSettings/*/ModelBindSettings[]': 104, '/ActorHoldSettings/*/ModelBindSettings[]{}': 0,
        '/ActorHoldSettings/*/ModelBindSettings[]/RotOffset{}': 0,
        '/ActorHoldSettings/*/ModelBindSettings[]/TransOffset{}': 0}),
    # the lights on actors' bones, one list per group: 160 per actor (exact for the game's 17 files)
    'game__gfx__LocationalLightRigGroupSetting': (5096, {'{}': 0, '/LightRigSettingList[]': 160,
                                                         '/LightRigSettingList[]{}': 0}),
    # the list of text colours. The game has one file of this type (8 colours, entry 6312 = size32 + 5864), so
    # what is constant and what is per colour cannot be told apart: the rule charges all of it per colour (733
    # each, constant 0), the most that file allows. It gives the game's entry for the game's file, and for a
    # longer list it can only be too much
    'game__ui__MessageColorTable': (0, {'{}': 0, '/MessageColorArray[]': 733, '/MessageColorArray[]{}': 0}),
}

# .bgyml types with a table whose keys are free names (the slots of ActorHoldSettings): in the containers of
# BGYML above, the name of an entry of such a table is written *
FREE_KEYS = {
    'game__component__ActorHolderParam': ('/ActorHoldSettings',),
}

# .bgyml types with no rule above, but whose tables are all structs: among the game's files of the type, those
# with the same lists (lengths, and types of their elements) all have the same headroom, however many members
# their structs have. A file of such a type may gain or lose struct members; its lists must stay as they are.
STRUCTS = {
    'game__component__AIScheduleParam',      # 502 files
    'game__component__ShopParam',            # 11 files
}

# other kinds: the constant
PLAIN = {
    'bfevfl': 272,
    'baev': 272,
    'pack': 312,
    'byml': 264,
}


def kind(path):
    return path.rsplit('.', 1)[-1]


def bgyml_type(path):
    parts = path.split('/')[-1].split('.')
    return parts[-2] if len(parts) >= 3 else ''


def containers(data):
    """{container: number of elements} of a BYML file (see BGYML)"""
    counts = {}

    def walk(v, where):
        if isinstance(v, dict):
            if '$type' in v:
                where += '<%s>' % v['$type']
                counts[where] = counts.get(where, 0) + 1
            counts[where + '{}'] = counts.get(where + '{}', 0) + len(v)
            for k, x in v.items():
                walk(x, where + '/' + str(k))
        elif isinstance(v, (list, tuple)):
            counts[where + '[]'] = counts.get(where + '[]', 0) + len(v)
            for x in v:
                walk(x, where + '[]')

    walk(byml.loads(data).root, '')
    return counts


def free_key(where, tables):
    """a container's name with the entry name of a free-key table (`tables`: their places) written *"""
    for t in tables:
        if where.startswith(t + '/'):
            rest = where[len(t) + 1:]
            end = min([rest.index(c) for c in '/{[<' if c in rest] or [len(rest)])
            return t + '/*' + rest[end:]
    return where


def exb_extra(data):
    """what an .ainb's expression block adds to its entry"""
    o_exb = struct.unpack_from('<I', data, 0x44)[0]
    if not o_exb:
        return 0
    if data[o_exb:o_exb + 4] != b'EXB ':
        raise Unknown('expression block not where expected')
    o_sig = struct.unpack_from('<I', data, o_exb + 0x20)[0]
    count = struct.unpack_from('<I', data, o_exb + o_sig)[0]
    return 16 + (4 * count + 7) // 8 * 8


def rule(path, data):
    """the entry the game's own files of this kind have for these contents; None: no rule for this kind"""
    k = kind(path)
    if k == 'byml' and path.endswith('.casset.byml'):
        return size32(len(data)) + 520
    if k in PLAIN:
        return size32(len(data)) + PLAIN[k]
    if k == 'sarc' and path.startswith('Mals/'):
        return size32(len(data)) + 312
    if k == 'bntx' and path.startswith('Tex/'):
        return size32(len(data)) + 264
    if k == 'ainb':
        if data[:4] != b'AIB ':
            raise Unknown('%s is not an AINB file' % path)
        return size32(len(data)) + 376 + exb_extra(data)
    if k == 'bgyml' and bgyml_type(path) in BGYML:
        const, costs = BGYML[bgyml_type(path)]
        total = size32(len(data)) + const
        for where, n in containers(data).items():
            where = free_key(where, FREE_KEYS.get(bgyml_type(path), ()))
            if where not in costs:
                raise Unknown('%s: no game file of its type has %s: what it costs is not known' % (path, where))
            total += costs[where] * n
        return total
    return None


def entry(path, data, ref_entry=None, ref_data=None):
    """the entry `path` needs with the contents `data`. ref_entry, ref_data: a game file of the same kind
    and its entry (the file itself before it was edited, or the file a new one was made from): the result
    keeps at least its headroom. Raises Unknown when the kind has no rule and the file has more elements
    in a list or table than the reference (what they cost is not known)."""
    need = rule(path, data)
    if ref_entry is None:
        if need is None:
            raise Unknown('%s: no size rule for this kind of file and no game file to go by' % path)
        return need
    keep = ref_entry - size32(len(ref_data)) + size32(len(data))
    if need is not None:
        return max(need, keep)
    if kind(path) == 'bgyml' and data != ref_data:
        was, now = containers(ref_data), containers(data)
        structs = bgyml_type(path) in STRUCTS
        more = sorted(w for w, n in now.items() if n > was.get(w, 0) and not (structs and w.endswith('{}')))
        if more:
            raise Unknown('%s: more elements than the game file it comes from (%s) and no size rule for its '
                          'type: add one to tools/sizes.py (BGYML)' % (path, ', '.join(more)))
    return keep
