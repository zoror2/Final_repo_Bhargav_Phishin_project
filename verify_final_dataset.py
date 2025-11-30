#!/usr/bin/env python3
"""
Verify and Analyze Final Dataset
Check the integrity and statistics of final_million_dataset.csv
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


def verify_dataset(filename="final_million_dataset.csv"):
    """Verify and analyze the final dataset"""
    
    print("="*70)
    print("📊 FINAL DATASET VERIFICATION & ANALYSIS")
    print("="*70)
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"\n❌ ERROR: File not found: {filename}")
        print("Please run the extraction first.")
        return False
    
    print(f"\n✅ File found: {filename}")
    
    # Get file size
    size_bytes = os.path.getsize(filename)
    size_mb = size_bytes / (1024 * 1024)
    size_gb = size_bytes / (1024 * 1024 * 1024)
    
    print(f"📦 File size: {size_mb:.2f} MB ({size_gb:.3f} GB)")
    
    # Read dataset
    try:
        print("\n📖 Loading dataset...")
        df = pd.read_csv(filename)
        print(f"✅ Successfully loaded dataset")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load dataset: {e}")
        return False
    
    # Basic info
    print("\n" + "="*70)
    print("📋 DATASET OVERVIEW")
    print("="*70)
    print(f"Total rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
    
    # Check expected columns
    expected_columns = [
        'url', 'label', 'success', 'num_events', 'ssl_valid', 'ssl_invalid',
        'redirects', 'forms', 'password_fields', 'iframes', 'scripts',
        'suspicious_keywords', 'external_requests', 'page_load_time',
        'has_errors', 'count_ssl_invalid', 'count_webdriver_error',
        'count_ssl_valid', 'count_redirects', 'count_external_requests',
        'count_forms_detected', 'count_password_fields', 'count_iframes_detected',
        'count_scripts_detected', 'count_suspicious_keywords', 'count_page_load_time'
    ]
    
    print("\n" + "="*70)
    print("✅ COLUMN VERIFICATION")
    print("="*70)
    
    missing_columns = set(expected_columns) - set(df.columns)
    extra_columns = set(df.columns) - set(expected_columns)
    
    if missing_columns:
        print(f"❌ Missing columns: {', '.join(missing_columns)}")
    else:
        print(f"✅ All {len(expected_columns)} expected columns present!")
    
    if extra_columns:
        print(f"ℹ️  Extra columns: {', '.join(extra_columns)}")
    
    print(f"\nColumns present: {', '.join(df.columns)}")
    
    # Data quality checks
    print("\n" + "="*70)
    print("🔍 DATA QUALITY CHECKS")
    print("="*70)
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    if missing_counts.sum() > 0:
        print("\n⚠️  Missing values detected:")
        for col in missing_counts[missing_counts > 0].index:
            pct = (missing_counts[col] / len(df)) * 100
            print(f"  {col}: {missing_counts[col]:,} ({pct:.2f}%)")
    else:
        print("✅ No missing values!")
    
    # Check for duplicates
    duplicates = df.duplicated(subset=['url']).sum()
    if duplicates > 0:
        print(f"\n⚠️  Duplicate URLs: {duplicates:,}")
    else:
        print("\n✅ No duplicate URLs!")
    
    # Statistics
    print("\n" + "="*70)
    print("📊 EXTRACTION STATISTICS")
    print("="*70)
    
    total = len(df)
    successful = df['success'].sum()
    failed = total - successful
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print(f"\nExtraction Success:")
    print(f"  ✅ Successful: {successful:,} ({success_rate:.2f}%)")
    print(f"  ❌ Failed: {failed:,} ({(failed/total)*100:.2f}%)")
    
    print(f"\nSSL Statistics:")
    print(f"  🔒 Valid SSL: {df['ssl_valid'].sum():,}")
    print(f"  ⚠️  Invalid SSL: {df['ssl_invalid'].sum():,}")
    print(f"  ℹ️  No SSL (HTTP): {total - df['ssl_valid'].sum() - df['ssl_invalid'].sum():,}")
    
    print(f"\nErrors:")
    print(f"  ⚠️  Has errors: {df['has_errors'].sum():,}")
    print(f"  ⏰ Timeout errors: {df[df['count_webdriver_error'] > 0].shape[0]:,}")
    
    print(f"\nRedirects:")
    print(f"  🔀 URLs with redirects: {df['redirects'].sum():,}")
    
    # Feature statistics
    print("\n" + "="*70)
    print("📈 FEATURE STATISTICS")
    print("="*70)
    
    print(f"\nForms:")
    print(f"  Average forms per page: {df['forms'].mean():.2f}")
    print(f"  Max forms on a page: {df['forms'].max()}")
    print(f"  Pages with forms: {df[df['forms'] > 0].shape[0]:,} ({df[df['forms'] > 0].shape[0]/total*100:.1f}%)")
    
    print(f"\nPassword Fields:")
    print(f"  Pages with password fields: {df[df['password_fields'] > 0].shape[0]:,}")
    print(f"  Average password fields: {df['password_fields'].mean():.2f}")
    
    print(f"\nIframes:")
    print(f"  Average iframes per page: {df['iframes'].mean():.2f}")
    print(f"  Max iframes: {df['iframes'].max()}")
    
    print(f"\nScripts:")
    print(f"  Average scripts per page: {df['scripts'].mean():.2f}")
    print(f"  Max scripts: {df['scripts'].max()}")
    
    print(f"\nSuspicious Keywords:")
    print(f"  Average per page: {df['suspicious_keywords'].mean():.2f}")
    print(f"  Max on a page: {df['suspicious_keywords'].max()}")
    print(f"  Pages with suspicious keywords: {df[df['suspicious_keywords'] > 0].shape[0]:,}")
    
    print(f"\nExternal Requests:")
    print(f"  Average per page: {df['external_requests'].mean():.2f}")
    print(f"  Max on a page: {df['external_requests'].max()}")
    
    print(f"\nPage Load Time:")
    print(f"  Average: {df['page_load_time'].mean():.2f}s")
    print(f"  Median: {df['page_load_time'].median():.2f}s")
    print(f"  Min: {df['page_load_time'].min():.2f}s")
    print(f"  Max: {df['page_load_time'].max():.2f}s")
    
    # Label distribution
    print("\n" + "="*70)
    print("🏷️  LABEL DISTRIBUTION")
    print("="*70)
    
    label_counts = df['label'].value_counts()
    print("\nLabel breakdown:")
    for label, count in label_counts.items():
        label_name = "Legitimate" if label == 0 else "Phishing"
        pct = (count / total) * 100
        print(f"  {label} ({label_name}): {count:,} ({pct:.2f}%)")
    
    # Sample data
    print("\n" + "="*70)
    print("📄 SAMPLE DATA (first 3 rows)")
    print("="*70)
    
    # Select key columns for display
    display_cols = ['url', 'label', 'success', 'ssl_valid', 'forms', 'password_fields', 
                   'iframes', 'scripts', 'suspicious_keywords', 'page_load_time', 'has_errors']
    available_cols = [col for col in display_cols if col in df.columns]
    
    print(df[available_cols].head(3).to_string(index=False))
    
    # Data types
    print("\n" + "="*70)
    print("🔤 DATA TYPES")
    print("="*70)
    print(df.dtypes.to_string())
    
    # Final verdict
    print("\n" + "="*70)
    print("✅ VERIFICATION COMPLETE")
    print("="*70)
    
    issues = []
    
    if missing_columns:
        issues.append(f"Missing {len(missing_columns)} expected columns")
    
    if missing_counts.sum() > 0:
        issues.append(f"Missing values in {len(missing_counts[missing_counts > 0])} columns")
    
    if duplicates > 0:
        issues.append(f"{duplicates} duplicate URLs")
    
    if success_rate < 50:
        issues.append(f"Low success rate: {success_rate:.1f}%")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nℹ️  Dataset may need review before training")
    else:
        print("\n✅ Dataset looks good! Ready for training!")
    
    print("\n📊 Summary:")
    print(f"  Total URLs: {len(df):,}")
    print(f"  Features: {len(df.columns)}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  File size: {size_mb:.2f} MB")
    
    print("\n🎯 Next Steps:")
    print("  1. Review the statistics above")
    print("  2. Combine with phishing dataset if needed (for label=1 samples)")
    print("  3. Upload to Kaggle for LSTM training")
    print("  4. Use all 26 features for model training")
    
    print("\n" + "="*70)
    
    return True


def export_summary(filename="final_million_dataset.csv", output="dataset_summary.txt"):
    """Export summary to text file"""
    
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return
    
    try:
        df = pd.read_csv(filename)
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("FINAL DATASET SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"File: {filename}\n")
            f.write(f"Total Rows: {len(df):,}\n")
            f.write(f"Total Columns: {len(df.columns)}\n")
            f.write(f"File Size: {os.path.getsize(filename) / (1024*1024):.2f} MB\n\n")
            
            f.write("Columns:\n")
            for col in df.columns:
                f.write(f"  - {col}\n")
            
            f.write("\nStatistics:\n")
            f.write(df.describe().to_string())
            
            f.write("\n\nLabel Distribution:\n")
            f.write(df['label'].value_counts().to_string())
            
        print(f"✅ Summary exported to: {output}")
        
    except Exception as e:
        print(f"❌ Error exporting summary: {e}")


def main():
    """Main function"""
    import sys
    
    filename = "final_million_dataset.csv"
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    verify_dataset(filename)
    
    # Ask if user wants to export summary
    print("\n💾 Export summary to file? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            export_summary(filename)
    except:
        pass


if __name__ == "__main__":
    main()
