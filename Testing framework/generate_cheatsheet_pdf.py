import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_path = os.path.join(os.getcwd(), "AI_Functional_Testing_Cheat_Sheet.pdf")

doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=20*mm, bottomMargin=20*mm)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=20, textColor=HexColor('#1e293b'), spaceAfter=10)
header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=14, textColor=HexColor('#2563eb'), spaceAfter=6, spaceBefore=10)
body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=10, textColor=HexColor('#334155'), spaceAfter=4, leading=14)
code_style = ParagraphStyle('CustomCode', parent=styles['Normal'], fontName='Courier', fontSize=9, textColor=HexColor('#be185d'), backColor=HexColor('#fce7f3'), borderPadding=2)

elements = []

# Title
elements.append(Paragraph("AI Functional Testing - Cheat Sheet", title_style))
elements.append(Paragraph("A comprehensive guide on how to write effective plain-English instructions and expected results for the AI-driven functional test engine.", body_style))
elements.append(Spacer(1, 4*mm))

# The engine supports: click, type, select, verify, hover, navigate, wait
elements.append(Paragraph("Supported Actions", header_style))

# Create table
table_data = [
    [Paragraph("<b>Action Type</b>", body_style), Paragraph("<b>How it works</b>", body_style), Paragraph("<b>Example Instruction (Prompt)</b>", body_style)]
]

actions = [
    ("Navigation", "Navigates the browser to a completely new URL. Always start URLs with http/https.", "&lt;font name='Courier'&gt;Navigate to https://example.com/login&lt;/font&gt;"),
    ("Click", "Finds the described button, link, or element and clicks it.", "1. &lt;font name='Courier'&gt;Click the 'Sign In' button&lt;/font&gt;\n2. &lt;font name='Courier'&gt;Click the profile account icon at the top right&lt;/font&gt;"),
    ("Type / Input", "Finds the correct input field and types the provided text into it.", "1. &lt;font name='Courier'&gt;Type 'admin@test.com' into the Email field&lt;/font&gt;\n2. &lt;font name='Courier'&gt;Search for 'Running Shoes'&lt;/font&gt;"),
    ("Hover", "Simulates moving the mouse cursor over an element to trigger dropdowns or tooltips.", "1. &lt;font name='Courier'&gt;Hover over the 'Products' menu&lt;/font&gt;\n2. &lt;font name='Courier'&gt;Hover on the 'Info' icon&lt;/font&gt;"),
    ("Select (Dropdown)", "Selects a specific option from a native dropdown select element.", "1. &lt;font name='Courier'&gt;Select 'United States' from the Country dropdown&lt;/font&gt;"),
    ("Wait", "Pauses execution for a set time (in milliseconds) or until a network state.", "1. &lt;font name='Courier'&gt;Wait for 3000 milliseconds&lt;/font&gt;\n2. &lt;font name='Courier'&gt;Wait for the loader to disappear&lt;/font&gt;"),
    ("Verify / Check", "Checks if a specific element or text is present and visible on the physical page.", "1. &lt;font name='Courier'&gt;Verify the 'Welcome back' message is visible&lt;/font&gt;\n2. &lt;font name='Courier'&gt;Check that the cart is empty&lt;/font&gt;")
]

for act, desc, ex in actions:
    ex_p = Paragraph(ex.replace('\n', '<br/>'), body_style)
    table_data.append([Paragraph(f"<b>{act}</b>", body_style), Paragraph(desc, body_style), ex_p])

action_table = Table(table_data, colWidths=[30*mm, 60*mm, 90*mm])
action_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), HexColor('#1e293b')),
    ('TEXTCOLOR', (0,0), (-1,0), HexColor('#ffffff')),
    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, HexColor('#e2e8f0')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#ffffff'), HexColor('#f8fafc')]),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING', (0,0), (-1,-1), 4),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
]))
elements.append(action_table)
elements.append(Spacer(1, 6*mm))


# Form filling best practices
elements.append(Paragraph("Best Practices for Writing Steps", header_style))
form_practices = [
    "<b>Be Specific with Inputs:</b> Instead of '<i>fill the form</i>', logically explain what to put where: '<i>Type \"John\" into the First Name field, and \"Doe\" into the Last Name field</i>'. Or split them into multiple test steps.",
    "<b>Combine Text with Values:</b> Use explicit quotes for values so the AI knows exactly what string to use. e.g. <i>Type \"password123\" into the Password box.</i>",
    "<b>Handling Multi-step Checkouts:</b> Use 'Wait' actions if you know the application has slow animated transitions that block clicking."
]
for fp in form_practices:
    elements.append(Paragraph(f"• {fp}", body_style))
elements.append(Spacer(1, 4*mm))


# Expected Results
elements.append(Paragraph("How to write 'Expected Results'", header_style))
elements.append(Paragraph("The Expected Result column acts as an assertion mechanism. After executing the 'Instruction', the AI compares the updated application layout against your Expectation text.", body_style))

er_table_data = [
    [Paragraph("<b>Scenario</b>", body_style), Paragraph("<b>Bad Expected Result ❌</b>", body_style), Paragraph("<b>Good Expected Result ✅</b>", body_style)],
    [Paragraph("Successful Login", body_style), Paragraph("User is logged in", body_style), Paragraph("The dashboard should be visible and contain the text 'Overview'", body_style)],
    [Paragraph("Failed Submission", body_style), Paragraph("It fails", body_style), Paragraph("A red error message saying 'Invalid Email' appears under the input", body_style)],
    [Paragraph("Cart Addition", body_style), Paragraph("Works correctly", body_style), Paragraph("The cart counter at the top right should update to '1'", body_style)]
]

er_table = Table(er_table_data, colWidths=[40*mm, 70*mm, 70*mm])
er_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), HexColor('#475569')),
    ('TEXTCOLOR', (0,0), (-1,0), HexColor('#ffffff')),
    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, HexColor('#cbd5e1')),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING', (0,0), (-1,-1), 4),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
]))
elements.append(er_table)


doc.build(elements)
print(f"✅ Generated Cheat Sheet PDF at: {pdf_path}")
