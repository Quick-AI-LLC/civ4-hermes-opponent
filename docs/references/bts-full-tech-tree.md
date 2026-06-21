# BtS Full Tech Tree (XML-Confirmed, BtS 3.19 Steam)

**CRITICAL: IDs are 0-indexed from XML `<Type>` tag order, NOT alphabetic.**
Verify yourself:
```bash
grep -n '<Type>' "CIV4TechInfos.xml" | cat -n
# ID = cat -n column - 1
```

## XML Path (Nick's machine)

```
/mnt/c/Program Files (x86)/Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword/Beyond the Sword/Assets/XML/Technologies/CIV4TechInfos.xml
```

## How to Read This Table

- **Bold units** = most relevant for military planning
- KnownTechs from state tell you what your civ has
- `currentResearch` in state tells you what's being researched (ID value)

## Complete Tech ID Mapping

| ID | Tech | Key Unlocks |
|----|------|-------------|
| 0 | Mysticism | Monuments, Oracle |
| 1 | Meditation | Monasteries, Buddhism |
| 2 | Polytheism | Hinduism |
| 3 | Priesthood | Temples, Priest specialist |
| 4 | Monotheism | Judaism, Organized Religion civic |
| 5 | Monarchy | Hereditary Rule civic |
| 6 | Literature | Great Library, Epics |
| 7 | Code of Laws | Caste System, Courthouses |
| 8 | Drama | Theatres |
| 9 | Feudalism | Vassalage, Serfdom, **Longbowman** |
| 10 | Theology | Apostolic Palace, Theocracy |
| 11 | Music | Cathedrals, Military Academy? |
| 12 | Civil Service | Bureaucracy civic, Irrigation |
| 13 | Guilds | Grocer, **Knight** |
| 14 | Divine Right | Versailles |
| 15 | Nationalism | Draft, Nationhood civic |
| 16 | Military Tradition | **Cavalry**, West Point |
| 17 | Constitution | Representation civic |
| 18 | Liberalism | Free Speech civic, free tech |
| 19 | Democracy | Emancipation civic, Statue of Liberty |
| 20 | Corporation | Executive units, Corporations |
| 21 | Fascism | Police State civic, Mounted units? |
| 22 | Utopia | (future/custom tech) |
| 23 | Mass Media | Broadcast Towers, Hollywood |
| 24 | Ecology | Recycling Centers |
| 25 | Fishing | Work boats |
| 26 | The Wheel | Roads, Chariot |
| 27 | Agriculture | Farms |
| 28 | Pottery | Cottages, Granaries |
| 29 | Aesthetics | → Literature |
| 30 | Sailing | Work boats, coastal trade |
| 31 | Writing | Libraries |
| 32 | Mathematics | → Construction |
| 33 | Alphabet | Tech trading |
| 34 | Calendar | Plantations |
| 35 | Currency | Markets, Wealth civic |
| 36 | Philosophy | Pacifism civic |
| 37 | Paper | → Education |
| 38 | Banking | Banks |
| 39 | Education | Universities |
| 40 | Printing Press | → Economics |
| 41 | Economics | Free Market civic, Smith's Trading Co. |
| 42 | Astronomy | Caravels |
| 43 | Chemistry | **Grenadier** |
| 44 | Scientific Method | → Physics |
| 45 | Physics | (science) |
| 46 | Biology | (science) |
| 47 | Medicine | Hospitals |
| 48 | Electricity | Industrial Park, Hydro Plant |
| 49 | Combustion | **Tank?**, Destroyer |
| 50 | Fission | Manhattan Project |
| 51 | Flight | Airport, **Fighter** |
| 52 | Advanced Flight | Jet Fighter |
| 53 | Plastics | Modern armor |
| 54 | Composites | Stealth Bomber |
| 55 | Stealth | Stealth Destroyer |
| 56 | Genetics | (science) |
| 57 | Fiber Optics | (science) |
| 58 | Fusion | (future) |
| 59 | Hunting | Camps, Scouts |
| 60 | Mining | Mines |
| 61 | Archery | **Archer** |
| 62 | Masonry | Walls, Quarries |
| 63 | Animal Husbandry | Pastures |
| 64 | Bronze Working | Slavery civic, Chop forests |
| 65 | Horseback Riding | **Horse Archer** |
| 66 | Iron Working | **Swordsman**, reveal Iron |
| 67 | Metal Casting | Forges, Triremes |
| 68 | Compass | Harbors? |
| 69 | Construction | Colosseum, **Catapult**, Aqueduct |
| 70 | Machinery | **Maceman**, **Crossbowman** |
| 71 | Engineering | Pikeman, castles |
| 72 | Optics | Caravels, Great Lighthouse |
| **73** | **Gunpowder** | **Musketman** |
| **74** | **Replaceable Parts** | **Rifleman** (key infantry upgrade) |
| **75** | **Military Science** | **Grenadier**, West Point? |
| **76** | **Rifling** | (next stage) |
| **77** | **Steam Power** | Ironclad, Levee |
| **78** | **Steel** | **Infantry** (ID 50), **Artillery** (ID 80+) |
| 79 | Assembly Line | **Industrial Park** |
| **80** | **Railroad** | Railroads (faster unit movement) |
| **81** | **Artillery** | **Mobile Artillery** |
| **82** | **Industrialism** | **Tank**, **Marine** |
| 83 | Radio | Broadcast Towers |
| 84 | Refrigeration | Supermarkets |
| 85 | Superconductors | (late tech) |
| 86 | Computers | (late tech) |
| 87 | Laser | (military) |
| 88 | Rocketry | SAM Infantry, Mobile SAM |
| 89 | Satellites | (space) |
| 90 | Robotics | Mechanized Infantry |
| 91 | Future Tech | (repeatable) |

## Mali's Position (from session, Turn 424 / Year 2004)

**Known techs:** IDs 0–20, 25–44, 59–77 (missing 21–24=Fascism through Ecology, and 45–58=Scientific Method through Fusion)

**Current research:** ID **78 = Steel** → unlocks Infantry (ID 50) and Artillery

**Strategic tech gaps to fill for modern warfare:**
1. **Steel (78)** — Infantry + Artillery ← currently researching
2. Assembly Line (79) — Industrial Park
3. Railroad (80) — faster unit movement
4. Artillery (81) — Mobile Artillery
5. Industrialism (82) — Tank, Marine
6. Combustion (49) — needed for Tank

## Tech ID → Unit ID Quick Reference

| Tech ID | Tech | Unlocks Unit ID | Unit Name |
|---------|------|------------------|-----------|
| 73 | Gunpowder | 42 | Musketman |
| 74 | Replaceable Parts | 46 | **Rifleman** |
| 75 | Military Science | 48 | **Grenadier** |
| 78 | Steel | 50 | **Infantry** |
| 82 | Industrialism | 78, 53 | **Tank**, Marine |
| 88 | Rocketry | 51, 52 | SAM Infantry, Mobile SAM |
| 90 | Robotics | 56 | Mechanized Infantry |
