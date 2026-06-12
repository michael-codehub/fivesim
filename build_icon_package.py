#!/usr/bin/env python3
"""
Wraps fivesim/assets/logo.png into a Sims 4 .package as a PNG resource
(type 0x2F7D0004, instance = modinfo.LOGO_INSTANCE) for dialog/notification icons.

DBPF layout + zlib compression conventions verified byte-for-byte against the
shipping Sims4CommunityLibrary package (the known-loading reference).

Usage:  python build_icon_package.py  ->  dist/5imulites_icons.package
"""
import os
import struct
import zlib
import importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location('_fivesim_modinfo', os.path.join(ROOT, 'fivesim', 'modinfo.py'))
_modinfo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_modinfo)
LOGO_INSTANCE = _modinfo.LOGO_INSTANCE

PNG = os.path.join(ROOT, 'fivesim', 'assets', 'logo.png')
OUT_DIR = os.path.join(ROOT, 'dist')
OUT = os.path.join(OUT_DIR, '5imulites_icons.package')

TYPE_PNG = 0x2F7D0004
GROUP = 0x00000000


def main():
    if not os.path.exists(PNG):
        print('missing', PNG)
        return 1
    with open(PNG, 'rb') as f:
        raw = f.read()
    comp = zlib.compress(raw, 9)

    os.makedirs(OUT_DIR, exist_ok=True)
    header = bytearray(96)
    header[0:4] = b'DBPF'
    struct.pack_into('<I', header, 0x04, 2)
    struct.pack_into('<I', header, 0x08, 1)

    body = comp
    index = struct.pack('<I', 0)
    index += struct.pack('<IIII', TYPE_PNG, GROUP, (LOGO_INSTANCE >> 32) & 0xFFFFFFFF, LOGO_INSTANCE & 0xFFFFFFFF)
    index += struct.pack('<I', 96)                         # offset
    index += struct.pack('<I', len(comp) | 0x80000000)     # compressed size (+ext bit)
    index += struct.pack('<I', len(raw))                   # uncompressed size
    index += struct.pack('<H', 0x5A42)                     # zlib
    index += struct.pack('<H', 0x0001)                     # committed

    struct.pack_into('<I', header, 0x24, 1)
    struct.pack_into('<I', header, 0x2C, len(index))
    struct.pack_into('<I', header, 0x3C, 3)
    struct.pack_into('<I', header, 0x40, 96 + len(body))

    with open(OUT, 'wb') as f:
        f.write(header)
        f.write(body)
        f.write(index)

    print('wrote %s (%d bytes, logo %d -> %d zlib)' % (OUT, os.path.getsize(OUT), len(raw), len(comp)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
