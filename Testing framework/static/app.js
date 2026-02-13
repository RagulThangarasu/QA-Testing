const form = document.getElementById("cmpForm");
const result = document.getElementById("result");
const toast = document.getElementById("toast");
const metricsDiv = document.getElementById("metrics");
const previews = document.getElementById("previews");
const dlOverlay = document.getElementById("dl_overlay");
const dlHeatmap = document.getElementById("dl_heatmap");
const dlAligned = document.getElementById("dl_aligned");
const dlReport = document.getElementById("dl_report");
const loader = document.getElementById("loader");
const progressFill = document.getElementById("progressFill");
const navRun = document.getElementById("nav-run");
const viewRun = document.getElementById("view-run");
const navHistory = document.getElementById("nav-history"); // This is now inside view-run
const viewHistory = document.getElementById("view-history");
const historyList = document.getElementById("history-list");
const actionsDiv = document.getElementById("actions");
const btnApprove = document.getElementById("btnApprove");
const btnReject = document.getElementById("btnReject");

const figmaInput = document.getElementById("figma");
const fileText = document.getElementById("file-text");
const dropZone = document.getElementById("drop-zone");

figmaInput.addEventListener("change", () => {
  if (figmaInput.files.length > 0) {
    fileText.textContent = figmaInput.files[0].name;
    fileText.classList.add("active");
    dropZone.classList.add("dragover");
  } else {
    fileText.textContent = "Click or Drop Figma PNG here";
    fileText.classList.remove("active");
    dropZone.classList.remove("dragover");
  }
});

figmaInput.addEventListener("dragenter", () => dropZone.classList.add("dragover"));
figmaInput.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
figmaInput.addEventListener("drop", () => dropZone.classList.remove("dragover"));

function showToast(msg, isError = false) {
  toast.textContent = msg;
  toast.classList.remove("hidden");
  toast.classList.toggle("error", isError);
  setTimeout(() => toast.classList.add("hidden"), 4000);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  const figmaFile = document.getElementById("figma").files[0];
  if (!figmaFile) {
    showToast("Please choose a Figma PNG.", true);
    return;
  }

  // Reset UI
  result.classList.add("hidden");
  toast.classList.add("hidden");
  loader.classList.remove("hidden");
  progressFill.style.width = "0%";
  statusText.textContent = "0% - Starting...";

  // Ensure checkbox posts value
  // User requested removal of fullpage toggle, defaulting to true in backend/assuming fullpage desirable.
  // fd.set('fullpage', 'true'); // Optional, backend defaults to true anyway.

  const enablePixelThreshold = document.getElementById("enable_pixel_threshold").checked;
  fd.set("enable_pixel_threshold", enablePixelThreshold ? "true" : "false");

  try {
    const res = await fetch("/api/compare", { method: "POST", body: fd });
    const data = await res.json();

    if (!res.ok) {
      loader.classList.add("hidden");
      showToast(data.error || "Comparison failed.", true);
      return;
    }

    // Start polling
    pollStatus(data.job_id);

  } catch (err) {
    console.error(err);
    loader.classList.add("hidden");
    showToast("Unexpected error.", true);
  }
});

// Navigation
navRun.addEventListener("click", (e) => {
  e.preventDefault();
  switchView("run");
});

navHistory.addEventListener("click", (e) => {
  e.preventDefault();
  switchView("history");
});

function switchView(view) {
  if (view === "run") {
    viewRun.classList.remove("hidden");
    viewHistory.classList.add("hidden");
    navRun.classList.add("active");
  } else {
    viewRun.classList.add("hidden");
    viewHistory.classList.remove("hidden");
    navRun.classList.remove("active");
    loadHistory();
  }
}

let currentPage = 1;
const LIMIT = 10;

