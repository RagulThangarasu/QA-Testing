from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import html

def generate_accessibility_pdf(issues, page_url, wcag_level, job_id, output_dir):
    """
    Generate a PDF report for accessibility testing results
    
    Args:
        issues: List of accessibility issues
        page_url: URL that was tested
        wcag_level: WCAG compliance level
        job_id: Job identifier
        output_dir: Directory to save the PDF
    
    Returns:
        Path to the generated PDF file
    """
    pdf_path = f"{output_dir}/accessibility_report.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Style for table content (wrapping text)
    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        wordWrap='CJK'
    )
    
    # Title
    title = Paragraph("Accessibility Testing Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Summary information
    escaped_url = html.escape(page_url)
    # Create a clickable link with blue color
    page_url_link = f'<a href="{escaped_url}" color="blue">{escaped_url}</a>'
    
    summary_data = [
        ['Report ID:', job_id],
        ['Test Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['Page URL:', Paragraph(page_url_link, table_text_style)], 
        ['WCAG Level:', wcag_level],
        ['Total Issues:', str(len(issues))]
    ]
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Issues breakdown
    if issues:
        # Count issues by severity
        violations = sum(1 for i in issues if i.get('severity') == 'violation')
        warnings = sum(1 for i in issues if i.get('severity') == 'warning')
        notices = sum(1 for i in issues if i.get('severity') == 'notice')
        
        breakdown_heading = Paragraph("Issues Breakdown", heading_style)
        elements.append(breakdown_heading)
        
        breakdown_data = [
            ['Severity', 'Count'],
            ['Violations (Critical)', str(violations)],
            ['Warnings (Moderate)', str(warnings)],
            ['Notices (Minor)', str(notices)]
        ]
        
        breakdown_table = Table(breakdown_data, colWidths=[3*inch, 2*inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8)
        ]))
        
        elements.append(breakdown_table)
        elements.append(Spacer(1, 20))
        
        # Detailed issues
        issues_heading = Paragraph("Detailed Issues", heading_style)
        elements.append(issues_heading)
        elements.append(Spacer(1, 12))
        
        # Check if we have multiple pages (Sitemap scan)
        multi_page = any('page_url' in i for i in issues)
        if multi_page:
            # Sort by URL to group issues
            issues.sort(key=lambda x: x.get('page_url', ''))

        current_page_url = None

        for idx, issue in enumerate(issues, 1):
            # If multi-page, add a header when URL changes
            if multi_page:
                issue_page_url = issue.get('page_url')
                if issue_page_url != current_page_url:
                    current_page_url = issue_page_url
                    # Add Page Separator
                    elements.append(Spacer(1, 10))
                    page_header = Paragraph(f"<b>Page: {html.escape(str(current_page_url))}</b>", styles['Heading3'])
                    elements.append(page_header)
                    elements.append(Spacer(1, 10))
            
            # Using Paragraph for the Title to allow wrapping if rule name is long
            # Escape the rule name as it might contain characters
            rule_name = html.escape(str(issue.get('rule', 'Unknown')))
            issue_title = Paragraph(f"<b>Issue #{idx}: {rule_name}</b>", styles['Normal'])
            elements.append(issue_title)
            elements.append(Spacer(1, 6))
            
            # Prepare data with Paragraphs for text wrapping
            # Escape all content to prevent ReportLab XML parsing errors
            severity = html.escape(str(issue.get('severity', 'Unknown')))
            element_code = html.escape(str(issue.get('element', 'N/A')))
            desc = html.escape(str(issue.get('description', 'No description available')))
            impact = html.escape(str(issue.get('impact', 'Unknown')))
            fix = html.escape(str(issue.get('fix', 'No fix information available')))

            # Use a slightly monospace-like font for element if possible, or just bold
            # Note: Standard ReportLab fonts: Courier is monospace.
            code_style = ParagraphStyle('Code', parent=table_text_style, fontName='Courier', fontSize=9, wordWrap='CJK')

            issue_details = [
                ['Severity:', Paragraph(severity, table_text_style)],
                ['Element:', Paragraph(element_code, code_style)],  
                ['Description:', Paragraph(desc, table_text_style)],
                ['Impact:', Paragraph(impact, table_text_style)],
                ['How to Fix:', Paragraph(fix, table_text_style)]
            ]
            
            # Increased width for the content column (Total ~6.5 inches available)
            issue_table = Table(issue_details, colWidths=[1.2*inch, 5.3*inch])
            issue_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f9fafb')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                # Ensure the first column doesn't wrap awkwardly
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            
            elements.append(issue_table)
            elements.append(Spacer(1, 15))
    else:
        # No issues found
        no_issues = Paragraph(
            "<b>✓ No accessibility issues found!</b><br/>"
            "Your page meets the selected WCAG compliance standards.",
            styles['Normal']
        )
        elements.append(no_issues)
    
    # Build PDF
    doc.build(elements)
    
    return pdf_path
