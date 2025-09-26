import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import joblib
import json

def load_trained_model():
    """
    Load the trained LSTM model and preprocessing scaler
    """
    try:
        # Load the trained model
        model = keras.models.load_model('phishing_lstm_model.h5')
        print("✅ Model loaded successfully!")
        
        # Load the scaler
        scaler = joblib.load('feature_scaler.pkl')
        print("✅ Scaler loaded successfully!")
        
        # Load model report (optional)
        try:
            with open('model_report.json', 'r') as f:
                report = json.load(f)
            print("✅ Model report loaded successfully!")
            print(f"📊 Model Performance:")
            print(f"   - Accuracy: {report['model_performance']['test_accuracy']:.4f}")
            print(f"   - Precision: {report['model_performance']['test_precision']:.4f}")
            print(f"   - Recall: {report['model_performance']['test_recall']:.4f}")
            print(f"   - ROC AUC: {report['model_performance']['roc_auc']:.4f}")
        except:
            print("⚠️ Model report not found, but model works fine")
        
        return model, scaler
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None, None

def predict_phishing(url_features, model, scaler):
    """
    Predict if a URL is phishing based on behavioral features
    
    Args:
        url_features: List or array of behavioral features
        model: Trained LSTM model
        scaler: Fitted StandardScaler
    
    Returns:
        probability of being phishing (0-1)
    """
    try:
        # Ensure features are in the right format
        features = np.array(url_features).reshape(1, -1)
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Reshape for LSTM (samples, timesteps, features)
        features_lstm = features_scaled.reshape(1, 1, -1)
        
        # Make prediction
        prediction = model.predict(features_lstm, verbose=0)[0][0]
        
        return prediction
        
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        return None

def test_with_existing_data():
    """
    Test the model with existing dataset
    """
    print("\n🧪 Testing model with existing data...")
    
    # Load existing dataset
    df = pd.read_csv('events_dataset.csv')
    print(f"📊 Loaded {len(df)} samples from existing dataset")
    
    # Prepare features (same as in training)
    feature_columns = [col for col in df.columns if col not in ['url', 'label']]
    X_test = df[feature_columns]
    y_true = df['label']
    
    print(f"🎯 Features: {len(feature_columns)}")
    
    # Load model and scaler
    model, scaler = load_trained_model()
    
    if model is None or scaler is None:
        return
    
    # Make predictions on a few samples
    print(f"\n🔍 Testing on first 10 samples:")
    
    for i in range(min(10, len(df))):
        url = df.iloc[i]['url']
        features = X_test.iloc[i].values
        true_label = y_true.iloc[i]
        
        # Make prediction
        prediction = predict_phishing(features, model, scaler)
        
        if prediction is not None:
            predicted_label = 1 if prediction > 0.5 else 0
            confidence = prediction if predicted_label == 1 else (1 - prediction)
            
            print(f"\n{i+1}. URL: {url[:60]}...")
            print(f"   True Label: {'Phishing' if true_label == 1 else 'Legitimate'}")
            print(f"   Predicted: {'Phishing' if predicted_label == 1 else 'Legitimate'}")
            print(f"   Confidence: {confidence:.4f}")
            print(f"   ✅ Correct" if predicted_label == true_label else "❌ Incorrect")

def test_manual_input():
    """
    Test with manual feature input
    """
    print("\n🔧 Manual feature testing...")
    
    # Load model and scaler
    model, scaler = load_trained_model()
    
    if model is None or scaler is None:
        return
    
    # Example features for testing (24 features to match dataset)
    # Features: success, num_events, ssl_valid, ssl_invalid, redirects, forms, password_fields, 
    # iframes, scripts, suspicious_keywords, external_requests, page_load_time, has_errors,
    # count_ssl_invalid, count_webdriver_error, count_ssl_valid, count_redirects, 
    # count_external_requests, count_forms_detected, count_password_fields, 
    # count_iframes_detected, count_scripts_detected, count_suspicious_keywords, count_page_load_time
    test_cases = [
        {
            'name': 'Suspicious phishing-like features',
            'features': [0, 1, 0, 1, 1, 1, 1, 3, 2, 1, 0, 5000, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1],  # 24 features
            'expected': 'Phishing'
        },
        {
            'name': 'Legitimate-like features', 
            'features': [1, 9, 1, 0, 1, 2, 0, 15, 25, 0, 0, 2000, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # 24 features
            'expected': 'Legitimate'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Test Case: {test_case['name']}")
        
        prediction = predict_phishing(test_case['features'], model, scaler)
        
        if prediction is not None:
            predicted_label = 'Phishing' if prediction > 0.5 else 'Legitimate'
            confidence = prediction if prediction > 0.5 else (1 - prediction)
            
            print(f"   Expected: {test_case['expected']}")
            print(f"   Predicted: {predicted_label}")
            print(f"   Confidence: {confidence:.4f}")
            print(f"   Raw Score: {prediction:.4f}")

def main():
    """
    Main testing function
    """
    print("🧪 LSTM Phishing Detection Model - Testing Suite")
    print("=" * 50)
    
    # Test with existing data
    test_with_existing_data()
    
    # Manual testing
    test_manual_input()
    
    print(f"\n✅ Testing completed!")

if __name__ == "__main__":
    main()