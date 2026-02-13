"""
Background validation utility for visual testing
Validates background colors and background images between Figma and Stage
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


def extract_background_info(url):
    """
    Extract background color and background image information from a webpage
    
    Args:
        url: URL of the webpage to analyze
    
    Returns:
        Dictionary containing background information for major elements
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        backgrounds = []
        
        # Find all elements with inline styles or classes
        elements = soup.find_all(['div', 'section', 'header', 'footer', 'main', 'article', 'aside', 'nav'])
        
        for elem in elements:
            elem_info = {}
            
            # Get element identifier
            elem_id = elem.get('id', '')
            elem_class = ' '.join(elem.get('class', []))
            elem_tag = elem.name
            
            # Create a selector for this element
            if elem_id:
                selector = f"{elem_tag}#{elem_id}"
            elif elem_class:
                selector = f"{elem_tag}.{elem_class.split()[0]}"
            else:
                selector = elem_tag
            
            # Check inline styles
            style = elem.get('style', '')
            if style:
                # Extract background-color
                bg_color_match = re.search(r'background-color\s*:\s*([^;]+)', style, re.IGNORECASE)
                if bg_color_match:
                    elem_info['background_color'] = bg_color_match.group(1).strip()
                
                # Extract background-image
                bg_image_match = re.search(r'background-image\s*:\s*url\(["\']?([^"\']+)["\']?\)', style, re.IGNORECASE)
                if bg_image_match:
                    bg_url = bg_image_match.group(1).strip()
                    elem_info['background_image'] = urljoin(url, bg_url)
                
                # Extract background shorthand
                bg_match = re.search(r'background\s*:\s*([^;]+)', style, re.IGNORECASE)
                if bg_match and 'background_color' not in elem_info:
                    bg_value = bg_match.group(1).strip()
                    # Try to extract color from background shorthand
                    color_pattern = r'(#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)|[a-z]+)'
                    color_match = re.search(color_pattern, bg_value)
                    if color_match:
                        elem_info['background_color'] = color_match.group(1)
                    
                    # Try to extract image URL
                    if 'url(' in bg_value:
                        url_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', bg_value)
                        if url_match:
                            bg_url = url_match.group(1).strip()
                            elem_info['background_image'] = urljoin(url, bg_url)
            
            # Only add if we found background information
            if elem_info:
                elem_info['selector'] = selector
                elem_info['element'] = elem_tag
                backgrounds.append(elem_info)
        
        return backgrounds
    
    except Exception as e:
        raise Exception(f"Failed to extract background info: {str(e)}")


def normalize_color(color_str):
    """
    Normalize color strings for comparison
    Converts rgb(), rgba(), hex, and named colors to a standard format
    """
    if not color_str:
        return None
    
    color_str = color_str.strip().lower()
    
    # Named colors to hex mapping (common ones)
    named_colors = {
        'white': '#ffffff',
        'black': '#000000',
        'red': '#ff0000',
        'green': '#008000',
        'blue': '#0000ff',
        'yellow': '#ffff00',
        'gray': '#808080',
        'grey': '#808080',
        'transparent': 'transparent'
    }
    
    if color_str in named_colors:
        return named_colors[color_str]
    
    # RGB/RGBA to hex
    rgb_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', color_str)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # Hex color (normalize to 6 digits)
    hex_match = re.match(r'#([0-9a-f]{3,6})', color_str)
    if hex_match:
        hex_val = hex_match.group(1)
        if len(hex_val) == 3:
            # Expand shorthand hex
            return f'#{hex_val[0]}{hex_val[0]}{hex_val[1]}{hex_val[1]}{hex_val[2]}{hex_val[2]}'
        return f'#{hex_val}'
    
    return color_str


def compare_backgrounds(figma_url, stage_url):
    """
    Compare background colors and images between Figma and Stage URLs
    
    Args:
        figma_url: URL of the Figma/reference page
        stage_url: URL of the staging/test page
    
    Returns:
        Dictionary containing comparison results and issues
    """
    figma_backgrounds = extract_background_info(figma_url)
    stage_backgrounds = extract_background_info(stage_url)
    
    issues = []
    matches = 0
    total_checked = 0
    
    # Create a map of stage backgrounds by selector
    stage_map = {bg['selector']: bg for bg in stage_backgrounds}
    
    for figma_bg in figma_backgrounds:
        selector = figma_bg['selector']
        
        if selector not in stage_map:
            # Element exists in Figma but not in Stage
            issues.append({
                'type': 'missing_element',
                'severity': 'warning',
                'selector': selector,
                'description': f"Element '{selector}' found in reference but not in stage",
                'figma_value': figma_bg,
                'stage_value': None
            })
            total_checked += 1
            continue
        
        stage_bg = stage_map[selector]
        
        # Compare background colors
        if 'background_color' in figma_bg or 'background_color' in stage_bg:
            total_checked += 1
            figma_color = normalize_color(figma_bg.get('background_color'))
            stage_color = normalize_color(stage_bg.get('background_color'))
            
            if figma_color != stage_color:
                issues.append({
                    'type': 'background_color_mismatch',
                    'severity': 'violation',
                    'selector': selector,
                    'description': f"Background color mismatch on '{selector}'",
                    'figma_value': figma_bg.get('background_color', 'none'),
                    'stage_value': stage_bg.get('background_color', 'none'),
                    'expected': figma_color,
                    'actual': stage_color
                })
            else:
                matches += 1
        
        # Compare background images
        if 'background_image' in figma_bg or 'background_image' in stage_bg:
            total_checked += 1
            figma_img = figma_bg.get('background_image')
            stage_img = stage_bg.get('background_image')
            
            if figma_img != stage_img:
                # Extract just the filename for comparison
                figma_filename = figma_img.split('/')[-1] if figma_img else 'none'
                stage_filename = stage_img.split('/')[-1] if stage_img else 'none'
                
                if figma_filename != stage_filename:
                    issues.append({
                        'type': 'background_image_mismatch',
                        'severity': 'violation',
                        'selector': selector,
                        'description': f"Background image mismatch on '{selector}'",
                        'figma_value': figma_filename,
                        'stage_value': stage_filename,
                        'figma_url': figma_img,
                        'stage_url': stage_img
                    })
                else:
                    matches += 1
            else:
                matches += 1
    
    # Calculate match percentage
    match_percentage = (matches / total_checked * 100) if total_checked > 0 else 100
    
    return {
        'total_elements_checked': total_checked,
        'matches': matches,
        'mismatches': len(issues),
        'match_percentage': round(match_percentage, 2),
        'issues': issues
    }
