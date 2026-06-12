#!/usr/bin/env python3
"""
Package the fivesim mod into `fivesim.ts4script` (a renamed ZIP) for The Sims 4.

The Sims 4 embeds CPython 3.7. If you build with python 3.7 the matching .pyc is
included (fastest load); otherwise we ship the .py sources and the game compiles
them on load. Either way the mod works.

Usage:  python build.py        ->  ./dist/fivesim.ts4script
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
PKG = 'fivesim'
SRC = os.path.join(ROOT, PKG)
OUT_DIR = os.path.join(ROOT, 'dist')
OUT = os.path.join(OUT_DIR, 'fivesim.ts4script')


def main():
    if not os.path.isdir(SRC):
        print('missing package dir:', SRC)
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)

    py37 = sys.version_info[:2] == (3, 7)
    if py37:
        import compileall
        compileall.compile_dir(SRC, quiet=1)
        print('compiled .pyc with CPython 3.7 (fast load)')
    else:
        print('WARNING: not running CPython 3.7 (got %d.%d) — shipping .py only; '
              'the game will compile on load. For best results build with 3.7.'
              % sys.version_info[:2])

    n = 0
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _dirs, files in os.walk(SRC):
            for fn in files:
                if fn.endswith('.py') or (py37 and fn.endswith('.pyc')):
                    full = os.path.join(base, fn)
                    arc = os.path.relpath(full, ROOT)  # keep "fivesim/..." prefix
                    z.write(full, arc)
                    n += 1
    print('wrote %s (%d files)' % (OUT, n))
    print('Install: copy it into  Documents/Electronic Arts/The Sims 4/Mods/')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
