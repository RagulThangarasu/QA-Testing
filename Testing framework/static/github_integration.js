/**
 * GitHub Integration — Visual Testing Studio
 * Handles: config modal, issue creation, PR report modal, PR status widget
 */

// ── Config Modal ──────────────────────────────────────────────────────────────

const navGithub = document.getElementById("nav-github");
if (navGithub) navGithub.addEventListener("click", openGitHubConfig);

const btnSaveGitHub = document.getElementById("btnSaveGitHub");
if (btnSaveGitHub) btnSaveGitHub.addEventListener("click", saveGitHubConfig);

const btnSendGitHub = document.getElementById("btnSendGitHub");
if (btnSendGitHub) btnSendGitHub.addEventListener("click", createGitHubIssue);

// ── Close modals on backdrop click ──
["github-config-modal", "github-report-modal"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("click", e => { if (e.target === el) el.classList.add("hidden"); });
});

function openGitHubConfig() {
    const modal = document.getElementById("github-config-modal");
    if (!modal) return;
    modal.classList.remove("hidden");

    fetch("/api/github/config")
        .then(r => r.json())
        .then(data => {
            if (document.getElementById("gh-token")) document.getElementById("gh-token").value = "";
            if (data.owner) document.getElementById("gh-owner").value = data.owner;
            if (data.repo) document.getElementById("gh-repo").value = data.repo;

            // Show connection status
            const statusEl = document.getElementById("gh-config-status");
            if (statusEl) {
                if (data.login && data.login !== "–") {
                    statusEl.innerHTML = `<div style="color:var(--success);font-size:.82rem;">✅ Connected as <strong>@${data.login}</strong> · ${data.owner}/${data.repo}</div>`;
                } else {
                    statusEl.innerHTML = `<div style="color:var(--muted);font-size:.82rem;">⭕ Not connected — enter credentials below</div>`;
                }
            }

            // Load open PRs for the mini list
            loadPRStatusWidget();
        })
        .catch(e => console.error("GitHub config load error:", e));
}

function saveGitHubConfig() {
    const token = document.getElementById("gh-token").value.trim();
    const owner = document.getElementById("gh-owner").value.trim();
    const repo = document.getElementById("gh-repo").value.trim();
    const webhookSecret = (document.getElementById("gh-webhook-secret") || {}).value || "";
    const stagingUrl = (document.getElementById("gh-staging-url") || {}).value || "";

    if (!token || !owner || !repo) {
        if (window.showToast) showToast("Token, Owner, and Repo are required", true);
        return;
    }

    const btn = document.getElementById("btnSaveGitHub");
    btn.disabled = true;
    btn.textContent = "⏳ Saving...";

    fetch("/api/github/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, owner, repo, webhook_secret: webhookSecret, staging_url: stagingUrl })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                if (window.showToast) showToast(`✅ Connected as @${data.login}!`);
                document.getElementById("github-config-modal").classList.add("hidden");
            } else {
                if (window.showToast) showToast(data.error || "Failed to connect", true);
            }
        })
        .catch(() => { if (window.showToast) showToast("Error saving GitHub config", true); })
        .finally(() => { btn.disabled = false; btn.textContent = "Save & Connect"; });
}

// ── Report Modal (from visual test issue cards) ───────────────────────────────

window.openGitHubReport = function (jobId, filename, label, description) {
    const modal = document.getElementById("github-report-modal");
    if (!modal) return;
    modal.classList.remove("hidden");

    document.getElementById("gh-title").value = `[Visual Regression] ${label || filename}`;

    const body = `## Visual Regression Detected

**Label:** ${label || "N/A"}
**Description:** ${description || "N/A"}

**QA Job Details:**
- Job ID: \`${jobId}\`
- File: \`${filename}\`
- Diff Overlay: ${window.location.origin}/download/${jobId}/diff_overlay.png
- Heatmap: ${window.location.origin}/download/${jobId}/diff_heatmap.png
- PDF Report: ${window.location.origin}/download/${jobId}/report.pdf

_Reported automatically by QA Visual Testing Framework_`;

    document.getElementById("gh-body").value = body;

    const btn = document.getElementById("btnSendGitHub");
    btn.dataset.jobId = jobId;
    btn.dataset.filename = filename;
};

