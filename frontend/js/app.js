import { renderPreview, handleGenerate } from './generator.js';
import './uploader.js';
import './placer.js';

const API_BASE = (() => {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
    return 'http://localhost:8000';
  }
  return 'https://your-backend.railway.app';
})();
// Replace the production URL above with your Railway backend URL

const state = {
  templateFile: null,
  templateWidth: 0,
  templateHeight: 0,
  xPct: 0.50,
  yPct: 0.58,
  spreadsheetFile: null,
  columns: [],
  nameColumn: "",
  totalNames: 0,
  fontName: "cinzel_bold",
  fontSize: 64,
  fontColorHex: "#C9A84C",
  outputFormat: "both",
  previewName: "Participant Name",
};

window.state = state;
window.API_BASE = API_BASE;
window.renderPreview = renderPreview;
window.handleGenerate = handleGenerate;

function fontLabelFromId(fontId){
  if(!fontId) return '';
  return fontId
    .split('_')
    .map(part => part ? part[0].toUpperCase() + part.slice(1) : part)
    .join(' ');
}

function normalizeFontEntry(entry){
  if(typeof entry === 'string'){
    return { id: entry, label: fontLabelFromId(entry), weight: 400, style: 'normal' };
  }
  if(!entry || !entry.id) return null;
  return {
    id: entry.id,
    label: entry.label || fontLabelFromId(entry.id),
    weight: entry.weight || 400,
    style: entry.style || 'normal'
  };
}

async function fetchFontManifest(){
  try{
    const res = await fetch(API_BASE + '/api/fonts');
    if(!res.ok) return [];
    const json = await res.json();
    const list = Array.isArray(json.fonts) ? json.fonts : [];
    return list.map(normalizeFontEntry).filter(Boolean);
  }catch(e){
    return [];
  }
}

function applyFontToNameTag(){
  const nameTag = document.getElementById('name-tag');
  if(nameTag && state.fontName){
    nameTag.style.fontFamily = `"${state.fontName}", serif`;
  }
}

function setActiveFontCard(fontId){
  document.querySelectorAll('.font-card').forEach(c=>{
    if(c.getAttribute('data-font') === fontId){
      c.classList.add('active');
    } else {
      c.classList.remove('active');
    }
  });
}

function setFontName(fontId){
  if(!fontId) return;
  state.fontName = fontId;
  setActiveFontCard(fontId);
  applyFontToNameTag();
  renderPreview();
}

function buildFontControls(fonts){
  const cardsWrap = document.getElementById('font-cards');
  if(!cardsWrap) return;

  cardsWrap.innerHTML = '';
  fonts.forEach(font => {
    const btn = document.createElement('button');
    btn.className = 'font-card';
    btn.setAttribute('data-font', font.id);
    btn.textContent = font.label;
    btn.style.fontFamily = `"${font.id}", serif`;
    if(font.weight) btn.style.fontWeight = String(font.weight);
    btn.addEventListener('click', ()=> setFontName(font.id));
    cardsWrap.appendChild(btn);
  });

  const exists = fonts.some(f => f.id === state.fontName);
  if(!exists && fonts.length > 0){
    state.fontName = fonts[0].id;
  }
  if(state.fontName){
    setActiveFontCard(state.fontName);
  }
  applyFontToNameTag();
}

async function loadFontFaces(fonts){
  const loads = fonts.map(font => {
    const url = API_BASE + '/api/fonts/' + encodeURIComponent(font.id);
    const face = new FontFace(font.id, `url(${url})`, {
      weight: String(font.weight || 'normal'),
      style: font.style || 'normal'
    });
    return face.load().then(loaded => { document.fonts.add(loaded); }).catch(()=>{});
  });
  await Promise.all(loads);
}

async function initFonts(){
  const fonts = await fetchFontManifest();
  if(!fonts.length){
    applyFontToNameTag();
    return;
  }
  buildFontControls(fonts);
  await loadFontFaces(fonts);
  applyFontToNameTag();
  renderPreview();
}

function goToStep(n){
  for(let i=1;i<=5;i++){
    const s = document.getElementById(`step-${i}`);
    if(s) s.style.display = (i===n)?'':'none';
    const marker = document.querySelectorAll('#step-indicator .marker')[i-1];
    if(marker){
      if(i<=n) marker.classList.add('active'); else marker.classList.remove('active');
    }
  }
}

