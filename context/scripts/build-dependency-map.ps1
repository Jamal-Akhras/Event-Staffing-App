param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ProjectRoot {
    if ($Root -and (Test-Path $Root)) {
        return (Resolve-Path $Root).Path
    }
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

$projectRoot = Get-ProjectRoot
$generatedDir = Join-Path $projectRoot "context/_generated"
New-Item -ItemType Directory -Path $generatedDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$outputPath = Join-Path $generatedDir "DEPENDENCY_MAP.md"

$excludeDirs = @(".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".tmp",
                  "data", "coverage_html", "example_transactions", ".venv", "dist", "build")

$pyFiles = Get-ChildItem -Path $projectRoot -Recurse -File -Filter "*.py" -Force | Where-Object {
    $fullPath = $_.FullName
    $skip = $false
    foreach ($ex in $excludeDirs) {
        if ($fullPath -match [regex]::Escape("\$ex\")) {
            $skip = $true
            break
        }
    }
    -not $skip
} | Sort-Object FullName

$lines = @(
    "# Dependency Map",
    "",
    "Generated: $timestamp",
    "Format: <- means 'imports from'",
    ""
)

foreach ($file in $pyFiles) {
    $relPath = $file.FullName.Substring($projectRoot.Length + 1) -replace '\\', '/'
    [string[]]$content = @(Get-Content $file.FullName -ErrorAction SilentlyContinue)

    if ($content.Count -eq 0) { continue }

    $imports = @()

    foreach ($line in $content) {
        if ($line -match '^\s*from\s+([\w.]+)\s+import') {
            $module = $Matches[1]
            if ($module -notmatch '^(os|sys|json|re|csv|datetime|pathlib|typing|uuid|hashlib|collections|functools|logging|math|copy|io|time|enum|abc|dataclasses|contextlib|itertools|decimal|urllib|http|asyncio|textwrap|shutil|tempfile|glob|socket|struct|base64|hmac|secrets|string|pprint|traceback|warnings|unittest|pytest)') {
                $imports += "  <- $module"
            }
        }
        elseif ($line -match '^\s*import\s+([\w.]+)') {
            $module = $Matches[1]
            if ($module -notmatch '^(os|sys|json|re|csv|datetime|pathlib|typing|uuid|hashlib|collections|functools|logging|math|copy|io|time|enum|abc|dataclasses|contextlib|itertools|decimal|urllib|http|asyncio|textwrap|shutil|tempfile|glob|socket|struct|base64|hmac|secrets|string|pprint|traceback|warnings|unittest|pytest)') {
                $imports += "  <- $module"
            }
        }

        if ($line -match '^\s*[^#]*\S' -and $line -notmatch '^\s*(from|import)\s' -and $line -notmatch '^\s*#' -and $line -notmatch '^\s*$' -and $line -notmatch '^"""' -and $line -notmatch "^'''") {
            break
        }
    }

    [string[]]$unique = @($imports | Sort-Object -Unique)
    if ($unique.Count -gt 0) {
        $lines += "## $relPath"
        $lines += $unique
        $lines += ""
    }
}

$lines | Set-Content -Path $outputPath -Encoding UTF8
Write-Host "Dependency map: $outputPath ($($pyFiles.Count) files scanned)"
