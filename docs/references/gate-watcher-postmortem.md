# Gate Watcher Postmortem — Civ4 Hotseat Password Automation

## Problem Summary

The hotseat bridge places Hermes as P2 in a password-protected hotseat slot.
When P1 ends their turn, Civ4 draws the password dialog INSIDE the game viewport
(not as a Win32 dialog box). The watcher script must auto-enter the password
"hermes" and click OK to let Hermes take their turn.

---

## What Was Tried (in order)

### 1. Win32 Dialog Detection
| File | Approach | Result |
|------|----------|--------|
| hermes_popup_dismiss.ps1 | Find #32770 dialog, EnumChildWindows for Edit control, WM_SETTEXT / WM_CHAR | FAILED — password dialog has no Win32 HWND. It's drawn by the game engine. |
| Same | SendKeys fallback | FAILED — SendKeys can crash the game; also relies on window focus that doesn't reach in-game UI. |

### 2. SendInput + Click Coordinates (Composer's version)
| Aspect | Detail |
|--------|--------|
| Focus | Focus-CivWindow via AttachThreadInput + SetForegroundWindow |
| Password entry | KEYEVENTF_UNICODE (SendInput with Unicode code points) |
| Click | ClientToScreen → MOUSEEVENTF_ABSOLUTE at 50%w/46%h (password), 50%w/58%h (OK) |
| Result | **14 attempts logged.** Watcher ran but password never entered. |

Root cause: **KEYEVENTF_UNICODE** — Civ4's text input handler (2007 engine) does
not process Unicode keyboard events. The characters are sent but the game ignores
them.

### 3. Virtual Key Codes (VK_A..VK_Z)
| Aspect | Detail |
|--------|--------|
| Change | Replaced KEYEVENTF_UNICODE with VK_A-VK_Z via Send-Key (wVk field) |
| Added | Keyboard-first: Tab x3 → VK password → Enter before click fallback |
| Result | **3 attempts logged.** Password still not entered. |

Likely cause: VK codes may not reach the game's DirectInput handler, or the
Focus-CivWindow call disrupts the game's exclusive input mode (fullscreen D3D).

### 4. Multi-Method (deployed but untested)
Four methods run in sequence each attempt:
1. **Hardware scan codes** (KEYEVENTF_SCANCODE) — injects at keyboard HW level
2. **PostMessage WM_CHAR** — sends chars directly to Civ4's window message queue
3. **Clipboard paste** — Ctrl+V the password into the focused field
4. **Click + scan codes** — click estimated field, retype via scan codes, click OK

Status: **Untested** — Nick decided to revert before this could be tested.

---

## Technical Details (for future reference)

### Environment
- Game: Civ4 Beyond the Sword (Steam)
- Resolution: 2560x1440 (ScreenWidth=0 in ini = desktop auto-detect)
- Window mode: Fullscreen exclusive (Direct3D)
- Window client rect (from GetClientRect): 2560x1440
- Password: "hermes" (6 lowercase ASCII chars)
- Watcher runs as: Hidden PowerShell process on Windows
- Bridge runs on: WSL port 3334
- Anti-virus flag: Avast IDP.generic (heuristic false positive from SendInput + hidden PS)

### Key File Locations
- Watcher: C:\Users\gainq\civ4-hermes-opponent\bridge\hermes_gate_watcher.ps1
- Password: C:\Users\gainq\.hermes\civ4_gate_password.txt
- Gate file (watcher reads): C:\Users\gainq\.hermes\turn_gate.json
- Gate file (mod writes): C:\Users\gainq\.hermes\turn_gate.json (same path ✓)
- Gate file (bridge writes): ~/.hermes/turn_gate.json (WSL path — unused, different dir!)
- Bridge: /mnt/c/Users/gainq/civ4-hermes-opponent/bridge/civ4_bridge.py
- Probe: C:\Users\gainq\civ4-hermes-opponent\bridge\hermes_gate_probe.ps1

### Channel Architecture
```
Civ4 mod (hermes_bridge.py)
    │
    ├── write turn_gate.json ─────► C:\Users\gainq\.hermes\turn_gate.json
    │                                   │
    │                                   ▼
    │                               watcher reads, submits password
    │
    ├── TCP handoff_pending ──────► WSL bridge (:3334)
    │                                   │
    │                                   └── write turn_gate.json
    │                                       (WSL ~/.hermes/ — UNUSED)
    │
    └── on_hermes_player_turn() ──► TCP state ──► WSL bridge
                                              ──► commands back
```

### Lock File Quirk
$PID is a read-only automatic variable in PowerShell. Do NOT use it as an
assignment target — the assignment silently fails and $pid keeps the current
process ID, causing lock checks to always find "the current process" running.
Use a different variable name ($lockPid, $pid_val, etc.).

---

## Potential Future Solutions (untested)

### A. PostMessage WM_CHAR with proper lParam
WM_CHAR alone may not work. The lParam must contain the scan code in bits 16-23:
  lParam = (scanCode << 16) | 1
  [HermesGate]::PostMessage($hwnd, WM_CHAR, (UIntPtr)(int)$ch, (IntPtr)(scanCode << 16 | 1))

### B. SendInput with hardware scan codes
Already deployed but untested (METHOD1 in current script). Uses KEYEVENTF_SCANCODE
which injects at the keyboard hardware level, bypassing both VK and Unicode
translation. Most likely to work with DirectInput games.

### C. Run game in windowed mode
Fullscreen exclusive mode makes SendInput unreliable. In windowed mode, standard
Windows input routing applies and the AttachThreadInput trick works reliably.
Add `FullScreen=0` to CivilizationIV.ini.

### D. C# compiled helper EXE
The PowerShell Add-Type + SendInput combo triggers heuristic AV. A compiled C#
console EXE (with Authenticode signature or just an exclusion) avoids PS
heuristic scanning entirely.

### E. UI Automation
Use Windows Automation API (UIA) to find the password text field within the
game's client area. Unlikely to work for in-game rendered UI but worth testing
if the game registers the field as an accessibility element.

### F. DirectInput API injection
Use IDirectInputDevice::SendDeviceData to inject raw keyboard packets directly
into the game's DirectInput device. Complex but guaranteed to work for DInput
games. Requires C++ and COM interop.

---

## Files Left Behind (need cleanup)
- C:\Users\gainq\.hermes\gate_watcher.* (lock, log, error)
- C:\Users\gainq\.hermes\popup_watcher.* (lock, log)
- C:\Users\gainq\.hermes\restart_watcher*.ps1
- C:\Users\gainq\.hermes\check_watcher.ps1
- C:\Users\gainq\.hermes\diag.ps1
- C:\Users\gainq\.hermes\diag2.ps1
- C:\Users\gainq\.hermes\gate_watcher_error.txt
- C:\Users\gainq\.hermes\civ4_gate_password.txt
