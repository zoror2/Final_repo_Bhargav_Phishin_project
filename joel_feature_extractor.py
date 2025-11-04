#!/usr/bin/env python3
"""
Joel Dataset Feature Extractor using Docker Selenium
Extracts 26 features from 5k URLs (2.5k phishing + 2.5k legitimate)
"""

import pandas as pd
import numpy as np
import time
import logging
import json
import re
import ssl
import socket
from urllib.parse import urlparse, urljoin
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    InvalidSessionIdException, SessionNotCreatedException
)
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('joel_feature_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JoelFeatureExtractor:
    def __init__(self, headless=True, timeout=10):
        """
        Initialize the Joel Feature Extractor
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Page load timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.suspicious_keywords = [
            'login', 'signin', 'password', 'bank', 'paypal', 'amazon', 'google',
            'facebook', 'apple', 'microsoft', 'secure', 'verify', 'account',
            'suspended', 'urgent', 'immediate', 'click', 'winner', 'congratulations',
            'free', 'prize', 'offer', 'limited', 'expire', 'confirm', 'update',
            'billing', 'payment', 'credit', 'card', 'ssn', 'social', 'security'
        ]
        
        # Initialize stats
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'ssl_errors': 0,
            'timeout_errors': 0,
            'webdriver_errors': 0,
            'start_time': time.time()
        }
    
    def setup_driver(self):
        """Setup Chrome WebDriver with optimized options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Performance optimizations
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")  # Disable JS for faster loading
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Additional security and performance settings
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Create service
            service = Service(ChromeDriverManager().install())
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            
            logger.info("✅ Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False
    
    def check_ssl_certificate(self, url):
        """Check SSL certificate validity"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme != 'https':
                return False, False  # ssl_valid, ssl_invalid
            
            hostname = parsed_url.hostname
            if not hostname:
                return False, False
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # If we get here, SSL is valid
                    return True, False
                    
        except Exception:
            # SSL error
            return False, True
    
    def extract_url_features(self, url, label):
        """
        Extract all 26 features from a single URL
        
        Returns:
            dict: Dictionary containing all extracted features
        """
        features = {
            'url': url,
            'label': label,
            'success': False,
            'num_events': 0,
            'ssl_valid': False,
            'ssl_invalid': False,
            'redirects': 0,
            'forms': 0,
            'password_fields': 0,
            'iframes': 0,
            'scripts': 0,
            'suspicious_keywords': 0,
            'external_requests': 0,
            'page_load_time': 0.0,
            'has_errors': True,
            'count_ssl_invalid': 0,
            'count_webdriver_error': 0,
            'count_ssl_valid': 0,
            'count_redirects': 0,
            'count_external_requests': 0,
            'count_forms_detected': 0,
            'count_password_fields': 0,
            'count_iframes_detected': 0,
            'count_scripts_detected': 0,
            'count_suspicious_keywords': 0,
            'count_page_load_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Check SSL certificate
            ssl_valid, ssl_invalid = self.check_ssl_certificate(url)
            features['ssl_valid'] = ssl_valid
            features['ssl_invalid'] = ssl_invalid
            features['count_ssl_valid'] = 1 if ssl_valid else 0
            features['count_ssl_invalid'] = 1 if ssl_invalid else 0
            
            # Navigate to URL
            initial_url = self.driver.current_url
            self.driver.get(url)
            
            # Calculate page load time
            load_time = time.time() - start_time
            features['page_load_time'] = round(load_time, 2)
            features['count_page_load_time'] = 1 if load_time > 0 else 0
            
            # Check for redirects
            final_url = self.driver.current_url
            if final_url != url:
                features['redirects'] = 1
                features['count_redirects'] = 1
            
            # Wait for page to load
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract page source for analysis
            page_source = self.driver.page_source.lower()
            
            # Count forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            features['forms'] = len(forms)
            features['count_forms_detected'] = len(forms)
            
            # Count password fields
            password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            features['password_fields'] = len(password_fields)
            features['count_password_fields'] = len(password_fields)
            
            # Count iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            features['iframes'] = len(iframes)
            features['count_iframes_detected'] = len(iframes)
            
            # Count scripts
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            features['scripts'] = len(scripts)
            features['count_scripts_detected'] = len(scripts)
            
            # Count suspicious keywords
            suspicious_count = 0
            for keyword in self.suspicious_keywords:
                if keyword in page_source:
                    suspicious_count += 1
            
            features['suspicious_keywords'] = suspicious_count
            features['count_suspicious_keywords'] = suspicious_count
            
            # Count external requests (approximate by counting external links)
            try:
                current_domain = urlparse(url).netloc
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                external_count = 0
                
                for link in all_links[:50]:  # Limit to first 50 links for performance
                    try:
                        href = link.get_attribute("href")
                        if href and href.startswith("http"):
                            link_domain = urlparse(href).netloc
                            if link_domain != current_domain:
                                external_count += 1
                    except:
                        continue
                
                features['external_requests'] = external_count
                features['count_external_requests'] = external_count
                
            except Exception:
                features['external_requests'] = 0
                features['count_external_requests'] = 0
            
            # Calculate number of events (total interactive elements)
            interactive_elements = (
                features['forms'] + 
                features['password_fields'] + 
                len(self.driver.find_elements(By.TAG_NAME, "button")) +
                len(self.driver.find_elements(By.TAG_NAME, "input"))
            )
            features['num_events'] = interactive_elements
            
            # Mark as successful
            features['success'] = True
            features['has_errors'] = False
            features['count_webdriver_error'] = 0
            
            self.stats['successful'] += 1
            
        except TimeoutException:
            logger.warning(f"⏰ Timeout for URL: {url}")
            features['count_webdriver_error'] = 1
            features['has_errors'] = True
            self.stats['timeout_errors'] += 1
            self.stats['failed'] += 1
            
        except WebDriverException as e:
            logger.warning(f"🌐 WebDriver error for URL {url}: {str(e)[:100]}")
            features['count_webdriver_error'] = 1
            features['has_errors'] = True
            self.stats['webdriver_errors'] += 1
            self.stats['failed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Unexpected error for URL {url}: {str(e)[:100]}")
            features['count_webdriver_error'] = 1
            features['has_errors'] = True
            self.stats['failed'] += 1
        
        self.stats['total_processed'] += 1
        return features
    
    def print_progress(self, current, total, url, success):
        """Print progress information"""
        elapsed = time.time() - self.stats['start_time']
        rate = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / rate if rate > 0 else 0
        
        status = "✅" if success else "❌"
        
        print(f"\r{status} [{current:4d}/{total}] {current/total*100:5.1f}% | "
              f"Rate: {rate:.1f}/s | ETA: {eta/60:.1f}m | "
              f"Success: {self.stats['successful']} | "
              f"Failed: {self.stats['failed']} | "
              f"URL: {url[:50]}...", end="", flush=True)
    
    def extract_features_from_dataset(self, input_file="Joel_dataset.csv", output_file="Joel_dataset_features.csv"):
        """
        Extract features from all URLs in the Joel dataset
        
        Args:
            input_file (str): Input CSV file path
            output_file (str): Output CSV file path
        """
        logger.info("🚀 Starting Joel Dataset Feature Extraction")
        logger.info(f"📁 Input file: {input_file}")
        logger.info(f"📁 Output file: {output_file}")
        
        # Setup WebDriver
        if not self.setup_driver():
            logger.error("❌ Failed to setup WebDriver")
            return False
        
        try:
            # Read dataset
            logger.info("📖 Reading Joel dataset...")
            df = pd.read_csv(input_file)
            total_urls = len(df)
            logger.info(f"📊 Total URLs to process: {total_urls}")
            
            # Prepare results list
            results = []
            
            # Process each URL
            logger.info("🔍 Starting feature extraction...")
            
            for idx, row in df.iterrows():
                url = row['url']
                label = row['label']
                
                # Extract features
                features = self.extract_url_features(url, label)
                results.append(features)
                
                # Print progress
                self.print_progress(idx + 1, total_urls, url, features['success'])
                
                # Save intermediate results every 100 URLs
                if (idx + 1) % 100 == 0:
                    temp_df = pd.DataFrame(results)
                    temp_df.to_csv(f"temp_{output_file}", index=False)
                    logger.info(f"\n💾 Saved intermediate results ({idx + 1} URLs)")
                
                # Small delay to be respectful
                time.sleep(0.1)
            
            print()  # New line after progress
            
            # Create final DataFrame and save
            logger.info("💾 Saving final results...")
            results_df = pd.DataFrame(results)
            results_df.to_csv(output_file, index=False)
            
            # Print final statistics
            self.print_final_stats(total_urls, output_file)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during feature extraction: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🚪 WebDriver closed")
    
    def print_final_stats(self, total_urls, output_file):
        """Print final extraction statistics"""
        elapsed = time.time() - self.stats['start_time']
        
        print("\n" + "="*60)
        print("🎉 JOEL DATASET FEATURE EXTRACTION COMPLETE!")
        print("="*60)
        print(f"📊 Total URLs processed: {self.stats['total_processed']}")
        print(f"✅ Successful extractions: {self.stats['successful']}")
        print(f"❌ Failed extractions: {self.stats['failed']}")
        print(f"🔒 SSL errors: {self.stats['ssl_errors']}")
        print(f"⏰ Timeout errors: {self.stats['timeout_errors']}")
        print(f"🌐 WebDriver errors: {self.stats['webdriver_errors']}")
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"📈 Average rate: {self.stats['total_processed']/elapsed:.1f} URLs/second")
        print(f"📁 Output file: {output_file}")
        print("="*60)

def main():
    """Main function to run the feature extraction"""
    print("🛡️ Joel Dataset Feature Extractor")
    print("🔍 Extracting 26 features from 5k URLs using Selenium")
    print("=" * 50)
    
    # Create extractor
    extractor = JoelFeatureExtractor(headless=True, timeout=10)
    
    # Run extraction
    success = extractor.extract_features_from_dataset(
        input_file="Joel_dataset.csv",
        output_file="Joel_dataset_features.csv"
    )
    
    if success:
        print("\n🎊 Feature extraction completed successfully!")
        print("📁 Results saved to: Joel_dataset_features.csv")
        print("📝 Log saved to: joel_feature_extraction.log")
    else:
        print("\n💥 Feature extraction failed!")

if __name__ == "__main__":
    main()