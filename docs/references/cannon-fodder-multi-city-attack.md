# Cannon Fodder + Multi-City Attack Pattern

*Proven in Turn 428 — German War*

## Concept

When your staged force contains a mix of obsolete units (macemen, longbows) and modern units (riflemen, grenadiers), use the obsolete ones as **cannon fodder** to absorb combat damage on the enemy tile before your real troops arrive. Simultaneously split the force to hit **multiple weakly-defended cities** in the same turn.

## Pattern Steps

### 1. Stage Everything at a Bridge City

Nick's preferred staging point: **Tadmekka (50,21)** — southern bridge city with access to both German and English lands.

Pull all combat units to the staging city via setXY teleport:
```json
{"action": "move", "unitId": N, "x": STAGING_X, "y": STAGING_Y}
```

### 2. Profile the Targets

Get intel from Nick on enemy city locations and garrison sizes:
- "Bonn has 2 guys" — very weak
- "Duisburg has 3 guys" — still very weak
- Compute coordinates from Nick's directional descriptions (Y-increases-north)

### 3. Split Force by Target

Divide the staged units between targets. Obsolete units go first to eat combat damage.

**Allocation heuristic:**
- Target with 2 defenders: ~20-25 units (load up macemen/longbows as first wave)
- Target with 3 defenders: ~25-30 units (similar ratio)
- Keep ~6 modern units at staging city for defense

### 4. Teleport Order Matters

Write commands so **fodder units appear first, modern units appear later** in the JSON array. On setXY teleport, combat triggers per unit arrival — fodder fights first, modern units finish.

```
Commands array order:
  1. All macemen → first to absorb
  2. All longbows → second wave
  3. Cavalry → fast strikers
  4. Grenadiers → main damage
  5. Riflemen → clean up
```

### 5. Hold the Territory

Nick's explicit instruction: **do NOT raze captured cities.** "Don't relinquish control of anything." Take and hold. Captured cities with existing infrastructure are more valuable than founding new ones at this stage of the game.

## Post-Capture Split Deployment

After the attack resolves, the survivors MUST be immediately split for defense:

1. Count survivors — macemen/longbows will mostly be dead (they did their job). Riflemen, grenadiers, infantry should still be alive.
2. Allocate in priority order: southern border first (8-12), staging city second (4-6), captured cities third (3-4 each)
3. Leave a forward reserve (about 14 units) at the nearest safe tile to the front
4. Verify the split by reading the next state — if Tekedda dropped below 8, adjust next turn

## When to Use This Pattern

- **You have obsolete units** (macemen, longbows) mixed with modern units (riflemen, grenadiers, infantry)
- **Multiple enemy cities are weakly defended** (< 5 units each)
- **Distance from staging city to all targets is similar** (setXY ignores distance)
- **You can spare 6+ defenders at the staging city and 12 at the southern border** (England may attack from the south)

## When NOT to Use

- **Single, well-defended target** — better to concentrate all forces
- **Enemy has counter-attack force nearby** — might lose both attack groups
- **Staging city itself is threatened** — defend first, attack later

## Proven Example (Turn 428)

| Input | Value |
|-------|-------|
| Staging | Tadmekka (50,21) — 54 units |
| Target 1 | Duisburg (58,19) — 3 defenders — 25 attackers |
| Target 2 | Bonn (58,23) — 2 defenders — 21 attackers |
| Garrison | Tadmekka — 6 units + Tekedda +2 |
| Force mix | 26 macemen (fodder) + 7 longbows (fodder) + 12 riflemen + 7 grenadiers + 2 cavalry |
