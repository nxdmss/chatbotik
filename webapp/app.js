// WebApp main JS for shop
let PRODUCTS = [];

async function fetchProducts(){
  try{
    const res = await fetch('/webapp/products.json');
    if(res.ok){ PRODUCTS = await res.json(); return; }
  }catch(e){}
  // fallback to default
  PRODUCTS = [
    {id:'p1', title:'Кроссовки Sprint', price:4990, sizes:[38,39,40,41], img:''},
    {id:'p2', title:'Кеды Classic', price:3490, sizes:[36,37,38,39,40], img:''},
    {id:'p3', title:'Ботинки Trail', price:7990, sizes:[40,41,42,43], img:''}
  ];
}

const productsEl = document.getElementById('products');
const searchInput = document.getElementById('search');
const cartList = document.getElementById('cart-list');
const totalEl = document.getElementById('total');
const checkoutBtn = document.getElementById('checkout');
const clearBtn = document.getElementById('clear');
const adminFormRoot = document.createElement('div');
adminFormRoot.style.margin = '12px 0';

// show admin form if ?admin=1
function isAdminView(){
  try{
    // allow admin mode via ?admin=1 OR server-side ADMINS check using Telegram initData
    if(new URLSearchParams(window.location.search).get('admin') === '1') return true;
    return false;
  }catch(e){return false}
}

// check if current user is admin by querying server /webapp/admins.json and comparing to Telegram init data
async function isUserAdmin(){
  // first, try URL param
  if(isAdminView()) return true;
  // try server-provided admins list
  try{
    const r = await fetch('/webapp/admins.json');
    if(!r.ok) return false;
    const admins = await r.json(); // array of strings
    // try to extract user id from Telegram WebApp initDataUnsafe
    if(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe){
      const user = window.Telegram.WebApp.initDataUnsafe.user;
      const uid = user && (user.id || user.user_id || user.id_str);
      if(uid && admins.map(String).includes(String(uid))) return true;
    }
  }catch(e){ }
  return false;
}

