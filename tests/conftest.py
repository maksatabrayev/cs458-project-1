"""
Pytest Configuration & Fixtures
================================
Shared fixtures for the self-healing Selenium test suite.
"""

import os
import sys
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Add tests directory to path
sys.path.insert(0, os.path.dirname(__file__))

from self_healing import SelfHealingDriver
from shadow_dom import ShadowDOMListener

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")


@pytest.fixture(params=["chrome"])
def healing_driver(request):
    """
    Fixture that provides a SelfHealingDriver instance.
    Selenium 4.x includes built-in Selenium Manager that
    automatically downloads the correct ChromeDriver.
    """
    browser = request.param

    if browser == "chrome":
        options = ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--headless=new")  # Uncomment for headless mode
        options.add_argument("--window-size=1280,900")
        driver = webdriver.Chrome(options=options)
    elif browser == "firefox":
        options = FirefoxOptions()
        # options.add_argument("--headless")  # Uncomment for headless mode
        driver = webdriver.Firefox(options=options)
    else:
        raise ValueError(f"Unsupported browser: {browser}")

    # Wrap with self-healing
    sh_driver = SelfHealingDriver(driver, base_url=BASE_URL)
    
    yield sh_driver

    # Teardown: print report and save
    sh_driver.save_healing_report(f"healing_report_{browser}.json")
    sh_driver.quit()


@pytest.fixture
def shadow_listener(healing_driver):
    """Fixture that provides a ShadowDOMListener attached to the driver."""
    listener = ShadowDOMListener(healing_driver.driver)
    return listener


@pytest.fixture
def chrome_driver():
    """Simple Chrome driver without self-healing (for baseline tests)."""
    options = ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()
