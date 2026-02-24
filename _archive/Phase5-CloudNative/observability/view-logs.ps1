#!/usr/bin/env pwsh
# Phase 5 - Log Viewer for All AI Employees

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("task-manager", "workflow", "reporting", "all")]
    [string]$Service = "all",
    
    [Parameter(Mandatory=$false)]
    [int]$Lines = 50,
    
    [Parameter(Mandatory=$false)]
    [switch]$Follow
)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI Employee Log Viewer - Phase 5" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

function Show-Logs {
    param(
        [string]$Namespace,
        [string]$Label,
        [string]$ServiceName
    )
    
    Write-Host "=== $ServiceName Logs ===" -ForegroundColor Yellow
    
    if ($Follow) {
        kubectl logs -n $Namespace -l $Label --tail=$Lines -f
    } else {
        kubectl logs -n $Namespace -l $Label --tail=$Lines
    }
    
    Write-Host ""
}

switch ($Service) {
    "task-manager" {
        Show-Logs -Namespace "task-manager" -Label "app=task-manager" -ServiceName "Task Manager"
    }
    "workflow" {
        Show-Logs -Namespace "workflow" -Label "app=workflow-automation" -ServiceName "Workflow Automation"
    }
    "reporting" {
        Show-Logs -Namespace "reporting" -Label "app=reporting-agent" -ServiceName "Reporting Agent"
    }
    "all" {
        Show-Logs -Namespace "task-manager" -Label "app=task-manager" -ServiceName "Task Manager"
        Show-Logs -Namespace "workflow" -Label "app=workflow-automation" -ServiceName "Workflow Automation"
        Show-Logs -Namespace "reporting" -Label "app=reporting-agent" -ServiceName "Reporting Agent"
    }
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Log Viewer Complete" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
