from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

def generate_seo_performance_pdf(metrics, page_url, test_type, device_type, job_id, output_dir):
    """
    Generate a PDF report for SEO & Performance testing results
    
    Args:
        metrics: Dictionary containing SEO and performance metrics
        page_url: URL that was tested
        test_type: Type of test (both, seo, performance)
        device_type: Device type (desktop, mobile)
        job_id: Job identifier
        output_dir: Directory to save the PDF
    
    Returns:
        Path to the generated PDF file
    """
    pdf_path = f"{output_dir}/seo_performance_report.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
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
    
    # Title
    title = Paragraph("SEO & Performance Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Summary information
    test_type_label = {
        'both': 'SEO & Performance',
        'seo': 'SEO Only',
        'performance': 'Performance Only'
    }.get(test_type, test_type)
    
    summary_data = [
        ['Report ID:', job_id],
        ['Test Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['Page URL:', page_url],
        ['Test Type:', test_type_label],
        ['Device:', device_type.capitalize()]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Scores Overview
    scores_heading = Paragraph("Scores Overview", heading_style)
    elements.append(scores_heading)
    
    scores_data = [['Metric', 'Score', 'Rating']]
    
    if metrics.get('seo_score') is not None:
        seo_score = metrics['seo_score']
        seo_rating = get_rating(seo_score)
        scores_data.append(['SEO Score', f"{seo_score}/100", seo_rating])
    
    if metrics.get('performance_score') is not None:
        perf_score = metrics['performance_score']
        perf_rating = get_rating(perf_score)
        scores_data.append(['Performance Score', f"{perf_score}/100", perf_rating])
    
    scores_table = Table(scores_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    scores_table.setStyle(TableStyle([
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
    
    elements.append(scores_table)
    elements.append(Spacer(1, 20))
    
    # SEO Details
    if test_type in ['both', 'seo'] and metrics.get('seo_details'):
        seo_heading = Paragraph("SEO Analysis", heading_style)
        elements.append(seo_heading)
        
        seo_details = metrics['seo_details']
        seo_data = [['Check', 'Status', 'Details']]
        
        for check in seo_details:
            status = '✓ Pass' if check['passed'] else '✗ Fail'
            seo_data.append([check['name'], status, check['details']])
        
        seo_table = Table(seo_data, colWidths=[2*inch, 1*inch, 3*inch])
        seo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(seo_table)
        elements.append(Spacer(1, 20))
    
    # Performance Details
    if test_type in ['both', 'performance'] and metrics.get('performance_details'):
        perf_heading = Paragraph("Performance Metrics", heading_style)
        elements.append(perf_heading)
        
        perf_details = metrics['performance_details']
        perf_data = [['Metric', 'Value', 'Rating']]
        
        for metric in perf_details:
            rating = get_metric_rating(metric['value'], metric.get('threshold'))
            perf_data.append([metric['name'], metric['value'], rating])
        
        perf_table = Table(perf_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        perf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(perf_table)
        elements.append(Spacer(1, 20))
    
    # Recommendations
    if metrics.get('recommendations'):
        rec_heading = Paragraph("Recommendations", heading_style)
        elements.append(rec_heading)
        
        for idx, rec in enumerate(metrics['recommendations'], 1):
            rec_text = Paragraph(f"<b>{idx}. {rec['title']}</b><br/>{rec['description']}", styles['Normal'])
            elements.append(rec_text)
            elements.append(Spacer(1, 8))
    
    # Build PDF
    doc.build(elements)
    
    return pdf_path


def get_rating(score):
    """Get rating based on score"""
    if score >= 95:
        return 'Excellent'
    elif score >= 50:
        return 'Needs Improvement'
    else:
        return 'Poor'


def get_metric_rating(value, threshold=None):
    """Get rating for a metric value"""
    if threshold is None:
        return 'N/A'
    # Since values are strings, we can't compare them directly
    # Just return N/A for now, or you could parse the numeric values
    return 'N/A'
