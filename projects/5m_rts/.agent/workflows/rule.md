---
description: guidelines
---

<instructions>
- Always aim for the minimal change to the codebase
- Avoid changing signatures unless absolutely necessary. Use alternative function or overload instead.
- Think critically on previous conversations and always point out potential problems.
- You MUST make a plan and seek confirmation before starting to edit any code.
</instructions>

<constraints>
- Code style: use guard clause and early return instead of nested indents
  1. Avoid nested `if/else` blocks.
  2. Check for failure conditions first and return early.
- Follow DRY and KISS
</constraints>