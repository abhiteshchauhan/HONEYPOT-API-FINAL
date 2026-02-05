# 🚀 Deploy to Railway RIGHT NOW - Complete Guide

## ⚡ Quick Start (10 Minutes Total)

Railway CLI is already installed! Follow these steps:

---

## Step 1: Login to Railway (2 minutes)

Open a **NEW PowerShell window** and run:

```powershell
cd C:\Users\Kundan\Desktop\HoneyPot-API-new
railway login
```

**What happens:**
1. Browser opens automatically
2. Login with your GitHub account (abhiteshchauhan)
3. Click "Authorize Railway"
4. Return to terminal - you'll see "Logged in as..."

---

## Step 2: Initialize Project (1 minute)

In the same terminal:

```powershell
railway init
```

**When prompted:**
- "Project name": Type `HONEYPOT-API-FINAL` and press Enter
- "Start from scratch": Press Enter

You'll see: "Project created: HONEYPOT-API-FINAL"

---

## Step 3: Create Railway Project with Redis (2 minutes)

```powershell
railway up
```

This will:
- Deploy your code to Railway
- Build the project
- Start the server

**Wait for:** "Build successful" and "Deployment successful"

---

## Step 4: Add Redis Database (1 minute)

```powershell
railway add
```

**When prompted:**
- Select: **Redis** (use arrow keys, press Enter)

Railway will automatically:
- Create Redis instance
- Set `REDIS_URL` environment variable
- Connect it to your app

---

## Step 5: Set Environment Variables (3 minutes)

### Option A: Via Railway Dashboard (Easier)

1. Run: `railway open` (opens project in browser)
2. Click on your service
3. Go to "Variables" tab
4. Click "New Variable" for each:

```
API_KEY = honeypot-api-key-2024-secure
OPENAI_API_KEY = your-openai-api-key-here
OPENAI_MODEL = gpt-3.5-turbo
OPENAI_TEMPERATURE = 0.7
GUVI_CALLBACK_URL = https://hackathon.guvi.in/api/updateHoneyPotFinalResult
MIN_MESSAGES_FOR_CALLBACK = 5
MIN_INTELLIGENCE_ITEMS = 2
SCAM_DETECTION_CONFIDENCE_THRESHOLD = 0.7
```

5. Click "Deploy" (or it auto-deploys)

### Option B: Via CLI (Faster)

```powershell
railway variables set API_KEY=honeypot-api-key-2024-secure
railway variables set OPENAI_API_KEY=your-openai-api-key-here
railway variables set OPENAI_MODEL=gpt-3.5-turbo
railway variables set GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
railway variables set MIN_MESSAGES_FOR_CALLBACK=5
railway variables set MIN_INTELLIGENCE_ITEMS=2
```

**Note**: `REDIS_URL` is automatically set when you added Redis!

---

## Step 6: Generate Public Domain (1 minute)

```powershell
railway domain
```

This generates a public URL like:
```
https://honeypot-api-production.railway.app
```

**Copy this URL** - this is your API endpoint!

---

## Step 7: Test Your Deployment

### Test Health Endpoint

```powershell
$url = "YOUR-RAILWAY-URL-HERE"
Invoke-WebRequest -Uri "$url/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

Expected:
```json
{"status":"healthy","redis":"connected","timestamp":1770331270046}
```

### Test Chat Endpoint

```powershell
$url = "YOUR-RAILWAY-URL-HERE"
$headers = @{
    "Content-Type" = "application/json"
    "x-api-key" = "honeypot-api-key-2024-secure"
}

$body = @{
    sessionId = "railway-test-001"
    message = @{
        sender = "scammer"
        text = "Your bank account will be blocked"
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

---

## 🔍 Troubleshooting

### "Not logged in"?
```powershell
railway login
```

### "No project found"?
```powershell
railway link
# Or start over with: railway init
```

### Build failed?
```powershell
railway logs
# Check error messages
```

### Variables not set?
```powershell
railway variables
# List all variables
```

### Redis not connected?
```powershell
railway add
# Select Redis again
```

---

## 📋 All Commands in Order

Copy and run these one by one:

```powershell
# 1. Go to project
cd C:\Users\Kundan\Desktop\HoneyPot-API-new

# 2. Login (browser opens)
railway login

# 3. Initialize project
railway init

# 4. Deploy
railway up

# 5. Add Redis
railway add
# → Select Redis

# 6. Set variables (use Option A or B from Step 5)
railway open
# → Go to Variables tab
# → Add all variables

# 7. Get your URL
railway domain

# 8. Test
# Use PowerShell commands from Step 7
```

---

## ✅ Success Indicators

You'll know it worked when:

1. ✅ `railway up` shows "Deployment successful"
2. ✅ `railway domain` returns a URL
3. ✅ Health check returns `{"status":"healthy"}`
4. ✅ Chat endpoint returns agent reply

---

## 🎯 After Deployment

### Your API will be at:
```
https://YOUR-APP-NAME.railway.app
```

### Update the tester with:
```
https://YOUR-APP-NAME.railway.app/chat
```

### API Key for tester:
```
honeypot-api-key-2024-secure
```

---

## 💡 Quick Commands Reference

```powershell
# View logs
railway logs

# Check status
railway status

# View variables
railway variables

# Open dashboard
railway open

# Get domain
railway domain
```

---

## 🚨 Important Notes

1. **First deployment takes 2-3 minutes** (building Docker image)
2. **Subsequent deploys are faster** (30 seconds)
3. **Redis URL is auto-set** when you add Redis
4. **Domain is permanent** (unless you delete project)
5. **Free tier is enough** for evaluation

---

## 📞 Need Help?

If you get stuck:
1. Run `railway logs` to see errors
2. Check Railway dashboard: `railway open`
3. Verify all environment variables are set
4. Make sure Redis is added

---

## 🎉 You're Almost There!

Just run these commands in a **NEW PowerShell window**:

```powershell
cd C:\Users\Kundan\Desktop\HoneyPot-API-new
railway login
railway init
railway up
railway add  # Select Redis
railway open # Set variables
railway domain
```

Then test your URL in the GUVI platform! 🚀

---

**Estimated Total Time**: 10 minutes  
**Success Rate**: 99% (Railway is very reliable)  
**Free Tier**: Yes (perfect for hackathon)
