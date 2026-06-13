<div align="center">

# 🎮 fivesim — let AI play your Sims

**A free mod that hands your Sims over to AI language models** (GPT, Claude,
Gemini, DeepSeek, Qwen). Click a Sim → **5imulites → Let AI Play This Sim** → it
starts living on its own: going to work, eating, socialising, spending money —
all decided by a real AI model, while you watch.

Part of the [5imulites](https://x.com/5imulites) project · works on its own too.

</div>

---

## 🚀 Install — everything is ready-made, no tools needed

**Step 1 — Mods.** Download **all 5 files** from the [`download/`](download/)
folder and put them straight into:

```
Documents\Electronic Arts\The Sims 4\Mods\
```

| File | What it is |
|---|---|
| `fivesim.ts4script` | the mod |
| `5imulites_interactions.package` | the pie-menu button |
| `5imulites_icons.package` | the logo icon |
| `sims4communitylib.ts4script` + `.package` | [S4CL](https://github.com/DeviantGameMods/Sims4CommunityLibrary) — bundled for convenience (CC BY 4.0, see `ATTRIBUTION.txt`) |

**Step 2 — The control app.** Grab **`5imulites-host-win-x64.exe`** from
[**Releases**](../../releases) and double-click it. A control window opens in
your browser — paste your [OpenRouter](https://openrouter.ai/settings/keys) key
there once. *(That little app is the AI "brain": The Sims 4 can't call the
internet from inside the game, so the host does it — that's how every AI-Sims
mod works. Everything stays on your PC.)*

**Step 3 — Enable mods in the game.**
**Settings → Game Options → Other** → ☑ Enable Custom Content and Mods ·
☑ Script Mods Allowed → **Apply → fully restart the game**.

**Step 4 — Play.** Load a household and either:

- **click a Sim** → **5imulites** submenu → *Setup* / *Let AI Play This Sim* / *Stop AI*, **or**
- in the control window press **“Load Sims from game”**, pick which Sim each
  model plays from the dropdowns, hit **Start**.

That's it — the Sim now reads its own needs, asks its model what to do, and acts.

---

## 🇷🇺 Установка по-русски

1. Скачай **все 5 файлов** из папки [`download/`](download/) → закинь в
   `Documents\Electronic Arts\The Sims 4\Mods\` (S4CL уже в комплекте).
2. Из [**Releases**](../../releases) скачай **`5imulites-host-win-x64.exe`** и
   просто запусти — откроется окно управления, вставь туда ключ с
   [openrouter.ai](https://openrouter.ai/settings/keys).
3. В игре включи обе галки: **Settings → Game Options → Other** →
   **Custom Content and Mods** + **Script Mods Allowed** → **полный перезапуск
   игры**.
4. Зайди в семью. Дальше два пути:
   - **кликни по симу** → меню **5imulites** → *Let AI Play This Sim*, или
   - в окне управления нажми **«Load Sims from game»**, выбери из выпадашек,
     кто кем играет, и жми **Start**.

Если что-то не работает: **Ctrl+Shift+C** → `fivesim.debug` — команда построчно
покажет, какой слой сломан (S4CL / пакет кнопки / хост).

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

**"host unreachable"** → start `5imulites-host-win-x64.exe` (or `npm run dev`).

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
