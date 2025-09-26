#!/usr/bin/env python3
"""
Test LSTM feature extraction to ensure it returns exactly 24 features
"""

from lstm_feature_extractor import extract_lstm_features

def test_feature_count():
    """Test that feature extraction returns exactly 24 features"""
    
    print("🧪 Testing LSTM Feature Extraction")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        'http://example.com',
        'https://google.com',
        'http://invalid-url-test.fake'
    ]
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n{i}️⃣ Testing: {test_url}")
        
        try:
            features, metadata = extract_lstm_features(test_url)
            
            print(f"   ✅ Extraction completed")
            print(f"   📊 Feature count: {len(features)}")
            print(f"   🔍 Sample features: {features[:5]}...")
            
            if len(features) == 24:
                print(f"   ✅ PERFECT! Feature count matches LSTM expectation")
            else:
                print(f"   ❌ MISMATCH: got {len(features)}, expected 24")
                print(f"   🔍 All features: {features}")
            
            if 'error' in metadata:
                print(f"   ⚠️  Error in metadata: {metadata['error']}")
            else:
                print(f"   ✅ No errors in metadata")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    print(f"\n🎯 Feature Extraction Test Complete!")

if __name__ == "__main__":
    test_feature_count()