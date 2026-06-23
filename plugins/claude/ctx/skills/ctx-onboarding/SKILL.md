---
name: ctx-onboarding
description: >
  Onboard a Context Engine tenant — check an LLM/agent model and embedder are
  configured (guide the operator to set them in the UI if not), then connect data
  sources (GitHub/GitLab/Jira/… repos + credentials) and kick off ingestion, and
  finally tour what CTX knows (stats, graph, capability map). Use for "set up /
  onboard / get started with CTX", "add a data source / connect repos", or "what
  can CTX do for me / show me my graph".
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# CTX onboarding

> **Prerequisites:** requires `ctx-cli` installed and authenticated against the target
> tenant. If it isn't, or you haven't run the once-per-session version check, see the
> [`ctx`](../ctx/SKILL.md) skill first — it's the single source of truth for install/auth.

Three steps, in order:

1. **Readiness check (read-only)** — verify a **model** (the agent LLM) and an **embedder**
   are configured. These are **operator/Solutions-Engineer tasks done in the CTX web UI**
   (provider + cloud credentials — Vertex/Bedrock/keys; fiddly and environment-specific), so
   the skill **does not set them** — it detects what's missing and tells the user to
   configure it.
2. **Connect data sources (the skill does this)** — create credentials + data sources
   (GitHub repos and the like) and start ingestion. This is the repetitive connect-the-repos
   work worth automating. Confirm before each write; never echo secrets.
3. **Show the value & assist (read-only)** — tour stats, graph, capability map; route the
   user's questions into the sibling skills.

## How to drive the API

All calls use the same `$CTX_API_URL` / `$CTX_API_KEY` the CLI uses.

```bash
# ctx-native key (ctx_...): Authorization: Bearer (or X-API-Key) both work
AUTH=(-H "Authorization: Bearer $CTX_API_KEY")
# Tabnine PAT (t9u_...): add the x-auth-type header
# AUTH=(-H "Authorization: Bearer $CTX_API_KEY" -H "x-auth-type: tabnine")
```

**Write rules (Part 2 only):** read current state first (idempotent, resumable); **confirm
the exact payload before any POST**; and **never echo secrets** — credentials never return
their `data`, and `GET /api/runner-environments` *does* echo `envVars` (show only
`name`/`provider`/`isActive`, never `envVars`).

---

# Part 1 — Readiness check (read-only)

