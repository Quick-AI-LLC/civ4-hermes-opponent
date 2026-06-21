# State Analysis Protocol — Systematic Multi-Pass Read

When the user ends a turn and says "clicked over" / "go" / "your turn", run this analysis in order. Each pass builds on the last. Do not skip passes — the pattern catches things a single look misses.

## Pass 1 — Freshness Check

Before analyzing, confirm the bridge delivered fresh data:

```python
import json, time
with open('/home/gainq/.hermes/civ4_state.json') as f:
    state = json.load(f)
print('_received_at:', state.get('_received_at'))
print('Turn:', state.get('turn'))
print('Year:', state.get('year'))
```

- `_received_at` should be recent (within last 60 seconds of the current turn)
- Turn should have advanced by 1
- If stale, the bridge may have missed the connection — ask Nick to end another turn

## Pass 2 — Headline Stats

Quick scan for change detection:

| Stat | What to check | Red flag |
|------|---------------|----------|
| `numCities` | Did we lose/gain any? | Fewer = city captured |
| `numUnits` | Dropped significantly? | Losses from combat |
| `gold` | Can we afford upgrades? | <100 gold = tight |
| `currentResearch` | Pivoting toward military tech? | Still on peaceful tech |

## Pass 3 — Unit Type Breakdown

Count all units by `unitType` to identify obsolete core:

```python
from collections import Counter
type_counts = Counter(u['unitType'] for u in state['units'])
```

**Questions to answer:**
- What is our **main combat unit** (highest count among military types)?
- Are we still fielding **medieval units** (Macemen = type 34 etc.) when we have **industrial tech** (Replaceable Parts 74+)?
- How many **workers** (type 5) vs military?
- Any **type 111** units (great people / special)?

## Pass 4 — Position Clustering

Find where forces are actually sitting:

```python
pos_counts = Counter((u['x'], u['y']) for u in state['units'])
```

**Map the big stacks:**
- Where is the **main army** stacked? (largest cluster)
- Is it on the **front line** or sitting behind it?
- Any **isolated units** far from any city?

**Compare to city coordinates:**
- Main stack at (45,26) while Awdaghost is at (45,24) = army is 2 tiles north of the front
- Main stack at (50,21) while Tadmekka is at (50,21) = army IS at the front

## Pass 5 — Front-Line vs Interior Split (Critical)

Filter units by city proximity to the known enemy border:

Count military combat units (NOT workers, NOT siege) at each threatened city tile. If a frontline city has 0-1 real defenders, it falls in one turn.

**Typical bad pattern:** 70+ units stacked at a rear staging tile — well behind the front — while the actual border cities have 0-1 combat units.

**Fix:** setXY teleport from the main stack directly into the undefended cities.

## Pass 6 — City Production Audit

Inspect every city's `production` field:

```python
for c in state['cities']:
    name, prod = c['name'], c.get('production', {})
    print(f'{name}: {prod.get("name","?")} ({prod.get("turnsLeft","?")}t)')
```

**What to check:**
- **Obsolete units:** Any city building Pikeman when we have Rifling? Switch to Rifleman.
- **Wrong buildings:** Stable (16t), Temple (7t), Bank (20t) while at war = misplaced priorities. Switch to military.
- **Already-building the right thing:** Leave it alone.
- **Food/growth:** Cities with high food can run more specialists or grow faster — relevant for economies but lower priority during war.

## Pass 7 — Tech Assessment

Check knownTechs vs what our units need:

```python
kt = state.get('knownTechs', [])
cr = state.get('currentResearch')
```

**Critical military techs (XML-confirmed — see `references/bts-full-tech-tree.md` for full mapping):**\n- 73 = Gunpowder → Musketmen\n- 74 = Replaceable Parts → **Riflemen** (key industrial upgrade)\n- 76 = Rifling → (next military tier)\n- 78 = Steel → **Infantry** + Artillery (modern line)\n- 82 = Industrialism → **Tank**, Marine\n- 88 = Rocketry → SAM Infantry, Mobile SAM\n\n**If we have Replaceable Parts (74) but most units are Macemen (34):**\n- We can build Riflemen now (ID 46)\n- Need ~200+ gold per maceman upgrade (unlikely to afford many)\n- **Action:** Switch ALL cities to Rifleman production; existing macemen serve as cannon fodder until new riflemen arrive

## Pass 8 — Strategic Assessment Brief (Output Format)

Deliver to the user as a **concise brief**, with your current mode stated:

```
Turn 397, 1977 AD — MODE: War — 13 cities, 130 units, 77g

FORCES: 80 Macemen (main), 21 Catapults, 15 Workers, rest filler
POSITION: Main stack (70) at (45,26) — 2 tiles north of the front. 
FRONT: NW city has 2 catapults and nothing else. Southern city similar. 
PRODUCTION: Capital+Rifleman(5t) ✓, NW city+Rifleman(3t) ✓ — but 
  E city/Pikeman(7t) should be Riflemen
  Border city/Stable(16t), Interior/Temple(7t) — switch to military for War mode
RESEARCH: Current = 46 (Biology) — DRIFTING. Overriding to 78 (Steel).

PLAN: Move main stack to front. Switch E cities to Riflemen. Fix research.
```

**Keep it under 6 lines.** Nick reads fast and hates walls of text.

## ⚠️ Common Mistakes This Protocol Catches

- **Army behind the front:** The DLL moves units randomly. Your carefully stacked army may end up 2-3 tiles away from where it needs to be. setXY fixes this.
- **Obsolete production:** Building Pikemen (medieval) when you have Rifling = wasted hammers.
- **Empty southern cities:** The sneak attack pattern. A city with 0 combat units is captured instantly.
- **Only gold matters:** 77 gold with 80 macemen = you can't upgrade. Build new riflemen instead.
- **Workers are not defenders:** Type 5 workers at a city tile don't count as garrison.
