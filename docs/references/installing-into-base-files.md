# Installing Bridge Files Into Base Civ4 Tiers

## When to Use

When Civ4 loads the HermesOpponent mod (confirmed in `init.log` as "Mod Loaded: Mods\HermesOpponent\") but the bridge Python code NEVER executes (no HermesDebug.log, no "load_module hermes_bridge" in PythonDbg.log, bridge server receives no connections). This means the mod's Python files aren't overlaying the base game's files.

## The Root Cause

Civ4 BTS has a **three-tier Python asset hierarchy**. Python modules are loaded from ALL tiers, and the FIRST match wins:

| Priority | Tier | Path |
|----------|------|------|
| 1st | Vanilla | `Assets/Python/` |
| 2nd | Warlords | `Warlords/Assets/Python/` |
| 3rd | BtS | `Beyond the Sword/Assets/Python/` |

**Key finding:** `CvEventManager.py` is loaded from the **Vanilla** tier (`Assets/Python/`), not from BtS. Patching only the BtS copy does nothing.

## Pre-Step: Enable Logging

Before doing anything, enable Python error logging:

1. Edit `CivilizationIV.ini` (in `Documents/My Games/beyond the sword/` — check OneDrive path too):
   ```
   LoggingEnabled = 1
   ```

2. After launching Civ4, check `Logs/PythonDbg.log` for "load_module hermes_bridge" and any error messages.
   - Empty `PythonErr.log` = no syntax errors
   - "HermesOpponent: Failed to import hermes_bridge" with error text = import failed

## Step-by-Step: Install Into All 3 Tiers

### 1. Back up original files

```bash
# Vanilla
cp "Assets/Python/CvEventManager.py" "Assets/Python/CvEventManager.py.bak"
# Warlords
cp "Warlords/Assets/Python/CvEventManager.py" "Warlords/Assets/Python/CvEventManager.py.bak"
# BtS
cp "Beyond the Sword/Assets/Python/CvEventManager.py" "Beyond the Sword/Assets/Python/CvEventManager.py.bak"
```

### 2. Copy bridge support files to all 3 tiers

```bash
SRC="Mods/HermesOpponent/Assets/Python"
for DEST in "Assets/Python" "Warlords/Assets/Python" "Beyond the Sword/Assets/Python"; do
    cp "$SRC/hermes_bridge.py" "$DEST/"
    cp "$SRC/simplejson.py" "$DEST/"
done
```

**Note:** If hermes_bridge.py has been modified (e.g., hardcoded config, exec fix), copy from the BtS copy since it has the fixes:
```bash
SRC="Beyond the Sword/Assets/Python"
for DEST in "Assets/Python" "Warlords/Assets/Python"; do
    cp "$SRC/hermes_bridge.py" "$DEST/"
    cp "$SRC/simplejson.py" "$DEST/"
done
```

### 3. Patch all 3 CvEventManager.py files

In each tier's `CvEventManager.py`:

**a) Add import after `import CvTechChooser`:**
```python
# HermesOpponent bridge support
try:
    import hermes_bridge
    HAS_HERMES = True
except Exception, e:
    HAS_HERMES = False
```

**b) Add hook in `onBeginPlayerTurn`** (right after `iGameTurn, iPlayer = argsList`):
```python
# HermesOpponent integration - send state when it's the Hermes player's turn
if HAS_HERMES:
    try:
        hermes_bridge.on_hermes_player_turn(iPlayer)
    except Exception, e:
        print("Hermes Bridge call error: " + str(e))
```

### 4. Hardcode config in hermes_bridge.py

Replace the import-based config block:
```python
# INSTEAD OF:
# try:
#     import hermes_config
#     HERMES_HOST = hermes_config.HERMES_HOST
# except Exception, e:
#     HERMES_HOST = '127.0.0.1'

# USE:
HERMES_HOST = "172.29.235.138"  # from `hostname -I` in WSL
HERMES_PORT = 3334
HERMES_PLAYER_ID = 1
```

### 5. Fix Python 2.4 `exec` issue

If `hermes_bridge.py` has a separate `_exec_command` helper function, merge the exec into `execute_commands` directly (see `references/python24-exec-pitfall.md`).

### 6. Disable mod loading

In `CivilizationIV.ini`:
```
Mod = 0
```

## Verifying

1. Launch Civ4 normally (no mod selection)
2. Start a new game with Hermes as player 1
3. On turn 0 (initialization), the bridge should receive a connection with turn=0 state
4. Check `PythonDbg.log` — should show "load_module hermes_bridge" and "load_module CvEventManager"
5. Check HermesDebug.log next to the .py files — should show import messages
6. The WSL bridge should log the incoming connection and return commands

## File Locations (Nick's Steam Install)

```
C:\Program Files (x86)\Steam\steamapps\common\
  Sid Meier's Civilization IV Beyond the Sword\
    Assets\Python\                    ← Vanilla tier
    Warlords\Assets\Python\           ← Warlords tier
    Beyond the Sword\Assets\Python\   ← BtS tier
    Beyond the Sword\Mods\HermesOpponent\Assets\Python\  ← Mod files
```
