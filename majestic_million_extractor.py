#!/usr/bin/env python3
"""
Majestic Million Feature Extractor - Production Grade
Extracts 26 features from majestic_million.csv using Docker Selenium
with crash recovery and automatic progress saving
"""

import pandas as pd
import numpy as np
import json
import time
import logging
import os
import ssl
import socket
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, 
    InvalidSessionIdException, NoSuchElementException
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
logger = logging.getLogger(__name__)

# Error-only logging
error_logger = logging.getLogger('errors')
error_handler = logging.FileHandler('extraction_errors_million.log', encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
error_logger.addHandler(error_handler)


class MajesticMillionExtractor:
    """
    Robust feature extractor with automatic progress saving and crash recovery
    """
    
    def __init__(
        self, 
        input_file="majestic_million.csv",
        output_file="final_million_dataset.csv",
        progress_file="extraction_progress_million.json",
        checkpoint_interval=100,
        selenium_hub_url="http://localhost:4444/wd/hub",
        timeout=15
    ):
        """Initialize the extractor with crash recovery capabilities"""
        
        self.input_file = input_file
        self.output_file = output_file
        self.temp_output_file = output_file.replace('.csv', '_temp.csv')
        self.progress_file = progress_file
        self.checkpoint_interval = checkpoint_interval
        self.selenium_hub_url = selenium_hub_url
        self.timeout = timeout
        
        self.driver = None
        self.suspicious_keywords = [
            'login', 'signin', 'password', 'bank', 'paypal', 'amazon', 'google',
            'facebook', 'apple', 'microsoft', 'secure', 'verify', 'account',
            'suspended', 'urgent', 'immediate', 'click', 'winner', 'congratulations',
            'free', 'prize', 'offer', 'limited', 'expire', 'confirm', 'update',
            'billing', 'payment', 'credit', 'card', 'ssn', 'social', 'security'
        ]
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'ssl_valid': 0,
            'ssl_invalid': 0,
            'timeout_errors': 0,
            'webdriver_errors': 0,
            'start_time': None,
            'last_checkpoint_time': None,
            'start_index': 0
        }
        
        # Feature columns (26 features total)
        self.feature_columns = [
            'url', 'label', 'success', 'num_events', 'ssl_valid', 'ssl_invalid',
            'redirects', 'forms', 'password_fields', 'iframes', 'scripts',
            'suspicious_keywords', 'external_requests', 'page_load_time',
            'has_errors', 'count_ssl_invalid', 'count_webdriver_error',
            'count_ssl_valid', 'count_redirects', 'count_external_requests',
            'count_forms_detected', 'count_password_fields', 'count_iframes_detected',
            'count_scripts_detected', 'count_suspicious_keywords', 'count_page_load_time'
        ]
    
    def setup_driver(self):
        """Setup Docker Selenium WebDriver with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to Docker Selenium (attempt {attempt + 1}/{max_retries})...")
                
                # Configure Chrome options
                chrome_options = Options()
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--disable-features=VizDisplayCompositor")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-images")  # Speed up loading
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument(
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                # Create remote driver
                self.driver = webdriver.Remote(
                    command_executor=self.selenium_hub_url,
                    options=chrome_options
                )
                
                self.driver.set_page_load_timeout(self.timeout)
                self.driver.implicitly_wait(3)
                
                logger.info("✅ Docker Selenium WebDriver connected successfully!")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to setup driver (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("❌ All connection attempts failed!")
                    logger.error("Make sure Docker Selenium is running:")
                    logger.error("  docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest")
                    return False
        
        return False
    
    def check_ssl_certificate(self, url):
        """Check SSL certificate validity"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme != 'https':
                return False, False  # Not HTTPS, no SSL to check
            
            hostname = parsed_url.hostname
            if not hostname:
                return False, False
            
            port = parsed_url.port or 443
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # SSL is valid
                    return True, False
                    
        except (ssl.SSLError, ssl.CertificateError):
            # SSL certificate error
            return False, True
        except Exception:
            # Other errors (timeout, connection refused, etc.)
            return False, False
    
    def extract_features(self, url, label=0):
        """
        Extract all 26 features from a single URL
        
        Args:
            url (str): URL to analyze
            label (int): Label (0 for legitimate, 1 for phishing)
        
        Returns:
            dict: Dictionary with all 26 features
        """
        # Initialize all features with default values
        features = {col: 0 for col in self.feature_columns}
        features['url'] = url
        features['label'] = label
        features['success'] = False
        features['has_errors'] = True
        features['page_load_time'] = 0.0
        
        start_time = time.time()
        
        try:
            # 1. Check SSL certificate (before loading page)
            ssl_valid, ssl_invalid = self.check_ssl_certificate(url)
            features['ssl_valid'] = 1 if ssl_valid else 0
            features['ssl_invalid'] = 1 if ssl_invalid else 0
            features['count_ssl_valid'] = 1 if ssl_valid else 0
            features['count_ssl_invalid'] = 1 if ssl_invalid else 0
            
            if ssl_valid:
                self.stats['ssl_valid'] += 1
            elif ssl_invalid:
                self.stats['ssl_invalid'] += 1
            
            # 2. Navigate to URL
            original_url = url
            self.driver.get(url)
            
            # 3. Wait for page load (with timeout)
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                pass  # Continue even if page doesn't fully load
            
            # 4. Calculate page load time
            load_time = time.time() - start_time
            features['page_load_time'] = round(load_time, 2)
            features['count_page_load_time'] = 1 if load_time > 0 else 0
            
            # 5. Check for redirects
            final_url = self.driver.current_url
            if final_url != original_url and not (original_url.endswith('/') or final_url == original_url + '/'):
                features['redirects'] = 1
                features['count_redirects'] = 1
            
            # 6. Extract page source for text analysis
            page_source = self.driver.page_source.lower()
            
            # 7. Count forms
            try:
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                features['forms'] = len(forms)
                features['count_forms_detected'] = len(forms)
            except Exception:
                pass
            
            # 8. Count password fields
            try:
                password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                features['password_fields'] = len(password_fields)
                features['count_password_fields'] = len(password_fields)
            except Exception:
                pass
            
            # 9. Count iframes
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                features['iframes'] = len(iframes)
                features['count_iframes_detected'] = len(iframes)
            except Exception:
                pass
            
            # 10. Count scripts
            try:
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                features['scripts'] = len(scripts)
                features['count_scripts_detected'] = len(scripts)
            except Exception:
                pass
            
            # 11. Count suspicious keywords
            suspicious_count = sum(1 for keyword in self.suspicious_keywords if keyword in page_source)
            features['suspicious_keywords'] = suspicious_count
            features['count_suspicious_keywords'] = suspicious_count
            
            # 12. Count external requests (approximate using external links)
            try:
                current_domain = urlparse(url).netloc.lower()
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                external_count = 0
                
                # Check first 50 links for performance
                for link in all_links[:50]:
                    try:
                        href = link.get_attribute("href")
                        if href and href.startswith("http"):
                            link_domain = urlparse(href).netloc.lower()
                            if link_domain and link_domain != current_domain:
                                external_count += 1
                    except:
                        continue
                
                features['external_requests'] = external_count
                features['count_external_requests'] = external_count
                
            except Exception:
                pass
            
            # 13. Calculate number of events (interactive elements)
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                num_events = (
                    features['forms'] +
                    features['password_fields'] +
                    len(buttons) +
                    len(inputs)
                )
                features['num_events'] = num_events
            except Exception:
                pass
            
            # Mark as successful extraction
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
            error_logger.error(f"TIMEOUT: {url}")
            
        except (WebDriverException, InvalidSessionIdException) as e:
            error_msg = str(e)
            
            # Check if this is a dead session error
            if "Cannot find session" in error_msg or "invalid session id" in error_msg.lower():
                logger.error(f"💀 SESSION DIED! Attempting to reconnect...")
                self.stats['webdriver_errors'] += 1
                error_logger.error(f"SESSION_DEAD: {url} - Reconnecting...")
                
                # Try to reconnect (up to 3 attempts)
                reconnected = False
                for attempt in range(1, 4):
                    try:
                        logger.info(f"🔄 Reconnection attempt {attempt}/3...")
                        if self.driver:
                            try:
                                self.driver.quit()
                            except:
                                pass
                        time.sleep(5)  # Wait 5 seconds before reconnecting
                        self.driver = self.setup_driver()
                        logger.info(f"✅ Session reconnected successfully!")
                        reconnected = True
                        break
                    except Exception as reconnect_error:
                        logger.error(f"❌ Reconnection attempt {attempt} failed: {str(reconnect_error)[:100]}")
                        if attempt < 3:
                            time.sleep(10)  # Wait longer between retries
                
                if not reconnected:
                    logger.critical("💀 FATAL: Could not reconnect to Docker Selenium after 3 attempts!")
                    raise Exception("Cannot reconnect to Docker Selenium")
                
                # Mark current URL as failed but continue with new session
                features['count_webdriver_error'] = 1
                features['has_errors'] = True
                self.stats['failed'] += 1
                
            else:
                # Other WebDriver errors (DNS, network, etc.) - just log and continue
                logger.warning(f"🌐 WebDriver error for URL {url}: {error_msg[:100]}")
                features['count_webdriver_error'] = 1
                features['has_errors'] = True
                self.stats['webdriver_errors'] += 1
                self.stats['failed'] += 1
                error_logger.error(f"WEBDRIVER: {url} - {error_msg[:200]}")
            
        except Exception as e:
            logger.error(f"❌ Unexpected error for URL {url}: {str(e)[:100]}")
            features['count_webdriver_error'] = 1
            features['has_errors'] = True
            self.stats['failed'] += 1
            error_logger.error(f"ERROR: {url} - {str(e)[:200]}")
        
        self.stats['total_processed'] += 1
        
        return features
    
    def save_progress(self, current_index, results_buffer):
        """
        Save progress to disk - CRASH RECOVERY CRITICAL
        
        Args:
            current_index (int): Current processing index
            results_buffer (list): List of feature dictionaries to save
        """
        try:
            # Save progress JSON
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
                'elapsed_hours': (time.time() - self.stats['start_time']) / 3600 if self.stats['start_time'] else 0
            }
            
            # Write progress file atomically
            progress_temp = self.progress_file + '.tmp'
            with open(progress_temp, 'w') as f:
                json.dump(progress_data, f, indent=2)
            os.replace(progress_temp, self.progress_file)
            
            # Save results to CSV
            if results_buffer:
                df_new = pd.DataFrame(results_buffer)
                
                # Check if main output file exists
                if os.path.exists(self.output_file):
                    # Append to existing file
                    df_new.to_csv(self.output_file, mode='a', header=False, index=False)
                else:
                    # Create new file with header
                    df_new.to_csv(self.output_file, mode='w', header=True, index=False)
                
                logger.info(f"💾 Checkpoint saved: {current_index} URLs processed, {len(results_buffer)} new rows saved")
            
            self.stats['last_checkpoint_time'] = time.time()
            
        except Exception as e:
            logger.error(f"❌ Error saving progress: {e}")
            error_logger.error(f"SAVE_ERROR: {e}")
    
    def load_progress(self):
        """
        Load previous progress if exists - RESUME FROM CRASH
        
        Returns:
            int: Index to start from (0 if no progress found)
        """
        if not os.path.exists(self.progress_file):
            logger.info("📝 No previous progress found - starting fresh")
            return 0
        
        try:
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
            
            start_index = progress.get('last_processed_index', 0)
            
            logger.info("="*70)
            logger.info("🔄 RESUMING FROM PREVIOUS RUN")
            logger.info("="*70)
            logger.info(f"📍 Last processed index: {start_index}")
            logger.info(f"✅ Previously successful: {progress.get('successful', 0)}")
            logger.info(f"❌ Previously failed: {progress.get('failed', 0)}")
            logger.info(f"🔒 SSL valid: {progress.get('ssl_valid', 0)}")
            logger.info(f"⚠️  SSL invalid: {progress.get('ssl_invalid', 0)}")
            logger.info(f"⏰ Previous timestamp: {progress.get('timestamp', 'Unknown')}")
            logger.info(f"⌚ Previous elapsed time: {progress.get('elapsed_hours', 0):.2f} hours")
            logger.info("="*70)
            
            # Update stats from previous run
            self.stats['total_processed'] = progress.get('total_processed', 0)
            self.stats['successful'] = progress.get('successful', 0)
            self.stats['failed'] = progress.get('failed', 0)
            self.stats['ssl_valid'] = progress.get('ssl_valid', 0)
            self.stats['ssl_invalid'] = progress.get('ssl_invalid', 0)
            self.stats['timeout_errors'] = progress.get('timeout_errors', 0)
            self.stats['webdriver_errors'] = progress.get('webdriver_errors', 0)
            
            return start_index
            
        except Exception as e:
            logger.error(f"❌ Error loading progress: {e} - starting from beginning")
            return 0
    
    def print_progress(self, current, total, url, success):
        """Print real-time progress information"""
        elapsed = time.time() - self.stats['start_time']
        processed_since_start = current - self.stats['start_index']
        
        if processed_since_start > 0:
            rate = processed_since_start / elapsed
            remaining = total - current
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_hours = eta_seconds / 3600
        else:
            rate = 0
            eta_hours = 0
        
        status = "✅" if success else "❌"
        success_rate = (self.stats['successful'] / self.stats['total_processed'] * 100) if self.stats['total_processed'] > 0 else 0
        
        print(f"\r{status} [{current:7d}/{total}] {current/total*100:5.1f}% | "
              f"Rate: {rate:.2f}/s | ETA: {eta_hours:.1f}h | "
              f"✅{self.stats['successful']} ❌{self.stats['failed']} ({success_rate:.1f}%) | "
              f"URL: {url[:35]}...", end="", flush=True)
    
    def extract_all_features(self):
        """
        Main extraction loop with automatic progress saving
        """
        logger.info("="*70)
        logger.info("🚀 MAJESTIC MILLION FEATURE EXTRACTION")
        logger.info("="*70)
        logger.info(f"📁 Input file: {self.input_file}")
        logger.info(f"📁 Output file: {self.output_file}")
        logger.info(f"💾 Progress file: {self.progress_file}")
        logger.info(f"🔄 Checkpoint interval: every {self.checkpoint_interval} URLs")
        logger.info(f"⏱️  Timeout per URL: {self.timeout} seconds")
        logger.info("="*70)
        
        # Load progress if resuming
        start_index = self.load_progress()
        self.stats['start_index'] = start_index
        
        # Setup Docker Selenium
        if not self.setup_driver():
            logger.error("❌ Failed to setup Docker Selenium - exiting")
            return False
        
        try:
            # Read input dataset
            logger.info(f"📖 Reading {self.input_file}...")
            
            # For very large files, read in chunks
            # First, check if we need to read specific columns
            try:
                # Try to read just the columns we need
                df = pd.read_csv(self.input_file, usecols=['GlobalRank', 'TldRank', 'Domain', 'TLD', 'RefSubNets', 'RefIPs'])
                # Create URL from Domain
                df['url'] = 'https://' + df['Domain'].astype(str)
                df['label'] = 0  # All are legitimate sites (Majestic Million)
                logger.info(f"✅ Loaded Majestic Million dataset with {len(df)} URLs")
            except Exception as e:
                logger.warning(f"⚠️  Standard column reading failed: {e}")
                # Fallback: try to read without column specification
                df = pd.read_csv(self.input_file)
                if 'url' not in df.columns:
                    if 'Domain' in df.columns:
                        df['url'] = 'https://' + df['Domain'].astype(str)
                    else:
                        logger.error("❌ Cannot find URL or Domain column in dataset")
                        return False
                if 'label' not in df.columns:
                    df['label'] = 0
                logger.info(f"✅ Loaded dataset with {len(df)} URLs")
            
            total_urls = len(df)
            remaining = total_urls - start_index
            
            logger.info(f"📊 Total URLs in dataset: {total_urls:,}")
            logger.info(f"📍 Starting from index: {start_index:,}")
            logger.info(f"📋 Remaining to process: {remaining:,}")
            logger.info("="*70)
            
            # Start timer
            self.stats['start_time'] = time.time()
            
            # Buffer for batch saving
            results_buffer = []
            
            # Process each URL
            for idx in range(start_index, total_urls):
                row = df.iloc[idx]
                url = row['url']
                label = row['label']
                
                # Extract features
                features = self.extract_features(url, label)
                results_buffer.append(features)
                
                # Print progress
                self.print_progress(idx + 1, total_urls, url, features['success'])
                
                # Save checkpoint
                if (idx + 1) % self.checkpoint_interval == 0:
                    print()  # New line before checkpoint message
                    self.save_progress(idx + 1, results_buffer)
                    results_buffer = []  # Clear buffer after saving
                    logger.info(f"✅ Checkpoint saved at URL #{idx + 1}")
                
                # Small delay to be respectful to websites
                time.sleep(0.1)
            
            # Save any remaining results
            print()  # New line after final progress
            if results_buffer:
                logger.info("💾 Saving final results...")
                self.save_progress(total_urls, results_buffer)
            
            # Print final statistics
            self.print_final_stats(total_urls)
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  EXTRACTION INTERRUPTED BY USER!")
            logger.warning("⚠️  Extraction interrupted by user")
            
            # Save whatever we have
            if results_buffer:
                logger.info("💾 Saving progress before exit...")
                current_index = start_index + len(results_buffer)
                self.save_progress(current_index, results_buffer)
            
            logger.info("✅ Progress saved successfully - you can resume later!")
            return False
            
        except Exception as e:
            logger.error(f"❌ Critical error during extraction: {e}")
            error_logger.error(f"CRITICAL: {e}")
            
            # Try to save whatever we have
            if results_buffer:
                try:
                    current_index = start_index + len(results_buffer)
                    self.save_progress(current_index, results_buffer)
                    logger.info("💾 Progress saved before crash")
                except:
                    logger.error("❌ Failed to save progress on crash")
            
            return False
            
        finally:
            # Cleanup
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("🚪 Docker Selenium WebDriver closed")
                except:
                    pass
    
    def print_final_stats(self, total_urls):
        """Print final extraction statistics"""
        elapsed = time.time() - self.stats['start_time']
        processed_this_run = self.stats['total_processed'] - self.stats['start_index']
        success_rate = (self.stats['successful'] / self.stats['total_processed'] * 100) if self.stats['total_processed'] > 0 else 0
        
        print("\n" + "="*70)
        print("🎉 FEATURE EXTRACTION COMPLETE!")
        print("="*70)
        print(f"📊 Total URLs processed: {self.stats['total_processed']:,} / {total_urls:,}")
        print(f"✅ Successful extractions: {self.stats['successful']:,} ({success_rate:.1f}%)")
        print(f"❌ Failed extractions: {self.stats['failed']:,}")
        print(f"🔒 SSL valid: {self.stats['ssl_valid']:,}")
        print(f"⚠️  SSL invalid: {self.stats['ssl_invalid']:,}")
        print(f"⏰ Timeout errors: {self.stats['timeout_errors']:,}")
        print(f"🌐 WebDriver errors: {self.stats['webdriver_errors']:,}")
        print(f"⏱️  Total time this run: {elapsed/3600:.2f} hours")
        print(f"📈 Average rate: {processed_this_run/elapsed:.2f} URLs/second" if elapsed > 0 else "")
        print(f"📁 Output file: {self.output_file}")
        print(f"📁 Progress file: {self.progress_file}")
        print(f"📁 Error log: extraction_errors_million.log")
        print("="*70)
        
        # Check output file size
        if os.path.exists(self.output_file):
            size_mb = os.path.getsize(self.output_file) / (1024 * 1024)
            print(f"📦 Output file size: {size_mb:.2f} MB")
            
            # Verify row count
            try:
                df_out = pd.read_csv(self.output_file)
                print(f"📝 Total rows in output: {len(df_out):,}")
                print(f"📋 Features per row: {len(df_out.columns)}")
            except:
                pass
        
        print("="*70)


def main():
    """Main execution function"""
    print("🚀 Majestic Million Feature Extractor - Production Grade")
    print("🛡️  Crash-resistant with automatic progress saving")
    print("="*70)
    
    # Create extractor instance
    extractor = MajesticMillionExtractor(
        input_file="majestic_million.csv",
        output_file="final_million_dataset.csv",
        progress_file="extraction_progress_million.json",
        checkpoint_interval=100,  # Save every 100 URLs
        selenium_hub_url="http://localhost:4444/wd/hub",
        timeout=15
    )
    
    # Run extraction
    success = extractor.extract_all_features()
    
    if success:
        print("\n✨ All extractions complete!")
        print(f"📁 Dataset ready: final_million_dataset.csv")
        print(f"🎯 Ready for Kaggle LSTM training!")
    else:
        print("\n⚠️  Extraction stopped or failed")
        print("📝 Progress has been saved - you can resume by running this script again")
        print("💡 The script will automatically continue from where it stopped")


if __name__ == "__main__":
    main()
