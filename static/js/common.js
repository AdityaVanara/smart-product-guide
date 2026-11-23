/* common.js - small helpers used by every page. */

const $ = (selector) => document.querySelector(selector);

// Create an element. textContent (not innerHTML) keeps user text safe.
function mk(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined && text !== null) el.textContent = text;
  return el;
}

// Format a number as Indian rupees, e.g. 22499 -> ₹22,499
const inr = (n) => (n === null || n === undefined ? '-' : '₹' + Number(n).toLocaleString('en-IN'));

const stars = (n) => '★'.repeat(n) + '☆'.repeat(5 - n);

// Talk to the Flask backend. Returns the JSON, or throws an Error with the server's message.
async function api(url, method = 'GET', body = null) {
  const options = { method, headers: {} };
  if (body !== null) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}

// Small message at the bottom of the screen
function toast(text) {
  let box = $('#toast');
  if (!box) { box = mk('div', 'toast'); box.id = 'toast'; document.body.append(box); }
  box.textContent = text;
  box.classList.add('show');
  setTimeout(() => box.classList.remove('show'), 2200);
}

function showMessage(element, text, isError) {
  element.textContent = text;
  element.className = 'msg' + (isError ? ' err' : '');
}

/* ---------- charts (plain JavaScript, no library needed) ---------- */

// Horizontal bar chart. items = [{label, value, text?}]
function drawBars(container, items, options = {}) {
  container.textContent = '';
  if (!items.length) { container.append(mk('div', 'empty', 'No data yet.')); return; }
  const max = options.max || Math.max(...items.map((i) => i.value), 1);
  items.forEach((item) => {
    const row = mk('div', 'bar');
    row.title = item.label + ': ' + (item.text || item.value);
    const track = mk('div', 'track');
    const fill = mk('div', 'fill' + (options.color ? ' ' + options.color : ''));
    track.append(fill);
    row.append(mk('span', '', item.label), track, mk('span', '', item.text || item.value));
    container.append(row);
    // set the width after the element is on screen, so the CSS animation plays
    requestAnimationFrame(() => { fill.style.width = (item.value / max * 100) + '%'; });
  });
}

// Donut chart made of SVG circles. items = [{label, value}]
const DONUT_COLORS = ['#2a56e8', '#ffb020', '#12a36b', '#e5484d', '#8e5cf7', '#6b7a99'];
function drawDonut(container, items) {
  container.textContent = '';
  const total = items.reduce((sum, i) => sum + i.value, 0);
  if (!total) { container.append(mk('div', 'empty', 'No data yet.')); return; }
  const radius = 54, circumference = 2 * Math.PI * radius;
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 150 150');
  const legend = mk('div', 'legend');
  let offset = 0;
  items.forEach((item, index) => {
    const part = item.value / total;
    const circle = document.createElementNS(ns, 'circle');
    const color = DONUT_COLORS[index % DONUT_COLORS.length];
    circle.setAttribute('cx', 75); circle.setAttribute('cy', 75); circle.setAttribute('r', radius);
    circle.setAttribute('fill', 'none'); circle.setAttribute('stroke', color); circle.setAttribute('stroke-width', 24);
    circle.setAttribute('stroke-dasharray', `${part * circumference} ${circumference}`);
    circle.setAttribute('stroke-dashoffset', -offset * circumference);
    circle.setAttribute('transform', 'rotate(-90 75 75)');
    const tip = document.createElementNS(ns, 'title');
    tip.textContent = `${item.label}: ${item.value} (${(part * 100).toFixed(1)}%)`;
    circle.append(tip);
    svg.append(circle);
    const line = mk('div');
    const dot = mk('i'); dot.style.background = color;
    line.append(dot, document.createTextNode(`${item.label} - ${(part * 100).toFixed(1)}%`));
    legend.append(line);
    offset += part;
  });
  const box = mk('div', 'donut-box');
  box.append(svg, legend);
  container.append(box);
}

// Count a number up from 0 (small visual effect for big numbers)
function countUp(element, end, decimals = 0, suffix = '') {
  const start = performance.now();
  (function step(now) {
    const progress = Math.min(1, (now - start) / 900);
    element.textContent = (end * progress).toFixed(decimals) + suffix;
    if (progress < 1) requestAnimationFrame(step);
  })(start);
}
