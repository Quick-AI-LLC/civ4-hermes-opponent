# Human Air Support Coordination — Bombers & ICBMs

*Proven in Turn 428–434 — German War (June 2026)*

## The Turn Cycle

Nick provides air support (bombers, stealth bombers, ICBMs) that fires during **his turn**, before my ground commands execute:

1. **Recon phase:** Nick flies a stealth bomber over the target area, reports what he sees (city garrisons, field army positions)
2. **Command phase:** I write setXY teleport commands targeting the coordinates he provided
3. **Bombing phase:** Nick ends his turn — his bombers/ICBMs hit the targets
4. **Ground phase:** My setXY teleport commands fire at end-of-turn, troops land on bombed tiles
5. **Result:** Bombers cratered the garrison, my troops walk into a nearly-empty city

## Bomber Recon vs State File Timing

**Critical distinction:** Nick's bomber sees **mid-turn** troop movements. The bridge state file shows **end-of-turn** results. These can disagree because:

- My teleport commands fire between his recon and the state capture
- Enemy units mid-march toward my cities are visible to his bomber but may not have resolved combat by state-capture time
- When Nick says "I see 8 at Tadmekka" and the state shows 6 of my units there, the difference is usually enemy mid-march

**Rule: Trust the state file for actual results, not mid-turn bomber intel.**

## ICBM/Nuke Protocol

| Nuke type | Effect | Counter |
|-----------|--------|---------|
| ICBM | Massive damage, can reduce city from a dozen guard to zero | SDI blocks ICBMs |
| Tactical nuke | Less range but cannot be blocked by SDI | No SDI defense |

**After a nuke hits a target city:** Sending even a small force (15 units) is enough to capture it. Nick will call out the garrison count post-nuke (e.g., "From a dozen guard to zero").

**Cannot nuke inside own borders:** Nick cannot nuke cities inside his own cultural borders. Those must be taken by ground forces alone.

## Proven Example (Turn 433, German War)

1. Nick had 3 bombers stationed at Gao (49,26)
2. German 25-stack was at Tadmekka (50,21) — their last stand
3. I wrote 36 move commands targeting Tadmekka
4. Nick ended his turn — bombers hit the German stack
5. My 36 troops landed on softened Germans
6. Result: Tadmekka retaken, German army destroyed (clean sweep of ~25 units)
