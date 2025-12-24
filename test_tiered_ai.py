import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.gemini_service import GeminiService

def test_tiered_logic():
    print("\n" + "="*60)
    print("VERIFYING TIERED AI LOGIC")
    print("="*60)
    
    # Initialize service
    service = GeminiService()
    
    # Mock settings/keys for testing
    service.free_key = "FREE_KEY_123"
    service.paid_key = "PAID_KEY_999"
    
    # Case 1: FREE USER - Simple Task
    free_user = MagicMock()
    free_user.is_premium = False
    free_user.subscription_status = "free"
    
    plan = service._get_execution_plan(free_user, is_complex=False)
    print(f"Free User (Simple) Plan: {plan}")
    # Plan should be: [(free_key, flash), (gemma_key, gemma), (llama_key, llama)]
    assert plan[0][1] == "google/gemini-3-flash-preview"
    
    # Case 2: FREE USER - Complex Task
    plan = service._get_execution_plan(free_user, is_complex=True)
    print(f"Free User (Complex) Plan: {plan}")
    assert plan[0][1] == "google/gemini-3-flash-preview"

    # Case 3: PREMIUM USER - Simple Task
    paid_user = MagicMock()
    paid_user.is_premium = True
    
    plan = service._get_execution_plan(paid_user, is_complex=False)
    print(f"Paid User (Simple) Plan: {plan}")
    assert plan[0][1] == "google/gemini-3-flash-preview"
    assert plan[1][1] == "google/gemini-3-pro-preview"
    
    # Case 4: PREMIUM USER - Complex Task
    plan = service._get_execution_plan(paid_user, is_complex=True)
    print(f"Paid User (Complex) Plan: {plan}")
    assert plan[0][1] == "google/gemini-3-pro-preview" 
    assert plan[0][0] == "PAID_KEY_999"
    assert plan[1][1] == "google/gemini-3-flash-preview"
    
    print("\n✅ TIERED ROUTING LOGIC PASSED")

if __name__ == "__main__":
    test_tiered_logic()
