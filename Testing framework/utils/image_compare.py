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

    # Force Rotation to 0 (Web screenshots are never rotated)
    # M = [[alpha, beta, tx], [-beta, alpha, ty]] where alpha=scale*cos, beta=scale*sin
    # We want beta=0, alpha=scale
    
    s_x = np.sqrt(M[0,0]**2 + M[0,1]**2)
    s_y = np.sqrt(M[1,0]**2 + M[1,1]**2)
    scale = (s_x + s_y) / 2
    
    # Sanity check on scale (should be close to 1.0 for screenshots)
    if scale < 0.9 or scale > 1.1:
        # Detected bad scaling -> Fallback to resize without alignment
        return cv2.resize(target_bgr, (template_bgr.shape[1], template_bgr.shape[0])), None
        
    # Reconstruct M with 0 rotation
    M[0,0] = scale
    M[0,1] = 0
    M[1,0] = 0
    M[1,1] = scale
    # Keep tx, ty as is (M[0,2], M[1,2])

    aligned = cv2.warpAffine(target_bgr, M, (template_bgr.shape[1], template_bgr.shape[0]), flags=cv2.INTER_LINEAR)
    return aligned, M


def _draw_regions(base_bgr, regions, color=(0, 0, 255), thickness=2):
    canvas = base_bgr.copy()
    for x, y, w, h in regions:
        cv2.rectangle(canvas, (x, y), (x + w, y + h), color, thickness)
    return canvas


