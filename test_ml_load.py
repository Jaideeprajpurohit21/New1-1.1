#!/usr/bin/env python3
"""
Test ML Model Loading
"""

from ml_category_predictor import MLCategoryPredictor

predictor = MLCategoryPredictor()
print(f"Model loaded: {predictor.is_trained}")
print(f"RF Model exists: {predictor.rf_model is not None}")
print(f"TF-IDF exists: {predictor.tfidf_vectorizer is not None}")
print(f"Scaler exists: {predictor.scaler is not None}")
print(f"Label encoder exists: {predictor.label_encoder is not None}")

if predictor.label_encoder:
    print(f"Categories: {predictor.label_encoder.classes_}")

# Try manual load
predictor.load_model()
print(f"\nAfter manual load - Model loaded: {predictor.is_trained}")