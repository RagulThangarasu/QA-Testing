/**
 * HTML Semantic Validator — Frontend Logic
 * Handles form submission, polling, result rendering, and history management.
 */

(function () {
    'use strict';

    // ─── DOM References ───
    const form = document.getElementById('semanticForm');
    const loader = document.getElementById('loader');
    const progressFill = document.getElementById('progressFill');
    const statusText = document.getElementById('statusText');
    const resultsDiv = document.getElementById('results');
    const viewRun = document.getElementById('view-run');
    const viewHistory = document.getElementById('view-history');
    const navHistory = document.getElementById('nav-history');
    const navRun = document.getElementById('nav-run');
    const btnClear = document.getElementById('btn-clear');
    const toast = document.getElementById('toast');

    let currentJobId = null;
    let pollTimer = null;
    let currentPage = 1;
    let activeCategory = 'all';

    // ─── Navigation ───
    navHistory.addEventListener('click', e => {
        e.preventDefault();
        viewRun.classList.add('hidden');
        viewHistory.classList.remove('hidden');
        loadHistory();
    });

    navRun.addEventListener('click', e => {
        e.preventDefault();
        viewHistory.classList.add('hidden');
        viewRun.classList.remove('hidden');
    });

    btnClear.addEventListener('click', () => {
        resultsDiv.classList.add('hidden');
        resultsDiv.innerHTML = '';
        loader.classList.add('hidden');
        form.reset();
    });

    // ─── Form Submit ───
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const inputType = document.querySelector('input[name="inputType"]:checked')?.value || 'url';

        let payload = {};
        if (inputType === 'sitemap') {
            const sitemapUrl = document.getElementById('sitemap').value.trim();
            if (!sitemapUrl) { showToast('Please enter a sitemap URL', true); return; }
            payload = { input_type: 'sitemap', sitemap_url: sitemapUrl };
        } else {
            const url = document.getElementById('url').value.trim();
            if (!url) { showToast('Please enter a URL', true); return; }
            payload = { page_url: url };
        }

        resultsDiv.classList.add('hidden');
        resultsDiv.innerHTML = '';
        loader.classList.remove('hidden');
        progressFill.style.width = '0%';
        statusText.textContent = '0% - Starting...';

        try {
            const res = await fetch('/api/semantic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.error) {
                showToast(data.error, true);
                loader.classList.add('hidden');
                return;
            }

            currentJobId = data.job_id;
            pollStatus();
        } catch (err) {
            showToast('Request failed: ' + err.message, true);
            loader.classList.add('hidden');
        }
    });

    // ─── Poll Status ───
    function pollStatus() {
        if (!currentJobId) return;

        pollTimer = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${currentJobId}`);
                const data = await res.json();

                if (!data) return;

                const progress = data.progress || 0;
                const step = data.step || 'Processing...';
                progressFill.style.width = progress + '%';
                statusText.textContent = `${progress}% - ${step}`;

                if (data.status === 'completed') {
                    clearInterval(pollTimer);
                    loader.classList.add('hidden');
                    if (data.result && data.result.batch) {
                        renderBatchResults(data.result);
                    } else {
                        renderResults(data.result);
                    }
                } else if (data.status === 'failed') {
                    clearInterval(pollTimer);
                    loader.classList.add('hidden');
                    showToast('Validation failed: ' + (data.error || 'Unknown error'), true);
                }
            } catch (err) {
                clearInterval(pollTimer);
                loader.classList.add('hidden');
                showToast('Polling failed: ' + err.message, true);
            }
        }, 800);
    }

    // ─── Render Results ───
    function renderResults(result) {
        if (!result) return;
        resultsDiv.classList.remove('hidden');

        const score = result.score || 0;
        const grade = score >= 90 ? 'Excellent' : score >= 75 ? 'Good' : score >= 50 ? 'Needs Work' : 'Poor';
        const scoreColor = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

        let html = '';

        // ─── Score + Stats ───
        html += `
        <div style="text-align: center; margin-bottom: 20px;">
            <div class="score-circle" style="--score-pct: ${score}; --score-color: ${scoreColor};">
                <span class="score-value">${score}</span>
                <span class="score-label">${grade}</span>
            </div>
            <p style="color: var(--muted); margin-top: 10px; font-size: 0.88rem;">Semantic Score for <strong style="color: var(--fg);">${escapeHtml(result.url)}</strong></p>
        </div>`;

        html += `
        <div class="stat-cards">
            <div class="stat-card total">
                <span class="stat-value">${result.total_issues}</span>
                <span class="stat-label">Total Issues</span>
            </div>
            <div class="stat-card critical">
                <span class="stat-value">${result.critical}</span>
                <span class="stat-label">Critical</span>
            </div>
            <div class="stat-card warning">
                <span class="stat-value">${result.warnings}</span>
                <span class="stat-label">Warnings</span>
            </div>
            <div class="stat-card info">
                <span class="stat-value">${result.info}</span>
                <span class="stat-label">Informational</span>
            </div>
        </div>`;

        // ─── Download buttons ───
        html += `<div class="downloads" style="margin-bottom: 16px;">`;
        if (result.pdf_report_url) {
            html += `<a href="${result.pdf_report_url}" download>📄 Download PDF Report</a>`;
        }
        html += `</div>`;

        // ─── Element Summary ───
        const summary = result.element_summary || {};
        if (summary) {
            html += `
            <div class="summary-grid">
                <div class="summary-box">
                    <h4>📊 Page Stats</h4>
                    <p style="color: var(--fg); font-size: 0.9rem;">Total Elements: <strong>${summary.total_elements || 0}</strong></p>
                    <p style="color: var(--fg); font-size: 0.9rem;">Semantic Ratio: <strong>${summary.semantic_ratio || 0}%</strong></p>
                    <div class="ratio-bar">
                        <div class="ratio-fill" style="width: ${summary.semantic_ratio || 0}%;"></div>
                    </div>
                    <p style="color: #6b7280; font-size: 0.75rem; margin-top: 6px;">% of elements using semantic tags</p>
                </div>
                <div class="summary-box">
                    <h4>📑 Heading Structure</h4>
                    <div class="element-tags">
                        ${Object.entries(summary.headings || {}).map(([tag, count]) =>
                `<span class="element-tag">&lt;${tag}&gt; <span class="tag-count">× ${count}</span></span>`
            ).join('') || '<span style="color: #6b7280; font-size: 0.84rem;">No headings found</span>'}
                    </div>
                </div>
                <div class="summary-box">
                    <h4>🏗️ Semantic Elements</h4>
                    <div class="element-tags">
                        ${Object.entries(summary.semantic_elements || {}).slice(0, 12).map(([tag, count]) =>
                `<span class="element-tag">&lt;${tag}&gt; <span class="tag-count">× ${count}</span></span>`
            ).join('') || '<span style="color: #6b7280; font-size: 0.84rem;">None found</span>'}
                    </div>
                </div>
            </div>`;
        }

        // ─── Recommended Heading Structure ───
        const recHeadings = result.recommended_headings || {};
        const currentOutline = recHeadings.current_outline || [];
        const recommended = recHeadings.recommended || [];

        if (currentOutline.length > 0 || recommended.length > 0) {
            html += `<div style="margin: 20px 0;">
                <h2 style="margin-bottom: 14px;">📐 Heading Structure</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">`;

            // Current outline
            html += `<div class="summary-box">
                <h4>📄 Current Outline</h4>`;
            if (currentOutline.length > 0) {
                currentOutline.forEach(h => {
                    const indent = (h.level - 1) * 18;
                    const tagColor = h.level === 1 ? '#a78bfa' : h.level === 2 ? '#60a5fa' : '#34d399';
                    html += `<div style="padding: 4px 0 4px ${indent}px; display: flex; align-items: center; gap: 8px;">
                        <code style="background: #1e293b; color: ${tagColor}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; min-width: 30px; text-align: center;">&lt;${h.tag}&gt;</code>
                        <span style="font-size: 0.85rem; color: var(--fg);">${escapeHtml(h.text)}</span>
                    </div>`;
                });
            } else {
                html += `<p style="color: #6b7280; font-size: 0.85rem; font-style: italic;">No headings found on the page.</p>`;
            }
            html += `</div>`;

            // Recommended structure
            html += `<div class="summary-box" style="border-color: #10b981;">
                <h4>✅ Recommended Structure</h4>`;
            if (recommended.length > 0) {
                recommended.forEach(h => {
                    const indent = (h.level - 1) * 18;
                    const tagColor = h.level === 1 ? '#a78bfa' : h.level === 2 ? '#60a5fa' : '#34d399';
                    html += `<div style="padding: 4px 0 4px ${indent}px; display: flex; align-items: flex-start; gap: 8px;" title="${escapeHtml(h.reason || '')}">
                        <code style="background: #0f3d2b; color: ${tagColor}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; min-width: 30px; text-align: center;">&lt;${h.tag}&gt;</code>
                        <div>
                            <span style="font-size: 0.85rem; color: var(--fg);">${escapeHtml(h.text)}</span>
                            <div style="font-size: 0.72rem; color: #6b7280; margin-top: 1px;">${escapeHtml(h.reason || '')}</div>
                        </div>
                    </div>`;
                });
            }
            html += `</div>`;

            html += `</div></div>`;
        }

        // ─── Category Filter Pills ───
        const categories = result.category_counts || {};
        if (Object.keys(categories).length > 0) {
            html += `<div class="results-header">
                <h2>🔎 Issues Found</h2>
            </div>`;
            html += `<div class="category-pills">
                <span class="category-pill active" data-category="all" onclick="filterCategory(this, 'all')">
                    All <span class="pill-count">${result.total_issues}</span>
                </span>`;
            for (const [cat, count] of Object.entries(categories).sort((a, b) => b[1] - a[1])) {
                html += `<span class="category-pill" data-category="${escapeHtml(cat)}" onclick="filterCategory(this, '${escapeHtml(cat)}')">
                    ${escapeHtml(cat)} <span class="pill-count">${count}</span>
                </span>`;
            }
            html += '</div>';
        }

        // ─── Issue Cards ───
        const issues = result.issues || [];
        if (issues.length > 0) {
            html += '<div id="issues-container">';
            issues.forEach((issue, idx) => {
                html += renderIssueCard(issue, idx);
            });
            html += '</div>';
        } else {
            html += `<div style="text-align: center; padding: 40px; color: #10b981;">
                <div style="font-size: 3rem; margin-bottom: 10px;">✅</div>
                <h3>Perfect Semantic Structure!</h3>
                <p style="color: var(--muted);">No issues found. Your HTML follows semantic best practices.</p>
            </div>`;
        }

        resultsDiv.innerHTML = html;

        // Animate issue cards with stagger
        setTimeout(() => {
            document.querySelectorAll('.issue-card').forEach((card, i) => {
                card.style.animationDelay = `${i * 0.05}s`;
            });
        }, 50);
    }

    function renderIssueCard(issue, index) {
        const sev = issue.severity || 'info';
        const sevIcon = sev === 'critical' ? '🔴' : sev === 'warning' ? '🟡' : '🔵';
        const elementStr = issue.element ? escapeHtml(issue.element) : '';
        const wcag = issue.wcag || '—';

        return `
        <div class="issue-card ${sev}" data-category="${escapeHtml(issue.category || 'Other')}" style="animation-delay: ${index * 0.05}s;">
            <div class="issue-header">
                <span class="severity-badge ${sev}">${sevIcon} ${sev}</span>
                <span class="issue-message">${escapeHtml(issue.message)}</span>
            </div>
            <div class="issue-detail">${escapeHtml(issue.detail || '')}</div>
            <div class="issue-meta">
                ${elementStr ? `<span class="issue-meta-item">Element: <code>${elementStr}</code></span>` : ''}
                ${wcag !== '—' ? `<span class="issue-meta-item">WCAG: <span class="wcag-badge">${wcag}</span></span>` : ''}
                <span class="issue-meta-item" style="color: #4b5563;">📂 ${escapeHtml(issue.category || 'Other')}</span>
            </div>
        </div>`;
    }

    // ─── Render Batch Results (Sitemap) ───
    function renderBatchResults(result) {
        if (!result) return;
        resultsDiv.classList.remove('hidden');

        const pages = result.pages || [];
        const avgScore = result.average_score || 0;
        const totalPages = result.total_pages || 0;
        const totalIssues = result.total_issues || 0;
        const totalCritical = result.total_critical || 0;
        const totalWarnings = result.total_warnings || 0;
        const totalInfo = result.total_info || 0;

        const grade = avgScore >= 90 ? 'Excellent' : avgScore >= 75 ? 'Good' : avgScore >= 50 ? 'Needs Work' : 'Poor';
        const scoreColor = avgScore >= 80 ? '#10b981' : avgScore >= 60 ? '#f59e0b' : '#ef4444';

        let html = '';

        html += `
        <div style="text-align: center; margin-bottom: 20px;">
            <div class="score-circle" style="--score-pct: ${avgScore}; --score-color: ${scoreColor};">
                <span class="score-value">${avgScore}</span>
                <span class="score-label">${grade}</span>
            </div>
            <p style="color: var(--muted); margin-top: 10px; font-size: 0.88rem;">Average Semantic Score across <strong style="color: var(--fg);">${totalPages} pages</strong></p>
        </div>`;

        html += `
        <div class="stat-cards">
            <div class="stat-card total">
                <span class="stat-value">${totalPages}</span>
                <span class="stat-label">Pages Scanned</span>
            </div>
            <div class="stat-card critical">
                <span class="stat-value">${totalCritical}</span>
                <span class="stat-label">Critical</span>
            </div>
            <div class="stat-card warning">
                <span class="stat-value">${totalWarnings}</span>
                <span class="stat-label">Warnings</span>
            </div>
            <div class="stat-card info">
                <span class="stat-value">${totalInfo}</span>
                <span class="stat-label">Informational</span>
            </div>
        </div>`;

        // Download report
        html += `<div class="downloads" style="margin-bottom: 16px;">`;
        if (result.pdf_report_url) {
            html += `<a href="${result.pdf_report_url}" download>📄 Download PDF Report</a>`;
        }
        html += `</div>`;

        // Per-page table
        html += `
        <h2 style="margin-top: 20px;">📋 Per-Page Results</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>URL</th>
                    <th>Score</th>
                    <th>Critical</th>
                    <th>Warnings</th>
                    <th>Info</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>`;

        pages.forEach((page, idx) => {
            const pScore = page.score ?? 'N/A';
            const pColor = typeof pScore === 'number' ? (pScore >= 80 ? '#10b981' : pScore >= 60 ? '#f59e0b' : '#ef4444') : '#6b7280';

            html += `
            <tr>
                <td>${idx + 1}</td>
                <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(page.url)}">${escapeHtml(page.url)}</td>
                <td><span style="color: ${pColor}; font-weight: 700;">${pScore}</span></td>
                <td style="color: #ef4444;">${page.critical || 0}</td>
                <td style="color: #f59e0b;">${page.warnings || 0}</td>
                <td style="color: #3b82f6;">${page.info || 0}</td>
                <td><button class="btn-download-issue" onclick="expandPageDetail(${idx})">👁️ View</button></td>
            </tr>
            <tr id="page-detail-${idx}" class="hidden">
                <td colspan="7" id="page-detail-content-${idx}" style="padding: 0;"></td>
            </tr>`;
        });

        html += `</tbody></table>`;

        resultsDiv.innerHTML = html;

        // Store pages data for expand
        window._batchPages = pages;
    }

    // Expand a single page's detail inline
    window.expandPageDetail = function (idx) {
        const row = document.getElementById(`page-detail-${idx}`);
        const content = document.getElementById(`page-detail-content-${idx}`);
        if (row.classList.contains('hidden')) {
            row.classList.remove('hidden');
            const page = window._batchPages[idx];
            if (page) {
                let issueHtml = `<div style="padding: 12px; background: #0f1930; border-radius: 8px;">`;
                const issues = page.issues || [];
                if (issues.length > 0) {
                    issues.forEach((issue, i) => {
                        issueHtml += renderIssueCard(issue, i);
                    });
                } else {
                    issueHtml += `<p style="color: #10b981; text-align: center; padding: 16px;">✅ No issues found</p>`;
                }
                issueHtml += `</div>`;
                content.innerHTML = issueHtml;
                // Trigger animations
                setTimeout(() => {
                    content.querySelectorAll('.issue-card').forEach((card, i) => {
                        card.style.animationDelay = `${i * 0.05}s`;
                    });
                }, 50);
            }
        } else {
            row.classList.add('hidden');
        }
    };

    // ─── Category Filter ───
    window.filterCategory = function (el, category) {
        activeCategory = category;

        // Update pills
        document.querySelectorAll('.category-pill').forEach(p => p.classList.remove('active'));
        el.classList.add('active');

        // Filter cards
        document.querySelectorAll('.issue-card').forEach(card => {
            if (category === 'all' || card.dataset.category === category) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    };

    // ─── History ───
    async function loadHistory(page = 1) {
        currentPage = page;
        try {
            const res = await fetch(`/api/semantic/history?page=${page}&limit=10`);
            const data = await res.json();
            renderHistory(data);
        } catch (err) {
            showToast('Failed to load history: ' + err.message, true);
        }
    }

    function renderHistory(data) {
        const list = document.getElementById('history-list');
        const pagination = document.getElementById('pagination');

        if (!data.jobs || data.jobs.length === 0) {
            list.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--muted);">No history yet. Run your first semantic validation!</td></tr>';
            pagination.innerHTML = '';
            return;
        }

        list.innerHTML = data.jobs.map(job => {
            const date = job.timestamp ? new Date(job.timestamp).toLocaleString() : 'N/A';
            const url = job.page_url || 'N/A';
            const score = job.result?.score ?? 'N/A';
            const totalIssues = job.result?.total_issues ?? 'N/A';
            const scoreColor = typeof score === 'number' ? (score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444') : '#6b7280';

            let actions = '';
            if (job.result?.pdf_report_url) {
                actions += `<a href="${job.result.pdf_report_url}" download class="btn-download-issue">📄 PDF</a> `;
            }
            if (job.status === 'completed') {
                actions += `<button class="btn-download-issue" onclick="viewHistoryResult('${job.job_id}')">👁️ View</button>`;
            }

            return `<tr>
                <td><input type="checkbox" class="job-checkbox" value="${job.job_id}"></td>
                <td>${date}</td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(url)}</td>
                <td><span style="color: ${scoreColor}; font-weight: 600;">${score}</span></td>
                <td>${totalIssues}</td>
                <td>${actions}</td>
            </tr>`;
        }).join('');

        // Pagination
        const totalPages = Math.ceil(data.total / data.limit);
        let paginationHtml = '';
        if (totalPages > 1) {
            paginationHtml += `<span style="color: var(--muted);">Page ${data.page} of ${totalPages}</span>`;
            paginationHtml += '<div style="display: flex; gap: 8px;">';
            if (data.page > 1) {
                paginationHtml += `<button class="btn-secondary" style="font-size: 13px; padding: 4px 12px;" onclick="loadHistoryPage(${data.page - 1})">← Prev</button>`;
            }
            if (data.page < totalPages) {
                paginationHtml += `<button class="btn-secondary" style="font-size: 13px; padding: 4px 12px;" onclick="loadHistoryPage(${data.page + 1})">Next →</button>`;
            }
            paginationHtml += '</div>';
        }

        // Delete button
        paginationHtml = `<button class="btn-reject" style="font-size: 13px; padding: 4px 12px;" onclick="deleteSelected()">🗑️ Delete Selected</button>` + paginationHtml;
        pagination.innerHTML = paginationHtml;
    }

    window.loadHistoryPage = function (page) {
        loadHistory(page);
    };

    window.viewHistoryResult = async function (jobId) {
        try {
            const res = await fetch(`/api/status/${jobId}`);
            const data = await res.json();
            if (data && data.result) {
                viewHistory.classList.add('hidden');
                viewRun.classList.remove('hidden');
                renderResults(data.result);
            }
        } catch (err) {
            showToast('Failed to load result', true);
        }
    };

    window.toggleAll = function (el) {
        document.querySelectorAll('.job-checkbox').forEach(cb => cb.checked = el.checked);
    };

    window.deleteSelected = async function () {
        const selected = [...document.querySelectorAll('.job-checkbox:checked')].map(cb => cb.value);
        if (selected.length === 0) {
            showToast('No items selected');
            return;
        }

        if (!confirm(`Delete ${selected.length} item(s)?`)) return;

        try {
            await fetch('/api/semantic/history', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_ids: selected })
            });
            showToast(`Deleted ${selected.length} item(s)`);
            loadHistory(currentPage);
        } catch (err) {
            showToast('Delete failed: ' + err.message, true);
        }
    };

    // ─── Utilities ───
    function showToast(msg, isError = false) {
        toast.textContent = msg;
        toast.className = isError ? 'toast error' : 'toast';
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 4000);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

})();
