#!/usr/bin/env python3
"""
Automated Visual Testing Runner
Runs visual tests and reports results for CI/CD integration
"""
import sys
import os
import json
import argparse
from datetime import datetime
from playwright.sync_api import sync_playwright
from utils.figma_extractor import extract_figma_design
from utils.screenshot_comparison import compare_screenshots

def load_config(config_path='auto_test_config.json'):
    """Load automated test configuration"""
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)

def load_baseline_config(baseline_config_path='baseline_config.json'):
    """Load baseline configuration"""
    if not os.path.exists(baseline_config_path):
        return {}
    
    with open(baseline_config_path, 'r') as f:
        return json.load(f)

def take_screenshot(url, output_path, viewport_width=1440, viewport_height=900):
    """Take screenshot of a URL"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': viewport_width, 'height': viewport_height})
        page = context.new_page()
        
        try:
            page.goto(url, timeout=30000, wait_until='networkidle')
            page.screenshot(path=output_path, full_page=False)
            print(f"✓ Screenshot saved: {output_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to screenshot {url}: {e}")
            return False
        finally:
            browser.close()

def run_automated_tests(config_path='auto_test_config.json', output_dir='ci_test_results'):
    """Run all configured visual tests"""
    config = load_config(config_path)
    baseline_config = load_baseline_config()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    results = {
        'timestamp': timestamp,
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'threshold_exceeded': 0,
        'tests': [],
        'build_should_fail': False
    }
    
    threshold = config['threshold']['max_diff_percentage']
    
    # Run each test
    for test in config['urls_to_test']:
        if not test.get('enabled', True):
            continue
        
        results['total_tests'] += 1
        test_name = test['name']
        url = test['url']
        baseline_name = test['baseline']
        
        print(f"\n{'='*60}")
        print(f"Testing: {test_name}")
        print(f"URL: {url}")
        print(f"Baseline: {baseline_name}")
        print(f"{'='*60}")
        
        # Get baseline path
        baseline_info = baseline_config.get('baselines', {}).get(baseline_name)
        if not baseline_info:
            print(f"⚠️  No baseline found for '{baseline_name}'. Skipping...")
            results['tests'].append({
                'name': test_name,
                'status': 'skipped',
                'reason': 'No baseline configured'
            })
            continue
        
        baseline_path = baseline_info.get('screenshot_path')
        if not baseline_path or not os.path.exists(baseline_path):
            print(f"⚠️  Baseline file not found: {baseline_path}")
            results['tests'].append({
                'name': test_name,
                'status': 'skipped',
                'reason': 'Baseline file missing'
            })
            continue
        
        # Take current screenshot
        current_screenshot = os.path.join(output_dir, f"{baseline_name}_{timestamp}.png")
        if not take_screenshot(url, current_screenshot):
            results['failed'] += 1
            results['tests'].append({
                'name': test_name,
                'status': 'failed',
                'reason': 'Screenshot failed'
            })
            continue
        
        # Compare screenshots
        print(f"Comparing against baseline...")
        comparison = compare_screenshots(baseline_path, current_screenshot)
        
        diff_percentage = comparison['diff_percentage']
        print(f"Diff: {diff_percentage:.2f}% (Threshold: {threshold}%)")
        
        # Save diff image
        if comparison.get('diff_image'):
            diff_path = os.path.join(output_dir, f"{baseline_name}_{timestamp}_diff.png")
            comparison['diff_image'].save(diff_path)
            print(f"Diff image saved: {diff_path}")
        
        # Check threshold
        test_result = {
            'name': test_name,
            'url': url,
            'baseline': baseline_name,
            'diff_percentage': diff_percentage,
            'threshold': threshold,
            'current_screenshot': current_screenshot,
            'baseline_screenshot': baseline_path,
            'diff_image': diff_path if comparison.get('diff_image') else None
        }
        
        if diff_percentage <= threshold:
            print(f"✅ PASSED - Within threshold")
            results['passed'] += 1
            test_result['status'] = 'passed'
        else:
            print(f"❌ FAILED - Exceeds threshold ({diff_percentage:.2f}% > {threshold}%)")
            results['failed'] += 1
            results['threshold_exceeded'] += 1
            test_result['status'] = 'failed'
            
            if config['notification']['fail_build_on_threshold']:
                results['build_should_fail'] = True
        
        results['tests'].append(test_result)
    
    # Save results
    results_file = os.path.join(output_dir, f'results_{timestamp}.json')
    with open(results_file, 'w') as f:
        # Remove non-serializable items
        safe_results = {k: v for k, v in results.items() if k != 'tests'}
        safe_results['tests'] = []
        for test in results['tests']:
            safe_test = {k: v for k, v in test.items() if k != 'diff_image'}
            safe_results['tests'].append(safe_test)
        json.dump(safe_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Threshold Exceeded: {results['threshold_exceeded']}")
    print(f"\nResults saved to: {results_file}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Automated Visual Testing Runner')
    parser.add_argument('--config', default='auto_test_config.json', help='Path to config file')
    parser.add_argument('--output', default='ci_test_results', help='Output directory')
    
    args = parser.parse_args()
    
    print("🔍 Starting Automated Visual Tests...")
    results = run_automated_tests(args.config, args.output)
    
    # Exit with appropriate code
    if results['build_should_fail']:
        print("\n❌ BUILD FAILED - Visual differences exceed threshold")
        sys.exit(1)
    elif results['failed'] > 0:
        print("\n⚠️  Tests completed with failures (but within threshold)")
        sys.exit(0)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()
