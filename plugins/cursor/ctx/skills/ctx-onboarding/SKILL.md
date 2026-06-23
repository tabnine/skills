---
name: ctx-onboarding
description: >
  Onboard a Context Engine tenant: confirm a model + embedder are configured, then
  connect data sources (GitHub/GitLab/Jira/… repos + credentials) and start ingestion,
  run the enrichment agents that build the service/dependency graph, and report stats
  on what CTX now knows. Use for "set up / onboard / get started with CTX", "connect
  repos and build the graph", or "what does CTX know about my system".
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# CTX onboarding

> **Prerequisites:** requires `ctx-cli` installed and authenticated against the target
> tenant. If it isn't, or you haven't run the once-per-session version check, see the
> [`ctx`](../ctx/SKILL.md) skill first — it's the single source of truth for install/auth.

The flow is: **check readiness → connect data sources → run enrichment agents → stats.**

The **model (agent LLM) and embedder are configured by the operator in the CTX web UI**
(provider + cloud credentials — Vertex/Bedrock/keys; environment-specific), so the skill
**checks** them but does not set them. Everything else — connecting repos, ingesting,
running the agents that build the graph, and reporting what landed — the skill does.

```bash
# Auth (same key the CLI uses). ctx_ key: Bearer or X-API-Key. t9u_ PAT: add x-auth-type.
AUTH=(-H "Authorization: Bearer $CTX_API_KEY")
# AUTH=(-H "Authorization: Bearer $CTX_API_KEY" -H "x-auth-type: tabnine")
```

**Write rules:** read current state first (idempotent / resumable); confirm before each
POST; never echo secrets (credentials never return `data`; `runner-environments` echoes
`envVars` — show only `name`/`provider`/`isActive`).

---

# 1. Check readiness (model + embedder)

Read-only. Verify the two operator-configured prerequisites; if either is missing, tell the
user to set it in the **web UI → Settings** and stop there for that capability.

```bash
curl -s -o /dev/null -w '%{http_code}\n' "${AUTH[@]}" "$CTX_API_URL/api/ai-settings/status"   # 200 = reachable
curl -s "${AUTH[@]}" "$CTX_API_URL/api/runner-environments"        # any "isActive": true ? (the agent model)
curl -s "${AUTH[@]}" "$CTX_API_URL/api/embedding-models/active"    # any scope modelId != "default" ? (the embedder)
```

- **Model (agent LLM):** no active runner environment → **agents can't run** (they fail
  `Not logged in · Please run /login`). Step 3 needs this. → "configure it in Settings → AI."
- **Embedder:** all scopes `modelId:"default"` (and `find_entities` 500s with *"Semantic
  search is not available"*) → no embedder; **code/semantic search won't work**. → "store an
  OpenAI key in Settings." (Structural ingestion in Step 2 still works without it.)

Report a one-line readiness verdict, then proceed with whatever is available.

---

# 2. Connect data sources & ingest

Create the credentials and data sources, then sync. Read existing state first and skip
anything already connected.

```bash
# credential types + existing creds/sources
curl -s "${AUTH[@]}" "$CTX_API_URL/api/credentials/meta/types"   # [{type,label,description,fields:[{name,label,type,required}]}]
curl -s "${AUTH[@]}" "$CTX_API_URL/api/credentials"              # existing (id/name/type/host — NO data)
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-sources"             # existing sources

# 2a. credential (secrets in data, never echoed back)
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/credentials" \
  -d '{"name":"GitHub PAT","type":"github_pat","data":{"token":"ghp_..."}}'   # → {id,...} (no data)

# 2b. discover repos for an org (GitHub) — for bulk-connect; skip alreadyConnected:true
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/data-sources/discover" \
  -d '{"credentialId":"<cred-id>","owner":"my-org"}'             # → {repositories:[{fullName,private,alreadyConnected}]}

# 2c. create source — GitHub config needs owner+repo AND a non-empty events array
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/data-sources" \
  -d '{"name":"ctx","type":"github","config":{"credentialId":"<cred-id>","owner":"codota","repo":"ctx","events":["push","pull_request"]}}'

# 2d. sync
curl -s "${AUTH[@]}" -X POST "$CTX_API_URL/api/data-sources/<id>/sync"
```

Credential type must match the source type (`github`→`github_pat`, `gitlab`→`gitlab_pat`,
`jira`/`confluence`→`atlassian_api_token`, `servicenow`→`servicenow_basic_auth`,
`bitbucket`→`bitbucket_app_password`, `jfrog_*`→`jfrog_access_token`) — the mismatch is
caught at sync (`Credential type mismatch`), not create. Bulk-connect by looping over the
`discover` results (confirm the set first). Omitting GitHub `events` fails validation
(`expected array, received undefined`); unfamiliar providers — confirm `config` shape from
an existing source via `GET /api/data-sources`.

**Verify by data, not sync-status** (which can stay `null` on the immediate-analysis path):

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/code-search/status"   # per-source embeddedChunks/totalChunks → "completed"
```

---

# 3. Run enrichment agents (build the graph)

Ingestion alone yields mostly `Repository` nodes. The **service/dependency/flow graph is
built by agents** — run them on the connected sources. (Requires the model from Step 1; if
it's not configured these fail `Not logged in`.)

```bash
# list available agents (92 kinds) — pick the graph-builders
curl -s "${AUTH[@]}" "$CTX_API_URL/api/agent-kinds" \
  | jq -r '.[] | "\(.id)\t\(.name)"' | grep -E 'service-discovery|dependency|package-linker|runbook|team'

# trigger a run on a data source — input must be an object (or omitted), NOT a string
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/agent-runs" \
  -d '{"agentKindId":"<kind-id>","dataSourceId":"<ds-id>"}'      # → {id, status:"queued", workflowId}

# poll until terminal
curl -s "${AUTH[@]}" "$CTX_API_URL/api/agent-runs/<run-id>"      # status: queued|running|completed|failed (+ error)
```

Good first agents to build the graph from code sources: **`service-discovery-agent`**, then
**`service-dependency-deriver`** / **`service-package-linker`**. Run the relevant ones per
data source, poll each to `completed`, and surface failures plainly (a `Not logged in` /
token error means the agent model isn't configured/usable — back to Step 1).

---

# 4. Stats — what CTX now knows

Report what the ingestion + agents produced.

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/processing/status"                  # totalSynced, totalProcessed, errors
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-source-health/stats/by-source" # per-source counts + health
# entity counts by type (use a tool that's actually listed — see note):
ctx-cli mcp call find_entities -p query="service" -p limit=50 -o json
```

Summarize: sources connected, code indexed (chunks), **entity counts by type** (services,
dependencies, flows, CVEs from the agent runs), and per-source health. **Be honest if the
graph is bare** — if it's mostly `Repository` nodes, the enrichment agents (Step 3) haven't
run/succeeded; say so rather than dressing up two nodes.

From here the tenant is queryable — hand off to the sibling skills:
[`ctx-search`](../ctx-search/SKILL.md) (find code/entities),
[`ctx-investigate`](../ctx-investigate/SKILL.md) (`investigate_service`, blast radius,
incident response), [`ctx-security`](../ctx-security/SKILL.md) (CVE/SAST inboxes).

> **Tool availability is seed-dependent** — `ctx-cli mcp list` may lack `query_entities` /
> `investigate_service` / `code_search` (*"Tool not found"*). List first; for code search
> fall back to REST (`POST /api/code-search`); prefer the tools that *are* listed
> (`find_entities`, `traverse_edges`, `get_entity_by_id`).
