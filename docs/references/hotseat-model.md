# Hotseat Model — ABANDONED (Postmortem)

**⚠️ Five approaches were tried. None succeeded.** The password dialog is rendered in-game by Civ4's DLL — no Windows automation method could type into it. Below is the full history and a postmortem with untested alternatives for anyone who revisits. See also `docs/gate_watcher_postmortem.md` for the full external reference.

## Architecture

The hotseat variant uses the same WSL bridge (`bridge/civ4_bridge.py`, port 3334, pure relay) as the standard model. Only the game-side Python client differs.

Files:
- `mod/hotseat/game-files/hermes_bridge.py` — Windows-side game client (Python 2.4) with `stage_orders()`, `notify_handoff_pending()`, `tick_hotseat()`
- `mod/hotseat/patches/CvEventManager.py.diff` — hooks (`onUpdate` + `onEndPlayerTurn`)
- `bridge/hermes_gate_watcher.ps1` — PowerShell script that auto-types P2's password
- `bridge/hermes_gate_probe.ps1` — diagnostic tool for calibrating click positions
- All deployed to `BtS/Assets/Python/` and `Warlords/Assets/Python/` (base file replacement, NOT mods)

**⚠️ The hotseat pass-keyboard popup is FUNDAMENTAL — it's a modal DLL dialog that blocks Python events and cannot be bypassed from Python alone.**

## Approach History

### Attempt 1: `onUpdate` + `tick_hotseat()` polling (FAILED)

Composer v2.5 proposed polling via `onUpdate` every frame to detect `getActivePlayer() == PID` + `isTurnActive()`. **Did not work** — the hotseat pass-keyboard popup is a modal DLL dialog that blocks the render loop. `onUpdate` never fires while the popup is showing.

**Symptoms:** Bridge loaded OK, but `tick_hotseat` never detected P2's active turn. User was presented with the popup, clicked OK, then had full manual P2 control.

### Attempt 2: `onEndPlayerTurn(P0)` without active-player-switching (FAILED)

Hooked `onEndPlayerTurn` for P0 to process P2's turn and call `sendTurnComplete()`. Problem: `sendTurnComplete()` ends CURRENT player (P0), not P2 — P0's turn is already ending. Popup still appears, P2 gets full manual control.

### Attempt 3: `onEndPlayerTurn(P0)` + active-player-switching (FAILED)

Switched active player to P1 before `sendTurnComplete()`:
```python
if g.getActivePlayer() != PID:
    g.setActivePlayer(PID)
CyMessageControl().sendTurnComplete()
```

**Why this failed:** The hotseat popup is queued by the DLL AFTER `onEndPlayerTurn` returns. The popup then starts P1's turn FRESH — the `sendTurnComplete` was for a turn that hadn't started yet. Popup dismissal resets the turn-complete flag.

### Attempt 5: VK codes + keyboard-first (June 6, 2026 — ALSO FAILED)

**Problem discovered after previous attempt:** The Unicode-based SendInput (`KEYEVENTF_UNICODE`) does not work with Civ4 (2007). The game engine never processes Unicode keyboard events despite SendInput reporting success. The password field never received typed characters — the watcher logged 14 attempts with "SendInput password (6 chars)" but Civ4 ignored every one.

**Fix attempted (STILL DID NOT WORK):** Replace `KEYEVENTF_UNICODE` with VK codes (virtual key codes). For lowercase ASCII letters, send the VK without any modifier. Also switched to a **keyboard-first approach**: send Tab x3 to navigate focus to the password field, type via VK codes, then press Enter. The click+type+Enter sequence serves as a fallback.

**Result:** 3 attempts logged — `"typing password via VK (6 chars)"` ran successfully but password field remained blank. VK codes also do not reach Civ4's in-game text field.

**Likely root cause:** Civ4 runs in fullscreen exclusive DirectInput mode. `SendInput` keystrokes (both Unicode and VK) may be intercepted or ignored by DirectInput, which reads keyboard state directly from the hardware driver, bypassing the Windows message queue. `SendInput` injects into the Windows input queue, not DirectInput's device state.

**Not tested (potential fixes if revisiting):**
1. Hardware scan codes via `KEYEVENTF_SCANCODE` — injects at the keyboard device level which DirectInput also reads
2. `PostMessage WM_CHAR` with lParam containing scan code bits 16-23 — bypasses SendInput entirely, goes straight to window queue
3. Clipboard paste (SetClipboard + Ctrl+V VK scan codes)
4. Setting `FullScreen=0` in CivilizationIV.ini to run in windowed mode — standard Win32 input routing then applies
5. Compiling a C# helper EXE to avoid PowerShell AV heuristics

