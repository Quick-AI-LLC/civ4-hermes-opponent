# BtS Unit Type ID Mapping (XML-Confirmed, BtS 3.19 Steam)

**CRITICAL: IDs are 0-indexed from XML `<Type>` tag order, NOT alphabetic.**
Verify yourself:
```bash
grep -n "<Type>UNIT_" "CIV4UnitInfos.xml" | cat -n
# ID = cat -n column - 1
```

## XML Paths (Nick's machine)

```
/mnt/c/Program Files (x86)/Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword/Beyond the Sword/Assets/XML/Units/CIV4UnitInfos.xml
```

## Verified Mapping (ID → UNIT_NAME)

| ID | Unit | Notes |
|----|------|-------|
| 0 | Lion | Animal, not controllable |
| 1 | Bear | Animal, not controllable |
| 2 | Panther | Animal, not controllable |
| 3 | Wolf | Animal, not controllable |
| **4** | **Settler** | ✅ `gc.getInfoTypeForString("UNIT_SETTLER")` = 4 |
| **5** | **Worker** | Build improvements |
| 6 | Indian Fast Worker | Gandhi UU, movesLeft=180 (3 moves) |
| **7** | **Scout** | movesLeft=120 (2 moves) |
| 8 | Explorer | movesLeft=120 (2 moves) |
| 9 | Spy | Espionage |
| 10–16 | Executive_1–7 | Corporation executives |
| 17 | Jewish Missionary | |
| 18 | Christian Missionary | |
| 19 | Islamic Missionary | |
| 20 | Hindu Missionary | |
| 21 | Buddhist Missionary | |
| 22 | Confucian Missionary | |
| 23 | Taoist Missionary | |
| **24** | **Warrior** | movesLeft=60, CANNOT found cities |
| 25 | Quechua | Inca UU |
| 26 | Swordsman | |
| 27 | Jaguar | Aztec UU |
| 28 | Gallic Warrior | Celtic UU |
| 29 | Praetorian | Roman UU |
| 30 | Axeman | |
| 31 | Phalanx | Greek UU |
| 32 | Vulture | Sumerian UU |
| 33 | Dog Soldier | Native American UU |
| **34** | **Maceman** | ✅ Confirmed from in-game production |
| 35 | Samurai | Japanese UU |
| 36 | Beserker | Viking UU |
| 37 | Spearman | |
| 38 | Impi | Zulu UU |
| 39 | Holkan | Mayan UU (replaces Spearman) |
| **40** | **Pikeman** | ✅ XML-confirmed (was previously mislabeled as Crossbowman) |
| 41 | Landsknecht | Holy Roman UU |
| 42 | Musketman | |
| 43 | Musketeer | French UU |
| 44 | Janissary | Ottoman UU |
| 45 | Oromo Warrior | Ethiopian UU |
| **46** | **Rifleman** | ✅ State-confirmed (30 units, 1 move, most common infantry) |
| 47 | Redcoat | English UU |
| **48** | **Grenadier** | ✅ State-confirmed (9 units, Tadmekka building them) |
| 49 | Anti-Tank Infantry | |
| | 50 | Infantry | ✅ CONFIRMED Turn 431 — Steel completed, Djenne producing "Infantry", 4 units in state |
| 51 | SAM Infantry | Anti-air, unlocked by Rocketry |
| 52 | Mobile SAM | Anti-air, unlocked by Laser? |
| 53 | Marine | Unlocked by Industrialism? |
| 54 | Navy SEAL | American UU |
| 55 | Paratrooper | |
| 56 | Mechanized Infantry | Late game, unlocked by Robotics? |
| 57 | Archer | Early ranged unit |
| 58 | Skirmisher | Mali UU (ours!) — replaces Archer |
| 59 | Bowman | Babylonian UU |
| 60 | Longbowman | ✅ XML-confirmed (NOT Catapult — previous file was wrong) |
| 61 | Crossbowman | |
| 62 | Cho-Ko-Nu | Chinese UU |
| 63 | Chariot | |
| 64 | War Chariot | Egyptian UU |
| 65 | Immortal | Persian UU |
| 66 | Horse Archer | |
| 67 | Numidian Cavalry | Carthaginian UU |
| 68 | Keshik | Mongolian UU |
| 69 | Knight | ✅ XML-confirmed (NOT Cuirassier) |
| 70 | Camel Archer | Arabian UU |
| 71 | Cataphract | Byzantine UU |
| 72 | Conquistador | Spanish UU |
| 73 | Cuirassier | |
| **74** | **Cavalry** | ✅ State-confirmed (6 units, movesLeft=120) |
| 75 | Cossack | Russian UU |
| 76 | War Elephant | |
| 77 | Ballista Elephant | Khmer UU |
| **78** | **Tank** | ✅ XML-confirmed |
| 79 | Panzer | German UU |
| 80+ | Artillery, modern ships, etc. | Verify XML for IDs 80+ |

