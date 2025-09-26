// ScamiFy Content Script - Dual-Model AI Phishing Detection Engine
console.log('🚀 SCAMIFY: Dual-Model AI Engine starting (ANN + LSTM)');

// ---------------------------------------------------------------------------
// State & Configuration
// ---------------------------------------------------------------------------
let SC_DIALOG = null;         // Floating dialog element
let SC_LAST_URL = null;       // Last analyzed URL
let SC_ACTIVE_EL = null;      // Current element (anchor / container)
let SC_FETCHING = false;      // In-flight analysis
let SC_HIDE_TIMER = null;     // Hide timer
let SC_ENABLED = true;        // Future: chrome.storage toggle
let SC_HOVER_ENABLED = true;  // Future: chrome.storage toggle
let SC_NAV_ENABLED = true;    // LSTM navigation protection
const SC_CACHE = new Map();   // url -> { prediction, probability, ts, model }
const SC_LSTM_CACHE = new Map(); // url -> { lstm_result, ts }
const SC_CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const SC_DEBUG = true;        // Debug flag
const SC_BACKEND_URL = 'http://127.0.0.1:5000'; // Backend base URL
let SC_BACKEND_AVAILABLE = true; // Backend health status

function scLog(...args){ if (SC_DEBUG) console.log('[SCAMIFY]', ...args); }
function scWarn(...args){ if (SC_DEBUG) console.warn('[SCAMIFY]', ...args); }
function scError(...args){ if (SC_DEBUG) console.error('[SCAMIFY]', ...args); }

// ---------------------------------------------------------------------------
// Backend Health & Communication
// ---------------------------------------------------------------------------
async function scCheckBackendHealth() {
  try {
    const res = await fetch(`${SC_BACKEND_URL}/health`, { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      timeout: 3000
    });
    if (res.ok) {
      const health = await res.json();
      SC_BACKEND_AVAILABLE = true;
      scLog('Backend health:', health);
      return health;
    }
  } catch (e) {
    scWarn('Backend unavailable:', e.message);
    SC_BACKEND_AVAILABLE = false;
  }
  return null;
}

// Enhanced fetch with multiple model support
async function scFetchANN(url) {
  const res = await fetch(`${SC_BACKEND_URL}/check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  if (!res.ok) throw new Error(`ANN API error: ${res.status}`);
  return await res.json();
}

async function scFetchLSTM(url) {
  const res = await fetch(`${SC_BACKEND_URL}/predict_lstm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
    timeout: 15000 // LSTM takes longer due to Selenium
  });
  if (!res.ok) throw new Error(`LSTM API error: ${res.status}`);
  return await res.json();
}

async function scFetchBothModels(url) {
  const res = await fetch(`${SC_BACKEND_URL}/predict_both`, {
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
    timeout: 20000 // Both models take longer
  });
  if (!res.ok) throw new Error(`Both models API error: ${res.status}`);
  return await res.json();
}

// ---------------------------------------------------------------------------
// Utilities & URL Extraction
// ---------------------------------------------------------------------------
const scNow = () => Date.now();
const scIsHttpUrl = (u) => typeof u === 'string' && /^https?:\/\//i.test(u);

