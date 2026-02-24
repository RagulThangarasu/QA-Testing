const form = document.getElementById("accessibilityForm");
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

window.toggleInputType = function () {
    const type = document.querySelector('input[name="inputType"]:checked').value;
    const urlContainer = document.getElementById('urlInputContainer');
    const sitemapContainer = document.getElementById('sitemapInputContainer');
    const urlInput = document.getElementById('url');
    const sitemapInput = document.getElementById('sitemap');

    if (type === 'url') {
        urlContainer.classList.remove('hidden');
        sitemapContainer.classList.add('hidden');
        if (urlInput) urlInput.required = true;
        if (sitemapInput) sitemapInput.required = false;
    } else {
        urlContainer.classList.add('hidden');
        sitemapContainer.classList.remove('hidden');
        if (urlInput) urlInput.required = false;
        if (sitemapInput) sitemapInput.required = true;
    }
};

// Initial call
document.addEventListener("DOMContentLoaded", () => {
    if (document.querySelector('input[name="inputType"]')) {
        toggleInputType();
    }
});

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

// Clear button
document.getElementById("btn-clear").addEventListener("click", (e) => {
    e.preventDefault();
    if (confirm("Clear current results and start a new session?")) {
        location.reload();
    }
});

async function loadHistory(page = 1) {
    currentPage = page;
    historyList.innerHTML = "<tr><td colspan='6'>Loading...</td></tr>";
    document.getElementById("pagination").innerHTML = "";

    try {
        const res = await fetch(`/api/accessibility/history?page=${page}&limit=${LIMIT}`);
        const data = await res.json();

        const jobs = Array.isArray(data) ? data : data.jobs;
        const total = data.total !== undefined ? data.total : jobs.length;



        if (jobs.length === 0) {
            historyList.innerHTML = "<tr><td colspan='6'>No history yet.</td></tr>";
            return;
        }

        historyList.innerHTML = jobs.map(job => {
            const date = new Date(job.timestamp).toLocaleString();
            const wcagLevel = job.wcag_level || "WCAG2AA";
            const issuesCount = job.result?.total_issues || 0;
            const reportUrl = job.result?.report_url || "";

            return `
                <tr>
                    <td><input type="checkbox" class="history-checkbox" value="${job.job_id}"></td>
                    <td>${date}</td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${job.page_url}">${job.page_url}</td>
                    <td>${wcagLevel}</td>
                    <td style="color: ${issuesCount > 0 ? 'var(--error)' : '#4effa0'}">${issuesCount}</td>
                    <td>
                        ${reportUrl ? `<a href="${reportUrl}" class="btn-secondary" style="padding: 5px 10px; font-size: 12px;">Download</a>` : '-'}
                    </td>
                </tr>
            `;
        }).join("");

        renderPagination(total, page);

    } catch (err) {
        console.error(err);
        historyList.innerHTML = "<tr><td colspan='6'>Error loading history.</td></tr>";
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
        const res = await fetch("/api/accessibility/history", {
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
            if (result.total_issues > 0) {
                resultsDiv.innerHTML = `
                    <div style="background: rgba(255, 107, 107, 0.1); padding: 20px; border-radius: 8px; border: 1px solid var(--error);">
                        <h3 style="color: var(--error); margin-top: 0;">Found ${result.total_issues} accessibility issues!</h3>
                        <div style="margin: 15px 0;">
                            <p style="margin: 5px 0;"><strong>Violations:</strong> ${result.violations || 0}</p>
                            <p style="margin: 5px 0;"><strong>Warnings:</strong> ${result.warnings || 0}</p>
                            <p style="margin: 5px 0;"><strong>Notices:</strong> ${result.notices || 0}</p>
                        </div>
                        <p>Download the detailed PDF report below:</p>
                        <a href="${result.report_url}" class="btn-secondary" style="display: inline-block; padding: 10px 20px; text-decoration: none; margin-top: 10px;">Download PDF Report</a>
                    </div>
                `;
            } else {
                resultsDiv.innerHTML = `
                    <div style="background: rgba(30, 200, 100, 0.1); padding: 20px; border-radius: 8px; border: 1px solid #10b981;">
                        <h3 style="color: #4effa0; margin-top: 0;">No accessibility issues found!</h3>
                        <p>Your page meets the selected WCAG standards.</p>
                    </div>
                `;
            }
            showToast("Accessibility test completed.");
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
    const inputType = document.querySelector('input[name="inputType"]:checked').value;

    if (inputType === 'url' && !formData.get("page_url")) {
        showToast("Page URL is required", true);
        return;
    }
    if (inputType === 'sitemap' && !formData.get("sitemap_url")) {
        showToast("Sitemap URL is required", true);
        return;
    }

    const data = {
        input_type: inputType,
        page_url: formData.get("page_url"),
        sitemap_url: formData.get("sitemap_url"),
        wcag_level: formData.get("wcag_level")
    };

    resultsDiv.classList.add("hidden");
    loader.classList.remove("hidden");
    progressFill.style.width = "0%";
    statusText.textContent = "0% - Starting...";

    try {
        const res = await fetch("/api/accessibility", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
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
