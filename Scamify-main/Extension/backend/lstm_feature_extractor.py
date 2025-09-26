"""
LSTM Feature Extraction Service for Phishing Detection
Extracts 25 behavioral features using Selenium WebDriver
"""

import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests
from urllib.parse import urlparse, urljoin
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LSTMFeatureExtractor:
    def __init__(self, headless=True, timeout=30):
        """
        Initialize the LSTM Feature Extractor
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Page load timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
        # Suspicious keywords for phishing detection
        self.suspicious_keywords = [
            'verify', 'account', 'suspended', 'login', 'confirm', 'urgent',
            'security', 'update', 'click', 'winner', 'congratulations',
            'prize', 'lottery', 'bank', 'paypal', 'amazon', 'microsoft',
            'apple', 'google', 'facebook', 'twitter', 'instagram',
            'password', 'username', 'ssn', 'social security', 'credit card',
            'expires', 'limited time', 'act now', 'immediate action'
        ]
    
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with optimized options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Security and performance options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')  # We'll enable selectively
            chrome_options.add_argument('--window-size=1920,1080')
            
            # User agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Download preferences
            prefs = {
                'profile.default_content_settings.popups': 0,
                'profile.default_content_setting_values.notifications': 2,
                'profile.managed_default_content_settings.images': 2
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # Setup service
            service = Service(ChromeDriverManager().install())
            
            # Create driver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            driver.implicitly_wait(10)
            
            logger.info("Chrome WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def extract_features(self, url: str) -> Tuple[List[float], Dict]:
        """
        Extract all 25 features required by the LSTM model
        
        Args:
            url (str): URL to analyze
            
        Returns:
            Tuple[List[float], Dict]: 25-element feature vector and metadata
        """
        logger.info(f"Starting feature extraction for: {url}")
        
        try:
            self.driver = self.setup_driver()
            
            # Initialize features with default values
            features = {
                'success': 0,
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
                'has_errors': 0,
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
            
            metadata = {
                'url': url,
                'timestamp': time.time(),
                'errors': [],
                'warnings': []
            }
            
            # Extract features
            start_time = time.time()
            
            try:
                # Navigate to URL
                self.driver.get(url)
                features['success'] = 1
                logger.info(f"Successfully loaded: {url}")
                
            except Exception as e:
                features['has_errors'] = 1
                features['count_webdriver_error'] = 1
                metadata['errors'].append(f"Navigation error: {str(e)}")
                logger.error(f"Navigation failed: {e}")
            
            # Calculate page load time
            page_load_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            features['page_load_time'] = page_load_time
            features['count_page_load_time'] = 1 if page_load_time > 0 else 0
            
            if features['success']:
                # SSL validation
                features.update(self._check_ssl(url))
                
                # Redirect detection
                features.update(self._check_redirects(url))
                
                # DOM analysis
                features.update(self._analyze_dom())
                
                # Content analysis
                features.update(self._analyze_content())
                
                # External requests analysis
                features.update(self._analyze_network_requests())
            
            # Calculate event counts
            features['num_events'] = sum([
                features['count_ssl_valid'],
                features['count_ssl_invalid'],
                features['count_redirects'],
                features['count_forms_detected'],
                features['count_password_fields'],
                features['count_iframes_detected'],
                features['count_scripts_detected'],
                features['count_suspicious_keywords'],
                features['count_external_requests'],
                features['count_page_load_time'],
                features['count_webdriver_error']
            ])
            
            # Convert to feature vector (24 elements) - excluding 'url' and 'label' 
            feature_vector = [
                features['success'],
                features['num_events'],
                features['ssl_valid'],
                features['ssl_invalid'],
                features['redirects'],
                features['forms'],
                features['password_fields'],
                features['iframes'],
                features['scripts'],
                features['suspicious_keywords'],
                features['external_requests'],
                features['page_load_time'],
                features['has_errors'],
                features['count_ssl_invalid'],
                features['count_webdriver_error'],
                features['count_ssl_valid'],
                features['count_redirects'],
                features['count_external_requests'],
                features['count_forms_detected'],
                features['count_password_fields'],
                features['count_iframes_detected'],
                features['count_scripts_detected'],
                features['count_suspicious_keywords'],
                features['count_page_load_time']
            ]
            
            logger.info(f"Feature extraction completed for: {url}")
            return feature_vector, metadata
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return default features on failure (exactly 24 features matching CSV order)
            default_features = [
                0,  # success
                0,  # num_events  
                0,  # ssl_valid
                0,  # ssl_invalid
                0,  # redirects
                0,  # forms
                0,  # password_fields
                0,  # iframes
                0,  # scripts
                0,  # suspicious_keywords
                0,  # external_requests
                0,  # page_load_time
                1,  # has_errors (set to 1 for failed extraction)
                0,  # count_ssl_invalid
                1,  # count_webdriver_error (set to 1 for failed extraction)
                0,  # count_ssl_valid
                0,  # count_redirects
                0,  # count_external_requests
                0,  # count_forms_detected
                0,  # count_password_fields
                0,  # count_iframes_detected
                0,  # count_scripts_detected
                0,  # count_suspicious_keywords
                0   # count_page_load_time
            ]
            return default_features, {'url': url, 'error': str(e)}
            
        finally:
            self._cleanup()
    
    def _check_ssl(self, url: str) -> Dict:
        """Check SSL certificate validity"""
        features = {'ssl_valid': 0, 'ssl_invalid': 0, 'count_ssl_valid': 0, 'count_ssl_invalid': 0}
        
        try:
            if url.startswith('https://'):
                # Simple SSL check - if we can load the page, SSL is likely valid
                current_url = self.driver.current_url
                if current_url.startswith('https://'):
                    features['ssl_valid'] = 1
                    features['count_ssl_valid'] = 1
                else:
                    features['ssl_invalid'] = 1
                    features['count_ssl_invalid'] = 1
            else:
                # HTTP site - no SSL
                features['ssl_invalid'] = 1
                features['count_ssl_invalid'] = 1
                
        except Exception as e:
            logger.warning(f"SSL check failed: {e}")
            features['ssl_invalid'] = 1
            features['count_ssl_invalid'] = 1
        
        return features
    
    def _check_redirects(self, original_url: str) -> Dict:
        """Check for redirects"""
        features = {'redirects': 0, 'count_redirects': 0}
        
        try:
            current_url = self.driver.current_url
            if current_url != original_url:
                features['redirects'] = 1
                features['count_redirects'] = 1
                logger.info(f"Redirect detected: {original_url} -> {current_url}")
                
        except Exception as e:
            logger.warning(f"Redirect check failed: {e}")
        
        return features
    
    def _analyze_dom(self) -> Dict:
        """Analyze DOM structure"""
        features = {
            'forms': 0, 'password_fields': 0, 'iframes': 0, 'scripts': 0,
            'count_forms_detected': 0, 'count_password_fields': 0,
            'count_iframes_detected': 0, 'count_scripts_detected': 0
        }
        
        try:
            # Count forms
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            if forms:
                features['forms'] = len(forms)
                features['count_forms_detected'] = 1
            
            # Count password fields
            password_fields = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            if password_fields:
                features['password_fields'] = len(password_fields)
                features['count_password_fields'] = 1
            
            # Count iframes
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            if iframes:
                features['iframes'] = len(iframes)
                features['count_iframes_detected'] = 1
            
            # Count scripts
            scripts = self.driver.find_elements(By.TAG_NAME, 'script')
            if scripts:
                features['scripts'] = len(scripts)
                features['count_scripts_detected'] = 1
                
        except Exception as e:
            logger.warning(f"DOM analysis failed: {e}")
        
        return features
    
    def _analyze_content(self) -> Dict:
        """Analyze page content for suspicious keywords"""
        features = {'suspicious_keywords': 0, 'count_suspicious_keywords': 0}
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            
            suspicious_count = 0
            for keyword in self.suspicious_keywords:
                if keyword.lower() in page_text:
                    suspicious_count += 1
            
            if suspicious_count > 0:
                features['suspicious_keywords'] = suspicious_count
                features['count_suspicious_keywords'] = 1
                logger.info(f"Found {suspicious_count} suspicious keywords")
                
        except Exception as e:
            logger.warning(f"Content analysis failed: {e}")
        
        return features
    
    def _analyze_network_requests(self) -> Dict:
        """Analyze network requests (simplified version)"""
        features = {'external_requests': 0, 'count_external_requests': 0}
        
        try:
            # Get all external links as a proxy for external requests
            current_domain = urlparse(self.driver.current_url).netloc
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            
            external_count = 0
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and href.startswith('http'):
                        link_domain = urlparse(href).netloc
                        if link_domain != current_domain:
                            external_count += 1
                except:
                    continue
            
            if external_count > 0:
                features['external_requests'] = external_count
                features['count_external_requests'] = 1
                
        except Exception as e:
            logger.warning(f"Network analysis failed: {e}")
        
        return features
    
    def _cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("WebDriver cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

# Convenience function for single URL analysis
def extract_lstm_features(url: str, headless: bool = True) -> Tuple[List[float], Dict]:
    """
    Extract LSTM features for a single URL
    
    Args:
        url (str): URL to analyze
        headless (bool): Run in headless mode
        
    Returns:
        Tuple[List[float], Dict]: Feature vector and metadata
    """
    extractor = LSTMFeatureExtractor(headless=headless)
    return extractor.extract_features(url)

if __name__ == "__main__":
    # Test the feature extractor
    test_url = "https://www.google.com"
    print(f"Testing feature extraction for: {test_url}")
    
    features, metadata = extract_lstm_features(test_url)
    print(f"Features extracted: {len(features)} elements")
    print(f"Feature vector: {features}")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")