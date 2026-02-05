"""
Vercel serverless entry point for FastAPI
"""
from app.main import app

# Vercel will use this as the handler
handler = app
