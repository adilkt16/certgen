// generator.js

function renderPreview(){
  const canvas = document.getElementById('preview-canvas');
  if(!window.state.templateFile) return;
  const previewName = window.state.previewName || 'Participant Name';
  const img = new Image();
  img.src = URL.createObjectURL(window.state.templateFile);
  img.onload = ()=>{
    canvas.width = 400;
    const templateWidth = Math.max(1, window.state.templateWidth || img.naturalWidth || 1);
    const templateHeight = Math.max(1, window.state.templateHeight || img.naturalHeight || 1);
    canvas.height = Math.round(400 * (templateHeight / templateWidth));
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    const x = window.state.xPct * canvas.width;
    const y = window.state.yPct * canvas.height;

    // Match backend sizing by scaling from real template dimensions,
    // then applying the same auto-shrink rule (max 80% width, min 12 on full image).
    const scale = canvas.width / templateWidth;
    let fullSize = parseInt(window.state.fontSize, 10) || 64;
    let previewSize = Math.max(1, Math.round(fullSize * scale));
    ctx.font = `${previewSize}px sans-serif`;
    let measured = ctx.measureText(previewName).width;
    while(measured > canvas.width * 0.80){
      fullSize -= 2;
      if(fullSize < 12) break;
      previewSize = Math.max(1, Math.round(fullSize * scale));
      ctx.font = `${previewSize}px sans-serif`;
      measured = ctx.measureText(previewName).width;
    }

    ctx.fillStyle = window.state.fontColorHex;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(previewName, x, y);
  };
}

let progressInterval = null;

async function handleGenerate(){
  if(!window.state.templateFile){ alert('Please upload a template'); return; }
  if(!window.state.spreadsheetFile){ alert('Please upload a spreadsheet'); return; }
  if(!window.state.nameColumn){ alert('Please select a name column'); return; }

  const progressWrap = document.getElementById('progress-bar-wrap');
  const inner = document.querySelector('.progress-inner');
  const text = document.querySelector('.progress-text');
  progressWrap.style.display = '';
  inner.style.width = '0%'; text.textContent = '0%';

  const estimatedSeconds = Math.max(2, window.state.totalNames * 0.3);
  let pct = 0;
  progressInterval = setInterval(()=>{
    pct = Math.min(90, pct + Math.random()*5);
    inner.style.width = pct + '%'; text.textContent = Math.round(pct) + '%';
  }, 200);

  const fd = new FormData();
  fd.append('template_file', window.state.templateFile);
  fd.append('spreadsheet_file', window.state.spreadsheetFile);
  fd.append('name_column', window.state.nameColumn);
  fd.append('x_pct', window.state.xPct);
  fd.append('y_pct', window.state.yPct);
  fd.append('font_name', window.state.fontName);
  fd.append('font_size', window.state.fontSize);
  fd.append('font_color_hex', window.state.fontColorHex);
  fd.append('output_format', window.state.outputFormat);

  try{
    const res = await fetch(window.API_BASE + '/api/generate', { method:'POST', body: fd });
    clearInterval(progressInterval);
    inner.style.width = '100%'; text.textContent = '100%';
    if(res.ok){
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const resultArea = document.getElementById('result-area');
      resultArea.style.display = '';
      const downloadBtn = document.getElementById('download-zip');
      downloadBtn.onclick = ()=>{ const a = document.createElement('a'); a.href = url; a.download = 'certificates.zip'; document.body.appendChild(a); a.click(); a.remove(); };
      const success = resultArea.querySelector('.success');
      success.textContent = `${window.state.totalNames} certificates generated`;
    } else {
      const err = await res.json().catch(()=>({error:'Unknown error'}));
      alert(err.error || 'Generation failed');
      progressWrap.style.display = 'none';
    }
  }catch(e){
    clearInterval(progressInterval);
    alert('Generation request failed');
    progressWrap.style.display = 'none';
  }
}

export { renderPreview, handleGenerate };
