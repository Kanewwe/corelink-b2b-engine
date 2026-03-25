# Linkora Backend Test Runner
# Usage: ./scripts/test.ps1

Write-Host "🧪 Running Linkora Backend Unit Tests..." -ForegroundColor Cyan

# Ensure we are in the project root
$ProjectRoot = Get-Location
if (-not (Test-Path "$ProjectRoot\backend")) {
    Write-Error "Error: Must run from project root."
    exit 1
}

# Add backend to PYTHONPATH for the session
$env:PYTHONPATH = "$ProjectRoot\backend"

# Run pytest
python -m pytest backend/tests -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Tests failed. Please check the output above." -ForegroundColor Red
    exit 1
}
