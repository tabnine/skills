---
name: ctx-onboarding
description: >
  Onboard a brand-new Context Engine tenant end-to-end — guided, resumable setup
  (LLM provider → embedder → credentials → data sources → ingestion) and then a
  show-the-value tour (stats, graph tour, capability map, first skills). Use for
  "set up / onboard / get started with CTX", "configure the LLM / add a data
  source", or "what can CTX do for me / show me my graph".
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# CTX onboarding

> **Prerequisites:** requires `ctx-cli` installed and authenticated against the target
> tenant. If it isn't, or you haven't run the once-per-session version check, see the
> [`ctx`](../ctx/SKILL.md) skill first — it's the single source of truth for install/auth.

This skill takes a fresh tenant (or one a Solutions Engineer is standing up for a
customer) from an **empty system** to a **working, value-demonstrating** Context Engine,
then keeps assisting. It has two arcs:

1. **Set it up** — make the system actually work: LLM → embedder → credentials → data
   sources → ingestion. A resumable, idempotent checklist (Arc 1 below).
2. **Show the value & assist** — once data exists, flip from configurator to guide:
   stats, graph tour, capability map, first skills, then generic assist (Arc 2 below).

This is the **setup + guided-tour layer** that runs *before* there's anything in the
graph to query, and hands off to [`ctx-search`](../ctx-search/SKILL.md) /
[`ctx-investigate`](../ctx-investigate/SKILL.md) / [`ctx-security`](../ctx-security/SKILL.md)
once data lands. It does **not** re-implement those query tools — Arc 2 routes into them.

## How to drive the API

Arc 1 configures the tenant via the **CTX REST API** (the setup writes have no MCP tools
yet); Arc 2 reuses the `ctx-cli mcp call` tools the sibling skills document. Both use the
same `$CTX_API_URL` / `$CTX_API_KEY` the CLI uses.

```bash
# ctx-native key (ctx_...): Authorization: Bearer (or X-API-Key) both work
AUTH=(-H "Authorization: Bearer $CTX_API_KEY")
# Tabnine PAT (t9u_...): add the x-auth-type header
# AUTH=(-H "Authorization: Bearer $CTX_API_KEY" -H "x-auth-type: tabnine")

curl -s "${AUTH[@]}" "$CTX_API_URL/api/ai-settings/status"   # preflight: any 200 = reachable
```

**Three rules hold for every Arc-1 step** (project conventions — non-negotiable):

- **Read before write.** Each step first GETs current state and shows the user what's
  already configured. Re-running the skill is safe and resumes where they left off.
- **Confirm before write.** Never POST/PATCH/activate without showing the user the exact
  payload and getting an explicit yes. Only write what's missing.
- **Never echo secrets.** Read back the *names/ids* of credentials, never the token. The
  API never returns secret `data` on list/create — keep it that way in your summaries.

---

# Arc 1 — Set it up

A checklist. Do the steps in order; skip any that a read shows is already done.

## Step 1 — Preflight

Confirm `$CTX_API_URL` / `$CTX_API_KEY` reach the API:

```bash
curl -s -o /dev/null -w '%{http_code}\n' "${AUTH[@]}" "$CTX_API_URL/api/ai-settings/status"
```

`200` → continue. `401/403` → the key is wrong or missing the `x-auth-type` header (for
`t9u_` tokens); walk the user through the auth setup in the [`ctx`](../ctx/SKILL.md) skill.
Connection refused → wrong URL / API not up.

## Step 2 — Configure the LLM (runner environment)

The LLM provider+model is the **active runner environment**. (Note: `/api/ai-settings` only
stores raw API keys and `/status` is deprecated — `runner-environments` is the real config.)

**Read current state:**

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/runner-environments"            # all envs; look for "isActive": true
curl -s "${AUTH[@]}" "$CTX_API_URL/api/runner-environments/presets"    # required/optional envVars per provider
```

If one is already `isActive`, show it and move on. Otherwise pick a provider and create one.

| `provider` | required `envVars` |
|---|---|
| `anthropic_direct` | `ANTHROPIC_API_KEY` |
| `gcp_vertex` | `CLAUDE_CODE_USE_VERTEX`, `CLOUD_ML_REGION`, `ANTHROPIC_VERTEX_PROJECT_ID` |
| `aws_bedrock` | `CLAUDE_CODE_USE_BEDROCK`, `AWS_REGION` |
| `azure_ai_foundry` | `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL` |
| `openai` | `OPENAI_API_KEY` |
| `gemini` | `GEMINI_API_KEY` |

The **model** is selected through `envVars` (e.g. `ANTHROPIC_MODEL` for `azure_ai_foundry`,
or chosen at agent-run time for `anthropic_direct`). List available models first when the
user is unsure: `GET /api/claude/models` (`{models:[{id,display_name,…}]}`) or
`GET /api/tabnine/models` (agent-capable models only).

**Create + activate** (confirm the payload first; `envVars` carries the secret — never echo it back):

```bash
# 1) create (isActive:true activates on create and deactivates the others)
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST \
  "$CTX_API_URL/api/runner-environments" \
  -d '{"name":"Anthropic Direct","provider":"anthropic_direct","envVars":{"ANTHROPIC_API_KEY":"sk-ant-..."},"isActive":true}'
