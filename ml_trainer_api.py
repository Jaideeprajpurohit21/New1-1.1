#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
ML Model Training API

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from pathlib import Path
import json

from ml_category_predictor import MLCategoryPredictor

# Setup logging
logger = logging.getLogger(__name__)

# Create API router
ml_router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

# Global ML predictor instance
ml_predictor = MLCategoryPredictor()

@ml_router.post("/train")
async def train_model(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Train the ML category prediction model using synthetic dataset
    """
    try:
        # Run training in background to avoid timeout
        background_tasks.add_task(train_model_background)
        
        return {
            'success': True,
            'message': 'Model training started in background',
            'status': 'training'
        }
        
    except Exception as e:
        logger.error(f"Error starting model training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")

def train_model_background():
    """Background task to train the ML model"""
    try:
        logger.info("Starting background ML model training...")
        
        results = ml_predictor.train_model()
        
        logger.info(f"Model training completed successfully! Accuracy: {results['test_accuracy']:.3f}")
        
        # Save training results
        results_path = Path("/app/models/training_results.json")
        with open(results_path, 'w') as f:
            # Convert numpy types to standard Python types for JSON serialization
            serializable_results = {}
            for key, value in results.items():
                if key == 'categories':
                    serializable_results[key] = [str(cat) for cat in value]
                elif key == 'top_features':
                    serializable_results[key] = [[str(feat), float(imp)] for feat, imp in value]
                elif isinstance(value, (float, int, str, bool, list, dict)):
                    serializable_results[key] = value
                else:
                    serializable_results[key] = str(value)
            
            json.dump(serializable_results, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error in background training: {str(e)}")

@ml_router.get("/status")
async def get_model_status() -> Dict[str, Any]:
    """
    Get current ML model status and performance metrics
    """
    try:
        # Check if model is trained
        is_trained = ml_predictor.is_trained
        
        # Get training results if available
        results_path = Path("/app/models/training_results.json")
        training_results = None
        
        if results_path.exists():
            try:
                with open(results_path, 'r') as f:
                    training_results = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load training results: {str(e)}")
        
        # Get model file info
        model_path = Path("/app/models/category_predictor.pkl")
        model_exists = model_path.exists()
        model_size = model_path.stat().st_size if model_exists else 0
        
        status = {
            'is_trained': is_trained,
            'model_exists': model_exists,
            'model_size_mb': round(model_size / 1024 / 1024, 2),
            'categories': list(ml_predictor.label_encoder.classes_) if ml_predictor.label_encoder else [],
            'feature_count': len(ml_predictor.feature_names) if ml_predictor.feature_names else 0,
            'training_results': training_results
        }
        
        return {
            'success': True,
            'status': status
        }
        
    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@ml_router.post("/predict")
async def predict_category(
    raw_text: str,
    amount: float = None,
    merchant: str = None,
    date_str: str = None
) -> Dict[str, Any]:
    """
    Predict category for a single transaction using ML model
    """
    try:
        if not ml_predictor.is_trained:
            raise HTTPException(status_code=400, detail="Model not trained yet")
        
        result = ml_predictor.predict_category(
            raw_text=raw_text,
            amount=amount,
            merchant=merchant,
            date_str=date_str
        )
        
        return {
            'success': True,
            'prediction': result
        }
        
    except Exception as e:
        logger.error(f"Error in ML prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@ml_router.get("/health")
async def ml_health_check() -> Dict[str, Any]:
    """
    Health check for ML system
    """
    try:
        health_status = {
            'ml_available': ml_predictor is not None,
            'model_loaded': ml_predictor.is_trained if ml_predictor else False,
            'components': {
                'random_forest': ml_predictor.rf_model is not None if ml_predictor else False,
                'tfidf_vectorizer': ml_predictor.tfidf_vectorizer is not None if ml_predictor else False,
                'scaler': ml_predictor.scaler is not None if ml_predictor else False,
                'label_encoder': ml_predictor.label_encoder is not None if ml_predictor else False
            } if ml_predictor else {}
        }
        
        return {
            'success': True,
            'health': health_status
        }
        
    except Exception as e:
        logger.error(f"Error in ML health check: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

# Export the router
__all__ = ['ml_router']