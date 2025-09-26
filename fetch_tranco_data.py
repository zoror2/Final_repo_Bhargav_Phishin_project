import requests
import pandas as pd
import zipfile
import io
from datetime import datetime

def fetch_tranco_data(num_urls=10000):
    """
    Fetch legitimate URLs from Tranco top sites list
    """
    print("Fetching Tranco top sites data...")
    
    # Tranco top sites list (latest)
    url = "https://tranco-list.eu/top-1m.csv.zip"
    
    try:
        # Download the ZIP file
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        print(f"Downloaded {len(response.content)} bytes")
        
        # Extract CSV from ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Get the first CSV file in the archive
            csv_filename = [name for name in z.namelist() if name.endswith('.csv')][0]
            
            with z.open(csv_filename) as csv_file:
                # Read CSV (format: rank,domain)
                df = pd.read_csv(csv_file, names=['rank', 'domain'])
        
        print(f"Found {len(df)} total domains")
        
        # Take top N domains and convert to URLs
        df = df.head(num_urls)
        
        # Create URLs with https prefix
        urls = []
        for _, row in df.iterrows():
            domain = row['domain']
            urls.append({
                'url': f"https://{domain}",
                'label': 0,  # 0 = legitimate
                'rank': row['rank'],
                'domain': domain
            })
        
        # Create DataFrame
        legit_df = pd.DataFrame(urls)
        
        # Save to CSV
        output_file = 'legit_urls.csv'
        legit_df.to_csv(output_file, index=False)
        
        print(f"✅ Saved {len(legit_df)} legitimate URLs to {output_file}")
        print(f"Sample URLs:")
        print(legit_df.head())
        
        return legit_df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    df = fetch_tranco_data(10000)  # Fetch top 10,000 domains
    if df is not None:
        print("\n📊 Dataset info:")
        print(f"Total legitimate URLs: {len(df)}")
        print(f"Columns: {list(df.columns)}")