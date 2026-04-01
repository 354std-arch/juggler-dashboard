// ====== グローバル ======
let G = {
  raw:[], dayStats:[], taiDetail:[], dateSummary:[], modelStats:[], nextStats:{}, heatmap:{}, autoSpecial:[], weekMatrix:{}, dayWdayMatrix:{},
  currentTargetContext: null, layer3Scored: [], layer3SelectionMeta: null, storeFreshness: {}, recommendations: []
};
let chartInst = null;
let currentStore = 'all';
let currentTaiFilter = 'all';
let currentModelFilter = '';
let currentPeriod = 30;
let currentTaiPeriod = 0;
let currentModelSpFilter = 'all';
let currentHeatMetric = 'avg';
let currentWeekMetric = 'avg';
let currentDayWdayMetric = 'avg';
let SPECIAL_BY_STORE = {};
const DEFAULT_SPECIAL = [1,6,7,11,16,17,22,26,27];
const GITHUB_TOKEN_STORAGE_KEY = 'github_pat';
const GITHUB_SESSIONS_REPO = '354std-arch/juggler-dashboard';
const GITHUB_SESSIONS_BRANCH = 'main';
const GITHUB_SESSIONS_PATH = 'sessions.json';

// ====== 機種別設定値（合成・BB・RB確率の分母） ======
const MODEL_SETTINGS = {
  'ネオアイムジャグラー':     { syn:{1:168,2:161,3:148,4:142,5:128,6:128}, bb:{1:273,2:269,3:269,4:259,5:259,6:255}, rb:{1:439,2:399,3:331,4:315,5:255,6:255} },
  'ウルトラミラクルジャグラー':{ syn:{1:164,2:158,3:147,4:138,5:130,6:121}, bb:{1:267,2:261,3:256,4:242,5:233,6:216}, rb:{1:425,2:402,3:350,4:322,5:297,6:277} },
  'ミスタージャグラー':       { syn:{1:156,2:152,3:145,4:134,5:124,6:118}, bb:{1:268,2:267,3:260,4:249,5:240,6:237}, rb:{1:374,2:354,3:331,4:291,5:257,6:237} },
  'ジャグラーガールズSS':     { syn:{1:159,2:152,3:142,4:132,5:128,6:119}, bb:{1:273,2:270,3:260,4:250,5:243,6:226}, rb:{1:381,2:350,3:316,4:281,5:270,6:252} },
  'ゴーゴージャグラー3':      { syn:{1:149,2:145,3:139,4:130,5:123,6:117}, bb:{1:259,2:258,3:257,4:254,5:247,6:234}, rb:{1:354,2:332,3:306,4:268,5:247,6:234} },
  'ハッピージャグラーVIII':   { syn:{1:161,2:154,3:146,4:137,5:127,6:120}, bb:{1:273,2:270,3:263,4:254,5:239,6:226}, rb:{1:397,2:362,3:332,4:300,5:273,6:256} },
  'マイジャグラーV':          { syn:{1:163,2:159,3:148,4:135,5:126,6:114}, bb:{1:273,2:270,3:266,4:254,5:240,6:229}, rb:{1:409,2:385,3:336,4:290,5:268,6:229} },
  'ファンキージャグラー2':    { syn:{1:165,2:158,3:150,4:140,5:133,6:119}, bb:{1:266,2:259,3:256,4:249,5:240,6:219}, rb:{1:439,2:407,3:366,4:322,5:299,6:262} },
};

// ====== 機種別小役確率（正確な設定値） ======
const MODEL_YAKUS = {
  'ネオアイムジャグラー': {
    budo:         {1:6.02,  2:6.02,  3:6.02,  4:6.02,  5:6.02,  6:5.78},
    cherry:       {1:32.29, 2:32.29, 3:32.29, 4:32.29, 5:32.29, 6:32.29},
    soloBB:       {1:387.78,2:381.02,3:381.02,4:370.25,5:370.25,6:362.07},
    soloRB:       {1:636.27,2:569.87,3:471.48,4:445.82,5:362.07,6:362.07},
    kadoBB:       {1:1598.43,2:1598.43,3:1598.43,4:1638.40,5:1638.40,6:1638.40},
    kadoRB:       {1:1424.69,2:1337.46,3:1110.77,4:1074.36,5:862.31,6:862.31},
    rareCherryBB: {1:2184.53,2:2184.53,3:2184.53,4:1820.44,5:1820.44,6:1820.44},
  },
  'ウルトラミラクルジャグラー': {
    budo:    {1:5.93,  2:5.93,  3:5.93,  4:5.93,  5:5.87,  6:5.81},
    cherry:  {1:35.1,  2:35.0,  3:34.8,  4:34.6,  5:33.5,  6:33.0},
    soloBB:  {1:334.36,2:332.67,3:329.32,4:310.59,5:304.81,6:281.27},
    soloRB:  {1:595.78,2:546.13,3:489.07,4:436.90,5:414.78,6:378.82},
    cherryBB:{1:1337.46,2:1213.62,3:1149.75,4:1110.77,5:992.96,6:936.22},
    cherryRB:{1:1489.45,2:1524.09,3:1236.52,4:1236.52,5:1057.03,6:1040.25},
  },
  'ミスタージャグラー': {
    budo:    {1:6.29,  2:6.22,  3:6.15,  4:6.09,  5:6.02,  6:5.96},
    cherry:  {1:37.24, 2:37.24, 3:37.24, 4:37.24, 5:37.24, 6:37.24},
    soloBB:  {1:348.59,2:348.59,3:337.81,4:324.43,5:315.07,6:310.59},
    soloRB:  {1:512.00,2:478.36,3:439.83,4:378.82,5:327.68,6:297.89},
    cherryBB:{1:1724.63,2:1680.41,3:1638.40,4:1524.09,5:1424.69,6:1394.38},
    cherryRB:{1:1638.40,2:1598.43,3:1560.38,4:1456.35,5:1365.33,6:1337.46},
  },
  'ジャグラーガールズSS': {
    budo:    {1:5.98,  2:5.98,  3:5.98,  4:5.98,  5:5.88,  6:5.83},
    cherry:  {1:33.56, 2:33.47, 3:33.21, 4:33.15, 5:33.10, 6:32.97},
    soloBB:  {1:387.78,2:381.02,3:370.26,4:350.46,5:337.81,6:312.07},
    soloRB:  {1:520.12,2:481.88,3:436.90,4:397.18,5:383.25,6:358.12},
    cherryBB:{1:923.04, 2:936.22, 3:873.81, 4:873.81, 5:873.81, 6:819.20},
    cherryRB:{1:1424.69,2:1285.02,3:1149.75,4:963.76, 5:923.04, 6:851.11},
  },
  'ゴーゴージャグラー3': {
    budo:    {1:6.25,  2:6.20,  3:6.15,  4:6.07,  5:6.00,  6:5.92},
    cherry:  {1:33.40, 2:33.30, 3:33.20, 4:33.10, 5:32.90, 6:32.80},
    soloBB:  {1:346.75,2:344.92,3:343.12,4:343.12,5:332.67,6:316.59},
    soloRB:  {1:471.48,2:448.87,3:417.42,4:362.07,5:330.99,6:316.59},
    cherryBB:{1:1024.00,2:1024.00,3:1024.00,4:978.14,5:963.76,6:910.22},
    cherryRB:{1:1424.69,2:1285.02,3:1149.75,4:1040.25,5:978.14,6:910.22},
  },
  'ハッピージャグラーVIII': {
    budo:    {1:6.04,  2:6.01,  3:5.98,  4:5.84,  5:5.81,  6:5.79},
    cherry:  {1:62.24, 2:62.47, 3:62.95, 4:64.00, 5:64.57, 6:64.34},
    soloBB:  {1:358.12,2:354.24,3:348.59,4:341.33,5:322.83,6:296.54},
    soloRB:  {1:682.66,2:612.48,3:574.87,4:496.48,5:455.11,6:439.83},
    cherryBB:{1:1149.75,2:1149.75,3:1149.75,4:936.22,5:923.04,6:949.79},
    cherryRB:{1:936.22, 2:885.62, 3:789.59, 4:762.04, 5:682.66, 6:612.48},
  },
  'マイジャグラーV': {
    budo:      {1:5.90,  2:5.85,  3:5.80,  4:5.78,  5:5.76,  6:5.66},
    cherry:    {1:38.1,  2:38.1,  3:38.1,  4:38.1,  5:35.1,  6:35.1},
    nonCherry: {1:38.10, 2:38.10, 3:36.82, 4:35.62, 5:35.62, 6:35.62},
    soloBB:    {1:420.10,2:414.78,3:404.54,4:376.64,5:348.59,6:341.33},
    soloRB:    {1:655.36,2:595.78,3:496.48,4:404.54,5:390.09,6:327.68},
    cherryBB:  {1:1365.33,2:1365.33,3:1365.33,4:1365.33,5:1337.46,6:1129.93},
    cherryRB:  {1:1092.26,2:1092.26,3:1040.25,4:1024.00,5:862.31, 6:762.04},
  },
  'ファンキージャグラー2': {
    budo:    {1:5.94,  2:5.92,  3:5.88,  4:5.83,  5:5.76,  6:5.67},
    cherry:  {1:35.6,  2:35.6,  3:35.6,  4:35.6,  5:35.6,  6:35.6},
    soloBB:  {1:404.54,2:397.19,3:394.80,4:383.25,5:374.49,6:334.37},
    soloRB:  {1:630.15,2:585.14,3:512.00,4:448.88,5:404.54,6:352.34},
    cherryBB:{1:1424.70,2:1365.33,3:1365.33,4:1365.33,5:1285.02,6:1260.31},
    cherryRB:{1:1456.36,2:1337.47,3:1285.02,4:1149.75,5:1149.75,6:1024.00},
  },
};

// 機種別理論機械割
const MODEL_RITU = {
  'ネオアイムジャグラー':     {1:97.1,2:98.2,3:99.3,4:101.0,5:103.0,6:109.0},
  'ウルトラミラクルジャグラー':{1:97.0,2:98.3,3:99.5,4:101.5,5:103.5,6:106.5},
  'ミスタージャグラー':       {1:97.0,2:98.0,3:99.0,4:101.0,5:103.0,6:105.0},
  'ジャグラーガールズSS':     {1:97.2,2:98.3,3:99.4,4:101.3,5:103.2,6:106.0},
  'ゴーゴージャグラー3':      {1:96.5,2:97.8,3:99.1,4:101.0,5:103.0,6:106.0},
  'ハッピージャグラーVIII':   {1:97.3,2:98.5,3:99.7,4:101.6,5:103.8,6:106.8},
  'マイジャグラーV':          {1:97.0,2:98.2,3:99.3,4:101.2,5:103.3,6:106.3},
  'ファンキージャグラー2':    {1:97.0,2:98.1,3:99.3,4:101.2,5:103.3,6:106.6},
};

// ====== 設定推測：ベイズ推定 ======
// 機種別重み付け：設定差の大きい指標ほど大きい値
const MODEL_WEIGHTS = {
  'ネオアイムジャグラー':      { bb:0.5, rb:3.0, budo:0.3, cherry:0.5, soloBB:0.8, soloRB:2.5, kadoBB:0.8, kadoRB:2.0 },
  'ウルトラミラクルジャグラー':  { bb:2.5, rb:0.8, budo:0.3, cherry:1.5, soloBB:2.0, soloRB:1.5, kadoBB:1.5, kadoRB:1.0 },
  'ミスタージャグラー':         { bb:0.5, rb:2.0, budo:2.5, cherry:1.0, soloBB:1.0, soloRB:2.0, kadoBB:0.8, kadoRB:1.5 },
  'ジャグラーガールズSS':       { bb:1.0, rb:1.5, budo:0.5, cherry:1.5, soloBB:1.2, soloRB:2.0, kadoBB:1.0, kadoRB:2.0 },
  'ゴーゴージャグラー3':        { bb:0.8, rb:2.0, budo:1.5, cherry:2.0, soloBB:1.0, soloRB:2.0, kadoBB:1.2, kadoRB:2.0 },
  'ハッピージャグラーVIII':     { bb:0.5, rb:2.0, budo:1.5, cherry:0.3, soloBB:1.0, soloRB:2.0, kadoBB:0.8, kadoRB:2.5 },
  'マイジャグラーV':            { bb:0.5, rb:1.5, budo:1.5, cherry:1.0, soloBB:0.8, soloRB:3.0, kadoBB:0.8, kadoRB:2.0 },
  'ファンキージャグラー2':      { bb:1.5, rb:2.5, budo:1.5, cherry:1.0, soloBB:0.5, soloRB:2.5, kadoBB:0.5, kadoRB:2.0 },
};

// 小台数機種フラグ（データから動的に計算）
// isSmallCountModel(model, rows) で判定
const SMALL_COUNT_THRESHOLD = 6; // 設置台数がこれ未満なら小台数機種とみなす

function getModelTaiCount(model, rows) {
  // 店舗内の当該機種の台数（ユニーク台番号数）
  const store = currentStore !== 'all' ? currentStore : null;
  const targetRows = store
    ? rows.filter(r => r.store === store && r.model === model)
    : rows.filter(r => r.model === model);
  return new Set(targetRows.map(r => r.tai)).size;
}

function isSmallCountModel(model, rows) {
  const count = getModelTaiCount(model, rows);
  return count > 0 && count < SMALL_COUNT_THRESHOLD;
}

// 機種のデータ信頼度（カバー率）を計算
// = 実際のデータ行数 ÷ 理論上の最大データ行数（設置台数 × 営業日数）
function calcModelDataCoverage(model, rows) {
  const store = currentStore !== 'all' ? currentStore : null;
  const targetRows = store
    ? rows.filter(r => r.store === store && r.model === model)
    : rows.filter(r => r.model === model);

  if(!targetRows.length) return { coverage: 0, taiCount: 0, dayCount: 0, actual: 0, label: 'データなし' };

  // 設置台数（ユニーク台番号数）
  const taiCount = new Set(targetRows.map(r => r.tai)).size;
  // 営業日数（ユニーク日付数）
  const dayCount = new Set(targetRows.map(r => r.dateStr)).size;
  // 理論最大
  const maxPossible = taiCount * dayCount;
  // 実際のデータ行数
  const actual = targetRows.length;
  // カバー率（0〜1）
  const coverage = maxPossible > 0 ? actual / maxPossible : 0;

  const label = coverage >= 0.85 ? '高'
    : coverage >= 0.60 ? '中'
    : coverage >= 0.35 ? '低'
    : '不足';

  const stars = coverage >= 0.85 ? '★★★'
    : coverage >= 0.60 ? '★★☆'
    : coverage >= 0.35 ? '★☆☆'
    : '☆☆☆';

  return { coverage: round1(coverage * 100), taiCount, dayCount, actual, maxPossible, label, stars };
}

// 後方互換：静的セットも残す（直接参照している箇所のフォールバック用）
const SMALL_COUNT_MODELS = new Set([
  'ミスタージャグラー',
  'ウルトラミラクルジャグラー',
  'ジャグラーガールズSS',
]);

const MODEL_SCORE_PROFILE = {
  'ネオアイムジャグラー':       { uiNote:'RB重視で判断（ブドウ設定差小）',          rbReliance:1.0, synReliance:0.6, budoReliance:0.3 },
  'ウルトラミラクルジャグラー': { uiNote:'BB・合算重視で判断（RB設定差中・BB重要）', rbReliance:0.5, synReliance:0.7, budoReliance:0.4 },
  'ミスタージャグラー':         { uiNote:'RBとブドウ両方で判断',                    rbReliance:0.9, synReliance:0.6, budoReliance:1.0 },
  'ジャグラーガールズSS':       { uiNote:'RB・合算バランスで判断',                  rbReliance:0.8, synReliance:0.8, budoReliance:0.4 },
  'ゴーゴージャグラー3':        { uiNote:'RBより合算重視で判断',                    rbReliance:0.6, synReliance:1.0, budoReliance:0.7 },
  'ハッピージャグラーVIII':     { uiNote:'RBとブドウ補助で判断',                    rbReliance:0.9, synReliance:0.6, budoReliance:0.7 },
  'マイジャグラーV':            { uiNote:'RB重視で判断',                            rbReliance:1.0, synReliance:0.8, budoReliance:0.8 },
  'ファンキージャグラー2':      { uiNote:'RB重視・BB偏り注意',                      rbReliance:1.0, synReliance:0.7, budoReliance:0.7 },
};

// ポアソン対数尤度（グローバル関数）
function logLikelihoodPoisson(observed, expected) {
  if(observed === null || observed === undefined || isNaN(observed) || expected <= 0) return 0;
  return observed * Math.log(expected) - expected;
}

function bayesEstimate(model, g, big, reg, ownG, budo, cherry, nonCherry, soloBig, soloReg, kadoBig, kadoReg) {
  const ms = MODEL_SETTINGS[model];
  const my = MODEL_YAKUS[model] || MODEL_YAKUS['マイジャグラーV'];
  const mw = MODEL_WEIGHTS[model] || MODEL_WEIGHTS['マイジャグラーV'];
  if(!ms || !g || g < 100) return null;

  // ownG: 自分が実際に打ったG数（ブドウ・チェリー等のカウント区間）
  // g:    合算G数（startG + ownG）= BIG/REG計算に使う
  const og = ownG > 0 ? ownG : g; // ownGが0なら朝イチ想定でgをそのまま使う

  const settings = [1,2,3,4,5,6];
  let probs = settings.map(()=> 1/6); // 事前確率：均等

  // ポアソン尤度を使った対数尤度計算
  settings.forEach((s, i) => {
    let logL = 0;

    // BIG・REG：合算G数で計算（ホールデータ引き継ぎ込み）
    if(big > 0) {
      const expBig = g / ms.bb[s];
      logL += mw.bb * logLikelihoodPoisson(big, expBig);
    }
    if(reg > 0) {
      const expReg = g / ms.rb[s];
      logL += mw.rb * logLikelihoodPoisson(reg, expReg);
    }

    // ブドウ・チェリー・小役系：自分が打った区間(og)で計算
    if(budo > 0) {
      const expBudo = og / my.budo[s];
      logL += mw.budo * logLikelihoodPoisson(budo, expBudo);
    }
    if(cherry > 0 && my.cherry[s] < 9000) {
      const expCherry = og / my.cherry[s];
      logL += mw.cherry * logLikelihoodPoisson(cherry, expCherry);
    }
    // 非重複チェリー（マイジャグラーV専用）
    if(nonCherry > 0 && my.nonCherry && my.nonCherry[s]) {
      const expNonCherry = og / my.nonCherry[s];
      logL += 2.0 * logLikelihoodPoisson(nonCherry, expNonCherry);
    }
    if(soloBig > 0 && my.soloBB[s] < 9000) {
      const expSoloBig = og / my.soloBB[s];
      logL += mw.soloBB * logLikelihoodPoisson(soloBig, expSoloBig);
    }
    if(soloReg > 0) {
      const expSoloReg = og / my.soloRB[s];
      logL += mw.soloRB * logLikelihoodPoisson(soloReg, expSoloReg);
    }
    if(kadoBig > 0 && my.kadoBB[s] < 9000) {
      const expKadoBig = og / my.kadoBB[s];
      logL += mw.kadoBB * logLikelihoodPoisson(kadoBig, expKadoBig);
    }
    if(kadoReg > 0) {
      const expKadoReg = og / my.kadoRB[s];
      logL += mw.kadoRB * logLikelihoodPoisson(kadoReg, expKadoReg);
    }

    probs[i] = Math.log(probs[i]) + logL;
  });

  // log-sum-exp で正規化
  const maxLog = Math.max(...probs);
  probs = probs.map(p => Math.exp(p - maxLog));
  const total = probs.reduce((a,b)=>a+b, 0);
  probs = probs.map(p => p/total);

  // 期待設定
  const expSet = settings.reduce((acc, s, i) => acc + s * probs[i], 0);
  // 期待機械割
  const ritu = MODEL_RITU[model] || MODEL_RITU['マイジャグラーV'];
  const expRitu = settings.reduce((acc, s, i) => acc + ritu[s] * probs[i], 0);

  // 各指標の「設定方向への寄与」を計算（高設定寄りなら+、低設定寄りなら−）
  const contributions = {};
  const contribLabels = {
    bb:'BIG確率', rb:'REG確率', budo:'ブドウ確率', cherry:'チェリー確率',
    nonCherry:'非重複チェリー', soloBB:'単独BIG', soloRB:'単独REG',
    kadoBB:'チェリー重複BIG', kadoRB:'チェリー重複REG'
  };

  // 各指標について「高設定(設定4-6)の対数尤度合計 vs 低設定(設定1-3)の対数尤度合計」の差で寄与を表現
  function calcContrib(key, observed, expectedFn, weight) {
    if(!observed || observed <= 0) return;
    let hiLogL = 0, loLogL = 0;
    [4,5,6].forEach(s => { hiLogL += logLikelihoodPoisson(observed, expectedFn(s)); });
    [1,2,3].forEach(s => { loLogL += logLikelihoodPoisson(observed, expectedFn(s)); });
    const diff = (hiLogL - loLogL) * weight / 3;
    if(Math.abs(diff) > 0.01) contributions[key] = { label: contribLabels[key], score: diff };
  }

  calcContrib('bb',  big,       s => g  / ms.bb[s],      mw.bb);
  calcContrib('rb',  reg,       s => g  / ms.rb[s],      mw.rb);
  calcContrib('budo', budo,     s => og / my.budo[s],    mw.budo);
  if(my.cherry) calcContrib('cherry', cherry, s => my.cherry[s] < 9000 ? og / my.cherry[s] : 0, mw.cherry);
  if(my.nonCherry) calcContrib('nonCherry', nonCherry, s => og / my.nonCherry[s], 2.0);
  if(my.soloBB)  calcContrib('soloBB', soloBig,  s => my.soloBB[s] < 9000 ? og / my.soloBB[s] : 0, mw.soloBB);
  if(my.soloRB)  calcContrib('soloRB', soloReg,  s => og / my.soloRB[s],   mw.soloRB);
  if(my.kadoBB)  calcContrib('kadoBB', kadoBig,  s => my.kadoBB[s] < 9000 ? og / my.kadoBB[s] : 0, mw.kadoBB);
  if(my.kadoRB)  calcContrib('kadoRB', kadoReg,  s => og / my.kadoRB[s],   mw.kadoRB);

  return { probs, expSet, expRitu, contributions };
}

// ====== 信頼度スコア ======
function stCalcScore(model, g, big, reg, budo, soloBig, soloReg, kadoBig, kadoReg) {
  let score = 0;
  // G数（最大50点）：8000Gで満点
  score += Math.min(g / 160, 50);
  // BIG+REG合計回数（最大20点）：60回で満点
  if(big > 0 && reg > 0) score += Math.min((big+reg) / 3, 20);
  // ブドウ（最大15点）：機種別重みで調整
  if(budo > 0) {
    const mw = MODEL_WEIGHTS[model] || MODEL_WEIGHTS['マイジャグラーV'];
    const budoWeight = mw.budo || 1.0; // 0.3〜2.5の範囲
    const budoMax = 15 * (budoWeight / 1.5); // 重み1.5を基準に最大点調整
    score += Math.min(budo / 67 * budoWeight, budoMax);
  }
  // 単独REG・チェリー重複REG（各5点）
  if(soloReg > 0) score += 5;
  if(kadoReg > 0) score += 5;
  // 単独BIG・チェリー重複BIG（各2.5点）
  if(soloBig > 0) score += 2.5;
  if(kadoBig > 0) score += 2.5;
  return Math.min(Math.round(score), 100);
}

// ====== 設定推測UI ======
let stRadarChart = null;

// カウンター状態（インメモリ）
const ST = {
  g:0, big:0, reg:0, budo:0, cherry:0,
  soloBig:0, kadoBig:0, unknBig:0,
  soloReg:0, kadoReg:0, unknReg:0,
  nonCherry:0,
};

function stCurrentTotals() {
  const startG   = parseInt(document.getElementById('stStartG')?.value)||0;
  const startBIG = parseInt(document.getElementById('stStartBIG')?.value)||0;
  const startREG = parseInt(document.getElementById('stStartREG')?.value)||0;
  return { totalG: startG + ST.g, totalBIG: startBIG + ST.big, totalREG: startREG + ST.reg };
}

function formatRateDenominator(rate) {
  return (rate && isFinite(rate)) ? `1/${Math.round(rate)}` : '—';
}

function summarizeWarningFlags(flags) {
  if(!flags || !flags.length) return '警戒メモなし';
  const strong = flags.filter(f => f.level === 'strong');
  const weak = flags.filter(f => f.level === 'weak');
  const topText = flags.slice(0,2).map(f => f.text.split('→')[0].trim()).join(' / ');
  return `strong:${strong.length} weak:${weak.length}（${topText}）`;
}

function getModelContextNotes(model, ctx) {
  const notes = [];
  const profile = MODEL_SCORE_PROFILE[model] || null;
  if(profile && profile.uiNote) notes.push(profile.uiNote);
  if(ctx?.modelProfileNote) notes.push(ctx.modelProfileNote);
  if(!notes.length) notes.push('現状は共通指標で照合（機種別プロファイル拡張に対応可能）');
  if(ctx?.isSpecial) notes.push('特定日文脈で抽出した候補');
  return [...new Set(notes)];
}

function summarizeFieldCheckPoints(points) {
  if(!points || !points.length) return '現地確認ポイントなし';
  return points.slice(0,2).join(' / ');
}

function getTodayRbRate() {
  const { totalG, totalREG } = stCurrentTotals();
  return totalREG > 0 ? totalG / totalREG : null;
}

function getTodaySynRate() {
  const { totalG, totalBIG, totalREG } = stCurrentTotals();
  const totalBonus = totalBIG + totalREG;
  return totalBonus > 0 ? totalG / totalBonus : null;
}

function getTodayBudoRate() {
  return (ST.g > 0 && ST.budo > 0) ? (ST.g / ST.budo) : null;
}

function getTodayJudgementPhase(totalG) {
  if(totalG <= 300) return 'early';
  if(totalG <= 1000) return 'mid';
  return 'late';
}

function getFitThresholds(phase) {
  const table = {
    early: { rbMatch:1.35, rbWarn:1.70, synMatch:1.25, synWarn:1.55, budoMatch:1.05, budoWarn:1.12 },
    mid:   { rbMatch:1.22, rbWarn:1.45, synMatch:1.15, synWarn:1.35, budoMatch:1.04, budoWarn:1.09 },
    late:  { rbMatch:1.12, rbWarn:1.28, synMatch:1.09, synWarn:1.22, budoMatch:1.03, budoWarn:1.07 },
  };
  return table[phase] || table.mid;
}

function ratioToBandLabel(ratio, matchTh, warnTh) {
  if(ratio === null || !isFinite(ratio)) return 'やや乖離';
  if(ratio <= matchTh) return '一致中';
  if(ratio <= warnTh) return 'やや乖離';
  return '警戒';
}

function labelColor(label) {
  if(label === '一致中') return 'var(--plus)';
  if(label === 'やや乖離') return 'var(--accent)';
  return 'var(--minus)';
}

function buildExpectedSettingBand(model, rbLevel, synLevel) {
  const lv = [rbLevel, synLevel].filter(v => v !== null && v !== undefined);
  if(!lv.length) return '設定3-4相当（参考）';
  const minLv = Math.max(1, Math.min(...lv));
  const maxLv = Math.min(6, Math.max(...lv));
  if(maxLv >= 5 && minLv >= 4) return '設定4-6相当';
  if(maxLv >= 4) return '設定3-5相当';
  return '設定2-4相当（参考）';
}

function getHighSettingBand(model) {
  const ms = MODEL_SETTINGS[model];
  const my = MODEL_YAKUS[model] || MODEL_YAKUS['マイジャグラーV'];
  if(!ms) return null;
  return {
    rb: { min: Math.min(ms.rb[4], ms.rb[5], ms.rb[6]), max: Math.max(ms.rb[4], ms.rb[5], ms.rb[6]) },
    syn:{ min: Math.min(ms.syn[4], ms.syn[5], ms.syn[6]), max: Math.max(ms.syn[4], ms.syn[5], ms.syn[6]) },
    budo: my?.budo ? { min: Math.min(my.budo[4], my.budo[5], my.budo[6]), max: Math.max(my.budo[4], my.budo[5], my.budo[6]) } : null
  };
}

function judgeCurrentFitToHighBand(model, totalG, todayRbRate, todaySynRate, todayBudoRate) {
  const band = getHighSettingBand(model);
  const phase = getTodayJudgementPhase(totalG);
  const th = getFitThresholds(phase);
  if(!band) {
    return {
      phase, totalG, label: 'やや乖離', color: 'var(--accent)',
      rbLabel: 'やや乖離', synLabel: 'やや乖離', budoLabel: 'やや乖離',
      rbRatio: null, synRatio: null, budoRatio: null,
      note: '機種設定値が未定義のため参考判定'
    };
  }

  // 分母型指標なので「帯の上限(設定4)」を基準に比較し、帯レンジ情報も表示に残す
  const rbRef = band.rb.max;
  const synRef = band.syn.max;
  const budoRef = band.budo ? band.budo.max : null;
  const rbRatio = todayRbRate ? todayRbRate / rbRef : null;
  const synRatio = todaySynRate ? todaySynRate / synRef : null;
  const budoRatio = (todayBudoRate && budoRef) ? (todayBudoRate / budoRef) : null;

  const rbLabel = ratioToBandLabel(rbRatio, th.rbMatch, th.rbWarn);
  const synLabel = ratioToBandLabel(synRatio, th.synMatch, th.synWarn);
  const budoLabel = budoRatio === null ? 'やや乖離' : ratioToBandLabel(budoRatio, th.budoMatch, th.budoWarn);

  const scoreMap = { '一致中':2, 'やや乖離':1, '警戒':0 };
  const profile = MODEL_SCORE_PROFILE[model] || {};
  const rbW = profile.rbReliance || 1.0;
  const synW = profile.synReliance || 1.0;
  const budoW = profile.budoReliance || 0.5;
  const totalW = rbW + synW + (budoRatio!==null ? budoW : 0);
  const weighted = ((scoreMap[rbLabel] * rbW) + (scoreMap[synLabel] * synW) + (budoRatio!==null ? scoreMap[budoLabel] * budoW : 0)) / (totalW || 1);

  const label = weighted >= 1.7 ? '一致中' : weighted >= 1.0 ? 'やや乖離' : '警戒';
  const phaseText = phase === 'early' ? '序盤(0〜300G)' : phase === 'mid' ? '中盤(301〜1000G)' : '後半(1001G〜)';
  const note = phase === 'early'
    ? '序盤帯のためブレを織り込み、判定を甘めにしています'
    : phase === 'late'
      ? '後半帯のため警戒判定をやや厳しめにしています'
      : '中盤帯の基準で判定しています';

  return {
    phase, phaseText, totalG, label, color: labelColor(label),
    rbLabel, synLabel, budoLabel, rbRatio, synRatio, budoRatio,
    rbBandMin: band.rb.min, rbBandMax: band.rb.max,
    synBandMin: band.syn.min, synBandMax: band.syn.max,
    budoBandMin: band.budo?.min || null, budoBandMax: band.budo?.max || null,
    note
  };
}

// backward compatibility
function judgeFitToHighSettingBand(model, todayRbRate, todaySynRate, totalG, todayBudoRate) {
  return judgeCurrentFitToHighBand(model, totalG, todayRbRate, todaySynRate, todayBudoRate);
}

function renderCurrentTargetContextComparison() {
  const el = document.getElementById('stPastContextCompare');
  if(!el) return;
  const ctx = G.currentTargetContext;
  if(!ctx) {
    el.innerHTML = '<div class="empty-msg">第3段階で台を選ぶと、ここに照合結果が表示されます</div>';
    return;
  }

  const { totalG } = stCurrentTotals();
  const todayRbRate = getTodayRbRate();
  const todaySynRate = getTodaySynRate();
  const todayBudoRate = getTodayBudoRate();
  const fit = judgeCurrentFitToHighBand(ctx.model, totalG, todayRbRate, todaySynRate, todayBudoRate);
  const modelMismatch = ctx.model && document.getElementById('stModel')?.value !== ctx.model;
  const notes = getModelContextNotes(ctx.model, ctx);

  el.innerHTML = `
    <div style="font-size:11px;color:var(--muted);margin-bottom:6px">A. 朝イチ仮説</div>
    <div style="background:var(--bg3);border-radius:8px;padding:10px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap">
        <div style="font-size:11px;color:var(--muted)">${ctx.store || '店舗不明'}${ctx.floor ? ` / ${ctx.floor}` : ''} / ${ctx.model || '機種不明'} / ${ctx.tai || '—'}番台</div>
        <div style="font-size:11px;color:var(--border)">基準日: ${ctx.targetDate || '—'}</div>
      </div>
      <div style="font-size:11px;color:var(--muted);margin-top:4px">rank: ${ctx.rank || '—'} / 配分${ctx.configScore}pt・数値${ctx.valueScore}pt・合計${ctx.totalScore}pt</div>
      ${modelMismatch ? '<div style="font-size:11px;color:var(--accent);margin-top:4px">※ 選択台の機種と現在の設定推測機種が異なります</div>' : ''}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
        <div>
          <div style="font-size:10px;color:var(--muted)">過去RB確率</div>
          <div style="font-size:13px;font-weight:700;color:var(--accent)">${formatRateDenominator(ctx.historicalRbRate)}</div>
        </div>
        <div>
          <div style="font-size:10px;color:var(--muted)">過去合算確率</div>
          <div style="font-size:13px;font-weight:700;color:var(--accent)">${formatRateDenominator(ctx.historicalSynRate)}</div>
        </div>
      </div>
      <div style="font-size:10px;color:var(--muted);margin-top:6px">参照: ${ctx.historicalSource || '—'} / 平均稼働 ${ctx.historicalAvgG || '—'}G / 期待帯 ${ctx.expectedSettingBand || '—'}</div>
      <div style="font-size:10px;color:var(--muted);margin-top:4px">warning: ${summarizeWarningFlags(ctx.warningFlags)}</div>
      <div style="font-size:10px;color:var(--muted);margin-top:4px">現地確認: ${summarizeFieldCheckPoints(ctx.fieldCheckPoints)}</div>
      <div style="font-size:10px;color:var(--muted);margin-top:4px">機種注記: ${notes.join(' / ')}</div>
    </div>

    <div style="font-size:11px;color:var(--muted);margin:8px 0 6px">B. 今日の高設定適合度</div>
    <div style="background:var(--bg3);border-radius:8px;padding:10px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap">
        <div style="font-size:11px;color:var(--muted)">判定帯: ${fit.phaseText || '中盤(301〜1000G)'} / ${totalG.toLocaleString()}G</div>
        <div style="font-size:15px;font-weight:900;color:${fit.color}">${fit.label}</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:8px">
        <div>
          <div style="font-size:10px;color:var(--muted)">今日RB</div>
          <div style="font-size:14px;font-weight:700">${formatRateDenominator(todayRbRate)}</div>
          <div style="font-size:10px;color:${labelColor(fit.rbLabel)}">高設定域 1/${Math.round(fit.rbBandMin || 0)}〜1/${Math.round(fit.rbBandMax || 0)} 比較: ${fit.rbLabel}</div>
        </div>
        <div>
          <div style="font-size:10px;color:var(--muted)">今日合算</div>
          <div style="font-size:14px;font-weight:700">${formatRateDenominator(todaySynRate)}</div>
          <div style="font-size:10px;color:${labelColor(fit.synLabel)}">高設定域 1/${Math.round(fit.synBandMin || 0)}〜1/${Math.round(fit.synBandMax || 0)} 比較: ${fit.synLabel}</div>
        </div>
        <div>
          <div style="font-size:10px;color:var(--muted)">今日ブドウ</div>
          <div style="font-size:14px;font-weight:700">${formatRateDenominator(todayBudoRate)}</div>
          <div style="font-size:10px;color:${labelColor(fit.budoLabel)}">${fit.budoBandMin ? `高設定域 1/${Math.round(fit.budoBandMin)}〜1/${Math.round(fit.budoBandMax)} 補助比較: ${fit.budoLabel}` : `補助比較: ${fit.budoLabel}`}</div>
        </div>
      </div>
      <div style="font-size:10px;color:var(--muted);margin-top:8px">注意補足: ${fit.note}</div>
    </div>

    <div style="margin-top:12px">
      <div style="font-size:11px;color:var(--muted);margin-bottom:6px">C. 撤退メモ（着席前に決める）</div>
      <div style="background:var(--bg3);border-radius:8px;padding:10px">
        ${renderWithdrawalMemo(ctx)}
      </div>
    </div>
  `;
}

function renderWithdrawalMemo(ctx) {
  const key = ctx ? `withdrawal_${ctx.store}_${ctx.tai}` : null;
  const saved = key ? (localStorage.getItem(key) || '') : '';
  const model = ctx?.model || '';
  const ms = MODEL_SETTINGS[model];

  // RBペースの目安を自動計算（設定4〜6の平均）
  let rbHint = '';
  if(ms) {
    const avg456rb = Math.round((ms.rb[4] + ms.rb[5] + ms.rb[6]) / 3);
    const avg456syn = Math.round((ms.syn[4] + ms.syn[5] + ms.syn[6]) / 3);
    rbHint = `設定4-6平均：RB 1/${avg456rb}・合算 1/${avg456syn}`;
  }

  return `
    <div style="font-size:10px;color:var(--accent);margin-bottom:6px">${rbHint}</div>
    <textarea id="withdrawalMemoArea"
      placeholder="例: 300GでRB1/350以下なら撤退・合算1/180以上で続行
朝イチ100GでRB0なら即撤退"
      onchange="saveWithdrawalMemo('${key}')"
      style="width:100%;box-sizing:border-box;background:var(--bg4);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px;font-size:12px;min-height:72px;resize:vertical;font-family:inherit"
    >${saved}</textarea>
    <div style="font-size:10px;color:var(--muted);margin-top:4px">※ 台ごとに保存されます</div>
  `;
}

function saveWithdrawalMemo(key) {
  if(!key) return;
  const val = document.getElementById('withdrawalMemoArea')?.value || '';
  localStorage.setItem(key, val);
}

function stSave() {
  localStorage.setItem('st_model', document.getElementById('stModel').value);
  localStorage.setItem('st_startG', document.getElementById('stStartG').value||'0');
  localStorage.setItem('st_startBIG', document.getElementById('stStartBIG').value||'0');
  localStorage.setItem('st_startREG', document.getElementById('stStartREG').value||'0');
}

