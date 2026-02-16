# MCP Server Setup

The Tabnine context engine MCP server must be configured for the user's agent. `TABNINE_HOST` and `TABNINE_TOKEN` must be set as environment variables before the agent is started.

Environment variable syntax differs between agents — use the correct config for the target agent.

## Config by agent

### Claude Code

```json
{
  "mcpServers": {
    "tabnine-context-engine": {
      "type": "http",
      "url": "https://${TABNINE_HOST}/indexer/mcp",
      "headers": {
        "Authorization": "Bearer ${TABNINE_TOKEN}"
      }
    }
  }
}
```

| Scope | Path |
|---|---|
| Project | `./.mcp.json` |
| User | `~/.claude/.mcp.json` |

### Cursor

Cursor uses `${env:VAR}` syntax for environment variables.

```json
{
  "mcpServers": {
    "tabnine-context-engine": {
      "type": "http",
      "url": "https://${env:TABNINE_HOST}/indexer/mcp",
      "headers": {
        "Authorization": "Bearer ${env:TABNINE_TOKEN}"
      }
    }
  }
}
```

| Scope | Path |
|---|---|
| Project | `./.cursor/mcp.json` |
| User | `~/.cursor/mcp.json` |

If the config file already exists, merge the `tabnine-context-engine` entry into the existing `mcpServers` object rather than overwriting the file.
