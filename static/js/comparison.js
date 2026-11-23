/* comparison.js - Compare page: budget, sort, search and side-by-side table. */

const budget = $('#bud');
let shortlist = [];   // product ids saved in the database

async function refresh() {
  $('#budv').textContent = inr(+budget.value);
  const query = new URLSearchParams({ budget: budget.value, sort: $('#sort').value, q: $('#q').value });
  const [products, ids] = await Promise.all([api('/api/products?' + query), api('/api/shortlist')]);
  shortlist = ids;
  drawProducts(products);
  drawComparison();
}

function drawProducts(products) {
  const box = $('#plist');
  box.textContent = '';
  if (!products.length) box.append(mk('div', 'empty', 'No products match. Raise the budget or clear the search.'));
  products.forEach((p) => {
    const selected = shortlist.includes(p.id);
    const card = mk('div', 'prod' + (selected ? ' sel' : ''));
    const tags = mk('div', 'tags');
    (p.badges || []).forEach((b) => tags.append(mk('span', 'tag ' + (b === 'Best match' ? 'g' : b === 'Top rated' ? 'b' : ''), b)));
    if (p.is_sample) tags.append(mk('span', 'tag demo', 'Sample'));
    card.append(tags, mk('h3', '', p.name), mk('div', 'pr', inr(p.low_price)),
      mk('small', '', 'Cheapest on ' + p.low_platform),
      mk('small', '', '★ ' + p.rating + ' · ' + p.review_count.toLocaleString('en-IN') + ' reviews'),
      mk('small', '', `${p.ram_gb} GB · ${p.storage_gb} GB · ${p.camera_mp} MP`));
    const actions = mk('div', 'actions');
    const button = mk('button', 'btn' + (selected ? ' alt' : ''), selected ? 'Remove' : 'Compare');
    button.onclick = () => toggle(p.id, selected);
    actions.append(button);
    card.append(actions);
    box.append(card);
  });
  $('#shortmsg').textContent = shortlist.length ? shortlist.length + ' of 3 selected' : 'Pick products to compare.';
}

async function toggle(id, selected) {
  try {
    await api('/api/shortlist/' + id, selected ? 'DELETE' : 'POST');
    refresh();
  } catch (err) { $('#shortmsg').textContent = err.message; }
}

async function drawComparison() {
  const box = $('#cmp');
  box.textContent = '';
  if (shortlist.length < 2) { box.hidden = true; return; }
  const data = await api('/api/compare');
  const items = data.products;
  box.hidden = false;

  const table = mk('table');
  const head = mk('tr');
  head.append(mk('th', '', 'Compare'));
  items.forEach((p) => head.append(mk('th', p.id === data.best_match_id ? 'best-col' : '', p.name)));
  table.append(head);

  // label, how to show it, number used to find the winner, 1 = smaller wins, -1 = bigger wins
  const rows = [
    ['Amazon', (p) => inr(p.price_amazon), (p) => p.price_amazon, 1],
    ['Flipkart', (p) => inr(p.price_flipkart), (p) => p.price_flipkart, 1],
    ['Meesho', (p) => inr(p.price_meesho), (p) => p.price_meesho, 1],
    ['Lowest price', (p) => inr(p.low_price) + ' (' + p.low_platform + ')', (p) => p.low_price, 1],
    ['Customer rating', (p) => p.rating + ' / 5', (p) => p.rating, -1],
    ['Reviews', (p) => p.review_count.toLocaleString('en-IN'), (p) => p.review_count, -1],
    ['Seller reliability', (p) => p.seller_score + ' / 5', (p) => p.seller_score, -1],
    ['Memory', (p) => p.ram_gb + ' GB RAM', (p) => p.ram_gb, -1],
    ['Storage', (p) => p.storage_gb + ' GB', (p) => p.storage_gb, -1],
    ['Camera', (p) => p.camera_mp + ' MP', (p) => p.camera_mp, -1],
    ['Battery', (p) => p.battery_mah + ' mAh', (p) => p.battery_mah, -1],
    ['Quality check', (p) => p.quality, (p) => null, 0],
    ['Overall match score', (p) => p.match_score + ' / 100', (p) => p.match_score, -1],
  ];
  rows.forEach(([label, show, value, direction]) => {
    const row = mk('tr');
    row.append(mk('th', '', label));
    // only compare products that actually have a value (a missing price is not "0")
    const numbers = items.map(value).filter((v) => v !== null && v !== undefined);
    const winner = direction === 0 || !numbers.length ? null : (direction > 0 ? Math.min(...numbers) : Math.max(...numbers));
    items.forEach((p) => {
      let cls = winner !== null && value(p) === winner ? 'win' : '';
      if (p.id === data.best_match_id) cls += ' best-col';
      row.append(mk('td', cls.trim(), show(p)));
    });
    table.append(row);
  });
  const best = items.find((p) => p.id === data.best_match_id);
  box.append(table, mk('small', '', 'Green marks the best value in each row. The shaded column is the best overall match (' + best.name + '). Sample products use demo data.'));
}

[budget, $('#q'), $('#sort')].forEach((el) => el.addEventListener('input', refresh));
$('#clr').onclick = async () => { await api('/api/shortlist', 'DELETE'); refresh(); };
refresh();
