// ═══════════════════════════════════════════════
//  Visual Testing Studio — app.js v6
// ═══════════════════════════════════════════════

const form = document.getElementById("cmpForm");
const result = document.getElementById("result");
const toast = document.getElementById("toast");
const loader = document.getElementById("loader");
const progressFill = document.getElementById("progressFill");
const navRun = document.getElementById("nav-run");
const viewRun = document.getElementById("view-run");
const navHistory = document.getElementById("nav-history");
const viewHistory = document.getElementById("view-history");
const historyList = document.getElementById("history-list");
const actionsDiv = document.getElementById("actions");
const btnApprove = document.getElementById("btnApprove");
const btnReject = document.getElementById("btnReject");
const navBaselines = document.getElementById("btn-manage-baselines");
const viewBaselines = document.getElementById("view-baselines");
const blHistoryModal = document.getElementById("baseline-history-modal");
const blHistoryList = document.getElementById("bl-history-list");
const blModalTitle = document.getElementById("bl-modal-title");
const figmaInput = document.getElementById("figma");
const fileText = document.getElementById("file-text");
const dropZone = document.getElementById("drop-zone");

// ── File input listeners ──
figmaInput.addEventListener("change", () => {
  const f = figmaInput.files[0];
  fileText.textContent = f ? f.name : "Click or Drop Figma PNG here";
  fileText.classList.toggle("active", !!f);
  dropZone.classList.toggle("dragover", !!f);
});
figmaInput.addEventListener("dragenter", () => dropZone.classList.add("dragover"));
figmaInput.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
figmaInput.addEventListener("drop", () => dropZone.classList.remove("dragover"));

// Batch/Component file pickers
["figma-batch", "figma-comp"].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  const txtId = id === "figma-batch" ? "file-text-batch" : "file-text-comp";
  el.addEventListener("change", () => {
    const f = el.files[0];
    document.getElementById(txtId).textContent = f ? f.name : "Drop reference PNG";
    document.getElementById(txtId).classList.toggle("active", !!f);
  });
});

// ── Baseline Check ──
async function checkBaseline(url) {
  const uploadSection = document.getElementById("figma-upload-section");
  const urlInput = document.querySelector("input[name='stage_url']");
  if (!url || !url.startsWith("http")) {
    if (uploadSection) uploadSection.style.display = "block";
    return false;
  }
  try {
    const res = await fetch("/api/baselines", { cache: "no-store" });
    const baselines = await res.json();
    if (!Array.isArray(baselines)) return false;
    const normalize = (u) => {
      try { const o = new URL(u); return (o.protocol + "//" + o.host + o.pathname).replace(/\/+$/, "").toLowerCase(); }
      catch (e) { return u.replace(/\/+$/, "").trim().toLowerCase(); }
    };
    const target = normalize(url);
    const bl = baselines.find(b => normalize(b.url) === target && b.active_version_id);
    if (bl) {
      if (uploadSection) uploadSection.style.display = "none";
      let msg = document.getElementById("baseline-status-msg");
      if (!msg) {
        msg = document.createElement("p");
        msg.id = "baseline-status-msg";
        Object.assign(msg.style, { color: "#10b981", fontSize: "0.88em", fontWeight: "500", marginTop: "8px", padding: "8px 12px", background: "rgba(16,185,129,0.1)", borderRadius: "6px", border: "1px solid rgba(16,185,129,0.2)" });
        urlInput.parentNode.appendChild(msg);
      }
      msg.innerHTML = `✅ <strong>Baseline Active (v${bl.active_version_id})</strong> — Using saved reference image.`;
      msg.style.display = "block";
      return true;
    } else {
      if (uploadSection) uploadSection.style.display = "block";
      const msg = document.getElementById("baseline-status-msg");
      if (msg) msg.style.display = "none";
      return false;
    }
  } catch (e) { console.error("Baseline check error:", e); return false; }
}

const urlInput = document.getElementsByName("stage_url")[0];
urlInput.addEventListener("input", e => checkBaseline(e.target.value.trim()));
urlInput.addEventListener("change", e => checkBaseline(e.target.value.trim()));
if (urlInput.value) checkBaseline(urlInput.value.trim());
else { const up = document.getElementById("figma-upload-section"); if (up) up.style.display = "block"; }

// ── Toast ──
function showToast(msg, isError = false) {
  toast.textContent = msg;
  toast.classList.remove("hidden");
  toast.classList.toggle("error", isError);
  setTimeout(() => toast.classList.add("hidden"), 4000);
}

