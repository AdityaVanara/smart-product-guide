/* products.js - Products page: view, add, edit and delete products (CRUD). */

const table = $('#ptable');
const dialog = $('#pdialog');
let editingId = null;           // null = adding a new product
let products = [];

// form field id -> database column
const FIELDS = {
  'f-name': 'name', 'f-brand': 'brand', 'f-amazon': 'price_amazon', 'f-flipkart': 'price_flipkart',
  'f-meesho': 'price_meesho', 'f-rating': 'rating', 'f-reviews': 'review_count', 'f-seller': 'seller_score',
  'f-ram': 'ram_gb', 'f-storage': 'storage_gb', 'f-camera': 'camera_mp', 'f-battery': 'battery_mah',
};

async function loadProducts() {
  products = await api('/api/products?sort=price');
  drawTable();
}

function drawTable() {
  table.textContent = '';
  const head = mk('tr');
  ['Product', 'Amazon', 'Flipkart', 'Meesho', 'Rating', 'Specs', 'Seller', 'Quality', ''].forEach((h) => head.append(mk('th', '', h)));
  table.append(head);
  if (!products.length) {
    const row = mk('tr'); const cell = mk('td', '', 'No products yet. Click "Add product".'); cell.colSpan = 9;
    row.append(cell); table.append(row); return;
  }
  products.forEach((p) => {
    const row = mk('tr');
    const name = mk('td'); name.append(mk('b', '', p.name));
    if (p.brand) name.append(mk('small', '', ' ' + p.brand));
    if (p.is_sample) name.append(document.createTextNode(' '), mk('span', 'tag demo', 'Sample'));
    row.append(name);
    ['price_amazon', 'price_flipkart', 'price_meesho'].forEach((c) => {
      const cell = mk('td', p[c] === p.low_price ? 'win' : '', inr(p[c]));
      row.append(cell);
    });
    row.append(mk('td', '', '★ ' + p.rating + ' (' + p.review_count.toLocaleString('en-IN') + ')'));
    row.append(mk('td', '', `${p.ram_gb} GB · ${p.storage_gb} GB · ${p.camera_mp} MP · ${p.battery_mah} mAh`));
    row.append(mk('td', '', p.seller_score + '/5'));
    row.append(mk('td', '', p.quality));
    const actions = mk('td');
    const edit = mk('button', 'link', 'Edit'); edit.onclick = () => openForm(p);
    const del = mk('button', 'link bad', 'Delete'); del.style.marginLeft = '12px'; del.onclick = () => removeProduct(p);
    actions.append(edit, del);
    row.append(actions);
    table.append(row);
  });
}

function openForm(product) {
  editingId = product ? product.id : null;
  $('#ptitle').textContent = product ? 'Edit product' : 'Add product';
  $('#form-err').textContent = '';
  Object.entries(FIELDS).forEach(([id, column]) => {
    const value = product ? product[column] : '';
    $('#' + id).value = value === null || value === undefined ? '' : value;
  });
  if (!product) $('#f-seller').value = 3;
  dialog.showModal();
}

$('#add-btn').onclick = () => openForm(null);
$('#cancel-btn').onclick = () => dialog.close();

$('#pform').onsubmit = async (event) => {
  event.preventDefault();
  const body = {};
  Object.entries(FIELDS).forEach(([id, column]) => { body[column] = $('#' + id).value; });
  try {
    if (editingId) await api('/api/products/' + editingId, 'PUT', body);
    else await api('/api/products', 'POST', body);
    dialog.close();
    toast(editingId ? 'Product updated' : 'Product added');
    loadProducts();
  } catch (err) {
    $('#form-err').textContent = err.message;
  }
};

async function removeProduct(product) {
  if (!confirm('Delete ' + product.name + '?')) return;
  try {
    await api('/api/products/' + product.id, 'DELETE');
    toast('Product deleted');
    loadProducts();
  } catch (err) { showMessage($('#pmsg'), err.message, true); }
}

loadProducts();
