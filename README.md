<div align="center">

# 🎮 fivesim — let AI play your Sims

**A free mod that hands your Sims over to AI language models** (GPT, Claude,
Gemini, DeepSeek, Qwen). Click a Sim → *"Let AI play this Sim"* → it starts
living on its own: going to work, eating, socialising, spending money — all
decided by a real AI model, while you watch.

Part of the [5imulites](https://x.com/5imulites) project · works on its own too.

</div>

---

## ✅ What you need

| | |
|---|---|
| 🎯 **The Sims 4** | any recent version, on Windows |
| 🐍 **Python 3** | only to build the mod once — [python.org](https://www.python.org/downloads/) |
| 📚 **Sims4CommunityLibrary** | free, required for the in-game button — [download](https://github.com/DeviantGameMods/Sims4CommunityLibrary/releases) |
| 🧠 **The 5imulites host app** | the "brain" that talks to the AI. Runs on your PC and holds your API key |
| 🔑 **An OpenRouter API key** | one key for all 5 models — get one at [openrouter.ai](https://openrouter.ai/settings/keys) |

> **Why a separate "host"?** The Sims 4 can't safely talk to the internet from
> inside the game, so a tiny companion app on your PC makes the AI calls for it.
> (Every AI-Sims mod works this way.) The mod and the host only talk to each
> other on your own computer.

---

## 🚀 Quick start

**1 · Get the mod**
Download this repo (green **Code → Download ZIP**) and unzip it, or:
```bash
git clone https://github.com/mariwatts/fivesim.git
```

**2 · Build it**
```bash
cd fivesim
python build.py
```
This creates three files in the `dist/` folder:
- `fivesim.ts4script` — the mod
- `5imulites_interactions.package` — the in-game button
- `5imulites_icons.package` — the logo icon

**3 · Install into The Sims 4**
Copy all three `dist/` files into:
```
Documents\Electronic Arts\The Sims 4\Mods\
```
Also download **Sims4CommunityLibrary** and drop its package in the same `Mods\` folder.

**4 · Turn on mods in the game**
Launch the game → **Settings → Game Options → Other** →
☑ **Enable Custom Content and Mods** + ☑ **Script Mods Allowed** →
**restart the game**. (Script mods only load after a restart.)

**5 · Start the "brain" (host)**
On the same PC, start the [5imulites host](https://x.com/5imulites)
(`npm run dev` → opens `localhost:4000`). This is where your OpenRouter key lives
and where the AI calls happen.

**6 · Play**
Load a household and enter the lot. Then **click a Sim**:
- **5imulites ♦ Setup** → paste your OpenRouter key
- **5imulites ♦ Let AI play this Sim** → the AI takes over 🎉
- **5imulites ♦ Stop AI** → take control back

That Sim now reads its own needs, asks its model what to do, and acts on it.

---

## 🕹️ No button? Use the cheat console

If you skip Sims4CommunityLibrary, you can still drive everything from the cheat
console (**Ctrl + Shift + C**):

```
fivesim.key sk-or-v1-…      ← paste your OpenRouter key
fivesim.connect             ← link the host to this game
fivesim.sims                ← shows each Sim and its id
fivesim.map gpt 12345       ← give Sim 12345 to "gpt" (also: claude, gemini, deepseek, qwen)
fivesim.start               ← AI starts playing
fivesim.status              ← see what's running
fivesim.stop                ← stop
```

Type `fivesim.help` to see them all.

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

**The pie-menu button doesn't show up.**
Make sure both Sims4CommunityLibrary **and** `5imulites_interactions.package` are
in `Mods\`, and that you restarted the game after enabling script mods. (The cheat
commands always work even without the button.)

**It says "host unreachable".**
Start the host app (`npm run dev`) on the same PC first — that's the brain.

**`curl /health` won't connect.**
Script mods aren't enabled, you didn't restart, or you're still in the main menu —
load into a lot. Check the `lastException` / `mod_logs` files in your
`Documents\Electronic Arts\The Sims 4\` folder.

**The logo icon doesn't appear.**
Optional — the mod works fine without it. To force it, repackage `assets/logo.png`
in Sims 4 Studio (type `0x2F7D0004`, instance `0x5130A1A1A1A10001`).

**No Python?**
You can also just zip the `fivesim` folder and rename it to `fivesim.ts4script`
(keep the inner `fivesim\…` path). The packages need Python though.

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
| `fivesim/commands.py` | the cheat-console commands |
| `fivesim/host_client.py` | talks to the local host |
| `build*.py` | package the mod + button + icon |

Everything runs on `127.0.0.1` only; the key never leaves your PC.

## License

MIT © 2026 Mari
