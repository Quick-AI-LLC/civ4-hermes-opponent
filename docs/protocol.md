# Protocol: State & Command JSON Schemas

The WSL bridge (`bridge/civ4_bridge.py`) and the Civ4 game-side client (`mod/game-files/hermes_bridge.py`) communicate via TCP on port 3334.

## Handshake Flow

```
Civ4 Python SDK                          WSL Bridge
      │                                       │
      │  ─── State JSON + \n ──────────────►  │
      │                                       │  writes to
      │                                       │  civ4_state.json
      │                                       │  reads from
      │                                       │  civ4_commands.json
      │  ◄── Commands JSON + \n ────────────  │
      │                                       │
      │  executes commands                    │
      │  (move, found, build, research)       │
```

## State JSON (Civ4 → Bridge)

Sent every turn from `hermes_bridge.on_hermes_player_turn()`.

```json
{
  "player_id": 1,
  "leader": 15,
  "civ": 16,
  "turn": 175,
  "year": 1150,
  "gold": 47,
  "numCities": 5,
  "numUnits": 29,

  "cities": [
    {
      "id": 8192,
      "name": "Delhi",
      "x": 61, "y": 23,
      "population": 7,
      "production": { "name": "Swordsman", "turnsLeft": 1, "isBuildingUnit": false },
      "growth": { "foodPerTurn": 17, "foodStored": 21, "foodNeeded": 44, "turnsToGrow": 2, "isStarving": false }
    }
  ],

  "units": [
    {
      "id": 360448,
      "x": 58, "y": 32,
      "unitType": 57,
      "movesLeft": 60,
      "damage": 0
    }
  ],

  "knownTechs": [0, 1, 2, 3, 4, 5, ...],
  "currentResearch": 34,

  "diplo": {
    "metCivs": [0, 1, 2, 3, 4, 6],
    "attitudes": [{ "playerId": 0, "level": 2 }],
    "warStatus": [{ "playerId": 0, "atWar": false }],
    "activeDeals": [{ "partner": 6, "type": "openBorders", "ourItems": [], "theirItems": [] }]
  },

  "visibleEnemies": {
    "totalVisible": 0,
    "byOwner": {}
  },

  "_received_at": 1780696302.39
}
```

### Tech ID Reference

Tech IDs are from `Assets/XML/Technologies/TechInfo.xml` (Civ4 BtS):

| ID | Tech | ID | Tech | ID | Tech |
|----|------|----|------|----|------|
| 0 | Mysticism | 27 | Agriculture | 59 | Hunting |
| 1 | Meditation | 28 | Pottery | 60 | Mining |
| 2 | Polytheism | 30 | Sailing | 61 | Archery |
| 3 | Priesthood | 31 | Writing | 62 | Masonry |
| 4 | The Wheel | 32 | Calendar | 63 | Animal Husbandry |
| 5 | Monotheism | 33 | Alphabet | 64 | Bronze Working |
| 7 | Code of Laws | 34 | Construction | 66 | Iron Working |
| 25 | Fishing | 35 | Currency | 67 | Metal Casting |
| 26 | The Wheel | 36 | Philosophy | | |

Full list at `docs/tech-reference.md`.

### Unit Type ID Reference

From `Assets/XML/Units/CIV4UnitInfos.xml`:

| ID | Unit | ID | Unit |
|----|------|----|------|
| 4 | Settler | 37 | Spearman |
| 5 | Worker | 57 | Archer |
| 6 | Indian Fast Worker | 60 | Chariot |
| 24 | Warrior | 117 | Artist (Great Person) |
| 30 | Axeman | | |

---

## Commands JSON (Bridge → Civ4)

Written to `civ4_commands.json` by the AI agent and synced to the Windows filesystem. The in-game `hermes_bridge.py` reads and executes them.

### Research
```json
{ "action": "research", "tech": 34 }
```
Sets current research target (via AI_chooseTech callback).

### Move
```json
{ "action": "move", "unitId": 294933, "x": 60, "y": 31 }
```
Teleports unit to (x, y). Used for strategic repositioning.

### Found City
```json
{ "action": "found", "unitId": 294933, "x": 60, "y": 31 }
```
Settler builds a city at (x, y). Queued after move via `bAppend=True`.

### Build
```json
{ "action": "build", "cityId": 8192, "unit": "axeman" }
```
Sets city production. Uses `gc.getInfoTypeForString("UNIT_" + name.upper())` for generic unit lookup.

### Command File Path Resolution (Windows-side)
The game-side Python 2.4 client searches in order:
1. Relative path from Assets/Python/ up to the game root, then .hermes/civ4_commands.json
2. `~/.hermes/civ4_commands.json` (user home)
3. `C:\Users\gainq\.hermes\civ4_commands.json` (absolute fallback)
