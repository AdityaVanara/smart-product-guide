const $=s=>document.querySelector(s),mk=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const store={get(k,d){try{const v=localStorage.getItem(k);return v?JSON.parse(v):d}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v));return true}catch(e){return false}}};
const inr=n=>'₹'+n.toLocaleString('en-IN');

/* survey bars + counters */
document.querySelectorAll('[data-bars]').forEach(b=>{JSON.parse(b.dataset.bars).forEach(([l,v])=>{const r=mk('div','bar');r.append(mk('span','',l));const t=mk('div','track'),f=mk('div','fill'+(b.hasAttribute('data-y')?' y':''));f.dataset.w=v;t.append(f);r.append(t,mk('span','',v+'%'));b.append(r)})});
const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const el=e.target;io.unobserve(el);
if(el.dataset.w)el.style.width=el.dataset.w+'%';
if(el.dataset.n){const end=+el.dataset.n,t0=performance.now();(function s(t){const p=Math.min(1,(t-t0)/1100);el.textContent=(end*p).toFixed(1)+'%';if(p<1)requestAnimationFrame(s)})(t0)}}),{threshold:.4});
document.querySelectorAll('.fill,[data-n]').forEach(e=>io.observe(e));

/* products */
const P=[
{n:'Nova X1',a:22499,f:22999,m:23200,r:3.9,rv:1820,ram:'6 GB',st:'128 GB',cam:'48 MP',s:3.8},
{n:'Pulse 5G',a:23999,f:24499,m:23500,r:4.6,rv:3410,ram:'8 GB',st:'128 GB',cam:'50 MP',s:4.7},
{n:'Orbit Pro',a:24999,f:24499,m:25800,r:4.4,rv:2650,ram:'8 GB',st:'256 GB',cam:'64 MP',s:4.4},
{n:'Zen Lite',a:14999,f:15499,m:14200,r:4.0,rv:5120,ram:'4 GB',st:'64 GB',cam:'13 MP',s:4.1},
{n:'Spark Max',a:31999,f:30999,m:32500,r:4.5,rv:1980,ram:'12 GB',st:'256 GB',cam:'108 MP',s:4.5},
{n:'Aero Neo',a:18999,f:19499,m:18500,r:4.2,rv:2210,ram:'6 GB',st:'128 GB',cam:'50 MP',s:3.9}];
P.forEach(p=>{p.low=Math.min(p.a,p.f,p.m);p.best=Object.entries({Amazon:p.a,Flipkart:p.f,Meesho:p.m}).sort((x,y)=>x[1]-y[1])[0][0];p.sc=p.r*.6+p.s*.4});
let sel=store.get('tp_short',[]).filter(n=>P.some(p=>p.n===n)).slice(0,3);
const bud=$('#bud');
function showTool(){
 $('#budv').textContent=inr(+bud.value);
 const q=$('#q').value.toLowerCase(),sk=$('#sort').value;
 let L=P.filter(p=>p.low<=+bud.value&&p.n.toLowerCase().includes(q));
 L.sort((a,b)=>sk==='p'?a.low-b.low:sk==='r'?b.r-a.r:b.sc-a.sc);
 const pool=P.filter(p=>p.low<=+bud.value);
 const lowest=pool.length&&pool.reduce((a,b)=>a.low<b.low?a:b),top=pool.length&&pool.reduce((a,b)=>a.r>b.r?a:b),match=pool.length&&pool.reduce((a,b)=>a.sc>b.sc?a:b);
 const box=$('#plist');box.textContent='';
 if(!L.length)box.append(mk('div','empty','No phones match. Raise the budget or clear the search.'));
 L.forEach(p=>{const c=mk('div','prod'+(sel.includes(p.n)?' sel':''));
  const tg=mk('div','tags');if(p===lowest)tg.append(mk('span','tag','Lowest price'));if(p===match)tg.append(mk('span','tag g','Best match'));if(p===top)tg.append(mk('span','tag b','Top rated'));
  c.append(tg,mk('h3','',p.n),mk('div','pr',inr(p.low)),mk('small','','Cheapest on '+p.best),mk('small','','★ '+p.r+' · '+p.rv.toLocaleString('en-IN')+' reviews'),mk('small','',p.ram+' · '+p.st+' · '+p.cam));
  const b=mk('button','btn'+(sel.includes(p.n)?' alt':''),sel.includes(p.n)?'Remove':'Compare');
  b.onclick=()=>{if(sel.includes(p.n))sel=sel.filter(x=>x!==p.n);else if(sel.length<3)sel.push(p.n);else{$('#shortmsg').textContent='You can compare up to 3 phones.';return}
   store.set('tp_short',sel);showTool()};
  c.append(b);box.append(c)});
 $('#shortmsg').textContent=sel.length?sel.length+' of 3 selected':'Pick phones to compare.';
 const cmp=$('#cmp');cmp.hidden=sel.length<2;cmp.textContent='';
 if(sel.length>=2){const S=sel.map(n=>P.find(p=>p.n===n)),t=mk('table'),h=mk('tr');h.append(mk('th','','Compare'));S.forEach(p=>h.append(mk('th','',p.n)));t.append(h);
  const rows=[['Amazon',p=>inr(p.a),p=>p.a,1],['Flipkart',p=>inr(p.f),p=>p.f,1],['Meesho',p=>inr(p.m),p=>p.m,1],['Review rating',p=>p.r+' / 5',p=>p.r,-1],['Seller reliability',p=>p.s+' / 5',p=>p.s,-1],['Memory',p=>p.ram+' RAM',p=>parseInt(p.ram),-1],['Storage',p=>p.st,p=>parseInt(p.st),-1],['Camera',p=>p.cam,p=>parseInt(p.cam),-1]];
  rows.forEach(([l,f,v,d])=>{const r=mk('tr');r.append(mk('th','',l));const vals=S.map(v),best=d>0?Math.min(...vals):Math.max(...vals);S.forEach(p=>{const c=mk('td',v(p)===best?'win':'',f(p));r.append(c)});t.append(r)});
  cmp.append(t,mk('small','','Green marks the best value in each row. Sample data for the prototype.'))}
}
[bud,$('#q'),$('#sort')].forEach(e=>e.addEventListener('input',showTool));
$('#clr').onclick=()=>{sel=[];store.set('tp_short',sel);showTool()};
showTool();

