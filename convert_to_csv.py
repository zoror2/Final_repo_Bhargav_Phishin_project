import json
import pandas as pd
from collections import defaultdict

def convert_events_to_csv(json_file="events_dataset.json", csv_file="events_dataset.csv"):
    """
    Convert events JSON to a CSV format for easier analysis
    """
    print(f"Loading {json_file}...")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} URLs in dataset")
    
    # Prepare rows for CSV
    rows = []
    
    for entry in data:
        url = entry['url']
        label = entry['label']
        success = entry['success']
        events = entry['events']
        
        # Initialize row with basic info
        row = {
            'url': url,
            'label': label,
            'success': success,
            'num_events': len(events)
        }
        
        # Extract event counts and features
        event_counts = defaultdict(int)
        ssl_valid = 0
        ssl_invalid = 0
        redirects = 0
        forms = 0
        password_fields = 0
        iframes = 0
        scripts = 0
        suspicious_keywords = 0
        external_requests = 0
        page_load_time = 0
        has_errors = 0
        
        for event in events:
            event_type = event['event_type']
            event_counts[event_type] += 1
            
            # Extract specific metrics
            if event_type == 'ssl_valid':
                ssl_valid = 1
            elif event_type == 'ssl_invalid':
                ssl_invalid = 1
            elif event_type == 'redirects':
                redirects = event.get('count', 0)
            elif event_type == 'forms_detected':
                forms = event.get('count', 0)
            elif event_type == 'password_fields':
                password_fields = event.get('count', 0)
            elif event_type == 'iframes_detected':
                iframes = event.get('count', 0)
            elif event_type == 'scripts_detected':
                scripts = event.get('count', 0)
            elif event_type == 'suspicious_keywords':
                suspicious_keywords = event.get('count', 0)
            elif event_type == 'external_requests':
                external_requests = event.get('count', 0)
            elif event_type == 'page_load_time':
                page_load_time = event.get('duration_ms', 0)
            elif 'error' in event_type:
                has_errors = 1
        
        # Add extracted features to row
        row.update({
            'ssl_valid': ssl_valid,
            'ssl_invalid': ssl_invalid,
            'redirects': redirects,
            'forms': forms,
            'password_fields': password_fields,
            'iframes': iframes,
            'scripts': scripts,
            'suspicious_keywords': suspicious_keywords,
            'external_requests': external_requests,
            'page_load_time': page_load_time,
            'has_errors': has_errors
        })
        
        # Add event type counts
        for event_type, count in event_counts.items():
            row[f'count_{event_type}'] = count
        
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Fill NaN values with 0
    df = df.fillna(0)
    
    # Save to CSV
    df.to_csv(csv_file, index=False)
    
    print(f"✅ Converted to {csv_file}")
    print(f"📊 Shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    
    # Show summary statistics
    print(f"\n📈 Summary Statistics:")
    print(f"Label distribution:")
    print(df['label'].value_counts())
    print(f"\nSuccess rate:")
    print(df['success'].value_counts())
    print(f"\nSample data:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    # Convert the full dataset collected overnight
    df = convert_events_to_csv(
        json_file="events_dataset_full.json",
        csv_file="events_dataset_full.csv"
    )
    print("\n✅ CSV conversion complete!")
    
    # Additional analysis for class imbalance
    print(f"\n🔍 DETAILED CLASS BALANCE ANALYSIS:")
    print(f"{'='*50}")
    
    # Overall counts
    total_urls = len(df)
    legit_count = len(df[df['label'] == 0])
    phishing_count = len(df[df['label'] == 1])
    
    print(f"Total URLs processed: {total_urls}")
    print(f"Legitimate URLs (label=0): {legit_count}")
    print(f"Phishing URLs (label=1): {phishing_count}")
    print(f"Class ratio (Legit:Phishing): {legit_count}:{phishing_count}")
    
    # Success rates by class
    legit_success = len(df[(df['label'] == 0) & (df['success'] == True)])
    phishing_success = len(df[(df['label'] == 1) & (df['success'] == True)])
    
    print(f"\n📊 SUCCESS RATES:")
    print(f"Legitimate URLs successfully processed: {legit_success}/{legit_count} ({legit_success/legit_count*100:.1f}%)")
    print(f"Phishing URLs successfully processed: {phishing_success}/{phishing_count} ({phishing_success/phishing_count*100:.1f}%)")
    
    # Error analysis
    legit_errors = len(df[(df['label'] == 0) & (df['success'] == False)])
    phishing_errors = len(df[(df['label'] == 1) & (df['success'] == False)])
    
    print(f"\n⚠️  ERROR ANALYSIS:")
    print(f"Legitimate URLs with errors: {legit_errors}/{legit_count} ({legit_errors/legit_count*100:.1f}%)")
    print(f"Phishing URLs with errors: {phishing_errors}/{phishing_count} ({phishing_errors/phishing_count*100:.1f}%)")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if abs(legit_count - phishing_count) / total_urls > 0.1:  # >10% imbalance
        print("⚠️  Class imbalance detected!")
        if legit_count > phishing_count:
            print(f"   - Consider downsampling legitimate URLs to {phishing_count}")
            print(f"   - Or use class weighting in training")
        else:
            print(f"   - Consider downsampling phishing URLs to {legit_count}")
            print(f"   - Or use class weighting in training")
    else:
        print("✅ Class balance looks good!")
    
    if (legit_errors + phishing_errors) / total_urls > 0.5:  # >50% errors
        print("⚠️  High error rate detected!")
        print("   - Errors are actually useful features for phishing detection")
        print("   - Many phishing sites are intentionally broken/suspicious")
    else:
        print("✅ Error rate acceptable for training!")