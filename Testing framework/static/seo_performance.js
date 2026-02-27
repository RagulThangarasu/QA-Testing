const form = document.getElementById("seoPerformanceForm");
const loader = document.getElementById("loader");
const progressFill = document.getElementById("progressFill");
const statusText = document.getElementById("statusText");
const resultsDiv = document.getElementById("results");
const toast = document.getElementById("toast");
const viewRun = document.getElementById("view-run");
const viewHistory = document.getElementById("view-history");
const navHistory = document.getElementById("nav-history");
const navRun = document.getElementById("nav-run");
const historyList = document.getElementById("history-list");

let currentPage = 1;
const LIMIT = 10;

function showToast(msg, isError = false) {
    toast.textContent = msg;
    toast.classList.remove("hidden");
    toast.classList.toggle("error", isError);
    setTimeout(() => toast.classList.add("hidden"), 4000);
}

function switchView(view) {
    if (view === "run") {
        viewRun.classList.remove("hidden");
        viewHistory.classList.add("hidden");
    } else if (view === "history") {
        viewRun.classList.add("hidden");
        viewHistory.classList.remove("hidden");
        loadHistory();
    }
}

navHistory.addEventListener("click", (e) => {
    e.preventDefault();
    switchView("history");
});

navRun.addEventListener("click", (e) => {
    e.preventDefault();
    switchView("run");
});

document.getElementById("btn-clear").addEventListener("click", (e) => {
    e.preventDefault();
    if (confirm("Clear current results and start a new session?")) {
        location.reload();
    }
});

function getScoreColor(score) {
    if (score >= 95) return '#4effa0';
    if (score >= 50) return '#fbbf24';
    return 'var(--error)';
}

async function loadHistory(page = 1) {
    currentPage = page;
    historyList.innerHTML = "<tr><td colspan='8'>Loading...</td></tr>";
    document.getElementById("pagination").innerHTML = "";

    try {
        const res = await fetch(`/api/seo-performance/history?page=${page}&limit=${LIMIT}`);
        const data = await res.json();

        const jobs = Array.isArray(data) ? data : data.jobs;
        const total = data.total !== undefined ? data.total : jobs.length;



        if (jobs.length === 0) {
            historyList.innerHTML = "<tr><td colspan='8'>No history yet.</td></tr>";
            return;
        }

        historyList.innerHTML = jobs.map(job => {
            const date = new Date(job.timestamp).toLocaleString();
            const testType = job.test_type || "both";
            const testTypeLabel = testType === "both" ? "SEO & Performance" :
                testType === "seo" ? "SEO Only" : "Performance Only";

            // Handle display name (URL or Filename)
            let displayName = job.page_url;
            if (!displayName && job.file_name) {
                displayName = `📄 ${job.file_name}`;
            }
            if (!displayName) displayName = "Unknown";

            // Handle Scores / Status
            let col1 = "-";
            let col2 = "-";

            if (job.status === 'failed') {
                col1 = `<span style="color: var(--error);">Failed</span>`;
            } else if (job.result?.total_processed !== undefined) {
                // Batch Job
                col1 = `<span style="color: var(--accent);">Batch (${job.result.total_processed} URLs)</span>`;
            } else {
                // Single Page Job
                const seoScore = job.result?.seo_score;
                const perfScore = job.result?.performance_score;

                if (seoScore !== undefined && seoScore !== null) {
                    col1 = `<span style="color: ${getScoreColor(seoScore)}">${seoScore}/100</span>`;
                }
                if (perfScore !== undefined && perfScore !== null) {
                    col2 = `<span style="color: ${getScoreColor(perfScore)}">${perfScore}/100</span>`;
                }
            }

            const reportUrl = job.result?.report_url || "";
            const pdfUrl = job.result?.pdf_report_url || "";



            return `
                <tr>
                    <td><input type="checkbox" class="history-checkbox" value="${job.job_id}"></td>
                    <td>${date}</td>
                    <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${displayName}">${displayName}</td>
                    <td>${testTypeLabel}</td>
                    <td>${col1}</td>
                    <td>${col2}</td>
                    <td>
                        ${pdfUrl ? `<a href="${reportUrl}" class="btn-secondary" style="padding: 4px 8px; font-size: 11px;" title="Download Excel">Excel</a>` : '-'}
                    </td>
                    <td>
                        ${pdfUrl ? `<a href="${pdfUrl}" class="btn-secondary" style="padding: 4px 8px; font-size: 11px;" title="Download PDF">PDF</a>` : (reportUrl ? `<a href="${reportUrl}" class="btn-secondary" style="padding: 4px 8px; font-size: 11px;" title="Download PDF">PDF</a>` : '-')}
                    </td>
                </tr>
            `;
        }).join("");

        renderPagination(total, page);

    } catch (err) {
        console.error(err);
        historyList.innerHTML = "<tr><td colspan='8'>Error loading history.</td></tr>";
    }
}

