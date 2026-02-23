---
name: codebase-search
description: Use when searching, exploring, or investigating remote repositories using Tabnine's Context Engine. Activates for cross-repo questions, service architecture questions, PR impact analysis, or when verifying usage of external APIs against real codebase examples.
---

When the user asks about remote codebases, search and explore using the tools provided by the `tabnine-context` MCP server.

## When to Use This Skill

- Asks about code in a remote repository or across multiple repos
- Needs architectural understanding of a service or system
- Is reviewing code or a PR and wants to assess cross-repo impact
- Is working with an external API and needs real usage examples from the codebase

## How to Search

Use the tools available from the `tabnine-context` MCP server. They cover:

- **Repository discovery** — list what repos are indexed
- **Code search** — semantic and lexical search across repos, symbol lookup, file search
- **File access** — browse repo structure, fetch file contents
- **API discovery** — search OpenAPI specs and service summaries, query specs, grep assets

Start broad with semantic search, then narrow down using symbol or file tools. Cross-reference multiple repos when investigating service interactions.
