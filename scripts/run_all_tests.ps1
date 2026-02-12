# ============================================
# Run All Tests - SQLite + pytest
# ============================================
# Runs: unit, integration, e2e, Docker (file-based + integration if Docker available)
# Uses SQLite for fast local testing - no PostgreSQL/Redis required
#
# Usage:
#   .\scripts\run_all_tests.ps1
#   .\scripts\run_all_tests.ps1 -IncludeLighthouse  # Also run Lighthouse (requires server)
#
# lighthouse.yml runs separately via GitHub Actions

param(
    [switch]$IncludeLighthouse = $false,
    [switch]$SkipDockerAdvanced = $false
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# SQLite for all tests - no external DB
$env:DATABASE_URL = "sqlite:///test_db.sqlite3"
# Unset Redis so conftest uses LocMemCache
$env:REDIS_URL = ""
$env:REDIS_HOST = ""
$env:DJANGO_DEBUG = "True"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"
$env:SECRET_KEY = "test-secret-key-for-ci"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " AgroHub - Full Test Suite (SQLite)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Migrations
Write-Host "[1/4] Running migrations..." -ForegroundColor Yellow
python manage.py migrate --noinput 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Migrations failed" }
Write-Host "  OK" -ForegroundColor Green

# 2. Unit, Integration, E2E, Docker tests
Write-Host ""
Write-Host "[2/4] Running pytest (all unit, integration, e2e, docker)..." -ForegroundColor Yellow
$pytestArgs = @(
    "editais/tests",
    "-v",
    "--tb=short",
    "-n", "auto",
    "--cov=editais",
    "--cov-report=term",
    "--cov-report=html",
    "-q"
)
if ($SkipDockerAdvanced) {
    $pytestArgs += @("--ignore=editais/tests/test_docker_advanced.py")
}
pytest @pytestArgs
$pytestExit = $LASTEXITCODE

# 3. Linting
Write-Host ""
Write-Host "[3/4] Running ruff (linting)..." -ForegroundColor Yellow
ruff check editais/ UniRV_Django/
$ruffExit = $LASTEXITCODE

# 4. Security scan
Write-Host ""
Write-Host "[4/4] Running bandit (security scan)..." -ForegroundColor Yellow
bandit -r editais/ UniRV_Django/ -ll -ii --format txt 2>$null
$banditExit = $LASTEXITCODE

# 5. Optional: Lighthouse (requires server to be running)
if ($IncludeLighthouse) {
    Write-Host ""
    Write-Host "[5/5] Running Lighthouse audits..." -ForegroundColor Yellow
    Write-Host "  (Ensure server is running: python manage.py runserver)" -ForegroundColor Gray
    python scripts/lighthouse_runner.py --all --track

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Lighthouse: some checks failed" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Lighthouse: skipped (use -IncludeLighthouse to run)" -ForegroundColor Gray
    Write-Host "  Start server manually, then: python scripts/lighthouse_runner.py --all" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  pytest: $pytestExit | ruff: $ruffExit | bandit: $banditExit"
if ($pytestExit -eq 0) { Write-Host "  All tests passed" -ForegroundColor Green } else { Write-Host "  Some tests failed" -ForegroundColor Red }
exit $pytestExit
