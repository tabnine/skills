# Tabnine Remote Repos Context — Cursor Plugin

Search, explore, and investigate remote repositories using Tabnine's Context Engine directly from Cursor.

## Installation

1. Copy the `mcp.json` file to your project root or Cursor settings directory
2. Set the required environment variables

## Prerequisites

Set the following environment variables:

```bash
export TABNINE_HOST="your-tabnine-instance.tabnine.com"
export TABNINE_TOKEN="your-personal-access-token"
```

### Obtaining a Token

1. Open `https://<TABNINE_HOST>` in a browser
2. Navigate to **Settings** > **Access Tokens**
3. Click **Generate token**
4. Copy the token and set it as `TABNINE_TOKEN`

## What's Included

### Skill: Remote Repositories Context
Describes the available Tabnine Context Engine MCP tools and when to use them.

### Agent: Tabnine Context Engine Investigator
A read-only agent for deep investigation of remote repositories using semantic search, symbol lookup, and file browsing.

### Rule: use-tabnine-context
An always-active Cursor rule that encourages use of the Tabnine Context Engine for cross-repo questions.

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `remote_repositories_list` | List all indexed repositories |
| `remote_codebase_search` | Semantic + lexical code search |
| `remote_symbol_content` | Find symbols with full source code |
| `remote_symbols_search` | Search for functions/classes/enums |
| `remote_file_content` | Fetch file contents |
| `remote_files_search` | Search files by path |
| `remote_repository_folder_tree` | Browse repo structure |
| `remote_search_assets` | Search OpenAPI specs and service summaries |
| `remote_openapi_spec_query` | Query OpenAPI specs with jq |
| `remote_get_asset` | Get full asset content |
| `remote_grep_asset` | Grep through asset content |
