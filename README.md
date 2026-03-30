# Tabnine Skills

Agent skills, tools, and integrations for AI coding agents — enabling semantic code search, coding guidelines enforcement, and Context Engine knowledge graph access across Claude Code, Cursor, Gemini CLI, and Tabnine agent.

## Plugins

This repo ships **two independent plugins** with support for four agents. Install what you need:

| Plugin | What it does | Claude Code | Cursor | Gemini CLI | Tabnine Agent |
|--------|-------------|-------------|--------|------------|---------------|
| **tabnine** | Semantic code search across remote repos, coding guidelines | `claude plugin add tabnine/skills` | Marketplace | `gemini skills install` | `tabnine skills install` |
| **ctx** | Query the Context Engine knowledge graph — investigate services, blast radius, Jira, incidents | `claude plugin add tabnine/skills:ctx` | Marketplace | `gemini skills install` | `tabnine skills install` |

## Quick Start

### Claude Code

```bash
# 1. Add the marketplace (one time)
claude plugin marketplace add tabnine/skills

# 2. Install plugins
claude plugin install tabnine       # codebase search + coding guidelines
claude plugin install ctx@tabnine   # Context Engine CLI
```

### Cursor

Install via the Cursor plugin marketplace — both `tabnine` and `ctx` appear as separate plugins.

Manual install:

```bash
# Install Tabnine plugin into current project
bash <(curl -fsSL https://raw.githubusercontent.com/tabnine/skills/main/scripts/install-cursor-plugin.sh)

# Install globally
bash <(curl -fsSL https://raw.githubusercontent.com/tabnine/skills/main/scripts/install-cursor-plugin.sh) --global
```

### Gemini CLI

Each skill is installed independently:

```bash
# Codebase search
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/tabnine/codebase-search

# Coding guidelines
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/tabnine/coding-guidelines

# Context Engine CLI
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/ctx
```

### Tabnine Agent

```bash
# Context Engine CLI
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/ctx

# Codebase search
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/codebase-search

# Coding guidelines
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/coding-guidelines
```

## Prerequisites

### Tabnine plugin (codebase search + coding guidelines)

```bash
export TABNINE_HOST="your-tabnine-instance.tabnine.com"
export TABNINE_TOKEN="your-personal-access-token"
```

**Obtaining a token:** Open `https://<TABNINE_HOST>` > **Settings** > **Access Tokens** > **Generate token**.

### ctx plugin (Context Engine CLI)

```bash
export CTX_API_URL="https://ctx.tabnine.com"
# Any of these work: CTX_API_KEY, TABNINE_TOKEN, or CTX_TOKEN
export CTX_API_KEY="ctx_..."
```

The ctx plugin also requires the `ctx-cli` binary. The skill teaches your agent how to download it, or install manually:

```bash
curl -fsSL https://github.com/tabnine/skills/releases/latest/download/ctx-cli-$(uname -s | tr A-Z a-z)-$(uname -m | sed 's/aarch64/arm64/') -o /usr/local/bin/ctx-cli && chmod +x /usr/local/bin/ctx-cli
```

## Tabnine Plugin

### Skills

| Skill | Description |
|-------|-------------|
| **codebase-search** | Search, explore, and investigate remote repositories using Tabnine's Context Engine |
| **coding-guidelines** | Fetch and apply team coding standards when reviewing or writing code |

### MCP Tools

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

### Investigator Agent

A read-only agent that performs deep investigation of remote repositories. It systematically explores code using all available MCP tools, follows references across repositories, and returns structured findings. Available in both Claude Code and Cursor.

```
/investigate How does the authentication flow work?
```

## ctx Plugin

### What it enables

The ctx skill teaches your agent to use the Context Engine CLI (`ctx-cli`) to query the knowledge graph. Examples:

```bash
# Investigate a service
ctx-cli mcp call investigate_service -p serviceName=auth-service -o json

# Check blast radius before making changes
ctx-cli mcp call blast_radius -p target=payment-api -p changeType=breaking -o json

# Search the knowledge graph
ctx-cli mcp call find_entities -p query="authentication" -o json

# Manage Jira issues
ctx-cli mcp call get_jira_issue -p issueKey=ENG-123 -o json

# Incident response
ctx-cli mcp call incident_response -p serviceName=auth-service -o json

# Discover all 100+ available tools
ctx-cli mcp list
```

### How it works

The skill teaches the agent *when* and *how* to call `ctx-cli`. The CLI dynamically discovers tools from the Context Engine API — no hardcoded commands. The agent shells out to `ctx-cli`, parses JSON output, and presents results.

See the [CLI spec](https://github.com/codota/ctx/blob/main/docs/specs/cli-mcp-tools-spec.md) for full design details.

## Project Structure

```
tabnine-skills/
├── .claude-plugin/
│   └── marketplace.json              # Claude marketplace (tabnine + ctx plugins)
├── .cursor-plugin/
│   └── marketplace.json              # Cursor marketplace (tabnine + ctx plugins)
├── plugins/
│   ├── claude/
│   │   ├── tabnine/                  # Tabnine plugin (codebase search + guidelines)
│   │   │   ├── .claude-plugin/plugin.json
│   │   │   ├── .mcp.json
│   │   │   ├── agents/investigator.md
│   │   │   ├── commands/investigate.md
│   │   │   ├── skills/
│   │   │   │   ├── codebase-search/SKILL.md
│   │   │   │   └── coding-guidelines/SKILL.md
│   │   │   └── README.md
│   │   └── ctx/                      # ctx plugin (Context Engine CLI)
│   │       ├── .claude-plugin/plugin.json
│   │       └── skills/ctx/SKILL.md
│   ├── cursor/
│   │   ├── tabnine/                  # Tabnine plugin
│   │   │   ├── .cursor-plugin/plugin.json
│   │   │   ├── .mcp.json
│   │   │   ├── agents/investigator.md
│   │   │   ├── rules/use-tabnine-context.mdc
│   │   │   ├── skills/
│   │   │   │   ├── codebase-search/SKILL.md
│   │   │   │   └── coding-guidelines/SKILL.md
│   │   │   └── README.md
│   │   └── ctx/                      # ctx plugin
│   │       ├── .cursor-plugin/plugin.json
│   │       ├── rules/ctx.mdc
│   │       └── skills/ctx/SKILL.md
│   ├── gemini/                       # Gemini CLI skills
│   │   ├── tabnine/
│   │   │   ├── codebase-search/SKILL.md
│   │   │   └── coding-guidelines/SKILL.md
│   │   └── ctx/SKILL.md
│   └── tabnine/                      # Tabnine agent skills
│       ├── ctx/SKILL.md
│       ├── codebase-search/SKILL.md
│       └── coding-guidelines/SKILL.md
└── scripts/
    ├── validate-cursor-plugin.mjs
    └── install-cursor-plugin.sh
```
