---
name: ctx-engine
description: Context Engine for searching and exploring repos, remote repos, repositories, remote repositories, codebase, remote codebase, and API specifications via the tabnine-context-engine MCP server. Use when users ask about repos, remote repos etc, searching code across repositories, finding functions/classes/symbols, querying OpenAPI specs, exploring remote codebases, or need to understand code in team repositories. Triggers include questions like "find where X is implemented", "search for Y in our repos", "how do we do Y in our repos", "what APIs do we have", "show me the code for Z", "list our repositories", or any task involving remote code exploration.
---

# Context Engine

Search and explore remote repositories, code symbols, and API specifications using the tabnine-context-engine MCP tools.

## Quick Tool Selection

| Task                    | Tool                            |
| ----------------------- | ------------------------------- |
| List available repos    | `remote_repositories_list`      |
| Browse repo structure   | `remote_repository_folder_tree` |
| Find files by path/name | `remote_files_search`           |
| Read file contents      | `remote_file_content`           |
| Find functions/classes  | `remote_symbols_search`         |
| Get symbol source code  | `remote_symbol_content`         |
| Semantic code search    | `remote_codebase_search`        |
| Find services/APIs      | `remote_search_assets`          |
| Get asset content       | `remote_get_asset`              |
| Search within assets    | `remote_grep_asset`             |
| Query OpenAPI specs     | `remote_openapi_spec_query`     |

## Common Workflows

### Find and Read Code

```
1. remote_repositories_list → get repoId
2. remote_symbols_search → find symbol by prefix
3. remote_symbol_content → get full source code
```

### Explore a Repository

```
1. remote_repositories_list → get repoId/repoUrl
2. remote_repository_folder_tree → see structure
3. remote_files_search → find specific files
4. remote_file_content → read file contents
```

### Discover APIs and Services

```
1. remote_search_assets (query: "payment API") → find services
2. remote_openapi_spec_query → query endpoints/schemas
   OR remote_get_asset → get full specification
```

### Search for Implementation Patterns

```
1. remote_codebase_search (text: "error handling pattern") → semantic search
2. remote_symbol_content → get matching code
```

## Tool Details

### Repository Tools

**remote_repositories_list**: Returns all accessible repos with `repoId` (for tool calls) and `url` (for display).

**remote_repository_folder_tree**: Browse folder structure. Use `foldersOnly: true` for large repos, `basePath` to start from subdirectory.

### File Tools

**remote_files_search**: Search by path/name substring. Optionally filter by repo or search for directories.

**remote_file_content**: Fetch full file contents. Requires exact `repoUrl`, `repoId`, and `filePath`.

### Symbol Tools

**remote_symbols_search**: Find symbols by prefix. Filter with:

- `snippetType`: "function" | "container" | "root" | "txt"
- `className`: Filter by containing class
- `filePath`: Filter by file path pattern
- `repo`: Filter by specific repository

**remote_symbol_content**: Same as search but includes full source code.

### Search Tools

**remote_codebase_search**: Semantic + lexical search. Use:

- `text`: Natural language or code snippet
- `denyListRepos`: Exclude repos (e.g., local project)
- `allowListRepos`: Limit to specific repos
- `language`: Filter by language
- `maxDistance`: Lower = more similar

### Asset Tools

**remote_search_assets**: Find OpenAPI specs and service summaries.

- Use `query` for semantic search: "payment processing APIs"
- Use `sourceId` to list assets from a specific repo
- Filter with `assetType`: "SERVICE_SUMMARY" | "OPENAPI_SPEC"

**remote_get_asset**: Retrieve full asset content by `assetIdentifier` from search results.

**remote_grep_asset**: Regex search within asset content.

- `pattern`: JS regex (e.g., `function\\s+\\w+`)
- `contextBefore`/`contextAfter`: Lines of context
- `headLimit`: Max matches (default: 50)

Common patterns:

- Find function definitions: `function\\s+\\w+`
- Find imports: `import.*from`
- Find class definitions: `class\\s+\\w+`
- Find TODO comments: `TODO|FIXME`

### OpenAPI Tools

**remote_openapi_spec_query**: Query specs with jq expressions.

Common queries:

- `.info.title` - API title
- `.paths | keys` - List endpoints
- `.components.schemas | keys` - List schemas
- `.components.schemas.User` - Get specific schema
- `.paths["/users"].get` - Endpoint details
- `.paths | to_entries | map(select(.value[].tags[]? == "users"))` - Find by tag

Supports batch queries with array of `assetIdentifiers`.

## Tips

- Always get `repoId` from `remote_repositories_list` before using other repo tools
- Use `remote_search_assets` to discover services, then `remote_openapi_spec_query` for details
- For large repos, use `remote_repository_folder_tree` with `foldersOnly: true` first
- When searching code, prefer `remote_codebase_search` for semantic understanding
- Use `remote_symbols_search` when you know the function/class name prefix
