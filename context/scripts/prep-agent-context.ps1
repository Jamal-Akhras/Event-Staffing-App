param(
    [Parameter(Mandatory = $true)]
    [string]$Pattern,

    [ValidateSet("mapping", "backend", "docs", "all")]
    [string]$Scope = "mapping"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path

Write-Host "[1/2] Updating context index..."
powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "update-context.ps1") -Root $root

Write-Host "[2/2] Running scoped search..."
powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "search-context.ps1") -Pattern $Pattern -Scope $Scope
