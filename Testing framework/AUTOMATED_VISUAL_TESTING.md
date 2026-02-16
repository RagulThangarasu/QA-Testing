# Automated Visual Testing System

## Overview
This system automatically runs visual regression tests on deployment and fails the build if visual differences exceed a configured threshold. No manual intervention required!

## 🎯 Features

- ✅ **Automatic execution** on push/PR
- ✅ **Threshold-based pass/fail** criteria
- ✅ **GitHub PR comments** with visual results
- ✅ **Commit status checks** integration
- ✅ **Build failure** when threshold exceeded
- ✅ **Artifact storage** for screenshots and diffs
- ✅ **Detailed reporting** in GitHub Actions summary

## 🚀 Quick Start

### 1. Configure Your Tests

Edit `auto_test_config.json`:

```json
{
  "threshold": {
    "max_diff_percentage": 5.0,
    "fail_on_new_elements": true,
    "fail_on_missing_elements": true
  },
  "urls_to_test": [
    {
      "name": "Homepage",
      "url": "https://staging.example.com",
      "baseline": "homepage",
      "enabled": true
    }
  ],
  "notification": {
    "github_status_check": true,
    "github_pr_comment": true,
    "fail_build_on_threshold": true
  }
}
```

### 2. Set Up Baselines

Create baselines using the web interface:
1. Go to `http://127.0.0.1:7860`
2. Navigate to "Manage Baselines"
3. Create named baselines (e.g., "homepage", "login")
4. Save them with descriptive names

Alternatively, use the API:
```bash
curl -X POST http://localhost:7860/api/baseline/save \
  -H "Content-Type: application/json" \
  -d '{
    "name": "homepage",
    "stage_url": "https://staging.example.com",
    "figma_url": "https://figma.com/file/...",
    "label": "Homepage Baseline"
  }'
```

### 3. Push to GitHub

The workflow automatically triggers on:
- Push to `main`, `staging`, or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch

```bash
git add .
git commit -m "Update homepage design"
git push origin main
```

### 4. Monitor Results

**In GitHub Actions:**
- Navigate to Actions tab → "Automated Visual Regression Tests"
- View detailed summary with pass/fail status
- Download artifacts for screenshots and diffs

**In Pull Requests:**
- Automatic comment with test results
- Commit status check (✅ or ❌)
- Build fails if threshold exceeded

## 📊 How It Works

### Workflow Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Code Push/PR Created                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  2. GitHub Actions Triggered                                │
│     - Setup Python & Dependencies                           │
│     - Install Playwright                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Download Baselines                                      │
│     - From previous artifacts OR                            │
│     - From committed baseline files                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Run Automated Tests (run_automated_tests.py)            │
│     - For each URL in config:                               │
│       • Take screenshot of staging URL                      │
│       • Compare against baseline                            │
│       • Calculate diff percentage                           │
│       • Generate diff image                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Check Threshold                                         │
│     - If diff > threshold → Mark as FAILED                  │
│     - If diff ≤ threshold → Mark as PASSED                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Generate Reports                                        │
│     - Upload artifacts (screenshots, diffs, JSON)           │
│     - Create PR comment with results                        │
│     - Update commit status                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Pass/Fail Build                                         │
│     - ✅ Exit 0 if all tests pass                           │
│     - ❌ Exit 1 if threshold exceeded                       │
└─────────────────────────────────────────────────────────────┘
```

## ⚙️ Configuration Options

### Threshold Settings

```json
{
  "threshold": {
    "max_diff_percentage": 5.0,        // Fail if diff > 5%
    "fail_on_new_elements": true,      // Fail if new elements appear
    "fail_on_missing_elements": true   // Fail if elements missing
  }
}
```

### Test URLs

```json
{
  "urls_to_test": [
    {
      "name": "Homepage",                    // Display name
      "url": "https://staging.example.com",  // URL to test
      "baseline": "homepage",                // Baseline name (from baseline_config.json)
      "enabled": true                        // Enable/disable this test
    }
  ]
}
```

### Notification Settings

```json
{
  "notification": {
    "github_status_check": true,      // Create commit status
    "github_pr_comment": true,        // Comment on PRs
    "fail_build_on_threshold": true   // Fail build if threshold exceeded
  }
}
```

## 🔧 Manual Testing

Run tests locally before pushing:

```bash
# Run all configured tests
python run_automated_tests.py

