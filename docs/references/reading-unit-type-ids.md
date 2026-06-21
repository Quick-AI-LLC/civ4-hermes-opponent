# Reading Civ4 Unit/Type IDs from XML

Unit type IDs are defined by **file-position order** in `CIV4UnitInfos.xml`. The `<Type>` tags in file order determine the 0-indexed ID. Animals come first (Lion=0 through Wolf=3), then civilian units (Settler=4, Worker=5), then UUs, then military.

## ⚠️ CRITICAL: Never Guess Unit IDs

**Guessing cost 20+ turns and a lot of frustration.** The IDs are non-obvious — animals are 0-3, Warrior is at 24, Settler is at 4. Always grep the XML.

## How to Extract Correct IDs

```bash
# From the BtS assets:
grep -n "<Type>UNIT_" "CIV4UnitInfos.xml" | cat -n | head -60
```

This gives a 0-indexed numbered list. Line 1 = ID 0, line 2 = ID 1, etc.

## Verified BtS 3.19 Early IDs

| ID | Unit | Notes |
|----|------|-------|
| 0 | Lion (animal) | Not player-controllable |
| 1 | Bear (animal) | Not player-controllable |
| 2 | Panther (animal) | Not player-controllable |
| 3 | Wolf (animal) | Not player-controllable |
| **4** | **Settler** | `gc.getInfoTypeForString("UNIT_SETTLER")` = 4 |
| 5 | Worker | Builds improvements |
| 6 | Indian Fast Worker | India's UU (3 moves) |
| **7** | **Scout** | 2 movement points (movesLeft 120) |
| 8-23 | Explorer, Spy, Executives, Missionaries | Various support units |
| **24** | **Warrior** | 1 movement point (movesLeft 60), CANNOT found cities |
| 25+ | Melee, ranged, mounted units | Military units in play order |
| 57 | Archer | Ranged defense unit |

## Key Rule

**ALWAYS use `gc.getInfoTypeForString("UNIT_*")`** for type lookups in code. The `UnitTypes.UNIT_*` enum constants are NOT guaranteed to exist in BtS Python and frequently crash with `AttributeError`.

```python
# ✅ CORRECT — works always:
settler_type = gc.getInfoTypeForString("UNIT_SETTLER")  # Returns 4
warrior_type = gc.getInfoTypeForString("UNIT_WARRIOR")  # Returns 24

# ❌ WRONG — may crash:
settler_type = UnitTypes.UNIT_SETTLER  # AttributeError
```
