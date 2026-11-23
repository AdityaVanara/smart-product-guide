/* home.js - home page: original survey bars + live database numbers. */

// Published percentages of the ORIGINAL Google Form survey (57 respondents).
const ORIGINAL = {
  'o-diff': [['Quality doubts', 54.4], ['Different prices', 36.8], ['Comparing specs', 35.1], ['Trusting reviews', 35.1], ['Finding good sellers', 33.3], ['Photos ≠ product', 29.8], ['Too many choices', 24.6]],
  'o-feat': [['Reliable reviews', 35.1], ['Compare specs', 17.5], ['Details in one place', 17.5], ['Price comparison', 14], ['Seller reliability', 8.8], ['Verified photos', 7]],
  'o-plat': [['Amazon', 84.2], ['Flipkart', 77.2], ['Meesho', 31.6], ['Myntra', 24.6], ['Other', 19.3]],
  'o-who': [['Male', 78.9], ['Female', 21.1], ['Age 18–25', 66.7], ['Urban', 86], ['Students', 36.8], ['Employed', 31.6]],
};
Object.entries(ORIGINAL).forEach(([id, rows]) => {
  drawBars($('#' + id), rows.map(([label, value]) => ({ label, value, text: value + '%' })), { max: 100, color: id === 'o-feat' || id === 'o-who' ? 'y' : '' });
});

// Big numbers count up when the page opens
document.querySelectorAll('[data-n]').forEach((el) => countUp(el, +el.dataset.n, 1, '%'));

// Live numbers from the database
api('/api/stats').then((s) => {
  const box = $('#live-stats');
  [[s.total_products, 'products in the database'],
   [s.total_feedback, 'feedback entries'], [s.avg_feedback_rating || '-', 'average feedback rating']].forEach(([n, label]) => {
    const card = mk('div', 'card stat');
    card.append(mk('b', '', n), mk('p', '', label));
    box.append(card);
  });
}).catch(() => {});
