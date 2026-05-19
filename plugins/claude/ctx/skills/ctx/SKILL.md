---
name: ctx
description: >
  Query the Context Engine knowledge graph — investigate services, check blast
  radius, search entities, manage Jira/Linear issues, and assess change risk.
  Use when working with service architecture, dependencies, incidents, or
  project management.
allowed-tools: Bash(ctx-cli:*)
---

# Context Engine CLI

## Prerequisites

If `ctx-cli` is not installed, download it:
```bash
curl -fsSL https://github.com/tabnine/skills/releases/latest/download/ctx-cli-$(uname -s | tr A-Z a-z)-$(uname -m | sed 's/aarch64/arm64/;s/x86_64/x64/') -o /usr/local/bin/ctx-cli && chmod +x /usr/local/bin/ctx-cli
```

Set your API key:
```bash
export CTX_API_KEY=<your-key>
export CTX_API_URL=https://ctx.tabnine.com
```

## Stay current

Once per session — before your first `ctx-cli` call — run the snippet below. It's idempotent, network-silent within 24h, and never blocks. If `tabnine/skills` has a newer release than the local CLI, it prints one stderr line and exits cleanly; pass the hint through to the user and move on with the task. If the network is unreachable or the tag can't be parsed, the snippet stays silent (no false-positive nags).

State is cached at `~/.ctx/mcp-cache/version-check.json` (same dir as the MCP tool cache).

```bash
F=$HOME/.ctx/mcp-cache/version-check.json
NOW=$(date +%s); MT=$(stat -f %m "$F" 2>/dev/null || stat -c %Y "$F" 2>/dev/null || echo 0)
if [ ! -f "$F" ] || [ $((NOW-MT)) -ge 86400 ]; then
  mkdir -p "$(dirname "$F")"
  URL=$(curl -fsLI -o /dev/null -w '%{url_effective}' --max-time 8 https://github.com/tabnine/skills/releases/latest 2>/dev/null)
  case "$URL" in */releases/tag/v*) LATEST="${URL##*/tag/v}" ;; *) LATEST="" ;; esac
  LOCAL=$(ctx-cli --version 2>/dev/null)
  printf '{"checkedAt":"%s","latest":"%s","local":"%s"}\n' "$(date -u +%FT%TZ)" "$LATEST" "$LOCAL" > "$F"
  [ -n "$LATEST" ] && [ -n "$LOCAL" ] && [ "$LATEST" != "$LOCAL" ] && \
    echo "ℹ️  ctx-cli v$LATEST available (you have v$LOCAL). Upgrade: curl -fsSL https://github.com/tabnine/skills/releases/latest/download/ctx-cli-\$(uname -s | tr A-Z a-z)-\$(uname -m | sed 's/aarch64/arm64/;s/x86_64/x64/') -o /usr/local/bin/ctx-cli && chmod +x /usr/local/bin/ctx-cli" >&2
fi
```

## Quick start

```bash
# Investigate a service before making changes
ctx-cli mcp call investigate_service -p serviceName=auth-service -o json

# Check impact of a change
ctx-cli mcp call blast_radius -p target=payment-api -p changeType=breaking -o json

# Search the knowledge graph
ctx-cli mcp call find_entities -p query="authentication" -o json

# Get change confidence score
ctx-cli mcp call get_change_confidence -p files=src/auth.ts -o json
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

## Service investigation

```bash
ctx-cli mcp call investigate_service -p serviceName=<name> -o json
ctx-cli mcp call blast_radius -p target=<name> -p changeType=breaking -o json
ctx-cli mcp call get_service_dependencies -p serviceName=<name> -o json
ctx-cli mcp call get_service_dependents -p serviceName=<name> -o json
```

## Jira

```bash
ctx-cli mcp call get_jira_issue -p issueKey=ENG-123 -o json
ctx-cli mcp call create_jira_issue --json '{"summary":"Fix auth timeout","projectKey":"ENG","issueType":"Bug"}' -o json
ctx-cli mcp call transition_jira_issue -p issueKey=ENG-123 -p status="In Progress" -o json
```

## Incident response

```bash
ctx-cli mcp call incident_response -p serviceName=<name> -o json
ctx-cli mcp call get_incident_contacts -p serviceName=<name> -o json
```

## Entity search

```bash
ctx-cli mcp call find_entities -p query="<search>" -o json
ctx-cli mcp call find_entities -p query="<search>" -p entityTypes='["Service"]' -o json
ctx-cli mcp call get_entity_by_id -p entityId=<entity-id> -o json
```