document.addEventListener('DOMContentLoaded', ()=>{
  initFonts();
  const on = (id, eventName, handler) => {
    const element = document.getElementById(id);
    if(element){
      element.addEventListener(eventName, handler);
    }
  };

  goToStep(1);

  // Proceed buttons
  on('to-step-2', 'click', ()=>{
    if(!state.templateFile){ alert('Please upload a template first'); return; }
    goToStep(2);
  });
  on('to-step-3', 'click', ()=>{
    goToStep(3);
  });
  on('to-step-4', 'click', ()=>{
    if(!state.nameColumn || state.totalNames<=0){ alert('Please load names and select a column'); return; }
    goToStep(4);
  });
  on('to-step-5', 'click', ()=>{
    goToStep(5);
  });

  // Style controls
  const fontSlider = document.getElementById('font-size-slider');
  const fontValue = document.getElementById('font-size-value');
  if(fontSlider){
    fontSlider.addEventListener('input', (e)=>{
      state.fontSize = parseInt(e.target.value,10);
      if(fontValue) fontValue.textContent = e.target.value;
      const nameTag = document.getElementById('name-tag');
      if(nameTag) nameTag.style.fontSize = state.fontSize + 'px';
      renderPreview();
    });
  }

  const colorPicker = document.getElementById('font-color-picker');
  if(colorPicker){
    colorPicker.addEventListener('input', (e)=>{
      state.fontColorHex = e.target.value;
      const nameTag = document.getElementById('name-tag');
      if(nameTag) nameTag.style.color = state.fontColorHex;
      renderPreview();
    });
  }

  document.querySelectorAll('input[name="output-format"]').forEach(r=>{
    r.addEventListener('change', (e)=>{ state.outputFormat = e.target.value; });
  });

  // Generate button
  on('generate-btn', 'click', ()=>{
    handleGenerate();
  });

  // Start new batch
  on('new-batch', 'click', ()=>{ location.reload(); });

  // Sidebar step navigation (wire visual sidebar to goToStep)
  document.querySelectorAll('.side-item').forEach((btn, idx)=>{
    btn.addEventListener('click', ()=>{ goToStep(idx+1);
      // update active class
      document.querySelectorAll('.side-item').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Text toolbar bindings
  const nameTag = document.getElementById('name-tag');
  const toolbarSize = document.getElementById('toolbar-size');
  on('toolbar-bold', 'click', ()=>{
    state.bold = !state.bold;
    if(nameTag) nameTag.style.fontWeight = state.bold ? '700' : '400';
    renderPreview();
  });
  on('toolbar-italic', 'click', ()=>{
    state.italic = !state.italic;
    if(nameTag) nameTag.style.fontStyle = state.italic ? 'italic' : 'normal';
    renderPreview();
  });
  on('toolbar-increase', 'click', ()=>{
    state.fontSize = Math.min(200, state.fontSize + 2); toolbarSize.textContent = state.fontSize + 'pt';
    const slider = document.getElementById('font-size-slider'); if(slider) slider.value = state.fontSize;
    if(nameTag) nameTag.style.fontSize = state.fontSize + 'px';
    renderPreview();
  });
  on('toolbar-decrease', 'click', ()=>{
    state.fontSize = Math.max(6, state.fontSize - 2); toolbarSize.textContent = state.fontSize + 'pt';
    const slider = document.getElementById('font-size-slider'); if(slider) slider.value = state.fontSize;
    if(nameTag) nameTag.style.fontSize = state.fontSize + 'px';
    renderPreview();
  });
  on('toolbar-align-left', 'click', ()=>{ if(nameTag) nameTag.style.textAlign = 'left'; renderPreview(); });
  on('toolbar-align-center', 'click', ()=>{ if(nameTag) nameTag.style.textAlign = 'center'; renderPreview(); });
  on('toolbar-align-right', 'click', ()=>{ if(nameTag) nameTag.style.textAlign = 'right'; renderPreview(); });

  // Font cards are built dynamically in initFonts()

  // Color swatches
  document.querySelectorAll('.color-swatch').forEach(s=>{
    s.addEventListener('click', ()=>{
      const c = s.getAttribute('data-color');
      const cp = document.getElementById('font-color-picker'); if(cp) cp.value = c;
      // trigger input handler
      const ev = new Event('input', { bubbles: true }); if(cp) cp.dispatchEvent(ev);
    });
  });

  // Preview zoom / fullscreen
  const modal = document.getElementById('preview-modal');
  const modalCanvas = document.getElementById('modal-canvas');
  const previewCanvas = document.getElementById('preview-canvas');
  on('preview-zoom', 'click', ()=>{
    if(!modal || !modalCanvas || !previewCanvas) return;
    // copy pixels
    modal.classList.add('active'); modal.setAttribute('aria-hidden','false');
    modalCanvas.width = previewCanvas.width * 2;
    modalCanvas.height = previewCanvas.height * 2;
    const mctx = modalCanvas.getContext('2d');
    mctx.clearRect(0,0,modalCanvas.width, modalCanvas.height);
    mctx.drawImage(previewCanvas, 0, 0, modalCanvas.width, modalCanvas.height);
  });
  on('modal-close', 'click', ()=>{ if(modal){ modal.classList.remove('active'); modal.setAttribute('aria-hidden','true'); } });

  on('preview-fullscreen', 'click', async ()=>{
    const el = document.getElementById('live-preview');
    if(el.requestFullscreen){ await el.requestFullscreen(); }
  });

});

export { API_BASE, state, goToStep };
