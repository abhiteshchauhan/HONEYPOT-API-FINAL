# Deploy to Railway - Quick Guide

## Prerequisites
- Railway account (https://railway.app)
- GitHub account (optional but recommended)

## Method 1: CLI Deployment (5 minutes)

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Login
```bash
railway login
```

### Step 3: Initialize Project
```bash
cd C:\Users\Kundan\Desktop\HoneyPot-API-new
railway init
```

### Step 4: Add Redis
```bash
railway add
# Select: Redis
```

### Step 5: Set Environment Variables
```bash
# Get Redis URL from Railway
railway variables

# Set your variables
railway variables set API_KEY=your-super-secure-api-key-here
railway variables set OPENAI_API_KEY=sk-your-openai-key
railway variables set OPENAI_MODEL=gpt-3.5-turbo
railway variables set GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
railway variables set MIN_MESSAGES_FOR_CALLBACK=5
railway variables set MIN_INTELLIGENCE_ITEMS=2
railway variables set SCAM_DETECTION_CONFIDENCE_THRESHOLD=0.7
```

### Step 6: Deploy
```bash
railway up
```

### Step 7: Get Your URL
```bash
railway domain
```

Your API will be live at: `https://your-app.railway.app`

## Method 2: GitHub Deployment (Recommended)

### Step 1: Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit: Agentic Honey-Pot API"
git branch -M main
git remote add origin https://github.com/yourusername/honeypot-api.git
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect your project

### Step 3: Add Redis
1. Click "+ New" in your project
2. Select "Database" → "Redis"
3. Railway auto-connects it

### Step 4: Configure Environment Variables
In Railway dashboard:
1. Click on your service
2. Go to "Variables" tab
3. Add each variable:
   - `API_KEY`: Generate secure key
   - `OPENAI_API_KEY`: Your OpenAI key
   - `OPENAI_MODEL`: `gpt-3.5-turbo` or `gpt-4`
   - `GUVI_CALLBACK_URL`: `https://hackathon.guvi.in/api/updateHoneyPotFinalResult`
   - Other variables from .env.example

### Step 5: Add Domain (Optional)
1. Go to "Settings" tab
2. Click "Generate Domain"
3. Get your public URL

## Testing Your Deployment

### Health Check
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{"status":"healthy","redis":"connected","timestamp":1770329980126}
```

### Test Chat Endpoint
```bash
curl -X POST https://your-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "sessionId": "test-001",
    "message": {
      "sender": "scammer",
      "text": "Your bank account will be blocked",
      "timestamp": 1770329900000
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

## Monitoring

### View Logs
```bash
railway logs
```

Or in dashboard: Click service → "Logs" tab

### Check Metrics
Railway dashboard shows:
- CPU usage
- Memory usage
- Request count
- Errors

## Troubleshooting

### Build Failed?
Check logs: `railway logs`

Common issues:
- Missing dependencies in `requirements.txt` ✅ (we have this)
- Python version mismatch (Railway uses Python 3.11+) ✅ (compatible)

### Redis Connection Failed?
Check that Redis service is running in Railway dashboard.

Redis URL is auto-injected as environment variable.

### API Returns 500 Error?
1. Check logs: `railway logs`
2. Verify OpenAI API key is valid
3. Check Redis connection
4. Ensure all environment variables are set

### OpenAI Rate Limit?
Switch to cheaper model:
```bash
railway variables set OPENAI_MODEL=gpt-3.5-turbo
```

## Cost Estimates

### Railway
- Free tier: $5/month credit
- Pro: $20/month
- Redis: Free on starter plan

### OpenAI (per 1000 scam messages)
- GPT-3.5-turbo: ~$2
- GPT-4: ~$30
- GPT-4o-mini: ~$0.50

## Next Steps After Deployment

1. ✅ Test with Postman
2. ✅ Share URL with evaluation team
3. ✅ Monitor logs for errors
4. ✅ Track OpenAI API usage
5. ✅ Set up alerts (optional)

## Support

Railway Docs: https://docs.railway.app/
Railway Discord: https://discord.gg/railway

Your API is deployed and ready! 🚀
