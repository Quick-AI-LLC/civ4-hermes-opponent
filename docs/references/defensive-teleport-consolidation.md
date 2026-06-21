# Defensive Teleport Consolidation

## When to Use

When an enemy stack is within 1-2 turns of one of your cities and you need immediate defenders. The `move` action's `u.setXY()` teleport lets you pull combat units from across your territory instantly.

## Technique Proven (June 2026 Session)

- **Situation:** Dutch stack 2 tiles north of Awdaghost (45,24). City had 2 catapults + 1 mystery unit. Essentially undefended.
- **Available forces:** 18 macemen + crossbowman at Tekedda (42,21) — 3 tiles west, zero moves left. ~35 macemen at Tadmekka (50,21) — some with full moves, many at 0. Cannons/macemen at Gao area (49,30), (50,23).
- **Action:** Wrote 39 simultaneous teleport commands, all targeting (45,24). Included units with 0 movesLeft (setXY ignores movement).
- **Result:** All 39 units teleported to Awdaghost in one turn. No crashes, no group issues (CyUnit.setXY() moves individual units out of shared groups).

## Command batch pattern

Write all commands to `civ4_commands.json` at once. The bridge delivers them as a batch to exec_cmds():

```json
[
  {"action": "move", "unitId": 2875557, "x": 45, "y": 24},
  {"action": "move", "unitId": 1589269, "x": 45, "y": 24},
  ... 37 more units ...
]
```

## Key Properties

- **setXY ignores movesLeft** — units with 0 movement can be teleported. This is essential because the DLL AI often moves units during its processing, leaving them with 0 or partial moves.
- **CyUnit.setXY() vs CySelectionGroup.setXY()** — the deployed code uses `u.setXY()` directly on the CyUnit object, which extracts that unit from its shared group. Does NOT crash like group-level setXY.
- **No joinGroup(None) needed** — each individual setXY call operates independently.
- **Distance doesn't matter** — teleport from anywhere on map to anywhere.
- **All unit types work** — macemen, catapults, cannons, crossbowmen, workers.

## ⚠️ DLL Moves-Burning Constraint

After teleporting 40 units to a city on turn N, only ~11 had movesLeft on turn N+2 in the June 2025 session. The DLL's `AI_unitUpdate` (`return False` in standard mode) burns movement points during its processing each turn — units on the same tile get fortified, moved randomly, or have their moves consumed.

**Impact on follow-up attacks:**
- Teleported defenders absorb attacks fine (don't need moves to defend a city)
- But launching an offensive from the teleported stack on the next turn is limited to the fraction of units the DLL didn't touch
- **Workaround:** Teleport units directly to the attack tile (enemy-occupied) on the teleport turn itself, triggering combat immediately via bCheckCollateral=True. This bypasses the DLL-burns-moves problem. See `references/offensive-teleport-attack.md`.

## When NOT to use

- For gradual troop movements (use DLL AI or pathfinding moves) — teleport looks like cheating
- When you want to park units on multiple tiles (setXY puts everything on one tile)
- For settlers founding cities (the `found` action already handles this via pushMission)
