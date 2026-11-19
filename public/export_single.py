#!/usr/bin/env python3
"""Export the whole manual as one self-contained HTML file.

Embeds all pages (stacked, router-switched), the stylesheet, all scripts,
and the now/search JSON, with a fetch shim so the unmodified scripts run
from embedded data. Output: public/haus-manual.html

Run after `python3 site/build.py`. No arguments.
"""
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / 'site'
ASSETS = SITE / 'assets'
OUT = REPO / 'public' / 'haus-manual.html'


def read(path):
    return path.read_text()


def embed_json(obj):
    return json.dumps(obj).replace('</', '<\\/')


def main():
    probe = read(SITE / 'index.html')
    favicon = re.search(r'<link rel="icon" href="([^"]+)"', probe).group(1)
    topbar = re.search(r'<header class="topbar">.*?</header>', probe, re.S).group(0)
    rail = re.search(r'<nav class="rail".*?</nav>', probe, re.S).group(0).replace(' class="on"', '')
    foot = re.search(r'<footer class="foot">.*?</footer>', probe, re.S).group(0)

    slugs = sorted(p.stem for p in SITE.glob('*.html'))
    pages, titles = {}, {}
    for slug in slugs:
        html = read(SITE / f'{slug}.html')
        pages[slug] = re.search(r'<main class="main">(.*?)</main>', html, re.S).group(1)
        titles[slug] = re.search(r'<title>(.*?)</title>', html).group(1)

    css = read(ASSETS / 'style.css')
    app_js = read(ASSETS / 'app.js')
    now_js = read(ASSETS / 'now.js')
    search_js = read(ASSETS / 'search.js')
    now_data = json.loads(read(ASSETS / 'now.json'))
    search_data = json.loads(read(ASSETS / 'search.json'))

    boxes = ''.join(
        f'<section class="main pagebox" data-slug="{s}">{pages[s]}</section>'
        for s in slugs)

    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The House Manual</title>
<link rel="icon" href="{favicon}">
<style>
{css}
/* ---------- single-file runtime ---------- */
.pagebox {{ display: none; }}
.pagebox.active {{ display: block; }}
.pages {{ min-width: 0; }}
</style>
</head>
<body data-page="index">
{topbar}
<div class="frame">
{rail}
<div class="pages">
{boxes}
</div>
</div>
{foot}
<script>
var EMBED_NOW = {embed_json(now_data)};
var EMBED_SEARCH = {embed_json(search_data)};
var PAGE_TITLES = {embed_json(titles)};
var origFetch = window.fetch;
window.fetch = function (u) {{
  var s = String(u);
  if (s.indexOf('now.json') !== -1) {{
    return Promise.resolve(new Response(JSON.stringify(EMBED_NOW), {{ headers: {{ 'Content-Type': 'application/json' }} }}));
  }}
  if (s.indexOf('search.json') !== -1) {{
    return Promise.resolve(new Response(JSON.stringify(EMBED_SEARCH), {{ headers: {{ 'Content-Type': 'application/json' }} }}));
  }}
  return origFetch.apply(this, arguments);
}};
</script>
<script>
{app_js}
</script>
<script>
{now_js}
</script>
<script>
{search_js}
</script>
<script>
(function () {{
  function go(slug) {{
    var boxes = document.querySelectorAll('.pagebox');
    for (var i = 0; i < boxes.length; i++) {{
      boxes[i].classList.toggle('active', boxes[i].getAttribute('data-slug') === slug);
    }}
    var links = document.querySelectorAll('.rail a');
    for (var j = 0; j < links.length; j++) {{
      links[j].classList.toggle('on', links[j].getAttribute('href') === slug + '.html');
    }}
    document.title = PAGE_TITLES[slug] || 'The House Manual';
    document.body.setAttribute('data-page', slug);
    window.scrollTo(0, 0);
    try {{ history.replaceState(null, '', '#' + slug); }} catch (e) {{}}
  }}
  document.addEventListener('click', function (e) {{
    var a = e.target && e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    if (a.classList.contains('ext')) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('.html') === -1) return;
    var slug = href.replace('.html', '');
    var boxes = document.querySelectorAll('.pagebox');
    for (var i = 0; i < boxes.length; i++) {{
      if (boxes[i].getAttribute('data-slug') === slug) {{
        e.preventDefault();
        go(slug);
        return;
      }}
    }}
  }});
  var start = 'index';
  if (location.hash) {{
    var want = location.hash.slice(1);
    var found = document.querySelector('.pagebox[data-slug="' + want + '"]');
    if (found) start = want;
  }}
  go(start);
}})();
</script>
</body>
</html>'''

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f'wrote {OUT} ({len(html) // 1024} KB, {len(slugs)} pages)')


if __name__ == '__main__':
    main()
