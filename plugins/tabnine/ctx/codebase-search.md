# Codebase search

This is the tool for any **search over the knowledge graph and the code it indexes** via `ctx-cli`. Three intents are covered: lexical search by type, semantic search by natural-language query, and adjacency — discovering entities directly connected to one you already have.

## When to reach for this

| Task | Tool |
|---|---|
| Find entities by natural-language query ("authentication services", "rate limit code") | `find_entities` |
| Broader semantic search across the whole graph (libraries, usages, patterns, …) | `search_knowledge` |
| Lexical lookup by type + regex name pattern (all `Service`s, names matching `.*Service`) | `query_entities` |
| What's connected to this entity? (callers, dependencies, contents) | `traverse_edges` |
| Full details for an ID returned by any of the above | `get_entity_by_id` |

The standard exploration loop is **`find_entities` → `traverse_edges` → `get_entity_by_id`**: semantic search to land on a starting entity, edge traversal to discover its neighborhood, then deep-read whichever neighbor matters.

## Semantic search — `find_entities`

Natural-language entry point. Returns entities ranked by similarity. Filter to specific kinds with `entityTypes`; the default `minSimilarity` of 0.5 is usually right.

```bash
# Find by concept
ctx-cli mcp call find_entities -p query="authentication service" -p limit=5 -o json

# Filter to specific entity kinds
ctx-cli mcp call find_entities -p query="rate limiting" -p 'entityTypes=["Service","Library","CodePattern"]' -o json

# Lower the similarity bar when the query is loose
ctx-cli mcp call find_entities -p query="payment retry" -p minSimilarity=0.3 -o json
```

Each row in `result.results[]` carries `entityId`, `entityType`, `entityName`, `similarity`, a parsed `data` object, and a `content` summary. Common types: `Service`, `Repository`, `Library`, `LibraryUsage`, `CodePattern`, `Feature`, `ModuleBoundary`, `Package`, `Finding`, `Vulnerability`.

## Broader semantic search — `search_knowledge`

Wider net than `find_entities`. Use when you want any node (not just first-class entities) that mentions the concept.

```bash
ctx-cli mcp call search_knowledge -p query="<concept>" -p limit=10 -o json
ctx-cli mcp call search_knowledge -p query="<concept>" -p 'entityTypes=["Service","CodePattern"]' -o json
```

Default `minSimilarity` is 0.7, which is often too tight; drop to 0.4–0.5 when results are empty. Note: `mcp describe search_knowledge` claims `entityTypes` is a comma-separated string — on the live tenant only a JSON-array string works (the same shape as `find_entities`).

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
- `namePattern` is a **regex**, despite `mcp describe` advertising `*` wildcards. `*API*` errors out (invalid regex); use `.*API.*`. Bare names like `Admin UI` work as literal regex.
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

Each result row includes `edgeType` and `edgeDirection` (`incoming` | `outgoing`). `edgeType` filtering is **case-sensitive** and the stored casings are mixed: `CALLS`, `depends_on`, `contains`, `produces`, `consumes`, `references`, `manages`. Confirm the actual casing from an unfiltered call before filtering. For multi-hop traversal, feed the returned IDs back into `traverse_edges`.

## Deep-read by ID — `get_entity_by_id`

`find_entities`, `search_knowledge`, `query_entities`, and `traverse_edges` already return `id`, `name`, `type`, and `data` inline — so most of the time you don't need a follow-up call. Use `get_entity_by_id` when you specifically need `createdAt` / `createdBy`:

```bash
ctx-cli mcp call get_entity_by_id -p entityId=<entity-id> -o json
```

Returns `id`, `name`, `type`, `data` (JSON string — same shape as `query_entities`), `createdAt`, `createdBy`.

**Wart:** `get_entity_by_id` does not retrieve every entity that other tools see — some entity IDs that `query_entities` and `traverse_edges` return come back as an empty `result: []` from `get_entity_by_id` (visibility/scope filtering, likely by `createdBy`). If you get an empty response, fall back to the `data` already inline in the upstream query's row.

## Tools that depend on optional indexers — verify on your tenant first

The following code-search tools exist in `ctx-cli mcp list --tier all` but only return useful data once the corresponding indexer has run for the tenant. If the indexer hasn't been enabled or hasn't finished its first pass, expect empty `result` arrays or 500s. Probe with `mcp describe <tool>` and a small call before scripting against them:

- **LSP / symbol pipeline** — `query_symbols`, `semantic_find_symbol`, `semantic_find_referencing_symbols`, `semantic_search_for_pattern`, `semantic_get_symbols_overview`, `semantic_read_file`, `semantic_list_dir`. Require a connected git-repo data source with the LSP analyzer active.
- **Git co-change / file context** — `get_file_context`, `get_related_files`, `resolve_file_to_service`. Require the `git-insights-analyzer` agent to have run on the repo.
- **Semantic concepts** — `search_concepts`, `get_concept_implementations`, `find_equivalent_fields`. Require concept extraction to have populated `Concept` nodes for the tenant.

When these are populated they are excellent — `get_file_context` is a tier-1 composite that returns ADRs, incidents, security patterns, experts and blast radius for a file path. But don't put them on the hot path of a script without first confirming they return data on the target tenant.
