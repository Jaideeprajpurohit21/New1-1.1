import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { CheckCircle, Loader2, Crown, ArrowRight, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BillingSuccessPage = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');
  const [sessionInfo, setSessionInfo] = useState(null);
  const [error, setError] = useState('');

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (sessionId) {
      checkPaymentStatus(sessionId);
    } else {
      setError('No session ID found');
      setStatus('error');
    }
  }, []);

  const checkPaymentStatus = async (sessionId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/billing/checkout-status/${sessionId}`,
        {
          withCredentials: true
        }
      );

      setSessionInfo(response.data);
      
      if (response.data.payment_status === 'paid') {
        setStatus('success');
        // Refresh user data to get updated plan
        await refreshUser();
      } else if (response.data.status === 'expired') {
        setStatus('expired');
      } else {
        setStatus('pending');
        // Keep checking for a bit
        setTimeout(() => checkPaymentStatus(sessionId), 2000);
      }
      
    } catch (err) {
      console.error('Error checking payment status:', err);
      setError('Failed to verify payment status');
      setStatus('error');
    }
  };

  const renderContent = () => {
    switch (status) {
      case 'processing':
      case 'pending':
        return (
          <div className="text-center">
            <Loader2 className="animate-spin h-16 w-16 text-blue-600 mx-auto mb-6" />
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Processing Your Payment
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              Please wait while we confirm your subscription...
            </p>
            <div className="bg-blue-50 rounded-lg p-4 max-w-md mx-auto">
              <p className="text-sm text-blue-800">
                This usually takes just a few seconds. Don't refresh the page.
              </p>
            </div>
          </div>
        );

      case 'success':
        return (
          <div className="text-center">
            <div className="bg-green-100 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-16 w-16 text-green-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Welcome to Lumina Pro!
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              Your subscription has been activated successfully.
            </p>
            
            {/* Success Details */}
            <div className="bg-gradient-to-r from-purple-500 to-blue-600 rounded-xl p-6 text-white max-w-md mx-auto mb-8">
              <div className="flex items-center justify-center mb-4">
                <Crown className="h-8 w-8 text-yellow-300 mr-2" />
                <span className="text-xl font-semibold">Lumina Pro</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Plan:</span>
                  <span className="font-semibold">Pro Monthly</span>
                </div>
                <div className="flex justify-between">
                  <span>Receipts per month:</span>
                  <span className="font-semibold">500</span>
                </div>
                {sessionInfo && (
                  <div className="flex justify-between">
                    <span>Amount paid:</span>
                    <span className="font-semibold">
                      ${(sessionInfo.amount_total / 100).toFixed(2)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* What's New */}
            <div className="bg-gray-50 rounded-lg p-6 max-w-2xl mx-auto mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                What's New with Pro
              </h2>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">10x More Receipts</p>
                    <p className="text-gray-600">Process up to 500 receipts per month</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Advanced AI</p>
                    <p className="text-gray-600">Smarter categorization and data extraction</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Priority Support</p>
                    <p className="text-gray-600">Get help faster when you need it</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Advanced Features</p>
                    <p className="text-gray-600">Search, filtering, and analytics</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-4">
              <button
                onClick={() => navigate('/')}
                className="bg-blue-600 text-white font-semibold px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center mx-auto"
              >
                <ArrowRight className="h-5 w-5 mr-2" />
                Start Using Pro Features
              </button>
              
              <button
                onClick={() => navigate('/billing')}
                className="text-blue-600 hover:text-blue-700 font-medium flex items-center mx-auto"
              >
                View Billing Details
              </button>
            </div>
          </div>
        );

      case 'expired':
        return (
          <div className="text-center">
            <div className="bg-yellow-100 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-16 w-16 text-yellow-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Session Expired
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              Your checkout session has expired. Please try again.
            </p>
            <div className="space-y-4">
              <button
                onClick={() => navigate('/billing')}
                className="bg-blue-600 text-white font-semibold px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center mx-auto"
              >
                <ArrowRight className="h-5 w-5 mr-2" />
                Try Again
              </button>
            </div>
          </div>
        );

      case 'error':
      default:
        return (
          <div className="text-center">
            <div className="bg-red-100 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-16 w-16 text-red-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Payment Verification Failed
            </h1>
            <p className="text-lg text-gray-600 mb-4">
              We couldn't verify your payment status.
            </p>
            {error && (
              <p className="text-red-600 mb-8">{error}</p>
            )}
            <div className="space-y-4">
              <button
                onClick={() => window.location.reload()}
                className="bg-blue-600 text-white font-semibold px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center mx-auto"
              >
                <ArrowRight className="h-5 w-5 mr-2" />
                Try Again
              </button>
              
              <button
                onClick={() => navigate('/')}
                className="text-blue-600 hover:text-blue-700 font-medium flex items-center mx-auto"
              >
                <Home className="h-5 w-5 mr-2" />
                Go Home
              </button>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-4xl mx-auto">
        {renderContent()}
      </div>
    </div>
  );
};

export default BillingSuccessPage;