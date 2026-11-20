# haus

This repo builds and maintains a homeowner's manual as a static site.

Skills live in `skills/`:

- `skills/haus-setup/SKILL.md`: run when the user asks to set up a new house, recreate the manual for another home, or rerun the wizard. It discovers the tools and sources available, researches the house behind the scenes, then runs a guided intake against a defined must-have list.
- `skills/haus-update/SKILL.md`: run when the user asks to change, add, log, or update anything about their house.

If this client has a native skills mechanism, the SKILL.md files register from `skills/` (OpenCode reads them via the `skills` entry in `opencode.json`; Claude Code via `skills/install.sh`). If it has none, read the relevant SKILL.md directly and follow it exactly, including approval-first writes and the sourcing rules.
