# Visual Testing — Figma PNG vs Stage URL

A small framework & static UI to compare a Figma-exported PNG against a live Stage URL. It captures a screenshot, aligns it, computes perceptual diffs, and outputs a PDF report plus diff images.

## Features
- Static UI (HTML/JS) to upload **Figma PNG** and enter **Stage URL**
- Backend (Flask + Python):
  - Screenshots stage via **Playwright**
  - **Feature-based alignment** (ORB + Homography)
  - **SSIM** diff + **contour regions** and heatmap
  - PDF report with metrics & visuals
- Downloadable **report.pdf**, **diff_overlay.png**, **diff_heatmap.png**, **stage_aligned.png**

## Quick Start (Local)

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install --with-deps
python app.py

.venv/bin/python app.py
```

Open http://localhost:7860

## Docker

```bash
docker build -t visual-testing .
docker run -p 7860:7860 --rm visual-testing
```

## API

`POST /api/compare` (multipart)
- `figma_png`: PNG file (required)
- `stage_url`: string URL (required)
- `viewport`: `desktop` | `mobile` | `WxH` (optional, default `desktop`)
- `fullpage`: `true` | `false` (optional, default `true`)
- `threshold`: float 0..1 (optional, default 0.85)

Returns JSON with `passed`, `metrics`, and `outputs` paths.

## Notes
- For dynamic pages, animations are disabled before screenshot to reduce noise.
- Use consistent Figma export scale (1x/2x) vs. chosen viewport for best results.
- You can tweak thresholds in `utils/image_compare.py` (`mask` cutoff, `min_area`).

## License
MIT
