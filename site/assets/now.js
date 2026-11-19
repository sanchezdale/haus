/* The House Manual · now screen logic (owned by the P1 now-screen worker) */
(function () {
  'use strict';

  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'];
  var SEASON_NOTES = {
    0: 'DRY SEASON // WATER LESS, PRUNE BEFORE SPRING',
    1: 'DRY SEASON // WATER LESS, CAULK WALK',
    2: 'PRE-SEASON PREP BEGINS',
    3: 'SPRING TUNE-UPS + FIRST FERTILIZE',
    4: 'PRE-STORM PREP // GUTTERS + KIT REFRESH',
    5: 'HURRICANE SEASON + FERTILIZER BAN START JUN 1',
    6: 'PEAK STORM WATCH',
    7: 'PEAK STORM WATCH',
    8: 'BAN ENDS SEP 30 // LATE-STORM WATCH',
    9: 'FALL FERTILIZER WINDOW, THE YEARS LAST',
    10: 'HURRICANE SEASON ENDS NOV 30',
    11: 'DRY SEASON SETTLES IN // TERMITE RENEWAL CHECK'
  };
  var QUARTER_MONTHS = [2, 5, 8, 11]; /* March, June, September, December */

  function list(ul, items) {
    if (!ul) return;
    ul.textContent = '';
    Array.prototype.forEach.call(items, function (t) {
      var li = document.createElement('li');
      li.textContent = t;
      ul.appendChild(li);
    });
  }

  function closingDate() {
    try {
      if (typeof localStorage === 'undefined') return null;
      var v = localStorage.getItem('homekb.closing');
      return v ? new Date(v + 'T00:00:00') : null;
    } catch (e) { return null; }
  }

  /* same date math app.js uses for its deadline chips, kept self-contained */
  function addDays(d, n) { var x = new Date(d.getTime()); x.setDate(x.getDate() + n); return x; }
  function addYears(d, n) { var x = new Date(d.getTime()); x.setFullYear(d.getFullYear() + n); return x; }
  function fmt(x) {
    try {
      return x.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase();
    } catch (e) { return x.toDateString().toUpperCase(); }
  }

  function windowChip(offset, closing) {
    if (offset === '30d') {
      var end = addDays(closing, 30);
      return { label: '30-DAY WINDOW ENDS ' + fmt(end) + ' · FILE NOW', fileBy: end };
    }
    var years = { '1y': 1, '2y': 2, '5y': 5, '10y': 10 }[offset];
    if (!years) return null;
    var covEnd = addYears(closing, years);
    var fileBy = addDays(covEnd, -30);
    return { label: years + 'Y COVERAGE ENDS ' + fmt(covEnd) + ' · FILE BY ' + fmt(fileBy), fileBy: fileBy };
  }

  function renderWindows(ul, now) {
    if (!ul) return;
    ul.textContent = '';
    var closing = closingDate();
    if (!closing) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = 'deadlines.html';
      var span = document.createElement('span');
      span.className = 'chip unset';
      span.textContent = 'SET CLOSING DATE';
      a.appendChild(span);
      li.appendChild(a);
      ul.appendChild(li);
      return;
    }
    var today = new Date(now.getTime());
    today.setHours(0, 0, 0, 0);
    ['30d', '1y', '2y', '5y', '10y'].forEach(function (off) {
      var info = windowChip(off, closing);
      if (!info) return;
      var li = document.createElement('li');
      var span = document.createElement('span');
      span.className = 'chip';
      if (today > info.fileBy) span.classList.add('over');
      else if (addDays(today, 60) >= info.fileBy) span.classList.add('soon');
      span.textContent = info.label;
      li.appendChild(span);
      ul.appendChild(li);
    });
  }

  function fillNow(data, now) {
    var monthName = MONTHS[now.getMonth()];
    list(document.getElementById('now-today'), (data && data.core) || []);

    var month = document.getElementById('now-month');
    if (month) {
      var text = (data && data.months && data.months[monthName]) || '';
      list(month, text ? text.split('; ') : []);
    }

    var quarter = document.getElementById('now-quarter');
    if (quarter) {
      if (QUARTER_MONTHS.indexOf(now.getMonth()) !== -1) {
        var qLabel = document.getElementById('now-quarter-label');
        if (qLabel) {
          qLabel.textContent = 'THIS QUARTER // BY ' + monthName.toUpperCase() + ' END';
        }
        list(quarter, (data && data.quarterly) || []);
      } else {
        var col = quarter.closest('.now-col');
        (col || quarter).style.display = 'none';
      }
    }

    renderWindows(document.getElementById('now-windows'), now);
  }

  /* calendar page: open only the current month and mark it */
  function focusCalendar() {
    var blocks = document.querySelectorAll('details.month-block');
    if (!blocks.length) return;
    var current = MONTHS[new Date().getMonth()];
    Array.prototype.forEach.call(blocks, function (d) {
      var here = d.getAttribute('data-month') === current;
      d.open = here;
      if (here) {
        var chip = document.createElement('span');
        chip.className = 'chip soon';
        chip.textContent = 'YOU ARE HERE';
        var summary = d.querySelector('summary');
        if (summary) summary.appendChild(chip);
      }
    });
  }

  function init() {
    focusCalendar();
    var panel = document.getElementById('now');
    if (!panel) return;
    var now = new Date();
    var head = document.getElementById('now-month-header');
    if (head) {
      head.textContent = 'THIS MONTH // ' + MONTHS[now.getMonth()].toUpperCase();
    }
    var season = document.getElementById('now-season');
    if (season) {
      season.textContent = SEASON_NOTES[now.getMonth()] || '';
    }
    if (typeof fetch !== 'function') return;
    fetch('assets/now.json?v=1')
      .then(function (r) {
        if (!r.ok) throw new Error('now.json ' + r.status);
        return r.json();
      })
      .then(function (data) { fillNow(data, now); })
      .catch(function () { /* data unavailable: lists stay empty */ });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