# 2) (if created inactive) activate by id:  POST /api/runner-environments/<id>/activate
# 3) validate connectivity:                  POST /api/runner-environments/<id>/test  →  {success,message}
```

Shortcut for a plain Anthropic key: `POST /api/ai-settings/anthropic {"apiKey":"sk-ant-..."}`
also provisions an `anthropic_direct` runner config. Prefer `runner-environments` for
anything non-Anthropic or when a model must be pinned.

## Step 3 — Configure the embedder (only if vectors are wanted)

Embeddings are **optional** — skip cleanly if the tenant doesn't need code-search /
semantic features. Mirror the platform's "embeddings optional" posture; don't push it.

**Read current state** (per-scope active models):

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/embedding-models/active"   # {scopes:{entities:{modelId,provider,dimensions},code:{…},…}}
curl -s "${AUTH[@]}" "$CTX_API_URL/api/embedding-models"          # {models:[…]}, status active|inactive|…
```

`/active` **always** returns a model per scope — but a scope whose `modelId` is the
literal `"default"` means the **built-in platform default**, i.e. no custom model is
configured. So "is an embedder set up?" = does any scope have `modelId !== "default"`
(equivalently, is `/api/embedding-models` `models[]` non-empty). If a real (non-default)
model is already active for the scopes they care about (`code`, `entities`, `passages`, …),
you're done. Otherwise, **validate before creating** — this does a live
embed call and returns measured dimensions/latency:

```bash
# 1) validate config (default: OpenAI text-embedding-3-small, 1536-dim — matches platform default)
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST \
  "$CTX_API_URL/api/embedding-models/validate-config" \
  -d '{"provider":"openai","modelIdentifier":"text-embedding-3-small","dimensions":1536}'
#    → {validation:{valid,errors,warnings,measuredDimensions,latencyMs}}  — only proceed if valid:true

# 2) create (status starts 'inactive')
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/embedding-models" \
  -d '{"name":"OpenAI small","provider":"openai","modelIdentifier":"text-embedding-3-small","dimensions":1536,"scope":"code"}'

# 3) activate the returned id:  POST /api/embedding-models/<id>/activate
```

`provider` ∈ `openai | openai-compatible | azure-openai | self-hosted | gemini`. OpenAI
needs an `openai_api_key` (Step 4, then pass its id as `apiKeyCredentialId`, or rely on a
tenant/env OpenAI key). Dimensions can't change on an active model — deactivate first.

## Step 4 — Define data-source credentials

Enumerate the supported credential types, then create only what the user needs. **Secrets
go in `data`; the API never returns them — don't echo them in your summary.**

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/credentials/meta/types"   # JSON array: [{type,label,description,fields:[{name,label,type,required}]}]
curl -s "${AUTH[@]}" "$CTX_API_URL/api/credentials"              # existing creds (id/name/type/host — NO data)
```

Create with `{name, type, data:{…}, host?}` (`host` required when the type's
`hostRequired:true`, e.g. Atlassian/ServiceNow):

```bash
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/credentials" \
  -d '{"name":"GitHub PAT","type":"github_pat","data":{"token":"ghp_..."}}'
#   → {id,name,type,host,createdAt}  (no data) — keep the id for Step 5
```

Common `type` → `data` fields: `github_pat`/`gitlab_pat` → `{token}`; `bitbucket_app_password`
→ `{username,appPassword}`; `atlassian_api_token` (Jira/Confluence, host required) →
`{email,apiToken}`; `servicenow_basic_auth` → `{username,password}`; `openai_api_key` /
`anthropic_api_key` → `{apiKey}`. Trust each type's `fields[]` from `meta/types` over this
list for the exact inputs (host-bound types like Atlassian/ServiceNow carry their host requirement there).

## Step 5 — Define data sources

A data source **binds to its credential via `config.credentialId`** — and the credential's
type must match the source type (the API rejects a mismatch). Mapping:

| source `type` | required credential `type` |
|---|---|
| `github`, `github_actions` | `github_pat` |
| `gitlab` | `gitlab_pat` |
| `bitbucket` | `bitbucket_app_password` |
| `jira`, `confluence` | `atlassian_api_token` |
| `servicenow` | `servicenow_basic_auth` |
| `jfrog_artifactory`, `jfrog_xray` | `jfrog_access_token` |

For **GitHub**, discover repos for an org/user (takes the credential id) before creating:

```bash
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/data-sources/discover" \
  -d '{"credentialId":"<cred-id>","owner":"my-org"}'
