---
name: ctx-guidelines
description: >
  Apply and audit a team's coding standards with ctx-cli — fetch managed coaching
  guidelines to write or review code to spec, and inspect discovered AI-guideline
  files (CLAUDE.md, .cursorrules, AGENTS.md) for coverage and cross-repo drift.
allowed-tools: Bash(ctx-cli:*), Bash(curl:*)
---

# Coding guidelines

> **Prerequisites:** requires `ctx-cli` installed and authenticated. If it isn't, or you
> haven't run the once-per-session version check, see the [`ctx`](../ctx/SKILL.md) skill first.

Two related but distinct surfaces live here:

1. **Managed coaching guidelines** (`get_coding_guidelines`) — the curated `/coaching-guidelines` catalog of team standards. Use when **writing** or **reviewing** code. See [Managed guidelines](#managed-guidelines--get_coding_guidelines).
2. **Discovered guideline sources** (`get_guideline_sources`) — the `CLAUDE.md` / `.cursorrules` / `AGENTS.md` files actually present across repos. Use for **coverage and drift** questions. See [Guideline sources](#guideline-sources--get_guideline_sources).

The first is the curated rule set; the second is what's actually checked into repos. They are different tools answering different questions.

---

## Managed guidelines — `get_coding_guidelines`

This is the tool for fetching your org's **managed coding guidelines** so you can apply them when **writing** or **reviewing** code. It's a curated set of team standards (security rules, error-handling patterns, code-quality conventions, …) maintained in the Context Engine.

Always **fetch the relevant guidelines first** — do not rely on training data or guess what the team's rules are. Then check the code against what the tool returns.

### When to reach for this

| Task | Call |
|---|---|
| Apply team standards while writing/reviewing code | `get_coding_guidelines` (filter by `language` / `category`) |
| "What are our rules for `<language>`?" | `get_coding_guidelines -p language=<lang>` |
| Only a topic (security, error handling, …) | `get_coding_guidelines -p category=<cat>` |
| Only the build-breaking rules | `get_coding_guidelines -p severity=critical` (and `error`) |
| Find one rule by keyword | `get_coding_guidelines -p search=<text>` |

### Fetch

All filters are optional and applied **server-side**; call with none to enumerate every enabled guideline (default `take=100`).

```bash
# Everything enabled for the tenant
ctx-cli mcp call get_coding_guidelines -o json

# Guidelines for a language — matches that language OR rules tagged "all"
ctx-cli mcp call get_coding_guidelines -p language=Python -o json

# One category (e.g. security, error-handling, code-quality)
ctx-cli mcp call get_coding_guidelines -p category=security -o json

# Build-breakers only
ctx-cli mcp call get_coding_guidelines -p severity=critical -o json

# Find a specific rule (matches name, description, and guidelineId)
ctx-cli mcp call get_coding_guidelines -p search="input validation" -o json

# Page through a large set
ctx-cli mcp call get_coding_guidelines -p take=50 -p skip=50 -o json
```

Filters:

| Param | Notes |
|---|---|
| `language` | **Singular.** Matches guidelines whose languages include it OR are tagged `all`. Honored server-side but not shown by `mcp describe`. |
| `category` | Exact match, e.g. `security` \| `error-handling` \| `code-quality`. |
| `severity` | Exact: `info` \| `warning` \| `error` \| `critical`. |
| `search` | `ILIKE` over `name`, `description`, and `guidelineId`. |
| `take` | Default `100`. |
| `skip` | Offset for paging. Honored server-side but not shown by `mcp describe`. |
| `packId` | Restrict to a single guideline pack. Honored server-side but not shown by `mcp describe`. |

`get_coding_guidelines` is a **tier-2** tool, so it appears only under `ctx-cli mcp list --tier all -s guidelines` — but `ctx-cli mcp call get_coding_guidelines` reaches it regardless of tier.

### Reading the output

The tool returns **markdown text**, not structured JSON entities. With `-o json` the markdown arrives as a single string on `.result` — read it directly; **do not** pipe it to `jq` expecting per-guideline fields (there is no entity array to filter). Use the server-side params above to narrow the set instead.

Each guideline block carries:

- `guidelineId` (e.g. `TabnineDefaults::Flask::FlaskInputSecurity`) and a human description
- `severity` (`info` / `warning` / `error` / `critical`) and `category`
- `languages` (omitted when the rule applies to `all`) and `libraries`
- `goodExample` / `badExample` code blocks where defined

### Applying them in a review

1. Fetch the guidelines relevant to the file's language / topic **before** judging the code.
2. Flag violations by their `guidelineId` (or name) and `severity`.
3. Lead with `critical` and `error` findings — those are the build-breakers (severity maps to a per-tenant `breaksBuild` setting); `warning` / `info` are advisory.
4. Show the fix using the guideline's own `goodExample` / `badExample` when it has them.

---

## Guideline sources — `get_guideline_sources`

This is the tool for inspecting the **AI-guideline files discovered across the org's repositories** — `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, Copilot/Windsurf/Cline instructions, and friends. Use it to answer coverage and consistency questions: which repos have (or lack) guideline files, and whether those files have drifted apart across repos.

> These are the **discovered** files actually present in repos. They are distinct from the **managed** coaching guidelines above (the curated `/coaching-guidelines` catalog) — for those, use [`get_coding_guidelines`](#managed-guidelines--get_coding_guidelines).

### When to reach for this

| Task | Call |
|---|---|
| "What % of our repos have guideline files? Which tools?" | `get_guideline_sources` (mode `coverage`, default) |
| "Do our `.cursorrules` / `CLAUDE.md` diverge across repos?" | `get_guideline_sources -p mode=inconsistencies` |
| "Which repos are missing a `CLAUDE.md`?" | `get_guideline_sources -p mode=inconsistencies` (look for `incomplete_coverage`) |
| "List the discovered `<tool>` files" | `get_guideline_sources -p mode=sources -p sourceType=<tool>` |
| "What guideline files exist for team / workspace X?" | `get_guideline_sources -p mode=sources -p level=<scope> -p id=<uuid>` |

### Fetch

```bash
# Org-wide coverage summary (default mode)
ctx-cli mcp call get_guideline_sources -o json

# Inconsistencies: divergent content + missing coverage across repos
ctx-cli mcp call get_guideline_sources -p mode=inconsistencies -o json

# List discovered files of one tool
ctx-cli mcp call get_guideline_sources -p mode=sources -p sourceType=claude -o json

# Scope inconsistencies / listing to a team or workspace (id required for non-org scope)
ctx-cli mcp call get_guideline_sources -p mode=inconsistencies -p level=team -p id=<uuid> -o json
ctx-cli mcp call get_guideline_sources -p mode=sources -p level=workspace -p id=<uuid> -o json
```

Parameters:

| Param | Notes |
|---|---|
| `mode` | `coverage` (default) \| `inconsistencies` \| `sources`. Unknown values fall back to `coverage`. |
| `level` | Scope for `inconsistencies` / `sources`: `repo` \| `workspace` \| `team` \| `organization` (default). |
| `id` | Scope id (data-source / workspace / team UUID). **Required when `level` is not `organization`.** |
| `sourceType` | Filter discovered files by tool: `claude`, `cursor`, `copilot`, `agents`, `windsurf`, `cline`, … |
| `search` | Match discovered files by path / repository / content. |
| `take` | Max files returned in `sources` mode (default 100). |

`get_guideline_sources` is a **tier-2** tool, so it appears only under `ctx-cli mcp list --tier all -s guideline` — but `ctx-cli mcp call get_guideline_sources` reaches it regardless of tier.

### What each mode returns

All modes return **markdown text** (not JSON entities). With `-o json` the markdown arrives as a single string on `.result` — read it directly; **do not** `jq` it. Use the params above to narrow.

- **`coverage`** — `reposWithGuidelines / totalRepos (percent)`, repos without any file, and a per-source-type table (files + repos per tool).
- **`inconsistencies`** — one block per finding:
  - `divergent_content` (severity `warning`): the same tool's file has **different content across repos** (hash mismatch) — lists the affected files/repos.
  - `incomplete_coverage` (severity `info`): some repos are **missing** a file that most repos in scope have — lists the repos without it.
- **`sources`** — a table of the discovered files (source type, repository, path, URL).

### How to use the findings

1. Start with `coverage` to see the lay of the land, then `inconsistencies` to find drift/gaps.
2. For a `divergent_content` finding, fetch the actual files (`mode=sources -p sourceType=<tool>`) or open their URLs to compare and propose a reconciled version.
3. For `incomplete_coverage`, the missing repos are candidates for adding the guideline file — you can seed one from the org's **managed** guidelines (see [Managed guidelines](#managed-guidelines--get_coding_guidelines)).
