"""
Updated Test Script for Tiered AI
Uses keys from .env/settings to verify your fresh implementation.
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.gemini_service import gemini_service

async def test_fresh_setup():
    print("\n" + "="*60)
    print("FRESH AI SYSTEM VERIFICATION (2025)")
    print("="*60)
    
    # 1. Test Free Gemini
    print("\n[1] Testing Free Gemini (3.0 Flash)...")
    res = gemini_service.generate_text("Say 'Free System Online'", is_complex=False)
    print(f"Result: {res}")
    
    # 2. Test Fallback (If you want to force test it, you'd mock the primary failure)
    print("\nNote: Fallback logic (Gemma/Llama) is active and will triggers if Gemini hits rate limits.")

if __name__ == "__main__":
    # Note: gemini_service currently uses sync calls, so we don't need full async for basic test
    import time
    start = time.time()
    
    try:
        from app.models.user import User
        # Mock user
        mock_user = type('obj', (object,), {'is_premium': False, 'subscription_status': 'free'})
        
        print(f"Testing with Free User context...")
        res = gemini_service.generate_text("Hello from the tiered system!", user=mock_user)
        print(f"AI Response: {res}")
        
    except Exception as e:
        print(f"Test Error: {e}")
    
    print(f"\nTime taken: {time.time() - start:.2f}s")
