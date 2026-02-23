---
name: coding-guidelines
description: Use when reviewing code, writing new code, or answering questions about coding standards. Activates when the user wants to apply team guidelines, check if code follows best practices, or understand the rules and recommendations defined for a specific language.
---

When the user needs to apply or check coding guidelines, use the `tabnine-coaching` MCP tool to fetch the relevant rules before responding. Do not guess or rely on training data — always fetch the actual guidelines defined for the team.

## When to Use This Skill

- User is writing or reviewing code and wants to follow team standards
- User asks what the guidelines or rules are for a given language
- User asks whether their code follows best practices
- User is doing a code review and wants to flag guideline violations

## How to Use

Use the `get_guidelines` tool from the `tabnine-coaching` MCP server:

- **`language`** — pass the relevant programming language to filter results (e.g. `TypeScript`, `Python`, `Java`)
- **`skip` / `take`** — use for pagination if there are many guidelines; fetch all pages before responding

Fetch guidelines first, then apply them to the code at hand. When reviewing code, explicitly reference the guideline name or description when flagging an issue.
