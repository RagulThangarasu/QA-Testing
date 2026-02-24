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

// New Baseline Elements
const navBaselines = document.getElementById("btn-manage-baselines"); // Changed ID
const viewBaselines = document.getElementById("view-baselines");
const blHistoryModal = document.getElementById("baseline-history-modal");

const blHistoryList = document.getElementById("bl-history-list");
const blModalTitle = document.getElementById("bl-modal-title");


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

// Baseline Check Logic for UI
async function checkBaseline(url) {
  const uploadSection = document.getElementById("figma-upload-section");
  const statusMsg = document.getElementById("baseline-status-msg");
  const urlInput = document.querySelector("input[name='stage_url']");

  if (!url || !url.startsWith("http")) {
    // Reset if invalid or empty: Show upload section (default state)
    if (uploadSection) uploadSection.style.display = "block";
    if (statusMsg) statusMsg.textContent = "";
    return;
  }

  // Check if baseline exists
  try {
    const res = await fetch("/api/baselines", { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch baselines");
    const baselines = await res.json();
    if (!Array.isArray(baselines)) return false;

    // Exact match on URL (with loose trailing slash check)
    // Use URL object for robust comparison (handles encoding, default ports, etc)
    const normalize = (u) => {
      try {
        const obj = new URL(u);
        // Compare protocol + host + path, ignore trailing slash on path
        return (obj.protocol + "//" + obj.host + obj.pathname).replace(/\/+$/, "").toLowerCase();
      } catch (e) {
        return u.replace(/\/+$/, "").trim().toLowerCase();
      }
    };

    const target = normalize(url);
    const hasBaseline = baselines.find(b => normalize(b.url) === target && b.active_version_id);

    if (hasBaseline) {
      if (uploadSection) uploadSection.style.display = "none";

      // Re-query statusMsg to avoid race conditions active active fetches
      const currentMsg = document.getElementById("baseline-status-msg");

      if (!currentMsg) {
        const msg = document.createElement("p");
        msg.id = "baseline-status-msg";
        msg.style.color = "#10b981";
        msg.style.fontSize = "0.9em";
        msg.style.fontWeight = "500";
        msg.style.marginTop = "8px";
        msg.style.padding = "8px";
        msg.style.background = "rgba(16, 185, 129, 0.1)";
        msg.style.borderRadius = "4px";
        msg.style.border = "1px solid rgba(16, 185, 129, 0.2)";

        urlInput.parentNode.appendChild(msg);
        msg.innerHTML = `✅ <strong>Baseline Active (v${hasBaseline.active_version_id})</strong><br><span style="font-size:0.9em; opacity:0.8">Using approved reference image. Upload hidden.</span>`;
      } else {
        currentMsg.innerHTML = `✅ <strong>Baseline Active (v${hasBaseline.active_version_id})</strong><br><span style="font-size:0.9em; opacity:0.8">Using approved reference image. Upload hidden.</span>`;
        currentMsg.style.display = "block";
      }
      return true;
    } else {
      // Valid URL but No Baseline -> Show Upload
      if (uploadSection) uploadSection.style.display = "block";
      if (statusMsg) statusMsg.style.display = "none";
      return false;
    }
  } catch (e) {
    console.error("Error checking baseline:", e);
    return false;
  }
}



const urlInput = document.getElementsByName("stage_url")[0];
urlInput.addEventListener("input", (e) => checkBaseline(e.target.value.trim()));
urlInput.addEventListener("change", (e) => checkBaseline(e.target.value.trim()));

// Run check on load
if (urlInput.value) {
  checkBaseline(urlInput.value.trim());
} else {
  // Ensure default visibility if empty
  const uploadSection = document.getElementById("figma-upload-section");
  if (uploadSection) uploadSection.style.display = "block";
}



figmaInput.addEventListener("dragenter", () => dropZone.classList.add("dragover"));
figmaInput.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
figmaInput.addEventListener("drop", () => dropZone.classList.remove("dragover"));


function showToast(msg, isError = false) {
  toast.textContent = msg;
  toast.classList.remove("hidden");
  toast.classList.toggle("error", isError);
  setTimeout(() => toast.classList.add("hidden"), 4000);
}

// Custom Modal for confirmations
function confirmModal(text) {
  return new Promise((resolve) => {
    let modal = document.getElementById("custom-modal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "custom-modal";
      modal.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:9999;";
      modal.innerHTML = `
            <div style="background:#1e293b;padding:24px;border-radius:12px;max-width:400px;width:90%;border:1px solid #334155;box-shadow:0 10px 25px -5px rgba(0,0,0,0.3);animation: modalFadeIn 0.2s ease-out;">
                <h3 style="margin-top:0;color:#f8fafc;font-size:1.25rem;">Confirm Action</h3>
                <p id="c-modal-text" style="color:#cbd5e1;margin:16px 0;line-height:1.6;font-size:0.95rem;"></p>
                <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:24px;">
                    <button id="c-modal-cancel" class="btn-secondary" style="background:#334155;color:#f1f5f9;border:none;">Cancel</button>
                    <button id="c-modal-confirm" class="btn-approve">Confirm</button>
                </div>
            </div>
          `;
      document.body.appendChild(modal);

      // Add animation style
      const style = document.createElement('style');
      style.innerHTML = `@keyframes modalFadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`;
      document.head.appendChild(style);
    }

    const txt = document.getElementById("c-modal-text");
    const btnYes = document.getElementById("c-modal-confirm");
    const btnNo = document.getElementById("c-modal-cancel");

    txt.textContent = text;
    modal.style.display = "flex";

    // One-time listeners unique to this promise
    const handleYes = () => { cleanup(); resolve(true); };
    const handleNo = () => { cleanup(); resolve(false); };

    function cleanup() {
      btnYes.removeEventListener("click", handleYes);
      btnNo.removeEventListener("click", handleNo);
      modal.style.display = "none";
    }

    btnYes.addEventListener("click", handleYes);
    btnNo.addEventListener("click", handleNo);
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  const figmaFile = document.getElementById("figma").files[0];
  const stageUrl = fd.get("stage_url");

  if (!figmaFile && !stageUrl) {
    showToast("Please provide either a Figma PNG or a valid Stage URL with an active baseline.", true);
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

  if (enablePixelThreshold) {
    const rawPercent = document.getElementById("pixel_threshold").value;
    // Send raw percentage (0-100) — backend handles all threshold mapping
    fd.set("pixel_threshold", parseInt(rawPercent, 10));
  }

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
  // Hide all first
  viewRun.classList.add("hidden");
  viewHistory.classList.add("hidden");
  viewBaselines.classList.add("hidden");

  // Reset nav active states
  navRun.classList.remove("active");
  navHistory.classList.remove("active");
  navBaselines.classList.remove("active");

  if (view === "run") {
    viewRun.classList.remove("hidden");
    navRun.classList.add("active");
    loadHistory(); // Optional: load history sidebar/list if it exists in run view?
    // Re-check baseline status
    const urlVal = document.getElementsByName("stage_url")[0].value;
    if (urlVal) checkBaseline(urlVal.trim());

  } else if (view === "history") {
    viewHistory.classList.remove("hidden");
    navHistory.classList.add("active");
    loadHistory();

  } else if (view === "baselines") {
    viewBaselines.classList.remove("hidden");
    navBaselines.classList.add("active");
    loadBaselines();
  }
}

navBaselines.addEventListener("click", (e) => {
  e.preventDefault();
  switchView("baselines");
});

document.getElementById("baselines-back").addEventListener("click", (e) => {
  e.preventDefault();
  switchView("run");
});

document.getElementById("history-back").addEventListener("click", (e) => {
  e.preventDefault();
  switchView("run");
});

window.deleteBaseline = async function (url) {
  if (!confirm(`Are you sure you want to delete the baseline for ${url}? This cannot be undone.`)) return;

  try {
    const res = await fetch("/api/baselines/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (res.ok) {
      showToast("Baseline deleted.");
      loadBaselines();
    } else {
      const d = await res.json();
      showToast(d.error || "Delete failed", true);
    }
  } catch (e) {
    showToast("Error deleting baseline", true);
  }
}

// Upload explicit baseline
const blUploadInput = document.createElement("input");
blUploadInput.type = "file";
blUploadInput.accept = "image/png";
blUploadInput.style.display = "none";
document.body.appendChild(blUploadInput);

let currentUploadUrl = null;

blUploadInput.addEventListener("change", async () => {
  if (blUploadInput.files.length === 0 || !currentUploadUrl) return;

  const file = blUploadInput.files[0];
  const fd = new FormData();
  fd.set("file", file);
  fd.set("url", currentUploadUrl);

  // Show loading...
  showToast("Uploading baseline...");

  try {
    const res = await fetch("/api/baselines/upload", { method: "POST", body: fd });
    const data = await res.json();

    if (res.ok) {
      showToast(`Baseline updated (v${data.version_id})`);
      loadBaselines();
    } else {
      showToast(data.error || "Upload failed", true);
    }
  } catch (e) {
    showToast("Error uploading baseline", true);
  }

  blUploadInput.value = ""; // reset
  currentUploadUrl = null;
});

window.uploadBaseline = function (url) {
  currentUploadUrl = url;
  blUploadInput.click();
}



let currentPage = 1;
let currentFilter = 'all'; // all, pending, approved, rejected
const LIMIT = 10;

window.filterHistory = function (filter, btn) {
  currentFilter = filter;
  // update buttons
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  else if (filter === 'all') document.querySelector('.filter-btn:first-child').classList.add('active');
  else {
    // Find button by text or index... simple approach:
    const map = { 'all': 0, 'pending': 1, 'approved': 2, 'rejected': 3 };
    // Logic simplified:
    if (filter === 'approved') document.querySelectorAll('.filter-btn')[2].classList.add('active');
    if (filter === 'rejected') document.querySelectorAll('.filter-btn')[3].classList.add('active');
  }
  loadHistory(1);
}


async function loadHistory(page = 1) {
  currentPage = page;
  historyList.innerHTML = "<tr><td colspan='7'>Loading...</td></tr>";
  document.getElementById("pagination").innerHTML = "";

  try {
    let url = `/api/history?page=${page}&limit=${LIMIT}`;
    if (currentFilter && currentFilter !== 'all') {
      url += `&filter=${currentFilter}`;
    }
    const res = await fetch(url);


    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    console.log('History data received:', data);

    // Support both old array format and new paginated response
    let jobs = Array.isArray(data) ? data : data.jobs;
    // Client-side filtering if API doesn't support it yet (it doesn't seem to)
    // To support real pagination with filtering, backend needs update.
    // For now, we will filter client side ONLY IF data.total is small, or assume backend returns filtered?
    // Backend `get_history` only filters by type=visual_testing.
    // So we fetch a page calling API, but filtering on page means we lose items.
    // WE MUST UPDATE BACKEND TO SUPPORT FILTERING.
    // I will update the backend in next step. Assuming backend supports ?filter=...

    const total = data.total !== undefined ? data.total : jobs.length;




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
      <button class="btn-reject" style="font-size: 13px; padding: 4px 12px;" onclick="deleteSelected()">🗑️ Delete Selected</button>
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

  if (!await confirmModal(`Delete ${ids.length} records?`)) return;

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

window.deleteBaseline = async function (url) {
  if (!await confirmModal(`Are you sure you want to delete the baseline for ${url}? This cannot be undone.`)) return;

  try {
    const res = await fetch("/api/baselines/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (res.ok) {
      showToast("Baseline deleted.");
      loadBaselines();
    } else {
      const d = await res.json();
      showToast(d.error || "Delete failed", true);
    }
  } catch (e) {
    showToast("Error deleting baseline", true);
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
      if (approve) {
        showToast("Job Approved.");
      } else {
        showToast("Job Rejected.");
      }

      // Delay slightly to show toast, then reload
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      showToast("Action failed.", true);
    }
  } catch (e) {
    showToast("Error sending review.", true);
  }
}

// Explicit Baseline Promotion
async function promoteBaseline(jobId) {
  if (!await confirmModal("Are you sure you want to update the official baseline with the reference image from this run?")) return;

  try {
    const res = await fetch(`/api/baselines/promote/${jobId}`, { method: "POST" });
    const data = await res.json();

    if (res.ok) {
      showToast(`Baseline Updated & Job Approved (v${data.version_id})`);
      setTimeout(() => window.location.reload(), 1500);
    } else {
      showToast("Error updating baseline: " + data.error, true);
    }
  } catch (e) {
    showToast("Error promoting baseline", true);
  }
}

// Baseline Logic
async function loadBaselines() {
  const list = document.getElementById("baselines-list");
  list.innerHTML = "<p>Loading baselines...</p>";

  try {
    const res = await fetch("/api/baselines");
    const baselines = await res.json();

    if (!baselines || baselines.length === 0) {
      list.innerHTML = "<p>No baselines found. Run a comparison and Approve it to create one.</p>";
      return;
    }

    list.innerHTML = baselines.map(b => {
      const active = b.versions.find(v => v.version_id === b.active_version_id);
      const date = active ? new Date(active.timestamp).toLocaleString() : "-";
      // Construct image URL
      const imgUrl = b.active_image_path ? `/api/baselines/image/${b.active_image_path}` : 'https://via.placeholder.com/300x200?text=No+Image';

      // Clean URL for display title (hide, or show domain path)
      let displayTitle = "Baseline";
      try {
        const urlObj = new URL(b.url);
        displayTitle = urlObj.pathname === "/" || urlObj.pathname === "" ? "Homepage" : urlObj.pathname;
      } catch (e) { displayTitle = b.url; }

      return `
             <div class="baseline-card">
                <div class="baseline-thumb" style="height: 180px; overflow: hidden; border-radius: 8px; background: #0f172a; border: 1px solid #1e293b; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                    <img src="${imgUrl}" alt="Baseline" style="width: 100%; height: 100%; object-fit: contain;">
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 title="${b.url}" style="font-size: 1.1rem; margin:0; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; max-width: 220px; color: #e2e8f0;">${displayTitle}</h3>
                    <button onclick="window.deleteBaseline('${b.url}')" class="btn-reject" style="padding:4px 8px; font-size:11px; opacity:0.8;">Delete</button>
                </div>
                <!-- Hide URL text as requested, rely on title hover -->
                <p style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">${b.active_version_id || "v1"}</p>
                <div style="margin-top:12px; display:flex; gap:10px;">
                    <button onclick="window.viewBaselineHistory('${encodeURIComponent(b.url)}')" class="btn-secondary" style="flex:1;">History</button>
                    <button onclick="window.uploadBaseline('${b.url}')" class="btn-approve" style="flex:1;">Update</button>
                </div>
             </div>
             `;

    }).join("");


  } catch (e) {
    list.innerHTML = `<p class="error">Error loading baselines: ${e.message}</p>`;
  }
}

window.viewBaselineHistory = async function (encodedUrl) {
  const url = decodeURIComponent(encodedUrl);
  blHistoryModal.classList.remove("hidden");

  // Clean title for modal
  let cleanTitle = url;
  try {
    const u = new URL(url);
    cleanTitle = u.pathname === "/" ? "Homepage" : u.pathname;
  } catch (e) { }

  blModalTitle.textContent = `History: ${cleanTitle}`;
  blHistoryList.innerHTML = "<tr><td colspan='4'>Loading...</td></tr>";


  try {
    const res = await fetch("/api/baselines");
    const baselines = await res.json();
    const baseline = baselines.find(b => b.url === url);

    if (!baseline) {
      blHistoryList.innerHTML = "<tr><td colspan='4'>Not found</td></tr>";
      return;
    }

    blHistoryList.innerHTML = baseline.versions.map(v => {
      const isActive = v.version_id === baseline.active_version_id;
      const date = new Date(v.timestamp).toLocaleString();
      const actionButton = !isActive
        ? `<button onclick="window.rollbackBaseline('${encodeURIComponent(url)}', '${v.version_id}')" class="btn-secondary" style="color: blue; border-color: blue;">Rollback to this</button>`
        : `<span>Current Active</span>`;

      return `
            <tr style="${isActive ? 'background:rgba(16, 185, 129, 0.15); color: #fff;' : ''}">
                <td style="font-family:monospace; font-size:0.9em;">${v.version_id}</td>
                <td>${date}</td>
                <td><a href="#" onclick="window.loadJob('${v.job_id}'); document.getElementById('baseline-history-modal').classList.add('hidden'); return false;" style="color:#60a5fa; text-decoration:none;">${v.job_id}</a></td>
                <td>${actionButton}</td>
            </tr>

            `;
    }).join("");

  } catch (e) {
    blHistoryList.innerHTML = `<tr><td colspan='4'>Error: ${e.message}</td></tr>`;
  }
}

window.rollbackBaseline = async function (encodedUrl, versionId) {
  const url = decodeURIComponent(encodedUrl);
  if (!await confirmModal(`Rollback ${url} to ${versionId}?`)) return;


  try {
    const res = await fetch("/api/baselines/rollback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, version_id: versionId })
    });

    if (res.ok) {
      showToast("Rollback successful.");
      window.viewBaselineHistory(encodedUrl); // refresh list
      loadBaselines(); // refresh main list if visible
    } else {
      const d = await res.json();
      showToast(d.error || "Rollback failed", true);
    }
  } catch (e) {
    showToast("Error during rollback", true);
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

      // Add Update Baseline Button
      const existingBtn = document.getElementById("btnUpdateBaseline");
      if (existingBtn) existingBtn.remove();

      const btnUpdate = document.createElement("button");
      btnUpdate.id = "btnUpdateBaseline";
      btnUpdate.textContent = "Update Baseline";
      btnUpdate.className = "btn-approve";
      btnUpdate.style.backgroundColor = "#8b5cf6";
      btnUpdate.style.marginLeft = "10px";
      btnUpdate.onclick = () => promoteBaseline(jobId);
      actionsDiv.appendChild(btnUpdate);

      // Check baseline status to toggle Approve button
      try {
        const jobRes = await fetch(`/api/job/${jobId}`);
        const jobData = await jobRes.json();
        if (jobData && jobData.url) {
          const hasBl = await checkBaseline(jobData.url);

          // Hide Approve if:
          // 1. No baseline exists for this URL
          // 2. OR The job used an uploaded file (manual override), so it's not a standard regression test
          if (!hasBl || (jobData.reference_source === 'upload')) {
            btnApprove.style.display = "none";
          } else {
            btnApprove.style.display = "inline-block";
          }
          // Also sync input value
          if (document.getElementsByName("stage_url")[0]) {
            document.getElementsByName("stage_url")[0].value = jobData.stage_url || jobData.url;
          }
        }
      } catch (e) { console.error("Error syncing baseline state:", e); }

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
          <figcaption>Baseline / Reference</figcaption>
          <img src="${results.outputs.figma_png}" alt="Reference Image"/>


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
        const issuesHtml = results.metrics.issues.map(issue => {
          // Determine category badge
          const desc = issue.description || '';
          let badge = '';
          let badgeColor = '';
          if (desc.includes('Spacing') || desc.includes('Margin') || desc.includes('Padding') || desc.includes('Gap') || desc.includes('Column')) {
            badge = '📐 Spacing';
            badgeColor = 'background:#dbeafe;color:#1d4ed8;';
          } else if (desc.includes('Color') || desc.includes('Style')) {
            badge = '🎨 Style';
            badgeColor = 'background:#fed7aa;color:#9a3412;';
          } else if (desc.includes('Content') || desc.includes('Text')) {
            badge = '📝 Content';
            badgeColor = 'background:#fef9c3;color:#854d0e;';
          } else if (desc.includes('Missing') || desc.includes('Extra')) {
            badge = '⚠️ Element';
            badgeColor = 'background:#fce7f3;color:#9d174d;';
          } else {
            badge = '🔲 Layout';
            badgeColor = 'background:#e9d5ff;color:#6b21a8;';
          }

          return `
          <div class="issue-card">
            <input type="checkbox" class="issue-checkbox" value="${issue.filename}" 
                   style="position:absolute; top:8px; left:8px; z-index:10; transform: scale(1.5);">
            <div class="issue-thumb">
              <img src="/download/${results.job_id}/${issue.filename}" alt="${issue.label}"/>
            </div>
            <div class="issue-info">
              <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px; flex-wrap:wrap;">
                <span style="font-size:0.72em; padding:2px 8px; border-radius:10px; font-weight:600; white-space:nowrap; ${badgeColor}">${badge}</span>
              </div>
              <h4 title="${issue.full_label || issue.label}">${issue.full_label || issue.label}</h4>
              <p style="font-size: 0.8em; color: #ccc;">X=${issue.x}, Y=${issue.y} ${issue.dims ? '(' + issue.dims + ')' : ''}</p>
              <a href="/download/${results.job_id}/${issue.filename}" download class="btn-download-issue">Download Issue</a>
              <button onclick="window.openJiraReport('${jobId}', '${issue.filename}', '${(issue.label || "").replace(/'/g, "\\'")}', '${(issue.description || "").replace(/'/g, "\\'")}')" class="btn-secondary" style="font-size:12px; margin-top:5px; width:100%;">To Jira</button>
              <button onclick="window.openGitHubReport('${jobId}', '${issue.filename}', '${(issue.label || "").replace(/'/g, "\\'")}', '${(issue.description || "").replace(/'/g, "\\'")}')" class="btn-secondary" style="font-size:12px; margin-top:5px; width:100%; border: 1px solid #ccc; background: #f6f8fa; color: #333;">To GitHub</button>
            </div>
          </div>`;
        }).join("");

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



