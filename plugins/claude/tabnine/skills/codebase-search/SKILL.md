---
name: codebase-search
description: >
  Use when searching, exploring, or investigating remote repositories using Tabnine's Context Engine.
  Activates for cross-repo questions, service architecture questions, PR impact analysis,
  or when verifying usage of external APIs against real codebase examples.
---

When the user asks about remote codebases, always use the `tabnine-context` MCP tools to search and explore. Do not guess or rely on training data — fetch real information from the indexed repositories.

## When to Use This Skill

- Asks about code in a remote repository or across multiple repos
- Needs architectural understanding of a service or system
- Is reviewing code or a PR and wants to assess cross-repo impact
- Is working with an external API and needs real usage examples from the codebase

## How to Search

The `tabnine-context` MCP server exposes tools for:

- **Repository discovery** — list what repos are indexed; always start here
- **Code search** — semantic and lexical search across repos, symbol lookup, file search
- **File access** — browse repo structure, fetch file contents
- **API discovery** — search OpenAPI specs and service summaries, query specs, grep assets

Always start with semantic search to cast a wide net, then narrow down with symbol or file tools. If the first search doesn't return useful results, try different queries or filters before giving up. Cross-reference multiple repos when investigating service interactions.
