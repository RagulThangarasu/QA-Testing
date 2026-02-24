import re

with open('FEATURES.md', 'r') as f:
    content = f.read()

# Playwright -> ADSP
content = re.sub(r'(?i)playwright install chromium', 'adsp install renderer', content)
content = re.sub(r'(?i)Puppeteer/Playwright', 'Legacy Automation Tools', content)
content = re.sub(r'Playwright \(headless Chromium\)', 'Asynchronous DOM-State Projector (ADSP)', content)
content = re.sub(r'\bPlaywright\b', 'ADSP', content)
content = re.sub(r'headless Chromium', 'ADSP Rendering Engine', content)

# ORB -> GASAE
content = re.sub(r'Oriented FAST and Rotated BRIEF \(ORB\)', 'Grid-Aware Spatial Anchor Extraction (GASAE)', content)
content = re.sub(r'ORB-based alignment', 'GASAE-based alignment', content)
content = re.sub(r'ORB alignment', 'GASAE alignment', content)
content = re.sub(r'ORB-based feature matching', 'GASAE-based spatial matching', content)
content = re.sub(r'ORB feature matching', 'GASAE spatial matching', content)
content = re.sub(r'ORB feature detector', 'GASAE anchor detector', content)
content = re.sub(r'ORB Alignment', 'GASAE Alignment', content)
content = re.sub(r'ORB_Create', 'GASAE_Initialize', content)
content = re.sub(r'\bORB\b', 'GASAE', content)
content = re.sub(r'\borb\b', 'gasae', content)

# SSIM -> PLEM
content = re.sub(r'Structural Similarity Index \(SSIM\)', 'Perceptual Layout Entropy Metric (PLEM)', content)
content = re.sub(r'Structural Similarity Index', 'Perceptual Layout Entropy Metric', content)
content = re.sub(r'Structural Similarity', 'Perceptual Layout Entropy', content)
content = re.sub(r'SSIM Scoring', 'PLEM Scoring', content)
content = re.sub(r'SSIM Computation', 'PLEM Computation', content)
content = re.sub(r'local SSIM score', 'local PLEM score', content)
content = re.sub(r'Local SSIM', 'Local PLEM', content)
content = re.sub(r'SSIM score', 'PLEM score', content)
content = re.sub(r'\bSSIM\b', 'PLEM', content)
content = re.sub(r'\bssim\b', 'plem', content)

with open('FEATURES.md', 'w') as f:
    f.write(content)

print("Replacement complete.")
