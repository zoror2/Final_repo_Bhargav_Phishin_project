#!/usr/bin/env python3
"""
Progress checker for Joel dataset extraction
"""

import pandas as pd
import time
from pathlib import Path

def check_progress():
    """Check extraction progress"""
    output_file = "Joel_dataset_features.csv"
    log_file = "joel_extraction.log"
    
    print("Joel Dataset Feature Extraction - Progress Checker")
    print("=" * 50)
    
    # Check if output file exists
    if Path(output_file).exists():
        try:
            df = pd.read_csv(output_file)
            extracted_count = len(df)
            print(f"✓ Features extracted so far: {extracted_count}")
            
            if extracted_count > 0:
                print(f"✓ Sample features from first URL:")
                sample = df.iloc[0]
                print(f"  URL: {sample['url']}")
                print(f"  Label: {sample['label']}")
                print(f"  URL Length: {sample['url_length']}")
                print(f"  Has SSL: {sample['has_ssl']}")
                print(f"  Form Count: {sample['form_count']}")
                print(f"  Link Count: {sample['link_count']}")
                
        except Exception as e:
            print(f"✗ Error reading output file: {e}")
    else:
        print("- Output file not created yet")
    
    # Check log file for latest status
    if Path(log_file).exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print(f"✓ Latest log entries:")
                    for line in lines[-5:]:  # Show last 5 lines
                        print(f"  {line.strip()}")
        except Exception as e:
            print(f"✗ Error reading log file: {e}")
    else:
        print("- Log file not found")
    
    # Check total target
    target_file = "Joel_dataset.csv"
    if Path(target_file).exists():
        try:
            target_df = pd.read_csv(target_file)
            total_target = len(target_df)
            print(f"✓ Total URLs to process: {total_target}")
            
            if Path(output_file).exists():
                progress_percent = (extracted_count / total_target) * 100
                print(f"✓ Progress: {progress_percent:.1f}% complete")
                
                if extracted_count > 0:
                    # Estimate remaining time based on current progress
                    # This is rough since we don't know exact start time
                    print(f"✓ Remaining URLs: {total_target - extracted_count}")
                    
        except Exception as e:
            print(f"✗ Error reading target file: {e}")

if __name__ == "__main__":
    check_progress()