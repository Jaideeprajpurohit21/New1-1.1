import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { 
  CreditCard, 
  Check, 
  X, 
  Crown, 
  Zap, 
  AlertCircle, 
  Loader2,
  ArrowRight,
  Receipt,
  TrendingUp
} from 'lucide-react';

const BillingPage = () => {
  const { user } = useAuth();
  const [billingInfo, setBillingInfo] = useState(null);
  const [plans, setPlans] = useState({});
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      
      // Fetch billing info and plans in parallel
      const [billingResponse, plansResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/billing/info`, {
          withCredentials: true
        }),
        axios.get(`${API_BASE_URL}/api/billing/plans`, {
          withCredentials: true
        })
      ]);

      setBillingInfo(billingResponse.data);
      setPlans(plansResponse.data.plans);
      
    } catch (err) {
      console.error('Error fetching billing data:', err);
      setError('Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planType) => {
    try {
      setUpgrading(true);
      setError('');

      const response = await axios.post(
        `${API_BASE_URL}/api/billing/create-checkout-session`,
        {
          plan_type: planType,
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading billing information...</p>
        </div>
      </div>
    );
  }

  if (!billingInfo) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Billing</h2>
          <p className="text-gray-600 mb-4">{error || 'Unable to load billing information'}</p>
          <button
            onClick={fetchBillingData}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Billing & Subscription
          </h1>
          <p className="text-lg text-gray-600">
            Manage your Lumina subscription and billing preferences
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              <span className="text-red-800">{error}</span>
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Current Plan Status */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Current Plan: {billingInfo.plan_name}
                  </h2>
                  <div className="flex items-center text-gray-600">
                    {billingInfo.plan === 'free' ? (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                        Free Plan
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-purple-500 to-blue-600 text-white">
                        <Crown className="w-4 h-4 mr-1" />
                        Pro Plan
                      </span>
                    )}
                  </div>
                </div>
                <Receipt className="h-12 w-12 text-blue-600" />
              </div>

              {/* Usage Statistics */}
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">Receipts Used</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {billingInfo.receipts_used}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${Math.min((billingInfo.receipts_used / billingInfo.receipt_limit) * 100, 100)}%` 
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {billingInfo.receipts_remaining} remaining of {billingInfo.receipt_limit}
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">Billing Period</span>
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  </div>
                  <p className="text-sm text-gray-900">
                    {formatDate(billingInfo.billing_period_start)}
                  </p>
                  <p className="text-sm text-gray-900">
                    to {formatDate(billingInfo.billing_period_end)}
                  </p>
                </div>
              </div>

              {/* Features */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Plan Features</h3>
                <div className="grid md:grid-cols-2 gap-2">
                  {billingInfo.features.map((feature, index) => (
                    <div key={index} className="flex items-center text-sm text-gray-600">
                      <Check className="h-4 w-4 text-green-600 mr-2 flex-shrink-0" />
                      {feature}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Upgrade Section */}
            {billingInfo.can_upgrade && (
              <div className="bg-gradient-to-r from-purple-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-2xl font-bold mb-2">Ready to Upgrade?</h3>
                    <p className="text-purple-100 mb-4">
                      Get 10x more receipts and advanced AI features with Lumina Pro
                    </p>
                    <ul className="space-y-2 text-sm text-purple-100">
                      <li className="flex items-center">
                        <Zap className="h-4 w-4 mr-2" />
                        500 receipts per month (10x more!)
                      </li>
                      <li className="flex items-center">
                        <Zap className="h-4 w-4 mr-2" />
                        Advanced AI categorization
                      </li>
                      <li className="flex items-center">
                        <Zap className="h-4 w-4 mr-2" />
                        Priority support
                      </li>
                    </ul>
                  </div>
                  <Crown className="h-16 w-16 text-yellow-300" />
                </div>
                <button
                  onClick={() => handleUpgrade('pro')}
                  disabled={upgrading}
                  className="mt-6 bg-white text-purple-600 font-semibold px-8 py-3 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {upgrading ? (
                    <>
                      <Loader2 className="animate-spin h-5 w-5 mr-2" />
                      Processing...
                    </>
                  ) : (
                    <>
                      Upgrade to Pro
                      <ArrowRight className="h-5 w-5 ml-2" />
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Available Plans */}
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-6">Available Plans</h2>
            <div className="space-y-4">
              {Object.entries(plans).map(([planKey, plan]) => (
                <div 
                  key={planKey}
                  className={`border rounded-xl p-4 transition-all ${
                    billingInfo.plan === planKey 
                      ? 'border-blue-500 bg-blue-50 shadow-md' 
                      : 'border-gray-200 bg-white hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 flex items-center">
                        {plan.name}
                        {planKey === 'pro' && <Crown className="h-4 w-4 ml-1 text-yellow-500" />}
                        {billingInfo.plan === planKey && (
                          <span className="ml-2 text-xs bg-blue-600 text-white px-2 py-1 rounded-full">
                            Current
                          </span>
                        )}
                      </h3>
                      <p className="text-2xl font-bold text-gray-900 mt-1">
                        ${plan.price}
                        <span className="text-sm font-normal text-gray-600">/month</span>
                      </p>
                    </div>
                    {planKey === 'pro' ? (
                      <Crown className="h-8 w-8 text-yellow-500" />
                    ) : (
                      <CreditCard className="h-8 w-8 text-gray-400" />
                    )}
                  </div>

                  <div className="space-y-2 mb-4">
                    <p className="text-sm font-medium text-gray-900">
                      {plan.receipt_limit} receipts/month
                    </p>
                    {plan.features.slice(0, 3).map((feature, index) => (
                      <div key={index} className="flex items-center text-sm text-gray-600">
                        <Check className="h-3 w-3 text-green-600 mr-2 flex-shrink-0" />
                        {feature}
                      </div>
                    ))}
                    {plan.features.length > 3 && (
                      <p className="text-xs text-gray-500">
                        +{plan.features.length - 3} more features
                      </p>
                    )}
                  </div>

                  {billingInfo.plan !== planKey && planKey !== 'free' && (
                    <button
                      onClick={() => handleUpgrade(planKey)}
                      disabled={upgrading}
                      className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {upgrading ? (
                        <Loader2 className="animate-spin h-4 w-4 mr-2" />
                      ) : (
                        <ArrowRight className="h-4 w-4 mr-2" />
                      )}
                      Upgrade Now
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BillingPage;