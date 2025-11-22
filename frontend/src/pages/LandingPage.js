import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  Upload, 
  Bot, 
  BarChart3, 
  Download, 
  CheckCircle, 
  ArrowRight,
  Sparkles,
  DollarSign,
  FileText,
  Zap,
  Shield,
  Clock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LandingPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Lumina
              </span>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <Button onClick={() => navigate('/app')} className="bg-blue-600 hover:bg-blue-700">
                  Go to Dashboard
                </Button>
              ) : (
                <>
                  <Button variant="ghost" onClick={() => navigate('/login')}>
                    Login
                  </Button>
                  <Button onClick={() => navigate('/app')} className="bg-blue-600 hover:bg-blue-700">
                    Start Free Demo
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <img 
            src="https://images.unsplash.com/photo-1665289420979-7c3636589418?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2MzR8MHwxfHNlYXJjaHwzfHxBSSUyMGZpbmFuY2UlMjB0ZWNobm9sb2d5fGVufDB8fHxibHVlfDE3NjM3NzAzNDN8MA&ixlib=rb-4.1.0&q=85"
            alt="AI Technology Background"
            className="w-full h-full object-cover opacity-20"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-purple-50 opacity-90"></div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
          <div className="text-center max-w-4xl mx-auto">
            <Badge className="mb-4 bg-blue-100 text-blue-700 hover:bg-blue-200">
              <Sparkles className="w-3 h-3 mr-1" />
              AI-Powered Expense Management
            </Badge>
            
            <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-6">
              Lumina – AI-Powered Receipt & Expense Management
            </h1>
            
            <p className="text-xl md:text-2xl text-slate-600 mb-8 max-w-3xl mx-auto">
              Upload receipts, let AI extract everything, and get tax-ready reports in minutes.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center gap-4 mb-12">
              <Button 
                size="lg" 
                onClick={() => navigate('/app')}
                className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-6"
              >
                Start Free Demo
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button 
                size="lg" 
                variant="outline"
                onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                className="text-lg px-8 py-6"
              >
                Learn More
              </Button>
            </div>

            {/* Stats/Trust Indicators */}
            <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto pt-8 border-t border-slate-200">
              <div>
                <div className="text-3xl font-bold text-blue-600">99%</div>
                <div className="text-sm text-slate-600">OCR Accuracy</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-600">10s</div>
                <div className="text-sm text-slate-600">Processing Time</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-600">10+</div>
                <div className="text-sm text-slate-600">Categories</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              Powerful Features for Modern Expense Tracking
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Everything you need to streamline your expense management and stay tax-ready.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1: Smart OCR */}
            <Card className="hover:shadow-lg transition-shadow border-2 hover:border-blue-200">
              <CardHeader>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle className="text-xl">Smart OCR & Data Extraction</CardTitle>
                <CardDescription>
                  Advanced optical character recognition automatically extracts merchant names, amounts, dates, and items from any receipt.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>99%+ accuracy rate</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Supports JPG, PNG, and PDF</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Line-item detection</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Feature 2: AI Categorization */}
            <Card className="hover:shadow-lg transition-shadow border-2 hover:border-purple-200">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <Bot className="h-6 w-6 text-purple-600" />
                </div>
                <CardTitle className="text-xl">AI Auto-Categorization</CardTitle>
                <CardDescription>
                  Machine learning models automatically categorize expenses based on merchant and content analysis.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>10+ expense categories</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Learns from your patterns</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Manual override available</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Feature 3: Dashboard Analytics */}
            <Card className="hover:shadow-lg transition-shadow border-2 hover:border-green-200">
              <CardHeader>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <BarChart3 className="h-6 w-6 text-green-600" />
                </div>
                <CardTitle className="text-xl">Dashboard Analytics & Insights</CardTitle>
                <CardDescription>
                  Real-time spending insights with visual analytics and category breakdowns.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Real-time statistics</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Category-wise breakdowns</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Search and filter tools</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Feature 4: Tax Export */}
            <Card className="hover:shadow-lg transition-shadow border-2 hover:border-orange-200">
              <CardHeader>
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                  <Download className="h-6 w-6 text-orange-600" />
                </div>
                <CardTitle className="text-xl">Tax-Ready CSV Export</CardTitle>
                <CardDescription>
                  Export your expenses in accountant-friendly formats ready for tax filing.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Professional CSV format</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Category summaries included</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Filter by date and category</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Get started in three simple steps and never worry about manual expense tracking again.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            {/* Connecting Lines (hidden on mobile) */}
            <div className="hidden md:block absolute top-1/3 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-200 via-purple-200 to-green-200 z-0"></div>

            {/* Step 1 */}
            <div className="relative z-10 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                <Upload className="h-10 w-10 text-white" />
              </div>
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl shadow-lg">
                1
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Upload Your Receipts</h3>
              <p className="text-slate-600">
                Simply snap a photo or upload a PDF of your receipt. Drag and drop or choose from your device.
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative z-10 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                <Bot className="h-10 w-10 text-white" />
              </div>
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-purple-600 text-white w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl shadow-lg">
                2
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">AI Extracts & Categorizes Automatically</h3>
              <p className="text-slate-600">
                Our AI instantly reads the receipt, extracts all data, and intelligently categorizes the expense for you.
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative z-10 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                <BarChart3 className="h-10 w-10 text-white" />
              </div>
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-green-600 text-white w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl shadow-lg">
                3
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Review Analytics & Export for Taxes</h3>
              <p className="text-slate-600">
                View spending insights in your dashboard and export tax-ready reports whenever you need them.
              </p>
            </div>
          </div>

          <div className="text-center mt-12">
            <Button 
              size="lg" 
              onClick={() => navigate('/app')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-lg px-8 py-6"
            >
              Try It Now – It's Free!
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Start free and upgrade when you need more power.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Plan */}
            <Card className="border-2 border-slate-200 hover:border-blue-300 transition-colors">
              <CardHeader className="text-center">
                <div className="text-sm font-semibold text-blue-600 mb-2">FREE</div>
                <CardTitle className="text-3xl mb-2">Free</CardTitle>
                <div className="text-4xl font-bold text-slate-900 mb-2">$0<span className="text-lg font-normal text-slate-500">/month</span></div>
                <CardDescription>Perfect for getting started</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>Limited receipts per month</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>Basic OCR and AI categorization</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>Dashboard analytics</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>CSV export</span>
                  </li>
                </ul>
                <Button 
                  className="w-full" 
                  variant="outline"
                  onClick={() => navigate('/app')}
                >
                  Start Free Demo
                </Button>
              </CardContent>
            </Card>

            {/* Pro Plan */}
            <Card className="border-2 border-blue-500 hover:border-blue-600 transition-colors relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-gradient-to-br from-blue-500 to-purple-500 text-white px-4 py-1 text-sm font-semibold">
                COMING SOON
              </div>
              <CardHeader className="text-center">
                <div className="text-sm font-semibold text-blue-600 mb-2">PRO</div>
                <CardTitle className="text-3xl mb-2">Pro</CardTitle>
                <div className="text-4xl font-bold text-slate-900 mb-2">$12<span className="text-lg font-normal text-slate-500">/month</span></div>
                <CardDescription>For power users and businesses</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="font-semibold">Unlimited receipts</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>Advanced AI analytics</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>Priority support</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>Custom integrations</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span>Team collaboration (coming soon)</span>
                  </li>
                </ul>
                <Button 
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700" 
                  onClick={() => navigate('/app')}
                >
                  Get Started
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="col-span-1">
              <div className="flex items-center space-x-2 mb-4">
                <Sparkles className="h-8 w-8 text-blue-400" />
                <span className="text-2xl font-bold">Lumina</span>
              </div>
              <p className="text-slate-400 text-sm">
                AI-powered expense management that saves you time and keeps you tax-ready.
              </p>
            </div>

            {/* Product Links */}
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>
                  <a href="#features" className="hover:text-white transition-colors">Features</a>
                </li>
                <li>
                  <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
                </li>
                <li>
                  <Link to="/app" className="hover:text-white transition-colors">Dashboard</Link>
                </li>
              </ul>
            </div>

            {/* Company Links */}
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>
                  <a href="#" className="hover:text-white transition-colors">About</a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">Contact</a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                </li>
              </ul>
            </div>

            {/* Support Links */}
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>
                  <Link to="/login" className="hover:text-white transition-colors">Login</Link>
                </li>
                <li>
                  <Link to="/app" className="hover:text-white transition-colors">Get Started</Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-800 mt-8 pt-8 text-center text-sm text-slate-400">
            <p>&copy; 2025 Lumina. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
