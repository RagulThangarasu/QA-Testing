const form = document.getElementById("brokenLinksForm");
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

// Clear button - refresh page to start new session
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
        const res = await fetch(`/api/broken-links/history?page=${page}&limit=${LIMIT}`);
        const data = await res.json();

        const jobs = Array.isArray(data) ? data : data.jobs;
        const total = data.total !== undefined ? data.total : jobs.length;

        if (!document.getElementById("btnDelete")) {
            const h1 = viewHistory.querySelector("h1");
            const btn = document.createElement("button");
            btn.id = "btnDelete";
            btn.textContent = "Clear Selected";
            btn.className = "btn-reject";
            btn.style.marginLeft = "auto";
            btn.onclick = deleteSelected;
            h1.parentElement.insertBefore(btn, h1.nextSibling);
        }

        if (jobs.length === 0) {
            historyList.innerHTML = "<tr><td colspan='6'>No history yet.</td></tr>";
            return;
        }

        historyList.innerHTML = jobs.map(job => {
            const date = new Date(job.timestamp).toLocaleString();
            const checkType = job.check_type || "broken_links";
            const checkTypeLabel = checkType === "all" ? "All" :
                checkType === "broken_links" ? "Broken Links" :
                    checkType === "overlapping_breaking" ? "Overlapping & Breaking" : checkType;
            const issuesCount = job.result?.broken_count || 0;
            const reportUrl = job.result?.report_url || "";

            return `
                <tr>
                    <td><input type="checkbox" class="history-checkbox" value="${job.job_id}"></td>
                    <td>${date}</td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${job.stage_url}">${job.stage_url}</td>
                    <td>${checkTypeLabel}</td>
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
    const totalPages = Math.ceil(total / LIMIT);
    if (totalPages <= 1) return;

    const paginationDiv = document.getElementById("pagination");

    const prevDisabled = page === 1 ? "disabled" : "";
    const nextDisabled = page === totalPages ? "disabled" : "";

    paginationDiv.innerHTML = `
        <button class="btn-secondary" ${prevDisabled} onclick="loadHistory(${page - 1})" style="padding: 5px 10px; font-size: 14px;">&larr; Previous</button>
        <span>Page ${page} of ${totalPages}</span>
        <button class="btn-secondary" ${nextDisabled} onclick="loadHistory(${page + 1})" style="padding: 5px 10px; font-size: 14px;">Next &rarr;</button>
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
        const res = await fetch("/api/broken-links/history", {
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

            if (data.result.broken_count > 0) {
                resultsDiv.innerHTML = `
                    <div style="background: rgba(255, 107, 107, 0.1); padding: 20px; border-radius: 8px; border: 1px solid var(--error);">
                        <h3 style="color: var(--error); margin-top: 0;">Found ${data.result.broken_count} broken items!</h3>
                        <p>Download the detailed Excel report below:</p>
                        <a href="${data.result.report_url}" class="btn-secondary" style="display: inline-block; padding: 10px 20px; text-decoration: none; margin-top: 10px;">Download Report (Excel)</a>
                    </div>
                `;
            } else {
                resultsDiv.innerHTML = `
                    <div style="background: rgba(30, 200, 100, 0.1); padding: 20px; border-radius: 8px; border: 1px solid #10b981;">
                        <h3 style="color: #4effa0; margin-top: 0;">No issues found!</h3>
                        <p>All checked items appear to be valid.</p>
                    </div>
                `;
            }
            showToast("Scan completed.");
        } else if (data.status === "failed") {
            loader.classList.add("hidden");
            resultsDiv.classList.remove("hidden");

            // Show detailed error message
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
    const data = {
        stage_url: formData.get("stage_url"),
        check_type: formData.get("check_type")
    };

    resultsDiv.classList.add("hidden");
    loader.classList.remove("hidden");
    progressFill.style.width = "0%";
    statusText.textContent = "0% - Starting...";

    try {
        const res = await fetch("/api/broken-links", {
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
