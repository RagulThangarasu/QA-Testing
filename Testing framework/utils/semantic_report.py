"""
HTML Semantic Validation PDF Report Generator
Generates a professional PDF report for semantic validation results.
"""

import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from xml.sax.saxutils import escape as _xml_escape


def _esc(text):
    """Escape text so it is safe for ReportLab Paragraph (XML-based parser)."""
    if not text:
        return ''
    return _xml_escape(str(text))


def generate_semantic_report(result, job_id, job_dir):
    """
    Generate a PDF report from semantic validation results.
    Returns the path to the generated PDF file.
    """
    pdf_filename = f"semantic_report_{job_id}.pdf"
    pdf_path = os.path.join(job_dir, pdf_filename)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor('#1a1a2e'),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor('#16213e'),
        fontName='Helvetica-Bold',
        borderPadding=(4, 0, 0, 0)
    ))
    
    styles.add(ParagraphStyle(
        name='SubHeader',
        parent=styles['Heading3'],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor('#0f3460'),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='IssueMessage',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='IssueDetail',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        spaceAfter=2,
        leftIndent=12
    ))
    
    styles.add(ParagraphStyle(
        name='MetaInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#777777'),
        spaceAfter=2
    ))
    
    elements = []
    
    # ─── TITLE ───
    elements.append(Paragraph("🔍 HTML Semantic Validation Report", styles['ReportTitle']))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3b82f6')))
    elements.append(Spacer(1, 10))
    
    # ─── SUMMARY INFO ───
    url = result.get('url', 'N/A')
    score = result.get('score', 0)
    total_issues = result.get('total_issues', 0)
    critical = result.get('critical', 0)
    warnings = result.get('warnings', 0)
    info_count = result.get('info', 0)
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary_data = [
        ['Field', 'Value'],
        ['URL', Paragraph(f'<font color="#3b82f6">{_esc(url)}</font>', styles['Normal'])],
        ['Date', now],
        ['Job ID', job_id],
        ['Semantic Score', f'{score}/100'],
        ['Total Issues', str(total_issues)],
        ['Critical', str(critical)],
        ['Warnings', str(warnings)],
        ['Informational', str(info_count)],
        ['HTTP Status', str(result.get('status_code', 'N/A'))],
        ['HTML Size', f'{result.get("html_size", 0):,} bytes'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2 * inch, 4.5 * inch])
    
    # Score color
    if score >= 80:
        score_color = colors.HexColor('#10b981')
    elif score >= 60:
        score_color = colors.HexColor('#f59e0b')
    else:
        score_color = colors.HexColor('#ef4444')
    
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#4b5563')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 12))
    
    # ─── SCORE INDICATOR ───
    grade = "Excellent" if score >= 90 else "Good" if score >= 75 else "Needs Work" if score >= 50 else "Poor"
    score_text = f'<font size="14" color="{score_color.hexval()}">{score}/100 — {grade}</font>'
    elements.append(Paragraph(score_text, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # ─── ELEMENT SUMMARY ───
    element_summary = result.get('element_summary', {})
    if element_summary:
        elements.append(Paragraph("📊 Element Summary", styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        elements.append(Spacer(1, 6))
        
        total_els = element_summary.get('total_elements', 0)
        semantic_ratio = element_summary.get('semantic_ratio', 0)
        elements.append(Paragraph(
            f"Total Elements: <b>{total_els}</b> | Semantic Ratio: <b>{semantic_ratio}%</b>",
            styles['Normal']
        ))
        elements.append(Spacer(1, 8))
        
        # Headings
        headings = element_summary.get('headings', {})
        if headings:
            elements.append(Paragraph("Heading Structure:", styles['SubHeader']))
            heading_text = " → ".join([f"<b>{tag}</b>: {count}" for tag, count in sorted(headings.items())])
            elements.append(Paragraph(heading_text, styles['IssueDetail']))
            elements.append(Spacer(1, 6))
        
        # Semantic elements
        semantic_els = element_summary.get('semantic_elements', {})
        if semantic_els:
            elements.append(Paragraph("Semantic Elements Found:", styles['SubHeader']))
            sem_text = ", ".join([f"<b>&lt;{tag}&gt;</b> ({count})" for tag, count in sorted(semantic_els.items())])
            elements.append(Paragraph(sem_text, styles['IssueDetail']))
            elements.append(Spacer(1, 6))
        
        # Structural elements
        structural_els = element_summary.get('structural_elements', {})
        if structural_els:
            elements.append(Paragraph("Structural Elements:", styles['SubHeader']))
            struct_text = ", ".join([f"<b>&lt;{tag}&gt;</b> ({count})" for tag, count in sorted(structural_els.items())])
            elements.append(Paragraph(struct_text, styles['IssueDetail']))
        
        elements.append(Spacer(1, 12))
    
    # ─── RECOMMENDED HEADING STRUCTURE ───
    rec_headings = result.get('recommended_headings', {})
    current_outline = rec_headings.get('current_outline', [])
    recommended = rec_headings.get('recommended', [])
    
    if current_outline or recommended:
        elements.append(Paragraph("📐 Heading Structure", styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        elements.append(Spacer(1, 6))
        
        # Current outline
        if current_outline:
            elements.append(Paragraph("Current Outline:", styles['SubHeader']))
            for h in current_outline:
                indent = (h.get('level', 1) - 1) * 20
                tag = h.get('tag', 'h1')
                text = _esc(h.get('text', ''))
                elements.append(Paragraph(
                    f'<font color="#6366f1"><b>&lt;{tag}&gt;</b></font>  {text}',
                    ParagraphStyle(
                        name=f'Heading_{tag}_{id(h)}',
                        parent=styles['Normal'],
                        fontSize=9,
                        leftIndent=indent + 12,
                        spaceAfter=2
                    )
                ))
            elements.append(Spacer(1, 8))
        
        # Recommended structure
        if recommended:
            elements.append(Paragraph("Recommended Structure:", styles['SubHeader']))
            for h in recommended:
                indent = (h.get('level', 1) - 1) * 20
                tag = h.get('tag', 'h1')
                text = _esc(h.get('text', ''))
                reason = _esc(h.get('reason', ''))
                para_text = f'<font color="#10b981"><b>&lt;{tag}&gt;</b></font>  {text}'
                if reason:
                    para_text += f'  <font size="7" color="#9ca3af">— {reason}</font>'
                elements.append(Paragraph(
                    para_text,
                    ParagraphStyle(
                        name=f'Rec_{tag}_{id(h)}',
                        parent=styles['Normal'],
                        fontSize=9,
                        leftIndent=indent + 12,
                        spaceAfter=2
                    )
                ))
            elements.append(Spacer(1, 12))
    
    # ─── CATEGORY BREAKDOWN ───
    category_counts = result.get('category_counts', {})
    if category_counts:
        elements.append(Paragraph("📂 Issues by Category", styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        elements.append(Spacer(1, 6))
        
        cat_data = [['Category', 'Issues']]
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            cat_data.append([cat, str(count)])
        
        cat_table = Table(cat_data, colWidths=[4 * inch, 2.5 * inch])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        
        elements.append(cat_table)
        elements.append(Spacer(1, 12))
    
    # ─── ISSUES DETAIL ───
    issues = result.get('issues', [])
    if issues:
        elements.append(Paragraph("🔎 Detailed Issues", styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        elements.append(Spacer(1, 8))
        
        # Group issues by category
        grouped = {}
        for issue in issues:
            cat = issue.get("category", "Other")
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(issue)
        
        severity_colors = {
            'critical': colors.HexColor('#ef4444'),
            'warning': colors.HexColor('#f59e0b'),
            'info': colors.HexColor('#3b82f6')
        }
        
        severity_labels = {
            'critical': '🔴 Critical',
            'warning': '🟡 Warning',
            'info': '🔵 Info'
        }
        
        for category, cat_issues in grouped.items():
            elements.append(Paragraph(f"▸ {category} ({len(cat_issues)} issue{'s' if len(cat_issues)>1 else ''})", styles['SubHeader']))
            
            for i, issue in enumerate(cat_issues):
                sev = issue.get("severity", "info")
                sev_label = severity_labels.get(sev, "Info")
                sev_color = severity_colors.get(sev, colors.HexColor('#3b82f6'))
                
                # Issue table
                issue_data = [
                    [
                        Paragraph(f'<font color="{sev_color.hexval()}">{sev_label}</font>', styles['Normal']),
                        Paragraph(f'<b>{_esc(issue.get("message", ""))}</b>', styles['Normal'])
                    ],
                    [
                        '',
                        Paragraph(f'<i>{_esc(issue.get("detail", ""))}</i>', styles['IssueDetail'])
                    ],
                ]
                
                wcag = issue.get('wcag', '—')
                element_str = issue.get('element', '')
                if wcag != '—' or element_str:
                    meta_parts = []
                    if element_str:
                        meta_parts.append(f'Element: <font color="#6366f1"><b>{_esc(element_str)}</b></font>')
                    if wcag != '—':
                        meta_parts.append(f'WCAG: {wcag}')
                    issue_data.append([
                        '',
                        Paragraph(' | '.join(meta_parts), styles['MetaInfo'])
                    ])
                
                issue_table = Table(issue_data, colWidths=[1.2 * inch, 5.3 * inch])
                issue_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ]))
                
                elements.append(issue_table)
                elements.append(Spacer(1, 4))
            
            elements.append(Spacer(1, 8))
    
    # ─── FOOTER ───
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f'<font size="8" color="#9ca3af">Generated by QA Testing Framework — Semantic Validator | {now}</font>',
        ParagraphStyle(name='Footer', parent=styles['Normal'], alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    return pdf_path