## How to Identify Unknown Types from State Data

When the state file shows a type ID not in this table, confirm via **movesLeft** heuristic:

| movesLeft | Likely class | Examples |
|-----------|--------------|----------|
| 60 | Foot / siege (1 move) | Rifleman, Grenadier, Infantry, Catapult, Artillery, Longbowman |
| 120 | Mounted / fast (2 moves) | Cavalry, Cuirassier, Knight, Scout, Explorer |
| 180 | Special fast (3 moves) | Indian Fast Worker |

**Caveats:** Promotions (Morale, Mobility) add moves. movesLeft = 0 means unit already acted this turn.

## Production-Name Confirmation (from this session, Turn 424)

These city production names were read from the state:
| ID | Production Name | Confidence |
|----|-----------------|------------|
| 46 | "Rifleman" | ✅ Confirmed (most produced unit) |
| 48 | "Grenadier" | ✅ Confirmed (Tadmekka producing) |
| 60 | "Catapult" (Tekedda) | ⚠️ Name shown in state but ID 60 = Longbowman per XML. Either the mod reorders XML, or Tekedda was building type 60 Catapult via different game logic. Verify by checking `gc.getInfoTypeForString("UNIT_CATAPULT")`. |
| - | "Trebuchet" (Niani) | No type ID assigned — verify XML for siege unit entries. |
| - | "Market" (Timbuktu) | Building, not unit — ORDER_TRAIN not involved. |
| - | "Bank" (Awdaghost) | Building, not unit. |
| - | "Culture" (Deventer, Utrecht, Dorestad) | Culture build in captured cities. |

## How to Build Correctly

```python
# Use getInfoTypeForString for reliable ID lookup:
type_id = gc.getInfoTypeForString(str("UNIT_RIFLEMAN"))  # Returns 46
type_id = gc.getInfoTypeForString(str("UNIT_GRENADIER")) # Returns 48
type_id = gc.getInfoTypeForString(str("UNIT_INFANTRY"))  # Returns 50
type_id = gc.getInfoTypeForString(str("UNIT_CAVALRY"))   # Returns 74

# DO NOT assume UnitTypes enum constants exist:
# type_id = UnitTypes.UNIT_RIFLEMAN  # ❌ May crash with AttributeError
```

## Key Takeaway

- **ID 4 = Settler** — founds cities
- **ID 5 = Worker** — improvements
- **ID 24 = Warrior** — basic, CANNOT found
- **ID 34 = Maceman** — medieval line, obsolete by Turn 400+
- **ID 46 = Rifleman** — industrial line, our main infantry at Turn 424
- **ID 48 = Grenadier** — industrial line
- **ID 74 = Cavalry** — fast movers (2 moves)
- **ID 50 = Infantry** — modern line ✅ CONFIRMED (Steel done, 4 units rolling off production)
- **ID 78 = Tank** — modern armor (need Combustion, Industrialism)
