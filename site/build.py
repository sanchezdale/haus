#!/usr/bin/env python3
"""Build The House Manual: static review site for ~/research/home markdown KB."""
import html
import json
import re
import pathlib
import markdown as md_lib

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO
OUT = SRC / 'site'
DATA = SRC / 'site-data'

# (slug, md file, display title)
SYSTEMS = [
    ('roof', 'roof.md', 'Roof'),
    ('siding', 'siding-and-exterior-paint.md', 'Siding & Exterior Paint'),
    ('pool', 'pool-and-screen-enclosure.md', 'Pool & Screen Enclosure'),
    ('hvac', 'hvac.md', 'HVAC'),
    ('plumbing', 'plumbing-and-water-heater.md', 'Plumbing & Water Heater'),
    ('electrical', 'electrical.md', 'Electrical'),
    ('irrigation', 'irrigation-and-lawn.md', 'Irrigation & Lawn'),
    ('windows', 'windows-and-doors.md', 'Windows & Doors'),
    ('pest', 'pest-and-termite.md', 'Pest & Termite'),
    ('hurricane', 'hurricane-prep.md', 'Hurricane Prep'),
]
WARRANTY = ('warranty', 'warranty.md', 'Warranty Terms')
ALL_DOCS = SYSTEMS + [WARRANTY]

HREF_MAP = {fname: f'{slug}.html' for slug, fname, _ in ALL_DOCS}
HREF_MAP['00-index.md'] = 'index.html'

MD = md_lib.Markdown(extensions=['tables', 'sane_lists'])


def convert(text: str) -> str:
    # rewrite .md links to page links, with friendly titles
    for slug, fname, title in ALL_DOCS:
        text = re.sub(r'\[' + re.escape(fname) + r'\]\(' + re.escape(fname) + r'\)',
                      f'[{title}]({slug}.html)', text)
        text = text.replace(f'({fname})', f'({slug}.html)')
    text = text.replace('(00-index.md)', '(index.html)')
    MD.reset()
    body = MD.convert(text)
    # task list checkboxes
    body = re.sub(r'<li>\s*\[ \]\s*', '<li class="task"><input type="checkbox">', body)
    # external links open in a new tab
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a class="ext" href="\1" target="_blank" rel="noopener"', body)
    # wrap tables for mobile scroll
    body = body.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')
    # first paragraph of each doc is the context strip
    body = body.replace('<p>', '<p class="context">', 1)
    # "Related files:" line becomes a chip row
    body = re.sub(r'<p(?: class="context")?>Related files:', '<p class="related"><span class="rel-label">SEE ALSO //</span>', body)
    return body


def doc_body(fname: str):
    """Return (title, converted body html) for a doc, stripping its H1."""
    raw = (SRC / fname).read_text()
    lines = raw.splitlines()
    title = ''
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if lines[i].startswith('# '):
        title = lines[i][2:].strip()
        raw = '\n'.join(lines[i + 1:])
    return title, convert(raw)


def find_section(sections: dict, needle: str) -> str:
    """First section whose heading contains needle; tolerant of climate or count suffixes."""
    for k, v in sections.items():
        if needle in k:
            return v
    return sections.get(needle, '')


def split_sections(fname: str) -> dict:
    """Split a doc on '## ' headings; keys are heading text."""
    raw = (SRC / fname).read_text()
    sections = {}
    cur = None
    buf = []
    for line in raw.splitlines():
        if line.startswith('## '):
            if cur is not None:
                sections[cur] = '\n'.join(buf).strip()
            cur = line[3:].strip()
            buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        sections[cur] = '\n'.join(buf).strip()
    return sections


def drop_first_h2(html: str) -> str:
    return re.sub(r'<h2>.*?</h2>\s*', '', html, count=1)


def extract_cards(section_html: str):
    """Split a rendered <ol> into per-item card bodies."""
    items = re.findall(r'<li>(.*?)</li>', section_html, flags=re.S)
    cards = []
    for it in items:
        m = re.match(r'\s*<strong>(.*?)</strong>(.*)', it, flags=re.S)
        if m:
            title, body = m.group(1).strip().rstrip('.'), m.group(2).strip()
        else:
            title, body = '', it.strip()
        cards.append((title, body))
    return cards


MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']


def strip_md_links(text: str) -> str:
    """[label](url) -> label: plain display text, no markdown link syntax."""
    return re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)


def parse_now_data() -> dict:
    """Extract the month-by-month calendar, monthly core, and quarterly tasks from 00-index.md."""
    cal = find_section(split_sections('00-index.md'), '12-month maintenance calendar')
    months = {}
    core = []
    quarterly = []
    subsection = None
    for line in cal.splitlines():
        stripped = line.strip()
        if stripped.startswith('### '):
            subsection = stripped[4:].strip()
            continue
        if subsection is None and stripped.startswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if len(cells) >= 2 and cells[0] in MONTHS:
                months[cells[0]] = strip_md_links(cells[1])
        elif subsection is not None and stripped.startswith('- '):
            if subsection.startswith('Recurring core'):
                core.append(strip_md_links(stripped[2:].strip()))
            elif subsection.startswith('Recurring quarterly'):
                quarterly.append(strip_md_links(stripped[2:].strip()))
    return {'months': months, 'core': core, 'quarterly': quarterly}


def emit_now_data() -> dict:
    """Write site/assets/now.json for the now screen; return the parsed data for reuse."""
    import json
    data = parse_now_data()
    (OUT / 'assets').mkdir(exist_ok=True)
    (OUT / 'assets' / 'now.json').write_text(json.dumps(data, indent=2) + '\n')
    return data


def month_blocks(months: dict) -> str:
    """Render the 12 months as closed <details> blocks for calendar.html."""
    import html as html_lib
    return ''.join(
        f'<details class="month-block" data-month="{m}">'
        f'<summary>{m}</summary>'
        f'<p>{html_lib.escape(months[m])}</p></details>'
        for m in MONTHS)


def donow_panel(fname: str) -> str:
    """Routine panel for a module page: Monthly and Quarterly rows of its Cadence tables."""
    import html as html_lib
    lines = (SRC / fname).read_text().splitlines()
    monthly, quarterly = [], []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith('|') and 'Cadence' in line:
            i += 1
            while i < len(lines) and re.match(r'^\s*\|[-\s|]+\|?\s*$', lines[i]):
                i += 1
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if len(cells) >= 2:
                    task = strip_md_links(cells[1])
                    if 'Monthly' in cells[0]:
                        monthly.append(task)
                    elif 'Quarterly' in cells[0]:
                        quarterly.append(task)
                i += 1
        else:
            i += 1
    if not monthly and not quarterly:
        return ''
    cols = ''
    for label, tasks in (('MONTHLY // ANYTIME THIS MONTH', monthly), ('QUARTERLY // ANYTIME THIS QUARTER', quarterly)):
        if not tasks:
            continue
        items = ''.join(f'<li>{html_lib.escape(t)}</li>' for t in tasks)
        cols += (f'<div class="now-col"><p class="rel-label">{label}</p>'
                 f'<ul class="mock-tasks">{items}</ul></div>')
    return (f'<section class="panel donow"><h2>ROUTINE // THIS SYSTEM</h2>'
            f'<div class="now-grid">{cols}</div></section>')


FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' "
           "shape-rendering='crispEdges'%3E%3Crect width='16' height='16' fill='%230b101c'/%3E"
           "%3Crect x='7' y='3' width='2' height='1' fill='%23ffb454'/%3E"
           "%3Crect x='6' y='4' width='4' height='1' fill='%23ffb454'/%3E"
           "%3Crect x='5' y='5' width='6' height='1' fill='%23ffb454'/%3E"
           "%3Crect x='3' y='6' width='10' height='1' fill='%23ffb454'/%3E"
           "%3Crect x='4' y='7' width='8' height='7' fill='%23182236'/%3E"
           "%3Crect x='5' y='8' width='2' height='2' fill='%236cd9ff'/%3E"
           "%3Crect x='9' y='8' width='2' height='2' fill='%23ffb454'/%3E"
           "%3Crect x='7' y='11' width='2' height='3' fill='%23e08a5e'/%3E%3C/svg%3E")

