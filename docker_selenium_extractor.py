#!/usr/bin/env python3
"""
Docker Selenium Feature Extractor for Phishing Detection Demo
Extracts features from URLs in small_dataset.csv using Docker Selenium
"""

import pandas as pd
import json
import time
import re
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import socket
import requests

class DockerSeleniumExtractor:
    def __init__(self, selenium_hub_url="http://localhost:4444/wd/hub"):
        """Initialize the Docker Selenium extractor"""
        self.selenium_hub_url = selenium_hub_url
        self.driver = None
        self.features = []
        self.extraction_log = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver to connect to Docker Selenium"""
        print("Setting up Chrome WebDriver for Docker Selenium...")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Remote(
                command_executor=self.selenium_hub_url,
                options=chrome_options
            )
            self.driver.set_page_load_timeout(30)
            print("✓ WebDriver connected to Docker Selenium successfully!")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Docker Selenium: {e}")
            print("Make sure Docker Selenium is running on port 4444")
            return False
    
    def extract_url_features(self, url):
        """Extract URL-based features without web scraping"""
        features = {}
        
        # Basic URL features
        features['url_length'] = len(url)
        features['num_dots'] = url.count('.')
        features['num_slashes'] = url.count('/')
        features['num_hyphens'] = url.count('-')
        features['num_underscores'] = url.count('_')
        features['num_question_marks'] = url.count('?')
        features['num_equal_signs'] = url.count('=')
        features['num_ampersands'] = url.count('&')
        
        # Parse URL components
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path
            query = parsed.query
            
            features['domain_length'] = len(domain)
            features['path_length'] = len(path)
            features['query_length'] = len(query)
            features['has_query'] = 1 if query else 0
            features['is_https'] = 1 if parsed.scheme == 'https' else 0
            features['has_port'] = 1 if ':' in domain and not domain.startswith('[') else 0
            
        except Exception:
            features['domain_length'] = 0
            features['path_length'] = 0
            features['query_length'] = 0
            features['has_query'] = 0
            features['is_https'] = 0
            features['has_port'] = 0
            domain = ""
        
        # IP address detection
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        features['has_ip_address'] = 1 if re.search(ip_pattern, url) else 0
        
        # Suspicious keywords
        suspicious_keywords = [
            'login', 'signin', 'account', 'verify', 'secure', 'update', 
            'confirm', 'suspend', 'limited', 'alert', 'warning', 'urgent',
            'click', 'here', 'now', 'immediately', 'expire', 'phish'
        ]
        
        url_lower = url.lower()
        features['suspicious_keywords'] = sum(1 for keyword in suspicious_keywords if keyword in url_lower)
        
        # Domain features
        if domain:
            features['domain_has_numbers'] = 1 if re.search(r'\d', domain) else 0
            features['domain_has_hyphens'] = 1 if '-' in domain else 0
            features['subdomain_count'] = len(domain.split('.')) - 2 if len(domain.split('.')) > 2 else 0
        else:
            features['domain_has_numbers'] = 0
            features['domain_has_hyphens'] = 0
            features['subdomain_count'] = 0
            
        return features
    
    def extract_web_features(self, url, timeout=15):
        """Extract web-based features using Selenium"""
        features = {}
        start_time = time.time()
        
        try:
            print(f"  Loading page: {url[:50]}{'...' if len(url) > 50 else ''}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Basic page info
            features['page_loaded'] = 1
            features['page_title_length'] = len(self.driver.title)
            features['response_time'] = time.time() - start_time
            
            # Count HTML elements
            features['num_forms'] = len(self.driver.find_elements(By.TAG_NAME, "form"))
            features['num_links'] = len(self.driver.find_elements(By.TAG_NAME, "a"))
            features['num_images'] = len(self.driver.find_elements(By.TAG_NAME, "img"))
            features['num_inputs'] = len(self.driver.find_elements(By.TAG_NAME, "input"))
            features['num_buttons'] = len(self.driver.find_elements(By.TAG_NAME, "button"))
            features['num_iframes'] = len(self.driver.find_elements(By.TAG_NAME, "iframe"))
            
            # Check for password inputs
            password_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            features['has_password_field'] = 1 if password_inputs else 0
            
            # Check for external links
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            external_links = 0
            for link in all_links[:10]:  # Check first 10 links to avoid timeout
                try:
                    href = link.get_attribute('href')
                    if href and not href.startswith(url.split('/')[2]):
                        external_links += 1
                except:
                    pass
            features['num_external_links'] = external_links
            
            # Check page source features
            page_source = self.driver.page_source
            features['page_size'] = len(page_source)
            features['has_javascript'] = 1 if '<script' in page_source else 0
            features['has_css'] = 1 if '<style' in page_source or 'css' in page_source.lower() else 0
            
            print(f"  ✓ Successfully extracted web features ({features['response_time']:.2f}s)")
            
        except TimeoutException:
            print(f"  ✗ Page load timeout after {timeout}s")
            features.update(self._get_default_web_features())
            features['page_loaded'] = 0
            features['response_time'] = timeout
            
        except WebDriverException as e:
            print(f"  ✗ WebDriver error: {str(e)[:50]}...")
            features.update(self._get_default_web_features())
            features['page_loaded'] = 0
            features['response_time'] = time.time() - start_time
            
        except Exception as e:
            print(f"  ✗ Unexpected error: {str(e)[:50]}...")
            features.update(self._get_default_web_features())
            features['page_loaded'] = 0
            features['response_time'] = time.time() - start_time
        
        return features
    
    def _get_default_web_features(self):
        """Return default values for web features when extraction fails"""
        return {
            'page_title_length': 0,
            'num_forms': 0,
            'num_links': 0,
            'num_images': 0,
            'num_inputs': 0,
            'num_buttons': 0,
            'num_iframes': 0,
            'has_password_field': 0,
            'num_external_links': 0,
            'page_size': 0,
            'has_javascript': 0,
            'has_css': 0
        }
    
    def extract_features_from_dataset(self, csv_file='small_dataset.csv'):
        """Extract features from all URLs in the dataset"""
        print("="*60)
        print("DOCKER SELENIUM FEATURE EXTRACTION DEMO")
        print("="*60)
        
        # Load dataset
        try:
            df = pd.read_csv(csv_file)
            print(f"✓ Loaded {len(df)} URLs from {csv_file}")
        except Exception as e:
            print(f"✗ Failed to load {csv_file}: {e}")
            return False
        
        # Setup WebDriver
        if not self.setup_driver():
            return False
        
        print(f"\\nStarting feature extraction at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        all_features = []
        successful_extractions = 0
        failed_extractions = 0
        
        for index, row in df.iterrows():
            url = row['url']
            label = row['label']
            label_type = "Phishing" if label == 1 else "Legitimate"
            
            print(f"\\n[{index+1:2d}/20] {label_type:10s}: {url[:40]}{'...' if len(url) > 40 else ''}")
            
            try:
                # Extract URL-based features
                url_features = self.extract_url_features(url)
                
                # Extract web-based features
                web_features = self.extract_web_features(url)
                
                # Combine all features
                combined_features = {
                    'url': url,
                    'label': label,
                    'label_type': label_type,
                    **url_features,
                    **web_features
                }
                
                all_features.append(combined_features)
                
                if web_features.get('page_loaded', 0) == 1:
                    successful_extractions += 1
                    status = "SUCCESS"
                else:
                    failed_extractions += 1
                    status = "FAILED"
                
                print(f"  Status: {status} | Features extracted: {len(combined_features)}")
                
                # Log extraction details
                self.extraction_log.append({
                    'url': url,
                    'label': label,
                    'status': status,
                    'features_count': len(combined_features),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"  ✗ Critical error extracting features: {e}")
                failed_extractions += 1
                
            # Small delay to be respectful
            time.sleep(1)
        
        print("\\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        print(f"Total URLs processed: {len(df)}")
        print(f"Successful extractions: {successful_extractions}")
        print(f"Failed extractions: {failed_extractions}")
        print(f"Success rate: {(successful_extractions/len(df)*100):.1f}%")
        
        # Save results
        self._save_results(all_features)
        self._save_extraction_report(successful_extractions, failed_extractions, len(df))
        
        return True
    
    def _save_results(self, features_data):
        """Save extracted features to CSV"""
        if not features_data:
            print("\\n✗ No features to save")
            return
            
        df_features = pd.DataFrame(features_data)
        output_file = 'extracted_features.csv'
        df_features.to_csv(output_file, index=False)
        
        print(f"\\n✓ Features saved to {output_file}")
        print(f"  Features per URL: {len(df_features.columns) - 3}")  # Subtract url, label, label_type
        print(f"  Feature columns: {', '.join(df_features.columns[3:8])}...")  # Show first 5 feature names
    
    def _save_extraction_report(self, successful, failed, total):
        """Save detailed extraction report"""
        report = {
            'extraction_timestamp': datetime.now().isoformat(),
            'total_urls': total,
            'successful_extractions': successful,
            'failed_extractions': failed,
            'success_rate_percent': round((successful/total)*100, 2),
            'extraction_log': self.extraction_log,
            'feature_categories': {
                'url_based_features': [
                    'url_length', 'num_dots', 'num_slashes', 'domain_length',
                    'has_ip_address', 'suspicious_keywords'
                ],
                'web_based_features': [
                    'page_loaded', 'response_time', 'num_forms', 'num_links',
                    'has_password_field', 'page_size'
                ]
            }
        }
        
        with open('extraction_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Detailed report saved to extraction_report.json")
    
    def cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("\\n✓ WebDriver cleaned up successfully")
            except:
                pass

def main():
    """Main execution function"""
    extractor = DockerSeleniumExtractor()
    
    try:
        # Check if small_dataset.csv exists
        import os
        if not os.path.exists('small_dataset.csv'):
            print("✗ small_dataset.csv not found. Please run create_small_dataset.py first.")
            return
        
        # Run the extraction
        success = extractor.extract_features_from_dataset()
        
        if success:
            print("\\n" + "="*60)
            print("DEMO COMPLETE!")
            print("="*60)
            print("Files created:")
            print("  • extracted_features.csv - Features for machine learning")
            print("  • extraction_report.json - Detailed extraction log")
            print("\\nNext steps:")
            print("  • Review extracted features")
            print("  • Use features to train/test phishing detection models")
            print("  • Monitor Docker container via VNC: http://localhost:7900")
            
    except KeyboardInterrupt:
        print("\\n\\n✗ Extraction interrupted by user")
        
    finally:
        extractor.cleanup()

if __name__ == "__main__":
    main()