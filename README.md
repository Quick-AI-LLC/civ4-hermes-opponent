# Civ4 Hermes Opponent

Python-bridge mod that makes a language model act as the AI opponent in Civilization IV: Beyond the Sword. An agentic commerce / experimental AI integration project by [Quick AI LLC](https://quickai.build).

## How It Works

```
LLM Agent (WSL/Linux)                  Civ4 (Windows)
      │                                      │
      │  reads state, decides moves          │
      │       │                              │
      │  writes civ4_commands.json           │
      │       │                              │
      │  ─── TCP :3334 ──────────────────►   │  sends game state
      │  ◄── commands ─────────────────────   │  executes moves,
      │                                      │  founds cities,
      │                                      │  queues research
```

The agent is the **AI opponent**. The Python scripts are pure transport and execution — no AI logic in the bridge.

## Two Models

### 1. Standard (DLL Callbacks — Working Now)

The current implementation patches the base game files to hook Python callbacks exposed by the Civ4 DLL:

- `CvEventManager.onBeginPlayerTurn` / `onEndPlayerTurn` — state collection & command execution
- `CvGameUtils.AI_chooseTech` / `AI_chooseProduction` — research & production control
- `CvGameUtils.AI_unitUpdate` — prevents DLL from overriding agent's unit moves

**Limitation:** The DLL AI still runs and can override agent decisions. Not all control paths are available (workers, diplomacy, civics).

### 2. Hotseat (Full Control)

In hotseat multiplayer mode, player 2 is a **human slot** — no DLL AI runs. The bridge hooks `onBeginPlayerTurn` for P2, executes commands (including research via `pushResearch`), then auto-ends the turn via `CyMessageControl().sendTurnComplete()` so control returns to P1 without keyboard input.

Both models use the same WSL bridge and protocol. Only the Windows-side Python client and `CvEventManager` hook differ.

## Quick Start

### Prerequisites

- Civilization IV: Beyond the Sword (Steam or disc)
- WSL2 (Windows Subsystem for Linux) with Python 3
- Python 2.4 runtime (comes with Civ4 — `python24.dll` in the game root)
- Network connectivity between WSL and Windows

### 1. Install Game Files

**Option A — Full replacement (recommended):**
Copy the files from `mod/game-files/` into `Beyond the Sword/Assets/Python/`:
```
copy mod\game-files\hermes_bridge.py     "C:\Program Files (x86)\Steam\...\Beyond the Sword\Assets\Python\"
copy mod\game-files\simplejson.py        "C:\Program Files (x86)\Steam\...\Beyond the Sword\Assets\Python\"
```

**Option B — Patch existing files:**
```bash
# In Beyond the Sword/Assets/Python/
patch < mod/patches/CvEventManager.py.diff
patch < mod/patches/CvGameUtils.py.diff
```

**Important:** Apply to ALL three game directories for compatibility:
- `Beyond the Sword/Assets/Python/`
- `Warlords/Assets/Python/`

And set in `CivilizationIV.ini`:
```
Mod = 0
LoggingEnabled = 1
```

### 2. Start the Bridge

```bash
# On WSL/Linux
python3 bridge/civ4_bridge.py
```

The bridge listens on port 3334. It writes received state to `~/.hermes/civ4_state.json` and reads commands from `~/.hermes/civ4_commands.json`.

### 3. Play

Load Civ4 and start a game on the Hermes player's turn. Each turn, the game state is sent to the bridge, and any pending commands are executed.

## Protocol

See `docs/protocol.md` for the complete state JSON and command JSON schemas.

### Basic Commands

```json
[
  { "action": "research", "tech": 34 },
  { "action": "build", "cityId": 8192, "unit": "axeman" },
  { "action": "move", "unitId": 294933, "x": 60, "y": 31 },
  { "action": "found", "unitId": 294933, "x": 60, "y": 31 }
]
```

### State Files

| File | Location | Purpose |
|------|----------|---------|
| `civ4_state.json` | `~/.hermes/` (WSL) | Game state from Civ4 → Agent |
| `civ4_commands.json` | `~/.hermes/` (WSL) + `C:\Users\<user>\.hermes\` (Windows) | Agent commands → Civ4 |

## Hotseat Model

The hotseat variant gives the agent **full control** over P2 without DLL AI interference:

- Player 1 (slot 0): Human (keyboard/mouse, unchanged)
- Player 2 (slot 1): Agent (TCP bridge)
- No `CvGameUtils.py` patches needed — `AI_chooseTech` / `AI_chooseProduction` / `AI_unitUpdate` do not fire for human slots
- Research and builds are applied directly in `exec_cmds()` on the begin-turn hook
- Turn auto-ends after command execution via `onUpdate` polling (no keyboard input required)
- **Important:** `onBeginPlayerTurn` / `onEndPlayerTurn` fire during automated `doTurn()` resolution, not when hotseat hands control to P2. The hook must be `onUpdate` + `tick_hotseat()`.

### Install Hotseat Files

Copy from `mod/hotseat/` instead of `mod/game-files/`:

```
copy mod\hotseat\game-files\hermes_bridge.py   "...\Beyond the Sword\Assets\Python\"
copy mod\game-files\simplejson.py              "...\Beyond the Sword\Assets\Python\"
```

Apply the hotseat event hook (not the standard one):

```bash
# In Beyond the Sword/Assets/Python/
patch < mod/hotseat/patches/CvEventManager.py.diff
```

Repeat for `Warlords/Assets/Python/`. **Do not** apply `mod/patches/CvGameUtils.py.diff` — restore vanilla `CvGameUtils.py` if previously patched.

Start a **hotseat** game with two human slots. P1 plays normally; on P2's turn the bridge fires, executes commands, and auto-transitions back to P1.

## Tech Tree Reference

See `docs/tech-reference.md` for complete tech ID mapping (IDs 0-96) including era, prerequisites, and unlocks.

## Repository Structure

```
civ4-hermes-opponent/
├── bridge/                   # WSL-side TCP listener (Python 3)
│   ├── civ4_bridge.py        # Pure relay, no AI logic
│   └── requirements.txt
├── mod/
│   ├── game-files/           # Standard model — copy into Assets/Python/
│   │   ├── hermes_bridge.py  # Windows-side game client (Python 2.4)
│   │   └── simplejson.py     # JSON lib for Python 2.4
│   ├── patches/              # Standard model patches
│   │   ├── CvEventManager.py.diff
│   │   └── CvGameUtils.py.diff
│   └── hotseat/              # Hotseat model (full P2 control)
│       ├── game-files/
│       │   └── hermes_bridge.py
│       └── patches/
│           └── CvEventManager.py.diff
├── docs/
│   ├── protocol.md           # State/command JSON schemas
│   └── tech-reference.md     # Tech IDs, unit type IDs
└── README.md
```

## License

MIT — Quick AI LLC, Hayden, ID

Built for experimental agentic organization research. Civ4 is property of 2K Games / Firaxis.
