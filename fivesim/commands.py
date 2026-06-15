# In-game console commands (Ctrl+Shift+C). No .package needed — pure Python.
# They configure and drive the 5imulites host (the sidecar brain) from inside
# the game, so the AI actually plays your Sims. Open the cheat console and type
# e.g.  fivesim.setup
import sims4.commands
import services
from . import host_client
from .modinfo import HOST, PORT

AGENTS = ['gpt', 'claude', 'gemini', 'deepseek', 'qwen']
BRIDGE_URL = 'http://%s:%d' % (HOST, PORT)


def _out(conn):
    return sims4.commands.CheatOutput(conn)


@sims4.commands.Command('fivesim.help', command_type=sims4.commands.CommandType.Live)
def fivesim_help(_connection=None):
    o = _out(_connection)
    o('5imulites commands:')
    o('  fivesim.setup                      open the guided setup (needs S4CL)')
    o('  fivesim.key <openrouter_key>       set the OpenRouter API key on the host')
    o('  fivesim.sims                       list your Sims and their sim_id')
    o('  fivesim.map <agent> <sim_id>       map an agent to a Sim (agents: %s)' % ', '.join(AGENTS))
    o('  fivesim.model <agent> <model>      set the model for an agent')
    o('  fivesim.connect                    point the host at this game bridge')
    o('  fivesim.bridge                     force-start + health-check the game bridge')
    o('  fivesim.act <action>               test an action in-game (work/sleep/eat/shower/toilet)')
    o('  fivesim.find <keyword>             list matching object interactions on the lot')
    o('  fivesim.start / fivesim.stop       start / stop the AI playing')
    o('  fivesim.status                     show host + engine status')


@sims4.commands.Command('fivesim.key', command_type=sims4.commands.CommandType.Live)
def fivesim_key(key=None, _connection=None):
    o = _out(_connection)
    if not key:
        return o('usage: fivesim.key <openrouter_key>')
    ok, res = host_client.set_key(key)
    o('API key saved on the host.' if ok else 'host unreachable: %s (is `npm run dev` running?)' % res.get('reason', res))


def _ensure_bridge():
    """Force-start the in-game bridge + drain alarm (idempotent, main-thread safe)."""
    try:
        from . import main_loop
        return main_loop.ensure_started()
    except Exception:
        return False


@sims4.commands.Command('fivesim.sims', command_type=sims4.commands.CommandType.Live)
def fivesim_sims(_connection=None):
    o = _out(_connection)
    _ensure_bridge()
    hh = services.active_household()
    if hh is None:
        return o('no active household — load a lot first')
    o('Your Sims (sim_id  name):')
    for si in hh.sim_info_gen():
        o('  %d  %s %s' % (si.sim_id, si.first_name, si.last_name))
    o('map them, e.g.:  fivesim.map gpt <sim_id>')


@sims4.commands.Command('fivesim.bridge', command_type=sims4.commands.CommandType.Live)
def fivesim_bridge(_connection=None):
    """Force-start the local game bridge and print its health (the thing the host app reads)."""
    o = _out(_connection)
    ok = _ensure_bridge()
    try:
        from . import main_loop
        d = main_loop.diagnostics()
        o('— 5imulites bridge (http://%s:%d) —' % (HOST, PORT))
        o('  server listening: %s' % d['server_up'])
        o('  drain alarm:      %s' % d['alarm_registered'])
        o('  sims in snapshot: %s' % d['snapshot_sims'])
        o('  active household: %s' % d['active_household'])
        if d.get('last_error'):
            o('  last error: %s' % d['last_error'].splitlines()[-1])
        if d['server_up'] and d['alarm_registered'] and d['snapshot_sims'] == 0 and not d['active_household']:
            o('  -> bridge is UP but no household loaded. Load a lot, then in the app press Load Sims.')
        elif d['server_up'] and d['alarm_registered']:
            o('  -> bridge healthy. In the app: Load Sims from game.')
    except Exception as e:
        o('bridge diagnostics failed: %r (started=%s)' % (e, ok))