// ── Confirm Modal ──
function confirmModal(text) {
  return new Promise(resolve => {
    let modal = document.getElementById("custom-modal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "custom-modal";
      modal.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.65);display:flex;align-items:center;justify-content:center;z-index:9999;";
      modal.innerHTML = `
        <div style="background:#111c35;padding:28px;border-radius:14px;max-width:420px;width:90%;border:1px solid rgba(59,130,246,0.2);box-shadow:0 20px 60px rgba(0,0,0,0.5);">
          <h3 style="margin-top:0;color:#f8fafc;font-size:1.15rem;">Confirm Action</h3>
          <p id="c-modal-text" style="color:#94a3b8;margin:14px 0;line-height:1.6;"></p>
          <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:20px;">
            <button id="c-modal-cancel" class="btn-secondary" style="background:#1e293b;color:#94a3b8;border:1px solid #334155;">Cancel</button>
            <button id="c-modal-confirm" class="btn-approve">Confirm</button>
          </div>
        </div>`;
      document.body.appendChild(modal);
    }
    const txt = document.getElementById("c-modal-text");
    const yes = document.getElementById("c-modal-confirm");
    const no = document.getElementById("c-modal-cancel");
    txt.textContent = text;
    modal.style.display = "flex";
    const done = ok => { yes.onclick = null; no.onclick = null; modal.style.display = "none"; resolve(ok); };
    yes.onclick = () => done(true);
    no.onclick = () => done(false);
  });
}

// ── Step Tracker ──
const STEPS = ["screenshot", "align", "compare", "classify", "report"];
function updateStepTracker(progress) {
  const thresholds = [0, 15, 50, 70, 85];
  STEPS.forEach((s, i) => {
    const el = document.getElementById("step-" + s);
    if (!el) return;
    if (progress >= (thresholds[i + 1] || 100)) { el.className = "step-item done"; }
    else if (progress >= thresholds[i]) { el.className = "step-item active"; }
    else { el.className = "step-item"; }
  });
}

// ── Form Submit ──
form.addEventListener("submit", async e => {
  e.preventDefault();

  if (typeof currentMode === 'undefined') window.currentMode = 'single';

  if (currentMode === 'batch') {
    await runBatchMode();
    return;
  }

  const fd = new FormData(form);

  // For component mode, use different inputs
  if (currentMode === 'component') {
    const compUrl = document.getElementById('url-component').value.trim();
    if (!compUrl) { showToast("Please enter a component stage URL.", true); return; }
    fd.set('stage_url', compUrl);
    const compSel = document.getElementById('component_selector_main').value.trim();
    fd.set('component_selector', compSel);
    const compFile = document.getElementById('figma-comp').files[0];
    if (compFile) fd.set('figma_png', compFile);
  }

  const stageUrl = fd.get("stage_url");
  if (!stageUrl) { showToast("Please enter a Stage URL.", true); return; }

  // Reset UI
  result.classList.add("hidden");
  document.getElementById("batch-result").classList.add("hidden");
  toast.classList.add("hidden");
  loader.classList.remove("hidden");
  progressFill.style.width = "0%";
  document.getElementById("statusText").textContent = "0% - Starting...";
  updateStepTracker(0);

  const enablePixel = document.getElementById("enable_pixel_threshold").checked;
  fd.set("enable_pixel_threshold", enablePixel ? "true" : "false");
  if (enablePixel) {
    fd.set("pixel_threshold", parseInt(document.getElementById("pixel_threshold").value, 10));
  }

  try {
    const res = await fetch("/api/compare", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) { loader.classList.add("hidden"); showToast(data.error || "Comparison failed.", true); return; }
    pollStatus(data.job_id);
  } catch (err) {
    loader.classList.add("hidden");
    showToast("Unexpected error: " + err.message, true);
  }
});

// ── Batch Mode ──
async function runBatchMode() {
  const rows = document.querySelectorAll('.batch-url-row');
  const batchJobs = [];

  rows.forEach(row => {
    const urlInput = row.querySelector('.batch-url-input');
    const fileInput = row.querySelector('.batch-file-input');
    if (urlInput && urlInput.value.trim()) {
      batchJobs.push({
        url: urlInput.value.trim(),
        file: fileInput ? fileInput.files[0] : null
      });
    }
  });

  if (batchJobs.length === 0) { showToast("Add at least one URL in batch mode.", true); return; }

  document.getElementById("batch-result").classList.remove("hidden");
  document.getElementById("batch-results-body").innerHTML =
    `<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:20px;">🔄 Running batch comparison...</td></tr>`;

  const results = [];
  let passed = 0, failed = 0;

  for (let i = 0; i < batchJobs.length; i++) {
    const { url, file } = batchJobs[i];
    const fd = new FormData(form);

    // Ensure we don't accidentally pass a shared Figma PNG
    fd.delete("figma_png");

    fd.set("stage_url", url);
    if (file) {
      fd.set("figma_png", file);
    }

    try {
      const startRes = await fetch("/api/compare", { method: "POST", body: fd });
      const startData = await startRes.json();
      if (!startRes.ok) { results.push({ url, status: 'failed', error: startData.error }); failed++; continue; }

      // Poll until done
      const jobResult = await waitForJob(startData.job_id);
      if (jobResult.status === 'completed') {
        const r = jobResult.result;
        results.push({ url, job_id: startData.job_id, ssim: r.metrics.ssim, change: r.metrics.change_ratio, issues: r.metrics.num_regions, passed: r.passed });
        r.passed ? passed++ : failed++;
      } else {
        results.push({ url, status: 'failed', error: jobResult.error });
        failed++;
      }
    } catch (err) {
      results.push({ url, status: 'failed', error: err.message });
      failed++;
    }
    renderBatchTable(results, batchJobs.length, passed, failed);
  }
  showToast(`Batch done: ${passed} passed, ${failed} failed.`);
}

