# Fabric Skills Toolkit — Setup Script (Windows)
# Run: .\setup.ps1

Write-Host "🔧 Fabric Skills Toolkit Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "❌ Python not found. Please install Python 3.10+ and try again." -ForegroundColor Red
    exit 1
}
$pyVersion = python --version 2>&1
Write-Host "✅ Found $pyVersion" -ForegroundColor Green

# Install Python dependencies
Write-Host ""
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install -q duckdb matplotlib pandas
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some Python dependencies may have failed to install" -ForegroundColor Yellow
}

# Check Node.js (for Context7)
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Found Node.js $nodeVersion (needed for Context7)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Node.js not found. Context7 wrapper won't work without it." -ForegroundColor Yellow
    Write-Host "   Install from: https://nodejs.org/" -ForegroundColor Yellow
}

# Set up .copilot directory
Write-Host ""
Write-Host "📁 Setting up .copilot directory..." -ForegroundColor Yellow
$copilotDir = Join-Path $env:USERPROFILE ".copilot"
if (-not (Test-Path $copilotDir)) {
    New-Item -ItemType Directory -Path $copilotDir -Force | Out-Null
    Write-Host "   Created $copilotDir" -ForegroundColor Gray
}

# Copy templates if not already present
$memoryDest = Join-Path $copilotDir "memory.json"
$contextDest = Join-Path $copilotDir "CONTEXT.md"

if (-not (Test-Path $memoryDest)) {
    Copy-Item "templates\memory.json" $memoryDest
    Write-Host "✅ Created $memoryDest (edit with your workspace IDs)" -ForegroundColor Green
} else {
    Write-Host "ℹ️  $memoryDest already exists (skipped)" -ForegroundColor Cyan
}

if (-not (Test-Path $contextDest)) {
    Copy-Item "templates\CONTEXT.md" $contextDest
    Write-Host "✅ Created $contextDest (edit with your preferences)" -ForegroundColor Green
} else {
    Write-Host "ℹ️  $contextDest already exists (skipped)" -ForegroundColor Cyan
}

# Verify tools work
Write-Host ""
Write-Host "🧪 Verifying tools..." -ForegroundColor Yellow

# Test DuckDB
try {
    $result = python tools/analyze.py query "SELECT 'toolkit works!' AS status" 2>&1
    if ($result -match "toolkit works") {
        Write-Host "✅ analyze.py (DuckDB) — working" -ForegroundColor Green
    } else {
        Write-Host "⚠️  analyze.py — unexpected output" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ analyze.py — failed" -ForegroundColor Red
}

# Test MS Learn
try {
    Write-Host "   Testing MS Learn docs (requires internet)..." -ForegroundColor Gray
    $result = python tools/mslearn.py tools 2>&1
    if ($result -match "microsoft_docs") {
        Write-Host "✅ mslearn.py — working" -ForegroundColor Green
    } else {
        Write-Host "⚠️  mslearn.py — unexpected output" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ mslearn.py — failed" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit $memoryDest with your workspace IDs" -ForegroundColor White
Write-Host "  2. Edit $contextDest with your preferences" -ForegroundColor White
Write-Host "  3. Try: python tools/mslearn.py search 'fabric lakehouse'" -ForegroundColor White
Write-Host "  4. Try: python tools/analyze.py query 'SELECT 1+1 AS answer'" -ForegroundColor White
Write-Host ""
Write-Host "For Context7 (library docs), ensure Node.js 18+ is installed, then try:" -ForegroundColor White
Write-Host "  python tools/context7.py search 'pandas'" -ForegroundColor White
Write-Host ""
Write-Host "For OneLake tools, see: docs/mcp-integration-guide.md" -ForegroundColor White
