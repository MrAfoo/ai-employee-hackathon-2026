# Silver Tier – Windows Task Scheduler Setup
# Run as Administrator to register all watcher tasks.
#
# Usage:  .\scheduler\setup_tasks.ps1
#         .\scheduler\setup_tasks.ps1 -Unregister   # remove all tasks

param(
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$PYTHON = (Get-Command python).Source

$Tasks = @(
    @{
        Name        = "AgentSkills_GmailWatcher"
        Script      = "$ROOT\..\BronzeTier\watchers\gmail_watcher.py"
        Description = "Bronze: Gmail IMAP watcher – writes vault Inbox notes"
        Trigger     = "Repetition every 5 minutes"
        Minutes     = 5
    },
    @{
        Name        = "AgentSkills_FilesystemWatcher"
        Script      = "$ROOT\..\BronzeTier\watchers\filesystem_watcher.py"
        Description = "Bronze: Filesystem watcher – monitors drop folder"
        Trigger     = "At startup"
        Minutes     = $null
    },
    @{
        Name        = "AgentSkills_WhatsAppWatcher"
        Script      = "$ROOT\watchers\whatsapp_watcher.py"
        Description = "Silver: WhatsApp export watcher"
        Trigger     = "Repetition every 15 minutes"
        Minutes     = 15
    },
    @{
        Name        = "AgentSkills_LinkedInWatcher"
        Script      = "$ROOT\watchers\linkedin_watcher.py"
        Description = "Silver: LinkedIn notification watcher"
        Trigger     = "Repetition every 30 minutes"
        Minutes     = 30
    },
    @{
        Name        = "AgentSkills_ReasoningLoop"
        Script      = "$ROOT\reasoning\reasoning_loop.py"
        Description = "Silver: Claude reasoning loop – generates Plan.md"
        Trigger     = "Daily at 07:00"
        Minutes     = $null
        DailyTime   = "07:00"
    }
)

foreach ($task in $Tasks) {
    if ($Unregister) {
        Write-Host "Removing task: $($task.Name)"
        Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false -ErrorAction SilentlyContinue
        continue
    }

    Write-Host "Registering: $($task.Name)"

    $action = New-ScheduledTaskAction `
        -Execute $PYTHON `
        -Argument "`"$($task.Script)`"" `
        -WorkingDirectory $ROOT

    if ($task.DailyTime) {
        $trigger = New-ScheduledTaskTrigger -Daily -At $task.DailyTime
    } elseif ($task.Minutes) {
        $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes $task.Minutes) -Once -At (Get-Date)
    } else {
        $trigger = New-ScheduledTaskTrigger -AtStartup
    }

    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -StartWhenAvailable

    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    Register-ScheduledTask `
        -TaskName $task.Name `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $task.Description `
        -Force | Out-Null

    Write-Host "  ✅ Registered: $($task.Name)"
}

if (-not $Unregister) {
    Write-Host ""
    Write-Host "=== All Agent Skill tasks registered ==="
    Get-ScheduledTask | Where-Object { $_.TaskName -like "AgentSkills_*" } |
        Select-Object TaskName, State |
        Format-Table -AutoSize
}
