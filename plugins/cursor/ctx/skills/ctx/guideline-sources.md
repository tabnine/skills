# Guideline coverage & consistency (guideline-sources)

This is the tool for inspecting the **AI-guideline files discovered across the org's repositories** — `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, Copilot/Windsurf/Cline instructions, and friends. The centerpiece is `get_guideline_sources`. Use it to answer coverage and consistency questions: which repos have (or lack) guideline files, and whether those files have drifted apart across repos.

> These are the **discovered** files actually present in repos. They are distinct from the **managed** coaching guidelines (the curated `/coaching-guidelines` catalog) — for those, use [`coaching-guidelines.md`](./coaching-guidelines.md) and `get_coding_guidelines`.

## When to reach for this

| Task | Call |
|---|---|
| "What % of our repos have guideline files? Which tools?" | `get_guideline_sources` (mode `coverage`, default) |
| "Do our `.cursorrules` / `CLAUDE.md` diverge across repos?" | `get_guideline_sources -p mode=inconsistencies` |
| "Which repos are missing a `CLAUDE.md`?" | `get_guideline_sources -p mode=inconsistencies` (look for `incomplete_coverage`) |
| "List the discovered `<tool>` files" | `get_guideline_sources -p mode=sources -p sourceType=<tool>` |
| "What guideline files exist for team / workspace X?" | `get_guideline_sources -p mode=sources -p level=<scope> -p id=<uuid>` |

## Fetch — `get_guideline_sources`

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

## What each mode returns

All modes return **markdown text** (not JSON entities). With `-o json` the markdown arrives as a single string on `.result` — read it directly; **do not** `jq` it. Use the params above to narrow.

- **`coverage`** — `reposWithGuidelines / totalRepos (percent)`, repos without any file, and a per-source-type table (files + repos per tool).
- **`inconsistencies`** — one block per finding:
  - `divergent_content` (severity `warning`): the same tool's file has **different content across repos** (hash mismatch) — lists the affected files/repos.
  - `incomplete_coverage` (severity `info`): some repos are **missing** a file that most repos in scope have — lists the repos without it.
- **`sources`** — a table of the discovered files (source type, repository, path, URL).

## How to use the findings

1. Start with `coverage` to see the lay of the land, then `inconsistencies` to find drift/gaps.
2. For a `divergent_content` finding, fetch the actual files (`mode=sources -p sourceType=<tool>`) or open their URLs to compare and propose a reconciled version.
3. For `incomplete_coverage`, the missing repos are candidates for adding the guideline file — you can seed one from the org's **managed** guidelines (see [`coaching-guidelines.md`](./coaching-guidelines.md)).
