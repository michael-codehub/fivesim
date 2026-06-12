# Background HTTP server thread. Accepts requests off the main thread, hands
# game-mutating work to the main thread via a queue, and blocks the worker until
# the main thread posts the result back (request-id + Event handshake).
import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .modinfo import HOST, PORT

cmd_queue = queue.Queue()          # background -> main
_results = {}                      # request_id -> result (written on MAIN thread)
_results_lock = threading.Lock()
_events = {}                       # request_id -> threading.Event

state_snapshot = {'agents': {}, 'ts': 0}
_snapshot_lock = threading.Lock()

AUTH_TOKEN = None
_server = None


def set_token(tok):
    global AUTH_TOKEN
    AUTH_TOKEN = tok


def publish_snapshot(snap):        # called on main thread
    global state_snapshot
    with _snapshot_lock:
        state_snapshot = snap


def _read_snapshot():
    with _snapshot_lock:
        return state_snapshot


def put_result(rid, result):       # called on main thread
    with _results_lock:
        _results[rid] = result
    ev = _events.get(rid)
    if ev:
        ev.set()


class _Handler(BaseHTTPRequestHandler):
    def _auth_ok(self):
        return AUTH_TOKEN is None or self.headers.get('X-Bridge-Token') == AUTH_TOKEN

    def _send(self, code, obj):
        out = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_GET(self):
        if not self._auth_ok():
            return self._send(401, {'error': 'unauthorized'})
        if self.path == '/health':
            return self._send(200, {'ok': True, 'service': 'fivesim-bridge'})
        if self.path.startswith('/state'):
            snap = _read_snapshot()
            parts = self.path.strip('/').split('/')
            if len(parts) == 2:
                agent = snap['agents'].get(parts[1])
                return self._send(200 if agent else 404, agent or {'error': 'unknown_sim'})
            return self._send(200, snap)
        return self._send(404, {'error': 'not_found'})

    def do_POST(self):
        if not self._auth_ok():
            return self._send(401, {'error': 'unauthorized'})
        if self.path != '/dispatch':
            return self._send(404, {'error': 'not_found'})
        length = int(self.headers.get('Content-Length', 0) or 0)
        body = self.rfile.read(length) if length else b'{}'
        try:
            cmd = json.loads(body or b'{}')
        except Exception:
            return self._send(400, {'error': 'bad_json'})
        rid = str(cmd.get('id') or id(cmd))
        ev = threading.Event()
        _events[rid] = ev
        cmd_queue.put((rid, cmd))
        got = ev.wait(timeout=5.0)
        with _results_lock:
            result = _results.pop(rid, {'error': 'timeout'})
        _events.pop(rid, None)
        return self._send(200 if got else 504, result)

    def log_message(self, *a):
        pass


def start_server():
    global _server
    if _server:
        return
    _server = ThreadingHTTPServer((HOST, PORT), _Handler)
    threading.Thread(target=_server.serve_forever, daemon=True, name='fivesim_http').start()


def stop_server():
    global _server
    if _server:
        _server.shutdown()
        _server = None
