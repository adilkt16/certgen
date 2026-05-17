// placer.js
const nameTag = document.getElementById('name-tag');
const wrapper = document.getElementById('canvas-wrapper');

let isDragging = false;
let dragOffsetX = 0;
let dragOffsetY = 0;

function getElemPos(el){
  const rect = el.getBoundingClientRect();
  return {left: rect.left, top: rect.top};
}

nameTag.addEventListener('mousedown', (e)=>{
  isDragging = true;
  nameTag.style.cursor = 'grabbing';
  const pos = nameTag.getBoundingClientRect();
  dragOffsetX = e.clientX - pos.left;
  dragOffsetY = e.clientY - pos.top;
  e.preventDefault();
});

document.addEventListener('mousemove', (e)=>{
  if(!isDragging) return;
  const rect = wrapper.getBoundingClientRect();
  let newLeft = e.clientX - rect.left - dragOffsetX + (nameTag.offsetWidth/2);
  let newTop = e.clientY - rect.top - dragOffsetY + (nameTag.offsetHeight/2);
  // optional snap
  const snapEl = document.getElementById('snap-toggle');
  const snap = snapEl ? snapEl.checked : false;
  newLeft = Math.max(0, Math.min(newLeft, wrapper.offsetWidth));
  newTop = Math.max(0, Math.min(newTop, wrapper.offsetHeight));
  if(snap){ newLeft = Math.round(newLeft/10)*10; newTop = Math.round(newTop/10)*10; }
  nameTag.style.left = newLeft + 'px';
  nameTag.style.top = newTop + 'px';
  window.state.xPct = Math.round((newLeft / wrapper.offsetWidth) * 1000) / 1000;
  window.state.yPct = Math.round((newTop / wrapper.offsetHeight) * 1000) / 1000;
  const pd = document.getElementById('position-display');
  pd.textContent = `X: ${(window.state.xPct*100).toFixed(1)}%  Y: ${(window.state.yPct*100).toFixed(1)}%`;
  // update pixel readouts if present
  const cx = document.getElementById('coord-x');
  const cy = document.getElementById('coord-y');
  if(cx) cx.textContent = `${Math.round(newLeft)} px`;
  if(cy) cy.textContent = `${Math.round(newTop)} px`;
});

document.addEventListener('mouseup', (e)=>{
  isDragging = false; nameTag.style.cursor = 'grab';
});

// touch events
nameTag.addEventListener('touchstart', (e)=>{
  const t = e.touches[0];
  isDragging = true; nameTag.style.cursor = 'grabbing';
  const pos = nameTag.getBoundingClientRect();
  dragOffsetX = t.clientX - pos.left; dragOffsetY = t.clientY - pos.top; e.preventDefault();
});

document.addEventListener('touchmove', (e)=>{
  if(!isDragging) return; const t = e.touches[0];
  const rect = wrapper.getBoundingClientRect();
  let newLeft = t.clientX - rect.left - dragOffsetX + (nameTag.offsetWidth/2);
  let newTop = t.clientY - rect.top - dragOffsetY + (nameTag.offsetHeight/2);
  const snapEl = document.getElementById('snap-toggle');
  const snap = snapEl ? snapEl.checked : false;
  newLeft = Math.max(0, Math.min(newLeft, wrapper.offsetWidth));
  newTop = Math.max(0, Math.min(newTop, wrapper.offsetHeight));
  if(snap){ newLeft = Math.round(newLeft/10)*10; newTop = Math.round(newTop/10)*10; }
  nameTag.style.left = newLeft + 'px'; nameTag.style.top = newTop + 'px';
  window.state.xPct = Math.round((newLeft / wrapper.offsetWidth) * 1000) / 1000;
  window.state.yPct = Math.round((newTop / wrapper.offsetHeight) * 1000) / 1000;
  const pd = document.getElementById('position-display');
  pd.textContent = `X: ${(window.state.xPct*100).toFixed(1)}%  Y: ${(window.state.yPct*100).toFixed(1)}%`;
  const cx = document.getElementById('coord-x');
  const cy = document.getElementById('coord-y');
  if(cx) cx.textContent = `${Math.round(newLeft)} px`;
  if(cy) cy.textContent = `${Math.round(newTop)} px`;
  e.preventDefault();
});

document.addEventListener('touchend', (e)=>{ isDragging = false; nameTag.style.cursor = 'grab'; });

export {};