function stUpdateDisplay() {
  const startG   = parseInt(document.getElementById('stStartG').value)||0;
  const startBIG = parseInt(document.getElementById('stStartBIG').value)||0;
  const startREG = parseInt(document.getElementById('stStartREG').value)||0;
  const totalG   = startG + ST.g;
  const totalBIG = startBIG + ST.big;
  const totalREG = startREG + ST.reg;

  document.getElementById('stDispG').textContent   = totalG.toLocaleString();
  document.getElementById('stDispBIG').textContent = totalBIG;
  document.getElementById('stDispREG').textContent = totalREG;
  document.getElementById('stDispStartG').textContent   = startG;
  document.getElementById('stDispStartBIG').textContent = startBIG;
  document.getElementById('stDispStartREG').textContent = startREG;
  const directGInput = document.getElementById('stDirectTotalG');
  if(directGInput && document.activeElement !== directGInput) {
    directGInput.value = totalG;
  }
  document.getElementById('stDispBudo').textContent   = ST.budo;
  // 🍒表示：マイジャグはnonCherryをcherry欄に表示
  const model = document.getElementById('stModel').value;
  const isMai = (model === 'マイジャグラーV');
  const cherryCount = isMai ? ST.nonCherry : ST.cherry;
  document.getElementById('stDispCherry').textContent = cherryCount;
  document.getElementById('stDispNonCherry').textContent = ST.nonCherry;
  document.getElementById('stDispSoloBIG').textContent  = ST.soloBig;
  document.getElementById('stDispKadoBIG').textContent  = ST.kadoBig;
  document.getElementById('stDispUnknBIG').textContent  = ST.unknBig;
  document.getElementById('stDispSoloREG').textContent  = ST.soloReg;
  document.getElementById('stDispKadoREG').textContent  = ST.kadoReg;
  document.getElementById('stDispUnknREG').textContent  = ST.unknReg;
  // 非重複チェリー専用行：🍒ボタンで代替するため非表示
  document.getElementById('rowNonCherry').style.display = 'none';

  // 小役確率をリアルタイム表示
  const g = totalG;
  if(g > 0) {
    document.getElementById('stDispBudoRate').textContent   = ST.budo   > 0 ? `1/${(ST.g/ST.budo).toFixed(1)}`   : '—';
    document.getElementById('stDispCherryRate').textContent = cherryCount > 0 ? `1/${(ST.g/cherryCount).toFixed(1)}` : '—';
  } else {
    document.getElementById('stDispBudoRate').textContent = '—';
    document.getElementById('stDispCherryRate').textContent = '—';
  }
  renderCurrentTargetContextComparison();
  // 自動判別（100G区切りのみ。それ以外は手動ボタン「🔍 設定を判別する」を使用）
  if(g >= 100 && g % 100 === 0) stCalc();
}

// タップ操作
function stAddG(n)       { ST.g = Math.max(0, ST.g+n); stUpdateDisplay(); }
function stAddBIG() { ST.big++; stUpdateDisplay(); }
function stSubBIG() { ST.big = Math.max(0, ST.big-1); stUpdateDisplay(); }
function stAddREG() { ST.reg++; stUpdateDisplay(); }
function stSubREG() { ST.reg = Math.max(0, ST.reg-1); stUpdateDisplay(); }
function stAddBudo()     { ST.budo++; stUpdateDisplay(); }
function stSubBudo()     { ST.budo = Math.max(0, ST.budo-1); stUpdateDisplay(); }
function stAddCherry()   {
  const model = document.getElementById('stModel').value;
  if(model === 'マイジャグラーV') { ST.nonCherry++; } else { ST.cherry++; }
  stUpdateDisplay();
}
function stSubCherry()   {
  const model = document.getElementById('stModel').value;
  if(model === 'マイジャグラーV') { ST.nonCherry = Math.max(0, ST.nonCherry-1); } else { ST.cherry = Math.max(0, ST.cherry-1); }
  stUpdateDisplay();
}
function stAddSoloBIG()  { ST.soloBig++;  stUpdateDisplay(); }
function stAddKadoBIG()  { ST.kadoBig++;  stUpdateDisplay(); }
function stAddUnknBIG()  { ST.unknBig++;  stUpdateDisplay(); }
function stAddSoloREG()  { ST.soloReg++;  stUpdateDisplay(); }
function stAddKadoREG()  { ST.kadoReg++;  stUpdateDisplay(); }
function stAddUnknREG()  { ST.unknReg++;  stUpdateDisplay(); }
function stSubSoloBIG()  { ST.soloBig = Math.max(0, ST.soloBig-1); stUpdateDisplay(); }
function stSubKadoBIG()  { ST.kadoBig = Math.max(0, ST.kadoBig-1); stUpdateDisplay(); }
function stSubUnknBIG()  { ST.unknBig = Math.max(0, ST.unknBig-1); stUpdateDisplay(); }
function stSubSoloREG()  { ST.soloReg = Math.max(0, ST.soloReg-1); stUpdateDisplay(); }
function stSubKadoREG()  { ST.kadoReg = Math.max(0, ST.kadoReg-1); stUpdateDisplay(); }
function stSubUnknREG()  { ST.unknReg = Math.max(0, ST.unknReg-1); stUpdateDisplay(); }
function stAddNonCherry()  { ST.nonCherry++; stUpdateDisplay(); }
function stSubNonCherry()  { ST.nonCherry = Math.max(0, ST.nonCherry-1); stUpdateDisplay(); }

function stSetTotalGFromInput() {
  const inputEl = document.getElementById('stDirectTotalG');
  if(!inputEl) return;
  const startG = parseInt(document.getElementById('stStartG').value) || 0;
  const raw = parseInt(inputEl.value);
  if(isNaN(raw)) {
    inputEl.value = (startG + ST.g);
    return;
  }
  const totalG = Math.max(0, raw);
  ST.g = Math.max(0, totalG - startG);
  stUpdateDisplay();
}

function stTapEditG() {
  const disp = document.getElementById('stDispG');
  const input = document.getElementById('stDirectTotalG');
  if(!disp || !input) return;
  // 現在の総G数をinputに設定して表示切り替え
  const { totalG } = stCurrentTotals();
  input.value = totalG || 0;
  disp.style.display = 'none';
  input.style.display = 'block';
  input.focus();
  input.select();
}

// stSetTotalGFromInputのonblur時に表示を戻す処理を上書き
const _origSetTotalG = typeof stSetTotalGFromInput === 'function' ? stSetTotalGFromInput : null;

function stSetTotalGFromInput() {
  const input = document.getElementById('stDirectTotalG');
  const disp = document.getElementById('stDispG');
  if(!input) return;
  const val = parseInt(input.value);
  if(!isNaN(val) && val >= 0) {
    const startG = parseInt(document.getElementById('stStartG')?.value) || 0;
    ST.g = Math.max(0, val - startG);
    stUpdateDisplay();
    if(document.getElementById('stResult')?.style.display !== 'none') stCalc();
  }
  // 表示を元に戻す
  if(input) input.style.display = 'none';
  if(disp) disp.style.display = 'block';
}

function stDirectAdjust(delta) {
  const el = document.getElementById('stDirectTotalG');
  if(!el) return;
  const cur = parseInt(el.value) || 0;
  el.value = Math.max(0, cur + delta);
  stSetTotalGFromInput();
}

function stAdjust(id, delta) {
  const el = document.getElementById(id);
  if(!el) return;
  const cur = parseInt(el.value) || 0;
  el.value = Math.max(0, cur + delta);
  stSave();
  if(document.getElementById('stResult').style.display !== 'none') stCalc();
}

function stOnModelChange() {
  stSave();
  renderModelHint(document.getElementById('stModel').value);
  renderCurrentTargetContextComparison();
}

function stReset() {
  Object.keys(ST).forEach(k => ST[k]=0);
  stUpdateDisplay();
  document.getElementById('stResult').style.display = 'none';
  if(stRadarChart){ stRadarChart.destroy(); stRadarChart=null; }
}

function stCalc() {
  const model    = document.getElementById('stModel').value;
  const startG   = parseInt(document.getElementById('stStartG').value)||0;
  const startBIG = parseInt(document.getElementById('stStartBIG').value)||0;
  const startREG = parseInt(document.getElementById('stStartREG').value)||0;
  const g   = startG + ST.g;
  const big = startBIG + ST.big;
  const reg = startREG + ST.reg;
  const budo    = ST.budo;
  const cherry  = model === 'マイジャグラーV' ? ST.nonCherry : ST.cherry;
  const soloBig = ST.soloBig;
  const soloReg = ST.soloReg;
  const kadoBig = ST.kadoBig;
  const kadoReg = ST.kadoReg;

  if(g < 100) return;

  const result = bayesEstimate(model, g, big, reg, ST.g, budo, cherry, ST.nonCherry, soloBig, soloReg, kadoBig, kadoReg);
  if(!result) return;

  document.getElementById('stResult').style.display = 'block';

  const ms = MODEL_SETTINGS[model];
  const my = MODEL_YAKUS[model] || MODEL_YAKUS['マイジャグラーV'];

  function frac(n, d) { return d>0 ? `1/${(n/d).toFixed(1)}` : '—'; }
  const realStats = [
    {label:'BIG確率', val: frac(g,big), sub: `設定1:1/${ms.bb[1]} / 設定6:1/${ms.bb[6]}`},
    {label:'REG確率', val: frac(g,reg), sub: `設定1:1/${ms.rb[1]} / 設定6:1/${ms.rb[6]}`},
    {label:'合算確率', val: frac(g,big+reg), sub: `設定1:1/${ms.syn[1]} / 設定6:1/${ms.syn[6]}`},
    {label:'ブドウ確率', val: budo>0?frac(ST.g,budo):'未カウント', sub: budo>0?`設定1:1/${my.budo[1]} / 設定6:1/${my.budo[6]}`:''},
  ];
  document.getElementById('stRealStats').innerHTML = realStats.map(s=>`
    <div style="background:var(--bg3);border-radius:8px;padding:10px">
      <div style="font-size:10px;color:var(--muted);margin-bottom:2px">${s.label}</div>
      <div style="font-size:16px;font-weight:700;color:var(--accent)">${s.val}</div>
      <div style="font-size:9px;color:var(--muted);margin-top:2px">${s.sub}</div>
    </div>`).join('');

  const colors = ['#888','#aaa','#bbb','#f0a500','#4caf50','#2196f3'];
  let barsHtml = '';
  result.probs.forEach((p, i) => {
    const pct = (p*100).toFixed(1);
    barsHtml += `
      <div style="margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px">
          <span style="color:${colors[i]};font-weight:700">設定${i+1}</span>
          <span style="color:var(--text)">${pct}%</span>
        </div>
        <div style="background:var(--bg3);border-radius:4px;height:10px;overflow:hidden">
          <div style="height:100%;width:${pct}%;background:${colors[i]};border-radius:4px;transition:width .4s"></div>
        </div>
      </div>`;
  });
  document.getElementById('stSettingBars').innerHTML = barsHtml;

  const prob456 = (result.probs[3]+result.probs[4]+result.probs[5])*100;
  const prob56  = (result.probs[4]+result.probs[5])*100;
  const prob6   = result.probs[5]*100;
  document.getElementById('stProb456').textContent = prob456.toFixed(1)+'%';
  document.getElementById('stProb56').textContent  = prob56.toFixed(1)+'%';
  document.getElementById('stProb6').textContent   = prob6.toFixed(1)+'%';
  document.getElementById('stLowProb').textContent  = (100-prob456).toFixed(1)+'%';
  document.getElementById('stHighProb').textContent = prob456.toFixed(1)+'%';

  document.getElementById('stExpSet').textContent = result.expSet.toFixed(2);
  const expRituColor = result.expRitu >= 100 ? 'var(--plus)' : 'var(--minus)';
  document.getElementById('stExpRitu').innerHTML = `<span style="color:${expRituColor}">${result.expRitu.toFixed(1)}%</span>`;

  renderStRadar(model, g, big, reg, budo);
  renderModelHint(model);
  renderViz();
  renderContrib(result.contributions);
  renderWithdraw(model, g, big, reg, result);

  const score = stCalcScore(model, g, big, reg, budo, soloBig, soloReg, kadoBig, kadoReg);
  const scoreColor = score >= 75 ? 'var(--plus)' : score >= 45 ? 'var(--accent)' : 'var(--minus)';
  const scoreEl = document.getElementById('stScoreCircle');
  scoreEl.textContent = score;
  scoreEl.style.borderColor = scoreColor;
  scoreEl.style.color = scoreColor;
  const msg = score >= 75 ? '信頼度高め：判別精度は比較的高いです' :
              score >= 45 ? '信頼度中程度：参考値としてご活用ください' :
              'まだデータが少ないです。G数・小役を増やすと精度が上がります';
  document.getElementById('stScoreMsg').textContent = msg;
}


function renderWithdraw(model, g, big, reg, result) {
  const el = document.getElementById('stWithdrawArea');
  if(!el) return;

  const ms = MODEL_SETTINGS[model];
  if(!ms || g < 100) { el.innerHTML = '<div class="empty-msg">G数が不足しています</div>'; return; }

  const prob456 = (result.probs[3] + result.probs[4] + result.probs[5]) * 100;
  const prob56  = (result.probs[4] + result.probs[5]) * 100;
  const expSet  = result.expSet;
  const phase   = g < 300 ? '序盤' : g < 1000 ? '中盤' : '後半';

  // 現在のRB確率
  const rbActual = reg > 0 ? g / reg : null;
  const rb4 = ms.rb[4];
  const rb3 = ms.rb[3];

  // 撤退判定ロジック
  let verdict = '';
  let verdictColor = '';
  let verdictBg = '';
  let reasons = [];
  let nextCheck = '';

  if(phase === '序盤') {
    // 序盤：高設定確率が低すぎる場合のみ撤退
    if(prob456 < 20) {
      verdict = '🔴 撤退推奨';
      verdictColor = '#e74c3c';
      verdictBg = '#2e1a1a';
      reasons.push(`設定4以上の確率が${prob456.toFixed(0)}%（20%未満）`);
      reasons.push('序盤でこの数値は低設定の可能性が高い');
    } else if(prob456 < 40) {
      verdict = '🟡 様子見';
      verdictColor = '#f0a500';
      verdictBg = '#2e2200';
      reasons.push(`設定4以上の確率が${prob456.toFixed(0)}%（やや低め）`);
      nextCheck = `次のチェックポイント: 500G時点でRBが1/${Math.round(rb4)}以上あるか確認`;
    } else {
      verdict = '🟢 続行';
      verdictColor = '#4caf50';
      verdictBg = '#1a2e1a';
      reasons.push(`設定4以上の確率が${prob456.toFixed(0)}%`);
      nextCheck = `次のチェックポイント: 500G時点でRBが1/${Math.round(rb4)}以上を維持できているか確認`;
    }
  } else if(phase === '中盤') {
    if(prob456 < 25) {
      verdict = '🔴 撤退推奨';
      verdictColor = '#e74c3c';
      verdictBg = '#2e1a1a';
      reasons.push(`設定4以上の確率が${prob456.toFixed(0)}%（25%未満）`);
      if(rbActual) reasons.push(`RB実測: 1/${rbActual.toFixed(0)}（設定4理論値: 1/${Math.round(rb4)}）`);
    } else if(prob456 < 50) {
      verdict = '🟡 様子見';
      verdictColor = '#f0a500';
      verdictBg = '#2e2200';
      reasons.push(`設定4以上の確率が${prob456.toFixed(0)}%`);
      if(rbActual) reasons.push(`RB実測: 1/${rbActual.toFixed(0)}（設定4理論値: 1/${Math.round(rb4)}）`);
      nextCheck = `次のチェックポイント: 1500G時点で設定4以上50%以上をキープできているか確認`;
    } else {
      verdict = '🟢 続行';
      verdictColor = '#4caf50';
      verdictBg = '#1a2e1a';
      reasons.push(`設定4以上の確率が${prob456.toFixed(0)}%`);
      if(prob56 >= 30) reasons.push(`設定5以上も${prob56.toFixed(0)}%と良好`);
      nextCheck = `次のチェックポイント: 2000G時点で設定4以上50%以上を維持できているか確認`;
    }
  } else {
    // 後半
    if(prob456 < 30) {
      verdict = '🔴 撤退推奨';
      verdictColor = '#e74c3c';
      verdictBg = '#2e1a1a';
      reasons.push(`${g}Gまで回して設定4以上${prob456.toFixed(0)}%`);
      reasons.push('後半でこの数値は低設定確定に近い');
    } else if(expSet < 4.0) {
      verdict = '🟡 様子見';
      verdictColor = '#f0a500';
      verdictBg = '#2e2200';
      reasons.push(`期待設定${expSet.toFixed(2)}（設定4未満）`);
      reasons.push('高設定の可能性は残るが確証なし');
    } else {
      verdict = '🟢 続行';
      verdictColor = '#4caf50';
      verdictBg = '#1a2e1a';
      reasons.push(`期待設定${expSet.toFixed(2)}・設定4以上${prob456.toFixed(0)}%`);
      if(prob56 >= 30) reasons.push(`設定5以上も${prob56.toFixed(0)}%と高い`);
    }
  }

  // RB目標ラインの計算
  const rbTargetG = g < 500 ? 500 : g < 1000 ? 1000 : 1500;
  const rbTarget4 = Math.round(rb4);
  const rbTarget3 = Math.round(rb3);

  el.innerHTML = `
    <div style="background:${verdictBg};border:1px solid ${verdictColor}44;border-radius:10px;padding:14px;margin-bottom:10px">
      <div style="font-size:18px;font-weight:900;color:${verdictColor};margin-bottom:8px">${verdict}</div>
      <div style="font-size:11px;color:var(--muted);margin-bottom:4px">現在: ${phase}（${g}G / REG ${reg}回）</div>
      ${reasons.map(r => `<div style="font-size:12px;color:var(--text);margin-top:4px">・${r}</div>`).join('')}
    </div>
    ${nextCheck ? `<div style="font-size:11px;color:var(--accent);padding:8px;background:var(--bg3);border-radius:6px;margin-bottom:8px">📍 ${nextCheck}</div>` : ''}
    <div style="background:var(--bg3);border-radius:8px;padding:10px">
      <div style="font-size:10px;color:var(--muted);margin-bottom:6px">📊 RB目標ライン（${model}）</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
        <div style="text-align:center;padding:6px;background:var(--bg4);border-radius:6px">
          <div style="font-size:9px;color:var(--muted)">設定3以上の目安</div>
          <div style="font-size:14px;font-weight:700;color:var(--accent)">1/${rbTarget3}以下</div>
        </div>
        <div style="text-align:center;padding:6px;background:var(--bg4);border-radius:6px">
          <div style="font-size:9px;color:var(--muted)">設定4以上の目安</div>
          <div style="font-size:14px;font-weight:700;color:var(--plus)">1/${rbTarget4}以下</div>
        </div>
      </div>
    </div>
  `;
}

// 機種別の重要指標の固定表示順
// rbReliance/synReliance/budoRelianceに基づいてキーをソート
const CONTRIB_KEY_ORDER = {
  'ネオアイムジャグラー':       ['rb','bb','budo','soloRB','cherry','nonCherry','kadoRB','soloBB','kadoBB'],
  'ウルトラミラクルジャグラー': ['bb','rb','budo','soloRB','cherry','nonCherry','kadoBB','soloBB','kadoRB'],
  'ミスタージャグラー':         ['rb','budo','bb','soloRB','cherry','nonCherry','kadoRB','soloBB','kadoBB'],
  'ジャグラーガールズSS':       ['rb','bb','budo','soloRB','cherry','nonCherry','kadoRB','soloBB','kadoBB'],
  'ゴーゴージャグラー3':        ['bb','rb','budo','soloRB','cherry','nonCherry','kadoBB','soloBB','kadoRB'],
  'ハッピージャグラーVIII':     ['rb','budo','bb','soloRB','cherry','nonCherry','kadoRB','soloBB','kadoBB'],
  'マイジャグラーV':            ['rb','budo','bb','soloRB','cherry','nonCherry','kadoRB','soloBB','kadoBB'],
  'ファンキージャグラー2':      ['rb','bb','budo','soloRB','cherry','nonCherry','kadoRB','soloBB','kadoBB'],
};
const CONTRIB_KEY_ORDER_DEFAULT = ['rb','bb','budo','soloRB','cherry','nonCherry','kadoRB','soloBB','kadoBB'];

function renderContrib(contributions) {
  const el = document.getElementById('stContribArea');
  if(!el) return;

  const model = document.getElementById('stModel')?.value || '';
  const keyOrder = CONTRIB_KEY_ORDER[model] || CONTRIB_KEY_ORDER_DEFAULT;

  // 入力済み（スコアあり）の指標を機種別固定順で並べる
  const entryMap = {};
  Object.entries(contributions).forEach(([k, v]) => { entryMap[k] = v; });

  const ordered = keyOrder
    .filter(k => entryMap[k])
    .map(k => ({ key: k, ...entryMap[k] }));

  // 固定順に含まれないキーはスコア順で末尾に
  const extra = Object.entries(entryMap)
    .filter(([k]) => !keyOrder.includes(k))
    .map(([k, v]) => ({ key: k, ...v }))
    .sort((a, b) => Math.abs(b.score) - Math.abs(a.score));

  const entries = [...ordered, ...extra];

  if(!entries.length) {
    el.innerHTML = '<div style="color:var(--muted);font-size:12px">入力データが少なく根拠を表示できません</div>';
    return;
  }

  const maxAbs = Math.max(...entries.map(e => Math.abs(e.score)), 0.01);

  // 機種のprofileからuiNoteを取得
  const profile = MODEL_SCORE_PROFILE[model];
  const uiNote = profile?.uiNote || '';

  el.innerHTML = (uiNote ? `<div style="font-size:11px;color:var(--accent);margin-bottom:8px;padding:6px 8px;background:var(--bg3);border-radius:6px">📌 ${uiNote}</div>` : '')
  + entries.map((e, idx) => {
    const isHigh = e.score > 0;
    const pct = Math.min(Math.abs(e.score) / maxAbs * 100, 100);
    const color   = isHigh ? '#4caf50' : '#e74c3c';
    const bgColor = isHigh ? '#1a2e1a' : '#2e1a1a';
    const dir     = isHigh ? '▲ 高設定寄り' : '▼ 低設定寄り';
    const strength = pct >= 80 ? '強' : pct >= 40 ? '中' : '弱';
    const isTop = idx < 2; // 上位2指標を強調
    const barLeft  = isHigh ? '50%' : `${50 - pct/2}%`;
    const barWidth = `${pct/2}%`;
    return `
    <div style="background:${bgColor};border-radius:8px;padding:10px;margin-bottom:6px;border:${isTop ? `1px solid ${color}44` : '1px solid transparent'}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
        <span style="font-size:13px;font-weight:700;color:var(--text)">${isTop ? '★ ' : ''}${e.label}</span>
        <span style="font-size:11px;color:${color};font-weight:700">${dir}（${strength}）</span>
      </div>
      <div style="position:relative;background:#222;border-radius:4px;height:10px;overflow:hidden">
        <div style="position:absolute;top:0;left:49.5%;width:1px;height:100%;background:#555"></div>
        <div style="position:absolute;top:0;left:${barLeft};width:${barWidth};height:100%;background:${color};border-radius:4px;transition:width .4s"></div>
      </div>
    </div>`;
  }).join('') + `
  <div style="font-size:10px;color:var(--muted);margin-top:8px;padding:6px;background:var(--bg3);border-radius:6px">
    ★ = この機種で特に重要な指標 / バーの長さは相対的な影響力
  </div>`;
}

function renderStRadar(model, g, big, reg, budo) {
  const ms = MODEL_SETTINGS[model];
  const my = MODEL_YAKUS[model] || MODEL_YAKUS['マイジャグラーV'];
  if(!ms) return;

  // 各指標を設定1〜6の範囲で0〜100に正規化
  // 分母が小さいほど高設定（BIG/REG/合算/ブドウ全て同じ方向）
  function normalize(actual, s1val, s6val) {
    if(actual === null || actual <= 0) return null;
    if(s1val === s6val) return 50;
    const pct = (s1val - actual) / (s1val - s6val) * 100;
    return Math.max(0, Math.min(100, pct));
  }

  const bbActual  = big > 0   ? g / big         : null;
  const rbActual  = reg > 0   ? g / reg         : null;
  const synActual = (big+reg) > 0 ? g/(big+reg) : null;
  // ブドウ：実測確率 = budo/g（例：67/3600=0.01861）、設定値も同スケールに変換して比較
  // 理論値も同じく「1/5.91」の分母（5.91）なので単位が合う
  // ブドウは「出現率 = budo/g」で比較。設定値は「1/X」の分母なので 1/my.budo[s] に変換して比較
  // normalize方向：ブドウは出現率が高い(分母小)ほど高設定なので s1val < s6val になるよう 1/分母 を渡す
  const budoActual = budo > 0 ? budo / g : null; // 実測出現率

  const data = [
    normalize(bbActual,   ms.bb[1],      ms.bb[6]),
    normalize(rbActual,   ms.rb[1],      ms.rb[6]),
    normalize(synActual,  ms.syn[1],     ms.syn[6]),
    normalize(budoActual, 1/my.budo[1], 1/my.budo[6]),
  ];

  const labels = ['BIG確率','REG確率','合算確率','ブドウ確率'];
  const actual = data.map(v => v !== null ? v : 0);

  if(stRadarChart){ stRadarChart.destroy(); stRadarChart=null; }
  const ctx = document.getElementById('stRadar').getContext('2d');
  stRadarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [
        { label:'実測値', data: actual, borderColor:'#4fc3f7', backgroundColor:'rgba(79,195,247,.25)', pointBackgroundColor:'#4fc3f7', borderWidth:2 },
        { label:'設定1基準', data:[0,0,0,0], borderColor:'#666', backgroundColor:'rgba(0,0,0,0)', borderDash:[4,4], borderWidth:1 },
        { label:'設定6基準', data:[100,100,100,100], borderColor:'#4caf50', backgroundColor:'rgba(76,175,80,.08)', borderDash:[4,4], borderWidth:1 },
      ]
    },
    options: {
      scales: { r: { min:0, max:100, ticks:{display:false}, grid:{color:'#333'}, pointLabels:{color:'#aaa',font:{size:11}} } },
      plugins: { legend:{labels:{color:'#aaa',font:{size:10}}} },
    }
  });
}
// ====== 機種別重要指標ヒント ======
const MODEL_HINTS = {
  'ネオアイムジャグラー': [
    {label:'REG確率', importance:'◎最重要', desc:'設定差が極端に大きい。設定1:1/439→設定6:1/127。REGが引けているほど高設定期待大。'},
    {label:'チェリー重複REG', importance:'◎最重要', desc:'設定1:1/1424→設定6:1/862。引けるほど高設定。設定5・6で同値（1/862）。'},
    {label:'単独REG', importance:'○重要', desc:'設定1:1/636→設定6:1/362。設定5・6で同値のため設定6断定には他指標が必要。'},
    {label:'ブドウ確率', importance:'△参考程度', desc:'設定1〜5はほぼ同値（1/6.02）。設定6のみ1/5.85に上昇。ブドウは設定6確認用。'},
  ],
  'ウルトラミラクルジャグラー': [
    {label:'BIG確率', importance:'◎最重要', desc:'この機種はBIG設定差が最大。設定1:1/267→設定6:1/216。BIGが引けているか重視。'},
    {label:'チェリー重複REG', importance:'◎最重要', desc:'設定1:1/1489→設定6:1/1040。設定2（1/1524）が設定1より悪い逆転仕様に注意。'},
    {label:'REG確率', importance:'△注意', desc:'設定6のREG（1/277）が設定5（1/297）より悪い特殊仕様。REG多い＝高設定とは限らない！'},
    {label:'ブドウ確率', importance:'△参考程度', desc:'設定差は非常に小さい（1/5.94→1/5.929）。ほぼ参考にならない。'},
  ],
  'ミスタージャグラー': [
    {label:'ブドウ確率', importance:'◎最重要', desc:'設定が上がるほどブドウが悪化する逆転仕様。設定1:1/6.22→設定6:1/6.02。必ず数える。'},
    {label:'単独REG', importance:'◎最重要', desc:'設定1:1/512→設定6:1/297。設定差が非常に大きい。'},
    {label:'REG確率', importance:'○重要', desc:'設定1:1/374→設定6:1/237。設定差大きい。'},
    {label:'ピエロBIG/REG', importance:'○重要', desc:'ピエロ重複は全設定共通（BIG:1/3640、REG:1/9362）。設定差なし・参考用。'},
  ],
  'ジャグラーガールズSS': [
    {label:'単独REG', importance:'◎最重要', desc:'設定1:1/520→設定6:1/358。設定差大きい。'},
    {label:'チェリー重複REG', importance:'◎最重要', desc:'設定1:1/1424→設定6:1/851。引けるほど高設定。'},
    {label:'BIG確率', importance:'△注意', desc:'設定1のBIG（1/273）がシリーズ内で最大。BIG多くても設定1の可能性あり。'},
  ],
  'ゴーゴージャグラー3': [
    {label:'ブドウ確率', importance:'◎最重要', desc:'設定1:1/6.25→設定6:1/5.92。設定差が大きく最重要指標。必ず数える。'},
    {label:'チェリー重複REG', importance:'◎最重要', desc:'設定1:1/1424→設定6:1/910。設定差大きい。'},
    {label:'REG確率', importance:'○重要', desc:'設定1:1/354→設定6:1/234。設定差あり。'},
    {label:'先告知なし', importance:'⚠️注意', desc:'先告知なし・第3ボタン停止後の後告知のみ。設定1のBIG・REG・合算が全機種中で最小。'},
  ],
  'ハッピージャグラーVIII': [
    {label:'チェリー重複REG', importance:'◎最重要', desc:'設定1:1/1057→設定6:1/642。設定差が大きく最重要指標。'},
    {label:'単独REG', importance:'◎最重要', desc:'設定1:1/636→設定6:1/425。設定差大きい。'},
    {label:'ブドウ確率', importance:'○重要', desc:'設定1:1/6.04→設定6:1/5.82。設定差中程度。小役優先制御。'},
    {label:'単独BIG', importance:'△注意', desc:'設定3（1/412）より設定4（1/414）の方が悪い逆転あり。BIG単独は過信禁物。'},
  ],
  'マイジャグラーV': [
    {label:'単独REG', importance:'◎最重要', desc:'設定1:1/655→設定6:1/327。設定差が全指標中で最大の最重要指標。'},
    {label:'チェリー重複REG', importance:'◎最重要', desc:'設定1:1/1092→設定6:1/762。引けるほど高設定。設定4以上で大きく上昇。'},
    {label:'ブドウ確率', importance:'○重要', desc:'設定1:1/5.91→設定6:1/5.67。設定差は中程度。積み重なると効く。'},
    {label:'REG確率', importance:'○重要', desc:'設定6のREG（1/229）が全機種中で最も低い特殊仕様。設定6はREGが少なくBIGが多い傾向。'},
  ],
  'ファンキージャグラー2': [
    {label:'REG確率', importance:'◎最重要', desc:'設定1:1/439→設定6:1/262。BIG偏向型だがREG設定差も大きい。'},
    {label:'単独REG', importance:'◎最重要', desc:'設定1:1/636→設定6:1/356。設定差が非常に大きい。'},
    {label:'チェリー重複REG', importance:'○重要', desc:'設定1:1/1424→設定6:1/992。設定差大きい。'},
    {label:'BIG確率', importance:'○重要', desc:'BIG偏向型。設定1:1/266→設定6:1/219。BIG設定差もある程度大きい。'},
  ],
};

// ====== 近似設定ビジュアライザー（テーブル特化） ======
let vizRadarChart = null;

function renderViz() {
  const model = document.getElementById('stModel').value;
  const ms = MODEL_SETTINGS[model];
  const my = MODEL_YAKUS[model] || MODEL_YAKUS['マイジャグラーV'];
  if(!ms) return;

  const startG   = parseInt(document.getElementById('stStartG').value)||0;
  const startBIG = parseInt(document.getElementById('stStartBIG').value)||0;
  const startREG = parseInt(document.getElementById('stStartREG').value)||0;
  const g   = startG + ST.g;
  const big = startBIG + ST.big;
  const reg = startREG + ST.reg;
  const budo    = ST.budo;
  const soloReg = ST.soloReg;
  const kadoReg = ST.kadoReg;
  if(g < 100) return;

  // 指標定義
  const METRICS = [
    { key:'bb',     label:'BIG確率',         actual: big>0    ? g/big         : null, theory: ms.bb,     smallIsHigh:true  },
    { key:'rb',     label:'REG確率',         actual: reg>0    ? g/reg         : null, theory: ms.rb,     smallIsHigh:true  },
    { key:'syn',    label:'合算確率',        actual: (big+reg)>0 ? g/(big+reg): null, theory: ms.syn,    smallIsHigh:true  },
    { key:'budo',   label:'ブドウ確率',      actual: budo>0   ? ST.g/budo      : null, theory: my.budo,   smallIsHigh:false },
    { key:'soloRb', label:'単独REG',         actual: soloReg>0? g/soloReg     : null, theory: my.soloRB, smallIsHigh:true  },
    // kadoRB キー名は機種によって kadoRB（ネオアイム）または cherryRB（他機種）に分かれるため両方を参照
    { key:'kadoRb', label:'チェリー重複REG', actual: kadoReg>0? g/kadoReg     : null, theory: my.kadoRB ?? my.cherryRB, smallIsHigh:true  },
  ].filter(m => m.actual !== null && m.theory != null && Object.values(m.theory).every(v=>v<9000));
  // ※ m.theory != null チェックがないと、理論値未定義の機種で Object.values(undefined) が
  //    TypeError を投げてテーブル更新が止まるバグがある（修正済み）

  if(!METRICS.length) return;

  renderVizTable(METRICS);
}

function getVizClosenessScore(actual, theoryVals) {
  const dists = [1,2,3,4,5,6].map(s => Math.abs(actual - theoryVals[s]));
  const minD = Math.min(...dists);
  const maxD = Math.max(...dists);
  const range = maxD - minD;
  return dists.map(d => range===0 ? 1 : 1 - (d - minD) / range);
}

function buildVizData(metrics) {
  const totalScores = [0,0,0,0,0,0];
  const rowScores = {};
  const nearestByMetric = {};

  metrics.forEach(m => {
    const scores = getVizClosenessScore(m.actual, m.theory);
    rowScores[m.key] = scores;
    const maxScore = Math.max(...scores);
    nearestByMetric[m.key] = scores.map((s,i) => ({s, i})).filter(x=>x.s===maxScore).map(x=>x.i+1);
    scores.forEach((s,i) => totalScores[i] += s);
  });

  return {
    totalScores,
    rowScores,
    nearestByMetric,
    topIdx: totalScores.indexOf(Math.max(...totalScores)),
  };
}

function renderVizSummary(metrics, vizData) {
  const SET_COLORS = ['#888','#999','#aab','#f0a500','#4caf50','#2196f3'];
  const { totalScores, topIdx, nearestByMetric } = vizData;
  const maxAvgScore = Math.max(...totalScores.map(s => s / metrics.length), 0.0001);

  return `
    <div style="margin-bottom:8px">
      <div style="font-size:10px;color:var(--muted);margin-bottom:6px">総合近似スコア（0-100）</div>
      <div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:4px">
        ${[1,2,3,4,5,6].map((s,i)=>{
          const avgScore = totalScores[i] / metrics.length;
          const pct = Math.round(avgScore * 100);
          const barW = Math.max(8, Math.round((avgScore / maxAvgScore) * 100));
          const isTop = i === topIdx;
          return `<div style="background:${isTop?SET_COLORS[i]+'25':'var(--bg3)'};border:${isTop?`1px solid ${SET_COLORS[i]}`:'1px solid var(--border)'};border-radius:7px;padding:6px 4px">
            <div style="font-size:9px;color:${SET_COLORS[i]};text-align:center;font-weight:700">設定${s}</div>
            <div style="font-size:15px;color:${isTop?SET_COLORS[i]:'var(--text)'};font-weight:${isTop?900:700};text-align:center;line-height:1.1">${pct}</div>
            <div style="height:3px;background:var(--bg4);border-radius:2px;margin-top:4px;overflow:hidden">
              <div style="height:100%;width:${barW}%;background:${SET_COLORS[i]}"></div>
            </div>
          </div>`;
        }).join('')}
      </div>
      <div style="margin-top:8px;padding:8px;background:${SET_COLORS[topIdx]}16;border:1px solid ${SET_COLORS[topIdx]}55;border-radius:8px;font-size:10px;color:var(--muted)">
        最近似: <span style="color:${SET_COLORS[topIdx]};font-weight:900">設定${topIdx+1}</span>
        ・一致指標: ${metrics.filter(m => nearestByMetric[m.key].includes(topIdx+1)).map(m=>m.label).join(' / ') || 'なし'}
      </div>
    </div>
  `;
}

function renderVizMatrix(metrics, vizData) {
  const SET_COLORS = ['#888','#999','#aab','#f0a500','#4caf50','#2196f3'];
  const { rowScores, nearestByMetric } = vizData;

  return `
    <div>
      <div style="font-size:10px;color:var(--muted);margin-bottom:6px">比較マトリクス（濃いほど近い）</div>
      <div style="display:grid;grid-template-columns:72px repeat(6,minmax(0,1fr));gap:4px;align-items:center">
        <div></div>
        ${[1,2,3,4,5,6].map((s,i)=>`<div style="text-align:center;font-size:10px;color:${SET_COLORS[i]};font-weight:700">設${s}</div>`).join('')}
        ${metrics.map(m=>{
          const scores = rowScores[m.key];
          return `
            <div style="font-size:10px;color:var(--muted);font-weight:700;line-height:1.2">${m.label.replace('確率','')}</div>
            ${[1,2,3,4,5,6].map((s,i)=>{
              const sc = scores[i];
              const isNearest = nearestByMetric[m.key].includes(s);
              const alpha = 0.12 + sc * 0.75;
              const bg = `rgba(46,160,67,${alpha.toFixed(3)})`;
              return `<div style="height:26px;border-radius:6px;background:${bg};border:${isNearest?`2px solid ${SET_COLORS[i]}`:'1px solid rgba(255,255,255,0.06)'};display:flex;align-items:center;justify-content:center">
                ${isNearest?`<span style="font-size:9px;color:${SET_COLORS[i]};font-weight:900">●</span>`:''}
              </div>`;
            }).join('')}
          `;
        }).join('')}
      </div>
    </div>
  `;
}

function renderVizDetails(metrics, vizData) {
  const { rowScores } = vizData;
  return `
    <details style="margin-top:10px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:8px">
      <summary style="cursor:pointer;font-size:11px;color:var(--muted);font-weight:700">詳細を見る（理論値 / 差分）</summary>
      <div style="margin-top:8px">
        ${metrics.map(m=>{
          const best = rowScores[m.key].indexOf(Math.max(...rowScores[m.key])) + 1;
          return `<div style="padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.06);font-size:10px">
            <div style="display:flex;justify-content:space-between;gap:8px">
              <span style="color:var(--text);font-weight:700">${m.label}</span>
              <span style="color:var(--accent)">実測 1/${m.actual.toFixed(1)}</span>
            </div>
            <div style="color:var(--muted);margin-top:3px">
              ${[1,2,3,4,5,6].map(s=>{
                const th = m.theory[s];
                const diff = ((m.actual - th) / th * 100);
                const diffStr = Math.abs(diff) < 0.05 ? '±0' : `${diff>0?'+':''}${diff.toFixed(1)}%`;
                return `設定${s}:1/${th}(${diffStr})`;
              }).join(' / ')}
            </div>
            <div style="color:var(--border);margin-top:2px">最近似: 設定${best}</div>
          </div>`;
        }).join('')}
      </div>
    </details>
  `;
}

function renderVizTable(metrics) {
  const vizData = buildVizData(metrics);
  const html = `
    ${renderVizSummary(metrics, vizData)}
    ${renderVizMatrix(metrics, vizData)}
    ${renderVizDetails(metrics, vizData)}
  `;
  document.getElementById('vizTableContent').innerHTML = html;
}

function renderModelHint(model) {
  const hints = MODEL_HINTS[model] || [];
  if(!hints.length){ document.getElementById('stModelHint').innerHTML = '<div style="color:var(--muted);font-size:12px">この機種のヒントはまだ登録されていません</div>'; return; }
  document.getElementById('stModelHint').innerHTML = hints.map(h=>`
    <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;padding:8px;background:var(--bg3);border-radius:6px">
      <div style="min-width:60px;font-size:10px;font-weight:700;color:${h.importance.startsWith('◎')?'var(--plus)':h.importance.startsWith('○')?'var(--accent)':'var(--muted)'}">${h.importance}</div>
      <div>
        <div style="font-size:12px;font-weight:700;color:var(--text);margin-bottom:2px">${h.label}</div>
        <div style="font-size:11px;color:var(--muted)">${h.desc}</div>
      </div>
    </div>`).join('');
}

