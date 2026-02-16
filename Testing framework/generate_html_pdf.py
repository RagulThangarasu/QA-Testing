#!/usr/bin/env python3
"""
Convert Markdown documentation to printable HTML (which can be saved as PDF from browser)
"""

import markdown
import os

def convert_markdown_to_html():
    """Convert COMPLETE_WORKFLOW_GUIDE.md to HTML"""
    
    input_file = "COMPLETE_WORKFLOW_GUIDE.md"
    output_file = "Automated_Visual_Testing_Workflow_Guide.html"
    
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
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Automated Visual Testing Workflow Guide</title>
            <style>
                @page {{
                    size: A4;
                    margin: 25mm;
                }}
                
                @media print {{
                    body {{
                        font-size: 10pt;
                    }}
                    h1 {{
                        page-break-before: always;
                    }}
                    h1:first-of-type {{
                        page-break-before: avoid;
                    }}
                    pre, table, .no-break {{
                        page-break-inside: avoid;
                    }}
                    a {{
                        color: #3b82f6;
                        text-decoration: none;
                    }}
                    a[href]:after {{
                        content: none;
                    }}
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.7;
                    color: #1a202c;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 40px;
                    background: white;
                }}
                
                h1 {{
                    color: #1e40af;
                    border-bottom: 4px solid #3b82f6;
                    padding-bottom: 12px;
                    margin-top: 50px;
                    font-size: 2.5em;
                }}
                
                h1:first-of-type {{
                    margin-top: 0;
                    font-size: 3.5em;
                    text-align: center;
                    border-bottom: none;
                }}
                
                h2 {{
                    color: #2563eb;
                    margin-top: 40px;
                    border-left: 5px solid #3b82f6;
                    padding-left: 15px;
                    font-size: 2em;
                }}
                
                h3 {{
                    color: #3b82f6;
                    margin-top: 30px;
                    font-size: 1.5em;
                }}
                
                h4 {{
                    color: #4f46e5;
                    margin-top: 25px;
                    font-size: 1.2em;
                }}
                
                p {{
                    margin: 15px 0;
                    text-align: justify;
                }}
                
                code {{
                    background: #f1f5f9;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
                    font-size: 0.9em;
                    color: #e11d48;
                }}
                
                pre {{
                    background: #1e293b;
                    color: #e2e8f0;
                    padding: 20px;
                    border-radius: 8px;
                    overflow-x: auto;
                    margin: 25px 0;
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
                    margin: 25px 0;
                    font-size: 0.95em;
                }}
                
                th, td {{
                    border: 1px solid #cbd5e1;
                    padding: 12px;
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
                    margin: 20px 0;
                    padding-left: 35px;
                }}
                
                li {{
                    margin: 10px 0;
                }}
                
                hr {{
                    border: none;
                    border-top: 2px solid #e2e8f0;
                    margin: 40px 0;
                }}
                
                a {{
                    color: #3b82f6;
                    text-decoration: none;
                }}
                
                a:hover {{
                    text-decoration: underline;
                }}
                
                .cover {{
                    text-align: center;
                    padding: 150px 0;
                    min-height: 80vh;
                }}
                
                .cover h1 {{
                    font-size: 4em;
                    color: #1e40af;
                    margin-bottom: 30px;
                    border-bottom: none;
                }}
                
                .cover .subtitle {{
                    font-size: 1.8em;
                    color: #64748b;
                    margin-top: 30px;
                }}
                
                .cover .version {{
                    font-size: 1.2em;
                    color: #94a3b8;
                    margin-top: 60px;
                }}
                
                .print-button {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #3b82f6;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
                    z-index: 1000;
                }}
                
                .print-button:hover {{
                    background: #2563eb;
                }}
                
                @media print {{
                    .print-button {{
                        display: none;
                    }}
                }}
                
                .toc {{
                    background: #f1f5f9;
                    padding: 30px;
                    border-radius: 12px;
                    margin: 40px 0;
                }}
                
                .toc h2 {{
                    margin-top: 0;
                    border-left: none;
                    padding-left: 0;
                }}
            </style>
        </head>
        <body>
            <button class="print-button" onclick="window.print()">🖨️ Print / Save as PDF</button>
            
            <div class="cover">
                <h1>Automated Visual Testing Workflow</h1>
                <div class="subtitle">Complete Guide & Documentation</div>
                <div class="version">Version 1.0 • February 2026</div>
            </div>
            
            {html_content}
            
            <hr>
            <p style="text-align: center; color: #94a3b8; margin: 60px 0;">
                <strong>End of Document</strong><br>
                For support, refer to the documentation files in the project.
            </p>
        </body>
        </html>
        """
        
        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        file_size = os.path.getsize(output_file) / 1024
        abs_path = os.path.abspath(output_file)
        
        print(f"\n✅ Successfully created {output_file}")
        print(f"📊 File size: {file_size:.1f} KB")
        print(f"📍 Location: {abs_path}")
        print(f"\n📖 To create PDF:")
        print(f"   1. Open file in browser: file://{abs_path}")
        print(f"   2. Click the 'Print / Save as PDF' button")
        print(f"   3. Or press Cmd+P (Mac) / Ctrl+P (Windows)")
        print(f"   4. Select 'Save as PDF' as destination")
        print(f"   5. Click 'Save'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = convert_markdown_to_html()
    sys.exit(0 if success else 1)
