"""
Model Compatibility Fixer
Loads and re-saves the LSTM model with current TensorFlow version
"""

import tensorflow as tf
import joblib
import numpy as np

def fix_model_compatibility():
    try:
        print("🔧 Attempting to load and fix model compatibility...")
        
        # Try to load the original model with different approaches
        model_paths = [
            'basic_lstm_model_best.h5',
            'phishing_lstm_model (1).h5'
        ]
        
        model = None
        for path in model_paths:
            try:
                print(f"Trying to load: {path}")
                # Try with compile=False to bypass compilation issues
                model = tf.keras.models.load_model(path, compile=False)
                print(f"✅ Loaded {path} successfully!")
                break
            except Exception as e:
                print(f"❌ Failed to load {path}: {e}")
        
        if model is None:
            print("❌ Could not load any model")
            return False
        
        print(f"Model input shape: {model.input_shape}")
        print(f"Model output shape: {model.output_shape}")
        
        # Re-compile the model with current TensorFlow
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Save the fixed model
        fixed_path = 'Scamify-main/Extension/backend/models/lstm_model_fixed.h5'
        model.save(fixed_path)
        print(f"✅ Fixed model saved to: {fixed_path}")
        
        # Test the fixed model
        test_model = tf.keras.models.load_model(fixed_path)
        print("✅ Fixed model loads successfully!")
        
        # Test with dummy data
        dummy_input = np.random.random((1, 1, 24))  # batch_size=1, timesteps=1, features=24
        prediction = test_model.predict(dummy_input, verbose=0)
        print(f"✅ Test prediction: {prediction[0][0]:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model fixing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_model_compatibility()
    if success:
        print("\n🎉 Model compatibility fixed!")
        print("You can now use 'lstm_model_fixed.h5' in your backend.")
    else:
        print("\n❌ Model fixing failed. We may need to retrain or use a different approach.")