import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class StatusCache:
    """Shared cache to avoid re-checking same URL multiple times"""
    def __init__(self):
        self.cache = {}

    def get(self, url):
        return self.cache.get(url)

    def set(self, url, status):
        self.cache[url] = status

    def clear(self):
        self.cache.clear()

global_status_cache = StatusCache()

class ImageIconCrawler:
    def __init__(self, start_url, max_pages=1000000, max_depth=1000):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited_pages = set()
        self.broken_assets = []
        self.special_interest_found = [] # For /archived/ tracking
        self.reported_urls = set() # For "links should not reapt"
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.status_cache = global_status_cache
        
        # Create session with connection pooling and retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        # Use a modern browser User-Agent to avoid blocking and handling some server-side checks
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        })

    def is_internal(self, url):
        return urlparse(url).netloc == self.domain

    def check_asset(self, url, referer=None):
        headers = self.session.headers.copy()
        if referer:
            headers['Referer'] = referer
            
        try:
            # Some servers block HEAD requests, or behave differently. verify with GET if HEAD fails.
            response = self.session.head(url, headers=headers, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                # Retry with GET and full headers
                response = self.session.get(url, headers=headers, timeout=10, stream=True)
                response.close()
            return response.status_code
        except requests.RequestException:
            return 0

    def check_assets_batch(self, assets_batch):
        """Check multiple assets concurrently while preserving order"""
        results = [None] * len(assets_batch)
        
        # Use cache for already checked URLs
        to_check_indices = []
        for i, asset in enumerate(assets_batch):
            url = asset[1]
            cached_status = self.status_cache.get(url)
            if cached_status is not None:
                results[i] = cached_status
            else:
                to_check_indices.append(i)
        
        if to_check_indices:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_idx = {executor.submit(self.check_asset, assets_batch[idx][1], assets_batch[idx][3]): idx 
                                 for idx in to_check_indices}
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        status = future.result()
                        results[idx] = status
                        self.status_cache.set(assets_batch[idx][1], status)
                    except Exception:
                        results[idx] = 0
                        self.status_cache.set(assets_batch[idx][1], 0)
        
        # Map findings back to broken items
        findings = []
        for i, status in enumerate(results):
            if status >= 400 or status == 0:
                asset_type, full_url, element, page_url = assets_batch[i]
                findings.append((asset_type, full_url, element, page_url, status))
        return findings

    def crawl(self, url, depth=0):
        if url in self.visited_pages or not self.is_internal(url) or depth > self.max_depth or len(self.visited_pages) >= self.max_pages:
            return []

        print(f"Crawling: {url} (depth: {depth})")
        self.visited_pages.add(url)

        links_to_crawl = []
        assets_to_check = []

        try:
            # Use Referer for the page crawl itself if possible (from parent?), 
            # but here start_url is entry. For deeper pages, we don't track parent easily in BFS without modifying queue.
            # For now, just getting the page is fine.
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')

            # Collect all assets
            images = soup.find_all('img')
            icons = soup.find_all('link', rel=lambda x: x and 'icon' in x.lower().split())
            svg_images = soup.find_all('image')

            # Enhanced Image Extraction (Lazy Load Support)
            for img in images:
                # Candidates for the image URL
                candidates = []
                
                # Standard src
                src = img.get('src')
                if src: candidates.append(src.strip())
                
                # Lazy loading attributes
                for attr in ['data-src', 'data-original', 'data-url', 'data-lazy', 'data-src-retina']:
                    val = img.get(attr)
                    if val: candidates.append(val.strip())
                
                # Check each unique candidate
                seen_candidates = set()
                for img_url in candidates:
                    if img_url in seen_candidates: continue
                    seen_candidates.add(img_url)
                    
                    if img_url.startswith('data:') or img_url.startswith('blob:'):
                        continue
                        
                    full_url = urljoin(url, img_url)
                    assets_to_check.append(('Image', full_url, img, url))
            
            # Srcset parsing
            for img in images:
                srcset = img.get('srcset') or img.get('data-srcset')
                if srcset:
                    # Parse srcset: "url1 1x, url2 2x"
                    parts = srcset.split(',')
                    for part in parts:
                        # Take the first part of the split (url) and ignore size descriptor
                        clean_url = part.strip().split(' ')[0]
                        if clean_url and not clean_url.startswith('data:'):
                            full_url = urljoin(url, clean_url.strip())
                            assets_to_check.append(('Image (srcset)', full_url, img, url))
            
            for icon in icons:
                href = icon.get('href')
                if href and not href.startswith('data:'):
                    full_url = urljoin(url, href.strip())
                    assets_to_check.append(('Icon', full_url, icon, url))

            for svg_img in svg_images:
                href = svg_img.get('href') or svg_img.get('xlink:href')
                if href and not href.startswith('data:'):
                    full_url = urljoin(url, href.strip())
                    assets_to_check.append(('SVG Image', full_url, svg_img, url))

            # Track special interest URLs (Archived) regardless of status
            for asset_type, full_url, element, page_url in assets_to_check:
                if '/archived/' in full_url.lower() or '/archieved/' in full_url.lower():
                    self.special_interest_found.append({
                        'Found On Page': page_url,
                        'Target URL': full_url,
                        'URL Type': f"Asset ({asset_type})",
                        'Context': str(element)[:150]
                    })


            # Check assets in batch
            broken_results = self.check_assets_batch(assets_to_check)
            
            for asset_type, full_url, element, page_url, status in broken_results:
                # Deduplicate based on "links should not reapt"
                if full_url in self.reported_urls:
                    continue
                self.reported_urls.add(full_url)
                
                parent = element.find_parent()
                section_info = "Unknown"
                while parent and parent.name != 'body':
                    if parent.get('id'):
                        section_info = f"#{parent['id']}"
                        break
                    if parent.get('class'):
                        section_info = f".{'.'.join(parent['class'])}"
                        break
                    parent = parent.find_parent()

                self.broken_assets.append({
                    'First Found On Page': page_url,
                    'Asset Type': asset_type,
                    'Asset URL': full_url,
                    'Status Code': status,
                    'Section/Component': section_info,
                    'HTML Element': str(element)[:100]
                })

            # Collect links for crawling
            links = soup.find_all('a', href=True)
            for link in links:
                next_url = urljoin(url, link['href'].strip())
                next_url = next_url.split('#')[0]
                if self.is_internal(next_url) and next_url not in self.visited_pages:
                    path = urlparse(next_url).path.lower()
                    if not any(path.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip']):
                        links_to_crawl.append(next_url)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

        return links_to_crawl

    def run(self):
        # BFS crawling with depth limit
        queue = [(self.start_url, 0)]
        
        while queue and len(self.visited_pages) < self.max_pages:
            current_url, depth = queue.pop(0)
            if current_url not in self.visited_pages:
                new_links = self.crawl(current_url, depth)
                for link in new_links:
                    if link not in self.visited_pages:
                        queue.append((link, depth + 1))
        
        return self.broken_assets, self.special_interest_found

class LinkCrawler:
    def __init__(self, start_url, max_pages=1000000, max_depth=1000):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited_pages = set()
        self.checked_links = set() # Links checked against server
        self.special_interest_found = [] # For /archived/ tracking
        self.reported_urls = set() # For unique reporting
        self.broken_links = []
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.status_cache = global_status_cache
        
        # Create session with connection pooling
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            # 'Accept-Language': 'en-US,en;q=0.9', # Removed to see if it fixes AsianPaints
            'Connection': 'keep-alive'
        })

    def is_internal(self, url):
        return urlparse(url).netloc == self.domain

    def check_link(self, url, referer=None):
        """Check if a link is broken"""
        headers = self.session.headers.copy()
        if referer:
            headers['Referer'] = referer
            
        try:
            response = self.session.head(url, headers=headers, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                response = self.session.get(url, headers=headers, timeout=10, stream=True)
                response.close()
            return response.status_code
        except requests.RequestException:
            return 0

    def check_links_batch(self, links_batch):
        """Check multiple links concurrently while preserving discovery order"""
        results = [None] * len(links_batch)
        
        # Use cache for already checked URLs
        to_check_indices = []
        for i, link_data in enumerate(links_batch):
            url = link_data[0]
            cached_status = self.status_cache.get(url)
            if cached_status is not None:
                results[i] = cached_status
            else:
                to_check_indices.append(i)
                
        if to_check_indices:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_idx = {executor.submit(self.check_link, links_batch[idx][0], links_batch[idx][2]): idx 
                                 for idx in to_check_indices}
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        status = future.result()
                        results[idx] = status
                        self.status_cache.set(links_batch[idx][0], status)
                    except Exception:
                        results[idx] = 0
                        self.status_cache.set(links_batch[idx][0], 0)
        
        findings = []
        for i, status in enumerate(results):
            if status >= 400 or status == 0:
                full_url, link_elem, page_url = links_batch[i]
                findings.append((full_url, link_elem, page_url, status))
        return findings

    def crawl(self, url, depth=0):
        if url in self.visited_pages or not self.is_internal(url) or depth > self.max_depth or len(self.visited_pages) >= self.max_pages:
            return []

        print(f"Crawling: {url} (depth: {depth})")
        self.visited_pages.add(url)

        links_to_crawl = []
        links_to_check = []

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                data_href = link.get('data-href')
                
                # Use data-href if href is # or javascript
                if (not href or href == '#' or href.startswith('javascript')) and data_href:
                    href = data_href

                if not href: continue
                
                href = href.strip()
                
                # Skip non-http links
                if href.startswith(('javascript:', 'mailto:', 'tel:', 'sms:', 'ftp:', 'file:', '#')):
                    continue
                
                full_url = urljoin(url, href)
                full_url = full_url.split('#')[0]
                
                # Strict External Link Skipping
                if not self.is_internal(full_url):
                    continue
                
                if full_url not in self.checked_links:
                    self.checked_links.add(full_url)
                    links_to_check.append((full_url, link, url))
                
                # Add to crawl queue if internal and NOT a file
                if full_url not in self.visited_pages:
                    path = urlparse(full_url).path.lower()
                    skip_ext = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.css', '.js', '.xml', '.json', '.txt']
                    if not any(path.endswith(ext) for ext in skip_ext):
                        links_to_crawl.append(full_url)
                
                # Track special interest URLs (Archived)
                if '/archived/' in full_url.lower() or '/archieved/' in full_url.lower():
                    self.special_interest_found.append({
                        'Found On Page': url,
                        'Target URL': full_url,
                        'Link Text/Label': link.get_text(strip=True),
                        'URL Type': 'Link (a tag)'
                    })

            # Check links in batch
            broken_results = self.check_links_batch(links_to_check)
            
            for full_url, link_elem, page_url, status in broken_results:
                # Deduplicate based on "links should not reapt"
                if full_url in self.reported_urls:
                    continue
                self.reported_urls.add(full_url)
                
                parent = link_elem.find_parent()
                section_info = "Unknown"
                while parent and parent.name != 'body':
                    if parent.get('id'):
                        section_info = f"#{parent['id']}"
                        break
                    if parent.get('class'):
                        section_info = f".{'.'.join(parent['class'])}"
                        break
                    parent = parent.find_parent()

                # Since we filter external, this will always be Internal
                link_type = "Internal Link"
                
                if status >= 400 or status == 0:
                    self.broken_links.append({
                        'First Found On Page': page_url,
                        'Link Type': link_type,
                        'Link URL': full_url,
                        'Link Text': link_elem.get_text(strip=True)[:100],
                        'Status Code': status,
                        'Section/Component': section_info,
                        'HTML Element': str(link_elem)[:100]
                    })

        except Exception as e:
            print(f"Error crawling {url}: {e}")

        return links_to_crawl

    def run(self):
        # BFS crawling with depth limit
        queue = [(self.start_url, 0)]
        
        while queue and len(self.visited_pages) < self.max_pages:
            current_url, depth = queue.pop(0)
            if current_url not in self.visited_pages:
                new_links = self.crawl(current_url, depth)
                for link in new_links:
                    if link not in self.visited_pages:
                        queue.append((link, depth + 1))
        
        return self.broken_links, self.special_interest_found

def generate_excel_report(broken_assets, special_interest, job_id, output_dir):
    if not broken_assets and not special_interest:
        return None
    
    output_path = os.path.join(output_dir, f"comprehensive_crawl_report_{job_id}.xlsx")
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        if broken_assets:
            df_broken = pd.DataFrame(broken_assets)
            df_broken.to_excel(writer, index=False, sheet_name='Broken Items')
        
        if special_interest:
            df_special = pd.DataFrame(special_interest)
            # Remove exact duplicates from special interest
            df_special = df_special.drop_duplicates()
            df_special.to_excel(writer, index=False, sheet_name='Archived Link Discovery')
            
    return output_path
