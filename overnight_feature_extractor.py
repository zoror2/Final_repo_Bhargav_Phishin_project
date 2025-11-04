#!/usr/bin/env python3
"""
Overnight Feature Extraction Script
Robust script that saves progress incrementally and can be safely interrupted
"""

import pandas as pd
import numpy as np
import time
import logging
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from joel_docker_selenium_extractor_fixed import DockerSeleniumExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('overnight_extraction.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class OvernightExtractor:
    def __init__(self):
        self.input_file = "Joel_dataset.csv"
        self.output_file = "joel_extracted_features.csv"  # Same format as events_dataset_full.csv
        self.progress_file = "extraction_progress.json"
        self.batch_size = 50  # Save progress every 50 URLs
        self.extractor = DockerSeleniumExtractor()
        self.should_stop = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle interruption signals gracefully"""
        logger.info("Received interruption signal. Finishing current URL and saving progress...")
        self.should_stop = True
    
    def load_progress(self):
        """Load extraction progress from file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                logger.info(f"Resuming from URL index {progress.get('last_processed_index', 0)}")
                return progress
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}. Starting fresh.")
        
        return {
            'last_processed_index': 0,
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': datetime.now().isoformat()
        }
    
    def save_progress(self, progress):
        """Save extraction progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save progress: {e}")
    
    def load_existing_results(self):
        """Load existing extracted features if any"""
        if os.path.exists(self.output_file):
            try:
                df = pd.read_csv(self.output_file)
                logger.info(f"Found existing results file with {len(df)} records")
                return df
            except Exception as e:
                logger.warning(f"Could not load existing results: {e}")
        
        return pd.DataFrame()
    
    def save_features_batch(self, new_features_list, existing_df):
        """Save a batch of features to file"""
        try:
            if new_features_list:
                new_df = pd.DataFrame(new_features_list)
                
                if len(existing_df) > 0:
                    # Append to existing data
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    combined_df = new_df
                
                # Save to file
                combined_df.to_csv(self.output_file, index=False)
                logger.info(f"Saved batch of {len(new_features_list)} features. Total: {len(combined_df)}")
                return combined_df
            
        except Exception as e:
            logger.error(f"Error saving features batch: {e}")
        
        return existing_df
    
    def extract_overnight(self):
        """Main extraction function that runs overnight"""
        logger.info("Starting overnight feature extraction")
        logger.info("=" * 70)
        
        # Load progress and existing results
        progress = self.load_progress()
        existing_results = self.load_existing_results()
        
        # Load dataset
        try:
            df = pd.read_csv(self.input_file)
            total_urls = len(df)
            start_index = progress['last_processed_index']
            
            logger.info(f"Dataset loaded: {total_urls} URLs")
            logger.info(f"Starting from index: {start_index}")
            logger.info(f"Remaining URLs: {total_urls - start_index}")
            
        except Exception as e:
            logger.error(f"Could not load dataset: {e}")
            return False
        
        # Setup Docker Selenium
        if not self.extractor.setup_driver():
            logger.error("Failed to setup Docker Selenium WebDriver")
            return False
        
        # Extract features
        batch_features = []
        current_results = existing_results.copy()
        
        try:
            for idx in range(start_index, total_urls):
                if self.should_stop:
                    logger.info("Stopping extraction due to interruption signal")
                    break
                
                row = df.iloc[idx]
                url = row['url']
                label = row.get('label', None)
                
                # Extract features for this URL
                logger.info(f"Processing {idx + 1}/{total_urls}: {url[:80]}")
                features, success = self.extractor.extract_features_for_url(url, label)
                
                if success and features:
                    batch_features.append(features)
                    progress['successful'] += 1
                else:
                    progress['failed'] += 1
                
                progress['total_processed'] += 1
                progress['last_processed_index'] = idx + 1
                
                # Save batch every N URLs
                if len(batch_features) >= self.batch_size:
                    current_results = self.save_features_batch(batch_features, current_results)
                    batch_features = []
                    self.save_progress(progress)
                    
                    # Log progress
                    self.log_progress(progress, total_urls)
                
                # Small delay to prevent overwhelming
                time.sleep(0.5)
            
            # Save any remaining features
            if batch_features:
                current_results = self.save_features_batch(batch_features, current_results)
                self.save_progress(progress)
            
            # Final stats
            self.print_final_stats(progress, current_results)
            return True
            
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            # Save current progress before exiting
            if batch_features:
                self.save_features_batch(batch_features, current_results)
            self.save_progress(progress)
            return False
        
        finally:
            # Cleanup
            self.extractor.cleanup()
    
    def log_progress(self, progress, total_urls):
        """Log current progress"""
        completion = (progress['last_processed_index'] / total_urls) * 100
        success_rate = (progress['successful'] / progress['total_processed'] * 100) if progress['total_processed'] > 0 else 0
        
        logger.info(f"PROGRESS: {progress['last_processed_index']}/{total_urls} ({completion:.1f}%)")
        logger.info(f"SUCCESS RATE: {progress['successful']}/{progress['total_processed']} ({success_rate:.1f}%)")
        logger.info(f"FAILED: {progress['failed']}")
    
    def print_final_stats(self, progress, results_df):
        """Print final extraction statistics"""
        print("\n" + "=" * 70)
        print("OVERNIGHT EXTRACTION COMPLETED")
        print("=" * 70)
        print(f"Total URLs processed: {progress['total_processed']}")
        print(f"Successful extractions: {progress['successful']}")
        print(f"Failed extractions: {progress['failed']}")
        
        if progress['total_processed'] > 0:
            success_rate = (progress['successful'] / progress['total_processed']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        if len(results_df) > 0:
            print(f"Features extracted: {len(results_df.columns) - 2} columns")  # -2 for url, label
            print(f"Total records saved: {len(results_df)}")
            file_size = Path(self.output_file).stat().st_size / 1024 / 1024
            print(f"Output file size: {file_size:.2f} MB")
        
        print(f"Results saved to: {self.output_file}")
        print(f"Log file: overnight_extraction.log")

def merge_datasets():
    """Merge the extracted features with events_dataset.csv"""
    print("\n" + "=" * 70)
    print("MERGING DATASETS")
    print("=" * 70)
    
    try:
        # Load both datasets
        events_df = pd.read_csv("../Phising_datasets/events_dataset.csv")
        extracted_df = pd.read_csv("joel_extracted_features.csv")
        
        print(f"Events dataset: {len(events_df)} rows, {len(events_df.columns)} columns")
        print(f"Extracted features: {len(extracted_df)} rows, {len(extracted_df.columns)} columns")
        
        # Merge datasets
        # Note: You might want to merge on URL or concatenate depending on your needs
        merged_df = pd.concat([events_df, extracted_df], ignore_index=True)
        
        # Save merged dataset
        output_file = "merged_training_dataset.csv"
        merged_df.to_csv(output_file, index=False)
        
        print(f"Merged dataset: {len(merged_df)} rows, {len(merged_df.columns)} columns")
        print(f"Merged dataset saved to: {output_file}")
        print("Ready for LSTM training!")
        
    except Exception as e:
        print(f"Error merging datasets: {e}")

if __name__ == "__main__":
    print("OVERNIGHT FEATURE EXTRACTION SCRIPT")
    print("====================================")
    print("This script will:")
    print("1. Extract features from Joel_dataset.csv using Docker Selenium")
    print("2. Save progress incrementally (every 50 URLs)")
    print("3. Handle interruptions gracefully (Ctrl+C)")
    print("4. Resume from where it left off if restarted")
    print("5. Merge with events_dataset.csv when complete")
    print("\nPress Ctrl+C anytime to stop safely")
    print("=" * 70)
    
    # Run extraction
    extractor = OvernightExtractor()
    
    try:
        success = extractor.extract_overnight()
        
        if success:
            print("\nExtraction completed successfully!")
            
            # Ask if user wants to merge datasets
            response = input("\nMerge with events_dataset.csv now? (y/n): ").lower()
            if response in ['y', 'yes']:
                merge_datasets()
        else:
            print("\nExtraction was interrupted or failed.")
            print("You can restart this script to resume from where it left off.")
            
    except KeyboardInterrupt:
        print("\n\nExtraction interrupted by user.")
        print("Progress has been saved. Restart the script to continue.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Check the log file for details: overnight_extraction.log")