# Complete Visual Testing Workflow - Testing Guide

## 🎯 Objective
Verify that the entire automated visual testing workflow is functioning correctly from UI to GitHub Actions.

---

## ✅ Testing Checklist

### Phase 1: Local Setup Verification
### Phase 2: Baseline Creation
### Phase 3: Git Push Test
### Phase 4: GitHub Actions Test
### Phase 5: Visual Regression Test
### Phase 6: End-to-End Test

---

## Phase 1: Local Setup Verification

### Test 1.1: Flask App is Running
```bash
# Check if app is running
curl -s http://127.0.0.1:7860 | head -n 5

# Expected: HTML content with "Visual Testing Studio"
```

**✅ Success Criteria:**
- App responds on port 7860
- Returns HTML page
- No errors in terminal

**❌ If Failed:**
```bash
# Restart app
pkill -f app.py
source .venv/bin/activate
python app.py
```

---

### Test 1.2: Git Repository Status
```bash
# Check git status
git status

# Check remote
git remote -v

# Check current branch
git branch --show-current
```

**✅ Success Criteria:**
- Git repository initialized
- Remote 'origin' configured
- On 'main' branch

**❌ If Failed:**
```bash
# Initialize git if needed
git init
git remote add origin https://github.com/RagulThangarasu/QA-Testing.git
```

---

### Test 1.3: Check Workflow File
```bash
# Verify workflow exists
ls -la .github/workflows/visual_tests.yml

# Check if committed
git log --oneline -1 -- .github/workflows/visual_tests.yml
```

**✅ Success Criteria:**
- File exists
- Shows commit hash

**❌ If Failed:**
```bash
# Commit workflow
git add .github/workflows/visual_tests.yml
git commit -m "Add visual testing workflow"
```

---

## Phase 2: Baseline Creation

### Test 2.1: Create Baselines via UI

**Steps:**
1. Open: http://127.0.0.1:7860
2. Go to "Visual Testing" tab
3. Enter URL: `http://127.0.0.1:7860`
4. Click "Compare"
5. Should see "New baseline created"
6. Click "Accept" or verify baseline saved

**✅ Success Criteria:**
- Screenshot taken
- Baseline saved to `tests/baselines/`
- Success message shown

**Check:**
```bash
# Verify baseline exists
ls -la tests/baselines/

# Should show .png files
```

---

### Test 2.2: Verify Baseline Files

```bash
# List all baselines
find tests/baselines -name "*.png" -type f

# Check file size (should be > 0)
du -h tests/baselines/*.png
```

**✅ Success Criteria:**
- At least 1 .png file exists
- File size > 10 KB
- PNG format valid

---

## Phase 3: Git Push Test

### Test 3.1: UI Push Button

**Steps:**
1. Make a small change:
   ```bash
   echo "# Test" >> README.md
   ```

2. Go to UI: http://127.0.0.1:7860

3. Click "🚀 Push to GitHub" button

4. Modal should open showing:
   - Current branch
   - Number of changes
   - Last commit

5. Enter commit message: "Test automated workflow"

6. Click "Push Changes"

7. Watch progress bar

**✅ Success Criteria:**
- Modal opens successfully
- Git status loads
- Progress bar shows 0% → 100%
- Success message appears
- "GitHub Actions Triggered" notification

**Check in Browser Console (F12):**
```javascript
// Should see these network requests:
POST /api/git/push
// Response: { success: true, steps: [...] }
```

---

### Test 3.2: Verify Push Succeeded

```bash
# Check git status
git status

# Should show: "Your branch is up to date"

# Check GitHub
git log --oneline -5
```

**✅ Success Criteria:**
- Working tree clean
- Latest commit visible
- Pushed to origin/main

---

## Phase 4: GitHub Actions Test

### Test 4.1: Check Workflow Triggered

**Manual Check:**
1. Go to: https://github.com/RagulThangarasu/QA-Testing/actions
2. Look for latest workflow run
3. Should see "Automated Visual Regression Tests"
4. Status: Running (⚡) or Completed (✅/❌)

**Expected Timeline:**
```
0:00 - Workflow triggered
0:15 - Setup Python
0:30 - Install dependencies
1:30 - Install Playwright
2:00 - Run tests
3:00 - Upload artifacts
3:30 - Complete
```

**✅ Success Criteria:**
- Workflow appears in Actions tab
- Started within 1 minute of push
- Status shows "running" or "completed"

---

### Test 4.2: Review Workflow Logs

**Steps:**
1. Click on the workflow run
2. Click on "visual-regression-test" job
3. Expand each step
4. Check for errors

**Key Steps to Verify:**
- ✅ Checkout code
- ✅ Set up Python
- ✅ Install dependencies
- ✅ Run automated visual tests
- ✅ Upload test results

