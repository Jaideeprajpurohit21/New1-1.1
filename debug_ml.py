#!/usr/bin/env python3
"""
Debug ML Predictor
"""

from ml_category_predictor import MLCategoryPredictor
import traceback

predictor = MLCategoryPredictor()
print(f"Model loaded: {predictor.is_trained}")

try:
    result = predictor.predict_category(
        raw_text="Starbucks Coffee charged $8.45",
        amount=8.45,
        merchant="Starbucks",
        date_str="2024-10-15"
    )
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()