function stRestoreInputs() {
  const model    = localStorage.getItem('st_model');
  const startG   = localStorage.getItem('st_startG');
  const startBIG = localStorage.getItem('st_startBIG');
  const startREG = localStorage.getItem('st_startREG');
  if(model)    document.getElementById('stModel').value    = model;
  if(startG)   document.getElementById('stStartG').value   = startG;
  if(startBIG) document.getElementById('stStartBIG').value = startBIG;
  if(startREG) document.getElementById('stStartREG').value = startREG;
  stUpdateDisplay();
  renderModelHint(document.getElementById('stModel').value);
}

// ====== セッション保存 ======
function getTodayDateStr() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function setSessionStatus(msg, type = '') {
  const el = document.getElementById('sessionStatus');
  if(!el) return;
  el.textContent = msg;
  el.className = 'session-status';
  if(type) el.classList.add(type);
}

function getGitHubToken() {
  return localStorage.getItem(GITHUB_TOKEN_STORAGE_KEY) || '';
}

function setGitHubToken(token) {
  localStorage.setItem(GITHUB_TOKEN_STORAGE_KEY, token);
}

function clearGitHubTokenStorage() {
  localStorage.removeItem(GITHUB_TOKEN_STORAGE_KEY);
}

function setGitHubTokenStatus(msg, type = '') {
  const el = document.getElementById('githubTokenStatus');
  if(!el) return;
  el.textContent = msg;
  el.className = 'session-status';
  if(type) el.classList.add(type);
}

function renderGitHubTokenUI() {
  const input = document.getElementById('githubTokenInput');
  const token = getGitHubToken();
  if(input && !input.value) input.value = token;
  if(token) {
    setGitHubTokenStatus('設定済み（保存ボタンで更新可能）', 'ok');
  } else {
    setGitHubTokenStatus('未設定', 'warn');
  }
}

function saveGitHubToken() {
  const input = document.getElementById('githubTokenInput');
  const token = (input?.value || '').trim();
  if(!token) {
    setGitHubTokenStatus('トークンを入力してください', 'warn');
    return;
  }
  setGitHubToken(token);
  setGitHubTokenStatus('トークンを保存しました', 'ok');
  setSessionStatus('トークン設定後に保存できます', 'warn');
}

function clearGitHubToken() {
  clearGitHubTokenStorage();
  const input = document.getElementById('githubTokenInput');
  if(input) input.value = '';
  setGitHubTokenStatus('トークンを削除しました', 'warn');
  setSessionStatus('GitHubトークン未設定です。設定タブで入力してください', 'warn');
}

function encodeBase64Utf8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = '';
  bytes.forEach(b => { binary += String.fromCharCode(b); });
  return btoa(binary);
}

function decodeBase64Utf8(base64Text) {
  const normalized = (base64Text || '').replace(/\n/g, '');
  const binary = atob(normalized);
  const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

async function fetchSessionsFromGitHub(token) {
  const url = `https://api.github.com/repos/${GITHUB_SESSIONS_REPO}/contents/${GITHUB_SESSIONS_PATH}?ref=${GITHUB_SESSIONS_BRANCH}`;
  const res = await fetch(url, {
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28'
    }
  });

  const body = await res.json();
  if(res.status === 404) {
    return { sessions: [], sha: null };
  }
  if(!res.ok) {
    const msg = body?.message || `HTTP ${res.status}`;
    throw new Error(`sessions.json取得失敗: ${msg}`);
  }
  const decoded = decodeBase64Utf8(body.content || '');
  const parsed = decoded ? JSON.parse(decoded) : [];
  if(!Array.isArray(parsed)) {
    throw new Error('sessions.json が配列形式ではありません');
  }
  return { sessions: parsed, sha: body.sha };
}

async function pushSessionsToGitHub(token, sessions, sha) {
  const url = `https://api.github.com/repos/${GITHUB_SESSIONS_REPO}/contents/${GITHUB_SESSIONS_PATH}`;
  const content = encodeBase64Utf8(JSON.stringify(sessions, null, 2) + '\n');
  const message = `chore: append session ${getTodayDateStr()}`;
  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    body: JSON.stringify({
      message,
      content,
      ...(sha ? { sha } : {}),
      branch: GITHUB_SESSIONS_BRANCH
    })
  });
  const body = await res.json();
  if(!res.ok) {
    const msg = body?.message || `HTTP ${res.status}`;
    throw new Error(`sessions.json更新失敗: ${msg}`);
  }
  return body;
}

function setSessionInputIfNeeded(id, value, force = false) {
  const el = document.getElementById(id);
  if(!el || value === null || value === undefined) return;
  if(force || !String(el.value || '').trim()) el.value = String(value);
}

function getCurrentSessionSnapshot() {
  const model = document.getElementById('stModel')?.value || '';
  const startG = parseInt(document.getElementById('stStartG')?.value, 10) || 0;
  const startBIG = parseInt(document.getElementById('stStartBIG')?.value, 10) || 0;
  const startREG = parseInt(document.getElementById('stStartREG')?.value, 10) || 0;
  const g = startG + ST.g;
  const big = startBIG + ST.big;
  const reg = startREG + ST.reg;
  const budo = ST.budo;
  const cherry = model === 'マイジャグラーV' ? ST.nonCherry : ST.cherry;
  const store = currentStore !== 'all' ? currentStore : (G.currentTargetContext?.store || '');
  const tai = G.currentTargetContext?.tai || '';

  let prob456 = null;
  if(g >= 100 && model) {
    const result = bayesEstimate(model, g, big, reg, ST.g, budo, cherry, ST.nonCherry, ST.soloBig, ST.soloReg, ST.kadoBig, ST.kadoReg);
    if(result?.probs?.length === 6) {
      prob456 = (result.probs[3] + result.probs[4] + result.probs[5]) * 100;
    }
  }
  if(prob456 === null) {
    const text = document.getElementById('stProb456')?.textContent || '';
    const parsed = parseFloat(text.replace('%', '').trim());
    if(Number.isFinite(parsed)) prob456 = parsed;
  }

  return {
    date: getTodayDateStr(),
    store,
    tai,
    model,
    g,
    big,
    reg,
    budo,
    cherry,
    soloBig: ST.soloBig,
    soloReg: ST.soloReg,
    kadoBig: ST.kadoBig,
    kadoReg: ST.kadoReg,
    prob456
  };
}

function syncSessionFormFromCurrent(force = false) {
  const snap = getCurrentSessionSnapshot();
  setSessionInputIfNeeded('sessionDate', snap.date, force);
  setSessionInputIfNeeded('sessionStore', snap.store, force);
  setSessionInputIfNeeded('sessionTai', snap.tai, force);
  setSessionInputIfNeeded('sessionModel', snap.model, force);
  setSessionInputIfNeeded('sessionG', snap.g, force);
  setSessionInputIfNeeded('sessionBig', snap.big, force);
  setSessionInputIfNeeded('sessionReg', snap.reg, force);
  setSessionInputIfNeeded('sessionBudo', snap.budo, force);
  setSessionInputIfNeeded('sessionCherry', snap.cherry, force);
  if(snap.prob456 !== null && Number.isFinite(snap.prob456)) {
    setSessionInputIfNeeded('sessionBayes', snap.prob456.toFixed(1), force);
  }
  const autoOther = `単独BIG:${snap.soloBig} / 単独REG:${snap.soloReg} / チェリー重複BIG:${snap.kadoBig} / チェリー重複REG:${snap.kadoReg}`;
  setSessionInputIfNeeded('sessionOtherKoyaku', autoOther, force);
}

function renderSessionStoreCandidates() {
  const list = document.getElementById('sessionStoreList');
  if(!list) return;
  const stores = Array.isArray(G.stores) ? G.stores.filter(s => s && s !== 'all') : [];
  list.innerHTML = stores.map(s => `<option value="${s}"></option>`).join('');
}

function renderSessionUI() {
  const dateEl = document.getElementById('sessionDate');
  if(dateEl && !dateEl.value) dateEl.value = getTodayDateStr();
  renderSessionStoreCandidates();
  syncSessionFormFromCurrent(false);
  const token = getGitHubToken();
  if(token) {
    setSessionStatus('GitHub保存の準備完了', 'ok');
  } else {
    setSessionStatus('先に設定タブでGitHubトークンを設定してください', 'warn');
  }
}

async function saveSessionRecord() {
  const token = getGitHubToken();
  if(!token) {
    setSessionStatus('GitHubトークン未設定です。設定タブで入力してください', 'error');
    return;
  }

  const date = document.getElementById('sessionDate')?.value || getTodayDateStr();
  const store = (document.getElementById('sessionStore')?.value || '').trim();
  const tai = (document.getElementById('sessionTai')?.value || '').trim();
  const model = (document.getElementById('sessionModel')?.value || '').trim();
  const g = parseInt(document.getElementById('sessionG')?.value, 10) || 0;
  const big = parseInt(document.getElementById('sessionBig')?.value, 10) || 0;
  const reg = parseInt(document.getElementById('sessionReg')?.value, 10) || 0;
  const diff = parseInt(document.getElementById('sessionDiff')?.value, 10) || 0;
  const budo = parseInt(document.getElementById('sessionBudo')?.value, 10) || 0;
  const cherry = parseInt(document.getElementById('sessionCherry')?.value, 10) || 0;
  const otherKoyaku = (document.getElementById('sessionOtherKoyaku')?.value || '').trim();
  const bayesRaw = parseFloat(document.getElementById('sessionBayes')?.value);
  const bayesProbOver4 = Number.isFinite(bayesRaw) ? Math.max(0, Math.min(100, Number(bayesRaw.toFixed(1)))) : null;
  const withdrawalReason = document.getElementById('sessionWithdrawReason')?.value || '';

  if(!store || !tai || !model) {
    setSessionStatus('店舗名・台番号・機種名は必須です', 'error');
    return;
  }
  if(!withdrawalReason) {
    setSessionStatus('撤退理由を選択してください', 'warn');
    return;
  }

  const record = {
    date,
    store,
    tai,
    model,
    g,
    big,
    reg,
    diff,
    koyaku: {
      budo,
      cherry,
      other: otherKoyaku
    },
    bayesProbOver4,
    withdrawalReason
  };
  setSessionStatus('GitHubへ保存中...', 'warn');

  try {
    const { sessions, sha } = await fetchSessionsFromGitHub(token);
    sessions.push(record);
    await pushSessionsToGitHub(token, sessions, sha);
    setSessionStatus(`GitHubに保存しました（合計 ${sessions.length} 件）`, 'ok');
  } catch (err) {
    setSessionStatus(`保存失敗: ${err.message}`, 'error');
  }
}

function escapeHtml(text) {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getSessionBayesProbOver4(session) {
  const raw = session?.bayesProbOver4;
  const n = Number(raw);
  if(!Number.isFinite(n)) return null;
  return Math.max(0, Math.min(100, n));
}

async function fetchSessionsForAnswerTab() {
  try {
    const res = await fetch(`${GITHUB_SESSIONS_PATH}?_ts=${Date.now()}`, { cache: 'no-store' });
    if(!res.ok) return [];
    const parsed = await res.json();
    return Array.isArray(parsed) ? parsed : [];
  } catch (_) {
    return [];
  }
}

function renderRateTable(rows, key, label) {
  const grouped = {};
  rows.forEach(row => {
    const bucket = row[key] || '不明';
    if(!grouped[bucket]) grouped[bucket] = { hit: 0, total: 0 };
    grouped[bucket].total += 1;
    if(row.judge === '◎') grouped[bucket].hit += 1;
  });
  const ranked = Object.entries(grouped)
    .map(([name, stat]) => ({ name, ...stat, rate: stat.total ? (stat.hit / stat.total) * 100 : 0 }))
    .sort((a, b) => b.rate - a.rate || b.total - a.total || a.name.localeCompare(b.name, 'ja'));
  if(!ranked.length) return '<div class="empty-msg">まだ記録がありません</div>';
  return `
    <div class="answer-table-wrap">
      <table class="data-table answer-rate-table">
        <thead><tr><th>${label}</th><th>的中率</th></tr></thead>
        <tbody>
          ${ranked.map(r => `
            <tr>
              <td>${escapeHtml(r.name)}</td>
              <td><span class="answer-rate-value">${r.rate.toFixed(1)}%</span><span class="answer-rate-sub">（${r.hit}/${r.total}）</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

async function renderAnswerTab() {
  const el = document.getElementById('answerContent');
  if(!el) return;

  el.innerHTML = '<div class="empty-msg">読み込み中...</div>';
  const sessions = await fetchSessionsForAnswerTab();
  const rows = sessions
    .map(session => {
      const bayes = getSessionBayesProbOver4(session);
      const diffRaw = Number(session?.diff);
      const diff = Number.isFinite(diffRaw) ? diffRaw : 0;
      return {
        date: session?.date || '',
        store: session?.store || '不明',
        tai: String(session?.tai || ''),
        model: session?.model || '不明',
        bayes,
        diff,
        judge: diff >= 0 ? '◎' : '×',
      };
    })
    .filter(row => row.bayes !== null && row.bayes >= 60)
    .sort((a, b) => String(b.date).localeCompare(String(a.date), 'ja'));

  if(!rows.length) {
    el.innerHTML = '<div class="empty-msg">まだ記録がありません</div>';
    return;
  }

  const mainTable = `
    <div class="answer-table-wrap">
      <table class="data-table answer-table">
        <thead>
          <tr>
            <th>日付</th>
            <th>店舗</th>
            <th>台番号</th>
            <th>機種</th>
            <th>ベイズスコア</th>
            <th>実測差枚</th>
            <th>判定</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(row => `
            <tr>
              <td>${escapeHtml(row.date)}</td>
              <td>${escapeHtml(row.store)}</td>
              <td>${escapeHtml(row.tai)}</td>
              <td>${escapeHtml(row.model)}</td>
              <td>${row.bayes.toFixed(1)}%</td>
              <td class="${row.diff >= 0 ? 'answer-diff-hit' : 'answer-diff-miss'}">${row.diff >= 0 ? '+' : ''}${row.diff.toLocaleString()}</td>
              <td><span class="answer-judge ${row.judge === '◎' ? 'hit' : 'miss'}">${row.judge}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;

  el.innerHTML = `
    <div class="card">
      <div class="card-title">✅ 予測 vs 実測</div>
      ${mainTable}
    </div>
    <div class="card">
      <div class="card-title">🏪 店舗別的中率</div>
      ${renderRateTable(rows, 'store', '店舗')}
    </div>
    <div class="card">
      <div class="card-title">🎮 機種別的中率</div>
      ${renderRateTable(rows, 'model', '機種')}
    </div>
  `;
}

// RB確率から推定設定（設定4以上のRB確率に相当するか判定）
function isHighSetRBLead(model, g, bb, rb) {
  if(!g||!rb||!bb) return false;
  const actualRB = g / rb;
  const actualBB = g / bb;
  const ms = MODEL_SETTINGS[model];
  if(!ms) return rb > bb; // 設定値不明なら単純比較
  // RBが設定4以上相当 かつ BBが設定4未満相当
  const rb4 = ms.rb[4];
  const bb4 = ms.bb[4];
  return actualRB <= rb4 && actualBB > bb4;
}

function getSpecial() {
  if (G._precomputed && currentStore !== 'all') {
    return G._precomputed.byStore[currentStore]?.special || DEFAULT_SPECIAL;
  }
  return SPECIAL_BY_STORE[currentStore] || SPECIAL_BY_STORE['all'] || DEFAULT_SPECIAL;
}

// ====== 特定日自動検出（データから上位日にちを自動算出） ======
function detectAutoSpecial(rows) {
  const byDay = {};
  rows.forEach(r=>{
    if(!byDay[r.day]) byDay[r.day]={diffs:[],dates:new Set()};
    byDay[r.day].diffs.push(r.diff);
    byDay[r.day].dates.add(r.dateStr);
  });
  // 平均差枚が上位かつサンプル5日以上の日を特定日候補とする
  const ranked = Object.entries(byDay)
    .map(([d,v])=>({day:parseInt(d), avg:round1(avg(v.diffs)), n:v.dates.size}))
    .filter(x=>x.n>=5)
    .sort((a,b)=>b.avg-a.avg);
  // 上位30%または平均+50枚以上の日を特定日とする
  const baseline = avg(ranked.map(x=>x.avg));
  const auto = ranked.filter(x=>x.avg > baseline+30).map(x=>x.day);
  return auto.length >= 3 ? auto : ranked.slice(0,6).map(x=>x.day);
}

// ====== タブ ======
const DETAIL_TABS = new Set(['tab-model','tab-heat','tab-period','tab-setsuteii','tab-next']);

function showTab(id, btn) {
  document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('#mainNav button').forEach(el=>el.classList.remove('active'));
  closeDetailMenu();
  document.getElementById(id).classList.add('active');
  if(btn) btn.classList.add('active');
  // TAB_RENDER_MAPで統一（未定義のタブは何もしない）
  const fn = TAB_RENDER_MAP[id];
  if(fn) {
    try { fn(); }
    catch(err) { console.error(`[showTab] ${id} failed`, err); }
  }
}

function showTabFromMenu(id, btn) {
  showTab(id, null);
  // 詳細ボタンをアクティブ色に
  document.getElementById('detailMenuBtn').classList.add('active');
  document.querySelectorAll('#detailMenu button').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
}

function toggleDetailMenu(btn) {
  const menu = document.getElementById('detailMenu');
  const isOpen = menu.style.display !== 'none';
  if(isOpen) {
    closeDetailMenu();
  } else {
    const rect = btn.getBoundingClientRect();
    menu.style.top  = (rect.bottom + 2) + 'px';
    menu.style.left = Math.min(rect.left, window.innerWidth - 160) + 'px';
    menu.style.display = 'block';
    btn.classList.add('active');
  }
}

function closeDetailMenu() {
  const menu = document.getElementById('detailMenu');
  if(menu) menu.style.display = 'none';
  // 詳細ボタンのアクティブ状態：詳細タブ表示中なら維持
  const activeTab = document.querySelector('.tab-content.active');
  if(!activeTab || !DETAIL_TABS.has(activeTab.id)) {
    document.getElementById('detailMenuBtn')?.classList.remove('active');
  }
}

// メニュー外タップで閉じる
document.addEventListener('click', e => {
  if(!e.target.closest('#detailMenu') && !e.target.closest('#detailMenuBtn')) {
    closeDetailMenu();
  }
});

// ====== 行データ正規化（共通） ======
function normalizeRow(date, dateStr, store, model, taiStr, g, diff, bb, rb) {
  const taiNum = parseInt(taiStr) || 0;
  const s = String(taiNum);
  return {
    date, dateStr,
    store: (store || '不明').trim(),
    model: (model || '').trim(),
    tai: String(taiStr).trim(),
    taiNum,
    g:    g    || 0,
    diff: diff || 0,
    sai:  diff || 0,
    bb:   bb   || 0,
    rb:   rb   || 0,
    day:      date.getDate(),
    weekday:  date.getDay(),
    suef:     taiNum % 10,
    isZoro:   s.length >= 2 && s[s.length-1] === s[s.length-2],
    isRBLead: rb > bb,
    isHighSetRBLead: isHighSetRBLead(model, g, bb, rb),
  };
}

// ====== GASからデータ取得 ======
const DEFAULT_GAS_URL = 'https://script.google.com/macros/s/AKfycbxkecyCx6PxoikwVdDYQxWqU9O0v4AjVZPskdvrvMsKy68MXwRc1V4H0bZ3pmxXloClGQ/exec';

function restoreGasUrlInput() {
  // 常にDEFAULT_GAS_URLを使う（localStorageの古いURLを無視）
  const el = document.getElementById('gasUrlInput');
  if(el) el.value = DEFAULT_GAS_URL;
  localStorage.setItem('juggler_gas_url', DEFAULT_GAS_URL);
}

function saveGasUrlInput() {
  // 常にDEFAULT_GAS_URLを返す
  localStorage.setItem('juggler_gas_url', DEFAULT_GAS_URL);
  return DEFAULT_GAS_URL;
}

function getAny(obj, keys) {
  for(const k of keys) {
    if(obj && obj[k] !== undefined && obj[k] !== null && obj[k] !== '') return obj[k];
  }
  return null;
}

function parseFlexibleDate(v) {
  if(v === null || v === undefined) return null;
  const s = String(v).trim();

  // YYYY/MM/DD or YYYY-MM-DD or ISO形式(2026-02-27T...)
  const isoM = s.match(/^(\d{4})[\/-](\d{1,2})[\/-](\d{1,2})/);
  if(isoM) {
    const y = Number(isoM[1]), mm = Number(isoM[2]), d = Number(isoM[3]);
    const dt = new Date(y, mm-1, d);
    if(!isNaN(dt)) return { date: dt, dateStr: `${y}-${String(mm).padStart(2,'0')}-${String(d).padStart(2,'0')}` };
  }

  // GASのDate.toString()形式: "Mon Feb 27 2026 00:00:00 GMT+0900"
  const gasM = s.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d{4})/);
  if(gasM) {
    const months = {Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12};
    const mm = months[gasM[1]], d = Number(gasM[2]), y = Number(gasM[3]);
    if(mm) {
      const dt = new Date(y, mm-1, d);
      if(!isNaN(dt)) return { date: dt, dateStr: `${y}-${String(mm).padStart(2,'0')}-${String(d).padStart(2,'0')}` };
    }
  }

  return null;
}

function parseNum(v) {
  if(v === null || v === undefined || v === '') return 0;
  const n = parseFloat(String(v).replace(/,/g,'').replace(/\+/g,'').trim());
  return isNaN(n) ? 0 : n;
}

function normalizeGasRows(payload) {
  const rows = Array.isArray(payload) ? payload
    : (Array.isArray(payload?.rows) ? payload.rows
    : (Array.isArray(payload?.data) ? payload.data : []));

  return rows.map(r => {
    const dateRaw = getAny(r, ['date','Date','日付']);
    const parsedDate = parseFlexibleDate(dateRaw);
    if(!parsedDate) return null;
    const store = getAny(r, ['store','店名','店舗名']) || '不明';
    const model = getAny(r, ['model','機種名']) || '';
    const tai   = getAny(r, ['tai','台番号']) || '';
    const g     = parseNum(getAny(r, ['g','G数','総G']));
    const bb    = parseNum(getAny(r, ['bb','BB']));
    const rb    = parseNum(getAny(r, ['rb','RB']));
    const diff  = parseNum(getAny(r, ['sai','diff','差枚']));
    if(!tai || !model) return null;
    return normalizeRow(parsedDate.date, parsedDate.dateStr, store, model, tai, g, diff, bb, rb);
  }).filter(Boolean);
}

function resetGasUrl() {
  localStorage.removeItem('juggler_gas_url');
  const el = document.getElementById('gasUrlInput');
  if(el) el.value = DEFAULT_GAS_URL;
  const status = document.getElementById('gasStatus');
  if(status) { status.textContent = '✅ URLをリセットしました'; status.style.color = 'var(--plus)'; }
  setTimeout(() => { if(status) status.textContent = ''; }, 2000);
}

function loadFromJSON() {
  const btn = document.getElementById('gasLoadBtn');
  const status = document.getElementById('gasStatus');
  btn.disabled = true;
  btn.textContent = '⏳ 読み込み中...';
  status.textContent = 'data.jsonを読み込んでいます...';
  status.style.color = 'var(--accent3)';

  fetch('./data.json', { cache: 'no-store' })
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(json => {
      if (json.byStore && typeof json.byStore === 'object') {
        loadFromPrecomputed(json);
        status.textContent = `✅ 読み込み完了（${json.updated_at || '更新日不明'}）`;
        status.style.color = 'var(--plus)';
        btn.textContent = '📡 データを読み込む';
        btn.disabled = false;
        return;
      }
      // 旧形式フォールバック
      const cols = json.columns || [];
      const rawRows = json.rows || [];
      const objRows = rawRows.map(arr => {
        const obj = {};
        cols.forEach((col, i) => { obj[col] = arr[i] || ''; });
        return obj;
      });
      const rows = normalizeGasRows(objRows);
      if (!rows.length) throw new Error('データが空です');
      G.raw = rows;
      if (!finishLoad()) throw new Error('データの処理に失敗しました');
      const dates = G.raw.map(r => r.dateStr).sort();
      const dateRange = dates.length ? `${dates[0]}〜${dates[dates.length-1]}` : '';
      status.textContent = `✅ ${G.raw.length.toLocaleString()}件読み込み完了 (${dateRange})`;
      status.style.color = 'var(--plus)';
      btn.textContent = '📡 データを読み込む';
      btn.disabled = false;
    })
    .catch(err => {
      status.textContent = `❌ エラー：${err.message}`;
      status.style.color = 'var(--minus)';
      btn.textContent = '📡 データを読み込む';
      btn.disabled = false;
    });
}

function loadFromPrecomputed(json) {
  const byStore = (json.byStore && typeof json.byStore === 'object') ? json.byStore : {};
  const storesFromByStore = Object.keys(byStore);
  G._precomputed = { ...json, byStore };
  G.storeFreshness = (json.store_freshness && typeof json.store_freshness === 'object')
    ? json.store_freshness
    : ((json.storeFreshness && typeof json.storeFreshness === 'object') ? json.storeFreshness : {});
  G.recommendations = Array.isArray(json.recommendations) ? json.recommendations : [];
  const stores = Array.isArray(json.stores) ? json.stores : storesFromByStore;
  G.stores = ['all', ...stores];
  const specialByStore = (json.specialByStore && typeof json.specialByStore === 'object') ? json.specialByStore : {};
  Object.entries(specialByStore).forEach(([store, days]) => {
    SPECIAL_BY_STORE[store] = days;
  });
  currentStore = 'all';
  currentTaiFilter = 'all';
  currentTaiPeriod = 0;
  document.querySelectorAll('#taiPeriodBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  document.querySelector('#taiPeriodBtns .filter-btn')?.classList.add('active');
  setStoreData('all');
  document.getElementById('saveBtn').disabled = false;
  setTimeout(() => {
    renderStoreBar();
    renderAll();
    showStatusPrecomputed(json);
  }, 0);
}

function setStoreData(store) {
  const json = G._precomputed;
  if (!json) return;
  const byStore = (json.byStore && typeof json.byStore === 'object') ? json.byStore : {};
  if (store === 'all') {
    const allStores = Array.isArray(json.stores) ? json.stores : Object.keys(byStore);
    if (!allStores.length) {
      G.dayStats = [];
      G.taiDetail = [];
      G.modelStats = [];
      G.nextStats = {};
      G.heatmap = {};
      G.weekMatrix = {};
      G.dayWdayMatrix = {};
      G.dateSummary = [];
      G.todayAnalysis = null;
      G.raw = [];
      return;
    }
    G.dayStats = mergeAllDayStats(allStores, json);
    G.taiDetail = mergeAllTaiDetail(allStores, json);
    G.modelStats = mergeAllModelStats(allStores, json);
    G.nextStats = mergeAllNextStats(allStores, json);
    G.heatmap = (byStore[allStores[0]] || {}).heatmap || {};
    G.weekMatrix = (byStore[allStores[0]] || {}).weekMatrix || {};
    G.dayWdayMatrix = (byStore[allStores[0]] || {}).dayWdayMatrix || {};
    G.dateSummary = mergeAllDateSummary(allStores, json);
    G.todayAnalysis = (byStore[allStores[0]] || {}).todayAnalysis || null;
  } else {
    const storeData = byStore[store] || {};
    G.dayStats = storeData.dayStats || [];
    G.taiDetail = storeData.taiDetail || [];
    G.modelStats = storeData.modelStats || [];
    G.nextStats = storeData.nextStats || {};
    G.heatmap = storeData.heatmap || {};
    G.weekMatrix = storeData.weekMatrix || {};
    G.dayWdayMatrix = storeData.dayWdayMatrix || {};
    G.dateSummary = storeData.dateSummary || [];
    G.todayAnalysis = storeData.todayAnalysis || null;
  }
  G.raw = [];
}

function mergeAllDayStats(stores, json) {
  const merged = {};
  stores.forEach(s => {
    (json.byStore[s]?.dayStats || []).forEach(d => {
      if (!merged[d.day]) merged[d.day] = { day: d.day, plus: 0, total: 0, special: d.special, sumAvg: 0 };
      merged[d.day].sumAvg += d.avg * d.total;
      merged[d.day].plus += d.plus;
      merged[d.day].total += d.total;
    });
  });
  return Object.values(merged).map(d => ({
    day: d.day,
    avg: round1(d.sumAvg / d.total),
    total: d.total,
    plus: d.plus,
    plusRate: round1(d.plus/d.total*100),
    special: d.special,
    reliable: d.total >= 10,
  })).sort((a,b)=>a.day-b.day);
}

function mergeAllTaiDetail(stores, json) {
  const all = [];
  stores.forEach(s => {
    (json.byStore[s]?.taiDetail || []).forEach(t => all.push({...t, store: s}));
  });
  return all;
}

function mergeAllModelStats(stores, json) {
  const merged = {};
  stores.forEach(s => {
    (json.byStore[s]?.modelStats || []).forEach(m => {
      if (!merged[m.model]) merged[m.model] = { ...m };
      else {
        merged[m.model].count += m.count;
        merged[m.model].spCount = (merged[m.model].spCount||0) + (m.spCount||0);
        merged[m.model].nmCount = (merged[m.model].nmCount||0) + (m.nmCount||0);
      }
    });
  });
  return Object.values(merged);
}

function mergeAllNextStats(stores, json) {
  if (stores.length === 0) return {};
  return json.byStore[stores[0]]?.nextStats || {};
}

function mergeAllDateSummary(stores, json) {
  const merged = {};
  stores.forEach(s => {
    (json.byStore[s]?.dateSummary || []).forEach(d => {
      if (!merged[d.dateStr]) merged[d.dateStr] = { ...d };
    });
  });
  return Object.values(merged).sort((a,b)=>a.dateStr.localeCompare(b.dateStr));
}

function showStatusPrecomputed(json) {
  const stores = json.stores || [];
  const el = document.getElementById('dataStatus');
  const updatedAt = json.updated_at || '更新日不明';
  el.textContent = `${updatedAt}更新`;
  el.classList.add('loaded');
  document.getElementById('loadedInfo').style.display = 'block';
  document.getElementById('loadedSummary').innerHTML = `
    <div style="font-size:12px;line-height:2;">
      📅 更新日: ${updatedAt}<br>
      🏪 ${stores.map(s=>`<span class="badge badge-normal">${s}</span>`).join('')}
    </div>`;
}

function renderRecommendations() {
  const el = document.getElementById('recommendationsList');
  if(!el) return;
  const rows = Array.isArray(G.recommendations) ? G.recommendations : [];
  if(!rows.length) {
    el.innerHTML = '<div class="empty-msg">本日の推薦台はありません</div>';
    return;
  }
  el.innerHTML = `
    <div class="recommendation-grid">
      ${rows.map(r => {
        const reasons = Array.isArray(r.reasons)
          ? r.reasons.filter(v => typeof v === 'string' && v.trim())
          : [];
        const reasonHtml = reasons.length
          ? `<div class="recommendation-reasons">根拠: ${reasons.map(v => escapeHtml(v)).join(' / ')}</div>`
          : '';
        return `
          <article class="recommendation-card">
            <div class="recommendation-head">
              <div>
                <div class="recommendation-store">${escapeHtml(r.store || '店舗不明')}</div>
                <div class="recommendation-model">${escapeHtml(r.model || '機種不明')}</div>
              </div>
              <span class="badge badge-special">${escapeHtml(r.confidence || '★')}</span>
            </div>
            <div class="recommendation-meta">
              <span>台番号 <b>${r.tai || '-'}</b></span>
              <span>ベイズスコア <b>${Number(r.bayes_score || 0).toFixed(1)}%</b></span>
              <span>期待時給 <b>${Math.round(Number(r.expected_hourly || 0)).toLocaleString()}円</b></span>
              <span>信頼度 <b>${r.confidence || '★'}</b></span>
            </div>
            ${reasonHtml}
          </article>
        `;
      }).join('')}
    </div>
  `;
}

function loadFromGAS() {
  const btn = document.getElementById('gasLoadBtn');
  const status = document.getElementById('gasStatus');
  const baseUrl = saveGasUrlInput();
  btn.disabled = true;
  btn.textContent = '⏳ 取得中...';
  status.textContent = 'スプレッドシートに接続しています...';
  status.style.color = 'var(--accent3)';
  const url = `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}_=${Date.now()}`;

  fetch(url, { cache:'no-store' })
    .then(r => {
      return r.text().then(text => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        try {
          return JSON.parse(text);
        } catch(_) {
          if(text.startsWith('<!DOCTYPE') || text.startsWith('<html')) {
            throw new Error('GASの公開設定エラーの可能性（アクセス権を「全員」にして再デプロイ）');
          }
          throw new Error('レスポンスがJSONではありません');
        }
      });
    })
    .then(json => {
      // デバッグ：最初の1件のキーとサンプル値をステータスに表示
      const sampleKeys = (() => {
        const arr = Array.isArray(json) ? json : (json?.rows || json?.data || []);
        if(arr.length > 0) return Object.keys(arr[0]).slice(0,6).join(' / ');
        return '不明';
      })();
      const rows = normalizeGasRows(json);
      if (!rows.length) throw new Error(`データが空です（取得キー: ${sampleKeys}）`);
      G.raw = rows;
      if(!finishLoad()) throw new Error('データの処理に失敗しました');
      const dates = G.raw.map(r=>r.dateStr).sort();
      const dateRange = dates.length ? `${dates[0]}〜${dates[dates.length-1]}` : '';
      status.textContent = `✅ ${G.raw.length.toLocaleString()}件取得完了 (${dateRange})`;
      status.style.color = 'var(--plus)';
      btn.textContent = '📡 スプシからデータを取得';
      btn.disabled = false;
    })
    .catch(err => {
      const msg = String(err && err.message ? err.message : err);
      const hint = /Failed to fetch|NetworkError|CORS/i.test(msg)
        ? '（URL誤り・公開設定・CORSを確認）'
        : '';
      status.textContent = `❌ エラー：${msg}${hint}`;
      status.style.color = 'var(--minus)';
      btn.textContent = '📡 スプシからデータを取得';
      btn.disabled = false;
    });
}

// ====== ファイル読込 ======
const dz = document.getElementById('dropZone');
dz.addEventListener('dragover',e=>{e.preventDefault();dz.style.borderColor='var(--accent)';});
dz.addEventListener('dragleave',()=>dz.style.borderColor='');
dz.addEventListener('drop',e=>{e.preventDefault();dz.style.borderColor='';handleFile(e.dataTransfer.files[0]);});
function handleFile(file){if(!file)return;const r=new FileReader();r.onload=e=>parseCSV(e.target.result);r.readAsText(file,'UTF-8');}
function parsePaste(){const t=document.getElementById('pasteArea').value.trim();if(!t){alert('データを貼り付けてください');return;}parseCSV(t);}

function parseCSV(text) {
  const lines = text.split(/\r?\n/).filter(l=>l.trim());
  const rows = [];
  const sep = lines[0].includes('\t')?'\t':',';
  const cleanNum = s=>parseFloat((s||'').toString().replace(/,/g,'').replace(/\+/g,'').trim());
  for(const line of lines){
    const cols = line.split(sep).map(c=>c.replace(/^"|"$/g,'').trim());
    if(cols.length<6) continue;
    if(cols[0]==='日付'||cols[0]==='date') continue;
    if(!cols[0].match(/\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}/)) continue;
    const [dy,dm,ddd] = cols[0].replace(/\//g,'-').split('-').map(Number);
    const d = new Date(dy, dm-1, ddd);
    if(isNaN(d)) continue;
    const dateStr = `${dy}-${String(dm).padStart(2,'0')}-${String(ddd).padStart(2,'0')}`;
    const diff = cleanNum(cols[5]);
    if(isNaN(diff)) continue;
    rows.push(normalizeRow(
      d, dateStr,
      cols[1], cols[2], cols[3],
      cleanNum(cols[4])||0, diff,
      cleanNum(cols[6])||0, cleanNum(cols[7])||0
    ));
  }
  if(rows.length<3){alert('データが読み込めませんでした\n形式：日付、店名、機種名、台番号、G数、差枚、BB、RB...');return;}
  G.raw = rows;
  finishLoad();
}

