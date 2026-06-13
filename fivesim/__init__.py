# Self-diagnostic loader. Writes a marker file RIGHT NEXT TO this mod (in your
# Mods folder, derived from __file__) plus a few fallbacks, so it can't get lost
# to OneDrive-redirected Documents:
#   fivesim_LOADED.txt  -> the mod imported fine (commands are registered)
#   fivesim_ERROR.txt   -> it crashed on load; the file holds the exact traceback
import os
import traceback


def _targets():
    out = []
    # 1) the Mods folder itself, derived from this file's path inside the .ts4script
    try:
        here = os.path.dirname(os.path.abspath(__file__))           # .../Mods/fivesim.ts4script/fivesim
        out.append(os.path.dirname(os.path.dirname(here)))          # .../Mods
        out.append(os.path.dirname(here))                           # .../fivesim.ts4script (parent)
    except Exception:
        pass
    # 2) common user-folder locations (incl. OneDrive-redirected Documents)
    home = os.path.expanduser('~')
    for docs in ('Documents', os.path.join('OneDrive', 'Documents'),
                 os.path.join('OneDrive - Personal', 'Documents')):
        out.append(os.path.join(home, docs, 'Electronic Arts', 'The Sims 4'))
    out.append(home)
    try:
        out.append(os.getcwd())
    except Exception:
        pass
    return out


def _diag(name, text):
    for base in _targets():
        try:
            with open(os.path.join(base, name), 'w') as f:
                f.write(text)
        except Exception:
            continue


# delete any stale error file from a previous run
for base in _targets():
    try:
        os.remove(os.path.join(base, 'fivesim_ERROR.txt'))
    except Exception:
        pass
_diag('fivesim_LOADED.txt', 'fivesim package import started\n')

try:
    from . import main_loop  # registers console commands + starts the bridge
    _diag('fivesim_LOADED.txt', 'fivesim loaded OK - commands registered, bridge starting.\n')
except Exception:
    _diag('fivesim_ERROR.txt', 'fivesim FAILED to load:\n\n' + traceback.format_exc())
    raise