async function waitForJob(jobId) {
  while (true) {
    const res = await fetch(`/api/status/${jobId}`);
    const data = await res.json();
    if (data.status === 'completed' || data.status === 'failed') return data;
    await new Promise(r => setTimeout(r, 800));
  }
}

function renderBatchTable(results, total, passed, failed) {
  const tbody = document.getElementById('batch-results-body');
  tbody.innerHTML = results.map((r, i) => {
    if (r.error) {
      return `<tr>
        <td>${i + 1}</td>
        <td title="${r.url}" style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${r.url}</td>
        <td colspan="4" style="color:var(--error);">Error: ${r.error}</td>
        <td>–</td>
      </tr>`;
    }
    const ssimFmt = r.ssim !== undefined ? r.ssim.toFixed(4) : '–';
    const changeFmt = r.change !== undefined ? (r.change * 100).toFixed(1) + '%' : '–';
    const statusPill = r.passed
      ? `<span class="status-pill pass">✅ Pass</span>`
      : `<span class="status-pill fail">❌ Fail</span>`;
    const pdfLink = r.job_id
      ? `<a href="/download/${r.job_id}/report.pdf" target="_blank" class="btn-secondary" style="font-size:11px;padding:3px 8px;">PDF</a>`
      : '–';
    return `<tr>
      <td>${i + 1}</td>
      <td title="${r.url}" class="history-url-cell">${r.url}</td>
      <td>${ssimFmt}</td>
      <td>${changeFmt}</td>
      <td>${r.issues !== undefined ? r.issues : '–'}</td>
      <td>${statusPill}</td>
      <td>${pdfLink}</td>
    </tr>`;
  }).join('');

  // Summary
  const pct = total > 0 ? Math.round(passed / total * 100) : 0;
  document.getElementById('batch-summary').innerHTML = `
    <div class="metric-card passed"><div class="metric-card-label">Passed</div><div class="metric-card-value">${passed}</div><div class="metric-card-sub">of ${total} URLs</div></div>
    <div class="metric-card failed"><div class="metric-card-label">Failed</div><div class="metric-card-value">${failed}</div><div class="metric-card-sub">visual regressions</div></div>
    <div class="metric-card"><div class="metric-card-label">Pass Rate</div><div class="metric-card-value">${pct}%</div><div class="metric-card-sub">Overall success</div></div>
  `;
}

// ── Navigation ──
navRun.addEventListener("click", e => { e.preventDefault(); switchView("run"); });
navHistory.addEventListener("click", e => { e.preventDefault(); switchView("history"); });
navBaselines.addEventListener("click", e => { e.preventDefault(); switchView("baselines"); });
document.getElementById("baselines-back").addEventListener("click", e => { e.preventDefault(); switchView("run"); });
document.getElementById("history-back").addEventListener("click", e => { e.preventDefault(); switchView("run"); });

function switchView(view) {
  viewRun.classList.add("hidden");
  viewHistory.classList.add("hidden");
  viewBaselines.classList.add("hidden");
  navRun.classList.remove("active");
  if (view === "run") { viewRun.classList.remove("hidden"); navRun.classList.add("active"); const v = urlInput.value; if (v) checkBaseline(v.trim()); }
  else if (view === "history") { viewHistory.classList.remove("hidden"); loadHistory(); }
  else if (view === "baselines") { viewBaselines.classList.remove("hidden"); loadBaselines(); }
}

