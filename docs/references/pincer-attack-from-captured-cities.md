# Pincer Attack from Captured Enemy Cities — Proven June 2026

**Session:** June 10, 2026 (turn 382+)
**Target:** Dutch border town (47, 31) — last city separating Mali from Dutch core territory
**Setup:** We held Maastricht (42, 28) and 's-Hertogenbosch (43, 32) after a successful dual-front turn

## The Pattern

After capturing enemy cities, you control forward staging points that are CLOSER to the next target than any of your original cities. Use these captured cities as launch points for the next attack wave.

### Sequence

**Turn 1:** Capture Maastricht (42,28) and reinforce Awdaghost (45,24) — dual front
**Turn 2:** Capture 's-Hertogenbosch (43,32) — the uranium town
**Turn 3:** Launch pincer from BOTH captured cities onto the next Dutch city (47,31):

```
From Maastricht (42,28) → (47,31): 4 tiles east, 3 tiles north
From 's-Hertogenbosch (43,32) → (47,31): 4 tiles east, 1 tile south
```

**Command structure:**
```json
[
  // From Maastricht area:
  {"action": "move", "unitId": N, "x": 47, "y": 31},
  {"action": "move", "unitId": N, "x": 47, "y": 31},
  // From 's-Hertogenbosch area:
  {"action": "move", "unitId": N, "x": 47, "y": 31},
  {"action": "move", "unitId": N, "x": 47, "y": 31},
  // From anywhere else (Gao, Awdaghost):
  {"action": "move", "unitId": N, "x": 47, "y": 31},
]
```

### Why It Works

1. **setXY ignores distance** — units from Maastricht and 's-Hertogenbosch arrive simultaneously regardless of path
2. **Captured cities provide staging** — no need to march from interior cities, use the captured ones as launch points
3. **Overwhelming force** — 40+ macemen from two directions guarantees the city falls
4. **Borders connect** — once the border town falls, your captured cities connect to your core territory

### Caveats

- **setXY onto a city tile may not capture instantly** — combat resolves on the next DLL tick. The city may show in your list 1-2 turns after teleporting
- **Garrison the captured cities** — leave at least 5-10 macemen in each captured city. The Dutch WILL counter-attack
- **The human can't see the teleport** — units vanish from one city and appear at the target. Tell Nick where they went
- **Don't strip interior cities completely** — leave 2-4 combat units per interior city
