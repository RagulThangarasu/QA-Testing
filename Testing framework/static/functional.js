/**
 * AI Functional Testing — Frontend Logic
 * Zero-locator, plain-English functional testing powered by local Ollama LLM
 */

// ─── State ────────────────────────────────────────────────
let currentJobId = null;
let pollTimer = null;
let historyPage = 1;
const HISTORY_LIMIT = 10;

// ─── DOM Ready ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    checkOllamaStatus();

    // Form submit
    const form = document.getElementById('functionalForm');
    form.addEventListener('submit', handleSubmit);

    // File upload / drag-and-drop
    const dropZone = document.getElementById('excel-drop-zone');
    const fileInput = document.getElementById('excelFile');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            showFileName(e.dataTransfer.files[0].name);
        }
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) showFileName(fileInput.files[0].name);
    });

    // Navigation
    document.getElementById('nav-history').addEventListener('click', e => {
        e.preventDefault();
        showView('history');
        loadHistory();
    });
    document.getElementById('nav-run').addEventListener('click', e => {
        e.preventDefault();
        showView('run');
    });
    document.getElementById('btn-clear').addEventListener('click', () => {
        clearResults();
    });
    document.getElementById('btn-delete-selected').addEventListener('click', deleteSelected);
});

// ─── Ollama Status ────────────────────────────────────────
async function checkOllamaStatus() {
    const badge = document.getElementById('ollama-status');
    const text = document.getElementById('ollama-status-text');
    const modelsList = document.getElementById('ollama-models-list');
    const installedModels = document.getElementById('installed-models');

    try {
        const resp = await fetch('/api/functional/ollama-status');
        const data = await resp.json();

        if (data.available) {
            badge.className = 'ai-badge connected';
            text.textContent = `Ollama Connected (${data.models.length} models)`;

            if (data.models.length > 0) {
                modelsList.style.display = 'block';
                installedModels.textContent = data.models.join(', ');

                // Auto-select first available model
                const modelSelect = document.getElementById('ollamaModel');
                const installedModelNames = data.models.map(m => m.split(':')[0]);
                for (const opt of modelSelect.options) {
                    if (installedModelNames.includes(opt.value)) {
                        opt.selected = true;
                        break;
                    }
                }
            }
        } else {
            badge.className = 'ai-badge disconnected';
            text.textContent = 'Ollama Not Connected';
        }
    } catch (e) {
        badge.className = 'ai-badge disconnected';
        text.textContent = 'Ollama Not Connected';
    }
}

// ─── File Upload ──────────────────────────────────────────
function showFileName(name) {
    const info = document.getElementById('file-info');
    const nameSpan = document.getElementById('file-name');
    nameSpan.textContent = name;
    info.style.display = 'block';
}

// ─── Input Type Toggle ───────────────────────────────────
function toggleInputType() {
    const inputType = document.querySelector('input[name="inputType"]:checked').value;
    document.getElementById('urlInputContainer').classList.toggle('hidden', inputType !== 'url');
    document.getElementById('sitemapInputContainer').classList.toggle('hidden', inputType !== 'sitemap');
}

// ─── Submit ───────────────────────────────────────────────
async function handleSubmit(e) {
    e.preventDefault();

    const inputType = document.querySelector('input[name="inputType"]:checked').value;
    const targetUrl = document.getElementById('targetUrl').value.trim();
    const sitemapUrl = document.getElementById('sitemapUrl').value.trim();
    const excelFile = document.getElementById('excelFile').files[0];
    const ollamaUrl = document.getElementById('ollamaUrl').value.trim();
    const ollamaModel = document.getElementById('ollamaModel').value;

    // Validation
    if (inputType === 'url' && !targetUrl) {
        toast('Please enter a target URL', true);
        return;
    }
    if (inputType === 'sitemap' && !sitemapUrl) {
        toast('Please enter a sitemap URL', true);
        return;
    }
    if (!excelFile) {
        toast('Please upload an Excel file with test cases', true);
        return;
    }

    // Build FormData
    const formData = new FormData();
    formData.append('input_type', inputType);
    if (inputType === 'url') formData.append('target_url', targetUrl);
    else formData.append('sitemap_url', sitemapUrl);
    formData.append('excel_file', excelFile);
    formData.append('ollama_url', ollamaUrl);
    formData.append('ollama_model', ollamaModel);

    // Show loader
    showLoader();
    hideResults();

    try {
        const resp = await fetch('/api/functional/run', {
            method: 'POST',
            body: formData
        });
        const data = await resp.json();

        if (data.error) {
            toast(data.error, true);
            hideLoader();
            return;
        }

        currentJobId = data.job_id;
        startPolling(currentJobId);
    } catch (err) {
        toast('Failed to start test: ' + err.message, true);
        hideLoader();
    }
}

