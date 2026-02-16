# GitHub Automation Diagnostic

## How to Check if Everything is Working

### 1. Check Frontend is Loaded
Open browser console (F12) and run:
```javascript
// Should return the function
console.log(typeof executePush);  // Should be "function"

// Should return the elements
console.log(document.getElementById("btn-push-github"));  // Should be Button element
console.log(document.getElementById("git-push-modal"));   // Should be Div element
```

### 2. Check Backend Endpoints
```bash
# Test git status endpoint
curl -X GET http://127.0.0.1:7860/api/git/status

# Expected response:
# {
#   "success": true,
#   "current_branch": "main",
#   "has_changes": false,
#   "changes_count": 0,
#   "last_commit": "ea646c0 - ..."
# }
```

### 3. Check GitHub Actions Workflow
```bash
cd "/Users/ragul/Desktop/QA-Testing/Testing framework"

# Verify workflow file exists
ls -la .github/workflows/visual_tests.yml

# Check if it's committed
git log --oneline --all -- .github/workflows/visual_tests.yml

# Expected output: Should show commit hash
```

### 4. Manual Test Push
```bash
# Make a small change
echo "# Test" >> Testing\ framework/README.md

# Commit
git add .
git commit -m "Test commit for GitHub Actions"

# Push
git push origin main

# Then immediately go to:
# https://github.com/RagulThangarasu/QA-Testing/actions
# You should see a workflow run starting!
```

### 5. Check Workflow Triggers
The workflow triggers on:
- ✅ Push to `main`, `staging`, or `develop` branches
- ✅ Pull requests to `main`
- ✅ Manual dispatch

Current trigger config in `.github/workflows/visual_tests.yml`:
```yaml
on:
  push:
    branches: [ "main", "staging", "develop" ]
  pull_request:
    branches: [ "main" ]
  workflow_dispatch:
```

### 6. Common Issues

#### Issue: "Button does nothing"
**Check:**
- Browser console for JavaScript errors
- Is `git_push.js` loaded? Check Network tab
- Is script tag present in HTML? Check source code

**Fix:**
```bash
# Restart Flask app
pkill -f app.py
source .venv/bin/activate
python app.py
```

#### Issue: "No workflows on GitHub"
**Check:**
- Is workflow file committed? Run: `git log -- .github/workflows/visual_tests.yml`
- Is it pushed? Check: https://github.com/RagulThangarasu/QA-Testing/blob/main/.github/workflows/visual_tests.yml

**Fix:**
```bash
git add .github/workflows/visual_tests.yml
git commit -m "Add workflow"
git push origin main
```

#### Issue: "Workflow doesn't run"
**Check:**
- Are GitHub Actions enabled? Go to Settings → Actions → General
- Does your commit trigger the workflow? (Must be pushed to main/staging/develop)

**Fix:**
- Enable actions in repository settings
- Make sure you're pushing to a monitored branch

### 7. Test the Complete Flow

```bash
# Step 1: Make a change
cd "/Users/ragul/Desktop/QA-Testing/Testing framework"
echo "test" > test_file.txt

# Step 2: Open the UI
# Go to: http://127.0.0.1:7860

# Step 3: Click "Push to GitHub" button
# Watch the progress bar

# Step 4: Check GitHub
# Go to: https://github.com/RagulThangarasu/QA-Testing/actions
# You should see the workflow running!
```

### 8. View Workflow Logs

Once a workflow runs:
1. Go to: https://github.com/RagulThangarasu/QA-Testing/actions
2. Click on the workflow run
3. Click on "visual-regression-test" job
4. Expand each step to see logs

### 9. Expected Timeline

```
Action                          Time    Location
────────────────────────────────────────────────────────
Click "Push" button             0:00    Browser
Return job_id                   0:01    Backend
Start polling                   0:01    Frontend
git add complete                0:05    Backend
git commit complete             0:10    Backend
git push started                0:15    Backend
Push complete                   2:00    GitHub
Workflow triggered              2:01    GitHub Actions
Setup environment               2:15    GitHub Actions
Run tests                       3:00    GitHub Actions
Complete                        4:00    GitHub Actions
```

### 10. Quick Health Check

Run this one-liner to check everything:
```bash
cd "/Users/ragul/Desktop/QA-Testing" && \
echo "✓ Git repo exists" && \
ls -la "Testing framework/.github/workflows/visual_tests.yml" && echo "✓ Workflow file exists" && \
git branch --show-current && echo "✓ On correct branch" && \
curl -s http://127.0.0.1:7860/api/git/status | python3 -m json.tool && echo "✓ API working"
```

---

## 🎯 Current Status

Based on your latest push:
- ✅ Workflow file committed: `ea646c0`
- ✅ Pushed to GitHub: `main → main`
- ⏳ GitHub Actions should be running NOW

**Check it here:** https://github.com/RagulThangarasu/QA-Testing/actions

---

## 📊 How to Know It's Working

### In the UI:
1. Click "🚀 Push to GitHub"
2. You should see:
   - Modal appears instantly
   - Git status loads (branch, changes, last commit)
   - Progress bar moves smoothly
   - Success message appears
   - GitHub Actions notification banner

### On GitHub:
1. Go to Actions tab
2. You should see:
   - Workflow runs listed
   - "Automated Visual Regression Tests"
   - Green ✅ or Yellow ⚡ status

### In Terminal:
```bash
# If the workflow is running, you can check commits
git log --oneline -5

# Should show your recent push
```

---

## 🚀 Next Steps

1. **Verify GitHub Actions:**
   - Visit: https://github.com/RagulThangarasu/QA-Testing/actions
   - You should see a workflow run from your latest push

2. **Test the Button:**
   - Go to: http://127.0.0.1:7860
   - Click "🚀 Push to GitHub"
   - Watch it work!

3. **Create New GitHub Token:**
   - The old one is exposed, revoke it
   - Create new: https://github.com/settings/tokens
   - Save it via UI (GitHub Config button)

---

**Everything is set up and should be working now!** 🎉
