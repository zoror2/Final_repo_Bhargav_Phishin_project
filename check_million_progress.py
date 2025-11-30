#!/usr/bin/env python3
"""
Progress Checker for Majestic Million Feature Extraction
Real-time monitoring of extraction progress
"""

import json
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import time


def format_time(seconds):
    """Format seconds into human-readable time"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


def check_progress():
    """Check and display extraction progress"""
    
    print("="*70)
    print("📊 MAJESTIC MILLION EXTRACTION - PROGRESS MONITOR")
    print("="*70)
    print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Files to check
    progress_file = "extraction_progress_million.json"
    output_file = "final_million_dataset.csv"
    input_file = "majestic_million.csv"
    error_log = "extraction_errors_million.log"
    main_log = "extraction_million.log"
    
    # Check progress JSON
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            print("\n📝 PROGRESS FILE STATUS")
            print("-"*70)
            print(f"✅ Progress file found: {progress_file}")
            print(f"📍 Last processed index: {progress.get('last_processed_index', 0):,}")
            print(f"📊 Total processed: {progress.get('total_processed', 0):,}")
            print(f"✅ Successful: {progress.get('successful', 0):,}")
            print(f"❌ Failed: {progress.get('failed', 0):,}")
            print(f"🔒 SSL Valid: {progress.get('ssl_valid', 0):,}")
            print(f"⚠️  SSL Invalid: {progress.get('ssl_invalid', 0):,}")
            print(f"⏰ Timeout errors: {progress.get('timeout_errors', 0):,}")
            print(f"🌐 WebDriver errors: {progress.get('webdriver_errors', 0):,}")
            print(f"🕐 Last update: {progress.get('timestamp', 'Unknown')}")
            print(f"⌚ Elapsed time: {progress.get('elapsed_hours', 0):.2f} hours")
            
            # Calculate success rate
            total = progress.get('total_processed', 0)
            successful = progress.get('successful', 0)
            if total > 0:
                success_rate = (successful / total) * 100
                print(f"📈 Success rate: {success_rate:.2f}%")
            
        except Exception as e:
            print(f"\n❌ Error reading progress file: {e}")
    else:
        print("\n📝 PROGRESS FILE STATUS")
        print("-"*70)
        print(f"⚠️  No progress file found - extraction not started or no checkpoints yet")
    
    # Check output CSV
    if os.path.exists(output_file):
        try:
            print("\n📁 OUTPUT FILE STATUS")
            print("-"*70)
            
            # Get file size
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"✅ Output file found: {output_file}")
            print(f"📦 File size: {size_mb:.2f} MB")
            
            # Read CSV to get row count
            df = pd.read_csv(output_file)
            print(f"📝 Total rows extracted: {len(df):,}")
            print(f"📋 Total columns: {len(df.columns)}")
            
            # Show column names
            print(f"📋 Columns: {', '.join(df.columns[:10])}...")
            
            # Show sample statistics
            if len(df) > 0:
                print(f"\n📊 SAMPLE STATISTICS (from output file)")
                print("-"*70)
                successful_in_file = df['success'].sum()
                print(f"✅ Successful extractions: {successful_in_file:,} ({successful_in_file/len(df)*100:.1f}%)")
                print(f"🔒 SSL Valid: {df['ssl_valid'].sum():,}")
                print(f"⚠️  SSL Invalid: {df['ssl_invalid'].sum():,}")
                print(f"📝 Avg forms per page: {df['forms'].mean():.2f}")
                print(f"🔐 Pages with password fields: {df[df['password_fields'] > 0].shape[0]:,}")
                print(f"⏱️  Avg page load time: {df['page_load_time'].mean():.2f}s")
                
                # Show last processed URL
                if len(df) > 0:
                    last_row = df.iloc[-1]
                    print(f"\n🔍 LAST PROCESSED URL")
                    print("-"*70)
                    print(f"URL: {last_row['url']}")
                    print(f"Success: {'✅ Yes' if last_row['success'] else '❌ No'}")
                    print(f"Forms: {last_row['forms']}")
                    print(f"Scripts: {last_row['scripts']}")
                    print(f"Load time: {last_row['page_load_time']}s")
            
        except Exception as e:
            print(f"\n❌ Error reading output file: {e}")
    else:
        print("\n📁 OUTPUT FILE STATUS")
        print("-"*70)
        print(f"⚠️  No output file found yet - extraction may not have reached first checkpoint")
    
    # Check input file
    if os.path.exists(input_file):
        try:
            print("\n📂 INPUT FILE STATUS")
            print("-"*70)
            print(f"✅ Input file found: {input_file}")
            
            # For very large files, this might be slow
            try:
                df_input = pd.read_csv(input_file, nrows=1)
                print(f"✅ Input file is readable")
            except:
                print(f"⚠️  Input file is very large (Majestic Million)")
            
            # Try to count lines (rough estimate)
            try:
                size_mb = os.path.getsize(input_file) / (1024 * 1024)
                print(f"📦 Input file size: {size_mb:.2f} MB")
                
                # Rough estimate: ~1 million URLs expected
                estimated_urls = 1000000
                print(f"📊 Estimated total URLs: ~{estimated_urls:,}")
                
                # Calculate progress percentage
                if os.path.exists(progress_file):
                    with open(progress_file, 'r') as f:
                        progress = json.load(f)
                    processed = progress.get('last_processed_index', 0)
                    progress_pct = (processed / estimated_urls) * 100
                    remaining = estimated_urls - processed
                    
                    print(f"\n📈 OVERALL PROGRESS")
                    print("-"*70)
                    print(f"✅ Completed: {processed:,} / ~{estimated_urls:,} ({progress_pct:.2f}%)")
                    print(f"📋 Remaining: ~{remaining:,} URLs")
                    
                    # Estimate time remaining
                    elapsed_hours = progress.get('elapsed_hours', 0)
                    if processed > 0 and elapsed_hours > 0:
                        rate = processed / (elapsed_hours * 3600)  # URLs per second
                        remaining_seconds = remaining / rate if rate > 0 else 0
                        remaining_hours = remaining_seconds / 3600
                        
                        print(f"⏱️  Current rate: {rate:.2f} URLs/second")
                        print(f"⏰ Estimated time remaining: {remaining_hours:.1f} hours ({remaining_hours/24:.1f} days)")
                        
                        # Estimate completion time
                        import datetime as dt
                        completion_time = dt.datetime.now() + dt.timedelta(seconds=remaining_seconds)
                        print(f"🎯 Estimated completion: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
            except Exception as e:
                print(f"⚠️  Could not estimate: {e}")
                
        except Exception as e:
            print(f"\n❌ Error checking input file: {e}")
    else:
        print("\n📂 INPUT FILE STATUS")
        print("-"*70)
        print(f"❌ Input file not found: {input_file}")
        print(f"⚠️  Please ensure majestic_million.csv is in the current directory")
    
    # Check error log
    if os.path.exists(error_log):
        try:
            with open(error_log, 'r', encoding='utf-8') as f:
                error_lines = f.readlines()
            
            print(f"\n⚠️  ERROR LOG STATUS")
            print("-"*70)
            print(f"📁 Error log found: {error_log}")
            print(f"📝 Total error entries: {len(error_lines)}")
            
            if len(error_lines) > 0:
                print(f"\n🔍 RECENT ERRORS (last 5)")
                print("-"*70)
                for line in error_lines[-5:]:
                    print(f"  {line.strip()}")
            
        except Exception as e:
            print(f"\n⚠️  Error reading error log: {e}")
    else:
        print(f"\n⚠️  ERROR LOG STATUS")
        print("-"*70)
        print(f"✅ No error log found - good sign or extraction not started")
    
    # Check main log
    if os.path.exists(main_log):
        try:
            print(f"\n📋 MAIN LOG STATUS")
            print("-"*70)
            print(f"✅ Main log found: {main_log}")
            
            with open(main_log, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            print(f"📝 Total log entries: {len(log_lines)}")
            
            if len(log_lines) > 0:
                print(f"\n🔍 RECENT LOG ENTRIES (last 10)")
                print("-"*70)
                for line in log_lines[-10:]:
                    print(f"  {line.strip()}")
            
        except Exception as e:
            print(f"\n⚠️  Error reading main log: {e}")
    
    print("\n" + "="*70)
    print("💡 TIP: Run this script periodically to monitor progress")
    print("💡 TIP: If extraction stopped, just run majestic_million_extractor.py again")
    print("💡 TIP: All progress is automatically saved - safe to stop anytime!")
    print("="*70)


def watch_progress(interval=60):
    """
    Continuously watch progress (update every interval seconds)
    
    Args:
        interval (int): Seconds between updates
    """
    print("🔄 Starting continuous progress monitoring...")
    print(f"📊 Updating every {interval} seconds")
    print("⚠️  Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            check_progress()
            print(f"\n⏰ Next update in {interval} seconds...\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n✋ Monitoring stopped by user")


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--watch':
        # Continuous monitoring mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        watch_progress(interval)
    else:
        # Single check
        check_progress()
        
        print("\n💡 USAGE OPTIONS:")
        print("  python check_million_progress.py              # Check once")
        print("  python check_million_progress.py --watch      # Watch continuously (60s interval)")
        print("  python check_million_progress.py --watch 30   # Watch continuously (30s interval)")


if __name__ == "__main__":
    main()
