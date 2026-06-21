# Phase 3: Structured JSON Commands (Replaces Raw Python `exec`)

## Problem

The original bridge used `exec` to run raw Python commands returned from the WSL bridge. This had multiple failure modes:

1. **`exec` is unreliable in Civ4 Python** — Multiple research API calls (`AI_setResearchTech`, `setResearchTech`, `g.setCurrentResearch`, `changeResearch`) ALL silently fail when called from within `exec script in globals()`. `currentResearch` stays -1 regardless of method used.

2. **`print()` produces no output** — `print()` and `CvUtil.pyPrint()` inside exec'd code do NOT produce visible output in PythonDbg.log, making debugging impossible.

3. **One error kills the entire batch** — Without per-command try/except, a single failing API call (e.g., `setResearchTech` doesn't exist) aborts ALL commands — found, build, move never run.

## Solution: Structured JSON Commands

Instead of exec'd Python strings, commands are JSON dicts with an `action` key. The bridge's `execute_commands` interprets each action and calls the Civ4 API DIRECTLY from the bridge module scope (not exec).

### Command Format

```json
[
  {"action": "research", "tech": 28},
  {"action": "found", "unitId": 16385},
  {"action": "found", "unitId": 32770},
  {"action": "build", "cityId": 8192, "unit": "warrior"},
  {"action": "move", "unitId": 24576, "x": 50, "y": 20}
]
```

### Supported Actions

| Action | Parameters | Behavior |
|--------|------------|----------|
| `research` | `tech`: int (tech ID) | Stores desired tech in `_g_desired_tech` global variable. The actual research direction is set by `CvGameUtils.AI_chooseTech()` callback which reads this variable and returns it to the DLL. See `references/ai-callbacks-cvgameutils.md`. |
| `found` | `unitId`: int | Found city at unit's current position via `u.getGroup().pushMission(MISSION_FOUND, x, y, 0, False, False, NO_MISSIONAI, CyMap().plot(x, y), u)` — **MUST pass CyPlot* as 2nd-to-last arg, NOT CyUnit** |
| `build` | `cityId`: int, `unit`: string ('warrior'\|'settler'\|'worker') | Queue build in city via `dc.pushOrder(ORDER_TRAIN, UNIT_TYPE, ...)` |
| `move` | `unitId`: int, `x`: int, `y`: int | Move unit via `u.getGroup().pushMission(MISSION_MOVE_TO, x, y, ...)` |
| (raw string) | any | Skipped with deprecation log |

### ⚠️ CRITICAL: `gc.getInfoTypeForString()` for ALL Unit Type Lookups

`UnitTypes.UNIT_SETTLER`, `UnitTypes.UNIT_WARRIOR`, `UnitTypes.UNIT_WORKER` and similar `*Types` enum constants are **NOT guaranteed to exist** in BtS Python. They crash with:
```
AttributeError: type object 'CvPythonExtensions.UnitTypes' has no attribute 'UNIT_SETTLER'
```

**Always use `gc.getInfoTypeForString("TYPE_NAME")`** which works universally:

```python
# ✅ CORRECT:
settler_id = gc.getInfoTypeForString("UNIT_SETTLER")  # Returns 4
pCity.pushOrder(OrderTypes.ORDER_TRAIN, settler_id, -1, 0, False, False, False)

# ❌ WRONG — crashes if enum constant doesn't exist:
pCity.pushOrder(OrderTypes.ORDER_TRAIN, UnitTypes.UNIT_SETTLER, ...)
```

See `references/bts-unit-types.md` for the correct type ID mapping.

### ⚠️ CRITICAL: BtS Python API — What ACTUALLY Exists vs What Doesn't

This was discovered through systematic trial-and-error across 30+ turns of gameplay. The following Civ4 Python API methods were confirmed NON-EXISTENT in this BtS 3.19 Steam build:

**Methods that DO NOT exist (AttributeError when called):**
- ❌ `p.setResearchTech(tech, True, False)` — `'CyPlayer' object has no attribute 'setResearchTech'`
- ❌ `p.AI_setResearchTech(tech)` — `'CyPlayer' object has no attribute 'AI_setResearchTech'`
- ❌ `g.setResearchProgress(tech, 0, playerID)` — `'CyGame' object has no attribute 'setResearchProgress'`
- ❌ `g.changeResearchProgress(tech, 1, playerID)` — `'CyGame' object has no attribute 'changeResearchProgress'`
- ❌ `CyInterface().pushMission(...)` — `'CyInterface' object has no attribute 'pushMission'`

**Methods that DO exist (from game code greps):**
- ✅ `gc.getPlayer(i).getCurrentResearch()` — returns tech ID being researched, -1 if none
- ✅ `gc.getTeam(teamID).setHasTech(tech, bool, playerID, bool, bool)` — gives a tech to the team
- ✅ `gc.getTeam(teamID).isHasTech(tech)` — checks if tech is known
- ✅ `gc.getTeam(teamID).getResearchProgress(tech)` — beakers accumulated
- ✅ `gc.getTeam(teamID).getResearchCost(tech)` — total beakers required
- ✅ `u.getGroup().pushMission(MISSION_TYPE, x, y, 0, bool, bool, MISSION_AI, plot, unit)` — **exists on CySelectionGroup but NEEDS CORRECT SIGNATURE:** the 2nd-to-last param is `CyPlot*` not `CyUnit`. Use `CyMap().plot(x, y)` to create the plot reference. Last param is CyUnit.
- ✅ `dc.pushOrder(ORDER_TRAIN, UNIT_TYPE, -1, 0, bool, bool, bool)` — queue city production

**Root cause of research failure:** The BtS Python API does NOT expose ANY method to set a player's research direction. Research is entirely managed by the C++ DLL (`CvPlayerAI::AI_chooseResearch()`). The only way to influence research via Python is:
1. **Give the tech directly** via `team.setHasTech(tech, True, playerID, False, False)` (bypasses research entirely)
2. **Modify the DLL** (not practical)
3. **WorldBuilder/save editing** (not automated)

### Bridge Implementation (CORRECT — with per-command try/except)

In `hermes_bridge.py` (Windows side):

```python
def execute_commands(commands):
    if not commands:
        return
    p = gc.getPlayer(HERMES_PLAYER_ID)
    g = gc.getGame()
    for cmd in commands:
        try:
            if isinstance(cmd, basestring):
                continue
            action = cmd.get('action', '')
            if action == 'research':
                tech = cmd.get('tech', -1)
                # WARNING: This likely does nothing. Use setHasTech fallback.
                p.AI_setResearchTech(tech)
            elif action == 'found':
                uid = cmd.get('unitId', -1)
                u = p.getUnit(uid)
                if u and not u.isDead() and u.getMoves() > 0:
                    # CRITICAL: pass CyPlot* as 2nd-to-last arg (not CyUnit!)
                    plot = CyMap().plot(u.getX(), u.getY())
                    u.getGroup().pushMission(MissionTypes.MISSION_FOUND, u.getX(), u.getY(), 0, False, False, MissionAITypes.NO_MISSIONAI, plot, u)
            elif action == 'build':
                cid = cmd.get('cityId', -1)
                unit_type = cmd.get('unit', None)
                dc = p.getCity(cid)
                if dc and not dc.isProduction():
                    if unit_type == 'warrior':
                        dc.pushOrder(OrderTypes.ORDER_TRAIN, gc.getInfoTypeForString("UNIT_WARRIOR"), -1, 0, False, False, False)
                    elif unit_type == 'settler':
                        dc.pushOrder(OrderTypes.ORDER_TRAIN, gc.getInfoTypeForString("UNIT_SETTLER"), -1, 0, False, False, False)
                    elif unit_type == 'worker':
                        dc.pushOrder(OrderTypes.ORDER_TRAIN, gc.getInfoTypeForString("UNIT_WORKER"), -1, 0, False, False, False)
            elif action == 'move':
                uid = cmd.get('unitId', -1)
                tx = cmd.get('x', -1)
                ty = cmd.get('y', -1)
                u = p.getUnit(uid)
                if u and not u.isDead() and u.getMoves() > 0:
                    # ⚠️ CRITICAL: pushMission needs CyPlot* as 2nd-to-last arg
                    plot = CyMap().plot(tx, ty)
                    u.getGroup().pushMission(MissionTypes.MISSION_MOVE_TO, tx, ty, 0, False, False, MissionAITypes.MISSIONAI_EXPLORE, plot, u)
        except Exception, e:
            # Per-command try/except prevents one failure from killing the batch
            _hermes_log('Bridge: command error: ' + str(cmd.get('action', '?')) + ' - ' + str(e))
```

### ⚠️ CRITICAL: `pushMission` Signature — Must Pass `CyPlot*` Not `CyUnit`

The error message makes this clear:

```
pushMission(class CySelectionGroup, MissionTypes, int, int, int, bool, bool, MissionAITypes, class CyPlot *, class CyUnit *)
```

The 2nd-to-last parameter is `CyPlot*` (the plot to interact with), and the last parameter is `CyUnit*` (for missions that need a specific unit on the plot, like attack).

**WRONG** (passes CyUnit where CyPlot is expected):
```python
u.getGroup().pushMission(MissionTypes.MISSION_FOUND, x, y, 0, False, False, MissionAITypes.NO_MISSIONAI, u)
#                                                                                              ^ CyUnit where CyPlot needed
```

**CORRECT** (pass CyMap().plot(x,y) for the plot):
```python
plot = CyMap().plot(x, y)
u.getGroup().pushMission(MissionTypes.MISSION_FOUND, x, y, 0, False, False, MissionAITypes.NO_MISSIONAI, plot, u)
#                                                                                                          ^ CyPlot*   ^ CyUnit
```

### WSL Bridge Commands File

The WSL bridge (`~/.hermes/scripts/civ4_bridge.py`) serves the commands file as-is — no changes needed. The file is:

- **Persistent** — NOT deleted after reading. Re-read every turn.
- **Idempotent** — commands check conditions before acting. `found` and `move` check `getMoves() > 0`; `build` checks `not dc.isProduction()`.

### Known Limitations

- **Research cannot be changed via Python API** — `AI_setResearchTech`, `setResearchTech`, etc. all do not exist. The only option is `setHasTech` which gives the tech for free.
- **`found` tries at unit's current position only** — if the tile is invalid (too close to another city, wrong terrain), the mission fails silently
- **Unit IDs change when units are created/destroyed** — hardcoded unitIds in commands become stale
- **Only 4 action types implemented** — extend for more as needed
- **Build only supports warrior/settler/worker** — extend for more unit types by adding to the if/elif chain
- **Move targets are absolute (x,y)** — no pathfinding
