#!/bin/bash

# Visual Testing Workflow - Automated Health Check
# This script validates all components of the system

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Visual Testing Workflow - Comprehensive Health Check        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0
WARN=0

# Function to print status
print_status() {
    local status=$1
    local message=$2
    
    if [ "$status" == "PASS" ]; then
        echo "  ✅ $message"
        ((PASS++))
    elif [ "$status" == "FAIL" ]; then
        echo "  ❌ $message"
        ((FAIL++))
    else
        echo "  ⚠️  $message"
        ((WARN++))
    fi
}

echo "📋 Phase 1: Local Environment"
echo "─────────────────────────────────────────────────────────────────"

# Test 1.1: Flask App
if curl -s http://127.0.0.1:7860 > /dev/null 2>&1; then
    print_status "PASS" "Flask app is running on port 7860"
else
    print_status "FAIL" "Flask app is NOT running"
fi

# Test 1.2: Git Repository
if git status > /dev/null 2>&1; then
    print_status "PASS" "Git repository initialized"
    
    # Check remote
    if git remote -v | grep -q "origin"; then
        print_status "PASS" "Git remote 'origin' configured"
    else
        print_status "FAIL" "Git remote not configured"
    fi
    
    # Check branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" == "main" ] || [ "$current_branch" == "master" ]; then
        print_status "PASS" "On main/master branch ($current_branch)"
    else
        print_status "WARN" "On branch: $current_branch (not main)"
    fi
else
    print_status "FAIL" "Not a git repository"
fi

echo ""
echo "📋 Phase 2: Required Files"
echo "─────────────────────────────────────────────────────────────────"

# Test 2.1: Workflow file
if [ -f ".github/workflows/visual_tests.yml" ]; then
    print_status "PASS" "GitHub Actions workflow file exists"
    
    # Check if committed
    if git ls-files --error-unmatch ".github/workflows/visual_tests.yml" > /dev/null 2>&1; then
        print_status "PASS" "Workflow file is committed"
    else
        print_status "WARN" "Workflow file exists but not committed"
    fi
else
    print_status "FAIL" "Workflow file missing: .github/workflows/visual_tests.yml"
fi

# Test 2.2: Config file
if [ -f "auto_test_config.json" ]; then
    print_status "PASS" "auto_test_config.json exists"
else
    print_status "WARN" "auto_test_config.json not found"
fi

# Test 2.3: Baseline directory
if [ -d "tests/baselines" ]; then
    baseline_count=$(find tests/baselines -name "*.png" 2>/dev/null | wc -l | xargs)
    if [ "$baseline_count" -gt 0 ]; then
        print_status "PASS" "Baseline images found ($baseline_count files)"
    else
        print_status "WARN" "Baseline directory exists but no images found"
    fi
else
    print_status "WARN" "Baseline directory not found (tests/baselines/)"
fi

# Test 2.4: Test runner script
if [ -f "run_automated_tests.py" ]; then
    print_status "PASS" "Test runner script exists"
else
    print_status "FAIL" "Test runner script missing"
fi

echo ""
echo "📋 Phase 3: API Endpoints"
echo "─────────────────────────────────────────────────────────────────"

# Test 3.1: Git status endpoint
response=$(curl -s -w "\n%{http_code}" http://127.0.0.1:7860/api/git/status 2>/dev/null)
http_code=$(echo "$response" | tail -n 1)
if [ "$http_code" == "200" ]; then
    print_status "PASS" "API endpoint /api/git/status responds"
else
    print_status "FAIL" "API endpoint /api/git/status failed (HTTP $http_code)"
fi

# Test 3.2: Main page
response=$(curl -s -w "\n%{http_code}" http://127.0.0.1:7860 2>/dev/null)
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)
if [ "$http_code" == "200" ] && echo "$body" | grep -q "Visual Testing"; then
    print_status "PASS" "Main UI loads correctly"
else
    print_status "FAIL" "Main UI failed to load"
fi

echo ""
echo "📋 Phase 4: Dependencies"
echo "─────────────────────────────────────────────────────────────────"

# Test 4.1: Python packages
if command -v python3 > /dev/null 2>&1; then
    print_status "PASS" "Python 3 is installed"
    
    # Check specific packages (in venv)
    if [ -d ".venv" ]; then
        print_status "PASS" "Virtual environment exists"
    else
        print_status "WARN" "No virtual environment found"
    fi
else
    print_status "FAIL" "Python 3 not found"
fi

# Test 4.2: Git
if command -v git > /dev/null 2>&1; then
    git_version=$(git --version | cut -d' ' -f3)
    print_status "PASS" "Git is installed (v$git_version)"
else
    print_status "FAIL" "Git not installed"
fi

echo ""
echo "📋 Phase 5: GitHub Integration"
echo "─────────────────────────────────────────────────────────────────"

# Test 5.1: GitHub remote
remote_url=$(git remote get-url origin 2>/dev/null)
if [ -n "$remote_url" ]; then
    print_status "PASS" "GitHub remote configured"
    echo "           Remote: $remote_url"
else
    print_status "FAIL" "GitHub remote not configured"
fi

# Test 5.2: Uncommitted changes
if git diff --quiet && git diff --cached --quiet; then
    print_status "PASS" "Working tree is clean"
else
    uncommitted=$(git status --short | wc -l | xargs)
    print_status "WARN" "Working tree has $uncommitted uncommitted change(s)"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                         SUMMARY                                ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  ✅ Passed:  $PASS                                              "
echo "║  ❌ Failed:  $FAIL                                              "
echo "║  ⚠️  Warnings: $WARN                                             "
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 Status: ALL CRITICAL TESTS PASSED!"
    echo ""
    echo "✅ Your visual testing workflow is ready to use!"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Create baselines: Open http://127.0.0.1:7860 → Visual Testing"
    echo "   2. Test push: Click '🚀 Push to GitHub' button"
    echo "   3. Check GitHub: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/' 2>/dev/null || echo 'YOUR-REPO')/actions"
    echo ""
    exit 0
else
    echo "⚠️  Status: SOME TESTS FAILED"
    echo ""
    echo "Please review the failures above and fix them before proceeding."
    echo "Refer to TESTING_GUIDE.md for troubleshooting steps."
    echo ""
    exit 1
fi
