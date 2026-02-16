document.getElementById("nav-github").addEventListener("click", openGitHubConfig);
document.getElementById("btnSaveGitHub").addEventListener("click", saveGitHubConfig);
document.getElementById("btnSendGitHub").addEventListener("click", createGitHubIssue);

function openGitHubConfig() {
    const modal = document.getElementById("github-config-modal");
    modal.classList.remove("hidden");

    // Load existing
    fetch("/api/github/config")
        .then(res => res.json())
        .then(data => {
            if (data.token) {
                document.getElementById("gh-token").value = data.token;
                document.getElementById("gh-owner").value = data.owner || "";
                document.getElementById("gh-repo").value = data.repo || "";
            }
        });
}

function saveGitHubConfig() {
    const token = document.getElementById("gh-token").value;
    const owner = document.getElementById("gh-owner").value;
    const repo = document.getElementById("gh-repo").value;

    if (!token || !owner || !repo) {
        showToast("All fields are required", true);
        return;
    }

    fetch("/api/github/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, owner, repo })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("GitHub configured & connected!");
                document.getElementById("github-config-modal").classList.add("hidden");
            } else {
                showToast(data.error || "Failed to connect", true);
            }
        })
        .catch(err => showToast("Error saving config", true));
}

// Global function to trigger issue modal (called from app.js)
window.openGitHubReport = function (jobId, filename, label, description) {
    const modal = document.getElementById("github-report-modal");
    modal.classList.remove("hidden");

    // Prefill
    document.getElementById("gh-title").value = `Visual Regression: ${label || filename}`;

    const desc = `Visual difference detected in ${filename}.
    
**Details:**
- Label: ${label || 'N/A'}
- Description: ${description || 'N/A'}
- Job ID: ${jobId}

_Reported via Visual Testing Tool_`;

    document.getElementById("gh-body").value = desc;

    // Store context on the button for sending
    const btn = document.getElementById("btnSendGitHub");
    btn.dataset.jobId = jobId;
    btn.dataset.filename = filename;
}

function createGitHubIssue() {
    const btn = document.getElementById("btnSendGitHub");
    const jobId = btn.dataset.jobId;
    const filename = btn.dataset.filename;

    const title = document.getElementById("gh-title").value;
    const body = document.getElementById("gh-body").value;

    if (!title) {
        showToast("Title is required", true);
        return;
    }

    btn.disabled = true;
    btn.textContent = "Creating...";

    fetch("/api/github/issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            title,
            body,
            job_id: jobId,
            issue_filename: filename
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(`Issue created! #${data.number}`);
                document.getElementById("github-report-modal").classList.add("hidden");
                // clear inputs
                document.getElementById("gh-title").value = "";
                document.getElementById("gh-body").value = "";
            } else {
                showToast(data.error || "Failed to create issue", true);
            }
        })
        .catch(err => showToast("Error creating issue", true))
        .finally(() => {
            btn.disabled = false;
            btn.textContent = "Create Issue";
        });
}
