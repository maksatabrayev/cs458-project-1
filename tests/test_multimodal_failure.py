"""
Test Case 2: Multimodal Failure
================================
A scenario where the "Login with Google" button is obscured by a dynamic popup.
The LLM must decide to close the popup first, then click the button.

This tests the framework's ability to handle complex, multi-step failures
where the element exists but isn't interactable.
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException


class TestMultimodalFailure:
    """Test self-healing when elements are obscured by dynamic popups."""

    def test_popup_obscures_google_login(self, healing_driver, shadow_listener):
        """
        Scenario: A cookie consent popup appears and covers the Google login button.
        The test must close the popup first, then proceed to click Google login.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Start monitoring DOM changes
        shadow_listener.start()

        # Trigger the popup overlay
        healing_driver.execute_script("""
            var triggerBtn = document.getElementById('trigger-popup-btn');
            if (triggerBtn) triggerBtn.click();
        """)
        time.sleep(1)

        # Verify popup appeared
        mutations = shadow_listener.get_mutations()
        assert len(mutations) > 0, "DOM mutations should be detected when popup appears"

        # Baseline: direct click should be blocked by popup
        try:
            google_btn = healing_driver.driver.find_element(By.ID, "google-login-btn")
            google_btn.click()
            # If we get here without error, the popup didn't block it (unexpected)
            pytest.skip("Popup did not block the button click")
        except ElementClickInterceptedException:
            # Expected! The popup is blocking the click.
            pass

        # Intelligent multimodal recovery:
        # LLM should identify blocker dismissal action, then retry click.
        healing_driver.click_element_resilient(
            By.ID,
            "google-login-btn",
            description="Click Google login button while popup may block the interaction",
        )
        time.sleep(1)

        # Verify popup is gone
        popups = healing_driver.driver.find_elements(By.ID, "dynamic-popup-overlay")
        assert len(popups) == 0, "Popup should be dismissed"

        # Verify multimodal healing was logged
        assert len(healing_driver.healing_log) > 0, "Multimodal healing event should be recorded"

        print("✅ Successfully handled multimodal failure: popup → close → click")

    def test_popup_with_changed_close_button(self, healing_driver):
        """
        Scenario: Popup appears WITH the close button having a different ID.
        Both the popup detection and close button finding require healing.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Trigger popup
        healing_driver.execute_script("""
            var triggerBtn = document.getElementById('trigger-popup-btn');
            if (triggerBtn) triggerBtn.click();
        """)
        time.sleep(1)

        # Change the close button's ID
        healing_driver.execute_script("""
            var closeBtn = document.getElementById('close-popup-btn');
            if (closeBtn) {
                closeBtn.id = 'accept-cookies-btn';
                closeBtn.textContent = 'Got it!';
            }
        """)
        time.sleep(0.5)

        # Try to find close button with old ID — should self-heal
        close_btn = healing_driver.find_element(
            By.ID, "close-popup-btn",
            description="Button to accept cookies and close the popup overlay"
        )
        assert close_btn is not None, "Healed close button should be found"
        close_btn.click()
        time.sleep(1)

        # Verify popup is closed and we can interact with login form
        login_btn = healing_driver.find_element(
            By.ID, "login-btn",
            description="Main login button"
        )
        assert login_btn is not None

        # Check healing happened
        assert len(healing_driver.healing_log) > 0
        print(f"\n🔧 Healing Report:\n{healing_driver.get_healing_report()}")

    def test_multiple_overlapping_popups(self, healing_driver):
        """
        Scenario: Multiple dynamic elements appear, requiring the LLM
        to determine the correct order of interaction.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Inject a second popup on top of the first
        healing_driver.execute_script("""
            // First popup
            var triggerBtn = document.getElementById('trigger-popup-btn');
            if (triggerBtn) triggerBtn.click();
            
            // Second overlay (notification banner)
            var banner = document.createElement('div');
            banner.id = 'notification-banner';
            banner.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:15px;background:rgba(99,102,241,0.9);color:white;text-align:center;z-index:2000;';
            banner.innerHTML = '<span>System maintenance scheduled</span> <button id="dismiss-banner" style="margin-left:10px;padding:5px 15px;border:1px solid white;background:transparent;color:white;border-radius:5px;cursor:pointer;">Dismiss</button>';
            document.body.appendChild(banner);
        """)
        time.sleep(1)

        # Step 1: Handle the top-most element first (banner)
        dismiss_btn = healing_driver.find_element(
            By.ID, "dismiss-banner",
            description="Dismiss button for notification banner"
        )
        dismiss_btn.click()
        time.sleep(0.5)

        # Step 2: Handle the popup
        close_popup = healing_driver.find_element(
            By.ID, "close-popup-btn",
            description="Close button for cookie popup"
        )
        close_popup.click()
        time.sleep(0.5)

        # Step 3: Verify login form is accessible
        login_btn = healing_driver.find_element(
            By.ID, "login-btn",
            description="Main login button"
        )
        assert login_btn is not None
        print("✅ Successfully navigated multiple overlapping elements")
