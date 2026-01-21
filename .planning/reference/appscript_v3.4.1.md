

  
// ============================================
// GLOBAL LIQUIDITY MONITOR - VERSION 3.4.1 PREMIUM
// Fed + ECB + BoJ + China Tracker
// VOLATILITY TRACKER: MOVE, VIX, VIX3M + Z-SCORES
// FIXED: MOVE fetch via Yahoo v8 Chart API
// ADDED: Volatility Legend in reports
// ============================================

// ================= CONFIGURATION =================
const CONFIG = {
  FRED_API_KEY: 'f768fba23c4cf57dcc1f97f7644c3379',
  EMAIL: 'samuele.morzenti@gmail.com',
  
  // === DISCORD WEBHOOK (DIRECT) ===
  // Get from Discord: Server Settings → Integrations → Webhooks → New Webhook → Copy URL
  DISCORD_WEBHOOK_URL: 'https://discord.com/api/webhooks/1453361777420144794/QzQlHdycqaxIIWDRkjLh95mlfhEOn__h9_iW4pqlDgcmTVENCWSCgYNtBcQZKWS4olSv',  // <-- PASTE YOUR DISCORD WEBHOOK HERE
  DISCORD_ALERTS_WEBHOOK_URL: 'https://discord.com/api/webhooks/1432322262949695508/v0-mhd2qIdpPY0rfoheN_EGrjRKAiXZUoJgR_9FAZimW9atKHpSPjtHxx8l0bSd4c5-A',  // Optional: separate channel for alerts
  
  // === N8N WEBHOOK (Optional - for data logging) ===
  N8N_ENABLED: false,  // Set to true if you still want n8n to receive data
  N8N_WEBHOOK_URL: 'https://n8nubuntu.princyx.xyz/webhook/fed-monitor',

  // === DEBUG & VALIDATION ===
  DEBUG_MODE: true,
  CROSS_VALIDATION: true,
  VALIDATION_TOLERANCE: 0.01,
  
  // === FED SERIES (Primary) ===
  FED_SERIES: {
    'WALCL': 'Fed Total Assets',
    'WTREGEN': 'Treasury General Account',
    'RRPONTSYD': 'Reverse Repo',
    'WRESBAL': 'Bank Reserves',
    'SOFR': 'SOFR Rate',
    'TREAST': 'Fed Holdings: US Treasuries',
    'WSHOMCB': 'Fed Holdings: MBS',
    'SWPT': 'Fed: Central Bank Liquidity Swaps',
    'WORAL': 'Fed: Other Assets',
    'RESPPLLOPNWW': 'Bank Term Funding Program'
  },
  
  // === GLOBAL CENTRAL BANKS SERIES ===
  GLOBAL_SERIES: {
    'ECBASSETSW': { name: 'ECB Total Assets', currency: 'EUR', region: 'ECB', units: 'millions' },
    'ECBDFR': { name: 'ECB Deposit Facility Rate', currency: 'EUR', region: 'ECB', units: 'percent' },
    'JPNASSETS': { name: 'BoJ Total Assets', currency: 'JPY', region: 'BOJ', units: '100_million_yen' },
    'TRESEGCNM052N': { name: 'China Foreign Reserves', currency: 'USD', region: 'PBOC', units: 'millions_usd' },
    'DEXUSEU': { name: 'EUR/USD Exchange Rate', currency: 'USD', region: 'FX', units: 'rate' },
    'DEXJPUS': { name: 'JPY/USD Exchange Rate', currency: 'USD', region: 'FX', units: 'rate' }
  },
  
  // === VOLATILITY SERIES (FRED) ===
  VOLATILITY_SERIES: {
    'VIXCLS': { name: 'VIX', source: 'FRED', description: 'CBOE Volatility Index' },
    'VXVCLS': { name: 'VIX3M', source: 'FRED', description: 'CBOE 3-Month Volatility Index' },
    'T10Y2Y': { name: '10Y-2Y Spread', source: 'FRED', description: 'Treasury Yield Curve Spread' }
  },
  
  // === VOLATILITY THRESHOLDS (for legend) ===
  VOL_THRESHOLDS: {
    VIX: {
      EXTREME_HIGH: 35,
      HIGH: 25,
      ELEVATED: 20,
      NORMAL_HIGH: 18,
      NORMAL_LOW: 12,
      LOW: 10
    },
    VIX_RATIO: {
      BACKWARDATION: 1.05,
      CONTANGO: 0.90
    },
    MOVE: {
      EXTREME_HIGH: 140,
      HIGH: 120,
      ELEVATED: 100,
      NORMAL_HIGH: 90,
      NORMAL_LOW: 70,
      LOW: 60
    },
    ZSCORE: {
      EXTREME_HIGH: 2.0,
      HIGH: 1.0,
      LOW: -1.0,
      EXTREME_LOW: -2.0
    }
  },
  
  // === VOLATILITY SETTINGS ===
  VOL_CONFIG: {
    ZSCORE_WINDOW: 20,
    DELTA_PERIODS: [1, 3, 7, 14],
    VIX_HIGH_THRESHOLD: 25,
    VIX_LOW_THRESHOLD: 15,
    MOVE_HIGH_THRESHOLD: 120,
    MOVE_LOW_THRESHOLD: 80,
    VIX_RATIO_CONTANGO: 0.9,
    VIX_RATIO_BACKWARDATION: 1.05
  },
  
  // === STEALTH QE SCORE CONFIG ===
  SCORE_CONFIG: {
    RRP_VELOCITY_MAX: 20,
    TGA_SPENDING_MAX: 200,
    FED_CHANGE_MAX: 100,
    WEIGHT_RRP: 0.40,
    WEIGHT_TGA: 0.40,
    WEIGHT_FED: 0.20,
    MAX_DAILY_CHANGE: 25,
    WEEKLY_CALC_DAY: 3
  },
  
  // === ALERT THRESHOLDS ===
  ALERTS: {
    RRP_DROP_MAJOR: -15,
    RRP_DROP_MODERATE: -10,
    TGA_SPENDING_SURGE: 100,
    STEALTH_QE_ACTIVATED: 60,
    FED_BALANCE_SPIKE: 50,
    GLOBAL_LIQUIDITY_SURGE: 500,
    GLOBAL_LIQUIDITY_DROP: -500,
    VIX_SPIKE: 30,
    VIX_ZSCORE_EXTREME: 2.0,
    MOVE_SPIKE: 130
  }
};

// ================= VALIDATION STORAGE =================
let VALIDATION_RESULTS = {
  checks: [],
  passed: 0,
  failed: 0,
  warnings: 0
};

// ================= LOGGING =================
function log(message) {
  Logger.log(message);
}

function debug(message, data) {
  if (CONFIG.DEBUG_MODE) {
    if (data !== undefined) {
      Logger.log('🔍 DEBUG: ' + message + ' → ' + JSON.stringify(data));
    } else {
      Logger.log('🔍 DEBUG: ' + message);
    }
  }
}

function section(title) {
  log('');
  log('═'.repeat(70));
  log('📊 ' + title);
  log('═'.repeat(70));
}

function subsection(title) {
  log('');
  log('┌─ ' + title + ' ' + '─'.repeat(Math.max(0, 60 - title.length)) + '┐');
}

function tableRow(label, value, extra) {
  const labelPad = label.padEnd(25);
  const valuePad = String(value).padStart(15);
  const extraStr = extra ? ' │ ' + extra : '';
  log('│ ' + labelPad + ' │ ' + valuePad + extraStr + ' │');
}

function tableEnd() {
  log('└' + '─'.repeat(68) + '┘');
}

// ================= FORMATTING =================
function formatMoney(value, showSign) {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  const sign = showSign && value > 0 ? '+' : '';
  const absValue = Math.abs(value);
  if (absValue < 0.001) return sign + '$0B';
  else if (absValue < 0.1) return sign + '$' + (value * 1000).toFixed(0) + 'M';
  else if (absValue < 1) return sign + '$' + value.toFixed(2) + 'B';
  else if (absValue < 100) return sign + '$' + value.toFixed(1) + 'B';
  else if (absValue < 1000) return sign + '$' + value.toFixed(0) + 'B';
  else return sign + '$' + (value / 1000).toFixed(2) + 'T';
}

function formatPercent(value, decimals) {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  decimals = decimals || 1;
  const sign = value > 0 ? '+' : '';
  return sign + value.toFixed(decimals) + '%';
}

function formatNum(value, decimals) {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  return value.toFixed(decimals || 2);
}

function formatDelta(value, decimals) {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  decimals = decimals || 2;
  const sign = value > 0 ? '+' : '';
  return sign + value.toFixed(decimals);
}

function getScoreStatus(score) {
  if (score === null || score === undefined) return '⚪ N/A';
  if (score > 70) return '🔥 VERY ACTIVE';
  if (score > 50) return '🟢 ACTIVE';
  if (score > 30) return '🟡 MODERATE';
  if (score > 10) return '⚪ LOW';
  return '⚫ MINIMAL';
}

function getVixStatus(vix) {
  if (vix === null || vix === undefined) return '⚪ N/A';
  if (vix > 35) return '🔴🔴 EXTREME';
  if (vix > 25) return '🔴 HIGH';
  if (vix > 20) return '🟡 ELEVATED';
  if (vix > 12) return '🟢 NORMAL';
  return '⚪ LOW';
}

function getMoveStatus(move) {
  if (move === null || move === undefined) return '⚪ N/A';
  if (move > 140) return '🔴🔴 EXTREME';
  if (move > 120) return '🔴 HIGH';
  if (move > 100) return '🟡 ELEVATED';
  if (move > 70) return '🟢 NORMAL';
  return '⚪ CALM';
}

function getZScoreStatus(z) {
  if (z === null || z === undefined || isNaN(z)) return '⚪ N/A';
  if (z > 2) return '🔴🔴 EXTREME';
  if (z > 1) return '🔴 HIGH';
  if (z > -1) return '⚪ NORMAL';
  if (z > -2) return '🟢 LOW';
  return '🟢🟢 EXTREME LOW';
}

function getVixTermStatus(ratio) {
  if (ratio === null || ratio === undefined || isNaN(ratio)) return '⚪ N/A';
  if (ratio < CONFIG.VOL_CONFIG.VIX_RATIO_CONTANGO) return '🟢 CONTANGO';
  if (ratio > CONFIG.VOL_CONFIG.VIX_RATIO_BACKWARDATION) return '🔴 BACKWARDATION';
  return '🟡 FLAT';
}

function getSentimentColor(sentiment) {
  if (sentiment.includes('BULLISH')) return 0x00FF00;
  if (sentiment.includes('BEARISH')) return 0xFF0000;
  return 0xFFD700;
}

// ================= VOLATILITY LEGEND GENERATOR =================
function getVolatilityLegendText() {
  return `
📊 VOLATILITY THRESHOLDS
─────────────────────────────────
VIX (Equity Fear Index)
  🔴🔴 >35  Extreme fear/panic
  🔴   >25  High fear
  🟡   >20  Elevated caution
  🟢   12-20 Normal range
  ⚪   <12  Complacency risk

VIX/VIX3M Term Structure
  🟢 <0.90  Contango (bullish)
  🟡 0.90-1.05 Flat (neutral)
  🔴 >1.05  Backwardation (bearish)

MOVE (Bond Volatility)
  🔴🔴 >140 Extreme bond stress
  🔴   >120 High volatility
  🟡   >100 Elevated
  🟢   70-100 Normal
  ⚪   <70  Calm

Z-Score (vs 20-day avg)
  🔴🔴 >+2  Extremely elevated
  🔴   >+1  Above normal
  ⚪   ±1   Normal range
  🟢   <-1  Below normal
  🟢🟢 <-2  Unusually calm
─────────────────────────────────`;
}

function getVolatilityLegendHTML() {
  return `
<div style="background:#f3e5f5;padding:15px;border:2px solid #4a148c;margin:10px 0;border-radius:8px;">
  <h3 style="margin:0 0 10px 0;color:#4a148c;">📊 VOLATILITY THRESHOLDS LEGEND</h3>
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr style="background:#4a148c;color:#fff;">
      <th style="padding:5px;text-align:left;">Indicator</th>
      <th style="padding:5px;text-align:center;">Level</th>
      <th style="padding:5px;text-align:left;">Interpretation</th>
    </tr>
    <tr><td colspan="3" style="background:#e1bee7;font-weight:bold;padding:5px;">VIX (Equity Fear)</td></tr>
    <tr><td>🔴🔴 Extreme</td><td>>35</td><td>Panic selling / capitulation</td></tr>
    <tr style="background:#f5f5f5;"><td>🔴 High</td><td>>25</td><td>Elevated fear</td></tr>
    <tr><td>🟡 Elevated</td><td>20-25</td><td>Above average caution</td></tr>
    <tr style="background:#f5f5f5;"><td>🟢 Normal</td><td>12-20</td><td>Typical volatility</td></tr>
    <tr><td>⚪ Low</td><td><12</td><td>Complacency warning</td></tr>
    <tr><td colspan="3" style="background:#e1bee7;font-weight:bold;padding:5px;">VIX/VIX3M Ratio</td></tr>
    <tr><td>🟢 Contango</td><td><0.90</td><td>Normal/bullish structure</td></tr>
    <tr style="background:#f5f5f5;"><td>🟡 Flat</td><td>0.90-1.05</td><td>Neutral</td></tr>
    <tr><td>🔴 Backwardation</td><td>>1.05</td><td>Fear spike / bearish</td></tr>
    <tr><td colspan="3" style="background:#e1bee7;font-weight:bold;padding:5px;">MOVE (Bond Volatility)</td></tr>
    <tr><td>🔴🔴 Extreme</td><td>>140</td><td>Bond market stress</td></tr>
    <tr style="background:#f5f5f5;"><td>🔴 High</td><td>>120</td><td>High bond volatility</td></tr>
    <tr><td>🟡 Elevated</td><td>100-120</td><td>Above average</td></tr>
    <tr style="background:#f5f5f5;"><td>🟢 Normal</td><td>70-100</td><td>Typical range</td></tr>
    <tr><td>⚪ Calm</td><td><70</td><td>Low bond vol</td></tr>
    <tr><td colspan="3" style="background:#e1bee7;font-weight:bold;padding:5px;">Z-Score (20-day)</td></tr>
    <tr><td>🔴🔴 Extreme High</td><td>>+2σ</td><td>Extremely elevated vs history</td></tr>
    <tr style="background:#f5f5f5;"><td>🔴 High</td><td>+1 to +2σ</td><td>Above normal</td></tr>
    <tr><td>⚪ Normal</td><td>±1σ</td><td>Within typical range</td></tr>
    <tr style="background:#f5f5f5;"><td>🟢 Low</td><td>-1 to -2σ</td><td>Below normal</td></tr>
    <tr><td>🟢🟢 Extreme Low</td><td><-2σ</td><td>Unusually calm (complacency)</td></tr>
  </table>
</div>`;
}