// ====== 読込後の共通処理 ======
function finishLoad() {
  if(!G.raw || G.raw.length < 3) {
    alert('データが読み込めませんでした');
    return false;
  }
  // 機種名の表記揺れを正規化（アナスロの表記ゆれ対応）
  const MODEL_NAME_MAP = {
    'ネオアイムジャグラーEX': 'ネオアイムジャグラー',
    'ジャグラーガールズ':     'ジャグラーガールズSS',
  };
  G.raw.forEach(r => { if(MODEL_NAME_MAP[r.model]) r.model = MODEL_NAME_MAP[r.model]; });

  // ジャグラー系以外の機種を除外（MODEL_SETTINGS未登録機種はスコアリング不能のため）
  const before = G.raw.length;
  G.raw = G.raw.filter(r => MODEL_SETTINGS[r.model]);
  const skipped = before - G.raw.length;
  if(skipped > 0) console.info(`[finishLoad] 非対応機種 ${skipped}行を除外（残:${G.raw.length}行）`);
  if(G.raw.length < 3) { alert('ジャグラー系のデータが不足しています（3行未満）'); return false; }
  // 読込時に台別の表示状態を初期化（古いフィルタ状態を持ち越さない）
  currentTaiFilter = 'all';
  currentTaiPeriod = 0;
  document.querySelectorAll('#taiPeriodBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  document.querySelector('#taiPeriodBtns .filter-btn')?.classList.add('active');
  G.stores = ['all', ...new Set(G.raw.map(r => r.store))];
  currentStore = 'all';
  loadSpecialDaysFromStorage();
  const storeList = [...new Set(G.raw.map(r => r.store))];
  storeList.forEach(s => {
    if(!SPECIAL_BY_STORE[s]) {
      const storeRows = G.raw.filter(r => r.store === s);
      SPECIAL_BY_STORE[s] = detectAutoSpecial(storeRows);
    }
  });
  G.autoSpecial = detectAutoSpecial(G.raw);
  G.recommendations = [];
  document.getElementById('saveBtn').disabled = false;
  // 重い処理を非同期化してUIをブロックしない
  setTimeout(() => {
    compute();
    renderStoreBar();
    renderAll();
    showStatus();
  }, 0);
  return true;
}

// ====== フィルター ======
function filteredRows() {
  return currentStore==='all' ? G.raw : G.raw.filter(r=>r.store===currentStore);
}

// ====== 集計 ======
const avg = arr=>arr.length?arr.reduce((a,b)=>a+b,0)/arr.length:0;
const round1 = v=>Math.round(v*10)/10;

function compute() {
  const rows = filteredRows();
  const SP = getSpecial();

  // 日にち別
  const byDay={};
  rows.forEach(r=>{
    if(!byDay[r.day]) byDay[r.day]={diffs:[],plus:0,total:0};
    byDay[r.day].diffs.push(r.diff);byDay[r.day].total++;
    if(r.diff>0) byDay[r.day].plus++;
  });
  G.dayStats=Array.from({length:31},(_,i)=>i+1).map(d=>{
    const b=byDay[d];if(!b)return null;
    return{day:d,avg:round1(avg(b.diffs)),total:b.total,plus:b.plus,
      plusRate:round1(b.plus/b.total*100),special:SP.includes(d)};
  }).filter(Boolean);

  // 台別
  const byTai={};
  rows.forEach(r=>{
    const k=`${r.taiNum}_${r.model}`;
    if(!byTai[k]) byTai[k]={tai:r.tai,taiNum:r.taiNum,model:r.model,all:[],sp:[],nm:[],
      g:[],bb:[],rb:[],spG:[],spBB:[],spRB:[],nmG:[],nmBB:[],nmRB:[]};
    byTai[k].all.push(r.diff);
    byTai[k].g.push(r.g||0);
    byTai[k].bb.push(r.bb||0);
    byTai[k].rb.push(r.rb||0);
    if(SP.includes(r.day)){
      byTai[k].sp.push(r.diff);
      byTai[k].spG.push(r.g||0); byTai[k].spBB.push(r.bb||0); byTai[k].spRB.push(r.rb||0);
    } else {
      byTai[k].nm.push(r.diff);
      byTai[k].nmG.push(r.g||0); byTai[k].nmBB.push(r.bb||0); byTai[k].nmRB.push(r.rb||0);
    }
  });
  G.taiDetail=Object.values(byTai).map(t=>{
    const totalG  = t.g.reduce((a,b)=>a+b,0);
    const totalBB = t.bb.reduce((a,b)=>a+b,0);
    const totalRB = t.rb.reduce((a,b)=>a+b,0);
    const spTotalG  = t.spG.reduce((a,b)=>a+b,0);
    const spTotalBB = t.spBB.reduce((a,b)=>a+b,0);
    const spTotalRB = t.spRB.reduce((a,b)=>a+b,0);
    const nmTotalG  = t.nmG.reduce((a,b)=>a+b,0);
    const nmTotalBB = t.nmBB.reduce((a,b)=>a+b,0);
    const nmTotalRB = t.nmRB.reduce((a,b)=>a+b,0);
    return {
      tai:t.tai, taiNum:t.taiNum, model:t.model,
      avg:round1(avg(t.all)), count:t.all.length,
      plus:t.all.filter(v=>v>0).length,
      plusRate:round1(t.all.filter(v=>v>0).length/t.all.length*100),
      spAvg:t.sp.length?round1(avg(t.sp)):null,
      nmAvg:t.nm.length?round1(avg(t.nm)):null,
      // 追加フィールド
      totalG, totalBB, totalRB,
      avgG: t.all.length ? round1(totalG/t.all.length) : 0,
      rbRate:  totalRB  > 0 ? Math.round(totalG/totalRB)  : null,
      synRate: (totalBB+totalRB) > 0 ? Math.round(totalG/(totalBB+totalRB)) : null,
      spRbRate:  spTotalRB  > 0 ? Math.round(spTotalG/spTotalRB)   : null,
      nmRbRate:  nmTotalRB  > 0 ? Math.round(nmTotalG/nmTotalRB)   : null,
      spSynRate: (t.spBB.reduce((a,b)=>a+b,0)+spTotalRB) > 0
        ? Math.round(spTotalG / (t.spBB.reduce((a,b)=>a+b,0)+spTotalRB)) : null,
      nmSynRate: (t.nmBB.reduce((a,b)=>a+b,0)+nmTotalRB) > 0
        ? Math.round(nmTotalG / (t.nmBB.reduce((a,b)=>a+b,0)+nmTotalRB)) : null,
      spTotalBonus: spTotalBB + spTotalRB,
      nmTotalBonus: t.nmBB.reduce((a,b)=>a+b,0) + nmTotalRB,
      spTotalRB, nmTotalRB,
      spTotalG, nmTotalG, spTotalBB, nmTotalBB,
      spCount: t.sp.length,
      nmCount: t.nm.length,
      // ベイズ確率を事前計算してキャッシュ（Layer3描画時の再計算を防ぐ）
      bayesProbAll: calcTaiBayesProb(t.model, totalG, totalBB, totalRB),
      bayesProbSp:  calcTaiBayesProb(t.model, spTotalG, spTotalBB, spTotalRB),
      bayesProbNm:  calcTaiBayesProb(t.model, nmTotalG, nmTotalBB, nmTotalRB),
    };
  }).sort((a,b)=>a.taiNum-b.taiNum);

  // 日付別サマリー
  const byDate={};
  rows.forEach(r=>{
    if(!byDate[r.dateStr]) byDate[r.dateStr]={dateStr:r.dateStr,date:r.date,diffs:[],plus:0,day:r.day};
    byDate[r.dateStr].diffs.push(r.diff);
    if(r.diff>0) byDate[r.dateStr].plus++;
  });
  G.dateSummary=Object.values(byDate).sort((a,b)=>a.date-b.date).map(d=>({
    dateStr:d.dateStr,date:d.date,
    total:round1(d.diffs.reduce((a,b)=>a+b,0)),
    count:d.diffs.length,plus:d.plus,
    plusRate:round1(d.plus/d.diffs.length*100),
    day:d.day,special:SP.includes(d.day)
  }));

  // 機種別
  const byModel={};
  rows.forEach(r=>{
    if(!byModel[r.model]) byModel[r.model]={model:r.model,all:[],sp:[],nm:[],byDay:{},g:[],bb:[],rb:[]};
    byModel[r.model].all.push(r.diff);
    byModel[r.model].g.push(r.g);
    byModel[r.model].bb.push(r.bb);
    byModel[r.model].rb.push(r.rb);
    if(SP.includes(r.day)) byModel[r.model].sp.push(r.diff);
    else byModel[r.model].nm.push(r.diff);
    if(!byModel[r.model].byDay[r.day]) byModel[r.model].byDay[r.day]=[];
    byModel[r.model].byDay[r.day].push(r.diff);
  });

  // 今月/先月の境界を計算
  const latestDate = rows.reduce((a,b)=>a.date>b.date?a:b).date;
  const thisMonthStart = new Date(latestDate.getFullYear(), latestDate.getMonth(), 1);
  const lastMonthStart = new Date(latestDate.getFullYear(), latestDate.getMonth()-1, 1);
  const lastMonthEnd   = new Date(latestDate.getFullYear(), latestDate.getMonth(), 0);

  const byModelMonth={};
  rows.forEach(r=>{
    if(!byModelMonth[r.model]) byModelMonth[r.model]={thisMonth:[],lastMonth:[]};
    if(r.date >= thisMonthStart) byModelMonth[r.model].thisMonth.push(r.diff);
    else if(r.date >= lastMonthStart && r.date <= lastMonthEnd) byModelMonth[r.model].lastMonth.push(r.diff);
  });

  G.modelStats=Object.values(byModel).map(m=>{
    const totalG = m.g.reduce((a,b)=>a+b,0);
    const totalBB = m.bb.reduce((a,b)=>a+b,0);
    const totalRB = m.rb.reduce((a,b)=>a+b,0);
    // 推定出率: 差枚から機械割を推定（1G=3枚投入として）
    const totalIn = totalG * 3;
    const totalOut = totalIn + m.all.reduce((a,b)=>a+b,0);
    const mechRitu = totalIn > 0 ? round1(totalOut/totalIn*100) : null;
    const mm = byModelMonth[m.model]||{thisMonth:[],lastMonth:[]};
    // 機種別RB確率（全期間・特定日・通常日）
    const spRows = rows.filter(r=>r.model===m.model && SP.includes(r.day));
    const nmRows = rows.filter(r=>r.model===m.model && !SP.includes(r.day));
    const spTotalG  = spRows.reduce((a,r)=>a+(r.g||0),0);
    const spTotalRB = spRows.reduce((a,r)=>a+(r.rb||0),0);
    const nmTotalG  = nmRows.reduce((a,r)=>a+(r.g||0),0);
    const nmTotalRB = nmRows.reduce((a,r)=>a+(r.rb||0),0);
    return {
      model:m.model, allAvg:round1(avg(m.all)), count:m.all.length,
      spAvg:m.sp.length?round1(avg(m.sp)):null, spCount:m.sp.length,
      nmAvg:m.nm.length?round1(avg(m.nm)):null, nmCount:m.nm.length,
      byDay:m.byDay, mechRitu,
      thisMonthAvg: mm.thisMonth.length ? round1(avg(mm.thisMonth)) : null,
      thisMonthCount: mm.thisMonth.length,
      lastMonthAvg: mm.lastMonth.length ? round1(avg(mm.lastMonth)) : null,
      lastMonthCount: mm.lastMonth.length,
      rbRate:  totalRB > 0 ? Math.round(totalG/totalRB) : null,
      synRate: (totalBB+totalRB) > 0 ? Math.round(totalG/(totalBB+totalRB)) : null,
      spRbRate: spTotalRB > 0 ? Math.round(spTotalG/spTotalRB) : null,
      nmRbRate: nmTotalRB > 0 ? Math.round(nmTotalG/nmTotalRB) : null,
      totalRB, spTotalRB, nmTotalRB,
    };
  });

  // 翌日成績分析
  computeNextDay(rows, SP);
}

// ====== 翌日成績分析 集計 ======
function computeNextDay(rows, SP) {
  // 台×日付でインデックス作成
  const byTaiDate = {};
  rows.forEach(r=>{
    const k = `${r.tai}_${r.store}`;
    if(!byTaiDate[k]) byTaiDate[k]=[];
    byTaiDate[k].push(r);
  });

  // 各台の時系列を日付順に並べて「翌日ペア」を作る
  const pairs = []; // {prevRow, nextRow}
  Object.values(byTaiDate).forEach(taiRows=>{
    const sorted = taiRows.sort((a,b)=>a.date-b.date);
    for(let i=0;i<sorted.length-1;i++){
      const prev = sorted[i];
      const next = sorted[i+1];
      // 翌日かどうか確認（1日差）
      const dayDiff = (next.date - prev.date) / (1000*60*60*24);
      if(dayDiff===1) pairs.push({prev, next});
    }
  });

  // 条件別集計
  const conditions = [
    { key:'凹み_2000以上', label:'前日差枚 -2000以下', filter: p=>p.prev.diff<=-2000 },
    { key:'凹み_1000_2000', label:'前日差枚 -1000〜-2000', filter: p=>p.prev.diff<-1000&&p.prev.diff>-2000 },
    { key:'凹み_500_1000', label:'前日差枚 -500〜-1000', filter: p=>p.prev.diff<=-500&&p.prev.diff>-1000 },
    { key:'凹み_0_500', label:'前日差枚 0〜-500', filter: p=>p.prev.diff<0&&p.prev.diff>-500 },
    { key:'プラス', label:'前日差枚 プラス', filter: p=>p.prev.diff>0 },
    { key:'プラス500以上', label:'前日差枚 +500以上', filter: p=>p.prev.diff>=500 },
    { key:'RB先行', label:'前日RB先行不発（RB>BB）', filter: p=>p.prev.isRBLead&&p.prev.diff<0 },
    { key:'RB先行高設定', label:'前日RB先行不発（設定4以上相当）', filter: p=>p.prev.isHighSetRBLead&&p.prev.diff<0 },
    { key:'連続凹み', label:'連続凹み2日以上', filter: (p,allPairs)=>{
      // この台の前日もマイナスだったか
      const prevPair = allPairs.find(pp=>pp.next.tai===p.prev.tai&&pp.next.store===p.prev.store&&pp.next.dateStr===p.prev.dateStr);
      return p.prev.diff<0 && prevPair && prevPair.prev.diff<0;
    }},
    { key:'特定日前日', label:'特定日の前日が凹み', filter: p=>SP.includes(p.next.day)&&p.prev.diff<0 },
    { key:'特定日翌日', label:'特定日翌日の台', filter: p=>SP.includes(p.prev.day) },
  ];

  const result = {};
  conditions.forEach(cond=>{
    const matched = cond.filter.length===2
      ? pairs.filter(p=>cond.filter(p,pairs))
      : pairs.filter(p=>cond.filter(p));
    const nextDiffs = matched.map(p=>p.next.diff);
    result[cond.key] = {
      label: cond.label,
      count: nextDiffs.length,
      avg: nextDiffs.length ? round1(avg(nextDiffs)) : null,
      plusRate: nextDiffs.length ? round1(nextDiffs.filter(v=>v>0).length/nextDiffs.length*100) : null,
    };
  });

  // 全体平均（ベースライン）
  const allDiffs = rows.map(r=>r.diff);
  result['__baseline'] = {
    label:'全期間平均（ベースライン）',
    count: allDiffs.length,
    avg: round1(avg(allDiffs)),
    plusRate: round1(allDiffs.filter(v=>v>0).length/allDiffs.length*100),
  };

  G.nextStats = result;
  G.pairs = pairs;

  // ヒートマップ集計：日にち末尾 × 台番号末尾（月=日・ゾロ目・月末を含む特殊行も追加）
  const heat = {};
  const addHeat = (key, r) => {
    if(!heat[key]) heat[key]={diffs:[],g:[],count:0,highSet:0};
    heat[key].diffs.push(r.diff);
    heat[key].g.push(r.g);
    heat[key].count++;
    if(r.isHighSetRBLead) heat[key].highSet++;
  };
  rows.forEach(r=>{
    const dk = r.day % 10;
    const tk = r.suef;
    addHeat(`${dk}_${tk}`, r);
    // 特殊行
    if(r.isZoro) addHeat(`zoro_${tk}`, r);
    if(r.day === r.date.getMonth()+1) addHeat(`tsuki_${tk}`, r); // 月=日
    // 月末：その月の最終日かどうか
    const lastDay = new Date(r.date.getFullYear(), r.date.getMonth()+1, 0).getDate();
    if(r.day === lastDay) addHeat(`end_${tk}`, r);
  });
  G.heatmap = {};
  Object.entries(heat).forEach(([k,v])=>{
    const totalIn = v.g.reduce((a,b)=>a+b,0)*3;
    const totalOut = totalIn + v.diffs.reduce((a,b)=>a+b,0);
    G.heatmap[k]={
      avg:round1(avg(v.diffs)),
      ritu: totalIn>0 ? round1(totalOut/totalIn*100) : null,
      win: round1(v.diffs.filter(x=>x>0).length/v.diffs.length*100),
      set456: round1(v.highSet/v.count*100),
      count:v.count,
      diffs:v.diffs,
    };
  });

  // 第○週×曜日マトリクス
  const wm = {};
  rows.forEach(r=>{
    const wday = r.weekday;
    const week = Math.ceil(r.day/7);
    const key = `${week}_${wday}`;
    if(!wm[key]) wm[key]={diffs:[],g:[],count:0,highSet:0};
    wm[key].diffs.push(r.diff);
    wm[key].g.push(r.g);
    wm[key].count++;
    if(r.isHighSetRBLead) wm[key].highSet++;
  });
  G.weekMatrix = {};
  Object.entries(wm).forEach(([k,v])=>{
    const totalIn = v.g.reduce((a,b)=>a+b,0)*3;
    const totalOut = totalIn + v.diffs.reduce((a,b)=>a+b,0);
    G.weekMatrix[k]={
      avg:round1(avg(v.diffs)),
      ritu: totalIn>0 ? round1(totalOut/totalIn*100) : null,
      win: round1(v.diffs.filter(x=>x>0).length/v.diffs.length*100),
      set456: round1(v.highSet/v.count*100),
      count:v.count,
    };
  });

  // 日付末尾×曜日マトリクス
  const dwm = {};
  const addDW = (rowKey, r) => {
    const wday = r.weekday;
    const key = `${rowKey}_${wday}`;
    if(!dwm[key]) dwm[key]={diffs:[],g:[],count:0,highSet:0};
    dwm[key].diffs.push(r.diff);
    dwm[key].g.push(r.g);
    dwm[key].count++;
    if(r.isHighSetRBLead) dwm[key].highSet++;
  };
  rows.forEach(r=>{
    addDW(r.day%10, r);
    if(r.isZoro) addDW('zoro', r);
    if(r.day === r.date.getMonth()+1) addDW('tsuki', r);
    const lastDay2 = new Date(r.date.getFullYear(), r.date.getMonth()+1, 0).getDate();
    if(r.day === lastDay2) addDW('end', r);
  });
  G.dayWdayMatrix = {};
  Object.entries(dwm).forEach(([k,v])=>{
    const totalIn = v.g.reduce((a,b)=>a+b,0)*3;
    const totalOut = totalIn + v.diffs.reduce((a,b)=>a+b,0);
    G.dayWdayMatrix[k]={
      avg:round1(avg(v.diffs)),
      ritu: totalIn>0 ? round1(totalOut/totalIn*100) : null,
      win: round1(v.diffs.filter(x=>x>0).length/v.diffs.length*100),
      set456: round1(v.highSet/v.count*100),
      count:v.count,
    };
  });
}

// ====== スコアリング（データ駆動・自動重み付け） ======

// ====== 第2段階：配分読み関数群 ======

function getRowsByCondition(rows, conditionType) {
  const SP = getSpecial();
  if(conditionType === 'sp') return rows.filter(r => SP.includes(r.day));
  if(conditionType === 'nm') return rows.filter(r => !SP.includes(r.day));
  return rows;
}

// RB良好率スコア（上書き式・最大2pt）
function calcRbGoodScore(rb3GoodRate, rb4GoodRate) {
  if(rb4GoodRate !== null && rb4GoodRate >= 30) return 2;
  if(rb4GoodRate !== null && rb4GoodRate >= 20) return 1;
  if(rb3GoodRate !== null && rb3GoodRate >= 40) return 1;
  return 0;
}

// 台単位RB良好率を計算する共通関数
function calcTaiRbGoodRates(taiMap, modelName) {
  let validTai = 0, rb3Good = 0, rb4Good = 0;
  for(const key in taiMap) {
    const t = taiMap[key];
    if(t.totalRB < 5) continue; // 有効台条件
    const rbRate = Math.round(t.totalG / t.totalRB);
    const setLevel = rbRateToSetLevel(modelName || t.model, rbRate);
    if(setLevel === null) continue;
    validTai++;
    if(setLevel >= 3) rb3Good++;
    if(setLevel >= 4) rb4Good++;
  }
  return {
    validTai,
    rb3GoodRate: validTai > 0 ? round1(rb3Good / validTai * 100) : null,
    rb4GoodRate: validTai > 0 ? round1(rb4Good / validTai * 100) : null,
  };
}

function scoreModelStrength({ avgDiff, mechRitu, plusRate, rb3GoodRate, rb4GoodRate, sampleCount }) {
  let pts = 0;

  // 差枚点
  if(avgDiff >= 200)      pts += 3;
  else if(avgDiff >= 100) pts += 2;
  else if(avgDiff >= 0)   pts += 1;

  // 出率点
  if(mechRitu !== null) {
    if(mechRitu >= 101.0)      pts += 2;
    else if(mechRitu >= 100.0) pts += 1;
  }

  // プラス率点
  if(plusRate >= 60)      pts += 1;
  else if(plusRate >= 50) pts += 0.5;

  // RB良好率点（上書き式・最大2pt）
  pts += calcRbGoodScore(rb3GoodRate, rb4GoodRate);

  const sampleState = sampleCount >= 10 ? '通常評価' : sampleCount >= 5 ? '参考値' : '不足';
  const label = sampleState === '不足' ? '傾向薄い'
    : pts >= 6 ? '有力'
    : pts >= 4 ? '対抗'
    : pts >= 2 ? '弱め'
    : '傾向薄い';

  return { score: round1(pts), label, sampleState };
}

function calcModelStrength(rows, conditionType) {
  const targetRows = getRowsByCondition(rows, conditionType);
  const byModel = {};

  for(const r of targetRows) {
    if(!byModel[r.model]) byModel[r.model] = { model:r.model, rows:[], diffs:[], gList:[], taiMap:{} };
    const m = byModel[r.model];
    m.rows.push(r);
    m.diffs.push(r.diff);
    m.gList.push(r.g || 0);
    const tk = `${r.tai}_${r.model}`;
    if(!m.taiMap[tk]) m.taiMap[tk] = { totalG:0, totalRB:0, model:r.model };
    m.taiMap[tk].totalG  += (r.g  || 0);
    m.taiMap[tk].totalRB += (r.rb || 0);
  }

  const result = [];
  for(const modelName in byModel) {
    const m = byModel[modelName];
    const sampleCount = m.rows.length;
    const totalDiff   = m.diffs.reduce((a,b)=>a+b,0);
    const avgDiff     = sampleCount ? totalDiff / sampleCount : 0;
    const totalG      = m.gList.reduce((a,b)=>a+b,0);
    const totalIn     = totalG * 3;
    const mechRitu    = totalIn > 0 ? (totalIn + totalDiff) / totalIn * 100 : null;
    const plusRate    = sampleCount ? m.rows.filter(x=>x.diff>0).length / sampleCount * 100 : 0;

    const { rb3GoodRate, rb4GoodRate } = calcTaiRbGoodRates(m.taiMap, modelName);
    const scored = scoreModelStrength({ avgDiff, mechRitu, plusRate, rb3GoodRate, rb4GoodRate, sampleCount });

    result.push({
      model: modelName,
      avgDiff: round1(avgDiff), mechRitu: mechRitu !== null ? round1(mechRitu) : null,
      plusRate: round1(plusRate), rb3GoodRate, rb4GoodRate, sampleCount,
      score: scored.score, label: scored.label, sampleState: scored.sampleState,
    });
  }
  return result.sort((a,b) => b.score - a.score);
}

function calcSuefStrength(rows, conditionType) {
  const targetRows = getRowsByCondition(rows, conditionType);
  const baseline   = targetRows.length ? targetRows.reduce((a,r)=>a+r.diff,0) / targetRows.length : 0;

  const bySuef = {};
  for(const r of targetRows) {
    const s = r.taiNum % 10;
    if(!bySuef[s]) bySuef[s] = { rows:[], diffs:[], taiMap:{} };
    bySuef[s].rows.push(r);
    bySuef[s].diffs.push(r.diff);
    const tk = `${r.tai}_${r.model}`;
    if(!bySuef[s].taiMap[tk]) bySuef[s].taiMap[tk] = { totalG:0, totalRB:0, model:r.model };
    bySuef[s].taiMap[tk].totalG  += (r.g  || 0);
    bySuef[s].taiMap[tk].totalRB += (r.rb || 0);
  }

  const result = [];
  for(const suefStr in bySuef) {
    const s = bySuef[suefStr];
    const sampleCount = s.rows.length;
    const avgDiff     = round1(s.diffs.reduce((a,b)=>a+b,0) / sampleCount);
    const plusRate    = round1(s.rows.filter(r=>r.diff>0).length / sampleCount * 100);
    const lift        = round1(avgDiff - baseline);

    const { rb3GoodRate, rb4GoodRate } = calcTaiRbGoodRates(s.taiMap, null);

    let pts = 0;
    if(lift >= 150)      pts += 3;
    else if(lift >= 80)  pts += 2;
    else if(lift >= 30)  pts += 1;
    else if(lift < -30)  pts -= 1;
    if(plusRate >= 60)      pts += 1;
    else if(plusRate >= 50) pts += 0.5;
    pts += calcRbGoodScore(rb3GoodRate, rb4GoodRate);

    const sampleState = sampleCount >= 10 ? '通常評価' : sampleCount >= 5 ? '参考値' : '不足';
    const label = sampleState === '不足' ? '傾向薄い'
      : pts >= 5 ? '有力' : pts >= 3 ? '対抗' : pts >= 1 ? '弱め' : '傾向薄い';

    result.push({
      suef: +suefStr, avgDiff, plusRate, rb3GoodRate, rb4GoodRate,
      sampleCount, lift, score: round1(pts), label, sampleState,
    });
  }
  return result.sort((a,b) => b.score - a.score);
}

function calcClusterStrength(rows, conditionType) {
  const targetRows = getRowsByCondition(rows, conditionType);

  // 日付ごとにグループ化
  const byDate = {};
  for(const r of targetRows) {
    if(!byDate[r.dateStr]) byDate[r.dateStr] = [];
    byDate[r.dateStr].push(r);
  }

  let clusterDays = 0, validDays = 0;
  let totalRbGoodInCluster = 0, totalClusterTai = 0;

  for(const dateStr in byDate) {
    const dayRows = byDate[dateStr];
    const plusTais = dayRows.filter(r=>r.diff>500).sort((a,b)=>a.taiNum-b.taiNum);
    if(plusTais.length < 3) continue;
    validDays++;

    // 台番号差3以内でつながる3台以上のクラスターを探す
    let hasCluster = false;
    let clusterStart = 0;
    for(let i = 1; i <= plusTais.length; i++) {
      const broken = i === plusTais.length || (plusTais[i].taiNum - plusTais[i-1].taiNum) > 3;
      if(broken) {
        const size = i - clusterStart;
        if(size >= 3) {
          hasCluster = true;
          // クラスター内のRB良好台を数える（補助表示用）
          const clusterTais = plusTais.slice(clusterStart, i);
          totalClusterTai += clusterTais.length;
          for(const t of clusterTais) {
            const rbRate = t.rb > 0 ? Math.round((t.g||0)/t.rb) : null;
            const setLevel = rbRate ? rbRateToSetLevel(t.model, rbRate) : null;
            if(setLevel !== null && setLevel >= 3) totalRbGoodInCluster++;
          }
        }
        clusterStart = i;
      }
    }
    if(hasCluster) clusterDays++;
  }

  const clusterRate = validDays > 0 ? round1(clusterDays / validDays * 100) : null;
  const style = clusterRate === null ? '不明'
    : clusterRate >= 60 ? '並び型'
    : clusterRate >= 40 ? '混合型'
    : '散らし型';
  const styleScore = clusterRate === null ? 0
    : clusterRate >= 60 ? 2
    : clusterRate >= 40 ? 1
    : clusterRate >= 20 ? 0 : -1;

  const sampleState = validDays >= 10 ? '通常評価' : validDays >= 5 ? '参考値' : '不足';
  const label = style + (sampleState !== '通常評価' ? '（参考）' : '');

  const rbGoodInCluster = totalClusterTai > 0
    ? round1(totalRbGoodInCluster / totalClusterTai * 100) : null;

  return { clusterRate, style, styleScore, sampleDays:validDays, sampleState, label, rbGoodInCluster };
}


// ====== 席配置マスター ======

let L = {
  store: '',
  floor: '',
  gridCols: 20,
  gridRows: 12,
  selectedTai: null,        // 未配置一覧から選択中
  selectedPlacedTai: null,  // マップ上で選択中
  placed: [],               // [{tai, x, y}]
  unplaced: []              // [台番号]
};

// 席配置マスターのタブを開いたとき初期化
function initLayoutMasterTab() {
  // 店舗リストをデータから取得
  const storeEl = document.getElementById('lmStore');
  storeEl.innerHTML = '<option value="">店舗を選択</option>';
  const stores = G.stores ? G.stores.filter(s => s !== 'all') : [];
  stores.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s; opt.textContent = s;
    storeEl.appendChild(opt);
  });

  // 前回選択を復元
  const saved = getSavedLayoutStores();
  // フロア一覧も更新
  renderLayoutMaster();
}

// 保存済みレイアウト一覧をlocalStorageから取得
function getSavedLayoutData() {
  try {
    const s = localStorage.getItem('juggler_layout_master');
    return s ? JSON.parse(s) : {};
  } catch(e) { return {}; }
}
function getSavedLayoutStores() {
  return Object.keys(getSavedLayoutData());
}

function onLayoutStoreChange() {
  L.store = document.getElementById('lmStore').value;
  L.floor = '';
  updateLayoutFloorSelect();
  loadLayoutForCurrentState();
}

function updateLayoutFloorSelect() {
  const floorEl = document.getElementById('lmFloor');
  floorEl.innerHTML = '<option value="">フロア</option>';
  if(!L.store) return;
  const data = getSavedLayoutData();
  const floors = Object.keys((data[L.store] || {}));
  floors.forEach(f => {
    const opt = document.createElement('option');
    opt.value = f; opt.textContent = f;
    floorEl.appendChild(opt);
  });
}

function onLayoutFloorChange() {
  L.floor = document.getElementById('lmFloor').value;
  loadLayoutForCurrentState();
}

function addNewFloor() {
  const name = document.getElementById('lmNewFloor').value.trim();
  if(!name || !L.store) { alert('店舗を選択してフロア名を入力してください'); return; }
  L.floor = name;
  document.getElementById('lmNewFloor').value = '';
  // 台番号をG.rawから生成
  loadLayoutSource(L.store, L.floor);
  updateLayoutFloorSelect();
  // セレクトを更新して選択
  setTimeout(() => {
    const floorEl = document.getElementById('lmFloor');
    // オプションがなければ追加
    let found = false;
    for(const opt of floorEl.options) { if(opt.value === name) { found = true; opt.selected = true; break; } }
    if(!found) {
      const opt = document.createElement('option');
      opt.value = name; opt.textContent = name; opt.selected = true;
      floorEl.appendChild(opt);
    }
  }, 50);
  renderLayoutMaster();
}

// 台番号をG.taiDetailから抽出（対象店舗）
function loadLayoutSource(store, floor) {
  const source = G.taiDetail.length ? G.taiDetail : G.raw;
  const rows = store === 'all' ? source : source.filter(r => r.store === store);
  const tais = [...new Set(rows.map(r => r.taiNum))].filter(Boolean).sort((a,b)=>a-b);
  // 保存済みの配置を読み込む
  const data = getSavedLayoutData();
  const saved = (data[store] || {})[floor] || null;
  if(saved) {
    L.placed = saved.placed || [];
    const placedSet = new Set(L.placed.map(p => p.tai));
    L.unplaced = tais.filter(t => !placedSet.has(t));
    if(saved.gridCols) { L.gridCols = saved.gridCols; document.getElementById('lmCols').value = L.gridCols; }
    if(saved.gridRows) { L.gridRows = saved.gridRows; document.getElementById('lmRows').value = L.gridRows; }
  } else {
    L.placed = [];
    L.unplaced = tais;
  }
  L.selectedTai = null;
  L.selectedPlacedTai = null;
}

function loadLayoutForCurrentState() {
  if(!L.store || !L.floor) {
    L.placed = []; L.unplaced = []; L.selectedTai = null; L.selectedPlacedTai = null;
    renderLayoutMaster(); return;
  }
  loadLayoutSource(L.store, L.floor);
  renderLayoutMaster();
}

// ===== 描画 =====
function renderLayoutMaster() {
  renderUnplacedTaiList();
  renderLayoutGrid();
  renderLayoutStatus();
}

function renderUnplacedTaiList() {
  const el = document.getElementById('lmUnplacedList');
  const countEl = document.getElementById('lmUnplacedCount');
  if(!el) return;
  countEl.textContent = `(${L.unplaced.length})`;
  if(!L.unplaced.length) {
    el.innerHTML = '<div style="font-size:10px;color:var(--muted);padding:6px;text-align:center">全台配置済み</div>';
    return;
  }
  el.innerHTML = L.unplaced.map(t => {
    const sel = L.selectedTai === t;
    return `<div onclick="selectUnplacedTai(${t})"
      style="padding:5px 8px;margin:2px;border-radius:4px;font-size:11px;cursor:pointer;text-align:center;
      background:${sel?'var(--accent)':'var(--bg4)'};color:${sel?'#000':'var(--text)'};
      border:1px solid ${sel?'var(--accent)':'var(--border)'}">
      ${t}
    </div>`;
  }).join('');
}

function renderLayoutGrid() {
  const el = document.getElementById('lmGrid');
  if(!el) return;
  const cols = L.gridCols, rows = L.gridRows;
  const CELL = 36;

  // placedをマップに変換
  const placedMap = {};
  L.placed.forEach(p => { placedMap[`${p.x}_${p.y}`] = p.tai; });

  let html = `<table style="border-collapse:collapse;table-layout:fixed">`;
  for(let y = 0; y < rows; y++) {
    html += '<tr>';
    for(let x = 0; x < cols; x++) {
      const key = `${x}_${y}`;
      const tai = placedMap[key];
      const isSelPlaced = tai !== undefined && L.selectedPlacedTai === tai;
      if(tai !== undefined) {
        html += `<td onclick="onGridCellClick(${x},${y})"
          style="width:${CELL}px;height:${CELL}px;text-align:center;vertical-align:middle;
          font-size:10px;font-weight:700;cursor:pointer;border:1px solid var(--border);
          background:${isSelPlaced?'var(--accent)':'var(--plus)'};
          color:${isSelPlaced?'#000':'#000'};border-radius:3px">${tai}</td>`;
      } else {
        const isHover = (L.selectedTai !== null || L.selectedPlacedTai !== null);
        html += `<td onclick="onGridCellClick(${x},${y})"
          style="width:${CELL}px;height:${CELL}px;cursor:${isHover?'crosshair':'default'};
          border:1px solid var(--border);background:var(--bg4);border-radius:2px"></td>`;
      }
    }
    html += '</tr>';
  }
  html += '</table>';
  el.innerHTML = html;
}

function renderLayoutStatus() {
  const statusEl = document.getElementById('lmStatusText');
  const delBtn   = document.getElementById('lmDeleteBtn');
  const clrBtn   = document.getElementById('lmClearSelBtn');
  if(!statusEl) return;

  if(L.selectedTai !== null) {
    statusEl.textContent = `選択中（未配置）: ${L.selectedTai} ← 空セルをクリックして配置`;
    statusEl.style.color = 'var(--accent)';
    delBtn.style.display  = 'none';
    clrBtn.style.display  = 'inline-block';
  } else if(L.selectedPlacedTai !== null) {
    statusEl.textContent = `選択中（配置済）: ${L.selectedPlacedTai} ← 空セルで移動 or 削除`;
    statusEl.style.color = 'var(--plus)';
    delBtn.style.display  = 'inline-block';
    clrBtn.style.display  = 'inline-block';
  } else {
    statusEl.textContent = L.store && L.floor
      ? `${L.store} / ${L.floor}　配置済み: ${L.placed.length}台　未配置: ${L.unplaced.length}台`
      : '店舗とフロアを選択してください';
    statusEl.style.color = 'var(--muted)';
    delBtn.style.display  = 'none';
    clrBtn.style.display  = 'none';
  }
}

// ===== クリック処理 =====
function onGridCellClick(x, y) {
  const tai = getPlacedAt(x, y);
  if(tai !== null) {
    // 配置済みセルクリック → 選択
    selectPlacedTai(tai);
  } else {
    // 空セルクリック
    if(L.selectedTai !== null) {
      placeSelectedTai(x, y);
    } else if(L.selectedPlacedTai !== null) {
      moveSelectedPlacedTai(x, y);
    }
  }
}

function selectUnplacedTai(tai) {
  L.selectedTai = (L.selectedTai === tai) ? null : tai;
  L.selectedPlacedTai = null;
  renderLayoutMaster();
}

function selectPlacedTai(tai) {
  L.selectedPlacedTai = (L.selectedPlacedTai === tai) ? null : tai;
  L.selectedTai = null;
  renderLayoutMaster();
}

function placeSelectedTai(x, y) {
  if(!isCellEmpty(x, y)) return;
  L.placed.push({ tai: L.selectedTai, x, y });
  L.unplaced = L.unplaced.filter(t => t !== L.selectedTai);
  L.selectedTai = null;
  renderLayoutMaster();
}

function moveSelectedPlacedTai(x, y) {
  if(!isCellEmpty(x, y)) return;
  const idx = L.placed.findIndex(p => p.tai === L.selectedPlacedTai);
  if(idx >= 0) { L.placed[idx].x = x; L.placed[idx].y = y; }
  L.selectedPlacedTai = null;
  renderLayoutMaster();
}

function removeSelectedPlacedTai() {
  if(L.selectedPlacedTai === null) return;
  L.unplaced.push(L.selectedPlacedTai);
  L.unplaced.sort((a,b) => a-b);
  L.placed = L.placed.filter(p => p.tai !== L.selectedPlacedTai);
  L.selectedPlacedTai = null;
  renderLayoutMaster();
}

function clearLayoutSelection() {
  L.selectedTai = null;
  L.selectedPlacedTai = null;
  renderLayoutMaster();
}

function resizeLayoutGrid() {
  L.gridCols = parseInt(document.getElementById('lmCols').value) || 20;
  L.gridRows = parseInt(document.getElementById('lmRows').value) || 12;
  renderLayoutGrid();
}

// ===== 判定系 =====
function getPlacedAt(x, y) {
  const p = L.placed.find(p => p.x === x && p.y === y);
  return p ? p.tai : null;
}
function isCellEmpty(x, y) { return getPlacedAt(x, y) === null; }

// ===== 保存・リセット =====
function saveLayoutMaster() {
  if(!L.store || !L.floor) { alert('店舗とフロアを選択してください'); return; }
  const all = getSavedLayoutData();
  if(!all[L.store]) all[L.store] = {};
  all[L.store][L.floor] = { placed: L.placed, gridCols: L.gridCols, gridRows: L.gridRows };
  try {
    localStorage.setItem('juggler_layout_master', JSON.stringify(all));
    updateLayoutFloorSelect();
    renderLayoutStatus();
    // フラッシュ
    const btn = event?.target;
    if(btn) { const orig = btn.textContent; btn.textContent = '✅ 保存済み'; setTimeout(()=>btn.textContent=orig, 1200); }
  } catch(e) { alert('保存に失敗しました: ' + e.message); }
}

function resetLayoutMaster() {
  if(!L.store || !L.floor) return;
  if(!confirm(`${L.store} / ${L.floor} の配置をリセットしますか？`)) return;
  const source = G.taiDetail.length ? G.taiDetail : G.raw;
  const rows = L.store === 'all' ? source : source.filter(r => r.store === L.store);
  const tais = [...new Set(rows.map(r => r.taiNum))].filter(Boolean).sort((a,b)=>a-b);
  L.placed = []; L.unplaced = tais;
  L.selectedTai = null; L.selectedPlacedTai = null;
  renderLayoutMaster();
}


// ====== 第3段階：台別評価関数群（Task 1〜11） ======

// Task 2: 条件別RB確率
function getConditionalRbRate(tai, isSpecial) {
  if(isSpecial) {
    if(tai.spRbRate) return { rbRate: tai.spRbRate, totalRB: tai.spTotalRB || tai.totalRB, source: '特定日' };
  } else {
    if(tai.nmRbRate) return { rbRate: tai.nmRbRate, totalRB: tai.nmTotalRB || tai.totalRB, source: '通常日' };
  }
  return { rbRate: tai.rbRate, totalRB: tai.totalRB, source: '全期間' };
}

// Task 3: 条件別合算確率
function getConditionalSynRate(tai, isSpecial) {
  if(isSpecial) {
    if(tai.spSynRate) return { synRate: tai.spSynRate, totalBonus: tai.spTotalBonus || (tai.totalBB + tai.totalRB), source: '特定日' };
  } else {
    if(tai.nmSynRate) return { synRate: tai.nmSynRate, totalBonus: tai.nmTotalBonus || (tai.totalBB + tai.totalRB), source: '通常日' };
  }
  return { synRate: tai.synRate, totalBonus: (tai.totalBB + tai.totalRB), source: '全期間' };
}

// Task 4: RB点関数
function scoreTaiRbRate(model, rbRate, totalRB) {
  if(!rbRate || !totalRB || totalRB < 5) return { pts: 0, setLevel: null, valid: false };
  const setLevel = rbRateToSetLevel(model, rbRate);
  if(setLevel === null) return { pts: 0, setLevel: null, valid: false };
  let pts = 0;
  if(setLevel >= 5)      pts = 3;
  else if(setLevel >= 4) pts = 2;
  else if(setLevel >= 3) pts = 1;
  else                   pts = 0;
  return { pts, setLevel, valid: true };
}

