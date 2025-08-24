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

// Import Lucide icons
import { 
  Upload, 
  FileText, 
  Calendar, 
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
  Search
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

  // Fetch receipts from API
  const fetchReceipts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/receipts`);
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
  }, [fetchReceipts, fetchCategories]);

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

  // Export receipts as CSV
  const exportReceipts = async () => {
    try {
      const response = await axios.get(`${API}/receipts/export/csv`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'lumina_receipts.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      showNotification('Receipts exported successfully!', 'success');
    } catch (error) {
      console.error('Error exporting receipts:', error);
      showNotification('Failed to export receipts', 'error');
    }
  };

  // Filter receipts
  const filteredReceipts = receipts.filter(receipt => {
    const matchesCategory = selectedCategory === 'All' || receipt.category === selectedCategory;
    const matchesSearch = receipt.merchant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         receipt.filename?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

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
              <Button
                variant="outline"
                size="sm"
                onClick={exportReceipts}
                disabled={receipts.length === 0}
              >
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
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
                <CardTitle>All Receipts ({filteredReceipts.length})</CardTitle>
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
                ) : filteredReceipts.length === 0 ? (
                  <EmptyState onUpload={handleReceiptUpload} uploading={uploadingReceipt} />
                ) : (
                  <div className="space-y-4">
                    {filteredReceipts.map(receipt => (
                      <ReceiptCard
                        key={receipt.id}
                        receipt={receipt}
                        onCategoryUpdate={updateReceiptCategory}
                        onDelete={deleteReceipt}
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
                <CardDescription>Breakdown of your expenses by category</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {categories.map(category => {
                    const categoryReceipts = receipts.filter(r => r.category === category.name);
                    const categoryTotal = categoryReceipts.reduce((sum, r) => {
                      const amount = parseFloat(r.total_amount?.replace(/[$,]/g, '') || '0');
                      return sum + amount;
                    }, 0);
                    const percentage = stats.totalAmount > 0 ? (categoryTotal / stats.totalAmount) * 100 : 0;

                    return (
                      <div key={category.name} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">{category.name}</span>
                          <span className="text-sm text-slate-500">
                            ${categoryTotal.toFixed(2)} ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
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

// Receipt Card Component
const ReceiptCard = ({ receipt, onCategoryUpdate, onDelete, categories, detailed = false }) => {
  const [isUpdating, setIsUpdating] = useState(false);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">Processed</Badge>;
      case 'processing':
        return <Badge className="bg-blue-100 text-blue-800">Processing</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Pending</Badge>;
    }
  };

  const handleCategoryUpdate = async (newCategory) => {
    setIsUpdating(true);
    await onCategoryUpdate(receipt.id, newCategory);
    setIsUpdating(false);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <FileText className="h-4 w-4 text-slate-400" />
              <span className="font-medium text-slate-900 truncate">{receipt.filename}</span>
              {getStatusBadge(receipt.processing_status)}
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
                  <Calendar className="h-3 w-3" />
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
                    <SelectItem value="Uncategorized">Uncategorized</SelectItem>
                    <SelectItem value="Travel">Travel</SelectItem>
                    <SelectItem value="Meals">Meals</SelectItem>
                    <SelectItem value="Office Supplies">Office Supplies</SelectItem>
                    <SelectItem value="Entertainment">Entertainment</SelectItem>
                    <SelectItem value="Transportation">Transportation</SelectItem>
                    <SelectItem value="Utilities">Utilities</SelectItem>
                    <SelectItem value="Healthcare">Healthcare</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
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

// Upload Receipt Dialog Component
const UploadReceiptDialog = ({ onUpload, uploading }) => {
  const [open, setOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [category, setCategory] = useState('Uncategorized');
  const [dragActive, setDragActive] = useState(false);

  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      await onUpload(selectedFile, category);
      setOpen(false);
      setSelectedFile(null);
      setCategory('Uncategorized');
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
            Upload an image of your receipt to extract expense data automatically.
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
                <CheckCircle className="mx-auto h-8 w-8 text-green-600" />
                <p className="text-sm font-medium">{selectedFile.name}</p>
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
                <Upload className="mx-auto h-8 w-8 text-slate-400" />
                <div>
                  <Label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-600 font-medium">Click to upload</span>
                    <span className="text-slate-600"> or drag and drop</span>
                  </Label>
                  <Input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => handleFileSelect(e.target.files[0])}
                  />
                </div>
                <p className="text-xs text-slate-500">PNG, JPG up to 10MB</p>
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
                <SelectItem value="Uncategorized">Uncategorized</SelectItem>
                <SelectItem value="Travel">Travel</SelectItem>
                <SelectItem value="Meals">Meals</SelectItem>
                <SelectItem value="Office Supplies">Office Supplies</SelectItem>
                <SelectItem value="Entertainment">Entertainment</SelectItem>
                <SelectItem value="Transportation">Transportation</SelectItem>
                <SelectItem value="Utilities">Utilities</SelectItem>
                <SelectItem value="Healthcare">Healthcare</SelectItem>
                <SelectItem value="Other">Other</SelectItem>
              </SelectContent>
            </Select>
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