/* feedback database */
let rate=0;const st=$('#stars');
for(let i=1;i<=5;i++){const b=mk('button','',' ★');b.textContent='★';b.setAttribute('role','radio');b.setAttribute('aria-label',i+' star');b.onclick=()=>{rate=i;[...st.children].forEach((c,j)=>c.classList.toggle('on',j<i))};st.append(b)}
function showFb(){const d=store.get('tp_feedback',[]),box=$('#flist');box.textContent='';$('#cnt').textContent='Saved feedback ('+d.length+')';
 if(!d.length){box.append(mk('div','empty','Nothing saved yet. Your entries will appear here.'));return}
 d.slice().reverse().forEach(e=>{const c=mk('div','');c.style.cssText='border:1px solid var(--line);border-radius:12px;padding:12px 14px';
  c.append(mk('b','',(e.name||'Anonymous')+'  ·  '+'★'.repeat(e.rate)+'☆'.repeat(5-e.rate)),mk('div','',e.comment||'(no comment)'),mk('small','','Likes: '+e.feature+' · '+new Date(e.at).toLocaleString('en-IN')));
  const x=mk('button','link','Delete');x.style.display='block';x.onclick=()=>{store.set('tp_feedback',store.get('tp_feedback',[]).filter(z=>z.id!==e.id));showFb()};c.append(x);box.append(c)})}
$('#save').onclick=()=>{const m=$('#fmsg');if(!rate){m.style.color='#d33';m.textContent='Choose a star rating first.';return}
 const d=store.get('tp_feedback',[]);d.push({id:Date.now(),name:$('#fn').value.trim(),rate,feature:$('#ff').value,comment:$('#fc').value.trim(),at:new Date().toISOString()});
 if(store.set('tp_feedback',d)){m.style.color='';m.textContent='Saved in your browser. Thank you!';$('#fn').value=$('#fc').value='';rate=0;[...st.children].forEach(c=>c.classList.remove('on'));showFb()}else{m.style.color='#d33';m.textContent='Could not save. Browser storage is blocked.'}};
$('#all').onclick=()=>{if(confirm('Delete all saved feedback?')){store.set('tp_feedback',[]);showFb()}};
$('#exp').onclick=()=>{const d=store.get('tp_feedback',[]);if(!d.length)return;const q=s=>'"'+String(s).replace(/"/g,'""')+'"';
 const csv=['name,rating,feature,comment,date',...d.map(e=>[e.name,e.rate,e.feature,e.comment,e.at].map(q).join(','))].join('\n');
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='feedback.csv';a.click()};
showFb();