function renderPagination(total, page) {
    const totalPages = Math.ceil(total / LIMIT) || 1;

    const paginationDiv = document.getElementById("pagination");

    const prevDisabled = page <= 1 ? "disabled" : "";
    const nextDisabled = page >= totalPages ? "disabled" : "";

    paginationDiv.innerHTML = `
        <button class="btn-reject" style="font-size: 13px; padding: 4px 12px;" onclick="deleteSelected()">🗑️ Delete Selected</button>
        <span>Page ${page} of ${totalPages}</span>
        <div style="display: flex; gap: 8px;">
            <button class="btn-secondary" ${prevDisabled} onclick="loadHistory(${page - 1})" style="padding: 5px 10px; font-size: 14px;">&larr; Previous</button>
            <button class="btn-secondary" ${nextDisabled} onclick="loadHistory(${page + 1})" style="padding: 5px 10px; font-size: 14px;">Next &rarr;</button>
        </div>
    `;
}

window.toggleAll = function (checkbox) {
    document.querySelectorAll(".history-checkbox").forEach(cb => {
        cb.checked = checkbox.checked;
    });
};

async function deleteSelected() {
    const selected = Array.from(document.querySelectorAll(".history-checkbox:checked"));
    if (selected.length === 0) {
        showToast("No items selected.", true);
        return;
    }

    if (!confirm(`Delete ${selected.length} record(s)?`)) return;

    const ids = selected.map(cb => cb.value);

    try {
        const res = await fetch("/api/seo-performance/history", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_ids: ids })
        });

        if (res.ok) {
            showToast("Records deleted.");
            const allOnPage = document.querySelectorAll(".history-checkbox").length;
            if (allOnPage === ids.length && currentPage > 1) {
                loadHistory(currentPage - 1);
            } else {
                loadHistory(currentPage);
            }
        } else {
            showToast("Delete failed.", true);
        }
    } catch (e) {
        console.error(e);
        showToast("Error deleting records.", true);
    }
}

// Toggle Input Type
// Toggle Input Type
window.toggleInputType = function () {
    const type = document.querySelector('input[name="inputType"]:checked').value;
    const urlContainer = document.getElementById("urlInputContainer");
    const sitemapContainer = document.getElementById("sitemapInputContainer");
    const fileContainer = document.getElementById("fileInputContainer");

    const urlInput = document.getElementById("url");
    const sitemapInput = document.getElementById("sitemap_url");
    const fileInput = document.getElementById("file");

    // Reset all
    urlContainer.classList.add("hidden");
    sitemapContainer.classList.add("hidden");
    fileContainer.classList.add("hidden");

    urlInput.required = false;
    sitemapInput.required = false;
    fileInput.required = false;

    if (type === "url") {
        urlContainer.classList.remove("hidden");
        urlInput.required = true;
        sitemapInput.value = "";
        fileInput.value = "";
    } else if (type === "sitemap") {
        sitemapContainer.classList.remove("hidden");
        sitemapInput.required = true;
        urlInput.value = "";
        fileInput.value = "";
    } else {
        fileContainer.classList.remove("hidden");
        fileInput.required = true;
        urlInput.value = "";
        sitemapInput.value = "";
    }
}

