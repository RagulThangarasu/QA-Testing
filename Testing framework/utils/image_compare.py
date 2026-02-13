import os
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


def _get_location_label(x, y, w, h, total_w, total_h):
    # simple heuristic to name the location
    cw = total_w / 2
    ch = total_h / 2
    
    # Vert
    if y + h < ch * 0.6: v = "Top"
    elif y > ch * 1.4: v = "Bottom"
    else: v = "Center"
    
    # Horz
    if x + w < cw * 0.6: h_ = "Left"
    elif x > cw * 1.4: h_ = "Right"
    else: h_ = "Center"
    
    if v == "Center" and h_ == "Center": return "Center"
    return f"{v}-{h_}"

def _read_png_as_bgr(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    # If BGRA, composite over white to BGR
    if len(img.shape) == 3 and img.shape[2] == 4:
        b, g, r, a = cv2.split(img)
        alpha = a.astype(np.float32) / 255.0
        alpha = cv2.merge([alpha, alpha, alpha])
        bgr = cv2.merge([b, g, r]).astype(np.float32)
        white = np.full_like(bgr, 255, dtype=np.float32)
        out = (bgr * alpha + white * (1.0 - alpha)).astype(np.uint8)
        return out
    # If already BGR
    if len(img.shape) == 3 and img.shape[2] == 3:
        return img
    # If grayscale, convert to BGR
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def _align_orb(template_bgr, target_bgr):
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    target_gray = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=5000, scaleFactor=1.2, edgeThreshold=15, patchSize=31)
    kps1, des1 = orb.detectAndCompute(template_gray, None)
    kps2, des2 = orb.detectAndCompute(target_gray, None)

    if des1 is None or des2 is None or len(kps1) < 10 or len(kps2) < 10:
        return cv2.resize(target_bgr, (template_bgr.shape[1], template_bgr.shape[0])), None

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    if len(good) < 8:
        return cv2.resize(target_bgr, (template_bgr.shape[1], template_bgr.shape[0])), None

    src_pts = np.float32([kps1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kps2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    # Use partial affine (rotation, scale, translation) to prevent perspective skew/distortion
    # limiting degrees of freedom is safer for screenshots
    M, mask = cv2.estimateAffinePartial2D(dst_pts, src_pts, method=cv2.RANSAC, ransacReprojThreshold=5.0)
    
    if M is None:
         return cv2.resize(target_bgr, (template_bgr.shape[1], template_bgr.shape[0])), None

    aligned = cv2.warpAffine(target_bgr, M, (template_bgr.shape[1], template_bgr.shape[0]), flags=cv2.INTER_LINEAR)
    return aligned, M


def _draw_regions(base_bgr, regions, color=(0, 0, 255), thickness=2):
    canvas = base_bgr.copy()
    for x, y, w, h in regions:
        cv2.rectangle(canvas, (x, y), (x + w, y + h), color, thickness)
    return canvas


def _find_diff_regions(diff_gray, min_area=100, dilate_iter=2):
    blur = cv2.GaussianBlur(diff_gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((3, 3), np.uint8)
    dil = cv2.dilate(th, kernel, iterations=dilate_iter)
    cnts, _ = cv2.findContours(dil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= min_area:
            rects.append((x, y, w, h))
    return rects


def _classify_diff(img1, img2):
    if img1.size == 0 or img2.size == 0: return "Unknown"
    
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 1. Check for Missing/Extra Content (Whitespace check)
    mean1 = np.mean(gray1)
    mean2 = np.mean(gray2)
    
    # 2. Check Line Counts (Smart Content Check)
    lines1 = _count_text_lines(gray1)
    lines2 = _count_text_lines(gray2)
    
    if lines1 > lines2:
        return "Missing Content (Text/List)"
    if lines2 > lines1:
        return "Extra Content (Text/List)"

    if mean1 > 250 and mean2 < 245: return "Extra Element"
    if mean1 < 245 and mean2 > 250: return "Missing Element"
    
    # 3. Check Structure vs Color
    try:
        s_score, _ = ssim(gray1, gray2, full=True)
        if s_score > 0.90:
            return "Color/Style Mismatch"
    except:
        pass

    # 4. Check for Text (Edge Density)
    edges1 = cv2.Canny(gray1, 50, 150)
    density1 = np.count_nonzero(edges1) / edges1.size
    if density1 > 0.05:
        return "Text/Content Mismatch"

    # 5. Geometry cues
    h, w = img1.shape[:2]
    if h > 0:
        ratio = w / h
        if ratio > 5 or ratio < 0.2:
            return "Spacing/Padding Issue"

    return "Layout Mismatch"


def _count_text_lines(gray):
    # Inverse binary: Text/Content is white, Background is black
    # Assuming white background usually
    # Use Otsu's binarization for better adaptability
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Horizontal projection
    h_proj = np.sum(thresh, axis=1)
    
    if np.max(h_proj) == 0:
        return 0
        
    # Normalize: any row with sufficient pixels is a "line"
    # Threshold: > 2% of width to avoid noise
    width = gray.shape[1]
    has_content = h_proj > (width * 255 * 0.02)
    
    lines = 0
    in_line = False
    for val in has_content:
        if val and not in_line:
            lines += 1
            in_line = True
        elif not val and in_line:
            in_line = False
            
    return lines


def compare_images(figma_path, stage_path, out_dir, **kwargs):
    figma_bgr = _read_png_as_bgr(figma_path)
    stage_bgr = _read_png_as_bgr(stage_path)

    # Align stage to figma
    stage_aligned_bgr, H = _align_orb(figma_bgr, stage_bgr)
    aligned_path = os.path.join(out_dir, "stage_aligned.png")
    cv2.imwrite(aligned_path, stage_aligned_bgr)

    # Convert to gray & crop to common area
    figma_gray = cv2.cvtColor(figma_bgr, cv2.COLOR_BGR2GRAY)
    stage_gray = cv2.cvtColor(stage_aligned_bgr, cv2.COLOR_BGR2GRAY)

    h = min(figma_gray.shape[0], stage_gray.shape[0])
    w = min(figma_gray.shape[1], stage_gray.shape[1])
    figma_gray = figma_gray[:h, :w]
    stage_gray = stage_gray[:h, :w]
    figma_bgr = figma_bgr[:h, :w]
    stage_aligned_bgr = stage_aligned_bgr[:h, :w]

    # Determine thresholds based on noise_tolerance
    # noise_tolerance: "strict", "medium", "relaxed"
    # strict: sensitive to small changes
    # medium: default
    # relaxed: ignores small changes (high noise tolerance)
    
    noise_tolerance = kwargs.get("noise_tolerance", "medium")
    highlight_diffs = kwargs.get("highlight_diffs", True)
    pixel_threshold = kwargs.get("pixel_threshold", None)
    
    if pixel_threshold is not None:
         # User provided custom threshold
         diff_thresh_val = int(pixel_threshold)
         # Default min_area based on noise_tolerance if not specified? 
         # Let's keep min_area linked to noise_tolerance for now or pick a reasonable default
         if noise_tolerance == "strict": min_area_val = 50
         elif noise_tolerance == "relaxed": min_area_val = 800
         else: min_area_val = 250
    elif noise_tolerance == "strict":
        diff_thresh_val = 30
        min_area_val = 50  # Increased to ignore small font rendering differences
    elif noise_tolerance == "relaxed":
        diff_thresh_val = 120
        min_area_val = 800  # Much higher to ignore most font variations
    else: # medium
        diff_thresh_val = 60
        min_area_val = 250  # Increased to reduce font-related noise

    # SSIM (Color-aware for gradients)
    try:
        # Use channel_axis=2 for multichannel (BGR) SSIM to capture color/gradient shifts
        score, diff = ssim(figma_bgr, stage_aligned_bgr, full=True, channel_axis=2)
        # Take the minimum SSIM across channels (worst case similarity) to highlight any color change
        diff = 1 - np.min(diff, axis=2)
    except TypeError:
        # Fallback if channel_axis is not supported
        score, diff = ssim(figma_gray, stage_gray, full=True)
        diff = 1 - diff

    diff_norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX).astype("uint8")

    # Regions & overlays
    regions = _find_diff_regions(diff_norm, min_area=min_area_val)
    overlay = stage_aligned_bgr.copy()
    heat = cv2.applyColorMap(diff_norm, cv2.COLORMAP_JET)

    # Highlight differences
    if highlight_diffs:
        _, mask = cv2.threshold(diff_norm, diff_thresh_val, 255, cv2.THRESH_BINARY)
        red_layer = np.zeros_like(overlay)
        red_layer[:, :] = (0, 0, 255)  # BGR
        alpha = (mask / 255.0 * 0.35).astype(np.float32)
        overlay = cv2.convertScaleAbs(overlay * (1 - alpha[..., None]) + red_layer * alpha[..., None])
        overlay = _draw_regions(overlay, regions, color=(0, 0, 255), thickness=2)

    # Save artifacts
    diff_overlay_path = os.path.join(out_dir, "diff_overlay.png")
    heatmap_path = os.path.join(out_dir, "diff_heatmap.png")
    cv2.imwrite(diff_overlay_path, overlay)
    cv2.imwrite(heatmap_path, heat)

    change_pixels = int((diff_norm > diff_thresh_val).sum())
    total_pixels = diff_norm.size
    change_ratio = change_pixels / total_pixels if total_pixels else 0.0

    # Process individual issues
    issues = []
    img_h, img_w = overlay.shape[:2]
    
    # sort regions by y then x
    regions = sorted(regions, key=lambda r: (r[1], r[0]))

    for i, (x, y, w, h) in enumerate(regions, 1):
        # Crop the issue from the Overlay (showing the red highlight)
        # Add some padding
        pad = 10
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img_w, x + w + pad)
        y2 = min(img_h, y + h + pad)
        
        crop = overlay[y1:y2, x1:x2]
        crop_filename = f"issue_{i}.png"
        crop_path = os.path.join(out_dir, crop_filename)
        cv2.imwrite(crop_path, crop)
        
        loc_label = _get_location_label(x, y, w, h, img_w, img_h)
        
        # Analyze content for classification
        figma_crop = figma_bgr[y:y+h, x:x+w]
        stage_crop = stage_aligned_bgr[y:y+h, x:x+w]
        issue_type = _classify_diff(figma_crop, stage_crop)
        
        issues.append({
            "id": i,
            "filename": crop_filename,
            "path": crop_path,
            "label": f"#{i}: {issue_type}",
            "full_label": f"Issue #{i}: {issue_type} at {loc_label} ({w}x{h}px)", # Keep old detailed label as fallback or tooltip
            "description": issue_type,
            "location": loc_label,
            "dims": f"{w}x{h}px",
            "x": int(x), "y": int(y), "w": int(w), "h": int(h)
        })

    return {
        "ssim": float(score),
        "change_ratio": float(change_ratio),
        "num_regions": int(len(regions)),
        "diff_overlay_path": diff_overlay_path,
        "heatmap_path": heatmap_path,
        "aligned_stage_path": aligned_path,
        "issues": issues
    }