async function loadHistory(page = 1) {
  currentPage = page;
  historyList.innerHTML = "<tr><td colspan='7'>Loading...</td></tr>";
  document.getElementById("pagination").innerHTML = "";

  try {
    const res = await fetch(`/api/history?page=${page}&limit=${LIMIT}`);

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    console.log('History data received:', data);

    // Support both old array format and new paginated response
    const jobs = Array.isArray(data) ? data : data.jobs;
    const total = data.total !== undefined ? data.total : jobs.length;

    // Add header interaction for bulk delete if not present
    if (!document.getElementById("btnDelete")) {
      const h1 = viewHistory.querySelector("h1");
      const btn = document.createElement("button");
      btn.id = "btnDelete";
      btn.textContent = "Clear Selected";
      btn.className = "btn-reject"; // reuse cancel style
      btn.style.float = "right";
      btn.style.fontSize = "14px";
      btn.onclick = deleteSelected;
      h1.appendChild(btn);
    }

    if (!jobs || jobs.length === 0) {
      historyList.innerHTML = "<tr><td colspan='7'>No history found.</td></tr>";
      return;
    }

    historyList.innerHTML = "";
    jobs.forEach((job) => {
      const row = document.createElement("tr");

      // Use timestamp if available, fallback to created_at for backward compatibility
      const date = job.timestamp ? new Date(job.timestamp).toLocaleString() : (job.created_at ? new Date(job.created_at).toLocaleString() : "-");

      const status = job.status || "unknown";
      const approved = job.approved ? "✓ Approved" : (job.approved === false ? "✗ Rejected" : "-");
      const ssim = job.result?.metrics?.ssim !== undefined ? job.result.metrics.ssim.toFixed(3) :
        (job.result?.ssim !== undefined ? job.result.ssim.toFixed(3) : "-");

      row.innerHTML = `
        <td><input type="checkbox" class="history-checkbox" value="${job.job_id}"></td>
        <td>${date}</td>
        <td>${job.job_id}</td>
        <td>${status}</td>
        <td>${approved}</td>
        <td>${ssim}</td>
        <td>
          ${status === "completed" && job.result
          ? `<a href="/download/${job.job_id}/report.pdf" target="_blank" class="btn-secondary" style="font-size: 12px; padding: 4px 8px;">PDF</a>`
          : "-"
        }
        </td>
      `;
      historyList.appendChild(row);
    });

    // Pagination controls
    const totalPages = Math.ceil(total / LIMIT);
    const prevDisabled = page <= 1 ? "disabled" : "";
    const nextDisabled = page >= totalPages ? "disabled" : "";

    document.getElementById("pagination").innerHTML = `
      <span>Page ${page} of ${totalPages} (${total} total)</span>
      <div style="display: flex; gap: 10px;">
        <button class="btn-secondary" ${prevDisabled} onclick="loadHistory(${page - 1})" style="padding: 5px 10px; font-size: 14px;">&larr; Previous</button>
        <button class="btn-secondary" ${nextDisabled} onclick="loadHistory(${page + 1})" style="padding: 5px 10px; font-size: 14px;">Next &rarr;</button>
      </div>
    `;
  } catch (err) {
    console.error("Error loading history:", err);
    historyList.innerHTML = `<tr><td colspan='7' style='color: var(--error);'>Error loading history: ${err.message}</td></tr>`;
  }
}