// ── Poll Status ──
async function pollStatus(jobId) {
  try {
    const res = await fetch(`/api/status/${jobId}`);
    if (!res.ok) { loader.classList.add("hidden"); showToast("Job not found.", true); return; }
    const data = await res.json();

    if (data.progress !== undefined) {
      progressFill.style.width = `${data.progress}%`;
      document.getElementById("statusText").textContent = `${data.progress}% — ${data.step || ""}`;
      updateStepTracker(data.progress);
    }

    if (data.status === "completed") {
      loader.classList.add("hidden");
      renderResults(data.result, jobId);

    } else if (data.status === "failed") {
      loader.classList.add("hidden");
      showToast(data.error || "Job failed.", true);
    } else {
      setTimeout(() => pollStatus(jobId), 600);
    }
  } catch (err) {
    loader.classList.add("hidden");
    showToast("Error checking status: " + err.message, true);
  }
}

// ── Render Results ──
async function renderResults(results, jobId) {
  result.classList.remove("hidden");

  // Slider images
  document.getElementById('slider-img-before').src = results.outputs.figma_png;
  document.getElementById('slider-img-after').src = results.outputs.aligned_stage;

  // Hero Banner
  const hero = document.getElementById('result-hero');
  const heroIcon = document.querySelector('#result-hero .result-hero-icon');
  const heroTitle = document.getElementById('result-hero-title');
  const heroSub = document.getElementById('result-hero-sub');
  if (results.passed) {
    hero.className = 'result-hero passed';
    heroIcon.textContent = '✅';
    heroTitle.textContent = 'All Visual Tests Passed';
    heroSub.textContent = `SSIM ${results.metrics.ssim.toFixed(4)} — No significant visual regressions detected.`;
  } else {
    hero.className = 'result-hero failed';
    heroIcon.textContent = '🔴';
    heroTitle.textContent = `${results.metrics.num_regions} Visual Difference${results.metrics.num_regions !== 1 ? 's' : ''} Detected`;
    heroSub.textContent = `SSIM ${results.metrics.ssim.toFixed(4)} — Review highlighted regions below.`;
  }

  // Metrics Dashboard
  const ssimPct = Math.round(results.metrics.ssim * 100);
  const ssimColor = ssimPct >= 95 ? 'var(--success)' : ssimPct >= 80 ? 'var(--warning)' : 'var(--error)';
  document.getElementById('mc-ssim-val').textContent = results.metrics.ssim.toFixed(4);
  document.getElementById('mc-ssim-val').style.color = ssimColor;
  document.getElementById('mc-ssim').style.setProperty('--ring-pct', ssimPct + '%');

  const changePct = (results.metrics.change_ratio * 100).toFixed(2);
  document.getElementById('mc-diff-val').textContent = changePct + '%';
  document.getElementById('mc-diff-val').style.color = parseFloat(changePct) < 2 ? 'var(--success)' : parseFloat(changePct) < 10 ? 'var(--warning)' : 'var(--error)';

  document.getElementById('mc-regions-val').textContent = results.metrics.num_regions;
  document.getElementById('mc-regions-val').style.color = results.metrics.num_regions === 0 ? 'var(--success)' : results.metrics.num_regions < 5 ? 'var(--warning)' : 'var(--error)';

  document.getElementById('mc-status-val').textContent = results.passed ? 'PASS' : 'FAIL';
  document.getElementById('mc-status-val').style.color = results.passed ? 'var(--success)' : 'var(--error)';

  // Actions
  actionsDiv.classList.remove("hidden");
  actionsDiv.style.display = "flex";
  btnApprove.dataset.jobId = jobId;
  btnReject.dataset.jobId = jobId;

  const existing = document.getElementById("btnUpdateBaseline");
  if (existing) existing.remove();
  const btnUpdate = document.createElement("button");
  btnUpdate.id = "btnUpdateBaseline";
  btnUpdate.innerHTML = "🔄 Update Baseline";
  btnUpdate.className = "btn-approve";
  btnUpdate.style.backgroundColor = "#7c3aed";
  btnUpdate.onclick = () => promoteBaseline(jobId);
  actionsDiv.appendChild(btnUpdate);

  try {
    const jobRes = await fetch(`/api/job/${jobId}`);
    const jobData = await jobRes.json();
    if (jobData?.url) {
      const hasBl = await checkBaseline(jobData.url);
      btnApprove.style.display = (!hasBl || jobData.reference_source === 'upload') ? "none" : "inline-flex";
      if (document.getElementsByName("stage_url")[0]) {
        document.getElementsByName("stage_url")[0].value = jobData.stage_url || jobData.url;
      }
    }
  } catch (e) { console.error(e); }

  // Downloads
  document.getElementById('dl_overlay').href = results.outputs.diff_overlay;
  document.getElementById('dl_heatmap').href = results.outputs.diff_heatmap;
  document.getElementById('dl_aligned').href = results.outputs.aligned_stage;
  document.getElementById('dl_report').href = results.outputs.report_pdf;

  // Preview Grid
  const previews = document.getElementById("previews");
  previews.innerHTML = `
    <figure>
      <figcaption>📐 Reference (Figma)</figcaption>
      <img src="${results.outputs.figma_png}" alt="Reference" loading="lazy"/>
    </figure>
    <figure>
      <figcaption>🌡 Diff Heatmap</figcaption>
      <img src="${results.outputs.diff_heatmap}" alt="Heatmap" loading="lazy"/>
    </figure>
    <figure>
      <figcaption>🔴 Diff Overlay (${results.metrics.num_regions} issues)</figcaption>
      <img src="${results.outputs.diff_overlay}" alt="Overlay" loading="lazy"/>
    </figure>
  `;

  // Issues
  renderIssues(results.metrics.issues, results, jobId);
  showToast(results.passed ? "✅ Test Passed!" : `🔴 ${results.metrics.num_regions} differences found.`);
}

