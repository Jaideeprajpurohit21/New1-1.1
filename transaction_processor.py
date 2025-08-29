#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Master Transaction Processor

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import re
import json
import numpy as np
from datetime import datetime, date
from typing import Dict, Optional, Any
import logging

# Import our robust extractors
from robust_amount_extractor import extract_amount
from robust_date_extractor import extract_date

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionProcessor:
    """Master transaction processor integrating amount, date, category, and merchant extraction"""
    
    def __init__(self):
        """Initialize the transaction processor with category prediction model"""
        self.category_rules = self._load_category_rules()
        self.merchant_patterns = self._load_merchant_patterns()
        
    def _load_category_rules(self) -> Dict[str, Any]:
        """Load rule-based category prediction system"""
        return {
            # High-confidence rules (ordered by priority)
            'entertainment': {
                'merchants': ['netflix', 'spotify', 'disney', 'amazon prime', 'hulu', 'youtube', 'steam', 'apple music'],
                'keywords': ['subscription', 'streaming', 'monthly', 'premium', 'game', 'music', 'video'],
                'amount_patterns': [(5, 50), 'recurring'],  # $5-50, recurring pattern
                'confidence': 0.95
            },
            'groceries': {
                'merchants': ['walmart', 'costco', 'kroger', 'safeway', 'whole foods', 'trader joe', 'alfamart', 'target'],
                'keywords': ['grocery', 'market', 'store', 'supercenter', 'organic', 'produce'],
                'amount_patterns': [(20, 300)],  # $20-300 range
                'confidence': 0.90
            },
            'dining': {
                'merchants': ['mcdonald', 'starbucks', 'chipotle', 'subway', 'kfc', 'domino', 'pizza', 'dunkin'],
                'keywords': ['restaurant', 'cafe', 'food', 'delivery', 'drive', 'order', 'menu', 'takeout'],
                'time_patterns': ['morning_rush', 'lunch_time', 'dinner_time'],
                'amount_patterns': [(3, 100)],
                'confidence': 0.88
            },
            'transportation': {
                'merchants': ['uber', 'lyft', 'shell', 'chevron', 'bp', 'exxon', 'tesla', 'gas station'],
                'keywords': ['ride', 'fuel', 'gas', 'parking', 'toll', 'metro', 'taxi', 'pump', 'station'],
                'time_patterns': ['morning_commute', 'evening_commute'],
                'amount_patterns': [(5, 150)],
                'confidence': 0.85
            },
            'utilities': {
                'merchants': ['verizon', 'at&t', 'comcast', 'electric', 'gas company', 'water', 'internet'],
                'keywords': ['bill', 'monthly', 'due', 'utility', 'electric', 'internet', 'phone', 'wireless'],
                'amount_patterns': [(25, 300), 'round_numbers'],
                'confidence': 0.92
            },
            'shopping': {
                'merchants': ['amazon', 'ebay', 'best buy', 'home depot', 'target', 'rei', 'clothing'],
                'keywords': ['purchase', 'order', 'shipping', 'item', 'product', 'store'],
                'amount_patterns': [(10, 1000)],
                'confidence': 0.75
            },
            'healthcare': {
                'merchants': ['cvs', 'walgreens', 'pharmacy', 'hospital', 'clinic', 'gym', 'fitness'],
                'keywords': ['prescription', 'pharmacy', 'medical', 'doctor', 'gym', 'membership', 'health'],
                'amount_patterns': [(10, 200), 'copay_amounts'],
                'confidence': 0.88
            },
            'travel': {
                'merchants': ['delta', 'united', 'marriott', 'hilton', 'airbnb', 'booking', 'expedia'],
                'keywords': ['flight', 'hotel', 'booking', 'reservation', 'travel', 'airline', 'airport'],
                'amount_patterns': [(50, 2000)],
                'confidence': 0.90
            },
            'subscriptions': {
                'merchants': ['microsoft', 'adobe', 'dropbox', 'office', 'cloud'],
                'keywords': ['annual', 'software', 'license', 'cloud', 'storage', 'office', 'pro'],
                'amount_patterns': [(5, 200), 'recurring'],
                'confidence': 0.93
            }
        }
    
    def _load_merchant_patterns(self) -> Dict[str, str]:
        """Common merchant name patterns and their clean versions"""
        return {
            # Clean up common merchant name variations
            'mcdonald.*': 'McDonald\'s',
            'starbucks.*': 'Starbucks',
            'walmart.*': 'Walmart',
            'amazon.*': 'Amazon',
            'netflix.*': 'Netflix',
            'spotify.*': 'Spotify',
            'uber.*': 'Uber',
            'lyft.*': 'Lyft',
            'shell.*': 'Shell',
            'target.*': 'Target',
            'costco.*': 'Costco',
            'home depot.*': 'Home Depot',
            'best buy.*': 'Best Buy'
        }
    
    def extract_merchant(self, text: str) -> Optional[str]:
        """Extract and clean merchant name from transaction text"""
        text_lower = text.lower()
        
        # Method 1: Look for known merchant patterns
        for pattern, clean_name in self.merchant_patterns.items():
            if re.search(pattern, text_lower):
                return clean_name
        
        # Method 2: Extract from common transaction patterns
        merchant_patterns = [
            # "at Starbucks", "from Amazon"
            r'\b(?:at|from)\s+([A-Za-z][A-Za-z\s&]+?)(?:\s+(?:on|charged|billed|purchase))',
            # "Merchant Name charged", "Merchant Name purchase"  
            r'^([A-Za-z][A-Za-z\s&]+?)\s+(?:charged|purchase|billed)',
            # "Payment to Merchant Name"
            r'payment\s+to\s+([A-Za-z][A-Za-z\s&]+?)(?:\s+(?:on|of))',
            # "Merchant Name Store #123"
            r'^([A-Za-z][A-Za-z\s&]+?)\s+(?:store|location)\s*#',
            # General merchant at start of text
            r'^([A-Z][A-Za-z\s&]{2,30}?)(?:\s+(?:purchase|charged|order|subscription))',
        ]
        
        for pattern in merchant_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                # Clean up the merchant name
                merchant = re.sub(r'\s+', ' ', merchant)  # Multiple spaces to single
                merchant = merchant.title()  # Title case
                
                # Filter out common false positives
                if len(merchant) > 2 and merchant.lower() not in ['you', 'your', 'card', 'account', 'bank']:
                    return merchant
        
        # Method 3: Look for capitalized words that might be merchants
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
        for word in words[:3]:  # Check first few capitalized phrases
            if (len(word) > 2 and 
                word.lower() not in ['purchase', 'payment', 'charged', 'billed', 'transaction', 'order']):
                return word
        
        return None
    
    def predict_category(self, text: str, amount: Optional[float], merchant: Optional[str], 
                        date_str: Optional[str]) -> tuple[str, float]:
        """Predict transaction category using rule-based system"""
        text_lower = text.lower()
        merchant_lower = (merchant or '').lower()
        
        category_scores = {}
        
        for category, rules in self.category_rules.items():
            score = 0.0
            
            # Check merchant matches (highest weight)
            if merchant_lower:
                for known_merchant in rules.get('merchants', []):
                    if known_merchant in merchant_lower:
                        score += 0.4
                        break
            
            # Check keyword matches
            keyword_matches = sum(1 for keyword in rules.get('keywords', []) 
                                if keyword in text_lower)
            if keyword_matches > 0:
                score += min(0.3, keyword_matches * 0.1)
            
            # Check amount patterns
            if amount and rules.get('amount_patterns'):
                for pattern in rules['amount_patterns']:
                    if isinstance(pattern, tuple) and len(pattern) == 2:
                        min_amt, max_amt = pattern
                        if min_amt <= amount <= max_amt:
                            score += 0.2
                    elif pattern == 'recurring' and self._is_recurring_amount(amount):
                        score += 0.15
                    elif pattern == 'round_numbers' and amount == int(amount):
                        score += 0.1
                    elif pattern == 'copay_amounts' and amount in [10, 15, 20, 25, 30, 35, 40, 45, 50]:
                        score += 0.15
            
            # Check time patterns (if extractable from text)
            time_context = self._extract_time_context(text_lower)
            if time_context and time_context in rules.get('time_patterns', []):
                score += 0.1
            
            category_scores[category] = score
        
        # Get best category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = min(0.99, category_scores[best_category])
            
            # Apply minimum confidence threshold
            if confidence >= 0.3:
                return best_category.title(), confidence
        
        # Default fallback
        return self._fallback_category_prediction(text_lower, amount, merchant_lower)
    
    def _is_recurring_amount(self, amount: float) -> bool:
        """Check if amount matches common recurring patterns"""
        recurring_amounts = [9.99, 14.99, 15.99, 19.99, 29.99, 39.99, 49.99, 79.99, 99.99]
        return any(abs(amount - recurring_amt) < 0.01 for recurring_amt in recurring_amounts)
    
    def _extract_time_context(self, text: str) -> Optional[str]:
        """Extract time context from text"""
        time_patterns = {
            'morning_rush': r'\b(?:0?[7-9]:[0-5]\d|morning|breakfast)\b',
            'lunch_time': r'\b(?:1[0-4]:[0-5]\d|lunch|noon)\b',
            'dinner_time': r'\b(?:1[7-9]:[0-5]\d|2[0-3]:[0-5]\d|dinner|evening)\b',
            'morning_commute': r'\b(?:0?[7-9]:[0-5]\d.*(?:am|AM))\b',
            'evening_commute': r'\b(?:1[7-9]:[0-5]\d.*(?:pm|PM))\b'
        }
        
        for context, pattern in time_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return context
        return None
    
    def _fallback_category_prediction(self, text: str, amount: Optional[float], 
                                    merchant: Optional[str]) -> tuple[str, float]:
        """Fallback category prediction for unmatched transactions"""
        
        # Amount-based fallbacks
        if amount:
            if amount < 10:
                return "Dining", 0.4  # Small amounts often food/coffee
            elif 10 <= amount <= 50:
                return "Shopping", 0.3  # Medium amounts often retail
            elif 50 <= amount <= 200:
                if any(word in text for word in ['bill', 'monthly', 'due']):
                    return "Utilities", 0.4
                else:
                    return "Shopping", 0.3
            else:  # > 200
                return "Shopping", 0.2  # Large amounts often major purchases
        
        # Keyword-based fallbacks
        if any(word in text for word in ['food', 'restaurant', 'cafe', 'delivery']):
            return "Dining", 0.5
        elif any(word in text for word in ['gas', 'fuel', 'ride', 'taxi']):
            return "Transportation", 0.5
        elif any(word in text for word in ['store', 'purchase', 'buy', 'order']):
            return "Shopping", 0.4
        
        return "Uncategorized", 0.1
    
    def process_transaction(self, raw_text: str) -> Dict[str, Any]:
        """
        Master function to process transaction text and extract all key information
        
        Args:
            raw_text (str): Raw transaction text from SMS/email
            
        Returns:
            Dict with keys: amount, date, category, merchant, confidence, raw_text
        """
        
        if not raw_text or not isinstance(raw_text, str):
            return {
                'amount': None,
                'date': None, 
                'category': 'Uncategorized',
                'merchant': None,
                'confidence': 0.0,
                'raw_text': raw_text,
                'processing_status': 'failed',
                'error': 'Invalid input text'
            }
        
        try:
            logger.info(f"Processing transaction: {raw_text[:100]}...")
            
            # Step 1: Extract amount using robust extractor
            extracted_amount = extract_amount(raw_text)
            
            # Step 2: Extract date using robust extractor  
            extracted_date = extract_date(raw_text)
            
            # Step 3: Extract merchant name
            extracted_merchant = self.extract_merchant(raw_text)
            
            # Step 4: Predict category using all available information
            predicted_category, confidence = self.predict_category(
                raw_text, extracted_amount, extracted_merchant, extracted_date
            )
            
            # Step 5: Compile results
            result = {
                'amount': extracted_amount,
                'date': extracted_date,
                'category': predicted_category,
                'merchant': extracted_merchant,
                'confidence': round(confidence, 3),
                'raw_text': raw_text,
                'processing_status': 'completed'
            }
            
            # Log results for debugging
            logger.info(f"Extracted - Amount: {extracted_amount}, Date: {extracted_date}, "
                       f"Merchant: {extracted_merchant}, Category: {predicted_category} "
                       f"(confidence: {confidence:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            return {
                'amount': None,
                'date': None,
                'category': 'Uncategorized', 
                'merchant': None,
                'confidence': 0.0,
                'raw_text': raw_text,
                'processing_status': 'failed',
                'error': str(e)
            }


