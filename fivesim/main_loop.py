# Starts the bridge on zone load and drains the command queue on the main thread
# via a real-time repeating alarm (keeps working even while the game is paused).
import os
import time
import alarms
import clock
import zone
from .injector import inject
from . import bridge_server, state_reader, action_executor
from . import commands  # noqa: F401  (registers the in-game console commands)
from .modinfo import TOKEN_FILENAMES

# Real pie-menu button — only loads if Sims4CommunityLibrary is installed.
# Without S4CL this is skipped and the console commands remain the entry point.
try:
    from . import interactions  # noqa: F401
except Exception:
    pass

_OWNER = object()        # keep a strong ref or the alarm gets GC-cancelled
_alarm = None
_started = False


def _refresh_snapshot():
    agents = {}
    for sid in state_reader.list_sim_ids():
        st = state_reader.build_state_for(sid)
        if st is not None:
            agents[str(sid)] = st
    bridge_server.publish_snapshot({'agents': agents, 'ts': time.time()})


def _drain(_handle):
    # RUNS ON MAIN THREAD -> safe to touch game state. Keep it short.
    drained = 0
    while drained < 32:
        try:
            rid, cmd = bridge_server.cmd_queue.get_nowait()
        except Exception:
            break
        drained += 1
        try:
            result = action_executor.execute_action(cmd.get('action', cmd))
        except Exception as e:
            result = {'ok': False, 'error': 'exec_exc: %s' % e}
        bridge_server.put_result(rid, result)
    try:
        _refresh_snapshot()
    except Exception:
        pass


def start_drain():
    global _alarm
    if _alarm is not None:
        return
    _alarm = alarms.add_alarm_real_time(
        _OWNER, clock.interval_in_real_seconds(0.25), _drain, repeating=True)


def _load_local_token():
    candidates = []
    home = os.path.expanduser('~')
    for name in TOKEN_FILENAMES:
        candidates.append(name)
        candidates.append(os.path.join(home, name))
        candidates.append(os.path.join(home, 'Documents', 'Electronic Arts', 'The Sims 4', name))
    for path in candidates:
        try:
            with open(path) as f:
                tok = f.read().strip()
                if tok:
                    return tok
        except Exception:
            continue
    return None


def start_all():
    global _started
    if _started:
        return
    _started = True
    bridge_server.set_token(_load_local_token())
    bridge_server.start_server()
    start_drain()


@inject(zone.Zone, 'do_zone_spin_up')
def _fivesim_on_zone_load(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)     # always chain + return original
    try:
        start_all()
    except Exception:
        pass
    return result