function renderIssues(issues, results, jobId) {
  const section = document.getElementById("issues-section");
  if (!issues || issues.length === 0) {
    section.innerHTML = `<div style="text-align:center;padding:30px;color:var(--success);font-size:1.1rem;">✅ No visual differences detected!</div>`;
    return;
  }

  // Diff legend
  const typeMap = {
    'Spacing': '📐 Spacing', 'Margin': '📐 Spacing', 'Padding': '📐 Spacing', 'Gap': '📐 Spacing', 'Column': '📐 Spacing',
    'Color': '🎨 Style', 'Style': '🎨 Style',
    'Content': '📝 Content', 'Text': '📝 Content',
    'Missing': '⚠️ Element', 'Extra': '⚠️ Element',
    'Layout': '🔲 Layout'
  };
  const colorMap = {
    '📐 Spacing': ['#dbeafe', '#1d4ed8'],
    '🎨 Style': ['#fed7aa', '#9a3412'],
    '📝 Content': ['#fef9c3', '#854d0e'],
    '⚠️ Element': ['#fce7f3', '#9d174d'],
    '🔲 Layout': ['#e9d5ff', '#6b21a8']
  };

  function getCategory(desc) {
    for (const [kw, cat] of Object.entries(typeMap)) {
      if (desc && desc.includes(kw)) return cat;
    }
    return '🔲 Layout';
  }

  const categories = [...new Set(issues.map(i => getCategory(i.description)))];
  const legendHtml = categories.map(cat => {
    const [bg, color] = colorMap[cat] || ['#e2e8f0', '#374151'];
    return `<div class="diff-legend-item"><div class="diff-legend-dot" style="background:${color};"></div>${cat}</div>`;
  }).join('');

  const issuesHtml = issues.map(issue => {
    const cat = getCategory(issue.description);
    const [bg, color] = colorMap[cat] || ['#e2e8f0', '#374151'];
    return `
      <div class="issue-card">
        <input type="checkbox" class="issue-checkbox" value="${issue.filename}" style="position:absolute;top:10px;left:10px;z-index:10;transform:scale(1.4);">
        <div class="issue-thumb">
          <img src="/download/${results.job_id}/${issue.filename}" alt="${issue.label}" loading="lazy"/>
        </div>
        <div class="issue-info">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
            <span style="font-size:0.72em;padding:2px 9px;border-radius:10px;font-weight:700;background:${bg};color:${color};">${cat}</span>
          </div>
          <h4 title="${issue.full_label || issue.label}" style="margin:0 0 4px;font-size:0.9rem;">${issue.full_label || issue.label}</h4>
          <p style="font-size:0.78em;color:var(--muted);margin:0 0 8px;">📍 X=${issue.x}, Y=${issue.y} &nbsp;·&nbsp; ${issue.dims || ''}</p>
          <div style="display:flex;flex-direction:column;gap:5px;">
            <a href="/download/${results.job_id}/${issue.filename}" download class="btn-download-issue">⬇ Download Crop</a>
            <button onclick="window.openJiraReport('${jobId}','${issue.filename}','${(issue.label || '').replace(/'/g, "\\'")}','${(issue.description || '').replace(/'/g, "\\'")}' )" class="btn-secondary" style="font-size:11px;padding:5px 10px;">🎫 Report to Jira</button>
            <button onclick="window.openGitHubReport('${jobId}','${issue.filename}','${(issue.label || '').replace(/'/g, "\\'")}','${(issue.description || '').replace(/'/g, "\\'")}' )" class="btn-secondary" style="font-size:11px;padding:5px 10px;background:#f6f8fa;color:#24292e;border:1px solid #d0d7de;">🐙 Report to GitHub</button>
          </div>
        </div>
      </div>`;
  }).join('');

  section.innerHTML = `
    <div class="section-heading">
      <h3>🔍 Detected Differences</h3>
      <span class="count-badge">${issues.length} issue${issues.length !== 1 ? 's' : ''}</span>
      <div style="margin-left:auto;display:flex;gap:10px;align-items:center;">
        <label style="font-size:13px;display:flex;align-items:center;gap:5px;cursor:pointer;">
          <input type="checkbox" id="selectAllIssues" onclick="window.toggleAllIssues(this)"> Select All
        </label>
        <button onclick="window.downloadSelectedIssues('${jobId}')" class="btn-secondary" style="font-size:12px;padding:6px 12px;">⬇ Download Selected</button>
      </div>
    </div>
    <div class="diff-legend">${legendHtml}</div>
    <div class="grid">${issuesHtml}</div>
  `;
}

