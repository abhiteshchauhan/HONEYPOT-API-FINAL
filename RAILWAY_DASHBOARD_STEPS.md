# 🚂 Railway Dashboard Deployment - Step by Step

Your Railway dashboard should be open at:
https://railway.com/project/d83dcb65-d21a-490b-86c6-16f2111d11fc

---

## 📋 Follow These Steps EXACTLY

### Step 1: Deploy from GitHub

In the Railway dashboard you just opened:

1. Click **"+ New"** button (top right)
2. Select **"GitHub Repo"**
3. Find and select: **`abhiteshchauhan/HONEYPOT-API-FINAL`**
4. Click **"Deploy Now"**

Railway will now:
- Clone your repository
- Detect it's a Python/FastAPI app
- Build automatically
- Start deploying

⏳ **Wait 2-3 minutes for build to complete**

---

### Step 2: Add Redis Database

While your app is building or after it's done:

1. Click **"+ New"** button again
2. Select **"Database"**
3. Choose **"Add Redis"**
4. Railway creates Redis instance

✅ Redis URL is automatically connected to your app!

---

### Step 3: Set Environment Variables

1. Click on your **service name** (HONEYPOT-API-FINAL or similar)
2. Go to **"Variables"** tab
3. Click **"New Variable"** button
4. Add each variable ONE BY ONE:

**Copy these exactly from your .env file:**

```
Variable 1:
Name: API_KEY
Value: honeypot-api-key-2024-secure

Variable 2:
Name: OPENAI_API_KEY
Value: (copy from your .env file - starts with sk-proj-)

Variable 3:
Name: OPENAI_MODEL
Value: gpt-3.5-turbo

Variable 4:
Name: OPENAI_TEMPERATURE
Value: 0.7

Variable 5:
Name: GUVI_CALLBACK_URL
Value: https://hackathon.guvi.in/api/updateHoneyPotFinalResult

Variable 6:
Name: MIN_MESSAGES_FOR_CALLBACK
Value: 5

Variable 7:
Name: MIN_INTELLIGENCE_ITEMS
Value: 2

Variable 8:
Name: SCAM_DETECTION_CONFIDENCE_THRESHOLD
Value: 0.7
```

5. After adding all variables, Railway will **auto-redeploy**

⏳ **Wait 1-2 minutes for redeployment**

---

### Step 4: Generate Public Domain

1. In your service view, go to **"Settings"** tab
2. Scroll to **"Networking"** section
3. Click **"Generate Domain"**
4. Copy the URL (example: `honeypot-api-production.railway.app`)

✅ **This is your public API URL!**

---

### Step 5: Verify Deployment

#### Check Build Logs:

1. Click on **"Deployments"** tab
2. Click the latest deployment
3. Watch the logs - should see:
   ```
   [STARTUP] Starting Agentic Honey-Pot API...
   [OK] Configuration validated
   [OK] Redis connection established
   [OK] API ready at /chat endpoint
   ```

#### Check if Service is Running:

In the "Deployments" tab, you should see:
- Status: **✅ Active** (green)
- Latest deployment: **Success**

---

## 🧪 Test Your Deployed API

### Test 1: Health Check

Open PowerShell and run:

```powershell
# Replace with your actual Railway URL
$url = "https://your-app.railway.app"
Invoke-WebRequest -Uri "$url/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Expected**:
```json
{"status":"healthy","redis":"connected","timestamp":1770331270046}
```

### Test 2: Chat Endpoint

```powershell
$url = "https://your-app.railway.app"
$headers = @{
    "Content-Type" = "application/json"
    "x-api-key" = "honeypot-api-key-2024-secure"
}

$body = @{
    sessionId = "railway-test-001"
    message = @{
        sender = "scammer"
        text = "Your bank account will be blocked today"
        timestamp = 1770331270000
    }
    conversationHistory = @()
    metadata = @{
        channel = "SMS"
        language = "English"
        locale = "IN"
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "$url/chat" -Method Post -Headers $headers -Body $body
```

**Expected**:
```json
{
  "status": "success",
  "reply": "Wait what?? Which account?"
}
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Build shows "Success" in Deployments tab
- [ ] Service status is "Active" (green)
- [ ] Health endpoint returns healthy status
- [ ] Chat endpoint returns agent reply
- [ ] Redis is connected
- [ ] All environment variables are set (check Variables tab)
- [ ] Public domain is generated

---

## 🎯 Submit to GUVI Platform

Once everything works:

**Your API URL**: `https://your-app.railway.app/chat`  
**API Key**: `honeypot-api-key-2024-secure`  
**Method**: POST  
**Headers**: `x-api-key` and `Content-Type: application/json`

---

## 🔧 Troubleshooting

### Build Failed?

**Check logs in Railway dashboard:**
1. Go to Deployments tab
2. Click the failed deployment
3. Read error message

**Common issues:**
- Missing environment variables → Add them in Variables tab
- Python version issue → Already fixed with railway.toml ✅
- Dependencies missing → Already in requirements.txt ✅

### App Crashes on Start?

**Check logs for:**
- Missing OPENAI_API_KEY
- Missing API_KEY
- Redis connection failed

**Fix:** Add missing variables in Variables tab

### Can't Access URL?

1. Make sure domain is generated (Settings → Networking)
2. Check service is "Active"
3. Try `railway logs` to see if app is running

### Redis Not Connected?

1. Make sure you added Redis (+ New → Database → Redis)
2. Check if REDIS_URL appears in Variables tab
3. Redeploy if needed

---

## 🚀 Quick Command Reference

```powershell
# View your Railway dashboard
railway open

# Check deployment status
railway status

# View real-time logs
railway logs

# Check environment variables
railway variables

# Get your public URL
railway domain

# Redeploy
railway up
```

---

## ⏰ Current Status

✅ Railway CLI installed  
✅ Railway project created: HONEYPOT-API-FINAL  
✅ Code pushed to GitHub (clean, no secrets)  
✅ Configuration files ready (railway.toml, Procfile, nixpacks.toml)  

**Next**: Follow Steps 1-5 above in your Railway dashboard!

---

## 💡 Pro Tips

1. **Use gpt-3.5-turbo** instead of gpt-4 (15x cheaper, still works great)
2. **Monitor logs** during first few tests
3. **Check Variables tab** - REDIS_URL should appear automatically
4. **Be patient** - First build takes 2-3 minutes

---

## 🎉 You're One Step Away!

Your Railway dashboard is open. Just:
1. Deploy from GitHub (Step 1)
2. Add Redis (Step 2)
3. Set variables (Step 3)
4. Generate domain (Step 4)
5. Test and submit! (Step 5)

**Total time: ~10 minutes**

Good luck! 🚀
