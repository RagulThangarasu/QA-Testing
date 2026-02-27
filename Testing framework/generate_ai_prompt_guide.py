import os
import signal
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black, lightgrey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Handle "[Errno 32] Broken pipe" gracefully
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except Exception:
    pass

def generate_prompt_guide(filename="AI_Testing_Prompt_Guide.pdf"):
    pdf_path = os.path.join(os.getcwd(), filename)
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                            leftMargin=15*mm, rightMargin=15*mm, 
                            topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=24, textColor=HexColor('#1e293b'), spaceAfter=20, alignment=1)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading1'], fontSize=18, textColor=HexColor('#2563eb'), spaceBefore=15, spaceAfter=10)
    subheader_style = ParagraphStyle('SubHeaderStyle', parent=styles['Heading2'], fontSize=14, textColor=HexColor('#0f172a'), spaceBefore=10, spaceAfter=8)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=11, leading=14, textColor=HexColor('#334155'), spaceAfter=8)
    code_style = ParagraphStyle('CodeStyle', parent=styles['Normal'], fontSize=9, fontName='Courier', textColor=HexColor('#1e293b'), leftIndent=10, rightIndent=10, spaceBefore=5, spaceAfter=5, backColor=HexColor('#f1f5f9'), borderPadding=5)
    bullet_style = ParagraphStyle('BulletStyle', parent=styles['Normal'], fontSize=11, leading=14, leftIndent=20, bulletIndent=10, spaceAfter=5)

    elements = []

    # Title Page
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph("AI Testing Prompt Engineering Guide", title_style))
    elements.append(Paragraph("A Masterclass in Zero-Locator Web Automation", styles['Normal']))
    elements.append(Spacer(1, 100*mm))
    elements.append(Paragraph("QA Testing Framework v2.0", styles['Normal']))
    elements.append(PageBreak())

    # Introduction
    elements.append(Paragraph("1. Understanding AI-Driven Testing", header_style))
    elements.append(Paragraph("Traditional testing relies on IDs, XPaths, and CSS selectors. When the UI changes, tests break. Our AI Functional Testing module uses a 'Zero-Locator' approach. You describe the action in plain English, and the AI deduces the target by looking at the page's current state (the DOM).", body_style))
    
    # Writing Effective Prompts
    elements.append(Paragraph("2. How to Write Effective Prompts", header_style))
    elements.append(Paragraph("The key to training the AI to execute your tests correctly is providing clear 'Action Descriptions'. Follow these best practices:", body_style))
    
    elements.append(Paragraph("• <b>Be Explicit:</b> Instead of 'Submit', say 'Click the blue login button'.", bullet_style))
    elements.append(Paragraph("• <b>Reference Text:</b> Use text visible on the screen. E.g., 'Click the link that says Contact Us'.", bullet_style))
    elements.append(Paragraph("• <b>Describe Type Actions:</b> Mention the input label. E.g., 'Type MySecretPassword into the Password field'.", bullet_style))
    elements.append(Paragraph("• <b>Chain Actions via Steps:</b> Keep each test case focused on ONE primary action.", bullet_style))

    # Internal Prompts (The "Training")
    elements.append(Paragraph("3. How the AI is 'Trained' (System Prompts)", header_style))
    elements.append(Paragraph("Under the hood, your 'Action Description' is injected into a sophisticated System Prompt. This prompt 'trains' the local LLM to behave like a QA engineer. Here is the exact frame used for decision making:", body_style))
    
    internal_prompt = """
    "You are an automated web browser QA tester. 
    The user wants to perform this test action: {instruction}
    Here are the visible interactive elements on the page (JSON array): {dom_state}
    Based on the instruction, determine: 
    1. Which element_id to interact with 
    2. What action to perform (click, type, hover, etc.)"
    """
    elements.append(Paragraph(internal_prompt.replace('\n', '<br/>'), code_style))

    # Examples & Use Cases
    elements.append(Paragraph("4. Common Testing Prompts & Examples", header_style))
    
    data = [
        ["Testing Category", "Action Description (Prompt)", "Expected Result (Verification)"],
        ["Navigation", "Click the 'Products' link in the main header", "The products listing page is visible"],
        ["Search", "Type 'Red Sneakers' in the search bar and press enter", "Search results for Red Sneakers are shown"],
        ["Forms", "Select 'United States' from the Country dropdown", "United States is selected"],
        ["Verification", "Verify that the error message 'Invalid email' is visible", "Success: User sees the validation error"],
        ["Validation", "Check if the navigation bar contains exactly 5 links", "Internal links are correct"]
    ]
    
    t = Table(data, colWidths=[35*mm, 75*mm, 70*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#2563eb')),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(Spacer(1, 5*mm))
    elements.append(t)

    # Advanced Guidance
    elements.append(Paragraph("5. Training the AI on Custom Logic", subheader_style))
    elements.append(Paragraph("If you have complex components, you can 'guide' the AI by including context in the Action Description. For example:", body_style))
    elements.append(Paragraph("<i>'In the second card within the product grid, find the heart icon and click it'</i>", code_style))
    elements.append(Paragraph("The AI will identify that it needs to look for a specific container before finding the interactable element.", body_style))

    # Conclusion
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("<b>Tip:</b> If the AI fails, check the 'Reasoning' column in the generated results. It often explains why it couldn't find an element, allowing you to refine your prompt further.", body_style))

    doc.build(elements)
    print(f"✅ Generated PDF at: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generate_prompt_guide()