**✅ Success Criteria:**
- All steps complete successfully
- No error messages in logs
- Exit code: 0

**❌ Common Errors:**

**Error: "Baseline not found"**
```
Fix: Create baselines locally and commit:
git add tests/baselines/
git commit -m "Add baselines"
git push origin main
```

**Error: "Module not found"**
```
Fix: Check requirements.txt has all dependencies
```

**Error: "Playwright not found"**
```
Fix: Workflow should run: playwright install
Check .github/workflows/visual_tests.yml
```

---

### Test 4.3: Download Artifacts

**Steps:**
1. Go to workflow run page
2. Scroll to bottom
3. Under "Artifacts" section
4. Click "Download" on "visual-test-results"
5. Unzip file locally

**✅ Success Criteria:**
- Artifact available
- Downloads successfully
- Contains test results

**Expected Files in Artifact:**
```
visual-test-results/
├── latest_report.json
├── screenshots/
│   ├── homepage_baseline.png
│   ├── homepage_current.png
│   └── homepage_diff.png
└── logs/
    └── test_output.log
```

---

## Phase 5: Visual Regression Test

### Test 5.1: Test Passing Scenario (No Changes)

**Setup:**
```bash
# Make sure baselines are committed
git add tests/baselines/
git commit -m "Add baselines"
git push origin main
```

**Expected Result:**
- Workflow runs
- Visual tests pass (diff ≤ 5%)
- Build status: ✅ Green
- Commit status: "All checks passed"

---

### Test 5.2: Test Failing Scenario (Visual Change)

**Steps:**
1. Make a visual change locally:
   ```bash
   # Edit CSS to change button color
   echo "button { background: red !important; }" >> static/styles.css
   ```

2. Don't update baseline

3. Commit and push:
   ```bash
   git add static/styles.css
   git commit -m "Test: Change button color"
   git push origin main
   ```

4. Go to GitHub Actions

**Expected Result:**
- Workflow runs
- Visual tests FAIL (diff > 5%)
- Build status: ❌ Red
- Commit status: "Checks failed"
- Comment/issue created with details

**✅ Success Criteria:**
- System detects visual change
- Build fails as expected
- Clear error message provided
- Diff images available in artifacts

---

### Test 5.3: Test Baseline Update

**Steps:**
1. After test fails (from 5.2)

2. Update baseline via UI:
   - Go to Visual Testing
   - Enter URL
   - Compare
   - Accept as new baseline

3. Commit new baseline:
   ```bash
   git add tests/baselines/
   git commit -m "Update baseline for button color"
   git push origin main
   ```

4. Check GitHub Actions

**Expected Result:**
- Workflow runs
- Visual tests PASS (comparing new vs new)
- Build status: ✅ Green

**✅ Success Criteria:**
- Updated baseline accepted
- Tests pass with new baseline
- Build succeeds

---

## Phase 6: End-to-End Test

### Test 6.1: Complete Developer Workflow

**Scenario:** You're adding a new feature

**Steps:**

1. **Make changes:**
   ```bash
   echo "<h2>New Feature</h2>" >> static/index.html
   ```

2. **Test locally:**
   - Open: http://127.0.0.1:7860
   - Verify change looks good

3. **Update baseline:**
   - Visual Testing tab
   - Compare
   - Accept new baseline

4. **Push via UI:**
   - Click "🚀 Push to GitHub"
   - Message: "Add new feature section"
   - Push

5. **Verify on GitHub:**
   - Check Actions tab
   - Wait for workflow to complete
   - Verify ✅ Green status

**⏱️ Expected Duration:** 3-5 minutes total

**✅ Success Criteria:**
- Change pushed successfully
- Tests run automatically
- Tests pass
- Commit shows green checkmark
- No manual intervention needed

---

## Phase 7: PR Workflow Test

### Test 7.1: Create Pull Request

**Steps:**

1. **Create feature branch:**
   ```bash
   git checkout -b feature/test-pr
   ```

2. **Make change:**
   ```bash
   echo "<!-- PR Test -->" >> static/index.html
   ```

3. **Push to branch:**
   ```bash
   git add .
   git commit -m "Test PR workflow"
   git push origin feature/test-pr
   ```

4. **Create PR on GitHub:**
   - Go to repository
   - Click "Compare & pull request"
   - Create PR

5. **Check PR page:**
   - Should see "Checks" section
   - Visual regression tests running
   - Wait for completion

**Expected on PR:**
```
✅ All checks have passed

Checks:
✅ visual-regression-test (3m 45s)

Comment from workflow (optional):
🎨 Visual Regression Test Results
✅ All visual tests passed!
```

**✅ Success Criteria:**
- Tests run automatically on PR
- Results shown in PR checks
- Comment posted (if configured)
- Green checkmark if tests pass

