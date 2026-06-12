#!/usr/bin/env python3
"""
Builds 5imulites_interactions.package — the DBPF that adds the real pie-menu
button to Sims. It contains one Interaction tuning (type 0xE882D22F, stored as
raw XML) per action, plus an English STBL (type 0x220557DA) with the pie-menu
labels. The tuning `s=` ids and label keys come from fivesim/modinfo.py and must
match interactions.py (which provides the Python classes).

Needs the mod + Sims4CommunityLibrary installed to actually appear in-game.
If the game ignores it, rebuild the tuning/STBL in Sims 4 Studio (the format is
otherwise correct). The mod still works via console commands without it.

Usage:  python build_interaction_package.py   ->  dist/5imulites_interactions.package
"""
import os
import struct
import importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))

# load modinfo.py standalone (importing the fivesim package would pull in game-only
# modules like `alarms`, which don't exist outside the game)
_spec = importlib.util.spec_from_file_location('_fivesim_modinfo', os.path.join(ROOT, 'fivesim', 'modinfo.py'))
_modinfo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_modinfo)
INTERACTIONS = _modinfo.INTERACTIONS
STBL_INSTANCE = _modinfo.STBL_INSTANCE

OUT_DIR = os.path.join(ROOT, 'dist')
OUT = os.path.join(OUT_DIR, '5imulites_interactions.package')

TYPE_TUNING = 0xE882D22F
TYPE_STBL = 0x220557DA
GROUP_TUNING = 0x00000000
GROUP_STBL = 0x80000000


def tuning_xml(class_name, s_id, key, _label):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<I c="%s" i="interaction" m="fivesim.interactions" n="fivesim:%s" s="%d">\n'
        '  <T n="display_name">0x%08X</T>\n'
        '  <E n="target_type">ACTOR</E>\n'
        '  <T n="allow_user_directed">True</T>\n'
        '  <T n="allow_autonomous">False</T>\n'
        '</I>\n'
    ) % (class_name, class_name, s_id, key)


def build_stbl(entries):
    # STBL v5 (little-endian). entries = list of (key_uint32, text)
    blob = bytearray()
    blob += b'STBL'
    blob += struct.pack('<H', 5)          # version
    blob += struct.pack('<B', 0)          # compressed (unused)
    blob += struct.pack('<Q', len(entries))  # string count
    blob += b'\x00\x00'                    # reserved
    total = sum(len(t.encode('utf-8')) for _, t in entries)
    blob += struct.pack('<I', total)      # mnStringLength (UTF-8 byte total)
    for key, text in entries:
        b = text.encode('utf-8')
        blob += struct.pack('<I', key & 0xFFFFFFFF)  # key hash
        blob += struct.pack('<B', 0)                  # flags
        blob += struct.pack('<H', len(b))             # size (utf-8 bytes)
        blob += b
    return bytes(blob)


def write_package(resources):
    # resources = list of (type, group, instance64, data_bytes), uncompressed
    os.makedirs(OUT_DIR, exist_ok=True)
    header = bytearray(96)
    header[0:4] = b'DBPF'
    struct.pack_into('<I', header, 0x04, 2)  # major
    struct.pack_into('<I', header, 0x08, 1)  # minor

    body = bytearray()
    placed = []  # (type, group, inst, offset, size)
    offset = 96
    for (rtype, group, inst, data) in resources:
        body += data
        placed.append((rtype, group, inst, offset, len(data)))
        offset += len(data)

    index = struct.pack('<I', 0)  # index flags: 0 = every field present per entry
    for (rtype, group, inst, off, size) in placed:
        inst_hi = (inst >> 32) & 0xFFFFFFFF
        inst_lo = inst & 0xFFFFFFFF
        index += struct.pack('<IIII', rtype, group, inst_hi, inst_lo)
        index += struct.pack('<I', off)
        index += struct.pack('<I', size | 0x80000000)  # file size (hi bit, v2)
        index += struct.pack('<I', size)               # uncompressed size
        index += struct.pack('<H', 0x0000)             # compression: none
        index += struct.pack('<H', 0x0001)             # committed

    index_offset = 96 + len(body)
    struct.pack_into('<I', header, 0x24, len(placed))    # entry count
    struct.pack_into('<I', header, 0x2C, len(index))     # index size
    struct.pack_into('<I', header, 0x3C, 3)              # index minor version
    struct.pack_into('<I', header, 0x40, index_offset)   # index offset

    with open(OUT, 'wb') as f:
        f.write(header)
        f.write(body)
        f.write(index)


def main():
    resources = []
    stbl_entries = []
    for (class_name, s_id, key, label) in INTERACTIONS:
        xml = tuning_xml(class_name, s_id, key, label).encode('utf-8')
        resources.append((TYPE_TUNING, GROUP_TUNING, s_id, xml))
        stbl_entries.append((key, label))
    resources.append((TYPE_STBL, GROUP_STBL, STBL_INSTANCE, build_stbl(stbl_entries)))

    write_package(resources)
    print('wrote %s (%d bytes, %d interactions + 1 STBL)' % (OUT, os.path.getsize(OUT), len(INTERACTIONS)))
    print('Install: copy it into Mods/ next to fivesim.ts4script (needs S4CL).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
