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
  goToStep(1);

  // Proceed buttons
  document.getElementById('to-step-2').addEventListener('click', ()=>{
    if(!state.templateFile){ alert('Please upload a template first'); return; }
    goToStep(2);
  });
  document.getElementById('to-step-3').addEventListener('click', ()=>{
    goToStep(3);
  });
  document.getElementById('to-step-4').addEventListener('click', ()=>{
    if(!state.nameColumn || state.totalNames<=0){ alert('Please load names and select a column'); return; }
    goToStep(4);
  });
  document.getElementById('to-step-5').addEventListener('click', ()=>{
    goToStep(5);
  });

  // Style controls
  const fontSelect = document.getElementById('font-select');
  fontSelect.addEventListener('change', (e)=>{
    state.fontName = e.target.value;
    const nameTag = document.getElementById('name-tag');
    nameTag.style.fontFamily = e.target.value;
    renderPreview();
  });

  const fontSlider = document.getElementById('font-size-slider');
  const fontValue = document.getElementById('font-size-value');
  fontSlider.addEventListener('input', (e)=>{
    state.fontSize = parseInt(e.target.value,10);
    fontValue.textContent = e.target.value;
    const nameTag = document.getElementById('name-tag');
    nameTag.style.fontSize = state.fontSize + 'px';
    renderPreview();
  });

  const colorPicker = document.getElementById('font-color-picker');
  colorPicker.addEventListener('input', (e)=>{
    state.fontColorHex = e.target.value;
    const nameTag = document.getElementById('name-tag');
    nameTag.style.color = state.fontColorHex;
    renderPreview();
  });

  document.querySelectorAll('input[name="output-format"]').forEach(r=>{
    r.addEventListener('change', (e)=>{ state.outputFormat = e.target.value; });
  });

  // Generate button
  document.getElementById('generate-btn').addEventListener('click', ()=>{
    handleGenerate();
  });

  // Start new batch
  document.getElementById('new-batch').addEventListener('click', ()=>{ location.reload(); });

});

export { API_BASE, state, goToStep };
