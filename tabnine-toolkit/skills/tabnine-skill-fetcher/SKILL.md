---
name: tabnine-skill-fetcher
description: Download and list Tabnine skills from a remote Tabnine server. Use when users ask to download skills, fetch skills, list available skills, get skills from Tabnine, install skills, or update skills from their Tabnine instance. Triggers include "download skills", "list skills from Tabnine", "fetch skill X", "what skills are available", "get me skill X from Tabnine", "update skills" or any task involving retrieving skills from a Tabnine server.
---

# Tabnine Skill Fetcher

List and download skills from a remote Tabnine server. Only downloads skills that need updating — if a skill already exists locally and is up to date, it is skipped.

## Credentials

Two environment variables are required to authenticate with the Tabnine server:

- **TABNINE_HOST** — The hostname of the Tabnine instance (the user must know this).
- **TABNINE_TOKEN** — A personal access token for authentication.

### Obtaining TABNINE_TOKEN

1. Open `https://<TABNINE_HOST>` in a browser.
2. Navigate to **Settings** > **Access Tokens**.
3. Click **Generate token**.
4. Copy the token immediately (it will not be shown again).

### Resolving Credentials

Before running any script, verify that `TABNINE_HOST` and `TABNINE_TOKEN` environment variables are set.
If either is missing, ask the user to set them and restart the agent.

DO NOT ask the user to paste their token into the chat.
DO NOT print the token in the terminal or logs.

## Scripts

### `list_skills.py` — List available skills

**Usage:**

```
python scripts/list_skills.py
```

**Input:** None (reads `TABNINE_HOST` and `TABNINE_TOKEN` from environment variables).

**Output:**

A JSON array of skill objects, each containing a name, version, and download URL:

```json
[
  {
    "name": "skill-name",
    "version": "1.0.0",
    "url": "https://<TABNINE_HOST>/path/to/skill.zip"
  },
  {
    "name": "another-skill-name",
    "version": "2.0.0",
    "url": "https://<TABNINE_HOST>/path/to/another-skill.zip"
  }
]
```

### `get_skill.py` — Download a skill

**Usage:**

```
python scripts/get_skill.py <url> --scope <project|user> [--output-dir <dir>]
```

**Input:**

| Argument | Required | Description |
|---|---|---|
| `<url>` | Yes | The download URL from the `list_skills.py` output. |
| `--scope <project\|user>` | Yes | Install scope. See [references/project-scope.md](references/project-scope.md) and [references/user-scope.md](references/user-scope.md). |
| `--output-dir <dir>` | No | Override base directory for extracted skills. |

Reads `TABNINE_TOKEN` from environment variables for authentication.

**Behavior:**

1. Downloads the zip archive from the given URL.
2. Extracts it into the appropriate `.agents/skills/<skill-name>/` directory based on scope.
3. Deletes the zip archive.
4. Creates symlinks at `.claude/skills/<skill-name>` and `.cursor/skills/<skill-name>` pointing to the extracted directory.

The skill name is derived from the last path segment of the URL.

## Workflow

1. **Resolve credentials** — Verify that `TABNINE_HOST` and `TABNINE_TOKEN` environment variables are set. If missing, ask the user to set them and restart the agent.
2. **Ask for install scope** — Ask the user whether to install skills at **project** scope (current project only) or **user** scope (available across all projects). See [references/project-scope.md](references/project-scope.md) and [references/user-scope.md](references/user-scope.md) for details on each scope.
3. **List skills** — Run `list_skills.py` to get all available skills with their names, versions, and download URLs.
4. **Check versions** — For each skill in the list, check whether it already exists by reading the `.version` file in the appropriate `.agents/skills/<skill-name>/` directory for the chosen scope. Compare the local version against the version from the list response. Skip any skill whose local version matches the server version.
5. **Download updated skills** — Run `get_skill.py <url> --scope <project|user>` for each skill that is new or has a changed version.
6. **Report results** — Summarize what was downloaded and where, including the paths to `.agents/skills/<skill-name>/` and the symlinks in `.claude/skills/` and `.cursor/skills/`.

### Versioning

Each skill zip contains a `.version` file with the server's package version (e.g., `1.188.0`). After extraction, this file is preserved alongside `SKILL.md` in the local skill directory. On subsequent syncs, the agent reads this file and compares it against the version from the list response to decide whether to re-download.
