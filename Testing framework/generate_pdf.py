#!/usr/bin/env python3
"""
Convert Markdown documentation to PDF
"""

import subprocess
import sys
import os

def convert_markdown_to_pdf():
    """Convert COMPLETE_WORKFLOW_GUIDE.md to PDF"""
    
    input_file = "COMPLETE_WORKFLOW_GUIDE.md"
    output_file = "Automated_Visual_Testing_Workflow_Guide.pdf"
    
    print(f"Converting {input_file} to {output_file}...")
    
    try:
        # Method 1: Try using pandoc (best quality)
        result = subprocess.run(
            [
                "pandoc",
                input_file,
                "-o", output_file,
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=1in",
                "-V", "fontsize=11pt",
                "-V", "colorlinks=true",
                "--toc",
                "--toc-depth=2"
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully created {output_file}")
            print(f"📄 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
            return True
        else:
            print(f"⚠️  Pandoc failed: {result.stderr}")
            raise Exception("Pandoc conversion failed")
            
    except FileNotFoundError:
        print("❌ Pandoc not installed. Trying alternative method...")
        
        try:
            # Method 2: Try using markdown-pdf (npm package)
            result = subprocess.run(
                ["md-to-pdf", input_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Rename to our desired filename
                os.rename(input_file.replace('.md', '.pdf'), output_file)
                print(f"✅ Successfully created {output_file}")
                return True
            else:
                raise Exception("md-to-pdf failed")
                
        except FileNotFoundError:
            print("❌ md-to-pdf not installed. Trying Python method...")
            
            try:
                # Method 3: Use Python markdown + pdfkit
                import markdown
                import pdfkit
                
                # Read markdown
                with open(input_file, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # Convert to HTML
                html = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'codehilite'])
                
                # Add CSS styling
                styled_html = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            line-height: 1.6;
                            max-width: 900px;
                            margin: 0 auto;
                            padding: 40px;
                            color: #333;
                        }}
                        h1 {{
                            color: #2563eb;
                            border-bottom: 3px solid #2563eb;
                            padding-bottom: 10px;
                        }}
                        h2 {{
                            color: #1e40af;
                            margin-top: 30px;
                        }}
                        h3 {{
                            color: #3b82f6;
                        }}
                        code {{
                            background: #f1f5f9;
                            padding: 2px 6px;
                            border-radius: 3px;
                            font-family: 'Monaco', 'Courier New', monospace;
                            font-size: 0.9em;
                        }}
                        pre {{
                            background: #1e293b;
                            color: #e2e8f0;
                            padding: 15px;
                            border-radius: 5px;
                            overflow-x: auto;
                        }}
                        pre code {{
                            background: none;
                            color: inherit;
                        }}
                        table {{
                            border-collapse: collapse;
                            width: 100%;
                            margin: 20px 0;
                        }}
                        th, td {{
                            border: 1px solid #e2e8f0;
                            padding: 12px;
                            text-align: left;
                        }}
                        th {{
                            background: #f1f5f9;
                            font-weight: 600;
                        }}
                        blockquote {{
                            border-left: 4px solid #3b82f6;
                            padding-left: 20px;
                            margin-left: 0;
                            color: #64748b;
                        }}
                    </style>
                </head>
                <body>
                    {html}
                </body>
                </html>
                """
                
                # Convert to PDF
                options = {
                    'page-size': 'A4',
                    'margin-top': '20mm',
                    'margin-right': '20mm',
                    'margin-bottom': '20mm',
                    'margin-left': '20mm',
                    'encoding': 'UTF-8',
                    'enable-local-file-access': None
                }
                
                pdfkit.from_string(styled_html, output_file, options=options)
                print(f"✅ Successfully created {output_file}")
                return True
                
            except ImportError:
                print("❌ Required Python packages not installed")
                print("\nTo convert to PDF, install one of:")
                print("  1. Pandoc: brew install pandoc")
                print("  2. md-to-pdf: npm install -g md-to-pdf")
                print("  3. Python packages: pip install markdown pdfkit")
                print("\nFor now, you can:")
                print(f"  • Read the markdown file: {input_file}")
                print(f"  • Use an online converter")
                print(f"  • Install one of the tools above")
                return False

if __name__ == "__main__":
    success = convert_markdown_to_pdf()
    sys.exit(0 if success else 1)
