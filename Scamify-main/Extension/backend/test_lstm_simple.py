"""
Simple LSTM Test - Without Selenium
Tests LSTM model loading and prediction with dummy features
"""

import os
import sys
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    from lstm_predictor import LSTMPhishingPredictor
    
    def test_lstm_model():
        print("🧪 Testing LSTM Model Loading...")
        
        # Initialize predictor
        predictor = LSTMPhishingPredictor()
        
        # Check if loaded
        print(f"Model loaded: {predictor.is_loaded}")
        
        if not predictor.is_loaded:
            print("❌ LSTM model failed to load")
            health = predictor.health_check()
            print(f"Health check: {health}")
            return
        
        print("✅ LSTM model loaded successfully!")
        
        # Test with dummy features (24 features)
        print("\n🔍 Testing prediction with dummy features...")
        
        # Create dummy feature vector that matches training data format
        dummy_features = [
            1,      # success
            8,      # num_events  
            1,      # ssl_valid
            0,      # ssl_invalid
            0,      # redirects
            1,      # forms
            0,      # password_fields
            2,      # iframes
            5,      # scripts
            0,      # suspicious_keywords
            3,      # external_requests
            1500,   # page_load_time
            0,      # has_errors
            0.0,    # count_ssl_invalid
            0.0,    # count_webdriver_error
            1.0,    # count_ssl_valid
            0.0,    # count_redirects
            1.0,    # count_external_requests
            1.0,    # count_forms_detected
            0.0,    # count_password_fields
            1.0,    # count_iframes_detected
            1.0,    # count_scripts_detected
            0.0,    # count_suspicious_keywords
            1.0     # count_page_load_time
        ]
        
        print(f"Feature vector length: {len(dummy_features)}")
        
        # Test direct prediction
        try:
            # Prepare features exactly like in training
            features_array = np.array(dummy_features).reshape(1, -1)
            print(f"Features array shape: {features_array.shape}")
            
            # Scale features
            features_scaled = predictor.scaler.transform(features_array)
            print(f"Scaled features shape: {features_scaled.shape}")
            
            # Reshape for LSTM (samples, timesteps, features)
            features_lstm = features_scaled.reshape(features_scaled.shape[0], 1, features_scaled.shape[1])
            print(f"LSTM input shape: {features_lstm.shape}")
            
            # Make prediction
            prediction_prob = predictor.model.predict(features_lstm, verbose=0)[0][0]
            
            # Convert to classification
            prediction = 'phishing' if prediction_prob > 0.5 else 'legitimate'
            
            print(f"✅ Prediction: {prediction}")
            print(f"✅ Probability: {prediction_prob:.4f}")
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}")
            import traceback
            traceback.print_exc()
    
    if __name__ == "__main__":
        test_lstm_model()
        
except Exception as e:
    print(f"❌ Failed to import or test: {e}")
    import traceback
    traceback.print_exc()