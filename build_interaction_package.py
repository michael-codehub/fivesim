#!/usr/bin/env python3
"""
Builds 5imulites_interactions.package — the pie-menu button on every Sim.

Contents (structure mirrors Sims4CommunityLibrary's own shipping package, which
is the proven-loading reference):
  - 3 Interaction tunings (type 0xE882D22F, zlib-compressed raw XML)
  - 1 PieMenuCategory tuning (type 0x03E9D964) -> the "5imulites" submenu,
    with our logo PNG as its icon (TGI reference into 5imulites_icons.package)
  - 1 English STBL (type 0x220557DA, group 0x00000000) with the labels

Requires the fivesim mod + Sims4CommunityLibrary in Mods/ to appear in-game.

Usage:  python build_interaction_package.py  ->  dist/5imulites_interactions.package
"""
import os
import struct
import zlib
import importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))

# load modinfo.py standalone (importing the fivesim package would pull in game-only
# modules like `alarms`, which don't exist outside the game)
_spec = importlib.util.spec_from_file_location('_fivesim_modinfo', os.path.join(ROOT, 'fivesim', 'modinfo.py'))
_modinfo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_modinfo)
INTERACTIONS = _modinfo.INTERACTIONS
STBL_INSTANCE = _modinfo.STBL_INSTANCE
CATEGORY_ID = _modinfo.CATEGORY_ID
KEY_CATEGORY = _modinfo.KEY_CATEGORY
LABEL_CATEGORY = _modinfo.LABEL_CATEGORY
LOGO_INSTANCE = _modinfo.LOGO_INSTANCE

OUT_DIR = os.path.join(ROOT, 'dist')
OUT = os.path.join(OUT_DIR, '5imulites_interactions.package')

TYPE_TUNING = 0xE882D22F
TYPE_PIE_CATEGORY = 0x03E9D964
TYPE_STBL = 0x220557DA
GROUP_TUNING = 0x00000000
GROUP_STBL = 0x00000000          # English STBL lives at group 0 (S4CL convention)


def interaction_xml(class_name, s_id, key):
    # field set copied from S4CL's shipping debug interactions (proven to load),
    # minus cheat/debug gating so ours shows in the normal pie menu.
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<I c="%s" i="interaction" m="fivesim.interactions" n="fivesim:%s" s="%d">\n'
        '  <V t="disabled" n="_saveable" />\n'
        '  <T n="allow_autonomous">False</T>\n'
        '  <T n="category">%d<!--PieMenuCategory: fivesim_Pie_5imulites--></T>\n'
        '  <T n="display_name">0x%08X</T>\n'
        '  <L n="interaction_category_tags">\n'
        '    <E>Interaction_Super</E>\n'
        '    <E>Interaction_All</E>\n'
        '  </L>\n'
        '  <T n="pie_menu_priority">9</T>\n'
        '  <U n="progress_bar_enabled">\n'
        '    <T n="bar_enabled">False</T>\n'
        '  </U>\n'
        '  <E n="target_type">OBJECT</E>\n'
        '</I>\n'
    ) % (class_name, class_name, s_id, CATEGORY_ID, key)


def category_xml():
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<I c="PieMenuCategory" i="pie_menu_category" m="interactions.pie_menu_category" '
        'n="fivesim:Pie_5imulites" s="%d">\n'
        '  <T n="_collapsible">False</T>\n'
        '  <T n="_display_name">0x%08X</T>\n'
        '  <T n="_display_priority">200</T>\n'
        '  <T n="_icon">2f7d0004:00000000:%016X</T>\n'
        '</I>\n'
    ) % (CATEGORY_ID, KEY_CATEGORY, LOGO_INSTANCE)


def build_stbl(entries):
    # STBL v5, little-endian. mnStringLength counts utf-8 bytes PLUS one per
    # string (null-terminated convention — verified against S4CL's own STBL).
    blob = bytearray()
    blob += b'STBL'
    blob += struct.pack('<H', 5)
    blob += struct.pack('<B', 0)
    blob += struct.pack('<Q', len(entries))
    blob += b'\x00\x00'
    total = sum(len(t.encode('utf-8')) + 1 for _, t in entries)
    blob += struct.pack('<I', total)
    for key, text in entries:
        b = text.encode('utf-8')
        blob += struct.pack('<I', key & 0xFFFFFFFF)
        blob += struct.pack('<B', 0)
        blob += struct.pack('<H', len(b))
        blob += b
    return bytes(blob)


def write_package(resources):
    # resources = list of (type, group, instance64, raw_bytes); zlib-compressed
    # on disk (compression 0x5A42), matching how S4CL ships its package.
    os.makedirs(OUT_DIR, exist_ok=True)
    header = bytearray(96)
    header[0:4] = b'DBPF'
    struct.pack_into('<I', header, 0x04, 2)
    struct.pack_into('<I', header, 0x08, 1)

    body = bytearray()
    placed = []
    offset = 96
    for (rtype, group, inst, raw) in resources:
        comp = zlib.compress(raw, 9)
        body += comp
        placed.append((rtype, group, inst, offset, len(comp), len(raw)))
        offset += len(comp)

    index = struct.pack('<I', 0)
    for (rtype, group, inst, off, csize, rsize) in placed:
        index += struct.pack('<IIII', rtype, group, (inst >> 32) & 0xFFFFFFFF, inst & 0xFFFFFFFF)
        index += struct.pack('<I', off)
        index += struct.pack('<I', csize | 0x80000000)
        index += struct.pack('<I', rsize)
        index += struct.pack('<H', 0x5A42)   # zlib
        index += struct.pack('<H', 0x0001)   # committed

    struct.pack_into('<I', header, 0x24, len(placed))
    struct.pack_into('<I', header, 0x2C, len(index))
    struct.pack_into('<I', header, 0x3C, 3)
    struct.pack_into('<I', header, 0x40, 96 + len(body))

    with open(OUT, 'wb') as f:
        f.write(header)
        f.write(body)
        f.write(index)


def main():
    resources = []
    stbl_entries = [(KEY_CATEGORY, LABEL_CATEGORY)]
    for (class_name, s_id, key, label) in INTERACTIONS:
        resources.append((TYPE_TUNING, GROUP_TUNING, s_id, interaction_xml(class_name, s_id, key).encode('utf-8')))
        stbl_entries.append((key, label))
    resources.append((TYPE_PIE_CATEGORY, GROUP_TUNING, CATEGORY_ID, category_xml().encode('utf-8')))
    resources.append((TYPE_STBL, GROUP_STBL, STBL_INSTANCE, build_stbl(stbl_entries)))

    write_package(resources)
    print('wrote %s (%d bytes: %d interactions + submenu + STBL)' % (OUT, os.path.getsize(OUT), len(INTERACTIONS)))
    print('Install: copy into Mods/ next to fivesim.ts4script (needs S4CL).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
