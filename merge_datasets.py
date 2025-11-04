#!/usr/bin/env python3
"""
Dataset Merger Script
Merges joel_extracted_features.csv with events_dataset_full.csv for LSTM training
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dataset_merger.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def merge_datasets():
    """Merge Joel's extracted features with events_dataset_full.csv"""
    
    print("=" * 70)
    print("DATASET MERGER FOR LSTM TRAINING")
    print("=" * 70)
    
    # File paths
    joel_file = "joel_extracted_features.csv"
    events_file = "../Phising_datasets/events_dataset_full.csv"
    output_file = "merged_training_dataset.csv"
    
    try:
        # Load Joel's extracted features
        print("Loading Joel's extracted features...")
        joel_df = pd.read_csv(joel_file)
        logger.info(f"Joel's dataset loaded: {len(joel_df)} rows, {len(joel_df.columns)} columns")
        
        # Load events dataset full
        print("Loading events_dataset_full.csv...")
        events_df = pd.read_csv(events_file)
        logger.info(f"Events dataset loaded: {len(events_df)} rows, {len(events_df.columns)} columns")
        
        # Display dataset info
        print("\n" + "-" * 50)
        print("DATASET INFORMATION")
        print("-" * 50)
        print(f"Joel's Features Dataset:")
        print(f"  - Rows: {len(joel_df)}")
        print(f"  - Columns: {len(joel_df.columns)}")
        print(f"  - Phishing URLs: {sum(joel_df['label'] == 1)}")
        print(f"  - Legitimate URLs: {sum(joel_df['label'] == 0)}")
        print(f"  - File size: {Path(joel_file).stat().st_size / 1024 / 1024:.2f} MB")
        
        print(f"\nEvents Dataset Full:")
        print(f"  - Rows: {len(events_df)}")
        print(f"  - Columns: {len(events_df.columns)}")
        print(f"  - Phishing URLs: {sum(events_df['label'] == 1)}")
        print(f"  - Legitimate URLs: {sum(events_df['label'] == 0)}")
        print(f"  - File size: {Path(events_file).stat().st_size / 1024 / 1024:.2f} MB")
        
        # Check column compatibility
        print("\n" + "-" * 50)
        print("COLUMN COMPATIBILITY CHECK")
        print("-" * 50)
        
        joel_columns = set(joel_df.columns)
        events_columns = set(events_df.columns)
        
        if joel_columns == events_columns:
            print("✅ PERFECT! All columns match exactly")
            print(f"Common columns: {len(joel_columns)}")
        else:
            missing_in_joel = events_columns - joel_columns
            missing_in_events = joel_columns - events_columns
            
            if missing_in_joel:
                print(f"❌ Missing in Joel's dataset: {missing_in_joel}")
            if missing_in_events:
                print(f"❌ Missing in Events dataset: {missing_in_events}")
            
            print("⚠️  Column mismatch detected!")
            return False
        
        # Check for duplicate URLs
        print("\n" + "-" * 50)
        print("DUPLICATE URL CHECK")
        print("-" * 50)
        
        joel_urls = set(joel_df['url'])
        events_urls = set(events_df['url'])
        common_urls = joel_urls & events_urls
        
        print(f"URLs in Joel's dataset: {len(joel_urls)}")
        print(f"URLs in Events dataset: {len(events_urls)}")
        print(f"Common URLs: {len(common_urls)}")
        
        if len(common_urls) > 0:
            print(f"⚠️  {len(common_urls)} duplicate URLs found")
            print("First few duplicates:")
            for i, url in enumerate(list(common_urls)[:5]):
                print(f"  {i+1}. {url}")
            
            # Option to remove duplicates
            response = input("\nRemove duplicates from Events dataset? (y/n): ").lower()
            if response in ['y', 'yes']:
                events_df = events_df[~events_df['url'].isin(common_urls)]
                print(f"✅ Removed {len(common_urls)} duplicates from Events dataset")
                print(f"Events dataset now has: {len(events_df)} rows")
        else:
            print("✅ No duplicate URLs found")
        
        # Merge datasets
        print("\n" + "-" * 50)
        print("MERGING DATASETS")
        print("-" * 50)
        
        # Ensure column order is the same
        column_order = joel_df.columns.tolist()
        events_df = events_df[column_order]
        
        # Concatenate datasets
        merged_df = pd.concat([joel_df, events_df], ignore_index=True)
        
        print(f"✅ Datasets merged successfully!")
        print(f"Final dataset shape: {merged_df.shape}")
        
        # Final dataset statistics
        print("\n" + "-" * 50)
        print("MERGED DATASET STATISTICS")
        print("-" * 50)
        print(f"Total URLs: {len(merged_df)}")
        print(f"Phishing URLs: {sum(merged_df['label'] == 1)} ({sum(merged_df['label'] == 1)/len(merged_df)*100:.1f}%)")
        print(f"Legitimate URLs: {sum(merged_df['label'] == 0)} ({sum(merged_df['label'] == 0)/len(merged_df)*100:.1f}%)")
        print(f"Successful extractions: {sum(merged_df['success'] == True)} ({sum(merged_df['success'] == True)/len(merged_df)*100:.1f}%)")
        print(f"Failed extractions: {sum(merged_df['success'] == False)} ({sum(merged_df['success'] == False)/len(merged_df)*100:.1f}%)")
        
        # Check data quality
        print("\n" + "-" * 50)
        print("DATA QUALITY CHECK")
        print("-" * 50)
        
        # Missing values
        missing_values = merged_df.isnull().sum().sum()
        print(f"Missing values: {missing_values}")
        
        # Data types
        print(f"Data types:")
        for dtype in merged_df.dtypes.value_counts().items():
            print(f"  {dtype[0]}: {dtype[1]} columns")
        
        # Save merged dataset
        print("\n" + "-" * 50)
        print("SAVING MERGED DATASET")
        print("-" * 50)
        
        merged_df.to_csv(output_file, index=False)
        file_size = Path(output_file).stat().st_size / 1024 / 1024
        
        print(f"✅ Merged dataset saved to: {output_file}")
        print(f"File size: {file_size:.2f} MB")
        
        # Summary for LSTM training
        print("\n" + "=" * 70)
        print("READY FOR LSTM TRAINING!")
        print("=" * 70)
        print(f"📄 Training file: {output_file}")
        print(f"📊 Total samples: {len(merged_df)}")
        print(f"🎯 Features: {len(merged_df.columns) - 1}")  # -1 for URL column
        print(f"⚖️  Class balance: {sum(merged_df['label'] == 1)} phishing, {sum(merged_df['label'] == 0)} legitimate")
        print(f"✅ Format: Ready for pandas/sklearn/tensorflow")
        print("\nNext steps:")
        print("1. Upload to Kaggle")
        print("2. Train LSTM model")
        print("3. Evaluate performance")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during dataset merger: {e}")
        print(f"❌ Error: {e}")
        return False

