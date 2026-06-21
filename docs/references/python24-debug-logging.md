# Debug Logging for Civ4 Python 2.4 Bridge Imports

## Problem
When `hermes_bridge.py` fails to import in Civ4's Python 2.4, the error is completely silent:
- `_hermes_log()` uses file writes — but can't write if the module has a syntax error before the function definition
- The `CvEventManager.py` try/except catches the error but only sets a boolean flag
- `PythonErr.log` may be empty or missing entirely
- No Hermes debug files are created

## Root Cause Detection

### 1. Enable Python Logging in CivilizationIV.ini
```ini
LoggingEnabled = 1
```
This enables `PythonDbg.log` which captures `CvUtil.pyPrint()` output.

### 2. Add CvUtil.pyPrint() to the except block
In `CvEventManager.py`, replace the silent error handler:
```python
# BEFORE (silent failure — impossible to diagnose):
HAS_HERMES = False
try:
    import hermes_bridge
    HAS_HERMES = True
except Exception, e:
    HAS_HERMES = False
    # nothing logged!

# AFTER (prints the real error to PythonDbg.log):
HAS_HERMES = False
try:
    import hermes_bridge
    HAS_HERMES = True
    CvUtil.pyPrint("Hermes: Bridge loaded OK")
except Exception, e:
    CvUtil.pyPrint("Hermes: Bridge import FAILED - " + str(e))
    HAS_HERMES = False
```

### 3. Read the error from PythonDbg.log
```bash
grep "Hermes:" "/path/to/My Games/beyond the sword/Logs/PythonDbg.log"
```

This will output something like:
```
PY:Hermes: Bridge import FAILED - invalid syntax (hermes_bridge, line 30)
```

### Common Python 2.4 Syntax Errors Found This Way
- `with open(...) as f:` — Python 2.4 doesn't have `with` statements (added in 2.5)
- `except Exception, e:` is fine but `except (A, B):` needs parentheses — fine for single exceptions
- `exec cmd in globals()` inside a helper function — see python24-exec-pitfall.md
- `any()` / `all()` — not available in Python 2.4
- `str.format()` — not available; use `%` formatting
- Backticks `` ` `` or f-strings — neither exist in Python 2.4
