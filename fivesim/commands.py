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
    o('  fivesim.start / fivesim.stop       start / stop the AI playing')
    o('  fivesim.status                     show host + engine status')


@sims4.commands.Command('fivesim.key', command_type=sims4.commands.CommandType.Live)
def fivesim_key(key=None, _connection=None):
    o = _out(_connection)
    if not key:
        return o('usage: fivesim.key <openrouter_key>')
    ok, res = host_client.set_key(key)
    o('API key saved on the host.' if ok else 'host unreachable: %s (is `npm run dev` running?)' % res.get('reason', res))


@sims4.commands.Command('fivesim.sims', command_type=sims4.commands.CommandType.Live)
def fivesim_sims(_connection=None):
    o = _out(_connection)
    hh = services.active_household()
    if hh is None:
        return o('no active household — load a lot first')
    o('Your Sims (sim_id  name):')
    for si in hh.sim_info_gen():
        o('  %d  %s %s' % (si.sim_id, si.first_name, si.last_name))
    o('map them, e.g.:  fivesim.map gpt <sim_id>')


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


@sims4.commands.Command('fivesim.status', command_type=sims4.commands.CommandType.Live)
def fivesim_status(_connection=None):
    o = _out(_connection)
    ok, res = host_client.status()
    if not ok:
        return o('host unreachable: %s (run `npm run dev`)' % res.get('reason', res))
    cfg = res.get('config', {})
    eng = res.get('engine', {})
    o('host: connected | running: %s | LLM: %s' % (res.get('running'), cfg.get('llmEnabled')))
    o('bridge connected: %s | decisions: %s' % ((eng.get('bridge') or {}).get('connected'), (eng.get('llm') or {}).get('calls')))
    for m in eng.get('models', []):
        o('  %s -> %s' % (m.get('id'), m.get('model')))


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
