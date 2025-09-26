#!/usr/bin/env python3
"""
Test script for fixed Flask API endpoints
"""
import requests
import json
import time

def test_fixed_endpoints():
    """Test the Flask backend endpoints after fixes"""
    base_url = 'http://127.0.0.1:5000'
    
    print("🔧 Testing Fixed Flask Backend API Endpoints")
    print("=" * 55)
    
    # Test health endpoint
    print("1️⃣ Testing Fixed Health Endpoint...")
    try:
        response = requests.get(f'{base_url}/health', timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ANN Available: {health_data.get('ann_available')}")
            print(f"   LSTM Available: {health_data.get('lstm_available')}")
            print(f"   Database Status: {health_data.get('database_status')}")
            if 'lstm_details' in health_data:
                lstm_status = health_data['lstm_details'].get('status')
                print(f"   LSTM Health: {lstm_status}")
        print()
    except Exception as e:
        print(f"   ❌ Health check failed: {str(e)}")
        return
    
    # Test URLs
    test_urls = [
        'http://paypal-security-update.fake-domain.com/login',
        'https://google.com'
    ]
    
    print("2️⃣ Testing Fixed LSTM Endpoint...")
    for i, test_url in enumerate(test_urls, 1):
        print(f"   Test {i}: {test_url}")
        try:
            test_data = {'url': test_url}
            response = requests.post(f'{base_url}/predict_lstm', 
                                   json=test_data, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                prediction = result.get('prediction', 'unknown')
                probability = result.get('probability', 0.0)
                processing_time = result.get('processing_time_ms', 0)
                
                print(f"     ✅ Prediction: {prediction}")
                print(f"     📊 Probability: {probability:.4f}")
                print(f"     ⚡ Processing Time: {processing_time}ms")
                
                if 'error' in result:
                    print(f"     ⚠️  Error: {result['error']}")
            else:
                print(f"     ❌ Error {response.status_code}: {response.text[:150]}")
            print()
        except Exception as e:
            print(f"     ❌ Request failed: {str(e)}")
            print()
    
    print("3️⃣ Testing Fixed Both Models Endpoint...")
    test_url = test_urls[0]  # Use suspicious URL
    print(f"   Testing: {test_url}")
    try:
        test_data = {'url': test_url}
        response = requests.post(f'{base_url}/predict_both', 
                               json=test_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=25)
        
        if response.status_code == 200:
            result = response.json()
            print('   ✅ Both Models Response:')
            
            # ANN Results
            ann_result = result.get('ann_prediction', {})
            if ann_result and 'error' not in ann_result:
                print(f"   🧠 ANN: {ann_result.get('prediction')} ({ann_result.get('probability', 0):.4f})")
            else:
                error_msg = ann_result.get('error', 'Unknown error') if ann_result else 'No result'
                print(f"   🧠 ANN: Error - {error_msg}")
            
            # LSTM Results  
            lstm_result = result.get('lstm_prediction', {})
            if lstm_result and 'error' not in lstm_result:
                print(f"   🔍 LSTM: {lstm_result.get('prediction')} ({lstm_result.get('probability', 0):.4f})")
            else:
                error_msg = lstm_result.get('error', 'Unknown error') if lstm_result else 'No result'
                print(f"   🔍 LSTM: Error - {error_msg}")
            
            # Consensus
            consensus = result.get('consensus', {})
            if consensus:
                print(f"   🎯 Consensus: {consensus.get('final_prediction')}")
                print(f"   📊 Confidence: {consensus.get('confidence_level')}")
                print(f"   🤝 Agreement: {consensus.get('agreement', False)}")
                if 'reason' in consensus:
                    print(f"   💭 Reason: {consensus['reason']}")
            
        else:
            print(f"   ❌ Error {response.status_code}: {response.text[:150]}")
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
    
    print()
    print("🎉 Fixed API Testing Complete!")

if __name__ == "__main__":
    test_fixed_endpoints()