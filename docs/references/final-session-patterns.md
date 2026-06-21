# Session Patterns (31 May 2026 — All Bugs Fixed)

## Bugs Discovered and Fixed (One Pass)

| # | Bug | Fix |
|---|-----|-----|
| 1 | `AI_chooseTech` crashed: `CyPlayer.isHasTech()` doesn't exist | Use `gc.getTeam().isHasTech()` |
| 2 | Research global (`_g_desired_tech`) not set before DLL asks | Callbacks read commands file directly, not globals |
| 3 | `UnitTypes.UNIT_SETTLER` enum constant doesn't exist | Use `gc.getInfoTypeForString("UNIT_SETTLER")` |
| 4 | `isProduction()` check blocks our build commands | Remove check, use `bNew=True` to force-push |
| 5 | Commands file not accessible from Windows Python | Bridge syncs to `/mnt/c/Users/gainq/.hermes/` after each TCP exchange |
| 6 | Bridge renamed `on_hermes_player_turn` to `on_turn` | CvEventManager calls `on_hermes_player_turn` — name must match |
| 7 | `gc.getInfoTypeForString()` rejects Python 2 unicode | Wrap in `str()`: `gc.getInfoTypeForString(str("UNIT_"+name.upper()))` |
| 8 | `MISSION_FOUND` replaces `MISSION_MOVE_TO` (bAppend=False) | Use `bAppend=True, bManual=True` so found queues after move |

## Final Confirmed Patterns

### Force-push city build (clears DLL's choice):
```python
dc.pushOrder(OrderTypes.ORDER_TRAIN, gc.getInfoTypeForString(str("UNIT_"+name.upper())), -1, 0, False, True, True)
```

### Found city after moving:
```python
u.getGroup().pushMission(MissionTypes.MISSION_FOUND, u.getX(), u.getY(), 0, True, True, MissionAITypes.NO_MISSIONAI, CyMap().plot(u.getX(), u.getY()), u)
```

### Shared command file reader (for both callbacks):
```python
def _read_cmds():
    paths = [os.path.join(...), os.path.join(os.path.expanduser("~"), ".hermes", "civ4_commands.json")]
    for p in paths:
        ap = os.path.abspath(p)
        if os.path.exists(ap):
            f = open(ap, 'r'); c = f.read(); f.close()
            if c.strip():
                return json_mod.loads(c)
    return []
```

## Cost Lesson

Nick spent ~$5 USD on API costs across ~10 restarts in one session. Every restart burns model calls. **Identify every issue before touching files. Fix in one pass.**
