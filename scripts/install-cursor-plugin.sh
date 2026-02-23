#!/usr/bin/env bash
# install-cursor-plugin.sh — install the Tabnine Cursor plugin
#
# Usage:
#   bash install-cursor-plugin.sh              # install from GitHub, local project scope
#   bash install-cursor-plugin.sh --global     # install from GitHub, global (~/.cursor)
#   bash install-cursor-plugin.sh --local      # install from this local repo, local project scope
#   bash install-cursor-plugin.sh --local --global  # install from this local repo, globally
#
# --local reads plugin files directly from the local skills repo instead of cloning from GitHub.
# Useful during development to test changes without pushing first.
# When calling from another repo, use the full path to the script:
#   bash /path/to/skills/scripts/install-cursor-plugin.sh --local
# The script installs into the current working directory's .cursor/ folder.
set -euo pipefail

REPO="https://github.com/tabnine/skills"
PLUGIN_PATH="plugins/cursor/tabnine"

# Parse flags
CURSOR_DIR="$(pwd)/.cursor"
LOCAL_SOURCE=""

for arg in "$@"; do
  case "$arg" in
    --global) CURSOR_DIR="$HOME/.cursor" ;;
    --local)  LOCAL_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/$PLUGIN_PATH" ;;
    *)        true ;;
  esac
done

echo "Scope: $CURSOR_DIR"

if [[ -n "$LOCAL_SOURCE" ]]; then
  echo "Source: local ($LOCAL_SOURCE)"
  PLUGIN_DIR="$LOCAL_SOURCE"
else
  # Clone into a temp dir and clean up on exit
  TMP=$(mktemp -d)
  trap 'rm -rf "$TMP"' EXIT

  echo "Cloning $REPO ..."
  git clone --depth 1 --quiet "$REPO" "$TMP"

  PLUGIN_DIR="$TMP/$PLUGIN_PATH"
fi

# --- Agents ---
if [ -d "$PLUGIN_DIR/agents" ]; then
  mkdir -p "$CURSOR_DIR/agents"
  for f in "$PLUGIN_DIR/agents/"*.md; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    cp "$f" "$CURSOR_DIR/agents/$name"
    echo "  [agent]  $name"
  done
fi

# --- Skills ---
if [ -d "$PLUGIN_DIR/skills" ]; then
  mkdir -p "$CURSOR_DIR/skills"
  for skill_dir in "$PLUGIN_DIR/skills/"/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name="$(basename "$skill_dir")"
    mkdir -p "$CURSOR_DIR/skills/$skill_name"
    cp "$skill_dir/SKILL.md" "$CURSOR_DIR/skills/$skill_name/SKILL.md"
    echo "  [skill]  $skill_name"
  done
fi

# --- Rules ---
if [ -d "$PLUGIN_DIR/rules" ]; then
  mkdir -p "$CURSOR_DIR/rules"
  for f in "$PLUGIN_DIR/rules/"*; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    cp "$f" "$CURSOR_DIR/rules/$name"
    echo "  [rule]   $name"
  done
fi

# --- MCP servers (merge into .cursor/mcp.json) ---
if [ -f "$PLUGIN_DIR/.mcp.json" ]; then
  mcp_target="$CURSOR_DIR/mcp.json"
  if [ ! -f "$mcp_target" ]; then
    echo '{"mcpServers":{}}' > "$mcp_target"
  fi
  merged=$(python3 - <<EOF
import json

with open("$mcp_target") as f:
    target = json.load(f)
with open("$PLUGIN_DIR/.mcp.json") as f:
    source = json.load(f)

target.setdefault("mcpServers", {}).update(source.get("mcpServers", {}))
print(json.dumps(target, indent=2))
EOF
)
  echo "$merged" > "$mcp_target"
  servers=$(python3 -c "import json; d=json.load(open('$PLUGIN_DIR/.mcp.json')); print(', '.join(d.get('mcpServers',{}).keys()))")
  echo "  [mcp]    $servers"
fi

echo ""
echo "Done. Restart Cursor to apply changes."
