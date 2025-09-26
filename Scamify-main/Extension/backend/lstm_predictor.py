"""
LSTM Prediction Service for Phishing Detection
Integrates LSTM model with feature extraction for real-time phishing detection
"""

import os
import numpy as np
try:
    # Try different TensorFlow import methods for compatibility
    import tensorflow as tf
    try:
        # TensorFlow 2.16+
        import keras  
        print(f"✅ TensorFlow {tf.__version__} with standalone Keras loaded")
        TF_AVAILABLE = True
    except ImportError:
        try:
            # TensorFlow 2.15 and below
            from tensorflow import keras
            print(f"✅ TensorFlow {tf.__version__} with tf.keras loaded")
            TF_AVAILABLE = True
        except ImportError:
            print("❌ Keras not available in TensorFlow")
            TF_AVAILABLE = False
            keras = None
except ImportError as e:
    print(f"❌ TensorFlow not available: {e}")
    TF_AVAILABLE = False
    tf = None
    keras = None

import joblib
import logging
from typing import Dict, List, Tuple, Optional
from lstm_feature_extractor import LSTMFeatureExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LSTMPhishingPredictor:
    def __init__(self, model_path: str = None, scaler_path: str = None):
        """
        Initialize LSTM Phishing Predictor
        
        Args:
            model_path (str): Path to the LSTM model file
            scaler_path (str): Path to the feature scaler file
        """
        # Set default paths
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models', 'basic_lstm_model_best.h5')
        self.scaler_path = scaler_path or os.path.join(os.path.dirname(__file__), 'models', 'feature_scaler.pkl')
        
        # Initialize components
        self.model = None
        self.scaler = None
        self.feature_extractor = LSTMFeatureExtractor(headless=True)
        self.is_loaded = False
        
        # Load model and scaler
        self._load_model_and_scaler()
    
    def _load_model_and_scaler(self):
        """Load the LSTM model and feature scaler"""
        try:
            # Check if TensorFlow is available
            if not TF_AVAILABLE:
                logger.error("TensorFlow not available, cannot load LSTM model")
                return
                
            # Load LSTM model
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                logger.info(f"LSTM model loaded from: {self.model_path}")
            else:
                logger.error(f"LSTM model not found at: {self.model_path}")
                return
            
            # Load feature scaler
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"Feature scaler loaded from: {self.scaler_path}")
            else:
                logger.error(f"Feature scaler not found at: {self.scaler_path}")
                return
            
            self.is_loaded = True
            logger.info("LSTM Phishing Predictor initialized successfully")
            
            # Print model info
            logger.info(f"Model input shape: {self.model.input_shape}")
            logger.info(f"Model output shape: {self.model.output_shape}")
            
        except Exception as e:
            logger.error(f"Failed to load LSTM model or scaler: {e}")
            self.is_loaded = False
    
    def predict_url(self, url: str, return_features: bool = False) -> Dict:
        """
        Predict if a URL is phishing or legitimate
        
        Args:
            url (str): URL to analyze
            return_features (bool): Whether to return extracted features
            
        Returns:
            Dict: Prediction results
        """
        if not self.is_loaded:
            return {
                'error': 'LSTM model not loaded properly',
                'prediction': 'unknown',
                'probability': 0.5,
                'confidence': 'low'
            }
        
        try:
            logger.info(f"Predicting URL: {url}")
            
            # Extract features
            features, metadata = self.feature_extractor.extract_features(url)
            
            # Validate features
            if len(features) != 24:  # Expecting 24 features (25th is excluded - likely 'has_errors')
                logger.error(f"Invalid feature count: {len(features)}, expected 24")
                return {
                    'error': f'Invalid feature count: {len(features)}',
                    'prediction': 'unknown',
                    'probability': 0.5,
                    'confidence': 'low'
                }
            
            # Prepare features for prediction
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            features_scaled = self.scaler.transform(features_array)
            
            # Reshape for LSTM (samples, timesteps, features)
            features_lstm = features_scaled.reshape(features_scaled.shape[0], 1, features_scaled.shape[1])
            
            # Make prediction
            prediction_prob = self.model.predict(features_lstm, verbose=0)[0][0]
            
            # Convert to classification
            prediction = 'phishing' if prediction_prob > 0.5 else 'legitimate'
            confidence = self._get_confidence_level(prediction_prob)
            
            result = {
                'url': url,
                'prediction': prediction,
                'probability': float(prediction_prob),
                'confidence': confidence,
                'model': 'LSTM',
                'processing_time': metadata.get('processing_time', 0)
            }
            
            # Add features if requested
            if return_features:
                result['features'] = {
                    'raw_features': features,
                    'feature_count': len(features),
                    'metadata': metadata
                }
            
            logger.info(f"Prediction completed: {prediction} ({prediction_prob:.4f})")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'error': str(e),
                'prediction': 'unknown',
                'probability': 0.5,
                'confidence': 'low',
                'url': url
            }
    
    def _get_confidence_level(self, probability: float) -> str:
        """
        Determine confidence level based on probability
        
        Args:
            probability (float): Prediction probability
            
        Returns:
            str: Confidence level
        """
        # Calculate distance from 0.5 (uncertainty)
        confidence_score = abs(probability - 0.5) * 2
        
        if confidence_score >= 0.8:
            return 'very_high'
        elif confidence_score >= 0.6:
            return 'high'
        elif confidence_score >= 0.4:
            return 'medium'
        elif confidence_score >= 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def batch_predict(self, urls: List[str]) -> List[Dict]:
        """
        Predict multiple URLs
        
        Args:
            urls (List[str]): List of URLs to analyze
            
        Returns:
            List[Dict]: List of prediction results
        """
        results = []
        for url in urls:
            result = self.predict_url(url)
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model
        
        Returns:
            Dict: Model information
        """
        if not self.is_loaded:
            return {'error': 'Model not loaded'}
        
        try:
            return {
                'model_path': self.model_path,
                'scaler_path': self.scaler_path,
                'input_shape': str(self.model.input_shape),
                'output_shape': str(self.model.output_shape),
                'total_params': self.model.count_params(),
                'is_loaded': self.is_loaded,
                'model_type': 'LSTM',
                'expected_features': 24
            }
        except Exception as e:
            return {'error': str(e)}
    
    def health_check(self) -> Dict:
        """
        Perform a health check on the predictor
        
        Returns:
            Dict: Health check results
        """
        try:
            # Check if model and scaler are loaded
            if not self.is_loaded:
                return {
                    'status': 'unhealthy',
                    'message': 'Model or scaler not loaded',
                    'model_loaded': self.model is not None,
                    'scaler_loaded': self.scaler is not None
                }
            
            # Test with a dummy feature vector
            dummy_features = np.zeros((1, 1, 24))  # 24 features reshaped for LSTM
            test_prediction = self.model.predict(dummy_features, verbose=0)
            
            return {
                'status': 'healthy',
                'message': 'All components loaded and working',
                'model_loaded': True,
                'scaler_loaded': True,
                'test_prediction': float(test_prediction[0][0])
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {str(e)}',
                'model_loaded': self.model is not None,
                'scaler_loaded': self.scaler is not None
            }

# Global predictor instance
_predictor_instance = None

def get_predictor() -> LSTMPhishingPredictor:
    """
    Get the global predictor instance (singleton pattern)
    
    Returns:
        LSTMPhishingPredictor: Global predictor instance
    """
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = LSTMPhishingPredictor()
    return _predictor_instance

# Convenience functions
def predict_phishing(url: str, return_features: bool = False) -> Dict:
    """
    Convenience function for single URL prediction
    
    Args:
        url (str): URL to analyze
        return_features (bool): Whether to return extracted features
        
    Returns:
        Dict: Prediction results
    """
    predictor = get_predictor()
    return predictor.predict_url(url, return_features)

def batch_predict_phishing(urls: List[str]) -> List[Dict]:
    """
    Convenience function for batch URL prediction
    
    Args:
        urls (List[str]): List of URLs to analyze
        
    Returns:
        List[Dict]: List of prediction results
    """
    predictor = get_predictor()
    return predictor.batch_predict(urls)

if __name__ == "__main__":
    # Test the predictor
    test_urls = [
        "https://www.google.com",
        "https://www.github.com",
        "http://suspicious-phishing-site.com"
    ]
    
    print("Testing LSTM Phishing Predictor...")
    predictor = LSTMPhishingPredictor()
    
    # Health check
    health = predictor.health_check()
    print(f"Health check: {health}")
    
    # Test predictions
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = predictor.predict_url(url)
        print(f"Result: {result}")