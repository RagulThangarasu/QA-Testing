import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_path = os.path.join(os.getcwd(), "AI_Functional_Testing_Flow_Diagram.pdf")

doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=22, textColor=HexColor('#1e293b'), spaceAfter=10)
code_style = ParagraphStyle('CustomCode', parent=styles['Normal'], fontName='Courier', fontSize=10, textColor=HexColor('#0f172a'), leading=14, spaceBefore=10)

elements = []

# Title
elements.append(Paragraph("AI Functional Testing - Engine Architecture & Execution Flow", title_style))
elements.append(Spacer(1, 4*mm))

flow_diagram = """
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              USER / CI TRIGGER PHASE                                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
 ┌─────────────┐        ┌──────────────────┐        ┌────────────────────────────────┐
 │ Excel Upload│   OR   │ Sitemap Endpoint │   OR   │ Single Plain-English Prompt    │
 └──────┬──────┘        └────────┬─────────┘        └──────────────┬─────────────────┘
        │                        │                                 │
        └────────────────────────┼─────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          STAGE 1: SYSTEM INITIALIZATION                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
         │
         ├──▶ 1. Validate Target Web URLs
         ├──▶ 2. Test connection to Local Ollama Client (Llama 3 / CodeLlama)
         └──▶ 3. Launch Headless Chromium instance via Playwright
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          STAGE 2: DOM RECONNAISSANCE                                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
         │
         ├──▶ 1. Playwright navigates to staging URL
         ├──▶ 2. Waits for page "Load" event (5-second timeout override)
         ├──▶ 3. Injects internal Javascript mapper into browser window
         └──▶ 4. Extracts full Accessibility Tree (Buttons, Links, Inputs, Modals)
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          STAGE 3: INTELLIGENT AI DECISION                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
         │     (Prompt sent securely to local Ollama API containing DOM & Instruction)
         ├──▶ 1. AI analyzes DOM state vs User Intent
         ├──▶ 2. AI calculates target node (e.g., data-ai-node-id="15")
         ├──▶ 3. AI outputs exact payload: { "action": "click", "element_id": "15" }
         │
         ├──▶ [Fallback Heuristic triggered if AI times out or disconnects!]
         │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          STAGE 4: EXECUTION & VERIFICATION                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
         │
         ├──▶ 1. Python Engine executes Playwright Action (click, type, hover, navigate)
         ├──▶ 2. Framework captures visual evidence snapshot (*_uuid.png format)
         ├──▶ 3. Engine captures updated DOM State post-interaction
         └──▶ 4. AI verifies if "Expected Results" match the new screen state
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          STAGE 5: REPORT GENERATION                                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
         │
         ├──▶ 1. Engine collates Steps into Card formats
         ├──▶ 2. Automatically draws Visual Pass/Fail Pie Charts
         └──▶ 3. Compiles high-resolution PDF for immediate user download
"""

# Format whitespace appropriately for Courier display
formatted_flow = flow_diagram.replace(" ", "&nbsp;").replace("\n", "<br/>")

elements.append(Paragraph(formatted_flow, code_style))

doc.build(elements)
print(f"✅ Generated Flow Diagram PDF at: {pdf_path}")
