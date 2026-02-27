from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.units import inch
import os, signal, sys
from datetime import datetime

# Handle "[Errno 32] Broken pipe" gracefully (common when piping output)
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except Exception:
    pass

def generate_pdf_documentation(filename="QA_Testing_Framework_Documentation.pdf"):
    # Adjusted margins to giving more width (0.75 inch = 54 pts)
    margin = 0.75 * inch
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=margin, leftMargin=margin,
                            topMargin=margin, bottomMargin=margin)
    
    # Calculate usable width
    page_width = A4[0] - (2 * margin)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='TitleCustom', parent=styles['Title'], fontSize=24, spaceAfter=20, alignment=1, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='Heading1Custom', parent=styles['Heading1'], fontSize=18, spaceBefore=20, spaceAfter=10, textColor=colors.darkblue, keepWithNext=True))
    styles.add(ParagraphStyle(name='Heading2Custom', parent=styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=8, textColor=colors.black, keepWithNext=True))
    styles.add(ParagraphStyle(name='BodyTextCustom', parent=styles['BodyText'], fontSize=11, leading=14, spaceAfter=10))
    styles.add(ParagraphStyle(name='BulletPoint', parent=styles['BodyText'], fontSize=11, leading=14, leftIndent=20, spaceAfter=5, bulletIndent=10))

    story = []

    # Title Page
    story.append(Paragraph("QA Testing Framework", styles['TitleCustom']))
    story.append(Paragraph("Comprehensive Documentation", styles['Title']))
    story.append(Spacer(1, 100))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d')}", styles['BodyTextCustom']))
    story.append(PageBreak())

    # Introduction
    intro_section = []
    intro_section.append(Paragraph("1. Introduction", styles['Heading1Custom']))
    intro_text = """
    This document provides a comprehensive overview of the QA Testing Framework, a unified tool designed to ensure the quality, consistency, and performance of web applications. 
    The framework consolidates visual regression testing, accessibility audits, broken link checking, and SEO performance analysis into a single, cohesive interface.
    """
    intro_section.append(Paragraph(intro_text, styles['BodyTextCustom']))
    story.append(KeepTogether(intro_section))

    # Architecture Overview
    arch_section = []
    arch_section.append(Paragraph("2. Architecture Overview", styles['Heading1Custom']))
    arch_text = """
    The application is built using a modern, lightweight architecture that separates checks into modular components while providing a unified dashboard for execution and reporting.
    """
    arch_section.append(Paragraph(arch_text, styles['BodyTextCustom']))
    story.append(KeepTogether(arch_section))

    data = [
        ["Component", "Technology", "Role"],
        ["Backend", "Python + Flask", "API handling, orchestration, core logic processing."],
        ["Frontend", "Vanilla HTML/JS/CSS", "User Interface, realtime updates via polling."],
        ["Database", "Local JSON / FS", "Persistent storage for job history and artifacts."],
        ["Browsers", "Playwright", "Headless browsing for screenshots and rendering."],
        ["Vision", "OpenCV + SSIM", "Image alignment, structural similarity, diff detection."]
    ]
    
    # Adjust column widths to fully utilize page width
    col1 = page_width * 0.15
    col2 = page_width * 0.25
    col3 = page_width * 0.60
    
    t = Table(data, colWidths=[col1, col2, col3])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('WORDWRAP', (0,0), (-1,-1), True), # Ensure text wraps within cells properly
    ]))
    story.append(KeepTogether([t])) # Keep table together

    # Backend Technology Stack
    section3 = []
    section3.append(Paragraph("3. Backend Technology Stack", styles['Heading1Custom']))
    
    # Python & Flask
    section3.append(Paragraph("3.1 Core Framework: Python & Flask", styles['Heading2Custom']))
    section3.append(Paragraph("What: We use Python 3.9+ with the Flask micro-framework.", styles['BodyTextCustom']))
    section3.append(Paragraph("Why:", styles['BodyTextCustom']))
    section3.append(Paragraph("• Simplicity: Flask is lightweight and allows for rapid development of API endpoints.", styles['BulletPoint']))
    section3.append(Paragraph("• Ecosystem: Python has the strongest ecosystem for data processing, image manipulation (OpenCV), and automation.", styles['BulletPoint']))
    story.append(KeepTogether(section3))

    # Playwright
    section_pw = []
    section_pw.append(Paragraph("3.2 Browser Automation: Playwright", styles['Heading2Custom']))
    section_pw.append(Paragraph("What: Microsoft's Playwright library is used to control headless Chromium browsers.", styles['BodyTextCustom']))
    section_pw.append(Paragraph("Why:", styles['BodyTextCustom']))
    section_pw.append(Paragraph("• Reliability: It is faster and more reliable than Selenium, managing dynamic content and network waiting states ('networkidle').", styles['BulletPoint']))
    section_pw.append(Paragraph("• Fidelity: Renders modern web features exactly as users see them.", styles['BulletPoint']))
    story.append(KeepTogether(section_pw))

    # OpenCV & SSIM
    section_cv = []
    section_cv.append(Paragraph("3.3 Computer Vision: OpenCV & scikit-image", styles['Heading2Custom']))
    section_cv.append(Paragraph("What: OpenCV is used for image alignment (ORB features) and processing. scikit-image provides the Structural Similarity Index (SSIM).", styles['BodyTextCustom']))
    section_cv.append(Paragraph("Why:", styles['BodyTextCustom']))
    section_cv.append(Paragraph("• Pixel-Perfect Accuracy: SSIM aligns with human visual perception better than simple pixel subtraction.", styles['BulletPoint']))
    section_cv.append(Paragraph("• Robustness: ORB alignment handles slight shifts in rendering, ensuring we compare the correct elements.", styles['BulletPoint']))
    story.append(KeepTogether(section_cv))

    # ReportLab
    section_rl = []
    section_rl.append(Paragraph("3.4 Reporting: ReportLab", styles['Heading2Custom']))
    section_rl.append(Paragraph("What: A library for programmatically generating PDF documents.", styles['BodyTextCustom']))
    section_rl.append(Paragraph("Why: Allows us to generate professional, sharable PDF reports with embedded images (diff overlays) and text.", styles['BulletPoint']))
    story.append(KeepTogether(section_rl))

    # Frontend Technology Stack
    section4 = []
    section4.append(Paragraph("4. Frontend Technology Stack", styles['Heading1Custom']))
    section4.append(Paragraph("What: Pure HTML5, CSS3, and Vanilla JavaScript (ES6+).", styles['BodyTextCustom']))
    section4.append(Paragraph("Why:", styles['BodyTextCustom']))
    section4.append(Paragraph("• Performance: Zero compilation steps, instant loading, and minimal overhead.", styles['BulletPoint']))
    section4.append(Paragraph("• Simplicity: Easy for any developer to maintain without needing knowledge of complex frameworks like React or Vue.", styles['BulletPoint']))
    section4.append(Paragraph("• Direct Control: Direct DOM manipulation for features like the interactive image difference toggle and file upload drag-and-drop.", styles['BulletPoint']))
    story.append(KeepTogether(section4))

    # Detailed Feature Breakdown
    story.append(Paragraph("5. Detailed Feature Breakdown", styles['Heading1Custom']))

    # Visual Testing
    section51 = []
    section51.append(Paragraph("5.1 Visual Testing Studio", styles['Heading2Custom']))
    section51.append(Paragraph("This module compares a Figma design (PNG) against a live staged URL.", styles['BodyTextCustom']))
    section51.append(Paragraph("Key Features:", styles['BodyTextCustom']))
    section51.append(Paragraph("• Smart Alignment: Automatically aligns the Figma design with the screenshot using feature matching, correcting for minor crop differences.", styles['BulletPoint']))
    section51.append(Paragraph("• Smart Cropping: Validates specific components (via selector) against full-page designs by auto-detecting the component's location.", styles['BulletPoint']))
    section51.append(Paragraph("• Dynamic Masking: Users can provide CSS selectors (e.g., '.ads') to mask out dynamic content that would cause false positives.", styles['BulletPoint']))
    section51.append(Paragraph("• Noise Tolerance: Adjustable sensitivity (Strict/Medium/Relaxed) to ignore minor font-rendering differences.", styles['BulletPoint']))
    section51.append(Paragraph("• Output: Generates Diff Overlay, Heatmap, and Aligned Side-by-Side images.", styles['BulletPoint']))
    story.append(KeepTogether(section51))

    # Broken Links
    section52 = []
    section52.append(Paragraph("5.2 Broken Links & Asset Crawler", styles['Heading2Custom']))
    section52.append(Paragraph("This module recursively crawls a website to ensure site health.", styles['BodyTextCustom']))
    section52.append(Paragraph("Key Features:", styles['BodyTextCustom']))
    section52.append(Paragraph("• Deep Crawling: Visits all internal links to finding broken pages (404s).", styles['BulletPoint']))
    section52.append(Paragraph("• Asset Validation: Checks all images and icons to ensure they load correctly.", styles['BulletPoint']))
    section52.append(Paragraph("• Integration: Uses `requests` for speed and `BeautifulSoup` for parsing.", styles['BulletPoint']))
    story.append(KeepTogether(section52))

    # Accessibility
    section53 = []
    section53.append(Paragraph("5.3 Accessibility Auditor", styles['Heading2Custom']))
    section53.append(Paragraph("Automated checks against WCAG 2.1 standards.", styles['BodyTextCustom']))
    section53.append(Paragraph("Key Features:", styles['BodyTextCustom']))
    section53.append(Paragraph("• Checks: Missing alt text, form labels, heading hierarchy, contrast ratios, and aria-labels.", styles['BulletPoint']))
    section53.append(Paragraph("• Sitemap Scanning: Can digest an entire XML sitemap and audit hundreds of pages in parallel.", styles['BulletPoint']))
    section53.append(Paragraph("• Reporting: Categorizes issues by severity (Critical, Serious, Moderate) and provides direct fix suggestions.", styles['BulletPoint']))
    story.append(KeepTogether(section53))

    # SEO & Performance
    section54 = []
    section54.append(Paragraph("5.4 SEO & Performance Monitor", styles['Heading2Custom']))
    section54.append(Paragraph("Ensures pages meet search engine and user experience standards.", styles['BodyTextCustom']))
    section54.append(Paragraph("Key Features:", styles['BodyTextCustom']))
    section54.append(Paragraph("• Meta Analysis: Validates Title, Description, and Viewport tags.", styles['BulletPoint']))
    section54.append(Paragraph("• H1 Verification: Ensures a single, unique H1 exists per page.", styles['BulletPoint']))
    section54.append(Paragraph("• Performance Metrics: Measures response time and page weight.", styles['BulletPoint']))
    story.append(KeepTogether(section54))

    # Visual Baseline Versioning
    section6 = []
    section6.append(Paragraph("6. Visual Baseline Versioning", styles['Heading1Custom']))
    section6.append(Paragraph("The framework includes robust capabilities for managing visual history and decisions.", styles['BodyTextCustom']))
    
    section6.append(Paragraph("6.1 Version History & Baselines", styles['Heading2Custom']))
    section6.append(Paragraph("What: Every test run creates a unique, immutable record stored in the file system.", styles['BodyTextCustom']))
    section6.append(Paragraph("Why: Allows teams to audit UI evolution over time. If a regression occurs, you can look back to see exactly when the change was introduced.", styles['BulletPoint']))

    section6.append(Paragraph("6.2 Approve / Reject Workflow", styles['Heading2Custom']))
    section6.append(Paragraph("What: An interactive review interface allows QA engineers to explicitly 'Approve' or 'Reject' a visual change.", styles['BodyTextCustom']))
    section6.append(Paragraph("Why: Distinguishes between intentional design updates and accidental regressions. Approved runs serve as the new 'signed-off' state.", styles['BulletPoint']))

    section6.append(Paragraph("6.3 Storing Historical Diffs", styles['Heading2Custom']))
    section6.append(Paragraph("What: All artifacts (Diff Overlays, Heatmaps, PDF Reports, and Input Images) are persisted indefinitely in unique job directories.", styles['BodyTextCustom']))
    section6.append(Paragraph("Why: Ensures that evidence of failures is never lost. You can download the exact diff image from a test run 3 months ago.", styles['BulletPoint']))
    
    section6.append(Paragraph("6.4 Rollback Capability", styles['Heading2Custom']))
    section6.append(Paragraph("What: Support for referencing previous successful runs.", styles['BodyTextCustom']))
    section6.append(Paragraph("Why: If a new deployment is rejected, the team can reference the last 'Approved' run to verify what the correct state should be during a rollback.", styles['BulletPoint']))
    story.append(KeepTogether(section6))

    # Integrations
    section7 = []
    section7.append(Paragraph("7. Third-Party Integrations", styles['Heading1Custom']))
    section7.append(Paragraph("The framework integrates directly with project management tools to streamline the feedback loop.", styles['BodyTextCustom']))
    
    section7.append(Paragraph("7.1 Jira Integration", styles['Heading2Custom']))
    section7.append(Paragraph("• Allows users to create Jira tasks directly from the test result page.", styles['BulletPoint']))
    section7.append(Paragraph("• Automatically attaches the issue screenshot and description.", styles['BulletPoint']))

    section7.append(Paragraph("7.2 GitHub Integration", styles['Heading2Custom']))
    section7.append(Paragraph("• Creates GitHub Issues for verified bugs.", styles['BulletPoint']))
    section7.append(Paragraph("• Tags issues with 'visual-regression' labels for easy filtering.", styles['BulletPoint']))
    story.append(KeepTogether(section7))
    
    # Process Flow Map
    section8 = []
    section8.append(Paragraph("8. Visual Workflow & Process Map", styles['Heading1Custom']))
    section8.append(Paragraph("The following diagram illustrates the end-to-end workflow for visual regression testing, from initiation to baseline promotion.", styles['BodyTextCustom']))
    
    # Flowchart Table
    flow_data = [
        ["Step", "Action / Decision", "Outcome"],
        ["1. Initiation", "User enters Stage URL", "System checks for active baseline"],
        ["2. Baseline Check", "Has Active Baseline?", "Yes: Auto-load Stored Image\nNo: Prompt for Figma Upload"],
        ["3. Execution", "Capture Screenshot & Compare", "Generates Diff, SSIM Score, Heatmap"],
        ["4. Review", "Is Diff Detected?", "No: Test Passed ✅\nYes: Human Review Required ⚠️"],
        ["5. Decision", "User Reviews Diff", "Approve: Promotes Stage Image to Baseline\nReject: Marks Job as Failed"],
        ["6. Maintenance", "Baseline Updated", "New version (v2, v3...) created & stored"]
    ]
    
    # Adjust widths
    col1 = 1.2*inch
    col2 = 2.5*inch
    col3 = page_width - col1 - col2
    
    ft = Table(flow_data, colWidths=[col1, col2, col3])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue), # Header row
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        
        # Step Column
        ('BACKGROUND', (0,1), (0,-1), colors.whitesmoke),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        
        # Decision/Action Column
        ('BACKGROUND', (1,1), (1,-1), colors.white),
        
        # Outcome Column
        ('BACKGROUND', (2,1), (2,-1), colors.lightgrey),
        
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    
    section8.append(ft)
    story.append(KeepTogether(section8))
    
    
    # Roadmap Section
    section9 = []
    section9.append(Paragraph("9. Project Roadmap", styles['Heading1Custom']))
    section9.append(Paragraph("The future development roadmap outlining the progression of the framework.", styles['BodyTextCustom']))
    
    roadmap_data = [
        ["Phase / Timeline", "Key Milestones", "Status"],
        ["Q1 2026\nFoundation", "• Core Framework (Flask + Playwright)\n• Visual Testing Engine (OpenCV)\n• Reporting Infrastructure", "Completed ✅"],
        ["Q2 2026\nExpansion", "• Accessibility Audits (WCAG)\n• Broken Link Crawler\n• SEO Performance Checks\n• Jira/GitHub Integration", "Completed ✅"],
        ["Q3 2026\nScalability", "• Cloud Storage Support (S3/GCS)\n• Multi-user Authentication\n• Dashboard Analytics & Trends", "Planned 🗓️"],
        ["Q4 2026\nIntelligence", "• AI Root Cause Analysis\n• Predictive Flakiness Detection\n• CI/CD Plugin Ecosystem", "Planned 🗓️"]
    ]
    
    rt = Table(roadmap_data, colWidths=[1.5*inch, 3.5*inch, 1.5*inch])
    rt.setStyle(TableStyle([
       ('BACKGROUND', (0,0), (-1,0), colors.darkgreen),
       ('TEXTCOLOR', (0,0), (-1,0), colors.white),
       ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
       ('ALIGN', (0,0), (-1,-1), 'LEFT'),
       ('VALIGN', (0,0), (-1,-1), 'TOP'),
       
       ('GRID', (0,0), (-1,-1), 1, colors.black),
       ('BACKGROUND', (0,1), (0,2), colors.lightgrey), # Completed phases row bg
       ('BACKGROUND', (0,3), (0,4), colors.whitesmoke), # Planned phases row bg
       ('BOTTOMPADDING', (0,0), (-1,-1), 12),
       ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    
    section9.append(rt)
    story.append(KeepTogether(section9))

    doc.build(story)
    print(f"PDF generated: {os.path.abspath(filename)}")

if __name__ == "__main__":
    generate_pdf_documentation()
