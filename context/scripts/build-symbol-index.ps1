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
$outputPath = Join-Path $generatedDir "SYMBOL_INDEX.md"

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
    "# Symbol Index",
    "",
    "Generated: $timestamp",
    "Python files: $($pyFiles.Count)",
    ""
)

foreach ($file in $pyFiles) {
    $relPath = $file.FullName.Substring($projectRoot.Length + 1) -replace '\\', '/'
    $lineCount = (Get-Content $file.FullName -ErrorAction SilentlyContinue | Measure-Object).Count
    [string[]]$content = @(Get-Content $file.FullName -ErrorAction SilentlyContinue)

    if ($content.Count -eq 0 -or $lineCount -eq 0) { continue }

    $symbols = @()

    for ($i = 0; $i -lt $content.Count; $i++) {
        $line = $content[$i]
        $lineNum = $i + 1

        if ($line -match '^\s*class\s+(\w+)') {
            $className = $Matches[1]
            $bases = ""
            if ($line -match 'class\s+\w+\(([^)]+)\)') {
                $bases = " ($($Matches[1].Trim()))"
            }
            $symbols += "  L$lineNum class $className$bases"
        }
        elseif ($line -match '^\s*def\s+(\w+)\s*\(') {
            $funcName = $Matches[1]
            $indent = ($line -replace '^(\s*).*', '$1').Length
            $prefix = if ($indent -eq 0) { "  L$lineNum def" } else { "  L$lineNum   def" }
            $symbols += "$prefix $funcName"
        }
        elseif ($line -match '^\s*async\s+def\s+(\w+)\s*\(') {
            $funcName = $Matches[1]
            $indent = ($line -replace '^(\s*).*', '$1').Length
            $prefix = if ($indent -eq 0) { "  L$lineNum async def" } else { "  L$lineNum   async def" }
            $symbols += "$prefix $funcName"
        }
        elseif ($line -match '@router\.(get|post|put|patch|delete)\s*\(\s*[''"]([^''"]+)') {
            $method = $Matches[1].ToUpper()
            $route = $Matches[2]
            $symbols += "  L$lineNum @$method $route"
        }
    }

    if ($symbols.Count -gt 0) {
        $lines += "## $relPath ($lineCount lines)"
        $lines += $symbols
        $lines += ""
    }
}

$lines | Set-Content -Path $outputPath -Encoding UTF8
Write-Host "Symbol index: $outputPath ($($pyFiles.Count) files scanned)"