HERO_SVG = '''<svg class="hero-art" viewBox="0 0 96 26" preserveAspectRatio="xMidYMax slice" aria-hidden="true" shape-rendering="crispEdges">
<rect width="96" height="26" fill="#0b101c"/>
<rect y="6" width="96" height="6" fill="#0e1526"/>
<rect y="12" width="96" height="4" fill="#131c33"/>
<rect y="22" width="96" height="4" fill="#131c33"/>
<g fill="#f2ead8"><rect x="6" y="3" width="1" height="1"/><rect x="20" y="7" width="1" height="1"/><rect x="55" y="3" width="1" height="1"/><rect x="78" y="6" width="1" height="1"/><rect x="88" y="4" width="1" height="1"/></g>
<g fill="#6cd9ff"><rect x="12" y="5" width="1" height="1"/><rect x="30" y="3" width="1" height="1"/><rect x="70" y="8" width="1" height="1"/><rect x="84" y="10" width="1" height="1"/></g>
<g fill="#f2ead8"><rect x="50" y="3" width="3" height="3"/><rect x="51" y="2" width="1" height="1"/></g>
<g fill="#ffb454">
<rect x="36" y="8" width="2" height="1"/><rect x="34" y="9" width="6" height="1"/><rect x="32" y="10" width="10" height="1"/><rect x="30" y="11" width="14" height="1"/><rect x="28" y="12" width="18" height="1"/>
</g>
<rect x="30" y="13" width="14" height="9" fill="#182236"/>
<g fill="#93a3b8" opacity="0.35"><rect x="30" y="13" width="1" height="9"/><rect x="43" y="13" width="1" height="9"/><rect x="30" y="21" width="14" height="1"/></g>
<g fill="#ffb454"><rect x="32" y="15" width="2" height="2"/><rect x="40" y="15" width="2" height="2"/></g>
<rect x="35" y="17" width="3" height="5" fill="#e08a5e"/>
<g fill="#243049"><rect x="52" y="9" width="1" height="13"/><rect x="58" y="9" width="1" height="13"/><rect x="64" y="9" width="1" height="13"/><rect x="70" y="9" width="1" height="13"/><rect x="51" y="8" width="21" height="1"/></g>
<g fill="#6cd9ff" opacity="0.5"><rect x="53" y="10" width="5" height="1"/><rect x="59" y="10" width="5" height="1"/><rect x="65" y="10" width="5" height="1"/><rect x="52" y="13" width="19" height="1"/><rect x="52" y="17" width="19" height="1"/></g>
<rect x="53" y="14" width="4" height="3" fill="#1c6e8c"/><rect x="60" y="14" width="4" height="3" fill="#1c6e8c"/>
<g fill="#0b101c"><rect x="6" y="17" width="1" height="5"/><rect x="7" y="15" width="1" height="1"/><rect x="8" y="13" width="1" height="1"/><rect x="9" y="11" width="1" height="1"/><rect x="10" y="10" width="1" height="3"/><rect x="11" y="12" width="1" height="1"/><rect x="12" y="13" width="1" height="2"/><rect x="13" y="15" width="1" height="1"/><rect x="14" y="16" width="1" height="1"/><rect x="15" y="17" width="1" height="5"/><rect x="6" y="16" width="1" height="1"/><rect x="8" y="14" width="1" height="1"/><rect x="10" y="9" width="1" height="1"/></g>
<g fill="#0b101c"><rect x="86" y="17" width="1" height="5"/><rect x="85" y="16" width="1" height="1"/><rect x="84" y="15" width="1" height="1"/><rect x="83" y="14" width="1" height="1"/><rect x="82" y="13" width="1" height="2"/><rect x="81" y="15" width="1" height="1"/><rect x="80" y="16" width="1" height="1"/><rect x="79" y="17" width="1" height="5"/><rect x="82" y="12" width="1" height="1"/><rect x="83" y="13" width="1" height="1"/></g>
</svg>'''


