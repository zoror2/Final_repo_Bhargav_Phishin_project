import pandas as pd
import json
import time
import ssl
import socket
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from datetime import datetime

class URLEventLogger:
    def __init__(self, use_remote=True, remote_url="http://localhost:4444/wd/hub"):
        """
        Initialize the event logger
        use_remote: True to use Docker container, False for local browser
        """
        self.use_remote = use_remote
        self.remote_url = remote_url
        self.driver = None
        self.events = []
        
    def setup_driver(self):
        """Setup Edge driver (local or remote)"""
        from selenium.webdriver.edge.options import Options as EdgeOptions
        
        options = EdgeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            if self.use_remote:
                # Use Docker container
                self.driver = webdriver.Remote(
                    command_executor=self.remote_url,
                    options=options
                )
            else:
                # Use local Edge (fallback)
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                from selenium.webdriver.edge.service import Service
                
                service = Service(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=options)
                
            print("✅ WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            return False
    
    def log_event(self, event_type, timestamp=None, **kwargs):
        """Log an event with timestamp"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)  # milliseconds
            
        event = {
            "event_type": event_type,
            "timestamp": timestamp,
            **kwargs
        }
        self.events.append(event)
        
    def check_ssl_certificate(self, url):
        """Check SSL certificate validity"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme == 'https':
                hostname = parsed_url.hostname
                port = parsed_url.port or 443
                
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        self.log_event("ssl_valid", cert_subject=str(cert.get('subject', '')))
                        return True
        except Exception as e:
            self.log_event("ssl_invalid", error=str(e))
            return False
    
    def count_external_requests(self, url, logs):
        """Count requests to external domains"""
        try:
            main_domain = urlparse(url).netloc
            external_count = 0
            
            for log_entry in logs:
                if log_entry['level'] == 'INFO' and 'message' in log_entry:
                    message = log_entry['message']
                    # Look for network requests in logs
                    if 'Network.requestWillBeSent' in message:
                        try:
                            import json
                            log_data = json.loads(message)
                            request_url = log_data.get('message', {}).get('params', {}).get('request', {}).get('url', '')
                            if request_url:
                                request_domain = urlparse(request_url).netloc
                                if request_domain and request_domain != main_domain:
                                    external_count += 1
                        except:
                            pass
            
            self.log_event("external_requests", count=external_count)
            return external_count
            
        except Exception as e:
            self.log_event("external_requests", count=0, error=str(e))
            return 0
    
    def analyze_page_content(self):
        """Analyze page content for suspicious elements"""
        try:
            # Count forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            self.log_event("forms_detected", count=len(forms))
            
            # Count password fields
            password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            self.log_event("password_fields", count=len(password_fields))
            
            # Count iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.log_event("iframes_detected", count=len(iframes))
            
            # Count scripts
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            self.log_event("scripts_detected", count=len(scripts))
            
            # Check for suspicious keywords in title/text
            title = self.driver.title.lower()
            suspicious_keywords = ['login', 'verify', 'account', 'suspended', 'urgent', 'click here']
            suspicious_count = sum(1 for keyword in suspicious_keywords if keyword in title)
            self.log_event("suspicious_keywords", count=suspicious_count)
            
        except Exception as e:
            self.log_event("content_analysis_error", error=str(e))
    
    def log_url_events(self, url, timeout=30):
        """Log all events for a single URL"""
        self.events = []  # Reset events for this URL
        start_time = time.time()
        
        print(f"🔍 Analyzing: {url}")
        
        try:
            # Check SSL before visiting
            if url.startswith('https'):
                self.check_ssl_certificate(url)
            
            # Navigate to URL and track redirects
            original_url = url
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            final_url = self.driver.current_url
            
            # Count redirects
            redirect_count = 0 if original_url == final_url else 1
            self.log_event("redirects", count=redirect_count, final_url=final_url)
            
            # Get browser logs for network analysis
            try:
                logs = self.driver.get_log('performance')
                self.count_external_requests(url, logs)
            except:
                self.log_event("external_requests", count=0, error="Could not get logs")
            
            # Analyze page content
            self.analyze_page_content()
            
            # Page load time
            load_time = int((time.time() - start_time) * 1000)
            self.log_event("page_load_time", duration_ms=load_time)
            
            print(f"✅ Completed analysis in {load_time}ms")
            return True
            
        except TimeoutException:
            self.log_event("timeout_error", duration_ms=timeout*1000)
            print(f"⏰ Timeout after {timeout}s")
            return False
            
        except WebDriverException as e:
            self.log_event("webdriver_error", error=str(e))
            print(f"❌ WebDriver error: {e}")
            return False
            
        except Exception as e:
            self.log_event("general_error", error=str(e))
            print(f"❌ Error: {e}")
            return False
    
    def process_dataset(self, csv_file="urls_dataset.csv", output_file="events_dataset.json", max_urls=None):
        """Process entire dataset and save events"""
        
        if not self.setup_driver():
            print("❌ Failed to setup driver")
            return
        
        try:
            # Load dataset
            df = pd.read_csv(csv_file)
            print(f"📂 Loaded {len(df)} URLs from {csv_file}")
            
            if max_urls:
                df = df.head(max_urls)
                print(f"🔢 Processing first {max_urls} URLs")
            
            all_events = []
            processed = 0
            
            for index, row in df.iterrows():
                url = row['url']
                label = row['label']
                
                print(f"\n[{index+1}/{len(df)}] Processing: {url[:60]}...")
                
                success = self.log_url_events(url)
                
                # Save events for this URL
                url_data = {
                    "url": url,
                    "label": label,
                    "success": success,
                    "events": self.events.copy()
                }
                
                all_events.append(url_data)
                processed += 1
                
                # Save progress every 100 URLs
                if processed % 100 == 0:
                    with open(output_file, 'w') as f:
                        json.dump(all_events, f, indent=2)
                    print(f"💾 Saved progress: {processed} URLs processed")
                
                # Small delay to be respectful
                time.sleep(1)
            
            # Final save
            with open(output_file, 'w') as f:
                json.dump(all_events, f, indent=2)
            
            print(f"\n✅ Event logging complete!")
            print(f"📊 Processed: {processed} URLs")
            print(f"💾 Saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error processing dataset: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                print("🚪 Browser closed")

def main():
    """Main function to run event logging"""
    # Create logger instance
    logger = URLEventLogger(use_remote=True)  # Set to False if Docker not working
    
    # Process all URLs for comprehensive training data
    logger.process_dataset(
        csv_file="urls_dataset.csv",
        output_file="events_dataset_full.json",
        max_urls=None  # Process ALL 20,000 URLs
    )

if __name__ == "__main__":
    main()