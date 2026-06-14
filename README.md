<div align="center">

# 🎮 fivesim — let AI play your Sims

**A free mod that hands your Sims over to AI language models** (GPT, Claude,
Gemini, DeepSeek, Qwen). Click a Sim → **5imulites → Let AI Play This Sim** → it
starts living on its own: going to work, eating, socialising, spending money —
all decided by a real AI model, while you watch.

Part of the [5imulites](https://x.com/5imulites) project · works on its own too.

</div>

---

## 🚀 Install — one folder, no thinking

Everything you need lives in [**`download/`**](download/). Grab it (click the
green **Code → Download ZIP** on the repo, files are under `download/`).

**1 — Copy the mod.** Drop **everything inside [`download/Mods/`](download/Mods)**
into your game's Mods folder:
```
Documents\Electronic Arts\The Sims 4\Mods\
```
(That's the mod, the button, the icon, and Sims4CommunityLibrary — all bundled.)

**2 — Enable mods.** In the game → **Settings → Game Options → Other** →
☑ Enable Custom Content and Mods · ☑ Script Mods Allowed → **Apply → fully
restart the game**.

**3 — Run the app.** Double-click
[`download/5imulites-Host.exe`](download/5imulites-Host.exe) (it's right there in
the folder you downloaded). A real desktop window opens (with the logo) — paste
your [OpenRouter](https://openrouter.ai/settings/keys) key, pick a model, and
that's your whole setup.
*(This app is the AI "brain": The Sims 4 can't reach the internet from inside the
game, so the host makes the AI calls — that's how every AI-Sims mod works.
Everything stays on your PC.)*

**4 — Play.** Load a household, then in the app press **Load Sims from game**,
assign each AI to a Sim, and hit **Save & Start the AI**. Or in-game just **click
a Sim** → **5imulites: Let AI Play** (also *Setup* / *Stop AI*).

That's it — the Sim now reads its own needs, asks its model what to do, and acts.

---

## 🕹️ Cheat-console fallback (works even without the button)

Press **Ctrl + Shift + C**:

```
fivesim.debug               ← diagnose: shows exactly what's broken
fivesim.key sk-or-v1-…      ← paste your OpenRouter key
fivesim.connect             ← link the host to this game
fivesim.sims                ← shows each Sim and its id
fivesim.map gpt 12345       ← give Sim 12345 to "gpt" (also: claude, gemini, deepseek, qwen)
fivesim.start / fivesim.stop / fivesim.status
```

---

## ❓ Troubleshooting

**No 5imulites submenu when clicking a Sim** → run `fivesim.debug` in the cheat
console; it names the broken layer. Most common: game wasn't fully restarted, or
a file isn't directly in `Mods\` (max one subfolder deep).

**"host unreachable"** → the app (`5imulites-Host.exe`) must be open; it runs the
local bridge the game talks to.

**Windows SmartScreen warns about the exe** → it's an unsigned open-source
build; "More info → Run anyway", or build it yourself from this repo.

**Did the mod load at all?** While on a lot:
```powershell
curl http://127.0.0.1:8123/health   # → {"ok":true,"service":"fivesim-bridge"}
```

---

## 🧠 How it works

```
   click a Sim / control window ──┐                   ┌─ reads the Sim, sends actions
                                  ▼                    ▼
   ┌──────────────────────────────┐  localhost  ┌──────────────────────────────┐
   │  The Sims 4  +  fivesim mod   │ ──────────▶ │  5imulites host (the brain)  │
   │  • sees needs / money / job   │ ◀────────── │  • holds your API key         │
   │  • performs the action        │             │  • asks the AI what to do     │
   └──────────────────────────────┘             └──────────────────────────────┘
```

The mod is the **eyes and hands** inside the game; the host is the **brain** that
calls the AI. Every decision is a real call to that Sim's model — nothing is
scripted.

---

## 🛠️ For developers

Build from source: `python build.py` → everything lands in `dist/`.
Host from source: `npm run dev` in the main 5imulites repo (`localhost:4000/host`).
Desktop app: `desktop/` is an Electron shell that boots the bundled host and
shows it in a native window — `cd desktop && npm install && npm run dist` builds
`5imulites-Host.exe` (CI does this on every push via
`.github/workflows/build-desktop.yml`).

The mod exposes a local bridge on `http://127.0.0.1:8123`:

| Method · Path | Body | Returns |
|---|---|---|
| `GET /health` | — | `{ ok, service }` |
| `GET /state[/:sim_id]` | — | ground-truth Sim state (needs, funds, career, relationships) |
| `POST /dispatch` | `{ id, action:{ type, sim_id, … } }` | result of running it in-game |

Action types: `console`, `modify_funds`, `go_to_work`, `interaction`
(allow-listed in `fivesim/ids.py`).

| File | Role |
|---|---|
| `fivesim/bridge_server.py` | local HTTP bridge (background thread + safe main-thread queue) |
| `fivesim/state_reader.py` | ground-truth Sim state |
| `fivesim/action_executor.py` | performs actions on the game's main thread |
| `fivesim/interactions.py` | the pie-menu button (S4CL, import paths verified against v3.21) |
| `fivesim/commands.py` | cheat-console commands incl. `fivesim.debug` |
| `fivesim/host_client.py` | talks to the local host |
| `build*.py` | package the mod + button + icon |

The interactions package mirrors S4CL's own shipping package byte-for-byte
(zlib tuning XML, `target_type OBJECT`, English STBL at group 0).

Everything runs on `127.0.0.1` only; your key never leaves your PC.

## License

MIT © 2026 andro · bundled S4CL is CC BY 4.0 (see `download/ATTRIBUTION.txt`)
