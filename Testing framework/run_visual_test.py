import argparse
import os
import sys
import shutil
from utils.screenshot import capture_screenshot
from utils.image_compare import compare_images

def main():
    parser = argparse.ArgumentParser(description="Run visual regression test")
    parser.add_argument("--url", required=True, help="URL to test (e.g. http://localhost:5000 or https://staging.example.com)")
    parser.add_argument("--baseline", required=True, help="Path to baseline image (Figma export or previous screenshot)")
    parser.add_argument("--output", default="visual_test_results", help="Output directory for artifacts")
    parser.add_argument("--threshold", type=float, default=0.90, help="SSIM Threshold (0-1), default 0.90")
    parser.add_argument("--wait", type=int, default=1000, help="Wait time in ms before screenshot")
    parser.add_argument("--fullpage", action="store_true", help="Capture full page screenshot")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    if os.path.exists(args.output):
        shutil.rmtree(args.output)
    os.makedirs(args.output)
    
    print(f"Starting visual test...")
    print(f"Target URL: {args.url}")
    print(f"Baseline: {args.baseline}")
    
    # 1. Capture Screenshot
    stage_path = os.path.join(args.output, "stage.png")
    print("Capturing screenshot...")
    try:
        capture_screenshot(
            url=args.url,
            out_path=stage_path,
            fullpage=args.fullpage,
            wait_time=args.wait
        )
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        sys.exit(1)
        
    if not os.path.exists(stage_path):
        print(f"Error: Screenshot not created at {stage_path}")
        sys.exit(1)
        
    # 2. Compare Images
    print("Comparing images...")
    try:
        # We need to verify baseline exists
        if not os.path.exists(args.baseline):
            print(f"Error: Baseline image not found at {args.baseline}")
            sys.exit(1)
            
        result = compare_images(
            figma_path=args.baseline,
            stage_path=stage_path,
            out_dir=args.output, 
            noise_tolerance="medium"
        )
        
        ssim_score = result.get("ssim", 0)
        change_ratio = result.get("change_ratio", 0)
        num_issues = result.get("num_regions", 0)
        
        print(f"\n--- Visual Test Results ---")
        print(f"SSIM Score: {ssim_score:.4f} (Threshold: {args.threshold})")
        print(f"Change Ratio: {change_ratio:.4f}")
        print(f"Issues Found: {num_issues}")
        
        passed = ssim_score >= args.threshold
        
        if passed:
            print("✅ Visual Test PASSED")
            sys.exit(0)
        else:
            print("❌ Visual Test FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during comparison: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
