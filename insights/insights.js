const state = {
  data: null,
  seatData: null,
  automation: null,
  selectedStore: '',
  scope: 'store',
};

const FOCUS_STORES = ['鶴見UNO', 'エスパス日拓新宿歌舞伎町'];
const TODAY = new Date('2026-06-22T00:00:00+09:00');
const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[ch]));

function toNumber(value) {
  if(value === null || value === undefined || value === '') return null;
  const n = Number(String(value).replace(/,/g, ''));
  return Number.isFinite(n) ? n : null;
}

function parseYmd(value) {
  const text = String(value || '').slice(0, 10);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(text)) return null;
  const d = new Date(`${text}T00:00:00+09:00`);
  return Number.isNaN(d.getTime()) ? null : d;
}

function daysLag(ymd) {
  const d = parseYmd(ymd);
  if(!d) return null;
  return Math.round((TODAY - d) / 86400000);
}

function fmtSigned(value, suffix = '') {
  const n = toNumber(value);
  if(n === null) return '-';
  return `${n >= 0 ? '+' : ''}${Math.round(n).toLocaleString()}${suffix}`;
}

function fmtNumber(value, suffix = '') {
  const n = toNumber(value);
  if(n === null) return '-';
  return `${Math.round(n).toLocaleString()}${suffix}`;
}

function fmtRate(value) {
  const n = toNumber(value);
  if(n === null) return '-';
  return `${Math.round(n * 10) / 10}%`;
}

function toneClass(toneOrLabel, avg = null, count = null, minCount = 10) {
  const text = String(toneOrLabel || '');
  if(text.includes('古い')) return 'stale';
  if(text.includes('件数少') || text === 'thin') return 'thin';
  if(text.includes('落ち') || text === 'down') return 'down';
  if(text.includes('強') || text.includes('注目') || text === 'up') return 'up';
  const c = toNumber(count);
  const a = toNumber(avg);
  if(c !== null && c < minCount) return 'thin';
  if(a !== null && a >= 100) return 'up';
  if(a !== null && a <= -120) return 'down';
  return '';
}

function qualityLabel({ ymd, count, minCount = 10 }) {
  const lag = daysLag(ymd);
  if(lag !== null && lag >= 8) return { label: 'データ古い', tone: 'stale', detail: `${lag}日前` };
  if(toNumber(count) !== null && toNumber(count) < minCount) return { label: '件数少', tone: 'thin', detail: `${fmtNumber(count, '件')}` };
  return { label: '要観察', tone: '', detail: lag === null ? '日付不明' : `${lag}日前` };
}

async function fetchJson(path) {
  const res = await fetch(path, { cache: 'no-store' });
  if(!res.ok) throw new Error(`${path} HTTP ${res.status}`);
  const text = await res.text();
  return JSON.parse(text.replace(/^\uFEFF/, ''));
}

async function loadAll() {
  $('statusLine').textContent = 'データ読込中...';
  const [data, seatData, automation] = await Promise.all([
    fetchJson('../data.json'),
    fetchJson('../seat_data.json'),
    fetchJson('../automation_status.json').catch(() => null),
  ]);
  state.data = data;
  state.seatData = seatData;
  state.automation = automation;
  state.selectedStore = state.selectedStore || firstStore();
  populateControls();
  renderAll();
}

function firstStore() {
  return storeNames()[0] || '';
}

function allStoreNames() {
  const names = state.data?.stores?.length ? state.data.stores : Object.keys(state.data?.byStore || {});
  return names.filter(Boolean);
}

function storeNames() {
  const all = allStoreNames();
  const focus = FOCUS_STORES.filter((store) => all.includes(store));
  return focus.length ? focus : all;
}

function byStore(store = state.selectedStore) {
  return state.data?.byStore?.[store] || {};
}

function trendView(store = state.selectedStore) {
  return byStore(store).trendView || {};
}

function populateControls() {
  if(!state.selectedStore) state.selectedStore = firstStore();
}

function renderAll() {
  renderHero();
  renderStoreSwitch();
  renderSnapshot();
  renderFreshness();
  renderStoreMomentum();
  renderTiming();
  renderModels();
  renderBands();
}

function renderStoreSwitch() {
  const active = state.selectedStore || firstStore();
  $('storeSwitch').innerHTML = `<div class="store-switcher">
    ${storeNames().map((store) => {
      const row = storeMomentumRows().find((item) => item.store === store) || {};
      const selected = store === active ? 'active' : '';
      return `<button type="button" class="${selected}" data-store="${escapeHtml(store)}">
        <span>${escapeHtml(store)}</span>
        <b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b>
      </button>`;
    }).join('')}
  </div>`;
}

