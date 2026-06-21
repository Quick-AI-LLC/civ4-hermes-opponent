# Mali Campaign Playthrough — June 2026 (Turn 379→470)

This is the record of the FIRST playthrough with the Hermes civ bridge. All strategic lessons, tactical patterns, and pitfalls discovered here are codified in the main SKILL.md. This file preserves the raw data for reference.

## Map Context

**Coordinate System:** Y increases NORTHWARD in this game. Verified by user: Awdaghost (45,24) is NE of Tekedda (42,21). X increases eastward (standard).

### Our Cities (Pre-German War)

| City | Coords | Notes |
|------|--------|-------|
| Timbuktu | (57,31) | Capital, central-east |
| Djenne | (57,35) | Northern interior |
| Kumbi Saleh | (53,29) | Central |
| Gao | (49,26) | Mid-west hub / airbase |
| Niani | (60,29) | Easternmost |
| Awdaghost | (45,24) | NW frontier |
| Tadmekka | (50,21) | Southern staging hub |
| Tekedda | (42,21) | Southernmost (south edge) |
| Wadan | (51,36) | Northernmost |
| Awlil | (47,31) | Central interior |
| Walata | (56,26) | East of Gao |

### Conquered Cities (From Dutch)
Maastricht (42,28), Utrecht (39,26), Deventer (42,37), Dorestad (38,33)

### Conquered Cities (From Germany)
Bonn (58,23), Duisburg (58,19), Bremen (53,19) — fluctuated

### Enemy Positions
- **Netherlands (orange):** NORTH — across narrow sea channel. Defeated early.
- **Germany (Frederick):** SE of Tadmekka. Main enemy in mid-game.
- **England (Elizabeth):** Southern border. Bigger existential threat. Had nukes + SDI.

---

## Phase 1: Dutch War (Early Game)

Captured Maastricht, Utrecht, Deventer, Dorestad from the Dutch. First use of setXY teleport in combat. Proven principles:
- setXY onto enemy unit stacks triggers combat (bCheckCollateral=True)
- 39 simultaneous unit teleports confirmed working
- Defensive consolidation across the empire in one turn

**Key Pattern Discovered:** Dual-front battle. Attacked Maastricht while simultaneously reinforcing Awdaghost from the Dutch counterattack — 91 commands in one turn, both fronts won.

---

## Phase 2: Germany Campaign (Turn 428→441)

**Setting:** Turn 424, Year 2004. Peace. Germany and England both neutral.
**Duration:** 13 turns to peace deal.
**Net Result:** +2 cities (Bonn and Duisburg retained), Cologne razed, Germany forced Confucianism.

### Timeline

**Turn 428 — War Declaration:** Germany declared war. Target: Bremen at (53,19). 46 units staged at Tadmekka.

**Turn 429 — Split Assault:** Recon confirmed Bonn=2 defenders, Duisburg=3. Split 46-unit stack: 25 to Duisburg, 21 to Bonn.

**Turn 431 — Three Cities Captured:** Bremen, Bonn, Duisburg all taken. 15→18 cities. German counterattack held by Tadmekka garrison (6 units).

**Turn 432→435 — Counterattack:** German 25-stack appeared at Tadmekka. City flipped 3 times in 4 turns due to over-concentration + stripping garrisons. Lost Bonn and Bremen temporarily to SAM Infantry. **Lesson:** Staging city needs 8-12 defenders kept behind.

**Turn 436→438 — Nuclear Campaign:** Nick's ICBMs cratered Cologne. SDI blocked ICBMs but not tactical nukes. Cologne eventually razed. Germany's production gutted.

**Turn 441 — Peace:** Frederick forced to adopt Confucianism. 15→17 cities at peace. England remains the greater threat.

### Key Stats

| Stat | Start (428) | End (441) |
|------|-------------|-----------|
| Cities | 15 | 17 |
| Military | 98 | 61 |
| Gold | 206 | 201 |
| Tech | Steel (78) | Assembly Line (79) — drifted to Utopia (22)! |

### Composition

| Unit | Start | End | Note |
|------|-------|-----|------|
| Maceman (34) | 29 | ~25 | Never modernized — research drift |
| Rifleman (46) | 30 | ~4 | Heavy casualties |
| Infantry (50) | 0 | ~8 | New from Steel tech |
| Cavalry (74) | 6 | ~3 | Light casualties |

---

## Phase 3: Game Freeze & Reset (Turn 470)

The game froze. Last save was pre-war. All progress lost. Nick called it — end of first playthrough.

---

## Key Discoveries (All Moved to Main Skill)

1. **Research Drift** — AI_chooseTech consumes command once, DLL backfills to junk (Utopia=22, Biology=46, Mass Media=23). Check + override every 3-5 turns.
2. **Staging City Vulnerability** — 40+ units at a single city = counterattack magnet. Split staging, leave garrison floor.
3. **NEVER Intermediate Stage** — setXY teleport ignores distance. Send directly to target, not to border city first.
4. **Southern Border Priority** — Weight defense toward the civ that matters most, even when fighting elsewhere.
5. **Nuke Follow-Up** — When human ICBMs a city, send strike team same turn (0 defenders).
6. **Teleport Invisibility** — Human can't see setXY moves. Report where you sent units.
7. **Antiquated Unit Spam** — Macemen at 8 strength vs SAM Infantry at 18 = cannon fodder at best, gold drain at worst. Don't overproduce obsolete units.
8. **Command File Bug** — execute_code BLOCKED error causes partial writes. Use terminal heredoc.
9. **Gifted Air Units** — Bombers gifted by human don't appear in state. Can't command them.
10. **Post-Peace Audit** — Always check currentResearch after peace. War consumed command slots.
