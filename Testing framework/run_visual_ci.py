#!/usr/bin/env python3
"""
CI/CD Visual Testing Runner — v3.0
Runs on GitHub Actions when a PR is opened/updated.
Accepts a deployed staging URL from the PR, runs visual tests
against stored baselines, and posts results back to the PR.

Usage:
  python run_visual_ci.py \
    --staging-url https://pr-123.staging.example.com \
    --pr-number 123 \
    --sha abc1234 \
    --output ci_results \
    [--config ci_visual_config.json] \
    [--baseline-dir baselines] \
    [--server-url https://qa.internal.example.com] \
    [--noise-tolerance medium] \
    [--threshold 0.85]
"""

import sys
import os
import json
import argparse
import datetime
import shutil
import signal
import tempfile

# Graceful pipe handling
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except Exception:
    pass

# ---------------------------------------------------------------------------
# Ensure we can import from utils/ no matter where the script is run from
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from utils.screenshot import capture_screenshot
from utils.image_compare import compare_images
from utils.report import build_pdf_report

try:
    from utils.github_client import (
        post_commit_status,
        upsert_pr_comment,
        get_pr_info,
        build_pr_comment,
        load_config as load_gh_config,
    )
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("⚠️  GitHub client not found — GitHub integration disabled", file=sys.stderr)


# ─── Config Loaders ─────────────────────────────────────────────────────────

def load_ci_config(path: str) -> dict:
    """Load CI visual test configuration."""
    defaults = {
        "threshold": {"ssim_min": 0.85, "change_ratio_max": 0.05, "fail_on_any": True},
        "urls_to_test": [],
        "noise_tolerance": "medium",
        "viewport": "1440x900",
        "wait_time_ms": 1500,
        "check_layout": True,
        "check_content": True,
        "check_colors": True,
        "ignore_selectors": [],
        "remove_selectors": [],
    }
    if path and os.path.exists(path):
        with open(path) as f:
            cfg = json.load(f)
        defaults.update(cfg)
    return defaults


