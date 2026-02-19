# Tabnine Context Engine

Multi-platform plugins for searching, exploring, and investigating remote repositories using [Tabnine's Context Engine](https://www.tabnine.com/).

Provides semantic code search, symbol lookup, OpenAPI spec querying, and deep codebase investigation across all your team's indexed repositories.

## Supported Platforms

| Platform | Path | Status |
|----------|------|--------|
| **Claude Code** | [`plugins/claude/tabnine-context-engine/`](plugins/claude/tabnine-context-engine/) | Plugin + Skill + Agent + Command |
| **Cursor** | [`plugins/cursor/tabnine-context-engine/`](plugins/cursor/tabnine-context-engine/) | Plugin + Skill + Agent + Rule |
| **Gemini** | [`plugins/gemini/gemini-extension.json`](plugins/gemini/gemini-extension.json) | Extension manifest |

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
claude plugin add tabnine-context-engine
```

Then ask Claude about remote repos or use the `/investigate` command:

```
/investigate How does the authentication flow work?
```

### Cursor

1. Copy `plugins/cursor/tabnine-context-engine/mcp.json` to your project
2. The always-active rule will guide Cursor to use Tabnine Context Engine for cross-repo questions

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

The **Tabnine Context Engine Investigator** is a read-only agent that performs deep investigation of remote repositories. It:

- Systematically explores code using all available MCP tools
- Follows references across repositories and services
- Returns structured findings with source references
- Maintains an exploration trace for transparency

Available in both Claude Code (as an agent) and Cursor (as an agent definition).

## Project Structure

```
tabnine-skills/
├── .claude-plugin/
│   └── marketplace.json              # Claude plugin marketplace entry
├── .cursor-plugin/
│   └── marketplace.json              # Cursor plugin marketplace entry
├── plugins/
│   ├── claude/
│   │   └── tabnine-context-engine/
│   │       ├── .claude-plugin/plugin.json
│   │       ├── .mcp.json
│   │       ├── agents/
│   │       │   └── tabnine-context-engine-investigator.md
│   │       ├── commands/
│   │       │   └── investigate.md
│   │       ├── skills/
│   │       │   └── remote-repositories-context/SKILL.md
│   │       └── README.md
│   ├── cursor/
│   │   └── tabnine-context-engine/
│   │       ├── .cursor-plugin/plugin.json
│   │       ├── mcp.json
│   │       ├── agents/
│   │       │   └── tabnine-context-engine-investigator.md
│   │       ├── rules/
│   │       │   └── use-tabnine-context.mdc
│   │       ├── skills/
│   │       │   └── remote-repositories-context/SKILL.md
│   │       └── README.md
│   └── gemini/
│       └── gemini-extension.json
├── scripts/
│   └── validate-cursor-plugin.mjs
└── README.md
```
