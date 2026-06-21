# Run while Civ4 password popup is visible. Dumps window info to gate_probe.log
$log = Join-Path (Join-Path $env:USERPROFILE ".hermes") "gate_probe.log"
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text;
public class Probe {
  public delegate bool E(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(E cb, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr h, E cb, IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int c);
  [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetClassName(IntPtr h, StringBuilder s, int c);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
}
"@
function T($h){$s=New-Object Text.StringBuilder 256;[Probe]::GetWindowText($h,$s,256)|Out-Null;return $s.ToString()}
function C($h){$s=New-Object Text.StringBuilder 256;[Probe]::GetClassName($h,$s,256)|Out-Null;return $s.ToString()}
$lines=@(); $civ=$null
foreach($n in @('Civ4BeyondSword','Civilization4')){
  $p=Get-Process -Name $n -EA SilentlyContinue|Select -First 1
  if($p){$civ=$p;break}
}
if(-not $civ){'No Civ4 process'; exit 1}
$pid=$civ.Id; $lines+="Process: $($civ.Name) pid=$pid hwnd=$($civ.MainWindowHandle)"
$r=New-Object Probe+RECT; [Probe]::GetClientRect($civ.MainWindowHandle,[ref]$r)|Out-Null
$lines+="ClientRect: $($r.L),$($r.T),$($r.R),$($r.B)"
$cb=[Probe+E]{param($h,$l)
  $wp=0; [Probe]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
  if($wp -ne $script:pid){return $true}
  $script:lines += ("HWND={0} class={1} text={2}" -f $h,(C $h),(T $h))
  [Probe]::EnumChildWindows($h,$cb,[IntPtr]::Zero)|Out-Null
  return $true
}
[Probe]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null
$lines | Set-Content $log
Write-Output "Wrote $log"