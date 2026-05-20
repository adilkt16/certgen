// uploader.js
// Uses window.state and window.API_BASE

const templateZone = document.getElementById('template-drop-zone');
const templateInput = document.getElementById('template-input');
const templateInfo = document.getElementById('template-info');
const templateWarning = document.getElementById('template-warning');

const spreadsheetZone = document.getElementById('spreadsheet-drop-zone');
const spreadsheetInput = document.getElementById('spreadsheet-input');
const spreadsheetInfo = document.getElementById('spreadsheet-info');
const columnSelect = document.getElementById('column-select');
const previewTable = document.getElementById('preview-table');
const rowCount = document.getElementById('row-count');

function showError(msg){
  // Prefer in-page upload warning element when available for better UX
  try{
    const warnEl = document.getElementById('spreadsheet-warning');
    if(warnEl){ warnEl.style.display=''; warnEl.textContent = msg; return; }
  }catch(e){}
  alert(msg);
}

function showTemplateError(msg){
  try{
    if(templateWarning){
      templateWarning.style.display = '';
      templateWarning.textContent = msg;
      return;
    }
  }catch(e){}
  showError(msg);
}

function clearTemplateError(){
  try{
    if(templateWarning){
      templateWarning.style.display = 'none';
      templateWarning.textContent = '';
    }
  }catch(e){}
}

// Template handlers
function handleTemplateFile(file){
  if(!file) return;
  clearTemplateError();
  if(file.type !== 'image/jpeg' && file.type !== 'image/png'){
    showTemplateError('Only JPEG or PNG files are allowed'); return;
  }
  try{
    const maxTpl = window.MAX_TEMPLATE_SIZE_MB || 10;
    if(file.size > maxTpl * 1024 * 1024){ showTemplateError(`Template is above the limit. Please upload a file under ${maxTpl}MB.`); return; }
  }catch(e){}
  window.state.templateFile = file;
  const url = URL.createObjectURL(file);
  const img = new Image();
  img.onload = ()=>{
    window.state.templateWidth = img.naturalWidth;
    window.state.templateHeight = img.naturalHeight;
    templateInfo.style.display = '';
    templateInfo.textContent = `${file.name} — ${img.naturalWidth}×${img.naturalHeight} — ${(file.size/1024).toFixed(1)} KB`;
    if (window.renderPreview) window.renderPreview();
  };
  img.src = url;
  // Replace upload zone content with thumbnail
  // Clear children safely instead of using HTML injection APIs
  while (templateZone.firstChild) templateZone.removeChild(templateZone.firstChild);
  const thumb = document.createElement('img');
  thumb.src = url;
  thumb.style.maxWidth = '160px';
  thumb.style.maxHeight = '120px';
  templateZone.appendChild(thumb);
}

templateZone.addEventListener('click', ()=> templateInput.click());
templateInput.addEventListener('change', (e)=> handleTemplateFile(e.target.files[0]));

templateZone.addEventListener('dragover', (e)=>{ e.preventDefault(); templateZone.classList.add('dragover'); });
templateZone.addEventListener('dragleave', ()=> templateZone.classList.remove('dragover'));
templateZone.addEventListener('drop', (e)=>{ e.preventDefault(); templateZone.classList.remove('dragover'); const f = e.dataTransfer.files[0]; handleTemplateFile(f); });

