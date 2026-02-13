import requests
from bs4 import BeautifulSoup
import re

def fetch_sitemap_urls(sitemap_url, visited=None):
    """
    Fetch and parse a sitemap (XML) to extract all page URLs.
    Handles standard sitemaps and sitemap indexes.
    """
    if visited is None:
        visited = set()
        
    if sitemap_url in visited:
        return []
        
    visited.add(sitemap_url)
    urls = set()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/xml,text/xml,application/xhtml+xml,text/html;q=0.9'
        }
        response = requests.get(sitemap_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        content = response.content
        locs = []
        
        # Try parsing with BS4
        try:
            # Try 'xml' parser first, then 'lxml', then 'html.parser'
            soup = None
            for parser in ['xml', 'lxml-xml', 'lxml', 'html.parser']:
                try:
                    soup = BeautifulSoup(content, parser)
                    if soup.find('loc'):
                        break
                except Exception:
                    continue
            
            if soup:
                loc_tags = soup.find_all('loc')
                locs = [t.text.strip() for t in loc_tags if t.text]
        except Exception as e:
            print(f"BS4 parsing error: {e}")
            
        # Fallback to regex if BS4 failed to find anything
        if not locs:
            locs = re.findall(r'<loc>(.*?)</loc>', response.text)
            
        for url in locs:
            url = url.strip()
            if not url: continue
            
            # Check if it's a nested sitemap
            if url.endswith('.xml') or 'sitemap' in url.split('/')[-1]:
                # Recursively fetch, but assume it's a sitemap index
                # Avoid infinite recursion with visited set
                sub_urls = fetch_sitemap_urls(url, visited)
                urls.update(sub_urls)
            else:
                urls.add(url)
                    
    except Exception as e:
        print(f"Error parsing sitemap {sitemap_url}: {e}")
        
    return list(urls)
