# Config Import Bug

## Symptom

`hermes_config.py` fails to import in Civ4's Python 2.4 during mod loading:

```
WARNING: Could not load hermes_config.py - using defaults. Error: No module named hermes_config
```

When this happens, `hermes_bridge.py` falls back to `HERMES_HOST = '127.0.0.1'` which makes the mod try to connect to localhost on Windows instead of the WSL bridge IP.

## Root Cause

Civ4's mod loading system adds `Assets/Python/` to the Python path, but the order and timing of module imports can cause `import hermes_config` to fail sporadically (race condition in mod initialization).

## Fix

Hardcode the config values directly in `hermes_bridge.py` instead of importing from `hermes_config.py`:

```python
# BEFORE (unreliable):
# try:
#     import hermes_config
#     HERMES_HOST = hermes_config.HERMES_HOST
# except Exception, e:
#     HERMES_HOST = '127.0.0.1'  # WRONG — unreachable from Windows

# AFTER (always works):
HERMES_HOST = "172.29.235.138"  # WSL IP from `hostname -I`
HERMES_PORT = 3334
HERMES_PLAYER_ID = 1
```

Keep `hermes_config.py` as reference documentation but treat `hermes_bridge.py` as the source of truth for connection settings.

## Verification

After applying the fix, check that HermesBridge.log shows the correct IP:

```
Hermes Bridge loaded. Will try to send game state to 172.29.235.138:3334 (player 1)
```

If it says `127.0.0.1:3334`, the config import is still failing.
