"""
Self-Healing Selenium Driver
============================
Core module that wraps Selenium WebDriver with self-healing capabilities.
When an element is not found, it:
1. Captures the current DOM
2. Sends the old selector + DOM to the LLM repair API
3. Applies the new selector
4. Logs the healed element for developer review
"""

import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
from llm_repair import LLMRepair
from heuristic_scorer import HeuristicScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("self_healing.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("SelfHealing")


class HealingRecord:
    """Record of a healed element for developer review."""

    def __init__(self, old_selector, new_selector, selector_type, confidence, reasoning, timestamp):
        self.old_selector = old_selector
        self.new_selector = new_selector
        self.selector_type = selector_type
        self.confidence = confidence
        self.reasoning = reasoning
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "old_selector": self.old_selector,
            "new_selector": self.new_selector,
            "selector_type": self.selector_type,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
        }


class SelfHealingDriver:
    """
    A wrapper around Selenium WebDriver that automatically heals
    broken selectors using LLM-based repair.
    """

    def __init__(self, driver, base_url="http://localhost:3000", api_url="http://localhost:3000"):
        self.driver = driver
        self.base_url = base_url
        self.api_url = api_url
        self.llm_repair = LLMRepair(api_url)
        self.heuristic_scorer = HeuristicScorer()
        self.healing_log = []
        self.element_metadata = {}  # Historical metadata for elements

    def navigate(self, path="/"):
        """Navigate to a page."""
        url = f"{self.base_url}{path}"
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        time.sleep(1)  # Wait for page load

    def find_element(self, by, value, description="", timeout=10):
        """
        Find an element with self-healing capability.
        If the element is not found, attempts to heal using LLM.
        """
        try:
            # First try: standard Selenium find
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            # Store metadata for future healing
            self._store_metadata(value, element)
            logger.info(f"[OK] Found element: {value}")
            return element

        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"[WARN] Element not found: {value} -- Initiating self-healing...")
            return self._heal_and_find(by, value, description, timeout)

    def find_element_clickable(self, by, value, description="", timeout=10):
        """Find an element and wait for it to be clickable."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            self._store_metadata(value, element)
            logger.info(f"[OK] Found clickable element: {value}")
            return element

        except (NoSuchElementException, TimeoutException):
            logger.warning(f"[WARN] Clickable element not found: {value} -- Initiating self-healing...")
            return self._heal_and_find(by, value, description, timeout, clickable=True)

    def _heal_and_find(self, by, value, description, timeout, clickable=False):
        """
        Self-healing process:
        1. Extract DOM
        2. Try heuristic scoring first
        3. If heuristics fail, call LLM for repair
        4. Apply new selector and log
        """
        # Step 1: Extract current DOM
        dom = self.driver.page_source
        logger.info("[DOM] Extracted page DOM for analysis")

        # Step 2: Try heuristic scoring with historical metadata
        historical = self.element_metadata.get(value)
        if historical:
            logger.info("[HEURISTIC] Attempting heuristic-based repair...")
            heuristic_result = self.heuristic_scorer.find_best_match(
                self.driver, historical
            )
            if heuristic_result and heuristic_result["confidence"] >= 0.6:
                logger.info(
                    f"[OK] Heuristic match found! Confidence: {heuristic_result['confidence']:.2f}"
                )
                try:
                    new_by = By.CSS_SELECTOR if heuristic_result["selector_type"] == "css" else By.XPATH
                    element = self.driver.find_element(new_by, heuristic_result["selector"])
                    self._record_healing(
                        value,
                        heuristic_result["selector"],
                        heuristic_result["selector_type"],
                        heuristic_result["confidence"],
                        "Heuristic match based on historical metadata",
                    )
                    return element
                except NoSuchElementException:
                    logger.warning("Heuristic match failed, falling back to LLM...")

        # Step 3: Call LLM for repair
        logger.info("[LLM] Calling LLM for selector repair...")
        selector_type = "css" if by == By.CSS_SELECTOR else "id" if by == By.ID else "xpath"
        old_selector = f"{selector_type}={value}"

        repair_result = self.llm_repair.repair_selector(
            old_selector=old_selector,
            dom_snippet=dom,
            element_description=description or f"Element with selector: {value}",
        )

        if repair_result and repair_result.get("newSelector"):
            new_selector = repair_result["newSelector"]
            new_type = repair_result.get("selectorType", "css")
            confidence = repair_result.get("confidence", 0)

            logger.info(
                f"[REPAIR] LLM suggested new selector: {new_selector} "
                f"(type: {new_type}, confidence: {confidence:.2f})"
            )

            # Step 4: Try the new selector
            try:
                new_by = By.CSS_SELECTOR if new_type == "css" else By.XPATH
                if clickable:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((new_by, new_selector))
                    )
                else:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((new_by, new_selector))
                    )

                # Record the healing
                self._record_healing(
                    value, new_selector, new_type, confidence,
                    repair_result.get("reasoning", "LLM repair")
                )
                self._store_metadata(new_selector, element)

                logger.info(f"[HEALED] Self-healing successful! Element found with: {new_selector}")
                return element

            except (NoSuchElementException, TimeoutException):
                logger.error(f"[FAIL] LLM-suggested selector also failed: {new_selector}")
                raise NoSuchElementException(
                    f"Self-healing failed. Original: {value}, "
                    f"Attempted: {new_selector}"
                )
        else:
            logger.error("[FAIL] LLM could not suggest a new selector")
            raise NoSuchElementException(
                f"Self-healing failed. LLM could not repair selector: {value}"
            )

    def _store_metadata(self, selector, element):
        """Store element metadata for future heuristic matching."""
        try:
            metadata = {
                "selector": selector,
                "tag_name": element.tag_name,
                "text": element.text[:100] if element.text else "",
                "attributes": {},
                "location": element.location,
                "size": element.size,
                "parent_tag": None,
            }
            # Get common attributes
            for attr in ["id", "class", "name", "type", "placeholder", "href", "data-testid"]:
                val = element.get_attribute(attr)
                if val:
                    metadata["attributes"][attr] = val

            # Get parent info
            try:
                parent = element.find_element(By.XPATH, "..")
                metadata["parent_tag"] = parent.tag_name
                metadata["parent_id"] = parent.get_attribute("id") or ""
            except Exception:
                pass

            self.element_metadata[selector] = metadata
        except StaleElementReferenceException:
            pass

    def _record_healing(self, old_selector, new_selector, selector_type, confidence, reasoning):
        """Record a healing event for developer review."""
        record = HealingRecord(
            old_selector=old_selector,
            new_selector=new_selector,
            selector_type=selector_type,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat(),
        )
        self.healing_log.append(record)
        logger.info(f"[LOG] Healing recorded: {old_selector} -> {new_selector}")

    def get_healing_report(self):
        """Generate a report of all healed elements."""
        if not self.healing_log:
            return "No elements were healed during this test session."

        report = "=" * 60 + "\n"
        report += "SELF-HEALING REPORT\n"
        report += "=" * 60 + "\n\n"

        for i, record in enumerate(self.healing_log, 1):
            report += f"Healing #{i}:\n"
            report += f"  Old Selector: {record.old_selector}\n"
            report += f"  New Selector: {record.new_selector}\n"
            report += f"  Type: {record.selector_type}\n"
            report += f"  Confidence: {record.confidence:.2f}\n"
            report += f"  Reasoning: {record.reasoning}\n"
            report += f"  Timestamp: {record.timestamp}\n"
            report += "-" * 40 + "\n"

        return report

    def save_healing_report(self, filepath="healing_report.json"):
        """Save healing log to JSON file."""
        data = [r.to_dict() for r in self.healing_log]
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"[SAVE] Healing report saved to: {filepath}")

    def execute_script(self, script, *args):
        """Execute JavaScript on the page."""
        return self.driver.execute_script(script, *args)

    def take_screenshot(self, filename):
        """Take a screenshot."""
        self.driver.save_screenshot(filename)
        logger.info(f"[SCREENSHOT] Screenshot saved: {filename}")

    @property
    def page_source(self):
        return self.driver.page_source

    @property
    def current_url(self):
        return self.driver.current_url

    @property
    def title(self):
        return self.driver.title

    def quit(self):
        """Quit the driver and print healing report."""
        report = self.get_healing_report()
        print("\n" + report)
        self.driver.quit()
