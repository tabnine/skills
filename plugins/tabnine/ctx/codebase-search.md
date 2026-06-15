# Codebase search

Two distinct search layers live here:

1. **Code search** — find the actual *source code* that does something (returns real file/line chunks). Reach for this whenever the answer is a **code location**. See [Code search](#code-search--actual-source-code-code_search) below.
2. **Knowledge-graph search** — find *entities* (Services, Libraries, CodePatterns…) and their relationships. Reach for this for architecture/dependency questions where the answer is a graph entity, not a line of code.

Before reaching for primitives, check whether a tier-1 composite already answers the question — see the intent table in [`SKILL.md`](./SKILL.md). For "how does this service work" or "what depends on this service," `investigate_service` is one call. Drop to the primitives below when no composite covers the shape of the question or you need a specific narrow slice.

## When to reach for this

| Task | Tool |
|---|---|
| **Find the code that does X / where is X implemented** (returns source chunks) | **`ctx-cli mcp call code_search`** — see [Code search](#code-search--actual-source-code-code_search) |
| Find entities by natural-language query ("authentication services", "rate limit code") | `find_entities` |
| Broader semantic search across the whole graph (libraries, usages, patterns, …) | `search_knowledge` |
| Lexical lookup by type + regex name pattern (all `Service`s, names matching `.*Service`) | `query_entities` |
| What's connected to this entity? (callers, dependencies, contents) | `traverse_edges` |
| Full details for an ID returned by any of the above | `get_entity_by_id` |
| How are two specific services / repos connected? | See "Cross-service traversal" below |
| Read or grep a file in an indexed repo I don't have checked out | `semantic_read_file` / `semantic_search_for_pattern` — but **probe first**, see "Optional indexers" below |

For **"find code"**, use Code search. For **graph exploration**, the standard loop is **`find_entities` → `traverse_edges` → `get_entity_by_id`**: semantic search to land on a starting entity, edge traversal to discover its neighborhood, then deep-read whichever neighbor matters.

## Code search — actual source code (`code_search`)

This is the tool for **"find the code that does X" / "where is X implemented"**. It returns real source-code chunks — file path, line range, and the code itself — ranked by hybrid vector + keyword similarity across every indexed repo. Use it instead of the graph tools whenever the answer is a *code location* rather than a graph entity. `matchType` tells you whether each hit came from `vector`, `keyword`, or `hybrid` matching.

```bash
# Find code by natural language
ctx-cli mcp call code_search -p query="authentication middleware" -p limit=20 -o json

# Scope to specific languages and/or indexed repos
ctx-cli mcp call code_search -p query="retry with backoff" -p limit=10 \
  -p 'languages=["typescript"]' -p 'dataSourceIds=["01518334-9f17-4761-a9ce-8cef1205d6a3"]' -o json
```

**Parameters** (`query` is the only required one):

| param | type | notes |
|---|---|---|
| `query` | string | natural-language query (required, min 3 chars) |
| `limit` | number | page size (default `20`, max `100`) |
| `page` | number | 1-based page number (default `1`, max `10`) |
| `minSimilarity` | number | default `0.3`; lower to widen, raise to tighten |
| `languages` | string[] | filter by language, e.g. `["typescript"]` (JSON-array string) |
| `dataSourceIds` | string[] | scope to specific indexed repos (JSON-array string) |

**Each `results[]` row:** `filePath`, `startLine`, `endLine`, `language`, `symbolName` (may be null), `content` (the code), `similarity`, `matchType` (`vector` | `keyword` | `hybrid`), `dataSourceId`, `dataSourceName`, `dataSourceType`, and `sourceUrl` (deep link to the exact lines on the host). Top level also carries `count`, `page`, `pageSize`, `hasMore`.

**Discover indexed repos / check availability** — this is how you get the `dataSourceId`s for the `dataSourceIds` filter. There's no MCP tool for status yet, so hit the REST endpoint:

```bash
curl -s "$CTX_API_URL/api/code-search/status" -H "Authorization: Bearer $CTX_API_KEY"
```

Returns `available`, `totalChunks`, `totalDataSources`, and a `dataSources[]` list with per-repo `dataSourceName`, `dataSourceId`, `status` (`completed` | `indexing` | `failed`), and chunk counts. A repo whose `status` isn't `completed` (or whose `embeddedChunks` is `0`) won't return results yet.

> **REST fallback (rollout window).** The `code_search` MCP tool is seeded from the platform's exported-tools config; on a tenant where it hasn't been re-seeded yet, `ctx-cli mcp call code_search` won't resolve. Until then (or for the `/status` call above), use the REST endpoint directly with the same `$CTX_API_KEY` / `$CTX_API_URL` the CLI uses — same params as the table:
> ```bash
> curl -s -X POST "$CTX_API_URL/api/code-search" \
>   -H "Authorization: Bearer $CTX_API_KEY" -H "Content-Type: application/json" \
>   -d '{"query":"authentication middleware","limit":20,"minSimilarity":0.3}'
> ```
> Note the `ctx code search` / `ctx code symbols` CLI subcommands remain broken (they issue `GET`, the endpoint is `POST`-only) — don't use them.

## Semantic search — `find_entities`

Natural-language entry point. Returns entities ranked by similarity. Filter to specific kinds with `entityTypes`; the default `minSimilarity` of 0.5 is usually right.

```bash
# Find by concept
ctx-cli mcp call find_entities -p query="authentication service" -p limit=5 -o json

# Filter to specific entity kinds (entityTypes is a JSON-array string)
ctx-cli mcp call find_entities -p query="rate limiting" -p 'entityTypes=["Service","Library","CodePattern"]' -o json

# Lower the similarity bar when the query is loose
ctx-cli mcp call find_entities -p query="payment retry" -p minSimilarity=0.3 -o json
```

Each row in `result.results[]` carries `entityId`, `entityType`, `entityName`, `similarity`, a parsed `data` object, and a `content` summary. Common types: `Service`, `Repository`, `Library`, `LibraryUsage`, `CodePattern`, `Feature`, `ModuleBoundary`, `Package`, `Finding`, `Vulnerability`.

**When results come back sparse (null `entityName` / empty `data`):** the query likely landed on stub nodes (e.g., bare `Repository` references from CVE pipelines that haven't been enriched). Three fallbacks, in order:
1. Re-query with `entityTypes=["Service"]` (or another concrete type) — `Service` nodes are reliably enriched.
2. Switch to `search_knowledge` with `minSimilarity=0.4` for a wider net.
3. If the question is about a specific service by name, use `query_entities -p entityType=Service -p namePattern=.*<name>.*` for a deterministic match.

## Broader semantic search — `search_knowledge`

Wider net than `find_entities`. Use when you want any node (not just first-class entities) that mentions the concept.

```bash
ctx-cli mcp call search_knowledge -p query="<concept>" -p limit=10 -o json
ctx-cli mcp call search_knowledge -p query="<concept>" -p 'entityTypes=["Service","CodePattern"]' -o json
```

Default `minSimilarity` is 0.7, which is often too tight; drop to 0.4–0.5 when results are empty. **`entityTypes` must be a JSON-array string** (same shape as `find_entities`) — `mcp describe` claims comma-separated, but the comma form 500s on the live tenant.

## Lexical / structured search — `query_entities`

Cypher-backed enumeration by type and optional regex name pattern. Use when you know the entity kind and want either all of them or a regex-matched slice.

```bash
# All Services
ctx-cli mcp call query_entities -p entityType=Service -p limit=50 -o json

# Name-pattern match (regex — see wart below)
ctx-cli mcp call query_entities -p entityType=Service -p 'namePattern=.*API.*' -o json

# Other common types
ctx-cli mcp call query_entities -p entityType=Repository -o json
ctx-cli mcp call query_entities -p entityType=Package -p 'namePattern=@ctx/.*' -o json
```

**Two warts:**
- `namePattern` is a **regex**, despite `mcp describe` advertising `*` wildcards. `*API*` 500s; use `.*API.*`. Bare names like `Admin UI` work as literal regex.
- `data` comes back as a **JSON string** you must re-parse (`jq '.result[] | .data | fromjson'`). Only the semantic-search tools (`find_entities`, `search_knowledge`) return `data` already parsed; the Cypher-backed tools (`query_entities`, `traverse_edges`, `get_entity_by_id`) all return the JSON-string form.

## Adjacency — `traverse_edges`

After you have an entity ID, walk its edges to find what's around it. This is how you answer "what does this depend on / call / contain?" and "what depends on / calls / contains this?".

```bash
# Everything connected (both directions)
ctx-cli mcp call traverse_edges -p entityId=<entity-id> -p limit=25 -o json

# What does X depend on?
ctx-cli mcp call traverse_edges -p entityId=<service-id> -p direction=out -o json

# What depends on X?
ctx-cli mcp call traverse_edges -p entityId=<service-id> -p direction=in -o json

# Only a specific edge kind (case-sensitive — see below)
ctx-cli mcp call traverse_edges -p entityId=<service-id> -p edgeType=CALLS -o json
ctx-cli mcp call traverse_edges -p entityId=<service-id> -p edgeType=depends_on -o json
```

Each result row carries top-level `id`, `name`, `type`, `data` (JSON string — same shape as `query_entities`), `edgeType`, `edgeDirection` (`incoming` | `outgoing`). `edgeType` filtering is **case-sensitive** and the stored casings are mixed: `CALLS`, `depends_on`, `contains`, `produces`, `consumes`, `references`, `manages`, `PUBLISHES_TO`, `SUBSCRIBES_TO`. Confirm the actual casing from an unfiltered call before filtering. For multi-hop traversal, feed the returned IDs back into `traverse_edges`.

## Cross-service traversal — "how are X and Y connected?"

For "do these two services talk to each other?" or "what's the path between them?", use the loop:

```bash
# 1. Find both endpoints
X_ID=$(ctx-cli mcp call find_entities -p query="<service X>" -p 'entityTypes=["Service"]' -p limit=1 -o json | jq -r '.result.results[0].entityId')
Y_NAME="<service Y>"

# 2. Walk X's outgoing edges and check whether any target is Y
ctx-cli mcp call traverse_edges -p entityId=$X_ID -p direction=out -p limit=50 -o json \
  | jq --arg y "$Y_NAME" '.result | map(select(.name == $y)) | map({edgeType, edgeDirection, target: .name, data: (.data | fromjson)})'

# 3. If no direct edge, expand to 2 hops by feeding each neighbor's id back into traverse_edges
```

When both services are indexed, this gives you the actual edge kind (`CALLS`, `depends_on`, `PUBLISHES_TO`) and the data payload (e.g. dependency host/port, queue topic). For "find the call-site in source code" — only viable if `semantic_*` is available on the tenant; see below.

## Deep-read by ID — `get_entity_by_id`

`find_entities`, `search_knowledge`, `query_entities`, and `traverse_edges` already return `id`, `name`, `type`, and `data` inline — so most of the time you don't need a follow-up call. Use `get_entity_by_id` when you specifically need `createdAt` / `createdBy`:

```bash
ctx-cli mcp call get_entity_by_id -p entityId=<entity-id> -o json
```

**Parameter wart:** the param is `entityId` (not `id`). Calling with `-p id=<value>` errors with `Missing required parameter: entityId`.

**Result-shape wart:** `result` is always an **array** (length 0 or 1), even though the description implies a single entity. Use `.result[0]` to extract. Returns `id`, `name`, `type`, `data` (JSON string — same shape as `query_entities`), `createdAt`, `createdBy`.

**Visibility wart:** `get_entity_by_id` does not retrieve every entity that other tools see — some entity IDs that `query_entities` and `traverse_edges` return come back as `result: []` (visibility/scope filtering, likely by `createdBy`). If you get an empty response, fall back to the `data` already inline in the upstream query's row.

## Optional indexers — probe before scripting

The following tools exist in `ctx-cli mcp list --tier all` but **only return useful data once the corresponding indexer has run for the tenant**. On a fresh tenant they 500 or return empty arrays. **Probe with one cheap call before relying on them** — the failures don't always come with a clear "not configured" message.

| Tool family | Requires | Probe |
|---|---|---|
| `semantic_search_for_pattern`, `semantic_read_file`, `semantic_list_dir`, `semantic_find_symbol`, `semantic_find_referencing_symbols`, `semantic_get_symbols_overview`, `query_symbols` | LSP analyzer connected to a git data source | `semantic_list_dir -p project_id=<ds-id> -p relative_path=.` — if it 500s, the whole family is unavailable on this tenant |
| `get_file_context`, `resolve_file_to_service`, `get_related_files` | `git-insights-analyzer` agent run on the repo | `resolve_file_to_service -p filepath=<known file>` — empty array means CodeModules not seeded |
| `search_concepts`, `get_concept_implementations`, `find_equivalent_fields` | Concept extraction populated `Concept` nodes | `search_concepts -p query=<term> -p limit=1` — empty means not populated |

When the LSP / `semantic_*` family is up, it's the **only** way to read source from repos you don't have checked out locally. To use it, first find the data source ID:

```bash
ctx-cli mcp call query_entities -p entityType=Repository -p 'namePattern=.*<repo-name>.*' -o json \
  | jq -r '.result[] | "\(.name)\t\((.data | fromjson).dataSourceId)"'
```

Then feed the `dataSourceId` as `project_id` to `semantic_read_file` / `semantic_search_for_pattern`. If the probe call returned 500, fall back to local `grep` on a checked-out copy or to the graph-only loop (`find_entities` → `traverse_edges`) — graph adjacency captures the *fact* of a connection even when source-level inspection isn't available.

When populated, `get_file_context` is a tier-1 composite that returns ADRs, incidents, security patterns, experts and blast radius for a file path. Worth trying first when working on a specific file.
