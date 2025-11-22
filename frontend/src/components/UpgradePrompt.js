import React, { useState } from 'react';
import { Crown, X, Zap, ArrowRight, Loader2 } from 'lucide-react';
import axios from 'axios';

const UpgradePrompt = ({ open, onOpenChange, billingInfo }) => {
  const [upgrading, setUpgrading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  const handleUpgrade = async () => {
    try {
      setUpgrading(true);
      setError('');

      const response = await axios.post(
        `${API_BASE_URL}/api/billing/create-checkout-session`,
        {
          plan_type: 'pro',
          origin_url: window.location.origin
        },
        {
          withCredentials: true
        }
      );

      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url;
      
    } catch (err) {
      console.error('Error creating checkout session:', err);
      setError(
        err.response?.data?.detail?.message || 
        'Failed to start upgrade process. Please try again.'
      );
    } finally {
      setUpgrading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-blue-600 text-white p-6 rounded-t-xl relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white hover:bg-white hover:bg-opacity-20 rounded-full p-1 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
          
          <div className="text-center">
            <Crown className="h-12 w-12 text-yellow-300 mx-auto mb-3" />
            <h2 className="text-2xl font-bold mb-2">Upgrade to Pro</h2>
            <p className="text-purple-100">
              You've reached your monthly limit!
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Current Usage */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Current Usage</p>
              <div className="text-2xl font-bold text-gray-900 mb-2">
                {receiptsUsed} / {receiptLimit}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-red-500 h-2 rounded-full"
                  style={{ width: '100%' }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                You've used all your {currentPlan} plan receipts this month
              </p>
            </div>
          </div>

          {/* Pro Benefits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Unlock Pro Features
            </h3>
            <div className="space-y-3">
              <div className="flex items-start">
                <Zap className="h-5 w-5 text-blue-600 mr-3 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">500 Receipts/Month</p>
                  <p className="text-sm text-gray-600">10x more than the free plan</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <Zap className="h-5 w-5 text-blue-600 mr-3 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">Advanced AI Processing</p>
                  <p className="text-sm text-gray-600">Smarter categorization and data extraction</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <Zap className="h-5 w-5 text-blue-600 mr-3 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">Priority Support</p>
                  <p className="text-sm text-gray-600">Get help when you need it</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <Zap className="h-5 w-5 text-blue-600 mr-3 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">Advanced Analytics</p>
                  <p className="text-sm text-gray-600">Deep insights into your expenses</p>
                </div>
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <div className="text-center">
              <p className="text-sm text-blue-600 font-medium mb-1">Pro Plan</p>
              <p className="text-3xl font-bold text-blue-900 mb-1">
                $9.99
                <span className="text-lg font-normal text-blue-700">/month</span>
              </p>
              <p className="text-sm text-blue-600">
                Cancel anytime • 30-day money back guarantee
              </p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={handleUpgrade}
              disabled={upgrading}
              className="w-full bg-gradient-to-r from-purple-500 to-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-purple-600 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {upgrading ? (
                <>
                  <Loader2 className="animate-spin h-5 w-5 mr-2" />
                  Processing...
                </>
              ) : (
                <>
                  <Crown className="h-5 w-5 mr-2" />
                  Upgrade to Pro Now
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </button>
            
            <button
              onClick={onClose}
              className="w-full text-gray-600 hover:text-gray-800 font-medium py-2 transition-colors"
            >
              Maybe Later
            </button>
          </div>

          {/* Trust Indicators */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-center space-x-6 text-xs text-gray-500">
              <span>🔒 Secure Payment</span>
              <span>💳 Stripe Protected</span>
              <span>⚡ Instant Access</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradePrompt;