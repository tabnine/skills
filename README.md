# Tabnine Skills

Agent skills, tools, and integrations for Tabnine's Context Engine — enabling semantic code search, symbol lookup, OpenAPI spec querying, and deep codebase investigation across all your team's indexed repositories.

## Supported Platforms

| Platform | Path | Status |
|----------|------|--------|
| **Claude Code** | [`plugins/claude/tabnine/`](plugins/claude/tabnine/) | Plugin + Skill + Agent + Command |
| **Cursor** | [`plugins/cursor/tabnine/`](plugins/cursor/tabnine/) | Plugin + Skill + Agent + Rule |

## Prerequisites

Set the following environment variables before using any plugin:

```bash
export TABNINE_HOST="your-tabnine-instance.tabnine.com"
export TABNINE_TOKEN="your-personal-access-token"
```

### Obtaining a Token

1. Open `https://<TABNINE_HOST>` in a browser
2. Navigate to **Settings** > **Access Tokens**
3. Click **Generate token**
4. Copy the token and set it as `TABNINE_TOKEN`

## Quick Start

### Claude Code

```bash
claude plugin add tabnine
```

Then ask Claude about remote repos or use the `/investigate` command:

```
/investigate How does the authentication flow work?
```

### Cursor

Install via the Cursor plugin marketplace, or copy `plugins/cursor/tabnine/mcp.json` to your project. The always-active rule will guide Cursor to use Tabnine Context Engine for cross-repo questions.

## Available MCP Tools

All tools are served by the `tabnine-context` MCP server.

| Tool | Description |
|------|-------------|
| `remote_repositories_list` | List all indexed repositories |
| `remote_codebase_search` | Semantic + lexical code search |
| `remote_symbol_content` | Find symbols with full source code |
| `remote_symbols_search` | Search for functions/classes/enums |
| `remote_file_content` | Fetch file contents from remote repos |
| `remote_files_search` | Search files by path/name |
| `remote_repository_folder_tree` | Browse repo directory structure |
| `remote_search_assets` | Search OpenAPI specs and service summaries |
| `remote_openapi_spec_query` | Query OpenAPI specs with jq expressions |
| `remote_get_asset` | Get full asset content |
| `remote_grep_asset` | Grep through asset content with regex |

## Investigator Agent

A read-only agent that performs deep investigation of remote repositories. It:

- Systematically explores code using all available MCP tools
- Follows references across repositories and services
- Returns structured findings with source references
- Maintains an exploration trace for transparency

Available in both Claude Code and Cursor.

## Project Structure

```
tabnine-skills/
├── .claude-plugin/
│   └── marketplace.json              # Claude plugin marketplace entry
├── .cursor-plugin/
│   └── marketplace.json              # Cursor plugin marketplace entry
├── plugins/
│   ├── claude/
│   │   └── tabnine/
│   │       ├── .claude-plugin/plugin.json
│   │       ├── .mcp.json
│   │       ├── agents/
│   │       │   └── investigator.md
│   │       ├── commands/
│   │       │   └── investigate.md
│   │       ├── skills/
│   │       │   └── codebase-search/SKILL.md
│   │       └── README.md
│   └── cursor/
│       └── tabnine/
│           ├── .cursor-plugin/plugin.json
│           ├── mcp.json
│           ├── agents/
│           │   └── investigator.md
│           ├── rules/
│           │   └── use-tabnine-context.mdc
│           ├── skills/
│           │   └── codebase-search/SKILL.md
│           └── README.md
└── README.md
```
