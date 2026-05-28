---
name: ctx
description: >
  Query the Context Engine knowledge graph — search entities and triage/resolve
  CVEs (the suggested fix is embedded in each resolution entity, filterable by
  severity). Use when searching the knowledge graph or working on security
  issues.
allowed-tools: Bash(ctx-cli:*)
---

# Context Engine CLI

## Prerequisites

If `ctx-cli` is not installed, download the newest CLI-scoped release:
```bash
RELEASES=$(curl -fsSL --max-time 8 'https://api.github.com/repos/tabnine/skills/releases?per_page=100')
TAG=$(printf '%s\n' "$RELEASES" | tr '{' '\n' | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(ctx-cli-v[0-9][^"]*\)".*/\1/p' | head -1)
[ -n "$TAG" ] || TAG=$(printf '%s\n' "$RELEASES" | tr '{' '\n' | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[0-9][^"]*\)".*/\1/p' | head -1)
test -n "$TAG" || { echo "No ctx-cli release found"; exit 1; }
curl -fsSL "https://github.com/tabnine/skills/releases/download/$TAG/ctx-cli-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/aarch64/arm64/;s/x86_64/x64/')" -o /usr/local/bin/ctx-cli && chmod +x /usr/local/bin/ctx-cli
```

Set your API key:
```bash
export CTX_API_KEY=<your-key>
export CTX_API_URL=https://ctx.tabnine.com
```

## Stay current

Once per session — before your first `ctx-cli` call — run the snippet below. It's idempotent, network-silent within 24h, and never blocks. If `tabnine/skills` has a newer `ctx-cli` release than the local CLI, it prints one stderr line and exits cleanly; pass the hint through to the user and move on with the task. If the network is unreachable or the tag can't be parsed, the snippet stays silent (no false-positive nags).

State is cached at `~/.ctx/mcp-cache/version-check.json` (same dir as the MCP tool cache).

```bash
F=$HOME/.ctx/mcp-cache/version-check.json
NOW=$(date +%s); MT=$(stat -f %m "$F" 2>/dev/null || stat -c %Y "$F" 2>/dev/null || echo 0)
if [ ! -f "$F" ] || [ $((NOW-MT)) -ge 86400 ]; then
  mkdir -p "$(dirname "$F")"
  RELEASES=$(curl -fsSL --max-time 8 'https://api.github.com/repos/tabnine/skills/releases?per_page=100' 2>/dev/null)
  TAG=$(printf '%s\n' "$RELEASES" | tr '{' '\n' | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(ctx-cli-v[0-9][^"]*\)".*/\1/p' | head -1)
  [ -n "$TAG" ] || TAG=$(printf '%s\n' "$RELEASES" | tr '{' '\n' | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[0-9][^"]*\)".*/\1/p' | head -1)
  LATEST=${TAG#ctx-cli-v}; LATEST=${LATEST#v}
  LOCAL=$(ctx-cli --version 2>/dev/null)
  printf '{"checkedAt":"%s","latest":"%s","local":"%s"}\n' "$(date -u +%FT%TZ)" "$LATEST" "$LOCAL" > "$F"
  [ -n "$LATEST" ] && [ -n "$LOCAL" ] && [ "$LATEST" != "$LOCAL" ] && \
    echo "ℹ️  ctx-cli v$LATEST available (you have v$LOCAL). Upgrade: curl -fsSL https://github.com/tabnine/skills/releases/download/$TAG/ctx-cli-\$(uname -s | tr '[:upper:]' '[:lower:]')-\$(uname -m | sed 's/aarch64/arm64/;s/x86_64/x64/') -o /usr/local/bin/ctx-cli && chmod +x /usr/local/bin/ctx-cli" >&2
fi
```

## Quick start

```bash
# Search the knowledge graph
ctx-cli mcp call find_entities -p query="authentication" -o json
```

## Discover tools

```bash
# List all available tools
ctx-cli mcp list -o json

# Search for tools by keyword
ctx-cli mcp list -s jira -o json

# See a tool's parameters before calling
ctx-cli mcp describe <tool-name>
```

## Security & CVEs

For any security search or work resolving CVEs — including severity-filtered queries and the suggested-resolution diff attached to each entity — see [`security.md`](./security.md). The core tool is `get_cve_resolution_status` (the CVE inbox with `data.recommendedAction` carrying the ready-to-apply fix).

## Entity search

```bash
ctx-cli mcp call find_entities -p query="<search>" -o json
ctx-cli mcp call find_entities -p query="<search>" -p entityTypes='["Service"]' -o json
ctx-cli mcp call get_entity_by_id -p entityId=<entity-id> -o json
```