// File Upload UI
const fileInput = document.getElementById("file");
const fileText = document.getElementById("file-text");
const dropZone = document.getElementById("drop-zone");

if (fileInput) {
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            fileText.textContent = fileInput.files[0].name;
            fileText.classList.add("active");
            dropZone.classList.add("dragover");
        } else {
            fileText.textContent = "Click or Drop file here";
            fileText.classList.remove("active");
            dropZone.classList.remove("dragover");
        }
    });

    fileInput.addEventListener("dragenter", () => dropZone.classList.add("dragover"));
    fileInput.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    fileInput.addEventListener("drop", () => dropZone.classList.remove("dragover"));
}


async function pollStatus(jobId) {
    try {
        const res = await fetch(`/api/status/${jobId}`);
        if (!res.ok) {
            loader.classList.add("hidden");
            showToast("Job not found.", true);
            return;
        }
        const data = await res.json();

        if (data.progress !== undefined) {
            progressFill.style.width = `${data.progress}%`;
            statusText.textContent = `${data.progress}% - ${data.step}`;
        }

        if (data.status === "completed") {
            loader.classList.add("hidden");
            resultsDiv.classList.remove("hidden");

            const result = data.result;

            // Check if it's a batch result (has report_url but maybe separate structure)
            // Or if it's a single page result

            let resultHTML = `<div style="background: rgba(30, 200, 100, 0.1); padding: 20px; border-radius: 8px; border: 1px solid #10b981;">`;
            resultHTML += `<h3 style="color: #4effa0; margin-top: 0;">Analysis Complete!</h3>`;

            if (result.total_processed !== undefined) {
                // Batch Result
                resultHTML += `<p>Processed <strong>${result.total_processed}</strong> URLs.</p>`;
                resultHTML += `<p>Download the consolidated reports below:</p>`;
                resultHTML += `<div style="display:flex; gap:10px; margin-top:10px;">`;
                resultHTML += `<a href="${result.report_url}" class="btn-secondary" style="padding: 10px 20px; text-decoration: none;">Download Excel Report</a>`;

                if (result.pdf_report_url) {
                    resultHTML += `<a href="${result.pdf_report_url}" class="btn-secondary" style="padding: 10px 20px; text-decoration: none;">Download PDF Summary</a>`;
                }
                resultHTML += `</div>`;
            } else {
                // Single Page Result
                resultHTML += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">`;

                if (result.seo_score !== undefined && result.seo_score !== null) {
                    const seoColor = getScoreColor(result.seo_score);
                    resultHTML += `
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px;">
                            <p style="margin: 0; color: var(--muted); font-size: 14px;">SEO Score</p>
                            <p style="margin: 5px 0 0 0; font-size: 32px; font-weight: bold; color: ${seoColor};">${result.seo_score}/100</p>
                        </div>
                    `;
                }

                if (result.performance_score !== undefined && result.performance_score !== null) {
                    if (result.desktop_score !== undefined && result.mobile_score !== undefined) {
                        // Show both
                        const dColor = getScoreColor(result.desktop_score);
                        const mColor = getScoreColor(result.mobile_score);
                        resultHTML += `
                            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px;">
                                <p style="margin: 0; color: var(--muted); font-size: 14px;">Performance (Desktop)</p>
                                <p style="margin: 5px 0 0 0; font-size: 32px; font-weight: bold; color: ${dColor};">${result.desktop_score}/100</p>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px;">
                                <p style="margin: 0; color: var(--muted); font-size: 14px;">Performance (Mobile)</p>
                                <p style="margin: 5px 0 0 0; font-size: 32px; font-weight: bold; color: ${mColor};">${result.mobile_score}/100</p>
                            </div>
                        `;
                    } else {
                        // Show single
                        const perfColor = getScoreColor(result.performance_score);
                        resultHTML += `
                            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px;">
                                <p style="margin: 0; color: var(--muted); font-size: 14px;">Performance Score</p>
                                <p style="margin: 5px 0 0 0; font-size: 32px; font-weight: bold; color: ${perfColor};">${result.performance_score}/100</p>
                            </div>
                        `;
                    }
                }

                if (result.load_time !== undefined && result.load_time !== null) {
                    resultHTML += `
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px;">
                            <p style="margin: 0; color: var(--muted); font-size: 14px;">Load Time</p>
                            <p style="margin: 5px 0 0 0; font-size: 32px; font-weight: bold; color: #4effa0;">${result.load_time}s</p>
                        </div>
                    `;
                }

                resultHTML += `</div>`;

                // Detailed Metrics Section
                if (result.performance_details && result.performance_details.length > 0) {
                    resultHTML += `<h4 style="color: #cbd5e1; margin-top: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px;">Core Web Vitals & Metrics</h4>`;
                    resultHTML += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; margin-bottom: 20px;">`;

                    result.performance_details.forEach(metric => {
                        let color = '#4effa0'; // Default green
                        if (metric.score !== undefined) {
                            if (metric.score < 0.5) color = '#ff4444'; // Red
                            else if (metric.score < 0.9) color = '#fbbf24'; // Orange
                        }

                        resultHTML += `
                            <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #334155;">
                                <span style="color: #94a3b8; font-size: 0.9em;">${metric.name}</span>
                                <span style="color: ${color}; font-weight: bold;">${metric.displayValue}</span>
                            </div>
                        `;
                    });
                    resultHTML += `</div>`;
                }

                // Recommendations Section
                if (result.recommendations && result.recommendations.length > 0) {
                    resultHTML += `<h4 style="color: #cbd5e1; margin-top: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px;">Improvement Opportunities</h4>`;
                    resultHTML += `<ul style="list-style: none; padding: 0;">`;
                    result.recommendations.forEach(rec => {
                        resultHTML += `
                            <li style="margin-bottom: 10px; background: rgba(51, 65, 85, 0.3); padding: 10px; border-radius: 6px;">
                                <div style="color: #e2e8f0; font-weight: 500;">${rec.title}</div>
                                <div style="color: #94a3b8; font-size: 0.85em; margin-top: 4px;">${rec.description}</div>
                            </li>`;
                    });
                    resultHTML += `</ul>`;
                }
                resultHTML += `<p>Download the detailed PDF report below:</p>`;
                resultHTML += `<a href="${result.report_url}" class="btn-secondary" style="display: inline-block; padding: 10px 20px; text-decoration: none; margin-top: 10px;">Download PDF Report</a>`;
            }

            resultHTML += `</div>`;
            resultsDiv.innerHTML = resultHTML;
            showToast("Analysis completed.");

        } else if (data.status === "failed") {
            loader.classList.add("hidden");
            resultsDiv.classList.remove("hidden");

            const errorMsg = data.error || "Job failed.";
            resultsDiv.innerHTML = `
                <div style="background: rgba(255, 107, 107, 0.1); padding: 20px; border-radius: 8px; border: 1px solid var(--error);">
                    <h3 style="color: var(--error); margin-top: 0;">Error</h3>
                    <p style="white-space: pre-wrap; font-family: monospace; font-size: 14px;">${errorMsg}</p>
                </div>
            `;
            showToast("Job failed. See details above.", true);
        } else {
            setTimeout(() => pollStatus(jobId), 1000);
        }
    } catch (err) {
        console.error(err);
        loader.classList.add("hidden");
        showToast("Error checking status.", true);
    }
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    // We don't manually construct JSON anymore
    // We send formData directly. 
    // Note: The backend must handle multipart/form-data now.

    resultsDiv.classList.add("hidden");
    loader.classList.remove("hidden");
    progressFill.style.width = "0%";
    statusText.textContent = "0% - Starting...";

    try {
        const res = await fetch("/api/seo-performance", {
            method: "POST",
            body: formData
            // Do NOT set Content-Type header when using FormData, browser does it automatically with boundary
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || "Request failed");
        }

        const { job_id } = await res.json();
        pollStatus(job_id);

    } catch (err) {
        console.error(err);
        loader.classList.add("hidden");
        showToast(err.message, true);
    }
});
