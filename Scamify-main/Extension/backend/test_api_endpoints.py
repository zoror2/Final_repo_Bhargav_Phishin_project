#!/usr/bin/env python3
"""
Test script for Flask API endpoints
Tests both ANN and LSTM model integration
"""

import requests
import json
import time

def test_flask_api():
    """Test all Flask API endpoints"""
    base_url = 'http://127.0.0.1:5000'
    
    print('🚀 Testing Flask Backend API Endpoints')
    print('=' * 50)
    
    # Test health endpoint
    print('1️⃣ Testing Health Endpoint...')
    try:
        response = requests.get(f'{base_url}/health', timeout=5)
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            health_data = response.json()
            print(f'   ANN Available: {health_data.get("ann_available")}')
            print(f'   LSTM Available: {health_data.get("lstm_available")}')
            print(f'   Database: {health_data.get("database_status")}')
        print()
    except Exception as e:
        print(f'   ❌ Health check failed: {str(e)}')
        print('   Make sure Flask app is running: python app.py')
        return False
    
    # Test data
    test_urls = [
        'http://paypal-security-update.fake-domain.com/login',
        'https://google.com',
        'http://suspicious-bank-login.temporary-site.net/secure'
    ]
    
    print('2️⃣ Testing LSTM Endpoint...')
    for i, test_url in enumerate(test_urls[:2], 1):  # Test first 2 URLs
        print(f'   Test {i}: {test_url}')
        try:
            test_data = {'url': test_url}
            response = requests.post(f'{base_url}/predict_lstm', 
                                   json=test_data, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                print(f'     ✅ Prediction: {result.get("prediction")}')
                print(f'     📊 Probability: {result.get("probability"):.4f}')
                print(f'     ⚡ Processing Time: {result.get("processing_time_ms")}ms')
            else:
                print(f'     ❌ Error {response.status_code}: {response.text[:100]}')
            print()
        except Exception as e:
            print(f'     ❌ Request failed: {str(e)}')
            print()
    
    print('3️⃣ Testing Both Models Endpoint...')
    test_url = test_urls[0]  # Use first suspicious URL
    print(f'   Testing: {test_url}')
    try:
        test_data = {'url': test_url}
        response = requests.post(f'{base_url}/predict_both', 
                               json=test_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            print('   ✅ Both Models Response:')
            
            # ANN Results
            ann_result = result.get('ann_prediction', {})
            print(f'   🧠 ANN: {ann_result.get("prediction")} ({ann_result.get("probability", 0):.4f})')
            
            # LSTM Results  
            lstm_result = result.get('lstm_prediction', {})
            print(f'   🔍 LSTM: {lstm_result.get("prediction")} ({lstm_result.get("probability", 0):.4f})')
            
            # Consensus
            consensus = result.get('consensus', {})
            print(f'   🎯 Consensus: {consensus.get("final_prediction")}')
            print(f'   📊 Confidence: {consensus.get("confidence_level")}')
            
        else:
            print(f'   ❌ Error {response.status_code}: {response.text[:100]}')
    except Exception as e:
        print(f'   ❌ Request failed: {str(e)}')
    
    print()
    print('🎉 API Testing Complete!')
    return True

def test_individual_endpoints():
    """Test individual endpoints with more detailed output"""
    base_url = 'http://127.0.0.1:5000'
    
    print('\n🔬 Detailed Individual Endpoint Testing')
    print('=' * 50)
    
    # Test ANN endpoint
    print('🧠 Testing ANN Endpoint...')
    try:
        test_data = {'url': 'http://paypal-security-update.fake-domain.com/login'}
        response = requests.post(f'{base_url}/predict', 
                               json=test_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f'   ✅ ANN Result: {json.dumps(result, indent=4)}')
        else:
            print(f'   ❌ ANN Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'   ❌ ANN Request failed: {str(e)}')
    
    print()

if __name__ == "__main__":
    print("🧪 Flask API Testing Suite")
    print("=" * 50)
    
    # Run main tests
    success = test_flask_api()
    
    if success:
        # Run detailed tests
        test_individual_endpoints()
    
    print("\n✨ Testing session complete!")