function renderAdminForm(){
  adminFormRoot.innerHTML = `
    <h3>Админ: добавить товар</h3>
    <div style="display:flex;flex-direction:column;gap:8px;max-width:420px">
      <input id="adm_title" placeholder="Название товара" />
      <input id="adm_price" placeholder="Цена (руб)" />
      <input id="adm_sizes" placeholder="Размеры через запятую, например: 38,39,40" />
      <input id="adm_img" placeholder="URL фото (опционально)" />
      <input id="adm_file" type="file" accept="image/*" />
      <img id="adm_preview" src="" alt="preview" style="max-width:180px;display:none;border:1px solid #ddd;padding:4px;margin-top:6px" />
      <button id="adm_add" class="btn">Добавить товар</button>
    </div>
  `;
  // Insert admin form at top of products section
  const section = document.querySelector('main section') || document.querySelector('main .grid section');
  if(section) section.prepend(adminFormRoot);
  const btn = document.getElementById('adm_add');
  btn.addEventListener('click', async ()=>{
    const title = document.getElementById('adm_title').value.trim();
    const price = parseInt(document.getElementById('adm_price').value || '0');
    const sizes = (document.getElementById('adm_sizes').value||'').split(',').map(s=>parseInt(s)).filter(Boolean);
    let img = document.getElementById('adm_img').value.trim()||'';
    const fileInput = document.getElementById('adm_file');
    if(!title || !price) return alert('Введите название и цену');
    // if file selected, upload it first
    if(fileInput && fileInput.files && fileInput.files[0]){
      const fd = new FormData();
      fd.append('file', fileInput.files[0]);
      try{
        const r = await fetch('/webapp/upload', {method:'POST', body: fd});
        if(r.ok){ const j = await r.json(); img = j.url; }
      }catch(e){ console.warn('upload failed', e); }
    }
    const prod = {title, price, sizes, photo: img, currency: 'RUB'};
    const payload = {action:'add_product', product: prod};
    if(window.Telegram && window.Telegram.WebApp){
      try{
        window.Telegram.WebApp.sendData(JSON.stringify(payload));
        alert('Запрос отправлен администратору бота.');
      }catch(e){
        // fallback: try server endpoint
        console.warn('sendData failed', e);
        const tryFallback = confirm('Не удалось отправить данные в бота через Telegram API. Попробовать отправить напрямую на сервер (требует admin=1)?');
        if(tryFallback){
          try{
            const r = await fetch('/webapp/add_product?admin=1', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
            const j = await r.json();
            if(r.ok && j.ok){ alert('Товар добавлен через сервер fallback.'); }
            else alert('Fallback failed: ' + (j.error || r.status));
          }catch(er){ alert('Fallback request failed: ' + er.message); }
        }
      }
    } else {
      // not inside Telegram — try direct server post when admin=1 param present
      const forced = new URLSearchParams(window.location.search).get('admin') === '1';
      if(forced){
        try{
          const r = await fetch('/webapp/add_product?admin=1', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
          const j = await r.json();
          if(r.ok && j.ok){ alert('Товар добавлен через сервер.'); }
          else alert('Добавление не удалось: ' + (j.error || r.status));
        }catch(e){ alert('Ошибка при добавлении через сервер: ' + e.message); }
      } else {
        alert('Откройте админскую версию внутри Telegram (admin=1) чтобы добавить товар.');
      }
    }
  });

  // preview when URL or file selected
  const preview = document.getElementById('adm_preview');
  const imgInput = document.getElementById('adm_img');
  imgInput.addEventListener('input', ()=>{
    const v = imgInput.value.trim();
    if(v){ preview.src = v; preview.style.display = 'block'; } else { preview.src=''; preview.style.display='none'; }
  });
  const fileInputEl = document.getElementById('adm_file');
  fileInputEl.addEventListener('change', ()=>{
    const f = fileInputEl.files && fileInputEl.files[0];
    if(!f) return;
    const url = URL.createObjectURL(f);
    preview.src = url; preview.style.display = 'block';
  });
}

// cart: { key: {id, qty, size} }, key = id + '::' + size
const CART_KEY = 'tupabotik_cart_v1';
const cart = JSON.parse(localStorage.getItem(CART_KEY) || '{}');

function money(v){ return v.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") + ' ₽'; }

function renderProducts(){
  productsEl.innerHTML = '';
  // filter by search
  const q = (searchInput && searchInput.value || '').toLowerCase().trim();
  PRODUCTS.forEach(p=>{
    if(q){
      const hay = (p.title + ' ' + (p.sku||'') + ' ' + (p.tags||'')).toLowerCase();
      if(!hay.includes(q)) return;
    }
    const card = document.createElement('div'); card.className='card';
    const photoSrc = p.photo || p.img || 'data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=400 height=300><rect width=400 height=300 fill=%23eeeeee/></svg>';
  // skip deleted items (hidden by default)
  if(p.deleted) return;
  const isDeleted = false;
    card.innerHTML = `
      <img src="${photoSrc}" alt="">
      <div class="title">${p.title}</div>
      <div class="price">${money(p.price)}</div>
      <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
        <select class="size-select" data-id="${p.id}">
          ${p.sizes.map(s=>`<option value="${s}">${s}</option>`).join('')}
        </select>
        <div class="qty">
          <button class="dec" data-id="${p.id}">-</button>
          <div style="min-width:28px;text-align:center" data-qtyid="${p.id}">1</div>
          <button class="inc" data-id="${p.id}">+</button>
        </div>
      </div>
      <div style="margin-top:10px;display:flex;gap:8px">
        ${isDeleted?'<span style="color:#a00">(удалён)</span>':''}
        <button class="btn add" data-id="${p.id}" ${isDeleted? 'disabled':''}>Добавить в корзину</button>
        <button class="btn ghost" data-id="${p.id}" data-action="quickbuy" ${isDeleted? 'disabled':''}>Купить</button>
        ${window._isAdmin? `<button class="btn danger del" data-id="${p.id}">Удалить</button>` : ''}
      </div>
    `;
    productsEl.appendChild(card);
  });
}

function rebuildCart(){
  cartList.innerHTML='';
  let total=0;
  Object.values(cart).forEach(item=>{
    const row = document.createElement('div'); row.className='cart-item';
    const title = document.createElement('div');
    title.innerHTML = `<div>${item.title} <small style="color:var(--muted)">(${item.size})</small></div><div style="color:var(--muted)">x${item.qty}</div>`;
    const price = document.createElement('div');
    price.textContent = money(item.qty * item.price);
    row.appendChild(title); row.appendChild(price);
    cartList.appendChild(row);
    total += item.qty * item.price;
  });
  totalEl.textContent = money(total);
  return total;
}

function persistCart(){
  try{ localStorage.setItem(CART_KEY, JSON.stringify(cart)); }catch(e){}
}

// helpers to get quantity element for product
function findQtyEl(pid){ return document.querySelector(`[data-qtyid='${pid}']`); }

productsEl.addEventListener('click', (e)=>{
  const add = e.target.closest('.add');
  const quick = e.target.closest('[data-action="quickbuy"]');
  const inc = e.target.closest('.inc');
  const dec = e.target.closest('.dec');
  if(inc||dec){
    const id = (inc||dec).dataset.id; const qtyEl = findQtyEl(id);
    let v = parseInt(qtyEl.textContent||'1');
    if(inc) v++; else v = Math.max(1, v-1);
    qtyEl.textContent = v;
    return;
  }
  if(add || quick){
    const id = (add||quick).dataset.id;
    const select = document.querySelector(`.size-select[data-id='${id}']`);
    const size = select ? select.value : '';
    const qtyEl = findQtyEl(id); const qty = parseInt(qtyEl.textContent||'1');
    const key = id + '::' + size;
    const prod = PRODUCTS.find(p=>p.id===id);
    if(!prod) return;
    if(!cart[key]){
      cart[key] = {id:prod.id, title:prod.title, price:prod.price, qty:0, size};
    }
    // for quickbuy, replace qty, else add
    if((add && !quick) || add) cart[key].qty += qty;
    if(quick) cart[key].qty = qty;
    // reset qty display to 1
    if(qtyEl) qtyEl.textContent = '1';
    rebuildCart();
    persistCart();
    if(quick){ doCheckout(); }
  }
  // delete product (admin only)
  const del = e.target.closest('.del');
  if(del){
    const id = del.dataset.id;
    if(!window._isAdmin){ return alert('Только администратор может удалять товары'); }
    if(!confirm('Удалить товар из каталога?')) return;
    fetch('/webapp/delete_product?admin=1', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id})})
      .then(async r => {
        const j = await r.json().catch(()=>({}));
        if(r.ok) { alert('Товар удалён'); location.reload(); }
        else alert('Ошибка удаления: ' + (j.error || r.status));
      }).catch(e=>alert('Ошибка запроса: '+e.message));
  }
  const restoreBtn = e.target.closest('[data-action="restore"]');
  if(restoreBtn){
    const id = restoreBtn.dataset.id;
    if(!window._isAdmin) return alert('Только администратор может восстанавливать товары');
    if(!confirm('Восстановить товар?')) return;
    fetch('/webapp/restore_product?admin=1', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id})})
      .then(async r => {
        const j = await r.json().catch(()=>({}));
        if(r.ok) { alert('Товар восстановлен'); location.reload(); }
        else alert('Ошибка восстановления: ' + (j.error || r.status));
      }).catch(e=>alert('Ошибка запроса: '+e.message));
  }
});

