# AI Decision Callbacks — CvGameUtils.py

**The ONLY way to set research direction for an AI player in BtS Python API.**
All `setResearchTech`/`AI_setResearchTech`/`setResearchProgress` variants tested and confirmed: `AttributeError`.

## Architecture

The DLL calls Python callbacks during AI processing (`CvPlayerAI::AI_doTurn()`). These are delegated to `CvGameUtils.py`. By overriding them for Player 1 (the Hermes player), we control the DLL's decisions.

## ⚠️ CRITICAL TIMING: Callbacks Fire BEFORE onBeginPlayerTurn

The DLL calls `AI_chooseTech()` INSIDE its AI processing, which happens BEFORE `onBeginPlayerTurn`. This means:

- A module-level global like `_g_desired_tech` is STILL -1 when `AI_chooseTech` fires
- `execute_commands()` hasn't run yet — it runs in `onBeginPlayerTurn`, which comes AFTER the callback
- **Don't rely on globals. Read the commands file directly.**

## Correct Implementation — Read Commands File Directly

### Bridge Side (hermes_bridge.py)

```python
def get_desired_research():
    '''Called by CvGameUtils.AI_chooseTech. Reads commands file directly.
    This fires BEFORE onBeginPlayerTurn, so don't use globals.'''
    try:
        # Python 2.4 fallback — json not in stdlib
        try:
            import simplejson as json_mod
        except ImportError:
            import json as json_mod

        cmd_path = os.path.expanduser("~/.hermes/civ4_commands.json")
        # Windows-side path check (Civ4 runs on Windows)
        if not os.path.exists(cmd_path):
            cmd_path = "C:\\Users\\gainq\\.hermes\\civ4_commands.json"
        if os.path.exists(cmd_path):
            f = open(cmd_path, 'r')
            cmds = json_mod.loads(f.read())
            f.close()
            for cmd in cmds:
                if cmd.get('action') == 'research':
                    return cmd.get('tech', -1)
    except:
        pass
    return -1

def handle_ai_production(pCity):
    '''Called by CvGameUtils.AI_chooseProduction. Reads commands file,
    pushes build order. Returns True so DLL doesn't override.'''
    try:
        try:
            import simplejson as json_mod
        except ImportError:
            import json as json_mod

        cmd_path = os.path.expanduser("~/.hermes/civ4_commands.json")
        if not os.path.exists(cmd_path):
            cmd_path = "C:\\Users\\gainq\\.hermes\\civ4_commands.json"
        if os.path.exists(cmd_path):
            f = open(cmd_path, 'r')
            cmds = json_mod.loads(f.read())
            f.close()
            for cmd in cmds:
                if cmd.get('action') == 'build' and cmd.get('cityId') == pCity.getID():
                    if cmd.get('unit') == 'settler':
                        pCity.pushOrder(OrderTypes.ORDER_TRAIN, gc.getInfoTypeForString("UNIT_SETTLER"), -1, 0, False, False, False)
                    elif cmd.get('unit') == 'warrior':
                        pCity.pushOrder(OrderTypes.ORDER_TRAIN, gc.getInfoTypeForString("UNIT_WARRIOR"), -1, 0, False, False, False)
                    elif cmd.get('unit') == 'worker':
                        pCity.pushOrder(OrderTypes.ORDER_TRAIN, gc.getInfoTypeForString("UNIT_WORKER"), -1, 0, False, False, False)
                    return True
    except:
        pass
    return False
```

### CvGameUtils.py Overrides

```python
def AI_chooseTech(self, argsList):
    ePlayer = argsList[0]
    bFree = argsList[1]
    if ePlayer == 1 and not bFree:
        import hermes_bridge
        desired = hermes_bridge.get_desired_research()
        if desired >= 0:
            # ⚠️ CRITICAL: Must use team object, NOT pPlayer
            # CyPlayer has NO isHasTech() — crashes with AttributeError
            pTeam = gc.getTeam(gc.getPlayer(ePlayer).getTeam())
            if not pTeam.isHasTech(desired):
                import CvUtil
                CvUtil.pyPrint("Hermes AI_chooseTech returning tech %d" % desired)
                return desired
    return TechTypes.NO_TECH  # DLL picks its own choice

def AI_chooseProduction(self, argsList):
    pCity = argsList[0]
    if pCity.getOwner() == 1:
        import hermes_bridge
        # MUST return the result — True = handled, False = DLL overrides
        return hermes_bridge.handle_ai_production(pCity)
    return False
```

## Known Pitfalls

- **`import json` fails in Python 2.4** — always use `try: import simplejson as json_mod / except: import json as json_mod`
- **File path mismatch between WSL and Windows** — `os.path.expanduser("~/.hermes/")` on Windows gives `C:\Users\gainq\.hermes\`. The file at `/home/gainq/.hermes/` (WSL) is NOT at the Windows path. Always sync when writing commands: `cp ~/.hermes/civ4_commands.json /mnt/c/Users/gainq/.hermes/civ4_commands.json`
- **`CyPlayer.isHasTech()` does NOT exist** — use `gc.getTeam(pPlayer.getTeam()).isHasTech()` where `pPlayer.getTeam()` returns an int (team ID)
- **`AI_chooseProduction` MUST return `True`** to prevent DLL override. `return hermes_bridge.handle_ai_production(pCity)` not `hermes_bridge.handle_ai_production(pCity); return False`
- **Callbacks fire every turn** even during autoplay. If your commands file requests a completed tech, the callback logs "tech already known" and returns NO_TECH — DLL picks its own.
