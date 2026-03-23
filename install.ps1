# Fabric Skills Toolkit - Install Script
# Installs skills, tools, templates, and dependencies to ~/.copilot/skills/fabric/
#
# Usage:
#   .\install.ps1
#   .\install.ps1 -ProjectPath "C:\MyProject"
#   .\install.ps1 -SkipCompatibility

param(
    [string]$ProjectPath = ".",
    [switch]$SkipCompatibility
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SkillsDir = "$env:USERPROFILE\.copilot\skills\fabric"
$ToolkitRoot = $PSScriptRoot

function Write-Status($message) { Write-Host "[*] $message" -ForegroundColor Cyan }
function Write-Ok($message) { Write-Host "[+] $message" -ForegroundColor Green }
function Write-Detail($message) { Write-Host "    $message" -ForegroundColor Gray }
function Write-Warn($message) { Write-Host "[!] $message" -ForegroundColor Yellow }

Write-Host ""
Write-Host "Fabric Skills Toolkit Installer" -ForegroundColor White
Write-Host ""

# Validate toolkit root
if (-not (Test-Path "$ToolkitRoot\skills\notebook-authoring-cli\SKILL.md")) {
    Write-Error "Cannot find skills directory. Run this script from the toolkit root."
    exit 1
}

# Check prerequisites
Write-Status "Checking prerequisites"

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Write-Detail "Python: $($python.Source)"
} else {
    Write-Warn "Python not found. Tools require Python 3.x."
}

$az = Get-Command az.cmd -ErrorAction SilentlyContinue
if (-not $az) { $az = Get-Command az -ErrorAction SilentlyContinue }
if ($az) {
    Write-Detail "Azure CLI: $($az.Source)"
} else {
    Write-Warn "Azure CLI not found. Run 'az login' before using Fabric tools."
}

$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    Write-Detail "Node.js: $($node.Source)"
} else {
    Write-Warn "Node.js not found. context7.py MCP wrapper requires npx."
}

# Clean previous install
if (Test-Path $SkillsDir) {
    Write-Status "Removing previous installation"
    Remove-Item -Recurse -Force $SkillsDir
}

# Create directories
Write-Status "Installing to $SkillsDir"
$dirs = @(
    "$SkillsDir\skills\notebook-authoring-cli\references",
    "$SkillsDir\skills\workspace-context-cli\references",
    "$SkillsDir\agents",
    "$SkillsDir\tools",
    "$SkillsDir\templates"
)
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# Copy skills
Copy-Item "$ToolkitRoot\skills\notebook-authoring-cli\SKILL.md" "$SkillsDir\skills\notebook-authoring-cli\" -Force
if (Test-Path "$ToolkitRoot\skills\notebook-authoring-cli\references\*") {
    Copy-Item "$ToolkitRoot\skills\notebook-authoring-cli\references\*" "$SkillsDir\skills\notebook-authoring-cli\references\" -Force
}
Copy-Item "$ToolkitRoot\skills\workspace-context-cli\SKILL.md" "$SkillsDir\skills\workspace-context-cli\" -Force
if (Test-Path "$ToolkitRoot\skills\workspace-context-cli\references\*") {
    Copy-Item "$ToolkitRoot\skills\workspace-context-cli\references\*" "$SkillsDir\skills\workspace-context-cli\references\" -Force
}
Write-Detail "Skills: notebook-authoring-cli, workspace-context-cli"

# Copy agents
if (Test-Path "$ToolkitRoot\agents") {
    Copy-Item "$ToolkitRoot\agents\*" "$SkillsDir\agents\" -Force -ErrorAction SilentlyContinue
    Write-Detail "Agent: FabricNotebookDev"
}

# Copy ALL tools
$tools = @("notebook.py", "workspace_context.py", "analyze.py", "mslearn.py", "context7.py")
foreach ($tool in $tools) {
    if (Test-Path "$ToolkitRoot\tools\$tool") {
        Copy-Item "$ToolkitRoot\tools\$tool" "$SkillsDir\tools\" -Force
    }
}
Write-Detail "Tools: $($tools -join ', ')"

# Copy templates
Copy-Item "$ToolkitRoot\templates\WORKSPACE-CONTEXT.ipynb" "$SkillsDir\templates\" -Force
Write-Detail "Templates: WORKSPACE-CONTEXT.ipynb"

# Install Python dependencies
Write-Status "Installing Python dependencies"
if ($python -and (Test-Path "$ToolkitRoot\requirements.txt")) {
    try {
        python -m pip install -r "$ToolkitRoot\requirements.txt" --quiet 2>&1 | Out-Null
        Write-Detail "Installed: duckdb, matplotlib, pandas"
    } catch {
        Write-Warn "pip install failed. Run manually: pip install -r requirements.txt"
    }
} else {
    Write-Warn "Skipped (Python not found). Run: pip install -r requirements.txt"
}

# Copy compatibility files to project root
if (-not $SkipCompatibility) {
    Write-Status "Setting up compatibility files"
    $ProjectPath = Resolve-Path $ProjectPath

    $compatFiles = @(
        @{ src = "compatibility\CLAUDE.md";       dst = "CLAUDE.md";       label = "Claude Code" },
        @{ src = "compatibility\.cursorrules";    dst = ".cursorrules";    label = "Cursor" },
        @{ src = "compatibility\AGENTS.md";       dst = "AGENTS.md";       label = "Copilot/Codex" },
        @{ src = "compatibility\.windsurfrules";  dst = ".windsurfrules";  label = "Windsurf" }
    )

    foreach ($f in $compatFiles) {
        $srcPath = Join-Path $ToolkitRoot $f.src
        $dstPath = Join-Path $ProjectPath $f.dst
        if ((Test-Path $srcPath) -and -not (Test-Path $dstPath)) {
            Copy-Item $srcPath $dstPath
            Write-Detail "Created: $($f.dst) ($($f.label))"
        } elseif (Test-Path $dstPath) {
            Write-Detail "Skipped: $($f.dst) (already exists)"
        }
    }
}

Write-Host ""
Write-Ok "Installation complete"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Detail "1. Run 'az login' if you haven't already"
Write-Detail "2. python $SkillsDir\tools\notebook.py list --workspace-id YOUR_WS_ID"
Write-Detail "3. python $SkillsDir\tools\workspace_context.py deploy --workspace-id YOUR_WS_ID"
Write-Host ""
