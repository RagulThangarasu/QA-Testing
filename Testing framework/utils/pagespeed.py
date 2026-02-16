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
        params['category'] = categories
        
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
        
        # Core Web Vitals & Metrics
        # FCP
        fcp = audits.get('first-contentful-paint', {})
        performance_details.append({
            'id': 'first-contentful-paint', # Add ID for lookup
            'name': 'First Contentful Paint (FCP)',
            'displayValue': fcp.get('displayValue', 'N/A'),
            'score': fcp.get('score', 0)
        })
        
        # LCP
        lcp = audits.get('largest-contentful-paint', {})
        performance_details.append({
            'id': 'largest-contentful-paint',
            'name': 'Largest Contentful Paint (LCP)',
            'displayValue': lcp.get('displayValue', 'N/A'),
            'score': lcp.get('score', 0)
        })
        
        # CLS
        cls = audits.get('cumulative-layout-shift', {})
        performance_details.append({
            'id': 'cumulative-layout-shift',
            'name': 'Cumulative Layout Shift (CLS)',
            'displayValue': cls.get('displayValue', 'N/A'),
            'score': cls.get('score', 0)
        })

        # TTI
        tti = audits.get('interactive', {})
        performance_details.append({
            'id': 'interactive',
            'name': 'Time to Interactive (TTI)',
            'displayValue': tti.get('displayValue', 'N/A'),
            'score': tti.get('score', 0)
        })
        
        # TBT
        tbt = audits.get('total-blocking-time', {})
        performance_details.append({
            'id': 'total-blocking-time',
            'name': 'Total Blocking Time (TBT)',
            'displayValue': tbt.get('displayValue', 'N/A'),
            'score': tbt.get('score', 0)
        })
        
        # Speed Index
        si = audits.get('speed-index', {})
        performance_details.append({
            'id': 'speed-index',
            'name': 'Speed Index',
            'displayValue': si.get('displayValue', 'N/A'),
            'score': si.get('score', 0)
        })

        # TTFB (Time to First Byte)
        # Audit ID: server-response-time
        ttfb = audits.get('server-response-time', {})
        performance_details.append({
            'id': 'server-response-time',
            'name': 'Time to First Byte (TTFB)',
            'displayValue': ttfb.get('displayValue', 'N/A'),
            'score': ttfb.get('score', 0)
        })

        # Core Web Vitals (Field Data) - FID (First Input Delay)
        # Usually found in loadingExperience from CrUX data
        loading_experience = data.get('loadingExperience', {})
        metrics_crux = loading_experience.get('metrics', {})
        
        if 'FIRST_INPUT_DELAY_MS' in metrics_crux:
            fid_metric = metrics_crux['FIRST_INPUT_DELAY_MS']
            # Format: { percentile: 13, distributions: [...], category: 'FAST' }
            fid_val = fid_metric.get('percentile', 0)
            fid_category = fid_metric.get('category', 'UNKNOWN')
            
            # Add to details
            performance_details.insert(0, { # Insert at top or near relevant metrics
                'id': 'first-input-delay',
                'name': 'First Input Delay (FID)',
                'displayValue': f"{fid_val} ms",
                'score': 1 if fid_category == 'FAST' else (0.5 if fid_category == 'AVERAGE' else 0),
                'is_field_data': True
            })
        else:
            # If no Field Data, usually use TBT as proxy for Lab
            pass
        
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
                    'passed': (audit.get('score') or 0) >= 0.9,
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