def test_transaction_processor():
    """Test the transaction processor with various examples"""
    
    processor = TransactionProcessor()
    
    test_cases = [
        "Netflix monthly subscription of $15.99 was automatically charged on 2024-10-05",
        "Alfamart PURCHASE INR 485.00 on 12-03-2024. Avl bal INR 12,345.67. Trxn ID 1234567890",
        "You spent $29.99 at Amazon.com on Oct 5. Your card ending in 1234 was charged",
        "Starbucks Coffee charged $8.45 on Oct 15 at 7:23 AM. Store: Downtown Seattle",
        "Uber ride payment of $23.67 on 2024-11-08. Trip from Airport to Downtown",
        "Electricity Bill Payment of INR 3,456.00 to State Power Board on 2024-09-20 successful",
        "UPI Payment to Zomato of ₹485.00 on 14-10-2024 at 20:15. Food delivered",
        "Microsoft Office 365 annual subscription $99.99 renewed on 2024-01-15"
    ]
    
    print("🧪 Testing Transaction Processor")
    print("=" * 80)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}:")
        print(f"Input: {test_text}")
        
        result = processor.process_transaction(test_text)
        
        print(f"Results:")
        print(f"  💰 Amount: {result['amount']}")
        print(f"  📅 Date: {result['date']}")  
        print(f"  🏪 Merchant: {result['merchant']}")
        print(f"  🏷️ Category: {result['category']} (confidence: {result['confidence']})")
        print(f"  ✅ Status: {result['processing_status']}")


if __name__ == "__main__":
    test_transaction_processor()