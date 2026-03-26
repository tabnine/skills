# Context Engine CLI

Use `ctx-cli` to query the Context Engine knowledge graph — investigate services, check blast radius, search entities, manage Jira/Linear issues, and assess change risk.

## Prerequisites

If `ctx-cli` is not installed, download it:

```bash
curl -fsSL https://github.com/codota/ctx/releases/latest/download/ctx-cli-$(uname -s | tr A-Z a-z)-$(uname -m | sed 's/aarch64/arm64/') -o /usr/local/bin/ctx-cli && chmod +x /usr/local/bin/ctx-cli
```

Set your API key:

```bash
export CTX_API_KEY=<your-key>
export CTX_API_URL=https://ctx.tabnine.com
```

## Quick start

```bash
# Investigate a service before making changes
ctx-cli mcp call investigate_service -p serviceName=auth-service -o json

# Check impact of a change
ctx-cli mcp call blast_radius -p target=payment-api -p changeType=breaking -o json

# Search the knowledge graph
ctx-cli mcp call find_entities -p query="authentication" -o json

# Get change confidence score
ctx-cli mcp call get_change_confidence -p files=src/auth.ts -o json
```

## Discover tools

```bash
# List all available tools (~100 tools available)
ctx-cli mcp list -o json

# Search for tools by keyword
ctx-cli mcp list -s jira -o json

# See a tool's parameters before calling
ctx-cli mcp describe <tool-name>
```

## Service investigation

```bash
ctx-cli mcp call investigate_service -p serviceName=<name> -o json
ctx-cli mcp call blast_radius -p target=<name> -p changeType=breaking -o json
ctx-cli mcp call get_service_dependencies -p serviceName=<name> -o json
ctx-cli mcp call get_service_dependents -p serviceName=<name> -o json
```

## Jira

```bash
ctx-cli mcp call get_jira_issue -p issueKey=ENG-123 -o json
ctx-cli mcp call create_jira_issue --json '{"summary":"Fix auth timeout","projectKey":"ENG","issueType":"Bug"}' -o json
ctx-cli mcp call transition_jira_issue -p issueKey=ENG-123 -p status="In Progress" -o json
```

## Incident response

```bash
ctx-cli mcp call incident_response -p serviceName=<name> -o json
ctx-cli mcp call get_incident_contacts -p serviceName=<name> -o json
```

## Entity search

```bash
ctx-cli mcp call find_entities -p query="<search>" -o json
ctx-cli mcp call find_entities -p query="<search>" -p entityTypes='["Service"]' -o json
ctx-cli mcp call get_entity_by_id -p id=<entity-id> -o json
```
