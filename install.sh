#!/bin/bash
# Fabric Skills Toolkit - Install Script
# Installs skills, tools, and templates to ~/.copilot/skills/fabric/
#
# After download: chmod +x install.sh
# Usage: ./install.sh

set -euo pipefail

SKILLS_DIR="$HOME/.copilot/skills/fabric"
TOOLKIT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Validate toolkit root contains expected files
if [ ! -f "$TOOLKIT_ROOT/skills/notebook-authoring-cli/SKILL.md" ]; then
    echo "Error: Cannot find skills directory. Run this script from the toolkit root." >&2
    exit 1
fi

# Create target directories
mkdir -p "$SKILLS_DIR/skills/notebook-authoring-cli/references"
mkdir -p "$SKILLS_DIR/skills/workspace-context-cli/references"
mkdir -p "$SKILLS_DIR/agents"
mkdir -p "$SKILLS_DIR/tools"
mkdir -p "$SKILLS_DIR/templates"

# Copy skills
cp "$TOOLKIT_ROOT/skills/notebook-authoring-cli/SKILL.md" "$SKILLS_DIR/skills/notebook-authoring-cli/"
if ls "$TOOLKIT_ROOT/skills/notebook-authoring-cli/references/"* >/dev/null 2>&1; then
    cp "$TOOLKIT_ROOT/skills/notebook-authoring-cli/references/"* "$SKILLS_DIR/skills/notebook-authoring-cli/references/"
fi

cp "$TOOLKIT_ROOT/skills/workspace-context-cli/SKILL.md" "$SKILLS_DIR/skills/workspace-context-cli/"
if ls "$TOOLKIT_ROOT/skills/workspace-context-cli/references/"* >/dev/null 2>&1; then
    cp "$TOOLKIT_ROOT/skills/workspace-context-cli/references/"* "$SKILLS_DIR/skills/workspace-context-cli/references/"
fi

# Copy agents (optional -- directory may not exist yet)
if [ -d "$TOOLKIT_ROOT/agents" ]; then
    cp "$TOOLKIT_ROOT/agents/"* "$SKILLS_DIR/agents/" 2>/dev/null || true
fi

# Copy tools
cp "$TOOLKIT_ROOT/tools/notebook.py" "$SKILLS_DIR/tools/"
cp "$TOOLKIT_ROOT/tools/workspace_context.py" "$SKILLS_DIR/tools/"

# Copy templates
cp "$TOOLKIT_ROOT/templates/WORKSPACE-CONTEXT.ipynb" "$SKILLS_DIR/templates/"

# Copy compatibility files (optional -- directory may not exist yet)
if [ -d "$TOOLKIT_ROOT/compatibility" ]; then
    cp -r "$TOOLKIT_ROOT/compatibility" "$SKILLS_DIR/"
fi

echo "Installed to $SKILLS_DIR"
echo ""
echo "Tools installed:"
echo "  python $SKILLS_DIR/tools/notebook.py --help"
echo "  python $SKILLS_DIR/tools/workspace_context.py --help"