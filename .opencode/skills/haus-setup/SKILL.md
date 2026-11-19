---
name: House Setup
description: Bootstrap a complete homeowner manual for any house. Runs the intake interview, parses documents, researches each system with primary sources, writes the knowledge markdown and data files, and rebuilds the static site. Use when the user asks to set up a new house, recreate this manual for another home, or rerun the wizard.
---

# House Setup

Recreates the House Manual for any house at the same quality bar as the original build (a 2025-26 Pulte Yorkshire in Florida). The product is: one sourced markdown file per system, `site-data/profile.json` + `site-data/tags.json`, and a rebuilt static site. Approval-first: propose every file change and get the user's yes before writing anything.

The quality bar is the product. A manual without inline sources is a failed run.

## Repo layout and build contracts

Read these before writing anything:

- `site/build.py` is the generator: one implementation of a swappable contract. The repo README defines the input and output shapes; any generator in any language that honors them works, because the runtime, the skills, and the deploy steps only ever see the outputs. Markdown files live at repo root. The build parses specific section shapes, so the contracts below are load-bearing, not style preferences.
- `site-data/profile.json` drives the House Profile page. `site-data/tags.json` drives the per-page tag strips.
- Run `python3 site/build.py` from the repo root. It prints the page count and must succeed with zero errors.
- Generated pages land in `site/`. Regenerate `site/assets/now.json` and `site/assets/search.json` automatically by running the build; never hand-edit them.
- When a house needs a different system list, update `SYSTEMS` and `ALL_DOCS` in `site/build.py` first, keep slugs one word (`slug.md` becomes `slug.html`), and align the rail plus tiles automatically.

### Markdown contracts the parser depends on

1. Each system file starts with `# Title` and lives at repo root as `<slug>.md`. Partial houses build fine: missing system files are skipped, so write systems incrementally.
2. Every system file needs a maintenance table whose header row contains the word `Cadence`, typically `| Cadence | Task | DIY or pro |`. Rows whose first cell contains `Monthly` or `Quarterly` become that page's ROUTINE panel. Without this table the page has no routine block.
3. `00-index.md` sections split on `## ` headings. Required sections and their shapes:
   - `## Files in this knowledge base`: a table `| [slug.md](slug.md) | one-line scope |`, one row per file. Rows become the Overview tiles.
   - `## The N known issues (act in warranty year one)` with N the honest count: a numbered list where every item begins with `**Title.**` then the detail. The build matches on `known issues` in the heading, and the first three items map in order to the Overview issue cards with deadline offsets 30d, 1y, 2y; extra issues show in prose only.
   - `## 12-month maintenance calendar` (a climate suffix like `(Florida-tuned)` is welcome; the build matches on the heading prefix): a table `| Month | Tasks |` with all twelve months, tasks separated by `; `. Inside the same section, two h3 bullet lists: `### Recurring core (every month, all year)` and `### Recurring quarterly`. These feed the home page's month panel (month names must be the full English month names).
   - `## File-before-warranty-expires checklist`: h3 subsections `### Within 30 days of closing (or now, if still open)`, `### Closing date + 1 year (file at least a month before)`, and the 2, 5, and 10 year equivalents, plus `### Insurance calendar (parallel, not warranty)`. Task items are `- [ ] text` checkboxes; they persist in the browser per user.
   - `## Most-used links`: a short link list shown on the Overview.
   - A line beginning `Property:` near the top becomes the hero blurb.
4. Cross-file links written as `[slug.md](slug.md)` auto-rewrite to the page URL. Use exactly the filename.
5. First paragraph of each file beginning `Home:` renders as the muted context strip. A paragraph beginning `Related files:` renders as the SEE ALSO chip row.

### Data schemas

`site-data/profile.json`:

```json
{
  "identity": {"builder": "", "plan": "", "built": "", "closing_date": "", "lot": "", "area": "", "county": ""},
  "house": {"stories": 0, "sqft": "", "floor_plan": "", "survey": ""},
  "systems": [{"name": "", "detail": "", "page": "slug.html"}],
  "yard": {"lawn": "", "trees": "", "lawn_company": "", "watering": ""},
  "automation": {"status": "", "detail": ""},
  "documents": [{"label": "", "status": "", "unlocks": ""}]
}
```

`site-data/tags.json`: `{"<slug>": ["CHIP TEXT", ...]}`. Per-page relevance rule: a page shows only the facts that matter to that system. The roof page never mentions the pool; the HVAC page does not mention the cage.

## Phase 1: intake interview

Ask these in one pass, accept partial answers, and record what is still unknown as TBD rather than guessing:

