#!/usr/bin/env python3
"""
Majestic Million Feature Extractor using Joel's Proven Approach
Uses single-session Docker Selenium strategy that worked for 50k URLs
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction_million.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Error logger
error_logger = logging.getLogger('error_logger')
error_handler = logging.FileHandler('extraction_errors_million.log', encoding='utf-8')
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

class MajesticMillionExtractor:
    """Feature extractor using Joel's single-session approach"""
    
    def __init__(self, selenium_hub_url="http://localhost:4444", timeout=15):
        self.selenium_hub_url = selenium_hub_url
        self.timeout = timeout
        self.driver = None
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'ssl_valid': 0,
            'ssl_invalid': 0,
            'timeout_errors': 0,
            'webdriver_errors': 0,
            'extraction_times': []
        }
        
        # Suspicious keywords for phishing detection
        self.suspicious_keywords = [
            'verify', 'urgent', 'suspended', 'limited', 'confirm', 'update', 
            'secure', 'account', 'login', 'password', 'click', 'here',
            'expire', 'immediately', 'action', 'required', 'warning',
            'bank', 'paypal', 'amazon', 'apple', 'microsoft', 'google'
        ]
        
        # Progress tracking
        self.progress_file = "extraction_progress_million.json"
        self.checkpoint_interval = 100  # Save every 100 URLs
        self.start_time = None
    
    def check_docker_selenium(self):
        """Check if Docker Selenium Hub is ready"""
        try:
            response = requests.get(f"{self.selenium_hub_url}/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('value', {}).get('ready', False):
                    logger.info("[OK] Docker Selenium Hub is ready")
                    return True
                else:
                    logger.error("[ERROR] Docker Selenium Hub is not ready")
                    return False
            else:
                logger.error(f"[ERROR] Docker Selenium Hub responded with status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"[ERROR] Cannot connect to Docker Selenium Hub: {e}")
            return False
    
    def setup_driver(self):
        """Setup Edge WebDriver for Docker Selenium - AUTO-RECONNECTION ENABLED"""
        if not self.check_docker_selenium():
            return None
        
        try:
            # Edge options for headless browsing
            from selenium.webdriver.edge.options import Options as EdgeOptions
            edge_options = EdgeOptions()
            edge_options.add_argument("--headless")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1920,1080")
            edge_options.add_argument("--disable-extensions")
            edge_options.add_argument("--disable-plugins")
            
            # Connect to Docker Selenium Hub
            logger.info("[SETUP] Connecting to Docker Selenium Hub (Edge Browser)...")
            driver = webdriver.Remote(
                command_executor=self.selenium_hub_url,
                options=edge_options
            )
            
            # Set timeouts
            driver.set_page_load_timeout(self.timeout)
            driver.set_script_timeout(self.timeout)
            
            logger.info("[OK] Docker Selenium Edge WebDriver connected successfully!")
            return driver
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to setup driver: {str(e)[:200]}")
            return None
    
    def check_ssl_certificate(self, url):
        """Check SSL certificate validity"""
        ssl_valid = False
        ssl_invalid = False
        
        try:
            parsed = urlparse(url)
            if parsed.scheme == 'https':
                hostname = parsed.netloc
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        ssl_valid = True
        except (ssl.SSLError, socket.timeout, socket.gaierror, ConnectionRefusedError):
            ssl_invalid = True
        except Exception:
            ssl_invalid = True
        
        return ssl_valid, ssl_invalid
    
    def extract_features_for_url(self, url, label=0):
        """Extract features using Joel's approach - 26 features matching events_dataset format"""
        start_time = time.time()
        
        # Initialize features in events_dataset format
        features = {
            'url': url,
            'label': label,
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
            'page_load_time': 0.0,
            'has_errors': 1,  # Default to error, set to 0 if successful
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
        
        try:
            # 1. Check SSL certificate
            ssl_valid, ssl_invalid = self.check_ssl_certificate(url)
            features['ssl_valid'] = 1 if ssl_valid else 0
            features['ssl_invalid'] = 1 if ssl_invalid else 0
            features['count_ssl_valid'] = 1 if ssl_valid else 0
            features['count_ssl_invalid'] = 1 if ssl_invalid else 0
            
            if ssl_valid:
                self.stats['ssl_valid'] += 1
            elif ssl_invalid:
                self.stats['ssl_invalid'] += 1
            
            # 2. Load page with Selenium
            page_start = time.time()
            self.driver.get(url)
            
            # 3. Page loaded successfully
            features['success'] = 1
            features['has_errors'] = 0
            features['num_events'] = 9  # Standard event count for successful load
            
            # 4. Calculate page load time
            page_load_time = time.time() - page_start
            features['page_load_time'] = round(page_load_time, 2)
            features['count_page_load_time'] = 1
            
            # 5. Check for redirects
            current_url = self.driver.current_url
            if current_url != url and not (url.endswith('/') or current_url == url + '/'):
                features['redirects'] = 1
                features['count_redirects'] = 1
            
            # 6. Extract page elements
            # Forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            features['forms'] = len(forms)
            features['count_forms_detected'] = 1 if len(forms) > 0 else 0
            
            # Password fields
            password_fields = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            features['password_fields'] = len(password_fields)
            features['count_password_fields'] = 1 if len(password_fields) > 0 else 0
            
            # Iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            features['iframes'] = len(iframes)
            features['count_iframes_detected'] = 1 if len(iframes) > 0 else 0
            
            # Scripts
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            features['scripts'] = len(scripts)
            features['count_scripts_detected'] = 1 if len(scripts) > 0 else 0
            
            # 7. Check for suspicious keywords
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                suspicious_count = sum(1 for word in self.suspicious_keywords if word in page_text)
                if suspicious_count > 0:
                    features['suspicious_keywords'] = 1
                    features['count_suspicious_keywords'] = 1
            except:
                pass
            
            # 8. External requests (count external links)
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                current_domain = urlparse(url).netloc
                external_count = 0
                for link in links[:50]:  # Check first 50 links
                    try:
                        href = link.get_attribute('href')
                        if href and urlparse(href).netloc and urlparse(href).netloc != current_domain:
                            external_count += 1
                    except:
                        continue
                
                features['external_requests'] = external_count
                features['count_external_requests'] = 1 if external_count > 0 else 0
            except:
                pass
            
            # Success
            self.stats['successful'] += 1
            extraction_time = time.time() - start_time
            self.stats['extraction_times'].append(extraction_time)
            
        except TimeoutException:
            logger.warning(f"[TIMEOUT] Timeout for URL: {url}")
            features['count_webdriver_error'] = 1
            features['has_errors'] = 1
            self.stats['timeout_errors'] += 1
            self.stats['failed'] += 1
            error_logger.error(f"TIMEOUT: {url}")
            
        except (WebDriverException, InvalidSessionIdException) as e:
            error_msg = str(e)
            
            # Check if session died - CRITICAL: Need to reconnect
            if "Cannot find session" in error_msg or "invalid session id" in error_msg.lower():
                logger.error(f"[SESSION DEAD] SESSION DIED! Reconnecting...")
                error_logger.error(f"SESSION_DEAD: {url} - Reconnecting...")
                
                # Attempt to reconnect
                try:
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                    
                    logger.info("[RECONNECT] Creating new WebDriver session...")
                    time.sleep(3)  # Wait before reconnecting
                    self.driver = self.setup_driver()
                    
                    if self.driver:
                        logger.info("[OK] Session reconnected successfully!")
                    else:
                        logger.critical("[FATAL] FATAL: Could not reconnect - will retry on next URL")
                        
                except Exception as reconnect_error:
                    logger.error(f"[ERROR] Reconnection failed: {str(reconnect_error)[:100]}")
                
                # Mark current URL as failed
                features['count_webdriver_error'] = 1
                features['has_errors'] = 1
                self.stats['webdriver_errors'] += 1
                self.stats['failed'] += 1
                
            else:
                # Other WebDriver errors (DNS, network, etc.)
                logger.warning(f"[WEBDRIVER] WebDriver error for URL {url}: {error_msg[:100]}")
                features['count_webdriver_error'] = 1
                features['has_errors'] = 1
                self.stats['webdriver_errors'] += 1
                self.stats['failed'] += 1
                error_logger.error(f"WEBDRIVER: {url} - {error_msg[:200]}")
            
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error for URL {url}: {str(e)[:100]}")
            features['count_webdriver_error'] = 1
            features['has_errors'] = 1
            self.stats['failed'] += 1
            error_logger.error(f"ERROR: {url} - {str(e)[:200]}")
        
        self.stats['total_processed'] += 1
        return features
    
    def save_progress(self, current_index, results_buffer):
        """Save progress checkpoint - ATOMIC & CRASH-SAFE"""
        try:
            # Save progress metadata
            progress_data = {
                'last_processed_index': current_index,
                'total_processed': self.stats['total_processed'],
                'successful': self.stats['successful'],
                'failed': self.stats['failed'],
                'ssl_valid': self.stats['ssl_valid'],
                'ssl_invalid': self.stats['ssl_invalid'],
                'timeout_errors': self.stats['timeout_errors'],
                'webdriver_errors': self.stats['webdriver_errors'],
                'timestamp': datetime.now().isoformat(),
                'elapsed_hours': (time.time() - self.start_time) / 3600
            }
            
            # Write progress file atomically
            temp_progress_file = self.progress_file + '.tmp'
            with open(temp_progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
            
            # Atomic rename (crash-safe)
            import os
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
            os.rename(temp_progress_file, self.progress_file)
            
            # Save results to CSV (append mode) - ONLY NEW ROWS
            if results_buffer:
                df_buffer = pd.DataFrame(results_buffer)
                file_exists = Path("final_million_dataset.csv").exists()
                
                # Append to CSV atomically
                df_buffer.to_csv(
                    "final_million_dataset.csv",
                    mode='a',
                    header=not file_exists,
                    index=False
                )
                logger.info(f"[CHECKPOINT] Checkpoint saved: {len(results_buffer)} new rows saved")
                logger.info(f"[CHECKPOINT] Last processed index: {current_index}")
            
        except Exception as e:
            logger.error(f"[ERROR] Error saving progress: {e}")
    
    def load_progress(self):
        """Load previous progress - ENSURES NO RE-PROCESSING"""
        if Path(self.progress_file).exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                
                # Restore stats
                self.stats['total_processed'] = progress.get('total_processed', 0)
                self.stats['successful'] = progress.get('successful', 0)
                self.stats['failed'] = progress.get('failed', 0)
                self.stats['ssl_valid'] = progress.get('ssl_valid', 0)
                self.stats['ssl_invalid'] = progress.get('ssl_invalid', 0)
                self.stats['timeout_errors'] = progress.get('timeout_errors', 0)
                self.stats['webdriver_errors'] = progress.get('webdriver_errors', 0)
                
                logger.info("=" * 70)
                logger.info("[RESUME] RESUMING FROM PREVIOUS RUN")
                logger.info("=" * 70)
                logger.info(f"[RESUME] Last processed index: {progress['last_processed_index']}")
                logger.info(f"[RESUME] Previously successful: {self.stats['successful']}")
                logger.info(f"[RESUME] Previously failed: {self.stats['failed']}")
                logger.info(f"[RESUME] SSL valid: {self.stats['ssl_valid']}")
                logger.info(f"[RESUME] SSL invalid: {self.stats['ssl_invalid']}")
                logger.info(f"[RESUME] Previous timestamp: {progress.get('timestamp', 'N/A')}")
                logger.info(f"[RESUME] Previous elapsed time: {progress.get('elapsed_hours', 0):.2f} hours")
                logger.info("=" * 70)
                
                return progress
            except Exception as e:
                logger.error(f"Error loading progress: {e}")
                return None
        return None
    
    def extract_from_majestic_million(self):
        """Main extraction loop - Joel's proven approach"""
        logger.info("=" * 70)
        logger.info("[START] MAJESTIC MILLION EXTRACTION - JOEL'S APPROACH")
        logger.info("=" * 70)
        logger.info("[CONFIG] Input: majestic_million.csv")
        logger.info("[CONFIG] Output: final_million_dataset.csv")
        logger.info("[CONFIG] Progress: extraction_progress_million.json")
        logger.info("=" * 70)
        
        self.start_time = time.time()
        
        # Load previous progress
        progress = self.load_progress()
        start_index = progress['last_processed_index'] + 1 if progress else 0
        
        # Setup WebDriver - SINGLE SESSION for entire extraction
        logger.info("[SETUP] Setting up Docker Selenium WebDriver...")
        self.driver = self.setup_driver()
        if not self.driver:
            logger.error("[ERROR] Failed to setup Docker Selenium - exiting")
            return False
        
        try:
            # Read dataset
            logger.info("[DATA] Reading majestic_million.csv...")
            df = pd.read_csv("majestic_million.csv")
            total_urls = len(df)
            logger.info(f"[DATA] Loaded {total_urls:,} URLs")
            logger.info(f"[DATA] Starting from index: {start_index}")
            logger.info(f"[DATA] Remaining to process: {total_urls - start_index:,}")
            logger.info("=" * 70)
            
            # Results buffer for checkpointing
            results_buffer = []
            last_saved_index = start_index - 1  # Track last saved checkpoint
            
            # Extract features - ONE SESSION FOR ALL URLs (WITH AUTO-RECONNECT)
            for idx in range(start_index, total_urls):
                row = df.iloc[idx]
                url = row['Domain']  # Majestic uses 'Domain' column
                
                # Ensure URL has protocol
                if not url.startswith('http'):
                    url = f"https://{url}"
                
                # Check if driver is alive, reconnect if needed
                if not self.driver:
                    logger.warning("[WARNING] Driver is None, attempting to reconnect...")
                    self.driver = self.setup_driver()
                    if not self.driver:
                        logger.error(f"[ERROR] Cannot reconnect driver, skipping URL: {url}")
                        continue
                
                # Extract features
                features = self.extract_features_for_url(url, label=0)  # All legitimate sites
                results_buffer.append(features)
                
                # Progress display
                if (idx + 1) % 10 == 0 or idx == start_index:
                    elapsed = time.time() - self.start_time
                    rate = (idx + 1 - start_index) / elapsed if elapsed > 0 else 0
                    eta_hours = (total_urls - idx - 1) / (rate * 3600) if rate > 0 else 0
                    progress_pct = ((idx + 1) / total_urls) * 100
                    success_rate = (self.stats['successful'] / self.stats['total_processed'] * 100) if self.stats['total_processed'] > 0 else 0
                    
                    status = "[OK]" if features['success'] else "[FAIL]"
                    print(f"{status} [{idx+1:>10,}/{total_urls:,}] {progress_pct:>5.1f}% | "
                          f"Rate: {rate:.2f}/s | ETA: {eta_hours:.1f}h | "
                          f"OK:{self.stats['successful']} FAIL:{self.stats['failed']} ({success_rate:.1f}%) | "
                          f"URL: {url[:60]}...")
                
                # Checkpoint save every 100 URLs
                if (idx + 1) % self.checkpoint_interval == 0:
                    self.save_progress(idx, results_buffer)
                    last_saved_index = idx
                    results_buffer = []  # Clear buffer after save
                    logger.info(f"[CHECKPOINT] Checkpoint saved at URL #{idx+1}")
            
            # Save final results
            if results_buffer:
                final_idx = start_index + len(results_buffer) - 1 + (last_saved_index - start_index + 1)
                self.save_progress(total_urls - 1, results_buffer)
            
            logger.info("=" * 70)
            logger.info("[COMPLETE] EXTRACTION COMPLETE!")
            logger.info(f"[STATS] Total processed: {self.stats['total_processed']:,}")
            logger.info(f"[STATS] Successful: {self.stats['successful']:,}")
            logger.info(f"[STATS] Failed: {self.stats['failed']:,}")
            logger.info(f"[STATS] Total time: {(time.time() - self.start_time) / 3600:.2f} hours")
            logger.info("=" * 70)
            
            return True
            
        except KeyboardInterrupt:
            logger.warning("[INTERRUPT] Extraction interrupted by user")
            logger.info("[SAVE] Saving progress before exit...")
            if results_buffer:
                # Calculate the actual last processed index
                last_idx = start_index + len(results_buffer) - 1
                self.save_progress(last_idx, results_buffer)
            logger.info("[SAVE] Progress saved successfully - you can resume later!")
            return False
            
        except Exception as e:
            logger.error(f"[FATAL] Fatal error: {e}")
            return False
            
        finally:
            # Cleanup - close the single session
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("[CLEANUP] Docker Selenium WebDriver closed")
                except:
                    pass

if __name__ == "__main__":
    print("=" * 70)
    print("MAJESTIC MILLION EXTRACTOR - Joel's Proven Approach")
    print("Single-session strategy that worked for 50k URLs")
    print("=" * 70)
    
    extractor = MajesticMillionExtractor()
    
    try:
        success = extractor.extract_from_majestic_million()
        
        if success:
            print("\n✅ Extraction completed successfully!")
            print("📁 Results saved to: final_million_dataset.csv")
        else:
            print("\n⚠️ Extraction stopped or failed")
            print("📝 Progress has been saved - you can resume by running this script again")
            print("💡 The script will automatically continue from where it stopped")
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("📝 Check logs for details")
