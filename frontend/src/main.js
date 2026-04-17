import './style.css';
import { api } from './api.js';

/* ── State ──────────────────────────────────────── */
const USER_ID = 1;
const S = {
  products: [], cart: [], recs: [], mlHealth: null,
  category: 'All', query: '',
  training: false, loadingProducts: true, loadingCart: true, loadingRecs: false,
};

const CAT_ICON = {
  'Electronics':'🎧','Books':'📚','Clothing':'👕','Home & Kitchen':'🏠',
  'Sports & Fitness':'🏋️','Beauty & Personal Care':'✨','Office & Stationery':'🖊️',
  'Toys & Games':'🎮','Grocery & Food':'☕','Pet Supplies':'🐾',
  'Shoes & Footwear':'👟','Automotive':'🚗','Bags & Luggage':'👜',
  'Jewelry & Watches':'💍','Musical Instruments':'🎵','Health & Wellness':'💊',
  'General':'📦',
};
const icon = c => CAT_ICON[c] || '📦';
const byId = id => S.products.find(p => p.id === id);
const inCart = id => S.cart.some(c => c.productId === id);

/* ── Toast ──────────────────────────────────────── */
function toast(msg, type='info') {
  let c = document.getElementById('toast-container');
  if (!c) { c = document.createElement('div'); c.id='toast-container'; c.className='toast-container'; document.body.appendChild(c); }
  const el = document.createElement('div'); el.className = `toast ${type}`;
  el.innerHTML = `<span>${{success:'✓',error:'✕',info:'ℹ'}[type]}</span> ${msg}`;
  c.appendChild(el); setTimeout(() => el.remove(), 3200);
}

/* ── Filters ───────────────────────────────────── */
function getCategories() { return ['All', ...new Set(S.products.map(p => p.category))].sort((a,b) => a==='All'?-1:b==='All'?1:a.localeCompare(b)); }
function getFiltered() {
  let l = S.products;
  if (S.category !== 'All') l = l.filter(p => p.category === S.category);
  if (S.query.trim()) { const q = S.query.toLowerCase(); l = l.filter(p => p.name.toLowerCase().includes(q)||(p.description||'').toLowerCase().includes(q)); }
  return l;
}

/* ── RENDER ─────────────────────────────────────── */
function render() {
  const app = document.getElementById('app');
  app.innerHTML = renderNav() + `<div class="page">`
    + renderCart()
    + renderRecs()
    + renderSearch()
    + renderTabs()
    + `<h1 class="heading">🛍️ Products <span class="badge">${getFiltered().length}</span></h1>`
    + renderGrid()
    + `</div>`;
  bind();
}

/* ── Nav ── */
function renderNav() {
  const s = S.mlHealth;
  const cls = s ? (s.status==='healthy'?'ok':'off') : 'wait';
  const txt = s ? (s.status==='healthy'?`ML Active · ${s.rulesCount} rules`:'ML Offline') : 'Connecting…';
  return `<nav class="navbar"><div class="navbar-inner">
    <a class="nav-left" href="#"><div class="nav-logo">🛒</div><div><div class="nav-title">SmartCart</div><div class="nav-sub">AI Recommendations</div></div></a>
    <div class="nav-right">
      <span class="status-pill ${cls}"><span class="status-dot"></span>${txt}</span>
    </div>
  </div></nav>`;
}

/* ── Cart Strip ── */
function renderCart() {
  if (S.loadingCart || !S.cart.length) return '';
  const total = S.cart.reduce((s,i) => s + i.productPrice * i.quantity, 0);
  const n = S.cart.reduce((s,i) => s + i.quantity, 0);
  return `<div class="cart-strip">
    <div class="cart-strip-header">
      <div class="cart-strip-title">🛒 Your Cart <span class="badge">${n}</span></div>
      <button class="btn-clear" id="btn-clear">Clear All</button>
    </div>
    <div class="cart-items">${S.cart.map(renderCartChip).join('')}</div>
    <div class="cart-strip-footer">
      <div class="cart-total"><span>Total:</span>$${total.toFixed(2)}</div>
    </div>
  </div>`;
}

