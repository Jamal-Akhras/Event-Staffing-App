param(
    [string]$Root = "",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

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

if (-not $Force) {
    $sentinel = Join-Path $generatedDir "FILE_INDEX.txt"
    if (Test-Path $sentinel) {
        $age = (Get-Date) - (Get-Item $sentinel).LastWriteTime
        if ($age.TotalMinutes -lt 60) {
            Write-Host "Context index is $([math]::Round($age.TotalMinutes))m old (< 1h). Use -Force to regenerate."
            return
        }
    }
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$rgExcludes = @(
    '-g "!.git"',
    '-g "!**/.git/**"',
    '-g "!**/__pycache__/**"',
    '-g "!**/.pytest_cache/**"',
    '-g "!**/.mypy_cache/**"',
    '-g "!**/node_modules/**"',
    '-g "!**/.tmp/**"',
    '-g "!**/data/plm_raw/**"',
    '-g "!**/data/jsq_output/**"',
    '-g "!**/data/example_transactions/**"',
    '-g "!**/coverage_html/**"',
    '-g "!**/.venv/**"',
    '-g "!**/dist/**"',
    '-g "!**/build/**"'
)

$psExcludePattern = @(
    "\\.git\\",
    "\\__pycache__\\",
    "\\.pytest_cache\\",
    "\\.mypy_cache\\",
    "\\node_modules\\",
    "\\.tmp\\",
    "\\maxim-pipeline-studio\\data\\",
    "\\data\\plm_raw\\",
    "\\data\\jsq_output\\",
    "\\data\\example_transactions\\",
    "\\coverage_html\\",
    "\\.venv\\",
    "\\dist\\",
    "\\build\\"
)

Push-Location $projectRoot
try {
    # --- FILE_INDEX.txt ---
    $fileIndexPath = Join-Path $generatedDir "FILE_INDEX.txt"
    if (Test-CommandExists "rg") {
        $rgArgs = @("--files", "--hidden")
        foreach ($ex in $rgExcludes) {
            $parts = $ex.Trim('"').Split('" "')
            foreach ($p in $parts) {
                $clean = $p.Trim().Trim('"')
                if ($clean -match '^-g$') { $rgArgs += "-g" }
                else { $rgArgs += $clean }
            }
        }
        & rg --files --hidden `
            -g "!.git" `
            -g "!**/.git/**" `
            -g "!**/__pycache__/**" `
            -g "!**/.pytest_cache/**" `
            -g "!**/.mypy_cache/**" `
            -g "!**/node_modules/**" `
            -g "!**/.tmp/**" `
            -g "!maxim-pipeline-studio/data/**" `
            -g "!**/data/plm_raw/**" `
            -g "!**/data/jsq_output/**" `
            -g "!**/data/example_transactions/**" `
            -g "!**/coverage_html/**" `
            -g "!**/.venv/**" `
            -g "!**/dist/**" `
            -g "!**/build/**" `
            | Sort-Object | Set-Content -Path $fileIndexPath -Encoding UTF8
    } else {
        Get-ChildItem -Path . -Recurse -File -Force `
            | Where-Object {
                $fullPath = $_.FullName
                $skip = $false
                foreach ($pat in $psExcludePattern) {
                    if ($fullPath -match $pat) { $skip = $true; break }
                }
                -not $skip
            } `
            | ForEach-Object { Resolve-Path -Relative $_.FullName } `
            | Sort-Object `
            | Set-Content -Path $fileIndexPath -Encoding UTF8
    }

    # --- DIRECTORY_SUMMARY.md (3-level depth) ---
    $summaryPath = Join-Path $generatedDir "DIRECTORY_SUMMARY.md"
    $summaryLines = @(
        "# Directory Summary",
        "",
        "Generated: $timestamp",
        "",
        "| Directory | Files |",
        "|---|---:|"
    )

    [string[]]$indexContent = @(Get-Content -Path $fileIndexPath -ErrorAction SilentlyContinue)
    if ($indexContent.Count -gt 0) {
        $dirCounts = @{}
        foreach ($entry in $indexContent) {
            $entry = $entry -replace '\\', '/'
            $parts = $entry.Split('/')
            for ($depth = 1; $depth -le [math]::Min($parts.Count - 1, 3); $depth++) {
                $key = ($parts[0..($depth - 1)] -join '/')
                if (-not $dirCounts.ContainsKey($key)) { $dirCounts[$key] = 0 }
                $dirCounts[$key]++
            }
        }

        $sorted = $dirCounts.GetEnumerator() | Sort-Object Name
        foreach ($kv in $sorted) {
            $depth = ($kv.Name.Split('/').Count)
            $indent = "  " * ($depth - 1)
            $summaryLines += "| $indent$($kv.Name)/ | $($kv.Value) |"
        }
    }

    $summaryLines | Set-Content -Path $summaryPath -Encoding UTF8

    # --- SEARCH_HOTSPOTS.md ---
    $hotspotsPath = Join-Path $generatedDir "SEARCH_HOTSPOTS.md"
    $hotspots = @(
        @{ Name = "Transaction Mapping"; Path = "docs/mapping" },
        @{ Name = "API Specs And Notes"; Path = "docs/api" },
        @{ Name = "Backend API"; Path = "maxim-pipeline-studio/backend/app/api" },
        @{ Name = "Backend Scripts"; Path = "maxim-pipeline-studio/backend/scripts" },
        @{ Name = "Data Models / Docs"; Path = "maxim-pipeline-studio/docs" },
        @{ Name = "PLM-JSQ Pipeline v2"; Path = "maxim-pipeline-studio/backend/full-plm-jsq-v2" }
    )

    $hotspotLines = @(
        "# Search Hotspots",
        "",
        "Generated: $timestamp",
        "",
        "| Area | Path | Exists |",
        "|---|---|---|"
    )

    foreach ($spot in $hotspots) {
        $exists = Test-Path (Join-Path $projectRoot $spot.Path)
        $hotspotLines += "| $($spot.Name) | $($spot.Path) | $exists |"
    }

    $hotspotLines | Set-Content -Path $hotspotsPath -Encoding UTF8

    # --- MAPPING_RELATED_FILES.txt ---
    $mappingFilesPath = Join-Path $generatedDir "MAPPING_RELATED_FILES.txt"
    if (Test-CommandExists "rg") {
        Get-Content -Path $fileIndexPath `
            | & rg -i "mapping|transaction|pipeline|plm|jsq|allocation" `
            | Sort-Object `
            | Set-Content -Path $mappingFilesPath -Encoding UTF8
    } else {
        Get-Content -Path $fileIndexPath `
            | Where-Object { $_ -match "(?i)mapping|transaction|pipeline|plm|jsq|allocation" } `
            | Sort-Object `
            | Set-Content -Path $mappingFilesPath -Encoding UTF8
    }

    # --- SYMBOL_INDEX.md ---
    $symbolScript = Join-Path $PSScriptRoot "build-symbol-index.ps1"
    if (Test-Path $symbolScript) {
        & $symbolScript -Root $projectRoot
    }

    # --- DEPENDENCY_MAP.md ---
    $depScript = Join-Path $PSScriptRoot "build-dependency-map.ps1"
    if (Test-Path $depScript) {
        & $depScript -Root $projectRoot
    }

    Write-Host "Context index updated: $generatedDir"
} finally {
    Pop-Location
}