---

## Troubleshooting Common Issues

### Issue: "Push button does nothing"

**Diagnosis:**
```bash
# Check browser console (F12)
# Look for JavaScript errors
```

**Fix:**
```bash
# Restart Flask app
pkill -f app.py
source .venv/bin/activate
python app.py

# Hard refresh browser: Cmd+Shift+R
```

---

### Issue: "GitHub Actions not running"

**Diagnosis:**
```bash
# Check if workflow is committed
git ls-files .github/workflows/

# Check GitHub Actions enabled
# Go to: Settings → Actions → General
```

**Fix:**
- Enable actions in GitHub repo settings
- Ensure workflow file is committed
- Check branch name triggers match

---

### Issue: "Tests fail with 'baseline not found'"

**Diagnosis:**
```bash
# Check if baselines exist and are committed
git ls-files tests/baselines/
```

**Fix:**
```bash
# Create and commit baselines
# Via UI or manually, then:
git add tests/baselines/
git commit -m "Add baseline images"
git push origin main
```

---

### Issue: "All tests fail with high diff %"

**Possible Causes:**
- Different viewport size
- Fonts not loaded
- Timing issues

**Fix:**
Update `auto_test_config.json`:
```json
{
  "wait_time": 5000,
  "viewport": {
    "width": 1920,
    "height": 1080
  }
}
```

---

## Quick Validation Script

Run this to check everything:

```bash
#!/bin/bash

echo "🔍 Visual Testing Workflow - Health Check"
echo "=========================================="
echo ""

# Check 1: Flask app
echo "✓ Checking Flask app..."
curl -s http://127.0.0.1:7860 > /dev/null && echo "  ✅ App is running" || echo "  ❌ App not running"

# Check 2: Git repo
echo "✓ Checking git repository..."
git status > /dev/null 2>&1 && echo "  ✅ Git repo initialized" || echo "  ❌ Not a git repo"

# Check 3: Workflow file
echo "✓ Checking workflow file..."
[ -f ".github/workflows/visual_tests.yml" ] && echo "  ✅ Workflow file exists" || echo "  ❌ Workflow file missing"

# Check 4: Baselines
echo "✓ Checking baselines..."
[ -d "tests/baselines" ] && [ "$(ls -A tests/baselines/*.png 2>/dev/null)" ] && echo "  ✅ Baselines exist" || echo "  ⚠️  No baselines found"

# Check 5: Config file
echo "✓ Checking config..."
[ -f "auto_test_config.json" ] && echo "  ✅ Config file exists" || echo "  ❌ Config missing"

echo ""
echo "=========================================="
echo "Health check complete!"
```

Save as `check_workflow.sh` and run:
```bash
chmod +x check_workflow.sh
./check_workflow.sh
```

---

## Success Indicators

### ✅ System is Working When:

1. **UI:**
   - Push button works
   - Modal shows git status
   - Progress bar animates
   - Success notification appears

2. **GitHub:**
   - Workflows appear in Actions tab
   - Workflows complete successfully
   - Commit shows green checkmark
   - Artifacts are created

3. **Tests:**
   - Baselines load correctly
   - Screenshots are taken
   - Comparisons complete
   - Pass/fail based on threshold

4. **Integration:**
   - Push → Tests run automatically
   - Results posted to commits/PRs
   - No manual steps needed

---

## Performance Benchmarks

### Expected Timing:

| Action | Duration |
|--------|----------|
| UI Push Click → Response | < 1 second |
| Git Push Complete | 2-10 seconds |
| GitHub Actions Start | < 1 minute |
| Workflow Complete | 3-5 minutes |
| **Total: Push to Result** | **4-6 minutes** |

---

## Final Checklist

Before considering workflow "complete":

- [ ] Flask app runs without errors
- [ ] Baselines created for all test URLs
- [ ] Push button works and shows progress
- [ ] GitHub Actions triggers on push
- [ ] Workflow completes successfully
- [ ] Tests pass with valid baselines
- [ ] Tests fail when visual changes detected
- [ ] Artifacts upload correctly
- [ ] PR checks run automatically
- [ ] Documentation is clear

---

## Next Steps After Testing

Once all tests pass:

1. **Document your baselines:**
   - Note which pages have baselines
   - Document the expected state

2. **Configure notifications:**
   - GitHub → Settings → Notifications
   - Enable Actions notifications

3. **Train your team:**
   - Share documentation
   - Walk through workflow

4. **Set up branch protection:**
   - Require visual tests to pass
   - Prevent merging on failure

---

**Testing Complete!** 🎉

If all phases pass, your automated visual testing workflow is fully operational!

**Version:** 1.0  
**Last Updated:** February 16, 2026