1. Address or ZIP (and county if known). Drives the location pack.
2. Builder and plan name, or custom. Cookie-cutter plans (Pulte, Lennar, DR Horton, KB, Taylor Morrison) are findable on the web: search the plan name plus the builder, find elevations and standard inclusions, and cite what you find. Label the plan details as inference when the builder has not confirmed them for this specific house.
3. Closing date, or a closing packet PDF to parse it from.
4. Systems walkthrough, one at a time:
   - HVAC: brand and model, or a photo of the data plate. Filter size if known.
   - Water: count every unit, fuel type, and what it serves (a pool heater is a separate unit).
   - Appliances: brand, model, purchase source. Offer the email lookup path: with permission, search the user's mail via the `himalaya` skill for order confirmations and warranty registrations. Otherwise receipts, photos, or manual entry.
   - Exterior: siding material and manufacturer if known, roof material and age, irrigation, trees by count and type.
   - Pool, cage, generator, softener, water treatment, pest contract: present or absent, with details.
5. Home automation: is there a Home Assistant or similar export? Ask for it now, use it in phase 4.
6. Documents: closing packet, floor plan, survey. For each, tell the user what it unlocks and ask where they want it stored: the repo `docs/` folder (private, local) or a link they provide. Never copy a document into `site/`: everything there is published.
7. Known issues: anything visible, recurring, or worrying. These become the issue cards.
8. Who uses the manual: household members. Sets the tone; the site assumes non-technical readers.

## Phase 2: research (the quality bar)

Per system, research and write the md file. Rules, in order of importance:

- Primary sources only for claims: manufacturer care and warranty PDFs, the builder's warranty book, the state extension service (UF/IFAS in Florida; the equivalent land-grant university per state), FEMA and county code pages, the water management district for watering rules. No blogger recaps as the sole source for a factual claim.
- Every claim carries an inline markdown link to its source. A claim without a link is a bug.
- Label estimates as estimates and inferences as inferences, inline.
- Costs are ranges labeled as estimates, typical for the county's metro area.
- No em dashes anywhere, in any file.
- County hazard pack: what this county actually prepares for (hurricane season in Gulf-coast Florida, winter and snow load up north, wildfire in the west, earthquake retrofits on the west coast). Search the county's own emergency management pages and cite them.
- Watering rules come from the water management district's current order, with its expiry date. Fertilizer blackout windows come from the county ordinance.
- The builder's warranty book is a required source when a builder exists: get the actual national book PDF, cite section numbers for coverage windows, and build the deadlines section from it.
- Manufacturer care rules: find the actual care bulletin or installation PDF (for example James Hardie's TB20 and HZ10 documents, GAF and Owens Corning shingle care). If the manufacturer is unknown, include both common brands and say so.

## Phase 3: write the files

1. Write or update `site-data/profile.json` from the intake. Every unknown stays TBD, never invented.
2. Write `site-data/tags.json` per the relevance rule.
3. Write one md file per system with: `Home:` context line, `Related files:` line, a system snapshot, known issues with warranty angles when any, manufacturer care rules, the Cadence maintenance table, DIY vs pro with cost estimates, what the builder warranty covers for this system, and sources on every claim.
4. Rewrite `00-index.md` with all the required sections from the contract list, tuned to the county and the house.
5. Show the user the complete list of proposed writes and the diffs that matter. On approval, write, then build and verify. On refusal, adjust and re-propose.

## Phase 4: Home Assistant and documents, when provided

- HA export: summarize the automations in household language (what the house does by itself). Put the summary in `profile.json` `automation.detail`. A full automation map can become its own md page if the user wants one; add the page to `SYSTEMS` and the files table then.
- Closing packet, floor plan, survey: parse per the unlocks promised in the intake, store where the user chose in phase 1, and reflect the extracted facts in `profile.json` and the relevant md files. Closing date extracted from the packet replaces TBD in `identity.closing_date` and the deadlines page chip logic goes live.

## Phase 5: rebuild and verify

1. `python3 site/build.py` from the repo root. Zero errors.
2. Verify: every expected page exists; `grep -r '\.md)' site/*.html` finds nothing (all md links rewrote); every system page contains a Cadence table so the ROUTINE panel renders; the calendar table has all twelve months; the three-issue cards appear on the Overview.
3. Asset version bumps: if you edited any file under `site/assets/`, bump its `?v=` query in the shell template in `site/build.py` so browsers reload it.
4. Commit with a message naming the house and the phase. Never push, never force, never commit generated noise outside `site/` and `site-data/`.

## Non-negotiables

- Approval-first: no file is written without a proposed diff and a yes.
- Sources on every claim; estimates and inferences labeled; no em dashes.
- Nothing invented: TBD is a valid value and always better than a guess.
- Documents never land in `site/`, only in the repo `docs/` folder or the user's chosen link.
- No pushes to any remote, no account creation, no purchases, no contacting anyone.
