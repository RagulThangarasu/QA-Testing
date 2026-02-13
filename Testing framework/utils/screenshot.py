from playwright.sync_api import sync_playwright

VIEWPORTS = {
    "desktop": {"width": 1366, "height": 768},
    "mobile":  {"width": 390,  "height": 844},
}

def _parse_viewport(vp):
    if isinstance(vp, str) and "x" in vp.lower():
        try:
            w, h = vp.lower().split("x")
            return {"width": int(w), "height": int(h)}
        except Exception:
            return VIEWPORTS["desktop"]
    return VIEWPORTS.get(vp, VIEWPORTS["desktop"])

def capture_screenshot(url, out_path, viewport="desktop", fullpage=True, wait="networkidle", mask_selectors=None, wait_time=1000):
    vp = _parse_viewport(viewport)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport=vp, device_scale_factor=1)
        page = context.new_page()
        page.set_default_timeout(60000)
        
        try:
            page.goto(url, wait_until=wait, timeout=60000)
        except Exception as e:
            print(f"Navigation timeout/error: {e}")
            
        # Reduce visual noise from animations/caret
        page.add_style_tag(content="""
          * { animation: none !important; transition: none !important; caret-color: transparent !important;}
        """)
        
        # Apply masks (ignore selectors)
        if mask_selectors:
            try:
                selector_str = ", ".join([s.strip() for s in mask_selectors if s.strip()])
                if selector_str:
                    # Hide elements completely
                    page.add_style_tag(content=f"{selector_str} {{ visibility: hidden !important; opacity: 0 !important; }}")
            except Exception as e:
                print(f"Error applying masks: {e}")

        # Custom wait before screenshot
        if wait_time > 0:
            page.wait_for_timeout(wait_time)
            
        page.screenshot(path=out_path, full_page=fullpage)
        context.close()
        browser.close()
