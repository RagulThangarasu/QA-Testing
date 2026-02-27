import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_path = os.path.join(os.getcwd(), "AI_Functional_Testing_Flow_Clear.pdf")

doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=20, textColor=HexColor('#0f172a'), spaceAfter=8)
subtitle_style = ParagraphStyle('CustomSub', parent=styles['Normal'], fontSize=11, textColor=HexColor('#64748b'), spaceAfter=20, alignment=1) # Center aligned

box_title_style = ParagraphStyle('BoxTitle', parent=styles['Normal'], fontSize=12, textColor=HexColor('#ffffff'), fontName='Helvetica-Bold', alignment=1)
box_body_style = ParagraphStyle('BoxBody', parent=styles['Normal'], fontSize=10, textColor=HexColor('#334155'), leading=14, alignment=1)
arrow_style = ParagraphStyle('Arrow', parent=styles['Normal'], fontSize=24, textColor=HexColor('#cbd5e1'), alignment=1, spaceAfter=5, spaceBefore=5)

elements = []

# Title
elements.append(Paragraph("<b>AI Functional Testing Flow</b>", title_style))
elements.append(Paragraph("A clear step-by-step Execution Pipeline", subtitle_style))

# Flow Steps Data
steps = [
    {
        "title": "1. User Input Trigger",
        "desc": "User uploads an Excel file, provides a Sitemap URL, or enters a Plain-English instruction.",
        "color": HexColor('#3b82f6') # Blue
    },
    {
        "title": "2. System Initialization",
        "desc": "Validates the target URLs, tests the connection to the Local Ollama AI Client (e.g., Llama 3), and launches a headless browser via Playwright.",
        "color": HexColor('#8b5cf6') # Purple
    },
    {
        "title": "3. DOM Reconnaissance",
        "desc": "Navigates to the staging URL, waits for structural loading, and injects a JS mapper to harvest the physical Accessibility Tree (all interactive nodes).",
        "color": HexColor('#06b6d4') # Cyan
    },
    {
        "title": "4. Intelligent AI Decision",
        "desc": "The AI calculates target element IDs natively within your local network. Combines DOM elements and user instructions to output an exact execution payload.",
        "color": HexColor('#f59e0b') # Amber / Orange
    },
    {
        "title": "5. Execution & Verification",
        "desc": "Physically simulates the typing/clicking actions. Takes a UUID-stamped screenshot, captures the updated DOM state, and validates Expected Results natively.",
        "color": HexColor('#10b981') # Emerald
    },
    {
        "title": "6. Report Generation",
        "desc": "Renders individual status cards and pass/fail summary pie charts into a dynamic PDF report for immediate user download.",
        "color": HexColor('#f43f5e') # Rose / Red
    }
]

# We will create nice rectangular boxes for each step, and down arrows between them
for i, step in enumerate(steps):
    # Box rendering
    card_data = [
        [Paragraph(step["title"], box_title_style)],
        [Paragraph(step["desc"], box_body_style)]
    ]
    
    t = Table(card_data, colWidths=[140*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), step["color"]), # Header Color
        ('BACKGROUND', (0,1), (0,1), HexColor('#f8fafc')), # Body Color
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    
    elements.append(t)
    
    # Draw arrow down (except for the last one)
    if i < len(steps) - 1:
        elements.append(Paragraph("⬇", arrow_style))

doc.build(elements)
print(f"✅ Generated Clear Flow PDF at: {pdf_path}")
