from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Image as RLImage, SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
import os
from datetime import datetime


def build_pdf_report(pdf_path, job_id, stage_url, metrics, figma_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    # Custom styles
    issue_heading_style = ParagraphStyle(
        'IssueHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#dc2626'),
        spaceAfter=6
    )
    
    issue_detail_style = ParagraphStyle(
        'IssueDetail',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=4
    )
    
    elems = []

    # Title and metadata
    elems.append(Paragraph(f"Visual Comparison Report — Job {job_id}", styles["Title"]))
    elems.append(Paragraph(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), styles["Normal"]))
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(f"<b>Stage URL:</b> {stage_url}", styles["Normal"]))
    elems.append(Spacer(1, 12))

    # Summary metrics
    data = [
        ["Metric", "Value"],
        ["SSIM (0..1, higher is better)", f"{metrics['ssim']:.4f}"],
        ["Changed Area (%)", f"{metrics['change_ratio']*100:.2f}%"],
        ["Regions Detected", str(metrics["num_regions"])]
    ]
    
    # Add background validation stats if available
    if 'background_stats' in metrics and metrics['background_stats']:
        bg_stats = metrics['background_stats']
        data.append(["Background Elements Checked", str(bg_stats.get('total_checked', 0))])
        data.append(["Background Match Rate", f"{bg_stats.get('match_percentage', 100):.1f}%"])
    
    t = Table(data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("FONT", (0,0), (-1,-1), "Helvetica"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 16))

    def add_image(label, path):
        if os.path.exists(path):
            elems.append(Paragraph(label, styles["Heading3"]))
            img = RLImage(path)
            img._restrictSize(17*cm, 18*cm)
            elems.append(img)
            elems.append(Spacer(1, 12))

    # Images
    add_image("Design (Figma PNG)", figma_path)
    add_image("Stage (Aligned)", metrics["aligned_stage_path"])
    
    issue_count = metrics["num_regions"]
    overlay_label = f"Differences — Overlay ({issue_count} issues highlighted in red)"
    add_image(overlay_label, metrics["diff_overlay_path"])
    
    add_image("Differences — Heatmap", metrics["heatmap_path"])

    # Detailed Issues Section
    if issue_count > 0:
        elems.append(PageBreak())
        elems.append(Paragraph("Detected Differences - Detailed Analysis", styles["Heading2"]))
        elems.append(Spacer(1, 12))
        
        issues = metrics.get('issues', [])
        
        for issue in issues:
            issue_num = issue['id']
            # Retrieve fields with fallbacks for backward compatibility
            issue_type = issue.get('description', 'Visual Difference')
            doc_location = issue.get('location', issue['label'])
            
            x, y, w, h = issue['x'], issue['y'], issue['w'], issue['h']
            
            # Issue heading
            elems.append(Paragraph(f"Issue #{issue_num}: {issue_type}", issue_heading_style))
            
            # Issue details
            elems.append(Paragraph(
                f"<b>Location:</b> {doc_location} (X={x}, Y={y})",
                issue_detail_style
            ))
            elems.append(Paragraph(
                f"<b>Size:</b> {w} × {h} pixels ({w*h:,} px²)",
                issue_detail_style
            ))
            
            # Description
            desc_text = generate_issue_description(issue_type, doc_location, w, h)
            elems.append(Paragraph(
                f"<b>Issue Description:</b> {desc_text}",
                issue_detail_style
            ))
            
            # Fix
            fix_suggestion = generate_fix_suggestion(issue_type, doc_location, w, h, x, y)
            elems.append(Paragraph(
                f"<b>Recommended Fix:</b> {fix_suggestion}",
                issue_detail_style
            ))
            
            if os.path.exists(issue['path']):
                elems.append(Spacer(1, 6))
                img = RLImage(issue['path'])
                
                # Resize logic
                img_w, img_h = img.imageWidth, img.imageHeight
                if img_w > 0 and img_h > 0:
                    # max dimensions
                    max_w = 15 * cm
                    max_h = 10 * cm
                    
                    scale = min(1.0, max_w/img_w if img_w > max_w else 1.0, max_h/img_h if img_h > max_h else 1.0)
                    if scale < 1.0:
                        img.drawWidth = img_w * scale
                        img.drawHeight = img_h * scale
                
                elems.append(img)
            
            elems.append(Spacer(1, 16))
    
    # Background validation issues
    if 'background_issues' in metrics and metrics['background_issues']:
        elems.append(PageBreak())
        elems.append(Paragraph("Background Color & Image Issues", styles["Heading2"]))
        elems.append(Spacer(1, 12))
        
        for idx, bg_issue in enumerate(metrics['background_issues'], 1):
            issue_type = bg_issue.get('type', 'unknown')
            selector = bg_issue.get('selector', 'unknown')
            
            elems.append(Paragraph(f"Background Issue #{idx}: {selector}", issue_heading_style))
            
            if issue_type == 'background_color_mismatch':
                elems.append(Paragraph(
                    f"<b>Issue:</b> Background color does not match the design",
                    issue_detail_style
                ))
                elems.append(Paragraph(
                    f"<b>Expected Color:</b> {bg_issue.get('figma_value', 'N/A')}",
                    issue_detail_style
                ))
                elems.append(Paragraph(
                    f"<b>Actual Color:</b> {bg_issue.get('stage_value', 'N/A')}",
                    issue_detail_style
                ))
                elems.append(Paragraph(
                    f"<b>Fix:</b> Update the CSS for '{selector}' to use background-color: {bg_issue.get('expected', 'N/A')}",
                    issue_detail_style
                ))
            
            elif issue_type == 'background_image_mismatch':
                elems.append(Paragraph(
                    f"<b>Issue:</b> Background image does not match the design",
                    issue_detail_style
                ))
                elems.append(Paragraph(
                    f"<b>Expected Image:</b> {bg_issue.get('figma_value', 'N/A')}",
                    issue_detail_style
                ))
                elems.append(Paragraph(
                    f"<b>Actual Image:</b> {bg_issue.get('stage_value', 'N/A')}",
                    issue_detail_style
                ))
                elems.append(Paragraph(
                    f"<b>Fix:</b> Update the CSS for '{selector}' to use the correct background image",
                    issue_detail_style
                ))
            
            elems.append(Spacer(1, 12))

    doc.build(elems)