Run these reads, give a short ✓/✗ **readiness report**, and for each ✗ point the user at the
**web UI → Settings** (don't configure the model/embedder from here).

## 1. Preflight

```bash
curl -s -o /dev/null -w '%{http_code}\n' "${AUTH[@]}" "$CTX_API_URL/api/ai-settings/status"
```

`200` → continue. `401/403` → key wrong / missing `x-auth-type` (for `t9u_`) — see
[`ctx`](../ctx/SKILL.md). Refused → wrong URL / API down.

## 2. Model (agent LLM)

The agent runtime (Claude Code) runs on the **active runner environment**. Without it,
**every agent run fails** (`Not logged in · Please run /login`) — so no enrichment, no
service/dependency graph.

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/runner-environments"   # array; any "isActive": true?
curl -s "${AUTH[@]}" "$CTX_API_URL/api/ai-settings/status"    # .runnerEnvironment (provider/active)
```

- Any `isActive: true` → ✓ (report `name`/`provider` only — not `envVars`).
- None / empty → ✗ **No agent model.** Tell the user to configure it in **web UI → Settings
  → AI / Runner config** (provider + cloud credentials). Until then, agent runs / graph
  enrichment are unavailable.

## 3. Embedder

Powers **semantic search** (`find_entities`) and **code search**. Optional, but most value
tours rely on it.

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/embedding-models/active"   # {scopes:{entities:{modelId,…},…}}
curl -s "${AUTH[@]}" "$CTX_API_URL/api/embedding-models"          # {models:[…]}
```

`/active` always returns a model per scope, but `modelId: "default"` means the built-in
default with **no key wired** (not usable). So:

- Any scope `modelId !== "default"`, or `models[]` non-empty → ✓.
- All `"default"` / empty → probe `ctx-cli mcp call find_entities -p query=test -p limit=1`.
  A 500 *"Semantic search is not available. Configure an OpenAI API key."* → ✗ **No
  embedder.** Tell the user to store an OpenAI key (or configure an embedding model) in
  **web UI → Settings → Embeddings / Credentials**.

Report the result. The model ✗ blocks enrichment; the embedder ✗ blocks search — but you can
still connect data sources (Part 2) regardless (structural ingestion doesn't need either;
code-search embeddings just won't populate until the embedder is set).

---

# Part 2 — Connect data sources

This is the part the skill **does**. Read existing state first and skip anything already
present (safe to re-run). Confirm each write; never echo the tokens.

## 2a. Credentials

Enumerate supported types, then create only what's needed. **Secrets go in `data`; the API
never returns them.**

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/credentials/meta/types"   # JSON array: [{type,label,description,fields:[{name,label,type,required}]}]
curl -s "${AUTH[@]}" "$CTX_API_URL/api/credentials"              # existing creds (id/name/type/host — NO data)
```

Create with `{name, type, data:{…}, host?}` (`host` required when the type's
`hostRequired:true`, e.g. Atlassian/ServiceNow):

```bash
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/credentials" \
  -d '{"name":"GitHub PAT","type":"github_pat","data":{"token":"ghp_..."}}'
#   → {id,name,type,host,createdAt}  (no data) — keep the id for 2b
```

Common `type` → `data`: `github_pat`/`gitlab_pat` → `{token}`; `bitbucket_app_password` →
`{username,appPassword}`; `atlassian_api_token` (Jira/Confluence, host required) →
`{email,apiToken}`; `servicenow_basic_auth` → `{username,password}`. Trust each type's
`fields[]` from `meta/types` for the exact inputs.

## 2b. Data sources (e.g. GitHub repos)

A data source **binds to its credential via `config.credentialId`**, and the credential type
must match the source type. The match is **not** enforced at create (a mismatch still returns
`201`); it surfaces at **sync** as `Credential type mismatch`. Pair them per this mapping:

| source `type` | required credential `type` |
|---|---|
| `github`, `github_actions` | `github_pat` |
| `gitlab` | `gitlab_pat` |
| `bitbucket` | `bitbucket_app_password` |
| `jira`, `confluence` | `atlassian_api_token` |
| `servicenow` | `servicenow_basic_auth` |
| `jfrog_artifactory`, `jfrog_xray` | `jfrog_access_token` |

For **GitHub**, discover an org/user's repos (takes the credential id) so the user can pick
which to connect — and to bulk-create them:

```bash
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/data-sources/discover" \
  -d '{"credentialId":"<cred-id>","owner":"my-org"}'
#   → {repositories:[{fullName,url,private,alreadyConnected}]} — skip alreadyConnected:true
```

Create each source. For **GitHub** the `config` needs `owner`, `repo`, **and a non-empty
`events` array** (`push`/`pull_request`/`issues`/`release`/`package.published`/
`package.deleted`) — omitting `events` fails validation (`expected array, received
undefined`). Other providers differ (Jira → `projectKey`, etc.); the `config` is validated by
a per-type Zod schema, so confirm an unfamiliar provider's shape from an existing source via
`GET /api/data-sources`:

```bash
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/data-sources" \
  -d '{"name":"ctx repo","type":"github","config":{"credentialId":"<cred-id>","owner":"codota","repo":"ctx","events":["push","pull_request"]}}'
#   → full data source incl. id, enabled:true
```

When connecting many repos, loop over the `discover` results (confirm the set with the user
first), creating one source each — that bulk connect is the whole point of automating this.

## 2c. Kick off ingestion & verify

```bash
curl -s "${AUTH[@]}" -X POST "$CTX_API_URL/api/data-sources/<id>/sync"
```

> **Verify by data, not just sync-status.** On a freshly-created source the analysis runs on
> an **immediate** path: `POST .../sync` may return nulls and `sync-status` can stay
> `state:null` even while ingestion succeeds. Confirm landing by the **data**:
> `GET /api/code-search/status` shows the repo `completed` with `embeddedChunks` climbing to
> `totalChunks`; `GET /api/processing/status` `stats`; and `find_entities` returns the repo.
> A small repo (or a cell without the LSP analyzer / agent enrichment) yields
> `Repository` + code chunks but a **sparse edge graph** — the rich service/dependency graph
> needs the agent model (Part 1 #2) and enrichment agents to run.

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/code-search/status"                 # per-source embeddedChunks/totalChunks
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-source-health/stats/summary"   # totalSources, successRate, …
```

---

# Part 3 — Show the value & assist

Once data exists, tour what CTX knows. Don't dump raw rows — show the connected picture.
This part **routes into the sibling skills** rather than duplicating them.

> **Tool availability is seed-dependent.** A tenant may expose only a subset of the catalog
> — `ctx-cli mcp list` can lack `query_entities`, `investigate_service`, even `code_search`
> (*"Tool not found"*). Run `ctx-cli mcp list` / `--tier all` to see what's there, fall back
> to REST for code search (`POST /api/code-search` — see [`ctx-search`](../ctx-search/SKILL.md)),
> and prefer the tools that *are* listed (`find_entities`, `traverse_edges`, `get_entity_by_id`).

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
> point to running enrichment agents rather than touring two nodes.

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
[`ctx-investigate`](../ctx-investigate/SKILL.md) / [`ctx-security`](../ctx-security/SKILL.md).
