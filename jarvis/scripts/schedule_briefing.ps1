# Register the morning briefing as a Windows Scheduled Task.
# Runs jarvis.briefing each morning and reads it aloud.
#
# NOTE: local Task Scheduler only fires while the PC is on/awake. For a briefing
# that runs with the machine OFF, use Claude Code Routines (cloud) instead and
# have this local task just SPEAK the file Routines produced.
#
# Usage (from the jarvis/ folder, in an elevated PowerShell):
#   .\scripts\schedule_briefing.ps1 -Time "06:45"

param(
  [string]$Time = "07:00",
  [string]$ProjectDir = (Resolve-Path "$PSScriptRoot\..").Path
)

$python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "py" }

$action  = New-ScheduledTaskAction -Execute $python `
           -Argument "-m jarvis.briefing --speak" -WorkingDirectory "$ProjectDir\src"
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable

Register-ScheduledTask -TaskName "JarvisMorningBriefing" -Action $action `
  -Trigger $trigger -Settings $settings -Description "Jarvis spoken morning briefing" -Force

Write-Host "Scheduled JarvisMorningBriefing daily at $Time."