def generate_issue_description(issue_type, location, width, height):
    """Generate a human-readable description of what the issue is"""
    area = width * height
    
    if area < 500:
        size_desc = "small"
    elif area < 5000:
        size_desc = "medium-sized"
    else:
        size_desc = "large"
    
    loc_str = location.lower() if location else "unknown location"
    
    text = f"A {size_desc} '{issue_type}' was detected in the {loc_str} area ({width}×{height}px)."
    
    if "Text" in issue_type:
        text += " This likely indicates changed text content, font rendering differences, or line-height shifts."
    elif "Color" in issue_type:
        text += " The structure matches, but the colors differ. Check CSS background-color, text color, or opacity."
    elif "Spacing" in issue_type:
        text += " The aspect ratio suggests a margin, padding, or alignment shift."
    elif "Missing Content (Text/List)" in issue_type:
        text += " Textual content or list items (like bullet points) appear to be missing compared to the design."
    elif "Extra Content (Text/List)" in issue_type:
        text += " Additional text or list items appear here that are not in the design."
    elif "Missing" in issue_type:
        text += " An element appears to be missing compared to the design."
    elif "Extra" in issue_type:
        text += " An unexpected element is present here."
    elif "Layout Mismatch" in issue_type:
        text += " The structural layout differs significantly. Check for container shifts, incorrect sizing, or major content displacement."
    else:
        text += " This could be due to missing elements, incorrect styling, or misaligned content."
        
    return text


def generate_fix_suggestion(issue_type, location, width, height, x, y):
    """Generate specific fix suggestions based on the issue characteristics"""
    area = width * height
    suggestions = []
    
    # Issue Type suggestions
    if "Text" in issue_type and "Content" not in issue_type:
        suggestions.append("Verify the text content is identical. Check font-family, font-weight, and line-height properties.")
    elif "Missing Content (Text/List)" in issue_type:
        suggestions.append("Check your CMS content or data source. Verify loop logic (e.g., v-for, map) is rendering the correct number of items.")
    elif "Extra Content (Text/List)" in issue_type:
        suggestions.append("Check for duplicate data entries or incorrect loop termination in your template.")
    elif "Color" in issue_type:
        suggestions.append("Use a color picker to compare the hex codes. Check for opacity/alpha transparency issues.")
    elif "Spacing" in issue_type:
        suggestions.append("Check padding and margin values on the container.")
    elif "Layout Mismatch" in issue_type:
        suggestions.append("Verify container dimensions and Flex/Grid gap properties. Check for unexpected margin collapsing or off-flow elements.")
    
    # Location-based suggestions
    if "Top" in location:
        suggestions.append("Check header elements, navigation bars, or hero sections.")
    elif "Bottom" in location:
        suggestions.append("Review footer content, copyright text, or bottom navigation.")
    elif "Center" in location:
        suggestions.append("Inspect main content area, central images, or primary text blocks.")
    
    # Generic
    suggestions.append(f"Inspect the element at coordinates ({x}, {y}) in your browser's developer tools.")
    
    return " ".join(suggestions)