function renderCartChip(item) {
  const p = byId(item.productId);
  const imgUrl = p?.imageUrl || item.productImageUrl;
  const hasImg = imgUrl && !imgUrl.startsWith('/');
  return `<div class="cart-chip">
    ${hasImg
      ? `<img class="cart-chip-img" src="${imgUrl}" alt="${item.productName}" onerror="this.outerHTML='<div class=\\'cart-chip-img-placeholder\\'>${icon(item.productCategory)}</div>'" />`
      : `<div class="cart-chip-img-placeholder">${icon(item.productCategory)}</div>`}
    <div>
      <div class="cart-chip-name">${item.productName}</div>
      <div class="cart-chip-price">$${item.productPrice.toFixed(2)} × ${item.quantity}</div>
    </div>
    <button class="cart-chip-remove" data-rm="${item.productId}">×</button>
  </div>`;
}

/* ── Recommendations Section ── */
function renderRecs() {
  // Only show this whole section if we have cart items
  if (!S.cart.length) return '';

  let body;
  if (S.loadingRecs || S.training) {
    body = `<div class="recs-loading"><span class="spinner"></span> Finding recommendations for you…</div>`;
  } else if (!S.recs.length) {
    body = `<div class="recs-empty"><span class="recs-empty-icon">🧠</span>Click "Train Model" to get AI recommendations<br/>
      <button class="btn-train" id="btn-train" style="margin-top:10px"${S.training?' disabled':''}>🧠 Train ML Model</button></div>`;
  } else {
    body = `<div class="recs-grid">${S.recs.map(renderRecCard).join('')}</div>`;
  }

  return `<div class="recs-section">
    <div class="recs-header">
      <div class="recs-title">✨ Recommended For You ${S.recs.length?`<span class="badge">${S.recs.length}</span>`:''}</div>
      ${S.recs.length ? `<button class="btn-train" id="btn-train"${S.training?' disabled':''}>${S.training?'<span class="spinner"></span> Training':'🧠 Retrain'}</button>` : ''}
    </div>
    ${body}
  </div>`;
}

function formatScore(score) {
  const mx = S.recs.length ? Math.max(...S.recs.map(r => r.score)) : 1;
  return Math.round(mx > 0 ? Math.min((score / mx) * 99, 99) : 0);
}

function renderRecCard(r) {
  const exp = r.explanations?.[0];
  const hasImg = r.imageUrl && !r.imageUrl.startsWith('/');
  const added = inCart(r.productId);
  return `<div class="rec-card">
    ${hasImg
      ? `<img class="rec-card-img" src="${r.imageUrl}" alt="${r.productName}" loading="lazy" onerror="this.outerHTML='<div class=\\'rec-card-img-placeholder\\'>${icon(r.category)}</div>'" />`
      : `<div class="rec-card-img-placeholder">${icon(r.category)}</div>`}
    <div class="rec-card-body">
      <div class="rec-card-match">⚡ ${formatScore(r.score)}% match</div>
      <div class="rec-card-cat">${r.category}</div>
      <div class="rec-card-name">${r.productName}</div>
      ${exp ? `<div class="rec-card-why">${exp.detail}</div>` : ''}
      <div class="rec-card-footer">
        <div class="rec-card-price"><small>$</small>${r.price.toFixed(2)}</div>
        <button class="btn-add-rec" data-addrec="${r.productId}">${added?'✓ Added':'+ Add'}</button>
      </div>
    </div>
  </div>`;
}

/* ── Search ── */
function renderSearch() {
  return `<div class="search-box"><span>🔍</span><input id="search-input" placeholder="Search 250+ products…" value="${S.query}" autocomplete="off" /></div>`;
}

/* ── Category Tabs ── */
function renderTabs() {
  return `<div class="tabs">${getCategories().map(c =>
    `<button class="tab${S.category===c?' on':''}" data-cat="${c}">${c==='All'?'🏷️':icon(c)} ${c}</button>`
  ).join('')}</div>`;
}

/* ── Product Grid ── */
function renderGrid() {
  if (S.loadingProducts) return `<div class="grid">${'<div class="skeleton skel-card"></div>'.repeat(12)}</div>`;
  const items = getFiltered();
  if (!items.length) return `<div class="empty"><div class="empty-icon">🔍</div><p>No products found</p></div>`;
  return `<div class="grid">${items.map(renderCard).join('')}</div>`;
}

function renderCard(p) {
  const added = inCart(p.id);
  const hasImg = p.imageUrl && !p.imageUrl.startsWith('/');
  return `<div class="card">
    ${hasImg
      ? `<img class="card-img" src="${p.imageUrl}" alt="${p.name}" loading="lazy" onerror="this.outerHTML='<div class=\\'card-img-ph\\'>${icon(p.category)}</div>'" />`
      : `<div class="card-img-ph">${icon(p.category)}</div>`}
    <div class="card-body">
      <div class="card-cat">${p.category}</div>
      <div class="card-name">${p.name}</div>
      <div class="card-desc">${p.description||''}</div>
      <div class="card-foot">
        <div class="card-price"><small>$</small>${p.price.toFixed(2)}</div>
        <button class="btn-add${added?' added':''}" data-add="${p.id}">${added?'✓ Added':'+ Add'}</button>
      </div>
    </div>
  </div>`;
}

