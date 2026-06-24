---
name: ctx-onboarding
description: >
  Onboard a Context Engine tenant: confirm a model + embedder are configured, connect data
  sources (GitHub/GitLab/Jira/… repos + credentials) and ingest, then immediately show what
  CTX understood about each repo (what it is, stack, what it does, what it talks to) with a
  live semantic-search demo and an invitation to ask questions — and kick off the slower
  enrichment agents that build the service/dependency graph as a follow-on. Use for "set up
  / onboard / get started with CTX", "connect repos", or "what does CTX know about my system".
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# CTX onboarding

> **Prerequisites:** requires `ctx-cli` installed and authenticated against the target
> tenant. If it isn't, or you haven't run the once-per-session version check, see the
> [`ctx`](../ctx/SKILL.md) skill first — it's the single source of truth for install/auth.

The flow is: **check readiness → connect & ingest → show what CTX understood (fast) → deepen the graph (follow-on).**

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

# 3. Show what CTX read & understood (fast — this is the reveal)

The instant a repo finishes indexing (Step 2), CTX can already tell the user **what their
system is and does** — *without* waiting on the enrichment agents (Step 4), which are slow
and may not be seeded with the tier-1 composites on a fresh tenant. **You** (the agent
running this skill) produce this from the repo's own signal. For the first 1–2 ingested
repos:

**3a. Pull the essence (cheap, fast).**
- Composition + size from the `RepositoryStats` node (written *during* ingestion): its `data`
  JSON has `totalFiles`, `totalLines`, and a per-language breakdown (`name`/`files`/`code`).
  Find it via `find_entities` / `query_entities` for `RepositoryStats`.
- README + manifest (`package.json` / `go.mod` / `pyproject.toml` …) + the entry file, via
  code search (scope to the one data source):
  ```bash
  curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/code-search" \
    -d '{"query":"readme overview what this project does","limit":3,"dataSourceIds":["<ds-id>"]}'
  # also query: "dependencies manifest package.json", "main entry point"
  ```
  (Use the `code_search` MCP tool if it's listed; otherwise this REST endpoint — see
  [`ctx-search`](../ctx-search/SKILL.md).)

**3b. Write the precise profile** — in plain language, this is the "smart system" moment:
  - **What it is** — one or two sentences (*"an MCP server that gives an AI long-term memory
    via DuckDB"*).
  - **Type** ▸ service / library / CLI / MCP server / infra …
  - **Stack** ▸ languages + key frameworks/libs (from the manifest deps)
  - **Does** ▸ its main capabilities (from the README / entry file)
  - **Talks to** ▸ external systems (DBs, clouds, APIs, other services)
  - **Shape** ▸ N files · N lines · top languages (from `RepositoryStats`)

  **Drop generic metrics** — raw counts as a headline and code-complexity scores don't read
  as understanding; they read as noise.

**3c. One live semantic hit** — run a natural-language `code_search` and show it landing on
the right file. Proof CTX searches by *meaning*, not keywords:
```
  🔍 "how does it authenticate?"  →  src/auth/credential.ts:22   (sim 0.70)
```

**Render each repo as a compact card**, e.g.:
```
  📂 yonidavidson/brain-mcp
     What it is ▸ an MCP server giving an AI long-term memory (last 2 conversations in
                  DuckDB; local / S3 / GCS backends)
     Stack      ▸ TypeScript · DuckDB · OpenAI SDK · node-cron
     Does       ▸ exposes MCP tools to store/recall conversation context
     Talks to   ▸ OpenAI · DuckDB · S3 / GCS
     Shape      ▸ 6 files · 1.6k lines · TypeScript 72%
     🔍 "where is a memory persisted?"  →  src/index.ts:145
```

**3d. Offer questions.** Close by inviting the user to ask about their system, and answer
via [`ctx-search`](../ctx-search/SKILL.md) (`code_search` / `find_entities`). Suggest 3–5
grounded examples keyed to what you just profiled (*"what external services does X depend
on?"*, *"where would I add a new MCP tool?"*). That's the hand-off into everyday use — and
it's available now, not after the slow agents.

---

# 4. Deepen the graph — enrichment agents (follow-on, slower)

Step 3 gives per-repo understanding immediately. To answer **cross-service** questions
("what depends on X", blast radius, flows), the **service / dependency / flow graph** has to
be built by enrichment agents — run these as a *background follow-on*, not a gate on the
Step-3 reveal. (Requires the model from Step 1; if it's not configured these fail
`Not logged in`.)

```bash
# list available agents — pick the graph-builders
curl -s "${AUTH[@]}" "$CTX_API_URL/api/agent-kinds" \
  | jq -r '.[] | "\(.id)\t\(.name)"' | grep -E 'service-discovery|dependency|package-linker|runbook|team'

# trigger a run on a data source — input must be an object (or omitted), NOT a string
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/agent-runs" \
  -d '{"agentKindId":"<kind-id>","dataSourceId":"<ds-id>"}'      # → {id, status:"queued", workflowId}

curl -s "${AUTH[@]}" "$CTX_API_URL/api/agent-runs/<run-id>"      # status: queued|running|completed|failed (+ error)
```

Good builders from code sources: **`service-discovery-agent`**, then
**`service-dependency-deriver`** / **`service-package-linker`**. **They're slow** (multi-turn
LLM, minutes per repo) and **time out on large repos** — so kick them off and let the graph
fill in behind the Step-3 reveal; don't make the user wait on them. Surface failures plainly
(a `Not logged in` / token error → the agent model isn't usable, back to Step 1).

Once the graph is built, cross-service questions become answerable via
[`ctx-investigate`](../ctx-investigate/SKILL.md) (`investigate_service`, `blast_radius`,
`understand_flow`) and [`ctx-security`](../ctx-security/SKILL.md) (CVE / SAST inboxes). Until
then, stay on the Step-3 per-repo understanding rather than touring a bare service graph.

> **Tool availability is seed-dependent** — `ctx-cli mcp list` may lack `query_entities` /
> `investigate_service` / `code_search` (*"Tool not found"*). List first; for code search
> fall back to REST (`POST /api/code-search`); prefer the tools that *are* listed
> (`find_entities`, `traverse_edges`, `get_entity_by_id`).
