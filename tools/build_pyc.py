#!/usr/bin/env python3
"""
Build dist/fivesim.ts4script as a SOURCELESS, .pyc-only archive — exactly how
Sims4CommunityLibrary ships (the only layout the current game patch loads).

MUST run under CPython 3.7 (the version The Sims 4 embeds) so the .pyc magic
matches. Bytecode is OS-independent, so a Linux/macOS 3.7 build loads fine in the
game's Windows 3.7. Run via GitHub Actions (.github/workflows/build.yml).

Layout produced inside the zip:  fivesim/<module>.pyc   (legacy, next to where
the .py would be — NOT __pycache__, which zipimport ignores).
"""
import os
import sys
import zipfile
import py_compile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, 'fivesim')
OUT_DIR = os.path.join(ROOT, 'dist')
OUT = os.path.join(OUT_DIR, 'fivesim.ts4script')


def main():
    if sys.version_info[:2] != (3, 7):
        print('ERROR: must run under CPython 3.7 (got %d.%d)' % sys.version_info[:2])
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)

    compiled = []
    for base, _dirs, files in os.walk(PKG):
        for fn in files:
            if not fn.endswith('.py'):
                continue
            src = os.path.join(base, fn)
            cfile = src[:-3] + '.pyc'  # legacy sourceless location: fivesim/x.pyc
            py_compile.compile(
                src, cfile=cfile, doraise=True,
                invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
            )
            compiled.append(cfile)

    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        for cfile in compiled:
            arc = os.path.relpath(cfile, ROOT)  # keep "fivesim/...pyc"
            z.write(cfile, arc)

    print('wrote %s with %d .pyc (sourceless, 3.7):' % (OUT, len(compiled)))
    for c in compiled:
        print('  ', os.path.relpath(c, ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