#   → {repositories:[{fullName,url,private,alreadyConnected}]} — let the user pick
```

Create the source (`config` holds `credentialId` + provider-specific fields). For
**GitHub** the config requires `owner`, `repo`, **and a non-empty `events` array** (enum:
`push`/`pull_request`/`issues`/`release`/`package.published`/`package.deleted`) — omitting
`events` fails validation (`expected array, received undefined`). Other providers differ
(Jira wants `projectKey`, etc.); the `config` is validated by a per-type Zod schema, so
**confirm a provider's exact shape from an existing source via `GET /api/data-sources`** (or
the engine `config-schemas`) if unsure:

```bash
curl -s "${AUTH[@]}" -H 'Content-Type: application/json' -X POST "$CTX_API_URL/api/data-sources" \
  -d '{"name":"ctx repo","type":"github","config":{"credentialId":"<cred-id>","owner":"codota","repo":"ctx","events":["push","pull_request"]}}'
#   → full data source incl. id, enabled:true
```

Re-running is safe: `GET /api/data-sources` first and skip any source that already exists
(`discover` also flags `alreadyConnected`).

## Step 6 — Kick off ingestion & wait

Trigger a sync per source, then poll until the first entities land:

```bash
curl -s "${AUTH[@]}" -X POST "$CTX_API_URL/api/data-sources/<id>/sync"           # → {workflowId,status,…}
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-sources/<id>/sync-status"            # state idle|syncing, lastSyncStatus, health
curl -s "${AUTH[@]}" "$CTX_API_URL/api/processing/status"                        # workflow + stats.totalSynced/errors + heartbeat
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-source-health/stats/summary"         # totalSources, enabledSources, healthy/warning/unhealthySources, totalSyncs, successRate
```

Report progress in plain terms ("3 repos syncing, 1 200 entities so far, 0 errors") until
`processing/status.stats.totalSynced` grows and at least one source's `lastSyncStatus` is
`success`. Then move to Arc 2.

---

# Arc 2 — Show the value & assist

Once data exists, flip from configurator to guide. Don't dump raw rows — show the
connected picture. This arc **routes into the sibling skills** rather than duplicating them.

## Statistics on your system

A "here's what CTX now knows about your system" snapshot:

```bash
curl -s "${AUTH[@]}" "$CTX_API_URL/api/processing/status"                  # totalSynced, totalProcessed, errors
curl -s "${AUTH[@]}" "$CTX_API_URL/api/data-source-health/stats/by-source" # per-source health + counts
# entity counts by type, from the graph:
ctx-cli mcp call query_entities -p entityType=Service -p limit=200 -o json | jq '.result | length'
```

Summarize: services, repositories, dependencies, flows, and CVEs ingested; per-source
health; anything still syncing.

## Tour the context graph

Walk a few high-value entities and their relationships using
[`ctx-search`](../ctx-search/SKILL.md) (`find_entities` → `traverse_edges`) and
[`ctx-investigate`](../ctx-investigate/SKILL.md) (`investigate_service` for the one-call
deps/owners/runbook picture). Pick 1–2 real services from the stats above and show what
they connect to — the goal is "look, it's connected," not a table.

## Capability map — "what can be done"

Present a concise menu keyed to the tier-1 composites, grounded in *their* entities, each
pointing at the skill that owns it. Fill the `<…>` from real names you just saw:

| Ask me… | Tool | Skill |
|---|---|---|
| "How does `<service>` work / what depends on it / who owns it?" | `investigate_service` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "What breaks if I change `<service>`?" | `blast_radius` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "We're seeing errors in `<service>` — runbook + escalation" | `incident_response` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "Is package `<pkg>` safe? / migrate `<x>`→`<y>`" | `dependency_check` / `code_migration` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "How does the `<flow>` flow work?" | `understand_flow` | [`ctx-investigate`](../ctx-investigate/SKILL.md) |
| "Where is `<thing>` implemented?" | `code_search` | [`ctx-search`](../ctx-search/SKILL.md) |
| "List CVEs / SAST findings with suggested fixes" | `get_cve_resolution_status` | [`ctx-security`](../ctx-security/SKILL.md) |

## Help set up the first skills (security, SRE)

Guide enabling the starter workflows pointed at the data sources just configured —
**explain the opt-in gates, don't flip anything silently:**

- **Security / CVE auto-remediation** — once a scanner data source (Snyk/Checkmarx) and a
  Git source are ingesting, the CVE inbox ([`ctx-security`](../ctx-security/SKILL.md),
  `get_cve_resolution_status`) carries ready-to-apply fix diffs. Auto-remediation (auto-PRs)
  is a deliberate opt-in: surface that it exists and what gates it, rather than enabling it.
- **SRE / incident response** — with a PagerDuty/Opsgenie or alert source plus the service
  graph, `incident_response` ([`ctx-investigate`](../ctx-investigate/SKILL.md)) returns
  runbooks + escalation for a service. Show one against a real service.

## Generic assist

After setup, default into "show me what I can do here" mode: take the user's own questions
and answer them against the live graph by routing into
[`ctx-search`](../ctx-search/SKILL.md) / [`ctx-investigate`](../ctx-investigate/SKILL.md) /
[`ctx-security`](../ctx-security/SKILL.md). Demonstrate value on *their* real data — that's
the hand-off from onboarding to everyday use.
