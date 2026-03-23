# Fabric Skills Toolkit - Install Script
# Installs skills, tools, and templates to ~/.copilot/skills/fabric/
#
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SkillsDir = "$env:USERPROFILE\.copilot\skills\fabric"
$ToolkitRoot = $PSScriptRoot

# Validate toolkit root contains expected files
if (-not (Test-Path "$ToolkitRoot\skills\notebook-authoring-cli\SKILL.md")) {
    Write-Error "Cannot find skills directory. Run this script from the toolkit root."
    exit 1
}

# Create target directories
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

# Copy agents (optional -- directory may not exist yet)
if (Test-Path "$ToolkitRoot\agents") {
    Copy-Item "$ToolkitRoot\agents\*" "$SkillsDir\agents\" -Force -ErrorAction SilentlyContinue
}

# Copy tools
Copy-Item "$ToolkitRoot\tools\notebook.py" "$SkillsDir\tools\" -Force
Copy-Item "$ToolkitRoot\tools\workspace_context.py" "$SkillsDir\tools\" -Force

# Copy templates
Copy-Item "$ToolkitRoot\templates\WORKSPACE-CONTEXT.ipynb" "$SkillsDir\templates\" -Force

# Copy compatibility files (optional -- directory may not exist yet)
if (Test-Path "$ToolkitRoot\compatibility") {
    Copy-Item "$ToolkitRoot\compatibility" "$SkillsDir\" -Recurse -Force
}

Write-Host "Installed to $SkillsDir"
Write-Host ""
Write-Host "Tools installed:"
Write-Host "  python $SkillsDir\tools\notebook.py --help"
Write-Host "  python $SkillsDir\tools\workspace_context.py --help"
