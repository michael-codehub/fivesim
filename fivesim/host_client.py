# Plain-HTTP client to the 5imulites host (the sidecar brain) on localhost.
# The Sims 4 runtime can't do HTTPS, so the in-game mod only talks plain HTTP to
# the local host, and the host makes the real HTTPS calls to OpenRouter.
# These calls are quick localhost requests run synchronously from console
# commands / dialog callbacks (user-initiated), never the LLM loop itself.
import json
import os
import urllib.request
import urllib.error

DEFAULT_HOST = 'http://127.0.0.1:4000'
_CFG_NAMES = ['fivesim_host.txt']


def _host_base():
    home = os.path.expanduser('~')
    for name in _CFG_NAMES:
        for path in (name, os.path.join(home, name),
                     os.path.join(home, 'Documents', 'Electronic Arts', 'The Sims 4', name)):
            try:
                with open(path) as f:
                    v = f.read().strip()
                    if v:
                        return v.rstrip('/')
            except Exception:
                continue
    return DEFAULT_HOST


def _request(method, path, body=None, timeout=4):
    url = _host_base() + path
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode('utf-8')
        return True, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        body_txt = ''
        try:
            body_txt = e.read().decode('utf-8')
        except Exception:
            pass
        return False, {'error': 'http_%d' % e.code, 'body': body_txt}
    except Exception as e:
        return False, {'error': 'unreachable', 'reason': str(e)}


# ── high-level helpers ───────────────────────────────────────────────────────
def set_config(partial):
    return _request('POST', '/api/host/config', partial)

def start():
    return _request('POST', '/api/host/start')

def stop():
    return _request('POST', '/api/host/stop')

def status():
    return _request('GET', '/api/host')

def set_key(key):
    return set_config({'openRouterKey': key})

def set_model(agent_id, model):
    return set_config({'models': {agent_id: model}})

def set_sim(agent_id, sim_id):
    return set_config({'simMap': {agent_id: int(sim_id)}})

def connect_bridge(bridge_url):
    return set_config({'bridgeUrl': bridge_url})

def host_base():
    return _host_base()
