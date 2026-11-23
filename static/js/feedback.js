/* feedback.js - Feedback page: star rating, save, edit, delete, average. */

let rating = 0;
let editingId = null;
const starBox = $('#stars');

function paintStars() {
  [...starBox.children].forEach((b, i) => b.classList.toggle('on', i < rating));
}
for (let i = 1; i <= 5; i++) {
  const b = mk('button', '', '★');
  b.type = 'button';
  b.setAttribute('role', 'radio');
  b.setAttribute('aria-label', i + ' star');
  b.onclick = () => { rating = i; paintStars(); };
  starBox.append(b);
}

function resetForm() {
  editingId = null; rating = 0; paintStars();
  $('#fn').value = ''; $('#fc').value = '';
  $('#ftitle').textContent = 'New feedback';
  $('#fsave').textContent = 'Save feedback';
  $('#fcancel').hidden = true;
}

async function loadFeedback() {
  const list = await api('/api/feedback');
  $('#cnt').textContent = 'Saved feedback (' + list.length + ')';
  const average = list.length ? (list.reduce((sum, f) => sum + f.rating, 0) / list.length).toFixed(2) : null;
  $('#avg').textContent = average ? 'Average rating: ' + average + ' / 5 from ' + list.length + ' entries' : '';
  const box = $('#flist');
  box.textContent = '';
  if (!list.length) box.append(mk('div', 'empty', 'Nothing saved yet. Your entries will appear here.'));
  list.forEach((f) => {
    const item = mk('div', 'item');
    const title = mk('b', '', (f.name || 'Anonymous') + ' · ' + stars(f.rating));
    if (f.is_sample) title.append(document.createTextNode(' '), mk('span', 'tag demo', 'Demo'));
    item.append(title, mk('div', '', f.comment || '(no comment)'),
      mk('small', '', 'Likes: ' + (f.helpful_feature || '-') + ' · ' + f.created_at));
    const actions = mk('div', 'row');
    const edit = mk('button', 'link', 'Edit');
    edit.onclick = () => {
      editingId = f.id; rating = f.rating; paintStars();
      $('#fn').value = f.name; $('#fc').value = f.comment; $('#ff').value = f.helpful_feature;
      $('#ftitle').textContent = 'Edit feedback';
      $('#fsave').textContent = 'Update feedback';
      $('#fcancel').hidden = false;
      $('#fform').scrollIntoView({ behavior: 'smooth' });
    };
    const del = mk('button', 'link bad', 'Delete');
    del.onclick = async () => { await api('/api/feedback/' + f.id, 'DELETE'); loadFeedback(); };
    actions.append(edit, del);
    item.append(actions);
    box.append(item);
  });
}

$('#fform').onsubmit = async (event) => {
  event.preventDefault();
  const body = { name: $('#fn').value, rating, helpful_feature: $('#ff').value, comment: $('#fc').value };
  try {
    if (editingId) await api('/api/feedback/' + editingId, 'PUT', body);
    else await api('/api/feedback', 'POST', body);
    showMessage($('#fmsg'), editingId ? 'Updated. Thank you!' : 'Saved in the database. Thank you!');
    resetForm();
    loadFeedback();
  } catch (err) { showMessage($('#fmsg'), err.message, true); }
};
$('#fcancel').onclick = resetForm;
$('#all').onclick = async () => {
  if (confirm('Delete all saved feedback?')) { await api('/api/feedback', 'DELETE'); loadFeedback(); }
};
loadFeedback();