@sims4.commands.Command('fivesim.act', command_type=sims4.commands.CommandType.Live)
def fivesim_act(action='sleep', sim_id: int = None, _connection=None):
    """Directly run one action on a Sim to test in-game actuation (no host/LLM)."""
    o = _out(_connection)
    ACTS = {
        'work':   {'type': 'go_to_work'},
        'sleep':  {'type': 'interaction', 'interaction': 'sleep_in_bed'},
        'eat':    {'type': 'interaction', 'interaction': 'eat_grab_quick'},
        'shower': {'type': 'interaction', 'interaction': 'shower'},
        'toilet': {'type': 'interaction', 'interaction': 'use_toilet'},
    }
    if action not in ACTS:
        return o('usage: fivesim.act <work|sleep|eat|shower|toilet> [sim_id]')
    if not sim_id:
        hh = services.active_household()
        if hh is None:
            return o('no active household — load a lot first')
        sims = list(hh.sim_info_gen())
        if not sims:
            return o('no sims in household')
        sim_id = sims[0].sim_id
    spec = dict(ACTS[action])
    spec['sim_id'] = int(sim_id)
    try:
        from . import action_executor
        res = action_executor.execute_action(spec)
        o('fivesim.act %s on sim %s -> %s' % (action, sim_id, res))
        if not res.get('ok'):
            o('  (if this fails, the in-game action layer is the problem, not the host)')
    except Exception as e:
        o('fivesim.act failed: %r' % e)


@sims4.commands.Command('fivesim.cam', command_type=sims4.commands.CommandType.Live)
def fivesim_cam(sim_id: int = None, _connection=None):
    """Focus + follow the camera on a Sim (test the auto-camera). No sim_id = first household Sim."""
    o = _out(_connection)
    if not sim_id:
        hh = services.active_household()
        sims = list(hh.sim_info_gen()) if hh is not None else []
        if not sims:
            return o('no sims in household')
        sim_id = sims[0].sim_id
    try:
        from . import action_executor
        res = action_executor.execute_action({'type': 'focus_camera', 'sim_id': int(sim_id), 'follow': True})
        o('fivesim.cam %s -> %s' % (sim_id, res))
    except Exception as e:
        o('fivesim.cam failed: %r' % e)


@sims4.commands.Command('fivesim.speed', command_type=sims4.commands.CommandType.Live)
def fivesim_speed(level=3, _connection=None):
    """Set game speed 0=pause 1=normal 2=fast 3=ultra (used to fast-forward long actions)."""
    o = _out(_connection)
    try:
        from . import action_executor
        action_executor._set_speed(int(level))
        o('game speed -> %s' % level)
    except Exception as e:
        o('fivesim.speed failed: %r' % e)


@sims4.commands.Command('fivesim.find', command_type=sims4.commands.CommandType.Live)
def fivesim_find(keyword='sleep', _connection=None):
    """List object super-affordances on the lot whose name contains <keyword>.
    Lets us discover the real interaction names for actuation."""
    o = _out(_connection)
    try:
        from . import action_executor
        om = services.object_manager()
        try:
            objects = list(om.get_all())
        except Exception:
            objects = list(om.values()) if hasattr(om, 'values') else []
        seen = {}
        for obj in objects:
            for aff in action_executor._obj_super_affordances(obj):
                nm = getattr(aff, '__name__', '') or ''
                if keyword.lower() in nm.lower() and nm not in seen:
                    seen[nm] = getattr(obj, 'definition', obj)
        o('affordances containing "%s": %d' % (keyword, len(seen)))
        for nm in list(seen.keys())[:25]:
            o('  %s' % nm)
        if not seen:
            o('  (none — try another keyword: bed, toilet, shower, fridge, sink)')
    except Exception as e:
        o('fivesim.find failed: %r' % e)


