# Self-diagnostic loader. Writes a small file to your Sims 4 user folder so we
# can see, with zero guessing, whether the mod's Python actually ran:
#   fivesim_LOADED.txt  -> the mod imported fine (commands are registered)
#   fivesim_ERROR.txt   -> it crashed on load; the file holds the exact traceback
import os
import traceback


def _diag(name, text):
    targets = [
        os.path.join(os.path.expanduser('~'), 'Documents', 'Electronic Arts', 'The Sims 4'),
        os.path.expanduser('~'),
        os.getcwd(),
    ]
    for base in targets:
        try:
            with open(os.path.join(base, name), 'w') as f:
                f.write(text)
            return
        except Exception:
            continue


# remove any stale error from a previous run, then mark that we started
try:
    for b in (os.path.join(os.path.expanduser('~'), 'Documents', 'Electronic Arts', 'The Sims 4'), os.path.expanduser('~')):
        try:
            os.remove(os.path.join(b, 'fivesim_ERROR.txt'))
        except Exception:
            pass
except Exception:
    pass

_diag('fivesim_LOADED.txt', 'fivesim package import started\n')

try:
    from . import main_loop  # registers console commands + starts the bridge
    _diag('fivesim_LOADED.txt', 'fivesim loaded OK — commands registered, bridge starting.\n')
except Exception:
    _diag('fivesim_ERROR.txt', 'fivesim FAILED to load:\n\n' + traceback.format_exc())
    raise
