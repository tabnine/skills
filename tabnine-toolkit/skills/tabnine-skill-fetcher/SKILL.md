---
name: tabnine-skill-fetcher
description: Download and list Tabnine skills from a remote Tabnine server. Use when users ask to download skills, fetch skills, list available skills, get skills from Tabnine, install skills, or update skills from their Tabnine instance. Triggers include "download skills", "list skills from Tabnine", "fetch skill X", "what skills are available", "get me skill X from Tabnine", "update skills" or any task involving retrieving skills from a Tabnine server.
---

# Tabnine Skill Fetcher

List and download skills from a remote Tabnine server. Only downloads skills that need updating — if a skill already exists locally and is up to date, it is skipped.

## Credentials

Two values are required to authenticate with the Tabnine server:

- **TABNINE_HOST** — The hostname of the Tabnine instance (the user must know this).
- **TABNINE_TOKEN** — A personal access token for authentication.

### Obtaining TABNINE_TOKEN

1. Open `https://<TABNINE_HOST>` in a browser.
2. Navigate to **Settings** > **Access Tokens**.
3. Click **Generate token**.
4. Copy the token immediately (it will not be shown again).

### Providing Credentials

Credentials can be supplied in two ways:

**Option A: Credentials file**

Create a plain-text file with:

```
TABNINE_HOST=your-tabnine-host.example.com
TABNINE_TOKEN=your-token-here
```

Then tell the agent the file path. Lines starting with `#` are ignored.

**Option B: Environment variables**

Set `TABNINE_HOST` and `TABNINE_TOKEN` as environment variables before starting the agent.

### Resolving Credentials

Before running any script, verify that credentials are available.
If you can't find `TABNINE_HOST` and `TABNINE_TOKEN` env vars, and the user did not provide a credentials file, ask the user:

1. Do you have `TABNINE_HOST` and `TABNINE_TOKEN` set as environment variables?
2. Or do you have a credentials file? If so, what is the path?

If neither exists, instruct them to:

- Obtain `TABNINE_TOKEN` following the steps above.
- Create a credentials file in the format shown above, or set the environment variables.
- Let you know the credentials file path once ready or that the environment variables are set.

DO NOT ask the user to paste their token into the chat.
DO NOT read the credentials file into the chat.

## Scripts

### `list_skills.py` — List available skills

**Usage:**

```
python scripts/list_skills.py [--creds-file <path>]
```

**Input:**

| Argument | Required | Description |
|---|---|---|
| `--creds-file <path>` | No | Path to a credentials file. Falls back to env vars if omitted. |

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
python scripts/get_skill.py <url> [--creds-file <path>] [--output-dir <dir>]
```

**Input:**

| Argument | Required | Description |
|---|---|---|
| `<url>` | Yes | The download URL from the `list_skills.py` output. |
| `--creds-file <path>` | No | Path to a credentials file. Falls back to env vars if omitted. |
| `--output-dir <dir>` | No | Base directory for extracted skills. Defaults to `.agents/skills/`. |

**Behavior:**

1. Downloads the zip archive from the given URL.
2. Extracts it into `<output-dir>/<skill-name>/`.
3. Deletes the zip archive.
4. Creates symlinks at `.cursor/skills/<skill-name>` and `.claude/skills/<skill-name>` pointing to the extracted directory.

The skill name is derived from the last path segment of the URL.

## Workflow

1. **Resolve credentials** — Verify that `TABNINE_HOST` and `TABNINE_TOKEN` are available via env vars or a credentials file. If missing, ask the user (see Resolving Credentials above).
2. **List skills** — Run `list_skills.py` to get all available skills with their names, versions, and download URLs.
3. **Check versions** — For each skill in the list, check whether it already exists locally by reading the `.version` file in `.agents/skills/<skill-name>/`. Compare the local version against the version from the list response. Skip any skill whose local version matches the server version.
4. **Download updated skills** — Run `get_skill.py <url>` for each skill that is new or has a changed version.
5. **Report results** — Summarize what was downloaded and where, including the paths to `.agents/skills/<skill-name>/` and the symlinks in `.cursor/skills/` and `.claude/skills/`.

### Versioning

Each skill zip contains a `.version` file with the server's package version (e.g., `1.188.0`). After extraction, this file is preserved alongside `SKILL.md` in the local skill directory. On subsequent syncs, the agent reads this file and compares it against the version from the list response to decide whether to re-download.