// ─── Polling ──────────────────────────────────────────────
function startPolling(jobId) {
    if (pollTimer) clearInterval(pollTimer);

    pollTimer = setInterval(async () => {
        try {
            const resp = await fetch(`/api/status/${jobId}`);
            const data = await resp.json();

            if (!data) return;

            // Update progress
            const progress = data.progress || 0;
            const step = data.step || 'Processing...';
            updateProgress(progress, step);

            if (data.status === 'completed') {
                clearInterval(pollTimer);
                pollTimer = null;
                hideLoader();
                renderResults(data.result);
                toast('✅ Functional tests completed!');
            } else if (data.status === 'failed') {
                clearInterval(pollTimer);
                pollTimer = null;
                hideLoader();
                toast('❌ ' + (data.error || 'Test failed'), true);
            }
        } catch (e) {
            // Retry silently
        }
    }, 1500);
}

// ─── Progress ─────────────────────────────────────────────
function showLoader() {
    document.getElementById('loader').classList.remove('hidden');
}

function hideLoader() {
    document.getElementById('loader').classList.add('hidden');
}

function updateProgress(pct, step) {
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('statusText');
    fill.style.width = pct + '%';
    text.textContent = `${pct}% — ${step}`;
}

function hideResults() {
    document.getElementById('results').classList.add('hidden');
}

