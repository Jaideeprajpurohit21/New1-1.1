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
 * PUBLIC DEMO MODE - Use current domain
 */
const getBackendURL = () => {
  // Priority 1: Environment variable (set during build)
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  
  if (envUrl && envUrl !== 'undefined' && envUrl.startsWith('http')) {
    console.log(`🔧 Using environment URL: ${envUrl}`);
    return envUrl;
  }

  // Priority 2: Use current window location origin (production fallback)
  if (typeof window !== 'undefined') {
    const currentOrigin = window.location.origin;
    console.log(`🌐 Using window.location.origin: ${currentOrigin}`);
    return currentOrigin;
  }

  // Priority 3: Fallback - use window.location.origin for deployed apps
  console.warn('⚠️ No backend URL found, using window.location.origin as fallback');
  return typeof window !== 'undefined' ? window.location.origin : 'https://luminaai.ai';
};

                                       // Configure axios with environment-based backend URL
                                       const BACKEND_URL = getBackendURL();
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