clearBtn.addEventListener('click', ()=>{ Object.keys(cart).forEach(k=>delete cart[k]); rebuildCart(); persistCart(); });

// cart toggle
const toggleCartBtn = document.getElementById('toggle_cart');
if(toggleCartBtn){
  toggleCartBtn.addEventListener('click', ()=>{
    const sidebar = document.querySelector('.sidebar');
    if(!sidebar) return;
    sidebar.style.display = sidebar.style.display === 'none' ? 'block' : 'none';
  });
}

// search input
if(searchInput){
  searchInput.addEventListener('input', ()=>{ renderProducts(); });
}

function doCheckout(){
  const items = Object.values(cart).map(i=>({id:i.id, qty:i.qty, size:i.size}));
  const total = rebuildCart();
  const payload = {action:'checkout', items, total};
  if(window.Telegram && window.Telegram.WebApp){
    try{
      window.Telegram.WebApp.sendData(JSON.stringify(payload));
      // попытка закрыть WebApp для удобства пользователя
      try{ window.Telegram.WebApp.close(); }catch(e){}
      // очистим локальную корзину после отправки
      Object.keys(cart).forEach(k=>delete cart[k]); rebuildCart(); persistCart();
    }catch(e){
      alert('Не удалось отправить данные в бота.');
    }
  } else {
    alert('Откройте этот магазин внутри Telegram, чтобы оформление прошло автоматически.');
  }
}

checkoutBtn.addEventListener('click', doCheckout);

// init flow
(async ()=>{
  await fetchProducts();
  const admin = await isUserAdmin();
  window._isAdmin = admin;
  if(admin) renderAdminForm();
  renderProducts();
  rebuildCart();
  // no show-deleted toggle (deleted items are hidden)
  try{ if(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.expand) window.Telegram.WebApp.expand(); }catch(e){}
})();