def _find_diff_regions(diff_gray, min_area=100, dilate_iter=2):
    """Detect ALL difference regions using Otsu auto-threshold (consistent detection)."""
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
    
    h, w = img1.shape[:2]
    if h == 0 or w == 0: return "Unknown"
    
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
    
    # 3. Spacing / Gap detection between sections
    aspect_ratio = w / h if h > 0 else 1
    
    # 3a. Horizontal spacing strip (wide & short = gap between stacked sections)
    if aspect_ratio > 4:
        # Check if one side is mostly uniform (whitespace/background)
        std1 = np.std(gray1)
        std2 = np.std(gray2)
        if std1 < 20 or std2 < 20:
            return f"Section Spacing / Margin Issue (height: {h}px)"
        return "Spacing/Padding Issue"
    
    # 3b. Vertical spacing strip (tall & narrow = gap between side-by-side elements)
    if aspect_ratio < 0.25:
        std1 = np.std(gray1)
        std2 = np.std(gray2)
        if std1 < 20 or std2 < 20:
            return f"Column Spacing / Gap Issue (width: {w}px)"
        return "Spacing/Padding Issue"
    
    # 3c. Detect content shift (same content but shifted = spacing changed)
    # Use cross-correlation to find if content is just displaced vertically
    if h > 20 and w > 20:
        try:
            # Compare vertical profile of content
            proj1 = np.mean(gray1, axis=1)  # horizontal projection (row means)
            proj2 = np.mean(gray2, axis=1)
            
            # Normalize
            p1 = proj1 - np.mean(proj1)
            p2 = proj2 - np.mean(proj2)
            n1 = np.linalg.norm(p1)
            n2 = np.linalg.norm(p2)
            
            if n1 > 0 and n2 > 0:
                p1 = p1 / n1
                p2 = p2 / n2
                
                # Cross-correlate to find shift
                correlation = np.correlate(p1, p2, mode='full')
                best_shift = np.argmax(correlation) - (len(p1) - 1)
                peak_corr = correlation[np.argmax(correlation)]
                
                # If content is similar but shifted
                if peak_corr > 0.6 and abs(best_shift) > 2:
                    return f"Section Spacing Mismatch (~{abs(best_shift)}px shift)"
        except Exception:
            pass
    
    # 3d. Check for uniform bands (margins/padding filled with background color)
    # Split region into top/bottom thirds and check uniformity
    third_h = max(1, h // 3)
    top_region = gray1[:third_h, :]
    bot_region = gray1[h-third_h:, :]
    mid_region = gray1[third_h:h-third_h, :]
    
    top_std = np.std(top_region)
    bot_std = np.std(bot_region)
    mid_std = np.std(mid_region)
    
    # If top or bottom is uniform but middle has content = padding added/removed
    if (top_std < 10 or bot_std < 10) and mid_std > 25:
        uniform_area = "top" if top_std < bot_std else "bottom"
        return f"Padding/Margin Difference ({uniform_area})"
    
    # 4. Check Structure vs Color
    try:
        s_score, _ = ssim(gray1, gray2, full=True)
        if s_score > 0.90:
            return "Color/Style Mismatch"
    except:
        pass

    # 5. Check for Text (Edge Density)
    edges1 = cv2.Canny(gray1, 50, 150)
    density1 = np.count_nonzero(edges1) / edges1.size
    if density1 > 0.05:
        return "Text/Content Mismatch"

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
    stage_aligned_bgr, M = _align_orb(figma_bgr, stage_bgr)
    
    # Smart Crop: Limit comparison to the overlapping area
    # This handles cases where Stage is a small component matches into a large Figma page
    # and prevents comparing "empty" black padding against content.
    if M is not None:
        h_stage, w_stage = stage_bgr.shape[:2]
        h_figma, w_figma = figma_bgr.shape[:2]
        
        # Transform stage corners to find where they land in figma space
        pts = np.float32([ [0,0], [w_stage, 0], [w_stage, h_stage], [0, h_stage] ]).reshape(-1, 1, 2)
        dst = cv2.transform(pts, M)
        
        x_min = int(np.min(dst[:,:,0]))
        y_min = int(np.min(dst[:,:,1]))
        x_max = int(np.max(dst[:,:,0]))
        y_max = int(np.max(dst[:,:,1]))
        
        # Intersect with Figma bounds
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(w_figma, x_max)
        y_max = min(h_figma, y_max)
        
        # Apply crop if valid
        if x_max > x_min and y_max > y_min:
            figma_bgr = figma_bgr[y_min:y_max, x_min:x_max]
            stage_aligned_bgr = stage_aligned_bgr[y_min:y_max, x_min:x_max]
    
    # Save aligned (and now cropped) stage
    aligned_path = os.path.join(out_dir, "stage_aligned.png")
    cv2.imwrite(aligned_path, stage_aligned_bgr)

    # Convert to gray
    figma_gray = cv2.cvtColor(figma_bgr, cv2.COLOR_BGR2GRAY)
    stage_gray = cv2.cvtColor(stage_aligned_bgr, cv2.COLOR_BGR2GRAY)

    # Ensure dimensions match (redundant if crop worked, but safe)
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
    
    check_layout = kwargs.get("check_layout", True)
    check_content = kwargs.get("check_content", True)
    check_colors = kwargs.get("check_colors", True)
    
    if pixel_threshold is not None:
        # pixel_threshold is a raw sensitivity percentage (0-100)
        # Higher % = More Sensitive = More issues detected
        sensitivity = max(0, min(100, int(pixel_threshold)))
        
        # severity_min: minimum mean pixel difference within a region to keep it
        #   High sensitivity (95%) → severity_min ~5  → keeps subtle differences
        #   Low sensitivity (25%) → severity_min ~100 → only keeps obvious differences
        severity_min = max(3, int(130 * (1 - sensitivity / 100)))
        
        # min_area_val: minimum region area in px²
        min_area_val = max(20, int(600 * (1 - sensitivity / 100)))
        
        # dilate_iter: merging of nearby diff pixels
        if sensitivity >= 80:
            dilate_iter = 1
        elif sensitivity >= 50:
            dilate_iter = 2
        else:
            dilate_iter = 3
        
        # diff_thresh_val: used only for highlight overlay rendering
        diff_thresh_val = max(5, int(200 * (1 - sensitivity / 100)))
    elif noise_tolerance == "strict":
        # HIGH sensitivity — catches everything, keeps regions separate
        severity_min = 3       # keeps even subtle differences
        min_area_val = 25      # catches tiny 5x5 regions
        dilate_iter = 1        # minimal merging → more separate issues
        diff_thresh_val = 15   # aggressive highlight overlay
    elif noise_tolerance == "relaxed":
        # LOW sensitivity — only obvious differences, merges aggressively
        severity_min = 60      # only keeps strong differences
        min_area_val = 500     # ignores anything smaller than ~22x22
        dilate_iter = 4        # heavy merging → fewer, larger issues
        diff_thresh_val = 100  # conservative highlight overlay
    else: # medium
        # STANDARD sensitivity — balanced
        severity_min = 25      # moderate filter
        min_area_val = 150     # catches 12x12+ regions
        dilate_iter = 2        # standard merging
        diff_thresh_val = 50   # balanced highlight overlay

    # SSIM (Color-aware if validation enabled)
    diff = None
    score = 0.0
    
    if check_colors:
        try:
            # Use channel_axis=2 for multichannel (BGR) SSIM to capture color/gradient shifts
            score, diff = ssim(figma_bgr, stage_aligned_bgr, full=True, channel_axis=2)
            # Take the minimum SSIM across channels (worst case similarity) to highlight any color change
            diff = 1 - np.min(diff, axis=2)
        except TypeError:
            # Fallback if channel_axis is not supported
            score, diff = ssim(figma_gray, stage_gray, full=True)
            diff = 1 - diff
    else:
        # User requested to ignore color -> Force Grayscale comparison
        score, diff = ssim(figma_gray, stage_gray, full=True)
        diff = 1 - diff

    # Use absolute scaling instead of relative (MinMax) to avoid amplifying noise
    # into "major diffs" when the actual major diffs (like color) are removed.
    diff_norm = (diff * 255).clip(0, 255).astype("uint8")

    # Step 1: Detect candidate regions using Otsu auto-threshold
    # dilate_iter controls merging: strict(1)=more regions, relaxed(4)=fewer merged regions
    all_regions = _find_diff_regions(diff_norm, min_area=min_area_val, dilate_iter=dilate_iter)
    
    # Step 2: Filter regions by severity — only keep regions whose mean pixel
    # difference exceeds severity_min. This is the industry-standard approach
    # (Percy/Applitools style) that guarantees:
    #   Pixel-perfect > Strict > Medium > Loose in issue count
    raw_regions = []
    for (x, y, w, h) in all_regions:
        region_diff = diff_norm[y:y+h, x:x+w]
        mean_severity = float(np.mean(region_diff))
        if mean_severity >= severity_min:
            raw_regions.append((x, y, w, h))
    
    # Filter regions based on classification and feature flags
    valid_regions = []
    issues = []
    
    # Prepare overlay base
    overlay = stage_aligned_bgr.copy()
    
    # Sort regions by y then x
    raw_regions = sorted(raw_regions, key=lambda r: (r[1], r[0]))
    
    for i, (x, y, w, h) in enumerate(raw_regions, 1):
        # Classify first
        figma_crop = figma_bgr[y:y+h, x:x+w]
        stage_crop = stage_aligned_bgr[y:y+h, x:x+w]
        issue_type = _classify_diff(figma_crop, stage_crop)
        
        # Check if we should keep this issue based on flags
        keep = True
        
        # Color Check
        if "Color" in issue_type and not check_colors:
            keep = False
            
        # Content Check
        if ("Content" in issue_type or "Text" in issue_type) and not check_content:
            keep = False
            
        # Layout Check (catch-all for layout/spacing issues)
        is_layout = any(kw in issue_type for kw in ["Layout", "Spacing", "Element", "Margin", "Padding", "Gap", "Column"])
        if is_layout and not check_layout:
            keep = False
            
        if keep:
            valid_regions.append((x, y, w, h))
            
            # Create crop and issue entry
            img_h, img_w = overlay.shape[:2]
            pad = 10
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(img_w, x + w + pad)
            y2 = min(img_h, y + h + pad)
            
            # Temporary draw on copy for crop to show highlight? 
            # Actually standard practice is to crop the Clean or Highlighted?
            # Existing code cropped from 'overlay' which had rectangles.
            # We will draw rectangles later, so crops here will be "clean" 
            # UNLESS we want to show the red box in the issue crop.
            # Let's crop from stage_aligned (clean) to be safe, or we draw rects on a temp canvas.
            # The previous code drew rects FIRST. Let's stick to clean crops or do it after.
            # Actually, let's just save the issue details now and generate the crop later if needed
            # OR generate crop from CLEAN image.
            
            crop = stage_aligned_bgr[y1:y2, x1:x2]
            crop_filename = f"issue_{len(issues)+1}.png"
            crop_path = os.path.join(out_dir, crop_filename)
            cv2.imwrite(crop_path, crop)
            
            loc_label = _get_location_label(x, y, w, h, img_w, img_h)
            
            issues.append({
                "id": len(issues)+1,
                "filename": crop_filename,
                "path": crop_path,
                "label": f"#{len(issues)+1}: {issue_type}",
                "full_label": f"Issue #{len(issues)+1}: {issue_type} at {loc_label} ({w}x{h}px)",
                "description": issue_type,
                "location": loc_label,
                "dims": f"{w}x{h}px",
                "x": int(x), "y": int(y), "w": int(w), "h": int(h)
            })

    # Prepare final overlay with ONLY valid regions
    heat = cv2.applyColorMap(diff_norm, cv2.COLORMAP_JET)

    if highlight_diffs:
        # We only highlight valid regions
        # To do valid highlighting of pixels, we might need a mask of valid regions
        # Current logic highlights ALL pixels in diff map.
        # Ideally, we should mask the diff map to only valid regions.
        
        _, mask = cv2.threshold(diff_norm, diff_thresh_val, 255, cv2.THRESH_BINARY)
        
        # Create a mask that only allows pixels inside valid regions
        region_mask = np.zeros_like(mask)
        for x, y, w, h in valid_regions:
            cv2.rectangle(region_mask, (x, y), (x + w, y + h), 255, -1)
            
        # Intersect
        final_mask = cv2.bitwise_and(mask, region_mask)
        
        red_layer = np.zeros_like(overlay)
        red_layer[:, :] = (0, 0, 255)  # BGR
        
        alpha = (final_mask / 255.0 * 0.35).astype(np.float32)
        overlay = cv2.convertScaleAbs(overlay * (1 - alpha[..., None]) + red_layer * alpha[..., None])
        
        # Draw boxes
        overlay = _draw_regions(overlay, valid_regions, color=(0, 0, 255), thickness=2)

    # Save artifacts
    diff_overlay_path = os.path.join(out_dir, "diff_overlay.png")
    heatmap_path = os.path.join(out_dir, "diff_heatmap.png")
    cv2.imwrite(diff_overlay_path, overlay)
    cv2.imwrite(heatmap_path, heat)

    # Recalculate change stats based on filtered results
    # Only count pixels in valid regions?
    # Approximating by re-calculating mask area
    # If highlight_diffs was False, we didn't compute final_mask.
    # Let's assume change_ratio is based on the VALID regions now.
    
    if highlight_diffs:
         change_pixels = np.count_nonzero(final_mask)
    else:
         # Rough fallback if no highlight requested (shouldn't happen often)
         change_pixels = sum([w*h for x,y,w,h in valid_regions]) # simple area sum, improved later if needed
         
    total_pixels = diff_norm.size
    change_ratio = change_pixels / total_pixels if total_pixels else 0.0

    return {
        "ssim": float(score),
        "change_ratio": float(change_ratio),
        "num_regions": int(len(issues)),
        "diff_overlay_path": diff_overlay_path,
        "heatmap_path": heatmap_path,
        "aligned_stage_path": aligned_path,
        "issues": issues
    }
