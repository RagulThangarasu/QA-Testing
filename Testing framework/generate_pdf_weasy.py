#!/usr/bin/env python3
"""
Convert Markdown documentation to PDF using WeasyPrint
"""

import markdown
from weasyprint import HTML, CSS
import os

def convert_markdown_to_pdf():
    """Convert COMPLETE_WORKFLOW_GUIDE.md to PDF"""
    
    input_file = "COMPLETE_WORKFLOW_GUIDE.md"
    output_file = "Automated_Visual_Testing_Workflow_Guide.pdf"
    
    print(f"📄 Converting {input_file} to {output_file}...")
    
    try:
        # Read markdown
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        print("✓ Markdown file loaded")
        
        # Convert to HTML
        html_content = markdown.markdown(
            md_content, 
            extensions=['tables', 'fenced_code', 'codehilite', 'toc']
        )
        
        print("✓ Converted to HTML")
        
        # Add CSS styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Automated Visual Testing Workflow Guide</title>
            <style>
                @page {{
                    size: A4;
                    margin: 25mm;
                    @bottom-right {{
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #666;
                    }}
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.7;
                    color: #1a202c;
                    font-size: 11pt;
                }}
                
                h1 {{
                    color: #1e40af;
                    border-bottom: 4px solid #3b82f6;
                    padding-bottom: 12px;
                    margin-top: 40px;
                    page-break-after: avoid;
                    font-size: 28pt;
                }}
                
                h1:first-of-type {{
                    margin-top: 0;
                    font-size: 36pt;
                    text-align: center;
                    border-bottom: none;
                }}
                
                h2 {{
                    color: #2563eb;
                    margin-top: 35px;
                    page-break-after: avoid;
                    border-left: 5px solid #3b82f6;
                    padding-left: 15px;
                    font-size: 20pt;
                }}
                
                h3 {{
                    color: #3b82f6;
                    margin-top: 25px;
                    page-break-after: avoid;
                    font-size: 16pt;
                }}
                
                h4 {{
                    color: #4f46e5;
                    margin-top: 20px;
                    font-size: 14pt;
                }}
                
                p {{
                    margin: 12px 0;
                    text-align: justify;
                }}
                
                code {{
                    background: #f1f5f9;
                    padding: 3px 7px;
                    border-radius: 4px;
                    font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
                    font-size: 9.5pt;
                    color: #e11d48;
                }}
                
                pre {{
                    background: #1e293b;
                    color: #e2e8f0;
                    padding: 16px;
                    border-radius: 6px;
                    overflow-x: auto;
                    margin: 20px 0;
                    page-break-inside: avoid;
                    border-left: 4px solid #3b82f6;
                }}
                
                pre code {{
                    background: none;
                    color: inherit;
                    padding: 0;
                }}
                
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                    page-break-inside: avoid;
                    font-size: 10pt;
                }}
                
                th, td {{
                    border: 1px solid #cbd5e1;
                    padding: 10px;
                    text-align: left;
                }}
                
                th {{
                    background: #3b82f6;
                    color: white;
                    font-weight: 600;
                }}
                
                tr:nth-child(even) {{
                    background: #f8fafc;
                }}
                
                blockquote {{
                    border-left: 4px solid #3b82f6;
                    padding-left: 20px;
                    margin-left: 0;
                    color: #64748b;
                    font-style: italic;
                }}
                
                ul, ol {{
                    margin: 15px 0;
                    padding-left: 30px;
                }}
                
                li {{
                    margin: 8px 0;
                }}
                
                hr {{
                    border: none;
                    border-top: 2px solid #e2e8f0;
                    margin: 30px 0;
                }}
                
                .toc {{
                    background: #f1f5f9;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 30px 0;
                    page-break-inside: avoid;
                }}
                
                a {{
                    color: #3b82f6;
                    text-decoration: none;
                }}
                
                /* Checkmarks and symbols */
                li:has(✅), li:has(❌), li:has(⚠️) {{
                    list-style: none;
                }}
                
                /* Page breaks */
                .page-break {{
                    page-break-after: always;
                }}
                
                /* Cover page styling */
                .cover {{
                    text-align: center;
                    padding: 100px 0;
                }}
                
                .cover h1 {{
                    font-size: 42pt;
                    color: #1e40af;
                    margin-bottom: 20px;
                }}
                
                .cover .subtitle {{
                    font-size: 18pt;
                    color: #64748b;
                    margin-top: 20px;
                }}
                
                .cover .version {{
                    font-size: 12pt;
                    color: #94a3b8;
                    margin-top: 40px;
                }}
            </style>
        </head>
        <body>
            <div class="cover">
                <h1>Automated Visual Testing Workflow</h1>
                <div class="subtitle">Complete Guide & Documentation</div>
                <div class="version">Version 1.0 • February 2026</div>
            </div>
            <div class="page-break"></div>
            {html_content}
        </body>
        </html>
        """
        
        print("✓ HTML styled")
        
        # Convert to PDF
        HTML(string=styled_html).write_pdf(output_file)
        
        file_size = os.path.getsize(output_file) / 1024
        print(f"\n✅ Successfully created {output_file}")
        print(f"📊 File size: {file_size:.1f} KB")
        print(f"📍 Location: {os.path.abspath(output_file)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = convert_markdown_to_pdf()
    sys.exit(0 if success else 1)
