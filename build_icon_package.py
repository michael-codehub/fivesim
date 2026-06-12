#!/usr/bin/env python3
"""
Best-effort: wrap fivesim/assets/logo.png into a Sims 4 .package as a PNG resource
so it can be used as the in-game notification/dialog icon.

The instance id matches fivesim/modinfo.py LOGO_INSTANCE, and the mod references
the same key. Output: dist/5imulites_icons.package — drop it in your Mods folder
ALONGSIDE the .ts4script.

This hand-writes a DBPF 2.1 package (one uncompressed PNG resource). It's
untested across every game patch — if the icon doesn't appear, repackage the PNG
in Sims 4 Studio instead (Tools -> Extract/Import, type 0x2F7D0004 PNG, instance
= 0x5130A1A1A1A10001). The mod degrades gracefully (no icon) either way.

Usage:  python build_icon_package.py
"""
import os
import struct

ROOT = os.path.dirname(os.path.abspath(__file__))
PNG = os.path.join(ROOT, 'fivesim', 'assets', 'logo.png')
OUT_DIR = os.path.join(ROOT, 'dist')
OUT = os.path.join(OUT_DIR, '5imulites_icons.package')

TYPE_PNG = 0x2F7D0004
GROUP = 0x00000000
INSTANCE = 0x5130A1A1A1A10001   # must equal modinfo.LOGO_INSTANCE


def main():
    if not os.path.exists(PNG):
        print('missing', PNG)
        return 1
    with open(PNG, 'rb') as f:
        data = f.read()

    os.makedirs(OUT_DIR, exist_ok=True)
    inst_hi = (INSTANCE >> 32) & 0xFFFFFFFF
    inst_lo = INSTANCE & 0xFFFFFFFF
    data_offset = 96
    index_offset = data_offset + len(data)

    # index: flags(0) + one full entry (type,group,instHi,instLo,offset,size,mem,comp,commit)
    index = struct.pack('<I', 0)
    index += struct.pack('<IIII', TYPE_PNG, GROUP, inst_hi, inst_lo)
    index += struct.pack('<I', data_offset)
    index += struct.pack('<I', len(data) | 0x80000000)   # file size (hi bit set, v2 convention)
    index += struct.pack('<I', len(data))                 # uncompressed size
    index += struct.pack('<H', 0x0000)                    # compression: none
    index += struct.pack('<H', 0x0001)                    # committed

    # DBPF 2.1 header (96 bytes)
    h = bytearray(96)
    h[0:4] = b'DBPF'
    struct.pack_into('<I', h, 0x04, 2)            # major
    struct.pack_into('<I', h, 0x08, 1)            # minor
    struct.pack_into('<I', h, 0x24, 1)            # index entry count
    struct.pack_into('<I', h, 0x2C, len(index))   # index size
    struct.pack_into('<I', h, 0x3C, 3)            # index minor version (TS4)
    struct.pack_into('<I', h, 0x40, index_offset) # index offset

    with open(OUT, 'wb') as f:
        f.write(h)
        f.write(data)
        f.write(index)

    print('wrote %s (%d bytes, logo %d bytes)' % (OUT, os.path.getsize(OUT), len(data)))
    print('Install: copy it into Mods/ alongside fivesim.ts4script.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
