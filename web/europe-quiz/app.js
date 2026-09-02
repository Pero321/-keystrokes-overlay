/* Тренажер політичної карти Європи. Дані карти — у map-data.js (window.EUROPE_MAP). */
(() => {
'use strict';

const DATA = window.EUROPE_MAP;

const REGIONS = {
  north:   { name: 'Північна',   color: '#4f9dff', hue: 212 },
  west:    { name: 'Західна',    color: '#a97bff', hue: 264 },
  central: { name: 'Центральна', color: '#ffb347', hue: 33  },
  east:    { name: 'Східна',     color: '#ff6f9c', hue: 344 },
  south:   { name: 'Південна',   color: '#33cfa6', hue: 165 },
};

/* Сусіди в одному регіоні мають різні відтінки — інакше кордон між ними
   не видно (Іспанія/Португалія, балканський вузол). */
const L = [56, 68, 48, 62, 52];
const S = [64, 76, 58];
function shadeOf(region, i) {
  const h = REGIONS[region].hue + ((i % 3) - 1) * 7;
  return `hsl(${h} ${S[i % S.length]}% ${L[i % L.length]}%)`;
}
const REGION_KEYS = Object.keys(REGIONS);

const MODES = {
  find:   { kicker: 'Знайди на карті',  hint: 'Клацни країну на карті' },
  name:   { kicker: 'Що це за країна?', hint: 'Обери правильну назву' },
  region: { kicker: 'Який це регіон?',  hint: 'Обери регіон країни' },
  study:  { kicker: 'Вивчення',         hint: 'Наводь і клацай країни, щоб дізнатися назву та регіон' },
};

const $  = (id) => document.getElementById(id);
const svg = $('map');
const gViewport = $('viewport');
const gCountries = $('countries');
const gMarkers = $('markers');
const gLabels = $('labels');

const byId = new Map(DATA.countries.map(c => [c.id, c]));
const paths = new Map();
const marks = new Map();

/* ------------------------------------------------------------------ стан */
const SAVE = 'europe-quiz/v1';
const state = {
  mode: 'find',
  regions: new Set(REGION_KEYS),
  queue: [],
  current: null,
  attempts: 0,
  score: 0,
  asked: 0,
  streak: 0,
  best: 0,
  missed: new Set(),
  answered: new Set(),
  locked: false,
  startedAt: 0,
};

function loadPrefs() {
  try {
    const p = JSON.parse(localStorage.getItem(SAVE) || '{}');
    if (p.mode && MODES[p.mode]) state.mode = p.mode;
    if (Array.isArray(p.regions) && p.regions.length) {
      state.regions = new Set(p.regions.filter(r => REGIONS[r]));
    }
    if (typeof p.best === 'number') state.best = p.best;
  } catch (_) { /* перший запуск */ }
}
function savePrefs() {
  try {
    localStorage.setItem(SAVE, JSON.stringify({
      mode: state.mode, regions: [...state.regions], best: state.best,
    }));
  } catch (_) { /* приватний режим — просто без збереження */ }
}

/* --------------------------------------------------------------- малюнок */
function buildMap() {
  svg.setAttribute('viewBox', `0 0 ${DATA.width} ${DATA.height}`);
  $('backdrop').setAttribute('d', DATA.backdrop);

  const seen = {};
  for (const c of DATA.countries) {
    const i = seen[c.region] = (seen[c.region] ?? -1) + 1;
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', c.d);
    p.setAttribute('class', 'cy');
    p.style.setProperty('--fill', shadeOf(c.region, i));
    p.dataset.id = c.id;
    gCountries.appendChild(p);
    paths.set(c.id, p);

    if (c.tiny) {
      const m = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      m.setAttribute('cx', c.c[0]);
      m.setAttribute('cy', c.c[1]);
      m.setAttribute('r', 7);
      m.setAttribute('class', 'mk');
      m.dataset.id = c.id;
      gMarkers.appendChild(m);
      marks.set(c.id, m);
    }
  }
}

/* Мікродержави ловлять клік по кружечку — інакше в них не влучити. */
function sizeMarkers() {
  const r = Math.max(1.6, 7 / view.k);
  for (const m of marks.values()) m.setAttribute('r', r);
}

function pool() {
  return DATA.countries.filter(c => state.regions.has(c.region));
}

function paint() {
  const active = new Set(pool().map(c => c.id));
  const study = state.mode === 'study';

  for (const c of DATA.countries) {
    const p = paths.get(c.id);
    const inPlay = active.has(c.id);
    const cls = ['cy'];

    if (study) {
      cls.push('tint');
      if (!inPlay) cls.push('dim');
      cls.push('hit');
    } else {
      if (!inPlay) cls.push('dim');
      if (state.answered.has(c.id)) cls.push('done');
      if (state.mode === 'find' && inPlay) cls.push('hit');
    }
    p.setAttribute('class', cls.join(' '));

    const m = marks.get(c.id);
    if (m) {
      const mc = ['mk'];
      if (inPlay && (study || state.mode === 'find')) mc.push('hit', 'show');
      else if (inPlay) mc.push('show');
      m.setAttribute('class', mc.join(' '));
    }
  }

  // У режимах «Назви країну» / «Вгадай регіон» підсвічуємо загадану країну.
  if (state.current && (state.mode === 'name' || state.mode === 'region')) {
    const p = paths.get(state.current.id);
    p.setAttribute('class', p.getAttribute('class') + ' target');
    const m = marks.get(state.current.id);
    if (m) m.setAttribute('class', m.getAttribute('class') + ' show target');
  }

  drawLabels();
}

/* Підписи лише в режимі вивчення: сталий екранний розмір, більші країни
   мають пріоритет, а ті, що не влізли, з'являються при наближенні. */
function drawLabels() {
  gLabels.textContent = '';
  if (state.mode !== 'study') return;

  const k = view.k;
  const fs = 12 / k;
  const active = new Set(pool().map(c => c.id));
  const vx0 = -view.x / k, vx1 = (DATA.width - view.x) / k;
  const vy0 = -view.y / k, vy1 = (DATA.height - view.y) / k;

  const boxes = [];
  const hits = (b) => boxes.some(o =>
    b.x < o.x + o.w && o.x < b.x + b.w && b.y < o.y + o.h && o.y < b.y + b.h);

  // Звичайні країни за спаданням площі, мікродержави — в останню чергу:
  // їхні підписи інакше витісняють сусідів. Що не влізло — при наближенні.
  const tier = (c) => (c.tiny ? 1 : 0);
  const cands = DATA.countries
    .filter(c => active.has(c.id) && (c.tiny || c.a * k * k >= 260) &&
                 c.c[0] > vx0 && c.c[0] < vx1 && c.c[1] > vy0 && c.c[1] < vy1)
    .sort((x, y) => tier(x) - tier(y) || y.a - x.a);

  // Якщо підпис не влазить у центрі країни, пробуємо кілька зсувів поруч.
  const NUDGE = [[0, 0], [0, -11], [0, 11], [-16, 0], [16, 0], [0, -20], [0, 20]];

  for (const c of cands) {
    const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    t.setAttribute('font-size', c.tiny ? fs * 0.88 : fs);
    t.setAttribute('stroke-width', 3 / k);
    t.setAttribute('class', 'lbl');
    t.textContent = c.name;
    gLabels.appendChild(t);

    const baseY = c.c[1] - (c.tiny ? 11 / k : 0);
    const pad = 1.5 / k;
    let placed = null;
    for (const [dx, dy] of NUDGE) {
      t.setAttribute('x', c.c[0] + dx / k);
      t.setAttribute('y', baseY + dy / k);
      const bb = t.getBBox();
      const box = { x: bb.x - pad, y: bb.y - pad, w: bb.width + 2 * pad, h: bb.height + 2 * pad };
      if (!hits(box)) { placed = box; break; }
    }
    if (placed) boxes.push(placed);
    else gLabels.removeChild(t);
  }
}

function flash(id, cls, ms = 700) {
  const nodes = [paths.get(id), marks.get(id)].filter(Boolean);
  nodes.forEach(n => n.setAttribute('class', n.getAttribute('class') + ' ' + cls));
  if (ms) setTimeout(() => nodes.forEach(n => {
    n.setAttribute('class', n.getAttribute('class').replace(' ' + cls, ''));
  }), ms);
}

/* ------------------------------------------------------- масштаб і зсув */
const view = { k: 1, x: 0, y: 0 };

let labelFrame = 0;
function applyView() {
  gViewport.setAttribute('transform', `translate(${view.x} ${view.y}) scale(${view.k})`);
  sizeMarkers();
  if (state.mode === 'study') {
    cancelAnimationFrame(labelFrame);
    labelFrame = requestAnimationFrame(drawLabels);
  }
}
function fit() {
  view.k = 1; view.x = 0; view.y = 0;
  applyView();
}
function zoomAt(factor, cx, cy) {
  const k = Math.min(14, Math.max(1, view.k * factor));
  const f = k / view.k;
  view.x = cx - (cx - view.x) * f;
  view.y = cy - (cy - view.y) * f;
  view.k = k;
  clampView();
  applyView();
}
function clampView() {
  const w = DATA.width, h = DATA.height;
  const minX = w - w * view.k, minY = h - h * view.k;
  view.x = Math.min(0, Math.max(minX, view.x));
  view.y = Math.min(0, Math.max(minY, view.y));
}
function toMap(ev) {
  const r = svg.getBoundingClientRect();
  const sx = DATA.width / r.width, sy = DATA.height / r.height;
  const scale = Math.max(sx, sy);           // preserveAspectRatio="xMidYMid meet"
  const offX = (r.width * scale - DATA.width) / 2;
  const offY = (r.height * scale - DATA.height) / 2;
  return {
    x: (ev.clientX - r.left) * scale - offX,
    y: (ev.clientY - r.top) * scale - offY,
  };
}
function focusOn(c, k = 6) {
  view.k = k;
  view.x = DATA.width / 2 - c.c[0] * k;
  view.y = DATA.height / 2 - c.c[1] * k;
  clampView();
  applyView();
}

/* ------------------------------------------------------------- раунд */
function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function restart() {
  const p = pool();
  state.queue = shuffle(p.map(c => c.id));
  state.current = null;
  state.score = 0;
  state.asked = 0;
  state.streak = 0;
  state.attempts = 0;
  state.missed.clear();
  state.answered.clear();
  state.locked = false;
  state.startedAt = Date.now();
  $('sheet').hidden = true;
  fit();
  paint();
  renderList();
  next();
}

function next() {
  state.attempts = 0;
  state.locked = false;
  if (state.mode === 'study') {
    state.current = null;
    paint();
    setPrompt('Вивчення', 'Регіони Європи', MODES.study.hint);
    $('choices').textContent = '';
    updateStats();
    return;
  }
  if (!state.queue.length) { finish(); return; }
  state.current = byId.get(state.queue.shift());
  paint();
  // У режимах «назви країну» / «вгадай регіон» дрібну країну треба показати —
  // інакше підсвітку просто не видно.
  if (state.mode === 'name' || state.mode === 'region') {
    if (state.current.a < 500) focusOn(state.current, state.current.tiny ? 9 : 3.5);
    else fit();
  }
  renderQuestion();
  renderList();
  updateStats();
}

function renderQuestion() {
  const c = state.current;
  const m = MODES[state.mode];
  const box = $('choices');
  box.textContent = '';

  if (state.mode === 'find') {
    setPrompt(m.kicker, c.name, m.hint);
    return;
  }
  if (state.mode === 'name') {
    setPrompt(m.kicker, 'Підсвічена країна', m.hint);
    const p = pool();
    const src = p.length >= 4 ? p : DATA.countries;      // варіанти з обраних регіонів
    const near = shuffle(src.filter(x => x.id !== c.id && x.region === c.region));
    const far  = shuffle(src.filter(x => x.id !== c.id && x.region !== c.region));
    const opts = shuffle([c, ...near, ...far].filter((x, i, a) => a.indexOf(x) === i).slice(0, 4));
    opts.forEach(o => box.appendChild(choiceBtn(o.name, o.id === c.id)));
    return;
  }
  // region
  setPrompt(m.kicker, c.name, m.hint);
  REGION_KEYS.forEach(k => {
    const b = choiceBtn(REGIONS[k].name + ' Європа', k === c.region);
    b.style.borderLeft = '4px solid ' + REGIONS[k].color;
    box.appendChild(b);
  });
}

function choiceBtn(text, correct) {
  const b = document.createElement('button');
  b.className = 'choice';
  b.textContent = text;
  if (correct) b.dataset.correct = '1';
  b.addEventListener('click', () => answerChoice(b, correct));
  return b;
}

function setPrompt(kicker, title, hint) {
  $('pKicker').textContent = kicker;
  $('pTitle').textContent = title;
  $('pHint').textContent = hint;
}

function answerChoice(btn, correct) {
  if (state.locked) return;
  if (correct) {
    state.locked = true;
    btn.classList.add('good');
    [...$('choices').children].forEach(b => b.disabled = true);
    scoreHit();
    setTimeout(next, 620);
  } else {
    btn.classList.add('bad');
    btn.disabled = true;
    scoreMiss();
  }
}

function pick(id) {
  if (state.mode === 'study') {
    const c = byId.get(id);
    setPrompt(REGIONS[c.region].name + ' Європа', c.name, 'Клацай далі, щоб вивчати карту');
    flash(id, 'good', 500);
    return;
  }
  if (state.mode !== 'find' || state.locked || !state.current) return;
  if (!state.regions.has(byId.get(id).region)) return;

  if (id === state.current.id) {
    state.locked = true;
    flash(id, 'good', 620);
    scoreHit();
    setTimeout(next, 620);
  } else {
    flash(id, 'wrong', 620);
    scoreMiss();
    if (state.attempts >= 2) {
      state.locked = true;
      flash(state.current.id, 'reveal', 1100);
      toast('Це ' + state.current.name, 'bad');
      setTimeout(next, 1150);
    } else {
      $('pHint').textContent = 'Не те — спробуй ще (' + (2 - state.attempts) + ')';
    }
  }
}

function scoreHit() {
  state.asked++;
  state.streak++;
  if (state.attempts === 0) {
    state.score++;
    state.answered.add(state.current.id);
  } else {
    state.missed.add(state.current.id);
  }
  if (state.streak > state.best) { state.best = state.streak; savePrefs(); }
  toast('Правильно', 'ok');
  updateStats();
}

function scoreMiss() {
  state.attempts++;
  state.streak = 0;
  if (state.current) state.missed.add(state.current.id);
  updateStats();
  if (state.mode !== 'find' && state.attempts >= 3) {
    state.asked++;
    state.locked = true;
    const right = $('choices').querySelector('[data-correct]');
    if (right) right.classList.add('good');
    [...$('choices').children].forEach(b => b.disabled = true);
    if (state.current) toast('Це ' + state.current.name, 'bad');
    setTimeout(next, 1100);
  }
}

function updateStats() {
  const total = pool().length;
  $('stScore').textContent = state.score;
  $('stLeft').textContent = state.queue.length + (state.current ? 1 : 0);
  $('stStreak').textContent = state.streak;
  const done = state.asked;
  $('stAcc').textContent = done ? Math.round(state.score / done * 100) + '%' : '—';
  $('lCount').textContent = state.answered.size + ' / ' + total;
}

function finish() {
  state.current = null;
  const total = pool().length;
  const secs = Math.max(1, Math.round((Date.now() - state.startedAt) / 1000));
  $('shTitle').textContent = state.score === total ? 'Ідеально! 🎉' : 'Раунд завершено';
  $('shSub').textContent = `${MODES[state.mode].kicker} · ${[...state.regions].map(r => REGIONS[r].name).join(', ')}`;
  $('shGrid').innerHTML =
    `<div><b>${state.score}/${total}</b><span>з першої</span></div>` +
    `<div><b>${Math.round(state.score / total * 100)}%</b><span>точність</span></div>` +
    `<div><b>${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}</b><span>час</span></div>`;
  const miss = [...state.missed].map(id => byId.get(id).name);
  $('shMiss').innerHTML = miss.length
    ? 'Повтори: ' + miss.map(n => `<b>${n}</b>`).join(', ')
    : 'Жодної помилки — усі країни з першої спроби.';
  $('sheet').hidden = false;
  paint();
  updateStats();
}

/* ------------------------------------------------------------ інтерфейс */
function renderChips() {
  const box = $('chips');
  box.textContent = '';
  for (const k of REGION_KEYS) {
    const n = DATA.countries.filter(c => c.region === k).length;
    const b = document.createElement('button');
    b.className = 'chip' + (state.regions.has(k) ? ' is-on' : '');
    b.style.setProperty('--c', REGIONS[k].color + '33');
    b.style.color = state.regions.has(k) ? REGIONS[k].color : '';
    b.innerHTML = `<i></i>${REGIONS[k].name} <small>${n}</small>`;
    b.addEventListener('click', () => {
      if (state.regions.has(k)) {
        if (state.regions.size === 1) return;   // хоча б один регіон має лишитись
        state.regions.delete(k);
      } else {
        state.regions.add(k);
      }
      savePrefs(); renderChips(); restart();
    });
    box.appendChild(b);
  }
}

function renderLegend() {
  $('legend').innerHTML = REGION_KEYS
    .map(k => `<div><i style="background:${REGIONS[k].color}"></i>${REGIONS[k].name} Європа — ${DATA.countries.filter(c => c.region === k).length} країн</div>`)
    .join('') + `<div style="margin-top:8px;opacity:.75">Усього ${DATA.countries.length} країн, разом із Сан-Марино, Ватиканом, Монако, Андоррою, Ліхтенштейном і Мальтою.</div>`;
}

function renderList() {
  const ul = $('clist');
  ul.textContent = '';
  const study = state.mode === 'study';
  for (const c of pool().slice().sort((a, b) => a.name.localeCompare(b.name, 'uk'))) {
    const li = document.createElement('li');
    const now = state.current && state.current.id === c.id && state.mode !== 'find';
    li.className = [
      state.answered.has(c.id) ? 'done' : '',
      state.missed.has(c.id) && !state.answered.has(c.id) ? 'miss' : '',
      now ? 'now' : '',
      study ? 'hit' : '',
    ].filter(Boolean).join(' ');
    li.innerHTML = `<i style="background:${REGIONS[c.region].color}"></i>${c.name}`;
    if (study) {
      li.addEventListener('click', () => { focusOn(c, c.tiny ? 9 : 4); pick(c.id); });
    }
    ul.appendChild(li);
  }
}

let toastTimer = 0;
function toast(text, kind) {
  const t = $('toast');
  t.textContent = text;
  t.className = 'toast ' + kind;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 900);
}

function setMode(m) {
  state.mode = m;
  [...$('modes').children].forEach(b => b.classList.toggle('is-on', b.dataset.mode === m));
  savePrefs();
  restart();
}

/* ------------------------------------------------------------- події */
function wire() {
  $('modes').addEventListener('click', e => {
    const b = e.target.closest('.mode');
    if (b) setMode(b.dataset.mode);
  });
  $('btnAll').addEventListener('click', () => {
    state.regions = new Set(REGION_KEYS);
    savePrefs(); renderChips(); restart();
  });
  $('btnRestart').addEventListener('click', restart);
  $('shAgain').addEventListener('click', restart);
  $('shClose').addEventListener('click', () => { $('sheet').hidden = true; });

  $('zIn').addEventListener('click', () => zoomAt(1.5, DATA.width / 2, DATA.height / 2));
  $('zOut').addEventListener('click', () => zoomAt(1 / 1.5, DATA.width / 2, DATA.height / 2));
  $('zFit').addEventListener('click', fit);

  svg.addEventListener('wheel', e => {
    e.preventDefault();
    const p = toMap(e);
    zoomAt(e.deltaY < 0 ? 1.18 : 1 / 1.18, p.x, p.y);
  }, { passive: false });

  // Перетягування однією вказівкою, масштаб — колесом або двома пальцями.
  const pointers = new Map();
  let drag = null, pinch = null, moved = 0;

  const mid = () => {
    const [a, b] = [...pointers.values()];
    return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2,
             d: Math.hypot(a.x - b.x, a.y - b.y) };
  };

  svg.addEventListener('pointerdown', e => {
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    svg.setPointerCapture(e.pointerId);
    if (pointers.size === 2) {
      const m = mid();
      pinch = { d: m.d, k: view.k };
      drag = null;
      moved = 99;                      // жест — не клік
    } else if (pointers.size === 1) {
      drag = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
      moved = 0;
      svg.classList.add('dragging');
    }
  });

  svg.addEventListener('pointermove', e => {
    if (pointers.has(e.pointerId)) pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    if (pinch && pointers.size >= 2) {
      const m = mid();
      if (m.d > 0 && pinch.d > 0) {
        const want = Math.min(14, Math.max(1, pinch.k * (m.d / pinch.d)));
        const c = toMap({ clientX: m.x, clientY: m.y });
        zoomAt(want / view.k, c.x, c.y);
      }
      return;
    }
    if (!drag) { hover(e.target.dataset && e.target.dataset.id, e); return; }

    const r = svg.getBoundingClientRect();
    const scale = Math.max(DATA.width / r.width, DATA.height / r.height);
    const dx = (e.clientX - drag.x) * scale, dy = (e.clientY - drag.y) * scale;
    moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
    view.x = drag.vx + dx; view.y = drag.vy + dy;
    clampView(); applyView();
  });

  const endPointer = e => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch = null;
    svg.classList.remove('dragging');
    const wasGesture = moved > 6;
    drag = null;
    if (wasGesture || pointers.size) return;
    const id = e.target.dataset && e.target.dataset.id;
    if (id) pick(id);
  };
  svg.addEventListener('pointerup', endPointer);
  svg.addEventListener('pointercancel', e => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch = null;
    drag = null;
    svg.classList.remove('dragging');
  });

  svg.addEventListener('pointerleave', () => { $('tip').hidden = true; });

  document.addEventListener('keydown', e => {
    if (e.key === 'r' || e.key === 'R' || e.key === 'к' || e.key === 'К') restart();
    if (e.key === 'Escape') { $('sheet').hidden = true; fit(); }
    if (e.key >= '1' && e.key <= '4') {
      const b = $('choices').children[+e.key - 1];
      if (b && !b.disabled) b.click();
    }
    if (e.key === 'z' || e.key === 'Z') {
      if (state.current) focusOn(state.current, state.current.tiny ? 9 : 4);
    }
  });
}

function hover(id, ev) {
  const t = $('tip');
  const show = id && (state.mode === 'study');
  if (!show) { t.hidden = true; return; }
  const c = byId.get(id);
  if (!c || !state.regions.has(c.region)) { t.hidden = true; return; }
  const r = svg.getBoundingClientRect();
  t.innerHTML = `${c.name}<em>${REGIONS[c.region].name} Європа</em>`;
  t.style.left = (ev.clientX - r.left) + 'px';
  t.style.top = (ev.clientY - r.top) + 'px';
  t.hidden = false;
}

/* --------------------------------------------------------------- старт */
loadPrefs();
buildMap();
renderChips();
renderLegend();
wire();
[...$('modes').children].forEach(b => b.classList.toggle('is-on', b.dataset.mode === state.mode));
fit();
restart();
})();
