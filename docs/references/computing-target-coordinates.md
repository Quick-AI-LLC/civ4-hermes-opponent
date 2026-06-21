# Computing Target Coordinates from Relative Directions

The most common way Nick gives you an attack target: **relative offset from a known city**. This pattern appears every session. The math is simple but critical — 1-pixel error sends your entire army to the wrong tile.

## The Pattern

Nick says: *"Utrecht is 3 west and 2 south of Maastricht"*

Your job: compute the target coordinates from the known city + offset.

## Known City Coordinates

| City | Coordinates | Notes |
|------|:-----------:|-------|
| Niani | (57,31) | Capital |
| Gao | (49,26) | Central |
| Tekedda | (42,21) | Southernmost |
| Tadmekka | (50,21) | South edge |
| Awdaghost | (45,24) | NW frontier |
| Wadan | (51,36) | Northern |
| Maastricht | (42,28) | Captured from Dutch |
| Timbuktu | (60,29) | East |
| Djenne | (57,35) | North |
| Kumbi Saleh | (53,29) | Interior |

## Direction → Coordinate Delta

**Verified for this game: Y increases NORTHWARD.**

| Direction | X change | Y change |
|-----------|:--------:|:--------:|
| North | 0 | +1 |
| South | 0 | -1 |
| East | +1 | 0 |
| West | -1 | 0 |
| Northeast | +1 | +1 |
| Northwest | -1 | +1 |
| Southeast | +1 | -1 |
| Southwest | -1 | -1 |

## Computation Examples

### Example 1: "3 west and 2 south of Maastricht"
- Maastricht = (42, 28)
- West = X - 3, South = Y - 2
- Target = (42 - 3, 28 - 2) = **(39, 26) ← Utrecht** ✅

### Example 2: "9 W 1 N of Wadan"
- Wadan = (51, 36)
- West = X - 9, North = Y + 1
- Target = (51 - 9, 36 + 1) = **(42, 37)** ✅

## Quick Verification

**Before writing commands,** run a sanity check in your head:
1. Is the target roughly in the expected direction from the reference city?
2. Is it on a plausible tile (not ocean, not overlapping a known friendly city)?
3. If the offset is large (9 tiles), is the target still within the map bounds?

If the target seems wrong (e.g., ocean tile, inside your own territory, or the offset doesn't match Nick's visual description), **ask Nick to confirm the raw coordinates** before committing 50+ teleport commands.

## Pitfalls

- **Orientation must be confirmed first.** If Y increases SOUTH (opposite of this game), swap +Y and -Y for north/south. See `germany-campaign-june2026.md` (Mali playthrough reference) for an example session context.
- **Nick says cardinal directions** (N/S/E/W), not compass degrees. Always use the direction→delta table above.
- **Offsets are cumulative.** "3 west and 2 south" = (X-3, Y-2), not two separate moves.
- **"Of [city name]" means the direction FROM that city.** The target city is that many tiles in that direction from the reference.
