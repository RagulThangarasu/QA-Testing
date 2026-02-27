"""
AI-Driven Functional Testing Engine
Uses Playwright + Local Ollama LLM for zero-locator, plain-English functional testing.
No paid API keys required.
"""
import os
import json
import time
import signal
import sys
import traceback
import re

# Global SIGPIPE handler to prevent crash on Unix-like pipes
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except Exception:
    pass
import pandas as pd
import requests as req
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


# ─── DOM Mapper JavaScript ───
DOM_MAPPER_JS = """
() => {
    const interactables = document.querySelectorAll(
        'a, button, input, textarea, select, [role="button"], [role="link"], ' +
        '[role="tab"], [role="menuitem"], [role="checkbox"], [role="radio"], ' +
        '[onclick], [data-component], details > summary, label'
    );
    const aiDOM = [];
    let id = 0;

    interactables.forEach((el) => {
        // Skip invisible elements
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        if (rect.width === 0 && rect.height === 0) return;
        if (style.display === 'none' || style.visibility === 'hidden') return;
        if (parseFloat(style.opacity) === 0) return;

        id++;
        el.setAttribute('data-ai-node-id', id);

        const text = (el.innerText || '').trim().substring(0, 120);
        const placeholder = el.placeholder || '';
        const ariaLabel = el.getAttribute('aria-label') || '';
        const name = el.name || '';
        const type = el.type || '';
        const value = el.value || '';
        const role = el.getAttribute('role') || '';
        const href = el.href || '';
        const className = el.className ? String(el.className).substring(0, 80) : '';
        const elId = el.id || '';
        const tagName = el.tagName;

        aiDOM.push({
            id: id,
            tag: tagName,
            text: text,
            placeholder: placeholder,
            aria_label: ariaLabel,
            name: name,
            type: type,
            value: value,
            role: role,
            href: href ? href.substring(0, 150) : '',
            class: className,
            el_id: elId
        });
    });

    return JSON.stringify(aiDOM);
}
"""

# ─── Component Discovery JavaScript ───
COMPONENT_DISCOVERY_JS = """
() => {
    const allElements = document.querySelectorAll('*');
    const components = {};

    allElements.forEach(el => {
        // Check for data-component attribute
        const compName = el.getAttribute('data-component') || el.getAttribute('data-testid') || el.getAttribute('data-cy');
        if (compName) {
            if (!components[compName]) {
                components[compName] = { name: compName, count: 1, tag: el.tagName };
            } else {
                components[compName].count++;
            }
        }
    });

    // Also detect common component patterns from class names
    const patterns = ['carousel', 'slider', 'nav', 'menu', 'modal', 'dialog',
                      'dropdown', 'accordion', 'tab', 'form', 'search', 'header',
                      'footer', 'sidebar', 'card', 'hero', 'banner', 'gallery',
                      'pagination', 'breadcrumb', 'tooltip', 'popover'];

    allElements.forEach(el => {
        const cls = (el.className && typeof el.className === 'string') ? el.className.toLowerCase() : '';
        const id = (el.id || '').toLowerCase();
        const role = (el.getAttribute('role') || '').toLowerCase();
        const tag = el.tagName.toLowerCase();

        for (const pattern of patterns) {
            if (cls.includes(pattern) || id.includes(pattern) || role.includes(pattern) || tag.includes(pattern)) {
                const key = pattern.charAt(0).toUpperCase() + pattern.slice(1);
                if (!components[key]) {
                    components[key] = { name: key, count: 1, tag: el.tagName, source: 'auto-detected' };
                } else {
                    components[key].count++;
                }
                break;
            }
        }
    });

    return JSON.stringify(Object.values(components));
}
"""

