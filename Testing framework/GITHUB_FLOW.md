# GitHub Visual Testing Workflow

This integration allows you to run visual regression tests automatically on every Push or Pull Request, similar to Percy or other visual testing tools.

## Structure

- **`run_visual_test.py`**: A CLI script that runs the visual test. it captures a screenshot of a target URL and compares it against a baseline image.
- **`.github/workflows/visual_tests.yml`**: The GitHub Actions workflow definition.

## Setup

1. **Add Baseline Image**:
   Place your "Source of Truth" image (Figma export or approved screenshot) in the repository.
   Default path: `tests/baseline.png`

2. **Configure Target URL**:
   In `.github/workflows/visual_tests.yml`, update the `TARGET_URL` variable to point to your application.
   
   If you are testing a static site or local app, you may need to uncomment the "Start App" step in the workflow to spin up your server before testing.

   ```yaml
   env:
     TARGET_URL: 'https://staging.myapp.com' 
     # or 'http://localhost:5000' if running locally in CI
   ```

3. **Adjust Thresholds**:
   You can tweak the sensitivity of the test by changing the `--threshold` argument in the workflow file (default is 0.90 SSIM).

## Running Manually

You can also trigger the workflow manually from the "Actions" tab in GitHub, where you can convert the URL and Baseline path for a one-off test.

## Artifacts

If the test fails, the workflow uploads a `visual-test-results` artifact containing:
- `stage.png` (The captured screenshot)
- `diff_overlay.png` (Highligthed differences)
- `stage_aligned.png` (Aligned image)
- Individual issue crops

## CLI Usage (Local)

You can run the test locally:

```bash
python run_visual_test.py --url http://localhost:5000 --baseline tests/baseline.png
```