function createGitHubIssue() {
    const btn = document.getElementById("btnSendGitHub");
    const jobId = btn.dataset.jobId;
    const filename = btn.dataset.filename;
    const title = document.getElementById("gh-title").value.trim();
    const body = document.getElementById("gh-body").value.trim();

    if (!title) { if (window.showToast) showToast("Title is required", true); return; }

    btn.disabled = true;
    btn.textContent = "⏳ Creating...";

    fetch("/api/github/issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            title,
            body,
            job_id: jobId,
            issue_filename: filename,
            labels: ["visual-regression", "bug"]
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                if (window.showToast) showToast(`✅ GitHub Issue #${data.number} created!`);
                document.getElementById("github-report-modal").classList.add("hidden");
                document.getElementById("gh-title").value = "";
                document.getElementById("gh-body").value = "";
                // Open issue in new tab
                if (data.html_url) window.open(data.html_url, "_blank");
            } else {
                if (window.showToast) showToast(data.error || "Failed to create issue", true);
            }
        })
        .catch(() => { if (window.showToast) showToast("Error creating issue", true); })
        .finally(() => { btn.disabled = false; btn.textContent = "Create Issue"; });
}

// ── PR Status Widget ─────────────────────────────────────────────────────────

async function loadPRStatusWidget() {
    const container = document.getElementById("gh-pr-list");
    if (!container) return;

    try {
        const [prRes, runsRes] = await Promise.all([
            fetch("/api/github/prs").then(r => r.json()),
            fetch("/api/github/pr-runs").then(r => r.json()),
        ]);

        const prs = prRes.prs || [];
        const runs = Array.isArray(runsRes) ? runsRes : [];

        if (prs.length === 0 && runs.length === 0) {
            container.innerHTML = `<div style="text-align:center; padding:12px; color:var(--muted); font-size:.82rem;">No open PRs found.</div>`;
            return;
        }

        const allPrs = [...prs];
        runs.forEach(r => {
            if (!allPrs.find(p => p.number === r.pr_number)) {
                allPrs.push({ number: r.pr_number, title: r.title || `PR #${r.pr_number}`, branch: r.branch || "" });
            }
        });

        container.innerHTML = allPrs.slice(0, 6).map(pr => {
            const run = runs.find(r => r.pr_number === pr.number);
            const statusIcon = run
                ? (run.status === "completed" ? (run.passed ? "✅" : "❌") : run.status === "running" ? "🔄" : "⏳")
                : "–";

            return `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border); font-size:.8rem;">
        <div style="flex:1; min-width:0;">
          <div style="font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${pr.title}</div>
          <div style="color:var(--muted); font-size:.72rem;">#${pr.number} · ${pr.branch || ""}</div>
        </div>
        <div style="display:flex; align-items:center; gap:6px; margin-left:8px;">
          <span>${statusIcon}</span>
          <button onclick="window.location.href='/ci-dashboard'" class="btn-secondary" style="font-size:10px; padding:2px 7px;">View</button>
        </div>
      </div>`;
        }).join("");

        if (allPrs.length > 6) {
            container.innerHTML += `<div style="text-align:center; padding:8px; font-size:.78rem; color:var(--muted);">
        +${allPrs.length - 6} more · <a href="/ci-dashboard" style="color:var(--accent);">View All</a>
      </div>`;
        }
    } catch (e) {
        console.error("PR widget error:", e);
        container.innerHTML = `<div style="color:var(--error); font-size:.78rem; padding:8px;">Failed to load PRs</div>`;
    }
}

// Auto-load PR widget if element exists
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("gh-pr-list")) {
        loadPRStatusWidget();
        setInterval(loadPRStatusWidget, 30000); // refresh every 30s
    }
});