// Task 5: 合算点関数
function scoreTaiSynRate(model, synRate, totalBonus) {
  if(!synRate || !totalBonus || totalBonus < 10) return { pts: 0, setLevel: null, valid: false };
  const ms = MODEL_SETTINGS[model];
  if(!ms) return { pts: 0, setLevel: null, valid: false };
  const syn = ms.syn;
  // 最も近い設定を判定
  let closest = 1, minDiff = Infinity;
  for(let s = 1; s <= 6; s++) {
    const d = Math.abs(syn[s] - synRate);
    if(d < minDiff) { minDiff = d; closest = s; }
  }
  let pts = 0;
  if(closest >= 4)      pts = 2;
  else if(closest >= 3) pts = 1;
  return { pts, setLevel: closest, valid: true };
}

// Task 6: 信頼度補正
function applyReliabilityAdjust(score, avgG, smallCount) {
  let factor = 1.0;
  if(avgG >= 4000)      factor = 1.0;
  else if(avgG >= 2000) factor = 0.7;
  else if(avgG >= 1000) factor = 0.5;
  else                  factor = 0.3;
  // 小台数機種はさらに0.8倍（配分が読みにくいため）
  if(smallCount) factor = Math.max(0.2, factor * 0.8);
  const raw = score;
  const adjusted = score >= 0 ? Math.floor(score * factor) : Math.ceil(score * factor);
  return { rawScore: raw, adjustedScore: adjusted, factor, smallCount: !!smallCount };
}


// ====== 角台補正（席配置マスター連携） ======

// 席配置から「角台」の台番号リストを返す
// 角台の定義：そのマスの上下左右4方向のうち、空マスまたはグリッド端が2方向以上ある台
function getLayoutCornerTais(store) {
  const data = getSavedLayoutData();
  if(!data || !data[store]) return { cornerTais: new Set(), edgeTais: new Set(), hasLayout: false };

  // フロアを全部マージして判定（フロアまたぎは別島扱いでも可）
  const floors = data[store];
  const cornerTais = new Set();
  const edgeTais   = new Set();

  for(const floorKey in floors) {
    const floor = floors[floorKey];
    const placed = floor.placed || [];
    const cols = floor.gridCols || 20;
    const rowCount = floor.gridRows || 12;

    // 配置済みマスをSetに
    const occupied = new Set(placed.map(p => `${p.x},${p.y}`));

    for(const p of placed) {
      const { x, y, tai } = p;
      // 4方向の「隣が空 or グリッド端」をカウント
      const dirs = [
        [x-1, y], [x+1, y], [x, y-1], [x, y+1]
      ];
      let emptyOrEdge = 0;
      for(const [nx, ny] of dirs) {
        const outOfGrid = nx < 0 || nx >= cols || ny < 0 || ny >= rowCount;
        const emptyCell = !occupied.has(`${nx},${ny}`);
        if(outOfGrid || emptyCell) emptyOrEdge++;
      }
      if(emptyOrEdge >= 3)      cornerTais.add(tai); // 3方向以上が空/端 = 角台
      else if(emptyOrEdge >= 2) edgeTais.add(tai);   // 2方向 = 端台（島端）
    }
  }

  return { cornerTais, edgeTais, hasLayout: true };
}

// 角台傾向をホール全体データから計算
// 角台 vs 非角台の平均差枚を比較してリフトを返す
function calcCornerTendency(rows, cornerTais, edgeTais) {
  if(!cornerTais || cornerTais.size === 0) return null;

  const cornerRows  = rows.filter(r => cornerTais.has(r.taiNum));
  const edgeRows    = rows.filter(r => edgeTais.has(r.taiNum) && !cornerTais.has(r.taiNum));
  const normalRows  = rows.filter(r => !cornerTais.has(r.taiNum) && !edgeTais.has(r.taiNum));

  const avg = arr => arr.length >= 3 ? round1(arr.reduce((a,r)=>a+r.diff,0)/arr.length) : null;

  const cornerAvg = avg(cornerRows);
  const normalAvg = avg(normalRows);
  const edgeAvg   = avg(edgeRows);
  const baseAvg   = avg(rows);

  if(cornerAvg === null || baseAvg === null) return null;

  const cornerLift = round1(cornerAvg - baseAvg);
  const edgeLift   = edgeAvg !== null ? round1(edgeAvg - baseAvg) : null;

  return {
    cornerAvg, normalAvg, edgeAvg, baseAvg,
    cornerLift, edgeLift,
    cornerCount: cornerRows.length,
    edgeCount:   edgeRows.length,
    normalCount: normalRows.length,
    // 角台有利かどうかの判定
    isCornerStrong: cornerLift >= 80,   // 全体平均より80枚以上良ければ有利
    isEdgeStrong:   edgeLift !== null && edgeLift >= 50,
  };
}

// 台単体が角台/端台なら補正点を返す
function getCornerBonus(taiNum, cornerTais, edgeTais, cornerTendency) {
  if(!cornerTendency) return { pts: 0, label: null };
  const isCorner = cornerTais && cornerTais.has(taiNum);
  const isEdge   = edgeTais   && edgeTais.has(taiNum) && !isCorner;

  if(isCorner && cornerTendency.isCornerStrong)
    return { pts: 1, label: `角台（全体比+${cornerTendency.cornerLift}枚）` };
  if(isEdge && cornerTendency.isEdgeStrong)
    return { pts: 0.5, label: `端台（全体比+${cornerTendency.edgeLift}枚）` };
  if(isCorner)
    return { pts: 0, label: `角台（傾向は薄い）` };
  if(isEdge)
    return { pts: 0, label: `端台（傾向は薄い）` };
  return { pts: 0, label: null };
}

// Task 8: 配分根拠点
// 台別蓄積データからP(設定4以上)を計算（機種別重み付きベイズ）
const _bayesCache = new Map();
function calcTaiBayesProb(model, totalG, totalBB, totalRB) {
  if(!totalG || totalG < 300 || !MODEL_SETTINGS[model]) return null;
  const cacheKey = `${model}_${totalG}_${totalBB}_${totalRB}`;
  if(_bayesCache.has(cacheKey)) return _bayesCache.get(cacheKey);
  const ms = MODEL_SETTINGS[model];
  const mw = MODEL_WEIGHTS[model] || MODEL_WEIGHTS['マイジャグラーV'];
  const settings = [1,2,3,4,5,6];
  let logProbs = settings.map(() => Math.log(1/6));

  if(totalBB >= 5) {
    settings.forEach((s, i) => {
      const expBB = totalG / ms.bb[s];
      logProbs[i] += mw.bb * logLikelihoodPoisson(totalBB, expBB);
    });
  }
  if(totalRB >= 5) {
    settings.forEach((s, i) => {
      const expRB = totalG / ms.rb[s];
      logProbs[i] += mw.rb * logLikelihoodPoisson(totalRB, expRB);
    });
  }

  const maxLog = Math.max(...logProbs);
  let probs = logProbs.map(p => Math.exp(p - maxLog));
  const total = probs.reduce((a,b) => a+b, 0);
  probs = probs.map(p => p/total);
  const result = Math.round((probs[3]+probs[4]+probs[5])*100);
  _bayesCache.set(cacheKey, result);
  return result;
}

function calcTaiConfigScore(tai, context) {
  const { isSpecial, baseline, rows, SP, modelStrength, suefStrength, clusterResult } = context;
  let score = 0;
  const reasons = [];

  // ① 台別ベイズスコア（キャッシュ済みの値を参照）
  const condN  = isSpecial ? (tai.spCount || 0) : (tai.nmCount || 0);
  const bayesProb = isSpecial ? tai.bayesProbSp : tai.bayesProbNm;

  if(bayesProb !== null) {
    let pts = 0;
    if(condN >= 5) {
      if(bayesProb >= 60)      pts = 3;
      else if(bayesProb >= 45) pts = 2;
      else if(bayesProb >= 30) pts = 1;
    } else if(condN >= 3) {
      if(bayesProb >= 60)      pts = 2;
      else if(bayesProb >= 45) pts = 1;
    }
    if(pts > 0) {
      score += pts;
      reasons.push({ label: `${isSpecial?'特定日':'通常日'}ベイズ評価`, val: `高設定確率${bayesProb}%（N=${condN}）`, pts });
    } else {
      // スコアなしでも参考表示
      reasons.push({ label: `${isSpecial?'特定日':'通常日'}ベイズ評価`, val: `高設定確率${bayesProb}%（N=${condN}）`, pts: 0 });
    }
  } else {
    // データ不足 → 全期間データでフォールバック
    const fallbackProb = tai.bayesProbAll;
    if(fallbackProb !== null) {
      reasons.push({ label: '全期間ベイズ評価（参考）', val: `高設定確率${fallbackProb}%（N=${tai.count}）`, pts: 0 });
    } else {
      reasons.push({ label: `${isSpecial?'特定日':'通常日'}データ`, val: `サンプル不足（N=${condN}）`, pts: 0 });
    }
  }

  // ② 末尾傾向（参考表示のみ・スコア加算なし）
  const suef = tai.taiNum % 10;
  const suefData = suefStrength ? suefStrength.find(s => s.suef === suef) : null;
  if(suefData && suefData.sampleState !== '不足') {
    reasons.push({ label: `末尾${suef}の傾向（参考）`, val: `${suefData.lift>=0?'+':''}${suefData.lift}枚 ${suefData.label}`, pts: 0 });
  }

  // ③ 機種配分（参考表示のみ・スコア加算なし）
  const mData = modelStrength ? modelStrength.find(m => m.model === tai.model) : null;
  if(mData) {
    reasons.push({ label: '機種配分（参考）', val: `${mData.label}（${mData.sampleCount}件）`, pts: 0 });
  }

  // ④ 角台補正（席配置マスター連携・参考表示のみ）
  const { cornerTais, edgeTais, cornerTendency } = context;
  if(cornerTais) {
    const bonus = getCornerBonus(tai.taiNum, cornerTais, edgeTais, cornerTendency);
    if(bonus.label) {
      reasons.push({ label: '角台/端台（参考）', val: bonus.label, pts: 0 });
    }
  }

  return { score: round1(score), reasons };
}

// Task 9: 数値根拠点
function calcTaiValueScore(tai, context) {
  const { isSpecial, rows } = context;
  let score = 0;
  const reasons = [];

  // RB確率（主軸）
  const { rbRate, totalRB, source: rbSrc } = getConditionalRbRate(tai, isSpecial);
  const rbMeta = scoreTaiRbRate(tai.model, rbRate, totalRB);

  // 合算確率（補助）
  const { synRate, totalBonus, source: synSrc } = getConditionalSynRate(tai, isSpecial);
  const synMeta = scoreTaiSynRate(tai.model, synRate, totalBonus);

  // 信頼度補正（avgGベース + 小台数機種補正）
  const smallCount = isSmallCountModel(tai.model, rows);
  const reliabilityMeta = applyReliabilityAdjust(rbMeta.pts + synMeta.pts, tai.avgG || 0, smallCount);

  // 補正後の値を使ってスコア分配
  const rawTotal = rbMeta.pts + synMeta.pts;
  const adjTotal = reliabilityMeta.adjustedScore;
  const factor = reliabilityMeta.factor;

  // 各点に補正を按分
  const adjRbPts  = rbMeta.valid  ? (rbMeta.pts  >= 0 ? Math.floor(rbMeta.pts  * factor) : Math.ceil(rbMeta.pts  * factor)) : 0;
  const adjSynPts = synMeta.valid ? (synMeta.pts >= 0 ? Math.floor(synMeta.pts * factor) : Math.ceil(synMeta.pts * factor)) : 0;
  score = adjRbPts + adjSynPts;

  if(rbMeta.valid) {
    const setLvLabel = rbMeta.setLevel ? `設定${rbMeta.setLevel}相当` : '';
    reasons.push({
      label: `RB確率（${rbSrc}）`,
      val: rbRate ? `1/${rbRate}  ${setLvLabel}` : '—',
      pts: adjRbPts,
      rawPts: rbMeta.pts
    });
  } else {
    reasons.push({ label: `RB確率（${rbSrc}）`, val: totalRB < 5 ? `サンプル不足(${totalRB}回)` : '—', pts: 0, rawPts: 0 });
  }

  if(synMeta.valid) {
    reasons.push({
      label: `合算確率（${synSrc}）`,
      val: synRate ? `1/${synRate}  設定${synMeta.setLevel}相当` : '—',
      pts: adjSynPts,
      rawPts: synMeta.pts
    });
  }

  return {
    score: round1(score),
    reasons,
    rbMeta: { ...rbMeta, rbRate, totalRB, source: rbSrc, adjPts: adjRbPts },
    synMeta: { ...synMeta, synRate, totalBonus, source: synSrc, adjPts: adjSynPts },
    reliabilityMeta
  };
}

// Task 10: 注意フラグ生成（level: strong/weak付き）
function buildTaiWarningFlags(tai, valueResult, configScore, isSpecial, rows) {
  const flags = [];
  const ref = isSpecial ? tai.spAvg : tai.nmAvg;
  const rbPts = valueResult.rbMeta.adjPts;
  const synPts = valueResult.synMeta.adjPts;

  // === strong: ランク低下対象 ===

  // 差枚プラスだがRB弱い（誤爆系）
  if(ref !== null && ref > 200 && rbPts <= 0)
    flags.push({ level: 'strong', text: '差枚プラスだがRBが弱い → 誤爆・一撃依存の可能性' });

  // 合算良いがRB弱い（BB偏り系）
  if(synPts >= 1 && rbPts <= 0)
    flags.push({ level: 'strong', text: '合算は良いがRBが弱い → BB偏り型の可能性' });

  // 稼働浅い＋差枚先行（見かけ強台）
  if(tai.avgG < 1000 && ref !== null && ref > 100)
    flags.push({ level: 'strong', text: `稼働浅い(${tai.avgG}G)＋差枚先行 → データ不足で過大評価の可能性` });

  // === weak: 表示のみ・ランク低下なし ===

  // 稼働が浅い（単体）
  if(tai.avgG < 1000 && !(ref !== null && ref > 100))
    flags.push({ level: 'weak', text: `平均稼働${tai.avgG}G/日（サンプル浅・信頼度低）` });

  // RB高いが差枚マイナス（不発・参考情報）
  if(rbPts >= 2 && ref !== null && ref < -200)
    flags.push({ level: 'weak', text: 'RBは高設定寄りだが差枚マイナス → 高設定不発の可能性' });

  // 特定日依存
  if(isSpecial && tai.spAvg !== null && tai.nmAvg !== null && tai.spAvg - tai.nmAvg > 300)
    flags.push({ level: 'weak', text: '特定日だけ突出 → 通常日は配分なしの可能性' });

  // 小台数機種
  if(rows && isSmallCountModel(tai.model, rows)) {
    const taiCount = getModelTaiCount(tai.model, rows);
    flags.push({ level: 'info', text: `小台数機種（店内${taiCount}台）：配分が読みにくいため参考値として判断`, strong: false });
  }

  return flags;
}

// adjustRankByWarnings: strongフラグでランクを1段階下げる
function adjustRankByWarnings(baseRank, warningFlags) {
  const hasStrong = warningFlags.some(f => f.level === 'strong');
  if(!hasStrong) return baseRank;
  const order = ['本命', '対抗', '保留', '注意'];
  const idx = order.indexOf(baseRank);
  return idx < order.length - 1 ? order[idx + 1] : '注意';
}

// Task 11: 現地確認ポイント生成（最大3件・優先順付き）
function buildFieldCheckPoints(tai, context, warningFlags, valueResult) {
  const { isSpecial, rows, targetDate, model } = context;
  const rbPts = valueResult.rbMeta.adjPts;
  const candidates = []; // { priority, text }

  // 前日データ取得
  const prevDay = new Date(targetDate);
  prevDay.setDate(prevDay.getDate()-1);
  const pds = `${prevDay.getFullYear()}-${String(prevDay.getMonth()+1).padStart(2,'0')}-${String(prevDay.getDate()).padStart(2,'0')}`;
  const prevRow = rows.find(r => r.tai === tai.tai && r.model === model && r.dateStr === pds);

  // 優先度1: 誤爆/不発の見極め（strongフラグ対応）
  const hasGobaku  = warningFlags.some(f => f.text.includes('誤爆'));
  const hasFupatu  = warningFlags.some(f => f.text.includes('不発'));
  const hasBBbias  = warningFlags.some(f => f.text.includes('BB偏り'));
  if(hasGobaku)  candidates.push({ priority: 1, text: 'グラフが一山型でないか確認（一撃依存型は見送り）' });
  if(hasFupatu)  candidates.push({ priority: 1, text: 'RBペースが続くなら高設定不発型 → 続行検討' });
  if(hasBBbias)  candidates.push({ priority: 1, text: 'BB偏り型の可能性 → RBが少なすぎるなら見送り' });
  if(!valueResult.rbMeta.valid) candidates.push({ priority: 1, text: 'RBデータ不足 → 当日RBペースを最重視' });

  // 優先度2: 周辺・並び・前日
  if(prevRow) {
    if(prevRow.isRBLead && prevRow.diff < 0)
      candidates.push({ priority: 2, text: `前日RB先行不発(${prevRow.diff}枚) → 粘り型か確認` });
    else if(prevRow.diff <= -2000)
      candidates.push({ priority: 2, text: `前日大負け(${prevRow.diff}枚) → 低設定の可能性。慎重に` });
    else if(prevRow.diff >= 500)
      candidates.push({ priority: 2, text: `前日好調(+${prevRow.diff}枚) → 据え置きか変更か周辺台も確認` });
  }
  candidates.push({ priority: 2, text: '周辺台が同時に動いているか確認（並び型か単品か）' });

  // 優先度3: 稼働深度・条件依存
  const hasShallow = warningFlags.some(f => f.text.includes('稼働浅'));
  if(hasShallow) candidates.push({ priority: 3, text: `稼働${tai.avgG}G/日と浅い → 立ち上がりを重視` });
  if(isSpecial)  candidates.push({ priority: 3, text: '特定日：開店直後の全体の出方を先に確認' });
  if(rbPts >= 2) candidates.push({ priority: 3, text: 'RBペース良 → 100Gごとに1/200以下なら続行' });

  // 優先度順にソートして最大3件
  candidates.sort((a, b) => a.priority - b.priority);
  const points = candidates.slice(0, 3).map(c => c.text);

  return { points, prevRow };
}

// Task 1: 台別評価メイン関数
function calcTaiStrength(tai, context) {
  const { isSpecial, baseline, suefStrength, modelStrength, rows } = context;

  // 配分根拠点
  const configResult = calcTaiConfigScore(tai, context);

  // 数値根拠点
  const valueResult = calcTaiValueScore(tai, context);

  // 注意フラグ
  const warningFlags = buildTaiWarningFlags(tai, valueResult, configResult.score, isSpecial, rows);

  // 現地確認ポイント
  const { points: fieldCheckPoints, prevRow } = buildFieldCheckPoints(tai, context, warningFlags, valueResult);

  // 合計スコア
  const totalScore = round1(configResult.score + valueResult.score);

  // ランク判定（configScoreがベイズベース3pt満点に変わったため閾値調整）
  let baseRank;
  if(valueResult.score >= 2 && configResult.score >= 2) {
    baseRank = '本命'; // 数値根拠強 + ベイズ配分根拠強
  } else if(valueResult.score >= 2 || (valueResult.score >= 1 && configResult.score >= 2)) {
    baseRank = '対抗'; // どちらかが強い
  } else if(totalScore >= 1) {
    baseRank = '保留';
  } else {
    baseRank = '注意';
  }
  // adjustRankByWarnings: strongフラグで1段階降格
  const rank = adjustRankByWarnings(baseRank, warningFlags);

  return {
    configScore:   configResult.score,
    valueScore:    valueResult.score,
    totalScore,
    configReasons: configResult.reasons,
    valueReasons:  valueResult.reasons,
    valueDetail:   valueResult,
    warningFlags,
    fieldCheckPoints,
    prevRow,
    rank
  };
}

// ベースライン比（lift）を正規化してスコア化する
// lift = この条件の翌日平均 - 全体ベースライン平均
// → liftが大きい条件ほど高スコア。一般論ではなくこの店のデータが重みを決める。

function liftToScore(lift, sampleOk) {
  if(!sampleOk) return 0;
  if(lift >= 150) return 3;
  if(lift >= 80)  return 2;
  if(lift >= 30)  return 1;
  if(lift >= -30) return 0;
  if(lift >= -80) return -1;
  if(lift >= -150)return -2;
  return -3;
}

// RB確率を設定段階(1〜6)に変換（MODEL_SETTINGS使用）
// rbRate は「1/N回」のNの部分（大きいほど出ていない）
function rbRateToSetLevel(model, rbRate) {
  if(!rbRate) return null;
  const ms = MODEL_SETTINGS[model];
  if(!ms) return null;
  const rb = ms.rb; // {1:439, 2:399, ... 6:127} ← 分母、小さいほど高設定
  // rbRateが各設定の理論値に近いかを判定
  // 設定6〜1の順に近い方を返す
  const diffs = [1,2,3,4,5,6].map(s => ({ s, d: Math.abs(rbRate - rb[s]) }));
  diffs.sort((a,b) => a.d - b.d);
  return diffs[0].s; // 最も近い設定
}

// RB確率から数値根拠点を計算
function rbRateScore(model, rbRate, totalRB) {
  if(!rbRate || totalRB < 5) return { pts: 0, label: null }; // サンプル不足
  const ms = MODEL_SETTINGS[model];
  if(!ms) return { pts: 0, label: null };
  const th = ms.rb;
  // 閾値を重複なく定義（rbは分母なので小さいほど高設定）
  // 設定6±5%以内
  if(rbRate <= th[6] * 1.05)          return { pts: 3, label: `RB確率 1/${rbRate}（設定6相当）` };
  // 設定5±5%以内
  if(rbRate <= th[5] * 1.05)          return { pts: 3, label: `RB確率 1/${rbRate}（設定5〜6相当）` };
  // 設定4〜5の間（設定5の5%超〜設定3の95%未満）
  if(rbRate <= th[3] * 0.95)          return { pts: 2, label: `RB確率 1/${rbRate}（設定4〜5相当）` };
  // 設定3〜4の間
  if(rbRate <= (th[2] + th[3]) / 2)   return { pts: 0, label: `RB確率 1/${rbRate}（設定3〜4相当）` };
  // 設定2〜3の間
  if(rbRate <= th[2] * 1.05)          return { pts: 0, label: `RB確率 1/${rbRate}（設定2〜3相当）` };
  // 設定1相当
  return { pts: -1, label: `RB確率 1/${rbRate}（設定1相当）` };
}

// 合算確率から数値根拠点を計算
function synRateScore(model, synRate, totalBonus) {
  if(!synRate || totalBonus < 10) return { pts: 0, label: null };
  const ms = MODEL_SETTINGS[model];
  if(!ms) return { pts: 0, label: null };
  const th = ms.syn;
  if(synRate <= th[4] * 1.05)   return { pts: 2, label: `合算確率 1/${synRate}（設定4以上相当）` };
  if(synRate <= th[3] * 1.05)   return { pts: 1, label: `合算確率 1/${synRate}（設定3〜4相当）` };
  if(synRate <= th[2] * 1.05)   return { pts: 0, label: `合算確率 1/${synRate}（設定2〜3相当）` };
  return { pts: -1, label: `合算確率 1/${synRate}（設定1相当以下）` };
}

function getCondLift(key) {
  const bl = G.nextStats['__baseline'];
  const s  = G.nextStats[key];
  if(!bl || !s || s.avg===null) return {lift:0, ok:false};
  const ok = s.count >= 10; // 最低10サンプル必要
  return {lift: round1(s.avg - bl.avg), ok, count:s.count, avg:s.avg};
}

function calcScore(tai, targetDate) {
  const SP = getSpecial();
  const day = targetDate.getDate();
  const isSpecial = SP.includes(day);
  const rows = filteredRows();
  const baseline = G.nextStats['__baseline'];
  let score = 0;
  const reasons = [];

  // ① 台の過去成績（特定日/通常日別）
  // → 「過去にこの台は儲かったか」。ベースライン比で評価。
  const taiInfo = G.taiDetail.find(t=>t.tai===tai.tai&&t.model===tai.model);
  if(taiInfo && baseline){
    const ref = isSpecial ? taiInfo.spAvg : taiInfo.nmAvg;
    const bl  = baseline.avg;
    if(ref !== null){
      const lift = round1(ref - bl);
      const pts = liftToScore(lift, taiInfo.count >= 5);
      score += pts;
      reasons.push({
        label:`台の過去${isSpecial?'特定日':'通常日'}成績`,
        val:`${ref>=0?'+':''}${ref}枚（ベース比${lift>=0?'+':''}${lift}）`,
        pts, lift
      });
    }
  }

  // ② 日にちの強さ（ベースライン比）
  const dayInfo = G.dayStats.find(d=>d.day===day);
  if(dayInfo && baseline){
    const lift = round1(dayInfo.avg - baseline.avg);
    const pts = liftToScore(lift, dayInfo.total >= 5);
    score += pts;
    reasons.push({
      label:`${day}日の強さ`,
      val:`平均${dayInfo.avg>=0?'+':''}${dayInfo.avg}枚（ベース比${lift>=0?'+':''}${lift}）`,
      pts, lift
    });
  }

  // ③ 前日条件（翌日分析のベース比liftをそのまま重みにする）
  const prevDay = new Date(targetDate);
  prevDay.setDate(prevDay.getDate()-1);
  const prevDateStr1 = prevDay.toISOString().slice(0,10).replace(/-/g,'/');
  const prevDateStr2 = prevDay.toISOString().slice(0,10);
  const prevRow = rows.find(r=>
    r.tai===tai.tai &&
    (r.dateStr===prevDateStr1 || r.dateStr===prevDateStr2)
  );

  if(prevRow){
    // 前日差枚の区分を判定して対応するliftを使う
    let condKey = null;
    if     (prevRow.diff <= -2000) condKey = '凹み_2000以上';
    else if(prevRow.diff <= -1000) condKey = '凹み_1000_2000';
    else if(prevRow.diff <=  -500) condKey = '凹み_500_1000';
    else if(prevRow.diff <      0) condKey = '凹み_0_500';
    else if(prevRow.diff >=   500) condKey = 'プラス500以上';
    else                           condKey = 'プラス';

    if(condKey){
      const {lift, ok, count, avg:cAvg} = getCondLift(condKey);
      const pts = liftToScore(lift, ok);
      score += pts;
      const label = condKey==='凹み_2000以上' ? '前日 -2000以下'
                  : condKey==='凹み_1000_2000'? '前日 -1000〜-2000'
                  : condKey==='凹み_500_1000' ? '前日 -500〜-1000'
                  : condKey==='凹み_0_500'    ? '前日 0〜-500'
                  : condKey==='プラス500以上'  ? '前日 +500以上'
                  :                             '前日プラス';
      reasons.push({
        label:`前日差枚（${label}）`,
        val:`前日${prevRow.diff>=0?'+':''}${prevRow.diff}枚 → 翌日avg${cAvg>=0?'+':''}${cAvg}枚（ベース比${lift>=0?'+':''}${lift}）`,
        pts, lift,
        note: !ok ? `※サンプル${count}件・参考値` : null
      });
    }

    // 前日RB先行不発：差枚マイナス かつ RB>BB
    if(prevRow.isRBLead && prevRow.diff < 0){
      const {lift, ok, count, avg:cAvg} = getCondLift('RB先行');
      const pts = liftToScore(lift, ok);
      score += pts;
      reasons.push({
        label:'前日RB先行不発',
        val:`翌日avg${cAvg>=0?'+':''}${cAvg}枚（ベース比${lift>=0?'+':''}${lift}）`,
        pts, lift,
        note: !ok ? `※サンプル${count}件・参考値` : null
      });
    }

    // 連続凹み
    const prevPrevDay = new Date(prevDay);
    prevPrevDay.setDate(prevPrevDay.getDate()-1);
    const pp1 = prevPrevDay.toISOString().slice(0,10).replace(/-/g,'/');
    const pp2 = prevPrevDay.toISOString().slice(0,10);
    const prevPrevRow = rows.find(r=>r.tai===tai.tai&&(r.dateStr===pp1||r.dateStr===pp2));
    if(prevRow.diff < 0 && prevPrevRow && prevPrevRow.diff < 0){
      const {lift, ok, count, avg:cAvg} = getCondLift('連続凹み');
      const pts = liftToScore(lift, ok);
      score += pts;
      reasons.push({
        label:'連続凹み（2日以上）',
        val:`翌日avg${cAvg>=0?'+':''}${cAvg}枚（ベース比${lift>=0?'+':''}${lift}）`,
        pts, lift,
        note: !ok ? `※サンプル${count}件・参考値` : null
      });
    }

    // 特定日前日の凹み
    if(isSpecial && prevRow.diff < 0){
      const {lift, ok, count, avg:cAvg} = getCondLift('特定日前日');
      const pts = liftToScore(lift, ok);
      score += pts;
      reasons.push({
        label:'特定日×前日凹み',
        val:`翌日avg${cAvg>=0?'+':''}${cAvg}枚（ベース比${lift>=0?'+':''}${lift}）`,
        pts, lift,
        note: !ok ? `※サンプル${count}件・参考値` : null
      });
    }

  } else {
    // 前日データなし：台の長期傾向のみ
    reasons.push({label:'前日データ', val:'なし（長期成績のみ参照）', pts:0});
  }

  // ④ 特定日ボーナス（特定日自体の強さをliftで評価）
  if(isSpecial){
    const spDayInfo = G.dayStats.filter(d=>SP.includes(d.day));
    if(spDayInfo.length && baseline){
      const spAvg = round1(avg(spDayInfo.map(d=>d.avg)));
      const lift = round1(spAvg - baseline.avg);
      const pts = liftToScore(lift, true);
      if(pts !== 0){
        score += pts;
        reasons.push({label:'特定日ボーナス', val:`特定日平均${spAvg>=0?'+':''}${spAvg}枚（ベース比${lift>=0?'+':''}${lift}）`, pts, lift});
      }
    }
  }

  return {score, reasons};
}

// ====== 今日の狙い台 3層絞り込み ======

let targetDate = null;
let selectedModel = null;

// ====== サマリーバナー ======
function updateSummaryBanner({ verdict, verdictColor, isSpecial, dayScore, day, wday, dayInfo, wdayAvg }) {
  const el = document.getElementById('summaryBanner');
  if(!el) return;

  // 背景グラデーションと絵文字
  const isHigh   = verdict.startsWith('✅');
  const isMid    = verdict.startsWith('🟡');
  const isLow    = verdict.startsWith('❌');
  const bg = isHigh ? 'linear-gradient(135deg,#0d2b0d 0%,#0a1f14 100%)'
           : isMid  ? 'linear-gradient(135deg,#1f1a00 0%,#1a1200 100%)'
           : 'linear-gradient(135deg,#1f0d0d 0%,#180808 100%)';
  const borderColor = isHigh ? 'var(--plus)' : isMid ? 'var(--accent)' : 'var(--minus)';
  const accentSize = isHigh ? '3px' : '2px';

  // 判定文字 整形（絵文字と文字を分離）
  const verdictText = verdict.replace(/^[✅🟡⬜❌]\s*/,'');

  // サブ情報
  const badges = [];
  badges.push(isSpecial ? '⭐ 特定日' : '通常日');
  badges.push(`${day}日（${wday}）`);
  if(dayInfo) badges.push(`過去平均 ${dayInfo.avg>=0?'+':''}${dayInfo.avg}枚`);
  if(wdayAvg !== null) badges.push(`${wday}曜日平均 ${wdayAvg>=0?'+':''}${wdayAvg}枚`);

  el.style.display = 'block';
  el.innerHTML = `
    <div class="summary-banner" style="background:${bg};border:${accentSize} solid ${borderColor}">
      <div class="summary-banner-verdict" style="color:${verdictColor}">${verdictText}</div>
      <div class="summary-banner-sub">
        ${badges.map(b=>`<span class="summary-badge">${b}</span>`).join('')}
      </div>
      ${dayInfo ? `
      <div class="summary-banner-detail">
        プラス台率 <strong>${dayInfo.plusRate}%</strong> &nbsp;|&nbsp;
        サンプル <strong>${dayInfo.total}件</strong>
        ${isSpecial ? '&nbsp;|&nbsp; ⭐ 特定日として分析中' : ''}
      </div>` : ''}
    </div>
  `;
}

function renderLayer1() {
  if(!G.raw.length && !G._precomputed){
    document.getElementById('layer1Result').innerHTML='<div class="empty-msg">先にデータを読み込んでください</div>';
    return;
  }

  // 集計済みモード：todayAnalysisを使う
  if(G._precomputed && G.todayAnalysis) {
    const ta = G.todayAnalysis;
    const wdays = ['日','月','火','水','木','金','土'];
    const wday = wdays[ta.weekday];
    const dayColor = ta.dayScore >= 3 ? 'var(--plus)' : ta.dayScore >= 2 ? 'var(--accent)' : ta.dayScore >= 1 ? 'var(--muted)' : 'var(--minus)';
    const verdictColor = ta.verdict.startsWith('✅') ? 'var(--plus)' : ta.verdict.startsWith('🟡') ? 'var(--accent)' : ta.verdict.startsWith('⬜') ? 'var(--muted)' : 'var(--minus)';
    targetDate = new Date(ta.date);
    selectedModel = null;
    document.getElementById('layer1Result').innerHTML = `
      <div style="margin-bottom:12px">
        <div style="font-family:'Share Tech Mono',monospace;font-size:22px;font-weight:700;color:var(--accent)">${ta.date}（${wday}）</div>
        <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
          <span class="badge ${ta.isSpecial?'badge-special':'badge-normal'}">${ta.isSpecial?'⭐ 特定日':'通常日'}</span>
          <span class="badge badge-normal" style="color:${dayColor}">${ta.dayJudge}</span>
        </div>
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:12px;margin-bottom:10px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:8px">${ta.day}日の過去成績</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:8px">
          <div style="text-align:center">
            <div style="font-size:10px;color:var(--muted)">平均差枚</div>
            <div style="font-size:18px;font-weight:700;color:${ta.dayInfo&&ta.dayInfo.avg>=0?'var(--plus)':'var(--minus)'}">${ta.dayInfo?`${ta.dayInfo.avg>=0?'+':''}${ta.dayInfo.avg}`:'—'}</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:10px;color:var(--muted)">プラス台率</div>
            <div style="font-size:18px;font-weight:700;color:var(--accent)">${ta.dayInfo?`${ta.dayInfo.plusRate}%`:'—'}</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:10px;color:var(--muted)">サンプル数</div>
            <div style="font-size:18px;font-weight:700;color:var(--accent3)">${ta.dayInfo?`${ta.dayInfo.total}件`:'—'}</div>
          </div>
        </div>
        ${ta.wdayAvg!==null?`<div style="font-size:11px;color:var(--muted)">${wday}曜日の平均差枚：<span style="color:${ta.wdayAvg>=0?'var(--plus)':'var(--minus)'};font-weight:700">${ta.wdayAvg>=0?'+':''}${ta.wdayAvg}枚</span></div>`:''}
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:12px;color:var(--muted);margin-bottom:4px">総合判定</div>
        <div style="font-size:20px;font-weight:900;color:${verdictColor}">${ta.verdict}</div>
      </div>
      ${ta.dayScore>=1||ta.isSpecial?`<button class="btn" onclick="renderLayer2()" style="margin-top:12px">次へ → 機種・配分傾向を見る</button>`:''}
    `;
    updateSummaryBanner({ verdict:ta.verdict, verdictColor, isSpecial:ta.isSpecial, dayScore:ta.dayScore, day:ta.day, wday, dayInfo:ta.dayInfo, wdayAvg:ta.wdayAvg });
    document.getElementById('layer2Card').style.display = 'none';
    document.getElementById('layer3Card').style.display = 'none';
    return;
  }

  const val = document.getElementById('diagDate').value;
  if(!val) return;
  const [y,m,dd] = val.split('-').map(Number);
  targetDate = new Date(y, m-1, dd);
  selectedModel = null;

  const day = targetDate.getDate();
  const wdays = ['日','月','火','水','木','金','土'];
  const wday = wdays[targetDate.getDay()];
  const SP = getSpecial();
  const isSpecial = SP.includes(day);
  const dayInfo = G.dayStats.find(x => x.day === day);
  const baseline = G.nextStats['__baseline'];

  // 日付の強さ判定
  let dayJudge = '', dayColor = '', dayScore = 0;
  if(dayInfo && baseline) {
    const lift = round1(dayInfo.avg - baseline.avg);
    if(dayInfo.avg > 100)      { dayJudge='🔥 かなり強い日'; dayColor='var(--plus)';    dayScore=3; }
    else if(dayInfo.avg > 0)   { dayJudge='🟡 やや強い日';   dayColor='var(--accent)';  dayScore=2; }
    else if(dayInfo.avg > -100){ dayJudge='⬜ 普通の日';     dayColor='var(--muted)';   dayScore=1; }
    else                       { dayJudge='❄️ 弱い日';       dayColor='var(--minus)';   dayScore=0; }
  }

  // 同じ日付の過去実績
  const rows = filteredRows();
  const sameDayRows = rows.filter(r => r.day === day);
  const sameDayDates = [...new Set(sameDayRows.map(r => r.dateStr))].sort().reverse().slice(0,5);

  // 同じ曜日の過去成績
  const wdayRows = rows.filter(r => r.weekday === targetDate.getDay());
  const wdayAvg = wdayRows.length ? round1(wdayRows.reduce((a,r)=>a+r.diff,0)/wdayRows.length) : null;

  const verdict = (isSpecial && dayScore >= 2) ? '✅ 狙う価値あり' :
                  (isSpecial && dayScore >= 1)  ? '🟡 条件次第' :
                  (!isSpecial && dayScore >= 2) ? '🟡 非特定日だが強い傾向' :
                  (!isSpecial && dayScore >= 1) ? '⬜ 普通・慎重に' :
                                                  '❌ 見送りを推奨';
  const verdictColor = verdict.startsWith('✅') ? 'var(--plus)' :
                       verdict.startsWith('🟡') ? 'var(--accent)' :
                       verdict.startsWith('⬜') ? 'var(--muted)' : 'var(--minus)';

  document.getElementById('layer1Result').innerHTML = `
    <div style="margin-bottom:12px">
      <div style="font-family:'Share Tech Mono',monospace;font-size:22px;font-weight:700;color:var(--accent)">${val}（${wday}）</div>
      <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
        <span class="badge ${isSpecial?'badge-special':'badge-normal'}">${isSpecial?'⭐ 特定日':'通常日'}</span>
        ${dayInfo?`<span class="badge badge-normal" style="color:${dayColor}">${dayJudge}</span>`:''}
      </div>
    </div>

    <div style="background:var(--bg3);border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="font-size:11px;color:var(--muted);margin-bottom:8px">${day}日の過去成績</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:8px">
        <div style="text-align:center">
          <div style="font-size:10px;color:var(--muted)">平均差枚</div>
          <div style="font-size:18px;font-weight:700;color:${dayInfo&&dayInfo.avg>=0?'var(--plus)':'var(--minus)'}">${dayInfo?`${dayInfo.avg>=0?'+':''}${dayInfo.avg}`:'—'}</div>
        </div>
        <div style="text-align:center">
          <div style="font-size:10px;color:var(--muted)">プラス台率</div>
          <div style="font-size:18px;font-weight:700;color:var(--accent)">${dayInfo?`${dayInfo.plusRate}%`:'—'}</div>
        </div>
        <div style="text-align:center">
          <div style="font-size:10px;color:var(--muted)">サンプル数</div>
          <div style="font-size:18px;font-weight:700;color:var(--accent3)">${dayInfo?`${dayInfo.total}件`:'—'}</div>
        </div>
      </div>
      ${wdayAvg!==null?`<div style="font-size:11px;color:var(--muted)">${wday}曜日の平均差枚：<span style="color:${wdayAvg>=0?'var(--plus)':'var(--minus)'};font-weight:700">${wdayAvg>=0?'+':''}${wdayAvg}枚</span>（${wdayRows.length}件）</div>`:''}
    </div>

    ${sameDayDates.length?`
    <div style="background:var(--bg3);border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="font-size:11px;color:var(--muted);margin-bottom:6px">直近の同日実績</div>
      ${sameDayDates.map(ds=>{
        const dayRows = sameDayRows.filter(r=>r.dateStr===ds);
        const total = round1(dayRows.reduce((a,r)=>a+r.diff,0));
        const plusCount = dayRows.filter(r=>r.diff>0).length;
        return `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);font-size:12px">
          <span style="color:var(--muted)">${ds}</span>
          <span style="color:${total>=0?'var(--plus)':'var(--minus)'};font-weight:700">${total>=0?'+':''}${total}枚</span>
          <span style="color:var(--accent3)">${plusCount}/${dayRows.length}台プラス</span>
        </div>`;
      }).join('')}
    </div>`:''}

    <div style="background:var(--bg3);border-radius:8px;padding:14px;text-align:center">
      <div style="font-size:12px;color:var(--muted);margin-bottom:4px">総合判定</div>
      <div style="font-size:20px;font-weight:900;color:${verdictColor}">${verdict}</div>
    </div>

    ${dayScore>=1||isSpecial?`
    <button class="btn" onclick="renderLayer2()" style="margin-top:12px">次へ → 機種・配分傾向を見る</button>`:''}
  `;

  document.getElementById('layer2Card').style.display = 'none';
  document.getElementById('layer3Card').style.display = 'none';

  // サマリーバナーを更新
  updateSummaryBanner({ verdict, verdictColor, isSpecial, dayScore, day, wday, dayInfo, wdayAvg });
}

