// placer.js
const canvas = document.getElementById('preview-canvas');

let isPlacing = false;

function isSnapEnabled(){
  const snapEl = document.getElementById('snap-toggle');
  return snapEl ? snapEl.checked : false;
}

function updatePlacement(clientX, clientY){
  if(!canvas) return;
  if(!window.state.templateFile) return;

  const rect = canvas.getBoundingClientRect();
  if(rect.width <= 0 || rect.height <= 0) return;

  let x = clientX - rect.left;
  let y = clientY - rect.top;

  x = Math.max(0, Math.min(x, rect.width));
  y = Math.max(0, Math.min(y, rect.height));

  if(isSnapEnabled()){
    x = Math.round(x / 10) * 10;
    y = Math.round(y / 10) * 10;
  }

  window.state.xPct = Math.round((x / rect.width) * 1000) / 1000;
  window.state.yPct = Math.round((y / rect.height) * 1000) / 1000;

  const pd = document.getElementById('position-display');
  if(pd){
    pd.textContent = `X: ${(window.state.xPct*100).toFixed(1)}%  Y: ${(window.state.yPct*100).toFixed(1)}%`;
  }

  const cx = document.getElementById('coord-x');
  const cy = document.getElementById('coord-y');
  const templateW = window.state.templateWidth || rect.width;
  const templateH = window.state.templateHeight || rect.height;
  if(cx) cx.textContent = `${Math.round(window.state.xPct * templateW)} px`;
  if(cy) cy.textContent = `${Math.round(window.state.yPct * templateH)} px`;

  if(window.renderPreview) window.renderPreview();
}

if(canvas){
  canvas.addEventListener('mousedown', (e)=>{
    isPlacing = true;
    updatePlacement(e.clientX, e.clientY);
  });

  document.addEventListener('mousemove', (e)=>{
    if(!isPlacing) return;
    updatePlacement(e.clientX, e.clientY);
  });

  document.addEventListener('mouseup', ()=>{
    isPlacing = false;
  });

  canvas.addEventListener('touchstart', (e)=>{
    if(!e.touches.length) return;
    isPlacing = true;
    updatePlacement(e.touches[0].clientX, e.touches[0].clientY);
    e.preventDefault();
  }, { passive: false });

  document.addEventListener('touchmove', (e)=>{
    if(!isPlacing || !e.touches.length) return;
    updatePlacement(e.touches[0].clientX, e.touches[0].clientY);
    e.preventDefault();
  }, { passive: false });

  document.addEventListener('touchend', ()=>{
    isPlacing = false;
  });
}

export {};
