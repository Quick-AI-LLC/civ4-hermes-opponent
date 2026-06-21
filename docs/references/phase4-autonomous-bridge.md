# Phase 4 — Autonomous Bridge (Decision Logic in Python)

**Context:** After ~60+ turns of LLM-in-the-loop play (Nick pings → I respond → write commands), Nick said: *"You should have already had a script on the bridge that checks state and makes decisions."*

The autonomous bridge embeds decision-making logic directly in the WSL server (`civ4_bridge.py`) so it handles every turn without Discord pings.

## Architecture

```
Civ4 (Windows) → hermes_bridge.py (TCP) → civ4_bridge.py (WSL, port 3334)
                                              ↓
                                      `decide(state)` function
                                              ↓
                                      writes civ4_commands.json
                                              ↓
                                      syncs to Windows path
                                              ↓
                                      responds INSTANTLY with commands
```

The `decide()` function runs every connection, reads the state, and generates appropriate commands.

## Tech Tree Decision Logic

```python
# Priority-ordered tech path for Gandhi (India):
# Priesthood(3) → CoL(7) → Philosophy(36) → Civil Service(12) → Math(32) → Alphabet(33)
TECH_ORDER = [3, 7, 36, 12, 32, 33, 35, 4, 64, 67, 69]

# Prereq map: tech_id -> [AND_preqs, OR_preqs]
PREREQS = {
    3:  [[],     [1, 2]],      # Priesthood: Meditation OR Polytheism
    7:  [[31],   [3, 35]],     # CoL: Writing AND (Priesthood OR Currency)
    36: [[7],    []],          # Philosophy: Code of Laws
    12: [[36,32],[]],          # Civil Service: Philosophy + Math
    32: [[31],   []],           # Mathematics: Writing
    33: [[31],   []],           # Alphabet: Writing
}

def can_research(t, known):
    """Check prereqs against known techs."""
    and_pre, or_pre = PREREQS.get(t, [[], []])
    if not all(p in known for p in and_pre):
        return False
    if or_pre and not any(o in known for o in or_pre):
        return False
    return True
```

## Production Logic (v2 — Balanced Economy)

```python
def count_nearby_units(state, city_x, city_y, unit_types, radius=3):
    """Count military units within radius of a city."""
    count = 0
    for u in state.get("units", []):
        utype = u.get("unitType", -1)
        if utype in unit_types:
            dx = abs(u.get("x", 0) - city_x)
            dy = abs(u.get("y", 0) - city_y)
            if dx <= radius and dy <= radius:
                count += 1
    return count

def pick_unit_to_build(city, state):
    """Decide what to build — garrison first, then workers, then settlers."""
    x, y = city.get("x", 0), city.get("y", 0)
    num_cities = state.get("numCities", 0)
    pop = city.get("population", 1)

    total_settlers = sum(1 for u in state.get("units", []) if u.get("unitType") == 4)
    total_workers = sum(1 for u in state.get("units", []) if u.get("unitType") in (5, 6))
    total_warriors = sum(1 for u in state.get("units", []) if u.get("unitType") in (24, 57))
    nearby_defenders = count_nearby_units(state, x, y, [24, 57], 3)

    # Priority 1: Every city needs at least 2 defenders nearby
    if nearby_defenders < 2:
        return "warrior" if total_warriors < num_cities * 3 else "settler"

    # Priority 2: Workers — need at least 2 per city
    if total_workers < num_cities * 2:
        return "worker"

    # Priority 3: Settlers — expand gradually, not spam
    target_cities = min(8, 3 + num_cities)
    if num_cities < target_cities and pop >= 3:
        return "settler"

    # Priority 4: More workers for improved tiles
    if total_workers < num_cities * 3:
        return "worker"

    # Priority 5: Rinse and repeat
    if pop >= 4:
        return "settler"
    return "worker"
```

**Why this matters:** Nick explicitly corrected: "you have to be able to defend your cities and feed the people." The v1 logic only pumped settlers — cities starved and had no garrisons. The v2 logic ensures every city has defenders before expanding, and enough workers to improve tiles for food/production.

## Settler Targeting

The bridge uses offsets from existing cities to estimate settle positions:

```python
SETTLE_OFFSETS = [(3,0), (0,3), (-3,0), (0,-3), (2,2), (2,-2), (-2,2), (-2,-2)]
```

The `decide()` function also includes a `found` command when settlers are within 3 tiles of their target, and the Windows-side `hermes_bridge.py` removes the `movesLeft > 0` guard on `MISSION_FOUND` so settlers can found on the same turn they arrive.

## Key Differences from LLM-in-the-Loop

| Aspect | Phase 3 (LLM) | Phase 4 (Autonomous) |
|--------|---------------|----------------------|
| Decision maker | LLM reads state, writes commands | `decide()` in bridge script |
| Response time | Minutes/hours (wait for ping) | Instant (every turn) |
| Turn coverage | Only turns after LLM responds | EVERY turn |
| Strategy quality | High (LLM reasoning) | Medium (coded heuristics) |
| Nick interaction | "few turns passed" pings | Silent — runs in background |

## Ongoing LLM Role

Even with autonomous bridge, the LLM still:
1. Monitors state periodically (every 5-10 turns)
2. Adjusts tech path if game situation changes
3. Fixes bugs when autonomous decisions go wrong
4. Adds new decision logic for new situations

## Known Pitfalls

- **`MISSION_FOUND` must NOT require moves** — the `found` action in `hermes_bridge.py` (Windows-side) originally checked `u.getMoves() > 0`. Since `move` runs before `found` in the same command batch, the unit had 0 moves by the time `found` executed. Fix: remove the moves guard — `MISSION_FOUND` queues correctly without it.
- **Settlers can't found on the same tile as another city** — if a new settler spawns in Delhi and immediately gets a `found` command, it fails because Delhi already exists there. The bridge's `estimate_good_settle_spots()` should avoid existing city tiles.
- **Balanced production is an ongoing tuning problem** — the priority system (garrison → workers → settlers) is a first pass. City size, happiness cap, strategic resource needs, and war pressure all affect the optimal build order. Expect to adjust ratios per-session.

## Sync to Windows

The `decide()` function writes to `~/.hermes/civ4_commands.json` (WSL path) then syncs to `/mnt/c/Users/gainq/.hermes/civ4_commands.json` (Windows path). The Civ4 Python callbacks read from the Windows path.