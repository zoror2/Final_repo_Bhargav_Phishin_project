#!/usr/bin/env python3
"""
Create Joel Dataset - Extract 2.5k phishing + 2.5k legitimate URLs
This script creates a balanced dataset for LSTM model training
"""

import pandas as pd
import numpy as np
import random
from pathlib import Path

def create_joel_dataset():
    """
    Create Joel dataset with 2.5k phishing + 2.5k legitimate URLs
    """
    print("🔥 Creating Joel Dataset - 5k Balanced URLs")
    print("=" * 50)
    
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # File paths
    phishing_file = "Phishing URLs (1).csv"
    legitimate_file = "majestic_million.csv"
    output_file = "Joel_dataset.csv"
    
    # Read phishing URLs
    print("📖 Reading phishing URLs...")
    try:
        phishing_df = pd.read_csv(phishing_file)
        print(f"   Found {len(phishing_df)} total phishing URLs")
        
        # Sample 2500 phishing URLs
        if len(phishing_df) >= 2500:
            sampled_phishing = phishing_df.sample(n=2500, random_state=42)
            print(f"   ✅ Sampled 2500 phishing URLs")
        else:
            sampled_phishing = phishing_df
            print(f"   ⚠️  Only {len(phishing_df)} phishing URLs available")
            
    except Exception as e:
        print(f"   ❌ Error reading phishing file: {e}")
        return False
    
    # Read legitimate URLs (Majestic Million)
    print("📖 Reading legitimate URLs from Majestic Million...")
    try:
        # Try different encodings and read methods for large file
        legitimate_df = pd.read_csv(legitimate_file, 
                                  encoding='utf-8', 
                                  on_bad_lines='skip',
                                  low_memory=False)
        print(f"   Found {len(legitimate_df)} total legitimate URLs")
        
        # Sample 2500 legitimate URLs
        if len(legitimate_df) >= 2500:
            sampled_legitimate = legitimate_df.sample(n=2500, random_state=42)
            print(f"   ✅ Sampled 2500 legitimate URLs")
        else:
            sampled_legitimate = legitimate_df
            print(f"   ⚠️  Only {len(legitimate_df)} legitimate URLs available")
            
    except Exception as e:
        print(f"   ❌ Error reading legitimate file: {e}")
        print("   Trying alternative reading method...")
        try:
            # Alternative method - read in chunks
            chunks = []
            chunk_size = 10000
            for chunk in pd.read_csv(legitimate_file, chunksize=chunk_size, 
                                   encoding='utf-8', on_bad_lines='skip'):
                chunks.append(chunk)
                if len(chunks) * chunk_size >= 10000:  # Read at least 10k for sampling
                    break
            
            legitimate_df = pd.concat(chunks, ignore_index=True)
            sampled_legitimate = legitimate_df.sample(n=min(2500, len(legitimate_df)), random_state=42)
            print(f"   ✅ Sampled {len(sampled_legitimate)} legitimate URLs using chunks")
            
        except Exception as e2:
            print(f"   ❌ Failed both methods: {e2}")
            return False
    
    # Prepare datasets
    print("🔧 Preparing datasets...")
    
    # Prepare phishing data
    if 'url' in sampled_phishing.columns:
        phishing_urls = sampled_phishing[['url']].copy()
    elif 'URL' in sampled_phishing.columns:
        phishing_urls = sampled_phishing[['URL']].copy()
        phishing_urls.rename(columns={'URL': 'url'}, inplace=True)
    else:
        # Use first column as URL
        phishing_urls = pd.DataFrame({'url': sampled_phishing.iloc[:, 0]})
    
    phishing_urls['label'] = 'Phishing'
    phishing_urls['type'] = 1  # 1 for phishing
    
    # Prepare legitimate data
    if 'Domain' in sampled_legitimate.columns:
        # Majestic Million format
        legitimate_urls = pd.DataFrame({
            'url': 'https://' + sampled_legitimate['Domain'].astype(str)
        })
    elif 'domain' in sampled_legitimate.columns:
        legitimate_urls = pd.DataFrame({
            'url': 'https://' + sampled_legitimate['domain'].astype(str)
        })
    elif 'url' in sampled_legitimate.columns:
        legitimate_urls = sampled_legitimate[['url']].copy()
    else:
        # Use first column and add https
        legitimate_urls = pd.DataFrame({
            'url': 'https://' + sampled_legitimate.iloc[:, 0].astype(str)
        })
    
    legitimate_urls['label'] = 'Legitimate'
    legitimate_urls['type'] = 0  # 0 for legitimate
    
    # Combine datasets
    print("🔗 Combining datasets...")
    joel_dataset = pd.concat([phishing_urls, legitimate_urls], ignore_index=True)
    
    # Shuffle the dataset
    joel_dataset = joel_dataset.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Clean URLs (remove any malformed entries)
    print("🧹 Cleaning URLs...")
    joel_dataset = joel_dataset.dropna(subset=['url'])
    joel_dataset = joel_dataset[joel_dataset['url'].str.len() > 0]
    
    # Save dataset
    print("💾 Saving Joel dataset...")
    joel_dataset.to_csv(output_file, index=False)
    
    # Print summary
    print("\n📊 JOEL DATASET SUMMARY")
    print("=" * 30)
    print(f"Total URLs: {len(joel_dataset)}")
    print(f"Phishing URLs: {len(joel_dataset[joel_dataset['label'] == 'Phishing'])}")
    print(f"Legitimate URLs: {len(joel_dataset[joel_dataset['label'] == 'Legitimate'])}")
    print(f"Output file: {output_file}")
    
    # Show sample
    print("\n🔍 SAMPLE DATA:")
    print(joel_dataset.head(10))
    
    print(f"\n✅ Joel dataset created successfully!")
    print(f"📁 File saved as: {output_file}")
    
    return True

if __name__ == "__main__":
    success = create_joel_dataset()
    if success:
        print("\n🎉 Ready for Docker Selenium feature extraction!")
    else:
        print("\n❌ Failed to create Joel dataset")