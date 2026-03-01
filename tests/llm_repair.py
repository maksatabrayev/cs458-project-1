"""
LLM Repair Module
=================
Handles communication with the Gemini LLM for repairing broken selectors.
Can use either the web app's /api/heal endpoint or direct Gemini API.
"""

import os
import json
import time
import logging
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

logger = logging.getLogger("SelfHealing.LLMRepair")

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


class LLMRepair:
    """
    LLM-based selector repair.
    Primary: uses the /api/heal endpoint on the web server.
    Fallback: directly calls Gemini API.
    """

    def __init__(self, api_url="http://localhost:3000"):
        self.api_url = api_url
        self.repair_history = []

    def repair_selector(self, old_selector, dom_snippet, element_description):
        """
        Attempt to repair a broken selector with retry logic.
        First tries the API endpoint, falls back to direct Gemini call.
        Retries up to 3 times with delays if rate limited.
        """
        max_retries = 3

        for attempt in range(max_retries):
            # Try API endpoint first
            try:
                result = self._repair_via_api(old_selector, dom_snippet, element_description)
                if result and result.get("newSelector"):
                    self.repair_history.append({
                        "method": "api",
                        "old": old_selector,
                        "new": result["newSelector"],
                        "confidence": result.get("confidence", 0),
                    })
                    return result
            except Exception as e:
                logger.warning(f"API repair failed: {e}, trying direct Gemini call...")

            # Fallback: direct Gemini API
            try:
                result = self._repair_via_gemini(old_selector, dom_snippet, element_description)
                if result and result.get("newSelector"):
                    self.repair_history.append({
                        "method": "gemini_direct",
                        "old": old_selector,
                        "new": result["newSelector"],
                        "confidence": result.get("confidence", 0),
                    })
                    return result
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    wait_time = (attempt + 1) * 15  # 15s, 30s, 45s
                    logger.warning(f"Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                logger.error(f"Direct Gemini repair also failed: {e}")

        return None

    def _repair_via_api(self, old_selector, dom_snippet, element_description):
        """Call the /api/heal endpoint on the web server."""
        # Trim DOM to avoid huge payloads
        trimmed_dom = self._trim_dom(dom_snippet)
        
        response = requests.post(
            f"{self.api_url}/api/heal",
            json={
                "oldSelector": old_selector,
                "domSnippet": trimmed_dom,
                "elementDescription": element_description,
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data
        
        logger.warning(f"API returned status {response.status_code}")
        return None

    def _repair_via_gemini(self, old_selector, dom_snippet, element_description):
        """Call Gemini API directly for selector repair."""
        if not client:
            logger.error("No GEMINI_API_KEY set, cannot use direct Gemini repair")
            return None

        trimmed_dom = self._trim_dom(dom_snippet)

        prompt = f"""You are a Selenium test repair assistant. A test element locator has broken due to UI changes.

OLD SELECTOR: {old_selector}
ELEMENT DESCRIPTION: {element_description}

CURRENT PAGE DOM (relevant section):
{trimmed_dom}

Your task:
1. Analyze the DOM to find the element that most likely matches the old selector's intent.
2. Return a new, valid CSS selector or XPath that will locate the correct element.
3. Do NOT hallucinate selectors. Only return selectors for elements actually present in the DOM.

RESPOND IN EXACTLY THIS JSON FORMAT (no markdown, no extra text):
{{
  "newSelector": "the new CSS selector or XPath",
  "selectorType": "css" or "xpath",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this element matches"
}}"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        
        # Clean markdown wrapping if present
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    def _trim_dom(self, dom, max_length=5000):
        """Trim DOM to relevant portions to avoid token limits."""
        if len(dom) <= max_length:
            return dom
        
        # Try to find the <body> content and trim that
        body_start = dom.find("<body")
        if body_start > 0:
            dom = dom[body_start:]
        
        # If still too long, take first and last portions
        if len(dom) > max_length:
            half = max_length // 2
            return dom[:half] + "\n... [DOM TRIMMED] ...\n" + dom[-half:]
        
        return dom
