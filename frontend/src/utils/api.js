/*
 * LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
 * API Utilities with Automatic Backend Detection and Retry Logic
 * 
 * Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
 * PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
 */

import axios from 'axios';

/**
 * Automatically detect the correct backend URL based on environment
 */
const detectBackendURL = () => {
  // FORCE DEBUG: Print all environment variables
  console.log('🔍 Environment Debug:');
  console.log('  NODE_ENV:', process.env.NODE_ENV);
  console.log('  REACT_APP_BACKEND_URL:', process.env.REACT_APP_BACKEND_URL);
  console.log('  All env vars:', Object.keys(process.env).filter(key => key.startsWith('REACT_APP')));
  
  // Check if we have an explicit backend URL from environment
  if (process.env.REACT_APP_BACKEND_URL) {
    console.log(`🔧 Using environment URL: ${process.env.REACT_APP_BACKEND_URL}`);
    return process.env.REACT_APP_BACKEND_URL;
  }

  // FALLBACK: Force preview URL if environment variable isn't working
  const hostname = window.location.hostname;
  console.log(`🔍 Hostname detected: ${hostname}`);
  
  if (hostname.includes('expense-ai-5.preview.emergentagent.com')) {
    const forcedUrl = 'https://expense-ai-5.preview.emergentagent.com';
    console.log(`🚨 FORCED URL (env var failed): ${forcedUrl}`);
    return forcedUrl;
  }
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // Local development
    console.log(`🏠 Local development detected`);
    return 'http://localhost:8001';
  } else if (hostname.includes('emergent.host') || hostname.includes('emergentagent.com')) {
    // Production on Emergent platform - use same hostname as frontend
    const backendUrl = `https://${hostname}`;
    console.log(`🌐 Emergent platform detected, using: ${backendUrl}`);
    return backendUrl;
  } else {
    // Fallback for custom domains
    const backendUrl = `https://api.${hostname}`;
    console.log(`🔗 Custom domain detected, using: ${backendUrl}`);
    return backendUrl;
  }
};

// Configure axios with automatic backend detection
const BACKEND_URL = detectBackendURL();
export const API_BASE_URL = `${BACKEND_URL}/api`;

console.log(`🔗 API Base URL: ${API_BASE_URL}`);

// Create axios instance with default configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Retry logic for failed requests
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export const retryRequest = async (requestFn, maxRetries = 3, delay = 2000) => {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`🔄 API Request attempt ${attempt}/${maxRetries}`);
      const result = await requestFn();
      console.log(`✅ API Request successful on attempt ${attempt}`);
      return result;
    } catch (error) {
      lastError = error;
      console.warn(`❌ API Request failed on attempt ${attempt}:`, error.message);
      
      // Don't retry on client errors (4xx) except for 408, 429
      if (error.response && error.response.status >= 400 && error.response.status < 500) {
        if (error.response.status !== 408 && error.response.status !== 429) {
          throw error;
        }
      }
      
      if (attempt < maxRetries) {
        console.log(`⏳ Retrying in ${delay}ms...`);
        await sleep(delay);
      }
    }
  }
  
  throw lastError;
};

/**
 * Enhanced API methods with retry logic
 */
export const api = {
  // GET request with retry
  get: async (url, config = {}) => {
    return retryRequest(() => apiClient.get(url, config));
  },

  // POST request with retry
  post: async (url, data = {}, config = {}) => {
    return retryRequest(() => apiClient.post(url, data, config));
  },

  // PUT request with retry
  put: async (url, data = {}, config = {}) => {
    return retryRequest(() => apiClient.put(url, data, config));
  },

  // DELETE request with retry
  delete: async (url, config = {}) => {
    return retryRequest(() => apiClient.delete(url, config));
  },

  // Special method for file uploads (no retry on large files)
  upload: async (url, formData, config = {}) => {
    const uploadConfig = {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config.headers,
      },
      timeout: 120000, // 2 minutes for uploads
    };
    
    return apiClient.post(url, formData, uploadConfig);
  }
};

/**
 * Health check function to test API connectivity
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/');
    return {
      success: true,
      url: API_BASE_URL,
      message: response.data?.message || 'API is healthy'
    };
  } catch (error) {
    return {
      success: false,
      url: API_BASE_URL,
      error: error.message
    };
  }
};

/**
 * Error handling utility
 */
export const getErrorMessage = (error) => {
  if (error.response) {
    // Server responded with error status
    return error.response.data?.detail || error.response.data?.message || `Server error: ${error.response.status}`;
  } else if (error.request) {
    // Network error
    return 'Network error: Unable to connect to server. Please check your internet connection.';
  } else {
    // Other error
    return error.message || 'An unexpected error occurred.';
  }
};

export default api;