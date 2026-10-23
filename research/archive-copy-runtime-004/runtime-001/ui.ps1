$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class EFMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint pid);
 [DllImport("user32.dll")] public static extern void keybd_event(byte key,byte scan,uint flags,UIntPtr extra);
}
'@
function FocusHost {
 $p=@(Get-Process -Id 20560 -ErrorAction Stop); if($p.Count -ne 1){throw 'Expected exactly one test Host'}
 $s=New-Object -ComObject WScript.Shell
 [uint32]$existingOwner=0;[void][EFMouse]::GetWindowThreadProcessId([EFMouse]::GetForegroundWindow(),[ref]$existingOwner)
 if($existingOwner -ne $p[0].Id){[void]$s.AppActivate($p[0].Id)}
 Start-Sleep -Milliseconds 150
 [uint32]$owner=0;[void][EFMouse]::GetWindowThreadProcessId([EFMouse]::GetForegroundWindow(),[ref]$owner)
 if($owner -ne $p[0].Id){throw 'Host focus mismatch'}
}
function ClickAt([int]$x,[int]$y){FocusHost;[void][EFMouse]::SetCursorPos($x,$y);[EFMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero);[EFMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 250}
function Keys([string]$text){FocusHost;[System.Windows.Forms.SendKeys]::SendWait($text);Start-Sleep -Milliseconds 200}
function Drag([int]$x,[int]$y,[int]$xx,[int]$yy){FocusHost;[void][EFMouse]::SetCursorPos($x,$y);[EFMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero);for($i=1;$i -le 15;$i++){[void][EFMouse]::SetCursorPos(($x+($xx-$x)*$i/15),($y+($yy-$y)*$i/15));Start-Sleep -Milliseconds 25};[EFMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 250}
function CtrlClick([int]$x,[int]$y){FocusHost;[EFMouse]::keybd_event(17,0,0,[UIntPtr]::Zero);try{ClickAt $x $y}finally{[EFMouse]::keybd_event(17,0,2,[UIntPtr]::Zero)}}
function Shot([string]$name){
 FocusHost;$b=[Drawing.Bitmap]::new(1920,1040);$g=[Drawing.Graphics]::FromImage($b)
 try{$g.CopyFromScreen(0,0,0,0,$b.Size);$b.Save((Join-Path $PSScriptRoot $name),[Drawing.Imaging.ImageFormat]::Png)}finally{$g.Dispose();$b.Dispose()}
}
function Ui([string]$name){
 $p=Get-Process -Id 20560;$w=[Windows.Automation.AutomationElement]::FromHandle($p.MainWindowHandle)
 @($w.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition) | ForEach-Object {[pscustomobject]@{Name=$_.Current.Name;Type=$_.Current.ControlType.ProgrammaticName;Id=$_.Current.AutomationId;Rect=$_.Current.BoundingRectangle.ToString()}}) | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $PSScriptRoot $name) -Encoding utf8
}