@sims4.commands.Command('fivesim.map', command_type=sims4.commands.CommandType.Live)
def fivesim_map(agent=None, sim_id=None, _connection=None):
    o = _out(_connection)
    if agent not in AGENTS or not sim_id:
        return o('usage: fivesim.map <agent> <sim_id>   agents: %s' % ', '.join(AGENTS))
    try:
        sid = int(sim_id)
    except Exception:
        return o('sim_id must be a number (see fivesim.sims)')
    ok, res = host_client.set_sim(agent, sid)
    o('mapped %s -> sim %d' % (agent, sid) if ok else 'host unreachable: %s' % res.get('reason', res))


@sims4.commands.Command('fivesim.model', command_type=sims4.commands.CommandType.Live)
def fivesim_model(agent=None, model=None, _connection=None):
    o = _out(_connection)
    if agent not in AGENTS or not model:
        return o('usage: fivesim.model <agent> <openrouter/model>   agents: %s' % ', '.join(AGENTS))
    ok, res = host_client.set_model(agent, model)
    o('%s now uses %s' % (agent, model) if ok else 'host unreachable: %s' % res.get('reason', res))


@sims4.commands.Command('fivesim.connect', command_type=sims4.commands.CommandType.Live)
def fivesim_connect(_connection=None):
    o = _out(_connection)
    ok, res = host_client.connect_bridge(BRIDGE_URL)
    o('host now reads this game at %s' % BRIDGE_URL if ok else 'host unreachable: %s' % res.get('reason', res))


@sims4.commands.Command('fivesim.start', command_type=sims4.commands.CommandType.Live)
def fivesim_start(_connection=None):
    o = _out(_connection)
    ok, res = host_client.start()
    o('AI started — your mapped Sims are now playing themselves.' if ok else 'host unreachable: %s' % res.get('reason', res))


@sims4.commands.Command('fivesim.stop', command_type=sims4.commands.CommandType.Live)
def fivesim_stop(_connection=None):
    o = _out(_connection)
    ok, res = host_client.stop()
    o('AI stopped.' if ok else 'host unreachable: %s' % res.get('reason', res))


def _print_local_bridge(o):
    try:
        from . import main_loop
        d = main_loop.diagnostics()
        o('local bridge: listening=%s alarm=%s sims=%s household=%s'
          % (d['server_up'], d['alarm_registered'], d['snapshot_sims'], d['active_household']))
        if d.get('last_error'):
            o('local bridge last error: %s' % d['last_error'].splitlines()[-1])
    except Exception as e:
        o('local bridge: diagnostics failed %r' % e)


@sims4.commands.Command('fivesim.status', command_type=sims4.commands.CommandType.Live)
def fivesim_status(_connection=None):
    o = _out(_connection)
    _ensure_bridge()
    _print_local_bridge(o)
    ok, res = host_client.status()
    if not ok:
        return o('host app: unreachable — open 5imulites-Host.exe (%s)' % res.get('reason', res))
    cfg = res.get('config', {})
    eng = res.get('engine', {})
    o('host app: connected | running: %s | LLM: %s' % (res.get('running'), cfg.get('llmEnabled')))
    o('host sees game: %s | decisions: %s' % ((eng.get('bridge') or {}).get('connected'), (eng.get('llm') or {}).get('calls')))
    for m in eng.get('models', []):
        o('  %s -> %s' % (m.get('id'), m.get('model')))


# ── pie-menu button targets ───────────────────────────────────────────────
# The pie buttons are pure EA tuning with a do_command basic_extra that calls
# these, passing the clicked Sim's id as an int (participant TargetSim).

def _notify(title, text):
    try:
        from . import ui
        ui.notify(title, text)
    except Exception:
        pass


