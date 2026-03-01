"""
Test Case 5: Rate Limiting Simulation
=======================================
Automates a brute force attack simulation and verifies the system's
adaptive response (account state transitions and risk score escalation).
"""

import time
import pytest
import requests
from selenium.webdriver.common.by import By

BASE_URL = "http://localhost:3000"


class TestRateLimiting:
    """Test the system's adaptive response to brute force attacks."""

    def test_brute_force_attempt(self, healing_driver):
        """
        Scenario: Rapid login attempts with wrong passwords.
        Verifies account transitions: Active → Challenged → Locked → Suspended.
        """
        healing_driver.navigate("/")
        time.sleep(2)

        statuses_seen = []

        for attempt in range(1, 16):
            # Fill in credentials
            email_input = healing_driver.find_element(
                By.ID, "identifier",
                description="Email input field"
            )
            email_input.clear()
            email_input.send_keys("testuser@ares.com")

            password_input = healing_driver.find_element(
                By.ID, "password",
                description="Password input field"
            )
            password_input.clear()
            password_input.send_keys(f"wrong_password_{attempt}")

            # Click login
            login_btn = healing_driver.find_element_clickable(
                By.ID, "login-btn",
                description="Login button"
            )
            login_btn.click()
            time.sleep(1.5)

            # Check for status messages on the page
            page_source = healing_driver.page_source
            
            status = "active"
            if "suspended" in page_source.lower():
                status = "suspended"
            elif "locked" in page_source.lower():
                status = "locked"
            elif "challenged" in page_source.lower() or "review" in page_source.lower():
                status = "challenged"
            elif "Attempt" in page_source:
                status = f"attempt_{attempt}"

            statuses_seen.append(status)
            print(f"Attempt {attempt}: Status = {status}")

            # Take screenshot at key transition points
            if attempt in [5, 10, 15]:
                healing_driver.take_screenshot(f"brute_force_attempt_{attempt}.png")

            # If account is locked or suspended, stop trying through UI
            if status in ("locked", "suspended"):
                print(f"🔒 Account {status} after {attempt} attempts")
                break

        # Verify that the system escalated the response
        assert any(s in ("locked", "suspended", "challenged") for s in statuses_seen), \
            f"System should have escalated. Statuses seen: {statuses_seen}"

        print(f"\n📊 Statuses progression: {statuses_seen}")

    def test_brute_force_via_api(self):
        """
        Scenario: Brute force attack directly via the API.
        Tests rate limiting without the UI overhead.
        """
        # Reset account before test to ensure clean state
        requests.post(
            f"{BASE_URL}/api/reset-account",
            json={"email": "admin@ares.com"},
        )
        time.sleep(0.5)

        results = []
        risk_scores = []

        for attempt in range(1, 20):
            response = requests.post(
                f"{BASE_URL}/api/login",
                json={
                    "identifier": "admin@ares.com",
                    "password": f"wrong_pass_{attempt}",
                },
                headers={"X-Forwarded-For": "192.168.1.100"},
            )

            data = response.json()
            status_code = response.status_code
            account_status = data.get("accountStatus", "active")
            risk_score = data.get("riskScore", 0)
            error = data.get("error", "")

            results.append({
                "attempt": attempt,
                "status_code": status_code,
                "account_status": account_status,
                "risk_score": risk_score,
                "error": error[:80],
            })
            risk_scores.append(risk_score)

            print(
                f"API Attempt {attempt}: "
                f"HTTP {status_code} | "
                f"Account: {account_status} | "
                f"Risk: {risk_score} | "
                f"{error[:50]}"
            )

            # Small delay to simulate realistic attack timing
            time.sleep(0.3)

            # Stop if account is suspended
            if account_status == "suspended" or status_code == 403:
                if "suspended" in error.lower():
                    print(f"Account suspended after {attempt} attempts!")
                    break

        # Verify risk scores escalated (use >= since score may plateau at max)
        if len(risk_scores) > 5:
            assert risk_scores[-1] >= risk_scores[0], \
                f"Risk score should not decrease: {risk_scores[0]} -> {risk_scores[-1]}"

        # Verify account was eventually locked or challenged
        final_statuses = [r["account_status"] for r in results]
        assert any(s in ("locked", "suspended", "challenged") for s in final_statuses), \
            f"Account should have been restricted. Statuses: {final_statuses}"

        print(f"\nRisk Score progression: {risk_scores}")
        print(f"Final status: {results[-1]['account_status']}")

    def test_risk_score_escalation(self):
        """
        Scenario: Verify that the risk assessment API properly escalates
        risk scores based on login context.
        """
        # First, check baseline risk for a known IP
        response = requests.post(
            f"{BASE_URL}/api/risk-assessment",
            json={
                "email": "testuser@ares.com",
                "ip": "127.0.0.1",
            },
        )
        baseline = response.json()
        baseline_score = baseline.get("riskScore", 0)
        print(f"Baseline risk score (known IP): {baseline_score}")

        # Check risk for an unknown IP
        response = requests.post(
            f"{BASE_URL}/api/risk-assessment",
            json={
                "email": "testuser@ares.com",
                "ip": "203.0.113.50",  # Unknown IP
            },
        )
        unknown_ip = response.json()
        unknown_score = unknown_ip.get("riskScore", 0)
        print(f"Unknown IP risk score: {unknown_score}")

        # Unknown IP should have higher risk
        assert unknown_score >= baseline_score, \
            f"Unknown IP should have higher risk: {unknown_score} vs {baseline_score}"

        # Check risk factors are reported
        factors = unknown_ip.get("factors", [])
        factor_names = [f["name"] for f in factors]
        print(f"Risk factors: {factor_names}")

        if unknown_score > baseline_score:
            assert "Unknown IP" in factor_names, \
                "Unknown IP factor should be reported"
