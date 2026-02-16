// Git Push Integration for Visual Testing Tool

document.getElementById("btn-push-github").addEventListener("click", openGitPushModal);
document.getElementById("btnExecutePush").addEventListener("click", executePush);

function openGitPushModal() {
    const modal = document.getElementById("git-push-modal");
    modal.classList.remove("hidden");

    // Load current git status
    loadGitStatus();
}

async function loadGitStatus() {
    try {
        const response = await fetch("/api/git/status");
        const data = await response.json();

        if (data.success) {
            document.getElementById("git-current-branch").textContent = data.current_branch;
            document.getElementById("git-changes-count").textContent = data.has_changes
                ? `${data.changes_count} file(s) modified`
                : "No uncommitted changes";
            document.getElementById("git-last-commit").textContent = data.last_commit;

            // Update branch input
            document.getElementById("git-branch").value = data.current_branch;

            // Update button state
            const pushBtn = document.getElementById("btnExecutePush");
            if (!data.has_changes) {
                pushBtn.disabled = true;
                pushBtn.textContent = "No Changes to Push";
            } else {
                pushBtn.disabled = false;
                pushBtn.textContent = "Push Changes";
            }
        } else {
            showToast("Git status check failed: " + data.error, true);
        }
    } catch (error) {
        console.error("Failed to load git status:", error);
        showToast("Failed to load git status", true);
    }
}

async function executePush() {
    const commitMessage = document.getElementById("git-commit-message").value.trim();
    const branch = document.getElementById("git-branch").value.trim();

    if (!commitMessage) {
        showToast("Please enter a commit message", true);
        return;
    }

    const pushBtn = document.getElementById("btnExecutePush");
    const progressDiv = document.getElementById("git-push-progress");
    const progressFill = document.getElementById("git-push-progress-fill");
    const statusText = document.getElementById("git-push-status");

    // Disable button and show progress
    pushBtn.disabled = true;
    pushBtn.textContent = "Pushing...";
    progressDiv.classList.remove("hidden");
    progressFill.style.width = "0%";
    progressFill.style.background = "";
    statusText.style.color = "#666";

    try {
        // Start the push (returns immediately with job_id)
        statusText.textContent = "🚀 Starting push...";

        const response = await fetch("/api/git/push", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                commit_message: commitMessage,
                branch: branch
            })
        });

        const data = await response.json();

        if (!data.success) {
            // Immediate error (e.g., not a git repo)
            progressFill.style.width = "100%";
            progressFill.style.background = "var(--error)";
            statusText.textContent = "❌ " + data.error;
            statusText.style.color = "var(--error)";
            showToast("Push failed: " + data.error, true);
            pushBtn.disabled = false;
            pushBtn.textContent = "Retry Push";
            return;
        }

        // Got job_id, now poll for status
        const jobId = data.job_id;
        statusText.textContent = "📡 Connecting...";

        await pollGitPushStatus(jobId, progressFill, statusText, pushBtn);

    } catch (error) {
        console.error("Push error:", error);
        showToast("Failed to push: " + error.message, true);

        progressFill.style.width = "100%";
        progressFill.style.background = "var(--error)";
        statusText.textContent = "❌ " + error.message;
        statusText.style.color = "var(--error)";

        pushBtn.disabled = false;
        pushBtn.textContent = "Retry Push";
    }
}

async function pollGitPushStatus(jobId, progressFill, statusText, pushBtn) {
    let attempts = 0;
    const maxAttempts = 120; // 2 minutes with 1 second intervals

    while (attempts < maxAttempts) {
        try {
            const statusResponse = await fetch(`/api/status/${jobId}`);
            const statusData = await statusResponse.json();

            if (!statusData) {
                await sleep(1000);
                attempts++;
                continue;
            }

            // Update progress
            const progress = statusData.progress || 0;
            progressFill.style.width = progress + "%";
            statusText.textContent = statusData.step || "Processing...";

            // Check if completed
            if (statusData.status === "completed") {
                progressFill.style.width = "100%";
                statusText.textContent = "✅ " + (statusData.result?.message || "Success!");
                statusText.style.color = "#10b981";

                showToast(`✅ Successfully pushed to GitHub! Automated tests will run shortly.`);

                // Wait a bit then close modal
                await sleep(1500);
                document.getElementById("git-push-modal").classList.add("hidden");

                // Reset progress
                await sleep(300);
                document.getElementById("git-push-progress").classList.add("hidden");
                progressFill.style.width = "0%";
                pushBtn.disabled = false;
                pushBtn.textContent = "Push Changes";

                // Show GitHub Actions info
                showGitHubActionsInfo();
                return;
            }

            // Check if failed
            if (statusData.status === "failed") {
                progressFill.style.width = "100%";
                progressFill.style.background = "var(--error)";
                statusText.textContent = "❌ " + (statusData.error || "Push failed");
                statusText.style.color = "var(--error)";

                showToast("Push failed: " + statusData.error, true);

                // Re-enable button after delay
                await sleep(3000);
                pushBtn.disabled = false;
                pushBtn.textContent = "Retry Push";
                return;
            }

            // Still running, wait and poll again
            await sleep(1000);
            attempts++;

        } catch (error) {
            console.error("Polling error:", error);
            attempts++;
            await sleep(1000);
        }
    }

    // Timeout
    progressFill.style.width = "100%";
    progressFill.style.background = "var(--error)";
    statusText.textContent = "❌ Operation timed out";
    statusText.style.color = "var(--error)";
    showToast("Push timed out. Check git status manually.", true);
    pushBtn.disabled = false;
    pushBtn.textContent = "Retry Push";
}

function showGitHubActionsInfo() {
    // Create a temporary info banner
    const banner = document.createElement("div");
    banner.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;

    banner.innerHTML = `
        <div style="display: flex; align-items: start; gap: 12px;">
            <span style="font-size: 24px;">🤖</span>
            <div>
                <div style="font-weight: bold; margin-bottom: 4px;">GitHub Actions Triggered!</div>
                <div style="font-size: 13px; opacity: 0.9;">
                    Your automated visual tests are now running. 
                    Check the <a href="https://github.com" target="_blank" 
                       style="color: white; text-decoration: underline;">Actions tab</a> on GitHub.
                </div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="background: none; border: none; color: white; cursor: pointer; font-size: 20px; padding: 0; margin-left: auto;">×</button>
        </div>
    `;

    document.body.appendChild(banner);

    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (banner.parentElement) {
            banner.remove();
        }
    }, 10000);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Add animation styles if not already present
if (!document.querySelector('style[data-git-push-styles]')) {
    const style = document.createElement('style');
    style.setAttribute('data-git-push-styles', 'true');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}