@sims4.commands.Command('fivesim.btn_play', command_type=sims4.commands.CommandType.Live)
def fivesim_btn_play(sim_id: int = None, _connection=None):
    o = _out(_connection)
    try:
        if not sim_id:
            o('fivesim: no sim id from the menu')
            return
        _ensure_bridge()
        host_client.connect_bridge(BRIDGE_URL)
        ok, res = host_client.assign(int(sim_id))   # host picks a free model-slot
        if not ok:
            o('fivesim: host app not running (%s)' % res.get('reason', res))
            _notify('5imulites', 'Open the 5imulites app, then try again.')
            return
        agent = res.get('agent', 'ai')
        model = ((res.get('config') or {}).get('models') or {}).get(agent, agent)
        ok2, _res = host_client.start()
        if ok2:
            o('fivesim: sim %s is now played by %s (%s)' % (sim_id, agent, model))
            _notify('5imulites', 'This Sim is now played by %s.\nChange its brain anytime in the 5imulites app.' % model)
        else:
            o('fivesim: mapped sim %s to %s, but the host is not running' % (sim_id, agent))
            _notify('5imulites', 'Sim mapped — open the 5imulites app to begin.')
    except Exception as e:
        o('fivesim: %r' % e)


@sims4.commands.Command('fivesim.btn_setup', command_type=sims4.commands.CommandType.Live)
def fivesim_btn_setup(sim_id: int = None, _connection=None):
    o = _out(_connection)
    try:
        from . import ui
        ui.open_setup()
        o('fivesim: setup dialog opened')
    except Exception as e:
        o('fivesim: setup needs S4CL dialogs (%r) — use: fivesim.key <key>' % e)


@sims4.commands.Command('fivesim.btn_stop', command_type=sims4.commands.CommandType.Live)
def fivesim_btn_stop(sim_id: int = None, _connection=None):
    o = _out(_connection)
    try:
        host_client.stop()
        o('fivesim: AI stopped')
        _notify('5imulites', 'AI stopped — you have control again.')
    except Exception as e:
        o('fivesim: %r' % e)


@sims4.commands.Command('fivesim.debug', command_type=sims4.commands.CommandType.Live)
def fivesim_debug(_connection=None):
    """One-shot diagnostic: tells you exactly which layer is broken."""
    o = _out(_connection)
    o('— 5imulites diagnostics —')
    # 0. local game bridge (the thing the host app reads to list your Sims)
    _ensure_bridge()
    _print_local_bridge(o)
    # 1. S4CL present?
    try:
        import sims4communitylib  # noqa: F401
        o('S4CL: installed OK')
    except Exception as e:
        o('S4CL: MISSING -> %s (download Sims4CommunityLibrary into Mods/)' % e)
    # 2. our interaction classes importable?
    try:
        from . import interactions  # noqa: F401
        o('interaction classes: imported OK')
    except Exception as e:
        o('interaction classes: FAILED -> %r' % e)
    # 3. did the .package tuning actually load?
    try:
        from .modinfo import INTERACTIONS, CATEGORY_ID
        am = services.affordance_manager()
        for (cls, sid, _key, _label) in INTERACTIONS:
            tuning = am.get(sid)
            o('%s tuning: %s' % (cls, 'LOADED' if tuning is not None else 'NOT FOUND (5imulites_interactions.package not loading)'))
        o('submenu id: %s' % CATEGORY_ID)
    except Exception as e:
        o('tuning check failed: %r' % e)
    o('host: %s' % ('reachable' if host_client.status()[0] else 'unreachable (run `npm run dev`)'))


@sims4.commands.Command('fivesim.setup', command_type=sims4.commands.CommandType.Live)
def fivesim_setup(_connection=None):
    o = _out(_connection)
    try:
        from . import ui
        ui.open_setup()
        o('opening 5imulites setup…')
    except Exception as e:
        o('guided setup needs Sims4CommunityLibrary installed. (%s)' % e)
        o('You can configure with commands instead — type: fivesim.help')
