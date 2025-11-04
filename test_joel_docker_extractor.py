#!/usr/bin/env python3
"""
Test Joel Docker Selenium Extractor on 10 URLs
"""

import pandas as pd
from joel_docker_selenium_extractor import DockerSeleniumExtractor

def test_docker_extractor():
    """Test the Docker Selenium extractor on first 10 URLs"""
    print("🧪 Testing Joel Docker Selenium Extractor on 10 URLs")
    print("=" * 60)
    
    # Read dataset and take first 10 URLs
    df = pd.read_csv("Joel_dataset.csv")
    test_df = df.head(10)
    test_df.to_csv("test_joel_dataset.csv", index=False)
    
    print("📊 Test dataset created with 10 URLs:")
    print(test_df[['url', 'label']].to_string())
    print()
    
    # Create extractor
    extractor = DockerSeleniumExtractor(
        selenium_hub_url="http://localhost:4444/wd/hub",
        timeout=10
    )
    
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
        print(f"📊 Successful: {len(results_df[results_df['success'] == True])}")
        print(f"📊 Failed: {len(results_df[results_df['success'] == False])}")
        
        print("\n🔍 Sample results:")
        sample_cols = ['url', 'label', 'success', 'forms', 'password_fields', 'suspicious_keywords', 'page_load_time']
        print(results_df[sample_cols].head())
        
        print("\n🎯 Ready to process all 5k URLs!")
        print("Run: python joel_docker_selenium_extractor.py")
        
    else:
        print("\n❌ Test extraction failed!")

if __name__ == "__main__":
    test_docker_extractor()