#!/usr/bin/env python3
"""
Script to create a small balanced dataset from urls_dataset.csv
Extracts 10 legitimate and 10 phishing URLs for demonstration purposes
"""

import pandas as pd
import random

def create_small_dataset():
    print("Reading urls_dataset.csv...")
    
    # Read the full dataset
    df = pd.read_csv('urls_dataset.csv')
    
    print(f"Total URLs in dataset: {len(df)}")
    
    # Separate legitimate and phishing URLs
    legit_urls = df[df['label'] == 0].copy()
    phish_urls = df[df['label'] == 1].copy()
    
    print(f"Legitimate URLs: {len(legit_urls)}")
    print(f"Phishing URLs: {len(phish_urls)}")
    
    # Randomly sample 10 URLs from each category
    random.seed(42)  # For reproducible results
    
    sample_legit = legit_urls.sample(n=10, random_state=42)
    sample_phish = phish_urls.sample(n=10, random_state=42)
    
    # Combine the samples
    small_dataset = pd.concat([sample_legit, sample_phish], ignore_index=True)
    
    # Shuffle the combined dataset
    small_dataset = small_dataset.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to small_dataset.csv
    small_dataset.to_csv('small_dataset.csv', index=False)
    
    print(f"\nSmall dataset created with {len(small_dataset)} URLs:")
    print(f"- Legitimate URLs: {len(small_dataset[small_dataset['label'] == 0])}")
    print(f"- Phishing URLs: {len(small_dataset[small_dataset['label'] == 1])}")
    print("\nSaved as 'small_dataset.csv'")
    
    # Display the sample URLs
    print("\nSample URLs in the small dataset:")
    for i, row in small_dataset.iterrows():
        label_type = "Legitimate" if row['label'] == 0 else "Phishing"
        print(f"{i+1:2d}. [{label_type:10s}] {row['url']}")

if __name__ == "__main__":
    create_small_dataset()