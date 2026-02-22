---
name: codebase-search
description: >
  Search, explore, and investigate remote repositories using Tabnine's Context Engine.
  Use when users ask about remote repos, search for code across repositories, need
  architectural understanding of remote codebases, want to find functions/classes/APIs
  in team repositories, or ask questions like "how does service X work", "find the
  implementation of Y", "what APIs does Z expose", "show me the code for W".
---

# Tabnine Remote Repositories Context

Provides access to Tabnine's Context Engine for searching, exploring, and understanding code across all indexed remote repositories.

## When to Use

Activate this skill when the user:
- Asks about code in remote repositories or across multiple repos
- Wants to search for functions, classes, symbols, or patterns across the codebase
- Needs architectural understanding of a service or system
- Asks "how does X work" about a remote service or module
- Wants to find API endpoints, OpenAPI specs, or service summaries
- Needs to explore the structure of a remote repository
- Asks to compare implementations across repos
- Wants to understand dependencies or integrations between services

## Available MCP Tools

All tools are provided by the `tabnine-context` MCP server.

### Repository Discovery

- **`remote_repositories_list`** — List all indexed repositories available to your team. Returns repository URLs and IDs for use with other tools.

### Code Search

- **`remote_codebase_search`** — Semantic (RAG) + lexical search across remote repositories. Use natural language queries to find relevant code snippets. Supports filtering by language, repository, and similarity threshold.

- **`remote_symbol_content`** — Search for code symbols (functions, classes, enums) and return their complete source code. Filter by name prefix, type, class, file, or repository.

- **`remote_symbols_search`** — Search for code symbols by prefix or substring. Returns symbol metadata without full source code. Use this for quick lookups, then fetch content with `remote_symbol_content`.

### File Access

- **`remote_file_content`** — Fetch the full content of specific files from remote repositories. Requires exact repository URL and file path.

- **`remote_files_search`** — Search for files by path or name pattern across repositories. Use to locate files before fetching their content.

- **`remote_repository_folder_tree`** — Browse the directory structure of a remote repository. Supports filtering to folders only and setting a base path.

### API & Service Discovery

- **`remote_search_assets`** — Search indexed OpenAPI specifications and service summaries using semantic + keyword search. Find services by functionality or capabilities.

- **`remote_openapi_spec_query`** — Query OpenAPI specifications using jq expressions. Extract endpoints, schemas, parameters, and other API details. Supports batch queries across multiple specs.

- **`remote_get_asset`** — Get the full content of an OpenAPI spec or service summary by its asset identifier.

- **`remote_grep_asset`** — Search through asset content using regex patterns. Find specific patterns, function definitions, or text within large assets.

## Workflow Patterns

### Finding Code
1. Start with `remote_codebase_search` for broad semantic search
2. Narrow down with `remote_symbols_search` or `remote_files_search`
3. Get full source with `remote_symbol_content` or `remote_file_content`

### Understanding a Service
1. Use `remote_search_assets` to find the service's OpenAPI spec or summary
2. Query the spec with `remote_openapi_spec_query` for endpoints and schemas
3. Explore implementation with `remote_codebase_search` and `remote_symbol_content`

### Exploring a Repository
1. List repos with `remote_repositories_list`
2. Browse structure with `remote_repository_folder_tree`
3. Search files with `remote_files_search`
4. Read specific files with `remote_file_content`

## Credentials

Two environment variables are required:

- **`TABNINE_HOST`** — The hostname of the Tabnine instance
- **`TABNINE_TOKEN`** — A personal access token for authentication

These are configured via the MCP server configuration and should be set as environment variables before starting the agent.
