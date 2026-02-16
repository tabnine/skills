# Project Scope Installation

Skills are installed within the current project directory. Use this when skills are specific to a single project or should be version-controlled with the project.

## Paths

| Purpose | Path |
|---|---|
| Skill storage | `./.agents/skills/<skill-name>/` |
| Claude symlink | `./.claude/skills/<skill-name>` -> `./.agents/skills/<skill-name>/` |
| Cursor symlink | `./.cursor/skills/<skill-name>` -> `./.agents/skills/<skill-name>/` |

## Version checking

Read `./.agents/skills/<skill-name>/.version` to determine the currently installed version.

## Script usage

```
python scripts/get_skill.py <url> --scope project
```
