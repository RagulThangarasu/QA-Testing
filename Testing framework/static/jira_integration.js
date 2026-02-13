
// ------------------------------------------------------------------
// JIRA INTEGRATION SHARED SCRIPT
// ------------------------------------------------------------------

(function () {
    // Helper to safely show toast if available, else alert
    function notify(msg, isError) {
        if (typeof showToast === 'function') {
            showToast(msg, isError);
        } else {
            console.log(msg);
            if (isError) alert(msg);
        }
    }

    const jiraConfigModal = document.getElementById("jira-config-modal");
    const jiraReportModal = document.getElementById("jira-report-modal");
    const btnSaveJira = document.getElementById("btnSaveJira");
    const btnSendJira = document.getElementById("btnSendJira");
    const navJira = document.getElementById("nav-jira");

    // Open Config Modal
    if (navJira) {
        navJira.onclick = async (e) => {
            e.preventDefault();
            // Load existing config
            try {
                const res = await fetch("/api/jira/config");
                if (res.ok) {
                    const data = await res.json();
                    if (data.server) document.getElementById("jira-server").value = data.server;
                    if (data.email) document.getElementById("jira-email").value = data.email;
                    if (data.project_key) document.getElementById("jira-project").value = data.project_key;
                }
            } catch (err) {
                console.error("Failed to load Jira config", err);
            }
            if (jiraConfigModal) jiraConfigModal.classList.remove("hidden");
        };
    }

    // Save Config
    if (btnSaveJira) {
        btnSaveJira.onclick = async () => {
            const server = document.getElementById("jira-server").value.trim();
            const email = document.getElementById("jira-email").value.trim();
            const token = document.getElementById("jira-token").value.trim();
            const projectKey = document.getElementById("jira-project").value.trim();

            if (!server || !email || !token || !projectKey) {
                notify("All fields are required.", true);
                return;
            }

            const originalText = btnSaveJira.textContent;
            btnSaveJira.textContent = "Testing Connection...";
            btnSaveJira.disabled = true;

            try {
                const res = await fetch("/api/jira/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ server, email, token, project_key: projectKey })
                });

                const data = await res.json();
                if (res.ok) {
                    notify("Jira Connected Successfully!");
                    setTimeout(() => jiraConfigModal.classList.add("hidden"), 1000);
                } else {
                    notify(data.error || "Connection Failed", true);
                }
            } catch (err) {
                notify("Error saving config.", true);
            } finally {
                btnSaveJira.textContent = originalText;
                btnSaveJira.disabled = false;
            }
        };
    }

    let currentJiraIssue = null;

    // Open Report Modal
    window.openJiraReport = function (jobId, filename, label, description) {
        currentJiraIssue = { jobId, filename };

        const summaryInput = document.getElementById("jira-summary");
        const descInput = document.getElementById("jira-desc");

        if (summaryInput) summaryInput.value = `Visual Defect: ${label}`;
        if (descInput) descInput.value = `Visual testing detected a discrepancy.

Issue Type: ${label}
Description: ${description}

See attached screenshot for details.`;

        if (jiraReportModal) jiraReportModal.classList.remove("hidden");
    };

    // Create Issue
    if (btnSendJira) {
        btnSendJira.onclick = async () => {
            if (!currentJiraIssue) return;

            const summary = document.getElementById("jira-summary").value.trim();
            const description = document.getElementById("jira-desc").value.trim();

            if (!summary) {
                notify("Summary is required.", true);
                return;
            }

            const originalText = btnSendJira.textContent;
            btnSendJira.textContent = "Creating Issue...";
            btnSendJira.disabled = true;

            try {
                const res = await fetch("/api/jira/issue", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        job_id: currentJiraIssue.jobId,
                        issue_filename: currentJiraIssue.filename,
                        summary: summary,
                        description: description
                    })
                });

                const data = await res.json();
                if (res.ok) {
                    notify(`Issue Created: ${data.key}`);
                    if (jiraReportModal) jiraReportModal.classList.add("hidden");
                } else {
                    notify(data.error || "Failed to create issue.", true);
                }
            } catch (err) {
                notify("Error creating issue.", true);
            } finally {
                btnSendJira.textContent = originalText;
                btnSendJira.disabled = false;
            }
        };
    }
})();
