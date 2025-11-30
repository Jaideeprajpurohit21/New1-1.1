# 🚨 PRODUCTION "SERVICE TEMPORARILY UNAVAILABLE" FIX

**Error:** Your production deployment shows "Service temporarily unavailable"  
**URL:** `bill-tracker-102.emergent.host/app`

---

## 🎯 ROOT CAUSE

The backend service **crashed on startup** due to one of these issues:

1. ❌ **MongoDB connection failed** (MONGODB_URI not set in production)
2. ❌ **ML imports failing** (sklearn/pandas/numpy not available)
3. ❌ **Missing environment variables**

---

## ✅ IMMEDIATE FIX STEPS

### Step 1: Check Emergent Dashboard Logs

**You MUST do this to see the exact error:**

1. Open **Emergent Dashboard**
2. Go to your **bill-tracker-102 deployment**
3. Click **"Logs"** tab
4. Look for **backend startup errors**

**Common errors you'll see:**

```
❌ "Cannot connect to mongodb://localhost:27017"
→ MONGODB_URI not set

❌ "ImportError: No module named 'sklearn'"
→ ML dependencies trying to load

❌ "not authorized on database 'lumina_development'"
→ DB_NAME doesn't match

❌ "Connection refused"
→ Backend can't start
```

---

## 🔧 FIX #1: Set Environment Variables

**In Emergent Dashboard → Deployment → Environment Variables:**

### Required Variables:
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/yourdb
DB_NAME=lumina_production
PORT=8001
HOST=0.0.0.0
JWT_SECRET=your-secure-32-character-secret-key-here
```

### How to Get MongoDB URI:

**If Emergent provides managed MongoDB:**
- It should auto-set MONGODB_URI
- Check if it's already there
- If not, contact Emergent support

**If using your own MongoDB Atlas:**
1. Go to MongoDB Atlas dashboard
2. Click "Connect"
3. Choose "Connect your application"
4. Copy the connection string
5. Replace `<password>` with your database password
6. Add to Emergent environment variables

---

## 🔧 FIX #2: Verify ML Dependencies Removed

**The deployment agent found:**
```
❌ ml_category_predictor.py still imports sklearn/pandas/numpy
❌ These libraries are NOT in requirements.txt (we removed them)
❌ Backend crashes when trying to import them
```

**Quick Check:**
```bash
# In Emergent logs, look for:
ImportError: No module named 'sklearn'
ImportError: No module named 'pandas'
ImportError: No module named 'numpy'
```

**If you see this error:**
- The code is still trying to import ML libraries
- We removed them from requirements.txt
- But transaction_processor.py still tries to import them

**Fix (already in code):**
The code has a try/except block that should handle this:
```python
try:
    from ml_category_predictor import MLCategoryPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False  # Uses rule-based categorization
```

This should work, but if backend still crashes, it means the import is happening before the try/except.

---

## 🔧 FIX #3: Test Backend Endpoint

**After setting environment variables and re-deploying:**

```bash
# Test health endpoint
curl https://bill-tracker-102.emergent.host/api/health

# Should return:
{
  "status": "ok",
  "version": "2.1.0",
  "database": "healthy"
}

# If it works:
✅ Backend is running!

# If still shows 503:
❌ Check logs again for new error
```

---

## 📋 STEP-BY-STEP CHECKLIST

### Do This NOW:

1. [ ] **Open Emergent Dashboard**
2. [ ] **Find bill-tracker-102 deployment**
3. [ ] **Click "Logs" tab**
4. [ ] **Find the backend error** (look for ERROR, CRASH, ImportError, MongoDB)
5. [ ] **Take a screenshot or copy the error**
6. [ ] **Share the error with me** so I can give you the exact fix

### After You Know the Error:

7. [ ] **Set missing environment variables** (especially MONGODB_URI and DB_NAME)
8. [ ] **Click "Re-deploy"** or "Deploy Again"
9. [ ] **Wait 5-7 minutes** for deployment to complete
10. [ ] **Check logs again** to verify no errors
11. [ ] **Test https://bill-tracker-102.emergent.host/api/health**
12. [ ] **Test the app** at https://bill-tracker-102.emergent.host/app

---

## 🎯 MOST LIKELY SCENARIOS

### Scenario 1: MongoDB Connection Failed (90% probability)
**Error in logs:**
```
Cannot connect to mongodb://localhost:27017
Connection refused
```

**Fix:**
- Set MONGODB_URI environment variable
- Re-deploy
- Backend will connect to correct MongoDB

### Scenario 2: ML Import Error (8% probability)
**Error in logs:**
```
ImportError: No module named 'sklearn'
```

**Fix:**
- Should auto-fallback to rule-based categorization
- If still crashing, we need to remove the import entirely

### Scenario 3: Database Name Mismatch (2% probability)
**Error in logs:**
```
not authorized on database 'lumina_development'
```

**Fix:**
- Set DB_NAME environment variable to match your actual database
- Re-deploy

---

## 💡 WHY THIS HAPPENS

**Development Environment:**
- Uses localhost MongoDB
- All dependencies installed
- .env files present
- Everything works ✅

**Production Environment:**
- Uses Atlas MongoDB (different connection string)
- ML dependencies removed (to save resources)
- Environment variables must be set in platform
- Missing config = crash ❌

**The Gap:**
Your .env files don't get deployed. Environment variables must be set in Emergent dashboard.

---

## ✅ AFTER THE FIX

**You should see:**
```
✅ Backend: Running
✅ Database: Connected
✅ Health: OK
✅ App: Working
✅ URL: https://bill-tracker-102.emergent.host/app
✅ Status: Service available 24/7
```

---

## 🚨 URGENT ACTION REQUIRED

**RIGHT NOW:**
1. Open Emergent Dashboard
2. Check the logs
3. Tell me what error you see

**Common errors:**
- "MongoDB connection failed" → Set MONGODB_URI
- "ImportError sklearn" → ML dependency issue
- "not authorized" → DB_NAME mismatch
- "Port 8001 in use" → Service conflict

**Once you share the error, I can give you the EXACT fix!**

---

*The app works in development (preview), just needs proper configuration in production.* 🚀
