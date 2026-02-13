
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Check if Selenium is installed
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not installed. Overlapping & Breaking detection will not work.")

class OverlappingBreakingCrawler:
    def __init__(self, start_url, max_pages=50):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.pages_to_check = set()
        self.issues = []
        self.max_pages = max_pages
        
    def is_internal(self, url):
        return urlparse(url).netloc == self.domain

    def discover_pages(self):
        """BFS to discover internal pages using fast requests"""
        queue = [self.start_url]
        self.pages_to_check.add(self.start_url)
        visited_bfs = set([self.start_url])
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        print("Discovering pages...")
        while queue and len(self.pages_to_check) < self.max_pages:
            url = queue.pop(0)
            try:
                # Fast fetch for links
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200: continue
                
                soup = BeautifulSoup(res.content, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href'].strip()
                    if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')): continue
                    
                    full_url = urljoin(url, href).split('#')[0]
                    
                    if self.is_internal(full_url) and full_url not in visited_bfs:
                        # Skip files
                        path = urlparse(full_url).path.lower()
                        if not any(path.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip', '.doc', '.css', '.js', '.xml']):
                            visited_bfs.add(full_url)
                            self.pages_to_check.add(full_url)
                            queue.append(full_url)
                            if len(self.pages_to_check) >= self.max_pages: break
                            
            except Exception as e:
                print(f"Discovery error on {url}: {e}")

        print(f"Discovered {len(self.pages_to_check)} pages.")

    def check_page_visuals(self, url):
        """Check a single page for overlapping and breaking layout issues using Selenium"""
        if not SELENIUM_AVAILABLE:
            return []
        
        issues = []
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.get(url)
            
            # Wait for meaningful paint
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2) # Allow animations/lazy-load
            
            # 1. Detect Overlapping Elements
            # Logic: Find elements that intersect significantly and are not nested
            overlapping_script = """
            function getVisibleElements() {
                // Select relevant layout candidates
                const all = document.querySelectorAll('div, section, article, nav, header, footer, main, aside, img, button, table');
                return Array.from(all).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                });
            }

            const elements = getVisibleElements();
            const issues = [];
            
            for (let i = 0; i < elements.length; i++) {
                const r1 = elements[i].getBoundingClientRect();
                if (r1.width < 20 || r1.height < 20) continue; // Skip tiny elements

                for (let j = i + 1; j < elements.length; j++) {
                    // Optimization: Limit checks
                    if (issues.length > 20) break;

                    const r2 = elements[j].getBoundingClientRect();
                    if (r2.width < 20 || r2.height < 20) continue;

                    // Check intersection
                    const intersectX = Math.max(0, Math.min(r1.right, r2.right) - Math.max(r1.left, r2.left));
                    const intersectY = Math.max(0, Math.min(r1.bottom, r2.bottom) - Math.max(r1.top, r2.top));
                    const area = intersectX * intersectY;

                    if (area > 500) { // Significant overlap > 500px^2
                        const el1 = elements[i];
                        const el2 = elements[j];

                        // Ignore if they are parent/child or regular flow siblings like spans
                        if (el1.contains(el2) || el2.contains(el1)) continue;
                        
                        // Ignore if one is positioned absolute/fixed (intentional overlap, e.g. modal, sticky header)
                        // This is a heuristic. Overlaps are bad if they obscure content unexpectedly.
                        // For this tool, we report text/content overlaps.
                        
                        // Check if they visually obscure text?
                        // Simple heuristic: Report it as potential issue.
                        
                        // Ignore standard negative margin hacks or sticky navs if top of page
                        // Filter out common sticky headers
                        const el1Style = window.getComputedStyle(el1);
                        const el2Style = window.getComputedStyle(el2);
                        if(el1Style.position === 'fixed' || el2Style.position === 'fixed') continue;

                        issues.push({
                            type: 'Overlap',
                            elem1: el1.tagName + (el1.className ? '.' + el1.className.split(' ')[0] : ''),
                            elem2: el2.tagName + (el2.className ? '.' + el2.className.split(' ')[0] : ''),
                            coords: `${Math.round(r1.x)},${Math.round(r1.y)} vs ${Math.round(r2.x)},${Math.round(r2.y)}`
                        });
                    }
                }
            }
            return issues;
            """
            found_overlaps = driver.execute_script(overlapping_script)
            if found_overlaps:
                for ov in found_overlaps:
                    issues.append({
                        'Page URL': url,
                        'Issue Type': 'Overlapping Elements',
                        'Element 1': ov['elem1'],
                        'Element 2': ov['elem2'],
                        'Position': ov['coords'],
                        'Details': 'Elements overlap significantly'
                    })

            # 2. Detect Horizontal Scroll / Breaking Layout
            breaking_script = """
            const docWidth = document.documentElement.clientWidth;
            const bodyWidth = document.body.scrollWidth;
            const issues = [];

            if (bodyWidth > docWidth + 10) {
                // Find culprits
                const all = document.querySelectorAll('*');
                for (let el of all) {
                    const rect = el.getBoundingClientRect();
                    if (rect.right > docWidth + 10) {
                         const style = window.getComputedStyle(el);
                         if (style.display !== 'none') {
                             issues.push({
                                 elem: el.tagName + (el.className ? '.' + el.className.split(' ')[0] : ''),
                                 overflow: Math.round(rect.right - docWidth)
                             });
                             if (issues.length > 5) break; 
                         }
                    }
                }
            }
            return issues;
            """
            found_breaking = driver.execute_script(breaking_script)
            if found_breaking:
                for br in found_breaking:
                    issues.append({
                        'Page URL': url,
                        'Issue Type': 'Breaking Layout (Horizontal Scroll)',
                        'Element 1': br['elem'],
                        'Element 2': '-',
                        'Position': 'Overflows viewport',
                        'Details': f"Exceeds viewport by {br['overflow']}px"
                    })

        except Exception as e:
            print(f"Visual check failed for {url}: {e}")
        finally:
            if driver:
                driver.quit()
        
        return issues

    def run(self):
        if not SELENIUM_AVAILABLE:
            return []

        # Step 1: Discover Pages
        self.discover_pages()
        
        # Step 2: Check pages in parallel
        # Limit concurrency for Selenium (RAM heavy)
        print(f"Checking {len(self.pages_to_check)} pages for layout issues...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(self.check_page_visuals, url): url for url in self.pages_to_check}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    page_issues = future.result()
                    if page_issues:
                        self.issues.extend(page_issues)
                except Exception as e:
                    print(f"Failed to check {url}: {e}")
                    
        return self.issues