function scNormalizeUrl(raw, baseEl){
  if (!raw) return null;
  try {
    // If already absolute http(s)
    if (/^https?:\/\//i.test(raw)) return new URL(raw).href;
    // Protocol-relative
    if (/^\/\//.test(raw)) return (location.protocol + raw);
    // Relative path
    if (/^[./]/.test(raw)) return new URL(raw, location.href).href;
    // Fallback: attempt constructing
    return new URL(raw, location.href).href;
  } catch(e){
    if (baseEl && baseEl.href) return baseEl.href; // anchor.href is normalized by browser
    return null;
  }
}

function scExtractUrl(el) {
  if (!el) return null;
  if (el.tagName === 'A' && el.href) {
    const norm = scNormalizeUrl(el.getAttribute('href'), el) || el.href;
    if (scIsHttpUrl(norm)) return norm;
  }
  const attrs = ['data-url','data-href','data-link'];
  for (const a of attrs) {
    const val = el.getAttribute && el.getAttribute(a);
    if (val && scIsHttpUrl(val)) return val;
  }
  if (el.childElementCount === 0) {
    const txt = (el.textContent||'').trim();
    if (txt.length <= 300) {
      const m = txt.match(/https?:\/\/[^\s<>'\"]+/i);
      if (m && scIsHttpUrl(m[0])) return m[0];
    }
  }
  return null;
}

function scFindUrlFromElement(el) {
  // 1. Direct / ancestor search (depth 6)
  let node = el, depth = 0;
  while (node && depth < 6) {
    const u = scExtractUrl(node);
    if (u) return u;
    node = node.parentElement;
    depth++;
  }
  // 2. Descendant quick search (anchors first)
  if (el && el.querySelector) {
    try {
      const a = el.querySelector('a[href^="http"],a[href^="https"]');
      if (a) {
        const norm = scNormalizeUrl(a.getAttribute('href'), a) || a.href;
        if (scIsHttpUrl(norm)) return norm;
      }
      const poss = el.querySelector('[data-url],[data-href],[data-link]');
      if (poss) {
        for (const key of ['data-url','data-href','data-link']) {
          const v = poss.getAttribute(key);
          if (v) {
            const norm = scNormalizeUrl(v, el);
            if (scIsHttpUrl(norm)) return norm;
          }
        }
      }
    } catch(e){}
  }
  return null;
}

function scFindUrlAtPoint(x,y) {
  const els = document.elementsFromPoint(x,y);
  for (const el of els) {
    const u = scFindUrlFromElement(el);
    if (u) { scLog('URL via elementsFromPoint', u); return { url: u, element: el }; }
  }
  return null;
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Backend Fetch with Caching & Multi-Model Support
// ---------------------------------------------------------------------------
async function scFetchAnalysis(url, modelType = 'ann') {
  const cacheKey = `${url}_${modelType}`;
  const cached = SC_CACHE.get(cacheKey);
  
  if (cached && (scNow() - cached.ts) < SC_CACHE_TTL) {
    scLog(`${modelType.toUpperCase()} CACHE HIT`, { url, prediction: cached.prediction, probability: cached.probability });
    return cached;
  }
  
  if (!SC_BACKEND_AVAILABLE) {
    scWarn('Backend unavailable, returning safe default');
    return { prediction: 'safe', probability: 0.5, ts: scNow(), model: 'fallback' };
  }
  
  scLog(`${modelType.toUpperCase()} FETCH START`, { url });
  try {
    let data;
    switch (modelType) {
      case 'ann':
        data = await scFetchANN(url);
        break;
      case 'lstm': 
        data = await scFetchLSTM(url);
        break;
      case 'both':
        data = await scFetchBothModels(url);
        // For 'both' mode, return consensus result
        if (data.consensus) {
          const norm = {
            prediction: (data.consensus.final_prediction || 'safe').toLowerCase(),
            probability: data.consensus.confidence_score || 0.5,
            confidence_level: data.consensus.confidence_level || 'low',
            ann_prediction: data.ann_prediction,
            lstm_prediction: data.lstm_prediction,
            agreement: data.consensus.models_agree || false,
            ts: scNow(),
            model: 'both'
          };
          SC_CACHE.set(cacheKey, norm);
          scLog('BOTH MODELS RESULT', { url, consensus: norm.prediction, confidence: norm.confidence_level });
          return norm;
        }
        break;
      default:
        throw new Error(`Unknown model type: ${modelType}`);
    }
    
    const norm = {
      prediction: (data.prediction || 'safe').toLowerCase(),
      probability: (typeof data.probability === 'number') ? data.probability : 0.5,
      processing_time: data.processing_time_ms || 0,
      ts: scNow(),
      model: modelType
    };
    SC_CACHE.set(cacheKey, norm);
    scLog(`${modelType.toUpperCase()} FETCH RESULT`, { url, prediction: norm.prediction, probability: norm.probability });
    return norm;
    
  } catch (e) {
    scError(`${modelType.toUpperCase()} FETCH ERROR`, url, e);
    const fb = { prediction: 'safe', probability: 0.5, ts: scNow(), model: 'fallback', error: e.message };
    SC_CACHE.set(cacheKey, fb);
    return fb;
  }
}

// ---------------------------------------------------------------------------
// Tooltip Rendering
// ---------------------------------------------------------------------------
function scCreateDialog() {
  if (SC_DIALOG) return SC_DIALOG;
  const d = document.createElement('div');
  d.id = 'scamify-dialog';
  d.style.cssText = 'position:fixed;top:0;left:0;transform:translate(-9999px,-9999px);background:#0f172a;color:#f1f5f9;font:12px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;border:1px solid #334155;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.45);padding:10px 12px;max-width:360px;z-index:2147483647;pointer-events:none;backdrop-filter:blur(4px);';
  d.innerHTML = '';
  document.documentElement.appendChild(d);
  SC_DIALOG = d;
  return d;
}

function scRenderLoading(url) {
  const d = scCreateDialog();
  d.innerHTML = `<div style="font-weight:600;margin-bottom:4px;color:#38bdf8;">🛡️ ScamiFy Scan</div><div style="font-size:10px;color:#94a3b8;margin-bottom:6px;">${url}</div><div style="color:#fbbf24;">Analyzing...</div>`;
}

function scRenderResult(url,res){
  const d = scCreateDialog();
  const prob = Math.round(res.probability*100);
  let color='#10b981', icon='✅', label='SAFE';
  if (['phishing','malicious'].includes(res.prediction)) { color='#ef4444'; icon='🚨'; label='PHISHING'; }
  else if (res.prediction==='suspicious') { color='#f59e0b'; icon='⚠️'; label='SUSPICIOUS'; }
  d.innerHTML = `<div style="font-weight:600;margin-bottom:4px;color:#38bdf8;">🛡️ ScamiFy Scan</div><div style="font-size:10px;color:#94a3b8;margin-bottom:6px;">${url}</div><div style="color:${color};font-weight:600;">${icon} ${label} (${prob}%)</div><div style="font-size:10px;color:#64748b;margin-top:6px;border-top:1px solid #334155;padding-top:4px;">ANN Model Result</div>`;
}

function scPositionDialogForElement(el) {
  if (!SC_DIALOG || !el) return;
  const r = el.getBoundingClientRect();
  const dRect = SC_DIALOG.getBoundingClientRect();
  let x = r.right + 12;
  let y = r.top - 4;
  if (x + dRect.width > window.innerWidth - 8) x = r.left - dRect.width - 12;
  if (y + dRect.height > window.innerHeight - 8) y = window.innerHeight - dRect.height - 8;
  if (y < 8) y = 8;
  SC_DIALOG.style.transform = `translate(${Math.max(0,x)}px,${Math.max(0,y)}px)`;
}

function scHideDialog(immediate=false){
  if (!SC_DIALOG) return;
  if (immediate){ SC_DIALOG.style.transform='translate(-9999px,-9999px)'; return; }
  if (SC_HIDE_TIMER) clearTimeout(SC_HIDE_TIMER);
  SC_HIDE_TIMER = setTimeout(()=>{ if (SC_DIALOG) SC_DIALOG.style.transform='translate(-9999px,-9999px)'; },140);
}

// ---------------------------------------------------------------------------
// Hover Handling
// ---------------------------------------------------------------------------
async function scAnalyzeElement(el, url){
  if (!url) return;
  if (url === SC_LAST_URL && !SC_FETCHING) { scPositionDialogForElement(el); return; }
  SC_LAST_URL = url;
  SC_ACTIVE_EL = el;
  SC_FETCHING = true;
  scRenderLoading(url);
  scPositionDialogForElement(el);
  const result = await scFetchAnalysis(url);
  if (SC_LAST_URL === url && SC_ACTIVE_EL === el) {
    scRenderResult(url,result);
    scPositionDialogForElement(el);
  }
  SC_FETCHING = false;
}

function scResolveUrlFromTarget(target){
  if (!target) return null;
  // Direct anchor or closest anchor
  const a = target.closest && target.closest('a[href]');
  if (a) {
    const norm = scNormalizeUrl(a.getAttribute('href'), a) || a.href;
    if (scIsHttpUrl(norm)) return { el: a, url: norm };
  }
  // Data-* wrappers
  let node = target; let depth = 0;
  while (node && depth < 5) {
    const u = scExtractUrl(node);
    if (u) return { el: node, url: u };
    node = node.parentElement; depth++;
  }
  return null;
}

function scOnMouseOver(ev){
  if (!SC_ENABLED || !SC_HOVER_ENABLED) return;
  const resolved = scResolveUrlFromTarget(ev.target);
  if (!resolved){ scHideDialog(); return; }
  scAnalyzeElement(resolved.el, resolved.url);
}

function scOnMouseMove(ev){
  if (!SC_ACTIVE_EL) return; // nothing active
  scPositionDialogForElement(SC_ACTIVE_EL);
}

function scOnMouseOut(ev){
  if (!SC_ACTIVE_EL) return;
  const rel = ev.relatedTarget;
  if (rel && (SC_ACTIVE_EL === rel || SC_ACTIVE_EL.contains(rel))) return;
  if (SC_DIALOG && (SC_DIALOG === rel || SC_DIALOG.contains(rel))) return;
  SC_ACTIVE_EL = null; SC_LAST_URL = null; scHideDialog();
}

// Legacy handlers removed in rewrite

// ---------------------------------------------------------------------------
// Navigation Detection & LSTM Deep Analysis
// ---------------------------------------------------------------------------
let SC_NAVIGATION_TIMER = null;
let SC_CURRENT_PAGE_ANALYZED = false;

// Detect navigation attempts and trigger LSTM analysis
function scDetectNavigation() {
  const currentUrl = window.location.href;
  
  // Skip analysis for same page or already analyzed
  if (SC_CURRENT_PAGE_ANALYZED) return;
  
  scLog('Navigation detected, starting LSTM analysis:', currentUrl);
  SC_CURRENT_PAGE_ANALYZED = true;
  
  // Analyze current page with LSTM (more thorough)
  scAnalyzePageWithLSTM(currentUrl);
}

async function scAnalyzePageWithLSTM(url) {
  if (!SC_NAV_ENABLED) return;
  
  try {
    scLog('Starting LSTM deep analysis for:', url);
    
    // Use both models for navigation analysis
    const result = await scFetchAnalysis(url, 'both');
    
    if (result && result.prediction === 'phishing') {
      scShowNavigationWarning(url, result);
    } else if (result && result.lstm_prediction && result.lstm_prediction.prediction === 'phishing') {
      // Show warning even if consensus is safe but LSTM detected phishing
      scShowLSTMWarning(url, result);
    }
    
  } catch (e) {
    scError('LSTM navigation analysis failed:', e);
  }
}

// Click handler for links - trigger LSTM analysis before navigation
function scOnLinkClick(event) {
  if (!SC_NAV_ENABLED) return;
  
  const link = event.target.closest('a[href]');
  if (!link) return;
  
  const href = link.getAttribute('href');
  const normalizedUrl = scNormalizeUrl(href, link);
  
  if (!scIsHttpUrl(normalizedUrl)) return;
  
  scLog('Link click detected:', normalizedUrl);
  
  // For external links, do quick LSTM check
  if (scIsExternalLink(normalizedUrl)) {
    event.preventDefault(); // Temporarily prevent navigation
    scAnalyzeLinkBeforeNavigation(normalizedUrl, link, event);
  }
}

function scIsExternalLink(url) {
  try {
    const currentDomain = window.location.hostname;
    const linkDomain = new URL(url).hostname;
    return currentDomain !== linkDomain;
  } catch (e) {
    return true; // Assume external if parsing fails
  }
}

async function scAnalyzeLinkBeforeNavigation(url, linkElement, originalEvent) {
  try {
    scLog('Pre-navigation LSTM analysis for:', url);
    
    // Quick ANN check first (faster)
    const annResult = await scFetchAnalysis(url, 'ann');
    
    if (annResult.prediction === 'phishing' && annResult.probability > 0.8) {
      // High confidence phishing from ANN - show immediate warning
      const userChoice = await scShowNavigationConfirm(url, annResult);
      if (userChoice) {
        window.location.href = url; // User chose to proceed
      }
      return;
    }
    
    // If ANN is uncertain, use LSTM for deeper analysis
    const lstmResult = await scFetchAnalysis(url, 'lstm');
    
    if (lstmResult.prediction === 'phishing') {
      const userChoice = await scShowNavigationConfirm(url, lstmResult);
      if (userChoice) {
        window.location.href = url; // User chose to proceed
      }
    } else {
      // Safe to proceed
      window.location.href = url;
    }
    
  } catch (e) {
    scError('Pre-navigation analysis failed:', e);
    // If analysis fails, allow navigation (don't block legitimate browsing)
    window.location.href = url;
  }
}

// ---------------------------------------------------------------------------
// Enhanced Warning System
// ---------------------------------------------------------------------------
function scShowNavigationWarning(url, result) {
  const warningLevel = scGetWarningLevel(result);
  
  scLog(`Showing navigation warning (${warningLevel}) for:`, url);
  
  if (warningLevel === 'high') {
    scShowHighSecurityWarning(url, result);
  } else if (warningLevel === 'medium') {
    scShowMediumWarning(url, result);
  } else {
    scShowLowWarning(url, result);
  }
}

function scShowLSTMWarning(url, result) {
  scLog('LSTM detected phishing, showing warning:', url);
  scShowMediumWarning(url, result, 'LSTM detected potential phishing');
}

function scGetWarningLevel(result) {
  if (!result) return 'low';
  
  // High: Both models agree it's phishing with high confidence
  if (result.agreement && result.prediction === 'phishing' && result.probability > 0.8) {
    return 'high';
  }
  
  // Medium: One model detects phishing or moderate confidence
  if (result.prediction === 'phishing' || 
      (result.lstm_prediction && result.lstm_prediction.prediction === 'phishing')) {
    return 'medium';
  }
  
  return 'low';
}

async function scShowNavigationConfirm(url, result) {
  return new Promise((resolve) => {
    const modal = scCreateWarningModal(url, result);
    document.body.appendChild(modal);
    
    const proceedBtn = modal.querySelector('.sc-proceed-btn');
    const blockBtn = modal.querySelector('.sc-block-btn');
    
    proceedBtn.onclick = () => {
      document.body.removeChild(modal);
      resolve(true);
    };
    
    blockBtn.onclick = () => {
      document.body.removeChild(modal);
      resolve(false);
    };
    
    // Auto-block after 10 seconds if no response
    setTimeout(() => {
      if (document.body.contains(modal)) {
        document.body.removeChild(modal);
        resolve(false);
      }
    }, 10000);
  });
}

function scShowHighSecurityWarning(url, result) {
  // Create blocking modal that's hard to dismiss
  const modal = scCreateWarningModal(url, result, 'high');
  document.body.appendChild(modal);
  
  // Block navigation completely for 3 seconds
  setTimeout(() => {
    if (document.body.contains(modal)) {
      const proceedBtn = modal.querySelector('.sc-proceed-btn');
      if (proceedBtn) proceedBtn.disabled = false;
    }
  }, 3000);
}

function scShowMediumWarning(url, result, customMessage = null) {
  // Show notification-style warning
  if (typeof chrome !== 'undefined' && chrome.runtime) {
    chrome.runtime.sendMessage({
      type: 'showNotification',
      title: 'ScamiFy: Potential Phishing Detected',
      message: customMessage || `${result.model.toUpperCase()} model detected potential phishing: ${scTruncateUrl(url)}`,
      iconUrl: 'icons/logo.png'
    });
  }
  
  // Also show banner warning
  scShowWarningBanner(url, result, customMessage);
}

function scShowLowWarning(url, result) {
  scLog('Low-level warning for:', url);
  // Just log for now, could add subtle UI indicator
}

function scShowWarningBanner(url, result, customMessage = null) {
  const banner = document.createElement('div');
  banner.id = 'scamify-warning-banner';
  banner.innerHTML = `
    <div style="display: flex; align-items: center; gap: 10px;">
      <span style="font-size: 16px;">⚠️</span>
      <div>
        <strong>ScamiFy Warning:</strong><br>
        ${customMessage || `Potential phishing detected by ${result.model.toUpperCase()} model`}
      </div>
      <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
    </div>
  `;
  banner.style.cssText = `
    position: fixed; top: 0; left: 0; right: 0; z-index: 2147483647;
    background: linear-gradient(135deg, #dc2626, #ef4444);
    color: white; padding: 12px 20px; font-family: system-ui, -apple-system, sans-serif;
    font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    border-bottom: 3px solid #991b1b;
  `;
  
  document.body.prepend(banner);
  
  // Auto-remove after 8 seconds
  setTimeout(() => {
    if (document.body.contains(banner)) {
      banner.remove();
    }
  }, 8000);
}

// ---------------------------------------------------------------------------
// Init & Setup
// ---------------------------------------------------------------------------
function scSetup(){
  // Existing hover detection (ANN model - fast)
  document.addEventListener('mouseover', scOnMouseOver, true);
  document.addEventListener('mousemove', scOnMouseMove, true);
  document.addEventListener('mouseout', scOnMouseOut, true);
  document.addEventListener('scroll', () => { if (SC_ACTIVE_EL) scPositionDialogForElement(SC_ACTIVE_EL); }, true);
  window.addEventListener('blur', () => scHideDialog(true));
  
  // New LSTM navigation detection
  document.addEventListener('click', scOnLinkClick, true);
  window.addEventListener('beforeunload', scDetectNavigation);
  
  // Page analysis on load
  if (document.readyState === 'complete') {
    setTimeout(scDetectNavigation, 1000); // Delay to let page settle
  } else {
    window.addEventListener('load', () => {
      setTimeout(scDetectNavigation, 1000);
    });
  }
  
  // Check backend health on startup
  scCheckBackendHealth().then(health => {
    if (health) {
      scLog('Backend health check passed:', health);
    }
  });
  
  console.log('✅ SCAMIFY: Dual-model listeners active (ANN hover + LSTM navigation)');
  scShowActivationBanner();
}

// Activation banner to confirm script injected
function scShowActivationBanner(){
  try {
    if (document.getElementById('scamify-activation-banner')) return;
    const b = document.createElement('div');
    b.id='scamify-activation-banner';
    b.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 14px;">🛡️</span>
        <div>
          <strong>ScamiFy Active</strong><br>
          <span style="font-size: 10px; opacity: 0.8;">ANN hover + LSTM navigation</span>
        </div>
      </div>
    `;
    b.style.cssText='position:fixed;bottom:12px;left:12px;background:#0f172a;color:#e2e8f0;font:12px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:8px 12px;border:1px solid #334155;border-radius:8px;z-index:2147483647;box-shadow:0 4px 12px rgba(0,0,0,.4);pointer-events:none;opacity:0;transition:opacity .3s;min-width:140px;';
    document.documentElement.appendChild(b);
    requestAnimationFrame(()=>{ b.style.opacity='1'; });
    setTimeout(()=>{ b.style.opacity='0'; setTimeout(()=> b.remove(),400); }, 2500);
  } catch(e){ scWarn('Activation banner failed', e); }
}


// ---------------------------------------------------------------------------
// Helper Functions for Enhanced Warning System
// ---------------------------------------------------------------------------
function scTruncateUrl(url, maxLength = 50) {
  if (!url || url.length <= maxLength) return url;
  return url.substring(0, maxLength) + '...';
}

function scCreateWarningModal(url, result, level = 'medium') {
  const modal = document.createElement('div');
  modal.id = 'scamify-warning-modal';
  
  const isHigh = level === 'high';
  const bgColor = isHigh ? '#dc2626' : '#f59e0b';
  const title = isHigh ? 'DANGER: Phishing Site Blocked' : 'Warning: Potential Phishing';
  const message = scGetWarningMessage(result);
  
  modal.innerHTML = `
    <div class="sc-modal-backdrop">
      <div class="sc-modal-content">
        <div class="sc-modal-header" style="background: ${bgColor};">
          <h2 style="margin: 0; color: white; font-size: 18px;">
            ${isHigh ? '🚨' : '⚠️'} ${title}
          </h2>
        </div>
        <div class="sc-modal-body">
          <p><strong>URL:</strong> ${scTruncateUrl(url, 60)}</p>
          <p>${message}</p>
          ${result.confidence_level ? `<p><strong>Confidence:</strong> ${result.confidence_level}</p>` : ''}
          ${result.processing_time ? `<p><strong>Analysis time:</strong> ${result.processing_time}ms</p>` : ''}
        </div>
        <div class="sc-modal-footer">
          <button class="sc-block-btn">🛡️ Stay Safe</button>
          <button class="sc-proceed-btn" ${isHigh ? 'disabled' : ''}>
            ${isHigh ? '⏳ Wait 3s...' : '⚠️ Proceed Anyway'}
          </button>
        </div>
      </div>
    </div>
  `;
  
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 2147483647; font-family: system-ui, -apple-system, sans-serif;
  `;
  
  // Add styles for modal components
  const style = document.createElement('style');
  style.textContent = `
    .sc-modal-backdrop {
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center;
    }
    .sc-modal-content {
      background: white; border-radius: 12px; overflow: hidden;
      max-width: 500px; margin: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .sc-modal-body {
      padding: 20px; font-size: 14px; line-height: 1.6;
    }
    .sc-modal-footer {
      padding: 15px 20px; background: #f9fafb; display: flex; gap: 10px; justify-content: flex-end;
    }
    .sc-modal-footer button {
      padding: 8px 16px; border: none; border-radius: 6px; font-weight: 500; cursor: pointer;
    }
    .sc-block-btn {
      background: #059669; color: white;
    }
    .sc-block-btn:hover {
      background: #047857;
    }
    .sc-proceed-btn {
      background: #dc2626; color: white;
    }
    .sc-proceed-btn:hover:not(:disabled) {
      background: #b91c1c;
    }
    .sc-proceed-btn:disabled {
      background: #9ca3af; cursor: not-allowed;
    }
  `;
  
  modal.appendChild(style);
  return modal;
}

function scGetWarningMessage(result) {
  if (!result) return 'Potential security risk detected.';
  
  if (result.model === 'both') {
    if (result.agreement) {
      return `Both AI models (ANN + LSTM) agree this is likely a phishing site. Confidence: ${(result.probability * 100).toFixed(1)}%`;
    } else {
      const annPred = result.ann_prediction?.prediction || 'unknown';
      const lstmPred = result.lstm_prediction?.prediction || 'unknown';
      return `AI models disagree: ANN says "${annPred}", LSTM says "${lstmPred}". Proceeding with caution recommended.`;
    }
  }
  
  const modelName = result.model === 'ann' ? 'Neural Network' : 'LSTM Deep Learning';
  const confidence = (result.probability * 100).toFixed(1);
  
  return `${modelName} model detected potential phishing with ${confidence}% confidence. This site may be attempting to steal your personal information.`;
}

function scInit() {
  if (window.__SCAMIFY_READY) return;
  window.__SCAMIFY_READY = true;
  scSetup();
  console.log('🚀 SCAMIFY: Dual-Model AI System Initialized');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', scInit);
} else {
  scInit();
}

console.log('🎯 SCAMIFY: Dual-Model AI Phishing Detection Engine loaded (ANN + LSTM)');