#!/bin/bash

# Lumina Production Deployment Script
# This script helps prepare the application for production deployment

set -e  # Exit on any error

echo "🚀 Lumina Production Deployment Preparation"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install git first."
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        print_error "Not in a git repository. Please initialize git first:"
        echo "  git init"
        echo "  git add ."
        echo "  git commit -m 'Initial commit'"
        exit 1
    fi
    
    print_success "Requirements check passed"
}

# Generate secure JWT secret
generate_jwt_secret() {
    print_status "Generating secure JWT secret..."
    
    # Generate a random 64-character string
    JWT_SECRET=$(openssl rand -hex 32)
    
    if [ -z "$JWT_SECRET" ]; then
        # Fallback if openssl is not available
        JWT_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    fi
    
    print_success "JWT secret generated"
    echo "JWT_SECRET=$JWT_SECRET"
    echo ""
    print_warning "Save this JWT secret securely! You'll need it for Railway deployment."
}

# Validate backend configuration
validate_backend() {
    print_status "Validating backend configuration..."
    
    # Check if required files exist
    if [ ! -f "backend/requirements.txt" ]; then
        print_error "backend/requirements.txt not found"
        exit 1
    fi
    
    if [ ! -f "backend/Dockerfile" ]; then
        print_error "backend/Dockerfile not found"
        exit 1
    fi
    
    if [ ! -f "backend/server.py" ]; then
        print_error "backend/server.py not found"
        exit 1
    fi
    
    # Check if config.py exists (production configuration)
    if [ ! -f "backend/config.py" ]; then
        print_error "backend/config.py not found. This is required for production deployment."
        exit 1
    fi
    
    print_success "Backend configuration validated"
}

# Validate frontend configuration
validate_frontend() {
    print_status "Validating frontend configuration..."
    
    # Check if required files exist
    if [ ! -f "frontend/package.json" ]; then
        print_error "frontend/package.json not found"
        exit 1
    fi
    
    # Check if environment files exist
    if [ ! -f "frontend/.env.production" ]; then
        print_error "frontend/.env.production not found"
        exit 1
    fi
    
    print_success "Frontend configuration validated"
}

# Build production frontend
build_frontend() {
    print_status "Building production frontend..."
    
    cd frontend
    
    # Install dependencies
    if command -v yarn &> /dev/null; then
        yarn install --production
        yarn build
    elif command -v npm &> /dev/null; then
        npm ci --production
        npm run build
    else
        print_error "Neither yarn nor npm found. Please install Node.js and npm/yarn."
        exit 1
    fi
    
    cd ..
    
    print_success "Frontend built successfully"
}

# Test backend locally
test_backend() {
    print_status "Testing backend configuration..."
    
    cd backend
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_warning "Python not found. Skipping backend test."
        cd ..
        return
    fi
    
    # Try to import the main modules
    python3 -c "import server; print('✅ Server module imports successfully')" 2>/dev/null || 
    python -c "import server; print('✅ Server module imports successfully')" 2>/dev/null ||
    print_warning "Could not test server module import. Make sure dependencies are installed."
    
    cd ..
    
    print_success "Backend test completed"
}

# Create deployment checklist
create_checklist() {
    print_status "Creating deployment checklist..."
    
    cat > DEPLOYMENT_CHECKLIST.md << EOF
# Lumina Production Deployment Checklist

## Pre-Deployment

- [ ] Code pushed to Git repository
- [ ] MongoDB Atlas cluster created
- [ ] Database user created with proper permissions
- [ ] Network access configured in MongoDB Atlas
- [ ] JWT secret generated and saved securely

## Backend Deployment (Railway)

- [ ] Railway account created
- [ ] New project created from Git repository
- [ ] Environment variables configured:
  - [ ] MONGODB_URI
  - [ ] DB_NAME
  - [ ] JWT_SECRET
  - [ ] FRONTEND_ORIGIN (update after frontend deployment)
  - [ ] PORT=8000
  - [ ] HOST=0.0.0.0
  - [ ] ENVIRONMENT=production
- [ ] Deployment successful
- [ ] API health check: \`curl https://your-app.railway.app/api/\`
- [ ] Backend URL noted for frontend configuration

## Frontend Deployment (Vercel)

- [ ] Vercel account created
- [ ] New project created from Git repository
- [ ] Root directory set to 'frontend'
- [ ] Environment variables configured:
  - [ ] REACT_APP_BACKEND_URL (Railway URL)
  - [ ] REACT_APP_ENV=production
- [ ] Deployment successful
- [ ] Frontend URL noted for CORS configuration

## Post-Deployment

- [ ] Update FRONTEND_ORIGIN in Railway with Vercel URL
- [ ] Backend redeployed with updated CORS
- [ ] Test authentication flow
- [ ] Test receipt upload and processing
- [ ] Test user isolation (multiple accounts)
- [ ] Monitor application logs
- [ ] Set up monitoring and alerts

## Security Verification

- [ ] HTTPS enabled for both frontend and backend
- [ ] Strong JWT secret (64+ characters)
- [ ] CORS configured with specific origin (not *)
- [ ] Database connection secured with authentication
- [ ] No sensitive data in client-side code
- [ ] Error messages don't leak sensitive information

---

**Generated on:** \$(date)
**JWT Secret:** Remember to use the generated JWT secret from the deployment script
EOF

    print_success "Deployment checklist created: DEPLOYMENT_CHECKLIST.md"
}

# Main execution
main() {
    echo ""
    check_requirements
    echo ""
    validate_backend
    echo ""
    validate_frontend
    echo ""
    generate_jwt_secret
    echo ""
    print_status "Building production assets..."
    build_frontend
    echo ""
    test_backend
    echo ""
    create_checklist
    echo ""
    print_success "Production preparation completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Review DEPLOYMENT_CHECKLIST.md"
    echo "2. Set up MongoDB Atlas cluster"
    echo "3. Deploy backend to Railway"
    echo "4. Deploy frontend to Vercel"
    echo "5. Update CORS configuration"
    echo "6. Test the complete application"
    echo ""
    print_warning "Don't forget to save your JWT secret securely!"
}

# Run main function
main "$@"