/* ── EVENTS ─────────────────────────────────────── */
function bind() {
  // Categories
  document.querySelectorAll('.tab').forEach(t =>
    t.addEventListener('click', () => { S.category = t.dataset.cat; render(); })
  );
  // Search
  const si = document.getElementById('search-input');
  if (si) si.addEventListener('input', () => {
    S.query = si.value; render();
    const n = document.getElementById('search-input');
    if (n) { n.focus(); n.selectionStart = n.selectionEnd = n.value.length; }
  });
  // Add to cart
  document.querySelectorAll('[data-add]').forEach(b =>
    b.addEventListener('click', e => { e.stopPropagation(); if (!inCart(+b.dataset.add)) addToCart(+b.dataset.add); })
  );
  // Add from recommendation
  document.querySelectorAll('[data-addrec]').forEach(b =>
    b.addEventListener('click', e => { e.stopPropagation(); if (!inCart(+b.dataset.addrec)) addToCart(+b.dataset.addrec); })
  );
  // Remove from cart
  document.querySelectorAll('[data-rm]').forEach(b =>
    b.addEventListener('click', () => removeFromCart(+b.dataset.rm))
  );
  // Clear cart
  document.getElementById('btn-clear')?.addEventListener('click', clearCart);
  // Train
  document.getElementById('btn-train')?.addEventListener('click', trainModel);
}

/* ── ACTIONS ────────────────────────────────────── */
async function addToCart(pid) {
  try {
    const item = await api.addToCart(USER_ID, pid);
    const idx = S.cart.findIndex(c => c.productId === pid);
    idx >= 0 ? (S.cart[idx] = item) : S.cart.push(item);
    toast(`${byId(pid)?.name||'Product'} added to cart`, 'success');
    render();
    // Auto-train + fetch recommendations
    if (!S.mlHealth?.modelTrained && !S.training) {
      await trainModel();
    } else {
      await fetchRecs();
    }
  } catch (e) { toast('Failed to add: ' + e.message, 'error'); }
}

async function removeFromCart(pid) {
  try {
    await api.removeFromCart(USER_ID, pid);
    S.cart = S.cart.filter(c => c.productId !== pid);
    toast('Removed from cart', 'info');
    render();
    if (S.cart.length) await fetchRecs();
    else { S.recs = []; render(); }
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

async function clearCart() {
  try {
    await api.clearCart(USER_ID);
    S.cart = []; S.recs = [];
    toast('Cart cleared', 'info');
    render();
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

async function trainModel() {
  if (S.training) return;
  S.training = true; render();
  toast('Training AI model…', 'info');
  try {
    const r = await api.trainModel();
    toast(`Trained! ${r.associationRulesCount} rules discovered`, 'success');
    await checkHealth();
    if (S.cart.length) await fetchRecs();
  } catch (e) { toast('Training failed: ' + e.message, 'error'); }
  finally { S.training = false; render(); }
}

async function fetchRecs() {
  if (!S.cart.length) { S.recs = []; return; }
  S.loadingRecs = true; render();
  try {
    S.recs = await api.getRecommendations(USER_ID, 5);
  } catch (e) {
    console.warn('Recs failed:', e.message);
    S.recs = [];
  }
  S.loadingRecs = false; render();
}

async function checkHealth() {
  try { S.mlHealth = await api.mlHealth(); }
  catch { S.mlHealth = { status: 'unavailable', modelTrained: false, rulesCount: 0 }; }
}

/* ── INIT ───────────────────────────────────────── */
async function init() {
  render();
  const [prods, cart] = await Promise.allSettled([api.getProducts(), api.getCart(USER_ID), checkHealth()]);
  if (prods.status === 'fulfilled') S.products = prods.value;
  else toast('Backend not running — start Spring Boot on :8080', 'error');
  if (cart.status === 'fulfilled') S.cart = cart.value;
  S.loadingProducts = false; S.loadingCart = false;
  render();
  if (S.cart.length) {
    if (S.mlHealth?.modelTrained) await fetchRecs();
    else await trainModel();
  }
}

init();
