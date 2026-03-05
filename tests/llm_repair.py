"""
LLM Repair Module
=================
Handles communication with the web app's /api/heal endpoint for
repairing broken selectors and resolving interaction blockers.
"""

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

logger = logging.getLogger("SelfHealing.LLMRepair")


class LLMRepair:
    """
    API-only selector repair.
    Calls /api/heal once per healing attempt and fails fast on errors.
    """

    def __init__(self, api_url="http://localhost:3000"):
        self.api_url = api_url
        self.repair_history = []

    def repair_selector(self, old_selector, dom_snippet, element_description):
        """
        Attempt to repair a broken selector with a single API call.
        Returns None immediately when the API cannot provide a selector.
        """
        result = self._repair_via_api(old_selector, dom_snippet, element_description)
        if result and result.get("newSelector"):
            self.repair_history.append(
                {
                    "method": "api",
                    "old": old_selector,
                    "new": result["newSelector"],
                    "confidence": result.get("confidence", 0),
                }
            )
            return result

        logger.warning(
            "Repair failed fast via /api/heal for selector '%s'. API response: %s",
            old_selector,
            result,
        )
        return None

    def _repair_via_api(self, old_selector, dom_snippet, element_description):
        """Call the /api/heal endpoint on the web server."""
        trimmed_dom = self._trim_dom(
            dom_snippet,
            context_hints=[old_selector, element_description],
        )

        response = requests.post(
            f"{self.api_url}/api/heal",
            json={
                "oldSelector": old_selector,
                "domSnippet": trimmed_dom,
                "elementDescription": element_description,
            },
            timeout=30,
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "success": False,
                "error": "Non-JSON response from /api/heal",
                "statusCode": response.status_code,
            }

        if response.status_code != 200:
            logger.warning(
                "API repair returned non-200 status=%s body=%s",
                response.status_code,
                data,
            )
            return data

        if not data.get("success"):
            logger.warning("API repair returned success=false body=%s", data)
            return data

        return data

    def resolve_interaction_blocker(self, target_selector, dom_snippet, action_description):
        """
        Resolve click/interact blockers with a single API call.
        Falls back immediately to deterministic close selector.
        """
        result = self._unblock_via_api(target_selector, dom_snippet, action_description)
        if result and result.get("blockerSelector"):
            self.repair_history.append(
                {
                    "method": "api_unblock",
                    "target": target_selector,
                    "blocker": result["blockerSelector"],
                    "confidence": result.get("confidence", 0),
                }
            )
            return result

        logger.warning(
            "Unblock failed fast via /api/heal for target '%s'. API response: %s. Using deterministic fallback.",
            target_selector,
            result,
        )
        return {
            "blockerSelector": "#close-popup-btn",
            "selectorType": "css",
            "action": "click",
            "confidence": 0.3,
            "reasoning": "Fallback unblock selector used after /api/heal could not resolve blocker",
        }

    def _unblock_via_api(self, target_selector, dom_snippet, action_description):
        trimmed_dom = self._trim_dom(
            dom_snippet,
            context_hints=[target_selector, action_description],
        )

        response = requests.post(
            f"{self.api_url}/api/heal",
            json={
                "taskType": "interaction_unblock",
                "oldSelector": target_selector,
                "domSnippet": trimmed_dom,
                "actionDescription": action_description,
            },
            timeout=30,
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "success": False,
                "error": "Non-JSON response from /api/heal",
                "statusCode": response.status_code,
            }

        if response.status_code != 200:
            logger.warning(
                "API unblock returned non-200 status=%s body=%s",
                response.status_code,
                data,
            )
            return data

        if not data.get("success"):
            logger.warning("API unblock returned success=false body=%s", data)
            return data

        return data

    def _trim_dom(self, dom, context_hints=None, max_length=12000):
        """Trim DOM to relevant portions while preserving likely interactive regions."""
        if len(dom) <= max_length:
            return dom

        body_start = dom.find("<body")
        if body_start > 0:
            dom = dom[body_start:]

        def centered_slice(source, center_idx):
            half = max_length // 2
            start = max(0, center_idx - half)
            end = min(len(source), start + max_length)
            start = max(0, end - max_length)
            return source[start:end]

        hints = []
        for hint in (context_hints or []):
            if not hint:
                continue
            norm = str(hint).lower()
            hints.extend([part for part in norm.replace("=", " ").split() if part])

        stable_markers = [
            "login-form",
            "login-container",
            "login-card",
            "sign in",
            "identifier",
            "password",
            "btn-primary",
            "google-login-btn",
            "facebook-login-btn",
            "github-login-btn",
            "dynamic-popup-overlay",
            "close-popup-btn",
            "<form",
            "<input",
            "<button",
        ]
        markers = hints + stable_markers

        for marker in markers:
            idx = dom.lower().find(marker.lower())
            if idx >= 0:
                return centered_slice(dom, idx)

        if len(dom) > max_length:
            half = max_length // 2
            return dom[:half] + "\n... [DOM TRIMMED] ...\n" + dom[-half:]

        return dom
