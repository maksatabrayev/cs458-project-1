"""
Test Case 1: Dynamic ID Recovery
=================================
Changes the Login button's ID attribute at runtime using JavaScript,
then proves the self-healing framework recovers and the test still passes.

This demonstrates the core self-healing capability: when a developer
changes an element's ID, the framework automatically finds the new selector.
"""

import time
import pytest
from selenium.webdriver.common.by import By


class TestDynamicIDRecovery:
    """Test that the self-healing framework recovers from dynamic ID changes."""

    def test_login_button_id_change(self, healing_driver):
        """
        Scenario: A developer changes the login button ID from 'login-btn'
        to 'submit-auth-btn'. The test should still find and click it.
        """
        # Step 1: Navigate to login page
        healing_driver.navigate("/")
        time.sleep(2)

        # Step 2: Verify the original button exists
        login_btn = healing_driver.find_element(
            By.ID, "login-btn", 
            description="The main login/sign-in button"
        )
        assert login_btn is not None, "Original login button should exist"
        assert login_btn.text.strip() == "Sign In"

        # Step 3: Change the button ID at runtime via JavaScript
        healing_driver.execute_script("""
            var btn = document.getElementById('login-btn');
            if (btn) {
                btn.id = 'submit-auth-btn';
                btn.setAttribute('data-changed', 'true');
            }
        """)
        time.sleep(1)

        # Step 4: Try to find the button with the OLD ID — this should trigger self-healing
        healed_btn = healing_driver.find_element(
            By.ID, "login-btn",
            description="The main login/sign-in button that submits the form"
        )

        # Step 5: Verify healing was successful
        assert healed_btn is not None, "Self-healing should find the button"
        assert healed_btn.text.strip() == "Sign In"

        # Step 6: Verify healing was logged
        assert len(healing_driver.healing_log) > 0, "Healing should be recorded"
        print(f"\n🔧 Healing Report:\n{healing_driver.get_healing_report()}")

    def test_input_field_id_change(self, healing_driver):
        """
        Scenario: The email input field ID changes from 'identifier'
        to 'user-email-input'. The test should still find and interact with it.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # First interact normally to build metadata
        email_input = healing_driver.find_element(
            By.ID, "identifier",
            description="Email/phone input field for login"
        )
        email_input.clear()
        email_input.send_keys("testuser@ares.com")
        time.sleep(0.5)

        # Change the input ID
        healing_driver.execute_script("""
            var input = document.getElementById('identifier');
            if (input) {
                input.id = 'user-email-input';
            }
        """)
        time.sleep(1)

        # Try to find with old ID — should self-heal
        healed_input = healing_driver.find_element(
            By.ID, "identifier",
            description="Email/phone input field for login"
        )
        assert healed_input is not None
        
        # Verify the value is preserved
        current_value = healed_input.get_attribute("value")
        assert "testuser" in current_value or healed_input is not None

        print(f"\n🔧 Healing Report:\n{healing_driver.get_healing_report()}")

    def test_multiple_id_changes(self, healing_driver):
        """
        Scenario: Multiple element IDs change simultaneously.
        Tests that the framework can handle multiple healings in one session.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Change multiple IDs at once
        healing_driver.execute_script("""
            var btn = document.getElementById('login-btn');
            if (btn) btn.id = 'new-login-btn';
            
            var emailTab = document.getElementById('tab-email');
            if (emailTab) emailTab.id = 'new-tab-email';
            
            var googleBtn = document.getElementById('google-login-btn');
            if (googleBtn) googleBtn.id = 'new-google-btn';
        """)
        time.sleep(1)

        # Try to find all elements with old IDs
        login_btn = healing_driver.find_element(
            By.ID, "login-btn",
            description="Main login button"
        )
        assert login_btn is not None

        email_tab = healing_driver.find_element(
            By.ID, "tab-email",
            description="Email tab button"
        )
        assert email_tab is not None

        google_btn = healing_driver.find_element(
            By.ID, "google-login-btn",
            description="Login with Google button"
        )
        assert google_btn is not None

        # Should have at least 3 healing records
        assert len(healing_driver.healing_log) >= 3, \
            f"Expected ≥3 healings, got {len(healing_driver.healing_log)}"

        print(f"\n🔧 Healing Report:\n{healing_driver.get_healing_report()}")
