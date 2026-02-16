## AGENTIC HONEYPOT API
An AI-powered honeypot system that detects scam messages, autonomously engages scammers in realistic conversations, and extracts actionable intelligence.

## Overview

This system uses advanced AI to:
- **Detect scam intent** using pattern matching and LLM analysis
- **Engage scammers** with human-like, believable responses
- **Extract intelligence** (bank accounts, UPI IDs, phone numbers, phishing links)
- **Report findings** to evaluation endpoints automatically

## Tech Stack

- **Framework**: FastAPI (async, high-performance)
- **AI**: OpenAI GPT-4.1 for conversational agent
- **Storage**: Redis for session management
- **Deployment**: Serverless-ready (Vercel, Railway, etc.)



## Quick Setup

### Prerequisites

- Python 3.11+
- Redis (local or cloud instance)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   cd HoneyPot-API-new
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set:
   - `API_KEY`: Your API authentication key
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `REDIS_URL`: Your Redis connection string

5. **Run the server**
   ```bash
   # Development mode
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Production mode
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

6. **Test the API**
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -H "x-api-key: your-api-key-here" \
     -d '{
       "sessionId": "test-123",
       "message": {
         "sender": "scammer",
         "text": "Your bank account will be blocked today. Verify immediately.",
         "timestamp": 1770005528731
       },
       "conversationHistory": [],
       "metadata": {
         "channel": "SMS",
         "language": "English",
         "locale": "IN"
       }
     }'
   ```


## API Endpoints

### POST `/chat`

Main endpoint for message processing.

**Headers:**
- `Content-Type: application/json`
- `x-api-key: YOUR_API_KEY`

**Request Body:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your account will be blocked. Click here to verify.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "Wait what?? Which account are you talking about?"
}
```

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "timestamp": 1770005528731
}
## Deployment

### Redis Cloud Setup

1. Sign up for [Redis Cloud](https://redis.com/try-free/) (free tier available)
2. Create a database
3. Copy the connection string
4. Update `REDIS_URL` in `.env`



### Deploy to Vercel (with Serverless)

Note: FastAPI requires special handling on Vercel. Consider using Railway or Render for easier deployment.

## Configuration

All configuration is managed via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `your-secret-api-key-here` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `OPENAI_TEMPERATURE` | Response creativity (0-1) | `0.7` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `REDIS_SESSION_TTL` | Session TTL in seconds | `86400` (24 hours) |
| `GUVI_CALLBACK_URL` | Callback endpoint URL | `https://hackathon.guvi.in/api/updateHoneyPotFinalResult` |
| `MIN_MESSAGES_FOR_CALLBACK` | Min messages before callback | `5` |
| `MIN_INTELLIGENCE_ITEMS` | Min intelligence items for callback | `2` |
| `SCAM_DETECTION_CONFIDENCE_THRESHOLD` | Scam confidence threshold | `0.7` |
| `DEBUG` | Enable debug mode | `False` |



## Features

### 🔍 Intelligent Scam Detection
- **Phase 1**: Fast pattern-based detection for urgency, threats, banking terms
- **Phase 2**: LLM-powered analysis for accurate classification
- Confidence scoring and category tagging

### 🤖 Human-like AI Agent
- Maintains believable persona as a concerned user
- Keeps responses short and natural (SMS-like)
- Asks probing questions to extract information
- Never reveals detection

### 📊 Intelligence Extraction
- Bank account numbers (10-18 digits)
- UPI IDs (username@provider format)
- Phone numbers (international/Indian formats)
- Phishing URLs and suspicious links
- Scam-related keywords

### 💾 Session Management
- Redis-based conversation persistence
- Tracks message counts and engagement depth
- Stores extracted intelligence cumulatively
- 24-hour session TTL

### 📤 Automated Reporting
- Triggers callback after sufficient engagement (5+ messages or 2+ intelligence items)
- Exponential backoff retry logic (3 attempts)
- Sends comprehensive results to evaluation endpoint