// ================= MOVE INDEX FETCHER (FIXED) =================
function fetchMoveIndex(startDate) {
  // Method 1: Yahoo Finance v8 Chart API (works without auth)
  try {
    log('📥 Fetching MOVE via Yahoo v8 Chart API...');
    
    const endDate = new Date();
    const start = new Date(startDate);
    
    // Calculate period in days
    const daysDiff = Math.ceil((endDate - start) / (1000 * 60 * 60 * 24));
    
    // Yahoo v8 Chart API - use range parameter
    // Valid ranges: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    let range = 'max';
    if (daysDiff < 30) range = '1mo';
    else if (daysDiff < 90) range = '3mo';
    else if (daysDiff < 180) range = '6mo';
    else if (daysDiff < 365) range = '1y';
    else if (daysDiff < 730) range = '2y';
    else if (daysDiff < 1825) range = '5y';
    
// FIX v3.4.1: Forza range=5y per avere dati giornalieri (max restituisce solo campioni)
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5EMOVE?interval=1d&range=5y';

  
    const options = {
      'muteHttpExceptions': true,
      'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      log('⚠️ MOVE v8 API failed: ' + responseCode);
      return tryAlternativeMoveSource(startDate);
    }
    
    const json = JSON.parse(response.getContentText());
    
    if (!json.chart || !json.chart.result || json.chart.result.length === 0) {
      log('⚠️ MOVE: No data in response');
      return tryAlternativeMoveSource(startDate);
    }
    
    const result = json.chart.result[0];
    const timestamps = result.timestamp;
    const quotes = result.indicators.quote[0];
    const closes = quotes.close;
    
    if (!timestamps || !closes) {
      log('⚠️ MOVE: Missing timestamp or close data');
      return tryAlternativeMoveSource(startDate);
    }
    
    const moveData = {};
    let validCount = 0;
    
    for (let i = 0; i < timestamps.length; i++) {
      if (closes[i] !== null && closes[i] !== undefined) {
        const date = new Date(timestamps[i] * 1000);
        const dateStr = Utilities.formatDate(date, 'GMT', 'yyyy-MM-dd');
        
        // Filter by start date
        if (date >= start) {
          moveData[dateStr] = closes[i];
          validCount++;
        }
      }
    }
    
    log('📥 MOVE: ' + validCount + ' observations via v8 Chart API');
    return moveData;
    
  } catch (error) {
    log('⚠️ MOVE v8 error: ' + error.toString().substring(0, 100));
    return tryAlternativeMoveSource(startDate);
  }
}

function tryAlternativeMoveSource(startDate) {
  // Method 2: Try query2 endpoint
  try {
    log('📥 Trying MOVE via query2 endpoint...');
    
    const url = 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/%5EMOVE?modules=price';
    
    const options = {
      'muteHttpExceptions': true,
      'headers': {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
      }
    };
    
    const response = UrlFetchApp.fetch(url, options);
    
    if (response.getResponseCode() === 200) {
      const json = JSON.parse(response.getContentText());
      
      if (json.quoteSummary && json.quoteSummary.result && json.quoteSummary.result[0]) {
        const price = json.quoteSummary.result[0].price;
        if (price && price.regularMarketPrice) {
          const currentPrice = price.regularMarketPrice.raw;
          const today = Utilities.formatDate(new Date(), 'GMT', 'yyyy-MM-dd');
          log('📥 MOVE current price: ' + currentPrice);
          
          // Return at least current price
          const moveData = {};
          moveData[today] = currentPrice;
          return moveData;
        }
      }
    }
    
    log('⚠️ MOVE: All fetch methods failed');
    return null;
    
  } catch (error) {
    log('⚠️ MOVE alternative error: ' + error.toString().substring(0, 50));
    return null;
  }
}

// Get current MOVE price (for real-time updates)
function getCurrentMovePrice() {
  try {
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5EMOVE?interval=1d&range=5d';
    
    const options = {
      'muteHttpExceptions': true,
      'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    };
    
    const response = UrlFetchApp.fetch(url, options);
    
    if (response.getResponseCode() === 200) {
      const json = JSON.parse(response.getContentText());
      
      if (json.chart && json.chart.result && json.chart.result[0]) {
        const meta = json.chart.result[0].meta;
        if (meta && meta.regularMarketPrice) {
          return meta.regularMarketPrice;
        }
      }
    }
    
    return null;
  } catch (error) {
    return null;
  }
}

// ================= VOLATILITY TRACKER =================
function setupVolatilitySheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let volSheet = ss.getSheetByName('Volatility_Tracker');
  
  if (!volSheet) {
    volSheet = ss.insertSheet('Volatility_Tracker');
  }
  
  const headers = [
    'Date',
    'VIX', 'VIX Δ1d', 'VIX Δ3d', 'VIX Δ7d', 'VIX Δ14d', 'VIX Z-Score',
    'VIX3M', 'VIX3M Δ1d', 'VIX3M Δ3d', 'VIX3M Δ7d', 'VIX3M Δ14d', 'VIX3M Z-Score',
    'VIX/VIX3M Ratio', 'Term Structure',
    'MOVE', 'MOVE Δ1d', 'MOVE Δ3d', 'MOVE Δ7d', 'MOVE Δ14d', 'MOVE Z-Score',
    '10Y-2Y Spread', 'Spread Δ7d',
    'Vol Signal', 'Risk Level'
  ];
  
  volSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  volSheet.getRange(1, 1, 1, headers.length)
    .setFontWeight('bold')
    .setBackground('#4a148c')
    .setFontColor('#ffffff');
  volSheet.setFrozenRows(1);
  
  debug('Volatility sheet setup complete');
}

function downloadVolatilityData() {
  section('DOWNLOADING VOLATILITY DATA');
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const volSheet = ss.getSheetByName('Volatility_Tracker');
  const configSheet = ss.getSheetByName('Config');
  
  const startDateCell = configSheet.getRange('B4').getValue();
  let startDate = '2020-01-01';
  if (startDateCell instanceof Date) {
    startDate = Utilities.formatDate(startDateCell, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  } else if (typeof startDateCell === 'string' && startDateCell.length > 0) {
    startDate = startDateCell;
  }
  
  // Clear existing data
  if (volSheet.getLastRow() > 1) {
    volSheet.getRange(2, 1, volSheet.getLastRow() - 1, volSheet.getLastColumn()).clearContent();
  }
  
  const allData = {};
  
  // Download FRED volatility series
  for (const [seriesId, seriesInfo] of Object.entries(CONFIG.VOLATILITY_SERIES)) {
    const url = 'https://api.stlouisfed.org/fred/series/observations?series_id=' + seriesId + 
                '&api_key=' + CONFIG.FRED_API_KEY + '&file_type=json&observation_start=' + startDate;
    
    try {
      const response = UrlFetchApp.fetch(url);
      const json = JSON.parse(response.getContentText());
      
      let obsCount = 0;
      if (json.observations) {
        json.observations.forEach(function(obs) {
          const date = obs.date;
          let value = obs.value === '.' ? null : parseFloat(obs.value);
          if (!allData[date]) allData[date] = { date: date };
          allData[date][seriesId] = value;
          if (value !== null) obsCount++;
        });
      }
      log('📥 ' + seriesId + ' (' + seriesInfo.name + '): ' + obsCount + ' obs');
    } catch (error) {
      log('⚠️ ' + seriesId + ': ' + error.toString().substring(0, 50));
    }
    Utilities.sleep(300);
  }
  
  // Download MOVE from Yahoo Finance (FIXED in v3.4.1)
  const moveData = fetchMoveIndex(startDate);
  if (moveData) {
    let moveCount = 0;
    for (const [date, value] of Object.entries(moveData)) {
      if (!allData[date]) allData[date] = { date: date };
      allData[date]['MOVE'] = value;
      moveCount++;
    }
    log('📥 MOVE: ' + moveCount + ' obs loaded');
  // === DEBUG: Aggiungi queste righe ===
  const moveKeys = Object.keys(moveData).sort();
  log('🔍 MOVE first date: ' + moveKeys[0]);
  log('🔍 MOVE last date: ' + moveKeys[moveKeys.length - 1]);
  log('🔍 MOVE last value: ' + moveData[moveKeys[moveKeys.length - 1]]);
  // === Fine DEBUG ===
  }
  
  // Process data
  const dates = Object.keys(allData).sort();
  
  // Forward fill
  let lastVIX = null, lastVIX3M = null, lastMOVE = null, lastSpread = null;
  
  const dataArray = dates.map(function(date) {
    const row = allData[date];
    
    if (row.VIXCLS !== null && row.VIXCLS !== undefined) lastVIX = row.VIXCLS;
    if (row.VXVCLS !== null && row.VXVCLS !== undefined) lastVIX3M = row.VXVCLS;
    if (row.MOVE !== null && row.MOVE !== undefined) lastMOVE = row.MOVE;
    if (row.T10Y2Y !== null && row.T10Y2Y !== undefined) lastSpread = row.T10Y2Y;
    
    return {
      date: new Date(date),
      vix: lastVIX,
      vix3m: lastVIX3M,
      move: lastMOVE,
      spread: lastSpread
    };
  });
  
  // Calculate deltas and Z-scores
  const outputData = dataArray.map(function(row, idx) {
    const vix = row.vix;
    const vix3m = row.vix3m;
    const move = row.move;
    const spread = row.spread;
    
    // VIX Deltas
    const vixD1 = idx >= 1 && vix && dataArray[idx-1].vix ? vix - dataArray[idx-1].vix : null;
    const vixD3 = idx >= 3 && vix && dataArray[idx-3].vix ? vix - dataArray[idx-3].vix : null;
    const vixD7 = idx >= 7 && vix && dataArray[idx-7].vix ? vix - dataArray[idx-7].vix : null;
    const vixD14 = idx >= 14 && vix && dataArray[idx-14].vix ? vix - dataArray[idx-14].vix : null;
    
    // VIX3M Deltas
    const vix3mD1 = idx >= 1 && vix3m && dataArray[idx-1].vix3m ? vix3m - dataArray[idx-1].vix3m : null;
    const vix3mD3 = idx >= 3 && vix3m && dataArray[idx-3].vix3m ? vix3m - dataArray[idx-3].vix3m : null;
    const vix3mD7 = idx >= 7 && vix3m && dataArray[idx-7].vix3m ? vix3m - dataArray[idx-7].vix3m : null;
    const vix3mD14 = idx >= 14 && vix3m && dataArray[idx-14].vix3m ? vix3m - dataArray[idx-14].vix3m : null;
    
    // MOVE Deltas
    const moveD1 = idx >= 1 && move && dataArray[idx-1].move ? move - dataArray[idx-1].move : null;
    const moveD3 = idx >= 3 && move && dataArray[idx-3].move ? move - dataArray[idx-3].move : null;
    const moveD7 = idx >= 7 && move && dataArray[idx-7].move ? move - dataArray[idx-7].move : null;
    const moveD14 = idx >= 14 && move && dataArray[idx-14].move ? move - dataArray[idx-14].move : null;
    
    // Spread Delta
    const spreadD7 = idx >= 7 && spread !== null && dataArray[idx-7].spread !== null ? spread - dataArray[idx-7].spread : null;
    
    // Z-Scores (20-day rolling)
    const window = CONFIG.VOL_CONFIG.ZSCORE_WINDOW;
    const vixZ = calculateZScore(dataArray, idx, 'vix', window);
    const vix3mZ = calculateZScore(dataArray, idx, 'vix3m', window);
    const moveZ = calculateZScore(dataArray, idx, 'move', window);
    
    // VIX/VIX3M Ratio
    const vixRatio = vix && vix3m ? vix / vix3m : null;
    const termStructure = getVixTermStatus(vixRatio);
    
    // Overall Vol Signal
    let volSignal = '⚪ NEUTRAL';
    let riskLevel = 'NORMAL';
    
    if (vix !== null) {
      if (vix > 30 || (vixZ !== null && vixZ > 2)) {
        volSignal = '🔴 HIGH FEAR';
        riskLevel = 'ELEVATED';
      } else if (vix > 25 || (vixRatio !== null && vixRatio > 1.05)) {
        volSignal = '🟡 CAUTION';
        riskLevel = 'ABOVE NORMAL';
      } else if (vix < 13 && (vixZ !== null && vixZ < -1.5)) {
        volSignal = '⚠️ COMPLACENCY';
        riskLevel = 'LOW VOL WARNING';
      } else if (vix < 18 && (vixRatio !== null && vixRatio < 0.95)) {
        volSignal = '🟢 RISK-ON';
        riskLevel = 'LOW';
      }
    }
    
    return [
      row.date,
      vix, vixD1, vixD3, vixD7, vixD14, vixZ,
      vix3m, vix3mD1, vix3mD3, vix3mD7, vix3mD14, vix3mZ,
      vixRatio, termStructure,
      move, moveD1, moveD3, moveD7, moveD14, moveZ,
      spread, spreadD7,
      volSignal, riskLevel
    ];
  });
  
  if (outputData.length > 0) {
    volSheet.getRange(2, 1, outputData.length, 25).setValues(outputData);
  }
  
  // Debug last row
  if (CONFIG.DEBUG_MODE && outputData.length > 0) {
    const last = outputData[outputData.length - 1];
    subsection('Volatility Data (Last Row)');
    tableRow('VIX', last[1] ? last[1].toFixed(2) : 'N/A', getVixStatus(last[1]));
    tableRow('VIX Z-Score', last[6] ? last[6].toFixed(2) : 'N/A', getZScoreStatus(last[6]));
    tableRow('VIX3M', last[7] ? last[7].toFixed(2) : 'N/A');
    tableRow('VIX/VIX3M Ratio', last[13] ? last[13].toFixed(3) : 'N/A', last[14] || 'N/A');
    tableRow('MOVE', last[15] ? last[15].toFixed(2) : 'N/A', getMoveStatus(last[15]));
    tableRow('MOVE Z-Score', last[20] ? last[20].toFixed(2) : 'N/A', getZScoreStatus(last[20]));
    tableRow('10Y-2Y Spread', last[21] ? last[21].toFixed(2) + '%' : 'N/A');
    tableRow('Vol Signal', last[23] || 'N/A');
    tableEnd();
  }
  
  log('✅ Written ' + outputData.length + ' volatility rows');
  return { totalRows: outputData.length };
}

function calculateZScore(dataArray, currentIdx, field, window) {
  if (currentIdx < window) return null;
  
  const values = [];
  for (let i = currentIdx - window; i < currentIdx; i++) {
    if (dataArray[i][field] !== null && dataArray[i][field] !== undefined) {
      values.push(dataArray[i][field]);
    }
  }
  
  // FIX: Soglia più bassa per MOVE (50% invece di 80%)
  const minRequired = (field === 'move') ? window * 0.3 : window * 0.8;
  if (values.length < minRequired) return null;
  
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);
  
  if (stdDev === 0) return 0;
  
  const currentVal = dataArray[currentIdx][field];
  if (currentVal === null || currentVal === undefined) return null;
  
  return (currentVal - mean) / stdDev;
}

