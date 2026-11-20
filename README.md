# haus

Fork or clone this repo, and it becomes your house's manual: two agent skills interview you and research your systems with primary sources, a swappable generator publishes a static site, and a publish kit puts it anywhere you want, from your own tailnet to a gated public URL to a single portable file.

It was built agent-first, for a real house: the skills encode the sourcing rules and every build contract learned while producing the original manual, so a fresh run for your house reproduces the same quality.

## The recommended path

1. **Fork or clone this repo.** Your copy is your manual; keep it private, because once you run setup it will hold your house's details. A fork also gives you updates to the engine and skills whenever they land here.
2. **Open your clone in an agent.** Any capable agent works: the skills are plain markdown contracts in the standard Agent Skills format. OpenCode registers them from `skills/` via the project config; every other agent installs them with one command (below).
3. **Say "run haus-setup".** It interviews you: builder and plan, closing date, every system and appliance, lawn and trees, county, documents you can share. It researches each system with primary sources, proposes the markdown and data files, and writes them only after you approve.
4. **Publish from your clone:**
   ```sh
   python3 site/build.py            # your site, generated into site/
   python3 public/export_single.py  # the whole manual as one portable HTML file
   ```
   Then host it: serve `site/` on your LAN or tailnet, deploy to Cloudflare Pages behind email-gated Access (`public/deploy-cloudflare.md`), or carry the single-file artifact anywhere. Your clone can even host the live site on GitHub Pages, if you accept that Pages URLs are public.
5. **Keep it current** with "run haus-update": add an appliance, log a receipt, set the closing date, import a Home Assistant export, close a known issue. Every change is an approved write, a rebuild, and a commit.

## What's inside

```
skills/               haus-setup (bootstrap a house) + haus-update (change things) + install.sh
site/build.py         the generator: your markdown + data -> static pages in site/
site/assets/          the runtime: styles, search, month-and-season logic
site-data/            profile.json + tags.json schemas, with .example files
public/               the publish kit: deploy guide, single-file artifact export
docs/                 convention for private documents (closing packet, floor plan, survey); never published
```

## Install the skills anywhere

The skills follow the open [Agent Skills](https://github.com/vercel-labs/skills) format and live in `skills/`, one of its standard container locations, so the `skills` CLI discovers them with no manifest:

```sh
npx skills add sanchezdale/haus          # from GitHub: pick skills and agents, project scope
npx skills add sanchezdale/haus -g       # global: available in every project
npx skills add .                        # from a local clone of this repo
npx skills add sanchezdale/haus -l       # list what it finds, install nothing
npx skills update                        # update installed skills later
```

Requires Node.js 22.20 or later. The CLI supports OpenCode, Claude Code, Codex, Cursor, and 75 more agents, and project installs land in `.agents/skills/` with links per agent. The CLI collects anonymous telemetry; set `DO_NOT_TRACK=1` to disable it. To keep a local clone as the single source of truth, run `npx skills add <path-to-your-clone> -g` and pull updates in the clone.

## The build is swappable

`site/build.py` is the reference implementation, not a requirement. The contract is the input and the output, not the language:

- Input: markdown files at repo root plus `site-data/*.json`, per the contracts in `skills/haus-setup/SKILL.md`.
- Output: the page set in `site/` (page-per-slug HTML with the runtime hooks, plus `assets/now.json` and `assets/search.json` in the shapes the scripts expect).

Any generator that honors those contracts works: the runtime scripts, the skills, the artifact exporter, and the deploy steps never see the build language. Python is here because it is preinstalled on macOS and the whole converter is stdlib-plus-one-package (`markdown`). If your stack is Node (which the Cloudflare deploy uses anyway), port the two scripts and keep the outputs identical.

## Quality bar (what the skills enforce)

- Primary sources only: manufacturer care and warranty documents, the builder's warranty book, the state extension service, county and district pages.
- Every claim carries an inline link to its source; estimates and inferences are labeled.
- Months and seasons drive the view, not dates: recurring items show as "anytime this month", seasonal items appear while they matter, and the only real dates are warranty filing windows.
- No reminders, no notifications, no accounts: the manual answers when asked and never pings anyone.
- Documents never land in `site/`, only in `docs/` or a link you choose.

## Privacy

Your manual contains real details about a real house. Keep your clone private, serve it on your tailnet, and put any public host behind Cloudflare Access.

## License

MIT. Fork it, clone it, change the generator, host your manual however you like.

