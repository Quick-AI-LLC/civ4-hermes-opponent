# Python 2.4 `with` Statement Pitfall

## The Bug

```python
# In hermes_bridge.py's _hermes_log():
with open(path, "a") as f:
    f.write(msg)
```

Python 2.4 does not support the `with` statement (introduced in Python 2.5). Civ4 BTS ships with Python 2.4, so any use of `with` causes:

```
PY:Hermes: Bridge import FAILED - invalid syntax (hermes_bridge, line 30)
```

## Root Cause

The `with` statement was added in PEP 343 for Python 2.5. In Python 2.4, it's a syntax error at parse time — the module never even starts executing. This means:
- No `_hermes_log()` calls fire (the function hasn't been defined yet when the syntax error is encountered at module scope)
- No `CvUtil.pyPrint()` output from the module itself
- The only way to see the error is a `CvUtil.pyPrint()` in the **CvEventManager.py** except block
- `PythonErr.log` stays empty (0 bytes) for syntax errors in imported modules

## The Fix

Replace all `with` statements with traditional open/close pattern:

```python
# ❌ Python 2.4 syntax error:
with open(path, "a") as f:
    f.write(msg + "\n")
    f.flush()

# ✅ Python 2.4 compatible:
f = open(path, "a")
f.write(msg + "\n")
f.flush()
f.close()
```

## Where to Scan

Check for `with` in these files before deploying to Civ4:
- `hermes_bridge.py` — the `_hermes_log()` function is the most common location
- `CvEventManager.py` — any new code added here
- `CvAppInterface.py` if modified

## Detection Pattern

The only symptom of this bug is **no connection attempts from Civ4** despite the mod loading. The game loads fine, no errors visible, but the bridge module never initializes.

## Recovery

1. Add `CvUtil.pyPrint()` to the except block in CvEventManager.py's import
2. Launch game, check `PythonDbg.log` for the error message
3. Fix the `with` statement, copy the fixed file to all 3 asset tiers (vanilla, Warlords, BtS)
