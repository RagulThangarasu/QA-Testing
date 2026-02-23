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

def capture_screenshot(url, out_path, viewport="desktop", fullpage=True, wait="networkidle", mask_selectors=None, wait_time=1000, selector=None, remove_selectors=None, max_height=None):
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
        
        # ─── ENSURE ALL IMAGES & ICONS LOAD ───────────────────────
        # Step 1: Scroll entire page to trigger lazy-loaded images
        if fullpage:
            try:
                page.evaluate("""
                    async () => {
                        const delay = ms => new Promise(r => setTimeout(r, ms));
                        const scrollHeight = document.body.scrollHeight;
                        const viewportHeight = window.innerHeight;
                        let currentPos = 0;
                        
                        // Scroll down in steps to trigger lazy loading
                        while (currentPos < scrollHeight) {
                            window.scrollTo(0, currentPos);
                            currentPos += viewportHeight;
                            await delay(150);
                        }
                        // Scroll to very bottom
                        window.scrollTo(0, scrollHeight);
                        await delay(300);
                        // Scroll back to top
                        window.scrollTo(0, 0);
                        await delay(200);
                    }
                """)
            except Exception as e:
                print(f"Auto-scroll for lazy loading: {e}")
        
        # Step 2: Wait for all <img> elements to fully load
        try:
            page.evaluate("""
                () => {
                    return Promise.all(
                        Array.from(document.images)
                            .filter(img => !img.complete || img.naturalWidth === 0)
                            .map(img => new Promise((resolve) => {
                                img.onload = resolve;
                                img.onerror = resolve;
                                // Force reload lazy images that haven't started
                                if (img.loading === 'lazy') {
                                    img.loading = 'eager';
                                }
                                // Timeout after 5s per image
                                setTimeout(resolve, 5000);
                            }))
                    );
                }
            """)
        except Exception as e:
            print(f"Image load wait: {e}")
        
        # Step 3: Wait for web fonts to load (icon fonts like Font Awesome, Material Icons)
        try:
            page.evaluate("() => document.fonts.ready")
        except Exception as e:
            print(f"Font load wait: {e}")
        
        # Step 4: Final settle wait for any remaining rendering
        page.wait_for_timeout(500)
        # ──────────────────────────────────────────────────────────
        
        # Remove sections from DOM (collapses space, reduces page height)
        if remove_selectors:
            try:
                selector_str = ", ".join([s.strip() for s in remove_selectors if s.strip()])
                if selector_str:
                    page.add_style_tag(content=f"{selector_str} {{ display: none !important; }}")
                    # Wait briefly for reflow
                    page.wait_for_timeout(200)
            except Exception as e:
                print(f"Error removing sections: {e}")

        # Apply masks (ignore selectors — hide but preserve layout space)
        if mask_selectors:
            try:
                selector_str = ", ".join([s.strip() for s in mask_selectors if s.strip()])
                if selector_str:
                    # Hide elements completely
                    page.add_style_tag(content=f"{selector_str} {{ visibility: hidden !important; opacity: 0 !important; }}")
            except Exception as e:
                print(f"Error applying masks: {e}")

        # Custom wait before screenshot (user-defined extra time)
        if wait_time > 0:
            page.wait_for_timeout(wait_time)
            
        # Component screenshot if selector provided
        if selector:
            try:
                locator = page.locator(selector).first
                if locator.count() > 0:
                    locator.screenshot(path=out_path)
                    context.close()
                    browser.close()
                    _crop_to_max_height(out_path, max_height)
                    return
                else:
                    print(f"Selector '{selector}' not found. Falling back to full page.")
            except Exception as e:
                 print(f"Error capturing element '{selector}': {e}. Falling back to full page.")

        page.screenshot(path=out_path, full_page=fullpage)
        context.close()
        browser.close()
    
    # Post-process: crop to max height if specified
    _crop_to_max_height(out_path, max_height)


def _crop_to_max_height(image_path, max_height):
    """Crop a screenshot to max_height pixels if it exceeds that height."""
    if not max_height:
        return
    try:
        from PIL import Image
        img = Image.open(image_path)
        w, h = img.size
        if h > max_height:
            cropped = img.crop((0, 0, w, max_height))
            cropped.save(image_path)
            print(f"Cropped screenshot from {h}px to {max_height}px height")
    except ImportError:
        # Fallback: use OpenCV if Pillow not available
        try:
            import cv2
            img = cv2.imread(image_path)
            if img is not None and img.shape[0] > max_height:
                cropped = img[:max_height, :, :]
                cv2.imwrite(image_path, cropped)
                print(f"Cropped screenshot from {img.shape[0]}px to {max_height}px height (cv2)")
        except Exception as e:
            print(f"Error cropping image: {e}")
    except Exception as e:
        print(f"Error cropping image: {e}")

