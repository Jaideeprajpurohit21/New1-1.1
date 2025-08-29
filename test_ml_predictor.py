#!/usr/bin/env python3
"""
Test ML Category Predictor
"""

from ml_category_predictor import MLCategoryPredictor

def test_ml_predictor():
    """Test the ML category predictor with various examples"""
    
    print("🧪 Testing ML Category Predictor")
    print("=" * 60)
    
    predictor = MLCategoryPredictor()
    
    test_cases = [
        {
            'raw_text': "Starbucks Coffee charged $8.45 on Oct 15 at 7:23 AM",
            'amount': 8.45,
            'merchant': "Starbucks",
            'date': "2024-10-15",
            'expected': 'Dining'
        },
        {
            'raw_text': "Netflix monthly subscription of $15.99 was automatically charged",
            'amount': 15.99,
            'merchant': "Netflix", 
            'date': "2024-10-05",
            'expected': 'Entertainment'
        },
        {
            'raw_text': "Walmart Supercenter purchase $156.78",
            'amount': 156.78,
            'merchant': "Walmart",
            'date': "2024-09-07",
            'expected': 'Groceries'
        },
        {
            'raw_text': "Shell Gas Station charged $65.40 for fuel",
            'amount': 65.40,
            'merchant': "Shell",
            'date': "2024-07-18",
            'expected': 'Transportation'
        },
        {
            'raw_text': "CVS Pharmacy prescription pickup $25.00 copay",
            'amount': 25.00,
            'merchant': "CVS",
            'date': "2024-10-08", 
            'expected': 'Healthcare'
        }
    ]
    
    correct_predictions = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['expected']} Prediction")
        print(f"Input: {test['raw_text']}")
        
        result = predictor.predict_category(
            raw_text=test['raw_text'],
            amount=test['amount'],
            merchant=test['merchant'],
            date_str=test['date']
        )
        
        predicted_category = result['category']
        confidence = result['confidence']
        method = result['method']
        
        print(f"Expected: {test['expected']}")
        print(f"Predicted: {predicted_category} (confidence: {confidence:.3f})")
        print(f"Method: {method}")
        
        if predicted_category == test['expected']:
            print("✅ CORRECT")
            correct_predictions += 1
        else:
            print("❌ INCORRECT")
            
        # Show top predictions
        print("Top 3 predictions:")
        for pred in result.get('top_predictions', [])[:3]:
            print(f"  - {pred['category']}: {pred['probability']:.3f}")
    
    accuracy = correct_predictions / len(test_cases)
    print(f"\n🎯 Overall Accuracy: {correct_predictions}/{len(test_cases)} = {accuracy:.1%}")
    
    if accuracy >= 0.6:
        print("🎉 ML predictor is working well!")
    else:
        print("⚠️ ML predictor needs improvement")

if __name__ == "__main__":
    test_ml_predictor()