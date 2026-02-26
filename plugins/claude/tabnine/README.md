# Tabnine — Claude Code Plugin

Search, explore, and investigate remote repositories using Tabnine's Context Engine directly from Claude Code.

## Installation

### From Marketplace

```bash
claude plugin marketplace add https://github.com/tabnine/skills
claude plugin install tabnine
```

### Manual Installation

```bash
claude plugin add ./plugins/claude/tabnine
```

## Prerequisites

Set the following environment variables:

```bash
export TABNINE_HOST="your-tabnine-instance.tabnine.com"
export TABNINE_TOKEN="your-personal-access-token"
```

### Obtaining a Token

1. Open `https://<TABNINE_HOST>/app/settings/access-tokens` in a browser
2. Click **Generate token**
3. Copy the token and set it as `TABNINE_TOKEN`

## What's Included

### Skill: `codebase-search`
Automatically activates when you ask about remote repositories, search for code across repos, or need architectural understanding of remote codebases.

### Agent: Investigator
A read-only agent that performs deep investigation of remote repositories. Systematically explores code using semantic search, symbol lookup, and file browsing to answer complex questions.

### Command: `/investigate`
Quick access to the investigator agent:

```
/investigate How does the authentication flow work in the backend service?
```

## Available MCP Tools

All tools are served by the `tabnine-context` MCP server.

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