function getVolatilityMetrics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const volSheet = ss.getSheetByName('Volatility_Tracker');
  
  if (!volSheet || volSheet.getLastRow() < 2) {
    return null;
  }
  
  const lastRow = volSheet.getLastRow();
  const data = volSheet.getRange(lastRow, 1, 1, 25).getValues()[0];
  
  return {
    date: data[0],
    vix: data[1],
    vixD1: data[2],
    vixD3: data[3],
    vixD7: data[4],
    vixD14: data[5],
    vixZ: data[6],
    vix3m: data[7],
    vix3mD1: data[8],
    vix3mD3: data[9],
    vix3mD7: data[10],
    vix3mD14: data[11],
    vix3mZ: data[12],
    vixRatio: data[13],
    termStructure: data[14],
    move: data[15],
    moveD1: data[16],
    moveD3: data[17],
    moveD7: data[18],
    moveD14: data[19],
    moveZ: data[20],
    spread: data[21],
    spreadD7: data[22],
    volSignal: data[23],
    riskLevel: data[24]
  };
}

// ================= DISCORD WEBHOOK =================
function sendDiscordEmbed(type, data) {
  const webhookUrl = CONFIG.DISCORD_WEBHOOK_URL;
  
  if (!webhookUrl || webhookUrl === 'YOUR_DISCORD_WEBHOOK_URL_HERE') {
    if (CONFIG.N8N_ENABLED) {
      sendToN8N(type, data);
    }
    return;
  }
  
  try {
    let payload;
    if (type === 'daily_report') {
      payload = buildDailyReportEmbed(data);
    } else if (type === 'alert') {
      payload = buildAlertEmbed(data);
    }
    
    sendWebhook(webhookUrl, payload);
    
  } catch (error) {
    log('❌ Discord webhook failed: ' + error.toString());
  }
}

