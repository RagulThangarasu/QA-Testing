from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
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
    report_title = "SEO & Performance Report"
    if test_type == "seo":
        report_title = "SEO Report"
    elif test_type == "performance":
        report_title = "Performance Report"
        
    title = Paragraph(report_title, title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Summary information
    test_type_label = {
        'both': 'SEO & Performance',
        'seo': 'SEO Only',
        'performance': 'Performance Only'
    }.get(test_type, test_type)
    
    device_label = "Desktop & Mobile" if device_type == 'both' else device_type.capitalize()
    
    summary_data = [
        ['Report ID:', job_id],
        ['Test Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['Page URL:', page_url],
        ['Test Type:', test_type_label],
        ['Device:', device_label]
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
    elements.append(Spacer(1, 25))
    
    # ---------------------------------------------------------
    # Visual Summary (Charts)
    # ---------------------------------------------------------
    visual_heading = Paragraph("Visual Analysis", heading_style)
    elements.append(visual_heading)

    # Prepare Data
    if device_type == 'both' and isinstance(metrics, dict) and 'desktop' in metrics:
        # Multi-device data
        m_d = metrics['desktop']
        m_m = metrics['mobile']
        
        # Scores
        s_seo_d = m_d.get('seo_score', 0) or 0
        s_perf_d = m_d.get('performance_score', 0) or 0
        s_seo_m = m_m.get('seo_score', 0) or 0
        s_perf_m = m_m.get('performance_score', 0) or 0
        
        # We'll use these for the charts
        chart_data_d = [s_seo_d, s_perf_d]
        chart_data_m = [s_seo_m, s_perf_m]
        chart_labels = ['SEO', 'Performance']
        
        # Draw Bar Chart (Scores Comparison)
        d_bar = Drawing(400, 200)
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 125
        bc.width = 300
        bc.data = [chart_data_d, chart_data_m]
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.categoryAxis.categoryNames = chart_labels
        bc.bars[0].fillColor = colors.HexColor("#2563eb") # Desktop Blue
        bc.bars[1].fillColor = colors.HexColor("#f59e0b") # Mobile Orange
        
        # Legend for Desktop/Mobile
        legend = Legend()
        legend.alignment = 'right'
        legend.x = 350
        legend.y = 150
        legend.colorNamePairs = [(colors.HexColor("#2563eb"), 'Desktop'), (colors.HexColor("#f59e0b"), 'Mobile')]
        d_bar.add(legend)
        
        d_bar.add(bc)
        elements.append(Paragraph("Score Comparison (Desktop vs Mobile)", styles['Heading3']))
        elements.append(d_bar)
        
        # Set primary for the rest of the report or we'll need loops
        # Usually Mobile is what they care about for discrepancy
        primary_metrics = m_m 
        pass_metrics = m_m
    else:
        # Single device data (Original Logic)
        s_seo = metrics.get('seo_score', 0) or 0
        s_perf = metrics.get('performance_score', 0) or 0
        s_acc = metrics.get('accessibility_score', 0) or 0
        s_best = metrics.get('best_practices_score', 0) or 0
        
        chart_data = []
        chart_labels = []
        if test_type in ['seo', 'both'] or s_seo > 0:
            chart_data.append(s_seo); chart_labels.append('SEO')
        if test_type in ['performance', 'both'] or s_perf > 0:
            chart_data.append(s_perf); chart_labels.append('Performance')
        if test_type == 'both' or s_acc > 0:
            chart_data.append(s_acc); chart_labels.append('Accessibility')
        if test_type == 'both' or s_best > 0:
            chart_data.append(s_best); chart_labels.append('Best Pract.')
            
        d_bar = Drawing(400, 200)
        bc = VerticalBarChart()
        bc.x = 50; bc.y = 50; bc.height = 125; bc.width = 300
        bc.data = [chart_data]
        bc.valueAxis.valueMin = 0; bc.valueAxis.valueMax = 100
        bc.categoryAxis.categoryNames = chart_labels
        bc.bars[0].fillColor = colors.HexColor("#2563eb")
        d_bar.add(bc)
        
        elements.append(Paragraph("Category Scores", styles['Heading3']))
        elements.append(d_bar)
        primary_metrics = metrics
        pass_metrics = metrics

    elements.append(Spacer(1, 15))
    
    # Counts (Pass/Fail)
    pass_count = 0
    fail_count = 0
    
    if pass_metrics.get('seo_details'):
        for i in pass_metrics['seo_details']:
            if i.get('passed'): pass_count += 1
            else: fail_count += 1
            
    if pass_metrics.get('performance_details'):
        for i in pass_metrics['performance_details']:
            score = i.get('score', 0)
            if score >= 0.9: pass_count += 1
            else: fail_count += 1
            
    # Draw Pie Chart (Pass/Fail)
    if pass_count + fail_count > 0:
        d_pie = Drawing(400, 150)
        pc = Pie()
        pc.x = 100; pc.y = 25; pc.width = 100; pc.height = 100
        pc.data = [pass_count, fail_count]
        pc.labels = [f"Passed ({pass_count})", f"Issues ({fail_count})"]
        pc.slices.strokeWidth = 0.5
        pc.slices[0].fillColor = colors.HexColor("#10b981")
        pc.slices[1].fillColor = colors.HexColor("#ef4444")
        d_pie.add(pc)
        
        legend_pf = Legend()
        legend_pf.alignment = 'right'; legend_pf.x = 300; legend_pf.y = 80
        legend_pf.colorNamePairs = [(colors.HexColor("#10b981"), 'Passed'), (colors.HexColor("#ef4444"), 'Issues')]
        d_pie.add(legend_pf)
        
        elements.append(Paragraph("Audit Status Breakdown", styles['Heading3']))
        elements.append(d_pie)
        elements.append(Spacer(1, 20))


    # ---------------------------------------------------------
    # Critical Issues & Improvements
    # ---------------------------------------------------------
    issues_heading = Paragraph("Required Improvements", heading_style)
    elements.append(issues_heading)
    
    issues_data = [['Category', 'Issue / Recommendation', 'impact']]
    has_issues = False
    
    # SEO Failures
    if metrics.get('seo_details'):
        for check in metrics['seo_details']:
            if not check['passed']:
                text = f"<b>{check['name']}</b><br/>{check.get('details', '')}"
                issues_data.append(['SEO', Paragraph(text, styles['Normal']), 'High'])
                has_issues = True

    # Performance Low Scores (< 0.5 is poor)
    if metrics.get('performance_details'):
        for metric in metrics['performance_details']:
            if metric.get('score', 1) < 0.5:
                text = f"<b>{metric['name']}</b><br/>Value: {metric.get('displayValue')}"
                issues_data.append(['Performance', Paragraph(text, styles['Normal']), 'High'])
                has_issues = True
    
    # Recommendations
    if metrics.get('recommendations'):
        for rec in metrics['recommendations']:
             text = f"<b>{rec['title']}</b><br/>{rec['description']}"
             issues_data.append(['Optimization', Paragraph(text, styles['Normal']), 'Medium'])
             has_issues = True

    if has_issues:
        issues_table = Table(issues_data, colWidths=[1.5*inch, 3.5*inch, 1*inch])
        issues_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('WORDWRAP', (0, 0), (-1, -1), True)
        ]))
        elements.append(issues_table)
    else:
        elements.append(Paragraph("No critical issues found! Great job.", styles['Normal']))
        
    elements.append(Spacer(1, 25))

    # Existing Scores Overview (Simplified or kept as is)
    # Scores Overview
    scores_heading = Paragraph("Detailed Scores", heading_style)
    elements.append(scores_heading)
    
    scores_data = [['Metric', 'Score', 'Rating']]
    
    # Add all 4 scores
    scores_list = [
        ('SEO', s_seo), 
        ('Performance', s_perf), 
        ('Accessibility', s_acc), 
        ('Best Practices', s_best)
    ]
    
    for name, val in scores_list:
        if val > 0: # Show if present
             scores_data.append([name, f"{val}/100", get_rating(val)])
    
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
        seo_heading = Paragraph("SEO Analysis Details", heading_style)
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
        perf_heading = Paragraph("Performance Metrics Details", heading_style)
        elements.append(perf_heading)
        
        perf_details = metrics['performance_details']
        perf_data = [['Metric', 'Value', 'Rating']]
        
        for metric in perf_details:
            # Use score for rating if available
            score = metric.get('score', 0)
            rating = get_metric_rating(score)
            perf_data.append([metric['name'], metric.get('displayValue', 'N/A'), rating])
        
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
    
    # Build PDF
    doc.build(elements)
    
    return pdf_path
    