// ── Approval Logic ──
btnApprove.onclick = () => handleReview(true);
btnReject.onclick = () => handleReview(false);

async function handleReview(approve) {
  const jobId = btnApprove.dataset.jobId;
  if (!jobId) return;
  const endpoint = approve ? "approve" : "reject";
  const res = await fetch(`/api/job/${jobId}/${endpoint}`, { method: "POST" });
  if (res.ok) {
    showToast(approve ? "✅ Job Approved." : "❌ Job Rejected.");
    setTimeout(() => window.location.reload(), 1500);
  } else {
    showToast("Action failed.", true);
  }
}

async function promoteBaseline(jobId) {
  if (!await confirmModal("Update the official baseline with the reference image from this run?")) return;
  const res = await fetch(`/api/baselines/promote/${jobId}`, { method: "POST" });
  const data = await res.json();
  if (res.ok) { showToast(`✅ Baseline Updated (v${data.version_id})`); setTimeout(() => window.location.reload(), 1500); }
  else { showToast("Error: " + (data.error || "Promotion failed"), true); }
}

// ── History ──
let currentPage = 1;
let currentFilter = 'all';
const LIMIT = 10;

window.filterHistory = function (filter, btn) {
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  loadHistory(1);
};

async function loadHistory(page = 1) {
  currentPage = page;
  historyList.innerHTML = "<tr><td colspan='8' style='text-align:center;color:var(--muted);'>Loading...</td></tr>";
  document.getElementById("pagination").innerHTML = "";
  try {
    let url = `/api/history?page=${page}&limit=${LIMIT}`;
    if (currentFilter && currentFilter !== 'all') url += `&filter=${currentFilter}`;
    const res = await fetch(url);
    const data = await res.json();
    let jobs = Array.isArray(data) ? data : data.jobs;
    const total = data.total !== undefined ? data.total : jobs.length;

    if (!jobs || jobs.length === 0) {
      historyList.innerHTML = "<tr><td colspan='8' style='text-align:center;color:var(--muted);padding:30px;'>No history found.</td></tr>";
      return;
    }

    historyList.innerHTML = "";
    jobs.forEach(job => {
      const row = document.createElement("tr");
      const date = job.timestamp ? new Date(job.timestamp).toLocaleString() : (job.created_at ? new Date(job.created_at).toLocaleString() : "–");
      const review = job.approved === true ? '<span class="status-pill pass">✅ Approved</span>' : job.approved === false ? '<span class="status-pill fail">✗ Rejected</span>' : '–';
      const ssim = job.result?.metrics?.ssim !== undefined ? job.result.metrics.ssim.toFixed(3) : (job.result?.ssim !== undefined ? job.result.ssim.toFixed(3) : "–");
      const ssimNum = parseFloat(ssim);
      const ssimBar = !isNaN(ssimNum) ? `<div class="ssim-bar-wrap"><div class="ssim-bar"><div class="ssim-bar-fill" style="width:${Math.round(ssimNum * 100)}%"></div></div><span style="font-size:0.8em;font-weight:600;">${ssim}</span></div>` : ssim;
      const url_ = job.stage_url || job.url || '';
      const urlDisplay = url_ ? `<div title="${url_}" class="history-url-cell" style="font-size:0.78em;color:var(--muted);">${url_}</div>` : '';

      row.innerHTML = `
        <td><input type="checkbox" class="history-checkbox" value="${job.job_id}"></td>
        <td style="font-size:0.82em;">${date}</td>
        <td style="font-family:monospace;font-size:0.78em;color:var(--muted);">${job.job_id}</td>
        <td>${urlDisplay}</td>
        <td><span class="status-pill ${job.status === 'completed' ? 'pass' : job.status === 'failed' ? 'fail' : 'running'}">${job.status}</span></td>
        <td>${review}</td>
        <td>${ssimBar}</td>
        <td>${job.status === "completed" && job.result ? `<a href="/download/${job.job_id}/report.pdf" target="_blank" class="btn-secondary" style="font-size:11px;padding:4px 9px;">📄 PDF</a>` : "–"}</td>
      `;
      historyList.appendChild(row);
    });

    const totalPages = Math.ceil(total / LIMIT);
    document.getElementById("pagination").innerHTML = `
      <button class="btn-reject" style="font-size:12px;padding:5px 12px;" onclick="deleteSelected()">🗑 Delete Selected</button>
      <span style="font-size:0.85rem;color:var(--muted);">Page ${page} of ${totalPages} (${total} total)</span>
      <div style="display:flex;gap:8px;">
        <button class="btn-secondary" ${page <= 1 ? 'disabled' : ''} onclick="loadHistory(${page - 1})" style="padding:5px 12px;font-size:13px;">← Prev</button>
        <button class="btn-secondary" ${page >= totalPages ? 'disabled' : ''} onclick="loadHistory(${page + 1})" style="padding:5px 12px;font-size:13px;">Next →</button>
      </div>`;
  } catch (err) {
    historyList.innerHTML = `<tr><td colspan='8' style='color:var(--error);'>Error: ${err.message}</td></tr>`;
  }
}

