/*
 * LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
 * Frontend Application Entry Point
 * 
 * Copyright (c) 2024-2025 Lumina Technologies. All rights reserved.
 * 
 * PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
 * This software contains confidential and proprietary information of Lumina Technologies.
 * Any reproduction, distribution, or transmission of this software, in whole or in part,
 * without the prior written consent of Lumina Technologies is strictly prohibited.
 * 
 * Trade secrets contained herein are protected under applicable laws.
 * Unauthorized disclosure may result in civil and criminal prosecution.
 * 
 * For licensing information, contact: legal@luminatech.com
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);