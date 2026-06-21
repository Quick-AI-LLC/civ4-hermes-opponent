# Auto-dismiss Civ4 hotseat/PBEM "it's your turn!" handoff dialog.
$lock = Join-Path $env:USERPROFILE ".hermes\popup_watcher.lock"
$log = Join-Path $env:USERPROFILE ".hermes\popup_watcher.log"
New-Item -ItemType Directory -Force -Path (Split-Path $lock) | Out-Null

if (Test-Path $lock) {
    try {
        $oldPid = [int](Get-Content $lock -ErrorAction Stop)
        $old = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($old) { exit 0 }
    } catch {}
}
Set-Content -Path $lock -Value $PID

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class HermesWin32 {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr hWnd, EnumProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const int VK_RETURN = 0x0D;
}
"@

function Log($msg) {
    Add-Content -Path $log -Value ((Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " " + $msg)
}

function Get-WindowTextSafe($hWnd) {
    $sb = New-Object System.Text.StringBuilder 512
    [HermesWin32]::GetWindowText($hWnd, $sb, 512) | Out-Null
    return $sb.ToString()
}

function Get-AllText($hWnd) {
    $parts = @()
    $root = Get-WindowTextSafe $hWnd
    if ($root) { $parts += $root }
    $collector = @()
    $childCb = [HermesWin32+EnumProc]{
        param($ch, $p)
        $t = Get-WindowTextSafe $ch
        if ($t) { $script:collector += $t }
        return $true
    }
    [HermesWin32]::EnumChildWindows($hWnd, $childCb, [IntPtr]::Zero) | Out-Null
    if ($collector.Count -gt 0) { $parts += ($collector -join " ") }
    return ($parts -join " ")
}

function Test-HandoffText($text) {
    if (-not $text) { return $false }
    $t = $text.ToLower()
    return ($t -match "your turn") -or ($t -match "enter password") -or ($t -match "player two") -or ($t -match "player 2")
}

function Send-Enter($hWnd) {
    [HermesWin32]::SetForegroundWindow($hWnd) | Out-Null
    Start-Sleep -Milliseconds 100
    [HermesWin32]::PostMessage($hWnd, [HermesWin32]::WM_KEYDOWN, [IntPtr][HermesWin32]::VK_RETURN, [IntPtr]::Zero) | Out-Null
    [HermesWin32]::PostMessage($hWnd, [HermesWin32]::WM_KEYUP, [IntPtr][HermesWin32]::VK_RETURN, [IntPtr]::Zero) | Out-Null
}

Log "popup watcher started pid=$PID"
$lastDismiss = [datetime]::MinValue

while ($true) {
    $civ = Get-Process -Name "Civilization4" -ErrorAction SilentlyContinue
    if (-not $civ) {
        Start-Sleep -Milliseconds 500
        continue
    }
    $civPid = $civ.Id
    $hitWnd = [IntPtr]::Zero
    $hitText = ""

    $topCb = [HermesWin32+EnumProc]{
        param($hWnd, $lParam)
        if (-not [HermesWin32]::IsWindowVisible($hWnd)) { return $true }
        $wpid = 0
        [HermesWin32]::GetWindowThreadProcessId($hWnd, [ref]$wpid) | Out-Null
        if ($wpid -ne $script:civPid) { return $true }
        $all = Get-AllText $hWnd
        if (Test-HandoffText $all) {
            $script:hitWnd = $hWnd
            $script:hitText = $all
            return $false
        }
        return $true
    }
    [HermesWin32]::EnumWindows($topCb, [IntPtr]::Zero) | Out-Null

    if ($hitWnd -ne [IntPtr]::Zero) {
        $now = Get-Date
        if (($now - $lastDismiss).TotalSeconds -gt 1.5) {
            Log ("dismissing: " + $hitText)
            Send-Enter $hitWnd
            $lastDismiss = $now
        }
    }
    Start-Sleep -Milliseconds 250
}