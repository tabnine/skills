---
name: ctx-onboarding
description: >
  Check a Context Engine tenant is ready and show its value — verify an LLM/agent
  model and an embedder are configured (and tell the operator what to configure if
  not), then tour what CTX knows (stats, graph, capability map). Read-only: it
  diagnoses and guides, it does NOT change configuration. Use for "is CTX set up /
  ready", "get started with CTX", "what can CTX do for me / show me my graph".
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# CTX readiness & value tour

> **Prerequisites:** requires `ctx-cli` installed and authenticated against the target
> tenant. If it isn't, or you haven't run the once-per-session version check, see the
> [`ctx`](../ctx/SKILL.md) skill first — it's the single source of truth for install/auth.

This skill onboards a user onto an existing Context Engine tenant in two read-only steps:

1. **Readiness check** — verify the tenant is actually usable: a **model** (the agent
   LLM) and an **embedder** are configured, and there's data. Where something is missing,
   **tell the user what to configure** — don't configure it here.
2. **Show the value & assist** — once it's ready and data exists, tour what CTX knows
   (stats, graph, capability map) and route the user's questions into the sibling skills.

**This skill does not change configuration.** Provisioning the LLM, embedder, credentials
and data sources is an operator/Solutions-Engineer task done in the **CTX web UI
(Settings)** — it's fiddly and environment-specific (Vertex/Bedrock auth, keys), so the
skill's job is to *detect* what's set up and *guide*, not to POST config. Every call below
is a `GET` (reads); never POST/PATCH from this skill.

## How to read the API

All checks use the same `$CTX_API_URL` / `$CTX_API_KEY` the CLI uses.

```bash
# ctx-native key (ctx_...): Authorization: Bearer (or X-API-Key) both work
AUTH=(-H "Authorization: Bearer $CTX_API_KEY")
# Tabnine PAT (t9u_...): add the x-auth-type header
# AUTH=(-H "Authorization: Bearer $CTX_API_KEY" -H "x-auth-type: tabnine")
```

When you read config back, **never print secrets.** Credentials never return their `data`,
but note `GET /api/runner-environments` **does** echo `envVars` (incl. keys) in plaintext —
show only `name`/`provider`/`isActive` from it, never `envVars`.

---

# Part 1 — Readiness check

Run these reads, then give the user a short **readiness report** (✓ / ✗ per item) and, for
each ✗, a one-line "configure this in the CTX web UI → Settings" pointer.

## 1. Preflight — can we reach the tenant?

```bash
curl -s -o /dev/null -w '%{http_code}\n' "${AUTH[@]}" "$CTX_API_URL/api/ai-settings/status"
```

`200` → continue. `401/403` → key wrong or missing the `x-auth-type` header (for `t9u_`
tokens) — see the [`ctx`](../ctx/SKILL.md) skill. Connection refused → wrong URL / API down.

## 2. Model (agent LLM) — is one configured?

The agent runtime (Claude Code) runs on the **active runner environment**. Without it,
**every agent run fails** (`Not logged in · Please run /login`) — so no enrichment, no
service/dependency graph.

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/runner-environments"     # array; is any "isActive": true?
curl -s "${AUTH[@]}" "$CTX_API_URL/api/ai-settings/status"      # .runnerEnvironment summary (provider/active)
```

- **Any `isActive: true`** → ✓ a model is configured (report `name`/`provider` — not `envVars`).
- **None active / empty** → ✗ **No agent model configured.** Tell the user: configure it in
  the **web UI → Settings → AI / Runner config** (provider + credentials: Anthropic key,
  GCP Vertex, AWS Bedrock, OpenAI, …). This needs real cloud credentials, which is why it's
  an operator step. Agent runs and graph enrichment stay unavailable until it's set.

## 3. Embedder — is one configured?

The embedder powers **semantic search** (`find_entities`) and **code search**. It's
optional — skip if the tenant doesn't need vectors — but most value tours rely on it.

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/embedding-models/active"   # {scopes:{entities:{modelId,provider,dimensions},…}}
curl -s "${AUTH[@]}" "$CTX_API_URL/api/embedding-models"          # {models:[…]}
```

`/active` **always** returns a model per scope, but a scope whose `modelId` is the literal
`"default"` means the **built-in default with no key wired** — not actually usable. So:

- **Any scope with `modelId !== "default"`, or `models[]` non-empty** → ✓ a real embedder
  is configured.
- **All scopes `"default"` and `models[]` empty** → likely ✗. Confirm by probing semantic
  search: `ctx-cli mcp call find_entities -p query=test -p limit=1`. If it 500s with
  *"Semantic search is not available. Configure an OpenAI API key."* → ✗ **No embedder.**
  Tell the user: store an OpenAI key (or configure an embedding model) in the **web UI →
  Settings → Embeddings / Credentials**. Until then, semantic + code search won't work.