# ─── Page Info Extraction JavaScript ───
PAGE_INFO_JS = """
() => {
    return JSON.stringify({
        title: document.title,
        url: window.location.href,
        forms: document.forms.length,
        links: document.querySelectorAll('a').length,
        buttons: document.querySelectorAll('button, [role="button"]').length,
        inputs: document.querySelectorAll('input, textarea, select').length,
        images: document.querySelectorAll('img').length,
        headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length
    });
}
"""


class OllamaClient:
    """Client for communicating with local Ollama LLM"""

    def __init__(self, base_url="http://localhost:11434", model="llama3"):
        self.base_url = base_url
        self.model = model

    def is_available(self):
        """Check if Ollama is running"""
        try:
            resp = req.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self):
        """List available models"""
        try:
            resp = req.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def generate(self, prompt, format_json=True, max_retries=3):
        """Generate a response from Ollama with retry logic.
        Returns a tuple (response_text, error_string).
        On success error_string is None; on failure response_text is None.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 600,
            }
        }
        if format_json:
            payload["format"] = "json"

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = req.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120
                )
                if resp.status_code == 200:
                    result = resp.json()
                    text = result.get("response", "")
                    if text and text.strip():
                        return text, None
                    last_error = f"Ollama returned empty response (attempt {attempt})"
                else:
                    last_error = f"Ollama HTTP {resp.status_code}: {resp.text[:200]} (attempt {attempt})"
            except req.exceptions.Timeout:
                last_error = f"Ollama request timed out after 120s (attempt {attempt})"
            except req.exceptions.ConnectionError as e:
                # Catch broken pipes which are common with local servers closing abruptly
                if "[Errno 32] Broken pipe" in str(e):
                    last_error = f"Ollama closed the connection abruptly ([Errno 32] Broken pipe). The model might be crashing or too heavy for your system RAM (attempt {attempt})"
                else:
                    last_error = f"Cannot connect to Ollama at {self.base_url} (attempt {attempt})"
            except Exception as e:
                last_error = f"Ollama error: {str(e)} (attempt {attempt})"

            # Exponential backoff before retry (2s, 4s)
            if attempt < max_retries:
                import time as _time
                _time.sleep(2 ** attempt)

        return None, last_error


class FunctionalTestEngine:
    """
    AI-Driven Functional Testing Engine.
    Uses Playwright for browser automation and Ollama for AI interpretation.
    """

    def __init__(self, ollama_url="http://localhost:11434", ollama_model="llama3"):
        self.ollama = OllamaClient(base_url=ollama_url, model=ollama_model)

    def parse_excel_test_cases(self, excel_path):
        """Parse test cases from Excel file"""
        df = pd.read_excel(excel_path)
        # Normalize column names
        df.columns = [c.strip() for c in df.columns]

        test_cases = []
        for _, row in df.iterrows():
            tc = {}
            for col in df.columns:
                val = row[col]
                if pd.notna(val):
                    tc[col] = str(val).strip()
            if tc:
                test_cases.append(tc)

        return test_cases

    def discover_components(self, page):
        """Discover active components on the current page"""
        try:
            raw = page.evaluate(COMPONENT_DISCOVERY_JS)
            return json.loads(raw) if raw else []
        except Exception:
            return []

    def extract_dom(self, page):
        """Extract interactable DOM elements from the page"""
        try:
            raw = page.evaluate(DOM_MAPPER_JS)
            return json.loads(raw) if raw else []
        except Exception:
            return []

    def get_page_info(self, page):
        """Get general page information"""
        try:
            raw = page.evaluate(PAGE_INFO_JS)
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

    def _extract_json(self, text):
        """Robustly extract a JSON object from an LLM response string."""
        if not text or not text.strip():
            return None

        # 1. Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Strip markdown code fences (```json ... ```)
        cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 3. Find outermost { ... }
        depth = 0
        start_idx = None
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start_idx = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start_idx is not None:
                    try:
                        return json.loads(text[start_idx:i + 1])
                    except json.JSONDecodeError:
                        start_idx = None

        # 4. Greedy regex fallback
        match = re.search(r'\{[^{}]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None

    def _fallback_decide_action(self, instruction, dom_state):
        """
        Keyword-based heuristic fallback when the AI is completely unreachable.
        Matches instruction words against DOM element text/labels to produce a
        best-effort action.
        """
        instruction_lower = instruction.lower()

        # Determine action type from instruction keywords
        action = "click"  # default
        value = ""
        if any(kw in instruction_lower for kw in ["type", "enter text", "input", "fill", "write", "search for"]):
            action = "type"
            # Try to extract the value from quotes or parentheses
            quote_match = re.search(r"['\"](.+?)['\"]", instruction)
            paren_match = re.search(r"use value:\s*(.+?)\)", instruction)
            if quote_match:
                value = quote_match.group(1)
            elif paren_match:
                value = paren_match.group(1).strip()
        elif any(kw in instruction_lower for kw in ["verify", "check", "confirm", "should see", "should be visible", "is visible", "is displayed"]):
            action = "verify_text"
        elif any(kw in instruction_lower for kw in ["hover", "mouse over"]):
            action = "hover"
        elif any(kw in instruction_lower for kw in ["scroll down", "scroll page"]):
            return {"element_id": None, "action": "scroll_down", "value": "", "reasoning": "Fallback heuristic: scroll action detected in instruction"}
        elif any(kw in instruction_lower for kw in ["press enter", "submit"]):
            return {"element_id": None, "action": "press_enter", "value": "", "reasoning": "Fallback heuristic: enter/submit action detected"}
        elif any(kw in instruction_lower for kw in ["wait"]):
            return {"element_id": None, "action": "wait", "value": "2000", "reasoning": "Fallback heuristic: wait action detected"}
        elif any(kw in instruction_lower for kw in ["navigate", "go to", "open url"]):
            url_match = re.search(r'https?://\S+', instruction)
            nav_url = url_match.group(0) if url_match else ""
            return {"element_id": None, "action": "navigate", "value": nav_url, "reasoning": "Fallback heuristic: navigate action detected"}

        # Extract important keywords from instruction (remove common stop words)
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'of', 'and', 'or',
                       'is', 'are', 'was', 'be', 'it', 'its', 'this', 'that', 'for',
                       'with', 'from', 'should', 'click', 'type', 'verify', 'check',
                       'press', 'button', 'link', 'text', 'page', 'enter'}
        keywords = [w for w in re.findall(r'[a-z]+', instruction_lower) if w not in stop_words and len(w) > 2]

        if not keywords or not dom_state:
            return None

        # Score each DOM element by keyword match count
        best_score = 0
        best_el = None
        for el in dom_state:
            searchable = f"{el.get('text', '')} {el.get('aria_label', '')} {el.get('placeholder', '')} {el.get('name', '')} {el.get('el_id', '')} {el.get('class', '')}".lower()
            score = sum(1 for kw in keywords if kw in searchable)
            if score > best_score:
                best_score = score
                best_el = el

        if best_el and best_score > 0:
            # For type actions on non-input elements, try to find a related input
            if action == "type" and best_el.get("tag", "") not in ["INPUT", "TEXTAREA", "SELECT"]:
                for el in dom_state:
                    if el.get("tag") in ["INPUT", "TEXTAREA"] and any(kw in f"{el.get('placeholder', '')} {el.get('name', '')} {el.get('aria_label', '')}".lower() for kw in keywords):
                        best_el = el
                        break

            return {
                "element_id": best_el["id"],
                "action": action,
                "value": value,
                "reasoning": f"Fallback heuristic: matched keywords {keywords[:5]} to element (score={best_score})"
            }

        return None

    def ai_decide_action(self, instruction, dom_state, page_info=None):
        """
        Ask the local LLM what action to take based on plain English instruction
        and the current DOM state.  Falls back to keyword heuristic if AI is unreachable.
        """
        # Truncate DOM state if too large for context
        dom_str = json.dumps(dom_state[:60], indent=0)  # Max 60 elements
        page_ctx = ""
        if page_info:
            page_ctx = f"\nPage title: {page_info.get('title', 'N/A')}, URL: {page_info.get('url', 'N/A')}"

        prompt = f"""You are an automated web browser QA tester.
{page_ctx}

