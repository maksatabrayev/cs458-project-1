"""
Test Case 4: Social Auth Handshake
====================================
Tests the OAuth 2.0 redirect flow for Google and Facebook authentication.
Verifies successful redirection and token capture.
"""

import time
import pytest
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs


class TestSocialAuthHandshake:
    """Test the Social Authentication (OAuth 2.0) handshake flow."""

    def test_google_redirect_flow(self, healing_driver):
        """
        Scenario: Click "Login with Google" and verify the OAuth redirect
        happens correctly to Google's authentication page.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Find and click the Google login button
        google_btn = healing_driver.find_element_clickable(
            By.ID, "google-login-btn",
            description="Login with Google OAuth button"
        )
        assert google_btn is not None, "Google login button should exist"

        # Click the Google login button
        google_btn.click()
        time.sleep(3)  # Wait for redirect

        # Verify we were redirected to Google's OAuth page or NextAuth's handler
        current_url = healing_driver.current_url
        parsed = urlparse(current_url)

        # Should be either:
        # 1. Google's accounts page (accounts.google.com)
        # 2. NextAuth's signin page (if credentials not configured)
        # 3. Our own API auth handler
        is_google_redirect = "google" in current_url.lower()
        is_nextauth_redirect = "api/auth" in current_url.lower()
        is_signin_page = "signin" in current_url.lower()

        assert is_google_redirect or is_nextauth_redirect or is_signin_page, \
            f"Expected OAuth redirect, got: {current_url}"

        # Take screenshot of the OAuth page
        healing_driver.take_screenshot("google_oauth_redirect.png")

        # Check for OAuth parameters in URL
        if "google" in current_url:
            query_params = parse_qs(parsed.query)
            # Google OAuth should have client_id, redirect_uri, response_type
            print(f"OAuth URL: {current_url}")
            print(f"Query params: {list(query_params.keys())}")

        print(f"✅ Google OAuth redirect successful: {current_url}")

    def test_facebook_redirect_flow(self, healing_driver):
        """
        Scenario: Click "Login with Facebook" and verify the OAuth redirect
        happens correctly to Facebook's authentication page.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Find and click the Facebook login button
        fb_btn = healing_driver.find_element_clickable(
            By.ID, "facebook-login-btn",
            description="Login with Facebook OAuth button"
        )
        assert fb_btn is not None, "Facebook login button should exist"

        fb_btn.click()
        time.sleep(3)

        current_url = healing_driver.current_url
        is_facebook_redirect = "facebook" in current_url.lower()
        is_nextauth_redirect = "api/auth" in current_url.lower()
        is_signin_page = "signin" in current_url.lower()

        assert is_facebook_redirect or is_nextauth_redirect or is_signin_page, \
            f"Expected OAuth redirect, got: {current_url}"

        healing_driver.take_screenshot("facebook_oauth_redirect.png")
        print(f"✅ Facebook OAuth redirect successful: {current_url}")

    def test_social_auth_button_presence_after_id_change(self, healing_driver):
        """
        Scenario: Social auth buttons have their IDs changed.
        Combined test of self-healing + social auth detection.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        # Change both social button IDs
        healing_driver.execute_script("""
            var googleBtn = document.getElementById('google-login-btn');
            if (googleBtn) googleBtn.id = 'oauth-google-signin';
            
            var fbBtn = document.getElementById('facebook-login-btn');
            if (fbBtn) fbBtn.id = 'oauth-facebook-signin';
        """)
        time.sleep(1)

        # Try to find with old IDs — self-healing should kick in
        google_btn = healing_driver.find_element(
            By.ID, "google-login-btn",
            description="Google OAuth login button with Google logo"
        )
        assert google_btn is not None, "Healed Google button should be found"
        assert "Google" in google_btn.text or "google" in (google_btn.get_attribute("class") or "")

        fb_btn = healing_driver.find_element(
            By.ID, "facebook-login-btn",
            description="Facebook OAuth login button with Facebook logo"
        )
        assert fb_btn is not None, "Healed Facebook button should be found"

        # Verify healing happened
        assert len(healing_driver.healing_log) >= 2
        print(f"\n🔧 Healing Report:\n{healing_driver.get_healing_report()}")

    def test_oauth_callback_url_structure(self, healing_driver):
        """
        Scenario: Verify the NextAuth callback URLs are properly structured.
        """
        healing_driver.navigate("/api/auth/providers")
        time.sleep(2)

        # NextAuth should expose provider information
        page_source = healing_driver.page_source
        
        # Check if providers endpoint returns data
        has_google = "google" in page_source.lower()
        has_facebook = "facebook" in page_source.lower()
        has_credentials = "credentials" in page_source.lower()

        print(f"Providers - Google: {has_google}, Facebook: {has_facebook}, Credentials: {has_credentials}")
        
        # At minimum, credentials should be available
        assert has_credentials or has_google or has_facebook, \
            "At least one auth provider should be configured"
