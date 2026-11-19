# Public setup: publishing the House Manual

The site under `site/` is fully static. Every publish path is a copy of it, so nothing breaks when the hosting choice changes.

Before publishing anywhere beyond your own devices, remember: the manual contains real details about a real house (area, systems, known issues, documents). The LAN and Tailscale hosts are private by default. Public hosts should stay behind Cloudflare Access or remain personal-use artifacts.

## Ways to publish

1. **Internal.** Any static file server on your LAN or tailnet, for example:
   ```sh
   python3 -m http.server 8787 --directory site
   ```
   On a Tailscale node, serve with `--bind 0.0.0.0` and the site is reachable from every device on the tailnet by IP.
2. **Cloudflare Pages + Access (the gated shareable URL).** See `deploy-cloudflare.md`. Direct upload of the `site/` folder, gated by email through Cloudflare Zero Trust. Nothing about the repo is exposed, only the built pages.
3. **Single-file artifact.** `haus-manual.html` is the whole manual in one portable file: all pages, styles, scripts, search index, and the month logic, with a tiny router. Verified working: page switching, instant search, closing-date chips, checkbox memory. Paste it into a Claude artifact, use it as the base for a ChatGPT site, or email it to yourself.
4. **GitHub Pages (easy but public).** Your clone can enable Pages on the `site/` folder of the `main` branch and the site is hosted on the repo's Pages URL with zero setup. Caveat: Pages URLs are public and un-gated even when the repo is private on a paid plan, so only use this if your manual's details are safe to expose.

## Build and export

From the repo root:

```sh
python3 site/build.py          # regenerate all pages, now.json, search.json
python3 public/export_single.py   # write public/haus-manual.html
```

Run the export after every build. The artifact is committed so a release is always ready, but regenerate it when the site changes.

## Release checklist

- [ ] `python3 site/build.py` succeeds with zero errors
- [ ] `python3 public/export_single.py` regenerated
- [ ] Opening `haus-manual.html` locally shows THIS MONTH and search works
- [ ] No document in `site/` that should be private (documents belong in `docs/`, never `site/`)
- [ ] Closing date either real or intentionally TBD
- [ ] Commit; the release is the commit, there is no registry
