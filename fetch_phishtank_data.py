import requests
import pandas as pd
import json
from datetime import datetime
import os

def fetch_phishtank_data():
    """
    Fetch phishing URLs from PhishTank API and save as CSV
    """
    print("Fetching PhishTank data...")
    
    # PhishTank API endpoint for verified phishing URLs
    url = "http://data.phishtank.com/data/online-valid.json"
    
    try:
        # Download the JSON data
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        print(f"Downloaded {len(response.content)} bytes")
        
        # Parse JSON
        phish_data = response.json()
        print(f"Found {len(phish_data)} phishing URLs")
        
        # Extract URLs and create DataFrame
        urls = []
        for entry in phish_data:
            if 'url' in entry:
                urls.append({
                    'url': entry['url'],
                    'label': 1,  # 1 = phishing
                    'phish_id': entry.get('phish_id', ''),
                    'submission_time': entry.get('submission_time', '')
                })
        
        # Create DataFrame
        df = pd.DataFrame(urls)
        
        # Save to CSV
        output_file = 'phish_urls.csv'
        df.to_csv(output_file, index=False)
        
        print(f"✅ Saved {len(df)} phishing URLs to {output_file}")
        print(f"Sample URLs:")
        print(df.head())
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    df = fetch_phishtank_data()
    if df is not None:
        print("\n📊 Dataset info:")
        print(f"Total phishing URLs: {len(df)}")
        print(f"Columns: {list(df.columns)}")