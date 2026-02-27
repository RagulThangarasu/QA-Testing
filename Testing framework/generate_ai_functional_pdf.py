import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_path = os.path.join(os.getcwd(), "AI_Functional_Testing_Features_and_Flow.pdf")

doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=22, textColor=HexColor('#1e293b'), spaceAfter=12)
header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=16, textColor=HexColor('#2563eb'), spaceAfter=8, spaceBefore=12)
body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=11, textColor=HexColor('#334155'), spaceAfter=6, leading=16)
bold_style = ParagraphStyle('CustomBold', parent=styles['Normal'], fontSize=11, textColor=HexColor('#0f172a'), spaceAfter=6, leading=16, fontName='Helvetica-Bold')

elements = []

# Title
elements.append(Paragraph("AI Functional Testing Module", title_style))
elements.append(Spacer(1, 4*mm))

# Intro
intro_text = "The AI Functional Testing module is a zero-locator, plain-English testing solution powered by local LLMs (Ollama) and Playwright. It bypasses the need for traditional brittle locators like XPath or CSS selectors by allowing the AI to logically deduce actions based on the DOM context."
elements.append(Paragraph(intro_text, body_style))
elements.append(Spacer(1, 4*mm))

# Features
elements.append(Paragraph("Core Features", header_style))

features = [
    "<b>Zero-Locator Testing:</b> Write test cases in simple English (e.g., 'Click the submit button' or 'Verify the success message'). The local AI engine maps these intents to actual DOM elements intelligently, preventing tests from breaking when class names or IDs change.",
    "<b>Component Auto-Discovery:</b> Automatically scans and identifies the semantic meaning of web elements (like buttons, navigation bars, modals, and inputs) using an injected JavaScript evaluator, granting the AI a comprehensive map of the page.",
    "<b>Batch Sitemap & Excel Processing:</b> Scale up automation effortlessly by uploading a spreadsheet of test cases alongside a root sitemap URL. The system will autonomy crawl through multiple pages testing all constraints simultaneously.",
    "<b>Visual Graph Reporting:</b> Automatically produces a dynamic PDF report packed with a high-level visual pie chart breaking down Passed/Failed/Skipped test steps, wrapping granular verification traces cleanly for easy analysis.",
    "<b>Self-Healing Fallbacks:</b> If the local AI inference engine times out, disconnects, or fails, the module features a robust keyword-matching fallback heuristic to guarantee tests finish without crashing.",
    "<b>100% Data Privacy (Local Execution):</b> By leveraging local instances of Ollama (like Llama 3), your proprietary staging DOMs and sensitive internal testing data never leave your local private network."
]

for feature in features:
    elements.append(Paragraph(f"• {feature}", body_style))

elements.append(Spacer(1, 6*mm))

# Workflow
elements.append(Paragraph("End-to-End Workflow Flow", header_style))

flow_steps = [
    "<b>1. Test Case Creation & Upload:</b> The user downloads the pre-formatted Excel template, fills in their goals, action descriptions, expected outcome text, and uploads it via the web dashboard.",
    "<b>2. Environment Initialization:</b> The user inputs the target Web URL (or sitemap) and connects the execution loop to the locally hosted Ollama client.",
    "<b>3. Headless Playwright Navigation:</b> The backend spawns an invisible Chrome instance, navigates to the target URLs, and waits for structural load completion.",
    "<b>4. DOM Extraction & Mapping:</b> The page is scanned. An accessibility tree of all interactable nodes (inputs, buttons, links) is sent as a compact JSON map to the LLM alongside the plain English instruction.",
    "<b>5. AI Decision Making:</b> The LLM identifies the precise DOM Element ID required and formats a Playwright action (click, type, hover, verify, navigate).",
    "<b>6. Action Execution & Verdict:</b> Playwright carries out the LLMs decision on the live page. For verifications, expected results are cross-checked contextually across the updated DOM.",
    "<b>7. PDF Report Generation:</b> A highly-formatted final summary report (complete with action logs and a visual pie chart) is bundled and served to the user for download."
]

for step in flow_steps:
    elements.append(Paragraph(f"{step}", body_style))


doc.build(elements)
print(f"✅ Generated PDF at: {pdf_path}")
