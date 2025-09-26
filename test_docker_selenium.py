#!/usr/bin/env python3
"""
Quick test script to verify Docker Selenium setup
Tests connection without running full extraction
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_docker_selenium():
    print("Testing Docker Selenium connection...")
    
    # Test 1: Check if Selenium hub is responding
    print("\\n1. Testing Selenium Hub API...")
    try:
        response = requests.get("http://localhost:4444/wd/hub/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Selenium Hub is responding")
            print(f"  Ready: {data.get('value', {}).get('ready', False)}")
            print(f"  Message: {data.get('value', {}).get('message', 'N/A')}")
        else:
            print(f"✗ Selenium Hub returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to Selenium Hub: {e}")
        print("Make sure Docker Selenium is running on port 4444")
        return False
    
    # Test 2: Create WebDriver and test basic functionality
    print("\\n2. Testing WebDriver connection...")
    try:
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            options=chrome_options
        )
        
        print("✓ WebDriver connected successfully")
        
        # Test 3: Navigate to a simple page
        print("\\n3. Testing page navigation...")
        driver.get("https://httpbin.org/html")
        title = driver.title
        print(f"✓ Successfully loaded page: '{title}'")
        
        # Test 4: Find elements
        print("\\n4. Testing element finding...")
        h1_elements = driver.find_elements("tag name", "h1")
        print(f"✓ Found {len(h1_elements)} H1 elements")
        
        driver.quit()
        print("\\n✓ All tests passed! Docker Selenium is working correctly.")
        return True
        
    except Exception as e:
        print(f"✗ WebDriver test failed: {e}")
        return False

def main():
    print("="*50)
    print("DOCKER SELENIUM CONNECTION TEST")
    print("="*50)
    
    success = test_docker_selenium()
    
    print("\\n" + "="*50)
    if success:
        print("SUCCESS: Ready to run the full feature extraction demo!")
        print("Run: python run_demo.py")
    else:
        print("FAILED: Please check Docker Selenium setup")
        print("\\nTroubleshooting:")
        print("1. Make sure Docker is running")
        print("2. Run: docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome")
        print("3. Wait a few seconds for container to start")
        print("4. Check: http://localhost:4444/wd/hub/status")
    print("="*50)

if __name__ == "__main__":
    main()