The user wants to perform this test action: "{instruction}"

Here are the currently visible interactive elements on the page (JSON array):
{dom_str}

Based on the instruction, determine:
1. Which element_id to interact with
2. What action to perform (click, type, hover, press_enter, scroll_down, verify_text, verify_visible, navigate, wait)
3. If action is "type", what text to type
4. If this is a verification step, what text or condition to check

Return ONLY valid JSON:
{{"element_id": number_or_null, "action": "click|type|hover|press_enter|scroll_down|verify_text|verify_visible|navigate|wait", "value": "text_to_type_or_verify", "reasoning": "brief explanation"}}

If the instruction is about verifying/checking something visible on the page, use "verify_text" or "verify_visible".
If no matching element is found, set element_id to null and explain in reasoning."""

        response, ai_error = self.ollama.generate(prompt)

        if response:
            parsed = self._extract_json(response)
            if parsed and isinstance(parsed, dict) and "action" in parsed:
                return parsed
            # AI responded but JSON parsing failed — log it but continue to fallback
            ai_error = f"AI responded but could not parse valid JSON. Raw: {response[:300]}"

        # --- Fallback: keyword heuristic ---
        fallback = self._fallback_decide_action(instruction, dom_state)
        if fallback:
            fallback["_fallback"] = True
            fallback["_ai_error"] = ai_error
            return fallback

        # Store the error for reporting
        return {"_failed": True, "_ai_error": ai_error or "Unknown error"}

    def ai_verify_result(self, expected_result, dom_state, page_info):
        """Ask AI to verify if expected result is met.  Falls back to text search."""
        dom_str = json.dumps(dom_state[:40], indent=0)

        prompt = f"""You are verifying a test result.

