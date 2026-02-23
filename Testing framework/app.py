import os, uuid, threading, time, datetime
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
from utils.screenshot import capture_screenshot
from utils.image_compare import compare_images
from utils.report import build_pdf_report
from utils.jira_client import JiraClient

app = Flask(__name__, static_folder='static', static_url_path='/static')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(BASE_DIR, "runs")
os.makedirs(RUNS_DIR, exist_ok=True)

ALLOWED_EXT = {"png"}


from utils.store import store
from utils.baseline_store import BaselineStore

baseline_store = BaselineStore(data_dir=os.path.join(RUNS_DIR, "baselines"), metadata_file=os.path.join(RUNS_DIR, "baselines.json"))




def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.post("/api/compare")
def compare():
    """
    Multipart form:
      - figma_png: file (PNG)
      - stage_url: str
      - viewport: "desktop"|"mobile"|"WxH" (optional)
      - fullpage: "true"/"false" (optional)
      - threshold: float 0..1 (optional)
    """
    stage_url = request.form.get("stage_url", "").strip()
    if not stage_url.startswith("http"):
        return jsonify({"error": "Valid stage_url (http/https) is required"}), 400

    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(RUNS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save stage_url in job data immediately so it's available for approval
    store.save_job(job_id, {"status": "starting", "progress": 0, "step": "Initializing", "stage_url": stage_url})

    import shutil
    figma_path = os.path.join(job_dir, "figma.png")
    uploaded_file = request.files.get("figma_png")

    if not uploaded_file or uploaded_file.filename == "":
        # No file - try to use stored baseline
        baseline_path = baseline_store.get_active_baseline_path(stage_url)
        if baseline_path and os.path.exists(baseline_path):
            shutil.copy2(baseline_path, figma_path)
            reference_source = "baseline"
        else:
            return jsonify({"error": "No baseline image uploaded and no active baseline found for this URL."}), 400
    else:
        # File uploaded - save it
        if not allowed_file(uploaded_file.filename):
             return jsonify({"error": "Please upload a PNG file"}), 400
        uploaded_file.save(figma_path)
        reference_source = "upload"

    viewport = request.form.get("viewport", "desktop")
    
    # Capture mode controls
    capture_mode = request.form.get("capture_mode", "fullpage")
    if capture_mode == "viewport":
        fullpage = False
    else:
        fullpage = True
    
    max_capture_height = None
    if capture_mode == "custom_height":
        try:
            max_capture_height = int(request.form.get("max_capture_height", "3000"))
        except ValueError:
            max_capture_height = 3000
    
    remove_selectors = request.form.get("remove_selectors", "")
    
    # Advanced options
    ignore_selectors = request.form.get("ignore_selectors", "")
    try:
        wait_time = int(request.form.get("wait_time", "1000"))
    except ValueError:
        wait_time = 1000

    # Highlight option (checkbox)
    highlight_diffs = request.form.get("highlight_diffs") == "on"

    try:
        threshold = float(request.form.get("threshold", "0.85"))
    except ValueError:
        threshold = 0.85

    noise_tolerance = request.form.get("noise_tolerance", "medium")
    
    enable_pixel_threshold = request.form.get("enable_pixel_threshold") == "true"
    pixel_threshold = request.form.get("pixel_threshold", None)
    
    if enable_pixel_threshold and pixel_threshold and pixel_threshold.isdigit():
        pixel_threshold = int(pixel_threshold)
    else:
        pixel_threshold = None

    # Validation options
    check_layout = request.form.get("check_layout") == "on"
    check_content = request.form.get("check_content") == "on"
    check_colors = request.form.get("check_colors") == "on"

    component_selector = request.form.get("component_selector", "").strip() or None

    # Initialize job status
    job_data = {
        "job_id": job_id,
        "type": "visual_testing",
        "status": "running",
        "progress": 0,
        "step": "Starting...",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "result": None,
        "error": None,
        "stage_url": stage_url,
        "figma_path": figma_path,
        "reference_source": reference_source
    }
    store.save_job(job_id, job_data)


    # Start background thread
    thread = threading.Thread(target=process_comparison, args=(job_id, figma_path, stage_url, viewport, fullpage, threshold, noise_tolerance, job_dir, ignore_selectors, wait_time, highlight_diffs, pixel_threshold, component_selector, check_layout, check_content, check_colors, remove_selectors, max_capture_height))
    thread.start()

    return jsonify({"job_id": job_id})

@app.post("/api/broken-links")
def check_broken_links():
    data = request.json
    stage_url = data.get("stage_url", "").strip()
    check_type = data.get("check_type", "all")

    if not stage_url.startswith("http"):
        return jsonify({"error": "Valid stage_url (http/https) is required"}), 400
    
    job_id = f"c_{str(uuid.uuid4())[:8]}"
    job_dir = os.path.join(RUNS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Initialize job
    job_data = {
        "job_id": job_id,
        "type": "broken_links",
        "stage_url": stage_url,
        "check_type": check_type,
        "status": "running",
        "progress": 0,
        "step": "Starting crawler...",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "result": None
    }
    store.save_job(job_id, job_data)
    
    # Start thread
    thread = threading.Thread(target=process_broken_links, args=(job_id, stage_url, check_type, job_dir))
    thread.start()
    
    return jsonify({"job_id": job_id})

def process_broken_links(job_id, stage_url, check_type, job_dir):
    try:
        from utils.crawler import ImageIconCrawler, LinkCrawler, generate_excel_report
        
        store.save_job(job_id, {"step": "Crawling pages...", "progress": 10})
        
        # Choose crawler based on check_type
        if check_type == "broken_links":
            # Run both image and link crawlers (default option)
            store.save_job(job_id, {"step": "Checking images & icons...", "progress": 20})
            img_crawler = ImageIconCrawler(stage_url)
            broken_images = img_crawler.run()
            
            store.save_job(job_id, {"step": "Checking links...", "progress": 50})
            link_crawler = LinkCrawler(stage_url)
            broken_links = link_crawler.run()
            
            broken_assets = broken_images + broken_links
            
        elif check_type == "overlapping_breaking":
            # Run overlapping and breaking detection
            try:
                from utils.overlapping_crawler import OverlappingBreakingCrawler
                store.save_job(job_id, {"step": "Checking overlapping & breaking...", "progress": 30})
                overlap_crawler = OverlappingBreakingCrawler(stage_url)
                broken_assets = overlap_crawler.run()
            except ImportError as e:
                raise Exception("Selenium is required for overlapping & breaking detection. Please install: pip install selenium")
            except Exception as e:
                raise Exception(f"Overlapping & breaking detection failed: {str(e)}")
            
        elif check_type == "all":
            # Run all crawlers including future features
            store.save_job(job_id, {"step": "Checking images & icons...", "progress": 15})
            img_crawler = ImageIconCrawler(stage_url)
            broken_images = img_crawler.run()
            
            store.save_job(job_id, {"step": "Checking links...", "progress": 35})
            link_crawler = LinkCrawler(stage_url)
            broken_links = link_crawler.run()
            
            # Add overlapping and breaking detection
            try:
                from utils.overlapping_crawler import OverlappingBreakingCrawler
                store.save_job(job_id, {"step": "Checking overlapping & breaking...", "progress": 60})
                overlap_crawler = OverlappingBreakingCrawler(stage_url)
                overlapping_issues = overlap_crawler.run()
            except Exception as e:
                print(f"Overlapping detection skipped: {e}")
                overlapping_issues = []
            
            broken_assets = broken_images + broken_links + overlapping_issues
            
        else:
            # Default to broken_links
            store.save_job(job_id, {"step": "Checking images & icons...", "progress": 20})
            img_crawler = ImageIconCrawler(stage_url)
            broken_images = img_crawler.run()
            
            store.save_job(job_id, {"step": "Checking links...", "progress": 50})
            link_crawler = LinkCrawler(stage_url)
            broken_links = link_crawler.run()
            
            broken_assets = broken_images + broken_links
        
        store.save_job(job_id, {"step": "Generating report...", "progress": 90})
        
        report_path = generate_excel_report(broken_assets, job_id, job_dir)
        
        final_result = {
            "broken_count": len(broken_assets),
            "report_url": f"/download/{job_id}/{os.path.basename(report_path)}" if report_path else None
        }
        
        store.save_job(job_id, {
            "result": final_result,
            "status": "completed",
            "progress": 100,
            "step": "Done"
        })
        
    except Exception as e:
        store.save_job(job_id, {"status": "failed", "error": str(e)})


@app.get("/api/broken-links/history")
def get_broken_links_history():
    jobs = store.list_jobs()
    # Filter only broken_links jobs (and legacy comprehensive_audit)
    broken_links_jobs = [j for j in jobs if j.get("type") in ["broken_links", "comprehensive_audit"]]
    
    # Pagination
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        page = 1
        limit = 10

    if page < 1: page = 1
    if limit < 1: limit = 10

    start = (page - 1) * limit
    end = start + limit
    
    paginated_jobs = broken_links_jobs[start:end]
    
    return jsonify({
        "jobs": paginated_jobs,
        "total": len(broken_links_jobs),
        "page": page,
        "limit": limit
    })


@app.delete("/api/broken-links/history")
def delete_broken_links_history():
    data = request.get_json()
    job_ids = data.get("job_ids", [])
    
    if not job_ids:
        return jsonify({"error": "No job IDs provided"}), 400
    
    for job_id in job_ids:
        store.delete_job(job_id)
        # Also delete the job directory
        job_dir = os.path.join(RUNS_DIR, job_id)
        if os.path.exists(job_dir):
            import shutil
            shutil.rmtree(job_dir)
    
    return jsonify({"message": f"Deleted {len(job_ids)} job(s)"}), 200



def process_comparison(job_id, figma_path, stage_url, viewport, fullpage, threshold, noise_tolerance, job_dir, ignore_selectors_str="", wait_time=1000, highlight_diffs=True, pixel_threshold=None, component_selector=None, check_layout=True, check_content=True, check_colors=True, remove_selectors_str="", max_capture_height=None):
    try:
        # 1) Screenshot
        store.save_job(job_id, {"step": "Capturing screenshot...", "progress": 10})
        
        # Parse masks (hide elements - visibility:hidden)
        mask_selectors = []
        if ignore_selectors_str:
            # Handle comma or newline separated
            import re
            parts = re.split(r'[,\n\r]+', ignore_selectors_str)
            mask_selectors = [p.strip() for p in parts if p.strip()]

        # Parse remove selectors (completely remove from DOM - display:none)
        remove_sels = []
        if remove_selectors_str:
            import re
            parts = re.split(r'[,\n\r]+', remove_selectors_str)
            remove_sels = [p.strip() for p in parts if p.strip()]

        stage_path = os.path.join(job_dir, "stage.png")
        try:
            capture_screenshot(stage_url, stage_path, 
                              viewport=viewport, 
                              fullpage=fullpage, 
                              mask_selectors=mask_selectors,
                              wait_time=wait_time,
                              selector=component_selector,
                              remove_selectors=remove_sels,
                              max_height=max_capture_height)
        except Exception as e:
            raise Exception(f"Screenshot failed: {e}")
        
        store.save_job(job_id, {"step": "Aligning & Comparing images...", "progress": 50})

        # 2) Compare
        try:
            result = compare_images(figma_path, stage_path, job_dir, noise_tolerance=noise_tolerance, highlight_diffs=highlight_diffs, pixel_threshold=pixel_threshold, check_layout=check_layout, check_content=check_content, check_colors=check_colors)
        except Exception as e:
            raise Exception(f"Comparison failed: {e}")
            
        store.save_job(job_id, {"step": "Generating report...", "progress": 80})

        # 3) Report
        try:
            pdf_path = os.path.join(job_dir, "report.pdf")
            build_pdf_report(
                pdf_path=pdf_path,
                job_id=job_id,
                stage_url=stage_url,
                metrics=result,
                figma_path=figma_path
            )
        except Exception as e:
            raise Exception(f"Report failed: {e}")

        passed = result["ssim"] >= threshold and result["change_ratio"] <= 0.05
        
        final_result = {
            "job_id": job_id,
            "passed": passed,
            "metrics": {
                "ssim": result["ssim"],
                "change_ratio": result["change_ratio"],
                "num_regions": result["num_regions"],
                "issues": result["issues"]
            },
            "outputs": {
                "diff_overlay": f"/download/{job_id}/diff_overlay.png",
                "diff_heatmap": f"/download/{job_id}/diff_heatmap.png",
                "aligned_stage": f"/download/{job_id}/stage_aligned.png",
                "report_pdf": f"/download/{job_id}/report.pdf",
                "figma_png": f"/download/{job_id}/figma.png"
            }
        }

        store.save_job(job_id, {
            "result": final_result,
            "progress": 100,
            "step": "Done",
            "status": "completed"
        })

    except Exception as e:
        store.save_job(job_id, {"status": "failed", "error": str(e)})


@app.get("/api/status/<job_id>")
def get_status(job_id):
    job = store.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.post("/api/job/<job_id>/approve")
def approve_job(job_id):
    job = store.get_job(job_id)
    if not job: return jsonify({"error": "Job not found"}), 404
    
    # Store approval status
    store.save_job(job_id, {"approved": True, "reviewed_at": datetime.datetime.utcnow().isoformat()})
    
    # Also Promote to Baseline
    # We need the job data to know where the stage image is
    job_dir = os.path.join(RUNS_DIR, job_id)
    stage_path = os.path.join(job_dir, "stage.png")
    
    # We need the original stage URL from the job
    # But job object from store might not have clean URL if it was just an adhoc run
    # Let's check job_data
    if os.path.exists(stage_path):
        # We need to find the URL this run was for.
        # It's recorded in the job report usually but maybe not in store metadata explicitly if not added
        # compare_images stores result in job_dir but we need URL
        # Let's look at get_job
        # Wait, compare() saves to store: "stage_url" is NOT saved in initial job_data in compare()!
        # It is passed to process_comparison but not saved to store initially.
        # But report building uses it.
        # Let's fix compare() to save stage_url to job_id so we can retrieve it here.
        # For now, we'll try to guess or rely on it being there if I add it.
        # EDIT: I will add stage_url to job_data in compare() in a separate chunk.
        pass

    return jsonify({"success": True, "approved": True})

@app.post("/api/baselines/promote/<job_id>")
def promote_baseline(job_id):
    job = store.get_job(job_id)
    if not job: return jsonify({"error": "Job not found"}), 404
    
    stage_url = job.get("stage_url")
    if not stage_url:
        return jsonify({"error": "Job does not have a stage_url recorded."}), 400
        
    job_dir = os.path.join(RUNS_DIR, job_id)
    # Use figma.png (the reference/uploaded file) as the new baseline source
    figma_path = os.path.join(job_dir, "figma.png")
    
    if not os.path.exists(figma_path):
        return jsonify({"error": "Reference image (figma.png) missing."}), 404
        
    version_id = baseline_store.add_baseline(stage_url, job_id, figma_path)
    
    # Also mark the job as approved since it is now the baseline
    store.save_job(job_id, {"approved": True, "reviewed_at": datetime.datetime.utcnow().isoformat()})

    if not version_id:
         return jsonify({"success": True, "message": "Baseline already up to date.", "version_id": "current"})
    
    return jsonify({"success": True, "version_id": version_id})

@app.get("/api/baselines")
def list_baselines():
    return jsonify(baseline_store.get_all_baselines())


@app.post("/api/baselines/rollback")
def rollback_baseline():
    data = request.json
    url = data.get("url")
    version_id = data.get("version_id")
    
    if not url or not version_id:
        return jsonify({"error": "Missing url or version_id"}), 400
        
    success = baseline_store.rollback(url, version_id)
    if success:
         return jsonify({"success": True})
    return jsonify({"error": "Rollback failed"}), 400


@app.post("/api/job/<job_id>/reject")
def reject_job(job_id):
    job = store.get_job(job_id)
    if not job: return jsonify({"error": "Job not found"}), 404
    
    # Store rejection status
    store.save_job(job_id, {"approved": False, "reviewed_at": datetime.datetime.utcnow().isoformat()})
    return jsonify({"success": True, "approved": False})

@app.get("/api/history")
def get_history():
    jobs = store.list_jobs()
    # Filter only visual_testing jobs (exclude broken_links, accessibility, seo_performance)
    visual_testing_jobs = [j for j in jobs if j.get("type") == "visual_testing"]
    
    # Sort by timestamp (newest first)
    visual_testing_jobs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Filter by approval status if requested
    filter_status = request.args.get("filter", "all")
    if filter_status == "pending":
        visual_testing_jobs = [j for j in visual_testing_jobs if j.get("approved") is None]
    elif filter_status == "approved":
        visual_testing_jobs = [j for j in visual_testing_jobs if j.get("approved") is True]
    elif filter_status == "rejected":
        visual_testing_jobs = [j for j in visual_testing_jobs if j.get("approved") is False]
    
    # Pagination
    try:
        page = int(request.args.get("page", 1))

        limit = int(request.args.get("limit", 10))
    except ValueError:
        page = 1
        limit = 10

    if page < 1: page = 1
    if limit < 1: limit = 10

    start = (page - 1) * limit
    end = start + limit
    
    paginated_jobs = visual_testing_jobs[start:end]
    
    return jsonify({
        "jobs": paginated_jobs,
        "total": len(visual_testing_jobs),
        "page": page,
        "limit": limit
    })





@app.get("/download/<job_id>/<filename>")
def download(job_id, filename):
    job_dir = os.path.join(RUNS_DIR, secure_filename(job_id))
    file_path = os.path.join(job_dir, secure_filename(filename))
    if not os.path.exists(file_path):
        return jsonify({"error": "Not found"}), 404
    # Serve inline so <img src> previews work; UI uses download attribute for saving
    return send_file(file_path, as_attachment=False)

@app.get("/api/baselines/image/<filename>")
def get_baseline_image(filename):
    path = baseline_store.get_baseline_path(secure_filename(filename))
    if not path:
        return jsonify({"error": "Image not found"}), 404
    return send_file(path)

@app.post("/api/baselines/delete")

def delete_baseline_api(): # Rename to avoid conflict if any
    data = request.json
    url = data.get("url")
    if not url: return jsonify({"error": "Missing URL"}), 400
    
    if baseline_store.delete_baseline(url):
        return jsonify({"success": True})
    return jsonify({"error": "Baseline not found"}), 404

@app.post("/api/baselines/upload")
def upload_baseline_api():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    url = request.form.get("url")
    
    if not url:
        return jsonify({"error": "Missing URL"}), 400
        
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        # Create a pseudo-job or just mark as manual
        version_id = baseline_store.add_baseline_from_file(url, file)
        return jsonify({"success": True, "version_id": version_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/")

def index():
    return app.send_static_file("index.html")

@app.get("/broken-links")
def broken_links_page():
    return app.send_static_file("broken_links.html")

@app.get("/accessibility")
def accessibility_page():
    return app.send_static_file("accessibility.html")



@app.post("/api/accessibility")
def run_accessibility_test():
    data = request.get_json()
    input_type = data.get("input_type", "url")
    page_url = data.get("page_url")
    sitemap_url = data.get("sitemap_url")
    wcag_level = data.get("wcag_level", "WCAG2AA")
    
    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(RUNS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    if input_type == "sitemap" and sitemap_url:
        target_url = sitemap_url
        job_type = "accessibility_sitemap"
        target_func = process_accessibility_sitemap
        args = (job_id, sitemap_url, wcag_level, job_dir)
    elif page_url:
        target_url = page_url
        job_type = "accessibility"
        target_func = process_accessibility_test
        args = (job_id, page_url, wcag_level, job_dir)
    else:
        return jsonify({"error": "Valid URL or Sitemap URL is required"}), 400

    # Initialize job
    job_data = {
        "job_id": job_id,
        "type": job_type,
        "page_url": target_url,
        "wcag_level": wcag_level,
        "status": "running",
        "progress": 0,
        "step": "Starting accessibility test...",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "result": None
    }
    store.save_job(job_id, job_data)
    
    # Start thread
    thread = threading.Thread(target=target_func, args=args)
    thread.start()
    
    return jsonify({"job_id": job_id})


def analyze_page_accessibility(page_url):
    import requests
    from bs4 import BeautifulSoup
    
    # Fetch the page
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; VisualTestingBot/1.0)'}
    response = requests.get(page_url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    issues = []
    
    # Check 1: Images without alt text
    images = soup.find_all('img')
    for img in images:
        if not img.get('alt'):
            src = img.get('src', 'unknown')
            issues.append({
                "rule": "Missing alt text on image",
                "severity": "violation",
                "element": f"<img src='{src}'>",
                "description": "Images must have alternate text for screen readers",
                "impact": "Critical",
                "fix": f"Add alt attribute: <img src='{src}' alt='Descriptive text'>"
            })
    
    # Check 2: Form inputs without labels
    inputs = soup.find_all(['input', 'textarea', 'select'])
    for inp in inputs:
        input_type = inp.get('type', 'text')
        if input_type not in ['hidden', 'submit', 'button']:
            input_id = inp.get('id')
            input_name = inp.get('name', 'unknown')
            
            # Check if there's an associated label
            has_label = False
            if input_id:
                label = soup.find('label', {'for': input_id})
                if label:
                    has_label = True
            
            # Check if input is wrapped in label
            if not has_label and inp.parent and inp.parent.name == 'label':
                has_label = True
            
            # Check for aria-label
            if not has_label and inp.get('aria-label'):
                has_label = True
            
            if not has_label:
                issues.append({
                    "rule": "Form input missing label",
                    "severity": "violation",
                    "element": f"<input type='{input_type}' name='{input_name}'>",
                    "description": "Form elements must have associated labels",
                    "impact": "Critical",
                    "fix": f"Add <label for='{input_name}'>Label text:</label> before the input"
                })
    
    # Check 3: Missing page title
    title = soup.find('title')
    if not title or not title.string or len(title.string.strip()) == 0:
        issues.append({
            "rule": "Missing or empty page title",
            "severity": "violation",
            "element": "<title></title>",
            "description": "Pages must have a descriptive title",
            "impact": "Serious",
            "fix": "Add <title>Descriptive Page Title</title> in the <head> section"
        })
    
    # Check 4: Missing lang attribute
    html_tag = soup.find('html')
    if html_tag and not html_tag.get('lang'):
        issues.append({
            "rule": "Missing language attribute",
            "severity": "violation",
            "element": "<html>",
            "description": "HTML element must have a lang attribute",
            "impact": "Serious",
            "fix": "Add lang attribute: <html lang='en'>"
        })
    
    # Check 5: Heading hierarchy
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    h1_count = len(soup.find_all('h1'))
    
    if h1_count == 0:
        issues.append({
            "rule": "Missing H1 heading",
            "severity": "warning",
            "element": "N/A",
            "description": "Page should have exactly one H1 heading",
            "impact": "Moderate",
            "fix": "Add a single <h1> heading that describes the main content"
        })
    elif h1_count > 1:
        issues.append({
            "rule": "Multiple H1 headings",
            "severity": "warning",
            "element": f"{h1_count} H1 tags found",
            "description": "Page should have only one H1 heading",
            "impact": "Moderate",
            "fix": "Use only one <h1> and use <h2>, <h3> for subheadings"
        })
    
    # Check for skipped heading levels
    heading_levels = [int(h.name[1]) for h in headings]
    for i in range(len(heading_levels) - 1):
        if heading_levels[i+1] - heading_levels[i] > 1:
            issues.append({
                "rule": "Skipped heading level",
                "severity": "warning",
                "element": f"<h{heading_levels[i]}> followed by <h{heading_levels[i+1]}>",
                "description": "Heading levels should not be skipped",
                "impact": "Moderate",
                "fix": "Use heading levels in sequential order (h1, h2, h3, etc.)"
            })
            break
    
    # Check 6: Links with non-descriptive text
    links = soup.find_all('a', href=True)
    non_descriptive_texts = ['click here', 'read more', 'more', 'link', 'here']
    for link in links:
        link_text = link.get_text().strip().lower()
        if link_text in non_descriptive_texts:
            issues.append({
                "rule": "Non-descriptive link text",
                "severity": "warning",
                "element": f"<a href='{link.get('href', '')}'>{link_text}</a>",
                "description": "Link text should describe the destination",
                "impact": "Moderate",
                "fix": "Use descriptive text like 'Read more about [topic]' instead of 'Click here'"
            })
    
    # Check 7: Buttons without accessible names
    buttons = soup.find_all('button')
    for button in buttons:
        button_text = button.get_text().strip()
        aria_label = button.get('aria-label', '').strip()
        
        if not button_text and not aria_label:
            issues.append({
                "rule": "Button without accessible name",
                "severity": "violation",
                "element": str(button),
                "description": "Buttons must have accessible text or aria-label",
                "impact": "Critical",
                "fix": "Add text inside button or aria-label attribute"
            })
    
    # Check 8: Missing meta viewport for mobile
    viewport = soup.find('meta', {'name': 'viewport'})
    if not viewport:
        issues.append({
            "rule": "Missing viewport meta tag",
            "severity": "warning",
            "element": "<head>",
            "description": "Page should include viewport meta tag for mobile responsiveness",
            "impact": "Moderate",
            "fix": "Add <meta name='viewport' content='width=device-width, initial-scale=1'> in <head>"
        })

    return issues

def process_accessibility_test(job_id, page_url, wcag_level, job_dir):
    try:
        store.save_job(job_id, {"step": "Analyzing accessibility...", "progress": 20})
        
        issues = analyze_page_accessibility(page_url)
        
        store.save_job(job_id, {"step": "Counting issues...", "progress": 70})
        
        violations = sum(1 for i in issues if i.get('severity') == 'violation')
        warnings = sum(1 for i in issues if i.get('severity') == 'warning')
        notices = sum(1 for i in issues if i.get('severity') == 'notice')
        
        store.save_job(job_id, {"step": "Generating PDF report...", "progress": 85})
        
        # Generate PDF report
        from utils.accessibility_report import generate_accessibility_pdf
        report_path = generate_accessibility_pdf(issues, page_url, wcag_level, job_id, job_dir)
        
        final_result = {
            "total_issues": len(issues),
            "violations": violations,
            "warnings": warnings,
            "notices": notices,
            "report_url": f"/download/{job_id}/{os.path.basename(report_path)}"
        }
        
        store.save_job(job_id, {
            "result": final_result,
            "status": "completed",
            "progress": 100,
            "step": "Done"
        })
        
    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        store.save_job(job_id, {"status": "failed", "error": error_details})

def process_accessibility_sitemap(job_id, sitemap_url, wcag_level, job_dir):
    try:
        from utils.sitemap_parser import fetch_sitemap_urls
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        store.save_job(job_id, {"step": "Fetching sitemap URLs...", "progress": 5})
        
        urls = list(fetch_sitemap_urls(sitemap_url))
        if not urls:
            raise Exception("No URLs found in sitemap")
            
        # Limit to 50 pages for performance safety
        urls = urls[:50]
        total_pages = len(urls)
        
        store.save_job(job_id, {"step": f"Found {total_pages} pages. Analyzing...", "progress": 10})
        
        all_issues = []
        completed = 0
        
        # Determine strict or lenient timeout based on page count
        # Use 5 workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(analyze_page_accessibility, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    page_issues = future.result()
                    # Tag issues with URL
                    for issue in page_issues:
                        issue['page_url'] = url
                    all_issues.extend(page_issues)
                except Exception as e:
                    print(f"Failed to analyze {url}: {e}")
                
                completed += 1
                progress = 10 + int((completed / total_pages) * 80)
                store.save_job(job_id, {"step": f"Analyzed {completed}/{total_pages} pages...", "progress": progress})

        store.save_job(job_id, {"step": "Generating Combined Report...", "progress": 90})
        
        violations = sum(1 for i in all_issues if i.get('severity') == 'violation')
        warnings = sum(1 for i in all_issues if i.get('severity') == 'warning')
        notices = sum(1 for i in all_issues if i.get('severity') == 'notice')

        # Generate PDF report (needs update to handle page_url per issue)
        from utils.accessibility_report import generate_accessibility_pdf
        report_path = generate_accessibility_pdf(all_issues, sitemap_url, wcag_level, job_id, job_dir)
        
        final_result = {
            "total_issues": len(all_issues),
            "violations": violations,
            "warnings": warnings,
            "notices": notices,
            "report_url": f"/download/{job_id}/{os.path.basename(report_path)}"
        }
        
        store.save_job(job_id, {
            "result": final_result,
            "status": "completed",
            "progress": 100,
            "step": "Done"
        })
        
    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        store.save_job(job_id, {"status": "failed", "error": error_details})



@app.get("/api/accessibility/history")
def get_accessibility_history():
    jobs = store.list_jobs()
    # Include sitemap jobs
    accessibility_jobs = [j for j in jobs if j.get("type") in ["accessibility", "accessibility_sitemap"]]
    
    # Pagination
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        page = 1
        limit = 10

    if page < 1: page = 1
    if limit < 1: limit = 10

    start = (page - 1) * limit
    end = start + limit
    
    paginated_jobs = accessibility_jobs[start:end]
    
    return jsonify({
        "jobs": paginated_jobs,
        "total": len(accessibility_jobs),
        "page": page,
        "limit": limit
    })


@app.delete("/api/accessibility/history")
def delete_accessibility_history():
    data = request.get_json()
    job_ids = data.get("job_ids", [])
    
    if not job_ids:
        return jsonify({"error": "No job IDs provided"}), 400
    
    for job_id in job_ids:
        store.delete_job(job_id)
        job_dir = os.path.join(RUNS_DIR, job_id)
        if os.path.exists(job_dir):
            import shutil
            shutil.rmtree(job_dir)
    
    return jsonify({"message": f"Deleted {len(job_ids)} job(s)"}), 200


@app.get("/seo-performance")
def seo_performance_page():
    return app.send_static_file("seo_performance.html")


@app.post("/api/seo-performance")
def run_seo_performance_test():
    # Handle both JSON (legacy/API) and FormData (new Browser UI)
    if request.content_type and request.content_type.startswith('application/json'):
        data = request.get_json()
        page_url = data.get("page_url")
        sitemap_url = data.get("sitemap_url")
        test_type = data.get("test_type", "both")
        device_type = data.get("device_type", "desktop")
        api_key = data.get("api_key", "").strip() or None
        file = None
    else:
        # FormData
        page_url = request.form.get("page_url")
        test_type = request.form.get("test_type", "both")
        device_type = request.form.get("device_type", "desktop")
        api_key = request.form.get("api_key", "").strip() or None
        api_key = request.form.get("api_key", "").strip() or None
        file = request.files.get("file")
        sitemap_url = request.form.get("sitemap_url")

    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(RUNS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(job_dir, filename)
        file.save(file_path)
        
        job_data = {
            "job_id": job_id,
            "type": "seo_performance",
            "input_type": "batch",
            "test_type": test_type,
            "device_type": device_type,
            "status": "running",
            "progress": 0,
            "step": "Starting batch analysis...",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "result": None
        }
        store.save_job(job_id, job_data)
        
        thread = threading.Thread(target=process_seo_performance_batch, 
                                 args=(job_id, file_path, test_type, device_type, job_dir, api_key))
        thread.start()
        
    elif sitemap_url:
        job_data = {
            "job_id": job_id,
            "type": "seo_performance",
            "input_type": "batch",  # Treat as batch for UI consistency
            "page_url": sitemap_url, # Store sitemap URL for reference
            "test_type": test_type,
            "device_type": device_type,
            "status": "running",
            "progress": 0,
            "step": "Fetching sitemap URLs...",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "result": None
        }
        store.save_job(job_id, job_data)
        
        thread = threading.Thread(target=process_seo_performance_sitemap, 
                                 args=(job_id, sitemap_url, test_type, device_type, job_dir, api_key))
        thread.start()

    elif page_url:
        job_data = {
            "job_id": job_id,
            "type": "seo_performance",
            "page_url": page_url,
            "test_type": test_type,
            "device_type": device_type,
            "status": "running",
            "progress": 0,
            "step": "Starting SEO & Performance test...",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "result": None
        }
        store.save_job(job_id, job_data)
        
        thread = threading.Thread(target=process_seo_performance_test, 
                                 args=(job_id, page_url, test_type, device_type, job_dir, api_key))
        thread.start()
    else:
         return jsonify({"error": "Page URL, Sitemap URL, or File upload is required"}), 400

    return jsonify({"job_id": job_id})


PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", "AIzaSyCETduV3lTJKEGn_JTjfXDuN5ZH19fMrtw") # Use env var or provided default

def process_seo_performance_test(job_id, page_url, test_type, device_type, job_dir, api_key=None):
    try:
        from utils.pagespeed import PageSpeedInsights
        
        store.save_job(job_id, {"step": "Connecting to PageSpeed Insights...", "progress": 10})
        
        # Initialize PageSpeed Insights API
        # Use user-provided key, or fallback to global/env key
        key_to_use = api_key or PAGESPEED_API_KEY
        psi = PageSpeedInsights(api_key=key_to_use)
        
        # Determine which categories to analyze
        categories = []
        if test_type in ['both', 'seo']:
            categories.extend(['seo', 'accessibility', 'best-practices'])
        if test_type in ['both', 'performance']:
            categories.append('performance')
        
        # If no specific type, analyze all
        if not categories:
            categories = ['performance', 'seo', 'accessibility', 'best-practices']
        
        store.save_job(job_id, {"step": f"Running PageSpeed analysis ({device_type})...", "progress": 30})
        
        # Run PageSpeed Insights analysis
        strategy = 'mobile' if device_type == 'mobile' else 'desktop'
        metrics = psi.analyze(page_url, strategy=strategy, categories=categories)
        
        store.save_job(job_id, {"step": "Processing results...", "progress": 70})
        
        # Ensure we have the required fields based on test_type
        if test_type == 'seo' and 'performance_score' not in metrics:
            metrics['performance_score'] = None
            metrics['load_time'] = None
            metrics['performance_details'] = []
        
        if test_type == 'performance' and 'seo_score' not in metrics:
            metrics['seo_score'] = None
            metrics['seo_details'] = []
        
        store.save_job(job_id, {"step": "Generating PDF report...", "progress": 85})
        
        # Generate PDF report
        from utils.seo_performance_report import generate_seo_performance_pdf
        report_path = generate_seo_performance_pdf(metrics, page_url, test_type, device_type, job_id, job_dir)
        
        final_result = {
            "seo_score": metrics.get('seo_score'),
            "performance_score": metrics.get('performance_score'),
            "load_time": metrics.get('load_time'),
            "performance_details": metrics.get('performance_details', []),
            "recommendations": metrics.get('recommendations', []),
            "report_url": f"/download/{job_id}/{os.path.basename(report_path)}"
        }
        
        store.save_job(job_id, {
            "result": final_result,
            "status": "completed",
            "progress": 100,
            "step": "Done"
        })
        
    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        store.save_job(job_id, {"status": "failed", "error": error_details})


def process_seo_performance_batch(job_id, file_path, test_type, device_type, job_dir, api_key=None):
    import pandas as pd
    from utils.pagespeed import PageSpeedInsights
    import traceback

    try:
        store.save_job(job_id, {"step": "Reading file...", "progress": 5})
        
        # Read Excel or CSV
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Find URL column
        url_col = None
        for col in df.columns:
            if "url" in str(col).lower() or "link" in str(col).lower() or "website" in str(col).lower():
                url_col = col
                break
        if not url_col:
            # Fallback: assume first column
            url_col = df.columns[0]
            
        urls = df[url_col].dropna().tolist()
        total_urls = len(urls)
        
        if total_urls == 0:
            raise Exception("No URLs found in the file.")
            
        store.save_job(job_id, {"step": f"Found {total_urls} URLs to process...", "progress": 10})
        
        key_to_use = api_key or PAGESPEED_API_KEY
        psi = PageSpeedInsights(api_key=key_to_use)
        
        # Determine categories
        categories = []
        if test_type in ['both', 'seo']:
            categories.extend(['seo', 'accessibility', 'best-practices'])
        if test_type in ['both', 'performance']:
            categories.append('performance')
        if not categories:
            categories = ['performance', 'seo', 'accessibility', 'best-practices']
            
        strategy = 'mobile' if device_type == 'mobile' else 'desktop'
        results = []
        
        for i, url in enumerate(urls):
            current_progress = 10 + int(((i) / total_urls) * 80)
            store.save_job(job_id, {"step": f"Analyzing {i+1}/{total_urls}: {url}", "progress": current_progress})
            
            try:
                # Basic validation
                if not url.startswith('http'):
                    # Try to prepend https if missing, or skip
                    if not url.startswith('www'):
                         results.append({
                            "URL": url,
                            "Status": "Skipped (Invalid URL)",
                            "Error": "URL must start with http/https"
                        })
                         continue
                    else:
                        url = "https://" + url
                    
                metrics = psi.analyze(url, strategy=strategy, categories=categories)
                
                row = {
                    "URL": url,
                    "Status": "Success",
                    "SEO Score": metrics.get('seo_score', 'N/A'),
                    "Performance Score": metrics.get('performance_score', 'N/A'),
                    "Load Time (s)": metrics.get('load_time', 'N/A'),
                    "First Contentful Paint": next((audit['displayValue'] for audit in metrics.get('performance_details', []) if audit['id'] == 'first-contentful-paint'), 'N/A'),
                    "Largest Contentful Paint": next((audit['displayValue'] for audit in metrics.get('performance_details', []) if audit['id'] == 'largest-contentful-paint'), 'N/A'),
                    "Cumulative Layout Shift": next((audit['displayValue'] for audit in metrics.get('performance_details', []) if audit['id'] == 'cumulative-layout-shift'), 'N/A'),
                    "Time to First Byte": next((audit['displayValue'] for audit in metrics.get('performance_details', []) if audit['id'] == 'server-response-time'), 'N/A'),
                    "First Input Delay": next((audit['displayValue'] for audit in metrics.get('performance_details', []) if audit['id'] == 'first-input-delay'), 'N/A'),
                }
                results.append(row)
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results.append({
                    "URL": url,
                    "Status": "Failed",
                    "Error": str(e)
                })
                
        store.save_job(job_id, {"step": "Generating consolidated report...", "progress": 95})
        
        # Create Excel Report
        report_df = pd.DataFrame(results)
        report_filename = f"seo_performance_report_{job_id}.xlsx"
        report_path = os.path.join(job_dir, report_filename)
        report_df.to_excel(report_path, index=False)
        
        final_result = {
            "total_processed": total_urls,
            "report_url": f"/download/{job_id}/{report_filename}"
        }
        
        store.save_job(job_id, {
            "result": final_result,
            "status": "completed",
            "progress": 100,
            "step": "Done"
        })

    except Exception as e:
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        store.save_job(job_id, {"status": "failed", "error": error_details})

def analyze_single_url_psi(url, psi, strategy, categories):
    try:
        if not url.startswith('http'):
            if not url.startswith('www'):
                 return {
                    "URL": url,
                    "Status": "Skipped (Invalid URL)",
                    "Error": "URL must start with http/https"
                }
            else:
                url = "https://" + url
            
        metrics = psi.analyze(url, strategy=strategy, categories=categories)
        
        return {
            "URL": url,
            "Status": "Success",
            "Performance Score": metrics.get('performance_score', 'N/A'),
            "Accessibility Score": metrics.get('accessibility_score', 'N/A'),
            "Best Practices Score": metrics.get('best_practices_score', 'N/A'),
            "Load Time (s)": metrics.get('load_time', 'N/A'),
            "First Contentful Paint": next((d['displayValue'] for d in metrics.get('performance_details', []) if d.get('id') == 'first-contentful-paint'), 'N/A'),
            "Largest Contentful Paint": next((d['displayValue'] for d in metrics.get('performance_details', []) if d.get('id') == 'largest-contentful-paint'), 'N/A'),
            "Cumulative Layout Shift": next((d['displayValue'] for d in metrics.get('performance_details', []) if d.get('id') == 'cumulative-layout-shift'), 'N/A'),
            "Time to First Byte": next((d['displayValue'] for d in metrics.get('performance_details', []) if d.get('id') == 'server-response-time'), 'N/A'),
            "First Input Delay": next((d['displayValue'] for d in metrics.get('performance_details', []) if d.get('id') == 'first-input-delay'), 'N/A'),
        }
    except Exception as e:
        return {
            "URL": url,
            "Status": "Failed",
            "Error": str(e)
        }

def process_seo_performance_batch(job_id, file_path, test_type, device_type, job_dir, api_key=None):
    import pandas as pd
    from utils.pagespeed import PageSpeedInsights
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import traceback

    try:
        store.save_job(job_id, {"step": "Reading file...", "progress": 5})
        
        # Read Excel or CSV
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Find URL column
        url_col = None
        for col in df.columns:
            if "url" in str(col).lower() or "link" in str(col).lower() or "website" in str(col).lower():
                url_col = col
                break
        if not url_col:
            # Fallback: assume first column
            url_col = df.columns[0]
            
        urls = df[url_col].dropna().tolist()
        total_urls = len(urls)
        
        if total_urls == 0:
            raise Exception("No URLs found in the file.")
            
        store.save_job(job_id, {"step": f"Found {total_urls} URLs to process...", "progress": 10})
        
        key_to_use = api_key or PAGESPEED_API_KEY
        psi = PageSpeedInsights(api_key=key_to_use)
        
        # Determine categories
        categories = []
        if test_type in ['both', 'seo']:
            categories.extend(['seo', 'accessibility', 'best-practices'])
        if test_type in ['both', 'performance']:
            categories.append('performance')
        if not categories:
            categories = ['performance', 'seo', 'accessibility', 'best-practices']
            
        strategy = 'mobile' if device_type == 'mobile' else 'desktop'
        results = []
        completed = 0
        
        # Process in parallel (max 3 workers to avoid strict rate limits if no API key)
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(analyze_single_url_psi, url, psi, strategy, categories): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    results.append({"URL": url, "Status": "System Error", "Error": str(e)})
                
                completed += 1
                current_progress = 10 + int((completed / total_urls) * 85)
                store.save_job(job_id, {"step": f"Analyzed {completed}/{total_urls}: {url}", "progress": current_progress})

        store.save_job(job_id, {"step": "Generating consolidated report...", "progress": 98})
        
        # Create Excel Report
        # Create Excel Report
        report_df = pd.DataFrame(results)
        report_filename = f"seo_performance_report_{job_id}.xlsx"
        report_path = os.path.join(job_dir, report_filename)
        report_df.to_excel(report_path, index=False)
        
        # Create PDF Report
        from utils.seo_performance_report import generate_batch_seo_pdf
        pdf_path = generate_batch_seo_pdf(results, job_id, job_dir)

        final_result = {
            "total_processed": total_urls,
            "report_url": f"/download/{job_id}/{report_filename}",
            "pdf_report_url": f"/download/{job_id}/{os.path.basename(pdf_path)}"
        }
        
        store.save_job(job_id, {
            "result": final_result,
            "status": "completed",
            "progress": 100,
            "step": "Done"
        })

    except Exception as e:
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        store.save_job(job_id, {"status": "failed", "error": error_details})


def process_seo_performance_sitemap(job_id, sitemap_url, test_type, device_type, job_dir, api_key=None):
    from utils.sitemap_parser import fetch_sitemap_urls
    from utils.pagespeed import PageSpeedInsights
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import traceback

    try:
        store.save_job(job_id, {"step": "Fetching sitemap URLs...", "progress": 5})
        
        urls = list(fetch_sitemap_urls(sitemap_url))
        if not urls:
            raise Exception("No URLs found in sitemap")
            
        # Limit processed pages
        urls = urls[:200]
        total_urls = len(urls)
        
        store.save_job(job_id, {"step": f"Found {total_urls} URLs to process...", "progress": 10})
        
        key_to_use = api_key or PAGESPEED_API_KEY
        psi = PageSpeedInsights(api_key=key_to_use)
        
        # Determine categories
        categories = []
        if test_type in ['both', 'seo']:
            categories.extend(['seo', 'accessibility', 'best-practices'])
        if test_type in ['both', 'performance']:
            categories.append('performance')
        if not categories:
            categories = ['performance', 'seo', 'accessibility', 'best-practices']
            
        strategy = 'mobile' if device_type == 'mobile' else 'desktop'
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(analyze_single_url_psi, url, psi, strategy, categories): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    results.append({"URL": url, "Status": "System Error", "Error": str(e)})
                    
                completed += 1
                current_progress = 10 + int((completed / total_urls) * 85)
                store.save_job(job_id, {"step": f"Analyzed {completed}/{total_urls}: {url}", "progress": current_progress})

        store.save_job(job_id, {"step": "Generating consolidated report...", "progress": 98})
        
        # Create Excel Report
        # Create Excel Report
        report_df = pd.DataFrame(results)
        report_filename = f"seo_performance_report_{job_id}.xlsx"
        report_path = os.path.join(job_dir, report_filename)
        report_df.to_excel(report_path, index=False)
        
        # Create PDF Report
        from utils.seo_performance_report import generate_batch_seo_pdf
        pdf_path = generate_batch_seo_pdf(results, job_id, job_dir)

        final_result = {
            "total_processed": total_urls,
            "report_url": f"/download/{job_id}/{report_filename}",
            "pdf_report_url": f"/download/{job_id}/{os.path.basename(pdf_path)}"
        }
        
        store.save_job(job_id, {
            "result": final_result,
            "status": "completed",
            "progress": 100,
            "step": "Done"
        })

    except Exception as e:
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        store.save_job(job_id, {"status": "failed", "error": error_details})


@app.get("/api/seo-performance/history")
def get_seo_performance_history():
    jobs = store.list_jobs()
    seo_perf_jobs = [j for j in jobs if j.get("type") == "seo_performance"]
    
    # Pagination
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        page = 1
        limit = 10

    if page < 1: page = 1
    if limit < 1: limit = 10

    start = (page - 1) * limit
    end = start + limit
    
    paginated_jobs = seo_perf_jobs[start:end]
    
    return jsonify({
        "jobs": paginated_jobs,
        "total": len(seo_perf_jobs),
        "page": page,
        "limit": limit
    })


@app.delete("/api/seo-performance/history")
def delete_seo_performance_history():
    data = request.get_json()
    job_ids = data.get("job_ids", [])
    
    if not job_ids:
        return jsonify({"error": "No job IDs provided"}), 400
    
    for job_id in job_ids:
        store.delete_job(job_id)
        job_dir = os.path.join(RUNS_DIR, job_id)
        if os.path.exists(job_dir):
            import shutil
            shutil.rmtree(job_dir)
    
    return jsonify({"message": f"Deleted {len(job_ids)} job(s)"}), 200



# Jira Integration Routes

@app.post("/api/jira/config")
def save_jira_config():
    data = request.json
    server = data.get("server")
    email = data.get("email")
    token = data.get("token")
    project_key = data.get("project_key")

    if not all([server, email, token, project_key]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        # Test connection
        JiraClient(server, email, token)
        JiraClient.save_config(server, email, token, project_key)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/jira/config")
def get_jira_config():
    config = JiraClient.load_config()
    # Mask token for security
    if config.get("token"):
        config["token"] = "********"
    return jsonify(config)

@app.post("/api/jira/issue")
def create_issue():
    data = request.json
    summary = data.get("summary")
    description = data.get("description")
    job_id = data.get("job_id")  # Can be none
    issue_filename = data.get("issue_filename")  # Can be none
    
    config = JiraClient.load_config()
    if not config:
        return jsonify({"error": "Jira configuration not found. Please configure Jira first."}), 400

    attachment_path = None
    if job_id and issue_filename:
        # Check in job dir
        job_dir = os.path.join(RUNS_DIR, secure_filename(job_id))
        attachment_path = os.path.join(job_dir, secure_filename(issue_filename))
        if not os.path.exists(attachment_path):
            attachment_path = None

    try:
        client = JiraClient(config["server"], config["email"], config["token"])
        jira_issue = client.create_issue(
            project_key=config["project_key"],
            summary=summary,
            description=description,
            attachment_path=attachment_path
        )
        return jsonify({"success": True, "key": jira_issue["key"], "url": jira_issue["url"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GitHub Integration Routes

@app.post("/api/github/config")
def save_github_config():
    data = request.json
    token = data.get("token")
    owner = data.get("owner")
    repo = data.get("repo")

    if not all([token, owner, repo]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        # Test connection
        from utils.github_client import GitHubClient
        client = GitHubClient(token, owner, repo)
        client.verify_connection()
        GitHubClient.save_config(token, owner, repo)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/github/config")
def get_github_config():
    from utils.github_client import GitHubClient
    config = GitHubClient.load_config()
    # Mask token
    if config.get("token"):
        config["token"] = "********"
    return jsonify(config)

@app.post("/api/github/issue")
def create_github_issue():
    data = request.json
    title = data.get("title")
    body = data.get("body")
    job_id = data.get("job_id")
    issue_filename = data.get("issue_filename")  # Context only
    
    from utils.github_client import GitHubClient
    config = GitHubClient.load_config()
    if not config:
        return jsonify({"error": "GitHub configuration not found. Please configure GitHub first."}), 400

    try:
        client = GitHubClient(config["token"], config["owner"], config["repo"])
        
        # Append some context if available
        if job_id:
            body += f"\n\n**Visual Testing Context**\nJob ID: {job_id}"
        if issue_filename:
             body += f"\nFile: {issue_filename}"

        gh_issue = client.create_issue(
            title=title,
            body=body,
            labels=["visual-regression"]
        )
        return jsonify({"success": True, "number": gh_issue["number"], "url": gh_issue["html_url"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.post("/api/history/delete")
def delete_history():
    try:
        data = request.json
        job_ids = data.get("job_ids", [])
        if not job_ids:
            return jsonify({"error": "No job_ids provided"}), 400
            
        store.delete_jobs(job_ids)
        
        # Cleanup directories
        for job_id in job_ids:
            safe_id = secure_filename(job_id)
            job_dir = os.path.join(RUNS_DIR, safe_id)
            if os.path.exists(job_dir):
                import shutil
                try:
                    shutil.rmtree(job_dir)
                except Exception:
                    pass
                    
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def process_git_push(job_id, commit_message, branch):
    """Background thread for git push operations - Optimized for speed"""
    import subprocess
    
    project_dir = BASE_DIR
    
    # Prevent git from opening any editor or interactive prompt
    git_env = os.environ.copy()
    git_env["GIT_TERMINAL_PROMPT"] = "0"
    git_env["GIT_EDITOR"] = "true"
    git_env["GIT_COMMITTER_NAME"] = git_env.get("GIT_COMMITTER_NAME", "Visual Testing Tool")
    git_env["GIT_COMMITTER_EMAIL"] = git_env.get("GIT_COMMITTER_EMAIL", "vt@tool.local")
    
    try:
        # Update status: Staging (10%)
        store.update_job(job_id, {
            "status": "running",
            "progress": 10,
            "step": "Staging changes..."
        })
        
        # Stage all changes
        add_result = subprocess.run(
            ["git", "add", "."],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=15,
            env=git_env
        )
        
        if add_result.returncode != 0:
            store.update_job(job_id, {
                "status": "failed",
                "error": f"Failed to stage changes: {add_result.stderr}",
                "progress": 100
            })
            return
        
        # Update status: Committing (40%)
        store.update_job(job_id, {
            "progress": 40,
            "step": "Committing changes..."
        })
        
        # Check if there are changes to commit
        status_result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
            env=git_env
        )
        
        has_staged_changes = status_result.returncode != 0  # returncode 1 = has changes
        
        if has_staged_changes:
            # Commit changes (with --no-edit to prevent editor from opening)
            commit_result = subprocess.run(
                ["git", "commit", "--no-edit", "-m", commit_message],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=15,
                env=git_env
            )
            
            if commit_result.returncode != 0:
                # Check if error is "nothing to commit"
                combined = commit_result.stdout + commit_result.stderr
                if "nothing to commit" in combined or "nothing added to commit" in combined:
                    pass  # Fall through to push — there may be unpushed commits
                else:
                    store.update_job(job_id, {
                        "status": "failed",
                        "error": f"Failed to commit: {commit_result.stderr}",
                        "progress": 100
                    })
                    return
        
        # Check if there are commits to push
        ahead_result = subprocess.run(
            ["git", "rev-list", "--count", f"origin/{branch}..HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
            env=git_env
        )
        
        commits_ahead = 0
        if ahead_result.returncode == 0:
            try:
                commits_ahead = int(ahead_result.stdout.strip())
            except ValueError:
                commits_ahead = 0
        
        if commits_ahead == 0 and not has_staged_changes:
            store.update_job(job_id, {
                "status": "completed",
                "progress": 100,
                "step": "Nothing to push — already up to date",
                "result": {
                    "success": True,
                    "message": "Already up to date, nothing to push",
                    "skipped": True
                }
            })
            return
        
        # Update status: Pushing (60%)
        store.update_job(job_id, {
            "progress": 60,
            "step": f"Pushing to {branch}..."
        })
        
        # Push to remote
        push_result = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
            env=git_env
        )
        
        if push_result.returncode != 0:
            error_msg = push_result.stderr.strip()
            # Provide a user-friendly error
            if "Could not resolve host" in error_msg:
                error_msg = "No internet connection. Check your network and try again."
            elif "Authentication failed" in error_msg or "403" in error_msg:
                error_msg = "Authentication failed. Check your GitHub credentials."
            elif "rejected" in error_msg:
                error_msg = f"Push rejected. Pull remote changes first. Details: {error_msg}"
            
            store.update_job(job_id, {
                "status": "failed",
                "error": f"Failed to push: {error_msg}",
                "progress": 100
            })
            return
        
        # Success! (100%)
        store.update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "step": "Successfully pushed to GitHub!",
            "result": {
                "success": True,
                "message": f"Successfully pushed to {branch}",
                "commit_message": commit_message,
                "branch": branch
            }
        })
        
    except subprocess.TimeoutExpired as e:
        store.update_job(job_id, {
            "status": "failed",
            "error": "Operation timed out. Check your internet connection and try again.",
            "progress": 100
        })
    except Exception as e:
        store.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": 100
        })


@app.post("/api/git/push")
def git_push():
    """
    Push changes to GitHub automatically (async with job_id)
    Expects JSON: { "commit_message": "...", "branch": "main" }
    Returns immediately with a job_id for status polling
    """
    try:
        import subprocess
        import threading
        
        data = request.json or {}
        commit_message = data.get("commit_message", "🎨 Update from Visual Testing Tool")
        branch = data.get("branch", "main")
        
        # Change to the project directory
        project_dir = BASE_DIR
        
        # Quick validation: Check if git repo exists
        check_git = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if check_git.returncode != 0:
            return jsonify({
                "success": False,
                "error": "Not a git repository. Initialize git first."
            }), 400
        
        # Create a background job
        job_id = str(uuid.uuid4())
        store.save_job(job_id, {
            "type": "git_push",
            "status": "running",
            "progress": 0,
            "step": "Initializing...",
            "created_at": datetime.datetime.now().isoformat()
        })
        
        # Start background thread for git operations
        thread = threading.Thread(
            target=process_git_push,
            args=(job_id, commit_message, branch),
            daemon=True
        )
        thread.start()
        
        # Return immediately with job_id
        return jsonify({
            "success": True,
            "job_id": job_id,
            "message": "Git push started in background"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.get("/api/git/status")
def git_status():
    """Get current git status"""
    try:
        import subprocess
        
        project_dir = BASE_DIR
        
        # Get branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        # Get status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        has_changes = bool(status_result.stdout.strip())
        
        # Get last commit
        log_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%h - %s (%ar)"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        last_commit = log_result.stdout.strip() if log_result.returncode == 0 else "No commits"
        
        return jsonify({
            "success": True,
            "current_branch": current_branch,
            "has_changes": has_changes,
            "changes_count": len(status_result.stdout.strip().split('\n')) if has_changes else 0,
            "last_commit": last_commit
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)