function clearResults() {
    hideResults();
    hideLoader();
    document.getElementById('results').innerHTML = '';
    currentJobId = null;
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

// ─── Render Results ───────────────────────────────────────
function renderResults(result) {
    const container = document.getElementById('results');
    if (!result) {
        container.innerHTML = '<p style="color: var(--muted);">No results.</p>';
        container.classList.remove('hidden');
        return;
    }

    // Handle sitemap batch results
    const isBatch = !!result.summary;
    const total = isBatch ? result.summary.total_steps : (result.total || 0);
    const passed = isBatch ? result.summary.total_passed : (result.passed || 0);
    const failed = isBatch ? result.summary.total_failed : (result.failed || 0);
    const skipped = isBatch ? result.summary.total_skipped : (result.skipped || 0);
    const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;

    // Determine color
    let rateColor = '#34d399';
    if (passRate < 50) rateColor = '#ef4444';
    else if (passRate < 80) rateColor = '#f59e0b';

    let html = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
            <h2 style="margin: 0;">📋 Test Results</h2>
            <div style="display: flex; gap: 8px;">`;

    if (result.pdf_report_url) {
        html += `<a href="${result.pdf_report_url}" class="btn-download-issue" download>📄 Download PDF</a>`;
    }

    html += `</div></div>`;

    // Pass rate circle + Summary cards
    html += `
        <div style="display: grid; grid-template-columns: 140px 1fr; gap: 24px; align-items: center; margin-bottom: 20px;">
            <div class="pass-rate-circle" style="--rate-pct: ${passRate}; --rate-color: ${rateColor};">
                <span class="pass-rate-value">${passRate}%</span>
                <span class="pass-rate-label">Pass Rate</span>
            </div>
            <div class="result-summary" style="margin: 0;">
                <div class="result-card total">
                    <span class="rc-value">${total}</span>
                    <span class="rc-label">Total Steps</span>
                </div>
                <div class="result-card passed">
                    <span class="rc-value">${passed}</span>
                    <span class="rc-label">Passed</span>
                </div>
                <div class="result-card failed">
                    <span class="rc-value">${failed}</span>
                    <span class="rc-label">Failed</span>
                </div>
                <div class="result-card skipped">
                    <span class="rc-value">${skipped}</span>
                    <span class="rc-label">Skipped</span>
                </div>
            </div>
        </div>`;

    // Components discovered
    if (result.components && result.components.length > 0) {
        html += `<h3 style="margin: 16px 0 8px;">🧩 Discovered Components</h3><div class="component-chips">`;
        for (const comp of result.components) {
            html += `<span class="component-chip">${comp.name} <span class="chip-count">×${comp.count}</span></span>`;
        }
        html += `</div>`;
    }

    // Steps
    const steps = isBatch ? [] : (result.steps || []);
    if (isBatch && result.url_results) {
        for (const ur of result.url_results) {
            for (const s of (ur.steps || [])) {
                s._url = ur.url;
                steps.push(s);
            }
        }
    }

    if (steps.length > 0) {
        html += `<h3 style="margin: 24px 0 12px 0;">🔬 Step-by-Step Results</h3><div class="step-list">`;

        for (let i = 0; i < steps.length; i++) {
            const s = steps[i];
            const status = s.status || 'unknown';
            const delay = Math.min(i * 0.05, 1);

            html += `
                <div class="step-card ${status}" style="animation-delay: ${delay}s;">
                    <div class="step-header">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span class="step-num">#${s.step || i + 1}</span>
                            ${s.test_id ? `<span style="font-size: 0.78rem; color: var(--muted);">${s.test_id}</span>` : ''}
                            ${s.component ? `<span class="component-chip" style="margin: 0; padding: 2px 10px; font-size: 0.74rem;">${s.component}</span>` : ''}
                        </div>
                        <span class="step-status ${status}">${statusIcon(status)} ${status}</span>
                    </div>
                    <div class="step-instruction">${escapeHtml(s.instruction || '')}</div>`;

            if (s._url) {
                html += `<div class="step-meta-item" style="margin-top: 4px; font-size: 0.76rem; color: #6b7280;">🔗 ${escapeHtml(s._url.substring(0, 60))}</div>`;
            }

            html += `<div class="step-meta">`;

            if (s.ai_decision) {
                html += `<span class="step-meta-item">🧠 AI Action: <code>${s.ai_decision.action || '?'}</code></span>`;
                if (s.ai_decision.element_id) {
                    html += `<span class="step-meta-item">🎯 Element: <code>#${s.ai_decision.element_id}</code></span>`;
                }
                if (s.ai_decision.reasoning) {
                    html += `<span class="step-meta-item">💡 ${escapeHtml(s.ai_decision.reasoning.substring(0, 80))}</span>`;
                }
            }

            if (s.test_data) {
                html += `<span class="step-meta-item">📝 Data: <code>${escapeHtml(s.test_data)}</code></span>`;
            }
            if (s.expected_result) {
                html += `<span class="step-meta-item">✅ Expected: <code>${escapeHtml(s.expected_result)}</code></span>`;
            }
            html += `</div>`;

            if (s.error) {
                html += `<div class="step-error">⚠️ ${escapeHtml(s.error)}</div>`;
            }

            if (s.screenshot) {
                html += `<div style="margin-top: 8px;">
                    <a href="/download/${currentJobId}/${s.screenshot}" target="_blank" class="template-link" style="margin: 0;">
                        📸 View Screenshot
                    </a>
                </div>`;
            }

            html += `</div>`;
        }

        html += `</div>`;
    }

    container.innerHTML = html;
    container.classList.remove('hidden');
}

function statusIcon(status) {
    switch (status) {
        case 'passed': return '✅';
        case 'failed': return '❌';
        case 'skipped': return '⏭️';
        default: return '❓';
    }
}

