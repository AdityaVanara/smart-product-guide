/* recommendations.js - AI page: send budget + priority, show ranking and reasons. */

function drawResult(result) {
  const box = $('#rresult');
  box.textContent = '';
  if (!result.best) { box.append(mk('div', 'empty', result.message)); return; }

  box.append(mk('p', 'muted', result.message + ' Confidence in the top pick: ' + result.confidence + '.'));
  const list = mk('div', 'list');
  result.ranking.forEach((p) => {
    const card = mk('div', 'rank-card' + (p.rank === 1 ? ' first' : ''));
    const top = mk('div', 'row between');
    const title = mk('div');
    title.append(mk('h3', '', '#' + p.rank + ' ' + p.name));
    if (p.rank === 1) title.append(mk('span', 'tag g', 'Best product'), document.createTextNode(' '));
    if (p.is_sample) title.append(mk('span', 'tag demo', 'Sample'));
    const score = mk('div'); score.append(mk('div', 'score', p.score), mk('small', '', 'out of 100'));
    top.append(title, score);

    // the four part-scores, so the result can be checked
    const parts = mk('div', 'bars');
    drawBars(parts, [
      { label: 'Price', value: p.parts.price, text: p.parts.price },
      { label: 'Rating quality', value: p.parts.quality, text: p.parts.quality },
      { label: 'Specifications', value: p.parts.specs, text: p.parts.specs },
      { label: 'Seller', value: p.parts.seller, text: p.parts.seller },
    ], { max: 100, color: p.rank === 1 ? 'g' : '' });

    const why = mk('ul', 'reasons');
    p.reasons.forEach((r) => why.append(mk('li', '', r)));
    card.append(top, mk('b', '', 'Why this product?'), why, parts);
    list.append(card);
  });
  box.append(list);
  const w = result.weights;
  box.append(mk('small', '', `Part-scores compare each product with the others inside your budget (0 = weakest, 100 = strongest). Weights used: price ${w.price * 100}%, rating ${w.quality * 100}%, specs ${w.specs * 100}%, seller ${w.seller * 100}%.`));
}

function drawTiers(tiers) {
  drawBars($('#tiers'), tiers.map((t) => ({ label: inr(t.budget), value: t.score, text: t.name + ' (' + t.score + ')' })), { max: 100, color: 'y' });
}

$('#rform').onsubmit = async (event) => {
  event.preventDefault();
  try {
    const result = await api('/api/recommend', 'POST', {
      budget: $('#r-budget').value, priority: $('#r-prio').value, min_ram: $('#r-ram').value });
    $('#rmsg').textContent = '';
    drawResult(result);
    drawTiers(result.tiers);
  } catch (err) { $('#rmsg').textContent = err.message; }
};

// Show the budget table when the page opens (this does not save a preference)
api('/api/tiers').then(drawTiers);
