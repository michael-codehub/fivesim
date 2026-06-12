# fivesim — The Sims 4 agent bridge

Let LLM agents **perceive and play The Sims 4 on your own PC**, and **control it
from inside the game**. `fivesim` is an open-source script mod that:

- reads a Sim's **ground-truth state** (needs, funds, career, relationships),
- **performs actions in-game** (work, eat, sleep, socialise, money, …),
- gives you **in-game console commands + a setup dialog** to plug in your API key,
  pick a model per Sim, and start/stop the AI — without leaving the game.

It's the eyes-and-hands of the [5imulites](https://x.com/5imulites) experiment
(five models living five lives), and works standalone for anyone.

> **Why a host?** The Sims 4 Python runtime is locked-down and **can't make HTTPS
> calls** — so, like every AI-Sims mod (Sentient Sims, sims4ai), the LLM call runs
> in a small local **host** (the "sidecar"). The mod talks plain HTTP to it on
> `127.0.0.1`; the host makes the real OpenRouter call and drives your Sim through
> this bridge. Reasoning is never faked — it's a real call to each agent's model.

```
  In-game commands ─┐                         ┌─ reads /state, posts /dispatch
                    ▼                          ▼
┌──────────────────────────┐  HTTP 127.0.0.1  ┌────────────────────────────────┐
│  The Sims 4 + fivesim mod │ ───────────────▶ │  5imulites host (the sidecar)   │
│  • bridge :8123           │ ◀─────────────── │  • holds your OpenRouter key     │
│  • console cmds + dialogs │   config/start   │  • HTTPS → OpenRouter (the brain)│
└──────────────────────────┘                  └────────────────────────────────┘
```

## Build

The Sims 4 embeds **CPython 3.7**. Build with 3.7 for the matching `.pyc`; any
Python 3 works (the game compiles the `.py` on load).

```bash
python build.py               # -> dist/fivesim.ts4script
python build_icon_package.py  # -> dist/5imulites_icons.package  (logo icon, optional)
```

## Install (Windows)

1. Copy `dist/fivesim.ts4script` into
   `Documents\Electronic Arts\The Sims 4\Mods\` (one subfolder deep, max).
2. *(optional, for the logo icon)* copy `dist/5imulites_icons.package` next to it.
3. *(optional, for the pretty setup dialog)* install
   [Sims4CommunityLibrary](https://github.com/ColonolNutty/Sims4CommunityLibrary)
   into `Mods\`. Without it, the console commands still do everything.
4. In-game → **Settings → Game Options → Other** → enable **Custom Content and Mods**
   + **Script Mods Allowed** → **restart the game**.
5. Load a household, enter the lot. The bridge is live on `http://127.0.0.1:8123`.

## Make the AI actually play (gameplay)

1. Start the host (the sidecar) on the same PC — see the
   [5imulites](https://x.com/5imulites) host (`npm run dev`, opens `localhost:4000`).
2. In the game press **Ctrl+Shift+C** to open the cheat console and type:

```
fivesim.setup                  # guided: paste your OpenRouter key (needs S4CL)
fivesim.connect                # point the host at this game
fivesim.sims                   # list your Sims + their sim_id
fivesim.map gpt 12345          # map an agent to a Sim (gpt claude gemini deepseek qwen)
fivesim.model gpt openai/gpt-5.4-nano   # (optional) choose the model
fivesim.start                  # the AI takes over — your Sim plays itself
fivesim.status                 # see what's running
fivesim.stop                   # hand control back
```

No S4CL? Set the key from the console instead: `fivesim.key sk-or-v1-…`.
From here the host reads your Sim's needs, asks its model what to do, and the mod
performs it in-game — **your Sim genuinely acts on the model's decisions.**

## Test the bridge directly (no host needed)

While on a loaded lot:

```powershell
curl http://127.0.0.1:8123/health      # {"ok":true,"service":"fivesim-bridge"}
curl http://127.0.0.1:8123/state        # all Sims + sim_id + ground-truth state
# give a Sim §5000 (watch the money jump):
curl.exe -X POST http://127.0.0.1:8123/dispatch -H "Content-Type: application/json" -d "{\"id\":\"t1\",\"action\":{\"type\":\"modify_funds\",\"sim_id\":<sim_id>,\"amount\":5000}}"
```

## Bridge API

| Method · Path | Body | Returns |
|---|---|---|
| `GET /health` | — | `{ ok, service }` |
| `GET /state[/:sim_id]` | — | ground-truth Sim state |
| `POST /dispatch` | `{ id, action:{ type, sim_id, … } }` | executed result (`504` on 5s timeout) |

Action types: `console` (`{command}`), `modify_funds` (`{amount}`), `go_to_work`,
`interaction` (`{interaction, target_sim_id?}` — key from the `ids.py` allow-list).

## In-game commands

`fivesim.help` lists them all: `setup`, `key`, `sims`, `map`, `model`, `connect`,
`start`, `stop`, `status`. They configure and drive the host from inside the game.

## What's inside

| File | Role |
|---|---|
| `fivesim/main_loop.py` | starts the bridge + drains commands on the main thread (real-time alarm) |
| `fivesim/bridge_server.py` | background HTTP thread + thread-safe queue + result handshake |
| `fivesim/state_reader.py` | ground-truth JSON: motives, funds, skills, careers, relationships |
| `fivesim/action_executor.py` | executes actions on the main thread |
| `fivesim/commands.py` | in-game console commands (no extra deps) |
| `fivesim/ui.py` + `modidentity.py` | optional S4CL setup dialog + branded notifications |
| `fivesim/host_client.py` | plain-HTTP client to the local host (config/start/stop) |
| `fivesim/ids.py` | motive GUIDs + interaction allow-list |
| `build_icon_package.py` | packages `assets/logo.png` as the in-game icon |

## Safety

- Bridge is **loopback-only** (`127.0.0.1`) + optional `X-Bridge-Token`.
- All game reads/writes run on the simulation **main thread**; only network I/O is
  off-thread — the documented-safe TS4 pattern.
- Only allow-listed interaction GUIDs are ever pushed; the in-game key is sent only
  to your local host, never bundled in the mod.

## Troubleshooting

- **`fivesim.*` says "host unreachable"** → start the host (`npm run dev`) on the
  same PC first.
- **`/health` refuses to connect** → script mods not enabled, didn't restart, or
  you're on the main menu (load a lot). Check `mod_logs` / `lastException`.
- **Logo icon missing** → repackage `assets/logo.png` in Sims 4 Studio as a PNG
  resource, type `0x2F7D0004`, instance `0x5130A1A1A1A10001`. The mod works without it.
- **Setup dialog missing** → install Sims4CommunityLibrary, or use `fivesim.key`.

## License

MIT © 2026 Mari
