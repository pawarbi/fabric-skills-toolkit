#!/bin/bash
# Fabric Skills Toolkit - Install Script
# Installs skills, tools, templates, and dependencies to ~/.copilot/skills/fabric/
#
# After download: chmod +x install.sh
# Usage: ./install.sh
# Usage: ./install.sh --skip-compat

set -euo pipefail

SKILLS_DIR="$HOME/.copilot/skills/fabric"
TOOLKIT_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKIP_COMPAT=false

for arg in "$@"; do
    case $arg in
        --skip-compat) SKIP_COMPAT=true ;;
    esac
done

info() { echo "[*] $1"; }
ok()   { echo "[+] $1"; }
warn() { echo "[!] $1"; }
detail() { echo "    $1"; }

echo ""
echo "Fabric Skills Toolkit Installer"
echo ""

# Validate toolkit root
if [ ! -f "$TOOLKIT_ROOT/skills/notebook-authoring-cli/SKILL.md" ]; then
    echo "Error: Cannot find skills directory. Run from the toolkit root." >&2
    exit 1
fi

# Check prerequisites
info "Checking prerequisites"
if command -v python3 &>/dev/null; then
    detail "Python: $(python3 --version 2>&1)"
elif command -v python &>/dev/null; then
    detail "Python: $(python --version 2>&1)"
else
    warn "Python not found. Tools require Python 3.x."
fi

if command -v az &>/dev/null; then
    detail "Azure CLI: found"
else
    warn "Azure CLI not found. Run 'az login' before using Fabric tools."
fi

if command -v node &>/dev/null; then
    detail "Node.js: $(node --version 2>&1)"
else
    warn "Node.js not found. context7.py MCP wrapper requires npx."
fi

# Clean previous install
if [ -d "$SKILLS_DIR" ]; then
    info "Removing previous installation"
    rm -rf "$SKILLS_DIR"
fi

# Create directories
info "Installing to $SKILLS_DIR"
mkdir -p "$SKILLS_DIR/skills/notebook-authoring-cli/references"
mkdir -p "$SKILLS_DIR/skills/workspace-context-cli/references"
mkdir -p "$SKILLS_DIR/agents"
mkdir -p "$SKILLS_DIR/tools"
mkdir -p "$SKILLS_DIR/templates"

# Copy skills
cp "$TOOLKIT_ROOT/skills/notebook-authoring-cli/SKILL.md" "$SKILLS_DIR/skills/notebook-authoring-cli/"
cp "$TOOLKIT_ROOT/skills/notebook-authoring-cli/references/"* "$SKILLS_DIR/skills/notebook-authoring-cli/references/" 2>/dev/null || true
cp "$TOOLKIT_ROOT/skills/workspace-context-cli/SKILL.md" "$SKILLS_DIR/skills/workspace-context-cli/"
cp "$TOOLKIT_ROOT/skills/workspace-context-cli/references/"* "$SKILLS_DIR/skills/workspace-context-cli/references/" 2>/dev/null || true
detail "Skills: notebook-authoring-cli, workspace-context-cli"

# Copy agents
if [ -d "$TOOLKIT_ROOT/agents" ]; then
    cp "$TOOLKIT_ROOT/agents/"* "$SKILLS_DIR/agents/" 2>/dev/null || true
    detail "Agent: FabricNotebookDev"
fi

# Copy ALL tools
for tool in notebook.py workspace_context.py analyze.py mslearn.py context7.py; do
    if [ -f "$TOOLKIT_ROOT/tools/$tool" ]; then
        cp "$TOOLKIT_ROOT/tools/$tool" "$SKILLS_DIR/tools/"
    fi
done
detail "Tools: notebook.py, workspace_context.py, analyze.py, mslearn.py, context7.py"

# Copy templates
cp "$TOOLKIT_ROOT/templates/WORKSPACE-CONTEXT.ipynb" "$SKILLS_DIR/templates/"
detail "Templates: WORKSPACE-CONTEXT.ipynb"

# Install Python dependencies
info "Installing Python dependencies"
PY_CMD="python3"
if ! command -v python3 &>/dev/null; then PY_CMD="python"; fi
if command -v $PY_CMD &>/dev/null && [ -f "$TOOLKIT_ROOT/requirements.txt" ]; then
    if $PY_CMD -m pip install -r "$TOOLKIT_ROOT/requirements.txt" --quiet 2>/dev/null; then
        detail "Installed: duckdb, matplotlib, pandas"
    else
        warn "pip install failed. Run manually: pip install -r requirements.txt"
    fi
else
    warn "Skipped (Python not found). Run: pip install -r requirements.txt"
fi

# Copy compatibility files to current directory
if [ "$SKIP_COMPAT" = false ] && [ -d "$TOOLKIT_ROOT/compatibility" ]; then
    info "Setting up compatibility files"
    for pair in "CLAUDE.md:Claude Code" ".cursorrules:Cursor" "AGENTS.md:Copilot/Codex" ".windsurfrules:Windsurf"; do
        file="${pair%%:*}"
        label="${pair#*:}"
        src="$TOOLKIT_ROOT/compatibility/$file"
        if [ -f "$src" ] && [ ! -f "./$file" ]; then
            cp "$src" "./$file"
            detail "Created: $file ($label)"
        elif [ -f "./$file" ]; then
            detail "Skipped: $file (already exists)"
        fi
    done
fi

echo ""
ok "Installation complete"
echo ""
echo "Next steps:"
detail "1. Run 'az login' if you haven't already"
detail "2. python $SKILLS_DIR/tools/notebook.py list --workspace-id YOUR_WS_ID"
detail "3. python $SKILLS_DIR/tools/workspace_context.py deploy --workspace-id YOUR_WS_ID"
echo ""