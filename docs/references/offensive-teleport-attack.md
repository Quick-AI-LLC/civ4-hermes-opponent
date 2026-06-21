# Offensive Teleport Attack — Proven Pattern

`setXY()` with `bCheckCollateral=True` triggers combat when teleporting onto an enemy-occupied tile. This was proven in the June 2025 Dutch-Mali war session.

## Session Context (Turn 372-373)

- Awdaghost (45,24) was threatened by a ~20-unit Dutch stack at (45,23) — 1 tile north
- Dutch composition: trebuchets and cavalry mostly (moderate melee counters)
- Awdaghost garrison: 40 units (35 macemen + 5 cannons/catapults), teleported in via defensive consolidation
- By the next turn, only ~11 macemen + 1 cannon had moves left (DLL AI_unitUpdate burned moves on the rest)

## The Attack

**Command:** 12 units teleported from Awdaghost (45,24) to Dutch tile (45,23):
```json
[{"action": "move", "unitId": 1318925, "x": 45, "y": 23},
 {"action": "move", "unitId": 1671186, "x": 45, "y": 23},
 ...11 macemen + 1 cannon total]
```

**Result:**
- My unit count: 168 → 154 (-14)
- 5 survivors at attack tile (45,23): 4 macemen (1 near-dead 91%, 1 damaged 22%, 1 clean, 1 clean) + 1 cannon (full health)
- Enemy stack: ~20 → ~8 damaged survivors (per human's recon, not shown in state)
- Awdaghost held with 20 remaining units (mix of damaged/undamaged)
- Combat was one-sided macemen vs mixed trebuchet/cavalry — favorable kill trade

## Key Observations

### 1. Offensive setXY Works
`u.setXY(tx, ty, False, True, True)` with `bCheckCollateral=True` triggers game-engine combat when the target tile has enemy units. The combat resolves during `onEndPlayerTurn` processing.

### 2. MovesLeft Is Irrelevant for setXY
`setXY` does NOT check `getMoves()`. Units with 0 movesLeft can be teleported and will fight. In this session, only units with >0 moves were sent (an unforced constraint). All 40 could have been sent.

### 3. DLL Burns Moves on Teleported Defenders
After teleporting 40 units to Awdaghost on turn N, only 11 had movesLeft on turn N+2. The DLL's `AI_unitUpdate` (returning False = let DLL handle) consumes movement points on fortified/sleeping units. This means:
- **Defensive teleport is best for absorbing attacks** — units are there even without moves
- **Offensive follow-up has limited force** — only units the DLL didn't move are attack-capable
- **Solution:** Teleport ALL combat units to the attack tile regardless of movesLeft. The combat resolves regardless of movement points.

### 4. Batch Teleport Works for Attack Too
The same batch teleport pattern (39 commands in one turn, proven defensive) works for offensive teleports. Each `u.setXY()` individually moves that CyUnit out of any shared group.

### 5. No setXY Crash
Despite the old skill warning about `setXY()` causing group-level teleport crashes, the deployed `CyUnit.setXY()` (individual unit) worked fine for offensive teleports. The crash risk only applies to `CySelectionGroup.setXY()` (group-level, NOT deployed).

## When to Use This Pattern

Use offensive teleport attack when:
- Enemy stack is **1-2 tiles from your city** (adjacent or nearly so)
- You have **numerical advantage** (2:1 or better)
- The unit matchup is favorable (melee vs siege = good)
- The human is **undeclared** and waiting for the right moment to flank (you draw aggro)
- You want to soften enemies for the human's follow-up flank

Do NOT use when:
- The tile contains a **fortified city** (setXY onto a city tile won't attack the garrison — use the `found` action or normal siege instead)
- The enemy has overwhelming modern tech (macemen vs SAM Infantry = pointless sacrifice)
- You need to preserve the garrison for multi-turn defense (offensive teleport commits units to combat)