def brand_sub_text():
    """Instance identity line for the header, from the profile when present."""
    try:
        prof = json.loads((DATA / 'profile.json').read_text())
        ident = prof.get('identity', {})
        parts = [str(v).upper() for v in (ident.get('area'), ident.get('builder')) if v and 'TBD' not in str(v)]
        return ' · '.join(parts[:2]) if parts else 'YOUR HOUSE'
    except Exception:
        return 'YOUR HOUSE'

def rail(active: str) -> str:
    def li(slug, title):
        on = ' class="on"' if slug == active else ''
        return f'<li><a href="{slug}.html"{on}>{title}</a></li>'
    main = (li('index', 'Overview') + li('profile', 'House Profile') + li('calendar', 'Maintenance Calendar')
            + li('deadlines', 'Warranty Deadlines'))
    rows = ''.join(li(s, t) for s, _, t in SYSTEMS)
    doc = li('warranty', 'Pulte Warranty Terms')
    return ('<nav class="rail" aria-label="Sections">'
            '<p class="rail-label">NAV // PAGES</p>'
            f'<ul>{main}</ul>'
            '<p class="rail-label">SYS // MODULES</p>'
            f'<ul>{rows}</ul>'
            '<p class="rail-label">DOC // REFERENCE</p>'
            f'<ul>{doc}</ul></nav>')


def render_tags(slug: str) -> str:
    tags_file = DATA / 'tags.json'
    if not tags_file.exists():
        return ''
    import json
    tags = json.loads(tags_file.read_text())
    chips = tags.get(slug, [])
    if not chips:
        return ''
    spans = ''.join(f'<span>{c}</span>' for c in chips)
    return f'<div class="spec-strip pagetags" aria-label="relevant facts for this page">{spans}</div>'


