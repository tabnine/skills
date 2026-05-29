---
name: ctx
description: >
  Query the Context Engine knowledge graph — semantic + lexical search, graph
  adjacency traversal, and CVE triage/resolution. Use when searching the
  codebase or graph, exploring what an entity is connected to, or working on
  security issues.
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

Configure the API URL and credentials. ctx-cli reads these from environment variables and/or a config file at `~/.ctx/config.yaml`. Env vars override config when both are set.

**ctx-native API key (`ctx_...`) — env-only works:**
```bash
export CTX_API_URL=https://ctx.tabnine.com
export CTX_API_KEY=ctx_...
```

**Tabnine PAT (`t9u_...`) — requires config.yaml for the `x-auth-type` header:**

The token itself can come from env (`TABNINE_TOKEN` or `CTX_TOKEN`) or from config, but custom headers can only be set in config — ctx-cli has no env var that maps to headers. So Tabnine PATs need at least one `ctx-cli config set-header` call.

```bash
ctx-cli config init                                  # interactive: prompts for url + key
ctx-cli config set api_url https://ctx.tabnine.com   # or set fields individually
ctx-cli config set api_key t9u_...
ctx-cli config set-header x-auth-type tabnine        # required for Tabnine PATs
```

Env vars ctx-cli recognizes (checked in this order for the bearer token): `CTX_API_KEY` → `TABNINE_TOKEN` → `CTX_TOKEN`. Plus `CTX_API_URL` for the URL.

Inspect or manage profiles:
```bash
ctx-cli config list                  # show profiles, active profile, masked secrets
ctx-cli config use-profile <name>    # switch active profile
ctx-cli config remove-header <key>   # remove a stored header
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

## Pick a tool by intent

Prefer a **composite (tier-1)** tool when one matches your intent — it bundles several primitive calls into one. Drop to primitives only when no composite covers the question or you need a specific narrow slice.

| Intent | Tool | Tier | Notes |
|---|---|---|---|
| "How does service X work / what does it depend on / who owns it?" | `investigate_service -p serviceName=<name>` | tier-1 | Returns service, deps, dependents, ownership (team/oncall/slack/pagerduty), ADRs, runbooks, flows, incidents, Jira/GitLab issues in one call. Supports partial name match. |
| "What breaks if I change X?" | `blast_radius -p target=<name>` | tier-1 | Param is `target` (not `serviceName`). Returns risk score (LOW/MEDIUM/HIGH), transitive dependents, affected flows, teams-to-notify, recommendations. |
| "We're seeing errors in X — runbook + escalation" | `incident_response -p service=<name>` | tier-1 | Param is `service` (not `serviceName`). Optional `symptom=<text>` finds similar past incidents. |
| "Is package X safe / should I use it?" | `dependency_check -p packageName=<name>` | tier-1 | Vulnerabilities + upgrade history + migration examples. Returns `[]` on tenants where package data isn't indexed. |
| "How do I migrate from X to Y?" | `code_migration -p fromPackage=<pkg> -p toPackage=<pkg>` | tier-1 | Params are `fromPackage` / `toPackage`. Migration status, examples from teams who've done it. |
| "How does the <X> business flow work?" | `understand_flow -p flowName=<name>` | tier-1 | Flow steps, services involved, related ADRs and incidents. Returns `[]` on tenants without indexed flows. |
| "What's the context for this file?" | `get_file_context -p filepath=<path>` | tier-1 | Param is `filepath` (one word, lowercase). Returns ADRs, incidents, security patterns, experts, blast radius for the file's service. **Requires** `git-insights-analyzer` to have run on the repo — returns `[]` on tenants where it hasn't. |
| "List CVEs with suggested fixes" | `get_cve_resolution_status` | tier-2 | The CVE inbox; `data.recommendedAction` carries the diff or advisory. See [`security.md`](./security.md). |
| Find entities by natural-language query | `find_entities -p query=<text>` | tier-2 | Starting point for graph exploration. See [`codebase-search.md`](./codebase-search.md). |
| Walk relationships from an entity | `traverse_edges -p entityId=<id>` | tier-2 | After `find_entities`. See [`codebase-search.md`](./codebase-search.md). |

## Quick start

```bash
# One-call investigation of a service
ctx-cli mcp call investigate_service -p serviceName="CTX API Server" -o json

# Semantic search across the graph (when no composite matches your intent)
ctx-cli mcp call find_entities -p query="authentication service" -o json
```

## Discover tools

```bash
# Default list = tier-1 composites only (25 tools — the curated entry points)
ctx-cli mcp list -o json

# Full list including tier-2 primitives (~130 tools — graph queries, semantic_*,
# data-source mutators, etc.). Use this when nothing in tier-1 matches the intent.
ctx-cli mcp list --tier all -o json

# Filter by keyword (across both tiers)
ctx-cli mcp list --tier all -s jira -o json

# See a tool's parameters before calling — check this whenever a call errors,
# because some params disagree with intuitive naming (see "Common parameter gotchas" below).
ctx-cli mcp describe <tool-name>
```

### Common parameter gotchas

These have bitten real callers — `mcp describe` lists them but they're easy to miss:

- `get_entity_by_id` takes `entityId` (not `id`). Result is always an `array` (length 0 or 1), even though the docstring says it returns a single entity.
- `blast_radius` takes `target` (not `serviceName`).
- `incident_response` takes `service` (not `serviceName`). `investigate_service` does take `serviceName` — the inconsistency is real.
- `code_migration` takes `fromPackage` and `toPackage` (not `from` / `to`).
- `get_file_context` / `resolve_file_to_service` take `filepath` (one word, lowercase — not `filePath`).
- `find_entities` and `search_knowledge` both take `entityTypes` as a **JSON-array string** (`'entityTypes=["Service"]'`) — despite `mcp describe` claiming comma-separated for `search_knowledge`. The comma form 500s.
- `query_entities` takes `entityType` (singular) and `namePattern` as a **regex** (despite `mcp describe` advertising `*` wildcards). `*API*` → 500; `.*API.*` → works.

## Codebase search

For searching the knowledge graph and the code it indexes — semantic queries, lexical lookups by type, adjacency, and the two-service connection pattern — see [`codebase-search.md`](./codebase-search.md). The standard loop is `find_entities` → `traverse_edges` → `get_entity_by_id`.

## Security & CVEs

For any security search or work resolving CVEs — including severity-filtered queries and the suggested-resolution diff attached to each entity — see [`security.md`](./security.md). The core tool is `get_cve_resolution_status` (the CVE inbox with `data.recommendedAction` carrying the ready-to-apply fix).
