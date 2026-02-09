---
name: tabnine-skill-fetcher
description: Download and list Tabnine skills from a remote Tabnine server. Use when users ask to download skills, fetch skills, list available skills, get skills from Tabnine, install skills, or update skills from their Tabnine instance. Triggers include "download skills", "list skills from Tabnine", "fetch skill X", "what skills are available", "get me skill X from Tabnine", or any task involving retrieving skills from a Tabnine server.
---

# Tabnine Skill Fetcher

List and download skills from a remote Tabnine server.

## Prerequisites

Two values are required to authenticate with the Tabnine server:

- **TABNINE_HOST** - The hostname of the Tabnine instance (the user must know this).
- **TABNINE_TOKEN** - A personal access token for authentication.

### Obtaining TABNINE_TOKEN

1. Open `https://<TABNINE_HOST>` in a browser.
2. Navigate to **Settings** > **Access Tokens**.
3. Click **Generate token**.
4. Copy the token immediately (it will not be shown again).

### Providing Credentials

Credentials can be supplied in two ways. A **credentials file** is recommended since environment variables require restarting the agent.

**Option A: Credentials file (recommended)**

Create a plain-text file with:

```
TABNINE_HOST=your-tabnine-host.example.com
TABNINE_TOKEN=your-token-here
```

Then tell the agent the file path. Lines starting with `#` are ignored.

**Option B: Environment variables**

Set `TABNINE_HOST` and `TABNINE_TOKEN` as environment variables before starting the agent.

## Checking for Credentials

Before running any script, verify that credentials are available.
If you can't find `TABNINE_HOST` and `TABNINE_TOKEN` env vars, and the user did not provide a credentials file, ask the user:

1. Do you have `TABNINE_HOST` and `TABNINE_TOKEN` set as environment variables?
2. Or do you have a credentials file? If so, what is the path?

If neither exists, instruct them to:

- Obtain `TABNINE_TOKEN` following the steps above.
- Create a credentials file in the format shown above, or set the environment variables and restart the agent.
- Let you know the credentials file path once ready.

Do NOT ask the user to paste their token into the chat.

## Scripts

### List available skills

```
python scripts/list_skills.py [--creds-file <path>]
```

Lists all skills available on the Tabnine server.

### Download a skill

```
python scripts/get_skill.py <url> <skill-name> [--creds-file <path>] [--output-dir <dir>]
```

Downloads a skill using the URL returned by `list_skills.py`. The `skill-name` is used for the output file name. Output defaults to `.yuvalili/skills/<skill-name>/` in the current working directory.

## Workflow

1. Verify credentials are available (env vars or credentials file).
2. Run `list_skills.py` to list available skills (returns skill names and URLs).
3. Run `get_skill.py <url> <skill-name>` for each skill the user wants to download, using the URL from step 2.
4. Report what was downloaded and where.
