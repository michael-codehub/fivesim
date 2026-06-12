# fivesim — The Sims 4 agent bridge

Let LLM agents **perceive and play The Sims 4 on your own PC**. `fivesim` is an
open-source script mod that runs **inside the game** and exposes a tiny
loopback HTTP API: it reads a Sim's ground-truth state (needs, funds, career,
relationships) and executes chosen actions in-game. It's the eyes-and-hands half
of the [5imulites](https://x.com/5imulites) experiment — five models living five
lives — but it works standalone for anyone.

```
┌───────────────────────────┐   127.0.0.1:8123    ┌───────────────────────────────┐
│  any controller / host     │  GET  /state/:id    │  The Sims 4  +  fivesim mod   │
│  (the 5imulites host, or    │  POST /dispatch     │  • reads motives/funds/career │
│   your own curl / script)   │ ◀────────────────▶  │  • performs actions on the    │
└───────────────────────────┘   X-Bridge-Token     │    game's main thread         │
                                                     └───────────────────────────────┘
```

## What's inside

| File | Role |
|---|---|
| `fivesim/main_loop.py` | starts the bridge on zone load; drains the command queue on the **main thread** via a real-time alarm (works even while paused) |
| `fivesim/bridge_server.py` | background HTTP thread + thread-safe queue + request-id/Event result handshake |
| `fivesim/state_reader.py` | builds ground-truth JSON: 6 motives (0–100), funds, skills, careers, relationships |
| `fivesim/action_executor.py` | executes actions on the main thread: console cheat → push interaction → go-to-work / modify-funds |
| `fivesim/ids.py` | motive GUIDs + a small **allow-list** of validated interaction GUIDs |
| `fivesim/injector.py` | vendored public-domain function injector |
| `build.py` | packages everything into `dist/fivesim.ts4script` |

## 1 · Build

The Sims 4 embeds **CPython 3.7**. Build with 3.7 for the matching `.pyc`
(fastest load); any Python 3 works (the game compiles the `.py` on load).

```bash
python build.py        # -> dist/fivesim.ts4script
```

## 2 · Install (Windows)

1. Copy `dist/fivesim.ts4script` into:
   `Documents\Electronic Arts\The Sims 4\Mods\`
   (at most one subfolder deep — e.g. `Mods\fivesim\fivesim.ts4script`).
2. Launch the game → **Settings → Game Options → Other** → tick
   **Enable Custom Content and Mods** and **Script Mods Allowed** → **restart the game**.
3. (optional auth) create
   `Documents\Electronic Arts\The Sims 4\fivesim_token.txt` with a secret; the
   bridge then requires the `X-Bridge-Token` header. It is bound to `127.0.0.1`
   regardless.
4. Load a household. On the loaded lot the bridge is live on
   `http://127.0.0.1:8123`.

## 3 · Test it in-game (no host needed)

Open a terminal / PowerShell while the game is on a loaded lot:

```powershell
# health
curl http://127.0.0.1:8123/health
# -> {"ok": true, "service": "fivesim-bridge"}

# every controllable Sim + ground-truth state (note each sim_id)
curl http://127.0.0.1:8123/state

# one Sim
curl http://127.0.0.1:8123/state/<sim_id>
```

Now make a Sim actually **do** something — give it §5000 (watch the funds jump):

```powershell
curl -X POST http://127.0.0.1:8123/dispatch ^
  -H "Content-Type: application/json" ^
  -d "{\"id\":\"t1\",\"action\":{\"type\":\"modify_funds\",\"sim_id\":<sim_id>,\"amount\":5000}}"
```

Send it to work, or trigger an interaction from the allow-list:

```powershell
curl -X POST http://127.0.0.1:8123/dispatch -H "Content-Type: application/json" ^
  -d "{\"id\":\"t2\",\"action\":{\"type\":\"go_to_work\",\"sim_id\":<sim_id>}}"

curl -X POST http://127.0.0.1:8123/dispatch -H "Content-Type: application/json" ^
  -d "{\"id\":\"t3\",\"action\":{\"type\":\"interaction\",\"sim_id\":<sim_id>,\"interaction\":\"sleep_in_bed\"}}"
```

PowerShell alternative for POST:
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8123/dispatch -Method Post -ContentType application/json `
  -Body '{"id":"t1","action":{"type":"modify_funds","sim_id":<sim_id>,"amount":5000}}'
```

If `/health` answers and `modify_funds` changes the on-screen money, the mod is
working end to end.

## Bridge API

| Method · Path | Body / params | Returns |
|---|---|---|
| `GET /health` | — | `{ ok, service }` |
| `GET /state` | — | all controllable Sims keyed by `sim_id` |
| `GET /state/:sim_id` | — | one Sim's state |
| `POST /dispatch` | `{ id, action:{ type, sim_id, … } }` | executed result (`504` if the 5s main-thread handshake times out) |

Action types: `console` (`{command}`), `modify_funds` (`{amount}`),
`go_to_work`, `interaction` (`{interaction, target_sim_id?}` — key must be in the
`ids.py` allow-list).

## Action coverage (v1)

Reliable in-game actuations: `go_to_work`, `sleep_in_bed`, `eat_grab_quick`,
`shower`, `use_toilet`, and funds changes. Other actions can be added by
validating their interaction GUID and appending it to `INTERACTION_GUIDS` in
`fivesim/ids.py`. The allow-list never accepts an arbitrary caller-supplied GUID.

## Safety

- Bridge is **loopback-only** (`127.0.0.1`) + optional shared token.
- All game-state reads/writes happen on the simulation **main thread**; the HTTP
  thread only enqueues work — the documented-safe pattern for TS4 mods.
- Only allow-listed interaction GUIDs are ever pushed.

## Troubleshooting

- **`/health` refuses to connect** → script mods not enabled, or you didn't
  restart after enabling, or you're on the main menu (load a lot). Check
  `Documents\Electronic Arts\The Sims 4\mod_logs` / `lastException` files.
- **Mod ignored** → the `.ts4script` must be ≤1 subfolder deep in `Mods/`, and
  the inner module path must stay `fivesim/…`.
- **`sim_not_instantiated`** → the Sim is off-lot; use `console`/`modify_funds`
  which don't need an instanced Sim, or switch to that household.
- **Wrong `.pyc` version warning** → harmless; the game falls back to the shipped
  `.py`. Build with CPython 3.7 to silence it.

## License

MIT © 2026 Mari
