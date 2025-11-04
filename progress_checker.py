#!/usr/bin/env python3
"""
Progress Checker - Monitor overnight extraction progress
"""

import json
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

def check_extraction_progress():
    """Check and display current extraction progress"""
    print("OVERNIGHT EXTRACTION PROGRESS CHECKER")
    print("=" * 50)
    
    # Check progress file
    progress_file = "extraction_progress.json"
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            print(f"Last processed index: {progress.get('last_processed_index', 0)}")
            print(f"Total processed: {progress.get('total_processed', 0)}")
            print(f"Successful: {progress.get('successful', 0)}")
            print(f"Failed: {progress.get('failed', 0)}")
            
            if progress.get('total_processed', 0) > 0:
                success_rate = (progress.get('successful', 0) / progress.get('total_processed', 1)) * 100
                print(f"Success rate: {success_rate:.1f}%")
            
            # Calculate completion percentage
            total_urls = 5000  # Joel dataset size
            completion = (progress.get('last_processed_index', 0) / total_urls) * 100
            print(f"Overall completion: {completion:.1f}%")
            
            # Estimate remaining time
            if progress.get('last_processed_index', 0) > 0:
                start_time = datetime.fromisoformat(progress.get('start_time', datetime.now().isoformat()))
                elapsed = datetime.now() - start_time
                avg_time_per_url = elapsed.total_seconds() / progress.get('last_processed_index', 1)
                remaining_urls = total_urls - progress.get('last_processed_index', 0)
                estimated_remaining = remaining_urls * avg_time_per_url / 3600  # hours
                
                print(f"Elapsed time: {elapsed}")
                print(f"Estimated remaining: {estimated_remaining:.1f} hours")
            
        except Exception as e:
            print(f"Error reading progress file: {e}")
    else:
        print("No progress file found. Extraction hasn't started yet.")
    
    print("-" * 50)
    
    # Check output file
    output_file = "joel_extracted_features.csv"
    if os.path.exists(output_file):
        try:
            df = pd.read_csv(output_file)
            file_size = Path(output_file).stat().st_size / 1024 / 1024  # MB
            
            print(f"Features file: {len(df)} records")
            print(f"Features extracted: {len(df.columns) - 2} columns")  # -2 for url, label
            print(f"File size: {file_size:.2f} MB")
            print(f"Last updated: {datetime.fromtimestamp(Path(output_file).stat().st_mtime)}")
        except Exception as e:
            print(f"Error reading features file: {e}")
    else:
        print("No features file found yet.")
    
    print("-" * 50)
    
    # Check log file
    log_file = "overnight_extraction.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"Log file: {len(lines)} lines")
            print("Last 3 log entries:")
            for line in lines[-3:]:
                print(f"  {line.strip()}")
        except Exception as e:
            print(f"Error reading log file: {e}")
    else:
        print("No log file found.")

if __name__ == "__main__":
    check_extraction_progress()