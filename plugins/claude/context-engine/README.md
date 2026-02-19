# Tabnine Remote Repos Context — Claude Plugin

Search, explore, and investigate remote repositories using Tabnine's Context Engine directly from Claude Code.

## Installation

### From Marketplace

```bash
claude plugin add tabnine-remote-repos-context
```

### Manual Installation

1. Clone this repository
2. Run `claude plugin add ./plugins/claude/tabnine-remote-repos-context`

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
Automatically activates when you ask about remote repositories, search for code across repos, or need architectural understanding of remote codebases.

### Agent: Tabnine Context Engine Investigator
A read-only agent that performs deep investigation of remote repositories. It systematically explores code using semantic search, symbol lookup, and file browsing to answer complex questions.

### Command: `/investigate`
Quick access to the investigator agent:

```
/investigate How does the authentication flow work in the backend service?
```

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
