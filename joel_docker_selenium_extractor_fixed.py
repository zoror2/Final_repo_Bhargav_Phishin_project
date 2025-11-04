#!/usr/bin/env python3
"""
Joel Dataset Feature Extractor using Docker Selenium
Extracts 26 features from 5k URLs using Docker Selenium Grid
"""

import pandas as pd
import numpy as np
import time
import logging
import json
import re
import ssl
import socket
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime
from pathlib import Path

# Selenium imports for Docker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    InvalidSessionIdException, SessionNotCreatedException
)

# Configure logging without emojis (Windows compatibility)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('joel_extraction.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DockerSeleniumExtractor:
    """Feature extractor using Docker Selenium Grid"""
    
    def __init__(self, selenium_hub_url="http://localhost:4444", timeout=10):
        self.selenium_hub_url = selenium_hub_url
        self.timeout = timeout
        self.driver = None
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'extraction_times': []
        }
        
        # Suspicious keywords for phishing detection
        self.suspicious_keywords = [
            'verify', 'urgent', 'suspended', 'limited', 'confirm', 'update', 
            'secure', 'account', 'login', 'password', 'click', 'here',
            'expire', 'immediately', 'action', 'required', 'warning',
            'bank', 'paypal', 'amazon', 'apple', 'microsoft', 'google'
        ]
    
    def check_docker_selenium(self):
        """Check if Docker Selenium Hub is ready"""
        try:
            response = requests.get(f"{self.selenium_hub_url}/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('value', {}).get('ready', False):
                    logger.info("Docker Selenium Hub is ready")
                    return True
                else:
                    logger.error("Docker Selenium Hub is not ready")
                    return False
            else:
                logger.error(f"Docker Selenium Hub responded with status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cannot connect to Docker Selenium Hub: {e}")
            return False
    
    def setup_driver(self):
        """Setup Chrome WebDriver for Docker Selenium"""
        if not self.check_docker_selenium():
            return False
        
        try:
            # Chrome options for headless browsing
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            
            # Security settings
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-web-security")
            
            # User agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Create remote driver using modern Selenium 4 syntax
            self.driver = webdriver.Remote(
                command_executor=self.selenium_hub_url,
                options=chrome_options
            )
            
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(5)
            
            logger.info("Docker Selenium WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Docker Selenium WebDriver: {e}")
            return False
    
    def check_ssl_certificate(self, url):
        """Check SSL certificate validity"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme != 'https':
                return {'has_ssl': False, 'ssl_valid': False, 'ssl_issuer': None}
            
            hostname = parsed_url.hostname
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    return {
                        'has_ssl': True,
                        'ssl_valid': True,
                        'ssl_issuer': issuer.get('organizationName', 'Unknown')
                    }
        except Exception:
            return {'has_ssl': False, 'ssl_valid': False, 'ssl_issuer': None}
    
    def extract_url_features(self, url):
        """Extract URL-based features without loading the page"""
        features = {}
        
        try:
            parsed = urlparse(url)
            
            # Basic URL features
            features['url_length'] = len(url)
            features['domain_length'] = len(parsed.netloc) if parsed.netloc else 0
            features['path_length'] = len(parsed.path) if parsed.path else 0
            features['query_length'] = len(parsed.query) if parsed.query else 0
            
            # URL structure features
            features['subdomain_count'] = len(parsed.netloc.split('.')) - 2 if parsed.netloc else 0
            features['dash_count'] = url.count('-')
            features['dot_count'] = url.count('.')
            features['slash_count'] = url.count('/')
            features['at_symbol'] = 1 if '@' in url else 0
            
            # Security features
            features['is_https'] = 1 if parsed.scheme == 'https' else 0
            features['has_ip'] = 1 if re.match(r'^\d+\.\d+\.\d+\.\d+', parsed.netloc) else 0
            
            # Suspicious patterns
            features['has_suspicious_words'] = 1 if any(word in url.lower() for word in self.suspicious_keywords) else 0
            
        except Exception:
            # Set default values on error
            for key in ['url_length', 'domain_length', 'path_length', 'query_length', 
                       'subdomain_count', 'dash_count', 'dot_count', 'slash_count',
                       'at_symbol', 'is_https', 'has_ip', 'has_suspicious_words']:
                features[key] = 0
        
        return features
    
    def extract_page_features(self, url):
        """Extract page-based features using Selenium"""
        features = {}
        
        try:
            # Navigate to URL
            self.driver.get(url)
            time.sleep(2)  # Wait for page load
            
            # Page title features
            title = self.driver.title or ""
            features['title_length'] = len(title)
            features['title_has_suspicious'] = 1 if any(word in title.lower() for word in self.suspicious_keywords) else 0
            
            # Form features
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            features['form_count'] = len(forms)
            
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")
            features['input_count'] = len(input_fields)
            
            # Password fields
            password_fields = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            features['password_fields'] = len(password_fields)
            
            # Links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            features['link_count'] = len(links)
            
            # External links
            external_links = 0
            current_domain = urlparse(url).netloc
            for link in links[:50]:  # Limit to first 50 links
                try:
                    href = link.get_attribute('href')
                    if href and urlparse(href).netloc and urlparse(href).netloc != current_domain:
                        external_links += 1
                except:
                    continue
            features['external_links'] = external_links
            
            # Script features
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            features['script_count'] = len(scripts)
            
            # Image features
            images = self.driver.find_elements(By.TAG_NAME, "img")
            features['image_count'] = len(images)
            
            # Meta features
            meta_tags = self.driver.find_elements(By.TAG_NAME, "meta")
            features['meta_count'] = len(meta_tags)
            
            # Text content analysis
            body_text = self.driver.find_element(By.TAG_NAME, "body").text if self.driver.find_elements(By.TAG_NAME, "body") else ""
            features['text_length'] = len(body_text)
            features['text_has_suspicious'] = 1 if any(word in body_text.lower() for word in self.suspicious_keywords) else 0
            
        except Exception as e:
            logger.warning(f"Error extracting page features for {url}: {str(e)[:100]}")
            # Set default values
            for key in ['title_length', 'title_has_suspicious', 'form_count', 'input_count',
                       'password_fields', 'link_count', 'external_links', 'script_count',
                       'image_count', 'meta_count', 'text_length', 'text_has_suspicious']:
                features[key] = 0
        
        return features
    
    def extract_features_for_url(self, url, label=None):
        """Extract features in events_dataset_full.csv format"""
        start_time = time.time()
        
        try:
            # Initialize features in events_dataset format
            features = {
                'url': url,
                'label': 1 if label == 'Phishing' else 0,  # Convert to binary
                'success': False,
                'num_events': 0,
                'ssl_valid': 0,
                'ssl_invalid': 0,
                'redirects': 0,
                'forms': 0,
                'password_fields': 0,
                'iframes': 0,
                'scripts': 0,
                'suspicious_keywords': 0,
                'external_requests': 0,
                'page_load_time': 0,
                'has_errors': 1,  # Default to error, set to 0 if successful
                'count_ssl_invalid': 0.0,
                'count_webdriver_error': 0.0,
                'count_ssl_valid': 0.0,
                'count_redirects': 0.0,
                'count_external_requests': 0.0,
                'count_forms_detected': 0.0,
                'count_password_fields': 0.0,
                'count_iframes_detected': 0.0,
                'count_scripts_detected': 0.0,
                'count_suspicious_keywords': 0.0,
                'count_page_load_time': 0.0
            }
            
            # Check SSL
            ssl_info = self.check_ssl_certificate(url)
            if ssl_info['ssl_valid']:
                features['ssl_valid'] = 1
                features['count_ssl_valid'] = 1.0
            else:
                features['ssl_invalid'] = 1
                features['count_ssl_invalid'] = 1.0
            
            # Extract page features using Selenium
            try:
                page_start = time.time()
                self.driver.get(url)
                
                # Page loaded successfully
                features['success'] = True
                features['has_errors'] = 0
                features['num_events'] = 9  # Standard event count for successful load
                
                # Calculate page load time
                page_load_time = int((time.time() - page_start) * 1000)  # milliseconds
                features['page_load_time'] = page_load_time
                features['count_page_load_time'] = 1.0
                
                # Extract page elements
                # Forms
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                features['forms'] = len(forms)
                features['count_forms_detected'] = 1.0 if len(forms) > 0 else 0.0
                
                # Password fields
                password_fields = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
                features['password_fields'] = len(password_fields)
                features['count_password_fields'] = 1.0 if len(password_fields) > 0 else 0.0
                
                # Iframes
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                features['iframes'] = len(iframes)
                features['count_iframes_detected'] = 1.0 if len(iframes) > 0 else 0.0
                
                # Scripts
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                features['scripts'] = len(scripts)
                features['count_scripts_detected'] = 1.0 if len(scripts) > 0 else 0.0
                
                # Check for redirects (simplified)
                current_url = self.driver.current_url
                if current_url != url:
                    features['redirects'] = 1
                    features['count_redirects'] = 1.0
                
                # Check for suspicious keywords
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    suspicious_count = sum(1 for word in self.suspicious_keywords if word in page_text)
                    if suspicious_count > 0:
                        features['suspicious_keywords'] = 1
                        features['count_suspicious_keywords'] = 1.0
                except:
                    pass
                
                # External requests (simplified - count external links)
                links = self.driver.find_elements(By.TAG_NAME, "a")
                domain = urlparse(url).netloc
                external_count = 0
                for link in links[:50]:  # Limit to first 50
                    try:
                        href = link.get_attribute('href')
                        if href and urlparse(href).netloc and urlparse(href).netloc != domain:
                            external_count += 1
                    except:
                        continue
                
                if external_count > 0:
                    features['external_requests'] = 1
                    features['count_external_requests'] = 1.0
                
            except Exception as e:
                # Page load failed
                features['success'] = False
                features['has_errors'] = 1
                features['num_events'] = 2  # Failed event count
                features['count_webdriver_error'] = 1.0
                logger.warning(f"Page load failed for {url}: {str(e)[:100]}")
            
            extraction_time = time.time() - start_time
            self.stats['extraction_times'].append(extraction_time)
            self.stats['successful'] += 1
            
            return features, True
            
        except Exception as e:
            logger.error(f"Unexpected error for URL {url}: {str(e)[:100]}")
            extraction_time = time.time() - start_time
            self.stats['extraction_times'].append(extraction_time)
            self.stats['failed'] += 1
            
            # Return default error features in events format
            error_features = {
                'url': url,
                'label': 1 if label == 'Phishing' else 0,
                'success': False,
                'num_events': 1,
                'ssl_valid': 0,
                'ssl_invalid': 1,
                'redirects': 0,
                'forms': 0,
                'password_fields': 0,
                'iframes': 0,
                'scripts': 0,
                'suspicious_keywords': 0,
                'external_requests': 0,
                'page_load_time': 0,
                'has_errors': 1,
                'count_ssl_invalid': 1.0,
                'count_webdriver_error': 1.0,
                'count_ssl_valid': 0.0,
                'count_redirects': 0.0,
                'count_external_requests': 0.0,
                'count_forms_detected': 0.0,
                'count_password_fields': 0.0,
                'count_iframes_detected': 0.0,
                'count_scripts_detected': 0.0,
                'count_suspicious_keywords': 0.0,
                'count_page_load_time': 0.0
            }
            return error_features, False
    
    def log_progress(self, current, total, url, success):
        """Log extraction progress"""
        progress = (current / total) * 100
        avg_time = np.mean(self.stats['extraction_times']) if self.stats['extraction_times'] else 0
        eta = (total - current) * avg_time
        
        status = "OK" if success else "FAIL"
        logger.info(f"Progress: {current}/{total} ({progress:.1f}%) | {status} | ETA: {eta:.0f}s | URL: {url[:80]}")
    
    def extract_features_from_dataset(self, input_file, output_file=None, max_urls=None):
        """Extract features from entire dataset"""
        logger.info("Starting Joel Dataset Feature Extraction with Docker Selenium")
        logger.info(f"Input file: {input_file}")
        logger.info(f"Output file: {output_file}")
        
        # Setup WebDriver
        if not self.setup_driver():
            logger.error("Failed to setup Docker Selenium WebDriver")
            return False
        
        try:
            # Read dataset
            df = pd.read_csv(input_file)
            if max_urls:
                df = df.head(max_urls)
            
            total_urls = len(df)
            logger.info(f"Total URLs to process: {total_urls}")
            
            # Prepare results storage
            results = []
            
            # Start extraction
            logger.info("Starting feature extraction with Docker Selenium...")
            
            for idx, row in df.iterrows():
                url = row['url']
                label = row.get('label', None)
                
                self.stats['total_processed'] += 1
                
                # Extract features
                features, success = self.extract_features_for_url(url, label)
                
                if success and features:
                    results.append(features)
                
                # Log progress every 10 URLs
                if (idx + 1) % 10 == 0 or idx == 0:
                    self.log_progress(idx + 1, total_urls, url, success)
            
            # Save results
            if results:
                results_df = pd.DataFrame(results)
                
                if output_file:
                    results_df.to_csv(output_file, index=False)
                    logger.info(f"Features saved to {output_file}")
                
                return True
            else:
                logger.error("No features extracted successfully")
                return False
                
        except Exception as e:
            logger.error(f"Error during feature extraction: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def print_extraction_stats(self):
        """Print extraction statistics"""
        total = self.stats['total_processed']
        success_rate = (self.stats['successful'] / total * 100) if total > 0 else 0
        avg_time = np.mean(self.stats['extraction_times']) if self.stats['extraction_times'] else 0
        
        print(f"Total URLs processed: {self.stats['total_processed']}")
        print(f"Successful extractions: {self.stats['successful']} ({success_rate:.1f}%)")
        print(f"Failed extractions: {self.stats['failed']}")
        print(f"Average extraction time: {avg_time:.2f} seconds")
        
        if output_file and Path(output_file).exists():
            file_size = Path(output_file).stat().st_size / 1024 / 1024  # MB
            print(f"Output file size: {file_size:.2f} MB")
        print(f"Output file: {output_file}")

if __name__ == "__main__":
    print("Joel Dataset Feature Extractor - Docker Selenium")
    print("Extracting 26 features from 5k URLs using Docker Selenium Grid")
    print("=" * 70)
    
    # Initialize extractor
    extractor = DockerSeleniumExtractor()
    
    try:
        # Extract features from Joel dataset
        input_file = "Joel_dataset.csv"
        output_file = "Joel_dataset_features.csv"
        
        success = extractor.extract_features_from_dataset(
            input_file=input_file,
            output_file=output_file
        )
        
        if success:
            extractor.print_extraction_stats()
            print("Results saved to: Joel_dataset_features.csv")
        else:
            print("Feature extraction failed!")
            
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
    except Exception as e:
        print(f"Extraction failed: {e}")
    finally:
        extractor.cleanup()