#!/usr/bin/env python3
"""
Comprehensive Testing Script for Both LSTM Models
Tests basic_lstm_model_best.h5 vs phishing_lstm_model (1).h5
"""

import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve, f1_score, accuracy_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings
warnings.filterwarnings('ignore')

print("🚀 COMPREHENSIVE LSTM MODEL TESTING")
print("="*60)

# Load dataset
print("\n📊 Loading dataset...")
try:
    df = pd.read_csv('events_dataset_full.csv')
    print(f"✅ Dataset loaded: {df.shape}")
except Exception as e:
    print(f"❌ Failed to load dataset: {e}")
    exit(1)

# Preprocess data (same as notebook)
print("\n🧹 Preprocessing data...")
df_clean = df.copy()

# Remove URL column
if 'url' in df_clean.columns:
    df_clean = df_clean.drop('url', axis=1)

# Fill missing values
df_clean = df_clean.fillna(0)

# Convert success to int if exists
if 'success' in df_clean.columns:
    df_clean['success'] = df_clean['success'].astype(int)

# Remove duplicates
df_clean = df_clean.drop_duplicates()

# Separate features and target
feature_columns = [col for col in df_clean.columns if col != 'label']
X = df_clean[feature_columns]
y = df_clean['label']

print(f"✅ Features: {len(feature_columns)}, Samples: {len(X)}")

# Load scaler
print("\n🔧 Loading feature scaler...")
try:
    scaler = joblib.load('feature_scaler (1).pkl')
    print("✅ Scaler loaded successfully")
except Exception as e:
    print(f"❌ Failed to load scaler: {e}")
    exit(1)

# Scale features
X_scaled = scaler.transform(X)
X_lstm = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])

# Split data (same random state for fair comparison)
X_train, X_test, y_train, y_test = train_test_split(
    X_lstm, y, test_size=0.2, random_state=42, stratify=y
)

print(f"✅ Data split: Train {X_train.shape}, Test {X_test.shape}")

# Model testing function
def test_model(model_path, model_name):
    """Test a single model and return metrics"""
    print(f"\n🧪 TESTING {model_name}")
    print("-" * 40)
    
    try:
        # Load model
        print(f"📦 Loading model from: {model_path}")
        model = tf.keras.models.load_model(model_path)
        print("✅ Model loaded successfully")
        
        # Model summary
        print(f"\n📊 Model Architecture:")
        print(f"   Input shape: {model.input_shape}")
        print(f"   Output shape: {model.output_shape}")
        print(f"   Parameters: {model.count_params():,}")
        
        # Make predictions
        print(f"\n🔮 Making predictions on test set...")
        y_pred_proba = model.predict(X_test, verbose=0)
        y_pred = (y_pred_proba > 0.5).astype(int).flatten()
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Print results
        print(f"\n📈 RESULTS FOR {model_name}:")
        print(f"   Accuracy:  {accuracy:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        print(f"   ROC AUC:   {roc_auc:.4f}")
        
        # Detailed classification report
        print(f"\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, 
                                  target_names=['Legitimate', 'Phishing'],
                                  digits=4))
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n📊 Confusion Matrix:")
        print(f"                Predicted")
        print(f"Actual    Legit  Phishing")
        print(f"Legit     {cm[0,0]:5d}  {cm[0,1]:8d}")
        print(f"Phishing  {cm[1,0]:5d}  {cm[1,1]:8d}")
        
        # Test sample predictions
        print(f"\n🧪 Sample Predictions (first 10):")
        print("Actual → Predicted (Probability)")
        for i in range(min(10, len(y_test))):
            actual = "Phish" if y_test.iloc[i] == 1 else "Legit"
            predicted = "Phish" if y_pred[i] == 1 else "Legit"
            prob = y_pred_proba[i][0]
            print(f"{actual:5s} → {predicted:5s} ({prob:.3f})")
        
        return {
            'name': model_name,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc,
            'predictions': y_pred_proba,
            'model': model
        }
        
    except Exception as e:
        print(f"❌ Error testing {model_name}: {e}")
        return None

# Test both models
print("\n" + "="*60)
print("🎯 TESTING BOTH MODELS")
print("="*60)

# Test Model 1: Best model (saved during training)
model1_results = test_model('basic_lstm_model_best.h5', 'BEST MODEL (Auto-saved)')

# Test Model 2: Final epoch model
model2_results = test_model('phishing_lstm_model (1).h5', 'FINAL EPOCH MODEL')

# Comparison
if model1_results and model2_results:
    print("\n" + "="*60)
    print("🏆 COMPREHENSIVE COMPARISON")
    print("="*60)
    
    print(f"\n📊 METRIC COMPARISON:")
    print(f"{'Metric':<12} {'Best Model':<12} {'Final Model':<12} {'Winner':<10}")
    print("-" * 50)
    
    metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
    winners = {'Best Model': 0, 'Final Model': 0}
    
    for metric in metrics:
        val1 = model1_results[metric]
        val2 = model2_results[metric]
        winner = 'Best Model' if val1 > val2 else 'Final Model' if val2 > val1 else 'Tie'
        if winner != 'Tie':
            winners[winner] += 1
        
        print(f"{metric.capitalize():<12} {val1:<12.4f} {val2:<12.4f} {winner:<10}")
    
    print("-" * 50)
    print(f"Best Model wins: {winners['Best Model']} metrics")
    print(f"Final Model wins: {winners['Final Model']} metrics")
    
    # Overall recommendation
    print(f"\n🎯 RECOMMENDATION:")
    if winners['Best Model'] > winners['Final Model']:
        print("✅ USE 'basic_lstm_model_best.h5'")
        print("   - Better overall performance")
        print("   - Auto-selected during training")
        print("   - Likely prevented overfitting")
    elif winners['Final Model'] > winners['Best Model']:
        print("✅ USE 'phishing_lstm_model (1).h5'") 
        print("   - Better overall performance")
        print("   - Final trained state")
    else:
        print("🤔 BOTH MODELS PERFORM SIMILARLY")
        print("   - Recommend 'basic_lstm_model_best.h5' (safer choice)")
    
    # Create comparison visualization data
    comparison_data = {
        'model_comparison': {
            'best_model': {
                'file': 'basic_lstm_model_best.h5',
                'metrics': {k: float(v) for k, v in model1_results.items() if k in metrics}
            },
            'final_model': {
                'file': 'phishing_lstm_model (1).h5',
                'metrics': {k: float(v) for k, v in model2_results.items() if k in metrics}
            }
        },
        'recommendation': 'basic_lstm_model_best.h5' if winners['Best Model'] >= winners['Final Model'] else 'phishing_lstm_model (1).h5',
        'test_samples': len(y_test),
        'feature_count': len(feature_columns)
    }
    
    # Save comparison results
    with open('model_comparison_results.json', 'w') as f:
        json.dump(comparison_data, f, indent=2)
    print(f"\n💾 Results saved to 'model_comparison_results.json'")

print(f"\n✅ TESTING COMPLETE!")
print("="*60)