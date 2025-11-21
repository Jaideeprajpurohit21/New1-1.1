/*
 * LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
 * API Utilities with Automatic Backend Detection and Retry Logic
 * 
 * Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
 * PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
 */

import axios from 'axios';

/**
 * Get backend URL from environment variables
 */
const getBackendURL = () => {
  // Use environment variable (prioritize REACT_APP_BACKEND_URL)
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  
  if (envUrl) {
    console.log(`🔧 Using environment URL: ${envUrl}`);
    return envUrl;
  }

  // Fallback for development
  if (process.env.NODE_ENV === 'development') {
    const devUrl = 'http://localhost:8000';
    console.log(`🏠 Using development fallback: ${devUrl}`);
    return devUrl;
  }

  // Production fallback (should not reach here if env vars are set correctly)
  throw new Error('REACT_APP_BACKEND_URL environment variable is required for production');
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