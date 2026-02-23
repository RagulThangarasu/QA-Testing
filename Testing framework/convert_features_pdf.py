"""
Convert FEATURES.md to a professionally formatted PDF.
Usage: python convert_features_pdf.py
"""
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Preformatted
)


def parse_markdown_to_elements(md_text):
    """Parse markdown text into ReportLab flowable elements."""
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Title'], fontSize=26,
        textColor=colors.HexColor('#1a1a2e'), spaceAfter=6,
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], fontSize=10,
        textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER,
        spaceAfter=20
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'], fontSize=20,
        textColor=colors.HexColor('#1e3a5f'), spaceBefore=24,
        spaceAfter=10, borderWidth=0, borderPadding=0
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'], fontSize=16,
        textColor=colors.HexColor('#2563eb'), spaceBefore=18,
        spaceAfter=8
    )
    h3_style = ParagraphStyle(
        'H3', parent=styles['Heading3'], fontSize=13,
        textColor=colors.HexColor('#374151'), spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=10,
        textColor=colors.HexColor('#1f2937'), leading=14,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=body_style, leftIndent=20,
        bulletIndent=8, spaceAfter=3
    )
    code_style = ParagraphStyle(
        'Code', parent=styles['Code'], fontSize=8,
        textColor=colors.HexColor('#1e293b'),
        backColor=colors.HexColor('#f1f5f9'),
        borderWidth=0.5, borderColor=colors.HexColor('#cbd5e1'),
        borderPadding=6, leading=11, spaceAfter=8,
        fontName='Courier'
    )
    blockquote_style = ParagraphStyle(
        'Blockquote', parent=body_style, fontSize=9,
        textColor=colors.HexColor('#6b7280'), leftIndent=15,
        borderWidth=0, spaceAfter=10, leading=13
    )

    elements = []
    lines = md_text.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    def process_inline(text):
        """Convert inline markdown to ReportLab XML."""
        # First, escape HTML entities in the raw text
        text = text.replace('&', '&amp;')
        
        # Handle inline code FIRST — extract, escape HTML inside, then wrap
        def escape_code(match):
            code = match.group(1)
            code = code.replace('<', '&lt;').replace('>', '&gt;')
            return f'<font face="Courier" size="9" color="#c026d3">{code}</font>'
        text = re.sub(r'`([^`]+)`', escape_code, text)
        
        # Bold + italic
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<u>\1</u>', text)
        return text

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            return
        # Build table
        processed = []
        for row_idx, row in enumerate(table_rows):
            cells = [c.strip() for c in row.split('|')]
            cells = [c for c in cells if c != '']
            # Skip separator rows (---)
            if cells and all(re.match(r'^[-:]+$', c) for c in cells):
                continue
            proc_cells = []
            for c in cells:
                p = Paragraph(process_inline(c), body_style)
                proc_cells.append(p)
            if proc_cells:
                processed.append(proc_cells)

        if not processed:
            table_rows = []
            in_table = False
            return

        # Normalize column count
        max_cols = max(len(r) for r in processed)
        for r in processed:
            while len(r) < max_cols:
                r.append(Paragraph('', body_style))

        # Calculate column widths
        avail = 6.5 * inch
        col_w = avail / max_cols

        t = Table(processed, colWidths=[col_w] * max_cols, repeatRows=1)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]
        # Alternate row colors
        for row_idx in range(1, len(processed)):
            if row_idx % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#f9fafb')))

        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(Spacer(1, 10))
        table_rows = []
        in_table = False

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_lines)
                code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Preformatted(code_text, code_style))
                code_lines = []
                in_code_block = False
            else:
                flush_table()
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Table rows
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
            table_rows.append(line.strip())
            i += 1
            continue
        elif in_table:
            flush_table()

        stripped = line.strip()

        # Empty line
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped in ['---', '***', '___']:
            elements.append(HRFlowable(width="100%", thickness=1,
                                       color=colors.HexColor('#e5e7eb'),
                                       spaceBefore=10, spaceAfter=10))
            i += 1
            continue

        # Headings
        if stripped.startswith('# '):
            text = process_inline(stripped[2:])
            # Main title
            if 'QA Testing Framework' in stripped:
                elements.append(Paragraph(text, title_style))
            else:
                elements.append(Paragraph(text, h1_style))
                elements.append(HRFlowable(width="100%", thickness=0.5,
                                           color=colors.HexColor('#2563eb'),
                                           spaceBefore=2, spaceAfter=8))
            i += 1
            continue
        if stripped.startswith('## '):
            text = process_inline(stripped[3:])
            elements.append(Paragraph(text, h2_style))
            i += 1
            continue
        if stripped.startswith('### '):
            text = process_inline(stripped[4:])
            elements.append(Paragraph(text, h3_style))
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            text = process_inline(stripped.lstrip('> '))
            elements.append(Paragraph(text, blockquote_style))
            i += 1
            continue

        # Bullet list
        if stripped.startswith('- ') or stripped.startswith('* '):
            text = process_inline(stripped[2:])
            elements.append(Paragraph(f"• {text}", bullet_style))
            i += 1
            continue

        # Numbered list
        num_match = re.match(r'^(\d+)\.\s+(.+)', stripped)
        if num_match:
            text = process_inline(num_match.group(2))
            elements.append(Paragraph(f"{num_match.group(1)}. {text}", bullet_style))
            i += 1
            continue

        # Regular paragraph
        text = process_inline(stripped)
        elements.append(Paragraph(text, body_style))
        i += 1

    # Flush remaining table
    if in_table:
        flush_table()

    return elements


def generate_pdf():
    md_path = "FEATURES.md"
    pdf_path = "FEATURES.pdf"

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        rightMargin=60, leftMargin=60,
        topMargin=50, bottomMargin=40
    )

    elements = parse_markdown_to_elements(md_text)
    doc.build(elements)
    print(f"✅ PDF generated: {pdf_path}")


if __name__ == '__main__':
    generate_pdf()
