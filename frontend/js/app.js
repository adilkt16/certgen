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
  const fontSelect = document.getElementById('font-select');
  if(fontSelect){
    fontSelect.addEventListener('change', (e)=>{
      state.fontName = e.target.value;
      const nameTag = document.getElementById('name-tag');
      if(nameTag) nameTag.style.fontFamily = e.target.value;
      renderPreview();
    });
  }

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

  // Font card clicks: keep select for compatibility but provide card UI
  document.querySelectorAll('.font-card').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const f = btn.getAttribute('data-font');
      state.fontName = f;
      const sel = document.getElementById('font-select'); if(sel) sel.value = f;
      // visual active
      document.querySelectorAll('.font-card').forEach(c=>c.classList.remove('active'));
      btn.classList.add('active');
      const nt = document.getElementById('name-tag'); if(nt) nt.style.fontFamily = f;
      renderPreview();
    });
  });

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
