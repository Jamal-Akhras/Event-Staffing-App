param(
    [Parameter(Mandatory = $true)]
    [string]$Pattern,

    [ValidateSet("mapping", "backend", "docs", "symbols", "deps", "all")]
    [string]$Scope = "mapping",

    [switch]$CaseSensitive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-ProjectRoot {
    $candidates = @(
        (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
        (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
    )
    foreach ($c in $candidates) {
        $hasNew = (Test-Path (Join-Path $c "docs/api")) -and (Test-Path (Join-Path $c "docs/mapping"))
        $hasOld = (Test-Path (Join-Path $c "API DOCS")) -and (Test-Path (Join-Path $c "Transaction Mapping Review"))
        if ($hasNew -or $hasOld) {
            return $c
        }
    }
    return $candidates[-1]
}

$root = Get-ProjectRoot
$generatedDir = Join-Path $root "context/_generated"

if ($Scope -eq "symbols") {
    $indexPath = Join-Path $generatedDir "SYMBOL_INDEX.md"
    if (-not (Test-Path $indexPath)) {
        Write-Host "SYMBOL_INDEX.md not found. Run update-context.ps1 first."
        return
    }
    $caseflag = if ($CaseSensitive) { } else { "-i" }
    if (Test-CommandExists "rg") {
        if ($CaseSensitive) {
            & rg --line-number --case-sensitive $Pattern $indexPath
        } else {
            & rg --line-number -i $Pattern $indexPath
        }
    } else {
        Get-Content $indexPath | Select-String -Pattern $Pattern -CaseSensitive:$CaseSensitive
    }
    return
}

if ($Scope -eq "deps") {
    $depsPath = Join-Path $generatedDir "DEPENDENCY_MAP.md"
    if (-not (Test-Path $depsPath)) {
        Write-Host "DEPENDENCY_MAP.md not found. Run update-context.ps1 first."
        return
    }
    if (Test-CommandExists "rg") {
        if ($CaseSensitive) {
            & rg --line-number --case-sensitive -C 3 $Pattern $depsPath
        } else {
            & rg --line-number -i -C 3 $Pattern $depsPath
        }
    } else {
        Get-Content $depsPath | Select-String -Pattern $Pattern -CaseSensitive:$CaseSensitive -Context 3
    }
    return
}

$targets = switch ($Scope) {
    "mapping" { @("docs/mapping", "docs/api", "maxim-pipeline-studio/backend/app/api", "Transaction Mapping Review", "API DOCS") }
    "backend" { @("maxim-pipeline-studio/backend") }
    "docs" { @("docs/mapping", "docs/api", "maxim-pipeline-studio/docs", "Transaction Mapping Review", "API DOCS") }
    "all" { @(".") }
}

Push-Location $root
try {
    if (Test-CommandExists "rg") {
        $rgArgs = @(
            "--line-number",
            "--hidden",
            "--glob", "!.git",
            "--glob", "!**/.git/**",
            "--glob", "!**/__pycache__/**",
            "--glob", "!**/.pytest_cache/**",
            "--glob", "!**/.mypy_cache/**",
            "--glob", "!**/node_modules/**",
            "--glob", "!**/.tmp/**",
            "--glob", "!maxim-pipeline-studio/data/**",
            "--glob", "!**/data/plm_raw/**",
            "--glob", "!**/data/jsq_output/**",
            "--glob", "!**/data/example_transactions/**",
            "--glob", "!**/coverage_html/**"
        )
        if ($CaseSensitive) {
            $rgArgs += "--case-sensitive"
        } else {
            $rgArgs += "--smart-case"
        }
        $rgArgs += @($Pattern)
        $rgArgs += $targets
        & rg @rgArgs
    } else {
        $files = foreach ($t in $targets) {
            Get-ChildItem -Path $t -Recurse -File -Force -ErrorAction SilentlyContinue
        }
        $files | Select-String -Pattern $Pattern -CaseSensitive:$CaseSensitive
    }
} finally {
    Pop-Location
}
