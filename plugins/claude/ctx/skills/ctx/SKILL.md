---
name: ctx
description: >
  Set up and route Context Engine CLI (ctx-cli) work — install, authenticate,
  check version, discover tools, and pick the right tool by intent. Start here
  for anything involving ctx-cli or the Context Engine; it routes to the
  ctx-onboarding, ctx-search, ctx-security, ctx-guidelines, and ctx-investigate skills.
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# Context Engine CLI

This is the **foundational** skill for `ctx-cli`: install, auth, version-check, tool
discovery, and routing. The domain work lives in sibling skills — load the one that
matches your intent:

- **[`ctx-search`](../ctx-search/SKILL.md)** — find source code (`code_search`), find entities by natural language, and traverse graph relationships.
- **[`ctx-security`](../ctx-security/SKILL.md)** — CVE + SAST resolution inboxes with ready-to-apply fix diffs.
- **[`ctx-guidelines`](../ctx-guidelines/SKILL.md)** — managed coaching guidelines + discovered AI-guideline files (coverage / drift).
- **[`ctx-investigate`](../ctx-investigate/SKILL.md)** — service investigation, blast radius, incident response, dependency/migration checks, flow understanding.
- **[`ctx-onboarding`](../ctx-onboarding/SKILL.md)** — check a tenant is ready (agent model + embedder configured), guide the operator to configure anything missing, then tour what it knows (stats, graph, capability map). Read-only. Start here to get oriented on a tenant.

The install/auth/version-check steps below are the **single source of truth** — domain
skills point back here rather than duplicating them.

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

Prefer a **composite (tier-1)** tool when one matches your intent — it bundles several primitive calls into one. Drop to primitives only when no composite covers the question or you need a specific narrow slice. The rightmost column points to the skill that documents the tool in depth.

| Intent | Tool | Tier | Skill |
|---|---|---|---|
| "How does service X work / what does it depend on / who owns it?" | `investigate_service -p serviceName=<name>` | tier-1 | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "What breaks if I change X?" | `blast_radius -p target=<name>` | tier-1 | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "We're seeing errors in X — runbook + escalation" | `incident_response -p service=<name>` | tier-1 | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "Is package X safe / should I use it?" | `dependency_check -p packageName=<name>` | tier-1 | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "How do I migrate from X to Y?" | `code_migration -p fromPackage=<pkg> -p toPackage=<pkg>` | tier-1 | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "How does the <X> business flow work?" | `understand_flow -p flowName=<name>` | tier-1 | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "What's the context for this file?" | `get_file_context -p filepath=<path>` | tier-1 | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| **Find the code that does X / where is X implemented** | `code_search -p query=<text>` | tier-2 | [`ctx-search`](../ctx-search/SKILL.md) |
| Find entities by natural-language query | `find_entities -p query=<text>` | tier-2 | [`ctx-search`](../ctx-search/SKILL.md) |
| Walk relationships from an entity | `traverse_edges -p entityId=<id>` | tier-2 | [`ctx-search`](../ctx-search/SKILL.md) |
| "List CVEs / SAST findings with suggested fixes" | `get_cve_resolution_status` / `get_sast_resolution_status` | tier-2 | [`ctx-security`](../ctx-security/SKILL.md) |
| "What are our team's coding standards / does this code follow them?" | `get_coding_guidelines` | tier-2 | [`ctx-guidelines`](../ctx-guidelines/SKILL.md) |
| "Which repos have/lack a CLAUDE.md / .cursorrules — do they diverge?" | `get_guideline_sources` | tier-2 | [`ctx-guidelines`](../ctx-guidelines/SKILL.md) |
| **Is CTX ready / get started / "what can it do for me / show me my graph"** | _readiness check + value tour_ | — | [`ctx-onboarding`](../ctx-onboarding/SKILL.md) |

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
