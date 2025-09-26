import pandas as pd
import numpy as np
from sklearn.utils import shuffle

def combine_datasets():
    """
    Combine phishing and legitimate URLs into a single balanced dataset
    """
    print("Combining datasets...")
    
    try:
        # Load phishing URLs
        phish_df = pd.read_csv('phish_urls.csv')
        print(f"Loaded {len(phish_df)} phishing URLs")
        
        # Load legitimate URLs
        legit_df = pd.read_csv('legit_urls.csv')
        print(f"Loaded {len(legit_df)} legitimate URLs")
        
        # Keep only url and label columns for consistency
        phish_clean = phish_df[['url', 'label']].copy()
        legit_clean = legit_df[['url', 'label']].copy()
        
        # Balance the dataset - take equal numbers from each class
        min_count = min(len(phish_clean), len(legit_clean))
        print(f"Balancing dataset to {min_count} samples per class")
        
        phish_balanced = phish_clean.head(min_count)
        legit_balanced = legit_clean.head(min_count)
        
        # Combine datasets
        combined_df = pd.concat([phish_balanced, legit_balanced], ignore_index=True)
        
        # Shuffle the dataset
        combined_df = shuffle(combined_df, random_state=42).reset_index(drop=True)
        
        # Save combined dataset
        output_file = 'urls_dataset.csv'
        combined_df.to_csv(output_file, index=False)
        
        print(f"✅ Combined dataset saved to {output_file}")
        print(f"Total samples: {len(combined_df)}")
        print(f"Class distribution:")
        print(combined_df['label'].value_counts())
        print(f"\nSample data:")
        print(combined_df.head(10))
        
        return combined_df
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("Make sure to run fetch_phishtank_data.py and fetch_tranco_data.py first")
        return None
    except Exception as e:
        print(f"❌ Error combining datasets: {e}")
        return None

if __name__ == "__main__":
    df = combine_datasets()
    if df is not None:
        print("\n📊 Final dataset ready for event logging!")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")