async function deleteSelected() {
  const checked = document.querySelectorAll(".history-checkbox:checked");
  const ids = Array.from(checked).map(cb => cb.value);

  if (ids.length === 0) {
    showToast("No records selected.", true);
    return;
  }

  if (!confirm(`Delete ${ids.length} records?`)) return;

  try {
    const res = await fetch("/api/history/delete", {
      method: "POST",
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

// Global for inline onclick
window.loadJob = function (jobId) {
  // Switch to run view and load status
  switchView("run");
  // Clear current inputs
  form.reset();
  result.classList.add("hidden");
  loader.classList.remove("hidden");
  progressFill.style.width = "100%";
  statusText.textContent = "Loading job...";

  pollStatus(jobId);
};

// Approval Actions
btnApprove.onclick = async () => handleReview(true);
btnReject.onclick = async () => handleReview(false);

async function handleReview(approve) {
  const jobId = btnApprove.dataset.jobId;
  if (!jobId) return;

  try {
    const endpoint = approve ? "approve" : "reject";
    const res = await fetch(`/api/job/${jobId}/${endpoint}`, { method: "POST" });
    if (res.ok) {
      showToast(approve ? "Job Approved!" : "Job Rejected.");

      // Delay slightly to show toast, then reload
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } else {
      showToast("Action failed.", true);
    }
  } catch (e) {
    showToast("Error sending review.", true);
  }
}

async function pollStatus(jobId) {
  try {
    const res = await fetch(`/api/status/${jobId}`);
    if (!res.ok) {
      // If job not found, maybe show error
      loader.classList.add("hidden");
      showToast("Job not found.", true);
      return;
    }
    const data = await res.json();

    // Update Progress
    if (data.progress !== undefined) {
      progressFill.style.width = `${data.progress}%`;
      statusText.textContent = `${data.progress}% - ${data.step}`;
    }

    if (data.status === "completed") {
      const results = data.result;
      loader.classList.add("hidden");

      // Render Results
      result.classList.remove("hidden");

      // Setup Actions
      actionsDiv.classList.remove("hidden");
      btnApprove.dataset.jobId = jobId;
      btnReject.dataset.jobId = jobId;

      metricsDiv.innerHTML = `
        <p><strong>Passed:</strong> ${results.passed ? "✅ Yes" : "❌ No"}</p>
        <p><strong>SSIM:</strong> ${results.metrics.ssim.toFixed(4)}</p>
        <p><strong>Changed Area:</strong> ${(results.metrics.change_ratio * 100).toFixed(2)}%</p>
        <p><strong>Regions:</strong> ${results.metrics.num_regions}</p>
      `;

      dlOverlay.href = results.outputs.diff_overlay;
      dlHeatmap.href = results.outputs.diff_heatmap;
      dlAligned.href = results.outputs.aligned_stage;
      dlReport.href = results.outputs.report_pdf;

      previews.innerHTML = `
        <figure>
          <figcaption>Figma Original</figcaption>
          <img src="${results.outputs.figma_png}" alt="Figma Original"/>
        </figure>
        <figure>
          <figcaption>Diff Overlay (${results.metrics.num_regions} issues highlighted)</figcaption>
          <img src="${results.outputs.diff_overlay}" alt="Diff Overlay"/>
        </figure>
        <figure>
          <figcaption>Diff Heatmap</figcaption>
          <img src="${results.outputs.diff_heatmap}" alt="Diff Heatmap"/>
        </figure>
      `;

      // Render Issues List
      if (results.metrics.issues && results.metrics.issues.length > 0) {
        const issuesHtml = results.metrics.issues.map(issue => `
          <div class="issue-card">
            <input type="checkbox" class="issue-checkbox" value="${issue.filename}" 
                   style="position:absolute; top:8px; left:8px; z-index:10; transform: scale(1.5);">
            <div class="issue-thumb">
              <img src="/download/${results.job_id}/${issue.filename}" alt="${issue.label}"/>
            </div>
            <div class="issue-info">
              <h4 title="${issue.full_label || issue.label}">${issue.full_label || issue.label}</h4>
              <p style="font-size: 0.8em; color: #ccc;">X=${issue.x}, Y=${issue.y} ${issue.dims ? '(' + issue.dims + ')' : ''}</p>
              <a href="/download/${results.job_id}/${issue.filename}" download class="btn-download-issue">Download Issue</a>
              <button onclick="window.openJiraReport('${jobId}', '${issue.filename}', '${(issue.label || "").replace(/'/g, "\\'")}', '${(issue.description || "").replace(/'/g, "\\'")}')" class="btn-secondary" style="font-size:12px; margin-top:5px; width:100%;">To Jira</button>
            </div>
          </div>
        `).join("");

        const issuesContainer = document.createElement("div");
        issuesContainer.className = "issues-list";
        issuesContainer.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <h3>Detected Differences</h3>
            <div style="display:flex; align-items:center; gap:10px;">
              <label style="font-size:14px; display:flex; align-items:center; cursor:pointer;">
                <input type="checkbox" id="selectAllIssues" onclick="window.toggleAllIssues(this)" style="margin-right:5px; transform: scale(1.2);"> Select All
              </label>
              <button onclick="window.downloadSelectedIssues('${jobId}')" class="btn-secondary" style="font-size:12px;">Download Selected</button>
            </div>
          </div>
          <div class="grid">${issuesHtml}</div>`;
        previews.appendChild(issuesContainer);
      }
      showToast("Done.");

    } else if (data.status === "failed") {
      loader.classList.add("hidden");
      showToast(data.error || "Job failed.", true);
    } else {
      // Still running
      setTimeout(() => pollStatus(jobId), 500);
    }

  } catch (err) {
    console.error(err);
    loader.classList.add("hidden");
    showToast("Error checking status.", true);
  }
}

function toggleAll(source) {
  const checkboxes = document.querySelectorAll('.history-checkbox');
  for (let cb of checkboxes) {
    cb.checked = source.checked;
  }
}
window.toggleAll = toggleAll;
window.deleteSelected = deleteSelected;

window.toggleAllIssues = function (source) {
  const checkboxes = document.querySelectorAll('.issue-checkbox');
  for (let cb of checkboxes) {
    cb.checked = source.checked;
  }
}

window.downloadSelectedIssues = function (jobId) {
  const checked = document.querySelectorAll(".issue-checkbox:checked");
  if (checked.length === 0) {
    showToast("No issues selected.", true);
    return;
  }

  Array.from(checked).forEach((cb, index) => {
    // stagger downloads
    setTimeout(() => {
      const filename = cb.value;
      const link = document.createElement('a');
      link.href = `/download/${jobId}/${filename}`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }, index * 300);
  });

  showToast(`Downloading ${checked.length} issues...`);
}

// Share report function



