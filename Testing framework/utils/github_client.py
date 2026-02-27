"""
GitHub API Client — Full PR Validation & CI/CD Integration
Handles: commit status, PR comments, issue creation, webhook verification
"""

import json
import os
import hashlib
import hmac
import requests
from datetime import datetime

GITHUB_API = "https://api.github.com"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "github_config.json")


def load_config():
    """Load GitHub config from file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    """Save GitHub config to file."""
    existing = load_config()
    existing.update(data)
    with open(CONFIG_FILE, "w") as f:
        json.dump(existing, f, indent=2)


def get_headers(token: str = None) -> dict:
    cfg = load_config()
    tok = token or cfg.get("token") or os.environ.get("GITHUB_TOKEN", "")
    return {
        "Authorization": f"token {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def test_connection() -> dict:
    """Test GitHub API connection and return user info."""
    cfg = load_config()
    if not cfg.get("token"):
        return {"success": False, "error": "No GitHub token configured"}
    try:
        r = requests.get(f"{GITHUB_API}/user", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {"success": True, "login": d.get("login"), "name": d.get("name")}
        return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Commit Status ───────────────────────────────────────────────────────────

def post_commit_status(sha: str, state: str, description: str,
                       context: str = "visual-regression/qa-framework",
                       target_url: str = "") -> dict:
    """
    Post a commit status check.
    state: 'pending' | 'success' | 'failure' | 'error'
    """
    cfg = load_config()
    owner, repo = cfg.get("owner", ""), cfg.get("repo", "")
    if not owner or not repo:
        return {"success": False, "error": "Owner/repo not configured"}

    payload = {
        "state": state,
        "description": description[:140],
        "context": context,
    }
    if target_url:
        payload["target_url"] = target_url

    url = f"{GITHUB_API}/repos/{owner}/{repo}/statuses/{sha}"
    try:
        r = requests.post(url, headers=get_headers(), json=payload, timeout=15)
        if r.status_code == 201:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── PR Comments ─────────────────────────────────────────────────────────────

def post_pr_comment(pr_number: int, body: str) -> dict:
    """Post or update a comment on a PR."""
    cfg = load_config()
    owner, repo = cfg.get("owner", ""), cfg.get("repo", "")
    if not owner or not repo:
        return {"success": False, "error": "Owner/repo not configured"}

    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    try:
        r = requests.post(url, headers=get_headers(), json={"body": body}, timeout=15)
        if r.status_code == 201:
            return {"success": True, "id": r.json().get("id"), "html_url": r.json().get("html_url")}
        return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_pr_comment(comment_id: int, body: str) -> dict:
    """Update an existing PR comment."""
    cfg = load_config()
    owner, repo = cfg.get("owner", ""), cfg.get("repo", "")
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/comments/{comment_id}"
    try:
        r = requests.patch(url, headers=get_headers(), json={"body": body}, timeout=15)
        if r.status_code == 200:
            return {"success": True}
        return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_bot_comment(pr_number: int, marker: str = "<!-- qa-visual-bot -->") -> int | None:
    """Find an existing bot comment on a PR by looking for a hidden marker."""
    cfg = load_config()
    owner, repo = cfg.get("owner", ""), cfg.get("repo", "")
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    try:
        r = requests.get(url, headers=get_headers(), params={"per_page": 50}, timeout=10)
        if r.status_code == 200:
            for c in r.json():
                if marker in c.get("body", ""):
                    return c["id"]
    except Exception:
        pass
    return None


def upsert_pr_comment(pr_number: int, body: str, marker: str = "<!-- qa-visual-bot -->") -> dict:
    """Create or update bot comment on PR (avoids spam)."""
    existing_id = find_bot_comment(pr_number, marker)
    full_body = f"{marker}\n{body}"
    if existing_id:
        return update_pr_comment(existing_id, full_body)
    return post_pr_comment(pr_number, full_body)


# ─── PR Info ─────────────────────────────────────────────────────────────────

def get_pr_info(pr_number: int) -> dict:
    """Get full PR info including head SHA and labels."""
    cfg = load_config()
    owner, repo = cfg.get("owner", ""), cfg.get("repo", "")
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                "success": True,
                "number": d["number"],
                "title": d["title"],
                "sha": d["head"]["sha"],
                "branch": d["head"]["ref"],
                "base_branch": d["base"]["ref"],
                "author": d["user"]["login"],
                "html_url": d["html_url"],
                "state": d["state"],
                "labels": [l["name"] for l in d.get("labels", [])],
                "body": d.get("body", ""),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            }
        return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_open_prs() -> dict:
    """List open PRs for the configured repo."""
    cfg = load_config()
    owner, repo = cfg.get("owner", ""), cfg.get("repo", "")
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
    try:
        r = requests.get(url, headers=get_headers(), params={"state": "open", "per_page": 30}, timeout=10)
        if r.status_code == 200:
            prs = []
            for d in r.json():
                prs.append({
                    "number": d["number"],
                    "title": d["title"],
                    "sha": d["head"]["sha"],
                    "branch": d["head"]["ref"],
                    "author": d["user"]["login"],
                    "html_url": d["html_url"],
                    "created_at": d.get("created_at"),
                    "draft": d.get("draft", False),
                })
            return {"success": True, "prs": prs}
        return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Issues ──────────────────────────────────────────────────────────────────

def create_issue(title: str, body: str, labels: list = None) -> dict:
    """Create a GitHub issue."""
    cfg = load_config()
    owner, repo = cfg.get("owner", ""), cfg.get("repo", "")
    if not owner or not repo:
        return {"success": False, "error": "Owner/repo not configured"}

    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    try:
        r = requests.post(url, headers=get_headers(), json=payload, timeout=15)
        if r.status_code == 201:
            d = r.json()
            return {"success": True, "number": d["number"], "html_url": d["html_url"]}
        return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Webhook Verification ─────────────────────────────────────────────────────

def verify_webhook_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    if not signature_header or not secret:
        return False
    try:
        algo, sig = signature_header.split("=", 1)
        if algo != "sha256":
            return False
        mac = hmac.new(secret.encode(), payload_bytes, hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), sig)
    except Exception:
        return False


# ─── PR Comment Builder ───────────────────────────────────────────────────────

def build_pr_comment(results: list, pr_info: dict, server_url: str = "") -> str:
    """Build a rich Markdown PR comment from visual test results."""
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed
    pass_rate = round(passed / total * 100) if total else 0

    status_emoji = "✅" if failed == 0 else "❌"
    status_text = "All visual checks passed!" if failed == 0 else f"{failed} visual regression(s) detected"

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    pr_link = pr_info.get("html_url", "")
    pr_title = pr_info.get("title", "")

    lines = [
        f"## {status_emoji} Visual Regression Test Report",
        f"",
        f"> **PR:** [{pr_title}]({pr_link})  ",
        f"> **Branch:** `{pr_info.get('branch', 'unknown')}` → `{pr_info.get('base_branch', 'main')}`  ",
        f"> **Commit:** `{pr_info.get('sha', '')[:8]}`  ",
        f"> **Triggered:** {now}",
        f"",
        f"### 📊 Summary",
        f"",
        f"| Metric | Value |",
        f"|:-------|:------|",
        f"| Total URLs Tested | `{total}` |",
        f"| ✅ Passed | `{passed}` |",
        f"| ❌ Failed | `{failed}` |",
        f"| Pass Rate | `{pass_rate}%` |",
        f"",
    ]

    if results:
        lines += [
            "### 🔍 Per-URL Results",
            "",
            "| URL | SSIM | Changed | Issues | Status | Report |",
            "|:----|:-----|:--------|:-------|:-------|:-------|",
        ]
        for r in results:
            url = r.get("url", "–")
            ssim = f"`{r['ssim']:.4f}`" if r.get("ssim") is not None else "–"
            change = f"`{r['change_ratio']*100:.1f}%`" if r.get("change_ratio") is not None else "–"
            issues = str(r.get("num_regions", "–"))
            status = "✅ Pass" if r.get("passed") else "❌ Fail"
            report = f"[View]({server_url}/download/{r['job_id']}/report.pdf)" if r.get("job_id") and server_url else "–"
            lines.append(f"| {url[:60]} | {ssim} | {change} | {issues} | {status} | {report} |")

    if failed > 0:
        lines += [
            "",
            "### ⚠️ Failed Checks",
            "",
        ]
        for r in results:
            if not r.get("passed"):
                lines.append(f"- **{r.get('url', 'Unknown URL')}**  ")
                if r.get("error"):
                    lines.append(f"  - Error: {r['error']}")
                else:
                    lines.append(f"  - SSIM: `{r.get('ssim', 'N/A')}`, Changed: `{r.get('change_ratio', 0)*100:.1f}%`, Regions: `{r.get('num_regions', 0)}`")
                    if server_url and r.get("job_id"):
                        lines.append(f"  - 📥 [Download Report]({server_url}/download/{r['job_id']}/report.pdf)")
                lines.append("")

    lines += [
        "",
        "---",
        f"*🤖 Generated by [QA Testing Framework](https://github.com/{load_config().get('owner','')}/{load_config().get('repo','')}) — Visual Regression Engine v3.0*",
    ]
    return "\n".join(lines)
