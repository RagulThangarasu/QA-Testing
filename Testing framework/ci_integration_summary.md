## 🚀 Complete Full-Scale GitHub & CI/CD Pipeline

The framework now has a complete visual validation pipeline that hooks directly into GitHub PRs and Actions, giving developers immediate feedback without leaving GitHub.

### 1. `visual_tests.yml` — GitHub Actions Workflow
A robust workflow added to `.github/workflows/visual_tests.yml` that:
- Runs automatically when a PR is opened, updated, or reopened.
- **Auto-detects the staging URL** from PR labels (e.g. `staging-url:https://...`), or falls back to repository secrets.
- Runs the test suite in parallel via the newly created `run_visual_ci.py`.
- Evaluates test results based on configurable thresholds (Default: max `5.0%` difference).
- If tests pass, it passes the commit status. If tests fail, it automatically fails the GitHub Actions build.
- **Baseline Promotion:** When PRs are merged securely to `main`, the passing screenshots are saved as the new active baselines automatically.

### 2. `run_visual_ci.py` — The CI Test Runner
A lightweight command-line script added explicitly for executing tests purely in CI environments:
- Reads the `ci_visual_config.json` configuration file.
- Checks `design_baselines/` directory for expected target baselines.
- Generates JSON summary artifacts for the pipeline to parse.

### 3. CI/CD Developer Dashboard (`/ci-dashboard`)
Added an entirely new dashboard directly inside the internal web app (available via top nav)!
- **🔁 PR Runs Tab:** Connects directly to GitHub via API and lists all open PRs in real-time. Select a PR to view its specific visual testing run, see the SSIM scores, and diff percentages. You can manually trigger tests for specific PRs directly from this page.
- **🏗 Pipeline Flow Tab:** A visual mapped guide to exactly how the workflow propagates from GitHub Actions, Webhooks, Image comparison, to the final Report.
- **⚙️ GitHub Setup Tab:** An updated setup panel taking PATs, Repo Owner keys, generating the Webhook URLs that the user can copy/paste directly into GitHub setting, and indicating active connections with real-time API checks.
- **📋 CI Config Tab:** A live IDE-like editor connecting to `ci_visual_config.json` to alter what URLs, sensitivities, and CSS selectors (like cookies/ads) the pipeline should run/ignore during CI validations, eliminating the need to edit the codebase.

### 4. GitHub API Client Extension (`utils/github_client.py`)
Upgraded the backend to not just open tickets, but fully interact with GitHub states:
- **`post_commit_status()`**: Allows the system to post "pending", "success", or "failure" checks directly onto a developers PR commit history timeline.
- **`build_pr_comment()`**: Assembles a beautiful Markdown table populated with test metrics, pass/fail status, and direct download links to the PDF reports.
- **`upsert_pr_comment()`**: Locates previous bot comments inside the PR and edits them rather than spamming the PR with new messages every refresh.

### 5. Webhook Endpoints (`app.py`)
The Flask backend now listens at `POST /api/github/webhook` and implements full HMAC-SHA256 GitHub signature verification security. When a webhook hits indicating a PR was opened, the python server offloads the Playwright visual capture and AI image comparisons off the main thread, acting effectively as its own self-hosted runner.
