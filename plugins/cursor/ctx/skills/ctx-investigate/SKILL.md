---
name: ctx-investigate
description: >
  Investigate services and assess change impact with ctx-cli — one-call service
  investigation (deps, owners, runbooks), blast radius, incident response,
  dependency/package safety checks, package migration, and business-flow
  understanding.
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# Service investigation & change impact

> **Prerequisites:** requires `ctx-cli` installed and authenticated. If it isn't, or you
> haven't run the once-per-session version check, see the [`ctx`](../ctx/SKILL.md) skill first.

These are the **tier-1 composites** — each bundles several primitive calls into one
answer. Prefer them when one matches your intent; drop to the primitives in
[`ctx-search`](../ctx-search/SKILL.md) only when no composite covers the question or you
need a specific narrow slice.

## Pick a composite by intent

| Intent | Tool | Notes |
|---|---|---|
| "How does service X work / what does it depend on / who owns it?" | `investigate_service -p serviceName=<name>` | Returns service, deps, dependents, ownership (team/oncall/slack/pagerduty), ADRs, runbooks, flows, incidents, Jira/GitLab issues in one call. Supports partial name match. |
| "What breaks if I change X?" | `blast_radius -p target=<name>` | Param is `target` (not `serviceName`). Returns risk score (LOW/MEDIUM/HIGH), transitive dependents, affected flows, teams-to-notify, recommendations. |
| "We're seeing errors in X — runbook + escalation" | `incident_response -p service=<name>` | Param is `service` (not `serviceName`). Optional `symptom=<text>` finds similar past incidents. |
| "Is package X safe / should I use it?" | `dependency_check -p packageName=<name>` | Vulnerabilities + upgrade history + migration examples. Returns `[]` on tenants where package data isn't indexed. |
| "How do I migrate from X to Y?" | `code_migration -p fromPackage=<pkg> -p toPackage=<pkg>` | Params are `fromPackage` / `toPackage`. Migration status, examples from teams who've done it. |
| "How does the <X> business flow work?" | `understand_flow -p flowName=<name>` | Flow steps, services involved, related ADRs and incidents. Returns `[]` on tenants without indexed flows. |
| "What's the context for this file?" | `get_file_context -p filepath=<path>` | Param is `filepath` (one word, lowercase). Returns ADRs, incidents, security patterns, experts, blast radius for the file's service. **Requires** `git-insights-analyzer` to have run on the repo — returns `[]` on tenants where it hasn't. |

## Quick start

```bash
# One-call investigation of a service (deps, owners, runbooks, incidents…)
ctx-cli mcp call investigate_service -p serviceName="CTX API Server" -o json

# What breaks if I change this service?
ctx-cli mcp call blast_radius -p target="CTX API Server" -o json

# Runbook + escalation for an active issue, with similar past incidents
ctx-cli mcp call incident_response -p service="CTX API Server" -p symptom="elevated 5xx" -o json

# Is this package safe to adopt?
ctx-cli mcp call dependency_check -p packageName="lodash" -o json

# How do teams migrate off package X?
ctx-cli mcp call code_migration -p fromPackage="moment" -p toPackage="date-fns" -o json
```

## Parameter gotchas (these bite)

The composites are inconsistent about their primary parameter name — confirm with
`ctx-cli mcp describe <tool>` whenever a call errors:

- `investigate_service` takes `serviceName`.
- `blast_radius` takes `target` (**not** `serviceName`).
- `incident_response` takes `service` (**not** `serviceName`).
- `code_migration` takes `fromPackage` / `toPackage` (**not** `from` / `to`).
- `get_file_context` takes `filepath` (one word, lowercase — **not** `filePath`).

## When a composite returns `[]`

Several composites depend on tenant-specific indexers having run:

- `understand_flow` / flow data → returns `[]` on tenants without indexed flows.
- `dependency_check` → returns `[]` where package data isn't indexed.
- `get_file_context` → requires `git-insights-analyzer`; returns `[]` otherwise.

When a composite comes back empty, fall back to the graph primitives in
[`ctx-search`](../ctx-search/SKILL.md) (`find_entities` → `traverse_edges`) — graph
adjacency still captures the underlying relationships even when the composite's
enriched view isn't available.
