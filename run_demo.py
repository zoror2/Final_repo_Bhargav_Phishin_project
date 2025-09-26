#!/usr/bin/env python3
"""
Complete Docker Selenium Demo Setup Script
Automates the entire process: dataset creation -> Docker setup check -> feature extraction
"""

import subprocess
import time
import sys
import os
import requests
import json

class DockerSeleniumDemo:
    def __init__(self):
        self.docker_container_name = "selenium-chrome"
        self.selenium_url = "http://localhost:4444"
        
    def check_docker_running(self):
        """Check if Docker is running"""
        print("Checking Docker status...")
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, text=True, check=True
            )
            print(f"✓ Docker is available: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Docker is not available or not running")
            print("Please install Docker Desktop and make sure it's running")
            return False
    
    def setup_docker_selenium(self):
        """Setup Docker Selenium container"""
        print("\\nSetting up Docker Selenium...")
        
        # Check if container already exists
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.docker_container_name}", "--format", "{{.Names}}"],
                capture_output=True, text=True
            )
            
            if self.docker_container_name in result.stdout:
                print("Docker Selenium container already exists. Stopping and removing...")
                subprocess.run(["docker", "stop", self.docker_container_name], capture_output=True)
                subprocess.run(["docker", "rm", self.docker_container_name], capture_output=True)
        except:
            pass
        
        # Pull latest image
        print("Pulling Selenium Chrome image...")
        try:
            subprocess.run(
                ["docker", "pull", "selenium/standalone-chrome:latest"],
                check=True
            )
            print("✓ Selenium Chrome image pulled successfully")
        except subprocess.CalledProcessError:
            print("✗ Failed to pull Selenium image")
            return False
        
        # Run container
        print("Starting Selenium Chrome container...")
        try:
            subprocess.run([
                "docker", "run", "-d",
                "-p", "4444:4444",
                "-p", "7900:7900", 
                "--shm-size=2g",
                "--name", self.docker_container_name,
                "selenium/standalone-chrome:latest"
            ], check=True)
            print("✓ Selenium Chrome container started")
            print("  WebDriver API: http://localhost:4444")
            print("  VNC Viewer: http://localhost:7900 (password: secret)")
        except subprocess.CalledProcessError:
            print("✗ Failed to start Selenium container")
            return False
        
        return True
    
    def wait_for_selenium(self, max_wait=60):
        """Wait for Selenium to be ready"""
        print("\\nWaiting for Selenium to be ready...")
        
        for i in range(max_wait):
            try:
                response = requests.get(f"{self.selenium_url}/wd/hub/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('value', {}).get('ready', False):
                        print(f"✓ Selenium is ready after {i+1} seconds")
                        return True
            except:
                pass
            
            print(f"  Waiting... ({i+1}/{max_wait})")
            time.sleep(1)
        
        print("✗ Selenium failed to start within timeout")
        return False
    
    def install_requirements(self):
        """Install Python requirements"""
        print("\\nInstalling Python requirements...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "selenium_requirements.txt"
            ], check=True)
            print("✓ Requirements installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install requirements")
            return False
    
    def run_demo(self):
        """Run the complete demo"""
        print("="*70)
        print("DOCKER SELENIUM PHISHING DETECTION DEMO")
        print("="*70)
        print("This demo will:")
        print("1. Create a small balanced dataset (10 legit + 10 phishing URLs)")
        print("2. Setup Docker Selenium Chrome container") 
        print("3. Extract features from URLs using web scraping")
        print("4. Save results for machine learning")
        print("="*70)
        
        # Step 1: Check Docker
        if not self.check_docker_running():
            return False
        
        # Step 2: Create small dataset if it doesn't exist
        if not os.path.exists('small_dataset.csv'):
            print("\\nCreating small dataset...")
            try:
                subprocess.run([sys.executable, "create_small_dataset.py"], check=True)
                print("✓ Small dataset created")
            except subprocess.CalledProcessError:
                print("✗ Failed to create small dataset")
                return False
        else:
            print("\\n✓ Small dataset already exists")
        
        # Step 3: Install requirements
        if not self.install_requirements():
            return False
        
        # Step 4: Setup Docker Selenium
        if not self.setup_docker_selenium():
            return False
        
        # Step 5: Wait for Selenium to be ready
        if not self.wait_for_selenium():
            return False
        
        # Step 6: Run feature extraction
        print("\\n" + "="*70)
        print("Starting feature extraction...")
        print("You can monitor the browser activity at: http://localhost:7900")
        print("VNC password: secret")
        print("="*70)
        
        try:
            subprocess.run([sys.executable, "docker_selenium_extractor.py"], check=True)
            print("\\n✓ Feature extraction completed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("\\n✗ Feature extraction failed")
            return False
    
    def cleanup(self):
        """Cleanup Docker resources"""
        print("\\nCleaning up Docker resources...")
        try:
            subprocess.run(["docker", "stop", self.docker_container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.docker_container_name], capture_output=True)
            print("✓ Docker container cleaned up")
        except:
            print("! Docker cleanup had issues (container may not exist)")
    
    def show_results_summary(self):
        """Show summary of extracted results"""
        try:
            # Read extraction report
            if os.path.exists('extraction_report.json'):
                with open('extraction_report.json', 'r') as f:
                    report = json.load(f)
                
                print("\\n" + "="*70)
                print("EXTRACTION RESULTS SUMMARY")
                print("="*70)
                print(f"Total URLs processed: {report['total_urls']}")
                print(f"Successful extractions: {report['successful_extractions']}")
                print(f"Failed extractions: {report['failed_extractions']}")
                print(f"Success rate: {report['success_rate_percent']}%")
                
                print("\\nFiles created:")
                if os.path.exists('small_dataset.csv'):
                    print("  ✓ small_dataset.csv - Input dataset (20 URLs)")
                if os.path.exists('extracted_features.csv'):
                    print("  ✓ extracted_features.csv - ML-ready features")
                if os.path.exists('extraction_report.json'):
                    print("  ✓ extraction_report.json - Detailed log")
                
                print("\\nNext steps for your team:")
                print("  • Review the extracted features in extracted_features.csv")
                print("  • Use features to train phishing detection models")
                print("  • Scale up to larger datasets using the same approach")
                print("  • Customize feature extraction based on your needs")
                
        except Exception as e:
            print(f"Could not load results summary: {e}")

def main():
    demo = DockerSeleniumDemo()
    
    try:
        success = demo.run_demo()
        
        if success:
            demo.show_results_summary()
            
            # Ask user if they want to keep the Docker container running
            print("\\n" + "="*70)
            response = input("Keep Docker Selenium running for manual testing? (y/N): ").lower()
            if response != 'y':
                demo.cleanup()
            else:
                print("Docker container kept running. You can:")
                print("  • View browser: http://localhost:7900 (password: secret)")
                print("  • Stop later with: docker stop selenium-chrome")
        else:
            demo.cleanup()
            
    except KeyboardInterrupt:
        print("\\n\\nDemo interrupted by user")
        demo.cleanup()
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
        demo.cleanup()

if __name__ == "__main__":
    main()