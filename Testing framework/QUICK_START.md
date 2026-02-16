# 🚀 Quick Start: Automated Visual Testing

Get your automated visual testing running in 5 minutes!

## Step 1: Setup Configuration (2 minutes)

Run the interactive setup:

```bash
python setup_automated_tests.py
```

This will ask you for:
- URLs to test
- Baseline names
- Threshold settings

## Step 2: Create Baselines (2 minutes)

### Option A: Via Web Interface (Recommended)
1. Start the app: `python app.py`
2. Go to http://127.0.0.1:7860
3. Click "Manage Baselines"
4. Create baselines with names matching your config
5. Save them

### Option B: Via Command Line
```bash
# Example: Take screenshot and save as baseline
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto('https://staging.example.com')
    page.screenshot(path='baselines/saved_baselines/homepage.png')
    browser.close()
"
```

Then update` baseline_config.json`:
```json
{
  "baselines": {
    "homepage": {
      "screenshot_path": "baselines/saved_baselines/homepage.png",
      "label": "Homepage Baseline",
      "timestamp": "2026-02-16T12:00:00"
    }
  }
}
```

## Step 3: Test Locally (30 seconds)

```bash
python run_automated_tests.py
```

Expected output:
```
🔍 Starting Automated Visual Tests...
============================================================
Testing: Homepage
URL: https://staging.example.com
Baseline: homepage
============================================================
✓ Screenshot saved: ci_test_results/homepage_20260216_120000.png
Comparing against baseline...
Diff: 2.34% (Threshold: 5.0%)
✅ PASSED - Within threshold
Diff image saved: ci_test_results/homepage_20260216_120000_diff.png

============================================================
SUMMARY
============================================================
Total Tests: 1
Passed: 1
Failed: 0
Threshold Exceeded: 0

✅ All tests passed!
```

## Step 4: Push to GitHub (30 seconds)

```bash
git add .
git commit -m "🎨 Add automated visual testing"
git push origin main
```

## Step 5: Watch It Work! ☕

1. Go to GitHub → Actions tab
2. See "Automated Visual Regression Tests" running
3. Watch the workflow execute automatically
4. View results in the summary

**That's it! No more manual intervention needed!**

---

## What Happens on Every Push?

```
You push code
    ↓
GitHub Actions starts
    ↓
Tests run automatically
    ↓
Screenshots compared
    ↓
Results posted to PR
    ↓
Build passes or fails
    ↓
You review (only if failed)
```

## Example GitHub Status

### ✅ When tests pass:
```
✓ Visual Regression Tests — Visual tests passed
  All 3 tests passed with differences below threshold
```

### ❌ When tests fail:
```
✗ Visual Regression Tests — Visual differences exceed threshold  
  2/3 tests passed, 1 exceeded threshold (7.2% > 5.0%)
  Review diff images in artifacts
```

## Common Commands

```bash
# Test locally
python run_automated_tests.py

# Setup new tests
python setup_automated_tests.py

# Check results
ls ci_test_results/

# View latest results
cat ci_test_results/results_*.json | jq .
```

## Troubleshooting

**"No baseline found"**
→ Create baseline using web interface or CLI

**"Screenshot failed"**
→ Check URL is accessible
→ Ensure Playwright is installed: `playwright install chromium`

**Tests always fail**
→ Lower threshold in `auto_test_config.json`
→ Update baseline if design changed intentionally

**GitHub Actions fails**
→ Check logs in Actions tab
→ Verify baseline files are committed
→ Ensure `requirements.txt` is up to date

## What's Configured?

After setup, you have:

- ✅ `auto_test_config.json` - Test URLs and thresholds
- ✅ `baseline_config.json` - Baseline image mappings
- ✅ `.github/workflows/visual_tests.yml` - GitHub Actions workflow
- ✅ `run_automated_tests.py` - Test execution script
- ✅ Baselines in `baselines/saved_baselines/`

## Next Steps

1. **Add more test URLs** - Edit `auto_test_config.json`
2. **Adjust thresholds** - Based on your needs
3. **Set up notifications** - Slack, email, etc.
4. **Review regularly** - Check GitHub Actions results

---

**🎉 Congratulations! Your visual testing is now fully automated!**

No more manual screenshot comparisons. Ever. 🚀