function sendWebhook(url, payload) {
  const options = {
    method: 'POST',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  
  if (responseCode >= 200 && responseCode < 300) {
    log('📤 Discord message sent successfully');
  } else {
    log('⚠️ Discord error: ' + responseCode);
  }
}

function buildDailyReportEmbed(data) {
  const timestamp = new Date().toISOString();
  const sentimentColor = getSentimentColor(data.sentiment);
  
  let description = '**' + data.sentiment + '**\n' + data.interpretation + '\n\n';
  description += '```\n';
  description += '╔══════════════════════════════════════╗\n';
  description += '║           EXECUTIVE SUMMARY          ║\n';
  description += '╠══════════════════════════════════════╣\n';
  description += '║ Fed Net Liq:     ' + formatMoney(data.netLiquidity).padStart(18) + ' ║\n';
  description += '║ Global Total:    ' + formatMoney(data.globalLiquidity).padStart(18) + ' ║\n';
  description += '║ Score Daily:     ' + (data.scoreDaily.toFixed(0) + '/100').padStart(18) + ' ║\n';
  description += '╚══════════════════════════════════════╝\n';
  description += '```';
  
  const fields = [
    {
      name: '🇺🇸 FED LIQUIDITY',
      value: '```\n' +
        'Net Liquidity: ' + formatMoney(data.netLiquidity) + '\n' +
        'Weekly Δ:      ' + formatMoney(data.weeklyDelta, true) + '\n' +
        '30d Δ:         ' + formatMoney(data.monthlyDelta, true) + '\n' +
        '60d Δ:         ' + formatMoney(data.delta60d, true) + '\n' +
        '90d Δ:         ' + formatMoney(data.delta90d, true) + '\n' +
        '```',
      inline: true
    },
    {
      name: '🏛️ TGA & RRP',
      value: '```\n' +
        'TGA Level:    ' + formatMoney(data.tgaLevel) + '\n' +
        'TGA Spending: ' + formatMoney(data.tgaSpending) + '/wk\n' +
        'RRP Level:    ' + formatMoney(data.rrpLevel) + (data.rrpLevel < 10 ? ' ⚠️' : '') + '\n' +
        'RRP Velocity: ' + (data.rrpVelocity !== null ? formatPercent(data.rrpVelocity) : 'N/A') + '\n' +
        'SOFR Rate:    ' + (data.sofr * 100).toFixed(2) + '%\n' +
        '```',
      inline: true
    }
  ];
  
  // Add volatility section with current values and status
  if (data.vol) {
    fields.push({ name: '\u200B', value: '\u200B', inline: false });
    fields.push({
      name: '📊 VOLATILITY METRICS',
      value: '```\n' +
        'VIX:      ' + (data.vol.vix ? data.vol.vix.toFixed(2).padStart(6) : '  N/A ') + ' ' + getVixStatus(data.vol.vix) + '\n' +
        'VIX Z:    ' + (data.vol.vixZ ? formatDelta(data.vol.vixZ).padStart(6) : '  N/A ') + ' ' + getZScoreStatus(data.vol.vixZ) + '\n' +
        'VIX Δ7d:  ' + (data.vol.vixD7 ? formatDelta(data.vol.vixD7).padStart(6) : '  N/A ') + '\n' +
        'VIX/VIX3M:' + (data.vol.vixRatio ? data.vol.vixRatio.toFixed(3).padStart(6) : '  N/A ') + '\n' +
        'Term:     ' + (data.vol.termStructure || 'N/A') + '\n' +
        '```',
      inline: true
    });
    fields.push({
      name: '📈 MOVE & BONDS',
      value: '```\n' +
        'MOVE:     ' + (data.vol.move ? data.vol.move.toFixed(2).padStart(6) : '  N/A ') + ' ' + getMoveStatus(data.vol.move) + '\n' +
        'MOVE Z:   ' + (data.vol.moveZ ? formatDelta(data.vol.moveZ).padStart(6) : '  N/A ') + ' ' + getZScoreStatus(data.vol.moveZ) + '\n' +
        'MOVE Δ7d: ' + (data.vol.moveD7 ? formatDelta(data.vol.moveD7).padStart(6) : '  N/A ') + '\n' +
        '10Y-2Y:   ' + (data.vol.spread ? (data.vol.spread.toFixed(2) + '%').padStart(6) : '  N/A ') + '\n' +
        'Signal:   ' + (data.vol.volSignal || 'N/A') + '\n' +
        '```',
      inline: true
    });
    
    // Add volatility thresholds legend
    fields.push({ name: '\u200B', value: '\u200B', inline: false });
    fields.push({
      name: '📖 VOLATILITY THRESHOLDS',
      value: '```\n' +
        'VIX: 🔴>25 🟡>20 🟢12-20 ⚪<12\n' +
        'VIX/VIX3M: 🟢<0.90 🟡0.90-1.05 🔴>1.05\n' +
        'MOVE: 🔴>120 🟡>100 🟢70-100 ⚪<70\n' +
        'Z-Score: 🔴>+1 ⚪±1 🟢<-1\n' +
        '```',
      inline: false
    });
  }
  
  // Global section
  fields.push({ name: '\u200B', value: '\u200B', inline: false });
  fields.push({
    name: '🌍 GLOBAL CENTRAL BANKS',
    value: '```\n' +
      '🇺🇸 Fed:   ' + formatMoney(data.fedNetLiq).padStart(10) + ' │ ' + ((data.fedNetLiq / data.globalLiquidity) * 100).toFixed(0) + '%\n' +
      '🇪🇺 ECB:   ' + formatMoney(data.ecbAssets).padStart(10) + ' │ ' + ((data.ecbAssets / data.globalLiquidity) * 100).toFixed(0) + '%\n' +
      '🇯🇵 BoJ:   ' + formatMoney(data.bojAssets).padStart(10) + ' │ ' + ((data.bojAssets / data.globalLiquidity) * 100).toFixed(0) + '%\n' +
      '🇨🇳 China: ' + formatMoney(data.chinaAssets).padStart(10) + ' │ ' + ((data.chinaAssets / data.globalLiquidity) * 100).toFixed(0) + '%\n' +
      '─────────────────────────\n' +
      'TOTAL:    ' + formatMoney(data.globalLiquidity).padStart(10) + '\n' +
      '```',
    inline: true
  });
  fields.push({
    name: '📊 GLOBAL DELTAS',
    value: '```\n' +
      'Weekly Δ: ' + formatMoney(data.globalWeeklyDelta, true) + '\n' +
      '30d Δ:    ' + formatMoney(data.global30dDelta, true) + '\n' +
      '60d Δ:    ' + formatMoney(data.global60dDelta, true) + '\n' +
      '90d Δ:    ' + formatMoney(data.global90dDelta, true) + '\n' +
      '```',
    inline: true
  });
  
  // Score section
  fields.push({ name: '\u200B', value: '\u200B', inline: false });
  fields.push({
    name: '🔬 STEALTH QE SCORE',
    value: '```\n' +
      '📊 Daily:  ' + data.scoreDaily.toFixed(0).padStart(3) + '/100 │ ' + getScoreStatus(data.scoreDaily) + '\n' +
      '📅 Weekly: ' + (data.scoreWeekly ? data.scoreWeekly.toFixed(0).padStart(3) : 'N/A') + '/100 │ ' + getScoreStatus(data.scoreWeekly) + '\n' +
      '```',
    inline: false
  });
  
  return {
    embeds: [{
      title: '🌍 Global Liquidity Daily Report',
      description: description,
      color: sentimentColor,
      fields: fields,
      footer: {
        text: 'Global Liquidity Monitor v3.4.1 │ Validation: ' + data.validationPassed + '/' + data.validationTotal + ' passed'
      },
      timestamp: timestamp
    }]
  };
}

function buildAlertEmbed(data) {
  const timestamp = new Date().toISOString();
  const isHigh = data.severity === 'HIGH';
  
  return {
    embeds: [{
      title: (isHigh ? '🔥' : '⚠️') + ' ALERT: ' + data.alertType,
      description: '**' + data.message + '**\n\n' + data.details,
      color: isHigh ? 0xFF0000 : 0xFFA500,
      fields: [
        { name: 'Severity', value: '`' + data.severity + '`', inline: true },
        { name: 'Value', value: '`' + String(data.value) + '`', inline: true }
      ],
      footer: { text: 'Global Liquidity Monitor Alert System' },
      timestamp: timestamp
    }]
  };
}

function sendToN8N(type, data) {
  if (!CONFIG.N8N_ENABLED) return;
  
  try {
    const payload = {
      type: type,
      timestamp: new Date().toISOString(),
      source: 'Global Liquidity Monitor v3.4.1',
      metrics: {
        fed: {
          netLiquidity: data.netLiquidity,
          weeklyDelta: data.weeklyDelta,
          monthlyDelta: data.monthlyDelta,
          delta60d: data.delta60d,
          delta90d: data.delta90d,
          sofr: data.sofr,
          rrpLevel: data.rrpLevel,
          rrpVelocity: data.rrpVelocity,
          tgaLevel: data.tgaLevel,
          tgaSpending: data.tgaSpending,
          scoreDaily: data.scoreDaily,
          scoreWeekly: data.scoreWeekly
        },
        global: {
          totalLiquidity: data.globalLiquidity,
          weeklyDelta: data.globalWeeklyDelta,
          delta30d: data.global30dDelta,
          delta60d: data.global60dDelta,
          delta90d: data.global90dDelta,
          ecb: data.ecbAssets,
          boj: data.bojAssets,
          china: data.chinaAssets
        },
        volatility: data.vol || null,
        sentiment: data.sentiment
      }
    };
    
    const options = {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(CONFIG.N8N_WEBHOOK_URL, options);
    if (response.getResponseCode() >= 200 && response.getResponseCode() < 300) {
      log('📤 Data sent to n8n');
    }
  } catch (error) {
    log('⚠️ n8n webhook error: ' + error.toString());
  }
}

// ================= CROSS-VALIDATION (FIXED for 0==0) =================
function validateCheck(name, condition, details, severity) {
  severity = severity || 'ERROR';
  const result = { name: name, passed: condition, details: details, severity: severity };
  VALIDATION_RESULTS.checks.push(result);
  
  if (condition) {
    VALIDATION_RESULTS.passed++;
    if (CONFIG.DEBUG_MODE) log('  ✅ PASS: ' + name + ' - ' + details);
  } else if (severity === 'WARNING') {
    VALIDATION_RESULTS.warnings++;
    log('  ⚠️ WARN: ' + name + ' - ' + details);
  } else {
    VALIDATION_RESULTS.failed++;
    log('  ❌ FAIL: ' + name + ' - ' + details);
  }
  return condition;
}

function crossValidate(label, value1, value2, tolerance) {
  tolerance = tolerance || CONFIG.VALIDATION_TOLERANCE;
  
  if (Math.abs(value1 || 0) < 0.001 && Math.abs(value2 || 0) < 0.001) {
    return validateCheck(label, true, 'Both values ~0: v1=' + value1 + ', v2=' + value2, 'INFO');
  }
  
  if (value1 === null || value2 === null || value1 === 0) {
    return validateCheck(label, false, 'Cannot compare: v1=' + value1 + ', v2=' + value2, 'WARNING');
  }
  
  const pctDiff = Math.abs((value1 - value2) / value1) * 100;
  const passed = pctDiff <= (tolerance * 100);
  return validateCheck(label, passed, 
    'Expected: ' + formatNum(value1) + ', Got: ' + formatNum(value2) + ' (diff: ' + pctDiff.toFixed(3) + '%)',
    passed ? 'INFO' : 'ERROR');
}

function runCrossValidation(rawData, rmpData, dashData) {
  if (!CONFIG.CROSS_VALIDATION) return { checks: [], passed: 0, failed: 0, warnings: 0 };
  
  section('CROSS-VALIDATION CHECKS');
  VALIDATION_RESULTS = { checks: [], passed: 0, failed: 0, warnings: 0 };
  
  const lastRaw = rawData[rawData.length - 1];
  const lastRmp = rmpData[rmpData.length - 1];
  const lastDash = dashData[dashData.length - 1];
  
  // Check 1: Net Liquidity
  subsection('Check 1: Net Liquidity Formula');
  const walcl = lastRaw[11] / 1000;
  const tga = lastRaw[13] / 1000;
  const rrp = lastRaw[14] / 1000;
  const calcNetLiq = walcl - tga - rrp;
  const reportedNetLiq = lastDash[1];
  tableRow('WALCL', formatMoney(walcl));
  tableRow('TGA', '-' + formatMoney(tga));
  tableRow('RRP', '-' + formatMoney(rrp));
  tableRow('Calculated', formatMoney(calcNetLiq));
  tableRow('Reported', formatMoney(reportedNetLiq));
  tableEnd();
  crossValidate('Net Liquidity', calcNetLiq, reportedNetLiq, 0.001);
  
  // Check 2: RRP Consistency
  subsection('Check 2: RRP Consistency');
  const rrpFromRaw = lastRaw[14] / 1000;
  const rrpFromRmp = lastRmp[5];
  tableRow('RRP Raw_Data', formatMoney(rrpFromRaw));
  tableRow('RRP RMP_Tracker', formatMoney(rrpFromRmp));
  tableEnd();
  crossValidate('RRP Consistency', rrpFromRaw, rrpFromRmp, 0.001);
  
  // Check 3: Weekly Delta
  if (rawData.length >= 8) {
    subsection('Check 3: Weekly Delta');
    const prevRaw = rawData[rawData.length - 8];
    const prevNetLiq = ((prevRaw[11] || 0) - (prevRaw[13] || 0) - (prevRaw[14] || 0)) / 1000;
    const calcWeeklyDelta = calcNetLiq - prevNetLiq;
    const reportedWeeklyDelta = lastDash[2];
    tableRow('Calc Delta', formatMoney(calcWeeklyDelta, true));
    tableRow('Reported Delta', formatMoney(reportedWeeklyDelta, true));
    tableEnd();
    crossValidate('Weekly Delta', calcWeeklyDelta, reportedWeeklyDelta, 0.01);
  }
  
  // Check 4: RRP Velocity
  if (rawData.length >= 8) {
    subsection('Check 4: RRP Velocity');
    const prevRrp = rawData[rawData.length - 8][14] / 1000;
    const currRrp = rrpFromRaw;
    
    let calcVelocity;
    if (prevRrp > 0.5) {
      calcVelocity = ((currRrp - prevRrp) / prevRrp) * 100;
    } else if (currRrp < 0.5) {
      calcVelocity = 0;
    } else {
      calcVelocity = null;
    }
    
    const reportedVelocity = lastRmp[9];
    tableRow('RRP 7d ago', formatMoney(prevRrp));
    tableRow('RRP now', formatMoney(currRrp));
    tableRow('Calc Velocity', calcVelocity !== null ? formatPercent(calcVelocity) : 'N/A (RRP depleted)');
    tableRow('Reported Velocity', reportedVelocity !== null ? formatPercent(reportedVelocity) : 'N/A');
    tableEnd();
    crossValidate('RRP Velocity', calcVelocity, reportedVelocity, 0.05);
  }
  
  // Check 5: TGA Spending
  if (rawData.length >= 8) {
    subsection('Check 5: TGA Spending');
    const prevTga = rawData[rawData.length - 8][13] / 1000;
    const calcSpending = -(tga - prevTga);
    const reportedSpending = lastRmp[12];
    tableRow('Calc Spending', formatMoney(calcSpending, true));
    tableRow('Reported Spending', formatMoney(reportedSpending, true));
    tableEnd();
    crossValidate('TGA Spending', calcSpending, reportedSpending, 0.01);
  }
  
  // Check 6: Data Freshness
  subsection('Check 6: Data Freshness');
  const lastDate = lastRaw[0];
  const daysSince = (new Date() - lastDate) / (1000 * 60 * 60 * 24);
  tableRow('Last Data', Utilities.formatDate(lastDate, Session.getScriptTimeZone(), 'yyyy-MM-dd'));
  tableRow('Days Since', daysSince.toFixed(1));
  tableEnd();
  validateCheck('Data Freshness', daysSince <= 5, daysSince.toFixed(1) + ' days ago', daysSince <= 5 ? 'INFO' : 'WARNING');
  
  // Summary
  section('VALIDATION SUMMARY');
  log('┌────────────────────────────────────────────────────────────────────┐');
  tableRow('Checks Passed', VALIDATION_RESULTS.passed, '✅');
  tableRow('Checks Failed', VALIDATION_RESULTS.failed, VALIDATION_RESULTS.failed > 0 ? '❌' : '');
  tableRow('Warnings', VALIDATION_RESULTS.warnings, VALIDATION_RESULTS.warnings > 0 ? '⚠️' : '');
  log('├────────────────────────────────────────────────────────────────────┤');
  const status = VALIDATION_RESULTS.failed === 0 ? '✅ ALL CHECKS PASSED' : '❌ VALIDATION FAILED';
  log('│ Status: ' + status.padEnd(59) + '│');
  log('└────────────────────────────────────────────────────────────────────┘');
  
  return VALIDATION_RESULTS;
}

// ================= EMAIL FUNCTIONS =================
function sendDailyReport(alerts, rmp, liq, global, vol, val) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const maxScore = Math.max(rmp.scoreDaily, rmp.scoreWeekly || 0);
  const subject = '✅ Global Liquidity v3.4.1 - ' + liq.sentiment + ' | Score: ' + maxScore.toFixed(0) + '/100';
  
  let body = '<div style="font-family:Arial;max-width:900px;margin:0 auto;">';
  body += '<div style="background:linear-gradient(135deg,#1c4587,#4a148c);color:#fff;padding:20px;border-radius:10px 10px 0 0;">';
  body += '<h1 style="margin:0;">🌍 GLOBAL LIQUIDITY + VOLATILITY REPORT</h1>';
  body += '<p style="margin:5px 0 0 0;opacity:0.9;">v3.4.1 - Fed + ECB + BoJ + China + VIX + MOVE</p></div>';
  
  const bgColor = liq.sentiment.includes('BULLISH') ? '#d9ead3' : (liq.sentiment.includes('BEARISH') ? '#f4cccc' : '#fff2cc');
  body += '<div style="background:' + bgColor + ';padding:15px;border:2px solid #ccc;"><h2 style="margin:0;">📈 ' + liq.sentiment + '</h2></div>';
  
  // Fed section
  body += '<div style="background:#f8f9fa;padding:20px;border:1px solid #ddd;margin:10px 0;">';
  body += '<h3 style="margin:0 0 15px 0;">🇺🇸 FED LIQUIDITY</h3>';
  body += '<table style="width:100%;"><tr><td><b>Net Liquidity</b></td><td>' + formatMoney(liq.netLiquidity) + '</td>';
  body += '<td><b>Weekly Δ</b></td><td>' + formatMoney(liq.weeklyDelta, true) + '</td></tr>';
  body += '<tr><td><b>TGA</b></td><td>' + formatMoney(rmp.tgaLevel) + '</td><td><b>TGA Spending</b></td><td>' + formatMoney(rmp.tgaSpending) + '/wk</td></tr>';
  body += '<tr><td><b>RRP</b></td><td>' + formatMoney(rmp.rrpLevel) + '</td><td><b>RRP Velocity</b></td><td>' + (rmp.rrpVelocity !== null ? formatPercent(rmp.rrpVelocity) : 'N/A') + '</td></tr></table></div>';
  
  // Volatility section with LEGEND
  if (vol) {
    body += '<div style="background:#f3e5f5;padding:20px;border:2px solid #4a148c;margin:10px 0;">';
    body += '<h3 style="margin:0 0 15px 0;color:#4a148c;">📊 VOLATILITY METRICS</h3>';
    body += '<table style="width:100%;">';
    body += '<tr><td><b>VIX</b></td><td>' + (vol.vix ? vol.vix.toFixed(2) : 'N/A') + ' <span style="background:#e1bee7;padding:2px 6px;border-radius:4px;">' + getVixStatus(vol.vix) + '</span></td>';
    body += '<td><b>VIX Z-Score</b></td><td>' + (vol.vixZ ? formatDelta(vol.vixZ) : 'N/A') + ' <span style="background:#e1bee7;padding:2px 6px;border-radius:4px;">' + getZScoreStatus(vol.vixZ) + '</span></td></tr>';
    body += '<tr><td><b>VIX Δ7d</b></td><td>' + (vol.vixD7 ? formatDelta(vol.vixD7) : 'N/A') + '</td>';
    body += '<td><b>VIX/VIX3M</b></td><td>' + (vol.vixRatio ? vol.vixRatio.toFixed(3) : 'N/A') + ' <span style="background:#e1bee7;padding:2px 6px;border-radius:4px;">' + (vol.termStructure || 'N/A') + '</span></td></tr>';
    body += '<tr><td><b>MOVE</b></td><td>' + (vol.move ? vol.move.toFixed(2) : 'N/A') + ' <span style="background:#e1bee7;padding:2px 6px;border-radius:4px;">' + getMoveStatus(vol.move) + '</span></td>';
    body += '<td><b>MOVE Z-Score</b></td><td>' + (vol.moveZ ? formatDelta(vol.moveZ) : 'N/A') + ' <span style="background:#e1bee7;padding:2px 6px;border-radius:4px;">' + getZScoreStatus(vol.moveZ) + '</span></td></tr>';
    body += '<tr><td><b>10Y-2Y Spread</b></td><td>' + (vol.spread ? vol.spread.toFixed(2) + '%' : 'N/A') + '</td>';
    body += '<td><b>Vol Signal</b></td><td><b>' + (vol.volSignal || 'N/A') + '</b></td></tr></table></div>';
    
    // ADD VOLATILITY LEGEND HTML
    body += getVolatilityLegendHTML();
  }
  
  // Global section
  body += '<div style="background:#e3f2fd;padding:20px;border:2px solid #1976d2;margin:10px 0;">';
  body += '<h3 style="margin:0 0 15px 0;color:#1976d2;">🌍 GLOBAL CENTRAL BANKS</h3>';
  body += '<table style="width:100%;"><tr style="background:#1976d2;color:#fff;"><th>Region</th><th>Assets (USD)</th><th>%</th></tr>';
  body += '<tr><td>🇺🇸 Fed</td><td>' + formatMoney(global.fedNetLiq) + '</td><td>' + ((global.fedNetLiq / global.totalUSD) * 100).toFixed(0) + '%</td></tr>';
  body += '<tr style="background:#f5f5f5;"><td>🇪🇺 ECB</td><td>' + formatMoney(global.ecbUSD) + '</td><td>' + ((global.ecbUSD / global.totalUSD) * 100).toFixed(0) + '%</td></tr>';
  body += '<tr><td>🇯🇵 BoJ</td><td>' + formatMoney(global.bojUSD) + '</td><td>' + ((global.bojUSD / global.totalUSD) * 100).toFixed(0) + '%</td></tr>';
  body += '<tr style="background:#f5f5f5;"><td>🇨🇳 China</td><td>' + formatMoney(global.chinaUSD) + '</td><td>' + ((global.chinaUSD / global.totalUSD) * 100).toFixed(0) + '%</td></tr>';
  body += '<tr style="background:#1976d2;color:#fff;font-weight:bold;"><td>TOTAL</td><td>' + formatMoney(global.totalUSD) + '</td><td>100%</td></tr></table>';
  body += '<p style="margin-top:10px;">Weekly: ' + formatMoney(global.weeklyDelta, true) + ' | 30d: ' + formatMoney(global.delta30d, true) + ' | 60d: ' + formatMoney(global.delta60d, true) + ' | 90d: ' + formatMoney(global.delta90d, true) + '</p></div>';
  
  // Score
  body += '<div style="background:#e8f5e9;padding:20px;border:2px solid #38761d;margin:10px 0;">';
  body += '<h3 style="margin:0 0 15px 0;color:#38761d;">🔬 STEALTH QE SCORE</h3>';
  body += '<table><tr><td><b>📊 DAILY</b></td><td style="font-size:24px;">' + rmp.scoreDaily.toFixed(0) + '/100</td><td>' + getScoreStatus(rmp.scoreDaily) + '</td></tr>';
  body += '<tr><td><b>📅 WEEKLY</b></td><td style="font-size:24px;">' + (rmp.scoreWeekly ? rmp.scoreWeekly.toFixed(0) : 'N/A') + '/100</td><td>' + getScoreStatus(rmp.scoreWeekly) + '</td></tr></table></div>';
  
  // Alerts
  if (alerts && alerts.length > 0) {
    body += '<div style="background:#f4cccc;padding:15px;border:2px solid #cc0000;margin:10px 0;">';
    body += '<h3 style="margin:0 0 10px 0;color:#cc0000;">🚨 ALERTS (' + alerts.length + ')</h3>';
    alerts.forEach(function(a) { body += '<p style="margin:5px 0;"><strong>' + a.message + '</strong> - ' + a.details + '</p>'; });
    body += '</div>';
  }
  
  body += '<div style="text-align:center;padding:15px;border-top:2px solid #1c4587;margin-top:15px;">';
  body += '<p>🔗 <a href="' + ss.getUrl() + '">Open Dashboard</a></p>';
  body += '<p style="color:#666;font-size:11px;">📅 ' + new Date().toLocaleString('en-US') + ' | Validation: ' + val.passed + '/' + val.checks.length + '</p></div></div>';
  
  MailApp.sendEmail({ to: CONFIG.EMAIL, subject: subject, htmlBody: body });
  log('📧 Daily report sent');
}

function sendQualityReport(quality, val) {
  const subject = (quality.overall === 'OK' ? '🟢' : '🟡') + ' Liquidity Quality: ' + quality.overall;
  MailApp.sendEmail({ to: CONFIG.EMAIL, subject: subject, htmlBody: '<h2>Quality: ' + quality.overall + '</h2><p>Validation: ' + val.passed + '/' + val.checks.length + '</p>' });
}

function sendAlertEmail(alerts) {
  if (!alerts.length) return;
  let body = '<h2>Liquidity Alerts</h2><ul>';
  alerts.forEach(function(a) { body += '<li><strong>' + a.message + '</strong>: ' + a.details + '</li>'; });
  body += '</ul>';
  MailApp.sendEmail({ to: CONFIG.EMAIL, subject: '🚨 Liquidity Alert', htmlBody: body });
}

function sendErrorEmail(error) {
  MailApp.sendEmail({ to: CONFIG.EMAIL, subject: '🔴 Liquidity Monitor Error', htmlBody: '<pre>' + error.toString() + '\n' + error.stack + '</pre>' });
}

// ================= MAIN FUNCTION =================
function updateLiquidity() {
  const startTime = new Date();
  
  try {
    log('');
    log('╔══════════════════════════════════════════════════════════════════════╗');
    log('║      GLOBAL LIQUIDITY MONITOR v3.4.1 - UPDATE STARTED                ║');
    log('║      ' + startTime.toLocaleString('en-US').padEnd(62) + '║');
    log('╚══════════════════════════════════════════════════════════════════════╝');
    
    debug('Debug Mode', 'ENABLED');
    debug('Discord', CONFIG.DISCORD_WEBHOOK_URL && CONFIG.DISCORD_WEBHOOK_URL !== 'YOUR_DISCORD_WEBHOOK_URL_HERE' ? 'CONFIGURED' : 'NOT SET');
    debug('N8N', CONFIG.N8N_ENABLED ? 'ENABLED' : 'DISABLED');
    
    setupSheets();
    setupRMPTracker();
    setupGlobalSheet();
    setupVolatilitySheet();
    setupLegendSheet();
    
    const fedStats = downloadFREDData();
    const globalStats = downloadGlobalData();
    const volStats = downloadVolatilityData();
    
    if (new Date().getDay() === 4) {
      const h41Data = scrapeFedH41();
      if (h41Data) saveH41Data(h41Data);
    }
    
    const qualityReport = validateDataQuality();
    const liquidityResult = calculateLiquidity();
    const rmpResult = calculateRMPMetrics();
    const globalResult = calculateGlobalLiquidity();
    const volResult = getVolatilityMetrics();
    const alerts = checkAlerts(liquidityResult, rmpResult, globalResult, volResult);
    
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const rawSheet = ss.getSheetByName('Raw_Data');
    const rmpSheet = ss.getSheetByName('RMP_Tracker');
    const dashSheet = ss.getSheetByName('Dashboard');
    
    const rawData = rawSheet.getRange(2, 1, rawSheet.getLastRow() - 1, 15).getValues();
    const rmpData = rmpSheet.getRange(2, 1, rmpSheet.getLastRow() - 1, 23).getValues();
    const dashData = dashSheet.getRange(2, 1, dashSheet.getLastRow() - 1, 8).getValues();
    
    const validationResults = runCrossValidation(rawData, rmpData, dashData);
    
    const endTime = new Date();
    const duration = (endTime - startTime) / 1000;
    
    section('EXECUTION SUMMARY');
    log('┌────────────────────────────────────────────────────────────────────┐');
    tableRow('Execution Time', duration.toFixed(1) + ' seconds');
    tableRow('Fed Rows', fedStats.totalRows);
    tableRow('Global Series', globalStats.seriesCount);
    tableRow('Volatility Rows', volStats.totalRows);
    log('├─────────────────── FED LIQUIDITY ──────────────────────────────────┤');
    tableRow('NET LIQUIDITY', formatMoney(liquidityResult.netLiquidity));
    tableRow('Weekly Δ', formatMoney(liquidityResult.weeklyDelta, true));
    tableRow('30d Δ', formatMoney(liquidityResult.monthlyDelta, true));
    tableRow('60d Δ', formatMoney(liquidityResult.delta60d, true));
    tableRow('90d Δ', formatMoney(liquidityResult.delta90d, true));
    tableRow('TGA Level', formatMoney(rmpResult.tgaLevel));
    tableRow('TGA Spending', formatMoney(rmpResult.tgaSpending) + '/wk');
    tableRow('RRP Level', formatMoney(rmpResult.rrpLevel));
    tableRow('RRP Velocity', rmpResult.rrpVelocity !== null ? formatPercent(rmpResult.rrpVelocity) : 'N/A');
    log('├─────────────────── VOLATILITY ──────────────────────────────────────┤');
    if (volResult) {
      tableRow('VIX', volResult.vix ? volResult.vix.toFixed(2) : 'N/A', getVixStatus(volResult.vix));
      tableRow('VIX Z-Score', volResult.vixZ ? formatDelta(volResult.vixZ) : 'N/A', getZScoreStatus(volResult.vixZ));
      tableRow('VIX/VIX3M Ratio', volResult.vixRatio ? volResult.vixRatio.toFixed(3) : 'N/A', volResult.termStructure);
      tableRow('MOVE', volResult.move ? volResult.move.toFixed(2) : 'N/A', getMoveStatus(volResult.move));
      tableRow('MOVE Z-Score', volResult.moveZ ? formatDelta(volResult.moveZ) : 'N/A', getZScoreStatus(volResult.moveZ));
      tableRow('10Y-2Y Spread', volResult.spread ? volResult.spread.toFixed(2) + '%' : 'N/A');
      tableRow('Vol Signal', volResult.volSignal || 'N/A');
    } else {
      tableRow('Volatility Data', 'Not available');
    }
    log('├─────────────────── GLOBAL LIQUIDITY ───────────────────────────────┤');
    tableRow('TOTAL GLOBAL', formatMoney(globalResult.totalUSD));
    tableRow('Weekly Δ', formatMoney(globalResult.weeklyDelta, true));
    tableRow('30d Δ', formatMoney(globalResult.delta30d, true));
    tableRow('60d Δ', formatMoney(globalResult.delta60d, true));
    tableRow('90d Δ', formatMoney(globalResult.delta90d, true));
    tableRow('ECB (USD)', formatMoney(globalResult.ecbUSD));
    tableRow('BoJ (USD)', formatMoney(globalResult.bojUSD));
    tableRow('China FX (USD)', formatMoney(globalResult.chinaUSD));
    log('├─────────────────── SCORES & ALERTS ─────────────────────────────────┤');
    tableRow('SCORE DAILY', rmpResult.scoreDaily.toFixed(1) + '/100');
    tableRow('SCORE WEEKLY', (rmpResult.scoreWeekly ? rmpResult.scoreWeekly.toFixed(1) : 'N/A') + '/100');
    tableRow('Alerts', alerts.length);
    tableRow('Validation', validationResults.failed === 0 ? 'PASSED' : 'FAILED');
    log('└────────────────────────────────────────────────────────────────────┘');
    
    const interpretation = generateInterpretation(liquidityResult.weeklyDelta, liquidityResult.monthlyDelta, liquidityResult.sofr);
    
    const reportData = {
      netLiquidity: liquidityResult.netLiquidity,
      weeklyDelta: liquidityResult.weeklyDelta,
      monthlyDelta: liquidityResult.monthlyDelta,
      delta60d: liquidityResult.delta60d,
      delta90d: liquidityResult.delta90d,
      sofr: liquidityResult.sofr,
      sentiment: liquidityResult.sentiment,
      interpretation: interpretation.text,
      rrpLevel: rmpResult.rrpLevel,
      rrpVelocity: rmpResult.rrpVelocity,
      tgaLevel: rmpResult.tgaLevel,
      tgaSpending: rmpResult.tgaSpending,
      scoreDaily: rmpResult.scoreDaily,
      scoreWeekly: rmpResult.scoreWeekly,
      globalLiquidity: globalResult.totalUSD,
      globalWeeklyDelta: globalResult.weeklyDelta,
      global30dDelta: globalResult.delta30d,
      global60dDelta: globalResult.delta60d,
      global90dDelta: globalResult.delta90d,
      fedNetLiq: globalResult.fedNetLiq,
      ecbAssets: globalResult.ecbUSD,
      bojAssets: globalResult.bojUSD,
      chinaAssets: globalResult.chinaUSD,
      vol: volResult,
      validationPassed: validationResults.passed,
      validationTotal: validationResults.checks.length
    };
    
    sendDiscordEmbed('daily_report', reportData);
    
    alerts.forEach(function(alert) {
      sendDiscordEmbed('alert', {
        alertType: alert.type,
        severity: alert.severity,
        message: alert.message,
        details: alert.details,
        value: alert.value
      });
    });
    
    sendDailyReport(alerts, rmpResult, liquidityResult, globalResult, volResult, validationResults);
    sendQualityReport(qualityReport, validationResults);
    if (alerts.length > 0) sendAlertEmail(alerts);
    
    ss.getSheetByName('Config').getRange('B1').setValue(new Date());
    
    log('✅ COMPLETED v3.4.1 in ' + duration.toFixed(1) + ' seconds');
    
  } catch (error) {
    log('❌ ERROR: ' + error.toString());
    log('Stack: ' + error.stack);
    sendErrorEmail(error);
  }
}

function updateWithCharts() {
  updateLiquidity();
  createDashboardCharts();
  createRMPCharts();
  createGlobalCharts();
  createVolatilityCharts();
}

// ================= SHEET SETUP =================
function setupSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  let configSheet = ss.getSheetByName('Config');
  if (!configSheet) {
    configSheet = ss.insertSheet('Config');
    configSheet.getRange('A1:B4').setValues([
      ['Last Update', new Date()],
      ['API Key', CONFIG.FRED_API_KEY],
      ['Email', CONFIG.EMAIL],
      ['Start Date', '2020-01-01']
    ]);
    configSheet.getRange('A1:A4').setFontWeight('bold');
  }
  
  ['Raw_Data', 'Dashboard', 'Data_Quality', 'Alert_Log', 'Global_CB', 'Global_Dashboard'].forEach(function(name) {
    if (!ss.getSheetByName(name)) {
      ss.insertSheet(name);
    }
  });
}

