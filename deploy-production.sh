#!/bin/bash

# LUMINA - Production Deployment Script
# Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.

set -e

echo "🚀 Starting Lumina Production Deployment..."

# Navigate to frontend directory
cd /app/frontend

# Install dependencies (if needed)
echo "📦 Installing dependencies..."
yarn install --frozen-lockfile

# Set production environment
echo "🌐 Setting production environment..."
export NODE_ENV=production
export REACT_APP_ENV=production

# Build for production
echo "🔨 Building production bundle..."
yarn build

echo "✅ Production build completed!"
echo ""
echo "📋 Deployment Summary:"
echo "   - Environment: Production"
echo "   - Backend URL: https://expensify-ai.emergent.host"
echo "   - Auto-retry: 3 attempts with 2s delay"
echo "   - Error handling: Enhanced user-friendly messages"
echo "   - Build output: /app/frontend/build/"
echo ""
echo "🎯 Next Steps:"
echo "   1. Upload the /app/frontend/build/ directory to your production server"
echo "   2. Configure your web server to serve the static files"
echo "   3. Ensure the backend API is accessible at https://expensify-ai.emergent.host"
echo ""
echo "🌟 Your Lumina app is ready for production!"

# Optional: Create a deployment package
if [ "$1" = "--package" ]; then
    echo "📦 Creating deployment package..."
    cd /app/frontend
    tar -czf lumina-production-$(date +%Y%m%d-%H%M%S).tar.gz build/
    echo "✅ Deployment package created!"
fi