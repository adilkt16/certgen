// uploader.js
// Uses window.state and window.API_BASE

const templateZone = document.getElementById('template-drop-zone');
const templateInput = document.getElementById('template-input');
const templatePreview = document.getElementById('template-preview');
const templateInfo = document.getElementById('template-info');

const spreadsheetZone = document.getElementById('spreadsheet-drop-zone');
const spreadsheetInput = document.getElementById('spreadsheet-input');
const spreadsheetInfo = document.getElementById('spreadsheet-info');
const columnSelect = document.getElementById('column-select');
const previewTable = document.getElementById('preview-table');
const rowCount = document.getElementById('row-count');

function showError(msg){ alert(msg); }

// Template handlers
function handleTemplateFile(file){
  if(!file) return;
  if(file.type !== 'image/jpeg' && file.type !== 'image/png'){
    showError('Only JPEG or PNG files are allowed'); return;
  }
  if(file.size > 10 * 1024 * 1024){ showError('File must be under 10MB'); return; }
  window.state.templateFile = file;
  const url = URL.createObjectURL(file);
  templatePreview.src = url;
  // Update a right-hand preview image and filename if the redesigned UI includes them
  try{
    const rightPreview = document.getElementById('right-preview-image');
    const rightFilename = document.getElementById('right-preview-filename');
    if(rightPreview) rightPreview.src = url;
    if(rightFilename) rightFilename.textContent = file.name || rightFilename.textContent;
  }catch(e){ /* ignore if elements not present */ }

  templatePreview.onload = ()=>{
    window.state.templateWidth = templatePreview.naturalWidth;
    window.state.templateHeight = templatePreview.naturalHeight;
    templateInfo.style.display = '';
    templateInfo.textContent = `${file.name} — ${templatePreview.naturalWidth}×${templatePreview.naturalHeight} — ${(file.size/1024).toFixed(1)} KB`;
    if (window.renderPreview) window.renderPreview();
  };
  // Replace upload zone content with thumbnail
  templateZone.innerHTML = '';
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
  window.state.spreadsheetFile = file;

  const fd = new FormData();
  fd.append('spreadsheet_file', file);
  fetch(window.API_BASE + '/api/parse-spreadsheet', { method:'POST', body: fd })
    .then(async res => {
      if(!res.ok){ throw new Error('Could not parse spreadsheet'); }
      return res.json();
    })
    .then(json => {
      window.state.columns = json.columns || [];
      window.state.totalNames = json.total || 0;
      if(window.state.totalNames > 200){ showError(`Batch limit is 200. You uploaded ${window.state.totalNames} names.`); return; }
      // update preview-count badge if present
      try{
        const previewCountBadge = document.querySelector('.preview-header .preview-badge') || document.getElementById('preview-count-badge');
        const previewRows = (json.preview || []).length;
        if(previewCountBadge) previewCountBadge.textContent = `Showing first ${previewRows} rows`;
      }catch(e){}
      // populate select
      columnSelect.innerHTML = '';
      json.columns.forEach(c=>{ const opt = document.createElement('option'); opt.value = c; opt.textContent = c; columnSelect.appendChild(opt); });
      columnSelect.addEventListener('change', ()=>{ window.state.nameColumn = columnSelect.value; });
      if(json.columns.length>0){ window.state.nameColumn = json.columns[0]; columnSelect.value = json.columns[0]; }
      // preview table
      previewTable.innerHTML = '';
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
        const warnEl = document.getElementById('upload-warning');
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
    .catch(err => { showError('Could not read spreadsheet. Please check the file.'); });
}

spreadsheetZone.addEventListener('click', ()=> spreadsheetInput.click());
spreadsheetInput.addEventListener('change', (e)=> handleSpreadsheetFile(e.target.files[0]));
spreadsheetZone.addEventListener('dragover', (e)=>{ e.preventDefault(); spreadsheetZone.classList.add('dragover'); });
spreadsheetZone.addEventListener('dragleave', ()=> spreadsheetZone.classList.remove('dragover'));
spreadsheetZone.addEventListener('drop', (e)=>{ e.preventDefault(); spreadsheetZone.classList.remove('dragover'); const f = e.dataTransfer.files[0]; handleSpreadsheetFile(f); });

export { handleTemplateFile, handleSpreadsheetFile };