async function deleteSelected() {
  const ids = Array.from(document.querySelectorAll(".history-checkbox:checked")).map(cb => cb.value);
  if (ids.length === 0) { showToast("No records selected.", true); return; }
  if (!await confirmModal(`Delete ${ids.length} record${ids.length > 1 ? 's' : ''}? This cannot be undone.`)) return;
  try {
    const res = await fetch("/api/history/delete", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_ids: ids }) });
    if (res.ok) { showToast("Records deleted."); loadHistory(currentPage); }
    else { showToast("Delete failed.", true); }
  } catch (e) { showToast("Error deleting records.", true); }
}

function toggleAll(source) {
  document.querySelectorAll('.history-checkbox').forEach(cb => { cb.checked = source.checked; });
}
window.toggleAll = toggleAll;
window.deleteSelected = deleteSelected;

window.toggleAllIssues = function (source) {
  document.querySelectorAll('.issue-checkbox').forEach(cb => { cb.checked = source.checked; });
};

window.downloadSelectedIssues = function (jobId) {
  const checked = document.querySelectorAll(".issue-checkbox:checked");
  if (checked.length === 0) { showToast("No issues selected.", true); return; }
  Array.from(checked).forEach((cb, i) => {
    setTimeout(() => {
      const a = document.createElement('a');
      a.href = `/download/${jobId}/${cb.value}`;
      a.download = cb.value;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
    }, i * 300);
  });
  showToast(`Downloading ${checked.length} issues...`);
};

// ── Baselines ──
async function loadBaselines() {
  const list = document.getElementById("baselines-list");
  list.innerHTML = "<p style='color:var(--muted);'>Loading baselines...</p>";
  try {
    const res = await fetch("/api/baselines");
    const baselines = await res.json();
    if (!baselines || baselines.length === 0) {
      list.innerHTML = "<p style='color:var(--muted);padding:30px;text-align:center;'>No baselines found. Run a comparison and Approve it to create one.</p>";
      return;
    }
    list.innerHTML = baselines.map(b => {
      const active = b.versions.find(v => v.version_id === b.active_version_id);
      const date = active ? new Date(active.timestamp).toLocaleString() : "–";
      const imgUrl = b.active_image_path ? `/api/baselines/image/${b.active_image_path}` : '';
      let displayTitle = "Baseline";
      try { const u = new URL(b.url); displayTitle = u.pathname === "/" || u.pathname === "" ? "Homepage" : u.pathname; } catch (e) { displayTitle = b.url; }
      return `
        <div class="baseline-card">
          <div style="height:160px;overflow:hidden;border-radius:8px;background:#0f172a;border:1px solid #1e293b;display:flex;align-items:center;justify-content:center;margin-bottom:14px;">
            ${imgUrl ? `<img src="${imgUrl}" alt="Baseline" style="width:100%;height:100%;object-fit:contain;">` : '<span style="color:#475569;font-size:0.8rem;">No image</span>'}
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <h3 title="${b.url}" style="font-size:1rem;margin:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;max-width:210px;color:#e2e8f0;">${displayTitle}</h3>
            <button onclick="window.deleteBaseline('${b.url}')" class="btn-reject" style="padding:3px 8px;font-size:11px;">✕</button>
          </div>
          <p style="font-size:0.78rem;color:#64748b;margin:4px 0;">${b.active_version_id || "v1"} · ${date}</p>
          <div style="margin-top:12px;display:flex;gap:8px;">
            <button onclick="window.viewBaselineHistory('${encodeURIComponent(b.url)}')" class="btn-secondary" style="flex:1;font-size:13px;">📜 History</button>
            <button onclick="window.uploadBaseline('${b.url}')" class="btn-approve" style="flex:1;font-size:13px;">🔄 Update</button>
          </div>
        </div>`;
    }).join('');
  } catch (e) { list.innerHTML = `<p style="color:var(--error);">Error: ${e.message}</p>`; }
}

