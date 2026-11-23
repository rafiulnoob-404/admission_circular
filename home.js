/* Card controls use explicit admission dates, not numbers parsed from prose. */
(function () {
  'use strict';
  var grid = document.querySelector('.cards');
  function init(data, loadFailed) {
  var byId = {};
  data.forEach(function (u) { byId[u.short] = u; });
  var cards = Array.prototype.slice.call(grid.querySelectorAll('article.card'));
  var search = document.getElementById('cardSearch');
  var sort = document.getElementById('cardSort');
  var count = document.getElementById('cardCount');
  var empty = document.getElementById('noCards');
  cards.forEach(function (card, i) {
    card.dataset.originalOrder = i;
    var badge = document.createElement('span');
    badge.className = 'application-status';
    badge.setAttribute('aria-label', 'আবেদনের অবস্থা');
    card.querySelector('.chips').appendChild(badge);
  });

  function appState(schedule, now) {
    if (!schedule || !schedule.start) return {rank: 3, label: 'আবেদনের তারিখ অপেক্ষমাণ', kind: 'unknown'};
    var start = Date.parse(schedule.start), end = schedule.end ? Date.parse(schedule.end) : NaN;
    if (!isFinite(start) || (schedule.end && !isFinite(end))) return {rank: 3, label: 'আবেদনের তারিখ অপেক্ষমাণ', kind: 'unknown'};
    if (now < start) return {rank: 1, label: 'আবেদন আসন্ন', kind: 'upcoming', date: start};
    if (!isFinite(end)) return {rank: 3, label: 'শেষ সময় নিশ্চিত নয়', kind: 'unknown'};
    if (now > end) return {rank: 2, label: 'আবেদনের সময় শেষ', kind: 'closed', date: end};
    var cutoff = schedule.new_application_cutoff ? Date.parse(schedule.new_application_cutoff) : NaN;
    if (isFinite(cutoff) && now > cutoff) return {rank: 0, label: 'নতুন আবেদন শুরু শেষ; জমা চলছে', kind: 'open', date: end};
    return {rank: 0, label: schedule.date_only ? 'সূচি অনুযায়ী আবেদনকাল' : 'আবেদন চলছে', kind: 'open', date: end};
  }
  function render() {
    var now = Date.now(), query = search.value.trim().toLocaleLowerCase('bn');
    var ordered = cards.slice();
    ordered.forEach(function (card) {
      var uni = byId[card.dataset.file] || {};
      var state = loadFailed ? {rank: 3, label: 'তথ্য লোড হয়নি', kind: 'unknown'} : appState(uni.application_schedule, now);
      card._appState = state;
      var badge = card.querySelector('.application-status');
      badge.textContent = state.label;
      badge.dataset.state = state.kind;
      card.hidden = !!query && (card.textContent + ' ' + card.dataset.file).toLocaleLowerCase('bn').indexOf(query) < 0;
    });
    ordered.sort(function (a, b) {
      var ua = byId[a.dataset.file] || {}, ub = byId[b.dataset.file] || {}, n = 0;
      if (sort.value === 'application') {
        n = a._appState.rank - b._appState.rank;
        if (!n) n = (a._appState.date || Infinity) - (b._appState.date || Infinity);
      } else if (sort.value === 'exam') {
        n = (ua.exam_sort_date || '9999').localeCompare(ub.exam_sort_date || '9999');
      } else if (sort.value === 'name') {
        n = (ua.name_bn || a.dataset.uni || '').localeCompare(ub.name_bn || b.dataset.uni || '', 'bn');
      }
      return n || Number(a.dataset.originalOrder) - Number(b.dataset.originalOrder);
    });
    var current = Array.prototype.slice.call(grid.querySelectorAll('article.card'));
    if (ordered.some(function (card, i) { return card !== current[i]; })) {
      ordered.forEach(function (card) { grid.appendChild(card); });
    }
    if (window.refreshCardLayout) window.refreshCardLayout();
    var shown = cards.filter(function (card) { return !card.hidden; }).length;
    count.textContent = shown.toLocaleString('bn-BD') + 'টি কার্ড';
    empty.hidden = shown !== 0;
  }
  search.addEventListener('input', render);
  sort.addEventListener('change', render);
  render();
  /* Re-evaluate the status when a tab is left open across a deadline. */
  setInterval(render, 60000);
  }
  fetch('data/universities.json').then(function (response) {
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  }).then(function (data) {
    if (!Array.isArray(data.universities)) throw new Error('Invalid university data');
    document.getElementById('homeDataStatus').textContent = '';
    init(data.universities, false);
  }).catch(function (err) {
    console.error('Admission data could not be loaded', err);
    var status = document.getElementById('homeDataStatus');
    status.textContent = 'আবেদনের অবস্থা ও তারিখ অনুযায়ী সাজানোর তথ্য লোড করা যায়নি। সংযোগ পরীক্ষা করে রিফ্রেশ করুন।';
    document.getElementById('cardSort').querySelectorAll('option[value="application"], option[value="exam"]').forEach(function (option) { option.disabled = true; });
    document.getElementById('cardSort').value = 'original';
    init([], true);
  });
})();
