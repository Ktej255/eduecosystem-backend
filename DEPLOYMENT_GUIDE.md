# Backend Deployment Guide

## Environment Variables
Ensure the following are set in your `.env` (or Vercel/AWS env vars):

```ini
# Security
SECRET_KEY=your_secret_key
TOTP_SECRET_KEY=your_totp_secret_key  # NEW: For 2FA
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Database
DATABASE_URL=postgresql://user:pass@host/db

# AI Services
GEMINI_API_KEY=your_google_gemini_key # NEW: For AI Tutor

# Cors
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://your-domain.com"]
```

## Verification
Run the following check to ensure the API starts correctly:
```bash
cd backend
python -c "from main import app; print('Backend Integrity: OK')"
```

## Deployment
1. **Build Frontend**: `npm run build`
2. **Start Backend**: `uvicorn main:app --host 0.0.0.0 --port 8000`
