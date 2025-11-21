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
- [ ] API health check: `curl https://your-app.railway.app/api/`
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

**Generated on:** $(date)
**JWT Secret:** Remember to use the generated JWT secret from the deployment script
