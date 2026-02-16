# User Scope Installation

Skills are installed in the user's home directory. Use this when skills should be available across all projects for the current user.

## Paths

| Purpose | Path |
|---|---|
| Skill storage | `~/.agents/skills/<skill-name>/` |
| Claude symlink | `~/.claude/skills/<skill-name>` -> `~/.agents/skills/<skill-name>/` |
| Cursor symlink | `~/.cursor/skills/<skill-name>` -> `~/.agents/skills/<skill-name>/` |

## Version checking

Read `~/.agents/skills/<skill-name>/.version` to determine the currently installed version.

## Script usage

```
python scripts/get_skill.py <url> --scope user
```
