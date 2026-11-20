---
name: House Update
description: Add to or change an existing House Manual. Verbs cover adding assets, logging receipts, setting the closing date, importing a Home Assistant export, updating per-page tags, closing known issues, and starting projects. Use when the user mentions changing, adding, logging, or updating anything about their house.
---

# House Update

Changes an existing house manual built with the `haus-setup` skill. Same quality bar, same approval-first rule: show the exact proposed change, get a yes, write, rebuild, verify, commit.

Read `skills/haus-setup/SKILL.md` for the repo layout, the markdown contracts the build parser depends on, the sourcing rules, the must-have list that defines a complete manual, and the phase 0 consent rule (never open a source the user declined) before the first run of a session.

## How every update runs

1. Identify the verb from the user's words (list below).
2. Show the proposed change: the exact JSON or markdown diff.
3. On approval: write the files, run `python3 site/build.py`, verify the affected page, commit.
4. Never push. Never invent a fact. Unknown stays TBD. No em dashes in any written text.

## Verbs

### add-asset

"I added a new water heater" / "we got a second fridge". Append a row to `site-data/profile.json` `systems` with `name`, `detail`, `page` (the most relevant existing system page). For a whole new system category, extend `SYSTEMS` in `site/build.py` and create the md file per the setup contract, then update the files table in `00-index.md`. When the asset needs care instructions, add sourced lines to its system md file's Cadence table and prose.

### log-receipt

A receipt photo, PDF, or email text. Extract: item, vendor, purchased date, warranty term. Append to `profile.json` (asset row with warranty end in the detail string as `warranty through YYYY-MM-DD (from receipt)`), and put care-relevant facts into the system md when they change maintenance. Offer the email path: with permission, search the user's mail via the `himalaya` skill for the order or registration email; cite nothing private into the manual, just the facts.

### set-closing-date

The real closing date. Set `profile.json` `identity.closing_date` in `YYYY-MM-DD`. Every deadline chip on every page goes live from this. Confirm the deadlines page sections match the warranty book years (1, 2, 5, 10) before writing.

### import-ha

A Home Assistant export (automations, devices, dashboard). Summarize what the house does by itself in household language and write it into `profile.json` `automation` (`status`, `detail`). If the user wants a full automation page, create it as a new system md per the setup contract and extend `SYSTEMS` in `site/build.py`. Say what was imported and what was skipped; never paste YAML into the site.

### update-tags

Per-page tag strips. Edit `site-data/tags.json` only. Relevance rule: each page shows only the facts that matter to that system. Keep chips short and uppercase.

### close-issue

A known issue is resolved. Rewrite its item in the `## The three known issues` section of `00-index.md`: keep the item, append `Resolved <date>: <one line how>.` in the item text. If the issue list shrinks or grows, update the section heading's count and tell the user which offsets (30d, 1y, 2y) the remaining items now map to, since the first three items drive the Overview cards in order.

### complete-pass

The room-by-room completeness pass from the setup skill against an existing manual: walk the HUD toolkit's room checklist plus the must-have list, list every gap (areas never covered, systems recorded without a Cadence table, appliances missing warranty rows), and propose the writes that close them. Cite the anchors for anything new.

### start-project

A repair, upgrade, or improvement project ("painting the exterior", "redoing the beds"). Add a short project section to the most relevant system md: goal, plan steps, what was done, dates, and links to any vendor documents. On completion, fold the durable facts into the system md prose and the profile, and mark the project section done with the date.

### update-knowledge

New facts learned (county watering rules changed, a new fertilizer ordinance). Verify against the primary source, update the md file, keep every claim linked, and note the verification date in the file's `Home:` line.

## Verification per run

- Build succeeds and the affected page changed (`grep` for the new fact in `site/<slug>.html`).
- `grep -r '\.md)' site/*.html` finds nothing.
- If any `site/assets/` file changed, bump its `?v=` in the shell template in `site/build.py`.
- Commit message names the verb and the target, for example `haus-update log-receipt: rheem water heater`.
