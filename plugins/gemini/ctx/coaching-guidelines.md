# Coding guidelines (coaching)

This is the tool for fetching your org's **managed coding guidelines** via `ctx-cli`, so you can apply them when **writing** or **reviewing** code. The centerpiece is `get_coding_guidelines` — a curated set of team standards (security rules, error-handling patterns, code-quality conventions, …) maintained in the Context Engine.

Always **fetch the relevant guidelines first** — do not rely on training data or guess what the team's rules are. Then check the code against what the tool returns.

> These are the **managed** guidelines (the `/coaching-guidelines` catalog). They are distinct from **guideline sources** — the discovered `CLAUDE.md` / `.cursorrules` / `AGENTS.md` files in repos — which are not yet exposed through `ctx-cli`.

## When to reach for this

| Task | Call |
|---|---|
| Apply team standards while writing/reviewing code | `get_coding_guidelines` (filter by `language` / `category`) |
| "What are our rules for `<language>`?" | `get_coding_guidelines -p language=<lang>` |
| Only a topic (security, error handling, …) | `get_coding_guidelines -p category=<cat>` |
| Only the build-breaking rules | `get_coding_guidelines -p severity=critical` (and `error`) |
| Find one rule by keyword | `get_coding_guidelines -p search=<text>` |

## Fetch guidelines — `get_coding_guidelines`

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

## Reading the output

The tool returns **markdown text**, not structured JSON entities. With `-o json` the markdown arrives as a single string on `.result` — read it directly; **do not** pipe it to `jq` expecting per-guideline fields (there is no entity array to filter). Use the server-side params above to narrow the set instead.

Each guideline block carries:

- `guidelineId` (e.g. `TabnineDefaults::Flask::FlaskInputSecurity`) and a human description
- `severity` (`info` / `warning` / `error` / `critical`) and `category`
- `languages` (omitted when the rule applies to `all`) and `libraries`
- `goodExample` / `badExample` code blocks where defined

## Applying them in a review

1. Fetch the guidelines relevant to the file's language / topic **before** judging the code.
2. Flag violations by their `guidelineId` (or name) and `severity`.
3. Lead with `critical` and `error` findings — those are the build-breakers (severity maps to a per-tenant `breaksBuild` setting); `warning` / `info` are advisory.
4. Show the fix using the guideline's own `goodExample` / `badExample` when it has them.
