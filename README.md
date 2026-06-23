# Tabnine Skills

Agent skills, tools, and integrations for AI coding agents — enabling semantic code search, coding guidelines enforcement, and Context Engine knowledge graph access across Claude Code, Cursor, Gemini CLI, and Tabnine agent.

## Plugins

This repo ships **two independent plugins** with support for four agents. Install what you need:

| Plugin | What it does | Claude Code | Cursor | Gemini CLI | Tabnine Agent |
|--------|-------------|-------------|--------|------------|---------------|
| **tabnine** | Semantic code search across remote repos, coding guidelines | `claude plugin install tabnine` | Marketplace | `gemini skills install` | `tabnine skills install` |
| **ctx** | Context Engine CLI, split into focused skills — code/graph search, service investigation, CVE & SAST triage, and coding guidelines | `claude plugin install ctx@tabnine` | Marketplace | `gemini skills install` | `tabnine skills install` |

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

# Context Engine CLI — install each ctx skill independently
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/ctx/ctx
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/ctx/ctx-search
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/ctx/ctx-security
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/ctx/ctx-guidelines
gemini skills install https://github.com/tabnine/skills.git --path plugins/gemini/ctx/ctx-investigate
```

### Tabnine Agent

```bash
# Context Engine CLI — install each ctx skill independently
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/ctx/ctx
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/ctx/ctx-search
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/ctx/ctx-security
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/ctx/ctx-guidelines
tabnine skills install https://github.com/tabnine/skills.git --path plugins/tabnine/ctx/ctx-investigate

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

The ctx plugin requires the `ctx-cli` binary. The skill teaches your agent how to download the newest CLI-scoped release, or install manually:

```bash
RELEASES=$(curl -fsSL --max-time 8 'https://api.github.com/repos/tabnine/skills/releases?per_page=100')
TAG=$(printf '%s\n' "$RELEASES" | tr '{' '\n' | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(ctx-cli-v[0-9][^"]*\)".*/\1/p' | head -1)
[ -n "$TAG" ] || TAG=$(printf '%s\n' "$RELEASES" | tr '{' '\n' | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[0-9][^"]*\)".*/\1/p' | head -1)
test -n "$TAG" || { echo "No ctx-cli release found"; exit 1; }
curl -fsSL "https://github.com/tabnine/skills/releases/download/$TAG/ctx-cli-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/aarch64/arm64/;s/x86_64/x64/')" -o /usr/local/bin/ctx-cli && chmod +x /usr/local/bin/ctx-cli
```

Then configure the API URL and credentials. ctx-cli reads these from environment variables and/or a config file at `~/.ctx/config.yaml`. Env vars override config when both are set.

**ctx-native API key (`ctx_...`) — env-only works:**
```bash
export CTX_API_URL="https://ctx.tabnine.com"
export CTX_API_KEY="ctx_..."
```

**Tabnine PAT (`t9u_...`) — requires config.yaml for the `x-auth-type` header:**

The token itself can come from env (`TABNINE_TOKEN` or `CTX_TOKEN`) or from config, but custom headers can only be set in config — ctx-cli has no env var that maps to headers. So Tabnine PATs need at least one `ctx-cli config set-header` call:

```bash
ctx-cli config init                                  # interactive: prompts for url + key
ctx-cli config set api_url https://ctx.tabnine.com   # or set fields individually
ctx-cli config set api_key t9u_...
ctx-cli config set-header x-auth-type tabnine        # required for Tabnine PATs
```

Env vars ctx-cli recognizes (checked in this order for the bearer token): `CTX_API_KEY` → `TABNINE_TOKEN` → `CTX_TOKEN`. Plus `CTX_API_URL` for the URL. Other useful commands: `ctx-cli config list` (show profiles with masked secrets), `ctx-cli config use-profile <name>` (switch active profile), `ctx-cli config remove-header <key>` (remove a stored header).

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

The ctx plugin teaches your agent to use the Context Engine CLI (`ctx-cli`). It is split into a foundational skill plus focused domain skills, so each user intent triggers the right one independently:

| Skill | What it covers |
|-------|----------------|
| **`ctx`** | Foundational — install, auth, version-check, tool discovery, routing, and the pick-a-tool-by-intent table. |
| **`ctx-search`** | Find source code (`code_search`), find entities by natural language, and traverse graph relationships. |
| **`ctx-investigate`** | Tier-1 composites — `investigate_service`, `blast_radius`, `incident_response`, `dependency_check`, `code_migration`, `understand_flow`, `get_file_context`. |
| **`ctx-security`** | CVE and SAST resolution inboxes (`get_cve_resolution_status` / `get_sast_resolution_status`), each row carrying a ready-to-apply fix diff or advisory. |
| **`ctx-guidelines`** | Managed coaching guidelines (`get_coding_guidelines`) plus discovered AI-guideline files (`get_guideline_sources`) — coverage and cross-repo drift. |
| **`ctx-onboarding`** | Checks the agent model + embedder are configured (guides the operator to set them in the UI if missing), connects data sources (repos + credentials) and triggers sync, then a show-the-value tour (stats, graph, capability map). Ships for Claude Code + Cursor. |

Examples:

```bash
# Semantic search — find entities by natural-language query
ctx-cli mcp call find_entities -p query="authentication service" -p limit=5 -o json

# Lexical search — enumerate entities by type
ctx-cli mcp call query_entities -p entityType=Service -p limit=50 -o json

# Graph adjacency — what is this entity connected to?
ctx-cli mcp call traverse_edges -p entityId=<id> -p direction=out -o json

# CVE inbox — each row carries the suggested fix in data.recommendedAction
ctx-cli mcp call get_cve_resolution_status -p status=fix_pending_review -o json

# Discover available tools
ctx-cli mcp list
```

Each domain skill loads in isolation and points back to the foundational `ctx` skill for the install/auth/version-check steps — the single source of truth, so the CLI bootstrap is never duplicated divergently across skills.

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
│   │       └── skills/           # ctx (router) + ctx-search / ctx-investigate / ctx-security / ctx-guidelines / ctx-onboarding
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
│   │       └── skills/           # ctx (router) + ctx-search / ctx-investigate / ctx-security / ctx-guidelines / ctx-onboarding
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