def load_baseline_map(baseline_dir: str) -> dict:
    """
    Load baseline index from <baseline_dir>/baseline_index.json
    Format: { "url_slug": { "path": "baselines/homepage.png", "url": "https://..." } }
    """
    index_path = os.path.join(baseline_dir, "baseline_index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return json.load(f)
    # Fallback: scan for .png files and build a simple map
    result = {}
    for fname in os.listdir(baseline_dir):
        if fname.endswith(".png"):
            slug = fname.replace(".png", "")
            result[slug] = {"path": os.path.join(baseline_dir, fname), "url": ""}
    return result


# ─── URL Resolution ──────────────────────────────────────────────────────────

def resolve_url(test_entry: dict, staging_url: str) -> str:
    """
    Resolve the test URL.
    If test_entry has 'path', append to staging_url.
    If it has 'url', use it directly (allows absolute overrides).
    """
    if test_entry.get("url") and test_entry["url"].startswith("http"):
        return test_entry["url"]
    path = test_entry.get("path", "/")
    base = staging_url.rstrip("/")
    return f"{base}{path}"


# ─── Core Test Runner ────────────────────────────────────────────────────────

def run_single_test(test_entry: dict, staging_url: str, baseline_dir: str,
                    output_dir: str, cfg: dict, job_index: int) -> dict:
    """Run one visual test. Returns a result dict."""
    name = test_entry.get("name", f"Test #{job_index}")
    baseline_key = test_entry.get("baseline")
    url = resolve_url(test_entry, staging_url)

    print(f"\n{'─'*60}")
    print(f"[{job_index}] {name}")
    print(f"    URL       : {url}")
    print(f"    Baseline  : {baseline_key}")

    result_base = {
        "name": name,
        "url": url,
        "baseline_key": baseline_key,
        "passed": False,
        "job_id": None,
        "ssim": None,
        "change_ratio": None,
        "num_regions": None,
        "error": None,
        "report_path": None,
    }

    # ── Find Baseline ──
    baseline_map = load_baseline_map(baseline_dir)
    bl = baseline_map.get(baseline_key)
    if not bl:
        msg = f"No baseline found for key '{baseline_key}' in {baseline_dir}"
        print(f"    ⚠️  {msg}")
        result_base["error"] = msg
        result_base["status"] = "skipped"
        return result_base

    baseline_path = bl.get("path", "")
    if not os.path.isabs(baseline_path):
        baseline_path = os.path.join(SCRIPT_DIR, baseline_path)
    if not os.path.exists(baseline_path):
        msg = f"Baseline file missing: {baseline_path}"
        print(f"    ⚠️  {msg}")
        result_base["error"] = msg
        result_base["status"] = "skipped"
        return result_base

    # ── Job Dir ──
    job_id = f"ci_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{job_index:02d}"
    job_dir = os.path.join(output_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Copy baseline to job dir as figma.png
    figma_path = os.path.join(job_dir, "figma.png")
    shutil.copy2(baseline_path, figma_path)

    # ── Screenshot ──
    stage_path = os.path.join(job_dir, "stage.png")
    viewport = test_entry.get("viewport") or cfg.get("viewport", "1440x900")
    wait_time = test_entry.get("wait_time_ms") or cfg.get("wait_time_ms", 1500)
    ignore_sels = test_entry.get("ignore_selectors") or cfg.get("ignore_selectors", [])
    remove_sels = test_entry.get("remove_selectors") or cfg.get("remove_selectors", [])
    component_sel = test_entry.get("component_selector")

    # Fullpage from config
    fullpage = test_entry.get("fullpage", cfg.get("fullpage", True))

    print(f"    📸 Capturing screenshot ({viewport}, fullpage={fullpage}) ...")
    try:
        capture_screenshot(
            url, stage_path,
            viewport=viewport,
            fullpage=fullpage,
            mask_selectors=ignore_sels if isinstance(ignore_sels, list) else [s.strip() for s in ignore_sels.split(",") if s.strip()],
            wait_time=wait_time,
            selector=component_sel,
            remove_selectors=remove_sels if isinstance(remove_sels, list) else [s.strip() for s in remove_sels.split(",") if s.strip()],
        )
    except Exception as e:
        msg = f"Screenshot failed: {e}"
        print(f"    ❌ {msg}")
        result_base["error"] = msg
        result_base["status"] = "failed"
        result_base["job_id"] = job_id
        return result_base

    # ── Compare ──
    print(f"    🔬 Comparing images ...")
    noise_tolerance = test_entry.get("noise_tolerance") or cfg.get("noise_tolerance", "medium")
    check_layout  = test_entry.get("check_layout",  cfg.get("check_layout",  True))
    check_content = test_entry.get("check_content", cfg.get("check_content", True))
    check_colors  = test_entry.get("check_colors",  cfg.get("check_colors",  True))

    try:
        cmp = compare_images(
            figma_path, stage_path, job_dir,
            noise_tolerance=noise_tolerance,
            highlight_diffs=True,
            check_layout=check_layout,
            check_content=check_content,
            check_colors=check_colors,
        )
    except Exception as e:
        msg = f"Comparison failed: {e}"
        print(f"    ❌ {msg}")
        result_base["error"] = msg
        result_base["status"] = "failed"
        result_base["job_id"] = job_id
        return result_base

    # ── Threshold Check ──
    ssim_min = test_entry.get("ssim_min") or cfg["threshold"].get("ssim_min", 0.85)
    change_max = test_entry.get("change_ratio_max") or cfg["threshold"].get("change_ratio_max", 0.05)

    passed = cmp["ssim"] >= ssim_min and cmp["change_ratio"] <= change_max

    print(f"    SSIM: {cmp['ssim']:.4f} (min={ssim_min:.2f}) | Changed: {cmp['change_ratio']*100:.2f}% (max={change_max*100:.1f}%) | Regions: {cmp['num_regions']}")
    print(f"    {'✅ PASSED' if passed else '❌ FAILED'}")

    # ── PDF Report ──
    pdf_path = os.path.join(job_dir, "report.pdf")
    try:
        build_pdf_report(pdf_path=pdf_path, job_id=job_id, stage_url=url, metrics=cmp, figma_path=figma_path)
    except Exception as e:
        print(f"    ⚠️  PDF report failed: {e}")

    return {
        **result_base,
        "job_id": job_id,
        "passed": passed,
        "status": "passed" if passed else "failed",
        "ssim": cmp["ssim"],
        "change_ratio": cmp["change_ratio"],
        "num_regions": cmp["num_regions"],
        "report_path": pdf_path if os.path.exists(pdf_path) else None,
        "diff_overlay": cmp.get("diff_overlay_path"),
        "heatmap_path": cmp.get("heatmap_path"),
    }


# ─── Main CI Run ─────────────────────────────────────────────────────────────

def run_ci(staging_url: str, pr_number: int | None, sha: str | None,
           output_dir: str, config_path: str, baseline_dir: str,
           server_url: str = "", noise_tolerance: str = None,
           ssim_threshold: float = None) -> dict:

    print("=" * 60)
    print("🔬  QA Framework — Visual CI Runner v3.0")
    print("=" * 60)
    print(f"Staging URL : {staging_url}")
    print(f"PR #        : {pr_number or 'N/A'}")
    print(f"SHA         : {sha or 'N/A'}")
    print(f"Output Dir  : {output_dir}")
    print(f"Baseline Dir: {baseline_dir}")

    os.makedirs(output_dir, exist_ok=True)
    cfg = load_ci_config(config_path)
    if noise_tolerance:
        cfg["noise_tolerance"] = noise_tolerance
    if ssim_threshold:
        cfg["threshold"]["ssim_min"] = ssim_threshold

    # ── Post "pending" status immediately ──
    if GITHUB_AVAILABLE and sha:
        post_commit_status(
            sha=sha,
            state="pending",
            description="Visual regression tests are running...",
            context="visual-regression/qa-framework",
            target_url=server_url,
        )
        print("\n⏳ Posted 'pending' commit status to GitHub")

    # ── Determine URLs to test ──
    tests = cfg.get("urls_to_test", [])
    if not tests:
        # If no explicit list, test the staging root
        tests = [{"name": "Homepage", "path": "/", "baseline": "homepage"}]

    # ── Run each test ──
    all_results = []
    for i, test in enumerate(tests, 1):
        if not test.get("enabled", True):
            print(f"\nSkipping (disabled): {test.get('name', f'Test {i}')}")
            continue
        res = run_single_test(test, staging_url, baseline_dir, output_dir, cfg, i)
        all_results.append(res)

    # ── Summary ──
    total   = len(all_results)
    passed  = sum(1 for r in all_results if r.get("passed"))
    failed  = total - passed
    skipped = sum(1 for r in all_results if r.get("status") == "skipped")
    build_should_fail = cfg["threshold"].get("fail_on_any", True) and failed > 0

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} passed, {failed} failed, {skipped} skipped")
    print(f"Build should fail: {build_should_fail}")
    print(f"{'='*60}")

    # ── Save JSON Summary ──
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    summary = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "staging_url": staging_url,
        "pr_number": pr_number,
        "sha": sha,
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "build_should_fail": build_should_fail,
        "tests": all_results,
    }
    results_file = os.path.join(output_dir, f"results_{timestamp}.json")
    # Save safely (strip non-serializable)
    def safe(o):
        if isinstance(o, dict):
            return {k: safe(v) for k, v in o.items() if k not in ("diff_image",)}
        if isinstance(o, list):
            return [safe(i) for i in o]
        return o
    with open(results_file, "w") as f:
        json.dump(safe(summary), f, indent=2, default=str)
    print(f"Results saved: {results_file}")

    # ── GitHub Integration ──
    if GITHUB_AVAILABLE:
        final_state = "success" if not build_should_fail else "failure"
        final_desc  = (f"All {total} visual checks passed" if not build_should_fail
                       else f"{failed}/{total} visual check(s) failed")

        # Post commit status
        if sha:
            post_commit_status(
                sha=sha,
                state=final_state,
                description=final_desc,
                context="visual-regression/qa-framework",
                target_url=f"{server_url}/ci-results/{timestamp}" if server_url else "",
            )
            print(f"\n📡 Posted '{final_state}' commit status to GitHub")

        # Post PR comment
        if pr_number:
            pr_info = get_pr_info(pr_number)
            if not pr_info.get("success"):
                pr_info = {"title": f"PR #{pr_number}", "branch": "unknown", "base_branch": "main",
                           "sha": sha or "", "html_url": "", "success": False}
            comment = build_pr_comment(all_results, pr_info, server_url=server_url)
            res = upsert_pr_comment(pr_number, comment)
            if res.get("success"):
                print(f"💬 Posted PR comment: {res.get('html_url', '')}")
            else:
                print(f"⚠️  Failed to post PR comment: {res.get('error')}")

    return summary


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CI/CD Visual Testing Runner")
    parser.add_argument("--staging-url",      required=True,  help="Base staging URL to test")
    parser.add_argument("--pr-number",        type=int,       default=None, help="PR number for GitHub integration")
    parser.add_argument("--sha",              default=None,   help="Commit SHA for GitHub status checks")
    parser.add_argument("--output",           default="ci_results", help="Output directory")
    parser.add_argument("--config",           default="ci_visual_config.json", help="CI config JSON")
    parser.add_argument("--baseline-dir",     default="design_baselines", help="Baselines directory")
    parser.add_argument("--server-url",       default="", help="Public URL of this QA server (for links in PR comments)")
    parser.add_argument("--noise-tolerance",  default=None,   choices=["strict", "medium", "relaxed"])
    parser.add_argument("--ssim-threshold",   type=float,     default=None)
    args = parser.parse_args()

    results = run_ci(
        staging_url=args.staging_url,
        pr_number=args.pr_number,
        sha=args.sha,
        output_dir=args.output,
        config_path=args.config,
        baseline_dir=args.baseline_dir,
        server_url=args.server_url,
        noise_tolerance=args.noise_tolerance,
        ssim_threshold=args.ssim_threshold,
    )

    if results.get("build_should_fail"):
        print("\n❌ BUILD FAILED — Visual regressions detected")
        sys.exit(1)
    elif results.get("failed", 0) > 0:
        print("\n⚠️  Tests completed — some failures (within threshold)")
        sys.exit(0)
    else:
        print("\n✅ All visual regression tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
