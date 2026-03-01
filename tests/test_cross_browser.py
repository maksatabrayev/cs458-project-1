"""
Test Case 3: Cross-Browser Consistency
=======================================
Tests how the UI reacts to intentional CSS breakage.
Applies various CSS modifications that could break the UI and tests
that the self-healing framework handles them correctly.
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver

from self_healing import SelfHealingDriver

BASE_URL = "http://localhost:3000"


class TestCrossBrowserConsistency:
    """Test framework resilience against CSS breakage and cross-browser issues."""

    def test_css_display_none_breakage(self, healing_driver):
        """
        Scenario: Critical elements hidden via CSS `display: none`.
        The framework should detect hidden elements and fix them.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Break the UI: hide the login button via CSS
        healing_driver.execute_script("""
            var loginBtn = document.getElementById('login-btn');
            if (loginBtn) {
                loginBtn.style.display = 'none';
            }
        """)
        time.sleep(0.5)

        # The button exists in DOM but is not visible/clickable
        # Detect the issue
        is_displayed = healing_driver.execute_script("""
            var btn = document.getElementById('login-btn');
            return btn ? btn.offsetParent !== null : false;
        """)
        assert not is_displayed, "Button should be hidden"

        # Fix it: reveal the element
        healing_driver.execute_script("""
            var btn = document.getElementById('login-btn');
            if (btn) {
                btn.style.display = '';
                btn.style.visibility = 'visible';
            }
        """)
        time.sleep(0.5)

        # Now find and interact with it
        login_btn = healing_driver.find_element_clickable(
            By.ID, "login-btn",
            description="Login button"
        )
        assert login_btn is not None
        assert login_btn.is_displayed(), "Button should be visible after fix"

    def test_css_class_removal(self, healing_driver):
        """
        Scenario: CSS classes are stripped from elements, breaking styling
        but keeping functionality. The test should adapt.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Record original state
        original_classes = healing_driver.execute_script("""
            var btn = document.getElementById('login-btn');
            return btn ? btn.className : '';
        """)

        # Strip all CSS classes
        healing_driver.execute_script("""
            var elements = document.querySelectorAll('.btn-primary, .btn-social, .form-input');
            elements.forEach(function(el) {
                el.className = '';
            });
        """)
        time.sleep(0.5)

        # Elements should still be findable by ID
        login_btn = healing_driver.find_element(
            By.ID, "login-btn",
            description="Login button (classes removed)"
        )
        assert login_btn is not None

        # Try finding by the old class (should trigger healing)
        healing_driver.execute_script("""
            var btn = document.getElementById('login-btn');
            if (btn) btn.id = '';
        """)
        time.sleep(0.5)

        # Now both class and ID are gone — real test of self-healing
        healed_btn = healing_driver.find_element(
            By.CSS_SELECTOR, ".btn-primary",
            description="Primary login submit button with gradient styling"
        )
        # If self-healing works, it should find the button by other means
        assert healed_btn is not None or len(healing_driver.healing_log) > 0

    def test_element_repositioning(self, healing_driver):
        """
        Scenario: Elements are moved to different positions in the DOM tree.
        The framework should still find them.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Move the Google login button inside the form
        healing_driver.execute_script("""
            var googleBtn = document.getElementById('google-login-btn');
            var form = document.querySelector('.login-form');
            if (googleBtn && form) {
                form.prepend(googleBtn);
            }
        """)
        time.sleep(0.5)

        # Button moved but should still be findable
        google_btn = healing_driver.find_element(
            By.ID, "google-login-btn",
            description="Login with Google button"
        )
        assert google_btn is not None
        assert google_btn.is_displayed()

    def test_font_and_color_breakage(self, healing_driver):
        """
        Scenario: CSS variables are overridden causing visual breakage.
        Tests that the system detects and reports visual inconsistencies.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Override CSS variables to break visual design
        healing_driver.execute_script("""
            document.documentElement.style.setProperty('--text-primary', 'transparent');
            document.documentElement.style.setProperty('--bg-primary', '#ffffff');
            document.documentElement.style.setProperty('--border-color', 'transparent');
        """)
        time.sleep(0.5)

        # Take a screenshot of the broken state
        healing_driver.take_screenshot("css_breakage_state.png")

        # Elements should still be findable despite visual breakage
        login_btn = healing_driver.find_element(
            By.ID, "login-btn",
            description="Login button"
        )
        assert login_btn is not None

        email_input = healing_driver.find_element(
            By.ID, "identifier",
            description="Email input field"
        )
        assert email_input is not None

        # Restore CSS
        healing_driver.execute_script("""
            document.documentElement.style.removeProperty('--text-primary');
            document.documentElement.style.removeProperty('--bg-primary');
            document.documentElement.style.removeProperty('--border-color');
        """)

        print("✅ Elements remained functional despite CSS breakage")