function setupRMPTracker() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let rmpSheet = ss.getSheetByName('RMP_Tracker');
  
  if (!rmpSheet) {
    rmpSheet = ss.insertSheet('RMP_Tracker');
  }
  
  const headers = [
    'Date', 'Fed Total Assets (B$)', 'Fed Treasuries (B$)', 'Fed MBS (B$)', 'Fed Other (B$)',
    'RRP Level (B$)', 'RRP % of Assets', 'RRP Weekly Δ (B$)', 'RRP Monthly Δ (B$)', 'RRP Velocity (%)',
    'TGA Level (B$)', 'TGA Weekly Δ (B$)', 'TGA Spending Rate (B$/wk)', 'Treasury Δ (B$)', 'MBS Δ (B$)',
    'Score DAILY', 'Score WEEKLY', 'Score Components',
    'BTFP Activity (B$)', 'Bills (B$)', 'Bonds (B$)', 'Bills %', 'Is Wed Data'
  ];
  
  rmpSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  rmpSheet.getRange(1, 1, 1, headers.length)
    .setFontWeight('bold')
    .setBackground('#1c4587')
    .setFontColor('#ffffff');
  rmpSheet.setFrozenRows(1);
}

function setupGlobalSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let globalSheet = ss.getSheetByName('Global_CB');
  
  if (!globalSheet) {
    globalSheet = ss.insertSheet('Global_CB');
  }
  
  const headers = [
    'Date',
    'ECB Assets (EUR B)', 'ECB Rate (%)',
    'BoJ Assets (JPY T)',
    'China FX (USD B)',
    'EUR/USD', 'JPY/USD', 'CNY/USD',
    'ECB (USD B)', 'BoJ (USD B)', 'China (USD B)',
    'Total Global (USD B)', 'Global Weekly Δ', 'Global 30d Δ', 'Global 60d Δ', 'Global 90d Δ'
  ];
  
  globalSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  globalSheet.getRange(1, 1, 1, headers.length)
    .setFontWeight('bold')
    .setBackground('#38761d')
    .setFontColor('#ffffff');
  globalSheet.setFrozenRows(1);
}

function setupLegendSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let legendSheet = ss.getSheetByName('Legend');
  
  if (!legendSheet) {
    legendSheet = ss.insertSheet('Legend');
  }
  
  legendSheet.clear();
  
  legendSheet.getRange('A1').setValue('📊 TRAFFIC LIGHT LEGEND - Global Liquidity Monitor v3.4.1');
  legendSheet.getRange('A1:D1').merge().setFontWeight('bold').setFontSize(14).setBackground('#1c4587').setFontColor('#ffffff');
  
  let row = 3;
  
  // Score Legend
  legendSheet.getRange('A' + row).setValue('🔬 STEALTH QE SCORE');
  legendSheet.getRange('A' + row + ':D' + row).merge().setFontWeight('bold').setBackground('#e8eaed');
  row++;
  const scoreItems = [
    ['🔥 VERY ACTIVE (70-100)', 'Major liquidity injection in progress'],
    ['🟢 ACTIVE (50-70)', 'Stealth QE detected. Bullish'],
    ['🟡 MODERATE (30-50)', 'Some injection signals. Neutral'],
    ['⚪ LOW (10-30)', 'Minimal activity'],
    ['⚫ MINIMAL (0-10)', 'No hidden injection']
  ];
  scoreItems.forEach(function(item) {
    legendSheet.getRange('A' + row).setValue(item[0]);
    legendSheet.getRange('B' + row + ':D' + row).merge().setValue(item[1]);
    row++;
  });
  row++;
  
  // VIX Legend
  legendSheet.getRange('A' + row).setValue('📊 VIX LEVELS (Equity Volatility)');
  legendSheet.getRange('A' + row + ':D' + row).merge().setFontWeight('bold').setBackground('#f3e5f5');
  row++;
  const vixItems = [
    ['🔴🔴 EXTREME (>35)', 'Panic selling / capitulation'],
    ['🔴 HIGH (>25)', 'Elevated fear'],
    ['🟡 ELEVATED (20-25)', 'Above average caution'],
    ['🟢 NORMAL (12-20)', 'Typical volatility environment'],
    ['⚪ LOW (<12)', 'Complacency - contrarian sell signal']
  ];
  vixItems.forEach(function(item) {
    legendSheet.getRange('A' + row).setValue(item[0]);
    legendSheet.getRange('B' + row + ':D' + row).merge().setValue(item[1]);
    row++;
  });
  row++;
  
  // VIX Term Structure
  legendSheet.getRange('A' + row).setValue('📈 VIX/VIX3M TERM STRUCTURE');
  legendSheet.getRange('A' + row + ':D' + row).merge().setFontWeight('bold').setBackground('#f3e5f5');
  row++;
  const termItems = [
    ['🟢 CONTANGO (<0.90)', 'VIX < VIX3M = Normal/Bullish structure'],
    ['🟡 FLAT (0.90-1.05)', 'Neutral term structure'],
    ['🔴 BACKWARDATION (>1.05)', 'VIX > VIX3M = Fear spike, bearish']
  ];
  termItems.forEach(function(item) {
    legendSheet.getRange('A' + row).setValue(item[0]);
    legendSheet.getRange('B' + row + ':D' + row).merge().setValue(item[1]);
    row++;
  });
  row++;
  
  // MOVE Legend
  legendSheet.getRange('A' + row).setValue('📈 MOVE INDEX (Bond Volatility)');
  legendSheet.getRange('A' + row + ':D' + row).merge().setFontWeight('bold').setBackground('#e3f2fd');
  row++;
  const moveItems = [
    ['🔴🔴 EXTREME (>140)', 'Bond market stress / crisis'],
    ['🔴 HIGH (>120)', 'High bond volatility'],
    ['🟡 ELEVATED (100-120)', 'Above average'],
    ['🟢 NORMAL (70-100)', 'Typical range'],
    ['⚪ CALM (<70)', 'Low bond volatility']
  ];
  moveItems.forEach(function(item) {
    legendSheet.getRange('A' + row).setValue(item[0]);
    legendSheet.getRange('B' + row + ':D' + row).merge().setValue(item[1]);
    row++;
  });
  row++;
  
  // Z-Score Legend
  legendSheet.getRange('A' + row).setValue('📉 Z-SCORE (vs 20-day average)');
  legendSheet.getRange('A' + row + ':D' + row).merge().setFontWeight('bold').setBackground('#fff3e0');
  row++;
  const zItems = [
    ['🔴🔴 EXTREME HIGH (>+2σ)', 'Extremely elevated vs recent history'],
    ['🔴 HIGH (+1 to +2σ)', 'Above normal'],
    ['⚪ NORMAL (±1σ)', 'Within typical range'],
    ['🟢 LOW (-1 to -2σ)', 'Below normal'],
    ['🟢🟢 EXTREME LOW (<-2σ)', 'Unusually calm - complacency risk']
  ];
  zItems.forEach(function(item) {
    legendSheet.getRange('A' + row).setValue(item[0]);
    legendSheet.getRange('B' + row + ':D' + row).merge().setValue(item[1]);
    row++;
  });
  
  legendSheet.setColumnWidth(1, 220);
  legendSheet.setColumnWidth(2, 150);
  legendSheet.setColumnWidth(3, 150);
  legendSheet.setColumnWidth(4, 150);
  
  debug('Legend sheet created with volatility thresholds');
}