The expected result is: "{expected_result}"

The current page state is:
Title: {page_info.get('title', 'N/A')}
URL: {page_info.get('url', 'N/A')}

Visible elements:
{dom_str}

Does the current page state satisfy the expected result?
Return ONLY valid JSON: {{"passed": true_or_false, "reason": "brief explanation"}}"""

        response, ai_error = self.ollama.generate(prompt)

        if response:
            parsed = self._extract_json(response)
            if parsed and isinstance(parsed, dict) and "passed" in parsed:
                return parsed

        # Fallback: simple keyword match against DOM text + page title/url
        expected_lower = expected_result.lower()
        page_text = f"{page_info.get('title', '')} {page_info.get('url', '')}".lower()
        all_element_text = " ".join(
            f"{el.get('text', '')} {el.get('aria_label', '')}" for el in dom_state
        ).lower()

        # Check if key phrases from the expected result appear on the page
        keywords = [w for w in re.findall(r'[a-z]+', expected_lower) if len(w) > 2]
        if keywords:
            matched = sum(1 for kw in keywords if kw in page_text or kw in all_element_text)
            ratio = matched / len(keywords)
            if ratio >= 0.5:
                return {"passed": True, "reason": f"Fallback verification: {matched}/{len(keywords)} keywords matched on page"}

        reason = ai_error or "AI unavailable and fallback keyword match failed"
        return {"passed": False, "reason": reason}

    def execute_action(self, page, ai_decision):
        """Execute an action in Playwright based on AI decision"""
        action = ai_decision.get("action", "")
        element_id = ai_decision.get("element_id")
        value = ai_decision.get("value", "")

        try:
            if action == "navigate":
                if value and value.startswith("http"):
                    page.goto(value, wait_until="domcontentloaded", timeout=30000)
                    try:
                        page.wait_for_load_state("load", timeout=5000)
                    except Exception:
                        pass
                return {"success": True, "action": action}

            if action == "wait":
                wait_ms = 2000
                try:
                    wait_ms = int(value) if value else 2000
                except (ValueError, TypeError):
                    wait_ms = 2000
                page.wait_for_timeout(wait_ms)
                return {"success": True, "action": action}

            if action == "scroll_down":
                page.evaluate("window.scrollBy(0, 500)")
                page.wait_for_timeout(500)
                return {"success": True, "action": action}

            if action == "press_enter":
                page.keyboard.press("Enter")
                page.wait_for_timeout(1000)
                return {"success": True, "action": action}

            if element_id is None:
                return {"success": False, "error": "No element_id provided by AI"}

            locator = page.locator(f'[data-ai-node-id="{element_id}"]')

            if not locator.count():
                return {"success": False, "error": f"Element with AI node ID {element_id} not found"}

            if action == "click":
                locator.first.click(timeout=5000)
                page.wait_for_timeout(1000)
                return {"success": True, "action": action, "element_id": element_id}

            elif action == "type":
                locator.first.fill(str(value))
                page.wait_for_timeout(500)
                return {"success": True, "action": action, "element_id": element_id, "value": value}

            elif action == "hover":
                locator.first.hover(timeout=5000)
                page.wait_for_timeout(500)
                return {"success": True, "action": action, "element_id": element_id}

            elif action == "verify_visible":
                is_visible = locator.first.is_visible()
                return {
                    "success": is_visible,
                    "action": action,
                    "element_id": element_id,
                    "error": None if is_visible else f"Element {element_id} is not visible"
                }

            elif action == "verify_text":
                actual_text = locator.first.inner_text()
                matched = value.lower() in actual_text.lower() if value else bool(actual_text)
                return {
                    "success": matched,
                    "action": action,
                    "element_id": element_id,
                    "actual_text": actual_text[:200],
                    "error": None if matched else f"Expected '{value}' not found in '{actual_text[:100]}'"
                }

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_single_url_tests(self, url, test_cases, job_id, job_dir, progress_callback=None):
        """Run functional tests on a single URL"""
        results = {
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "steps": []
        }

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) QA-Testing-Framework/2.0"
            )
            page = context.new_page()

            try:
                if progress_callback:
                    progress_callback("Navigating to URL...", 10)

                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                try:
                    page.wait_for_load_state("load", timeout=5000)
                except Exception:
                    pass

                # Take initial screenshot
                initial_screenshot_path = os.path.join(job_dir, "initial_page.png")
                page.screenshot(path=initial_screenshot_path, full_page=False)

                # Get page info and components
                page_info = self.get_page_info(page)
                components = self.discover_components(page)
                results["page_info"] = page_info
                results["components"] = components

                for idx, tc in enumerate(test_cases):
                    step_num = idx + 1
                    instruction = tc.get("Action_Description") or tc.get("Goal_Description") or tc.get("Test_Step") or tc.get("action_description") or tc.get("goal_description") or tc.get("test_step") or ""
                    test_data = tc.get("Test_Data") or tc.get("test_data") or ""
                    expected = tc.get("Expected_Result") or tc.get("expected_result") or ""
                    component = tc.get("Component") or tc.get("Component_Name") or tc.get("component") or tc.get("component_name") or ""
                    test_id = tc.get("Test_ID") or tc.get("test_id") or f"TC_{step_num:03d}"

                    if not instruction:
                        results["skipped"] += 1
                        results["steps"].append({
                            "step": step_num,
                            "test_id": test_id,
                            "instruction": "(empty)",
                            "status": "skipped",
                            "reason": "No instruction provided"
                        })
                        continue

                    if progress_callback:
                        pct = 15 + int((step_num / len(test_cases)) * 70)
                        progress_callback(f"Step {step_num}/{len(test_cases)}: {instruction[:60]}...", pct)

                    # Combine instruction with test data if present
                    full_instruction = instruction
                    if test_data:
                        full_instruction += f" (use value: {test_data})"

                    # Re-extract DOM before each action (state may have changed)
                    dom_state = self.extract_dom(page)
                    page_info_current = self.get_page_info(page)

                    step_result = {
                        "step": step_num,
                        "test_id": test_id,
                        "component": component,
                        "instruction": instruction,
                        "test_data": test_data,
                        "expected_result": expected,
                    }

                    # Ask AI what to do
                    ai_decision = self.ai_decide_action(full_instruction, dom_state, page_info_current)

                    if not ai_decision or ai_decision.get("_failed"):
                        results["failed"] += 1
                        step_result["status"] = "failed"
                        error_detail = "AI failed to produce a decision"
                        if ai_decision and ai_decision.get("_ai_error"):
                            error_detail += f": {ai_decision['_ai_error']}"
                        step_result["error"] = error_detail
                        step_result["ai_decision"] = None
                        results["steps"].append(step_result)
                        continue

                    step_result["ai_decision"] = {
                        "action": ai_decision.get("action"),
                        "element_id": ai_decision.get("element_id"),
                        "reasoning": ai_decision.get("reasoning", "")
                    }

                    # --- HIGHLIGHT & SCREENSHOT BEFORE ACTION ---
                    import uuid
                    try:
                        step_id = str(uuid.uuid4())[:6]
                        file_name = f"step_{step_num}_{step_id}.png"
                        step_screenshot = os.path.join(job_dir, file_name)
                        
                        el_id = ai_decision.get("element_id")
                        if el_id:
                            page.evaluate(f'''
                                (function() {{
                                    var el = document.querySelector('[data-ai-node-id="{el_id}"]');
                                    if (el) {{
                                        el.setAttribute('data-original-border', el.style.border || '');
                                        el.setAttribute('data-original-box-shadow', el.style.boxShadow || '');
                                        el.style.border = '4px solid red';
                                        el.style.boxShadow = '0 0 10px red';
                                        el.scrollIntoView({{behavior: "instant", block: "center"}});
                                    }}
                                }})()
                            ''')
                            page.wait_for_timeout(300)

                        page.screenshot(path=step_screenshot, full_page=False)
                        step_result["screenshot"] = file_name
                        
                        if el_id:
                            page.evaluate(f'''
                                (function() {{
                                    var el = document.querySelector('[data-ai-node-id="{el_id}"]');
                                    if (el) {{
                                        el.style.border = el.getAttribute('data-original-border') || '';
                                        el.style.boxShadow = el.getAttribute('data-original-box-shadow') || '';
                                    }}
                                }})()
                            ''')
                    except Exception:
                        pass
                    # --------------------------------------------

                    # Execute the action
                    exec_result = self.execute_action(page, ai_decision)
                    step_result["execution"] = exec_result

                    if not exec_result.get("success"):
                        results["failed"] += 1
                        step_result["status"] = "failed"
                        step_result["error"] = exec_result.get("error", "Action execution failed")
                    else:
                        # If there's an expected result, verify it
                        if expected:
                            # Re-extract DOM after action
                            new_dom = self.extract_dom(page)
                            new_page_info = self.get_page_info(page)
                            verification = self.ai_verify_result(expected, new_dom, new_page_info)
                            step_result["verification"] = verification

                            if verification.get("passed"):
                                results["passed"] += 1
                                step_result["status"] = "passed"
                            else:
                                results["failed"] += 1
                                step_result["status"] = "failed"
                                step_result["error"] = verification.get("reason", "Verification failed")
                        else:
                            results["passed"] += 1
                            step_result["status"] = "passed"

                    results["steps"].append(step_result)

            except Exception as e:
                results["error"] = str(e)
            finally:
                browser.close()

        # Save results JSON
        results_path = os.path.join(job_dir, "functional_results.json")
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)

        return results

    def crawl_sitemap_urls(self, sitemap_url):
        """Fetch URLs from a sitemap"""
        try:
            resp = req.get(sitemap_url, timeout=30, headers={"User-Agent": "QA-Testing-Framework/2.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml-xml")
            urls = [loc.text.strip() for loc in soup.find_all("loc") if loc.text.strip()]

            # If sitemap index, crawl child sitemaps
            if not urls:
                sitemaps = [s.text.strip() for s in soup.find_all("sitemap")]
                for sm_url in sitemaps[:5]:
                    try:
                        sm_resp = req.get(sm_url, timeout=30, headers={"User-Agent": "QA-Testing-Framework/2.0"})
                        sm_soup = BeautifulSoup(sm_resp.text, "lxml-xml")
                        urls.extend([loc.text.strip() for loc in sm_soup.find_all("loc")])
                    except Exception:
                        pass

            return urls[:100]  # Cap at 100 URLs
        except Exception as e:
            return []

    def run_sitemap_tests(self, sitemap_url, test_cases, job_id, job_dir, progress_callback=None):
        """Run functional tests across all URLs from a sitemap"""
        urls = self.crawl_sitemap_urls(sitemap_url)

        if not urls:
            return {"error": "No URLs found in sitemap", "total_urls": 0}

        all_results = {
            "sitemap_url": sitemap_url,
            "timestamp": datetime.utcnow().isoformat(),
            "total_urls": len(urls),
            "url_results": [],
            "summary": {
                "total_passed": 0,
                "total_failed": 0,
                "total_skipped": 0,
                "total_steps": 0
            }
        }

        for url_idx, url in enumerate(urls):
            if progress_callback:
                pct = 5 + int((url_idx / len(urls)) * 90)
                progress_callback(f"Testing URL {url_idx + 1}/{len(urls)}: {url[:50]}...", pct)

            url_results = self.run_single_url_tests(
                url, test_cases, job_id, job_dir, progress_callback=None
            )
            all_results["url_results"].append(url_results)
            all_results["summary"]["total_passed"] += url_results.get("passed", 0)
            all_results["summary"]["total_failed"] += url_results.get("failed", 0)
            all_results["summary"]["total_skipped"] += url_results.get("skipped", 0)
            all_results["summary"]["total_steps"] += url_results.get("total", 0)

        # Save results
        results_path = os.path.join(job_dir, "functional_results.json")
        with open(results_path, "w") as f:
            json.dump(all_results, f, indent=2)

        return all_results


def generate_functional_report_pdf(results, job_id, job_dir):
    """Generate a PDF report of functional test results"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.piecharts import Pie

    pdf_path = os.path.join(job_dir, f"functional_report_{job_id}.pdf")

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, textColor=HexColor('#1e293b'), spaceAfter=6)
    header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=13, textColor=HexColor('#334155'), spaceAfter=4)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=9, textColor=HexColor('#475569'), spaceAfter=2, leading=13)

    elements = []
    elements.append(Paragraph("AI Functional Testing Report", title_style))
    elements.append(Spacer(1, 4*mm))

    # Summary
    url = results.get("url", results.get("sitemap_url", "N/A"))
    timestamp = results.get("timestamp", "N/A")
    total = results.get("total", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    skipped = results.get("skipped", 0)

    # Check for sitemap batch results
    if "summary" in results:
        total = results["summary"].get("total_steps", 0)
        passed = results["summary"].get("total_passed", 0)
        failed = results["summary"].get("total_failed", 0)
        skipped = results["summary"].get("total_skipped", 0)

    summary_data = [
        ["URL", url[:80]],
        ["Timestamp", timestamp],
        ["Total Steps", str(total)],
        ["Passed", str(passed)],
        ["Failed", str(failed)],
        ["Skipped", str(skipped)],
        ["Pass Rate", f"{round(passed/total*100) if total > 0 else 0}%"]
    ]

    summary_table = Table(summary_data, colWidths=[80, 400])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#334155')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6*mm))

    # --- Add Graph ---
    if total > 0:
        drawing = Drawing(300, 150)
        pie = Pie()
        pie.x = 80
        pie.y = 15
        pie.width = 120
        pie.height = 120
        
        pie.data = []
        pie.labels = []
        colors_list = []
        
        if passed > 0:
            pie.data.append(passed)
            pie.labels.append("Passed")
            colors_list.append(HexColor('#22c55e'))
        if failed > 0:
            pie.data.append(failed)
            pie.labels.append("Failed")
            colors_list.append(HexColor('#ef4444'))
        if skipped > 0:
            pie.data.append(skipped)
            pie.labels.append("Skipped")
            colors_list.append(HexColor('#94a3b8'))
            
        pie.slices.strokeWidth = 0.5
        for i, c in enumerate(colors_list):
            pie.slices[i].fillColor = c
            
        drawing.add(pie)
        elements.append(drawing)
        elements.append(Spacer(1, 6*mm))

    # Step Details
    elements.append(Paragraph("Detailed Step-by-Step Report", header_style))
    elements.append(Spacer(1, 3*mm))

    steps = results.get("steps", [])
    # For sitemap results, aggregate steps from all URLs
    if "url_results" in results:
        steps = []
        for ur in results.get("url_results", []):
            for s in ur.get("steps", []):
                s["url"] = ur.get("url", "")
                steps.append(s)

    if steps:
        for s in steps[:150]:  # Cap to prevent out of memory
            status = s.get("status", "?").upper()
            step_num = s.get("step", "N/A")
            instruction = s.get("instruction", "None")
            error_text = s.get("error") or "No issue detected"
            
            ai_action = "None"
            if s.get("ai_decision"):
                ad = s["ai_decision"]
                ai_action = f"Action: {ad.get('action', 'N/A')} | Element ID: {ad.get('element_id', 'N/A')}"
                if ad.get("reasoning"):
                    ai_action += f"<br/>Reasoning: {ad.get('reasoning')}"

            if status == 'PASSED':
                bg_color = HexColor('#dcfce7')
                text_color = HexColor('#166534')
            elif status == 'FAILED':
                bg_color = HexColor('#fee2e2')
                text_color = HexColor('#991b1b')
            else:
                bg_color = HexColor('#f1f5f9')
                text_color = HexColor('#475569')

            card_data = []
            card_data.append([
                Paragraph(f"<b>Step {step_num} - {status}</b>", ParagraphStyle('cardHead', fontSize=10, textColor=text_color)), 
                ""
            ])
            card_data.append([Paragraph("<b>Instruction:</b>", body_style), Paragraph(instruction, body_style)])
            card_data.append([Paragraph("<b>AI Action:</b>", body_style), Paragraph(ai_action, body_style)])
            card_data.append([Paragraph("<b>Exact Issue:</b>", body_style), Paragraph(str(error_text), body_style)])
            
            img_file = s.get("screenshot")
            if img_file:
                img_path = os.path.join(job_dir, img_file)
                if os.path.exists(img_path):
                    try:
                        img = Image(img_path)
                        avail_w = 130 * mm
                        max_h = 100 * mm
                        ratio = img.imageHeight / img.imageWidth
                        calc_h = avail_w * ratio
                        
                        if calc_h > max_h:
                            img.drawHeight = max_h
                            img.drawWidth = max_h / ratio
                        else:
                            img.drawWidth = avail_w
                            img.drawHeight = calc_h
                            
                        card_data.append([Paragraph("<b>Screenshot:</b>", body_style), img])
                    except Exception:
                        pass

            card_table = Table(card_data, colWidths=[35*mm, 135*mm])
            card_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (1,0), bg_color),
                ('SPAN', (0,0), (1,0)),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, HexColor('#e2e8f0')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            
            elements.append(card_table)
            elements.append(Spacer(1, 6*mm))

    doc.build(elements)
    return pdf_path