## 4. Data — is anything ingested?

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-sources"                       # array of sources (or [])
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-source-health/stats/summary"   # totalSources, successRate, …
curl -s "${AUTH[@]}" "$CTX_API_URL/api/code-search/status"                 # available, totalChunks, per-source status
```

- **Sources present + ingested** (`totalSources>0`, code-search `completed`) → ✓.
- **No sources / nothing ingested** → ✗ **No data yet.** Tell the user: add data sources
  (GitHub/GitLab/Jira/Slack/PagerDuty/…) in the **web UI → Data Sources** and let them sync.
  There's nothing to tour until data lands.

## Readiness report

Summarize plainly, e.g.:

```
CTX readiness for <tenant>:
  ✓ Reachable
  ✓ Model (agent LLM): gcp_vertex (active)
  ✗ Embedder: not configured → Settings → Embeddings (store an OpenAI key)
  ✓ Data: 3 sources, code search indexed (1,958 chunks)
→ Configure the embedder, then re-run me for the value tour.
```

If model + (embedder, if wanted) + data are all ✓ → go to Part 2.

---

# Part 2 — Show the value & assist

Once it's ready, tour what CTX knows. Don't dump raw rows — show the connected picture.
This part **routes into the sibling skills** rather than duplicating them.

> **Tool availability is seed-dependent.** A tenant may expose only a subset of the catalog
> — `ctx-cli mcp list` can lack `query_entities`, `investigate_service`, even `code_search`
> (*"Tool not found"*). Run `ctx-cli mcp list` / `--tier all` to see what's actually there,
> fall back to REST for code search (`POST /api/code-search` — see
> [`ctx-search`](../ctx-search/SKILL.md)), and prefer the tools that *are* listed
> (`find_entities`, `traverse_edges`, `get_entity_by_id`).

## Statistics — what CTX knows

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/processing/status"                  # totalSynced, totalProcessed, errors
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-source-health/stats/by-source" # per-source health + counts
```

Summarize entity counts by type, services, repositories, dependencies, flows, CVEs, and
what's still syncing.

> **Be honest about a bare graph.** Raw code ingestion alone yields mostly `Repository` /
> `RepositoryStats` nodes — the rich graph (services, dependencies, flows, ownership) is
> built by **enrichment agents**, which need the agent model (Part 1 #2) *and* the analysis
> pipeline running. If the graph is just repo nodes, **say so** ("repos + code search are
> indexed, but the service/dependency graph isn't built yet — that needs agent runs"), and
> point to running enrichment agents rather than performing a tour of two nodes.

## Tour the context graph

Walk a few high-value entities and their relationships via
[`ctx-search`](../ctx-search/SKILL.md) (`find_entities` → `traverse_edges`) and
[`ctx-investigate`](../ctx-investigate/SKILL.md) (`investigate_service`). Pick 1–2 real
services and show what they connect to — "look, it's connected," not a table.

## Capability map — "what can be done"

Present a concise menu keyed to the tier-1 composites, grounded in *their* entities, each
pointing at the skill that owns it. Fill the `<…>` from real names you saw:

| Ask me… | Tool | Skill |
|---|---|---|
| "How does `<service>` work / what depends on it / who owns it?" | `investigate_service` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "What breaks if I change `<service>`?" | `blast_radius` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "We're seeing errors in `<service>` — runbook + escalation" | `incident_response` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "Is package `<pkg>` safe? / migrate `<x>`→`<y>`" | `dependency_check` / `code_migration` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "How does the `<flow>` flow work?" | `understand_flow` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "Where is `<thing>` implemented?" | `code_search` | [`ctx-search`](../ctx-search/SKILL.md) |
| "List CVEs / SAST findings with suggested fixes" | `get_cve_resolution_status` | [`ctx-security`](../ctx-security/SKILL.md) |

## First skills (security, SRE) & generic assist

Point at the starter workflows — **explain the opt-in gates, don't flip anything:**

- **Security / CVE auto-remediation** — once a scanner source (Snyk/Checkmarx) + a Git
  source are ingesting, the CVE inbox ([`ctx-security`](../ctx-security/SKILL.md)) carries
  ready-to-apply fix diffs. Auto-remediation (auto-PRs) is a deliberate opt-in.
- **SRE / incident response** — with a PagerDuty/Opsgenie or alert source plus the service
  graph, `incident_response` returns runbooks + escalation.

Then default into "show me what I can do here": answer the user's own questions against the
live graph by routing into [`ctx-search`](../ctx-search/SKILL.md) /
[`ctx-investigate`](../ctx-investigate/SKILL.md) / [`ctx-security`](../ctx-security/SKILL.md)
— value on *their* real data.
