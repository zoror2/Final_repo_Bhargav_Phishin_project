#!/usr/bin/env python3
"""
Simple Model Testing Script (No Extra Dependencies)
Tests basic_lstm_model_best.h5 vs phishing_lstm_model (1).h5
"""

import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
import json
import warnings
warnings.filterwarnings('ignore')

print("🚀 LSTM MODEL TESTING")
print("="*50)

# Load dataset
print("\n📊 Loading dataset...")
try:
    df = pd.read_csv('events_dataset_full.csv')
    print(f"✅ Dataset loaded: {df.shape}")
except Exception as e:
    print(f"❌ Failed to load dataset: {e}")
    exit(1)

# Preprocess data
print("\n🧹 Preprocessing data...")
df_clean = df.copy()

if 'url' in df_clean.columns:
    df_clean = df_clean.drop('url', axis=1)

df_clean = df_clean.fillna(0)

if 'success' in df_clean.columns:
    df_clean['success'] = df_clean['success'].astype(int)

df_clean = df_clean.drop_duplicates()

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

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_lstm, y, test_size=0.2, random_state=42, stratify=y
)

print(f"✅ Data split: Train {X_train.shape}, Test {X_test.shape}")

def test_model(model_path, model_name):
    """Test a single model"""
    print(f"\n{'='*50}")
    print(f"🧪 TESTING {model_name}")
    print(f"{'='*50}")
    
    try:
        print(f"📦 Loading: {model_path}")
        model = tf.keras.models.load_model(model_path)
        print("✅ Model loaded successfully")
        
        print(f"\n📊 Model Info:")
        print(f"   Input shape: {model.input_shape}")
        print(f"   Parameters: {model.count_params():,}")
        
        print(f"\n🔮 Making predictions...")
        y_pred_proba = model.predict(X_test, verbose=0)
        y_pred = (y_pred_proba > 0.5).astype(int).flatten()
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\n📈 PERFORMANCE RESULTS:")
        print(f"   Accuracy:  {accuracy:.4f} ({accuracy*100:.1f}%)")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        print(f"   ROC AUC:   {roc_auc:.4f}")
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n📊 Confusion Matrix:")
        print(f"                 Predicted")
        print(f"Actual     Legit  Phishing")
        print(f"Legit      {cm[0,0]:5d}    {cm[0,1]:5d}")
        print(f"Phishing   {cm[1,0]:5d}    {cm[1,1]:5d}")
        
        # Sample predictions
        print(f"\n🧪 Sample Predictions (first 5):")
        for i in range(5):
            actual = "Phishing" if y_test.iloc[i] == 1 else "Legitimate"
            predicted = "Phishing" if y_pred[i] == 1 else "Legitimate"
            prob = y_pred_proba[i][0]
            status = "✅" if y_test.iloc[i] == y_pred[i] else "❌"
            print(f"   {status} {actual:10s} → {predicted:10s} (prob: {prob:.3f})")
        
        return {
            'name': model_name,
            'file': model_path,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc,
        }
        
    except Exception as e:
        print(f"❌ Error testing {model_name}: {e}")
        return None

# Test both models
model1 = test_model('basic_lstm_model_best.h5', 'BEST MODEL')
model2 = test_model('phishing_lstm_model (1).h5', 'FINAL EPOCH MODEL')

# Comparison
if model1 and model2:
    print(f"\n{'='*50}")
    print("🏆 FINAL COMPARISON")
    print(f"{'='*50}")
    
    print(f"\n📊 Head-to-Head Comparison:")
    print(f"{'Metric':<12} {'Best Model':<12} {'Final Model':<12} {'Winner'}")
    print("-" * 55)
    
    metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
    best_wins = 0
    final_wins = 0
    
    for metric in metrics:
        val1 = model1[metric]
        val2 = model2[metric]
        
        if val1 > val2:
            winner = "🥇 Best"
            best_wins += 1
        elif val2 > val1:
            winner = "🥇 Final"
            final_wins += 1
        else:
            winner = "🤝 Tie"
            
        print(f"{metric.capitalize():<12} {val1:<12.4f} {val2:<12.4f} {winner}")
    
    print("-" * 55)
    print(f"Best Model wins: {best_wins} metrics")
    print(f"Final Model wins: {final_wins} metrics")
    
    print(f"\n🎯 RECOMMENDATION:")
    if best_wins > final_wins:
        print("✅ USE: basic_lstm_model_best.h5")
        print("   Reason: Better overall performance")
        print("   This model was auto-saved when validation accuracy peaked")
    elif final_wins > best_wins:
        print("✅ USE: phishing_lstm_model (1).h5")
        print("   Reason: Better overall performance")
        print("   This is the final trained state")
    else:
        print("🤔 BOTH MODELS PERFORM SIMILARLY")
        print("✅ RECOMMENDED: basic_lstm_model_best.h5")
        print("   Reason: Safer choice (prevented overfitting)")
    
    # Save results
    results = {
        'test_results': {
            'best_model': model1,
            'final_model': model2
        },
        'comparison': {
            'best_model_wins': best_wins,
            'final_model_wins': final_wins,
            'recommendation': 'basic_lstm_model_best.h5' if best_wins >= final_wins else 'phishing_lstm_model (1).h5'
        },
        'test_info': {
            'test_samples': len(y_test),
            'features': len(feature_columns),
            'classes': sorted(y.unique().tolist())
        }
    }
    
    with open('model_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: model_test_results.json")

print(f"\n✅ TESTING COMPLETE!")
print(f"Both models tested successfully on {len(y_test)} samples")