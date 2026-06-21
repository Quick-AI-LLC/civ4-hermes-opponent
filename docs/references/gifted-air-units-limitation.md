# Gifted Air Units — Bridge Limitation

**Finding (June 2025 session):** When the human player gifts an air unit (bomber, fighter) to the Hermes-controlled civ, the gifted unit does NOT appear in `civ4_state.json`. The unit count (`numUnits`) stays unchanged, and no new unit entry appears at the airbase city's coordinates.

## Session Evidence

- Nick gifted a Bomber to Mali, based at Gao (49,26)
- Turn advanced from 369→370 (confirmed by city production changing and `_received_at` timestamp updating)
- State showed exactly the same units before and after: 168 total, same type distribution [5, 7, 34, 40, 60, 69, 82, 111]
- No new unit at Gao — still had the same 3 catapults
- Unit type 111 (at Awdaghost) existed in both turns and didn't change

## Likely Causes

1. **State collection skips air units:** `pPlayer.firstUnit(False)/nextUnit` (or the Python-side state builder) may filter out or fail to serialize airborne units. Air units in Civ4 have different properties (unitAirBase, airRange, etc.) that may cause serialization to skip them.

2. **Gift delivery timing:** The gift may be pending when `onBeginPlayerTurn` fires — the human gifted it on their turn, but the unit transfer doesn't take effect until the human's turn processes fully. The state is captured at turn start.

3. **Air units have different state schema:** Air units have properties (airbase city, missions remaining) that don't fit the simple `{x, y, type, movesLeft, damage}` schema used for ground units. The bridge's state collector might intentionally or accidentally drop them.

## Implications

- ❌ **Cannot command gifted air units through the bridge** — no unit ID = no way to send move/rebase/attack commands
- ❌ **Cannot send air recon** — even if the player wants the bomber to scout, the bridge provides no mechanism
- ❌ **Cannot re-base for safety** — the bomber stays wherever the human parked it, at risk if that city falls
- ✅ **City defense matters more** — since you can't move the bomber, you must defend the airbase city with ground troops

## Workarounds

1. **Stack defenders on the airbase city** — this is the only way to protect it. Fortify existing units in the city the bomber is based in.
2. **Ask the human to move/rebase it** — the human can control their gift during their turn
3. **Check the game's Python log** — `PythonErr.log` or `HermesDebug.log` in `My Games/Beyond the Sword/Logs/` may reveal whether the bridge state collection is silently crashing on air units
4. **Future fix:** Add explicit air unit iteration to `hermes_bridge.py`'s state builder — use `pPlayer.firstUnit(True)` or check `pUnit.getDomainType()` for `DOMAIN_AIR`

## Related

- `bridge-connection-checklist.md` for verifying bridge health
