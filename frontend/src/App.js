import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Import Shadcn components
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Separator } from './components/ui/separator';
import { Alert, AlertDescription } from './components/ui/alert';
import { Progress } from './components/ui/progress';
import { Checkbox } from './components/ui/checkbox';
import { Popover, PopoverContent, PopoverTrigger } from './components/ui/popover';

// Import Lucide icons
import { 
  Upload, 
  FileText, 
  Calendar as CalendarIcon, 
  DollarSign, 
  Tag, 
  Download, 
  Trash2, 
  Edit, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Receipt,
  BarChart3,
  Settings,
  Plus,
  Search,
  Eye,
  ExternalLink,
  Filter,
  Image as FileImage,
  FileText as FilePdf,
  Bot,
  Sparkles
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LuminaApp />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

// Main Lumina Application
const LuminaApp = () => {
  const [receipts, setReceipts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadingReceipt, setUploadingReceipt] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [notification, setNotification] = useState(null);
  
  // Enhanced export filters
  const [exportFilters, setExportFilters] = useState({
    startDate: null,
    endDate: null,
    categories: []
  });
  const [showExportDialog, setShowExportDialog] = useState(false);
  
  // Receipt detail modal state
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const [showReceiptDetail, setShowReceiptDetail] = useState(false);

  // Fetch receipts from API with enhanced search
  const fetchReceipts = useCallback(async (search = '', category = '') => {
    try {
      setLoading(true);
      let url = `${API}/receipts`;
      const params = new URLSearchParams();
      
      if (search) params.append('search', search);
      if (category && category !== 'All') params.append('category', category);
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await axios.get(url);
      setReceipts(response.data);
    } catch (error) {
      console.error('Error fetching receipts:', error);
      showNotification('Failed to load receipts', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch categories from API
  const fetchCategories = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  }, []);

  // Show notification
  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  // Initialize data
  useEffect(() => {
    fetchReceipts();
    fetchCategories();
  }, [fetchCategories]); // Remove fetchReceipts from dependencies since it's handled by search effect

  // Upload receipt
  const handleReceiptUpload = async (file, category = 'Uncategorized') => {
    try {
      setUploadingReceipt(true);
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);

      const response = await axios.post(`${API}/receipts/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      showNotification('Receipt uploaded and processed successfully!', 'success');
      fetchReceipts();
      fetchCategories();
      
    } catch (error) {
      console.error('Error uploading receipt:', error);
      showNotification('Failed to upload receipt. Please try again.', 'error');
    } finally {
      setUploadingReceipt(false);
    }
  };

  // Update receipt category
  const updateReceiptCategory = async (receiptId, newCategory) => {
    try {
      await axios.put(`${API}/receipts/${receiptId}/category`, {
        category: newCategory
      });
      
      showNotification('Category updated successfully!', 'success');
      fetchReceipts();
      fetchCategories();
      
    } catch (error) {
      console.error('Error updating category:', error);
      showNotification('Failed to update category', 'error');
    }
  };

  // Delete receipt
  const deleteReceipt = async (receiptId) => {
    try {
      await axios.delete(`${API}/receipts/${receiptId}`);
      showNotification('Receipt deleted successfully!', 'success');
      fetchReceipts();
      fetchCategories();
    } catch (error) {
      console.error('Error deleting receipt:', error);
      showNotification('Failed to delete receipt', 'error');
    }
  };

  // Enhanced CSV export with filters
  const exportReceipts = async (filters = null) => {
    try {
      const response = await axios.post(`${API}/receipts/export/csv`, filters || {}, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'lumina_tax_export.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      showNotification('Tax-ready CSV exported successfully!', 'success');
      setShowExportDialog(false);
    } catch (error) {
      console.error('Error exporting receipts:', error);
      showNotification('Failed to export receipts', 'error');
    }
  };

  // View original receipt file
  const viewOriginalReceipt = (receiptId, filename) => {
    const fileUrl = `${BACKEND_URL}/api/receipts/${receiptId}/file`;
    window.open(fileUrl, '_blank');
  };

  // Open receipt detail modal
  const openReceiptDetail = (receipt) => {
    setSelectedReceipt(receipt);
    setShowReceiptDetail(true);
  };

  // Close receipt detail modal
  const closeReceiptDetail = () => {
    setSelectedReceipt(null);
    setShowReceiptDetail(false);
  };

  // Real-time search with debouncing
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchReceipts(searchTerm, selectedCategory);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, selectedCategory, fetchReceipts]);

  // Stats are calculated from current receipts (already filtered by search/category)
  // No need for client-side filtering since backend handles it

  // Calculate statistics
  const stats = {
    totalReceipts: receipts.length,
    processedReceipts: receipts.filter(r => r.processing_status === 'completed').length,
    totalAmount: receipts
      .filter(r => r.total_amount)
      .reduce((sum, r) => {
        const amount = parseFloat(r.total_amount.replace(/[$,]/g, '')) || 0;
        return sum + amount;
      }, 0),
    categories: categories.length
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Notification */}
      {notification && (
        <div className="fixed top-4 right-4 z-50">
          <Alert className={`${
            notification.type === 'error' ? 'border-red-500 bg-red-50' : 
            notification.type === 'success' ? 'border-green-500 bg-green-50' : 
            'border-blue-500 bg-blue-50'
          }`}>
            {notification.type === 'error' ? <AlertCircle className="h-4 w-4" /> : 
             notification.type === 'success' ? <CheckCircle className="h-4 w-4" /> : 
             <AlertCircle className="h-4 w-4" />}
            <AlertDescription>{notification.message}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Receipt className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Lumina
                </h1>
                <p className="text-sm text-slate-500">Intelligent Receipt Manager</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <UploadReceiptDialog onUpload={handleReceiptUpload} uploading={uploadingReceipt} />
              <ExportDialog 
                onExport={exportReceipts}
                disabled={receipts.length === 0}
                categories={categories}
                open={showExportDialog}
                onOpenChange={setShowExportDialog}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="receipts">Receipts</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatsCard
                title="Total Receipts"
                value={stats.totalReceipts}
                icon={FileText}
                gradient="from-blue-500 to-blue-600"
              />
              <StatsCard
                title="Processed"
                value={stats.processedReceipts}
                icon={CheckCircle}
                gradient="from-green-500 to-green-600"
              />
              <StatsCard
                title="Total Amount"
                value={`$${stats.totalAmount.toFixed(2)}`}
                icon={DollarSign}
                gradient="from-purple-500 to-purple-600"
              />
              <StatsCard
                title="Categories"
                value={stats.categories}
                icon={Tag}
                gradient="from-orange-500 to-orange-600"
              />
            </div>

            {/* Recent Receipts */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Receipts</CardTitle>
                <CardDescription>Your latest uploaded receipts</CardDescription>
              </CardHeader>
              <CardContent>
                {receipts.length === 0 ? (
                  <EmptyState onUpload={handleReceiptUpload} uploading={uploadingReceipt} />
                ) : (
                  <div className="space-y-4">
                    {receipts.slice(0, 5).map(receipt => (
                      <ReceiptCard
                        key={receipt.id}
                        receipt={receipt}
                        onCategoryUpdate={updateReceiptCategory}
                        onDelete={deleteReceipt}
                        onViewOriginal={viewOriginalReceipt}
                        onOpenDetail={openReceiptDetail}
                        categories={categories}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Receipts Tab */}
          <TabsContent value="receipts" className="space-y-6">
            {/* Filters */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        placeholder="Search receipts..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="w-full sm:w-[200px]">
                      <SelectValue placeholder="Filter by category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">All Categories</SelectItem>
                      {categories.map(category => (
                        <SelectItem key={category.name} value={category.name}>
                          {category.name} ({category.count})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Receipts List */}
            <Card>
              <CardHeader>
                <CardTitle>All Receipts ({receipts.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="animate-pulse">
                        <div className="h-20 bg-slate-200 rounded-lg"></div>
                      </div>
                    ))}
                  </div>
                ) : receipts.length === 0 ? (
                  <EmptyState onUpload={handleReceiptUpload} uploading={uploadingReceipt} />
                ) : (
                  <div className="space-y-4">
                    {receipts.map(receipt => (
                      <ReceiptCard
                        key={receipt.id}
                        receipt={receipt}
                        onCategoryUpdate={updateReceiptCategory}
                        onDelete={deleteReceipt}
                        onViewOriginal={viewOriginalReceipt}
                        onOpenDetail={openReceiptDetail}
                        categories={categories}
                        detailed
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Expense Analytics</CardTitle>
                <CardDescription>AI-powered insights and expense breakdown by category</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {categories.map(category => {
                    const categoryTotal = category.total_amount || 0;
                    const percentage = stats.totalAmount > 0 ? (categoryTotal / stats.totalAmount) * 100 : 0;

                    return (
                      <div key={category.name} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">{category.name}</span>
                            {category.name !== 'Uncategorized' && (
                              <Bot className="w-4 h-4 text-purple-500" title="AI Categorized" />
                            )}
                          </div>
                          <span className="text-sm text-slate-500">
                            ${categoryTotal.toFixed(2)} ({percentage.toFixed(1)}%) • {category.count} receipts
                          </span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    );
                  })}
                </div>
                
                {/* Additional Analytics */}
                <div className="mt-6 pt-6 border-t">
                  <h4 className="text-sm font-medium text-slate-700 mb-4">Quick Insights</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="bg-green-50 p-3 rounded-lg">
                      <div className="text-green-800 font-medium">Processing Accuracy</div>
                      <div className="text-green-600">
                        {receipts.length > 0 
                          ? Math.round((receipts.filter(r => r.confidence_score > 0.8).length / receipts.length) * 100) 
                          : 0}% high confidence
                      </div>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg">
                      <div className="text-purple-800 font-medium">AI Categorization</div>
                      <div className="text-purple-600">
                        {receipts.length > 0 
                          ? Math.round((receipts.filter(r => r.category !== 'Uncategorized').length / receipts.length) * 100) 
                          : 0}% auto-categorized
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Receipt Detail Modal */}
      {selectedReceipt && (
        <ReceiptDetailModal
          receipt={selectedReceipt}
          open={showReceiptDetail}
          onOpenChange={closeReceiptDetail}
          onViewOriginal={viewOriginalReceipt}
          onCategoryUpdate={updateReceiptCategory}
          onDelete={deleteReceipt}
          categories={categories}
        />
      )}
    </div>
  );
};

// Statistics Card Component
const StatsCard = ({ title, value, icon: Icon, gradient }) => (
  <Card className="relative overflow-hidden">
    <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-10`}></div>
    <CardContent className="p-6 relative">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-600">{title}</p>
          <p className="text-2xl font-bold text-slate-900">{value}</p>
        </div>
        <Icon className={`h-8 w-8 text-white bg-gradient-to-br ${gradient} p-1.5 rounded-lg`} />
      </div>
    </CardContent>
  </Card>
);

// Receipt Card Component with enhanced features
const ReceiptCard = ({ receipt, onCategoryUpdate, onDelete, onViewOriginal, categories, detailed = false }) => {
  const [isUpdating, setIsUpdating] = useState(false);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Processed
        </Badge>;
      case 'processing':
        return <Badge className="bg-blue-100 text-blue-800">
          <Clock className="w-3 h-3 mr-1" />
          Processing
        </Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">
          <AlertCircle className="w-3 h-3 mr-1" />
          Failed
        </Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Pending</Badge>;
    }
  };

  const getFileIcon = (filename) => {
    const extension = filename.split('.').pop().toLowerCase();
    if (extension === 'pdf') {
      return <FilePdf className="h-4 w-4 text-red-500" />;
    }
    return <FileImage className="h-4 w-4 text-blue-500" />;
  };

  const getCategoryBadge = (category) => {
    if (category === 'Uncategorized') {
      return <span className="text-xs text-slate-500">Uncategorized</span>;
    }
    return (
      <div className="flex items-center space-x-1">
        <Bot className="w-3 h-3 text-purple-500" />
        <span className="text-xs text-purple-700 font-medium">{category}</span>
      </div>
    );
  };

  const handleCategoryUpdate = async (newCategory) => {
    setIsUpdating(true);
    await onCategoryUpdate(receipt.id, newCategory);
    setIsUpdating(false);
  };

  return (
    <Card className="hover:shadow-md transition-all hover:border-blue-200">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              {getFileIcon(receipt.filename)}
              <span className="font-medium text-slate-900 truncate">{receipt.filename}</span>
              {getStatusBadge(receipt.processing_status)}
              {receipt.category !== 'Uncategorized' && (
                <Sparkles className="w-3 h-3 text-purple-500" title="Auto-categorized" />
              )}
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-sm text-slate-600">
              {receipt.merchant_name && (
                <div className="flex items-center space-x-1">
                  <span className="font-medium">Merchant:</span>
                  <span>{receipt.merchant_name}</span>
                </div>
              )}
              {receipt.receipt_date && (
                <div className="flex items-center space-x-1">
                  <CalendarIcon className="h-3 w-3" />
                  <span>{receipt.receipt_date}</span>
                </div>
              )}
              {receipt.total_amount && (
                <div className="flex items-center space-x-1">
                  <DollarSign className="h-3 w-3" />
                  <span className="font-medium">{receipt.total_amount}</span>
                </div>
              )}
              <div className="flex items-center space-x-1">
                <Tag className="h-3 w-3" />
                <Select
                  value={receipt.category}
                  onValueChange={handleCategoryUpdate}
                  disabled={isUpdating}
                >
                  <SelectTrigger className="h-6 text-xs border-none p-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Auto-Detect">🤖 Auto-Detect</SelectItem>
                    <SelectItem value="Meals & Entertainment">🍽️ Meals & Entertainment</SelectItem>
                    <SelectItem value="Groceries">🛒 Groceries</SelectItem>
                    <SelectItem value="Transportation & Fuel">🚗 Transportation & Fuel</SelectItem>
                    <SelectItem value="Office Supplies">📎 Office Supplies</SelectItem>
                    <SelectItem value="Shopping">🛍️ Shopping</SelectItem>
                    <SelectItem value="Utilities">⚡ Utilities</SelectItem>
                    <SelectItem value="Healthcare">🏥 Healthcare</SelectItem>
                    <SelectItem value="Travel">✈️ Travel</SelectItem>
                    <SelectItem value="Uncategorized">📂 Uncategorized</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {detailed && receipt.items && receipt.items.length > 0 && (
              <div className="mt-3 pt-3 border-t">
                <p className="text-sm font-medium text-slate-700 mb-2">Items:</p>
                <div className="space-y-1">
                  {receipt.items.slice(0, 3).map((item, index) => (
                    <div key={index} className="flex justify-between text-xs text-slate-600">
                      <span>{item.description}</span>
                      {item.amount && <span>{item.amount}</span>}
                    </div>
                  ))}
                  {receipt.items.length > 3 && (
                    <p className="text-xs text-slate-500">+{receipt.items.length - 3} more items</p>
                  )}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            {receipt.confidence_score && (
              <div className="text-xs text-slate-500">
                {Math.round(receipt.confidence_score * 100)}%
              </div>
            )}
            
            {/* View Original Receipt Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewOriginal(receipt.id, receipt.filename)}
              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
              title="View original receipt"
            >
              <Eye className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(receipt.id)}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Enhanced Upload Receipt Dialog with PDF support
const UploadReceiptDialog = ({ onUpload, uploading }) => {
  const [open, setOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [category, setCategory] = useState('Auto-Detect');
  const [dragActive, setDragActive] = useState(false);

  const handleFileSelect = (file) => {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'application/pdf'];
    if (file && allowedTypes.includes(file.type)) {
      setSelectedFile(file);
    } else {
      alert('Please select a valid image file (JPG, PNG, TIFF, BMP) or PDF file.');
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      await onUpload(selectedFile, category);
      setOpen(false);
      setSelectedFile(null);
      setCategory('Auto-Detect');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const getFileIcon = () => {
    if (!selectedFile) return <Upload className="mx-auto h-8 w-8 text-slate-400" />;
    
    if (selectedFile.type === 'application/pdf') {
      return <FilePdf className="mx-auto h-8 w-8 text-red-500" />;
    }
    return <FileImage className="mx-auto h-8 w-8 text-blue-500" />;
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Upload Receipt
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Receipt</DialogTitle>
          <DialogDescription>
            Upload an image or PDF of your receipt for automatic OCR processing and AI categorization.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : selectedFile
                ? 'border-green-500 bg-green-50'
                : 'border-slate-300 hover:border-slate-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="space-y-2">
                {getFileIcon()}
                <p className="text-sm font-medium">{selectedFile.name}</p>
                <p className="text-xs text-slate-500">
                  {selectedFile.type === 'application/pdf' ? 'PDF Document' : 'Image File'} • {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedFile(null)}
                >
                  Choose Different File
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {getFileIcon()}
                <div>
                  <Label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-600 font-medium">Click to upload</span>
                    <span className="text-slate-600"> or drag and drop</span>
                  </Label>
                  <Input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    accept="image/*,.pdf"
                    onChange={(e) => handleFileSelect(e.target.files[0])}
                  />
                </div>
                <p className="text-xs text-slate-500">Supports JPG, PNG, and PDF files up to 10MB</p>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Auto-Detect">
                  <div className="flex items-center space-x-2">
                    <Bot className="w-4 h-4 text-purple-500" />
                    <span>Auto-Detect (AI Powered)</span>
                  </div>
                </SelectItem>
                <Separator />
                <SelectItem value="Meals & Entertainment">🍽️ Meals & Entertainment</SelectItem>
                <SelectItem value="Groceries">🛒 Groceries</SelectItem>
                <SelectItem value="Transportation & Fuel">🚗 Transportation & Fuel</SelectItem>
                <SelectItem value="Office Supplies">📎 Office Supplies</SelectItem>
                <SelectItem value="Shopping">🛍️ Shopping</SelectItem>
                <SelectItem value="Utilities">⚡ Utilities</SelectItem>
                <SelectItem value="Healthcare">🏥 Healthcare</SelectItem>
                <SelectItem value="Travel">✈️ Travel</SelectItem>
                <SelectItem value="Uncategorized">📂 Uncategorized</SelectItem>
              </SelectContent>
            </Select>
            {category === 'Auto-Detect' && (
              <p className="text-xs text-purple-600 flex items-center space-x-1">
                <Sparkles className="w-3 h-3" />
                <span>AI will analyze the merchant and content to suggest the best category</span>
              </p>
            )}
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setOpen(false)} disabled={uploading}>
              Cancel
            </Button>
            <Button onClick={handleUpload} disabled={!selectedFile || uploading}>
              {uploading ? 'Processing...' : 'Upload & Process'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Enhanced Export Dialog with Tax Preparation Features
const ExportDialog = ({ onExport, disabled, categories, open, onOpenChange }) => {
  const [filters, setFilters] = useState({
    startDate: null,
    endDate: null,
    categories: []
  });

  const handleExport = () => {
    const exportFilters = {
      start_date: filters.startDate?.toISOString().split('T')[0],
      end_date: filters.endDate?.toISOString().split('T')[0],
      categories: filters.categories.length > 0 ? filters.categories : null
    };
    
    onExport(exportFilters);
  };

  const toggleCategory = (categoryName) => {
    setFilters(prev => ({
      ...prev,
      categories: prev.categories.includes(categoryName)
        ? prev.categories.filter(c => c !== categoryName)
        : [...prev.categories, categoryName]
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
        >
          <Download className="w-4 h-4 mr-2" />
          Tax Export
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Export Tax-Ready CSV</DialogTitle>
          <DialogDescription>
            Generate a comprehensive CSV report with category summaries for tax preparation and accounting.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Date Range Selection */}
          <div className="space-y-2">
            <Label>Date Range (Optional)</Label>
            <div className="flex space-x-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    {filters.startDate ? filters.startDate.toLocaleDateString() : 'Start Date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Input
                    type="date"
                    value={filters.startDate ? filters.startDate.toISOString().split('T')[0] : ''}
                    onChange={(e) => setFilters(prev => ({ 
                      ...prev, 
                      startDate: e.target.value ? new Date(e.target.value) : null 
                    }))}
                  />
                </PopoverContent>
              </Popover>
              
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    {filters.endDate ? filters.endDate.toLocaleDateString() : 'End Date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Input
                    type="date"
                    value={filters.endDate ? filters.endDate.toISOString().split('T')[0] : ''}
                    onChange={(e) => setFilters(prev => ({ 
                      ...prev, 
                      endDate: e.target.value ? new Date(e.target.value) : null 
                    }))}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Category Selection */}
          <div className="space-y-2">
            <Label>Categories (Optional - All if none selected)</Label>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {categories.map((category) => (
                <div key={category.name} className="flex items-center space-x-2">
                  <Checkbox
                    id={category.name}
                    checked={filters.categories.includes(category.name)}
                    onCheckedChange={() => toggleCategory(category.name)}
                  />
                  <Label htmlFor={category.name} className="text-sm cursor-pointer">
                    {category.name} ({category.count} receipts - ${category.total_amount?.toFixed(2) || '0.00'})
                  </Label>
                </div>
              ))}
            </div>
          </div>

          {/* Export Info */}
          <div className="bg-blue-50 p-3 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900">Tax-Ready Features:</h4>
            <ul className="text-xs text-blue-800 mt-1 space-y-1">
              <li>• Category summary with totals</li>
              <li>• Detailed transaction records</li>
              <li>• Confidence scores for audit trails</li>
              <li>• Professional formatting for accountants</li>
            </ul>
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Empty State Component
const EmptyState = ({ onUpload, uploading }) => (
  <div className="text-center py-12">
    <Receipt className="mx-auto h-12 w-12 text-slate-400 mb-4" />
    <h3 className="text-lg font-medium text-slate-900 mb-2">No receipts yet</h3>
    <p className="text-slate-600 mb-6">
      Upload your first receipt to get started with automated expense tracking.
    </p>
    <UploadReceiptDialog onUpload={onUpload} uploading={uploading} />
  </div>
);

export default App;