function renderLayer2() {
  if(!targetDate && !G._precomputed) return;

  // 集計済みモード：todayAnalysisのmodelStrengthを使う
  if(G._precomputed && G.todayAnalysis) {
    const ta = G.todayAnalysis;
    const condLabel = ta.isSpecial ? '特定日' : '通常日';
    const modelStrength = ta.modelStrength || [];
    const goodModels = modelStrength.filter(m => m.label === '有力' || m.label === '対抗');
    const topModel = modelStrength[0] || null;

    document.getElementById('layer2Card').style.display = 'block';
    document.getElementById('layer2Result').innerHTML = `
      <div style="font-size:12px;font-weight:700;color:var(--accent3);margin-bottom:10px">${condLabel}の配分傾向まとめ</div>
      ${modelStrength.length ? `
      <div style="margin-bottom:12px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">🎮 機種別強さ一覧（${condLabel}）</div>
        ${modelStrength.map(m => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:var(--bg3);border-radius:6px;margin-bottom:4px;cursor:pointer"
               onclick="renderLayer3('${m.model}')">
            <div>
              <span style="font-size:13px;font-weight:700;color:var(--text)">${m.model}</span>
              <span style="font-size:10px;color:var(--muted);margin-left:8px">${m.count}件</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:12px;font-weight:700;color:${m.avg>=0?'var(--plus)':'var(--minus)'}">${m.avg>=0?'+':''}${m.avg}枚</span>
              <span style="font-size:11px;font-weight:700;color:${m.label==='有力'?'var(--plus)':m.label==='対抗'?'var(--accent)':'var(--muted)'}">${m.label}</span>
            </div>
          </div>`).join('')}
        <div style="font-size:11px;color:var(--muted);margin-top:8px">👆 機種をタップすると候補台を表示します</div>
      </div>` : '<div class="empty-msg">データ不足</div>'}
    `;
    return;
  }

  if(!targetDate) return;
  const day = targetDate.getDate();
  const SP = getSpecial();
  const isSpecial = SP.includes(day);
  const condLabel = isSpecial ? '特定日' : '通常日';
  const conditionType = isSpecial ? 'sp' : 'nm';
  const allRows = filteredRows();
  const rows = getRowsByCondition(allRows, conditionType); // 条件内行（ゾロ目等で使用）

  // 3関数で第2段階を計算
  const modelStrength  = calcModelStrength(allRows, conditionType);
  const suefStrength   = calcSuefStrength(allRows, conditionType);
  const clusterResult  = calcClusterStrength(allRows, conditionType);

  const topModel    = modelStrength[0] || null;
  const goodModels  = modelStrength.filter(m => m.label === '有力' || m.label === '対抗');
  const topSuef     = suefStrength[0] || null;
  const strongSuefs = suefStrength.filter(s => s.lift > 50 && s.sampleState !== '不足');
  const { clusterRate, style:clStyle, sampleState:clSampleState, label:clLabel, rbGoodInCluster } = clusterResult;
  const totalDays = clusterResult.sampleDays;

  // ④ 前日凹み上げ傾向
  const rowsWithPrev = allRows.filter(r => {
    const pd = new Date(r.date); pd.setDate(pd.getDate()-1);
    const pds = `${pd.getFullYear()}-${String(pd.getMonth()+1).padStart(2,'0')}-${String(pd.getDate()).padStart(2,'0')}`;
    return allRows.some(p => p.tai===r.tai && p.model===r.model && p.dateStr===pds && p.diff <= -1000);
  });
  const prevUpRows = rowsWithPrev.filter(r => r.diff > 0);
  const prevUpRate = rowsWithPrev.length >= 5
    ? round1(prevUpRows.length / rowsWithPrev.length * 100) : null;

  // ⑤ ゾロ目傾向
  const zoroRows    = rows.filter(r => r.isZoro);
  const nonZoroRows = rows.filter(r => !r.isZoro);
  const zoroAvg    = zoroRows.length    >= 3 ? round1(zoroRows.reduce((a,r)=>a+r.diff,0)/zoroRows.length)       : null;
  const nonZoroAvg = nonZoroRows.length >= 3 ? round1(nonZoroRows.reduce((a,r)=>a+r.diff,0)/nonZoroRows.length) : null;
  const zoroStrong  = zoroAvg !== null && nonZoroAvg !== null && zoroAvg > nonZoroAvg + 100;

  // ===== 結論カードの生成 =====
  const conclusions = [];

  // 機種（calcModelStrength）
  if(topModel && topModel.label !== '傾向薄い') {
    const rbNote = topModel.rb4GoodRate !== null && topModel.rb4GoodRate >= 20 ? '・RB高設定寄り台あり'
      : topModel.rb3GoodRate !== null && topModel.rb3GoodRate >= 40 ? '・RB中高設定台あり' : '';
    const sampleNote = topModel.sampleState !== '通常評価' ? `（${topModel.sampleState}）` : '';
    conclusions.push({
      icon:'🎰', label:'狙い機種',
      verdict: `<span style="color:var(--plus);font-weight:900">${topModel.model}</span>　<span style="font-size:11px;color:var(--accent)">${topModel.label}${sampleNote}</span>`,
      detail:  `${condLabel}平均 ${topModel.avgDiff>=0?'+':''}${topModel.avgDiff}枚 / 出率${topModel.mechRitu}%${rbNote}`,
      sub:     goodModels.length > 1 ? `対抗：${goodModels.slice(1,3).map(m=>m.model+'('+m.label+')').join('・')}` : null
    });
  } else if(topModel) {
    conclusions.push({
      icon:'🎰', label:'狙い機種',
      verdict: `${condLabel}での機種差は小さい`,
      detail:  topModel ? `最高は${topModel.model}（スコア${topModel.score}）、明確な傾向なし` : 'データ不足',
      sub: null
    });
  }

  // 配分スタイル（calcClusterStrength）
  if(clusterRate !== null) {
    const styleIcon  = clStyle === '並び型' ? '🔗' : clStyle === '混合型' ? '↔️' : '🎲';
    const styleColor = clStyle === '並び型' ? 'var(--plus)' : clStyle === '混合型' ? 'var(--accent)' : 'var(--accent3)';
    const advice = clStyle === '並び型'
      ? '高設定台は3台以上まとまって上がる傾向。両隣の動きも重視'
      : clStyle === '混合型' ? '並びあり・単品ありの混合。周辺台の動きを見ながら判断'
      : '高設定が散って入る傾向。台単体の数値を重視する';
    const rbClusterNote = rbGoodInCluster !== null ? `　クラスター内RB良好${rbGoodInCluster}%` : '';
    conclusions.push({
      icon: styleIcon, label:'配分スタイル（参考）',
      verdict: `<span style="color:${styleColor};font-weight:900">${clStyle}</span>（並び発生率 ${clusterRate}%）`,
      detail:  advice + rbClusterNote,
      sub:     `${totalDays}日・${clLabel}・推定精度は低め`
    });
  }

  // 末尾（calcSuefStrength）
  if(strongSuefs.length > 0) {
    const top3 = strongSuefs.slice(0,3);
    conclusions.push({
      icon:'🔢', label:'末尾傾向',
      verdict: `末尾 <span style="color:var(--plus);font-weight:900">${top3.map(s=>s.suef).join('・')}</span> が強い`,
      detail:  top3.map(s=>`末尾${s.suef}：lift${s.lift>=0?'+':''}${s.lift}枚 / ${s.label}`).join('　'),
      sub:     `${condLabel}baseline比・${topSuef?.sampleState||''}`
    });
  } else {
    conclusions.push({
      icon:'🔢', label:'末尾傾向',
      verdict: '末尾による明確な傾向なし',
      detail:  topSuef ? `最高は末尾${topSuef.suef}（lift${topSuef.lift>=0?'+':''}${topSuef.lift}枚・${topSuef.label}）` : 'サンプル不足',
      sub: null
    });
  }

  // 前日凹み上げ
  if(prevUpRate !== null) {
    const prevColor   = prevUpRate >= 50 ? 'var(--plus)' : prevUpRate >= 35 ? 'var(--accent)' : 'var(--muted)';
    const prevVerdict = prevUpRate >= 50 ? '前日凹み上げが多い' : prevUpRate >= 35 ? 'やや前日凹み上げあり' : '前日凹み上げは少ない';
    conclusions.push({
      icon:'📈', label:'前日凹み上げ',
      verdict: `<span style="color:${prevColor};font-weight:900">${prevVerdict}</span>（${prevUpRate}%）`,
      detail:  prevUpRate >= 40
        ? '前日-1000枚以下の台が翌日プラスになるケースが多い。前日大負け台を優先候補に'
        : '前日凹みからの上げは少ない。別根拠を重視する',
      sub: `${rowsWithPrev.length}件中${prevUpRows.length}件がプラス転換`
    });
  }

  // ゾロ目
  if(zoroStrong) {
    conclusions.push({
      icon:'✨', label:'ゾロ目傾向',
      verdict: `<span style="color:var(--plus);font-weight:900">ゾロ目台が強い</span>`,
      detail:  `ゾロ目平均 ${zoroAvg>=0?'+':''}${zoroAvg}枚 vs 非ゾロ目 ${nonZoroAvg>=0?'+':''}${nonZoroAvg}枚（差 ${round1(zoroAvg-nonZoroAvg)}枚）`,
      sub:     `${zoroRows.length}件のゾロ目台より`
    });
  }

  // 角台傾向（席配置マスター連携）
  const l2Store = (G.raw && G.raw.length) ? G.raw[0].store : '';
  const { cornerTais: l2Corner, edgeTais: l2Edge, hasLayout: l2HasLayout } = getLayoutCornerTais(l2Store);
  if(l2HasLayout) {
    const ct = calcCornerTendency(allRows, l2Corner, l2Edge);
    if(ct) {
      const cornerColor  = ct.isCornerStrong ? 'var(--plus)' : ct.cornerLift >= 30 ? 'var(--accent)' : 'var(--muted)';
      const cornerVerdict = ct.isCornerStrong
        ? `角台が強い（全体比 +${ct.cornerLift}枚）`
        : ct.cornerLift >= 30 ? `角台がやや強い（+${ct.cornerLift}枚）`
        : `角台の明確な傾向なし（${ct.cornerLift>=0?'+':''}${ct.cornerLift}枚）`;
      const edgeNote = ct.edgeLift !== null ? `　端台:${ct.edgeLift>=0?'+':''}${ct.edgeLift}枚` : '';
      conclusions.push({
        icon: '📐', label: '角台傾向（席配置連携）',
        verdict: `<span style="color:${cornerColor};font-weight:900">${cornerVerdict}</span>`,
        detail:  `角台平均 ${ct.cornerAvg>=0?'+':''}${ct.cornerAvg}枚 / 全体平均 ${ct.baseAvg>=0?'+':''}${ct.baseAvg}枚${edgeNote}`,
        sub:     `${l2Corner.size}台が角台・${l2Edge.size}台が端台として配置済み`
      });
    }
  }

  document.getElementById('layer2Result').innerHTML = `
    <div style="margin-bottom:14px">
      <div style="font-size:12px;font-weight:700;color:var(--accent);margin-bottom:10px">
        ${condLabel}の配分傾向まとめ
      </div>
      ${conclusions.map(c => `
        <div style="background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid var(--accent)">
          <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">
            <span style="font-size:10px;color:var(--muted);min-width:72px;flex-shrink:0">${c.icon} ${c.label}</span>
            <span style="font-size:13px">${c.verdict}</span>
          </div>
          <div style="font-size:11px;color:var(--muted);padding-left:80px">${c.detail}</div>
          ${c.sub ? `<div style="font-size:10px;color:var(--border);padding-left:80px;margin-top:2px">${c.sub}</div>` : ''}
        </div>`).join('')}
    </div>

    <div style="margin-bottom:12px">
      <div style="font-size:11px;color:var(--muted);margin-bottom:6px">📊 機種別強さ一覧（${condLabel}）</div>
      ${modelStrength.slice(0,8).map((m,i) => {
        const barW = Math.min(Math.max(m.score / 8 * 100, 0), 100);
        const barColor = m.label==='有力'?'var(--plus)':m.label==='対抗'?'var(--accent)':'var(--muted)';
        const labelColor = m.label==='有力'?'var(--plus)':m.label==='対抗'?'var(--accent)':'var(--muted)';
        const rb3 = m.rb3GoodRate !== null ? `RB3+:${m.rb3GoodRate}%` : '';
        const rb4 = m.rb4GoodRate !== null ? `RB4+:${m.rb4GoodRate}%` : '';
        const cov = calcModelDataCoverage(m.model, allRows);
        const covColor = cov.label==='高'?'var(--plus)':cov.label==='中'?'var(--accent)':cov.label==='低'?'var(--muted)':'#555';
        return `<div style="margin-bottom:6px">
          <div style="display:flex;justify-content:space-between;margin-bottom:2px">
            <span style="font-size:11px;font-weight:${i<2?'700':'400'};color:${i===0?'var(--accent)':'var(--text)'}">${i===0?'👑 ':i===1?'★ ':''} ${m.model}</span>
            <div style="display:flex;gap:6px;align-items:center">
              ${rb4?`<span style="font-size:9px;color:var(--plus)">${rb4}</span>`:''}
              ${rb3&&!rb4?`<span style="font-size:9px;color:var(--muted)">${rb3}</span>`:''}
              <span style="font-size:9px;color:${covColor}" title="データ信頼度: ${cov.taiCount}台×${cov.dayCount}日 ${cov.actual}/${cov.maxPossible}件">${cov.stars}</span>
              <span style="font-size:11px;font-weight:700;color:${m.avgDiff>=0?'var(--plus)':'var(--minus)'}">${m.avgDiff>=0?'+':''}${m.avgDiff}枚</span>
              <span style="font-size:10px;color:${labelColor};font-weight:700">${m.label}</span>
            </div>
          </div>
          <div style="height:3px;background:var(--bg4);border-radius:2px">
            <div style="height:3px;width:${barW}%;background:${barColor};border-radius:2px"></div>
          </div>
        </div>`;
      }).join('')}
    </div>

    <div style="font-size:11px;color:var(--muted);margin-bottom:8px">狙う機種を選んでください：</div>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:4px">
      ${modelStrength.map(m=>`
        <button onclick="selectModel('${m.model}')" id="modelBtn_${m.model.replace(/[^\w]/g,'_')}"
          style="background:var(--bg3);color:var(--text);border:1px solid var(--border);border-radius:20px;padding:6px 14px;font-size:12px;cursor:pointer;transition:all .2s">
          ${m.model}
        </button>`).join('')}
    </div>
  `;

  document.getElementById('layer2Card').style.display = 'block';
  document.getElementById('layer3Card').style.display = 'none';
  document.getElementById('layer2Card').scrollIntoView({behavior:'smooth', block:'start'});
}

function selectModel(model) {
  selectedModel = model;
  document.querySelectorAll('[id^="modelBtn_"]').forEach(btn => {
    btn.style.background = 'var(--bg3)';
    btn.style.color = 'var(--text)';
    btn.style.borderColor = 'var(--border)';
  });
  const btnId = 'modelBtn_' + model.replace(/[^\w]/g,'_');
  const btn = document.getElementById(btnId);
  if(btn){
    btn.style.background = 'var(--accent)';
    btn.style.color = '#000';
    btn.style.borderColor = 'var(--accent)';
  }
  renderLayer3(model);
}

function renderLayer3(model) {
  if(!model) return;

  // 集計済みモード：todayAnalysisのtopTargetsを使う
  if(G._precomputed && G.todayAnalysis) {
    const ta = G.todayAnalysis;
    const targets = ta.topTargets.filter(t => t.model === model);
    const condLabel = ta.isSpecial ? '特定日' : '通常日';

    document.getElementById('layer3Card').style.display = 'block';
    document.getElementById('layer3Filter').innerHTML = '';

    if(!targets.length) {
      document.getElementById('layer3Result').innerHTML = '<div class="empty-msg">この機種のデータがありません</div>';
      return;
    }

    const rankColor = r => r.rank==='本命'?'var(--plus)':r.rank==='対抗'?'var(--accent)':r.rank==='保留'?'var(--muted)':'var(--minus)';
    const rankIcon  = r => r.rank==='本命'?'🎯':r.rank==='対抗'?'★':r.rank==='保留'?'△':'⚠️';

    const html = targets.map((t, idx) => {
      const rc = rankColor(t);
      const ri = rankIcon(t);
      const ref = ta.isSpecial ? t.spAvg : t.nmAvg;
      return `
      <div style="background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:12px;border-left:4px solid ${rc}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
          <div>
            <span style="font-size:18px;font-weight:900;color:var(--text)">${t.tai}番</span>
            <span style="font-size:10px;color:var(--muted);margin-left:6px">${t.count}件 / 平均${t.avgG}G/日</span>
          </div>
          <div style="text-align:right">
            <div style="font-size:14px;font-weight:900;color:${rc}">${ri} ${t.rank}</div>
            <div style="font-size:10px;color:var(--muted)">スコア ${t.totalScore}pt</div>
            <button class="btn" onclick="selectLayer3CandidatePrecomputed(${idx},'${model}')" style="margin-top:6px;padding:4px 8px;font-size:10px">この台で設定推測</button>
          </div>
        </div>
        <div style="background:var(--bg4);border-radius:6px;padding:8px;margin-bottom:6px">
          <div style="font-size:10px;color:var(--accent);font-weight:700;margin-bottom:5px">📊 スコア根拠</div>
          ${(t.reasons||[]).map(r=>`
            <div style="display:flex;justify-content:space-between;margin-bottom:3px">
              <span style="font-size:11px;color:var(--muted)">${r.label}</span>
              <span style="font-size:12px;font-weight:700;color:${r.pts>0?'var(--plus)':r.pts<0?'var(--minus)':'var(--muted)'}">${r.pts>0?'+':''}${r.pts}pt ${r.val}</span>
            </div>`).join('')}
        </div>
        ${t.prevRow?`
        <div style="font-size:11px;color:var(--muted);padding:5px 8px;background:var(--bg4);border-radius:6px;margin-bottom:6px">
          前日：<span style="color:${t.prevRow.diff>=0?'var(--plus)':'var(--minus)'};font-weight:700">${t.prevRow.diff>=0?'+':''}${t.prevRow.diff}枚</span>
          　BB${t.prevRow.bb} RB${t.prevRow.rb}
          ${t.prevRow.isRBLead?'<span style="color:var(--accent3);margin-left:4px">RB先行</span>':''}
        </div>`:''}
        <div style="display:flex;gap:10px;font-size:11px;color:var(--muted);padding:5px 8px;background:var(--bg4);border-radius:6px;flex-wrap:wrap">
          <span>${condLabel}平均 <b style="color:${ref!==null&&ref>=0?'var(--plus)':'var(--minus)'}">${ref!==null?(ref>=0?'+':'')+ref+'枚':'—'}</b></span>
          <span>全体平均 <b style="color:${t.avg>=0?'var(--plus)':'var(--minus)'}">${t.avg>=0?'+':''}${t.avg}枚</b></span>
          ${t.bayesProbSp!==null?`<span>P(設定4+) <b style="color:var(--accent3)">${ta.isSpecial?t.bayesProbSp:t.bayesProbNm}%</b></span>`:''}
        </div>
      </div>`;
    }).join('');

    document.getElementById('layer3Result').innerHTML = html || '<div class="empty-msg">候補台がありません</div>';
    document.getElementById('layer3Card').scrollIntoView({behavior:'smooth', block:'start'});
    return;
  }

  if(!targetDate || !model) return;
  const day = targetDate.getDate();
  const SP  = getSpecial();
  const isSpecial = SP.includes(day);
  const baseline  = G.nextStats['__baseline'];
  const rows      = filteredRows();
  const allRows   = filteredRows();
  const condLabel = isSpecial ? '特定日' : '通常日';
  const conditionType = isSpecial ? 'sp' : 'nm';

  const modelStrength = calcModelStrength(allRows, conditionType);
  const suefStrength  = calcSuefStrength(allRows, conditionType);
  const clusterResult = calcClusterStrength(allRows, conditionType);

  // 角台データを席配置マスターから取得
  const layoutStore = (G.raw && G.raw.length) ? G.raw[0].store : '';
  const { cornerTais, edgeTais, hasLayout } = getLayoutCornerTais(layoutStore);
  const cornerTendency = hasLayout ? calcCornerTendency(allRows, cornerTais, edgeTais) : null;

  const context = { isSpecial, baseline, rows, SP, model, targetDate, modelStrength, suefStrength, clusterResult,
                    cornerTais, edgeTais, cornerTendency };

  const taiList = G.taiDetail.filter(t => t.model === model);
  if(!taiList.length) {
    document.getElementById('layer3Result').innerHTML = '<div class="empty-msg">この機種のデータがありません</div>';
    document.getElementById('layer3Card').style.display = 'block';
    return;
  }

  // 機種のデータ信頼度を計算
  const coverage = calcModelDataCoverage(model, allRows);
  const covColor = coverage.label==='高'?'var(--plus)':coverage.label==='中'?'var(--accent)':coverage.label==='低'?'var(--muted)':'#555';

  const scored = taiList.map(t => {
    const result = calcTaiStrength(t, context);
    return { ...t, ...result };
  }).sort((a, b) => b.totalScore - a.totalScore);
  G.layer3Scored = scored;
  G.layer3SelectionMeta = {
    store: currentStore === 'all' ? (G.raw[0]?.store || 'all') : currentStore,
    model,
    targetDate: targetDate ? targetDate.toISOString().slice(0,10) : null,
    isSpecial
  };

  // ランク色・アイコン
  const rankColor = r => r.rank==='本命'?'var(--plus)':r.rank==='対抗'?'var(--accent)':r.rank==='保留'?'var(--muted)':'var(--minus)';
  const rankIcon  = r => r.rank==='本命'?'🎯':r.rank==='対抗'?'★':r.rank==='保留'?'△':'⚠️';

  // warningフラグ色（levelベース）
  const warnColor = f => f.level==='strong' ? 'var(--minus)' : 'var(--muted)';
  const warnBg    = f => f.level==='strong' ? 'rgba(255,60,60,0.08)' : 'rgba(255,255,255,0.03)';
  const warnBorder= f => f.level==='strong' ? 'rgba(255,60,60,0.25)' : 'rgba(255,255,255,0.08)';

  // 機種信頼度バナー
  const coverageBanner = `
    <div style="background:var(--bg3);border-radius:8px;padding:10px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-size:11px;color:var(--muted)">データ信頼度</div>
        <div style="font-size:13px;font-weight:700;color:${covColor}">${coverage.stars} ${coverage.label}</div>
      </div>
      <div style="text-align:right;font-size:10px;color:var(--muted)">
        <div>${coverage.taiCount}台 × ${coverage.dayCount}日</div>
        <div>${coverage.actual}件 / 最大${coverage.maxPossible}件</div>
        <div style="color:${covColor}">カバー率 ${coverage.coverage}%</div>
      </div>
    </div>
  `;

  const html = scored.map((t, idx) => {
    const rc  = rankColor(t);
    const ri  = rankIcon(t);
    const ref = isSpecial ? t.spAvg : t.nmAvg;

    // strongフラグのみ表示（weakは現地確認ポイントに集約）
    const strongFlags = t.warningFlags.filter(f => f.level === 'strong');
    const weakFlags   = t.warningFlags.filter(f => f.level === 'weak');

    return `
    <div style="background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:12px;border-left:4px solid ${rc}">

      <!-- ① 台番号 + ランク -->
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
        <div>
          <span style="font-size:18px;font-weight:900;color:var(--text)">${t.tai}番</span>
          <span style="font-size:10px;color:var(--muted);margin-left:6px">${t.count}件 / 平均${t.avgG}G/日</span>
        </div>
        <div style="text-align:right">
          <div style="font-size:14px;font-weight:900;color:${rc}">${ri} ${t.rank}</div>
          <div style="font-size:10px;color:var(--muted)">数値${t.valueScore}pt + 配分${t.configScore}pt = 計${t.totalScore}pt</div>
          <button class="btn" onclick="selectLayer3Candidate(${idx})" style="margin-top:6px;padding:4px 8px;font-size:10px">この台で設定推測</button>
        </div>
      </div>

      <!-- ② 数値根拠点（主役：RB・合算・信頼度） -->
      <div style="background:var(--bg4);border-radius:6px;padding:8px;margin-bottom:6px">
        <div style="font-size:10px;color:var(--accent);font-weight:700;margin-bottom:5px">
          📊 数値根拠 ${t.valueScore}pt
          ${t.valueDetail.reliabilityMeta.factor < 1.0 ? `<span style="color:var(--accent4);font-size:9px;margin-left:4px">×${t.valueDetail.reliabilityMeta.factor}補正</span>` : ''}
        </div>
        ${t.valueReasons.map(r=>`
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px">
            <span style="font-size:11px;color:var(--muted)">${r.label}</span>
            <div style="text-align:right">
              <span style="font-size:12px;font-weight:700;color:${r.pts>0?'var(--plus)':r.pts<0?'var(--minus)':'var(--muted)'}">${r.pts>0?'+':''}${r.pts}pt</span>
              <div style="font-size:10px;color:var(--border)">${r.val}</div>
            </div>
          </div>`).join('')}
        ${!t.valueReasons.length ? '<div style="font-size:11px;color:var(--muted)">RBデータ不足</div>' : ''}
      </div>

      <!-- ③ 配分根拠点（補助） -->
      <div style="background:var(--bg4);border-radius:6px;padding:8px;margin-bottom:6px">
        <div style="font-size:10px;color:var(--muted);font-weight:700;margin-bottom:5px">📍 配分根拠 ${t.configScore}pt</div>
        ${t.configReasons.length ? t.configReasons.map(r=>`
          <div style="font-size:11px;display:flex;justify-content:space-between;margin-bottom:2px">
            <span style="color:var(--muted)">${r.label}</span>
            <span style="color:${r.pts>0?'var(--plus)':r.pts<0?'var(--minus)':'var(--muted)'};font-weight:700">${r.pts>0?'+':''}${r.pts}pt</span>
          </div>`).join('') : '<div style="font-size:11px;color:var(--muted)">根拠なし</div>'}
      </div>

      <!-- ④ strongフラグ（目立たせる） -->
      ${strongFlags.length ? `
      <div style="margin-bottom:6px">
        ${strongFlags.map(f=>`
          <div style="font-size:11px;color:${warnColor(f)};background:${warnBg(f)};border:1px solid ${warnBorder(f)};border-radius:4px;padding:4px 8px;margin-bottom:3px">
            ⚠ ${f.text}
          </div>`).join('')}
      </div>` : ''}

      <!-- ⑤ 現地確認ポイント（最大3件） -->
      <div style="background:#0a1a0a;border:1px solid #1a3a1a;border-radius:6px;padding:8px;margin-bottom:6px">
        <div style="font-size:10px;color:var(--plus);font-weight:700;margin-bottom:4px">📋 現地確認（最大3点）</div>
        ${t.fieldCheckPoints.map(p=>`<div style="font-size:11px;color:var(--muted);margin-bottom:2px">・${p}</div>`).join('')}
      </div>

      <!-- ⑥ 参考情報（差枚・プラス率は末尾） -->
      <div style="display:flex;gap:10px;font-size:11px;color:var(--muted);padding:5px 8px;background:var(--bg4);border-radius:6px;flex-wrap:wrap">
        <span style="color:var(--border)">参考：</span>
        <span>${condLabel}平均 <b style="color:${ref!==null&&ref>=0?'var(--plus)':'var(--minus)'}">${ref!==null?(ref>=0?'+':'')+ref+'枚':'—'}</b></span>
        <span>プラス率 <b style="color:var(--accent)">${t.plusRate}%</b></span>
        <span>全体平均 <b style="color:${t.avg>=0?'var(--plus)':'var(--minus)'}">${t.avg>=0?'+':''}${t.avg}枚</b></span>
        ${weakFlags.length ? `<span style="color:var(--border)">${weakFlags.map(f=>f.text.split('→')[0].trim()).join(' / ')}</span>` : ''}
      </div>

      <!-- 前日データ（参考内に統合） -->
      ${t.prevRow ? `
      <div style="font-size:11px;color:var(--muted);padding:5px 8px;margin-top:4px">
        前日：<span style="color:${t.prevRow.diff>=0?'var(--plus)':'var(--minus)'};font-weight:700">${t.prevRow.diff>=0?'+':''}${t.prevRow.diff}枚</span>
        　BB${t.prevRow.bb} RB${t.prevRow.rb}
        ${t.prevRow.isRBLead?'<span style="color:var(--accent3);margin-left:4px">RB先行</span>':''}
      </div>` : ''}

    </div>`;
  }).join('');

  document.getElementById('layer3Result').innerHTML = coverageBanner + (html || '<div class="empty-msg">候補台がありません</div>');
  document.getElementById('layer3Card').style.display = 'block';
  document.getElementById('layer3Card').scrollIntoView({behavior:'smooth', block:'start'});
}

function selectLayer3CandidatePrecomputed(idx, model) {
  if(!G.todayAnalysis) return;
  const targets = G.todayAnalysis.topTargets.filter(t => t.model === model);
  const t = targets[idx];
  if(!t) return;
  G.currentTargetContext = {
    store: currentStore,
    model: t.model,
    tai: t.tai,
    targetDate: G.todayAnalysis.date,
    isSpecial: G.todayAnalysis.isSpecial,
    historicalRbRate: t.rbRate,
    historicalSynRate: t.synRate,
    totalScore: t.totalScore,
    configScore: 0,
    valueScore: t.totalScore,
  };
  document.getElementById('stModel').value = t.model;
  showTab('tab-setsuteii', document.querySelector('[onclick*="tab-setsuteii"]'));
}

function selectLayer3Candidate(idx) {
  const t = G.layer3Scored && G.layer3Scored[idx];
  if(!t) return;
  const meta = G.layer3SelectionMeta || {};
  const rbSource = t.valueDetail?.rbMeta?.source || null;
  const synSource = t.valueDetail?.synMeta?.source || null;
  const historicalSource = rbSource && synSource ? `RB:${rbSource} / 合算:${synSource}` : (rbSource || synSource || '全期間');
  const expectedSettingBand = buildExpectedSettingBand(t.model, t.valueDetail?.rbMeta?.setLevel ?? null, t.valueDetail?.synMeta?.setLevel ?? null);
  const modelProfileNote = (MODEL_SCORE_PROFILE[t.model] && MODEL_SCORE_PROFILE[t.model].uiNote) ? MODEL_SCORE_PROFILE[t.model].uiNote : '';

  G.currentTargetContext = {
    store: meta.store || (currentStore === 'all' ? (G.raw[0]?.store || 'all') : currentStore),
    floor: (typeof L !== 'undefined' && L && L.store === meta.store && L.floor) ? L.floor : '',
    model: t.model || meta.model || '',
    tai: t.tai,
    targetDate: meta.targetDate || (targetDate ? targetDate.toISOString().slice(0,10) : ''),
    isSpecial: !!meta.isSpecial,
    rank: t.rank || '',
    configScore: t.configScore,
    valueScore: t.valueScore,
    totalScore: t.totalScore,
    warningFlags: t.warningFlags || [],
    fieldCheckPoints: t.fieldCheckPoints || [],
    historicalRbRate: t.valueDetail?.rbMeta?.rbRate || null,
    historicalSynRate: t.valueDetail?.synMeta?.synRate || null,
    historicalAvgG: t.avgG || null,
    historicalSource,
    expectedSettingBand,
    modelProfileNote,
    // backward compatibility
    pastRates: {
      rbRate: t.valueDetail?.rbMeta?.rbRate || null,
      synRate: t.valueDetail?.synMeta?.synRate || null,
      rbSource,
      synSource,
      totalRB: t.valueDetail?.rbMeta?.totalRB || 0,
      totalBonus: t.valueDetail?.synMeta?.totalBonus || 0
    },
    floorRef: (typeof L !== 'undefined' && L) ? L.floor : ''
  };

  const stModelEl = document.getElementById('stModel');
  if(stModelEl && G.currentTargetContext.model) {
    stModelEl.value = G.currentTargetContext.model;
    stSave();
    renderModelHint(stModelEl.value);
  }
  renderCurrentTargetContextComparison();
  showTab('tab-setsuteii');
  document.getElementById('detailMenuBtn')?.classList.add('active');
}


// 旧関数（他タブから呼ばれている可能性があるため残す）
function renderTarget() { renderLayer1(); }

// ====== 翌日分析 レンダリング ======
function renderNextAnalysis() {
  if(!G.nextStats||!G.nextStats['__baseline']){
    document.getElementById('nextAnalysis').innerHTML='<div class="empty-msg">データを読み込んでください</div>';
    return;
  }
  const baseline = G.nextStats['__baseline'];
  const keys = ['凹み_2000以上','凹み_1000_2000','凹み_500_1000','凹み_0_500','プラス','プラス500以上','RB先行','連続凹み','特定日前日','特定日翌日'];

  const sections = [
    { title:'📉 前日差枚別', keys:['凹み_2000以上','凹み_1000_2000','凹み_500_1000','凹み_0_500','プラス','プラス500以上'] },
    { title:'🔍 特殊条件別', keys:['RB先行','連続凹み','特定日前日','特定日翌日'] },
  ];

  let html = `
    <div class="cond-card" style="background:rgba(232,255,0,0.05);border:1px solid rgba(232,255,0,0.2);margin-bottom:12px;">
      <div class="cond-header">
        <div class="cond-name" style="color:var(--accent)">📊 ベースライン（全期間平均）</div>
        <div class="cond-sample">${baseline.count}台分</div>
      </div>
      <div class="cond-stats">
        <div class="cond-stat"><div class="cond-stat-label">平均差枚</div><div class="cond-stat-val" style="color:${baseline.avg>=0?'var(--plus)':'var(--minus)'}">${baseline.avg>=0?'+':''}${baseline.avg}</div></div>
        <div class="cond-stat"><div class="cond-stat-label">プラス率</div><div class="cond-stat-val" style="color:var(--accent)">${baseline.plusRate}%</div></div>
        <div class="cond-stat"><div class="cond-stat-label">-</div><div class="cond-stat-val">-</div></div>
      </div>
    </div>`;

  sections.forEach(sec=>{
    html += `<div class="next-section"><div class="next-section-title">${sec.title}</div>`;
    sec.keys.forEach(k=>{
      const s = G.nextStats[k];
      if(!s||s.count<3){
        html+=`<div class="cond-card"><div class="cond-header"><div class="cond-name">${s?.label||k}</div><div class="cond-sample" style="color:var(--minus)">サンプル不足（${s?.count||0}件）</div></div></div>`;
        return;
      }
      const lift = s.avg!==null ? round1(s.avg - baseline.avg) : null;
      const liftColor = lift>50?'var(--plus)':lift>0?'var(--accent)':lift<-50?'var(--minus)':'var(--muted)';
      const liftStr = lift!==null?(lift>=0?`+${lift}`:`${lift}`):'—';
      html+=`
      <div class="cond-card">
        <div class="cond-header">
          <div class="cond-name">${s.label}</div>
          <div class="cond-sample">${s.count}件</div>
        </div>
        <div class="cond-stats">
          <div class="cond-stat"><div class="cond-stat-label">翌日平均差枚</div><div class="cond-stat-val" style="color:${s.avg>=0?'var(--plus)':'var(--minus)'}">${s.avg>=0?'+':''}${s.avg}</div></div>
          <div class="cond-stat"><div class="cond-stat-label">プラス率</div><div class="cond-stat-val" style="color:var(--accent)">${s.plusRate}%</div></div>
          <div class="cond-stat"><div class="cond-stat-label">ベース比</div><div class="cond-stat-val" style="color:${liftColor}">${liftStr}</div></div>
        </div>
      </div>`;
    });
    html+='</div>';
  });

  document.getElementById('nextAnalysis').innerHTML = html;

  // 店の癖サマリー
  renderStoreTendency(baseline);
}

const STICKINESS_CFG = {
  prevMinG: 1500,
  nextMinG: 1200,
  rbGoodFactor: 1.12,
  synGoodFactor: 1.08,
  singleGoodHighG: 3000,
  minSampleForStable: 20,
  strongRate: 45,
  midRate: 30,
};

function getSpecialDaysByStore(store) {
  return SPECIAL_BY_STORE[store] || SPECIAL_BY_STORE['all'] || DEFAULT_SPECIAL;
}

function isHighLikeRow(row, cfg, ms) {
  if(!row || !ms || !row.g || row.g <= 0) return false;
  const rbRate = row.rb > 0 ? (row.g / row.rb) : null;
  const synRate = (row.bb + row.rb) > 0 ? (row.g / (row.bb + row.rb)) : null;
  const rbGood = rbRate !== null && rbRate <= (ms.rb[4] * cfg.rbGoodFactor);
  const synGood = synRate !== null && synRate <= (ms.syn[4] * cfg.synGoodFactor);
  if(row.g >= cfg.singleGoodHighG && (rbGood || synGood)) return true;
  return rbGood && synGood;
}

function calcStoreStickinessSummary(rows) {
  const cfg = STICKINESS_CFG;
  const byTai = {};
  rows.forEach(r => {
    const key = `${r.store}__${r.model}__${r.tai}`;
    if(!byTai[key]) byTai[key] = [];
    byTai[key].push(r);
  });

  const s = {
    pairCount: 0,
    prevGoodCount: 0,
    maintainCount: 0,
    specialPrevGood: 0,
    specialMaintain: 0,
    normalPrevGood: 0,
    normalMaintain: 0,
    prevRbGoodCount: 0,
    prevRbGoodMaintain: 0,
  };

  Object.values(byTai).forEach(list => {
    list.sort((a,b)=>a.date-b.date);
    for(let i=0; i<list.length-1; i++) {
      const prev = list[i];
      const next = list[i+1];
      const prevMs = MODEL_SETTINGS[prev.model];
      const nextMs = MODEL_SETTINGS[next.model];
      if(!prevMs || !nextMs) continue;
      s.pairCount++;

      const prevGood = prev.g >= cfg.prevMinG && isHighLikeRow(prev, cfg, prevMs);
      if(!prevGood) continue;
      s.prevGoodCount++;

      const prevRbRate = prev.rb > 0 ? (prev.g / prev.rb) : null;
      const prevRbGood = prevRbRate !== null && prevRbRate <= (prevMs.rb[4] * cfg.rbGoodFactor);
      if(prevRbGood) s.prevRbGoodCount++;

      const nextGood = next.g >= cfg.nextMinG && isHighLikeRow(next, cfg, nextMs);
      if(nextGood) {
        s.maintainCount++;
        if(prevRbGood) s.prevRbGoodMaintain++;
      }

      const sp = getSpecialDaysByStore(prev.store);
      const isSpecialPrev = sp.includes(prev.day);
      if(isSpecialPrev) {
        s.specialPrevGood++;
        if(nextGood) s.specialMaintain++;
      } else {
        s.normalPrevGood++;
        if(nextGood) s.normalMaintain++;
      }
    }
  });

  const rate = (num, den) => den > 0 ? round1(num / den * 100) : null;
  return {
    ...s,
    maintainRate: rate(s.maintainCount, s.prevGoodCount),
    specialRate: rate(s.specialMaintain, s.specialPrevGood),
    normalRate: rate(s.normalMaintain, s.normalPrevGood),
    rbGoodRate: rate(s.prevRbGoodMaintain, s.prevRbGoodCount),
  };
}

function getStickinessLabel(maintainRate, sample) {
  if(maintainRate === null) return { label:'サンプル不足', color:'var(--muted)', note:'前日良台ペア不足' };
  const stable = sample >= STICKINESS_CFG.minSampleForStable;
  if(maintainRate >= STICKINESS_CFG.strongRate) return { label: stable ? '強' : '強（参考）', color:'var(--plus)', note:'前日良台の翌日維持が高め' };
  if(maintainRate >= STICKINESS_CFG.midRate) return { label: stable ? '中' : '中（参考）', color:'var(--accent)', note:'維持傾向は中程度' };
  return { label: stable ? '弱' : '弱（参考）', color:'var(--minus)', note:'維持傾向は低め' };
}

function renderStoreTendency(baseline) {
  const stats = G.nextStats;
  const findings = [];

  // 全条件を自動評価：liftが大きい順に表示
  const condKeys = [
    {key:'プラス500以上', label:'前日+500以上台'},
    {key:'プラス', label:'前日プラス台'},
    {key:'凹み_0_500', label:'前日小凹み（0〜-500）台'},
    {key:'凹み_500_1000', label:'前日中凹み（-500〜-1000）台'},
    {key:'凹み_1000_2000', label:'前日中凹み（-1000〜-2000）台'},
    {key:'凹み_2000以上', label:'前日大凹み（-2000以下）台'},
    {key:'RB先行高設定', label:'前日RB先行不発（設定4以上相当）台'},
    {key:'RB先行', label:'前日RB先行不発（単純）台'},
    {key:'連続凹み', label:'連続凹み台'},
    {key:'特定日前日', label:'特定日前日の凹み台'},
    {key:'特定日翌日', label:'特定日翌日台'},
  ];

  const evaluated = condKeys.map(c=>{
    const s = stats[c.key];
    if(!s||s.count<10||s.avg===null) return null;
    const lift = round1(s.avg - baseline.avg);
    return {...c, lift, count:s.count, avg:s.avg, plusRate:s.plusRate};
  }).filter(Boolean).sort((a,b)=>b.lift-a.lift);

  // 上位3つ（プラス）と最下位（マイナス）を表示
  const top = evaluated.filter(x=>x.lift>20).slice(0,4);
  const bot = evaluated.filter(x=>x.lift<-30).slice(-2);

  const stickiness = calcStoreStickinessSummary(filteredRows());
  const stickLabel = getStickinessLabel(stickiness.maintainRate, stickiness.prevGoodCount);
  const rateText = v => v===null ? '—' : `${v}%`;

  let html = `
    <div style="margin-bottom:10px;padding:10px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;border-left:4px solid ${stickLabel.color}">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
        <div style="font-size:12px;color:var(--text);font-weight:700">🔁 据え置き傾向サマリー（過去傾向）</div>
        <div style="font-size:13px;font-weight:900;color:${stickLabel.color}">据え置き傾向: ${stickLabel.label}</div>
      </div>
      <div style="font-size:10px;color:var(--muted);margin-top:4px">${stickLabel.note} / 前日良台→翌日維持率 ${rateText(stickiness.maintainRate)} / サンプル ${stickiness.prevGoodCount}件（全ペア${stickiness.pairCount}件）</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px">
        <div style="background:var(--bg2);border-radius:6px;padding:7px">
          <div style="font-size:10px;color:var(--muted)">特定日翌日 維持率</div>
          <div style="font-size:14px;color:${(stickiness.specialRate||0)>=40?'var(--plus)':'var(--accent)'};font-weight:700">${rateText(stickiness.specialRate)}</div>
          <div style="font-size:9px;color:var(--muted)">サンプル ${stickiness.specialPrevGood}件</div>
        </div>
        <div style="background:var(--bg2);border-radius:6px;padding:7px">
          <div style="font-size:10px;color:var(--muted)">通常日翌日 維持率</div>
          <div style="font-size:14px;color:${(stickiness.normalRate||0)>=30?'var(--accent)':'var(--muted)'};font-weight:700">${rateText(stickiness.normalRate)}</div>
          <div style="font-size:9px;color:var(--muted)">サンプル ${stickiness.normalPrevGood}件</div>
        </div>
      </div>
      <div style="font-size:9px;color:var(--muted);margin-top:6px">※ 当日の据え置き断定ではなく、過去の前日→翌日連続傾向を示す補助情報です。</div>
    </div>
  `;

  const mkRow = (x, isGood)=>`
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:var(--bg3);border-radius:6px;margin-bottom:5px;font-size:12px;border-left:3px solid ${isGood?'var(--plus)':'var(--minus)'}">
      <div>
        <span>${isGood?'✅':'❌'} ${x.label}</span>
        <span style="font-size:10px;color:var(--muted);margin-left:6px">${x.count}件</span>
      </div>
      <div style="text-align:right;font-family:'Share Tech Mono',monospace;">
        <span style="color:${x.avg>=0?'var(--plus)':'var(--minus)'}">${x.avg>=0?'+':''}${x.avg}枚</span>
        <span style="color:${x.lift>=0?'var(--plus)':'var(--minus)'};font-size:10px;margin-left:5px">ベース比${x.lift>=0?'+':''}${x.lift}</span>
      </div>
    </div>`;

  if(top.length) html += `<div style="font-size:11px;font-weight:700;color:var(--plus);margin-bottom:6px">📈 有効な狙い方（翌日成績が良い条件）</div>`+top.map(x=>mkRow(x,true)).join('');
  if(bot.length) html += `<div style="font-size:11px;font-weight:700;color:var(--minus);margin:10px 0 6px">📉 避けるべき条件</div>`+bot.map(x=>mkRow(x,false)).join('');

  // 最強条件を一行サマリー
  if(top.length){
    const best = top[0];
    html += `<div style="margin-top:10px;padding:10px;background:rgba(57,255,20,0.07);border:1px solid rgba(57,255,20,0.25);border-radius:6px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--accent)">💡 この店の最優先狙い：</strong><br>
      「${best.label}」の翌日が最も期待値が高い（ベース比${best.lift>=0?'+':''}${best.lift}枚）。<br>
      ${top.length>1?`次点：「${top[1].label}」（ベース比${top[1].lift>=0?'+':''}${top[1].lift}枚）`:''}
    </div>`;
  }

  if(top.length===0 && bot.length===0){
    html += '<div style="font-size:12px;color:var(--muted)">明確な翌日条件傾向は検出されませんでした。データが増えると精度が上がります。</div>';
  }
  document.getElementById('storeTendency').innerHTML = html;
}

// ====== ヒートマップ共通ユーティリティ ======
function selectHeatMetric(m, btn) {
  currentHeatMetric = m;
  document.querySelectorAll('#heatMetricBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderHeatmap();
}
function selectWeekMetric(m, btn) {
  currentWeekMetric = m;
  document.querySelectorAll('#weekMatrixMetricBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderWeekMatrix();
}
function selectDayWdayMetric(m, btn) {
  currentDayWdayMetric = m;
  document.querySelectorAll('#dayWdayMetricBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderDayWdayMatrix();
}

function metricLabel(m) {
  return m==='avg'?'差枚':m==='ritu'?'推定出率%':'勝率%';
}

function cellColorForMetric(val, maxAbs, metric) {
  if(val === null) return 'var(--bg3)';
  let norm = val;
  if(metric==='avg') norm = val;
  else if(metric==='ritu') norm = val - 100;
  else if(metric==='win') norm = val - 50;
  else if(metric==='set456') norm = val - 40; // 40%基準
  const intensity = Math.min(Math.abs(norm)/Math.max(maxAbs,1), 1);
  if(norm >= 0){
    const g = Math.round(80+intensity*175); const r = Math.round(30*(1-intensity));
    return `rgb(${r},${g},${r})`;
  } else {
    const r2 = Math.round(80+intensity*175); const g2 = Math.round(30*(1-intensity));
    return `rgb(${r2},${g2},${g2})`;
  }
}

function showHeatPopup(title, data, metric) {
  if(!data || data.count < 5) return;
  document.getElementById('popupTitle').textContent = title;
  document.getElementById('popupBody').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
      <div style="background:var(--bg3);border-radius:6px;padding:8px;text-align:center">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">平均差枚</div>
        <div style="font-size:16px;font-weight:700;color:${data.avg>=0?'var(--plus)':'var(--minus)'}">${data.avg>=0?'+':''}${data.avg}枚</div>
      </div>
      <div style="background:var(--bg3);border-radius:6px;padding:8px;text-align:center">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">推定出率</div>
        <div style="font-size:16px;font-weight:700;color:${(data.ritu||0)>=100?'var(--plus)':'var(--minus)'}">${data.ritu!==null?data.ritu+'%':'—'}</div>
      </div>
      <div style="background:var(--bg3);border-radius:6px;padding:8px;text-align:center">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">勝率</div>
        <div style="font-size:16px;font-weight:700;color:var(--accent)">${data.win}%</div>
      </div>
      <div style="background:var(--bg3);border-radius:6px;padding:8px;text-align:center">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">推定設定456率</div>
        <div style="font-size:16px;font-weight:700;color:${(data.set456||0)>=40?'var(--plus)':'var(--muted)'}">${data.set456!==undefined?data.set456+'%':'—'}</div>
      </div>
      <div style="background:var(--bg3);border-radius:6px;padding:8px;text-align:center;grid-column:1/-1">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">サンプル数</div>
        <div style="font-size:16px;font-weight:700;color:var(--accent3)">${data.count}件</div>
      </div>
    </div>`;
  document.getElementById('heatPopup').style.display='block';
  document.getElementById('heatPopupOverlay').style.display='block';
}

function buildHeatTable(rowDefs, colDefs, dataMap, metric, minCount) {
  // rowDefs: [{key, label}], colDefs: [{key, label}]
  const vals = rowDefs.flatMap(r=>colDefs.map(c=>{
    const d = dataMap[`${r.key}_${c.key}`];
    return d&&d.count>=minCount ? d[metric] : null;
  })).filter(v=>v!==null);
  let maxAbs = 1;
  if(metric==='avg') maxAbs = Math.max(...vals.map(Math.abs), 1);
  else if(metric==='ritu') maxAbs = Math.max(...vals.map(v=>Math.abs(v-100)), 1);
  else if(metric==='set456') maxAbs = Math.max(...vals.map(v=>Math.abs(v-40)), 1);
  else maxAbs = Math.max(...vals.map(v=>Math.abs(v-50)), 1);

  let html = '<table class="heat-table"><thead><tr><th></th>';
  colDefs.forEach(c=>{ html+=`<th>${c.label}</th>`; });
  html += '</tr></thead><tbody>';

  rowDefs.forEach(r=>{
    const isSpecial = ['zoro','tsuki','end'].includes(String(r.key));
    html += `<tr><th style="${isSpecial?'color:var(--accent3)':''}">${r.label}</th>`;
    colDefs.forEach(c=>{
      const d = dataMap[`${r.key}_${c.key}`];
      if(!d||d.count<minCount){
        html+=`<td class="heat-cell-none">-</td>`;
      } else {
        const val = d[metric];
        const bg = cellColorForMetric(val, maxAbs, metric);
        const isPos = metric==='avg'?val>=0:metric==='ritu'?val>=100:metric==='set456'?val>=40:val>=50;
        const cls = isPos?'heat-cell-pos':'heat-cell-neg';
        const disp = metric==='avg'?(val>=0?'+':'')+val : val+'%';
        const rLabel = `${r.label}×${c.label}`;
        html+=`<td class="${cls}" style="background:${bg};cursor:pointer" onclick="showHeatPopup('${rLabel}',G.heatmap['${r.key}_${c.key}']||G.weekMatrix['${r.key}_${c.key}']||G.dayWdayMatrix['${r.key}_${c.key}'],'${metric}')">${disp}</td>`;
      }
    });
    html+='</tr>';
  });
  html+='</tbody></table>';
  return html;
}

// ====== ヒートマップ ======
function renderHeatmap() {
  if(!Object.keys(G.heatmap).length) return;
  const digits = [0,1,2,3,4,5,6,7,8,9];
  const rowDefs = [
    ...digits.map(d=>({key:d, label:`${d}の日`})),
    {key:'zoro', label:'ゾロ目'},
    {key:'tsuki', label:'月=日'},
    {key:'end', label:'月末'},
  ];
  const colDefs = digits.map(t=>({key:t, label:`${t}番台`}));
  document.getElementById('heatmapWrap').innerHTML = buildHeatTable(rowDefs, colDefs, G.heatmap, currentHeatMetric, 5);

  // TOP10（常に差枚でランキング）
  const ranked = [];
  rowDefs.forEach(r=>{
    colDefs.forEach(c=>{
      const key=`${r.key}_${c.key}`;
      const d=G.heatmap[key];
      if(d&&d.count>=5) ranked.push({rLabel:r.label, cLabel:c.label, rKey:r.key, cKey:c.key, ...d});
    });
  });
  ranked.sort((a,b)=>b.avg-a.avg);
  document.getElementById('heatRanking').innerHTML = ranked.slice(0,10).map((x,i)=>`
    <div class="tai-row" style="border-left:3px solid ${x.avg>=0?'var(--plus)':'var(--minus)'}">
      <div><div class="tai-num">${i+1}位</div><div class="tai-info">${x.count}件</div></div>
      <div style="flex:1">
        <div style="font-size:13px;font-weight:700">${x.rLabel} × ${x.cLabel}</div>
        <div class="tai-info">出率${x.ritu!==null?x.ritu+'%':'—'} ｜ 勝率${x.win}%</div>
      </div>
      <div class="tai-diff" style="color:${x.avg>=0?'var(--plus)':'var(--minus)'}">${x.avg>=0?'+':''}${x.avg}</div>
    </div>`).join('');
}

// ====== 第○週×曜日マトリクス ======
function renderWeekMatrix() {
  if(!Object.keys(G.weekMatrix).length) return;
  const weeks = [1,2,3,4,5];
  const wdays = [0,1,2,3,4,5,6];
  const wdayLabels = ['日','月','火','水','木','金','土'];
  const rowDefs = weeks.map(w=>({key:w, label:`第${w}週`}));
  const colDefs = wdays.map((w,i)=>({key:w, label:wdayLabels[i]}));

  // セルクリックはweekMatrixから参照
  const tableHtml = buildHeatTableCustom(rowDefs, colDefs, G.weekMatrix, currentWeekMetric, 3, 'weekMatrix');
  document.getElementById('weekMatrixWrap').innerHTML = tableHtml;
}

// ====== 日付末尾×曜日マトリクス ======
function renderDayWdayMatrix() {
  if(!Object.keys(G.dayWdayMatrix).length) return;
  const digits = [0,1,2,3,4,5,6,7,8,9];
  const wdays = [0,1,2,3,4,5,6];
  const wdayLabels = ['日','月','火','水','木','金','土'];
  const rowDefs = [
    ...digits.map(d=>({key:d, label:`${d}の付く日`})),
    {key:'zoro', label:'ゾロ目'},
    {key:'tsuki', label:'月=日'},
    {key:'end', label:'月末'},
  ];
  const colDefs = wdays.map((w,i)=>({key:w, label:wdayLabels[i]}));
  document.getElementById('dayWdayWrap').innerHTML = buildHeatTableCustom(rowDefs, colDefs, G.dayWdayMatrix, currentDayWdayMetric, 3, 'dayWdayMatrix');
}

function buildHeatTableCustom(rowDefs, colDefs, dataMap, metric, minCount, mapName) {
  const vals = rowDefs.flatMap(r=>colDefs.map(c=>{
    const d = dataMap[`${r.key}_${c.key}`];
    return d&&d.count>=minCount ? d[metric] : null;
  })).filter(v=>v!==null);
  let maxAbs = 1;
  if(metric==='avg') maxAbs = Math.max(...vals.map(Math.abs), 1);
  else if(metric==='ritu') maxAbs = Math.max(...vals.map(v=>Math.abs(v-100)), 1);
  else if(metric==='set456') maxAbs = Math.max(...vals.map(v=>Math.abs(v-40)), 1);
  else maxAbs = Math.max(...vals.map(v=>Math.abs(v-50)), 1);

  let html = '<table class="heat-table"><thead><tr><th></th>';
  colDefs.forEach(c=>{ html+=`<th>${c.label}</th>`; });
  html += '</tr></thead><tbody>';

  rowDefs.forEach(r=>{
    const isSpecial = ['zoro','tsuki','end'].includes(String(r.key));
    html += `<tr><th style="${isSpecial?'color:var(--accent3)':''}">${r.label}</th>`;
    colDefs.forEach(c=>{
      const d = dataMap[`${r.key}_${c.key}`];
      if(!d||d.count<minCount){
        html+=`<td class="heat-cell-none">-</td>`;
      } else {
        const val = d[metric];
        const bg = cellColorForMetric(val, maxAbs, metric);
        const isPos = metric==='avg'?val>=0:metric==='ritu'?val>=100:metric==='set456'?val>=40:val>=50;
        const cls = isPos?'heat-cell-pos':'heat-cell-neg';
        const disp = metric==='avg'?(val>=0?'+':'')+val : val+'%';
        const rLabel = `${r.label}×${c.label}`;
        html+=`<td class="${cls}" style="background:${bg};cursor:pointer" onclick="showHeatPopup('${rLabel}',G.${mapName}['${r.key}_${c.key}'],'${metric}')">${disp}</td>`;
      }
    });
    html+='</tr>';
  });
  html+='</tbody></table>';
  return html;
}

// ====== 日にち別 ======
function renderDayBar() {
  if(!G.dayStats.length) return;
  const SP = getSpecial();
  const maxAbs=Math.max(...G.dayStats.map(d=>Math.abs(d.avg)),1);
  document.getElementById('dayBarChart').innerHTML=G.dayStats.map(d=>{
    const pct=Math.abs(d.avg)/maxAbs*100;
    return`<div class="bar-row">
      <div class="bar-label">${d.day}${SP.includes(d.day)?'<span style="color:var(--accent3)">★</span>':''}</div>
      <div class="bar-bg"><div class="bar-fill ${d.avg>=0?'pos':'neg'}" style="width:${pct}%"></div></div>
      <div class="bar-val" style="color:${d.avg>=0?'var(--plus)':'var(--minus)'}">${d.avg>=0?'+':''}${d.avg}</div>
    </div>`;}).join('');
  document.getElementById('dayRanking').innerHTML=[...G.dayStats].sort((a,b)=>b.avg-a.avg).slice(0,10).map((d,i)=>`
    <div class="tai-row">
      <div class="tai-num">${i+1}. ${d.day}日</div>
      <div>${SP.includes(d.day)?'<span class="badge badge-special">⭐特定日</span>':'<span style="font-size:10px;color:var(--muted)">通常日</span>'}
        <div class="tai-info">プラス率${d.plusRate}% / ${d.total}台分</div></div>
      <div class="tai-diff" style="color:${d.avg>=0?'var(--plus)':'var(--minus)'}">${d.avg>=0?'+':''}${d.avg}</div>
    </div>`).join('');
}

// ====== 機種比較 ======
function renderModelSpFilter() {
  const SP = getSpecial();
  // フィルター選択肢：全体・特定日・通常日・日付末尾0〜9
  const opts = [
    {key:'all', label:'全体'},
    {key:'sp', label:'特定日'},
    {key:'nm', label:'通常日'},
    ...([0,1,2,3,4,5,6,7,8,9].map(d=>({key:`digit_${d}`, label:`${d}の付く日`}))),
    {key:'zoro', label:'ゾロ目'},
  ];
  document.getElementById('modelSpFilterBtns').innerHTML = opts.map(o=>`
    <button class="filter-btn ${currentModelSpFilter===o.key?'active':''}"
      onclick="selectModelSpFilter('${o.key}',this)">${o.label}</button>`).join('');
}

function selectModelSpFilter(key, btn) {
  currentModelSpFilter = key;
  document.querySelectorAll('#modelSpFilterBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderModelComp();
}

function getModelFilteredRows() {
  const rows = filteredRows();
  const SP = getSpecial();
  if(currentModelSpFilter==='all') return rows;
  if(currentModelSpFilter==='sp') return rows.filter(r=>SP.includes(r.day));
  if(currentModelSpFilter==='nm') return rows.filter(r=>!SP.includes(r.day));
  if(currentModelSpFilter==='zoro') return rows.filter(r=>r.isZoro);
  const digit = parseInt(currentModelSpFilter.replace('digit_',''));
  if(!isNaN(digit)) return rows.filter(r=>r.day%10===digit);
  return rows;
}

function renderModelComp() {
  if(!G.modelStats.length) return;
  renderModelSpFilter();

  // 集計済みモード：G.modelStatsを使う
  if(G._precomputed) {
    const SP = getSpecial();
    const isSpecial = currentModelSpFilter === 'sp';
    const isNormal = currentModelSpFilter === 'nm';
    const allAvgDiff = round1(avg(G.modelStats.map(m=>m.allAvg)));

    const data = G.modelStats.map(m => {
      let a, count;
      if(isSpecial) { a = m.spAvg; count = m.spCount; }
      else if(isNormal) { a = m.nmAvg; count = m.nmCount; }
      else { a = m.allAvg; count = m.count; }
      if(a === null || a === undefined) return null;
      const lift = round1(a - allAvgDiff);
      return {model:m.model, avg:a, count, mechRitu:m.mechRitu, lift};
    }).filter(Boolean).sort((a,b)=>b.avg-a.avg);

    const col = v => v>=0 ? 'var(--plus)' : 'var(--minus)';
    const fmt = v => v===null ? '—' : `${v>=0?'+':''}${v}`;
    const fmtR = v => v===null ? '—' : `${v.toFixed(1)}%`;

    document.getElementById('modelCompTable').innerHTML=`
      <div style="font-size:10px;color:var(--muted);margin-bottom:8px">全体平均：${fmt(allAvgDiff)}枚</div>
      <table class="data-table">
        <thead><tr>
          <th style="text-align:left">機種名</th>
          <th>平均差枚</th>
          <th>推定出率</th>
          <th>件数</th>
          <th>ベース比</th>
        </tr></thead>
        <tbody>${data.map(m=>`<tr>
          <td style="font-size:11px;font-weight:700">${m.model}</td>
          <td style="color:${col(m.avg)};font-family:'Share Tech Mono',monospace">${fmt(m.avg)}</td>
          <td style="color:${m.mechRitu===null?'var(--muted)':m.mechRitu>=100?'var(--plus)':'var(--minus)'};font-family:'Share Tech Mono',monospace">${fmtR(m.mechRitu)}</td>
          <td style="color:var(--muted);font-size:11px">${m.count}</td>
          <td style="color:${col(m.lift)};font-size:11px">${fmt(m.lift)}</td>
        </tr>`).join('')}
        </tbody>
      </table>`;

    renderModelMonthComp();
    renderModelFilter();
    return;
  }

  const rows = getModelFilteredRows();
  if(!rows.length){
    document.getElementById('modelCompTable').innerHTML='<div class="empty-msg">該当データなし</div>';
    return;
  }

  // フィルター後の機種別集計
  const byModel={};
  rows.forEach(r=>{
    if(!byModel[r.model]) byModel[r.model]={diffs:[],g:[],bb:[],rb:[]};
    byModel[r.model].diffs.push(r.diff);
    byModel[r.model].g.push(r.g);
    byModel[r.model].bb.push(r.bb||0);
    byModel[r.model].rb.push(r.rb||0);
  });

  const allRows = filteredRows();
  const allAvgDiff = round1(avg(allRows.map(r=>r.diff)));

  const data = Object.entries(byModel).map(([model,v])=>{
    const totalG = v.g.reduce((a,b)=>a+b,0);
    const totalIn = totalG * 3;
    const totalDiff = v.diffs.reduce((a,b)=>a+b,0);
    const totalOut = totalIn + totalDiff;
    const mechRitu = totalIn > 0 ? round1(totalOut/totalIn*100) : null;
    const a = round1(avg(v.diffs));
    const lift = round1(a - allAvgDiff);
    return {model, avg:a, count:v.diffs.length, mechRitu, lift};
  }).sort((a,b)=>b.avg-a.avg);

  const col = v => v>=0 ? 'var(--plus)' : 'var(--minus)';
  const fmt = v => v===null ? '—' : `${v>=0?'+':''}${v}`;
  const fmtR = v => v===null ? '—' : `${v.toFixed(1)}%`;

  document.getElementById('modelCompTable').innerHTML=`
    <div style="font-size:10px;color:var(--muted);margin-bottom:8px">全体平均：${fmt(allAvgDiff)}枚 | フィルター：${currentModelSpFilter==='all'?'全体':currentModelSpFilter==='sp'?'特定日':currentModelSpFilter==='nm'?'通常日':currentModelSpFilter.replace('digit_','')+'の付く日'}</div>
    <table class="data-table">
      <thead><tr>
        <th style="text-align:left">機種名</th>
        <th>平均差枚</th>
        <th>推定出率</th>
        <th>件数</th>
        <th>ベース比</th>
      </tr></thead>
      <tbody>${data.map(m=>`<tr>
        <td style="font-size:11px;font-weight:700">${m.model}</td>
        <td style="color:${col(m.avg)};font-family:'Share Tech Mono',monospace">${fmt(m.avg)}</td>
        <td style="color:${m.mechRitu===null?'var(--muted)':m.mechRitu>=100?'var(--plus)':'var(--minus)'};font-family:'Share Tech Mono',monospace">${fmtR(m.mechRitu)}</td>
        <td style="color:var(--muted);font-size:11px">${m.count}</td>
        <td style="color:${col(m.lift)};font-size:11px">${fmt(m.lift)}</td>
      </tr>`).join('')}
      </tbody>
    </table>`;

  renderModelMonthComp();
  renderModelFilter();
}

function renderModelMonthComp() {
  const data = [...G.modelStats]
    .filter(m=>m.thisMonthCount>0||m.lastMonthCount>0)
    .sort((a,b)=>{
      const da = a.thisMonthAvg??-999, db = b.thisMonthAvg??-999;
      return db-da;
    });
  if(!data.length){document.getElementById('modelMonthComp').innerHTML='<div class="empty-msg">データなし</div>';return;}

  // 集計済みモードではdateSummaryから最新日を取得
  const latestDateStr = G.dateSummary.length ? G.dateSummary[G.dateSummary.length-1].dateStr : null;
  if(!latestDateStr && !filteredRows().length) { document.getElementById('modelMonthComp').innerHTML='<div class="empty-msg">データなし</div>'; return; }
  const latestDate2 = latestDateStr ? new Date(latestDateStr) : filteredRows().reduce((a,b)=>a.date>b.date?a:b).date;
  const thisLabel = `${latestDate2.getMonth()+1}月`;
  const lastLabel = `${latestDate2.getMonth()===0?12:latestDate2.getMonth()}月`;
  // 今月の経過日数
  const thisMonthDays = latestDate2.getDate();
  const fewDaysWarning = thisMonthDays <= 7;

  const col = v => v===null?'var(--muted)':v>=0?'var(--plus)':'var(--minus)';
  const fmt = (v,n) => v===null?`<span style="color:var(--muted)">—</span>`:`<span style="color:${col(v)}">${v>=0?'+':''}${v}枚</span><br><span style="font-size:10px;color:${n<10?'var(--accent4)':'var(--muted)'}">${n}件${n<10?' ⚠️':''}</span>`;

  const warning = fewDaysWarning ? `<div style="padding:8px 10px;background:rgba(255,159,0,0.1);border:1px solid rgba(255,159,0,0.3);border-radius:6px;font-size:11px;color:var(--accent4);margin-bottom:10px">⚠️ 今月はまだ${thisMonthDays}日分のデータです。件数が少ない機種は参考値としてご覧ください。</div>` : '';

  document.getElementById('modelMonthComp').innerHTML= warning + `
    <table class="data-table">
      <thead><tr>
        <th style="text-align:left">機種名</th>
        <th>${thisLabel}（今月）</th>
        <th>${lastLabel}（先月）</th>
        <th>変化</th>
      </tr></thead>
      <tbody>${data.map(m=>{
        const delta = m.thisMonthAvg!==null&&m.lastMonthAvg!==null ? round1(m.thisMonthAvg-m.lastMonthAvg) : null;
        const arrow = delta===null?'—':delta>50?'⬆️急上昇':delta>20?'↗上昇':delta<-50?'⬇️急落':delta<-20?'↘下落':'→横ばい';
        return`<tr>
          <td style="font-size:11px;font-weight:700">${m.model}</td>
          <td style="font-family:'Share Tech Mono',monospace;font-size:12px">${fmt(m.thisMonthAvg,m.thisMonthCount)}</td>
          <td style="font-family:'Share Tech Mono',monospace;font-size:12px">${fmt(m.lastMonthAvg,m.lastMonthCount)}</td>
          <td style="font-size:12px">${arrow}${delta!==null?`<br><span style="font-size:10px;color:${col(delta)}">${delta>=0?'+':''}${delta}</span>`:''}</td>
        </tr>`;}).join('')}
      </tbody>
    </table>`;
}

function renderModelFilter() {
  if(!G.modelStats.length) return;
  const models=G.modelStats.map(m=>m.model);
  document.getElementById('modelFilterBtns').innerHTML=models.map((m,i)=>`
    <button class="filter-btn ${i===0?'active':''}" onclick="selectModelFilter('${m}',this)">${m.slice(0,7)}</button>`).join('');
  if(models.length){currentModelFilter=models[0];renderModelDayBar();}
}

function selectModelFilter(model,btn) {
  document.querySelectorAll('#modelFilterBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');currentModelFilter=model;renderModelDayBar();
}

function renderModelDayBar() {
  const SP = getSpecial();
  const m=G.modelStats.find(x=>x.model===currentModelFilter);
  if(!m) return;
  const days=Array.from({length:31},(_,i)=>i+1).filter(d=>m.byDay[d]);
  const maxAbs=Math.max(...days.map(d=>Math.abs(avg(m.byDay[d]))),1);
  document.getElementById('modelDayBar').innerHTML=days.map(d=>{
    const a=round1(avg(m.byDay[d]));const pct=Math.abs(a)/maxAbs*100;const isSp=SP.includes(d);
    return`<div class="bar-row">
      <div class="bar-label" style="${isSp?'color:var(--accent3)':''}">${d}${isSp?'★':''}</div>
      <div class="bar-bg"><div class="bar-fill ${a>=0?'pos':'neg'}" style="width:${pct}%"></div></div>
      <div class="bar-val" style="color:${a>=0?'var(--plus)':'var(--minus)'}">${a>=0?'+':''}${a}</div>
    </div>`;}).join('');
}

// ====== 台別 ======
function selectTaiPeriod(days, btn) {
  currentTaiPeriod = days;
  document.querySelectorAll('#taiPeriodBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderTaiList();
}

function getTaiRowsForCurrentPeriod() {
  let rows = filteredRows();
  if(currentTaiPeriod > 0 && rows.length) {
    const latestDate = rows.map(r=>r.date).reduce((a,b)=>a>b?a:b);
    const cutoff = new Date(latestDate);
    cutoff.setDate(cutoff.getDate() - currentTaiPeriod);
    rows = rows.filter(r => r.date >= cutoff);
  }
  return rows;
}

function getModelTreatmentLabel(stat) {
  if(stat.count < 10) return { label:'標準', note:'サンプル少なめ', color:'var(--muted)' };
  let score = 0;
  if(stat.avg >= 120) score += 2;
  else if(stat.avg >= 30) score += 1;
  else if(stat.avg <= -80) score -= 2;
  else if(stat.avg <= -20) score -= 1;
  if(stat.plusRate >= 58) score += 1;
  else if(stat.plusRate < 45) score -= 1;
  if(stat.rbGoodRate >= 35) score += 1;
  else if(stat.rbGoodRate < 18) score -= 1;

  if(score >= 2) {
    const note = stat.rbGoodRate >= 30 ? 'RB良好率高め' : (stat.avg >= 120 ? '平均差枚が強め' : '機種全体で安定');
    return { label:'良扱い', note, color:'var(--plus)' };
  }
  if(score <= -1) {
    const note = stat.count < 15 ? 'サンプル少なめ' : (stat.avg < 0 ? '平均差枚が弱め' : 'RB良好率が低め');
    return { label:'弱め', note, color:'var(--minus)' };
  }
  return { label:'標準', note:'直近は横ばい', color:'var(--accent)' };
}

function filterTaiFromSummary(model) {
  currentTaiFilter = model;
  document.querySelectorAll('#taiFilterBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  const btnId = 'taiFilterBtn_' + model.replace(/[^\w]/g,'_');
  const btn = document.getElementById(btnId);
  if(btn) btn.classList.add('active');
  renderTaiList();
}

function renderTaiModelSummary(sourceRows) {
  const el = document.getElementById('taiModelSummary');
  if(!el) return;

  // 集計済みモード：G.modelStatsを使う
  if (G._precomputed && G.modelStats && G.modelStats.length) {
    const stats = G.modelStats.map(m => {
      const rbGoodRate = 0;
      const treatment = getModelTreatmentLabel({ avg: m.allAvg, plusRate: 0, rbGoodRate, count: m.count });
      return { model:m.model, count:m.count, avg:m.allAvg, plusRate:0, rbGoodRate, ...treatment };
    }).sort((a,b) => {
      const order = x => x.label==='良扱い' ? 2 : x.label==='標準' ? 1 : 0;
      if(order(b) !== order(a)) return order(b) - order(a);
      return b.avg - a.avg;
    });
    const periodLabel = '全期間';
    const visible = stats.slice(0, 8);
    const hiddenCount = Math.max(0, stats.length - visible.length);
    const maxAbsAvg = Math.max(...stats.map(s => Math.abs(s.avg)), 1);
    el.innerHTML = `
    <div style="font-size:10px;color:var(--muted);margin-bottom:8px">${periodLabel} ・ タップで機種フィルタ</div>
    <div style="display:flex;flex-direction:column;gap:5px">
      ${visible.map((s, i) => {
        const barW = Math.min(Math.abs(s.avg) / maxAbsAvg * 100, 100);
        const isPlus = s.avg >= 0;
        const rank = i === 0 ? '👑' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}.`;
        return `
        <button data-model="${s.model}" onclick="filterTaiFromSummary(this.dataset.model)"
          style="background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:8px 10px;text-align:left;cursor:pointer;width:100%">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
            <div style="display:flex;align-items:center;gap:6px">
              <span style="font-size:11px;color:var(--muted);min-width:18px">${rank}</span>
              <span style="font-size:12px;font-weight:700;color:var(--text)">${s.model}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:11px;font-weight:700;color:${isPlus?'var(--plus)':'var(--minus)'}">${s.avg>=0?'+':''}${s.avg}枚</span>
              <span style="font-size:11px;font-weight:900;color:${s.color};min-width:36px;text-align:right">${s.label}</span>
            </div>
          </div>
          <div style="position:relative;height:6px;background:var(--bg4);border-radius:3px;overflow:hidden">
            <div style="position:absolute;top:0;${isPlus?'left:0':'right:0'};width:${barW}%;height:100%;background:${s.color};border-radius:3px"></div>
          </div>
          <div style="font-size:9px;color:var(--muted);margin-top:3px">${s.note} ・ ${s.count}件</div>
        </button>`;
      }).join('')}
      ${hiddenCount>0 ? `<div style="font-size:10px;color:var(--muted);padding:2px 4px">他 ${hiddenCount} 機種</div>` : ''}
    </div>
  `;
    return;
  }

  const rows = sourceRows || getTaiRowsForCurrentPeriod();
  if(!rows.length) {
    el.innerHTML = '<div class="empty-msg">該当データなし</div>';
    return;
  }

  const byModel = {};
  rows.forEach(r => {
    if(!byModel[r.model]) byModel[r.model] = { model:r.model, diffs:[], rbGood:0, rbCount:0 };
    byModel[r.model].diffs.push(r.diff);
    if(r.rb > 0) {
      byModel[r.model].rbCount++;
      const rbRate = Math.round((r.g||0)/r.rb);
      const lv = rbRateToSetLevel(r.model, rbRate);
      if(lv !== null && lv >= 4) byModel[r.model].rbGood++;
    }
  });

  const stats = Object.values(byModel).map(m => {
    const count = m.diffs.length;
    const avgDiff = round1(avg(m.diffs));
    const plusRate = round1(m.diffs.filter(v=>v>0).length / count * 100);
    const rbGoodRate = m.rbCount > 0 ? round1(m.rbGood / m.rbCount * 100) : 0;
    const treatment = getModelTreatmentLabel({ avg: avgDiff, plusRate, rbGoodRate, count });
    return { model:m.model, count, avg: avgDiff, plusRate, rbGoodRate, ...treatment };
  }).sort((a,b) => {
    const order = x => x.label==='良扱い' ? 2 : x.label==='標準' ? 1 : 0;
    if(order(b) !== order(a)) return order(b) - order(a);
    return b.avg - a.avg;
  });

  const periodLabel = currentTaiPeriod === 0 ? '全期間' : `直近${currentTaiPeriod}日`;
  const visible = stats.slice(0, 8);
  const hiddenCount = Math.max(0, stats.length - visible.length);

  // 棒グラフ用：平均差枚の最大絶対値を基準にバー幅を計算
  const maxAbsAvg = Math.max(...stats.map(s => Math.abs(s.avg)), 1);

  el.innerHTML = `
    <div style="font-size:10px;color:var(--muted);margin-bottom:8px">${periodLabel} ・ タップで機種フィルタ</div>
    <div style="display:flex;flex-direction:column;gap:5px">
      ${visible.map((s, i) => {
        const barW = Math.min(Math.abs(s.avg) / maxAbsAvg * 100, 100);
        const isPlus = s.avg >= 0;
        const rank = i === 0 ? '👑' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}.`;
        return `
        <button data-model="${s.model}" onclick="filterTaiFromSummary(this.dataset.model)"
          style="background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:8px 10px;text-align:left;cursor:pointer;width:100%">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
            <div style="display:flex;align-items:center;gap:6px">
              <span style="font-size:11px;color:var(--muted);min-width:18px">${rank}</span>
              <span style="font-size:12px;font-weight:700;color:var(--text)">${s.model}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:11px;font-weight:700;color:${isPlus?'var(--plus)':'var(--minus)'}">${s.avg>=0?'+':''}${s.avg}枚</span>
              <span style="font-size:11px;font-weight:900;color:${s.color};min-width:36px;text-align:right">${s.label}</span>
            </div>
          </div>
          <div style="position:relative;height:6px;background:var(--bg4);border-radius:3px;overflow:hidden">
            <div style="position:absolute;top:0;${isPlus?'left:0':'right:0'};width:${barW}%;height:100%;background:${s.color};border-radius:3px"></div>
          </div>
          <div style="font-size:9px;color:var(--muted);margin-top:3px">${s.note} ・ プラス率${s.plusRate}% ・ ${s.count}件</div>
        </button>`;
      }).join('')}
      ${hiddenCount>0 ? `<div style="font-size:10px;color:var(--muted);padding:2px 4px">他 ${hiddenCount} 機種</div>` : ''}
    </div>
  `;
}

function renderTaiFilter() {
  if(!G.taiDetail.length) return;
  const models=[...new Set(G.taiDetail.map(t=>t.model))];
  document.getElementById('taiFilterBtns').innerHTML=
    `<button class="filter-btn ${currentTaiFilter==='all'?'active':''}" onclick="filterTai('all',this)">すべて</button>`+
    models.map(m=>`<button id="taiFilterBtn_${m.replace(/[^\w]/g,'_')}" class="filter-btn ${currentTaiFilter===m?'active':''}" onclick="filterTai('${m}',this)">${m.slice(0,6)}</button>`).join('');
}

function filterTai(model,btn) {
  currentTaiFilter=model;
  document.querySelectorAll('#taiFilterBtns .filter-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderTaiList();
}

function renderTaiList() {
  // 集計済みモード：G.taiDetailを直接使う
  if (G._precomputed) {
    renderTaiModelSummary(null);
    let taiData = G.taiDetail.filter(t => currentStore === 'all' || t.store === currentStore);
    if (currentTaiFilter !== 'all') taiData = taiData.filter(t => t.model === currentTaiFilter);
    if (!taiData.length) { document.getElementById('taiList').innerHTML='<div class="empty-msg">該当データなし</div>'; return; }

    const SP = getSpecial();
    const html = taiData.map(t => {
      const isPlus = t.avg >= 0;
      const ref = t.spAvg !== null ? t.spAvg : t.avg;
      const bayesProb = t.bayesProbSp !== null ? t.bayesProbSp : t.bayesProbAll;
      return `
      <div class="tai-row" style="border-color:${isPlus?'rgba(57,255,20,.2)':'rgba(255,77,109,.1)'}">
        <div>
          <div class="tai-num">${t.tai}</div>
          <div class="tai-info">${t.model.slice(0,6)} / ${t.count}件</div>
        </div>
        <div>
          <div style="font-size:10px;color:var(--muted)">特定日平均</div>
          <div style="font-size:12px;font-weight:700;color:${t.spAvg!==null&&t.spAvg>=0?'var(--plus)':'var(--minus)'}">${t.spAvg!==null?(t.spAvg>=0?'+':'')+t.spAvg+'枚':'—'}</div>
          <div style="font-size:10px;color:var(--muted)">全体平均 ${t.avg>=0?'+':''}${t.avg}枚</div>
          ${bayesProb!==null?`<div style="font-size:10px;color:var(--accent3)">P(設定4+) ${bayesProb}%</div>`:''}
          ${t.prevRow?`<div style="font-size:10px;color:var(--muted)">前日:${t.prevRow.diff>=0?'+':''}${t.prevRow.diff}枚 BB${t.prevRow.bb} RB${t.prevRow.rb}</div>`:''}
        </div>
        <div class="tai-diff" style="color:${isPlus?'var(--plus)':'var(--minus)'}">${t.avg>=0?'+':''}${t.avg}</div>
      </div>`;
    }).join('');
    document.getElementById('taiList').innerHTML = html;
    return;
  }

  const SP = getSpecial();
  let rows = getTaiRowsForCurrentPeriod();
  renderTaiModelSummary(rows);

  // 機種フィルター
  if(currentTaiFilter !== 'all') rows = rows.filter(r=>r.model===currentTaiFilter);

  if(!rows.length){document.getElementById('taiList').innerHTML='<div class="empty-msg">該当データなし</div>';return;}

  // 台別集計
  const byTai={};
  rows.forEach(r=>{
    const k=`${r.tai}_${r.model}`;
    if(!byTai[k]) byTai[k]={tai:r.tai,taiNum:r.taiNum,model:r.model,diffs:[],spDiffs:[],nmDiffs:[],g:[],bb:[],rb:[]};
    byTai[k].diffs.push(r.diff);
    byTai[k].g.push(r.g);
    byTai[k].bb.push(r.bb||0);
    byTai[k].rb.push(r.rb||0);
    if(SP.includes(r.day)) byTai[k].spDiffs.push(r.diff);
    else byTai[k].nmDiffs.push(r.diff);
  });

  const data = Object.values(byTai).map(t=>{
    const a = round1(avg(t.diffs));
    const totalG  = t.g.reduce((a,b)=>a+b,0);
    const totalBB = t.bb.reduce((a,b)=>a+b,0);
    const totalRB = t.rb.reduce((a,b)=>a+b,0);
    const totalIn  = totalG * 3;
    const totalOut = totalIn + t.diffs.reduce((a,b)=>a+b,0);
    const mechRitu = totalIn > 0 ? round1(totalOut/totalIn*100) : null;
    const rbRate  = totalRB > 0 ? Math.round(totalG/totalRB)  : null;
    const synRate = (totalBB+totalRB) > 0 ? Math.round(totalG/(totalBB+totalRB)) : null;
    const avgG    = t.diffs.length ? Math.round(totalG/t.diffs.length) : 0;
    return {
      tai:t.tai, taiNum:t.taiNum, model:t.model,
      avg:a, count:t.diffs.length,
      plusRate:round1(t.diffs.filter(v=>v>0).length/t.diffs.length*100),
      spAvg:t.spDiffs.length?round1(avg(t.spDiffs)):null,
      nmAvg:t.nmDiffs.length?round1(avg(t.nmDiffs)):null,
      mechRitu, rbRate, synRate, avgG, totalRB,
    };
  }).sort((a,b)=>a.taiNum-b.taiNum);

  const col = v => v>=0 ? 'var(--plus)' : 'var(--minus)';
  document.getElementById('taiList').innerHTML=data.map(t=>{
    const rbScr  = scoreTaiRbRate(t.model, t.rbRate, t.totalRB);
    const rbColor = rbScr.pts >= 3 ? 'var(--plus)' : rbScr.pts >= 2 ? 'var(--accent)' :
                    rbScr.pts <= 0 ? 'var(--muted)' : 'var(--muted)';
    const rbLabel = t.rbRate ? `1/${t.rbRate}` : '—';
    const synLabel = t.synRate ? `1/${t.synRate}` : '—';
    return `
    <div class="tai-row">
      <div>
        <div class="tai-num">${t.tai}番</div>
        <div class="tai-info">${t.count}日分</div>
      </div>
      <div style="flex:1;min-width:0">
        <div style="font-size:11px;color:var(--muted);margin-bottom:3px">${t.model}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;font-size:11px">
          <span>RB <span style="font-weight:700;color:${rbColor}">${rbLabel}</span>${rbScr.pts>0?' <span style="font-size:9px;color:var(--plus)">▲</span>':rbScr.pts<0?' <span style="font-size:9px;color:var(--minus)">▼</span>':''}</span>
          <span style="color:var(--muted)">合算 <span style="color:var(--text)">${synLabel}</span></span>
          <span style="color:var(--muted)">${t.avgG.toLocaleString()}G</span>
        </div>
        <div style="font-size:10px;color:var(--muted);margin-top:2px">
          ${t.spAvg!==null?`特定:<span style="color:${col(t.spAvg)}">${t.spAvg>=0?'+':''}${t.spAvg}</span> `:''}
          ${t.nmAvg!==null?`通常:<span style="color:${col(t.nmAvg)}">${t.nmAvg>=0?'+':''}${t.nmAvg}</span>`:''}
        </div>
      </div>
      <div class="tai-diff" style="color:${col(t.avg)}">${t.avg>=0?'+':''}${t.avg}</div>
    </div>`;
  }).join('');
}

// ====== 期間分析 ======
function selectPeriod(days,btn) {
  currentPeriod=days;
  document.querySelectorAll('.period-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderPeriod();
}

function renderPeriod() {
  const allDates=G.dateSummary;
  if(!allDates.length) return;
  let filtered=allDates;
  if(currentPeriod>0){
    // dateStrが文字列なので文字列比較で絞り込む
    const lastDateStr = allDates[allDates.length-1].dateStr;
    const cutoff = new Date(lastDateStr);
    cutoff.setDate(cutoff.getDate()-currentPeriod);
    const cutoffStr = cutoff.toISOString().slice(0,10);
    filtered=allDates.filter(d=>d.dateStr>=cutoffStr);
  }
  if(!filtered.length) return;
  const totalDiff=filtered.reduce((a,b)=>a+b.total,0);
  const plusDays=filtered.filter(d=>d.total>0).length;
  const plusRate=round1(plusDays/filtered.length*100);
  const avgPerDay=round1(totalDiff/filtered.length);
  const maxDay=filtered.reduce((a,b)=>b.total>a.total?b:a);
  document.getElementById('periodStats').innerHTML=`
    <div class="win-box"><div class="win-label">合計差枚</div><div class="win-value" style="color:${totalDiff>=0?'var(--plus)':'var(--minus)'};font-size:16px">${totalDiff>=0?'+':''}${totalDiff.toLocaleString()}</div></div>
    <div class="win-box"><div class="win-label">勝率（日単位）</div><div class="win-value" style="color:${plusRate>=50?'var(--plus)':'var(--minus)'}">${plusRate}%</div></div>
    <div class="win-box"><div class="win-label">1日平均差枚</div><div class="win-value" style="color:${avgPerDay>=0?'var(--plus)':'var(--minus)'}">${avgPerDay>=0?'+':''}${avgPerDay}</div></div>
    <div class="win-box"><div class="win-label">最強日</div><div class="win-value" style="color:var(--accent3);font-size:15px">${maxDay.dateStr.slice(5)}</div></div>`;
  const ctx=document.getElementById('timelineChart').getContext('2d');
  if(chartInst) chartInst.destroy();
  const chartFiltered = filtered.slice(-60); // 最大60日分を表示
  chartInst=new Chart(ctx,{type:'bar',
    data:{labels:chartFiltered.map(d=>d.dateStr.slice(5)),
      datasets:[{data:chartFiltered.map(d=>d.total),backgroundColor:chartFiltered.map(d=>d.total>=0?'rgba(57,255,20,0.6)':'rgba(255,77,109,0.6)'),borderWidth:0}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{x:{ticks:{color:'#666680',font:{size:9},maxRotation:45},grid:{color:'rgba(255,255,255,0.04)'}},
              y:{ticks:{color:'#666680',font:{size:10}},grid:{color:'rgba(255,255,255,0.04)'}}}}});
  // 強い日・強い台：集計済みデータを使う
  const topDays = [...G.dayStats].sort((a,b)=>b.avg-a.avg).slice(0,5);
  document.getElementById('periodTopDays').innerHTML = topDays.map((d,i)=>`
    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:12px;">
      <span style="color:var(--muted)">${i+1}. ${d.day}日</span>
      <span style="color:${d.avg>=0?'var(--plus)':'var(--minus)'};font-family:'Share Tech Mono',monospace">${d.avg>=0?'+':''}${d.avg}</span>
    </div>`).join('');
  const topTai = [...G.taiDetail].sort((a,b)=>b.avg-a.avg).filter(t=>t.count>=3).slice(0,5);
  document.getElementById('periodTopTai').innerHTML = topTai.map((t,i)=>`
    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:12px;">
      <span style="color:var(--muted)">${i+1}. ${t.tai}番</span>
      <span style="color:${t.avg>=0?'var(--plus)':'var(--minus)'};font-family:'Share Tech Mono',monospace">${t.avg>=0?'+':''}${t.avg}</span>
    </div>`).join('');
  document.getElementById('timelineList').innerHTML=[...filtered].reverse().map(d=>{
    const cls=d.total>10000?'hot':d.total>0?'warm':'cold';
    const j=d.total>10000?'🔥':d.total>0?'🟡':'❄️';
    return`<div class="tl-row ${cls}">
      <div class="tl-date">${d.dateStr.slice(5)}</div>
      <div>${d.special?'<span style="color:var(--accent3);font-size:10px">★</span>':''}</div>
      <div style="font-size:11px;color:var(--muted)">${j} ${d.plusRate}%（${d.count}台）</div>
      <div class="tl-diff" style="color:${d.total>=0?'var(--plus)':'var(--minus)'}">${d.total>=0?'+':''}${d.total.toLocaleString()}</div>
    </div>`;}).join('');
}

// ====== 設定 ======
function loadSpecialDaysFromStorage() {
  try{const s=localStorage.getItem('juggler_special_days');if(s) SPECIAL_BY_STORE=JSON.parse(s);}catch(e){}
}

function saveSpecialDays() {
  document.querySelectorAll('.special-input').forEach(input=>{
    const store=input.dataset.store;
    const days=input.value.split(',').map(d=>parseInt(d.trim())).filter(d=>d>=1&&d<=31);
    if(days.length) SPECIAL_BY_STORE[store]=days;
  });
  try{localStorage.setItem('juggler_special_days',JSON.stringify(SPECIAL_BY_STORE));}catch(e){}
  compute(); renderAll();
  alert('✅ 保存しました！');
}

function renderStoreSettings() {
  const stores=G.stores.filter(s=>s!=='all');
  if(!stores.length) return;
  document.getElementById('storeSettingList').innerHTML=stores.map(s=>{
    const precomputedSpecial = G._precomputed ? (G._precomputed.specialByStore[s] || []) : null;
    const auto = precomputedSpecial || (G.raw.length ? detectAutoSpecial(G.raw.filter(r=>r.store===s)) : []);
    const manual = SPECIAL_BY_STORE[s];
    const days=(manual||auto).join(', ');
    const isAuto = !manual;
    return`<div class="setting-store">
      <div class="setting-store-name">🏪 ${s}</div>
      ${isAuto?`<div style="font-size:10px;color:var(--accent4);margin-bottom:6px;">⚡ アナスロ登録日：${auto.join('・')}日</div>`:''}
      <input class="paste-area special-input" data-store="${s}" value="${days}"
        style="min-height:auto;padding:8px 10px;font-size:13px;"
        placeholder="例: 4, 8, 14, 18, 24, 28">
      <div style="font-size:10px;color:var(--muted);margin-top:4px">カンマ区切りで入力（1〜31）／「日にち」タブの強い日を参考に</div>
    </div>`;}).join('');
}

// ====== データ入りHTML保存 ======
function saveDataHTML() {
  if(!G.raw.length && !G._precomputed){alert('データを読み込んでください');return;}
  const dataJSON=JSON.stringify(G.raw.map(r=>({...r,date:r.date.toISOString()})));
  const html=document.documentElement.outerHTML;
  const injected=html.replace('// ====== グローバル ======',
    `// ====== グローバル ======\nwindow._PRELOAD=${dataJSON};\nwindow._SPECIAL_STORE=${JSON.stringify(SPECIAL_BY_STORE)};`);
  const blob=new Blob([injected],{type:'text/html;charset=utf-8'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=`juggler_${new Date().toISOString().slice(0,10)}.html`;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ====== 全レンダリング（アクティブタブのみ描画） ======
const TAB_RENDER_MAP = {
  'tab-data':     () => { renderSessionUI(); },
  'tab-answer':   () => { renderAnswerTab(); },
  'tab-days':     () => { renderDayBar(); },
  'tab-model':    () => { renderModelComp(); },
  'tab-tai':      () => { renderTaiFilter(); renderTaiList(); },
  'tab-settings': () => { renderStoreSettings(); renderGitHubTokenUI(); },
  'tab-target':   () => { renderTarget(); },
  'tab-heat':     () => { renderHeatmap(); renderWeekMatrix(); renderDayWdayMatrix(); },
  'tab-calendar': () => { renderCalendar(); },
  'tab-period':   () => { renderPeriod(); },
  'tab-next':     () => { renderNextAnalysis(); },
  'tab-setsuteii':() => { renderCurrentTargetContextComparison(); },
  'tab-layout':   () => { initLayoutMasterTab(); },
};

function renderAll() {
  renderRecommendations();
  // アクティブタブのみ描画（タブ切り替え時に初めて描画）
  const activeTab = document.querySelector('.tab-content.active');
  if(!activeTab) return;
  const fn = TAB_RENDER_MAP[activeTab.id];
  if(fn) {
    try { fn(); }
    catch(err) { console.error(`[renderAll] ${activeTab.id} failed`, err); }
  }
  // 読込タブのデータ件数表示は常に更新
  renderStoreSettings();
}

// ====== 店舗バー ======
function getStoreFreshnessMeta(storeName) {
  const freshness = G.storeFreshness ? G.storeFreshness[storeName] : null;
  const record = (freshness && typeof freshness === 'object') ? freshness : {};
  const dataDate = record.data_date || null;
  const scrapedAt = record.scraped_at || '';

  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = `${yesterday.getFullYear()}-${String(yesterday.getMonth()+1).padStart(2,'0')}-${String(yesterday.getDate()).padStart(2,'0')}`;

  const title = `data_date: ${dataDate || 'N/A'}${scrapedAt ? ` / scraped_at: ${scrapedAt}` : ''}`;
  if(dataDate === todayStr) return { color: 'green', icon: '🟢', ts: title };
  if(dataDate === yesterdayStr) return { color: 'yellow', icon: '🟡', ts: title };
  return { color: 'red', icon: '🔴', ts: title };
}

function renderStoreFreshnessBadge(storeName) {
  const meta = getStoreFreshnessMeta(storeName);
  if(!meta) return '';
  return `<span class="store-freshness-badge ${meta.color}" title="${meta.ts}">${meta.icon}</span>`;
}

function renderStoreBar() {
  document.getElementById('storeBar').innerHTML=
    '<span class="store-label">店舗：</span>'+
    G.stores.map(s=>`<button class="store-btn ${s===currentStore?'active':''}" onclick="switchStore(${JSON.stringify(s)},this)"><span>${s==='all'?'全店舗':s}</span>${s==='all'?'':renderStoreFreshnessBadge(s)}</button>`).join('');
}

function switchStore(store,btn) {
  currentStore=store;
  document.querySelectorAll('.store-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  _bayesCache.clear();
  setTimeout(() => {
    if (G._precomputed) {
      setStoreData(store);
    } else {
      compute();
    }
    renderAll();
  }, 0);
}

// ====== ステータス ======
function showStatus() {
  const rows=G.raw;
  const dates=[...new Set(rows.map(r=>r.dateStr))].sort();
  const el=document.getElementById('dataStatus');
  el.textContent=`${dates.length}日分`;el.classList.add('loaded');
  document.getElementById('saveBtn').disabled=false;
  document.getElementById('loadedInfo').style.display='block';
  document.getElementById('loadedSummary').innerHTML=`
    <div style="font-size:12px;line-height:2;">
      📅 ${dates[0]} 〜 ${dates[dates.length-1]}（${dates.length}日間）<br>
      🏪 ${[...new Set(rows.map(r=>r.store))].map(s=>`<span class="badge badge-normal">${s}</span>`).join('')}<br>
      🎰 ${[...new Set(rows.map(r=>r.tai))].length}台 / ${rows.length}行
    </div>`;
}

// ====== 初期化 ======
window.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('diagDate').valueAsDate=new Date();
  restoreGasUrlInput();
  if(window._PRELOAD&&window._PRELOAD.length){
    if(window._SPECIAL_STORE) SPECIAL_BY_STORE=window._SPECIAL_STORE;
    G.raw=window._PRELOAD.map(r=>({
      ...r,
      date:new Date(r.date),
      isRBLead:r.rb>r.bb,
      isHighSetRBLead: isHighSetRBLead(r.model, r.g, r.bb, r.rb),
    }));
    G.stores=['all',...new Set(G.raw.map(r=>r.store))];
    setTimeout(() => { compute(); renderStoreBar(); renderAll(); showStatus(); }, 0);
  }
  loadSpecialDaysFromStorage();
  stRestoreInputs();
  renderSessionUI();
  renderGitHubTokenUI();
});

// ====== カレンダー予報 ======
let G_calYear = null, G_calMonth = null;
const CAL_MIN_SAMPLE = 3;
const WDAY_LABELS = ['日','月','火','水','木','金','土'];

function renderCalendar() {
  if(!G.raw.length && !G._precomputed) {
    document.getElementById('calMonthWrap').innerHTML = '<div class="empty-msg">データを読み込んでください</div>';
    document.getElementById('calUpcomingWrap').innerHTML = '<div class="empty-msg">データを読み込んでください</div>';
    return;
  }
  if(G_calYear === null) {
    const now = new Date();
    G_calYear = now.getFullYear();
    G_calMonth = now.getMonth();
  }
  buildCalendarMonth();
  buildUpcomingList();
}

function getCalDateMeta(year, month, day) {
  const date = new Date(year, month, day);
  const wday = date.getDay();
  const week = Math.ceil(day / 7);
  const suffix = day % 10;
  const lastDay = new Date(year, month + 1, 0).getDate();
  const isZoro = day >= 11 && String(day).length === 2 && String(day)[0] === String(day)[1];
  const isEnd = day === lastDay;
  const isTsuki = day === month + 1;
  return { date, wday, week, suffix, lastDay, isZoro, isEnd, isTsuki };
}

function getDateScore(year, month, day) {
  const { wday, week, suffix, isZoro, isEnd, isTsuki } = getCalDateMeta(year, month, day);
  if(!G.weekMatrix || !G.dayWdayMatrix) return null;
  const scores = [];

  const wkS = G.weekMatrix[`${week}_${wday}`];
  if(wkS && wkS.count >= CAL_MIN_SAMPLE)
    scores.push({ label: `第${week}週×${WDAY_LABELS[wday]}曜`, ...wkS });

  const dyS = G.dayWdayMatrix[`${suffix}_${wday}`];
  if(dyS && dyS.count >= CAL_MIN_SAMPLE)
    scores.push({ label: `${suffix}の付く日×${WDAY_LABELS[wday]}曜`, ...dyS });

  if(isZoro) {
    const zS = G.dayWdayMatrix[`zoro_${wday}`];
    if(zS && zS.count >= CAL_MIN_SAMPLE) scores.push({ label: `ゾロ目×${WDAY_LABELS[wday]}曜`, ...zS });
  }
  if(isEnd) {
    const eS = G.dayWdayMatrix[`end_${wday}`];
    if(eS && eS.count >= CAL_MIN_SAMPLE) scores.push({ label: `月末×${WDAY_LABELS[wday]}曜`, ...eS });
  }
  if(isTsuki) {
    const tS = G.dayWdayMatrix[`tsuki_${wday}`];
    if(tS && tS.count >= CAL_MIN_SAMPLE) scores.push({ label: `月=日×${WDAY_LABELS[wday]}曜`, ...tS });
  }

  if(!scores.length) return null;
  const totalCount = scores.reduce((a, s) => a + s.count, 0);
  // set456（高設定台率）を主指標、avgを副指標として加重平均
  const weightedSet456 = scores.reduce((a, s) => a + (s.set456 || 0) * s.count, 0) / totalCount;
  const weightedAvg    = scores.reduce((a, s) => a + s.avg * s.count, 0) / totalCount;
  const weightedWin    = scores.reduce((a, s) => a + s.win * s.count, 0) / totalCount;
  return {
    set456: Math.round(weightedSet456),
    avg: Math.round(weightedAvg),
    win: Math.round(weightedWin),
    totalCount,
    scores
  };
}

function calScoreStyle(set456) {
  if(set456 == null) return { bg:'transparent', col:'var(--muted)', label:'—' };
  if(set456 >= 50)   return { bg:'rgba(57,255,20,0.22)',  col:'var(--plus)',    label:'◎' };
  if(set456 >= 35)   return { bg:'rgba(57,255,20,0.11)',  col:'var(--plus)',    label:'○' };
  if(set456 >= 20)   return { bg:'rgba(232,255,0,0.07)',  col:'var(--accent)',  label:'△' };
  if(set456 >= 10)   return { bg:'rgba(255,159,0,0.11)',  col:'var(--accent4)', label:'▽' };
  return              { bg:'rgba(255,77,109,0.14)', col:'var(--minus)',   label:'×' };
}

function buildCalendarMonth() {
  const today = new Date(); today.setHours(0,0,0,0);
  const firstDay = new Date(G_calYear, G_calMonth, 1).getDay();
  const lastDate = new Date(G_calYear, G_calMonth + 1, 0).getDate();
  const wdayCols = ['var(--minus)','var(--text)','var(--text)','var(--text)','var(--text)','var(--text)','#55aaff'];

  let html = `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
    <button onclick="calPrevMonth()" class="cal-nav-btn">◀</button>
    <div style="font-weight:900;font-size:16px">${G_calYear}年${G_calMonth+1}月</div>
    <button onclick="calNextMonth()" class="cal-nav-btn">▶</button>
  </div>
  <table style="width:100%;border-collapse:collapse;table-layout:fixed"><tr>`;

  WDAY_LABELS.forEach((w, i) => {
    html += `<th style="text-align:center;padding:3px 0;font-size:11px;color:${wdayCols[i]};font-weight:700">${w}</th>`;
  });
  html += '</tr><tr>';

  for(let i = 0; i < firstDay; i++) html += '<td style="padding:2px"></td>';

  for(let d = 1; d <= lastDate; d++) {
    const col = (firstDay + d - 1) % 7;
    if(col === 0 && d > 1) html += '</tr><tr>';

    const score = getDateScore(G_calYear, G_calMonth, d);
    const cellDate = new Date(G_calYear, G_calMonth, d);
    const isToday = cellDate.getTime() === today.getTime();
    const isPast  = cellDate < today;
    const { bg, col: tc } = score ? calScoreStyle(score.set456) : { bg:'transparent', col:'var(--muted)' };
    const border = isToday ? 'border:2px solid var(--accent)' : 'border:1px solid rgba(255,255,255,0.06)';
    const opacity = isPast ? 'opacity:0.45;' : '';
    const dc = col===0?'var(--minus)':col===6?'#55aaff':'var(--text)';

    let scoreHtml = '';
    if(score) {
      scoreHtml = `<div style="font-size:9px;color:${tc};font-family:'Share Tech Mono',monospace;line-height:1.3;margin-top:1px">${score.set456}%</div>`;
    }

    html += `<td style="padding:2px;${opacity}">
      <div onclick="showCalendarDayDetail(${G_calYear},${G_calMonth},${d})"
           style="${border};border-radius:6px;background:${bg};padding:3px 1px;text-align:center;cursor:pointer;min-height:46px;-webkit-tap-highlight-color:transparent">
        <div style="font-size:13px;font-weight:700;color:${dc};line-height:1.5">${d}</div>
        ${scoreHtml}
      </div></td>`;
  }

  const lastCol = (firstDay + lastDate - 1) % 7;
  if(lastCol < 6) for(let i = lastCol+1; i <= 6; i++) html += '<td style="padding:2px"></td>';

  html += `</tr></table>
  <div style="display:flex;gap:5px;flex-wrap:wrap;margin-top:9px;align-items:center">
    <span style="font-size:10px;color:var(--muted)">凡例（高設定台率）：</span>
    <span style="font-size:10px;padding:1px 8px;border-radius:3px;background:rgba(57,255,20,0.22);color:var(--plus)">◎50%↑</span>
    <span style="font-size:10px;padding:1px 8px;border-radius:3px;background:rgba(57,255,20,0.11);color:var(--plus)">○35%↑</span>
    <span style="font-size:10px;padding:1px 8px;border-radius:3px;background:rgba(232,255,0,0.07);color:var(--accent)">△20%↑</span>
    <span style="font-size:10px;padding:1px 8px;border-radius:3px;background:rgba(255,159,0,0.11);color:var(--accent4)">▽10%↑</span>
    <span style="font-size:10px;padding:1px 8px;border-radius:3px;background:rgba(255,77,109,0.14);color:var(--minus)">×-500↓</span>
  </div>
  <p style="font-size:10px;color:var(--muted);margin-top:5px;line-height:1.6">※第○週×曜日・日付末尾×曜日の統計差枚加重平均。サンプル3件未満は非表示。過去データは薄く表示。</p>`;

  document.getElementById('calMonthWrap').innerHTML = html;
}

function buildUpcomingList() {
  const today = new Date(); today.setHours(0,0,0,0);
  const upcoming = [];
  for(let offset = 0; offset < 35; offset++) {
    const d = new Date(today);
    d.setDate(today.getDate() + offset);
    const score = getDateScore(d.getFullYear(), d.getMonth(), d.getDate());
    if(score) upcoming.push({ date: d, score, offset });
  }
  upcoming.sort((a, b) => b.score.set456 - a.score.set456);
  const top = upcoming.slice(0, 8);
  const wdayCols = ['var(--minus)','var(--text)','var(--text)','var(--text)','var(--text)','var(--text)','#55aaff'];

  let html = '';
  top.forEach(item => {
    const d = item.date;
    const { set456, avg, win, scores } = item.score;
    const { bg, col: tc } = calScoreStyle(set456);
    const wday = d.getDay();
    const diffLabel = item.offset === 0 ? '今日' : item.offset === 1 ? '明日' : `${item.offset}日後`;
    const labelsStr = scores.map(s => s.label).join('  ／  ');
    const avgSign = avg >= 0 ? '+' : '';
    const avgDisp = Math.abs(avg) >= 1000 ? `${avgSign}${(avg/1000).toFixed(1)}k` : `${avgSign}${avg}`;
    html += `<div onclick="showCalendarDayDetail(${d.getFullYear()},${d.getMonth()},${d.getDate()})"
      style="display:flex;align-items:center;gap:10px;background:${bg};border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px;cursor:pointer;margin-bottom:6px;-webkit-tap-highlight-color:transparent">
      <div style="flex-shrink:0;text-align:center;min-width:50px">
        <div style="font-size:10px;color:var(--muted)">${diffLabel}</div>
        <div style="font-size:18px;font-weight:900;color:${wdayCols[wday]}">${d.getMonth()+1}/${d.getDate()}</div>
        <div style="font-size:10px;color:var(--muted)">${WDAY_LABELS[wday]}曜</div>
      </div>
      <div style="flex:1;min-width:0">
        <div style="font-size:10px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${labelsStr}</div>
        <div style="font-size:10px;color:var(--muted);margin-top:2px">N=${item.score.totalCount} サンプル</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div style="font-size:19px;font-weight:900;color:${tc};font-family:'Share Tech Mono',monospace">${set456}%</div>
        <div style="font-size:10px;color:var(--muted)">高設定台率 / 差枚${avgDisp}</div>
      </div>
    </div>`;
  });

  if(!html) html = '<div class="empty-msg">近日中のデータが不足しています（サンプル3件未満）</div>';
  document.getElementById('calUpcomingWrap').innerHTML = html;
}

function calPrevMonth() {
  G_calMonth--;
  if(G_calMonth < 0) { G_calMonth = 11; G_calYear--; }
  buildCalendarMonth();
}
function calNextMonth() {
  G_calMonth++;
  if(G_calMonth > 11) { G_calMonth = 0; G_calYear++; }
  buildCalendarMonth();
}

function showCalendarDayDetail(year, month, day) {
  const meta = getCalDateMeta(year, month, day);
  const score = getDateScore(year, month, day);
  const title = `${month+1}月${day}日（${WDAY_LABELS[meta.wday]}）第${meta.week}週`;

  let body = '';
  if(!score) {
    body = '<div style="padding:16px;text-align:center;color:var(--muted);font-size:13px">データが不足しています<br>（サンプル3件未満）</div>';
  } else {
    const { set456, avg, win, scores } = score;
    const { bg, col: tc, label: lbl } = calScoreStyle(set456);
    const avgSign = avg >= 0 ? '+' : '';
    body += `<div style="text-align:center;padding:14px;border-radius:10px;background:${bg};margin-bottom:14px">
      <div style="font-size:11px;color:${tc};font-weight:700;letter-spacing:.1em;margin-bottom:2px">${lbl}</div>
      <div style="font-size:36px;font-weight:900;color:${tc};font-family:'Share Tech Mono',monospace">${set456}%</div>
      <div style="font-size:12px;color:var(--muted);margin-top:4px">高設定台率 ／ 差枚平均 ${avgSign}${avg.toLocaleString()} ／ 勝率 ${win}%</div>
    </div>
    <div style="font-size:11px;color:var(--muted);margin-bottom:7px;font-weight:700;letter-spacing:.06em">📊 根拠内訳</div>`;
    scores.forEach(s => {
      const { col: sc } = calScoreStyle(s.set456 || 0);
      const set456Bar = Math.min(100, Math.round((s.set456||0) * 2));
      const avgSign2 = s.avg >= 0 ? '+' : '';
      body += `<div style="background:var(--bg3);border-radius:7px;padding:10px 12px;margin-bottom:6px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
          <div style="font-size:12px;font-weight:700">${s.label}</div>
          <div style="font-size:15px;font-weight:900;color:${sc};font-family:'Share Tech Mono',monospace">${s.set456||0}%</div>
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <div style="font-size:10px;color:var(--muted);white-space:nowrap">高設定台率</div>
          <div style="flex:1;background:var(--bg2);border-radius:2px;height:5px;overflow:hidden">
            <div style="width:${set456Bar}%;height:100%;background:${sc};border-radius:2px"></div>
          </div>
          <div style="font-size:10px;color:var(--muted);white-space:nowrap">差枚${avgSign2}${s.avg} N=${s.count}</div>
        </div>
      </div>`;
    });
    const tags = [];
    if(meta.isZoro) tags.push('⭐ ゾロ目');
    if(meta.isEnd)  tags.push('🔚 月末');
    if(meta.isTsuki) tags.push('📅 月=日');
    if(tags.length) {
      body += `<div style="font-size:11px;color:var(--accent3);margin-top:8px;padding:6px 10px;background:rgba(0,229,255,0.07);border-radius:6px">${tags.join('  ／  ')}</div>`;
    }
  }

  document.getElementById('calPopupTitle').textContent = title;
  document.getElementById('calPopupBody').innerHTML = body;
  document.getElementById('calPopup').style.display = 'block';
  document.getElementById('calPopupOverlay').style.display = 'block';

  if(G_calYear !== year || G_calMonth !== month) {
    G_calYear = year; G_calMonth = month;
    buildCalendarMonth();
  }
}

// ====== 撤退判断フローティングUI ======
const WITHDRAW_PRIOR = [1/6, 1/6, 1/6, 1/6, 1/6, 1/6];
const WITHDRAW_SETTINGS = [
  { bb: 1 / 287, rb: 1 / 455, grape: 1 / 6.2,  cherry: 1 / 33.5 },
  { bb: 1 / 282, rb: 1 / 420, grape: 1 / 6.15, cherry: 1 / 33.3 },
  { bb: 1 / 273, rb: 1 / 390, grape: 1 / 6.05, cherry: 1 / 33.1 },
  { bb: 1 / 252, rb: 1 / 320, grape: 1 / 5.95, cherry: 1 / 32.9 },
  { bb: 1 / 240, rb: 1 / 280, grape: 1 / 5.85, cherry: 1 / 32.7 },
  { bb: 1 / 220, rb: 1 / 210, grape: 1 / 5.75, cherry: 1 / 32.5 },
];

function wdSafeNum(v) {
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? n : 0;
}

function wdLogBinomialLike(trials, success, p) {
  const n = Math.max(0, Math.floor(trials));
  const k = Math.max(0, Math.min(n, Math.floor(success)));
  const pp = Math.min(Math.max(p, 1e-9), 1 - 1e-9);
  return k * Math.log(pp) + (n - k) * Math.log(1 - pp);
}

function calcWithdrawPosterior(games, big, reg, grape, cherry) {
  if(games <= 0) return null;

  let logs = WITHDRAW_SETTINGS.map((s, i) => {
    let logL = Math.log(WITHDRAW_PRIOR[i]);
    logL += wdLogBinomialLike(games, big, s.bb);
    logL += wdLogBinomialLike(games, reg, s.rb);
    if(grape > 0) logL += wdLogBinomialLike(games, grape, s.grape);
    if(cherry > 0) logL += wdLogBinomialLike(games, cherry, s.cherry);
    return logL;
  });

  const maxLog = Math.max(...logs);
  logs = logs.map(v => Math.exp(v - maxLog));
  const sum = logs.reduce((a, b) => a + b, 0);
  if(sum <= 0) return null;
  const probs = logs.map(v => v / sum);
  return probs[3] + probs[4] + probs[5];
}

function setWithdrawBanner(isWarn, message) {
  const banner = document.getElementById('withdrawJudgeBanner');
  const text = document.getElementById('withdrawJudgeBannerText');
  if(!banner || !text) return;

  banner.classList.remove('warn', 'ok', 'show');
  banner.classList.add(isWarn ? 'warn' : 'ok', 'show');
  text.textContent = message;

  try {
    if(typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      navigator.vibrate([500, 200, 500]);
    }
  } catch (e) {
    // iOS等の非対応環境は無視
  }
}

function closeWithdrawPopup() {
  const overlay = document.getElementById('withdrawJudgeOverlay');
  if(overlay) overlay.classList.remove('open');
}

function runWithdrawJudge() {
  const games = wdSafeNum(document.getElementById('withdrawGames')?.value);
  const big = wdSafeNum(document.getElementById('withdrawBig')?.value);
  const reg = wdSafeNum(document.getElementById('withdrawReg')?.value);
  const investment = wdSafeNum(document.getElementById('withdrawInvestment')?.value);
  const grape = wdSafeNum(document.getElementById('withdrawGrape')?.value);
  const cherry = wdSafeNum(document.getElementById('withdrawCherry')?.value);

  const p4OrMore = calcWithdrawPosterior(games, big, reg, grape, cherry);
  const pPercent = p4OrMore == null ? 0 : Math.round(p4OrMore * 100);

  const warnByInvestment = investment >= 20000;
  const warnByProb = p4OrMore !== null ? p4OrMore <= 0.30 : true;
  const isWarn = warnByInvestment || warnByProb;

  if(isWarn) {
    setWithdrawBanner(true, '⚠️ 撤退を検討してください');
  } else {
    setWithdrawBanner(false, `✅ 続行推奨：P(設定4以上) ${pPercent}%`);
  }

  closeWithdrawPopup();
}

function initWithdrawJudgeUI() {
  const fab = document.getElementById('withdrawJudgeFab');
  const overlay = document.getElementById('withdrawJudgeOverlay');
  const popup = overlay ? overlay.querySelector('.withdraw-judge-popup') : null;
  const runBtn = document.getElementById('withdrawJudgeRunBtn');
  const bannerClose = document.getElementById('withdrawJudgeBannerClose');
  const banner = document.getElementById('withdrawJudgeBanner');

  if(!fab || !overlay || !popup || !runBtn || !bannerClose || !banner) return;

  fab.addEventListener('click', () => {
    overlay.classList.add('open');
  });
  overlay.addEventListener('click', (ev) => {
    if(ev.target === overlay) closeWithdrawPopup();
  });
  popup.addEventListener('click', (ev) => {
    ev.stopPropagation();
  });
  runBtn.addEventListener('click', runWithdrawJudge);
  bannerClose.addEventListener('click', () => {
    banner.classList.remove('show');
  });
}

document.addEventListener('DOMContentLoaded', initWithdrawJudgeUI);
