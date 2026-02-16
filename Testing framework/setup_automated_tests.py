#!/usr/bin/env python3
"""
Quick setup script for automated visual testing
"""
import json
import os
import sys

def create_sample_config():
    """Create a sample auto_test_config.json"""
    config = {
        "threshold": {
            "max_diff_percentage": 5.0,
            "fail_on_new_elements": True,
            "fail_on_missing_elements": True
        },
        "urls_to_test": [],
        "notification": {
            "github_status_check": True,
            "github_pr_comment": True,
            "fail_build_on_threshold": True
        },
        "comparison": {
            "ignore_antialiasing": True,
            "ignore_colors": False,
            "pixel_ratio": 0.1
        }
    }
    
    print("🎨 Automated Visual Testing Setup")
    print("=" * 60)
    
    # Get user input
    num_urls = input("\nHow many URLs do you want to test? (1-10): ").strip()
    try:
        num_urls = int(num_urls)
        if num_urls < 1 or num_urls > 10:
            num_urls = 1
    except:
        num_urls = 1
    
    for i in range(num_urls):
        print(f"\n📍 Test #{i+1}")
        name = input(f"  Test name (e.g., 'Homepage'): ").strip()
        url = input(f"  URL to test: ").strip()
        baseline = input(f"  Baseline name (e.g., 'homepage'): ").strip()
        
        if name and url and baseline:
            config["urls_to_test"].append({
                "name": name,
                "url": url,
                "baseline": baseline,
                "enabled": True
            })
    
    threshold = input(f"\n⚙️  Max difference threshold (default: 5.0%): ").strip()
    if threshold:
        try:
            config["threshold"]["max_diff_percentage"] = float(threshold)
        except:
            pass
    
    # Save config
    config_file = "auto_test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to {config_file}")
    print("\nNext steps:")
    print("1. Create baselines in the web interface (http://127.0.0.1:7860)")
    print("2. Test locally: python run_automated_tests.py")
    print("3. Push to GitHub to trigger automated tests")
    print("\n📚 See AUTOMATED_VISUAL_TESTING.md for full documentation")

if __name__ == '__main__':
    create_sample_config()
