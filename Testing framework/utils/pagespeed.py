import requests
import os
import time

class PageSpeedInsights:
    """
    Wrapper for Google PageSpeed Insights API
    """
    
    def __init__(self, api_key=None):
        """
        Initialize PageSpeed Insights API client
        
        Args:
            api_key: Google API key (optional, but recommended to avoid rate limits)
        """
        self.api_key = api_key or os.environ.get('PAGESPEED_API_KEY')
        self.base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    def analyze(self, url, strategy='desktop', categories=None):
        """
        Analyze a URL using PageSpeed Insights
        
        Args:
            url: URL to analyze
            strategy: 'desktop' or 'mobile'
            categories: List of categories to analyze (performance, accessibility, best-practices, seo)
        
        Returns:
            Dictionary containing analysis results
        """
        if categories is None:
            categories = ['performance', 'accessibility', 'best-practices', 'seo']
        
        params = {
            'url': url,
            'strategy': strategy
        }
        
        # Add categories
        for category in categories:
            params[f'category'] = category
        
        # Add API key if available
        if self.api_key:
            params['key'] = self.api_key
        
        max_retries = 3
        retry_delay = 5  # Start with 5 seconds
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(self.base_url, params=params, timeout=60)
                response.raise_for_status()
                return self._parse_response(response.json())
                
            except requests.exceptions.HTTPError as e:
                # Handle API Key errors (400, 401, 403) - Retry WITHOUT key
                if e.response.status_code in [400, 401, 403] and 'key' in params:
                    print(f"API Key failed with {e.response.status_code}, retrying without key...")
                    params.pop('key')
                    continue # Retry immediately without key
                
                # Handle Rate Limit (429) - Backoff and Retry
                if e.response.status_code == 429:
                    if attempt < max_retries:
                        print(f"Rate limit exceeded (429). Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        raise Exception(
                            "PageSpeed Insights API rate limit exceeded even after retries.\n"
                            "Please try again later or use a valid Google API Key."
                        )
                
                # Raise other HTTP errors immediately
                raise Exception(f"PageSpeed Insights API error: {str(e)}")
                
            except requests.exceptions.RequestException as e:
                # Retry network errors
                if attempt < max_retries:
                    print(f"Network error: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                raise Exception(f"PageSpeed Insights API error: {str(e)}")
    
    def _parse_response(self, data):
        """
        Parse PageSpeed Insights API response
        
        Args:
            data: Raw API response
        
        Returns:
            Parsed metrics dictionary
        """
        lighthouse = data.get('lighthouseResult', {})
        categories = lighthouse.get('categories', {})
        audits = lighthouse.get('audits', {})
        
        # Extract scores
        performance_score = int(categories.get('performance', {}).get('score', 0) * 100)
        seo_score = int(categories.get('seo', {}).get('score', 0) * 100)
        accessibility_score = int(categories.get('accessibility', {}).get('score', 0) * 100)
        best_practices_score = int(categories.get('best-practices', {}).get('score', 0) * 100)
        
        # Extract performance metrics
        metrics = audits.get('metrics', {}).get('details', {}).get('items', [{}])[0]
        
        performance_details = []
        
        # Core Web Vitals
        if 'first-contentful-paint' in audits:
            fcp = audits['first-contentful-paint']
            performance_details.append({
                'name': 'First Contentful Paint (FCP)',
                'value': fcp.get('displayValue', 'N/A'),
                'threshold': 1.8,
                'score': fcp.get('score', 0)
            })
        
        if 'largest-contentful-paint' in audits:
            lcp = audits['largest-contentful-paint']
            performance_details.append({
                'name': 'Largest Contentful Paint (LCP)',
                'value': lcp.get('displayValue', 'N/A'),
                'threshold': 2.5,
                'score': lcp.get('score', 0)
            })
        
        if 'interactive' in audits:
            tti = audits['interactive']
            performance_details.append({
                'name': 'Time to Interactive (TTI)',
                'value': tti.get('displayValue', 'N/A'),
                'threshold': 3.8,
                'score': tti.get('score', 0)
            })
        
        if 'total-blocking-time' in audits:
            tbt = audits['total-blocking-time']
            performance_details.append({
                'name': 'Total Blocking Time (TBT)',
                'value': tbt.get('displayValue', 'N/A'),
                'threshold': 200,
                'score': tbt.get('score', 0)
            })
        
        if 'cumulative-layout-shift' in audits:
            cls = audits['cumulative-layout-shift']
            performance_details.append({
                'name': 'Cumulative Layout Shift (CLS)',
                'value': cls.get('displayValue', 'N/A'),
                'threshold': 0.1,
                'score': cls.get('score', 0)
            })
        
        if 'speed-index' in audits:
            si = audits['speed-index']
            performance_details.append({
                'name': 'Speed Index',
                'value': si.get('displayValue', 'N/A'),
                'threshold': 3.4,
                'score': si.get('score', 0)
            })
        
        # Extract SEO details
        seo_details = []
        
        seo_audits = {
            'document-title': 'Title Tag',
            'meta-description': 'Meta Description',
            'heading-order': 'Heading Structure',
            'image-alt': 'Image Alt Text',
            'is-crawlable': 'Crawlability',
            'robots-txt': 'Robots.txt',
            'canonical': 'Canonical URL',
            'hreflang': 'Hreflang',
            'link-text': 'Link Text'
        }
        
        for audit_key, audit_name in seo_audits.items():
            if audit_key in audits:
                audit = audits[audit_key]
                seo_details.append({
                    'name': audit_name,
                    'passed': audit.get('score', 0) >= 0.9,
                    'details': audit.get('title', 'N/A')
                })
        
        # Extract recommendations
        recommendations = []
        
        # Get opportunities (performance improvements)
        if 'opportunities' in categories.get('performance', {}):
            for opportunity in categories['performance'].get('details', {}).get('items', [])[:5]:
                if 'title' in opportunity:
                    recommendations.append({
                        'title': opportunity.get('title', ''),
                        'description': opportunity.get('description', '')
                    })
        
        # Get diagnostics
        diagnostic_audits = ['uses-optimized-images', 'uses-text-compression', 'uses-responsive-images', 
                            'efficient-animated-content', 'unused-css-rules']
        
        for audit_key in diagnostic_audits:
            if audit_key in audits:
                audit = audits[audit_key]
                if audit.get('score', 1) < 1:
                    recommendations.append({
                        'title': audit.get('title', ''),
                        'description': audit.get('description', '')
                    })
        
        # Calculate load time from metrics
        load_time = metrics.get('observedLoad', 0) / 1000 if 'observedLoad' in metrics else 0
        
        return {
            'seo_score': seo_score,
            'performance_score': performance_score,
            'accessibility_score': accessibility_score,
            'best_practices_score': best_practices_score,
            'load_time': round(load_time, 2),
            'seo_details': seo_details,
            'performance_details': performance_details,
            'recommendations': recommendations[:5]  # Limit to top 5
        }