// Spreadsheet handlers
function handleSpreadsheetFile(file){
  if(!file) return;
  const name = (file.name || '').toLowerCase();
  if(!(name.endsWith('.xlsx') || name.endsWith('.csv'))){ showError('Only .xlsx and .csv files are allowed'); return; }
  try{
    const maxSp = window.MAX_SPREADSHEET_SIZE_MB || 5;
    if(file.size > maxSp * 1024 * 1024){ showError(`Spreadsheet must be under ${maxSp}MB`); return; }
  }catch(e){}
  window.state.spreadsheetFile = file;

  const fd = new FormData();
  fd.append('spreadsheet_file', file);
  const spHeaders = {};
  if (window.API_KEY) spHeaders['X-API-Key'] = window.API_KEY;
  fetch(window.API_BASE + '/api/parse-spreadsheet', { method: 'POST', headers: spHeaders, body: fd })
    .then(async res => {
      if(!res.ok){
        // try to surface a helpful server-provided message
        let body = null;
        try{ body = await res.json(); }catch(e){ /* non-json response */ }
        if(body && body.code === 'SPREADSHEET_TOO_LARGE'){
          showError(`Spreadsheet is too large. Please keep files under the limit (${body.error || 'see server settings'}).`);
          throw new Error('SPREADSHEET_TOO_LARGE');
        }
        if(body && body.code === 'PARSE_ERROR'){
          showError(body.error || 'Could not parse spreadsheet. Please check the file format.');
          throw new Error('PARSE_ERROR');
        }
        // fallback to generic
        throw new Error('Could not parse spreadsheet');
      }
      return res.json();
    })
    .then(json => {
      window.state.columns = json.columns || [];
      window.state.totalNames = json.total || 0;
      // Client-side quick check: prefer configured `window.MAX_BATCH_SIZE`, fallback to 77
      const maxBatch = (typeof window.MAX_BATCH_SIZE === 'number' && window.MAX_BATCH_SIZE) ? window.MAX_BATCH_SIZE : 77;
      if (window.state.totalNames > maxBatch) { showError(`Batch limit is ${maxBatch}. You uploaded ${window.state.totalNames} names.`); return; }
      // update preview-count badge if present
      try{
        const previewCountBadge = document.querySelector('.preview-header .preview-badge') || document.getElementById('preview-count-badge');
        const previewRows = (json.preview || []).length;
        if(previewCountBadge) previewCountBadge.textContent = `Showing first ${previewRows} rows`;
      }catch(e){}
      // populate select (clear options safely)
      if(columnSelect){ columnSelect.options.length = 0; }
      json.columns.forEach(c=>{ const opt = document.createElement('option'); opt.value = c; opt.textContent = c; columnSelect.appendChild(opt); });
      columnSelect.addEventListener('change', ()=>{ window.state.nameColumn = columnSelect.value; });
      if(json.columns.length>0){ window.state.nameColumn = json.columns[0]; columnSelect.value = json.columns[0]; }
      // preview table (clear children safely)
      while (previewTable.firstChild) previewTable.removeChild(previewTable.firstChild);
      const rows = json.preview || [];
      if(rows.length>0){
        const thead = document.createElement('thead');
        const tr = document.createElement('tr');
        Object.keys(rows[0]).forEach(k=>{ const th = document.createElement('th'); th.textContent = k; tr.appendChild(th); });
        thead.appendChild(tr); previewTable.appendChild(thead);
        const tbody = document.createElement('tbody');
        rows.forEach(r=>{ const tr2 = document.createElement('tr'); Object.values(r).forEach(v=>{ const td = document.createElement('td'); td.textContent = v===null?'':v; tr2.appendChild(td); }); tbody.appendChild(tr2); });
        previewTable.appendChild(tbody);
      }
      rowCount.textContent = `${window.state.totalNames} names loaded`;
      spreadsheetInfo.style.display = '';
      // show upload success callout
      try{
        const successEl = document.getElementById('upload-success');
        if(successEl){ successEl.style.display=''; successEl.textContent = `Upload Success — ${window.state.totalNames} names found`; }
      }catch(e){}
      // quick preview checks: empty values in first column or duplicates in preview
      try{
        const warnEl = document.getElementById('preview-warning');
        const rows = json.preview || [];
        if(warnEl){
          const firstCol = rows.length>0?Object.keys(rows[0])[0]:null;
          let emptyCount = 0;
          const seen = new Set(); let dupCount = 0;
          rows.forEach(r=>{
            const v = firstCol? (r[firstCol]||'').toString().trim() : '';
            if(!v) emptyCount++;
            if(v){ if(seen.has(v)) dupCount++; else seen.add(v); }
          });
          if(emptyCount>0 || dupCount>0){
            warnEl.style.display='';
            const parts = [];
            if(emptyCount>0) parts.push(`${emptyCount} empty rows in preview`);
            if(dupCount>0) parts.push(`${dupCount} duplicate names in preview`);
            warnEl.textContent = parts.join(' · ');
          } else { warnEl.style.display='none'; }
        }
      }catch(e){}
      // set previewName for renderPreview
      if(rows.length>0){ const firstRow = rows[0]; const firstCol = Object.keys(firstRow)[0]; window.state.previewName = firstRow[firstCol] || window.state.previewName; }
      if (window.renderPreview) window.renderPreview();
    })
    .catch(err => {
      // ignore thrown internal sentinel errors (message already shown)
      if(err && (err.message === 'SPREADSHEET_TOO_LARGE' || err.message === 'PARSE_ERROR')) return;
      showError('Could not read spreadsheet. Please check the file.');
    });
}

spreadsheetZone.addEventListener('click', ()=> spreadsheetInput.click());
spreadsheetInput.addEventListener('change', (e)=> handleSpreadsheetFile(e.target.files[0]));
spreadsheetZone.addEventListener('dragover', (e)=>{ e.preventDefault(); spreadsheetZone.classList.add('dragover'); });
spreadsheetZone.addEventListener('dragleave', ()=> spreadsheetZone.classList.remove('dragover'));
spreadsheetZone.addEventListener('drop', (e)=>{ e.preventDefault(); spreadsheetZone.classList.remove('dragover'); const f = e.dataTransfer.files[0]; handleSpreadsheetFile(f); });

export { handleTemplateFile, handleSpreadsheetFile };