// ================= REMAINING FUNCTIONS =================
function downloadFREDData() {
  section('DOWNLOADING FED DATA');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rawSheet = ss.getSheetByName('Raw_Data');
  const configSheet = ss.getSheetByName('Config');
  
  const startDateCell = configSheet.getRange('B4').getValue();
  let startDate = '2020-01-01';
  if (startDateCell instanceof Date) {
    startDate = Utilities.formatDate(startDateCell, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  } else if (typeof startDateCell === 'string' && startDateCell.length > 0) {
    startDate = startDateCell;
  }
  
  if (rawSheet.getLastRow() > 1) {
    rawSheet.getRange(2, 1, rawSheet.getLastRow() - 1, rawSheet.getLastColumn()).clearContent();
  }
  
  const headers = ['Date', 'WALCL', 'WTREGEN', 'RRPONTSYD', 'WRESBAL', 'SOFR',
    'TREAST', 'WSHOMCB', 'SWPT', 'WORAL', 'RESPPLLOPNWW',
    'WALCL_ffill', 'WRESBAL_ffill', 'TGA_ffill', 'RRP_ffill'];
  rawSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  rawSheet.getRange(1, 1, 1, headers.length).setFontWeight('bold').setBackground('#e8eaed');
  
  const allData = {};
  
  for (const [seriesId, seriesName] of Object.entries(CONFIG.FED_SERIES)) {
    const url = 'https://api.stlouisfed.org/fred/series/observations?series_id=' + seriesId + 
                '&api_key=' + CONFIG.FRED_API_KEY + '&file_type=json&observation_start=' + startDate;
    try {
      const response = UrlFetchApp.fetch(url);
      const json = JSON.parse(response.getContentText());
      let obsCount = 0;
      if (json.observations) {
        json.observations.forEach(function(obs) {
          const date = obs.date;
          let value = obs.value === '.' ? null : parseFloat(obs.value);
          if (seriesId === 'SOFR' && value !== null && value > 1) value = value / 100;
          if (!allData[date]) allData[date] = { date: date };
          allData[date][seriesId] = value;
          if (value !== null) obsCount++;
        });
      }
      log('📥 ' + seriesId + ': ' + obsCount + ' observations');
    } catch (error) {
      log('❌ Error ' + seriesId + ': ' + error);
    }
    Utilities.sleep(300);
  }
  
  const dates = Object.keys(allData).sort();
  let lastWALCL = null, lastWRESBAL = null, lastTGA = null, lastRRP = null;
  
  const dataArray = dates.map(function(date) {
    const row = allData[date];
    if (row.WALCL !== null && row.WALCL !== undefined) lastWALCL = row.WALCL;
    if (row.WRESBAL !== null && row.WRESBAL !== undefined) lastWRESBAL = row.WRESBAL;
    if (row.WTREGEN !== null && row.WTREGEN !== undefined) lastTGA = row.WTREGEN;
    if (row.RRPONTSYD !== null && row.RRPONTSYD !== undefined) lastRRP = row.RRPONTSYD;
    
    return [new Date(date),
      row.WALCL || null, row.WTREGEN || null, row.RRPONTSYD || null, row.WRESBAL || null, row.SOFR || null,
      row.TREAST || null, row.WSHOMCB || null, row.SWPT || null, row.WORAL || null, row.RESPPLLOPNWW || null,
      lastWALCL, lastWRESBAL, lastTGA, lastRRP];
  });
  
  if (dataArray.length > 0) {
    rawSheet.getRange(2, 1, dataArray.length, 15).setValues(dataArray);
  }
  
  log('✅ Written ' + dataArray.length + ' Fed rows');
  return { totalRows: dataArray.length, seriesCount: Object.keys(CONFIG.FED_SERIES).length };
}

function downloadGlobalData() {
  section('DOWNLOADING GLOBAL CENTRAL BANKS DATA');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const globalSheet = ss.getSheetByName('Global_CB');
  const configSheet = ss.getSheetByName('Config');
  
  const startDateCell = configSheet.getRange('B4').getValue();
  let startDate = '2020-01-01';
  if (startDateCell instanceof Date) {
    startDate = Utilities.formatDate(startDateCell, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }
  
  if (globalSheet.getLastRow() > 1) {
    globalSheet.getRange(2, 1, globalSheet.getLastRow() - 1, globalSheet.getLastColumn()).clearContent();
  }
  
  const allData = {};
  let successCount = 0;
  
  for (const [seriesId, seriesInfo] of Object.entries(CONFIG.GLOBAL_SERIES)) {
    const url = 'https://api.stlouisfed.org/fred/series/observations?series_id=' + seriesId + 
                '&api_key=' + CONFIG.FRED_API_KEY + '&file_type=json&observation_start=' + startDate;
    try {
      const response = UrlFetchApp.fetch(url);
      const json = JSON.parse(response.getContentText());
      let obsCount = 0;
      if (json.observations) {
        json.observations.forEach(function(obs) {
          const date = obs.date;
          let value = obs.value === '.' ? null : parseFloat(obs.value);
          if (!allData[date]) allData[date] = { date: date };
          allData[date][seriesId] = value;
          if (value !== null) obsCount++;
        });
      }
      if (obsCount > 0) {
        log('📥 ' + seriesId + ' (' + seriesInfo.region + '): ' + obsCount + ' obs');
        successCount++;
      }
    } catch (error) {
      log('⚠️ ' + seriesId + ': ' + error.toString().substring(0, 50));
    }
    Utilities.sleep(300);
  }
  
  const dates = Object.keys(allData).sort();
  let lastEURUSD = 1.08, lastJPYUSD = 150;
  let lastECB = null, lastBOJ = null, lastChinaFX = null, lastECBRate = null;
  
  const dataArray = dates.map(function(date) {
    const row = allData[date];
    if (row.DEXUSEU) lastEURUSD = row.DEXUSEU;
    if (row.DEXJPUS) lastJPYUSD = row.DEXJPUS;
    if (row.ECBASSETSW) lastECB = row.ECBASSETSW / 1000;
    if (row.ECBDFR) lastECBRate = row.ECBDFR;
    if (row.JPNASSETS) lastBOJ = row.JPNASSETS / 10000;
    if (row.TRESEGCNM052N) lastChinaFX = row.TRESEGCNM052N / 1000;
    
    const ecbUSD = lastECB ? lastECB * lastEURUSD : null;
    const bojUSD = lastBOJ ? (lastBOJ * 1000) / lastJPYUSD : null;
    const chinaUSD = lastChinaFX || null;
    
    let totalCB = null;
    if (ecbUSD !== null || bojUSD !== null || chinaUSD !== null) {
      totalCB = (ecbUSD || 0) + (bojUSD || 0) + (chinaUSD || 0);
    }
    
    return [new Date(date), lastECB, lastECBRate, lastBOJ, lastChinaFX,
      lastEURUSD, lastJPYUSD, null, ecbUSD, bojUSD, chinaUSD, totalCB, null, null, null, null];
  });
  
  for (let i = 0; i < dataArray.length; i++) {
    const totalNow = dataArray[i][11];
    if (i >= 7 && totalNow !== null) dataArray[i][12] = totalNow - (dataArray[i-7][11] || 0);
    if (i >= 30 && totalNow !== null) dataArray[i][13] = totalNow - (dataArray[i-30][11] || 0);
    if (i >= 60 && totalNow !== null) dataArray[i][14] = totalNow - (dataArray[i-60][11] || 0);
    if (i >= 90 && totalNow !== null) dataArray[i][15] = totalNow - (dataArray[i-90][11] || 0);
  }
  
  if (dataArray.length > 0) {
    globalSheet.getRange(2, 1, dataArray.length, 16).setValues(dataArray);
  }
  
  log('✅ Written ' + dataArray.length + ' global rows');
  return { totalRows: dataArray.length, seriesCount: successCount };
}

function validateDataQuality() {
  section('DATA QUALITY VALIDATION');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rawSheet = ss.getSheetByName('Raw_Data');
  const qualitySheet = ss.getSheetByName('Data_Quality');
  
  const lastRow = rawSheet.getLastRow();
  if (lastRow < 2) return { overall: 'FAIL', checks: [] };
  
  const data = rawSheet.getRange(2, 1, lastRow - 1, 15).getValues();
  const checks = [];
  
  let maxGap = 0;
  for (let i = 1; i < data.length; i++) {
    const gap = (data[i][0] - data[i-1][0]) / (1000 * 60 * 60 * 24);
    if (gap > maxGap) maxGap = gap;
  }
  checks.push(['Date Gaps', maxGap > 7 ? '🟡 WARNING' : '🟢 OK', 'Max: ' + maxGap.toFixed(0) + ' days']);
  
  const cols = [11, 12, 13, 14];
  const names = ['WALCL', 'WRESBAL', 'TGA', 'RRP'];
  for (let c = 0; c < cols.length; c++) {
    let nulls = 0;
    for (let r = 0; r < data.length; r++) {
      if (data[r][cols[c]] === null || data[r][cols[c]] === '') nulls++;
    }
    const pct = ((data.length - nulls) / data.length * 100).toFixed(1);
    checks.push([names[c], pct < 90 ? '🔴 FAIL' : '🟢 OK', pct + '% complete']);
  }
  
  const lastDate = data[data.length - 1][0];
  const days = (new Date() - lastDate) / (1000 * 60 * 60 * 24);
  checks.push(['Freshness', days > 7 ? '🔴 STALE' : '🟢 FRESH', days.toFixed(0) + ' days ago']);
  
  qualitySheet.getRange('A1:C1').setValues([['Check', 'Status', 'Details']]);
  qualitySheet.getRange(2, 1, checks.length, 3).setValues(checks);
  
  return { overall: checks.some(c => c[1].includes('FAIL')) ? 'FAIL' : 'OK', checks: checks };
}

function calculateLiquidity() {
  section('CALCULATING FED NET LIQUIDITY');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rawSheet = ss.getSheetByName('Raw_Data');
  const dashSheet = ss.getSheetByName('Dashboard');
  
  const lastRow = rawSheet.getLastRow();
  if (lastRow < 2) return { netLiquidity: 0, weeklyDelta: 0, monthlyDelta: 0, delta60d: 0, delta90d: 0, sofr: 0, sentiment: '⚪ N/A' };
  
  const data = rawSheet.getRange(2, 1, lastRow - 1, 15).getValues();
  
  dashSheet.getRange('A1:H1').setValues([['Date', 'Net Liquidity (B$)', 'Weekly Δ', '30d Δ', '60d Δ', '90d Δ', 'SOFR', 'Sentiment']]);
  dashSheet.getRange('A1:H1').setFontWeight('bold').setBackground('#1c4587').setFontColor('#ffffff');
  
  const dashData = data.map(function(row, idx) {
    const walcl = row[11] || 0;
    const tga = row[13] || 0;
    const rrp = row[14] || 0;
    const netLiq = (walcl - tga - rrp) / 1000;
    
    let weekly = null, monthly = null, delta60 = null, delta90 = null;
    if (idx >= 7) weekly = netLiq - ((data[idx-7][11] || 0) - (data[idx-7][13] || 0) - (data[idx-7][14] || 0)) / 1000;
    if (idx >= 30) monthly = netLiq - ((data[idx-30][11] || 0) - (data[idx-30][13] || 0) - (data[idx-30][14] || 0)) / 1000;
    if (idx >= 60) delta60 = netLiq - ((data[idx-60][11] || 0) - (data[idx-60][13] || 0) - (data[idx-60][14] || 0)) / 1000;
    if (idx >= 90) delta90 = netLiq - ((data[idx-90][11] || 0) - (data[idx-90][13] || 0) - (data[idx-90][14] || 0)) / 1000;
    
    let sofr = null;
    for (let i = idx; i >= 0 && sofr === null; i--) {
      if (data[i][5] !== null && data[i][5] !== '') sofr = data[i][5];
    }
    
    let sentiment = '🟡 MIXED';
    if (weekly > 0 && monthly > 0) sentiment = '🟢 BULLISH';
    else if (weekly < 0 && monthly < 0) sentiment = '🔴 BEARISH';
    
    return [row[0], netLiq, weekly, monthly, delta60, delta90, sofr, sentiment];
  });
  
  if (dashSheet.getLastRow() > 1) dashSheet.getRange(2, 1, dashSheet.getLastRow() - 1, 8).clearContent();
  if (dashData.length > 0) dashSheet.getRange(2, 1, dashData.length, 8).setValues(dashData);
  
  const last = dashData[dashData.length - 1];
  log('✅ Net Liquidity: ' + formatMoney(last[1]) + ', Weekly: ' + formatMoney(last[2], true));
  
  return {
    netLiquidity: last[1],
    weeklyDelta: last[2] || 0,
    monthlyDelta: last[3] || 0,
    delta60d: last[4] || 0,
    delta90d: last[5] || 0,
    sofr: last[6] || 0,
    sentiment: last[7]
  };
}

function calculateGlobalLiquidity() {
  section('CALCULATING GLOBAL LIQUIDITY');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const globalSheet = ss.getSheetByName('Global_CB');
  const rawSheet = ss.getSheetByName('Raw_Data');
  
  const globalLastRow = globalSheet.getLastRow();
  const fedLastRow = rawSheet.getLastRow();
  
  if (globalLastRow < 2 || fedLastRow < 2) {
    return { totalUSD: 0, weeklyDelta: 0, delta30d: 0, delta60d: 0, delta90d: 0, ecbUSD: 0, bojUSD: 0, chinaUSD: 0, fedNetLiq: 0 };
  }
  
  const globalData = globalSheet.getRange(2, 1, globalLastRow - 1, 16).getValues();
  const fedData = rawSheet.getRange(2, 1, fedLastRow - 1, 15).getValues();
  
  const lastGlobal = globalData[globalData.length - 1];
  const lastFed = fedData[fedData.length - 1];
  
  const fedNetLiq = ((lastFed[11] || 0) - (lastFed[13] || 0) - (lastFed[14] || 0)) / 1000;
  const ecbUSD = lastGlobal[8] || 0;
  const bojUSD = lastGlobal[9] || 0;
  const chinaUSD = lastGlobal[10] || 0;
  const totalGlobal = fedNetLiq + ecbUSD + bojUSD + chinaUSD;
  
  let weeklyDelta = 0, delta30d = 0, delta60d = 0, delta90d = 0;
  
  function getTotalAt(globalIdx, fedIdx) {
    if (globalIdx < 0 || fedIdx < 0) return null;
    const fed = ((fedData[fedIdx][11] || 0) - (fedData[fedIdx][13] || 0) - (fedData[fedIdx][14] || 0)) / 1000;
    return fed + (globalData[globalIdx][8] || 0) + (globalData[globalIdx][9] || 0) + (globalData[globalIdx][10] || 0);
  }
  
  const ci = globalData.length - 1;
  const fi = fedData.length - 1;
  
  if (ci >= 7 && fi >= 7) weeklyDelta = totalGlobal - (getTotalAt(ci - 7, fi - 7) || totalGlobal);
  if (ci >= 30 && fi >= 30) delta30d = totalGlobal - (getTotalAt(ci - 30, fi - 30) || totalGlobal);
  if (ci >= 60 && fi >= 60) delta60d = totalGlobal - (getTotalAt(ci - 60, fi - 60) || totalGlobal);
  if (ci >= 90 && fi >= 90) delta90d = totalGlobal - (getTotalAt(ci - 90, fi - 90) || totalGlobal);
  
  log('✅ Global Liquidity: ' + formatMoney(totalGlobal) + ' (Weekly: ' + formatMoney(weeklyDelta, true) + ')');
  
  return { totalUSD: totalGlobal, weeklyDelta, delta30d, delta60d, delta90d, ecbUSD, bojUSD, chinaUSD, fedNetLiq };
}

function calculateRMPMetrics() {
  section('CALCULATING RMP METRICS');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rawSheet = ss.getSheetByName('Raw_Data');
  const rmpSheet = ss.getSheetByName('RMP_Tracker');
  
  const lastRow = rawSheet.getLastRow();
  if (lastRow < 2) return { scoreDaily: 0, scoreWeekly: 0, rrpLevel: 0, rrpVelocity: 0, tgaLevel: 0, tgaSpending: 0 };
  
  const data = rawSheet.getRange(2, 1, lastRow - 1, 15).getValues();
  let prevDailyScore = 0;
  let lastWedScore = null;
  
  const wednesdays = [];
  for (let i = 0; i < data.length; i++) {
    if (data[i][0] instanceof Date && data[i][0].getDay() === 3 && data[i][1] !== null) {
      wednesdays.push(i);
    }
  }
  
  const rmpData = data.map(function(row, idx) {
    const date = row[0];
    const isWed = date instanceof Date && date.getDay() === 3;
    const hasFed = row[1] !== null && row[1] !== '';
    
    const fedTotal = (row[11] || 0) / 1000;
    const fedTreas = (row[6] || 0) / 1000;
    const fedMBS = (row[7] || 0) / 1000;
    const fedOther = (row[9] || 0) / 1000;
    
    const rrpRaw = row[14];
    const rrpLevel = (rrpRaw !== null && !isNaN(rrpRaw)) ? rrpRaw / 1000 : 0;
    const rrpPct = fedTotal > 0 ? rrpLevel / fedTotal : 0;
    
    let prevWedIdx = -1;
    for (let w = wednesdays.length - 1; w >= 0; w--) {
      if (wednesdays[w] < idx - 5) { prevWedIdx = wednesdays[w]; break; }
    }
    
    let rrpWeekly = null, rrpMonthly = null, rrpVelocity = null;
    if (idx >= 7) {
      const prev = (data[idx-7][14] || 0) / 1000;
      rrpWeekly = rrpLevel - prev;
      if (prev > 0.5) rrpVelocity = (rrpWeekly / prev) * 100;
      else if (rrpLevel < 0.5) rrpVelocity = 0;
    }
    if (idx >= 30) rrpMonthly = rrpLevel - (data[idx-30][14] || 0) / 1000;
    
    const tgaRaw = row[13];
    const tgaLevel = (tgaRaw !== null && !isNaN(tgaRaw)) ? tgaRaw / 1000 : 0;
    let tgaWeekly = null, tgaSpending = null;
    if (idx >= 7) {
      const prev = (data[idx-7][13] || 0) / 1000;
      tgaWeekly = tgaLevel - prev;
      tgaSpending = -tgaWeekly;
    }
    
    let treasChange = null, mbsChange = null;
    if (idx >= 7) {
      treasChange = fedTreas - (data[idx-7][6] || 0) / 1000;
      mbsChange = fedMBS - (data[idx-7][7] || 0) / 1000;
    }
    
    let fedChange = 0;
    if (idx >= 7) fedChange = fedTotal - (data[idx-7][11] || 0) / 1000;
    
    let comp1 = 0, comp2 = 0, comp3 = 0;
    if (idx >= 7) {
      if (rrpVelocity !== null && rrpVelocity < 0) comp1 = Math.min(100, Math.abs(rrpVelocity) / CONFIG.SCORE_CONFIG.RRP_VELOCITY_MAX * 100);
      if (tgaSpending !== null && tgaSpending > 0) comp2 = Math.min(100, tgaSpending / CONFIG.SCORE_CONFIG.TGA_SPENDING_MAX * 100);
      if (fedChange > 0) comp3 = Math.min(100, fedChange / CONFIG.SCORE_CONFIG.FED_CHANGE_MAX * 100);
    }
    
    let rawScore = comp1 * 0.4 + comp2 * 0.4 + comp3 * 0.2;
    if (idx > 7 && prevDailyScore > 0) {
      const max = CONFIG.SCORE_CONFIG.MAX_DAILY_CHANGE;
      rawScore = Math.max(prevDailyScore - max, Math.min(prevDailyScore + max, rawScore));
    }
    const scoreDaily = Math.max(0, Math.min(100, rawScore));
    prevDailyScore = scoreDaily;
    
    let scoreWeekly = null;
    if (isWed && hasFed && prevWedIdx >= 0) {
      const prevWed = data[prevWedIdx];
      const rrpPrev = (prevWed[14] || 0) / 1000;
      const rrpChg = rrpLevel - rrpPrev;
      let rrpVel = rrpPrev > 0.5 ? (rrpChg / rrpPrev) * 100 : (rrpLevel < 0.5 ? 0 : null);
      const tgaPrev = (prevWed[13] || 0) / 1000;
      const tgaSp = -(tgaLevel - tgaPrev);
      const fedPrev = (prevWed[11] || 0) / 1000;
      const fedChg = fedTotal - fedPrev;
      
      let wc1 = 0, wc2 = 0, wc3 = 0;
      if (rrpVel !== null && rrpVel < 0) wc1 = Math.min(100, Math.abs(rrpVel) / CONFIG.SCORE_CONFIG.RRP_VELOCITY_MAX * 100);
      if (tgaSp > 0) wc2 = Math.min(100, tgaSp / CONFIG.SCORE_CONFIG.TGA_SPENDING_MAX * 100);
      if (fedChg > 0) wc3 = Math.min(100, fedChg / CONFIG.SCORE_CONFIG.FED_CHANGE_MAX * 100);
      
      scoreWeekly = Math.max(0, Math.min(100, wc1 * 0.4 + wc2 * 0.4 + wc3 * 0.2));
      lastWedScore = scoreWeekly;
    } else if (lastWedScore !== null) {
      scoreWeekly = lastWedScore;
    }
    
    const compStr = 'RRP:' + comp1.toFixed(0) + '% TGA:' + comp2.toFixed(0) + '% FED:' + comp3.toFixed(0) + '%';
    const btfp = (row[10] || 0) / 1000;
    
    return [date, fedTotal, fedTreas, fedMBS, fedOther,
      rrpLevel, rrpPct, rrpWeekly, rrpMonthly, rrpVelocity,
      tgaLevel, tgaWeekly, tgaSpending, treasChange, mbsChange,
      scoreDaily, scoreWeekly, compStr, btfp, null, null, null, isWed && hasFed ? 'YES' : ''];
  });
  
  if (rmpSheet.getLastRow() > 1) rmpSheet.getRange(2, 1, rmpSheet.getLastRow() - 1, 23).clearContent();
  if (rmpData.length > 0) rmpSheet.getRange(2, 1, rmpData.length, 23).setValues(rmpData);
  
  const last = rmpData[rmpData.length - 1];
  log('✅ RMP: Daily=' + last[15].toFixed(1) + ', Weekly=' + (last[16] ? last[16].toFixed(1) : 'N/A'));
  
  return { scoreDaily: last[15] || 0, scoreWeekly: last[16] || 0, rrpLevel: last[5] || 0, rrpVelocity: last[9], tgaLevel: last[10] || 0, tgaSpending: last[12] || 0 };
}

function checkAlerts(liquidityResult, rmpResult, globalResult, volResult) {
  section('CHECKING ALERTS');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const alerts = [];
  
  if (rmpResult.rrpVelocity !== null && rmpResult.rrpVelocity < CONFIG.ALERTS.RRP_DROP_MAJOR) {
    alerts.push({ type: 'RRP_DROP_MAJOR', severity: 'HIGH', message: '🔥 RRP MEGA DROP', details: 'RRP declining rapidly', value: rmpResult.rrpVelocity });
  }
  if (rmpResult.tgaSpending > CONFIG.ALERTS.TGA_SPENDING_SURGE) {
    alerts.push({ type: 'TGA_SPENDING_SURGE', severity: 'HIGH', message: '🔥 TGA Spending Surge', details: 'Treasury spending aggressively', value: rmpResult.tgaSpending });
  }
  if (rmpResult.scoreDaily > CONFIG.ALERTS.STEALTH_QE_ACTIVATED) {
    alerts.push({ type: 'STEALTH_QE_ACTIVATED', severity: 'HIGH', message: '🔥 Stealth QE Active', details: 'High injection score', value: rmpResult.scoreDaily });
  }
  
  if (globalResult.weeklyDelta > CONFIG.ALERTS.GLOBAL_LIQUIDITY_SURGE) {
    alerts.push({ type: 'GLOBAL_LIQUIDITY_SURGE', severity: 'HIGH', message: '🌍 Global Liquidity Surge', details: 'Major CB expansion', value: globalResult.weeklyDelta });
  }
  
  if (volResult) {
    if (volResult.vix && volResult.vix > CONFIG.ALERTS.VIX_SPIKE) {
      alerts.push({ type: 'VIX_SPIKE', severity: 'HIGH', message: '📊 VIX Spike: ' + volResult.vix.toFixed(1), details: 'High fear in equity markets', value: volResult.vix });
    }
    if (volResult.vixZ && volResult.vixZ > CONFIG.ALERTS.VIX_ZSCORE_EXTREME) {
      alerts.push({ type: 'VIX_ZSCORE_EXTREME', severity: 'MEDIUM', message: '📊 VIX Z-Score Extreme: ' + volResult.vixZ.toFixed(2), details: 'Volatility unusually elevated', value: volResult.vixZ });
    }
    if (volResult.move && volResult.move > CONFIG.ALERTS.MOVE_SPIKE) {
      alerts.push({ type: 'MOVE_SPIKE', severity: 'HIGH', message: '📈 MOVE Spike: ' + volResult.move.toFixed(1), details: 'High bond market volatility', value: volResult.move });
    }
  }
  
  if (alerts.length > 0) {
    const alertSheet = ss.getSheetByName('Alert_Log');
    alerts.forEach(function(a) {
      alertSheet.appendRow([new Date(), a.type, a.severity, a.message]);
      log('🚨 ALERT: ' + a.message);
    });
  }
  
  log('✅ Alerts: ' + alerts.length);
  return alerts;
}

function generateInterpretation(weekly, monthly, sofr) {
  let text = 'Mixed signals';
  if (weekly > 0 && monthly > 0) text = weekly > 50 ? 'Strong liquidity expansion - bullish' : 'Mild growth - neutral to bullish';
  else if (weekly < 0 && monthly < 0) text = weekly < -50 ? 'Strong contraction - bearish' : 'Mild contraction - cautious';
  return { text };
}

function scrapeFedH41() {
  try {
    const response = UrlFetchApp.fetch('https://www.federalreserve.gov/releases/h41/current/h41.htm', { muteHttpExceptions: true });
    if (response.getResponseCode() !== 200) return null;
    const html = response.getContentText();
    const billsMatch = html.match(/Bills[^\d]*([\d,]{4,})/i);
    const bondsMatch = html.match(/Notes and bonds[^\d]*([\d,]{4,})/i);
    if (billsMatch && bondsMatch) {
      const bills = parseFloat(billsMatch[1].replace(/,/g, ''));
      const bonds = parseFloat(bondsMatch[1].replace(/,/g, ''));
      if (bills > 100 && bonds > 100) return { bills: bills / 1000, bonds: bonds / 1000, billsPercent: bills / (bills + bonds) * 100 };
    }
    return null;
  } catch (e) { return null; }
}

function saveH41Data(h41) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rmpSheet = ss.getSheetByName('RMP_Tracker');
  const lastRow = rmpSheet.getLastRow();
  for (let i = 0; i < 7 && lastRow - i >= 2; i++) {
    rmpSheet.getRange(lastRow - i, 20).setValue(h41.bills);
    rmpSheet.getRange(lastRow - i, 21).setValue(h41.bonds);
    rmpSheet.getRange(lastRow - i, 22).setValue(h41.billsPercent / 100);
  }
}

// ================= CHARTS =================
function createDashboardCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Dashboard');
  sheet.getCharts().forEach(function(c) { sheet.removeChart(c); });
  const lastRow = sheet.getLastRow();
  if (lastRow < 10) return;
  const chart = sheet.newChart().setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange('A1:B' + lastRow)).setPosition(2, 14, 0, 0)
    .setOption('title', 'Fed Net Liquidity').setOption('width', 700).setOption('height', 350).build();
  sheet.insertChart(chart);
  log('📈 Dashboard chart created');
}

function createRMPCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('RMP_Tracker');
  sheet.getCharts().forEach(function(c) { sheet.removeChart(c); });
  const lastRow = sheet.getLastRow();
  if (lastRow < 10) return;
  const chart = sheet.newChart().setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange('A1:A' + lastRow)).addRange(sheet.getRange('P1:Q' + lastRow))
    .setPosition(2, 25, 0, 0).setOption('title', 'Stealth QE Score')
    .setOption('width', 800).setOption('height', 350).setOption('vAxis', { viewWindow: { min: 0, max: 100 }}).build();
  sheet.insertChart(chart);
  log('📈 RMP chart created');
}

function createGlobalCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Global_CB');
  sheet.getCharts().forEach(function(c) { sheet.removeChart(c); });
  const lastRow = sheet.getLastRow();
  if (lastRow < 10) return;
  const chart = sheet.newChart().setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange('A1:A' + lastRow)).addRange(sheet.getRange('L1:L' + lastRow))
    .setPosition(2, 18, 0, 0).setOption('title', 'Total Global CB Liquidity').setOption('width', 700).setOption('height', 350).build();
  sheet.insertChart(chart);
  log('📈 Global chart created');
}

function createVolatilityCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Volatility_Tracker');
  if (!sheet) return;
  sheet.getCharts().forEach(function(c) { sheet.removeChart(c); });
  const lastRow = sheet.getLastRow();
  if (lastRow < 10) return;
  
  const vixChart = sheet.newChart().setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange('A1:A' + lastRow)).addRange(sheet.getRange('B1:B' + lastRow))
    .setPosition(2, 27, 0, 0).setOption('title', 'VIX Index')
    .setOption('width', 600).setOption('height', 300).build();
  sheet.insertChart(vixChart);
  
  const moveChart = sheet.newChart().setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange('A1:A' + lastRow)).addRange(sheet.getRange('P1:P' + lastRow))
    .setPosition(18, 27, 0, 0).setOption('title', 'MOVE Index (Bond Volatility)')
    .setOption('width', 600).setOption('height', 300).build();
  sheet.insertChart(moveChart);
  
  log('📈 Volatility charts created');
}

// ================= MENU =================
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🌍 Liquidity Monitor v3.4.1')
    .addItem('🔄 Update All Data', 'updateLiquidity')
    .addItem('📊 Update + Charts', 'updateWithCharts')
    .addSeparator()
    .addItem('📊 Update Volatility Only', 'updateVolatilityOnly')
    .addItem('📈 Test MOVE Fetch', 'testMoveFetch')
    .addSeparator()
    .addItem('📤 Test Discord', 'testDiscordWebhook')
    .addItem('📧 Test Email', 'testEmail')
    .addItem('🧪 Test System', 'testRun')
    .addSeparator()
    .addItem('📈 Create All Charts', 'createAllCharts')
    .addItem('📖 View Legend', 'showLegend')
    .addToUi();
}

function updateVolatilityOnly() {
  setupVolatilitySheet();
  downloadVolatilityData();
  createVolatilityCharts();
  log('✅ Volatility data updated');
}

function testMoveFetch() {
  log('═══ TESTING MOVE FETCH v3.4.1 ═══');
  
  // Test current price
  const currentPrice = getCurrentMovePrice();
  log('Current MOVE price: ' + (currentPrice || 'FAILED'));
  
  // Test historical
  const historicalData = fetchMoveIndex('2024-01-01');
  if (historicalData) {
    const keys = Object.keys(historicalData);
    log('Historical data points: ' + keys.length);
    if (keys.length > 0) {
      const lastKey = keys[keys.length - 1];
      log('Last date: ' + lastKey + ' = ' + historicalData[lastKey]);
    }
  } else {
    log('Historical fetch FAILED');
  }
  
  log('═══════════════════════════════════');
}

function createAllCharts() {
  createDashboardCharts();
  createRMPCharts();
  createGlobalCharts();
  createVolatilityCharts();
  log('✅ All charts created');
}

function showLegend() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const legendSheet = ss.getSheetByName('Legend');
  if (legendSheet) ss.setActiveSheet(legendSheet);
}

function testDiscordWebhook() {
  const vol = { vix: 14.75, vixZ: -0.29, vixD7: 1.15, vixRatio: 0.813, termStructure: '🟢 CONTANGO', move: 65.8, moveZ: -1.2, moveD7: -2.5, spread: 0.71, volSignal: '🟢 RISK-ON' };
  sendDiscordEmbed('daily_report', {
    netLiquidity: 5800, weeklyDelta: 59.2, monthlyDelta: 190, delta60d: 19.9, delta90d: -210, sofr: 0.0366,
    sentiment: '🟢 BULLISH', interpretation: 'Strong liquidity expansion - bullish', rrpLevel: 0.003, rrpVelocity: 0, tgaLevel: 837, tgaSpending: -0.19,
    scoreDaily: 12, scoreWeekly: 17, globalLiquidity: 20770, globalWeeklyDelta: 62.7, global30dDelta: 274,
    global60dDelta: -108, global90dDelta: -377, fedNetLiq: 5800, ecbAssets: 7240, bojAssets: 4320, chinaAssets: 3410,
    vol: vol, validationPassed: 6, validationTotal: 6
  });
  log('📤 Test Discord message sent');
}

function testEmail() {
  const rmp = { scoreDaily: 12, scoreWeekly: 17, rrpLevel: 0.003, rrpVelocity: 0, tgaLevel: 837, tgaSpending: -0.19 };
  const liq = { netLiquidity: 5800, weeklyDelta: 59.2, monthlyDelta: 190, delta60d: 19.9, delta90d: -210, sofr: 0.0366, sentiment: '🟢 BULLISH' };
  const global = { totalUSD: 20770, weeklyDelta: 62.7, delta30d: 274, delta60d: -108, delta90d: -377, ecbUSD: 7240, bojUSD: 4320, chinaUSD: 3410, fedNetLiq: 5800 };
  const vol = { vix: 14.75, vixZ: -0.29, vixD7: 1.15, vixRatio: 0.813, termStructure: '🟢 CONTANGO', move: 65.8, moveZ: -1.2, moveD7: -2.5, spread: 0.71, volSignal: '🟢 RISK-ON' };
  const val = { checks: [], passed: 6, failed: 0, warnings: 0 };
  sendDailyReport([], rmp, liq, global, vol, val);
  log('📧 Test email sent');
}

function testRun() {
  log('═══ TEST RUN v3.4.1 ═══');
  log('Discord: ' + (CONFIG.DISCORD_WEBHOOK_URL !== 'YOUR_DISCORD_WEBHOOK_URL_HERE' ? 'CONFIGURED' : 'NOT SET'));
  log('N8N: ' + (CONFIG.N8N_ENABLED ? 'ENABLED' : 'DISABLED'));
  log('Fed Series: ' + Object.keys(CONFIG.FED_SERIES).length);
  log('Global Series: ' + Object.keys(CONFIG.GLOBAL_SERIES).length);
  log('Volatility Series: ' + Object.keys(CONFIG.VOLATILITY_SERIES).length);
  log('═══════════════════════════════════');
}