def shell(slug: str, title: str, label: str, body_html: str, active: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{('The House Manual' if slug == 'index' else title + ' · The House Manual')}</title>
<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="assets/style.css?v=6">
</head>
<body data-page="{slug}">
<header class="topbar">
<a class="brand" href="index.html">
<svg class="brand-mark" viewBox="0 0 16 16" shape-rendering="crispEdges" aria-hidden="true"><rect width="16" height="16" fill="#0b101c"/><rect x="7" y="3" width="2" height="1" fill="#ffb454"/><rect x="6" y="4" width="4" height="1" fill="#ffb454"/><rect x="5" y="5" width="6" height="1" fill="#ffb454"/><rect x="3" y="6" width="10" height="1" fill="#ffb454"/><rect x="4" y="7" width="8" height="7" fill="#182236"/><rect x="5" y="8" width="2" height="2" fill="#6cd9ff"/><rect x="9" y="8" width="2" height="2" fill="#ffb454"/><rect x="7" y="11" width="2" height="3" fill="#e08a5e"/></svg>
<span class="brand-text">THE&nbsp;HOUSE&nbsp;MANUAL<span class="brand-sub">{brand_sub_text()}</span></span>
</a>
<div class="searchbox" id="searchbox"></div>
</header>
<div class="frame">
{rail(active)}
<main class="main">
<p class="syslabel">{label}</p>
{render_tags(slug)}
{body_html}
</main>
</div>
<footer class="foot">
<span>HOME.KB // LOCAL BUILD</span>
<span>Sources verified Nov 18, 2026 · costs are estimates · every claim links to its source</span>
</footer>
<script src="assets/app.js?v=2"></script>
<script src="assets/now.js?v=3"></script>
<script src="assets/search.js?v=2"></script>
</body>
</html>'''


def write(name: str, content: str):
    (OUT / name).write_text(content)


def esc_tbd(text) -> str:
    """Escape a profile value for HTML and mute any TBD marker inside it."""
    return html.escape(str(text)).replace('TBD', '<span class="profile-tbd">TBD</span>')


def build_profile_page():
    """Render the House Profile page: the full inventory from site-data/profile.json."""
    data = json.loads((DATA / 'profile.json').read_text())
    ident, house, yard = data['identity'], data['house'], data['yard']
    auto, systems, documents = data['automation'], data['systems'], data['documents']

    def two_col(rows):
        body = ''.join(f'<tr><td>{label}</td><td>{value}</td></tr>' for label, value in rows)
        return f'<div class="table-wrap"><table><tr><th>Item</th><th>Value</th></tr>{body}</table></div>'

    def doc_status(status: str) -> str:
        if status == 'awaiting drop':
            return f'<span class="chip soon">{html.escape(status)}</span>'
        return esc_tbd(status)

    # identity: spec chips plus the closing date as an amber action chip
    chips = ''.join(
        f'<span>{key.upper()} // {html.escape(str(ident[key]))}</span>'
        for key in ('builder', 'plan', 'built', 'lot', 'area', 'county'))
    closing = str(ident['closing_date'])
    if 'TBD' in closing.upper():
        closing_chip = '<a class="chip soon" href="deadlines.html">CLOSING DATE // TBD</a>'
        closing_note = f'<p class="profile-tbd">{html.escape(closing)}</p>'
    else:
        closing_chip = f'<span>CLOSING DATE // {html.escape(closing)}</span>'
        closing_note = ''

    structure = two_col([
        ('Stories', esc_tbd(house['stories'])),
        ('Square feet', esc_tbd(house['sqft'])),
        ('Floor plan', esc_tbd(house['floor_plan'])),
        ('Survey', esc_tbd(house['survey'])),
    ])

    sys_rows = ''.join(
        f'<tr><td>{html.escape(s["name"])}</td><td>{esc_tbd(s["detail"])}</td>'
        f'<td><a href="{html.escape(s["page"])}">{html.escape(s["page"])}</a></td></tr>'
        for s in systems)
    systems_table = (f'<div class="table-wrap"><table>'
                     f'<tr><th>System</th><th>Detail</th><th>Page</th></tr>{sys_rows}</table></div>')

    yard_table = two_col([
        ('Lawn', esc_tbd(yard['lawn'])),
        ('Trees', esc_tbd(yard['trees'])),
        ('Lawn company', f'<span class="profile-tbd">{html.escape(yard["lawn_company"])}</span>'),
        ('Watering', esc_tbd(yard['watering'])),
    ])

    auto_panel = ('<section class="panel"><h2>AUTOMATION // HOME ASSISTANT</h2>'
                  f'<p><strong>{html.escape(auto["status"])}</strong>. {html.escape(auto["detail"])}</p></section>')

    doc_rows = ''.join(
        f'<tr><td>{html.escape(d["label"])}</td><td>{doc_status(d["status"])}</td>'
        f'<td>{esc_tbd(d["unlocks"])}</td></tr>'
        for d in documents)
    docs_table = (f'<div class="table-wrap"><table>'
                  f'<tr><th>Document</th><th>Status</th><th>Unlocks</th></tr>{doc_rows}</table></div>')

    known = ('<section class="panel"><h2>KNOWN ISSUES</h2>'
             '<p>The three open issues live on the <a href="index.html">Overview page</a>.</p></section>')

    body = f'''
<h1>House Profile</h1>
<p class="context">The full inventory of the house: everything the assistant knows lives here, and every other page shows only the tags it needs.</p>
<h2>HOUSE // IDENTITY</h2>
<div class="spec-strip">{chips}{closing_chip}</div>
{closing_note}
<h2>HOUSE // STRUCTURE</h2>
{structure}
<h2>SYSTEMS // INVENTORY</h2>
{systems_table}
<h2>YARD</h2>
{yard_table}
{auto_panel}
<h2>DOCUMENTS // AWAITING</h2>
{docs_table}
{known}'''
    return shell('profile', 'House Profile', 'SYS // PROFILE', body, 'profile')


def plain_text(fragment: str) -> str:
    """Plain text of an HTML fragment: tags gone, entities resolved, whitespace collapsed."""
    import html
    text = re.sub(r'<[^>]+>', ' ', fragment)
    text = html.unescape(text)
    # angle brackets left at this point are literal characters that were
    # escaped in the source (code arrows like "<-"); they have no search
    # value and must not appear in the index text
    text = re.sub(r'[<>]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def build_search_index():
    """Write site/assets/search.json: {title, url, text} for every built page."""
    import json
    pages = []
    for path in sorted(OUT.glob('*.html')):
        raw = path.read_text()
        raw = re.sub(r'<script\b.*?</script>', ' ', raw, flags=re.S | re.I)
        raw = re.sub(r'<style\b.*?</style>', ' ', raw, flags=re.S | re.I)
        m = re.search(r'<h1[^>]*>(.*?)</h1>', raw, flags=re.S | re.I)
        if m is None:
            m = re.search(r'<title[^>]*>(.*?)</title>', raw, flags=re.S | re.I)
        pages.append({
            'title': plain_text(m.group(1)) if m else path.stem,
            'url': path.name,
            'text': plain_text(raw),
        })
    (OUT / 'assets').mkdir(exist_ok=True)
    (OUT / 'assets' / 'search.json').write_text(
        json.dumps({'pages': pages}, ensure_ascii=False) + '\n')


def main():
    OUT.mkdir(exist_ok=True)
    if not (SRC / '00-index.md').exists():
        raise SystemExit('No knowledge base found (00-index.md). Run the haus-setup skill first: '
                         'it interviews you, researches your systems, and writes the markdown and '
                         'site-data files this generator consumes.')

    # ---- index ----------------------------------------------------------
    idx = split_sections('00-index.md')
    issues_html = convert(find_section(idx, 'known issues'))
    cards = extract_cards(issues_html)
    card_offsets = ['30d', '1y', '2y']
    issues = ''
    for i, ((ctitle, cbody), off) in enumerate(zip(cards, card_offsets), 1):
        issues += (f'<article class="issue" data-offset="{off}">'
                   f'<div class="issue-head"><span class="crystal" aria-hidden="true"></span>'
                   f'<span class="issue-num">0{i}</span>'
                   f'<h3>{ctitle}</h3></div>'
                   f'<div class="issue-body">{cbody}</div>'
                   f'<p class="deadline-chip" data-chip></p></article>')

    # systems grid from the files table
    tbl = idx['Files in this knowledge base']
    fname_map = {fname: (slug, title) for slug, fname, title in ALL_DOCS}
    grid_items = []
    for m in re.finditer(r'^\|\s*\[([^\]]+)\]\((\S+?)\)\s*\|\s*(.+?)\s*\|\s*$', tbl, flags=re.M):
        _, href, scope = m.groups()
        if href in fname_map:
            slug, t = fname_map[href]
            grid_items.append((slug, t, scope))
    grid_items.insert(0, ('calendar', 'Maintenance Calendar', '12-month Florida-tuned task list, monthly core, quarterly checks'))
    grid_items.insert(1, ('deadlines', 'Warranty Deadlines', 'File-before-it-expires checklist with a closing-date calculator'))
    grid_items.insert(2, ('plan', 'House Assistant Roadmap', 'From manual to assistant: the Now screen, database, documents, skills, aerial measure'))
    grid_items.insert(0, ('profile', 'House Profile', 'The full inventory: identity, systems, yard, automation, documents'))
    grid = ''.join(
        f'<a class="tile" href="{s}.html"><span class="tile-num">{i:02d}</span>'
        f'<span class="tile-title">{t}</span><span class="tile-scope">{sc}</span></a>'
        for i, (s, t, sc) in enumerate(grid_items, 1))

    blurb = ''
    for line in (SRC / '00-index.md').read_text().splitlines():
        if line.startswith('Property:'):
            blurb = line[len('Property: '):]
            break

    links_html = convert(idx.get('Most-used links', ''))

    body = f'''
<section class="hero">
{HERO_SVG}
<div class="hero-text">
<p class="syslabel">HOME.KB // 2025-26</p>
<h1>The House Manual</h1>
<p class="hero-blurb">{blurb}</p>
</div>
</section>
<section class="panel now-panel" id="now">
<h2><span id="now-month-header">THIS MONTH</span> <span class="now-season" id="now-season"></span></h2>
<p class="rel-label">MONTHLY + SEASONAL + FILING WINDOWS // COMPUTED FROM THE CALENDAR, THE SEASON, AND YOUR CLOSING DATE</p>
<div class="now-grid">
<div class="now-col"><p class="rel-label">MONTHLY // ANYTIME THIS MONTH</p><ul class="mock-tasks" id="now-today"></ul></div>
<div class="now-col"><p class="rel-label">FROM THE CALENDAR //</p><ul class="mock-tasks" id="now-month"></ul></div>
<div class="now-col"><p class="rel-label" id="now-quarter-label">THIS QUARTER //</p><ul class="mock-tasks" id="now-quarter"></ul></div>
<div class="now-col"><p class="rel-label">FILING WINDOWS // WARRANTY</p><ul class="mock-tasks" id="now-windows"></ul></div>
</div>
</section>
<section class="panel">
<h2>Three known issues · act in warranty year one</h2>
<div class="issues">{issues}</div>
</section>
<section class="panel">
<h2>All modules</h2>
<div class="tiles">{grid}</div>
</section>
<section class="panel">
<h2>Most-used links</h2>
{links_html}
</section>'''
    write('index.html', shell('index', 'The House Manual', 'HOME.KB // INDEX', body, 'index'))

    # ---- now screen data (home NOW panel + calendar focus) --------------
    now_data = emit_now_data()

    # ---- calendar -------------------------------------------------------
    cal = drop_first_h2(convert(find_section(idx, '12-month maintenance calendar')))
    # the 12-row months table becomes per-month blocks; recurring lists stay as-is
    cal = re.sub(r'<div class="table-wrap"><table>.*?</table></div>\s*', '', cal, flags=re.S, count=1)
    cal = cal.replace('<h3>', month_blocks(now_data['months']) + '<h3>', 1)
    body = f'<h1>Maintenance Calendar</h1>{cal}'
    write('calendar.html', shell('calendar', 'Maintenance Calendar', 'SYS // CALENDAR', body, 'calendar'))

    # ---- deadlines ------------------------------------------------------
    dl = convert(idx.get('File-before-warranty-expires checklist', ''))
    dl = re.sub(r'<h3>Within 30 days of closing[^<]*</h3>',
                '<h3 data-offset="30d">Within 30 days of closing (or now, if still open)</h3>', dl)
    dl = re.sub(r'<h3>Closing date \+ 1 year[^<]*</h3>',
                '<h3 data-offset="1y">Closing date + 1 year (file at least a month before)</h3>', dl)
    dl = re.sub(r'<h3>Closing date \+ 2 years[^<]*</h3>',
                '<h3 data-offset="2y">Closing date + 2 years (file at least a month before)</h3>', dl)
    dl = re.sub(r'<h3>Closing date \+ 5 years[^<]*</h3>',
                '<h3 data-offset="5y">Closing date + 5 years (file at least a month before)</h3>', dl)
    dl = re.sub(r'<h3>Closing date \+ 10 years[^<]*</h3>',
                '<h3 data-offset="10y">Closing date + 10 years (structural only)</h3>', dl)
    dl = re.sub(r'<h3>Insurance calendar[^<]*</h3>',
                '<h3 data-offset="insurance">Insurance calendar (parallel, not warranty)</h3>', dl)
    body = f'''<h1>Warranty Deadlines</h1>
<p class="context">Every deadline below runs from your closing date. Pulte must receive claims no
later than 30 days after a coverage period ends, so file at least a month early. Check off items as
you send them; this page remembers.</p>
<div class="closing panel-inset">
<label for="closing-date"><span class="rel-label">CLOSING DATE //</span></label>
<input type="date" id="closing-date">
</div>
{dl}'''
    write('deadlines.html', shell('deadlines', 'Warranty Deadlines', 'SYS // DEADLINES', body, 'deadlines'))

    # ---- doc pages ------------------------------------------------------
    labels = {'warranty': 'DOC // WARRANTY'}
    for slug, fname, _ in ALL_DOCS:
        if not (SRC / fname).exists():
            continue
        title, body = doc_body(fname)
        label = labels.get(slug, f'SYS // {slug.upper()}')
        donow = donow_panel(fname)
        write(f'{slug}.html', shell(slug, title, label, f'<h1>{title}</h1>{donow}{body}', slug))

    # ---- house profile ---------------------------------------------------
    write('profile.html', build_profile_page())

    # ---- search index ----------------------------------------------------
    build_search_index()

    print('built:', ', '.join(sorted(p.name for p in OUT.glob('*.html'))))


if __name__ == '__main__':
    main()