```

## Architecture

```
┌─────────────────┐
│ Evaluation      │
│ Platform        │
└────────┬────────┘
         │ POST /chat
         ▼
┌─────────────────┐
│ FastAPI         │◄─── API Key Auth
│ Endpoint        │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────┐
    ▼         ▼          ▼         ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌──────────┐
│ Scam   │ │ AI   │ │ Intel  │ │ Session  │
│Detector│ │Agent │ │Extract │ │ Manager  │
└────────┘ └──────┘ └────────┘ └─────┬────┘
                                      │
                                 ┌────▼────┐
                                 │ Redis   │
                                 └─────────┘
```


## Project Structure

```
HoneyPot-API-new/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app & endpoints
│   ├── models.py               # Pydantic models
│   ├── auth.py                 # API key authentication
│   ├── config.py               # Configuration management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scam_detector.py   # Scam detection logic
│   │   ├── ai_agent.py        # OpenAI conversational agent
│   │   ├── intelligence.py    # Intelligence extraction
│   │   ├── session_manager.py # Redis session management
│   │   └── callback.py        # GUVI callback logic
│   └── prompts/
│       ├── __init__.py
│       └── agent_system.py    # AI agent system prompts
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore patterns
└── README.md                 # This file
```

## How It Works

1. **Message Received**: Platform sends message to `/chat` endpoint
2. **Authentication**: API key validated
3. **Session Loaded**: Previous conversation retrieved from Redis
4. **Scam Detection**: 
   - Pattern matching checks for common scam indicators
   - LLM analyzes message for scam intent
   - Confidence score calculated
5. **Agent Response**: If scam detected:
   - AI agent generates human-like response
   - Response stays in character (curious but cautious victim)
   - Asks probing questions to extract intelligence
6. **Intelligence Extraction**: 
   - Regex patterns extract bank accounts, UPI IDs, phone numbers, URLs
   - Keywords tracked for scam indicators
7. **Session Update**: 
   - Conversation history updated
   - Message count incremented
   - Intelligence stored cumulatively
8. **Callback Triggered**: When criteria met (5+ messages or 2+ intelligence items):
   - Final results sent to GUVI endpoint
   - Retry logic ensures delivery
9. **Response Returned**: Human-like reply sent back to platform

## Example Conversation Flow

**Message 1 (Scammer):**
> "Your bank account will be blocked today. Verify immediately by clicking this link: http://fake-bank.com"

**Response (Agent):**
> "Wait what?? Which bank account are you talking about?"

**Message 2 (Scammer):**
> "Your HDFC account ending in 1234. Click the link now or account will be suspended."

**Response (Agent):**
> "Ok but can you give me a phone number to call instead? I don't trust links"

**Message 3 (Scammer):**
> "Call +91-9876543210 immediately. Reference code: HDFC1234"

**Response (Agent):**
> "Ok calling now. What was that link again just in case?"

**Intelligence Extracted:**
- Phone: +91-9876543210
- URL: http://fake-bank.com
- Keywords: urgent, verify, blocked, suspended
- Bank reference: HDFC account 1234

**Callback Sent** (after 5+ messages or significant intelligence)

## Testing

### Manual Testing

Use the provided test script:

```bash
python test_api.py
```

Or use curl:

```bash
# Test scam detection
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d @test_scam_message.json
```

### Example Test Scenarios

1. **Bank Account Scam**
   - "Your account is suspended. Verify your details."
   - "Send OTP to confirm your identity."

2. **UPI Fraud**
   - "You won 50,000 rupees! Send to pramod@paytm to claim."
   - "Refund of 2,500 pending. Share your UPI ID."

3. **Phishing**
   - "Click here to update KYC: http://fake-bank.com"
   - "Your parcel is stuck. Pay customs: http://delivery-scam.com"

## License

MIT License - See LICENSE file for details




                      

