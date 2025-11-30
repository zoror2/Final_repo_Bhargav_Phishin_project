import pandas as pd
import os

# CSV files with extracted features (not just URLs)
feature_files = [
    'joel_extracted_features.csv',
    'final_million_dataset.csv',
    'test_5_features.csv',
    'merged_training_dataset.csv'
]

print("=" * 80)
print("Merging Feature Datasets and Removing Duplicates")
print("=" * 80)

# List to store all dataframes
all_dataframes = []

# Read each file and inspect its structure
for file in feature_files:
    file_path = os.path.join(r'd:\Phishing LSTM Model', file)
    
    if os.path.exists(file_path):
        print(f"\nProcessing: {file}")
        try:
            df = pd.read_csv(file_path)
            print(f"  - Rows: {len(df)}")
            print(f"  - Columns: {len(df.columns)}")
            print(f"  - Features: {list(df.columns[:5])}... (showing first 5)")
            
            # Check if 'url' column exists
            if 'url' in df.columns:
                all_dataframes.append(df)
                print(f"  ✓ Added to merge list")
            else:
                print(f"  ✗ Skipped: No 'url' column found")
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
    else:
        print(f"\n✗ File not found: {file}")

print("\n" + "=" * 80)
print("Merging and Deduplicating")
print("=" * 80)

if not all_dataframes:
    print("ERROR: No valid dataframes to merge!")
else:
    # Concatenate all dataframes
    merged_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"\nTotal rows before deduplication: {len(merged_df)}")
    
    # Check for duplicates
    duplicate_count = merged_df['url'].duplicated().sum()
    print(f"Duplicate URLs found: {duplicate_count}")
    
    # Remove duplicates based on URL column, keeping the first occurrence
    merged_df = merged_df.drop_duplicates(subset=['url'], keep='first')
    print(f"Total rows after deduplication: {len(merged_df)}")
    
    # Get label distribution
    if 'label' in merged_df.columns:
        print(f"\nLabel distribution:")
        print(merged_df['label'].value_counts())
    
    # Save the final dataset
    output_file = 'final_lstm_training_dataset.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"\n✓ Final dataset saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print("Dataset Summary")
    print("=" * 80)
    print(f"Total unique URLs: {len(merged_df)}")
    print(f"Total features: {len(merged_df.columns)}")
    print(f"Column names: {list(merged_df.columns)}")
    print("\nFirst few rows:")
    print(merged_df.head(3))
