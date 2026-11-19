/* The House Manual · instant search (owned by the P1 search worker) */
(function () {
  'use strict';

  var mount = document.getElementById('searchbox');
  if (!mount) return;

  var INDEX_URL = 'assets/search.json?v=1';
  var pages = null;      /* fetched index, null until loaded */
  var loading = false;
  var query = '';        /* lowercased, trimmed */
  var hits = [];         /* ranked results for the current query */
  var rows = [];         /* their DOM rows */
  var active = -1;
  var hideTimer = null;

  var input = document.createElement('input');
  input.type = 'search';
  input.id = 'search-input';
  input.placeholder = 'Search the manual';
  input.autocomplete = 'off';
  input.spellcheck = false;
  input.setAttribute('aria-label', 'Search the manual');
  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-expanded', 'false');
  input.setAttribute('aria-controls', 'search-results');
  input.setAttribute('aria-autocomplete', 'list');

  var list = document.createElement('div');
  list.className = 'search-results';
  list.id = 'search-results';
  list.hidden = true;
  list.setAttribute('role', 'listbox');
  list.setAttribute('aria-label', 'Search results');

  mount.appendChild(input);
  mount.appendChild(list);

  function go(url) { window.location.href = url; }

  function loadIndex() {
    if (pages || loading) return;
    loading = true;
    fetch(INDEX_URL).then(function (r) { return r.json(); }).then(function (data) {
      pages = data && data.pages ? data.pages : [];
      render();
    }).catch(function () { loading = false; });
  }

  function show() {
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  function hide() {
    list.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    if (rows[active]) rows[active].classList.remove('active');
    active = -1;
    input.removeAttribute('aria-activedescendant');
  }

  function setActive(i) {
    if (rows[active]) rows[active].classList.remove('active');
    active = i;
    var row = rows[active];
    if (row) {
      row.classList.add('active');
      input.setAttribute('aria-activedescendant', row.id);
      if (row.scrollIntoView) row.scrollIntoView({ block: 'nearest' });
    } else {
      input.removeAttribute('aria-activedescendant');
    }
  }

  /* ~90 chars centered on the first match, the match wrapped in <mark> */
  function appendSnippet(el, text, pos) {
    var start = pos < 0 ? 0 : Math.max(0, pos - 40);
    var end = Math.min(text.length, start + 90);
    if (end === text.length) start = Math.max(0, end - 90);
    if (start > 0) el.appendChild(document.createTextNode('…'));
    if (pos >= 0) {
      el.appendChild(document.createTextNode(text.slice(start, pos)));
      var mark = document.createElement('mark');
      mark.textContent = text.slice(pos, pos + query.length);
      el.appendChild(mark);
      el.appendChild(document.createTextNode(text.slice(pos + query.length, end)));
    } else {
      el.appendChild(document.createTextNode(text.slice(start, end)));
    }
    if (end < text.length) el.appendChild(document.createTextNode('…'));
  }

  function makeRow(hit, index) {
    var row = document.createElement('div');
    row.className = 'sr';
    row.id = 'sr-' + index;
    row.setAttribute('role', 'option');
    var title = document.createElement('div');
    title.className = 'sr-title';
    title.textContent = hit.page.title;
    row.appendChild(title);
    var snip = document.createElement('div');
    snip.className = 'sr-snippet';
    appendSnippet(snip, hit.page.text, hit.textPos);
    row.appendChild(snip);
    row.addEventListener('click', function () { go(hit.page.url); });
    return row;
  }

  function render() {
    query = input.value.trim().toLowerCase();
    list.textContent = '';
    rows = [];
    hits = [];
    active = -1;
    input.removeAttribute('aria-activedescendant');
    if (query.length < 2) { hide(); return; }
    if (!pages) return;   /* index still loading; render() reruns on arrival */

    var i, p, tp, xp;
    for (i = 0; i < pages.length; i++) {
      p = pages[i];
      tp = p.title.toLowerCase().indexOf(query);
      xp = p.text.toLowerCase().indexOf(query);
      if (tp < 0 && xp < 0) continue;
      hits.push({ page: p, titleHit: tp >= 0, textPos: xp });
    }
    /* title matches first, then earlier text positions */
    hits.sort(function (a, b) {
      if (a.titleHit !== b.titleHit) return a.titleHit ? -1 : 1;
      return (a.textPos < 0 ? 1e9 : a.textPos) - (b.textPos < 0 ? 1e9 : b.textPos);
    });
    hits = hits.slice(0, 8);

    if (!hits.length) {
      var none = document.createElement('div');
      none.className = 'sr-empty';
      none.setAttribute('role', 'option');
      none.setAttribute('aria-disabled', 'true');
      none.textContent = 'NO MATCHES';
      list.appendChild(none);
      show();
      return;
    }
    for (i = 0; i < hits.length; i++) {
      var row = makeRow(hits[i], i);
      rows.push(row);
      list.appendChild(row);
    }
    show();
  }

  input.addEventListener('focus', function () {
    if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    loadIndex();
    render();
  });
  input.addEventListener('input', function () {
    loadIndex();
    render();
  });
  input.addEventListener('blur', function () {
    hideTimer = setTimeout(hide, 160);
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (!rows.length) return;
      e.preventDefault();
      if (active === -1) setActive(e.key === 'ArrowDown' ? 0 : rows.length - 1);
      else setActive((active + (e.key === 'ArrowDown' ? 1 : -1) + rows.length) % rows.length);
    } else if (e.key === 'Enter') {
      var i = active >= 0 ? active : 0;
      if (hits[i]) { e.preventDefault(); go(hits[i].page.url); }
    } else if (e.key === 'Escape') {
      input.value = '';
      render();
    }
  });

  /* keep focus on the input so a row click lands before any blur */
  list.addEventListener('mousedown', function (e) { e.preventDefault(); });

  /* "/" anywhere outside an input focuses the search box */
  document.addEventListener('keydown', function (e) {
    if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' ||
              t.tagName === 'SELECT' || t.isContentEditable)) return;
    e.preventDefault();
    input.focus();
    input.select();
  });
})();