function storeFreshnessRows() {
  return storeNames().map((store) => {
    const raw = state.data?.store_freshness?.[store] || {};
    const tvFresh = trendView(store).dataFreshness || {};
    const ymd = raw.data_date || raw.dataDate || tvFresh.latestDate || tvFresh.sourceYmd || state.data?.data_date || '';
    const st = trendView(store).storeTrend || {};
    const recent = st.recent30 || {};
    return {
      store,
      ymd,
      lag: daysLag(ymd),
      rows: recent.count,
      label: qualityLabel({ ymd, count: recent.count, minCount: 100 }).label,
      scrapedAt: raw.scraped_at || '',
    };
  });
}

function renderHero() {
  const stores = storeNames();
  const freshness = storeFreshnessRows();
  const stale = freshness.filter((row) => row.lag === null || row.lag >= 8).length;
  const latest = freshness.slice().sort((a, b) => (a.lag ?? 999) - (b.lag ?? 999))[0];
  $('statusLine').textContent = `対象: 鶴見UNO / エスパス / data ${state.data?.data_date || '-'} / source ${state.automation?.source || '-'}`;
  $('heroStats').innerHTML = [
    ['対象', `${stores.length}店`],
    ['最新', latest?.ymd || '-'],
    ['古い', `${stale}店`],
  ].map(([label, value]) => `<div class="hero-stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join('');
}

function renderSnapshot() {
  const freshness = storeFreshnessRows();
  const plan = buildStorePlan(state.selectedStore || firstStore());

  $('snapshotView').innerHTML = `
    <div class="snapshot-title">
      <h2>${escapeHtml(plan.store)} の狙い筋</h2>
      <span>店 → 機種 → 癖 → 場所</span>
    </div>
    <div class="store-plan-grid">
      ${renderStorePlanCard(plan)}
    </div>
    <div class="route-board">
      ${renderRouteStep('1', '店', plan.store, plan.momentum.avg, 'まず店の状態を見る')}
      ${renderRouteStep('2', '機種', plan.model?.model || '-', plan.model?.avg, '店内で扱いが上向き')}
      ${renderRouteStep('3', '癖', plan.timing?.label || '-', plan.timing?.avg, '日付・末尾・曜日の偏り')}
      ${renderRouteStep('4', '場所', plan.band ? `${plan.band.band}番台` : '-', plan.band?.avg, '台番帯で最後に絞る')}
    </div>
    <div class="dashboard-grid store-focus">
      ${renderStoreFocus(plan)}
      ${renderPatternHeat(topTimingItemsForStores([plan.store]).slice(0, 8))}
      ${renderFreshnessStrip([plan.fresh])}
    </div>`;
}

function buildStorePlan(store) {
  const momentum = storeMomentumRows().find((row) => row.store === store) || { store };
  const fresh = storeFreshnessRows().find((row) => row.store === store) || {};
  const models = modelItemsForStores([store]).sort((a, b) => b.avg - a.avg);
  const timing = topTimingItemsForStores([store])[0];
  const band = bandItemsForStores([store])[0];
  const model = models[0];
  const stalePenalty = fresh.lag !== null && fresh.lag >= 8 ? 120 : 0;
  const score = (toNumber(momentum.avg) || 0) + (toNumber(momentum.delta) || 0) * 0.4 + (toNumber(model?.avg) || 0) * 0.08 + (toNumber(timing?.avg) || 0) * 0.04 + (toNumber(band?.avg) || 0) * 0.05 - stalePenalty;
  const label = fresh.lag !== null && fresh.lag >= 8 ? 'データ古い' : score >= 140 ? '根拠厚め' : score >= 40 ? '狙い筋あり' : '要観察';
  return { store, momentum, fresh, model, timing, band, score, label };
}

function renderStorePlanCard(plan) {
  const cls = toneClass(plan.label, plan.momentum.avg, plan.momentum.count, 100);
  return `<article class="plan-card ${cls}">
    <div class="plan-head">
      <div><span>STORE</span><strong>${escapeHtml(plan.store)}</strong></div>
      <b class="${cls}">${escapeHtml(plan.label)}</b>
    </div>
    <div class="plan-main">
      <div class="plan-score ${plan.momentum.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(plan.momentum.avg, '枚')}</div>
      <p>直近30日 / 前30日比 ${fmtSigned(plan.momentum.delta, '枚')} / 勝率 ${fmtRate(plan.momentum.win)}</p>
    </div>
    <div class="plan-route">
      ${renderSignalBox('機種', plan.model?.model, plan.model?.avg, `${fmtNumber(plan.model?.count, '件')} / ${escapeHtml(plan.model?.category || '-')}`)}
      ${renderSignalBox('癖', plan.timing?.label, plan.timing?.avg, `${escapeHtml(plan.timing?.type || '-')} / ${fmtNumber(plan.timing?.count, '件')}`)}
      ${renderSignalBox('場所', plan.band ? `${plan.band.band}番台` : '-', plan.band?.avg, `${fmtNumber(plan.band?.tais, '台')} / ${fmtNumber(plan.band?.count, '件')}`)}
    </div>
    <div class="plan-foot">最新 ${escapeHtml(plan.fresh.ymd || '-')} / 遅延 ${plan.fresh.lag === null ? '-' : `${plan.fresh.lag}日`}</div>
  </article>`;
}

function renderSignalBox(label, title, value, meta) {
  return `<div class="signal-box">
    <span>${escapeHtml(label)}</span>
    <strong>${escapeHtml(title || '-')}</strong>
    <b class="${toNumber(value) >= 0 ? 'plus' : 'minus'}">${fmtSigned(value, '枚')}</b>
    <small>${meta || '-'}</small>
  </div>`;
}

function renderRouteStep(step, label, title, value, note) {
  return `<article class="route-step">
    <span>${escapeHtml(step)}</span>
    <div>
      <b>${escapeHtml(label)}</b>
      <strong>${escapeHtml(title)}</strong>
      <small>${escapeHtml(note)}</small>
    </div>
    <em class="${toNumber(value) >= 0 ? 'plus' : 'minus'}">${fmtSigned(value, '枚')}</em>
  </article>`;
}

function renderStoreFocus(plan) {
  return `<article class="viz-card">
    <div class="viz-head"><strong>店内シグナル</strong><span>重なりを見る</span></div>
    <div class="focus-meter">
      ${renderFocusMeter('店', plan.momentum.avg, plan.momentum.count)}
      ${renderFocusMeter('機種', plan.model?.avg, plan.model?.count)}
      ${renderFocusMeter('癖', plan.timing?.avg, plan.timing?.count)}
      ${renderFocusMeter('場所', plan.band?.avg, plan.band?.count)}
    </div>
  </article>`;
}

function renderFocusMeter(label, value, count) {
  const n = Math.abs(toNumber(value) || 0);
  const width = Math.max(8, Math.min(100, n / 12));
  return `<div class="focus-meter-row">
    <span>${escapeHtml(label)}</span>
    <div class="compare-bar"><i class="${toNumber(value) >= 0 ? 'up' : 'down'}" style="width:${width}%"></i></div>
    <b class="${toNumber(value) >= 0 ? 'plus' : 'minus'}">${fmtSigned(value, '枚')}</b>
    <small>${fmtNumber(count, '件')}</small>
  </div>`;
}

function renderMomentumMap(rows) {
  const valid = rows.filter((row) => row.avg !== null || row.delta !== null);
  if(!valid.length) return '<div class="viz-card"><div class="viz-head"><strong>勢いマップ</strong><span>データなし</span></div></div>';
  const maxAbsAvg = Math.max(1, ...valid.map((row) => Math.abs(row.avg || 0)));
  const maxAbsDelta = Math.max(1, ...valid.map((row) => Math.abs(row.delta || 0)));
  const points = valid.map((row) => {
    const x = 50 + ((row.delta || 0) / maxAbsDelta) * 42;
    const y = 50 - ((row.avg || 0) / maxAbsAvg) * 42;
    const cls = toneClass(row.tone, row.avg, row.count, 100);
    return `<span class="map-dot ${cls}" style="left:${Math.max(7, Math.min(93, x))}%;top:${Math.max(10, Math.min(90, y))}%" title="${escapeHtml(row.store)}"><b>${escapeHtml(shortStore(row.store))}</b></span>`;
  }).join('');
  return `<article class="viz-card">
    <div class="viz-head"><strong>勢いマップ</strong><span>上=強い / 右=上向き</span></div>
    <div class="momentum-map">${points}</div>
  </article>`;
}

function renderPatternHeat(rows) {
  const cells = rows.map((row) => {
    const avg = toNumber(row.avg) || 0;
    const intensity = Math.max(0.08, Math.min(0.36, Math.abs(avg) / 7000));
    const cls = avg >= 0 ? 'up' : 'down';
    return `<div class="heat-tile ${cls}" style="--heat-alpha:${intensity.toFixed(2)}">
      <span>${escapeHtml(row.label)}</span>
      <b>${fmtSigned(row.avg, '枚')}</b>
      <small>${escapeHtml(shortStore(row.store))}</small>
    </div>`;
  }).join('');
  return `<article class="viz-card">
    <div class="viz-head"><strong>癖ヒート</strong><span>日付・末尾・曜日</span></div>
    <div class="heat-matrix">${cells || '<div class="empty">組合せデータなし</div>'}</div>
  </article>`;
}

function renderFreshnessStrip(rows) {
  const sorted = rows.slice().sort((a, b) => (a.lag ?? 999) - (b.lag ?? 999));
  const cells = sorted.map((row) => {
    const lag = row.lag ?? 99;
    const cls = lag >= 8 ? 'stale' : 'fresh';
    const height = Math.max(16, Math.min(72, 76 - lag * 2));
    return `<span class="fresh-cell ${cls}" style="height:${height}px" title="${escapeHtml(`${row.store} ${row.ymd || '-'}`)}"><i>${escapeHtml(shortStore(row.store))}</i></span>`;
  }).join('');
  return `<article class="viz-card">
    <div class="viz-head"><strong>鮮度ストリップ</strong><span>低いほど古い</span></div>
    <div class="fresh-strip">${cells}</div>
  </article>`;
}

function renderFreshness() {
  const selected = selectedStoresForScope();
  const rows = storeFreshnessRows().filter((row) => selected.includes(row.store)).sort((a, b) => (a.lag ?? 999) - (b.lag ?? 999));
  const topRows = rows.slice(0, 4);
  const allCards = rows.map(renderFreshnessCard).join('');
  $('freshnessView').innerHTML = `
    <div class="summary-strip">${topRows.map((row) => {
      const q = qualityLabel({ ymd: row.ymd, count: row.rows, minCount: 100 });
      const lagText = row.lag === null ? '日付不明' : `${row.lag}日遅れ`;
      return `<div class="summary-row">
        <div class="summary-main">
          <strong>${escapeHtml(row.store)}</strong>
          <span>${escapeHtml(row.ymd || '-')} / ${fmtNumber(row.rows, '件')} / ${escapeHtml(q.label)}</span>
          <div class="bar"><i class="${q.tone}" style="width:${Math.max(8, Math.min(100, 100 - (row.lag || 0) * 5))}%"></i></div>
        </div>
        <div class="summary-score ${q.tone === 'stale' ? 'warn' : ''}">${escapeHtml(lagText)}</div>
      </div>`;
    }).join('')}</div>
    <details class="compact-details">
      <summary>全店舗の鮮度を見る</summary>
      <div class="grid cols-3">${allCards}</div>
    </details>`;
}

function renderFreshnessCard(row) {
    const q = qualityLabel({ ymd: row.ymd, count: row.rows, minCount: 100 });
    return `<article class="card ${q.tone}">
      <div class="card-head"><strong>${escapeHtml(row.store)}</strong><span class="badge ${q.tone}">${escapeHtml(q.label)}</span></div>
      <div class="metrics">
        <div class="metric"><span>最新日</span><b>${escapeHtml(row.ymd || '-')}</b></div>
        <div class="metric"><span>遅延</span><b class="${row.lag >= 8 ? 'warn' : ''}">${row.lag === null ? '-' : `${row.lag}日`}</b></div>
        <div class="metric"><span>直近件数</span><b>${fmtNumber(row.rows, '件')}</b></div>
        <div class="metric"><span>取得</span><b>${escapeHtml(row.scrapedAt ? row.scrapedAt.slice(0, 10) : '-')}</b></div>
      </div>
    </article>`;
}

function storeMomentumRows() {
  return storeNames().map((store) => {
    const st = trendView(store).storeTrend || {};
    const recent = st.recent30 || {};
    const prior = st.prior30 || {};
    const fresh = storeFreshnessRows().find((row) => row.store === store) || {};
    return {
      store,
      label: st.label || '要観察',
      tone: st.tone || '',
      avg: toNumber(recent.avgDiff),
      count: toNumber(recent.count),
      win: toNumber(recent.winRate),
      priorAvg: toNumber(prior.avgDiff),
      delta: toNumber(st.delta30),
      ymd: fresh.ymd,
      lag: fresh.lag,
    };
  });
}

function renderStoreMomentum() {
  const selected = selectedStoresForScope();
  const rows = storeMomentumRows().filter((row) => selected.includes(row.store));
  const valid = rows.filter((row) => row.avg !== null || row.delta !== null);
  const maxAbsAvg = Math.max(1, ...valid.map((row) => Math.abs(row.avg || 0)));
  const maxAbsDelta = Math.max(1, ...valid.map((row) => Math.abs(row.delta || 0)));
  const points = valid.map((row) => {
    const x = 50 + ((row.delta || 0) / maxAbsDelta) * 42;
    const y = 50 - ((row.avg || 0) / maxAbsAvg) * 42;
    return `<button class="point ${toneClass(row.tone, row.avg, row.count)}" style="left:${Math.max(6, Math.min(94, x))}%;top:${Math.max(8, Math.min(92, y))}%" title="${escapeHtml(`${row.store} ${fmtSigned(row.avg, '枚')} / 前30日比 ${fmtSigned(row.delta, '枚')}`)}">${escapeHtml(shortStore(row.store))}</button>`;
  }).join('');
  const ranked = rows
    .filter((row) => row.avg !== null)
    .sort((a, b) => visibleScore(b) - visibleScore(a))
    .slice(0, 8);
  $('storeMomentumView').innerHTML = `
    <div class="visual-board">
      <div class="mini-chart">${ranked.slice(0, 7).map((row) => renderChartRow(row.store, row.avg, row.count, toneClass(row.tone, row.avg, row.count, 100))).join('')}</div>
      <div class="tile-grid">${ranked.slice(0, 4).map((row) => renderStoreTile(row)).join('')}</div>
    </div>
    <details class="compact-details">
      <summary>散布図と店舗カードを見る</summary>
      <div class="scatter" aria-label="店の勢い散布図">${points}</div>
      <div class="grid cols-2">${ranked.map((row) => renderStoreCard(row)).join('')}</div>
    </details>`;
}

function renderChartRow(label, value, count, cls = '') {
  const n = Math.abs(toNumber(value) || 0);
  const width = Math.max(7, Math.min(100, n / 8));
  return `<div class="chart-row">
    <span>${escapeHtml(label)}</span>
    <div class="chart-bar"><i class="${cls}" style="width:${width}%"></i></div>
    <b class="${toNumber(value) >= 0 ? 'plus' : 'minus'}">${fmtSigned(value, '枚')}</b>
  </div>`;
}

function renderStoreTile(row) {
  const cls = toneClass(row.tone, row.avg, row.count, 100);
  return `<article class="tile">
    <span>${escapeHtml(row.label || '要観察')}</span>
    <strong>${escapeHtml(row.store)}</strong>
    <b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b>
    <span>前30日比 ${fmtSigned(row.delta, '枚')} / ${fmtNumber(row.count, '件')}</span>
  </article>`;
}

function visibleScore(row) {
  const avg = toNumber(row.avg) || 0;
  const delta = toNumber(row.delta) || 0;
  const count = Math.min(toNumber(row.count) || 0, 500) / 500;
  const stalePenalty = row.lag !== null && row.lag >= 8 ? 180 : 0;
  return avg + delta * 0.35 + count * 80 - stalePenalty;
}

function renderStoreSummaryRow(row) {
  const cls = toneClass(row.tone, row.avg, row.count, 100);
  const width = Math.max(8, Math.min(100, Math.abs(row.avg || 0) / 8));
  return `<div class="summary-row">
    <div class="summary-main">
      <strong>${escapeHtml(row.store)}</strong>
      <span>直近30日 ${fmtSigned(row.avg, '枚')} / 前30日比 ${fmtSigned(row.delta, '枚')} / ${fmtNumber(row.count, '件')}</span>
      <div class="bar"><i class="${cls}" style="width:${width}%"></i></div>
    </div>
    <div class="summary-score ${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</div>
  </div>`;
}

function shortStore(store) {
  return String(store || '').replace('マルハンメガシティ2000-', 'M').replace('エスパス日拓新宿歌舞伎町', '歌舞伎').replace('楽園蒲田店', '楽園').replace('店', '').slice(0, 4);
}

function renderStoreCard(row) {
  const q = qualityLabel({ ymd: row.ymd, count: row.count, minCount: 100 });
  const cls = q.tone || toneClass(row.tone, row.avg, row.count, 100);
  return `<article class="card ${cls}">
    <div class="card-head"><strong>${escapeHtml(row.store)}</strong><span class="badge ${cls}">${escapeHtml(q.tone ? q.label : row.label)}</span></div>
    <div class="metrics">
      <div class="metric"><span>直近30日</span><b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b></div>
      <div class="metric"><span>前30日比</span><b class="${row.delta >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.delta, '枚')}</b></div>
      <div class="metric"><span>勝率</span><b>${fmtRate(row.win)}</b></div>
      <div class="metric"><span>件数</span><b>${fmtNumber(row.count, '件')}</b></div>
    </div>
  </article>`;
}

function selectedStoresForScope() {
  return [state.selectedStore || firstStore()].filter(Boolean);
}

function renderTiming() {
  const { dayItems, comboItems } = timingItems();
  const dayRank = dayItems.sort((a, b) => b.avg - a.avg).slice(0, 8);
  const comboRank = comboItems.sort((a, b) => b.avg - a.avg).slice(0, 12);
  $('timingView').innerHTML = `
    <div class="visual-board">
      <div>
        <div class="snapshot-title"><h2>日付</h2><span>平均差枚</span></div>
        <div class="mini-chart">${dayRank.slice(0, 7).map((row) => renderChartRow(`${row.store} / ${row.label}`, row.avg, row.count, toneClass('', row.avg, row.count, 80))).join('') || '<div class="empty">日付データなし</div>'}</div>
      </div>
      <div>
        <div class="snapshot-title"><h2>組合せ</h2><span>末尾・曜日</span></div>
        <div class="tile-grid">${comboRank.slice(0, 6).map(renderPatternTile).join('') || '<div class="empty">組合せデータなし</div>'}</div>
      </div>
    </div>
    <details class="compact-details">
      <summary>ランキング形式で見る</summary>
      <div class="grid cols-2">
        <div>${renderRankList('強い日付', dayRank)}</div>
        <div>${renderRankList('強い組合せ', comboRank)}</div>
      </div>
    </details>`;
}

function renderPatternTile(row) {
  return `<article class="tile">
    <span>${escapeHtml(row.type)}</span>
    <strong>${escapeHtml(row.label)}</strong>
    <b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b>
    <span>${escapeHtml(row.store)} / ${fmtNumber(row.count, '件')}</span>
  </article>`;
}

function timingItems() {
  return timingItemsForStores(selectedStoresForScope());
}

function timingItemsForStores(stores) {
  const dayItems = [];
  const comboItems = [];
  for(const store of stores) {
    const bs = byStore(store);
    (bs.dayStats || []).forEach((row) => {
      const avg = toNumber(row.avg);
      const count = toNumber(row.total ?? row.count);
      if(avg === null || count === null || count < 80) return;
      dayItems.push({ store, label: `${row.day}日`, avg, count, win: row.plusRate, type: '日付' });
    });
    collectCombo(bs.heatmap, '日付末尾 x 台番末尾', store, 80, comboItems);
    collectCombo(bs.weekMatrix, '第○週 x 曜日', store, 80, comboItems);
    collectCombo(bs.dayWdayMatrix, '日付末尾 x 曜日', store, 80, comboItems);
  }
  return { dayItems, comboItems };
}

function topTimingItems() {
  const { dayItems, comboItems } = timingItems();
  return [...dayItems, ...comboItems].sort((a, b) => b.avg - a.avg);
}

function topTimingItemsForStores(stores) {
  const { dayItems, comboItems } = timingItemsForStores(stores);
  return [...dayItems, ...comboItems].sort((a, b) => b.avg - a.avg);
}

function collectCombo(map, type, store, minCount, out) {
  Object.entries(map || {}).forEach(([key, row]) => {
    const avg = toNumber(row?.avg);
    const count = toNumber(row?.count);
    if(avg === null || count === null || count < minCount) return;
    out.push({ store, key, label: comboLabel(key), type, avg, count, win: row.win });
  });
}

function comboLabel(key) {
  return String(key)
    .replace('tsuki_', '月=')
    .replace('end_', '末尾=')
    .replace('zoro_', 'ゾロ=')
    .replace('_', ' x ');
}

function renderRankList(title, rows) {
  if(!rows.length) return `<div class="empty">${escapeHtml(title)}データなし</div>`;
  return `<div class="rank-list" aria-label="${escapeHtml(title)}">
    ${rows.map((row, i) => `<div class="rank-row">
      <div class="rank-num">${String(i + 1).padStart(2, '0')}</div>
      <div class="rank-main"><strong>${escapeHtml(row.label || row.model || row.store || '-')}</strong><span>${escapeHtml(row.store)} / ${escapeHtml(row.type || '')} / ${fmtNumber(row.count, '件')} / 勝率 ${fmtRate(row.win)}</span></div>
      <div class="rank-score ${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</div>
    </div>`).join('')}
  </div>`;
}

function renderHeatCell(row) {
  return `<div class="heat-cell">
    <strong>${escapeHtml(row.label)}</strong>
    <span class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</span>
    <small class="mini-label">${escapeHtml(row.store)} / ${fmtNumber(row.count, '件')}</small>
  </div>`;
}

function renderModels() {
  const rows = topModelItems(false);
  const strong = rows.sort((a, b) => b.avg - a.avg).slice(0, 12);
  const drops = rows.slice().sort((a, b) => a.avg - b.avg).slice(0, 6);
  $('modelView').innerHTML = `
    <div class="visual-board">
      <div>
        <div class="snapshot-title"><h2>強め推移</h2><span>今月平均</span></div>
        <div class="mini-chart">${strong.slice(0, 8).map((row) => renderChartRow(row.model, row.avg, row.count, toneClass(row.label, row.avg, row.count, 10))).join('')}</div>
      </div>
      <div>
        <div class="snapshot-title"><h2>落ち気味</h2><span>確認用</span></div>
        <div class="tile-grid">${drops.slice(0, 6).map(renderModelTile).join('')}</div>
      </div>
    </div>
    <details class="compact-details">
      <summary>機種カードを全部見る</summary>
      <div class="grid cols-2">
        <div>${renderModelCards('扱い上向き', strong)}</div>
        <div>${renderModelCards('落ち気味', drops)}</div>
      </div>
    </details>`;
}

function renderModelTile(row) {
  return `<article class="tile">
    <span>${escapeHtml(row.category)}</span>
    <strong>${escapeHtml(row.model)}</strong>
    <b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b>
    <span>${escapeHtml(row.store)} / ${fmtNumber(row.count, '件')}</span>
  </article>`;
}

function topModelItems(sort = true) {
  return modelItemsForStores(selectedStoresForScope(), sort);
}

function modelItemsForStores(stores, sort = true) {
  const rows = [];
  stores.forEach((store) => {
    (trendView(store).modelTrends || []).forEach((row) => {
      const count = toNumber(row.thisMonthCount ?? row.count);
      const avg = toNumber(row.thisMonthAvg);
      if(avg === null || count === null) return;
      rows.push({
        store,
        model: row.model || '機種不明',
        avg,
        count,
        delta: toNumber(row.deltaMonth),
        label: row.label || '要観察',
        category: row.category === 'smart_slot' ? 'スマスロ' : 'Aタイプ/通常',
      });
    });
  });
  return sort ? rows.sort((a, b) => b.avg - a.avg) : rows;
}

function renderModelCards(title, rows) {
  if(!rows.length) return `<div class="empty">${escapeHtml(title)}データなし</div>`;
  return `<div class="rank-list">
    ${rows.map((row, i) => {
      const cls = toneClass(row.label, row.avg, row.count, 10);
      return `<article class="card ${cls}">
        <div class="card-head"><strong>${escapeHtml(row.model)}</strong><span class="badge ${cls}">${escapeHtml(row.count < 10 ? '件数少' : row.label)}</span></div>
        <div class="metrics">
          <div class="metric"><span>今月平均</span><b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b></div>
          <div class="metric"><span>先月比</span><b class="${row.delta >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.delta, '枚')}</b></div>
          <div class="metric"><span>件数</span><b>${fmtNumber(row.count, '件')}</b></div>
          <div class="metric"><span>区分</span><b>${escapeHtml(row.category)}</b></div>
        </div>
        <div class="note">${escapeHtml(row.store)}</div>
      </article>`;
    }).join('')}
  </div>`;
}

function renderBands() {
  const ranked = topBandItems().slice(0, 16);
  $('bandView').innerHTML = ranked.length ? `
    <div class="visual-board">
      <div class="mini-chart">${ranked.slice(0, 8).map((row) => renderChartRow(`${row.store} / ${row.band}番台`, row.avg, row.count, toneClass('', row.avg, row.count, 60))).join('')}</div>
      <div class="tile-grid">${ranked.slice(0, 6).map(renderBandTile).join('')}</div>
    </div>
    <details class="compact-details">
      <summary>台番帯カードを見る</summary>
      <div class="grid cols-4">${ranked.map((row) => {
    const cls = toneClass('', row.avg, row.count, 60);
    return `<article class="card ${cls}">
      <div class="card-head"><strong>${escapeHtml(row.band)}番台</strong><span class="badge ${cls}">${row.avg >= 80 ? '注目変化' : '要観察'}</span></div>
      <div class="metrics">
        <div class="metric"><span>平均</span><b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b></div>
        <div class="metric"><span>台数</span><b>${fmtNumber(row.tais, '台')}</b></div>
        <div class="metric"><span>件数</span><b>${fmtNumber(row.count, '件')}</b></div>
        <div class="metric"><span>店舗</span><b>${escapeHtml(shortStore(row.store))}</b></div>
      </div>
    </article>`;
  }).join('')}</div>
    </details>` : '<div class="empty">台番帯データなし</div>';
}

function topBandItems() {
  return bandItemsForStores(selectedStoresForScope());
}

function bandItemsForStores(stores) {
  const rows = [];
  stores.forEach((store) => {
    const bands = new Map();
    (trendView(store).taiTrends || []).forEach((row) => {
      const count = toNumber(row.count);
      const avg = toNumber(row.avgDiff);
      const tai = toNumber(row.taiNum ?? row.tai);
      if(count === null || count < 20 || avg === null || tai === null) return;
      const band = Math.floor(tai / 10) * 10;
      const stat = bands.get(band) || { store, band, weighted: 0, count: 0, tais: 0 };
      stat.weighted += avg * count;
      stat.count += count;
      stat.tais += 1;
      bands.set(band, stat);
    });
    bands.forEach((stat) => {
      if(stat.tais < 3 || !stat.count) return;
      rows.push({ ...stat, avg: stat.weighted / stat.count });
    });
  });
  return rows.sort((a, b) => b.avg - a.avg);
}

function renderBandTile(row) {
  return `<article class="tile">
    <span>${escapeHtml(row.store)}</span>
    <strong>${escapeHtml(row.band)}番台</strong>
    <b class="${row.avg >= 0 ? 'plus' : 'minus'}">${fmtSigned(row.avg, '枚')}</b>
    <span>${fmtNumber(row.tais, '台')} / ${fmtNumber(row.count, '件')}</span>
  </article>`;
}

function getLineRows() {
  const rows = [];
  Object.entries(state.seatData?.data || {}).forEach(([date, stores]) => {
    Object.entries(stores || {}).forEach(([store, items]) => {
      (items || []).forEach((row) => {
        if(row.line) rows.push({ ...row, date, store });
      });
    });
  });
  return rows;
}

function renderLine() {
  const rows = getLineRows();
  if(!rows.length) {
    $('lineView').innerHTML = '<div class="empty">LINEデータなし</div>';
    return;
  }
  const byStoreMap = new Map();
  rows.forEach((row) => {
    const stat = byStoreMap.get(row.store) || { store: row.store, rows: 0, dates: new Set(), labels: new Map(), models: new Set() };
    stat.rows += 1;
    stat.dates.add(row.date);
    stat.models.add(row.model || '機種不明');
    const label = row.treatmentLabel || row.lineStrengthLabel || 'データ不足';
    stat.labels.set(label, (stat.labels.get(label) || 0) + 1);
    byStoreMap.set(row.store, stat);
  });
  const cards = Array.from(byStoreMap.values()).map((stat) => {
    const labels = Array.from(stat.labels.entries()).sort((a, b) => b[1] - a[1]).map(([label, count]) => `${label} ${count}`).join(' / ');
    return `<article class="card thin">
      <div class="card-head"><strong>${escapeHtml(stat.store)}</strong><span class="badge thin">LINE別枠</span></div>
      <div class="metrics">
        <div class="metric"><span>行数</span><b>${fmtNumber(stat.rows, '件')}</b></div>
        <div class="metric"><span>日数</span><b>${fmtNumber(stat.dates.size, '日')}</b></div>
        <div class="metric"><span>機種</span><b>${fmtNumber(stat.models.size, '機種')}</b></div>
        <div class="metric"><span>差枚</span><b>混ぜない</b></div>
      </div>
      <div class="note">${escapeHtml(labels || 'データ不足')}</div>
    </article>`;
  }).join('');
  $('lineView').innerHTML = `<div class="grid cols-3">${cards}</div>`;
}

$('reloadBtn').addEventListener('click', () => loadAll().catch(showError));
$('storeSwitch').addEventListener('click', (event) => {
  const button = event.target.closest('button[data-store]');
  if(!button) return;
  state.selectedStore = button.dataset.store;
  state.scope = 'store';
  renderAll();
});

function showError(error) {
  console.error(error);
  $('statusLine').textContent = `読込エラー: ${error.message}`;
}

loadAll().catch(showError);
