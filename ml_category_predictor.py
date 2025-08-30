#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
ML-Powered Category Prediction System

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
import re

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionFeatureExtractor:
    """Advanced feature extraction for transaction categorization"""
    
    def __init__(self):
        """Initialize feature extractor with predefined patterns and mappings"""
        
        # Merchant patterns for feature extraction
        self.merchant_categories = {
            'coffee_chain': ['starbucks', 'dunkin', 'coffee', 'cafe', 'espresso'],
            'fast_food': ['mcdonald', 'burger king', 'kfc', 'taco bell', 'subway', 'chipotle'],
            'grocery_chain': ['walmart', 'target', 'kroger', 'safeway', 'whole foods', 'costco', 'alfamart'],
            'gas_station': ['shell', 'chevron', 'exxon', 'bp', 'mobil', 'texaco'],
            'pharmacy': ['cvs', 'walgreens', 'pharmacy', 'rite aid'],
            'streaming_service': ['netflix', 'spotify', 'hulu', 'disney', 'amazon prime', 'apple music'],
            'ride_sharing': ['uber', 'lyft', 'taxi', 'rideshare'],
            'hotel_chain': ['marriott', 'hilton', 'hyatt', 'holiday inn', 'airbnb'],
            'airline': ['delta', 'american', 'united', 'southwest', 'jetblue'],
            'telecom': ['verizon', 'at&t', 't-mobile', 'sprint', 'comcast']
        }
        
        # Time-based patterns
        self.time_patterns = {
            'morning_rush': (6, 10),
            'lunch_time': (11, 14), 
            'dinner_time': (17, 21),
            'late_night': (22, 5)
        }
        
        # Amount buckets for feature engineering
        self.amount_buckets = [
            (0, 5, 'micro'),           # $0-5
            (5, 15, 'small'),          # $5-15  
            (15, 50, 'medium_small'),  # $15-50
            (50, 150, 'medium'),       # $50-150
            (150, 500, 'large'),       # $150-500
            (500, float('inf'), 'xlarge') # $500+
        ]
        
        # Subscription pricing patterns
        self.subscription_amounts = [9.99, 14.99, 15.99, 19.99, 29.99, 39.99, 49.99, 99.99]
    
    def extract_features(self, raw_text: str, amount: Optional[float] = None, 
                        merchant: Optional[str] = None, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Extract comprehensive features for ML prediction"""
        
        features = {}
        text_lower = raw_text.lower()
        
        # 1. Amount-based features
        if amount is not None:
            features.update(self._extract_amount_features(amount))
        else:
            features.update(self._get_default_amount_features())
        
        # 2. Merchant-based features
        if merchant:
            features.update(self._extract_merchant_features(merchant.lower()))
        else:
            features.update(self._get_default_merchant_features())
        
        # 3. Time-based features
        features.update(self._extract_time_features(text_lower, date_str))
        
        # 4. Text-based features
        features.update(self._extract_text_features(text_lower))
        
        # 5. Transaction pattern features
        features.update(self._extract_transaction_patterns(text_lower, amount))
        
        # 6. Contextual features
        features.update(self._extract_contextual_features(raw_text))
        
        return features
    
    def _extract_amount_features(self, amount: float) -> Dict[str, Any]:
        """Extract amount-based features"""
        features = {}
        
        # Amount bucket
        for min_amt, max_amt, bucket in self.amount_buckets:
            if min_amt <= amount < max_amt:
                features[f'amount_bucket_{bucket}'] = 1
                features['amount_bucket'] = bucket
                break
        else:
            features['amount_bucket_xlarge'] = 1
            features['amount_bucket'] = 'xlarge'
        
        # Round number detection
        features['is_round_amount'] = 1 if amount == int(amount) else 0
        
        # Subscription pricing pattern
        features['is_subscription_price'] = 1 if any(abs(amount - sub_price) < 0.01 
                                                    for sub_price in self.subscription_amounts) else 0
        
        # Amount statistical features
        features['amount_log'] = np.log(amount + 1)  # Log transform
        features['amount_sqrt'] = np.sqrt(amount)
        
        # Specific amount patterns
        features['is_micro_transaction'] = 1 if amount < 5 else 0
        features['is_large_transaction'] = 1 if amount > 200 else 0
        
        return features
    
    def _get_default_amount_features(self) -> Dict[str, Any]:
        """Default features when amount is not available"""
        features = {}
        for _, _, bucket in self.amount_buckets:
            features[f'amount_bucket_{bucket}'] = 0
        features.update({
            'amount_bucket': 'unknown',
            'is_round_amount': 0,
            'is_subscription_price': 0,
            'amount_log': 0,
            'amount_sqrt': 0,
            'is_micro_transaction': 0,
            'is_large_transaction': 0
        })
        return features
    
    def _extract_merchant_features(self, merchant_lower: str) -> Dict[str, Any]:
        """Extract merchant-based features"""
        features = {}
        
        # Merchant category detection
        merchant_category_found = False
        for category, keywords in self.merchant_categories.items():
            if any(keyword in merchant_lower for keyword in keywords):
                features[f'merchant_category_{category}'] = 1
                features['merchant_category'] = category
                merchant_category_found = True
            else:
                features[f'merchant_category_{category}'] = 0
        
        if not merchant_category_found:
            features['merchant_category'] = 'other'
        
        # Merchant name length and characteristics
        features['merchant_name_length'] = len(merchant_lower)
        features['merchant_has_numbers'] = 1 if re.search(r'\d', merchant_lower) else 0
        features['merchant_word_count'] = len(merchant_lower.split())
        
        return features
    
    def _get_default_merchant_features(self) -> Dict[str, Any]:
        """Default features when merchant is not available"""
        features = {}
        for category in self.merchant_categories.keys():
            features[f'merchant_category_{category}'] = 0
        features.update({
            'merchant_category': 'unknown',
            'merchant_name_length': 0,
            'merchant_has_numbers': 0,
            'merchant_word_count': 0
        })
        return features
    
    def _extract_time_features(self, text_lower: str, date_str: Optional[str]) -> Dict[str, Any]:
        """Extract time-based features"""
        features = {}
        
        # Initialize all time pattern features
        for pattern in self.time_patterns.keys():
            features[f'time_pattern_{pattern}'] = 0
        
        # Extract time from text
        time_match = re.search(r'(\d{1,2}):(\d{2})', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            
            # Determine time pattern
            for pattern, (start, end) in self.time_patterns.items():
                if start <= end:  # Normal time range
                    if start <= hour <= end:
                        features[f'time_pattern_{pattern}'] = 1
                        features['time_pattern'] = pattern
                        break
                else:  # Overnight range (e.g., 22-5)
                    if hour >= start or hour <= end:
                        features[f'time_pattern_{pattern}'] = 1
                        features['time_pattern'] = pattern
                        break
        
        # Date-based features
        if date_str:
            try:
                if isinstance(date_str, str):
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    transaction_date = date_str
                
                features['day_of_week'] = transaction_date.weekday()  # 0=Monday, 6=Sunday
                features['is_weekend'] = 1 if transaction_date.weekday() >= 5 else 0
                features['month'] = transaction_date.month
                features['is_month_start'] = 1 if transaction_date.day <= 5 else 0
                features['is_month_end'] = 1 if transaction_date.day >= 25 else 0
                
            except (ValueError, AttributeError):
                features.update({'day_of_week': 0, 'is_weekend': 0, 'month': 1, 
                               'is_month_start': 0, 'is_month_end': 0})
        else:
            features.update({'day_of_week': 0, 'is_weekend': 0, 'month': 1, 
                           'is_month_start': 0, 'is_month_end': 0})
        
        return features
    
    def _extract_text_features(self, text_lower: str) -> Dict[str, Any]:
        """Extract text-based features using keywords and patterns"""
        features = {}
        
        # Category-specific keywords
        category_keywords = {
            'dining': ['restaurant', 'food', 'cafe', 'delivery', 'takeout', 'menu', 'order', 'eat'],
            'groceries': ['grocery', 'market', 'store', 'supermarket', 'produce', 'organic'],
            'transportation': ['ride', 'fuel', 'gas', 'parking', 'toll', 'uber', 'lyft', 'taxi'],
            'entertainment': ['subscription', 'streaming', 'music', 'video', 'game', 'premium'],
            'utilities': ['bill', 'monthly', 'electric', 'internet', 'phone', 'utility', 'wireless'],
            'healthcare': ['pharmacy', 'prescription', 'medical', 'doctor', 'health', 'rx'],
            'travel': ['hotel', 'flight', 'booking', 'reservation', 'airline', 'airport'],
            'shopping': ['purchase', 'order', 'shopping', 'item', 'product', 'store', 'buy']
        }
        
        # Count keyword matches for each category
        for category, keywords in category_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            features[f'text_keywords_{category}'] = count
            features[f'has_{category}_keywords'] = 1 if count > 0 else 0
        
        # Payment method features
        payment_methods = ['card', 'cash', 'upi', 'credit', 'debit', 'auto-pay', 'autopay']
        for method in payment_methods:
            features[f'payment_method_{method}'] = 1 if method in text_lower else 0
        
        # Transaction type features
        transaction_types = ['purchase', 'payment', 'subscription', 'renewal', 'charge', 'bill']
        for tx_type in transaction_types:
            features[f'transaction_type_{tx_type}'] = 1 if tx_type in text_lower else 0
        
        return features
    
    def _extract_transaction_patterns(self, text_lower: str, amount: Optional[float]) -> Dict[str, Any]:
        """Extract transaction pattern features"""
        features = {}
        
        # Recurring transaction indicators
        recurring_keywords = ['monthly', 'annual', 'subscription', 'renewal', 'auto', 'recurring']
        features['has_recurring_pattern'] = 1 if any(keyword in text_lower for keyword in recurring_keywords) else 0
        
        # Reference number patterns
        features['has_reference_number'] = 1 if re.search(r'(?:ref|id|confirmation|order).*\d{4,}', text_lower) else 0
        
        # Balance/account information
        features['has_balance_info'] = 1 if any(keyword in text_lower for keyword in ['balance', 'bal', 'available']) else 0
        
        # Location indicators
        features['has_location_info'] = 1 if re.search(r'store|location|#\d+|downtown|highway', text_lower) else 0
        
        # Promotional/discount features
        features['has_promotion'] = 1 if any(keyword in text_lower for keyword in ['discount', 'sale', 'promo', 'offer']) else 0
        
        return features
    
    def _extract_contextual_features(self, raw_text: str) -> Dict[str, Any]:
        """Extract contextual features from full transaction text"""
        features = {}
        
        # Text length features
        features['text_length'] = len(raw_text)
        features['word_count'] = len(raw_text.split())
        features['sentence_count'] = len([s for s in raw_text.split('.') if s.strip()])
        
        # Currency features
        currencies = ['USD', 'INR', 'EUR', 'GBP', '$', '₹', '€', '£']
        for currency in currencies:
            features[f'currency_{currency.lower().replace("$", "dollar").replace("₹", "rupee")}'] = 1 if currency in raw_text else 0
        
        # Number of numeric values (excluding amounts)
        numeric_matches = re.findall(r'\b\d+\b', raw_text)
        features['numeric_value_count'] = len(numeric_matches)
        
        return features

class MLCategoryPredictor:
    """Complete ML-based category prediction system"""
    
    def __init__(self, model_path: str = "/app/models/category_predictor.pkl"):
        """Initialize ML category predictor"""
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(exist_ok=True)
        
        self.feature_extractor = TransactionFeatureExtractor()
        self.rf_model = None
        self.tfidf_vectorizer = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.is_trained = False
        
        # Try to load existing model
        self.load_model()
    
    def prepare_training_data(self, dataset_path: str = "/app/synthetic_training_dataset.json") -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from synthetic dataset"""
        
        logger.info(f"Loading training dataset from {dataset_path}")
        
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
        
        logger.info(f"Loaded {len(dataset)} training examples")
        
        # Extract features and labels
        X_features = []
        X_text = []
        y = []
        
        for example in dataset:
            # Extract structured features
            features = self.feature_extractor.extract_features(
                raw_text=example['raw_text'],
                amount=example.get('true_amount'),
                merchant=example.get('key_merchant'),
                date_str=example.get('true_date')
            )
            
            X_features.append(features)
            X_text.append(example['raw_text'])
            y.append(example['true_category'])
        
        # Convert structured features to DataFrame
        features_df = pd.DataFrame(X_features)
        
        # Handle categorical features with one-hot encoding
        categorical_features = ['amount_bucket', 'merchant_category', 'time_pattern']
        
        # Convert categorical columns to strings and then one-hot encode
        for col in categorical_features:
            if col in features_df.columns:
                features_df[col] = features_df[col].astype(str)
        
        # One-hot encode categorical features
        features_encoded = pd.get_dummies(features_df, columns=categorical_features, prefix=categorical_features)
        
        # Initialize TF-IDF vectorizer for text features
        if self.tfidf_vectorizer is None:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
        
        # Fit and transform text data
        X_text_tfidf = self.tfidf_vectorizer.fit_transform(X_text).toarray()
        
        # Get feature names for text features
        tfidf_feature_names = [f'tfidf_{name}' for name in self.tfidf_vectorizer.get_feature_names_out()]
        
        # Combine structured and text features
        X_combined = np.hstack([features_encoded.values, X_text_tfidf])
        
        # Store feature names
        self.feature_names = list(features_encoded.columns) + tfidf_feature_names
        
        # Encode labels
        if self.label_encoder is None:
            self.label_encoder = LabelEncoder()
        
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
        
        X_scaled = self.scaler.fit_transform(X_combined)
        
        logger.info(f"Prepared training data: {X_scaled.shape[0]} samples, {X_scaled.shape[1]} features")
        logger.info(f"Categories: {list(self.label_encoder.classes_)}")
        
        return X_scaled, y_encoded
    
    def train_model(self, dataset_path: str = "/app/synthetic_training_dataset.json") -> Dict[str, Any]:
        """Train Random Forest model on synthetic dataset"""
        
        logger.info("Starting ML model training...")
        
        # Prepare training data
        X, y = self.prepare_training_data(dataset_path)
        
        # Split data for validation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Initialize Random Forest with optimized parameters
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        # Train model
        logger.info("Training Random Forest model...")
        self.rf_model.fit(X_train, y_train)
        
        # Evaluate model
        train_accuracy = self.rf_model.score(X_train, y_train)
        test_accuracy = self.rf_model.score(X_test, y_test)
        
        # Cross-validation (reduce CV folds for small dataset)
        cv_folds = min(3, len(np.unique(y_train)))  # Use fewer folds for small dataset
        cv_scores = cross_val_score(self.rf_model, X_train, y_train, cv=cv_folds)
        
        # Predictions for detailed evaluation
        y_pred = self.rf_model.predict(X_test)
        
        # Get unique classes in test set
        unique_classes = np.unique(np.concatenate([y_test, y_pred]))
        target_names = [self.label_encoder.inverse_transform([i])[0] for i in unique_classes]
        
        # Feature importance
        feature_importance = dict(zip(self.feature_names, self.rf_model.feature_importances_))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:15]
        
        training_results = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'cv_mean_accuracy': cv_scores.mean(),
            'cv_std_accuracy': cv_scores.std(),
            'classification_report': classification_report(
                y_test, y_pred, labels=unique_classes, target_names=target_names, output_dict=True, zero_division=0
            ),
            'top_features': top_features,
            'n_samples': len(X),
            'n_features': len(self.feature_names),
            'categories': list(self.label_encoder.classes_)
        }
        
        logger.info(f"Training completed! Test accuracy: {test_accuracy:.3f}")
        logger.info(f"Cross-validation accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        # Save model
        self.save_model()
        self.is_trained = True
        
        return training_results
    
    def predict_category(self, raw_text: str, amount: Optional[float] = None, 
                        merchant: Optional[str] = None, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Predict category using trained ML model"""
        
        if not self.is_trained or self.rf_model is None:
            logger.warning("Model not trained, falling back to rule-based prediction")
            return self._fallback_prediction(raw_text, merchant)
        
        try:
            logger.info(f"Starting ML prediction for: {raw_text[:50]}...")
            
            # Extract features
            features = self.feature_extractor.extract_features(raw_text, amount, merchant, date_str)
            logger.info(f"Extracted {len(features)} raw features")
            
            # Convert to DataFrame to maintain feature order
            features_df = pd.DataFrame([features])
            
            # Handle categorical features with same encoding as training
            categorical_features = ['amount_bucket', 'merchant_category', 'time_pattern']
            
            # Only encode columns that exist in the dataframe
            existing_categorical_features = [col for col in categorical_features if col in features_df.columns]
            
            for col in existing_categorical_features:
                features_df[col] = features_df[col].astype(str)
            
            # One-hot encode categorical features (need to match training columns)
            if existing_categorical_features:
                features_encoded = pd.get_dummies(features_df, columns=existing_categorical_features, prefix=existing_categorical_features)
            else:
                features_encoded = features_df.copy()
                
            logger.info(f"After encoding: {features_encoded.shape[1]} structured features")
            
            # Add missing columns that were present during training
            missing_columns = []
            structured_feature_names = [col for col in self.feature_names if not col.startswith('tfidf_')]
            
            for feature_name in structured_feature_names:
                if feature_name not in features_encoded.columns:
                    features_encoded[feature_name] = 0
                    missing_columns.append(feature_name)
            
            logger.info(f"Added {len(missing_columns)} missing columns")
            
            # Reorder columns to match training order (avoiding duplicates)
            structured_feature_names = [col for col in self.feature_names if not col.startswith('tfidf_')]
            
            # Remove duplicates from feature names and ensure no duplicate columns
            structured_feature_names = list(dict.fromkeys(structured_feature_names))  # Remove duplicates
            
            # Only reindex with columns that exist and are not duplicated
            available_columns = [col for col in structured_feature_names if col in features_encoded.columns]
            features_encoded = features_encoded[available_columns]
            
            # Add missing columns with default values
            for col in structured_feature_names:
                if col not in features_encoded.columns:
                    features_encoded[col] = 0
                    
            # Ensure final column order matches training
            features_encoded = features_encoded.reindex(columns=structured_feature_names, fill_value=0)
            logger.info(f"Reordered to {len(structured_feature_names)} structured features")
            
            # Get TF-IDF features
            text_tfidf = self.tfidf_vectorizer.transform([raw_text]).toarray()
            logger.info(f"TF-IDF features: {text_tfidf.shape[1]}")
            
            # Combine features
            combined_features = np.hstack([features_encoded.values, text_tfidf])
            logger.info(f"Combined features shape: {combined_features.shape}")
            
            # Scale features
            X_scaled = self.scaler.transform(combined_features)
            logger.info(f"Scaled features shape: {X_scaled.shape}")
            
            # Predict
            prediction = self.rf_model.predict(X_scaled)[0]
            probabilities = self.rf_model.predict_proba(X_scaled)[0]
            
            # Get category name and confidence
            predicted_category = self.label_encoder.inverse_transform([prediction])[0]
            confidence = float(np.max(probabilities))
            
            # Get top predictions with probabilities
            top_predictions = []
            for i, prob in enumerate(probabilities):
                category = self.label_encoder.inverse_transform([i])[0]
                top_predictions.append({'category': category, 'probability': float(prob)})
            
            top_predictions.sort(key=lambda x: x['probability'], reverse=True)
            
            result = {
                'category': predicted_category,
                'confidence': confidence,
                'method': 'ml_random_forest',
                'top_predictions': top_predictions[:3],
                'feature_count': len(self.feature_names)
            }
            
            logger.info(f"ML prediction successful: {predicted_category} (confidence: {confidence:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._fallback_prediction(raw_text, merchant)
    
    def _fallback_prediction(self, raw_text: str, merchant: Optional[str]) -> Dict[str, Any]:
        """Fallback prediction when ML fails"""
        # Simple rule-based fallback
        text_lower = raw_text.lower()
        merchant_lower = (merchant or '').lower()
        
        # Simple keyword matching
        if any(word in text_lower + merchant_lower for word in ['starbucks', 'coffee', 'restaurant', 'food']):
            return {'category': 'Dining', 'confidence': 0.6, 'method': 'fallback_rules'}
        elif any(word in text_lower + merchant_lower for word in ['walmart', 'grocery', 'market']):
            return {'category': 'Groceries', 'confidence': 0.6, 'method': 'fallback_rules'}
        elif any(word in text_lower + merchant_lower for word in ['netflix', 'spotify', 'streaming']):
            return {'category': 'Entertainment', 'confidence': 0.6, 'method': 'fallback_rules'}
        else:
            return {'category': 'Uncategorized', 'confidence': 0.2, 'method': 'fallback_default'}
    
    def save_model(self):
        """Save trained model and components"""
        try:
            model_data = {
                'rf_model': self.rf_model,
                'tfidf_vectorizer': self.tfidf_vectorizer,
                'scaler': self.scaler,
                'label_encoder': self.label_encoder,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self):
        """Load trained model and components"""
        try:
            if self.model_path.exists():
                model_data = joblib.load(self.model_path)
                
                self.rf_model = model_data.get('rf_model')
                self.tfidf_vectorizer = model_data.get('tfidf_vectorizer')
                self.scaler = model_data.get('scaler')
                self.label_encoder = model_data.get('label_encoder')
                self.feature_names = model_data.get('feature_names')
                self.is_trained = model_data.get('is_trained', False)
                
                # Check if all components are loaded
                components_loaded = all([
                    self.rf_model is not None,
                    self.tfidf_vectorizer is not None,
                    self.scaler is not None,
                    self.label_encoder is not None,
                    self.feature_names is not None
                ])
                
                if components_loaded:
                    self.is_trained = True
                    logger.info("Pre-trained model loaded successfully")
                    return True
                else:
                    logger.warning("Some model components missing")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
        
        return False

def train_model_cli():
    """CLI function to train the model"""
    print("🤖 Training ML Category Prediction Model...")
    
    predictor = MLCategoryPredictor()
    results = predictor.train_model()
    
    print("\n📊 Training Results:")
    print(f"✅ Test Accuracy: {results['test_accuracy']:.3f}")
    print(f"✅ Cross-validation: {results['cv_mean_accuracy']:.3f} (+/- {results['cv_std_accuracy'] * 2:.3f})")
    print(f"✅ Categories: {', '.join(results['categories'])}")
    print(f"✅ Features: {results['n_features']}")
    
    print("\n🎯 Top Features:")
    for feature, importance in results['top_features'][:10]:
        print(f"  {feature}: {importance:.4f}")
    
    print(f"\n💾 Model saved to: {predictor.model_path}")
    return results

if __name__ == "__main__":
    # Train the model
    train_model_cli()