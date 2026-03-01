"""
Shadow DOM Listener
===================
Monitors for asynchronous DOM changes that can break Selenium scripts.
Injects JavaScript to observe mutations and track dynamic element changes.
"""

import logging
import json
from selenium.webdriver.common.by import By

logger = logging.getLogger("SelfHealing.ShadowDOM")


class ShadowDOMListener:
    """
    Monitors DOM mutations using MutationObserver injected via JavaScript.
    Tracks elements that are added, removed, or modified asynchronously.
    """

    OBSERVER_SCRIPT = """
    if (!window.__aresObserver) {
        window.__aresMutations = [];
        window.__aresObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                var record = {
                    type: mutation.type,
                    timestamp: new Date().toISOString(),
                    target: {
                        tag: mutation.target.tagName,
                        id: mutation.target.id || '',
                        className: mutation.target.className || ''
                    }
                };
                
                if (mutation.type === 'childList') {
                    record.addedNodes = [];
                    record.removedNodes = [];
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            record.addedNodes.push({
                                tag: node.tagName,
                                id: node.id || '',
                                className: node.className || '',
                                text: (node.textContent || '').substring(0, 50)
                            });
                        }
                    });
                    mutation.removedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            record.removedNodes.push({
                                tag: node.tagName,
                                id: node.id || '',
                                className: node.className || ''
                            });
                        }
                    });
                }
                
                if (mutation.type === 'attributes') {
                    record.attributeName = mutation.attributeName;
                    record.oldValue = mutation.oldValue;
                    record.newValue = mutation.target.getAttribute(mutation.attributeName);
                }
                
                window.__aresMutations.push(record);
                
                // Keep only last 100 mutations
                if (window.__aresMutations.length > 100) {
                    window.__aresMutations = window.__aresMutations.slice(-100);
                }
            });
        });
        
        window.__aresObserver.observe(document.body, {
            childList: true,
            attributes: true,
            subtree: true,
            attributeOldValue: true
        });
        
        return 'Observer started';
    }
    return 'Observer already running';
    """

    GET_MUTATIONS_SCRIPT = """
    return JSON.stringify(window.__aresMutations || []);
    """

    CLEAR_MUTATIONS_SCRIPT = """
    window.__aresMutations = [];
    return 'Cleared';
    """

    CHECK_ELEMENT_REMOVED = """
    var selector = arguments[0];
    var mutations = window.__aresMutations || [];
    var removed = mutations.filter(function(m) {
        if (m.type === 'childList' && m.removedNodes) {
            return m.removedNodes.some(function(n) {
                return n.id === selector.replace('#', '') ||
                       n.className.includes(selector.replace('.', ''));
            });
        }
        return false;
    });
    return JSON.stringify(removed);
    """

    def __init__(self, driver):
        self.driver = driver
        self._started = False

    def start(self):
        """Start the MutationObserver on the page."""
        result = self.driver.execute_script(self.OBSERVER_SCRIPT)
        self._started = True
        logger.info(f"Shadow DOM Listener: {result}")
        return result

    def get_mutations(self):
        """Get all recorded DOM mutations."""
        if not self._started:
            self.start()

        result = self.driver.execute_script(self.GET_MUTATIONS_SCRIPT)
        mutations = json.loads(result)
        logger.info(f"Retrieved {len(mutations)} DOM mutations")
        return mutations

    def clear_mutations(self):
        """Clear the mutation log."""
        self.driver.execute_script(self.CLEAR_MUTATIONS_SCRIPT)
        logger.info("Mutation log cleared")

    def was_element_removed(self, selector):
        """Check if a specific element was removed from the DOM."""
        result = self.driver.execute_script(self.CHECK_ELEMENT_REMOVED, selector)
        removed = json.loads(result)
        if removed:
            logger.warning(f"Element '{selector}' was removed from DOM! {len(removed)} removals detected.")
        return len(removed) > 0

    def get_attribute_changes(self, element_id):
        """Get all attribute changes for a specific element."""
        mutations = self.get_mutations()
        changes = [
            m for m in mutations
            if m["type"] == "attributes" and m["target"].get("id") == element_id
        ]
        return changes

    def wait_for_stability(self, timeout=5, check_interval=0.5):
        """Wait until the DOM stabilizes (no new mutations for a period)."""
        import time
        
        self.clear_mutations()
        time.sleep(check_interval)
        
        stable_for = 0
        elapsed = 0
        
        while elapsed < timeout:
            mutations = self.get_mutations()
            if not mutations:
                stable_for += check_interval
                if stable_for >= check_interval * 2:
                    logger.info("DOM is stable")
                    return True
            else:
                stable_for = 0
                self.clear_mutations()
            
            time.sleep(check_interval)
            elapsed += check_interval
        
        logger.warning("DOM did not stabilize within timeout")
        return False
