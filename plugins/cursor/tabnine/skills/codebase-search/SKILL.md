---
name: codebase-search
description: Use when searching, exploring, or investigating remote repositories using Tabnine's Context Engine. Activates for cross-repo questions, service architecture questions, PR impact analysis, or when verifying usage of external APIs against real codebase examples.
---

When the user asks about remote codebases, search and explore using Tabnine's Context Engine MCP tools.

## When to Use This Skill

- Asks about code in a remote repository or across multiple repos
- Needs architectural understanding of a service or system
- Is reviewing code or a PR and wants to assess cross-repo impact
- Is working with an external API and needs real usage examples from the codebase

## How to Search

### Step 1: Discover repositories
Call `remote_repositories_list` to see what's indexed.

### Step 2: Search for code
Use `remote_codebase_search` for broad semantic search, then narrow with:
- `remote_symbols_search` + `remote_symbol_content` for specific functions or classes
- `remote_files_search` + `remote_file_content` for specific files
- `remote_repository_folder_tree` to browse repo structure

### Step 3: Find APIs
Use `remote_search_assets` to find OpenAPI specs, then `remote_openapi_spec_query` to query them.

## Guidelines

- Start broad with semantic search, then narrow down
- Cross-reference multiple repos when investigating service interactions
- Always include exact file paths and repo references in your response
