#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/tabnine/skills"
PLUGIN_PATH="plugins/cursor/tabnine"

# Default to local repo scope; pass --global to install into ~/.cursor
if [[ "${1:-}" == "--global" ]]; then
  CURSOR_DIR="$HOME/.cursor"
  echo "Scope: global (~/.cursor)"
else
  CURSOR_DIR="$(pwd)/.cursor"
  echo "Scope: local ($CURSOR_DIR)"
fi

# Clone into a temp dir and clean up on exit
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "Cloning $REPO ..."
git clone --depth 1 --quiet "$REPO" "$TMP"

PLUGIN_DIR="$TMP/$PLUGIN_PATH"

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
