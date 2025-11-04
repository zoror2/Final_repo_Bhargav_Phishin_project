#!/usr/bin/env python3
"""
Quick Feature Extraction Test
Test the extractor on a small sample before running on full dataset
"""

import pandas as pd
from joel_feature_extractor import JoelFeatureExtractor

def test_extractor():
    """Test the extractor on first 10 URLs"""
    print("🧪 Testing Joel Feature Extractor on 10 URLs")
    print("=" * 50)
    
    # Read dataset and take first 10 URLs
    df = pd.read_csv("Joel_dataset.csv")
    test_df = df.head(10)
    test_df.to_csv("test_joel_dataset.csv", index=False)
    
    # Create extractor
    extractor = JoelFeatureExtractor(headless=False, timeout=5)  # Non-headless for testing
    
    # Run extraction on test data
    success = extractor.extract_features_from_dataset(
        input_file="test_joel_dataset.csv",
        output_file="test_joel_features.csv"
    )
    
    if success:
        print("\n✅ Test extraction successful!")
        # Show results
        results_df = pd.read_csv("test_joel_features.csv")
        print(f"📊 Features extracted: {len(results_df.columns)}")
        print(f"📊 URLs processed: {len(results_df)}")
        print("\n🔍 Sample results:")
        print(results_df[['url', 'label', 'success', 'forms', 'password_fields', 'suspicious_keywords']].head())
    else:
        print("\n❌ Test extraction failed!")

if __name__ == "__main__":
    test_extractor()