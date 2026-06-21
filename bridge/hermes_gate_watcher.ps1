# Civ4 hotseat gate watcher.
# Civ4 password popups are rendered inside the game viewport (not Win32 Edit controls).
# Strategy: focus game window -> SendInput scan codes -> clipboard paste fallback -> click+type
$hermesDir = Join-Path $env:USERPROFILE ".hermes"
$lock = Join-Path $hermesDir "gate_watcher.lock"
$log = Join-Path $hermesDir "gate_watcher.log"
$passFile = Join-Path $hermesDir "civ4_gate_password.txt"
$gateFile = Join-Path $hermesDir "turn_gate.json"
New-Item -ItemType Directory -Force -Path $hermesDir | Out-Null

if (Test-Path $lock) {
    try {
        $oldPid_val = [int](Get-Content $lock -ErrorAction Stop)
        $old = Get-Process -Id $oldPid_val -ErrorAction SilentlyContinue
        if ($old) { exit 0 }
    } catch {}
}
Set-Content -Path $lock -Value $PID

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class HermesGate {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int c);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int n);
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr hWnd, ref POINT p);
    [DllImport("user32.dll")] public static extern uint SendInput(uint n, INPUT[] inputs, int cb);
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool f);
    [DllImport("user32.dll")] public static extern IntPtr PostMessage(IntPtr hWnd, uint msg, UIntPtr wParam, IntPtr lParam);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X; public int Y; }
    [StructLayout(LayoutKind.Sequential)] public struct INPUT {
        public uint type;
        public InputUnion U;
    }
    [StructLayout(LayoutKind.Explicit)] public struct InputUnion {
        [FieldOffset(0)] public MOUSEINPUT mi;
        [FieldOffset(0)] public KEYBDINPUT ki;
    }
    [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT {
        public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT {
        public ushort wVk, wScan; public uint dwFlags, time; public IntPtr dwExtraInfo;
    }
    public const uint INPUT_MOUSE = 0;
    public const uint INPUT_KEYBOARD = 1;
    public const uint KEYEVENTF_KEYUP = 0x0002;
    public const uint KEYEVENTF_SCANCODE = 0x0008;
    public const uint MOUSEEVENTF_MOVE = 0x0001;
    public const uint MOUSEEVENTF_ABSOLUTE = 0x8000;
    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP = 0x0004;
    public const int SW_RESTORE = 9;
    public const int SW_MINIMIZE = 6;
    public const uint WM_CHAR = 0x0102;
    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
}
"@

# Scan codes for lowercase a-z (standard PS/2 set 1)
$__scanMap = @{}
$__scanLetters = @(
    0x1E,0x30,0x2E,0x20,0x12,0x21,0x22,0x23,0x17,0x24,0x25,0x26,0x32,
    0x31,0x18,0x19,0x10,0x13,0x1F,0x14,0x16,0x2F,0x11,0x2D,0x15,0x2C
)
for ($__si = 0; $__si -lt 26; $__si++) { $__scanMap[([char](0x61 + $__si))] = $__scanLetters[$__si] }
for ($__si = 0; $__si -lt 10; $__si++) { $__scanMap[([char](0x30 + $__si))] = 0x0B + $__si }  # 0-9
$__scanMap[([char]'-')] = 0x0C; $__scanMap[([char]'=')] = 0x0D
$__scanMap[([char]' ')] = 0x39
$__scanENTER = 0x1C
$__scanTAB = 0x0F

function Log($msg) {
    Add-Content -Path $log -Value ((Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " " + $msg)
}

function Get-GateStatus() {
    if (-not (Test-Path $gateFile)) { return $null }
    try {
        $raw = Get-Content $gateFile -Raw -ErrorAction Stop
        if ($raw -match '"status"\s*:\s*"([^"]+)"') { return $Matches[1] }
        if ($raw -match "awaiting_gate") { return "awaiting_gate" }
        if ($raw -match "gate_opened") { return "gate_opened" }
    } catch {}
    return $null
}

function Get-GatePassword() {
    if (-not (Test-Path $passFile)) { return $null }
    $p = (Get-Content $passFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $p) { return $null }
    return $p.Trim()
}

function Get-CivWindow() {
    foreach ($name in @("Civ4BeyondSword", "Civilization4")) {
        $civ = Get-Process -Name $name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($civ -and $civ.MainWindowHandle -ne [IntPtr]::Zero) {
            return @{ Name = $name; Process = $civ; Hwnd = $civ.MainWindowHandle; Pid = $civ.Id }
        }
    }
    return $null
}

function Focus-CivWindow($hwnd) {
    [HermesGate]::ShowWindow($hwnd, [HermesGate]::SW_RESTORE) | Out-Null
    $fg = [HermesGate]::GetForegroundWindow()
    $fgTid_val = 0; [HermesGate]::GetWindowThreadProcessId($fg, [ref]$fgTid_val) | Out-Null
    $cvTid_val = 0; [HermesGate]::GetWindowThreadProcessId($hwnd, [ref]$cvTid_val) | Out-Null
    $myTid = [HermesGate]::GetCurrentThreadId()
    if ($fgTid_val -ne $cvTid_val) {
        [HermesGate]::AttachThreadInput($myTid, $fgTid_val, $true) | Out-Null
        [HermesGate]::AttachThreadInput($myTid, $cvTid_val, $true) | Out-Null
    }
    [HermesGate]::SetForegroundWindow($hwnd) | Out-Null
    if ($fgTid_val -ne $cvTid_val) {
        [HermesGate]::AttachThreadInput($myTid, $cvTid_val, $false) | Out-Null
        [HermesGate]::AttachThreadInput($myTid, $fgTid_val, $false) | Out-Null
    }
    for ($i = 0; $i -lt 15; $i++) {
        if ([HermesGate]::GetForegroundWindow() -eq $hwnd) { return $true }
        Start-Sleep -Milliseconds 40
        [HermesGate]::SetForegroundWindow($hwnd) | Out-Null
    }
    return $false
}

# === SendInput scan code helpers (hardware-level, works with DirectInput) ===
function Send-ScanKey($scanCode, $down) {
    $flags = [HermesGate]::KEYEVENTF_SCANCODE
    if (-not $down) { $flags = $flags -bor [HermesGate]::KEYEVENTF_KEYUP }
    $inp = New-Object HermesGate+INPUT
    $inp.type = [HermesGate]::INPUT_KEYBOARD
    $inp.U.ki = New-Object HermesGate+KEYBDINPUT
    $inp.U.ki.wScan = [ushort]$scanCode
    $inp.U.ki.dwFlags = $flags
    [HermesGate]::SendInput(1, @($inp), [Runtime.InteropServices.Marshal]::SizeOf([HermesGate+INPUT])) | Out-Null
}

function Send-ScanChar([char]$ch) {
    if ($__scanMap.ContainsKey($ch)) {
        $sc = $__scanMap[$ch]
        Send-ScanKey $sc $true
        Start-Sleep -Milliseconds 10
        Send-ScanKey $sc $false
    }
}

function Send-ScanStroke($scanCode) {
    Send-ScanKey $scanCode $true
    Start-Sleep -Milliseconds 15
    Send-ScanKey $scanCode $false
}

# === PostMessage helpers (direct window message queue) ===
function PostWMChar($hwnd, [char]$ch) {
    [HermesGate]::PostMessage($hwnd, [HermesGate]::WM_CHAR, [UIntPtr][int]$ch, [IntPtr]0)
}

function PostWMKey($hwnd, $vk) {
    [HermesGate]::PostMessage($hwnd, [HermesGate]::WM_KEYDOWN, [UIntPtr][ushort]$vk, [IntPtr]0)
    Start-Sleep -Milliseconds 5
    [HermesGate]::PostMessage($hwnd, [HermesGate]::WM_KEYUP, [UIntPtr][ushort]$vk, [IntPtr]0)
}

# === Mouse click helper ===
function Click-ClientPoint($hwnd, $x, $y) {
    $pt = New-Object HermesGate+POINT
    $pt.X = $x; $pt.Y = $y
    [HermesGate]::ClientToScreen($hwnd, [ref]$pt) | Out-Null
    $sw = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width
    $sh = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height
    $ax = [int](($pt.X * 65535) / ($sw - 1))
    $ay = [int](($pt.Y * 65535) / ($sh - 1))
    $move = New-Object HermesGate+INPUT
    $move.type = [HermesGate]::INPUT_MOUSE
    $move.U.mi = New-Object HermesGate+MOUSEINPUT
    $move.U.mi.dx = $ax; $move.U.mi.dy = $ay
    $move.U.mi.dwFlags = [HermesGate]::MOUSEEVENTF_MOVE -bor [HermesGate]::MOUSEEVENTF_ABSOLUTE
    $down = New-Object HermesGate+INPUT
    $down.type = [HermesGate]::INPUT_MOUSE
    $down.U.mi = New-Object HermesGate+MOUSEINPUT
    $down.U.mi.dwFlags = [HermesGate]::MOUSEEVENTF_LEFTDOWN
    $up = New-Object HermesGate+INPUT
    $up.type = [HermesGate]::INPUT_MOUSE
    $up.U.mi = New-Object HermesGate+MOUSEINPUT
    $up.U.mi.dwFlags = [HermesGate]::MOUSEEVENTF_LEFTUP
    [HermesGate]::SendInput(1, @($move), [Runtime.InteropServices.Marshal]::SizeOf([HermesGate+INPUT])) | Out-Null
    Start-Sleep -Milliseconds 30
    [HermesGate]::SendInput(1, @($down), [Runtime.InteropServices.Marshal]::SizeOf([HermesGate+INPUT])) | Out-Null
    Start-Sleep -Milliseconds 30
    [HermesGate]::SendInput(1, @($up), [Runtime.InteropServices.Marshal]::SizeOf([HermesGate+INPUT])) | Out-Null
}

Add-Type -AssemblyName System.Windows.Forms

function Submit-Gate($civWin) {
    $hwnd = $civWin.Hwnd
    if (-not (Focus-CivWindow $hwnd)) {
        Log "Civ4 did not take foreground - will retry"
        return $false
    }

    # Popup needs a moment to finish drawing after handoff.
    Start-Sleep -Milliseconds 600

    $rect = New-Object HermesGate+RECT
    [HermesGate]::GetClientRect($hwnd, [ref]$rect) | Out-Null
    $cw = $rect.Right - $rect.Left
    $ch = $rect.Bottom - $rect.Top
    $cx = [int]($cw * 0.50)
    $pwdY = [int]($ch * 0.46)
    $okY = [int]($ch * 0.58)

    $password = Get-GatePassword
    Log ("submit attempt: process=" + $civWin.Name + " client=" + $cw + "x" + $ch)

    # === METHOD 1: Scan codes (hardware-level, bypasses VK/Unicode) ===
    Log "METHOD1: scan codes"
    # Tab to reach password field
    for ($t = 0; $t -lt 2; $t++) { Send-ScanStroke $__scanTAB; Start-Sleep -Milliseconds 80 }
    Start-Sleep -Milliseconds 100
    # Type password via scan codes
    if ($password) {
        foreach ($ch in $password.ToCharArray()) {
            Send-ScanChar $ch
            Start-Sleep -Milliseconds 35
        }
        Start-Sleep -Milliseconds 100
        Send-ScanStroke $__scanENTER
    } else {
        Send-ScanStroke $__scanENTER
    }

    # === METHOD 2: PostMessage WM_CHAR (direct window queue, bypasses input focus) ===
    Start-Sleep -Milliseconds 200
    Log "METHOD2: PostMessage WM_CHAR"
    if ($password) {
        foreach ($ch in $password.ToCharArray()) {
            PostWMChar $hwnd $ch
            Start-Sleep -Milliseconds 15
        }
        PostWMKey $hwnd 0x0D  # VK_RETURN
    }

    # === METHOD 3: Clipboard paste ===
    Start-Sleep -Milliseconds 200
    Log "METHOD3: clipboard paste"
    try {
        # Focus password field with a click first
        Click-ClientPoint $hwnd $cx $pwdY
        Start-Sleep -Milliseconds 200
        # Copy password to clipboard
        [System.Windows.Forms.Clipboard]::SetText($password)
        Start-Sleep -Milliseconds 80
        # Send Ctrl+V as scan codes
        Send-ScanKey 0x1D $true   # Ctrl down
        Send-ScanKey 0x2F $true   # V down
        Start-Sleep -Milliseconds 20
        Send-ScanKey 0x2F $false  # V up
        Send-ScanKey 0x1D $false  # Ctrl up
        Start-Sleep -Milliseconds 100
        Send-ScanStroke $__scanENTER
    } catch {
        Log "clipboard paste failed: $_"
    }

    # === METHOD 4: Click+scan type at OK ===
    Start-Sleep -Milliseconds 200
    Log "METHOD4: click OK + retype"
    Click-ClientPoint $hwnd $cx $pwdY
    Start-Sleep -Milliseconds 200
    if ($password) {
        foreach ($ch in $password.ToCharArray()) {
            Send-ScanChar $ch
            Start-Sleep -Milliseconds 35
        }
        Start-Sleep -Milliseconds 100
        Send-ScanStroke $__scanENTER
    }
    Start-Sleep -Milliseconds 200
    Click-ClientPoint $hwnd $cx $okY

    return $true
}

Log "gate watcher started pid=$PID"
$lastSubmit = [datetime]::MinValue
$attempts = 0

while ($true) {
    $status = Get-GateStatus
    if ($status -eq "gate_opened") {
        Start-Sleep -Milliseconds 500
        continue
    }

    if ($status -ne "awaiting_gate") {
        Start-Sleep -Milliseconds 300
        continue
    }

    $civWin = Get-CivWindow
    if (-not $civWin) {
        Start-Sleep -Milliseconds 500
        continue
    }

    $now = Get-Date
    if (($now - $lastSubmit).TotalSeconds -lt 4.0) {
        Start-Sleep -Milliseconds 200
        continue
    }

    $attempts++
    Log ("handoff gate pending - attempt " + $attempts)
    Submit-Gate $civWin | Out-Null
    $lastSubmit = $now

    Start-Sleep -Milliseconds 800
    $after = Get-GateStatus
    if ($after -eq "gate_opened") {
        Log "gate opened confirmed by bridge"
        $attempts = 0
    }
    Start-Sleep -Milliseconds 200
}