def analyze_merged_dataset():
    """Analyze the merged dataset for LSTM training insights"""
    
    output_file = "merged_training_dataset.csv"
    
    if not Path(output_file).exists():
        print(f"❌ {output_file} not found. Run merge first.")
        return
    
    print("\n" + "=" * 70)
    print("MERGED DATASET ANALYSIS FOR LSTM")
    print("=" * 70)
    
    try:
        df = pd.read_csv(output_file)
        
        # Feature analysis
        print("Feature Analysis:")
        numerical_features = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = df.select_dtypes(include=['object']).columns.tolist()
        
        print(f"  Numerical features: {len(numerical_features)}")
        print(f"  Categorical features: {len(categorical_features)}")
        
        # Remove non-feature columns
        feature_columns = [col for col in numerical_features if col not in ['label']]
        print(f"  Training features: {len(feature_columns)}")
        
        # Feature statistics
        print(f"\nFeature Statistics:")
        print(f"  Feature range: {df[feature_columns].min().min():.2f} to {df[feature_columns].max().max():.2f}")
        print(f"  Features with zeros: {(df[feature_columns] == 0).all().sum()}")
        print(f"  Features with missing values: {df[feature_columns].isnull().any().sum()}")
        
        # Label distribution
        print(f"\nLabel Distribution:")
        label_counts = df['label'].value_counts()
        for label, count in label_counts.items():
            label_name = "Phishing" if label == 1 else "Legitimate"
            print(f"  {label_name}: {count} ({count/len(df)*100:.1f}%)")
        
        # LSTM readiness check
        print(f"\n🚀 LSTM Training Readiness:")
        print(f"  ✅ Balanced dataset: {abs(label_counts[0] - label_counts[1]) < len(df) * 0.3}")
        print(f"  ✅ Sufficient samples: {len(df) >= 1000}")
        print(f"  ✅ Feature count: {len(feature_columns)} features")
        print(f"  ✅ Clean data: {df.isnull().sum().sum() == 0}")
        
    except Exception as e:
        print(f"❌ Error analyzing dataset: {e}")

if __name__ == "__main__":
    print("🔗 DATASET MERGER FOR LSTM TRAINING")
    print("Merging joel_extracted_features.csv + events_dataset_full.csv")
    print("=" * 70)
    
    # Run merger
    success = merge_datasets()
    
    if success:
        # Analyze merged dataset
        analyze_merged_dataset()
        
        print("\n🎉 MERGER COMPLETED SUCCESSFULLY!")
        print("Your dataset is ready for LSTM training on Kaggle!")
    else:
        print("\n❌ MERGER FAILED!")
        print("Check the logs for details.")