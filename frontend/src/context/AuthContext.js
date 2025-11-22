import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Auth Context
const AuthContext = createContext({});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState(null);

  // Import API base URL from environment - MUST be set correctly
  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
  
  console.log('🔗 AuthContext API_BASE_URL:', API_BASE_URL);

  // Configure axios defaults
  useEffect(() => {
    if (accessToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [accessToken]);

  // Check for existing session on app start
  useEffect(() => {
    checkExistingSession();
  }, []);

  // Check for session ID in URL fragment (OAuth redirect)
  useEffect(() => {
    const hash = window.location.hash;
    if (hash.includes('session_id=')) {
      const sessionId = hash.split('session_id=')[1].split('&')[0];
      if (sessionId) {
        processOAuthSession(sessionId);
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  }, []);

  const checkExistingSession = async () => {
    try {
      // Check if we have a valid session
      const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
        withCredentials: true
      });
      
      if (response.data) {
        setUser(response.data);
        // Get access token if available in response headers or set a flag
        const token = response.headers['authorization'] || 'session-based';
        setAccessToken(token);
      }
    } catch (error) {
      console.log('No existing session found');
      // Clear any existing auth state
      setUser(null);
      setAccessToken(null);
    } finally {
      setLoading(false);
    }
  };

  const processOAuthSession = async (sessionId) => {
    try {
      setLoading(true);
      
      const response = await axios.post(`${API_BASE_URL}/api/auth/oauth/session`, {
        session_id: sessionId
      }, {
        withCredentials: true
      });

      if (response.data) {
        setUser(response.data.user);
        setAccessToken(response.data.access_token);
        
        // Redirect to dashboard
        window.location.href = '/';
      }
    } catch (error) {
      console.error('OAuth session processing failed:', error);
      setLoading(false);
    }
  };

  const signup = async (email, password, name = '') => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/signup`, {
        email,
        password,
        name
      }, {
        withCredentials: true
      });

      if (response.data) {
        setUser(response.data.user);
        setAccessToken(response.data.access_token);
        return { success: true, user: response.data.user };
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Signup failed';
      return { success: false, error: message };
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        email,
        password
      }, {
        withCredentials: true
      });

      if (response.data) {
        setUser(response.data.user);
        setAccessToken(response.data.access_token);
        return { success: true, user: response.data.user };
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/auth/logout`, {}, {
        withCredentials: true
      });
    } catch (error) {
      console.log('Logout request failed, but clearing local state');
    } finally {
      // Clear local state regardless
      setUser(null);
      setAccessToken(null);
      delete axios.defaults.headers.common['Authorization'];
      
      // Redirect to login
      window.location.href = '/login';
    }
  };

  const googleLogin = () => {
    // Redirect to Emergent OAuth
    const redirectUrl = encodeURIComponent(window.location.origin);
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  const refreshUser = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
        withCredentials: true
      });
      
      if (response.data) {
        setUser(response.data);
        return response.data;
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails, user might be logged out
      setUser(null);
      setAccessToken(null);
    }
  };

  const value = {
    user,
    loading,
    accessToken,
    signup,
    login,
    logout,
    googleLogin,
    refreshUser,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};