# Custom config and output
python run_automated_tests.py --config my_config.json --output my_results

# Check exit code
python run_automated_tests.py
echo $?  # 0 = pass, 1 = fail
```

## 📁 File Structure

```
Testing framework/
├── auto_test_config.json           # Main configuration
├── baseline_config.json            # Baseline definitions
├── run_automated_tests.py          # Test runner script
├── .github/
│   └── workflows/
│       └── visual_tests.yml        # GitHub Actions workflow
├── ci_test_results/                # Test output (gitignored)
│   ├── results_TIMESTAMP.json      # Test results
│   ├── homepage_TIMESTAMP.png      # Current screenshots
│   └── homepage_TIMESTAMP_diff.png # Diff images
└── baselines/                      # Baseline storage
    └── saved_baselines/
```

## 🎨 Example PR Comment

When tests run on a PR, you'll see:

```
## 🎨 Visual Regression Test Results

| Metric | Value |
|--------|-------|
| Total Tests | 3 |
| ✅ Passed | 2 |
| ❌ Failed | 1 |
| ⚠️ Threshold Exceeded | 1 |

### ❌ Build Failed

Visual differences exceed the configured threshold.

### Test Details

✅ **Homepage**
   - Difference: 2.34%
   - Threshold: 5.0%

✅ **Login Page**
   - Difference: 1.89%
   - Threshold: 5.0%

❌ **Dashboard**
   - Difference: 7.21%
   - Threshold: 5.0%

📊 [View detailed artifacts](https://github.com/your-repo/actions/runs/123)
```

## 🔒 Security Notes

- Baselines are stored as GitHub artifacts (encrypted at rest)
- Test results are only visible to repository collaborators
- No sensitive data in screenshots (configure exclusions if needed)

## 🐛 Troubleshooting

### "No baseline configured"
- Ensure baseline name in `auto_test_config.json` matches `baseline_config.json`
- Create baseline using web interface or API

### "Baseline file missing"
- Check that baseline files exist in expected paths
- Commit baseline files to repository or ensure artifacts are downloaded

### Tests always fail
- Lower threshold in `auto_test_config.json`
- Check if baseline is outdated
- Review diff images in artifacts

### GitHub Actions fails immediately
- Verify `requirements.txt` includes all dependencies
- Check Python version compatibility
- Ensure Playwright can install on Ubuntu

## 📚 Advanced Usage

### Multiple Environments

Create separate configs:
- `auto_test_config.staging.json`
- `auto_test_config.production.json`

Use in workflow:
```yaml
- name: Run staging tests
  run: python run_automated_tests.py --config auto_test_config.staging.json
```

### Custom Thresholds Per Page

Modify the script to support per-URL thresholds:
```json
{
  "urls_to_test": [
    {
      "name": "Homepage",
      "url": "https://staging.example.com",
      "baseline": "homepage",
      "threshold": 3.0  // Override default
    }
  ]
}
```

### Slack/Email Notifications

Add notification step to workflow:
```yaml
- name: Send Slack notification
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Visual tests failed!'
```

## 🎯 Best Practices

1. **Set realistic thresholds** - Start with 5-10%, adjust based on your needs
2. **Regular baseline updates** - Update baselines when designs intentionally change
3. **Test critical pages first** - Prioritize key user journeys
4. **Review failures carefully** - Some differences are intentional (dynamic content)
5. **Use descriptive baseline names** - Makes debugging easier

## 📞 Support

For issues or questions:
1. Check GitHub Actions logs
2. Review test artifacts
3. Verify configuration files
4. Check baseline files exist

---

**Status:** ✅ Fully Automated - Zero Manual Intervention Required!
