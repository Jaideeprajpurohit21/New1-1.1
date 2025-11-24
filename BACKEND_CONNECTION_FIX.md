# 🔧 BACKEND CONNECTION ERROR - DEPLOYMENT FIX

**Error:** "Failed to load receipts. Network error: Unable to connect to server."

---

## 🎯 ROOT CAUSE

The deployed frontend is trying to connect to the backend, but the backend is either:
1. Not started properly in production
2. Crashed during startup  
3. Environment variables not set correctly

---

## 🔍 DIAGNOSIS

### Common Causes in Emergent Deployments:

**1. MongoDB Connection Failure (Most Likely)**
```python
# In server.py line 44-45:
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "lumina_development")
```

**Problem:**
- Default MongoDB URI is `localhost:27017` (development)
- Emergent provides **Atlas MongoDB** with different URI
- If `MONGODB_URI` env var not set → backend tries localhost → fails → crashes
- If `DB_NAME` doesn't match Atlas database → "not authorized" error → crashes

**2. Missing Dependencies**
- If ML files (`ml_category_predictor.py`) try to import removed dependencies
- Backend crashes on startup

**3. Port Configuration**
- Backend needs to listen on correct port (8001)
- Environment might expect different port

---

## ✅ FIXES NEEDED

### Fix 1: Ensure MongoDB Environment Variables Set

**In Emergent Dashboard → Deployment Settings → Environment Variables:**

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=lumina_production
```

**These MUST be set by Emergent platform, not in code!**

### Fix 2: Make ML Import Optional

**File:** `/app/ml_category_predictor.py`

Currently imports ML libs unconditionally. Need to make it optional:

```python
# At top of file, wrap imports:
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("ML dependencies not available, using rule-based only")
```

### Fix 3: Backend Startup Verification

**Check backend logs in Emergent dashboard for:**
- "MongoDB connection failed"
- "ImportError" for sklearn/pandas/numpy
- "Address already in use" (port conflict)
- "Permission denied" errors

---

## 🚀 IMMEDIATE FIX STEPS

### Step 1: Verify Environment Variables

In Emergent Dashboard:
1. Go to your deployment
2. Click "Environment Variables" or "Settings"
3. Verify these are set:
   - `MONGODB_URI` - Atlas connection string
   - `DB_NAME` - Your database name
   - `PORT` - Should be 8001
   - `HOST` - Should be 0.0.0.0

### Step 2: Check Backend Logs

1. Go to Emergent dashboard
2. Find your deployment
3. Click "Logs" or "View Logs"
4. Look for backend errors:
   ```
   ERROR: MongoDB connection failed
   ERROR: Cannot import sklearn
   ERROR: Port 8001 already in use
   ```

### Step 3: Fix Based on Logs

**If MongoDB error:**
- Verify `MONGODB_URI` is set correctly
- Verify `DB_NAME` matches your Atlas database
- Check MongoDB Atlas whitelist includes Kubernetes IPs

**If Import error:**
- ML dependencies still being imported
- Need to make them optional (see Fix 2 above)

**If Port error:**
- Backend trying wrong port
- Check `PORT` environment variable

### Step 4: Re-deploy

After fixing environment variables:
1. Click "Re-deploy" in Emergent dashboard
2. Wait for build to complete (5-7 minutes)
3. Check logs again
4. Test `/api/health` endpoint

---

## 🧪 TESTING BACKEND

### Test if Backend is Running:

```bash
# Health check
curl https://luminaai.ai/api/health

# Expected response:
{
  "status": "ok",
  "version": "2.1.0",
  "database": "healthy"
}

# If returns 502/504:
Backend not running

# If returns 500:
Backend crashed on startup

# If connection timeout:
Backend not deployed or wrong URL
```

---

## 🔍 SPECIFIC CHECKS

### Check 1: MongoDB Connection

**Test query:**
```bash
curl https://luminaai.ai/api/categories
```

**If returns `[]`:** Database connected but empty ✅  
**If returns 500 with "not authorized":** DB_NAME mismatch ❌  
**If times out:** MongoDB not accessible ❌

### Check 2: Backend Startup

**In deployment logs, look for:**
```
✅ "Uvicorn running on http://0.0.0.0:8001"
✅ "Application startup complete"
❌ "MongoDB connection failed"
❌ "ImportError: No module named 'sklearn'"
```

### Check 3: Environment Variables

**Verify in Emergent dashboard:**
- MONGODB_URI is set and starts with `mongodb+srv://`
- DB_NAME is set (not default "lumina_development")
- PORT is 8001
- HOST is 0.0.0.0

---

## 💡 WHY THIS HAPPENS

**Development vs Production:**

| Aspect | Development | Production |
|--------|-------------|------------|
| MongoDB | localhost:27017 | Atlas mongodb+srv:// |
| Database | lumina_development | lumina_production |
| ML libs | Installed locally | Not in container |
| Env vars | From .env files | From platform |

**The Error Sequence:**
1. Frontend builds and deploys successfully ✅
2. Backend starts in container
3. Backend tries to connect to MongoDB
4. `MONGODB_URI` not set → uses localhost
5. localhost MongoDB doesn't exist in container
6. Connection fails → backend crashes
7. Frontend tries to call `/api/receipts`
8. Backend not responding → "Network error"

---

## ✅ CORRECT CONFIGURATION

### Environment Variables (Set in Emergent):
```env
# MongoDB (PROVIDED BY EMERGENT)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=lumina_production

# Server
PORT=8001
HOST=0.0.0.0

# Security
JWT_SECRET=your-secure-secret-here

# CORS (Optional - currently allows all)
CORS_ORIGINS=https://luminaai.ai
```

### Backend Code (Already Correct):
```python
# Uses environment variables with fallbacks
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "lumina_development")
```

**The code is correct! Just need environment variables set properly.**

---

## 🎯 ACTION PLAN

**Priority 1: Check Emergent Dashboard**
1. Open deployment logs
2. Look for specific error message
3. Note if backend even started

**Priority 2: Verify Environment Variables**
1. Check MONGODB_URI is set
2. Check DB_NAME is set
3. Verify connection string format

**Priority 3: Re-deploy if Needed**
1. Fix any missing environment variables
2. Click "Re-deploy"
3. Monitor logs for successful startup

**Priority 4: Test**
1. Check `/api/health` endpoint
2. Try uploading a receipt
3. Verify frontend can load data

---

## 📞 WHAT TO CHECK IN EMERGENT DASHBOARD

1. **Deployment Status**
   - Is deployment "Running" or "Failed"?

2. **Backend Logs** (Most Important!)
   - What error appears on startup?
   - Does it say "MongoDB connection failed"?
   - Any import errors?

3. **Environment Variables**
   - Are MongoDB credentials set?
   - Is DB_NAME configured?

4. **Health Check**
   - Can you access `/api/health`?
   - What status code does it return?

---

## ✅ EXPECTED OUTCOME

**After Fix:**
```
Frontend: ✅ Loads
Backend: ✅ Running
Database: ✅ Connected
API: ✅ Responds
Receipts: ✅ Load successfully
```

**The app should work end-to-end!**

---

*Next step: Check Emergent deployment logs for the specific backend error*
