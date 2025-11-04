#!/usr/bin/env python3
"""
Docker Selenium Setup and Test for Joel Dataset
"""

import requests
import time
import subprocess
import sys

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is installed:", result.stdout.strip())
            return True
        else:
            print("❌ Docker is not installed")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed or not in PATH")
        return False

def start_selenium_container():
    """Start Docker Selenium container"""
    try:
        print("🐳 Starting Docker Selenium container...")
        
        # Stop any existing selenium container
        subprocess.run(['docker', 'stop', 'selenium-chrome'], capture_output=True)
        subprocess.run(['docker', 'rm', 'selenium-chrome'], capture_output=True)
        
        # Start new container
        cmd = [
            'docker', 'run', '-d',
            '-p', '4444:4444',
            '-p', '7900:7900',
            '--shm-size=2g',
            '--name', 'selenium-chrome',
            'selenium/standalone-chrome:latest'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Docker Selenium container started successfully!")
            print("🌐 Selenium Hub: http://localhost:4444")
            print("📺 VNC Viewer: http://localhost:7900 (password: secret)")
            return True
        else:
            print("❌ Failed to start Docker Selenium container:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error starting Docker Selenium: {e}")
        return False

def wait_for_selenium():
    """Wait for Selenium Hub to be ready"""
    print("⏳ Waiting for Selenium Hub to be ready...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:4444/wd/hub/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('value', {}).get('ready', False):
                    print("✅ Selenium Hub is ready!")
                    return True
        except Exception:
            pass
        
        print(f"⏳ Waiting... ({i+1}/30)")
        time.sleep(1)
    
    print("❌ Selenium Hub failed to start within 30 seconds")
    return False

def test_selenium_connection():
    """Test connection to Docker Selenium"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        
        print("🧪 Testing Docker Selenium connection...")
        
        caps = DesiredCapabilities.CHROME.copy()
        driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            desired_capabilities=caps
        )
        
        # Test navigation
        driver.get("https://www.google.com")
        title = driver.title
        
        driver.quit()
        
        print(f"✅ Test successful! Page title: {title}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🐳 Docker Selenium Setup for Joel Dataset Feature Extraction")
    print("=" * 60)
    
    # Check Docker
    if not check_docker():
        print("\n💡 Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return False
    
    # Start Selenium container
    if not start_selenium_container():
        return False
    
    # Wait for Selenium to be ready
    if not wait_for_selenium():
        return False
    
    # Test connection
    if not test_selenium_connection():
        return False
    
    print("\n🎉 Docker Selenium setup complete!")
    print("\n📋 Next steps:")
    print("1. Run: python joel_docker_selenium_extractor.py")
    print("2. Monitor progress at: http://localhost:7900 (password: secret)")
    print("3. Results will be saved to: Joel_dataset_features.csv")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)