# fivesim — The Sims 4 agent bridge

Let LLM agents **play The Sims 4 on your own PC**, controlled **from inside the
game**: click a Sim → **5imulites ▸ Let AI play this Sim**, and that Sim starts
living on its own — reading its needs, deciding with a real model, and acting in
the game. `fivesim` is an open-source script mod that reads ground-truth Sim
state, performs actions in-game, and gives you a pie-menu button + console
commands to wire it all up.

It's the eyes-and-hands of the [5imulites](https://x.com/5imulites) experiment
(five models living five lives), and works standalone for anyone.

> **Why a host?** The Sims 4 Python runtime is locked-down and **can't make HTTPS
> calls** — so, like every AI-Sims mod, the LLM call runs in a small local **host**
> (the "sidecar"). The mod talks plain HTTP to it on `127.0.0.1`; the host makes
> the real OpenRouter call and drives your Sim through this bridge. Reasoning is
> never faked — it's a real call to each agent's model.

```
  pie-menu / commands ─┐                       ┌─ reads /state, posts /dispatch
                       ▼                        ▼
┌──────────────────────────┐  HTTP 127.0.0.1  ┌────────────────────────────────┐
│  The Sims 4 + fivesim mod │ ───────────────▶ │  5imulites host (the sidecar)   │
│  • bridge :8123           │ ◀─────────────── │  • holds your OpenRouter key     │
│  • button + console cmds  │   config/start   │  • HTTPS → OpenRouter (the brain)│
└──────────────────────────┘                  └────────────────────────────────┘
```

## Build

The Sims 4 embeds **CPython 3.7**. Build with 3.7 for the matching `.pyc`; any
Python 3 works. One command builds everything:

```bash
python build.py
# -> dist/fivesim.ts4script            (the mod)
# -> dist/5imulites_interactions.package (the pie-menu button)
# -> dist/5imulites_icons.package        (the logo icon)
```

## Install (Windows)

Copy into `Documents\Electronic Arts\The Sims 4\Mods\` (≤1 subfolder deep):

1. `dist/fivesim.ts4script` — **required**.
2. `dist/5imulites_interactions.package` — the **pie-menu button** (needs S4CL).
3. `dist/5imulites_icons.package` — the logo icon (optional).
4. [**Sims4CommunityLibrary**](https://github.com/ColonolNutty/Sims4CommunityLibrary)
   into `Mods\` — required for the button + setup dialog. (Without it, the console
   commands still do everything.)

Then in-game → **Settings → Game Options → Other** → enable **Custom Content and
Mods** + **Script Mods Allowed** → **restart the game** → load a household.

## Play (the button)

Click any Sim. In the pie menu:

- **5imulites ▸ Setup** — paste your OpenRouter API key (dialog).
- **5imulites ▸ Let AI play this Sim** — hands that Sim to the next free model and
  starts it. The Sim now lives on its own.
- **5imulites ▸ Stop AI** — take control back.

First, start the host (the sidecar) on the same PC: the
[5imulites](https://x.com/5imulites) host (`npm run dev`, opens `localhost:4000`).
That's where your key lives and where the HTTPS call to OpenRouter happens.

## Play (console, no S4CL needed)

Press **Ctrl+Shift+C** and type:

```
fivesim.key sk-or-v1-…         # set the OpenRouter key on the host
fivesim.connect                # point the host at this game
fivesim.sims                   # list your Sims + their sim_id
fivesim.map gpt 12345          # map an agent to a Sim (gpt claude gemini deepseek qwen)
fivesim.start                  # the AI takes over
fivesim.status / fivesim.stop
```

`fivesim.help` lists everything.

## Test the bridge directly (no host)

While on a loaded lot:

```powershell
curl http://127.0.0.1:8123/health      # {"ok":true,"service":"fivesim-bridge"}
curl http://127.0.0.1:8123/state        # all Sims + sim_id + ground-truth state
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

## What's inside

| File | Role |
|---|---|
| `fivesim/main_loop.py` | starts the bridge + drains commands on the main thread |
| `fivesim/bridge_server.py` | background HTTP thread + thread-safe queue + handshake |
| `fivesim/state_reader.py` | ground-truth JSON: motives, funds, skills, careers, relationships |
| `fivesim/action_executor.py` | executes actions on the main thread |
| `fivesim/interactions.py` | the pie-menu button (S4CL interactions) |
| `fivesim/commands.py` | in-game console commands (no extra deps) |
| `fivesim/ui.py` + `modidentity.py` | S4CL setup dialog + branded notifications |
| `fivesim/host_client.py` | plain-HTTP client to the local host |
| `build_interaction_package.py` | builds the pie-menu `.package` (tuning XML + STBL) |
| `build_icon_package.py` | packages `assets/logo.png` as the in-game icon |

## Safety

- Bridge is **loopback-only** (`127.0.0.1`) + optional `X-Bridge-Token`.
- All game reads/writes run on the simulation **main thread**; only network I/O is
  off-thread — the documented-safe TS4 pattern.
- The in-game key is sent only to your local host, never bundled in the mod. Only
  allow-listed interaction GUIDs are ever pushed.

## Troubleshooting

- **No pie-menu button** → install Sims4CommunityLibrary **and**
  `5imulites_interactions.package`, then restart. If the tuning is still ignored,
  rebuild it in Sims 4 Studio (interaction tuning type `0xE882D22F`, class
  `FiveSimPlay`/`FiveSimSetup`/`FiveSimStop`, module `fivesim.interactions`). The
  console commands work regardless.
- **`fivesim.*` says "host unreachable"** → start the host (`npm run dev`) first.
- **`/health` refuses to connect** → script mods not enabled, didn't restart, or
  you're on the main menu (load a lot). Check `mod_logs` / `lastException`.
- **Logo icon missing** → repackage `assets/logo.png` in Sims 4 Studio (PNG,
  type `0x2F7D0004`, instance `0x5130A1A1A1A10001`). The mod works without it.

## License

MIT © 2026 Mari
