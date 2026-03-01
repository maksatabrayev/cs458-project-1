"""
Heuristic Scorer
================
Compares DOM elements against historical metadata to find the best match
without needing to call the LLM. This is the first-pass healing attempt.

Scores based on:
- Tag name similarity
- Location proximity
- Size similarity
- Attribute overlap (id, class, type, etc.)
- Text content similarity
- Parent hierarchy
"""

import logging
from selenium.webdriver.common.by import By

logger = logging.getLogger("SelfHealing.Heuristic")


class HeuristicScorer:
    """
    Scores DOM elements against historical element metadata to find
    the best match for a broken selector.
    """

    # Weight configuration for scoring
    # Weights tuned so that elements with changed IDs but same
    # tag/text/location/size/parent still score above 0.7
    WEIGHTS = {
        "tag_name": 0.25,
        "location": 0.15,
        "size": 0.10,
        "attributes": 0.10,
        "text": 0.20,
        "parent": 0.20,
    }

    def find_best_match(self, driver, historical_metadata, threshold=0.5):
        """
        Search the current DOM for the element that best matches
        the historical metadata.
        
        Returns: { selector, selector_type, confidence, element } or None
        """
        if not historical_metadata:
            return None

        tag = historical_metadata.get("tag_name", "*")
        candidates = driver.find_elements(By.TAG_NAME, tag)

        if not candidates:
            # Try broader search
            candidates = driver.find_elements(By.CSS_SELECTOR, "input, button, a, select, textarea")

        best_score = 0
        best_candidate = None
        best_selector = None

        for element in candidates:
            try:
                score = self._score_element(element, historical_metadata)
                if score > best_score:
                    best_score = score
                    best_candidate = element
                    # Build a selector for this element
                    best_selector = self._build_selector(element)
            except Exception as e:
                continue

        if best_score >= threshold and best_selector:
            logger.info(f"Heuristic best match: score={best_score:.2f}, selector={best_selector}")
            return {
                "selector": best_selector,
                "selector_type": "css",
                "confidence": best_score,
                "element": best_candidate,
            }

        logger.info(f"No heuristic match above threshold ({threshold}). Best: {best_score:.2f}")
        return None

    def _score_element(self, element, historical):
        """Score a single element against historical metadata."""
        score = 0.0

        # 1. Tag name match
        if element.tag_name == historical.get("tag_name"):
            score += self.WEIGHTS["tag_name"]

        # 2. Location proximity
        try:
            loc = element.location
            hist_loc = historical.get("location", {})
            if hist_loc:
                dx = abs(loc.get("x", 0) - hist_loc.get("x", 0))
                dy = abs(loc.get("y", 0) - hist_loc.get("y", 0))
                distance = (dx**2 + dy**2) ** 0.5
                # Within 100px = full score, linear decay to 500px
                location_score = max(0, 1 - distance / 500)
                score += self.WEIGHTS["location"] * location_score
        except Exception:
            pass

        # 3. Size similarity
        try:
            size = element.size
            hist_size = historical.get("size", {})
            if hist_size:
                w_ratio = min(size.get("width", 1), hist_size.get("width", 1)) / max(
                    size.get("width", 1), hist_size.get("width", 1)
                )
                h_ratio = min(size.get("height", 1), hist_size.get("height", 1)) / max(
                    size.get("height", 1), hist_size.get("height", 1)
                )
                score += self.WEIGHTS["size"] * ((w_ratio + h_ratio) / 2)
        except Exception:
            pass

        # 4. Attribute overlap
        try:
            hist_attrs = historical.get("attributes", {})
            if hist_attrs:
                matches = 0
                total = len(hist_attrs)
                for attr_name, attr_value in hist_attrs.items():
                    current_value = element.get_attribute(attr_name)
                    if current_value == attr_value:
                        matches += 1
                    elif current_value and attr_value and attr_value in current_value:
                        matches += 0.5
                if total > 0:
                    score += self.WEIGHTS["attributes"] * (matches / total)
        except Exception:
            pass

        # 5. Text content similarity
        try:
            current_text = (element.text or "").strip()[:100]
            hist_text = (historical.get("text", "") or "").strip()[:100]
            if current_text and hist_text:
                # Simple word overlap
                current_words = set(current_text.lower().split())
                hist_words = set(hist_text.lower().split())
                if hist_words:
                    overlap = len(current_words & hist_words) / len(hist_words)
                    score += self.WEIGHTS["text"] * overlap
            elif not current_text and not hist_text:
                score += self.WEIGHTS["text"]  # Both empty = match
        except Exception:
            pass

        # 6. Parent hierarchy
        try:
            parent = element.find_element(By.XPATH, "..")
            hist_parent_tag = historical.get("parent_tag")
            if parent.tag_name == hist_parent_tag:
                score += self.WEIGHTS["parent"]
        except Exception:
            pass

        return score

    def _build_selector(self, element):
        """Build a CSS selector for the given element."""
        tag = element.tag_name
        elem_id = element.get_attribute("id")
        if elem_id:
            return f"#{elem_id}"

        classes = element.get_attribute("class")
        name = element.get_attribute("name")
        elem_type = element.get_attribute("type")
        placeholder = element.get_attribute("placeholder")

        # Try id first, then class + type, then other attributes
        if classes:
            class_selector = "." + ".".join(classes.strip().split())
            return f"{tag}{class_selector}"

        if name:
            return f'{tag}[name="{name}"]'

        if elem_type:
            return f'{tag}[type="{elem_type}"]'

        if placeholder:
            return f'{tag}[placeholder="{placeholder}"]'

        # Fallback: use tag and positional index
        return tag
