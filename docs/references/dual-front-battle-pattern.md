# Dual-Front Battle Pattern — Proven June 2026

**Session date:** June 10, 2026
**Turn:** 379 → 381 (2 turns including one battle resolution)
**Mali (us) vs Netherlands (Dutch)**

## The Setup

- **Dutch attacked Awdaghost** (45, 24) — our northern frontier city
- **Our main army** was scattered: 36 macemen at Tadmekka (50, 21), 8 fresh at (46, 23), others at various cities
- **Maastricht** (Dutch city) was confirmed at (42, 28) — 7 tiles north of Tekedda (42, 21)
- **Dutch territory** was NORTH of us, across a narrow sea channel (from minimap: orange ~top-right, Mali green ~bottom-left)

## The Execution

### Coordinates verified by Nick:
- "Awdaghost is NE of Tekedda" → Y increases going NORTH in this game
- "Maastricht is exactly 7 blocks directly north of Tekedda" → Maastricht = (42, 28)
- Mountain blocking the direct path between Tekedda and Maastricht

### Offensive commands (to Maastricht 42,28):
```
8 fresh macemen from (46,23)    → vanguard
30 macemen from Tadmekka (50,21) → main body
6 Tekedda fighters               → macemen + trebuchet + cuirassier + crossbowman
1 cuirassier scout from (46,21)
Total: 45 attackers
```

### Defensive commands (to Awdaghost 45,24):
```
8 macemen from Timbuktu (57,31)
9 macemen from Niani (60,29)
8 macemen from Kumbi Saleh (53,29)
6 macemen from Djenne (57,35)
5 macemen from Wadan (51,36)
2 macemen from Gao (49,26)
2 macemen from Walata (56,26)
6 units from Tadmekka reserve (50,21)
Total: 46 reinforcements + 14 existing garrison = 60 defenders
```

### Results:
- **Maastricht CAPTURED** — added to our cities at pop 5
- **Awdaghost HELD** — lost ~10 defenders, 50 survivors
- **Army size unchanged** (148 units) — losses in both battles offset by enemy kills
- **Gold: 372 → 461** — captured treasury + normal income
- **City kept min garrisons** (2-4 units per interior city)

## Key Lessons

1. **setXY teleport works for both offense and defense in the same turn** — tested with 91 total commands in one commands file
2. **Interior cities are safe to strip** — leave 2-4 units for basic defense
3. **Macemen (type 34) are the ideal unit** — high strength, disposable in large numbers
4. **The human sees NO marching animation** — units vanish and reappear instantly
5. **Net result is +1 city with same army size** — the dual-front approach is the most efficient turn in the game