**Remaining uncertainty:** If the password field is not reachable via Tab (in-game popup may not support keyboard navigation), the click fallback uses estimated coordinates: (50%width, 46%height) for password field and (50%width, 58%height) for OK button.

**The insight:** The hotseat pass-keyboard popup is unavoidable from Python. So lean into it — enable passwords for P2, then use an external process to auto-type the password.

**⚠️ Anti-virus heuristic trigger:** The watcher script (`SendInput` + `Add-Type` C# P/Invoke + `-WindowStyle Hidden`) triggers Avast/AVG's **IDP.generic** heuristic detection. This is a false positive — the script legitimately auto-types the Civ4 password. To suppress: add an AV exclusion for `C:\Users\gainq\civ4-hermes-opponent\bridge\` or compile the C# P/Invoke into a standalone EXE. Without an exclusion, the watcher may be silently quarantined between sessions.

**⚠️ Why Win32 dialog automation doesn't work:** The hotseat password popup is rendered INSIDE the game viewport by the DLL. It is NOT a Win32 dialog window (no `#32770` class, no `Edit` child HWND). `EnumChildWindows` on the Civ4 main window finds zero dialogs. `WM_SETTEXT`, `WM_CHAR`, `SendKeys` — all fail because there's no Win32 control to target. The popup exists only as a 3D-rendered texture in the game's client area.

**ABANDONED: No approach successfully entered the password.** Over 3 sessions, 4 distinct input methods were tried — none reached the Civ4 text field. See the Postmortem section below.

### Attempt 5: VK codes + keyboard-first (June 6, 2026 — ALSO FAILED)

The game renders the password textbox and OK button at fixed positions within the client area. Send standard Windows input events (not Civ4-specific) to those positions:

1. **Focus the Civ4 window** (SetForegroundWindow + AttachThreadInput)
2. **Keyboard-first:** Send Tab x3 to navigate focus to password field
3. **Type password** via VK codes (key-down/key-up pairs) — NOT KEYEVENTF_UNICODE which Civ4 ignores
4. **Press Enter** to submit
5. **Click fallback:** Click password field at ~50%w,46%h, VK-type + Enter again, then click OK at ~50%w,58%h
6. **Bridge confirms success** — tick_hotseat calls _mark_gate_opened which writes gate_opened to the gate file; watcher reads this and stops submitting

#### Two-Phase Processing

**Phase 1: `onEndPlayerTurn(P0)` -> `stage_orders()`**

Called from CvEventManager when P0 ends their turn. Pushes research + build orders early (safe anytime, doesn't need P1 active):

```python
def stage_orders():
    cmds = _read_cmds()
    early = [c for c in cmds if c.get('action') in ('research','build')]
    exec_cmds(early)  # pushResearch, pushOrder
    notify_handoff_pending()  # write turn_gate.json
```

Also writes `turn_gate.json` signal file for the watcher and starts the watcher (if not already running) via `os.system()`.

**Phase 2: `tick_hotseat()` via `onUpdate` (after gate dismissal)**

After the password dialog is dismissed by the watcher, P1 becomes active. `tick_hotseat()` detects:

```python
def tick_hotseat():
    if not isHotSeat(): return
    ap = getActivePlayer()
    if ap == PID:  # P1 just became active
        settle_frames += 1
        if settle_frames >= SETTLE_DELAY(8):  # ~133ms for watcher to finish
            on_hermes_player_turn(PID)  # state, exec remaining cmds (moves), end turn
```

`_auto_end_turn()` now guards against ending the wrong player's turn:

```python
def _auto_end_turn():
    if getActivePlayer() != PID:
        _hermes_log('active player is not P%d, skipping sendTurnComplete' % PID)
        return  # don't end wrong player's turn
    try:
        CyMessageControl().sendTurnComplete()
    except:
        g.setAIAutoPlay(1); g.setAIAutoPlay(0)  # fallback
```

Also removed the `setActivePlayer` + `setAIAutoPlay` fallback chaining from earlier failed attempts — those were needed when `_auto_end_turn` was called from P0's context in the old `on_human_end_turn` approach. With the password-gate approach, `_auto_end_turn` is only called from `tick_hotseat()` when P1 is already the active player.

#### PowerShell Gate Watcher

Located at `bridge/hermes_gate_watcher.ps1`. Architecture:

- **Signal file:** `C:\Users\gainq\.hermes\turn_gate.json` — mod writes `{"event":"handoff_pending","status":"awaiting_gate","..."}`
- **Password:** Read from `civ4_gate_password.txt` at `$env:USERPROFILE\.hermes\` (convention: `hermes`)
- **Detection:** PowerShell polls `turn_gate.json` every 200ms for `awaiting_gate` status; stops when bridge writes `gate_opened`
- **Submit sequence (keyboard-first + VK codes + click fallback — current):**
  1. `Focus-CivWindow` — `SetForegroundWindow` + `AttachThreadInput` + retry loop (up to 600ms)
  2. Wait 600ms for popup to finish rendering after handoff
  3. `GetClientRect` to get client area dimensions
  4. **Keyboard-first:** Send Tab x3 to navigate focus to password field (resolution-independent)
  5. Send password via **VK codes** per character (NOT `KEYEVENTF_UNICODE` — Civ4 ignores Unicode) — key-down/key-up pairs with 35ms gap
  6. Send `VK_RETURN` (submits if password field is focused)
  7. **Click fallback:** Click password field at `(width*0.50, height*0.46)`, retype VK + Enter
  8. Click OK button at `(width*0.50, height*0.58)` as final fallback
  9. Check if gate status changed to `gate_opened` — if so, done; else retry in 3s

**Key coordinates (assuming centered popup, default Civ4 resolution):**

```
+-----------------------------------------+
|                                         |
|              PASSWORD POPUP             |
|                                         |
|          +-------------------+          |
|          |  password field   | <- 50%x46%
|          +-------------------+          |
|                                         |
|          +--------------+               |
|          |     OK       |     <- 50%x58%
|          +--------------+               |
+-----------------------------------------+
```

**Click calibration:** If clicks miss, run `bridge/hermes_gate_probe.ps1` while the popup is visible — it dumps all child window info (HWND, class, text, client rect) to `~/.hermes/gate_probe.log`. Adjust the % multipliers accordingly.

**Turn gate file path: TWO copies on separate filesystems**

The mod and watcher use different paths — this is BY DESIGN but easy to confuse:

| Side | Path | Written by | Read by |
|------|------|------------|---------|
| Windows | `C:\Users\gainq\.hermes\turn_gate.json` | `hermes_bridge.py` (`notify_handoff_pending`, `_mark_gate_opened`) | `hermes_gate_watcher.ps1` |
| WSL | `~/.hermes/turn_gate.json` (`/home/gainq/.hermes/`) | `civ4_bridge.py` (redundant, on `handoff_pending` event) | nobody |

The mod writes the authoritative gate file directly to the Windows path. The bridge's parallel write to WSL is harmless but unused. If debugging why the watcher isn't firing, always check the **Windows-side** file. The two files are NOT synced — they can differ (e.g., WSL shows `"awaiting_gate"` while Windows shows stale `"gate_opened"`).

- **Lock:** `gate_watcher.lock` prevents duplicate instances
- **Cooldown:** Won't re-submit within 3 seconds of last attempt
- **Log:** `C:\Users\gainq\.hermes\gate_watcher.log`
- **Auto-start:** `_start_gate_watcher()` in `hermes_bridge.py` uses `os.system('start "" /B powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "...")`. This WORKS from inside Civ4's Python 2.4 (tested, PIDs verified in lock files and log entries). Manual launch is only needed when testing without the game or when the auto-start has previously failed:
```bash
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "C:\Users\gainq\civ4-hermes-opponent\bridge\hermes_gate_watcher.ps1"
```

Clear old lock/log/gate files before starting fresh:
```bash
rm -f /mnt/c/Users/gainq/.hermes/gate_watcher.lock \
      /mnt/c/Users/gainq/.hermes/gate_watcher.log \
      /mnt/c/Users/gainq/.hermes/turn_gate.json
```

**PS1 Process Name:** The watcher must match the EXACT process name. BtS on Steam is `Civ4BeyondSword`, NOT `Civilization4`. Use PowerShell to check: `Get-Process | Where-Object { $_.ProcessName -like '*Civ*' }`

**PS1 Encoding Gotchas (PowerShell 5.1 on Windows 11):**
- UTF-8 em dashes (U+2014) in .ps1 files cause parser errors ("Unexpected token"). Use regular hyphens instead.
- Complex string interpolation like `$($variable.Property)` inside double-quoted strings can trigger parser confusion. Pre-capture into a simple variable first: `$len = $password.Length` then `Log "text $len more text"`
- **PowerShell `$pid` is a read-only automatic variable.** Do NOT write `$pid = Get-Content file` — it throws `SessionStateUnauthorizedAccessException` and the file content is silently never read. Use `$lockPid`, `$gatePid`, or any other variable name. This bug surfaces every time a diagnostic PS1 is written that checks the lock file — the `$pid` value remains the current script's own PID, reporting itself as "running" regardless of the actual watcher state.

#### Gate Probe Script

Located at `bridge/hermes_gate_probe.ps1`. Run while the password popup is visible to dump:
- Process name, PID, main window handle
- Client rect dimensions
- EnumWindows output (HWND, class name, text) for ALL windows belonging to the Civ4 process

Output written to `~/.hermes/gate_probe.log`. Use to verify whether the popup creates any Win32 child windows (it shouldn't — it's in-game rendered) and to calibrate click-position percentages.

#### CvEventManager Hooks (Current)

```python
def onUpdate(self, argsList):
    CvCameraControls.g_CameraControls.onUpdate(fDeltaTime)
    if HAS_HERMES:
        try:
            hermes_bridge.tick_hotseat()
        except Exception, e:
            CvUtil.pyPrint("Hermes tick_hotseat error: " + str(e))

def onEndPlayerTurn(self, argsList):
    iGameTurn, iPlayer = argsList
    if HAS_HERMES and iPlayer == 0:
        try:
            hermes_bridge.stage_orders()
        except Exception, e:
            CvUtil.pyPrint("Hermes stage_orders error: " + str(e))
    # ... stock handler continues ...
```

## Event Timing (Corrected, June 2026)

| Event | When it fires in hotseat | Utility |
|---|---|---|
| `onEndPlayerTurn(P0)` | After P0's `doTurn()` — popup hasn't appeared yet | Phase 1 trigger — apply research/build, write gate signal |
| (password dialog) | DLL shows modal password dialog | External watcher types password + presses Enter |
| `onUpdate` | Every render frame — fires AFTER popup dismissed | Phase 2 trigger — detect P1 active, send state, end turn |
| `onBeginPlayerTurn(P1)` | When P2's `doTurn()` fires (when P2 ENDS turn) | Too late |

#### Bridge `handoff_pending` Handling

`civ4_bridge.py` must treat `handoff_pending` as a separate event from full game state:

```python
if payload.get("event") == "handoff_pending":
    # Write to turn_gate.json only — do NOT overwrite civ4_state.json
    os.makedirs(os.path.dirname(GATE_FILE), exist_ok=True)
    with open(GATE_FILE, "w") as f:
        json.dump(payload, f)
    log("HANDOFF pending: P{} turn {}".format(...))
    send(b"[]\n")  # return empty commands
    return
```

Bridge writes to WSL `~/.hermes/turn_gate.json` — the mod already writes the authoritative gate to Windows `C:\Users\gainq\.hermes\turn_gate.json`. The bridge's write is redundant. Only the Windows-side file is read by the watcher.

Without this guard, `handoff_pending` events would overwrite `civ4_state.json` with a partial/handoff payload, corrupting the stored state for the next `on_hermes_player_turn` cycle.

## Debug Logging

### Success Signals

| Log | Success signal |
|---|---|
| Bridge terminal | `HANDOFF pending: P1 turn N` then later `T{N}: Xc Yu` (state received) |
| `gate_watcher.log` | `handoff gate pending — submitting` -> `gate opened confirmed by bridge` |
| `HermesBridge.log` | `handoff_pending` -> `tick_hotseat: P1 action phase` -> `sendTurnComplete OK` |

### Log Locations

- `HermesBridge.log` at `C:\Users\gainq\OneDrive\Documents\My Games\beyond the sword\Logs\`
- `HermesDebug.log` alongside the Python file (`Assets/Python/HermesDebug.log`)
- `gate_watcher.log` at `C:\Users\gainq\.hermes\`
- `PythonDbg.log` for load/success messages
- `PythonErr.log` for silent failures

Remove verbose per-frame logging from `tick_hotseat()` before committing to repo.
