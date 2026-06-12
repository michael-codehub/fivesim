<div align="center">

# 🎮 fivesim — let AI play your Sims

**A free mod that hands your Sims over to AI language models** (GPT, Claude,
Gemini, DeepSeek, Qwen). Click a Sim → **5imulites → Let AI Play This Sim** → it
starts living on its own: going to work, eating, socialising, spending money —
all decided by a real AI model, while you watch.

Part of the [5imulites](https://x.com/5imulites) project · works on its own too.

</div>

---

## 🚀 Install in 4 steps (no tools needed)

**1 — Download the ready-made files** from the [`download/`](download/) folder
of this repo (3 files):

| File | What it is |
|---|---|
| [`fivesim.ts4script`](download/fivesim.ts4script) | the mod itself |
| [`5imulites_interactions.package`](download/5imulites_interactions.package) | the pie-menu button |
| [`5imulites_icons.package`](download/5imulites_icons.package) | the logo icon |

…and **Sims4CommunityLibrary** (free, needed for the button):
[latest release](https://github.com/DeviantGameMods/Sims4CommunityLibrary/releases)
→ download the `sims4communitylib.vX.XX.zip` → unzip it.

**2 — Put everything into your Mods folder:**
```
Documents\Electronic Arts\The Sims 4\Mods\
```
That's our 3 files **+** `sims4communitylib.ts4script` **+** `sims4communitylib.package`.

**3 — Turn on mods in the game:**
**Settings → Game Options → Other** →
☑ Enable Custom Content and Mods · ☑ Script Mods Allowed →
**Apply → fully restart the game** (script mods only load after a restart).

**4 — Play.** Load a household, click any Sim → **5imulites** submenu:

| Button | What it does |
|---|---|
| **Setup (API Key)** | paste your [OpenRouter](https://openrouter.ai/settings/keys) key |
| **Let AI Play This Sim** | the AI takes over this Sim 🎉 |
| **Stop AI** | take control back |

> ⚠️ For the AI to actually think, the small **5imulites host app** must be
> running on your PC (`npm run dev` → `localhost:4000`). The Sims 4 can't talk
> to the internet from inside the game, so the host makes the AI calls — that's
> how every AI-Sims mod works. The mod and host only talk on your own computer.

---

## 🇷🇺 Установка по-русски

1. **Скачай 3 файла** из папки [`download/`](download/) этого репозитория
   и **Sims4CommunityLibrary** ([отсюда](https://github.com/DeviantGameMods/Sims4CommunityLibrary/releases), распакуй zip).
2. **Всё положи в** `Documents\Electronic Arts\The Sims 4\Mods\`
   (наши 3 файла + `sims4communitylib.ts4script` + `sims4communitylib.package`).
3. В игре: **Settings → Game Options → Other** → включи обе галки
   (**Custom Content and Mods** + **Script Mods Allowed**) → **полностью
   перезапусти игру**.
4. Зайди в семью, **кликни по симу** → меню **5imulites** → **Setup** (вставь
   ключ с [openrouter.ai](https://openrouter.ai/settings/keys)) → **Let AI Play
   This Sim**. Чтобы ИИ думал, на ПК должен работать хост 5imulites
   (`npm run dev`).

Проверка, если что-то не так: **Ctrl+Shift+C** → `fivesim.debug` — команда
покажет, какой слой не работает (S4CL / пакет кнопки / хост).

---

## 🕹️ No button? Everything works from the cheat console too

Press **Ctrl + Shift + C** and type:

```
fivesim.debug               ← diagnose: shows exactly what's broken
fivesim.key sk-or-v1-…      ← paste your OpenRouter key
fivesim.connect             ← link the host to this game
fivesim.sims                ← shows each Sim and its id
fivesim.map gpt 12345       ← give Sim 12345 to "gpt" (also: claude, gemini, deepseek, qwen)
fivesim.start               ← AI starts playing
fivesim.status / fivesim.stop
```

`fivesim.help` lists them all. The commands don't need Sims4CommunityLibrary.

---

## 🔌 Quick "is it alive?" test (no host needed)

While you're on a loaded lot, open PowerShell:

```powershell
curl http://127.0.0.1:8123/health
# {"ok":true,"service":"fivesim-bridge"}  ← the mod is running

curl http://127.0.0.1:8123/state
# lists your Sims with their needs, money, career…

# give a Sim §5000 and watch the money jump on screen:
curl.exe -X POST http://127.0.0.1:8123/dispatch -H "Content-Type: application/json" -d "{\"id\":\"t1\",\"action\":{\"type\":\"modify_funds\",\"sim_id\":<sim_id>,\"amount\":5000}}"
```

If `/health` answers and the money changes — everything works. 🎉

---

## ❓ Troubleshooting

**The 5imulites submenu doesn't show when I click a Sim.**
1. Run `fivesim.debug` in the cheat console — it tells you which piece is missing.
2. Make sure **both** S4CL files (`.ts4script` + `.package`) and our
   `5imulites_interactions.package` are in `Mods\`, no deeper than one subfolder.
3. Restart the game fully after any file change.
4. The cheat commands always work even without the button.

**It says "host unreachable".**
Start the host app (`npm run dev`) on the same PC first — that's the brain.

**`curl /health` won't connect.**
Script mods aren't enabled, you didn't restart, or you're still in the main
menu — load into a lot. Check `lastException…txt` / `mod_logs` in
`Documents\Electronic Arts\The Sims 4\`.

**Building from source instead of using `download/`:**
```bash
git clone https://github.com/mariwatts/fivesim.git
cd fivesim && python build.py     # everything lands in dist/
```

---

## 🧠 How it works

```
   click a Sim / type a command ─┐                    ┌─ reads the Sim, sends actions
                                 ▼                     ▼
   ┌──────────────────────────────┐  localhost  ┌──────────────────────────────┐
   │  The Sims 4  +  fivesim mod   │ ──────────▶ │  5imulites host (the brain)  │
   │  • sees needs / money / job   │ ◀────────── │  • holds your API key         │
   │  • performs the action        │             │  • asks the AI what to do     │
   └──────────────────────────────┘             └──────────────────────────────┘
```

The mod is the **eyes and hands** inside the game; the host is the **brain** that
calls the AI. The AI's reasoning is real — every decision is an actual call to
that Sim's model.

---

## 🛠️ For developers

The mod exposes a tiny local API (the "bridge") on `http://127.0.0.1:8123`:

| Method · Path | Body | Returns |
|---|---|---|
| `GET /health` | — | `{ ok, service }` |
| `GET /state[/:sim_id]` | — | ground-truth Sim state (needs, funds, career, relationships) |
| `POST /dispatch` | `{ id, action:{ type, sim_id, … } }` | result of running it in-game |

Action types: `console`, `modify_funds`, `go_to_work`, `interaction`
(allow-listed in `fivesim/ids.py`).

| File | Role |
|---|---|
| `fivesim/bridge_server.py` | the local HTTP bridge (background thread + safe main-thread queue) |
| `fivesim/state_reader.py` | reads ground-truth Sim state |
| `fivesim/action_executor.py` | performs actions on the game's main thread |
| `fivesim/interactions.py` | the pie-menu button (Sims4CommunityLibrary) |
| `fivesim/commands.py` | the cheat-console commands (incl. `fivesim.debug`) |
| `fivesim/host_client.py` | talks to the local host |
| `build*.py` | package the mod + button + icon |

The interactions package structure mirrors S4CL's own shipping package
(zlib-compressed tuning XML, `target_type OBJECT`, English STBL at group 0) —
extracted and verified against it byte-for-byte.

Everything runs on `127.0.0.1` only; the key never leaves your PC.

## License

MIT © 2026 Mari