// ─── View Toggle ──────────────────────────────────────────
function showView(name) {
    document.getElementById('view-run').classList.toggle('hidden', name !== 'run');
    document.getElementById('view-history').classList.toggle('hidden', name !== 'history');
}

// ─── History ──────────────────────────────────────────────
async function loadHistory(page = 1) {
    historyPage = page;

    try {
        const resp = await fetch(`/api/functional/history?page=${page}&limit=${HISTORY_LIMIT}`);
        const data = await resp.json();
        const tbody = document.getElementById('history-list');
        tbody.innerHTML = '';

        if (!data.jobs || data.jobs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color: var(--muted); padding: 30px;">No functional test history yet.</td></tr>';
            return;
        }

        for (const job of data.jobs) {
            const date = job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A';
            const result = job.result || {};
            const total = result.total || result.summary?.total_steps || 0;
            const passed = result.passed || result.summary?.total_passed || 0;
            const failed = result.failed || result.summary?.total_failed || 0;
            const url = job.target_url || job.sitemap_url || 'N/A';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="checkbox" name="job_select" value="${job.job_id}"></td>
                <td style="font-size: 0.85rem;">${date}</td>
                <td style="font-size: 0.85rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(url)}">${escapeHtml(url.substring(0, 40))}</td>
                <td><span style="color: #a78bfa; font-weight: 600;">${total}</span></td>
                <td><span style="color: #34d399; font-weight: 600;">${passed}</span></td>
                <td><span style="color: #f87171; font-weight: 600;">${failed}</span></td>
                <td>
                    ${result.pdf_report_url ? `<a href="${result.pdf_report_url}" class="btn-download-issue" download>PDF</a>` : ''}
                    <button onclick="viewHistoryResult('${job.job_id}')" class="btn-download-issue" style="cursor: pointer;">View</button>
                </td>`;
            tbody.appendChild(row);
        }

        // Pagination
        const paginationDiv = document.getElementById('pagination');
        const totalPages = Math.ceil(data.total / HISTORY_LIMIT);
        paginationDiv.innerHTML = `
            <span style="color: var(--muted); font-size: 0.85rem;">Page ${page} of ${totalPages} (${data.total} total)</span>
            <div style="display: flex; gap: 8px;">
                ${page > 1 ? `<button class="btn-secondary" style="font-size: 12px; padding: 4px 12px;" onclick="loadHistory(${page - 1})">← Prev</button>` : ''}
                ${page < totalPages ? `<button class="btn-secondary" style="font-size: 12px; padding: 4px 12px;" onclick="loadHistory(${page + 1})">Next →</button>` : ''}
            </div>`;

    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

async function viewHistoryResult(jobId) {
    try {
        const resp = await fetch(`/api/status/${jobId}`);
        const data = await resp.json();
        if (data && data.result) {
            currentJobId = jobId;
            showView('run');
            renderResults(data.result);
        } else {
            toast('No results found for this job', true);
        }
    } catch (e) {
        toast('Failed to load result', true);
    }
}

async function deleteSelected() {
    const checkboxes = document.querySelectorAll('input[name="job_select"]:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);

    if (ids.length === 0) {
        toast('No jobs selected', true);
        return;
    }

    try {
        await fetch('/api/functional/history', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_ids: ids })
        });
        toast(`Deleted ${ids.length} job(s)`);
        loadHistory(historyPage);
    } catch (e) {
        toast('Failed to delete', true);
    }
}

function toggleAll(checkbox) {
    document.querySelectorAll('input[name="job_select"]').forEach(cb => cb.checked = checkbox.checked);
}

// ─── Toast ────────────────────────────────────────────────
function toast(msg, isError = false) {
    const toastEl = document.getElementById('toast');
    toastEl.textContent = msg;
    toastEl.className = 'toast' + (isError ? ' error' : '');
    setTimeout(() => toastEl.classList.add('hidden'), 4000);
}

// ─── Utilities ────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}
