# PageSpeed Insights API Integration

## Overview
The SEO & Performance testing feature now uses **Google PageSpeed Insights API** to provide real performance and SEO analysis.

## Features
- ✅ Real performance scores from Google
- ✅ Core Web Vitals (LCP, FID, CLS, FCP, TTI)
- ✅ SEO analysis and recommendations
- ✅ Accessibility scores
- ✅ Best practices checks
- ✅ Detailed improvement suggestions

## API Key (Optional but Recommended)

### Why You Need an API Key
- **Without API Key**: Limited to 25 requests per day
- **With API Key**: 25,000 requests per day (free tier)

### How to Get a Google API Key

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project** (or select existing)
   - Click "Select a project" → "New Project"
   - Enter project name → Click "Create"

3. **Enable PageSpeed Insights API**
   - Go to: https://console.cloud.google.com/apis/library
   - Search for "PageSpeed Insights API"
   - Click on it → Click "Enable"

4. **Create API Credentials**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "API Key"
   - Copy the generated API key

5. **Restrict API Key** (Recommended for security)
   - Click on your API key to edit it
   - Under "API restrictions":
     - Select "Restrict key"
     - Check "PageSpeed Insights API"
   - Click "Save"

### How to Use the API Key

#### Option 1: Environment Variable (Recommended)
```bash
export PAGESPEED_API_KEY="your-api-key-here"
```

Or add to your `.env` file:
```
PAGESPEED_API_KEY=your-api-key-here
```

#### Option 2: Direct Configuration
Edit `utils/pagespeed.py` and add your key:
```python
psi = PageSpeedInsights(api_key="your-api-key-here")
```

## Usage

The API is automatically used when you run SEO & Performance tests:

1. Go to `/seo-performance` page
2. Enter a URL
3. Select test type (SEO, Performance, or Both)
4. Select device type (Desktop or Mobile)
5. Click "Run Analysis"

## API Response Time

- **Typical response time**: 10-30 seconds
- **Timeout**: 60 seconds
- The API analyzes the page in real-time, so it may take longer for complex pages

## Rate Limits

### Without API Key
- 25 requests per day
- Shared across all users

### With API Key (Free Tier)
- 25,000 requests per day
- Per API key

### Quota Exceeded Error
If you see "Quota exceeded" error:
1. Wait 24 hours for quota reset, OR
2. Add an API key (see above), OR
3. Create a new Google Cloud project with a new API key

## Metrics Provided

### Performance Metrics
- Performance Score (0-100)
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Time to Interactive (TTI)
- Total Blocking Time (TBT)
- Cumulative Layout Shift (CLS)
- Speed Index
- Load Time

### SEO Checks
- Title Tag
- Meta Description
- Heading Structure
- Image Alt Text
- Crawlability
- Robots.txt
- Canonical URL
- Hreflang
- Link Text

### Additional Scores
- Accessibility Score (0-100)
- Best Practices Score (0-100)

## Troubleshooting

### Error: "PageSpeed Insights API error"
- Check your internet connection
- Verify the URL is publicly accessible
- Ensure the URL starts with `http://` or `https://`

### Error: "Quota exceeded"
- Add an API key (see above)
- Wait 24 hours for quota reset

### Slow Response
- PageSpeed Insights analyzes pages in real-time
- Complex pages take longer (30-60 seconds)
- This is normal behavior

## Cost

**Free Tier**: 25,000 requests/day per API key
**Paid Tier**: Not typically needed for most use cases

For pricing details: https://developers.google.com/speed/docs/insights/v5/about#pricing

## Documentation

Official PageSpeed Insights API documentation:
https://developers.google.com/speed/docs/insights/v5/get-started
