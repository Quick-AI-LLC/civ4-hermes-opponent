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

### 2. Hotseat (Full Control — Under Development)

In hotseat multiplayer mode, player 2 is a **human slot** — the DLL does not override anything. The same bridge hooks into the player 2 turn and executes commands with **total control**: workers, tiles, diplomacy, civic switching, everything.

Both models use the same bridge and protocol. Only the game-side hook code differs.

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

## Hotseat Model (Planned)

The hotseat variant will give the agent **full control** over its civilization without DLL interference:

- Player 1: Human (keyboard/mouse)
- Player 2: Agent (TCP bridge)
- All DLL AI bypassed — agent controls workers, tiles, diplomacy, civics
- Same bridge, same protocol — only the event hook logic changes

See `models/hotseat/` for the in-progress implementation.

## Tech Tree Reference

See `docs/tech-reference.md` for complete tech ID mapping (IDs 0-96) including era, prerequisites, and unlocks.

## Repository Structure

```
civ4-hermes-opponent/
├── bridge/                   # WSL-side TCP listener (Python 3)
│   ├── civ4_bridge.py        # Pure relay, no AI logic
│   └── requirements.txt
├── mod/
│   ├── game-files/           # Copy these into Assets/Python/
│   │   ├── hermes_bridge.py  # Windows-side game client (Python 2.4)
│   │   └── simplejson.py     # JSON lib for Python 2.4
│   └── patches/              # Unified diffs for existing files
│       ├── CvEventManager.py.diff
│       └── CvGameUtils.py.diff
├── docs/
│   ├── protocol.md           # State/command JSON schemas
│   └── tech-reference.md     # Tech IDs, unit type IDs
└── README.md
```

## License

MIT — Quick AI LLC, Hayden, ID

Built for experimental agentic organization research. Civ4 is property of 2K Games / Firaxis.