window.deleteBaseline = async function (url) {
  if (!await confirmModal(`Delete baseline for ${url}? Cannot be undone.`)) return;
  try {
    const res = await fetch("/api/baselines/delete", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) });
    if (res.ok) { showToast("Baseline deleted."); loadBaselines(); }
    else { const d = await res.json(); showToast(d.error || "Delete failed", true); }
  } catch (e) { showToast("Error deleting baseline", true); }
};

const blUploadInput = document.createElement("input");
blUploadInput.type = "file"; blUploadInput.accept = "image/png"; blUploadInput.style.display = "none";
document.body.appendChild(blUploadInput);
let currentUploadUrl = null;
blUploadInput.addEventListener("change", async () => {
  if (!blUploadInput.files[0] || !currentUploadUrl) return;
  const fd = new FormData();
  fd.set("file", blUploadInput.files[0]); fd.set("url", currentUploadUrl);
  showToast("Uploading baseline...");
  try {
    const res = await fetch("/api/baselines/upload", { method: "POST", body: fd });
    const data = await res.json();
    if (res.ok) { showToast(`Baseline updated (v${data.version_id})`); loadBaselines(); }
    else { showToast(data.error || "Upload failed", true); }
  } catch (e) { showToast("Upload error", true); }
  blUploadInput.value = ""; currentUploadUrl = null;
});
window.uploadBaseline = function (url) { currentUploadUrl = url; blUploadInput.click(); };

window.viewBaselineHistory = async function (encodedUrl) {
  const url = decodeURIComponent(encodedUrl);
  blHistoryModal.classList.remove("hidden");
  let cleanTitle = url;
  try { const u = new URL(url); cleanTitle = u.pathname === "/" ? "Homepage" : u.pathname; } catch (e) { }
  blModalTitle.textContent = `History: ${cleanTitle}`;
  blHistoryList.innerHTML = "<tr><td colspan='4'>Loading...</td></tr>";
  try {
    const res = await fetch("/api/baselines");
    const baselines = await res.json();
    const bl = baselines.find(b => b.url === url);
    if (!bl) { blHistoryList.innerHTML = "<tr><td colspan='4'>Not found</td></tr>"; return; }
    blHistoryList.innerHTML = bl.versions.map(v => {
      const isActive = v.version_id === bl.active_version_id;
      const date = new Date(v.timestamp).toLocaleString();
      const action = !isActive
        ? `<button onclick="window.rollbackBaseline('${encodeURIComponent(url)}','${v.version_id}')" class="btn-secondary" style="font-size:12px;">↩ Rollback</button>`
        : `<span style="color:var(--success);font-weight:600;">● Current</span>`;
      return `<tr style="${isActive ? 'background:rgba(16,185,129,0.1);' : ''}">
        <td style="font-family:monospace;font-size:0.85em;">${v.version_id}</td>
        <td style="font-size:0.85em;">${date}</td>
        <td><a href="#" onclick="window.loadJob('${v.job_id}');document.getElementById('baseline-history-modal').classList.add('hidden');return false;" style="color:#60a5fa;">${v.job_id}</a></td>
        <td>${action}</td>
      </tr>`;
    }).join('');
  } catch (e) { blHistoryList.innerHTML = `<tr><td colspan='4'>Error: ${e.message}</td></tr>`; }
};

window.rollbackBaseline = async function (encodedUrl, versionId) {
  const url = decodeURIComponent(encodedUrl);
  if (!await confirmModal(`Rollback ${url} to version ${versionId}?`)) return;
  const res = await fetch("/api/baselines/rollback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url, version_id: versionId }) });
  if (res.ok) { showToast("Rollback successful."); window.viewBaselineHistory(encodedUrl); loadBaselines(); }
  else { const d = await res.json(); showToast(d.error || "Rollback failed", true); }
};

// ── Load Job (from history) ──
window.loadJob = function (jobId) {
  switchView("run");
  form.reset();
  result.classList.add("hidden");
  loader.classList.remove("hidden");
  progressFill.style.width = "100%";
  document.getElementById("statusText").textContent = "Loading job...";
  pollStatus(jobId);
};