def generate_batch_seo_pdf(results, job_id, output_dir, test_type='both'):
    """
    Generate a summary PDF for batch SEO/Performance jobs
    """
    pdf_path = f"{output_dir}/batch_report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    report_title = "Batch SEO & Performance Report"
    if test_type == "seo":
        report_title = "Batch SEO Report"
    elif test_type == "performance":
        report_title = "Batch Performance Report"
        
    elements.append(Paragraph(report_title, styles['Title']))
    elements.append(Paragraph(f"Job ID: {job_id} | Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Statistics
    total = len(results)
    success = len([r for r in results if r.get('Status') == 'Success'])
    failed = total - success
    
    # Calculate Averages (filtering out N/A)
    seo_scores = [r.get('SEO Score') for r in results if isinstance(r.get('SEO Score'), (int, float))]
    perf_scores = [r.get('Performance Score') for r in results if isinstance(r.get('Performance Score'), (int, float))]
    
    avg_seo = sum(seo_scores) / len(seo_scores) if seo_scores else 0
    avg_perf = sum(perf_scores) / len(perf_scores) if perf_scores else 0
    
    stats_data = [
        ['Total URLs', total],
        ['Successful Scans', success],
        ['Failed Scans', failed],
        ['Avg SEO Score', f"{avg_seo:.1f}"],
        ['Avg Performance', f"{avg_perf:.1f}"]
    ]
    
    t = Table(stats_data, colWidths=[2*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 25))
    
    # ---------------------------------------------------------
    # Visual Analysis (Charts)
    # ---------------------------------------------------------
    elements.append(Paragraph("Batch Analysis Overview", styles['Heading2']))
    
    # Pie Chart: Success vs Failure
    d_pie = Drawing(400, 150)
    pc = Pie()
    pc.x = 100
    pc.y = 25
    pc.width = 100
    pc.height = 100
    pc.data = [success, failed]
    pc.labels = [f"Success ({success})", f"Failed ({failed})"]
    pc.slices.strokeWidth = 0.5
    pc.slices[0].fillColor = colors.HexColor("#10b981") 
    pc.slices[1].fillColor = colors.HexColor("#ef4444")
    
    d_pie.add(pc)
    
    # Legend
    legend = Legend()
    legend.alignment = 'right'
    legend.x = 300
    legend.y = 80
    legend.colorNamePairs = [(colors.HexColor("#10b981"), 'Success'), (colors.HexColor("#ef4444"), 'Failed')]
    d_pie.add(legend)
    
    elements.append(d_pie)
    elements.append(Spacer(1, 25))
    
    # ---------------------------------------------------------
    # Detailed URL List
    # ---------------------------------------------------------
    elements.append(Paragraph("Detailed URL Analysis", styles['Heading2']))
    
    # Table Header
    has_dual = any('Perf (Desktop)' in r for r in results)
    
    if has_dual:
        det_data = [['URL', 'SEO', 'Perf (D)', 'Perf (M)', 'LCP (M)', 'CLS']]
    else:
        det_data = [['URL', 'SEO', 'Perf', 'LCP', 'CLS', 'TTFB']]
    
    for r in results:
        # Truncate URL for display
        url_text = r.get('URL', '')
        disp_url = Paragraph(url_text, styles['Normal'])
        
        if has_dual:
             det_data.append([
                disp_url,
                r.get('SEO Score', '-'),
                r.get('Perf (Desktop)', '-'),
                r.get('Perf (Mobile)', '-'),
                r.get('LCP (Mobile)', '-'),
                r.get('Cumulative Layout Shift', '-')
            ])
        else:
            det_data.append([
                disp_url,
                r.get('SEO Score', '-'),
                r.get('Performance Score', '-'),
                r.get('Largest Contentful Paint', '-'),
                r.get('Cumulative Layout Shift', '-'),
                r.get('Time to First Byte', '-')
            ])
        
    t_det = Table(det_data, colWidths=[2.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch], repeatRows=1)
    t_det.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('WORDWRAP', (0,0), (-1,-1), True)
    ]))
    
    elements.append(t_det)
    
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


def get_metric_rating(score):
    """Get rating for a metric value based on score (0-1)"""
    if score >= 0.9:
        return 'Good'
    elif score >= 0.5:
        return 'Needs Improv.'
    return 'Poor'
