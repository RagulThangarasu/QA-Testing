"""
HTML Semantic Validator Module
Validates HTML pages for proper semantic structure, accessibility, and best practices.
"""

import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse, urljoin
import re


def validate_html_semantics(url):
    """
    Fetch a URL and validate its HTML for semantic correctness.
    Returns a dict with score, issues list, and summary stats.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; SemanticValidator/1.0)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to fetch URL: {str(e)}",
            "url": url
        }
    
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    
    issues = []
    
    # ────────────────────────────────────────────
    # 1. DOCUMENT STRUCTURE CHECKS
    # ────────────────────────────────────────────
    issues.extend(_check_doctype(html_content))
    issues.extend(_check_html_lang(soup))
    issues.extend(_check_head_elements(soup))
    issues.extend(_check_meta_tags(soup, url))
    
    # ────────────────────────────────────────────
    # 2. HEADING HIERARCHY CHECKS
    # ────────────────────────────────────────────
    issues.extend(_check_headings(soup))
    
    # ────────────────────────────────────────────
    # 3. LANDMARK / SEMANTIC ELEMENTS
    # ────────────────────────────────────────────
    issues.extend(_check_landmark_elements(soup))
    
    # ────────────────────────────────────────────
    # 4. FORM ACCESSIBILITY
    # ────────────────────────────────────────────
    issues.extend(_check_forms(soup))
    
    # ────────────────────────────────────────────
    # 5. IMAGE / MEDIA SEMANTICS
    # ────────────────────────────────────────────
    issues.extend(_check_images(soup))
    
    # ────────────────────────────────────────────
    # 6. LINK SEMANTICS
    # ────────────────────────────────────────────
    issues.extend(_check_links(soup))
    
    # ────────────────────────────────────────────
    # 7. LIST SEMANTICS
    # ────────────────────────────────────────────
    issues.extend(_check_lists(soup))
    
    # ────────────────────────────────────────────
    # 8. TABLE SEMANTICS
    # ────────────────────────────────────────────
    issues.extend(_check_tables(soup))
    
    # ────────────────────────────────────────────
    # 9. DEPRECATED / NON-SEMANTIC ELEMENTS
    # ────────────────────────────────────────────
    issues.extend(_check_deprecated_elements(soup))
    
    # ────────────────────────────────────────────
    # 10. INLINE STYLES & PRESENTATIONAL MARKUP
    # ────────────────────────────────────────────
    issues.extend(_check_presentational_markup(soup))
    
    # ────────────────────────────────────────────
    # 11. ARIA USAGE CHECKS
    # ────────────────────────────────────────────
    issues.extend(_check_aria_usage(soup))
    
    # ────────────────────────────────────────────
    # 12. INTERACTIVE ELEMENTS
    # ────────────────────────────────────────────
    issues.extend(_check_interactive_elements(soup))
    
    # Compute score
    score = _compute_score(issues)
    
    # Group counts by severity
    critical_count = sum(1 for i in issues if i["severity"] == "critical")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    info_count = sum(1 for i in issues if i["severity"] == "info")
    
    # Group counts by category
    category_counts = {}
    for issue in issues:
        cat = issue.get("category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Build element tree summary
    element_summary = _build_element_summary(soup)
    
    # Build recommended heading structure
    recommended_headings = _build_recommended_headings(soup)
    
    return {
        "success": True,
        "url": url,
        "score": score,
        "total_issues": len(issues),
        "critical": critical_count,
        "warnings": warning_count,
        "info": info_count,
        "category_counts": category_counts,
        "issues": issues,
        "element_summary": element_summary,
        "recommended_headings": recommended_headings,
        "html_size": len(html_content),
        "status_code": response.status_code
    }


# ═══════════════════════════════════════════════
# CHECK FUNCTIONS
# ═══════════════════════════════════════════════

def _check_doctype(html_content):
    issues = []
    if not html_content.strip().lower().startswith("<!doctype html"):
        issues.append({
            "rule": "missing-doctype",
            "message": "Missing <!DOCTYPE html> declaration",
            "detail": "Every HTML5 document should start with <!DOCTYPE html> to ensure standards mode rendering.",
            "severity": "critical",
            "category": "Document Structure",
            "element": "<!DOCTYPE>",
            "wcag": "4.1.1"
        })
    return issues


def _check_html_lang(soup):
    issues = []
    html_tag = soup.find('html')
    if html_tag:
        lang = html_tag.get('lang')
        if not lang:
            issues.append({
                "rule": "missing-lang",
                "message": "Missing 'lang' attribute on <html> element",
                "detail": "The <html> element should have a 'lang' attribute (e.g., lang=\"en\") for screen readers and search engines.",
                "severity": "critical",
                "category": "Document Structure",
                "element": "<html>",
                "wcag": "3.1.1"
            })
        elif len(lang) < 2:
            issues.append({
                "rule": "invalid-lang",
                "message": f"Invalid 'lang' attribute value: '{lang}'",
                "detail": "The lang attribute should contain a valid BCP 47 language tag (e.g., 'en', 'en-US', 'fr').",
                "severity": "warning",
                "category": "Document Structure",
                "element": f'<html lang="{lang}">',
                "wcag": "3.1.1"
            })
    return issues


def _check_head_elements(soup):
    issues = []
    head = soup.find('head')
    
    if not head:
        issues.append({
            "rule": "missing-head",
            "message": "Missing <head> element",
            "detail": "The document should have a <head> section containing metadata.",
            "severity": "critical",
            "category": "Document Structure",
            "element": "<head>",
            "wcag": "—"
        })
        return issues
    
    # Check <title>
    title = head.find('title')
    if not title:
        issues.append({
            "rule": "missing-title",
            "message": "Missing <title> tag",
            "detail": "Every page must have a <title> element for accessibility and SEO.",
            "severity": "critical",
            "category": "Document Structure",
            "element": "<title>",
            "wcag": "2.4.2"
        })
    elif not title.get_text(strip=True):
        issues.append({
            "rule": "empty-title",
            "message": "Empty <title> tag",
            "detail": "The <title> element exists but contains no text.",
            "severity": "critical",
            "category": "Document Structure",
            "element": "<title></title>",
            "wcag": "2.4.2"
        })
    
    # Check charset
    charset_meta = head.find('meta', attrs={'charset': True})
    http_equiv_charset = head.find('meta', attrs={'http-equiv': lambda v: v and v.lower() == 'content-type'})
    if not charset_meta and not http_equiv_charset:
        issues.append({
            "rule": "missing-charset",
            "message": "Missing character encoding declaration",
            "detail": "Add <meta charset=\"UTF-8\"> to prevent encoding issues.",
            "severity": "warning",
            "category": "Document Structure",
            "element": '<meta charset="...">',
            "wcag": "—"
        })
    
    # Check viewport
    viewport_meta = head.find('meta', attrs={'name': 'viewport'})
    if not viewport_meta:
        issues.append({
            "rule": "missing-viewport",
            "message": "Missing viewport meta tag",
            "detail": "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> for responsive design.",
            "severity": "warning",
            "category": "Document Structure",
            "element": '<meta name="viewport">',
            "wcag": "1.4.10"
        })
    
    return issues


def _check_meta_tags(soup, url):
    issues = []
    head = soup.find('head')
    if not head:
        return issues
    
    # Meta description
    meta_desc = head.find('meta', attrs={'name': 'description'})
    if not meta_desc:
        issues.append({
            "rule": "missing-meta-description",
            "message": "Missing meta description",
            "detail": "Add <meta name=\"description\" content=\"...\"> for SEO and social sharing.",
            "severity": "info",
            "category": "SEO & Meta",
            "element": '<meta name="description">',
            "wcag": "—"
        })
    elif meta_desc.get('content', '') == '':
        issues.append({
            "rule": "empty-meta-description",
            "message": "Empty meta description",
            "detail": "The meta description exists but has no content.",
            "severity": "warning",
            "category": "SEO & Meta",
            "element": '<meta name="description" content="">',
            "wcag": "—"
        })
    
    # Open Graph tags
    og_title = head.find('meta', attrs={'property': 'og:title'})
    og_desc = head.find('meta', attrs={'property': 'og:description'})
    if not og_title and not og_desc:
        issues.append({
            "rule": "missing-og-tags",
            "message": "Missing Open Graph meta tags",
            "detail": "Add og:title and og:description for better social media previews.",
            "severity": "info",
            "category": "SEO & Meta",
            "element": '<meta property="og:title">',
            "wcag": "—"
        })
    
    # Canonical URL
    canonical = head.find('link', attrs={'rel': 'canonical'})
    if not canonical:
        issues.append({
            "rule": "missing-canonical",
            "message": "Missing canonical URL",
            "detail": "Add <link rel=\"canonical\" href=\"...\"> to prevent duplicate content issues.",
            "severity": "info",
            "category": "SEO & Meta",
            "element": '<link rel="canonical">',
            "wcag": "—"
        })
    
    return issues


def _check_headings(soup):
    issues = []
    headings = soup.find_all(re.compile(r'^h[1-6]$'))
    
    if not headings:
        issues.append({
            "rule": "no-headings",
            "message": "No heading elements found",
            "detail": "The page has no <h1>–<h6> elements. Headings provide document outline and navigation for screen readers. Recommended: Add at least one <h1> for the page title and <h2> for major sections.",
            "severity": "critical",
            "category": "Heading Hierarchy",
            "element": "h1–h6",
            "wcag": "1.3.1"
        })
        return issues
    
    # Check for H1
    h1_tags = soup.find_all('h1')
    if len(h1_tags) == 0:
        issues.append({
            "rule": "missing-h1",
            "message": "No <h1> heading found",
            "detail": "Every page should have exactly one <h1> as the main page heading. Recommended: Add an <h1> element as the first heading on the page.",
            "severity": "critical",
            "category": "Heading Hierarchy",
            "element": "<h1>",
            "wcag": "1.3.1"
        })
    elif len(h1_tags) > 1:
        h1_texts = [h.get_text(strip=True)[:60] for h in h1_tags]
        h1_list = ', '.join([f'"{t}"' for t in h1_texts])
        issues.append({
            "rule": "multiple-h1",
            "message": f"Multiple <h1> headings found ({len(h1_tags)}): {h1_list}",
            "detail": f"There should be only one <h1> per page. Found: {h1_list}. Recommended: Keep one <h1> and change the others to <h2>.",
            "severity": "warning",
            "category": "Heading Hierarchy",
            "element": f"<h1> × {len(h1_tags)}",
            "wcag": "1.3.1"
        })
    
    # Check empty headings
    for h in headings:
        text = h.get_text(strip=True)
        if not text and not h.find('img'):
            issues.append({
                "rule": "empty-heading",
                "message": f"Empty <{h.name}> heading",
                "detail": "Headings should not be empty. Screen readers announce heading levels but empty ones cause confusion. Recommended: Add descriptive text or remove the empty heading.",
                "severity": "warning",
                "category": "Heading Hierarchy",
                "element": f"<{h.name}></{h.name}>",
                "wcag": "1.3.1"
            })
    
    # Check heading level skip
    levels = [int(h.name[1]) for h in headings]
    texts = [h.get_text(strip=True)[:80] for h in headings]
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            prev_text = texts[i - 1] if texts[i - 1] else '(empty)'
            curr_text = texts[i] if texts[i] else '(empty)'
            recommended_level = levels[i - 1] + 1
            issues.append({
                "rule": "skipped-heading-level",
                "message": f"Heading level skipped: <h{levels[i-1]}> \"{prev_text}\" → <h{levels[i]}> \"{curr_text}\"",
                "detail": f"Heading levels should not skip. Found <h{levels[i]}> \"{curr_text}\" after <h{levels[i-1]}> \"{prev_text}\". Recommended: Change <h{levels[i]}> to <h{recommended_level}> to maintain proper hierarchy.",
                "severity": "warning",
                "category": "Heading Hierarchy",
                "element": f"<h{levels[i-1]}> → <h{levels[i]}>",
                "wcag": "1.3.1"
            })
    
    # Check if first heading is h1
    if levels and levels[0] != 1:
        first_text = headings[0].get_text(strip=True)[:60]
        issues.append({
            "rule": "first-heading-not-h1",
            "message": f"First heading is <h{levels[0]}> \"{first_text}\", not <h1>",
            "detail": f"The first heading on the page should be an <h1> to define the page's main topic. Found <h{levels[0]}> \"{first_text}\" instead. Recommended: Change <h{levels[0]}> to <h1> or add an <h1> before it.",
            "severity": "warning",
            "category": "Heading Hierarchy",
            "element": f"<h{levels[0]}>",
            "wcag": "1.3.1"
        })
    
    return issues


def _check_landmark_elements(soup):
    issues = []
    
    landmarks = {
        'header': {'tag': 'header', 'desc': 'site header/banner'},
        'nav': {'tag': 'nav', 'desc': 'navigation'},
        'main': {'tag': 'main', 'desc': 'main content'},
        'footer': {'tag': 'footer', 'desc': 'footer/content info'},
    }
    
    for key, info in landmarks.items():
        element = soup.find(info['tag'])
        if not element:
            severity = "critical" if key == "main" else "warning"
            issues.append({
                "rule": f"missing-{key}",
                "message": f"Missing <{info['tag']}> landmark element",
                "detail": f"Use the <{info['tag']}> element to define the {info['desc']} region of the page.",
                "severity": severity,
                "category": "Semantic Landmarks",
                "element": f"<{info['tag']}>",
                "wcag": "1.3.1"
            })
    
    # Check for multiple <main> elements
    main_tags = soup.find_all('main')
    if len(main_tags) > 1:
        issues.append({
            "rule": "multiple-main",
            "message": f"Multiple <main> elements found ({len(main_tags)})",
            "detail": "There should be only one visible <main> element per page.",
            "severity": "warning",
            "category": "Semantic Landmarks",
            "element": f"<main> × {len(main_tags)}",
            "wcag": "1.3.1"
        })
    
    # Check for <section> without headings
    sections = soup.find_all('section')
    for section in sections:
        heading = section.find(re.compile(r'^h[1-6]$'))
        if not heading:
            # Only flag if section has significant content
            text_content = section.get_text(strip=True)
            if len(text_content) > 50:
                issues.append({
                    "rule": "section-without-heading",
                    "message": "A <section> element lacks a heading",
                    "detail": "Each <section> should have a heading (h2–h6) that describes its content.",
                    "severity": "info",
                    "category": "Semantic Landmarks",
                    "element": "<section> (no heading)",
                    "wcag": "1.3.1"
                })
                break  # Only report once to avoid noise
    
    # Check for <article> usage
    articles = soup.find_all('article')
    for article in articles:
        heading = article.find(re.compile(r'^h[1-6]$'))
        if not heading:
            text_content = article.get_text(strip=True)
            if len(text_content) > 50:
                issues.append({
                    "rule": "article-without-heading",
                    "message": "An <article> element lacks a heading",
                    "detail": "Each <article> should have a heading to describe its content.",
                    "severity": "info",
                    "category": "Semantic Landmarks",
                    "element": "<article> (no heading)",
                    "wcag": "1.3.1"
                })
                break
    
    return issues


def _check_forms(soup):
    issues = []
    
    forms = soup.find_all('form')
    inputs = soup.find_all(['input', 'select', 'textarea'])
    
    # Check inputs without labels
    for inp in inputs:
        inp_type = inp.get('type', 'text').lower()
        if inp_type in ('hidden', 'submit', 'button', 'reset', 'image'):
            continue
        
        inp_id = inp.get('id')
        inp_name = inp.get('name', '')
        has_label = False
        
        # Check for associated <label>
        if inp_id:
            label = soup.find('label', attrs={'for': inp_id})
            if label:
                has_label = True
        
        # Check for wrapping <label>
        if not has_label:
            parent = inp.find_parent('label')
            if parent:
                has_label = True
        
        # Check for aria-label or aria-labelledby
        if not has_label:
            if inp.get('aria-label') or inp.get('aria-labelledby'):
                has_label = True
        
        # Check for a title attribute (less preferred but valid)
        if not has_label and inp.get('title'):
            has_label = True
        
        if not has_label:
            element_desc = f'<{inp.name} type="{inp_type}"'
            if inp_name:
                element_desc += f' name="{inp_name}"'
            element_desc += '>'
            issues.append({
                "rule": "input-without-label",
                "message": f"Form input without label: {element_desc}",
                "detail": "Every form input should have an associated <label>, aria-label, or aria-labelledby.",
                "severity": "critical",
                "category": "Form Accessibility",
                "element": element_desc,
                "wcag": "1.3.1"
            })
    
    # Check buttons without accessible names
    buttons = soup.find_all('button')
    for btn in buttons:
        text = btn.get_text(strip=True)
        if not text and not btn.get('aria-label') and not btn.get('aria-labelledby') and not btn.get('title'):
            # Check if button has an image with alt
            img = btn.find('img')
            if not img or not img.get('alt'):
                issues.append({
                    "rule": "button-no-name",
                    "message": "Button without accessible name",
                    "detail": "Buttons must have visible text, aria-label, or aria-labelledby for screen readers.",
                    "severity": "critical",
                    "category": "Form Accessibility",
                    "element": str(btn)[:100],
                    "wcag": "4.1.2"
                })
    
    # Check for form action
    for form in forms:
        if not form.get('action') and not form.get('id'):
            issues.append({
                "rule": "form-no-action",
                "message": "Form without action attribute or id",
                "detail": "Forms should have an 'action' attribute or be identifiable with an 'id'.",
                "severity": "info",
                "category": "Form Accessibility",
                "element": "<form>",
                "wcag": "—"
            })
    
    return issues


def _check_images(soup):
    issues = []
    
    images = soup.find_all('img')
    for img in images:
        src = img.get('src', '')
        alt = img.get('alt')
        
        if alt is None:
            # Missing alt entirely
            issues.append({
                "rule": "img-missing-alt",
                "message": f"Image missing alt attribute",
                "detail": f"Image '{src[:80]}' has no alt attribute. All images must have alt (use alt=\"\" for decorative images).",
                "severity": "critical",
                "category": "Media & Images",
                "element": f'<img src="{src[:60]}">',
                "wcag": "1.1.1"
            })
        elif alt.strip() == '' and not img.get('role') == 'presentation':
            # Empty alt without role=presentation — could be ok for decorative
            pass  # Not an issue if used correctly
        
        # Check for redundant alt like "image", "photo", "picture"
        if alt and alt.strip().lower() in ('image', 'photo', 'picture', 'img', 'icon', 'graphic', 'image.png', 'image.jpg', 'untitled'):
            issues.append({
                "rule": "img-redundant-alt",
                "message": f"Image has non-descriptive alt text: \"{alt}\"",
                "detail": "Alt text should describe the image content, not just say 'image' or 'photo'.",
                "severity": "warning",
                "category": "Media & Images",
                "element": f'<img alt="{alt}">',
                "wcag": "1.1.1"
            })
    
    # Check <figure> and <figcaption>
    figures = soup.find_all('figure')
    for figure in figures:
        caption = figure.find('figcaption')
        if not caption:
            issues.append({
                "rule": "figure-no-figcaption",
                "message": "A <figure> element has no <figcaption>",
                "detail": "Use <figcaption> inside <figure> to provide a caption for the content.",
                "severity": "info",
                "category": "Media & Images",
                "element": "<figure> (no <figcaption>)",
                "wcag": "1.1.1"
            })
            break  # Only flag once
    
    # Check <video> / <audio> without captions / track
    videos = soup.find_all('video')
    for video in videos:
        track = video.find('track')
        if not track:
            issues.append({
                "rule": "video-no-captions",
                "message": "Video element without caption track",
                "detail": "Add <track kind=\"captions\"> inside <video> for hearing accessibility.",
                "severity": "warning",
                "category": "Media & Images",
                "element": "<video>",
                "wcag": "1.2.2"
            })
    
    audios = soup.find_all('audio')
    for audio in audios:
        # Check for transcript nearby
        issues.append({
            "rule": "audio-check-transcript",
            "message": "Audio element detected — verify transcript availability",
            "detail": "Ensure a text transcript is available near the audio content.",
            "severity": "info",
            "category": "Media & Images",
            "element": "<audio>",
            "wcag": "1.2.1"
        })
        break  # Only flag once
    
    return issues


def _check_links(soup):
    issues = []
    
    links = soup.find_all('a')
    generic_texts = {'click here', 'here', 'read more', 'more', 'link', 'learn more', 'click', 'this'}
    
    for link in links:
        text = link.get_text(strip=True).lower()
        href = link.get('href', '')
        
        # Non-descriptive link text
        if text in generic_texts:
            issues.append({
                "rule": "generic-link-text",
                "message": f"Non-descriptive link text: \"{link.get_text(strip=True)}\"",
                "detail": "Use meaningful link text that describes the destination. Avoid 'click here' or 'read more'.",
                "severity": "warning",
                "category": "Link Semantics",
                "element": f'<a href="{href[:60]}">{link.get_text(strip=True)}</a>',
                "wcag": "2.4.4"
            })
        
        # Empty links
        if not text and not link.find('img') and not link.get('aria-label'):
            if href and href != '#':
                issues.append({
                    "rule": "empty-link",
                    "message": "Link with no accessible text",
                    "detail": "Links must have visible text, an image with alt, or aria-label.",
                    "severity": "critical",
                    "category": "Link Semantics",
                    "element": f'<a href="{href[:60]}"></a>',
                    "wcag": "2.4.4"
                })
        
        # Links with href="#" (JavaScript-dependent)
        if href == '#' or href == 'javascript:void(0)' or href.startswith('javascript:'):
            if not link.get('role') == 'button':
                issues.append({
                    "rule": "link-href-hash",
                    "message": "Link used as interactive element (href=\"#\" or javascript:)",
                    "detail": "Use <button> instead of <a> for interactive actions. If it navigates, use a real href.",
                    "severity": "info",
                    "category": "Link Semantics",
                    "element": f'<a href="{href}">{link.get_text(strip=True)[:40]}</a>',
                    "wcag": "—"
                })
    
    # Check for target="_blank" without rel="noopener"
    external_links = soup.find_all('a', attrs={'target': '_blank'})
    for link in external_links:
        rel = link.get('rel', [])
        if isinstance(rel, str):
            rel = [rel]
        if 'noopener' not in rel and 'noreferrer' not in rel:
            issues.append({
                "rule": "link-no-noopener",
                "message": "External link (target=\"_blank\") without rel=\"noopener\"",
                "detail": "Add rel=\"noopener noreferrer\" to links with target=\"_blank\" for security.",
                "severity": "info",
                "category": "Link Semantics",
                "element": f'<a target="_blank" href="{link.get("href", "")[:50]}">',
                "wcag": "—"
            })
            break  # Only flag once
    
    return issues


def _check_lists(soup):
    issues = []
    
    # Check for <li> not inside <ul>, <ol>, or <menu>
    list_items = soup.find_all('li')
    for li in list_items:
        parent = li.find_parent(['ul', 'ol', 'menu'])
        if not parent:
            issues.append({
                "rule": "li-outside-list",
                "message": "<li> element found outside of <ul>, <ol>, or <menu>",
                "detail": "List items must be wrapped in a proper list container.",
                "severity": "warning",
                "category": "List Semantics",
                "element": f'<li>{li.get_text(strip=True)[:40]}...</li>',
                "wcag": "1.3.1"
            })
            break  # Only flag once
    
    # Check for <dt>/<dd> outside <dl>
    dts = soup.find_all('dt')
    for dt in dts:
        parent = dt.find_parent('dl')
        if not parent:
            issues.append({
                "rule": "dt-outside-dl",
                "message": "<dt> element found outside of <dl>",
                "detail": "Definition terms must be inside a <dl> (definition list).",
                "severity": "warning",
                "category": "List Semantics",
                "element": "<dt> outside <dl>",
                "wcag": "1.3.1"
            })
            break
    
    return issues


def _check_tables(soup):
    issues = []
    
    tables = soup.find_all('table')
    for table in tables:
        # Check for <caption>
        caption = table.find('caption')
        if not caption:
            # Check for aria-label or aria-labelledby
            if not table.get('aria-label') and not table.get('aria-labelledby'):
                issues.append({
                    "rule": "table-no-caption",
                    "message": "Data table without caption or aria-label",
                    "detail": "Use <caption> or aria-label to describe the table's purpose.",
                    "severity": "info",
                    "category": "Table Semantics",
                    "element": "<table>",
                    "wcag": "1.3.1"
                })
        
        # Check for <thead>/<th>
        headers = table.find_all('th')
        if not headers:
            # Check if the table has data rows (not just used for layout)
            rows = table.find_all('tr')
            if len(rows) > 1:
                issues.append({
                    "rule": "table-no-headers",
                    "message": "Data table without <th> header cells",
                    "detail": "Use <th> elements to define table headers for accessibility.",
                    "severity": "warning",
                    "category": "Table Semantics",
                    "element": "<table> (no <th>)",
                    "wcag": "1.3.1"
                })
        
        # Check for scope attribute on <th>
        for th in headers:
            if not th.get('scope') and not th.get('id'):
                issues.append({
                    "rule": "th-no-scope",
                    "message": "<th> without scope attribute",
                    "detail": "Add scope=\"col\" or scope=\"row\" to <th> elements for proper header association.",
                    "severity": "info",
                    "category": "Table Semantics",
                    "element": f'<th>{th.get_text(strip=True)[:30]}</th>',
                    "wcag": "1.3.1"
                })
                break  # Only flag once
    
    return issues


def _check_deprecated_elements(soup):
    issues = []
    
    deprecated_tags = {
        'center': 'Use CSS text-align: center instead.',
        'font': 'Use CSS for font styling.',
        'b': 'Consider using <strong> for importance or CSS for visual bold.',
        'i': 'Consider using <em> for emphasis or CSS for visual italics.',
        'u': 'Consider using CSS text-decoration: underline instead.',
        'strike': 'Use <del> for deleted text or CSS for visual strikethrough.',
        's': 'Use <del> for deleted text or CSS.',
        'marquee': 'Use CSS animation instead. Marquees cause accessibility issues.',
        'blink': 'Remove blinking content. It fails WCAG 2.2.2.',
        'big': 'Use CSS font-size instead.',
        'small': 'Consider if <small> is semantically appropriate (legal text, etc).',
        'tt': 'Use <code> or <kbd> for monospace text.',
        'frame': 'Use <iframe> or remove frames entirely.',
        'frameset': 'Use modern layout techniques instead.',
    }
    
    for tag, recommendation in deprecated_tags.items():
        elements = soup.find_all(tag)
        if elements:
            count = len(elements)
            severity = "warning"
            if tag in ('marquee', 'blink', 'frame', 'frameset'):
                severity = "critical"
            if tag in ('b', 'i', 'small'):
                severity = "info"  # These are valid in HTML5 but worth noting
            
            issues.append({
                "rule": f"deprecated-{tag}",
                "message": f"Non-semantic <{tag}> element found ({count} instance{'s' if count > 1 else ''})",
                "detail": recommendation,
                "severity": severity,
                "category": "Deprecated / Non-Semantic",
                "element": f"<{tag}> × {count}",
                "wcag": "—"
            })
    
    return issues


def _check_presentational_markup(soup):
    issues = []
    
    # Check excessive inline styles
    elements_with_style = soup.find_all(attrs={'style': True})
    if len(elements_with_style) > 20:
        issues.append({
            "rule": "excessive-inline-styles",
            "message": f"Excessive inline styles detected ({len(elements_with_style)} elements)",
            "detail": "Move styles to external CSS for better maintainability and separation of concerns.",
            "severity": "info",
            "category": "Code Quality",
            "element": f"style=\"...\" × {len(elements_with_style)}",
            "wcag": "—"
        })
    
    # Check for <div> soup (too many nested divs without semantic meaning)
    divs = soup.find_all('div')
    semantic_elements = soup.find_all(['header', 'nav', 'main', 'footer', 'section', 'article', 'aside'])
    
    if len(divs) > 30 and len(semantic_elements) < 3:
        issues.append({
            "rule": "div-soup",
            "message": f"Potential 'div soup' — {len(divs)} <div>s but only {len(semantic_elements)} semantic elements",
            "detail": "Replace generic <div> elements with semantic HTML5 elements (header, nav, main, section, article, aside, footer).",
            "severity": "warning",
            "category": "Code Quality",
            "element": f"<div> × {len(divs)}",
            "wcag": "1.3.1"
        })
    
    return issues


def _check_aria_usage(soup):
    issues = []
    
    # Check for role="button" without keyboard support (can't fully check from HTML alone, but flag it)
    role_buttons = soup.find_all(attrs={'role': 'button'})
    for el in role_buttons:
        if el.name not in ('button', 'a', 'input'):
            if not el.get('tabindex'):
                issues.append({
                    "rule": "role-button-no-tabindex",
                    "message": f"Non-interactive element with role=\"button\" lacks tabindex",
                    "detail": f"<{el.name} role=\"button\"> should have tabindex=\"0\" for keyboard access. Consider using <button> instead.",
                    "severity": "warning",
                    "category": "ARIA Usage",
                    "element": f'<{el.name} role="button">',
                    "wcag": "4.1.2"
                })
                break
    
    # Check for aria-hidden="true" on focusable elements
    aria_hidden = soup.find_all(attrs={'aria-hidden': 'true'})
    for el in aria_hidden:
        if el.name in ('a', 'button', 'input', 'select', 'textarea'):
            issues.append({
                "rule": "aria-hidden-focusable",
                "message": f"Focusable <{el.name}> element has aria-hidden=\"true\"",
                "detail": "This hides the element from screen readers but it remains focusable. Remove aria-hidden or make it non-focusable.",
                "severity": "critical",
                "category": "ARIA Usage",
                "element": f'<{el.name} aria-hidden="true">',
                "wcag": "4.1.2"
            })
            break
    
    return issues


def _check_interactive_elements(soup):
    issues = []
    
    # Check for tabindex > 0 (positive tabindex is almost always wrong)
    positive_tabindex = soup.find_all(attrs={'tabindex': lambda v: v and str(v).isdigit() and int(v) > 0})
    if positive_tabindex:
        issues.append({
            "rule": "positive-tabindex",
            "message": f"Positive tabindex value found ({len(positive_tabindex)} element(s))",
            "detail": "Avoid tabindex > 0. It disrupts the natural tab order. Use tabindex=\"0\" or tabindex=\"-1\" instead.",
            "severity": "warning",
            "category": "Interactive Elements",
            "element": f"tabindex > 0 × {len(positive_tabindex)}",
            "wcag": "2.4.3"
        })
    
    # Check for autoplaying media
    autoplay_videos = soup.find_all('video', attrs={'autoplay': True})
    autoplay_audios = soup.find_all('audio', attrs={'autoplay': True})
    if autoplay_videos or autoplay_audios:
        count = len(autoplay_videos) + len(autoplay_audios)
        issues.append({
            "rule": "autoplay-media",
            "message": f"Auto-playing media detected ({count} element(s))",
            "detail": "Auto-playing media can be disorienting. Ensure users can pause/stop it. WCAG 1.4.2 requires audio control.",
            "severity": "warning",
            "category": "Interactive Elements",
            "element": "<video autoplay> / <audio autoplay>",
            "wcag": "1.4.2"
        })
    
    # Check for onclick on non-interactive elements
    onclick_elements = soup.find_all(attrs={'onclick': True})
    for el in onclick_elements:
        if el.name not in ('a', 'button', 'input', 'select', 'textarea', 'summary', 'details'):
            if not el.get('role') and not el.get('tabindex'):
                issues.append({
                    "rule": "onclick-non-interactive",
                    "message": f"onclick on non-interactive <{el.name}> element",
                    "detail": f"<{el.name}> with onclick but no role or tabindex. Use <button> or add role=\"button\" and tabindex=\"0\".",
                    "severity": "warning",
                    "category": "Interactive Elements",
                    "element": f'<{el.name} onclick="...">',
                    "wcag": "4.1.2"
                })
                break
    
    return issues


# ═══════════════════════════════════════════════
# SCORE COMPUTATION
# ═══════════════════════════════════════════════

def _compute_score(issues):
    """
    Compute a 0-100 score based on issue severity.
    Start at 100, deduct points per issue.
    """
    score = 100.0
    for issue in issues:
        severity = issue.get("severity", "info")
        if severity == "critical":
            score -= 8
        elif severity == "warning":
            score -= 3
        elif severity == "info":
            score -= 1
    
    return max(0, round(score))


# ═══════════════════════════════════════════════
# ELEMENT SUMMARY
# ═══════════════════════════════════════════════

def _build_element_summary(soup):
    """
    Build a summary of semantic elements used on the page.
    """
    semantic_tags = [
        'header', 'nav', 'main', 'footer', 'section', 'article', 'aside',
        'figure', 'figcaption', 'details', 'summary', 'dialog', 'mark',
        'time', 'address', 'abbr', 'cite', 'blockquote', 'code', 'pre',
        'strong', 'em', 'small', 'sub', 'sup', 'del', 'ins'
    ]
    
    structural_tags = ['div', 'span', 'p', 'br', 'hr']
    
    summary = {
        "semantic_elements": {},
        "structural_elements": {},
        "headings": {},
        "total_elements": len(soup.find_all(True)),
    }
    
    for tag in semantic_tags:
        count = len(soup.find_all(tag))
        if count > 0:
            summary["semantic_elements"][tag] = count
    
    for tag in structural_tags:
        count = len(soup.find_all(tag))
        if count > 0:
            summary["structural_elements"][tag] = count
    
    for i in range(1, 7):
        count = len(soup.find_all(f'h{i}'))
        if count > 0:
            summary["headings"][f'h{i}'] = count
    
    # Semantic ratio
    semantic_count = sum(summary["semantic_elements"].values())
    total = summary["total_elements"]
    summary["semantic_ratio"] = round((semantic_count / total) * 100, 1) if total > 0 else 0
    
    return summary


def _build_recommended_headings(soup):
    """
    Analyze the page and produce:
      1. The current heading outline (what IS on the page)
      2. A recommended heading structure (what SHOULD be on the page)
    """
    # ── Current heading outline ──
    current_outline = []
    headings = soup.find_all(re.compile(r'^h[1-6]$'))
    for h in headings:
        text = h.get_text(strip=True)
        if text:
            current_outline.append({
                "level": int(h.name[1]),
                "tag": h.name,
                "text": text[:120]
            })

    # ── Recommended heading structure ──
    recommended = []
    
    # The page title → h1
    title_tag = soup.find('title')
    h1 = soup.find('h1')
    page_title = ""
    if h1:
        page_title = h1.get_text(strip=True)[:100]
    elif title_tag:
        page_title = title_tag.get_text(strip=True)[:100]
    else:
        page_title = "Page Title"
    
    recommended.append({
        "level": 1,
        "tag": "h1",
        "text": page_title,
        "reason": "Main page heading — one per page"
    })

    # Analyze content sections to suggest h2/h3 structure
    def _get_region_label(el, fallback):
        """Try to extract a label from a region element."""
        # Check for aria-label
        aria = el.get('aria-label')
        if aria:
            return aria.strip()[:80]
        # Check for aria-labelledby
        labelledby = el.get('aria-labelledby')
        if labelledby:
            ref = soup.find(id=labelledby)
            if ref:
                return ref.get_text(strip=True)[:80]
        # Check for a direct child heading
        child_heading = el.find(re.compile(r'^h[1-6]$'), recursive=False)
        if not child_heading:
            child_heading = el.find(re.compile(r'^h[1-6]$'))
        if child_heading:
            return child_heading.get_text(strip=True)[:80]
        return fallback

    # Header region → h2 Navigation / Branding
    header = soup.find('header')
    if header:
        label = _get_region_label(header, "Site Header")
        nav_in_header = header.find('nav')
        if nav_in_header:
            recommended.append({
                "level": 2,
                "tag": "h2",
                "text": "Navigation",
                "reason": "<header> with <nav> — primary navigation area"
            })

    # Standalone <nav> outside header
    navs = soup.find_all('nav')
    standalone_navs = [n for n in navs if not n.find_parent('header')]
    for nav in standalone_navs[:2]:
        label = _get_region_label(nav, "Navigation")
        recommended.append({
            "level": 2,
            "tag": "h2",
            "text": label,
            "reason": "Standalone <nav> element"
        })

    # <main> content
    main = soup.find('main')
    content_root = main if main else soup.find('body')
    
    if content_root:
        # Sections within main → h2 per section
        sections = content_root.find_all('section', recursive=False)
        if not sections:
            sections = content_root.find_all('section')
        
        for section in sections[:10]:
            label = _get_region_label(section, "Content Section")
            recommended.append({
                "level": 2,
                "tag": "h2",
                "text": label,
                "reason": "<section> — thematic grouping of content"
            })
            # Sub-articles within section → h3
            sub_articles = section.find_all('article', recursive=False)
            for art in sub_articles[:3]:
                art_label = _get_region_label(art, "Article")
                recommended.append({
                    "level": 3,
                    "tag": "h3",
                    "text": art_label,
                    "reason": "<article> inside <section>"
                })
        
        # Top-level articles not inside sections → h2
        articles = content_root.find_all('article', recursive=False)
        for article in articles[:5]:
            label = _get_region_label(article, "Article")
            recommended.append({
                "level": 2,
                "tag": "h2",
                "text": label,
                "reason": "<article> — self-contained content"
            })

    # <aside> → h2 sidebar
    asides = soup.find_all('aside')
    for aside in asides[:2]:
        label = _get_region_label(aside, "Sidebar")
        recommended.append({
            "level": 2,
            "tag": "h2",
            "text": label,
            "reason": "<aside> — complementary content"
        })

    # Forms → h2 if prominent
    forms = soup.find_all('form')
    for form in forms[:3]:
        label = _get_region_label(form, None)
        if label:
            recommended.append({
                "level": 2,
                "tag": "h2",
                "text": label,
                "reason": "<form> — interactive form region"
            })

    # Footer → h2
    footer = soup.find('footer')
    if footer:
        label = _get_region_label(footer, "Footer")
        recommended.append({
            "level": 2,
            "tag": "h2",
            "text": label,
            "reason": "<footer> — site footer content"
        })

    # If we have very few recommendations (simple page), suggest minimal structure
    if len(recommended) == 1:
        recommended.append({
            "level": 2,
            "tag": "h2",
            "text": "Main Content",
            "reason": "Primary content area"
        })
        recommended.append({
            "level": 2,
            "tag": "h2",
            "text": "Additional Information",
            "reason": "Supporting content or footer"
        })

    return {
        "current_outline": current_outline,
        "recommended": recommended
    }
