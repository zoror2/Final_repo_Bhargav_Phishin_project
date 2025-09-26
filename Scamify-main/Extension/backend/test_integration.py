#!/usr/bin/env python3
"""
ScamiFy Integration Test Script
Tests the complete integration of ANN + LSTM models in the backend
"""

import requests
import json
import time
from typing import List, Dict

# Test configuration
BACKEND_URL = "http://127.0.0.1:5000"
TEST_URLS = [
    "https://www.google.com",
    "https://www.github.com",
    "https://www.microsoft.com",
    "http://suspicious-phishing-test.com",
    "https://secure-bank-login-verify123456.com"
]

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   ANN Model: {'✅' if data['models']['ann']['loaded'] else '❌'}")
            print(f"   LSTM Model: {'✅' if data['models']['lstm']['loaded'] else '❌'}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_ann_prediction(url: str) -> Dict:
    """Test ANN prediction endpoint"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/predict_url",
            json={"url": url},
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def test_lstm_prediction(url: str) -> Dict:
    """Test LSTM prediction endpoint"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/predict_lstm",
            json={"url": url, "return_features": True},
            timeout=30  # LSTM takes longer due to Selenium
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def test_both_predictions(url: str) -> Dict:
    """Test both ANN and LSTM predictions"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/predict_both",
            json={"url": url},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def format_prediction_result(result: Dict, model_type: str) -> str:
    """Format prediction result for display"""
    if "error" in result:
        return f"❌ {model_type} Error: {result['error']}"
    
    prediction = result.get('prediction', 'unknown')
    probability = result.get('probability', 0)
    
    # Choose emoji based on prediction
    if prediction.lower() == 'phishing':
        emoji = '🚨'
    elif prediction.lower() == 'suspicious':
        emoji = '⚠️'
    else:
        emoji = '✅'
    
    return f"{emoji} {model_type}: {prediction} ({probability:.2%})"

def main():
    """Run all tests"""
    print("🚀 Starting ScamiFy Integration Tests")
    print("=" * 60)
    
    # Test 1: Health Check
    if not test_health_check():
        print("❌ Backend is not healthy. Please start the backend first.")
        return
    
    print("\n" + "=" * 60)
    print("🧪 Testing URL Predictions")
    print("=" * 60)
    
    for i, url in enumerate(TEST_URLS, 1):
        print(f"\n📋 Test {i}/5: {url}")
        print("-" * 50)
        
        # Test ANN prediction
        print("🔍 Testing ANN model...")
        ann_result = test_ann_prediction(url)
        print(f"   {format_prediction_result(ann_result, 'ANN')}")
        
        # Test LSTM prediction (with longer timeout)
        print("🧠 Testing LSTM model (this may take 10-30 seconds)...")
        lstm_start = time.time()
        lstm_result = test_lstm_prediction(url)
        lstm_duration = time.time() - lstm_start
        print(f"   {format_prediction_result(lstm_result, 'LSTM')} (took {lstm_duration:.1f}s)")
        
        # Test combined prediction
        print("🤝 Testing combined prediction...")
        both_result = test_both_predictions(url)
        
        if "error" not in both_result and both_result.get('consensus'):
            consensus = both_result['consensus']
            conf_level = consensus.get('confidence', 'unknown')
            print(f"   🎯 Consensus: {consensus['prediction']} (confidence: {conf_level})")
        else:
            print(f"   ❌ Combined prediction failed")
        
        # Add delay between tests to avoid overwhelming the system
        if i < len(TEST_URLS):
            print("   ⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    print("\n" + "=" * 60)
    print("✅ Integration tests completed!")
    print("=" * 60)
    
    print("\n📋 Test Summary:")
    print("- ANN Model: Fast hover detection")
    print("- LSTM Model: Comprehensive behavioral analysis")
    print("- Combined: Best of both models")
    print("\n🎯 Ready for Chrome Extension testing!")

if __name__ == "__main__":
    main()