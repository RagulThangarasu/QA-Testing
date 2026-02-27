import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_path = os.path.join(os.getcwd(), "AI_Functional_Testing_Technical_Architecture.pdf")

doc = SimpleDocTemplate(
    pdf_path, 
    pagesize=A4, 
    leftMargin=15*mm, rightMargin=15*mm, 
    topMargin=20*mm, bottomMargin=20*mm
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'DocTitle', parent=styles['Title'], 
    fontSize=18, textColor=HexColor('#0f172a'), 
    spaceAfter=6, fontName='Helvetica-Bold', alignment=0
)
subtitle_style = ParagraphStyle(
    'DocSubtitle', parent=styles['Normal'], 
    fontSize=10, textColor=HexColor('#64748b'), 
    spaceAfter=20, alignment=0
)

# Dark header for the cards
phase_title_style = ParagraphStyle(
    'PhaseTitle', parent=styles['Normal'], 
    fontSize=11, textColor=HexColor('#ffffff'), 
    fontName='Helvetica-Bold', leading=14
)
# Normal body for explanations
phase_body_style = ParagraphStyle(
    'PhaseBody', parent=styles['Normal'], 
    fontSize=9, textColor=HexColor('#334155'), 
    leading=13
)
# Monospace for technical details / payloads
tech_detail_style = ParagraphStyle(
    'TechDetail', parent=styles['Normal'], 
    fontSize=8, textColor=HexColor('#0369a1'), 
    fontName='Courier', leading=10, 
    backColor=HexColor('#f0f9ff'), borderPadding=3
)

arrow_style = ParagraphStyle(
    'Arrow', parent=styles['Normal'], 
    fontSize=16, textColor=HexColor('#94a3b8'), 
    alignment=1, spaceAfter=8, spaceBefore=8
)

elements = []

elements.append(Paragraph("AI-Driven Functional Engine: Technical Architecture", title_style))
elements.append(Paragraph("Pipeline execution flow, system boundaries, and data payloads.", subtitle_style))

# Define the technical pipeline steps
pipeline = [
    {
        "phase": "PHASE 1: ORCHESTRATION & INPUT PARSING",
        "desc": "The Flask backend receives an execution request via REST API. It initializes a unique Job ID, allocates working directories, and parses the input payload containing target URLs, test instructions, and expected state conditions.",
        "tech": "Endpoints: /api/functional | Payload schema verification | Job Thread Allocation"
    },
    {
        "phase": "PHASE 2: HEADLESS BROWSER INSTANTIATION",
        "desc": "The engine orchestrates a synchronous Playwright Chromium context. It injects custom User-Agent strings, sets explicit viewport boundaries (1440x900), and navigates to the target staging URI with strict load-state overrides.",
        "tech": "Dependencies: playwright.sync_api | State: wait_until='domcontentloaded', timeout=30s"
    },
    {
        "phase": "PHASE 3: DOM HARVESTING & NORMALIZATION",
        "desc": "Post-navigation, a proprietary JavaScript mapper is injected via page.evaluate(). It traverses the physical DOM, filtering out non-interactive nodes, and constructs a minimalist Accessibility Tree mapped by unique data-ai-node-id tags.",
        "tech": "Output Payload: List[Dict] -> { 'id': 5, 'tag': 'button', 'text': 'Submit', 'aria': 'login' }"
    },
    {
        "phase": "PHASE 4: AI INFERENCE PIPELINE",
        "desc": "The engine constructs a comprehensive prompt containing the parsed Accessibility Tree, the specific test instruction, and the current DOM state matrix. This is transmitted via HTTP to the localized Ollama integration (LLM inference).",
        "tech": "Model: llama3 / codellama | Retry Logic: Exponential Backoff (Max 3) | Timeout: 120s"
    },
    {
        "phase": "PHASE 5: ACTION EXECUTION & STATE ASSERTION",
        "desc": "Upon structured JSON response from the LLM, Playwright executes the simulated hardware action (click, type, hover) on the mapped data-ai-node-id. The engine snaps a UUID-bound screenshot and verifies visual text assertions against the subsequent DOM state.",
        "tech": "Action Router: execute_action() | Locators: page.locator('[data-ai-node-id=\"#\"]')"
    },
    {
        "phase": "PHASE 6: ARTIFACT & REPORT COMPILATION",
        "desc": "The workflow aggregates step metrics, error stack traces, and captured screenshot URIs. ReportLab computes dynamic layout wrapping and renders a standardized A4 PDF containing execution analytics and pie-chart visualizations.",
        "tech": "Generators: json.dump(), reportlab.platypus.SimpleDocTemplate | Metrics: Passed/Failed %"
    }
]

for i, step in enumerate(pipeline):
    # Construct the table row data
    card_data = [
        [Paragraph(step["phase"], phase_title_style)],
        [Paragraph(step["desc"], phase_body_style)],
        [Paragraph(f"TECHNICAL CONTEXT:<br/>{step['tech']}", tech_detail_style)]
    ]
    
    t = Table(card_data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), HexColor('#1e293b')), # Slate-900 header
        ('BACKGROUND', (0,1), (0,1), HexColor('#ffffff')), # White body
        ('BACKGROUND', (0,2), (0,2), HexColor('#f8fafc')), # Light tech background
        
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#cbd5e1')),
        
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        
        ('TOPPADDING', (0,1), (-1,1), 8),
        ('BOTTOMPADDING', (0,1), (-1,1), 8),
        
        ('TOPPADDING', (0,2), (-1,-1), 6),
        ('BOTTOMPADDING', (0,2), (-1,-1), 6),
        
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    
    elements.append(t)
    
    # Draw arrow down (except for the last one)
    if i < len(pipeline) - 1:
        elements.append(Paragraph("↓", arrow_style))

doc.build(elements)
print(f"✅ Generated Technical Flow PDF at: {pdf_path}")
