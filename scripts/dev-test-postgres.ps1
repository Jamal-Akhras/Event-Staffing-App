param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "start", "stop", "status", "migrate", "test", "url")]
    [string]$Action
)

$ErrorActionPreference = "Stop"

$pgHome = if ($env:PGTOOLS_HOME) { $env:PGTOOLS_HOME } else { Join-Path $env:USERPROFILE ".pgtools" }
$binDir = Join-Path $pgHome "pgsql\bin"
$dataDir = Join-Path $pgHome "data-event-staffing-test"
$logFile = Join-Path $pgHome "event-staffing-test-postgres.log"
$port = if ($env:PGTOOLS_PORT) { $env:PGTOOLS_PORT } else { "54329" }
$dbUser = "event_staffing"
$dbName = "event_staffing_test"
$databaseUrl = "postgresql+psycopg://${dbUser}@127.0.0.1:${port}/${dbName}"
$repoRoot = Split-Path -Parent $PSScriptRoot

function Assert-Binaries {
    if (-not (Test-Path (Join-Path $binDir "initdb.exe"))) {
        throw "PostgreSQL binaries not found at $binDir. Download the EnterpriseDB 'binaries' zip (e.g. postgresql-16.x-windows-x64-binaries.zip), extract it so that $pgHome\pgsql\bin exists, or set PGTOOLS_HOME."
    }
}

function Invoke-Init {
    Assert-Binaries
    if (Test-Path (Join-Path $dataDir "PG_VERSION")) {
        Write-Output "Cluster already initialized at $dataDir"
        return
    }
    & (Join-Path $binDir "initdb.exe") -D $dataDir -U $dbUser -A trust -E UTF8 --no-locale
    if ($LASTEXITCODE -ne 0) { throw "initdb failed with exit code $LASTEXITCODE" }
    Write-Output "Initialized test cluster at $dataDir (trust auth, local test use only)"
}

function Invoke-Start {
    Assert-Binaries
    & (Join-Path $binDir "pg_ctl.exe") status -D $dataDir | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "PostgreSQL already running on port $port"
    } else {
        & (Join-Path $binDir "pg_ctl.exe") start -D $dataDir -l $logFile -w -o "-p $port -c listen_addresses=127.0.0.1"
        if ($LASTEXITCODE -ne 0) { throw "pg_ctl start failed; see $logFile" }
    }
    & (Join-Path $binDir "psql.exe") -U $dbUser -p $port -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$dbName'" | Set-Variable exists
    if ($exists -ne "1") {
        & (Join-Path $binDir "createdb.exe") -U $dbUser -p $port $dbName
        if ($LASTEXITCODE -ne 0) { throw "createdb $dbName failed" }
        Write-Output "Created database $dbName"
    }
    Write-Output "Ready: $databaseUrl"
}

function Invoke-Stop {
    Assert-Binaries
    & (Join-Path $binDir "pg_ctl.exe") stop -D $dataDir -m fast
}

function Invoke-Status {
    Assert-Binaries
    & (Join-Path $binDir "pg_ctl.exe") status -D $dataDir
}

function Invoke-Migrate {
    $env:DATABASE_URL = $databaseUrl
    Push-Location $repoRoot
    try {
        python -m alembic -c apps/api/alembic.ini upgrade head
        if ($LASTEXITCODE -ne 0) { throw "alembic upgrade failed" }
    } finally {
        Pop-Location
    }
}

function Invoke-Test {
    Invoke-Migrate
    $env:TEST_DATABASE_URL = $databaseUrl
    $env:USE_IN_MEMORY = "false"
    $env:REQUIRE_POSTGRES_TESTS = "true"
    $baseTemp = Join-Path $env:TEMP "event-staffing-pytest"
    Push-Location $repoRoot
    try {
        python -m pytest -q --basetemp $baseTemp
        if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
    } finally {
        Pop-Location
    }
}

switch ($Action) {
    "init" { Invoke-Init }
    "start" { Invoke-Start }
    "stop" { Invoke-Stop }
    "status" { Invoke-Status }
    "migrate" { Invoke-Migrate }
    "test" { Invoke-Test }
    "url" { Write-Output $databaseUrl }
}
