// generator.js

function drawPreviewToCanvas(canvas, img, showGuides){
  if(!canvas) return;
  const previewName = window.state.previewName || 'Participant Name';
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
  const fontFamily = window.state.fontName ? `"${window.state.fontName}"` : 'sans-serif';
  ctx.font = `${previewSize}px ${fontFamily}, sans-serif`;
  let measured = ctx.measureText(previewName).width;
  while(measured > canvas.width * 0.80){
    fullSize -= 2;
    if(fullSize < 12) break;
    previewSize = Math.max(1, Math.round(fullSize * scale));
    ctx.font = `${previewSize}px ${fontFamily}, sans-serif`;
    measured = ctx.measureText(previewName).width;
  }

  const textAlign = window.state.textAlign || 'center';
  const isBold = !!window.state.bold;
  const isItalic = !!window.state.italic;
  const italicSkew = 0.2;
  const drawX = textAlign === 'left' ? x : (textAlign === 'right' ? x - measured : x - (measured / 2));

  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = window.state.fontColorHex;

  const strokeWidth = isBold ? Math.max(1, Math.round(previewSize / 24)) : 0;

  const drawText = (px, py)=>{
    if(strokeWidth > 0){
      ctx.lineWidth = strokeWidth;
      ctx.strokeStyle = window.state.fontColorHex;
      ctx.strokeText(previewName, px, py);
    }
    ctx.fillText(previewName, px, py);
  };

  if(isItalic){
    ctx.save();
    ctx.translate(drawX, y);
    ctx.transform(1, italicSkew, 0, 1, 0, 0);
    drawText(0, 0);
    ctx.restore();
  } else {
    drawText(drawX, y);
  }

  if(showGuides){
    const textCenterX = drawX + (measured / 2);
    const textCenterY = y;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const guideThreshold = 10;
    const nearX = Math.abs(textCenterX - centerX) <= guideThreshold;
    const nearY = Math.abs(textCenterY - centerY) <= guideThreshold;

    ctx.save();
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(201,168,76,0.18)';
    ctx.beginPath();
    ctx.moveTo(centerX, 0);
    ctx.lineTo(centerX, canvas.height);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(canvas.width, centerY);
    ctx.stroke();

    if(nearX){
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgba(201,168,76,0.85)';
      ctx.beginPath();
      ctx.moveTo(centerX, 0);
      ctx.lineTo(centerX, canvas.height);
      ctx.stroke();
    }
    if(nearY){
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgba(201,168,76,0.85)';
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(canvas.width, centerY);
      ctx.stroke();
    }
    ctx.restore();
  }
}

function renderPreview(){
  if(!window.state.templateFile) return;
  const canvases = [
    document.getElementById('preview-canvas'),
    document.getElementById('generate-preview-canvas')
  ].filter(Boolean);
  if(!canvases.length) return;
  const img = new Image();
  img.src = URL.createObjectURL(window.state.templateFile);
  img.onload = ()=>{
    canvases.forEach(canvas => drawPreviewToCanvas(canvas, img, canvas.id === 'preview-canvas'));
  };
}

let progressInterval = null;

async function handleGenerate(){
  if(!window.state.templateFile){ window.showAppError('Please upload a template'); return; }
  if(!window.state.spreadsheetFile){ window.showAppError('Please upload a spreadsheet'); return; }
  if(!window.state.nameColumn){ window.showAppError('Please select a name column'); return; }

  const progressWrap = document.getElementById('progress-bar-wrap');
  const inner = document.querySelector('.progress-inner');
  const text = document.querySelector('.progress-text');
  // show both compact progress and the larger hero
  const hero = document.getElementById('progress-hero');
  if(hero) hero.style.display = '';
  progressWrap.style.display = '';
  inner.style.width = '0%'; text.textContent = '0%';
  // big percent and files count
  const bigPercent = document.querySelector('.big-percent'); if(bigPercent) bigPercent.textContent = '0%';
  const filesCount = document.getElementById('files-count'); if(filesCount) filesCount.textContent = window.state.totalNames || 0;
  const etaEl = document.getElementById('eta'); if(etaEl) etaEl.textContent = 'Estimating…';

  const estimatedSeconds = Math.max(2, window.state.totalNames * 0.3);
  let pct = 0;
  const startTime = Date.now();
  progressInterval = setInterval(()=>{
    pct = Math.min(90, pct + Math.random()*5);
    inner.style.width = pct + '%'; text.textContent = Math.round(pct) + '%';
    if(document.querySelector('.big-percent')) document.querySelector('.big-percent').textContent = Math.round(pct) + '%';
    // naive ETA estimate: remaining percent / progress rate
    const etaEl2 = document.getElementById('eta');
    if(etaEl2){
      // approximate remaining seconds based on pct increments over time
      const elapsed = (Date.now() - startTime)/1000; // seconds
      const rate = Math.max(0.5, pct/Math.max(1, elapsed));
      const remain = Math.max(0, 100 - pct);
      const estSec = Math.round(remain / rate);
      etaEl2.textContent = estSec > 60 ? Math.round(estSec/60) + 'm' : estSec + 's';
    }
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
  fd.append('bold', window.state.bold ? 'true' : 'false');
  fd.append('italic', window.state.italic ? 'true' : 'false');
  fd.append('text_align', window.state.textAlign || 'center');

  try{
    const res = await fetch(window.API_BASE + '/api/generate', { method:'POST', body: fd });
    clearInterval(progressInterval);
    inner.style.width = '100%'; text.textContent = '100%';
    if(document.querySelector('.big-percent')) document.querySelector('.big-percent').textContent = '100%';
    const etaEl3 = document.getElementById('eta'); if(etaEl3) etaEl3.textContent = 'Done';
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
      window.showAppError(err.error || 'Generation failed');
      progressWrap.style.display = 'none';
    }
  }catch(e){
    clearInterval(progressInterval);
    window.showAppError('Generation request failed');
    progressWrap.style.display = 'none';
  }
}

export { renderPreview, handleGenerate };
