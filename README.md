# Lumina - AI-Powered Receipt Management System

![Lumina Logo](https://via.placeholder.com/800x200/4F46E5/FFFFFF?text=LUMINA+-+AI-POWERED+RECEIPT+MANAGEMENT)

Lumina is a sophisticated SaaS application that transforms receipts into categorized, accounting-ready data using advanced AI and machine learning technologies.

## 🚀 Features

- **AI-Powered OCR**: Extract text from receipts with high accuracy using EasyOCR
- **Smart Categorization**: ML-powered automatic expense categorization 
- **Multi-User Support**: Full authentication system with JWT and OAuth
- **Receipt Management**: Upload, view, edit, and organize receipts
- **Export Functionality**: Export data to CSV for accounting software
- **Search & Filter**: Advanced search and filtering capabilities
- **Mobile-Friendly**: Responsive design for all devices

## 🏗 Architecture

```
Lumina/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main application server
│   ├── auth.py            # Authentication module
│   ├── auth_routes.py     # Auth API endpoints
│   ├── config.py          # Configuration management
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile        # Backend containerization
├── frontend/              # React frontend
│   ├── src/              # Source code
│   ├── package.json      # Node.js dependencies
│   └── public/           # Static assets
└── docs/                 # Documentation
```

## 📋 Prerequisites

Before deploying Lumina, ensure you have:

- MongoDB Atlas account (free tier available)
- Railway account (for backend deployment)
- Vercel account (for frontend deployment)
- Git repository (GitHub, GitLab, or Bitbucket)

---

## Overview

Lumina is an advanced AI-powered SaaS application designed for automated expense management, featuring:

- **Intelligent OCR Processing**: Advanced receipt text extraction with GPU acceleration
- **AI-Powered Categorization**: Automatic expense categorization using machine learning
- **Comprehensive Receipt Management**: Upload, process, and organize receipts with detailed views
- **Tax-Ready Exports**: Professional CSV exports formatted for accounting and tax preparation
- **Advanced Search**: Real-time search across all receipt data
- **Multi-Format Support**: Handle images (JPG, PNG, TIFF, BMP) and PDF receipts

## 🔒 Security & Compliance

- Enterprise-grade security measures
- Secure file storage with audit trails
- Encrypted data transmission
- GDPR and compliance-ready data handling

## 🛡️ Legal Notice

### COPYRIGHT PROTECTION
This software and all associated materials are protected by copyright law. The software contains confidential and proprietary information that is the exclusive property of Jaideep Singh Rajpurohit.

### TRADE SECRET PROTECTION  
This software contains valuable trade secrets and proprietary algorithms developed by Jaideep Singh Rajpurohit. Any unauthorized disclosure or use of these trade secrets is prohibited.

### LICENSING
This software is available only under a proprietary license agreement. See [LICENSE.md](LICENSE.md) for complete terms and conditions.

## 🗄 Database Setup (MongoDB Atlas)

### Step 1: Create MongoDB Atlas Cluster

1. **Sign up for MongoDB Atlas**: Visit [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)

2. **Create a new cluster**:
   - Choose the **FREE** shared cluster
   - Select your preferred cloud provider and region
   - Name your cluster (e.g., `lumina-cluster`)

3. **Create database user**:
   - Go to **Database Access** → **Add New Database User**
   - Choose **Password** authentication
   - Username: `lumina-admin` (or your preference)
   - Generate a strong password and save it securely
   - Grant **Read and Write** access to any database

4. **Configure network access**:
   - Go to **Network Access** → **Add IP Address**
   - Click **Allow Access from Anywhere** (0.0.0.0/0) for simplicity
   - Or add specific IPs for better security

5. **Get connection string**:
   - Go to **Clusters** → **Connect** → **Connect your application**
   - Copy the connection string (it looks like):
   ```
   mongodb+srv://<username>:<password>@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 2: Create Database and Collections

The application will automatically create the required collections when it starts:
- `users` - User account information
- `user_sessions` - Authentication sessions  
- `receipts` - Receipt data and metadata

## 🖥 Backend Deployment (Railway)

### Step 1: Prepare Repository

1. **Push your code to Git**:
   ```bash
   git add .
   git commit -m "Prepare for production deployment"
   git push origin main
   ```

### Step 2: Deploy to Railway

1. **Sign up for Railway**: Visit [railway.app](https://railway.app)

2. **Create new project**:
   - Click **New Project** → **Deploy from GitHub repo**
   - Select your repository
   - Railway will detect the Dockerfile automatically

3. **Configure environment variables**:
   Go to your project → **Variables** and add:

   ```bash
   # MongoDB Configuration
   MONGODB_URI=mongodb+srv://lumina-admin:YOUR_PASSWORD@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=lumina_production
   
   # JWT Configuration (generate a secure random string)
   JWT_SECRET=your-super-secret-jwt-key-make-it-at-least-64-characters-long
   
   # CORS Configuration  
   FRONTEND_ORIGIN=https://your-app-name.vercel.app
   
   # Server Configuration
   PORT=8000
   HOST=0.0.0.0
   ENVIRONMENT=production
   ```

4. **Deploy**:
   - Railway will automatically build and deploy your application
   - Note the deployment URL (e.g., `https://your-app.railway.app`)

### Step 3: Verify Backend Deployment

Test your backend API:
```bash
curl https://your-app.railway.app/api/
```

Expected response:
```json
{
  "message": "Lumina Enhanced Receipt OCR API",
  "version": "2.0.0", 
  "status": "operational"
}
```

## 🌐 Frontend Deployment (Vercel)

### Step 1: Update Environment Variables

1. **Update production environment**:
   Edit `/frontend/.env.production`:
   ```bash
   REACT_APP_BACKEND_URL=https://your-app.railway.app
   REACT_APP_ENV=production
   GENERATE_SOURCEMAP=false
   ```

### Step 2: Deploy to Vercel

1. **Sign up for Vercel**: Visit [vercel.com](https://vercel.com)

2. **Create new project**:
   - Click **New Project** → **Import Git Repository**
   - Select your repository
   - Set **Framework Preset**: Create React App
   - Set **Root Directory**: `frontend`

3. **Configure build settings**:
   ```bash
   # Build Command
   npm run build
   
   # Output Directory  
   build
   
   # Install Command
   npm install
   ```

4. **Add environment variables**:
   In project settings → **Environment Variables**:
   ```bash
   REACT_APP_BACKEND_URL=https://your-app.railway.app
   REACT_APP_ENV=production
   ```

5. **Deploy**:
   - Vercel will build and deploy automatically
   - Note your deployment URL (e.g., `https://lumina.vercel.app`)

### Step 3: Update Backend CORS

Update your Railway environment variables:
```bash
FRONTEND_ORIGIN=https://your-actual-vercel-url.vercel.app
```

Redeploy the backend after updating the CORS origin.

## 🔧 Local Development Setup

### Backend Setup

1. **Clone repository**:
   ```bash
   git clone <your-repository-url>
   cd lumina/backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Run backend**:
   ```bash
   python server.py
   ```

### Frontend Setup

1. **Navigate to frontend**:
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with local backend URL
   ```

4. **Run frontend**:
   ```bash
   npm start
   ```

## 🚨 Troubleshooting

### Common Issues

**1. CORS Errors**
```
Access to XMLHttpRequest blocked by CORS policy
```
**Solution**: Verify `FRONTEND_ORIGIN` environment variable matches your Vercel URL exactly.

**2. Database Connection Failed**
```
MongoServerError: Authentication failed
```
**Solution**: Check MongoDB Atlas connection string, username, and password.

**3. JWT Authentication Errors**
```
Could not validate credentials
```
**Solution**: Ensure `JWT_SECRET` is set and consistent across deployments.

## 🔐 LEGAL & LICENSING INFORMATION

---

## ⚖️ LEGAL DISCLAIMER

THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND. JAIDEEP SINGH RAJPUROHIT SHALL NOT BE LIABLE FOR ANY DAMAGES ARISING FROM THE USE OF THIS SOFTWARE.

**For licensing inquiries contact: legal@luminatech.com**

---

**CONFIDENTIAL AND PROPRIETARY - NOT FOR DISTRIBUTION**