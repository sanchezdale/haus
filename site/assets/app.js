/* The House Manual · interactions: checkbox memory, closing-date deadline chips */
(function () {
  'use strict';

  var store = {
    get: function (k, d) { try { return localStorage.getItem(k) === null ? d : localStorage.getItem(k); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  function hash(s) {
    var h = 5381, i;
    for (i = 0; i < s.length; i++) { h = ((h << 5) + h + s.charCodeAt(i)) | 0; }
    return (h >>> 0).toString(36);
  }

  /* checkbox persistence, keyed by task text */
  var boxes = document.querySelectorAll('li.task input[type="checkbox"]');
  Array.prototype.forEach.call(boxes, function (cb) {
    var li = cb.closest('li');
    var key = 'homekb.task.' + hash(li.textContent.trim());
    if (store.get(key, '0') === '1') { cb.checked = true; li.classList.add('done'); }
    cb.addEventListener('change', function () {
      store.set(key, cb.checked ? '1' : '0');
      li.classList.toggle('done', cb.checked);
    });
  });

  /* deadline chips from the closing date */
  var input = document.getElementById('closing-date');
  if (input && store.get('homekb.closing', '')) input.value = store.get('homekb.closing', '');

  function addDays(d, n) { var x = new Date(d.getTime()); x.setDate(x.getDate() + n); return x; }
  function addYears(d, n) { var x = new Date(d.getTime()); x.setFullYear(x.getFullYear() + n); return x; }
  function fmt(x) {
    try {
      return x.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase();
    } catch (e) { return x.toDateString().toUpperCase(); }
  }

  function chipText(offset, closing) {
    if (offset === '30d') {
      var end = addDays(closing, 30);
      return { label: 'WINDOW ENDS ' + fmt(end) + ' · FILE NOW', end: end, fileBy: end };
    }
    if (offset === 'insurance') {
      var now = new Date();
      var june = new Date(now.getFullYear(), 5, 1);
      if (now > june) june = new Date(now.getFullYear() + 1, 5, 1);
      return { label: 'NEXT CHECK: ' + fmt(june), end: june, fileBy: june };
    }
    var years = { '1y': 1, '2y': 2, '5y': 5, '10y': 10 }[offset];
    if (!years) return null;
    var covEnd = addYears(closing, years);
    var fileBy = addDays(covEnd, -30);
    return { label: 'COVERAGE ENDS ' + fmt(covEnd) + ' · FILE BY ' + fmt(fileBy), end: covEnd, fileBy: fileBy };
  }

  function renderChips() {
    var value = input ? input.value : store.get('homekb.closing', '');
    if (input) store.set('homekb.closing', value);
    var closing = value ? new Date(value + 'T00:00:00') : null;
    var today = new Date(); today.setHours(0, 0, 0, 0);

    var targets = document.querySelectorAll('[data-offset]');
    Array.prototype.forEach.call(targets, function (el) {
      var p = el.querySelector('[data-chip]') || el;
      var holder = el.classList.contains('issue') ? el.querySelector('[data-chip]') : null;
      var span = document.createElement('span');
      span.className = 'chip';
      if (!closing) {
        span.classList.add('unset');
        span.textContent = 'SET CLOSING DATE';
        if (holder) {
          holder.textContent = '';
          holder.appendChild(span);
          if (!input) {
            var a = document.createElement('a');
            a.href = 'deadlines.html';
            a.textContent = '→ enter it once on the Deadlines page';
            holder.appendChild(a);
          }
        } else {
          el.appendChild(span);
        }
        return;
      }
      var info = chipText(el.getAttribute('data-offset'), closing);
      if (!info) return;
      if (today > info.fileBy) span.classList.add('over');
      else if (addDays(today, 60) >= info.fileBy) span.classList.add('soon');
      span.textContent = info.label;
      if (holder) { holder.textContent = ''; holder.appendChild(span); }
      else { var prev = el.querySelector('.chip'); if (prev) prev.remove(); el.appendChild(span); }
    });
  }

  if (input) input.addEventListener('change', renderChips);
  renderChips();
})();
