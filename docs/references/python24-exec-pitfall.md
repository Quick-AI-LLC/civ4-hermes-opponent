# Python 2.4 `exec` Pitfall

## The Bug

When `exec cmd in globals()` is placed in a **separate helper function** that is called from another function, Python 2.4 raises:

```
HermesOpponent: Failed to import hermes_bridge - unqualified exec is not allowed in
function 'execute_commands' it contains a nested function with free variables
(hermes_bridge, line 77)
```

## Root Cause

Python 2.4's compiler treats `exec` inside any function as creating a nested scope with free variables. When the exec is in a helper function (`_exec_command`) that is called from the main function (`execute_commands`), the compiler sees the helper as a "nested function" with variables from the enclosing scope, and the `exec` statement is flagged as "unqualified" (not allowed in this context).

## The Fix

**Never separate exec into a helper function.** Inline it directly in the function that processes commands:

```python
# ❌ WRONG — causes the error:
def _exec_command(cmd):
    exec cmd in globals()

def execute_commands(commands):
    ...
    _exec_command(cmd)  # ← Python 2.4 errors here

# ✅ CORRECT — inline exec:
def execute_commands(commands):
    ...
    exec cmd in globals()  # ← works fine
```

## How to Test

The error only appears at module import time inside Civ4's Python 2.4 engine. It won't show up testing with Python 3 or modern Python 2.7.

To verify the fix:
1. Enable `LoggingEnabled = 1` in `CivilizationIV.ini`
2. Launch Civ4 with the mod
3. Check `PythonDbg.log` — look for "HermesOpponent: Failed to import hermes_bridge" or "Hermes Bridge loaded and ACTIVE."

## Error in PythonDbg.log

The exact error from Civ4's `PythonDbg.log` (with `LoggingEnabled=1`):
```
HermesOpponent: Failed to import hermes_bridge - unqualified exec is not allowed
in function 'execute_commands' it contains a nested function with free variables
(hermes_bridge, line 77)
```

If the import succeeds, you'll see:
```
load_module hermes_bridge
```
With occasional Hermes pyPrint messages mixed into `PythonDbg.log`.
