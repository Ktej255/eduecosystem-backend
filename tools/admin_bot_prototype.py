import os
import google.generativeai as genai
import json
from typing import Dict, List, Any

# Setup Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Mock Data simulating a database query from SadhanaProgress and User tables
MOCK_DB_DATA = {
    "total_batch2_students": 150,
    "archetype_distribution": {
        "Diligent": 45,       # 30%
        "Hopper": 60,         # 40%
        "Struggling": 30,     # 20%
        "Dormant": 15         # 10%
    },
    "average_streak": 12,
    "struggling_skill": "Digital Literacy & Tool Fluency (Immediate)"
}


def fetch_system_health() -> str:
    """Simulates fetching real-time data from the backend databases."""
    return json.dumps(MOCK_DB_DATA, indent=2)


def generate_admin_response(admin_prompt: str, context_data: str) -> str:
    """Uses LLM to act as the Admin Co-Pilot."""
    if not api_key:
        return f"[MOCK MODE] Received Prompt: {admin_prompt}\nWould normally generate a response based on context: {context_data}"

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_prompt = f"""
        You are the 'Eduecosystem Admin Co-Pilot'. 
        You assist the platform administrator in analyzing student metrics, generating curriculum, and drafting communications.
        
        CURRENT SYSTEM HEALTH DATA:
        {context_data}
        
        Admin Request: {admin_prompt}
        
        Provide a concise, professional, and highly actionable response. Format output in Markdown.
        """
        
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {e}"


def run_admin_bot():
    print("=======================================================")
    print("🤖 ADMIN COMPREHENSIVE BOT - PROTOTYPE INIT")
    print("=======================================================\n")
    
    print("📊 Fetching real-time system context (Simulated)...")
    context = fetch_system_health()
    print("System context loaded.\n")
    
    prompts = [
        "What is the current distribution of student archetypes in Batch 2?",
        "Draft a short, encouraging email targeted specifically at the 'Hopper' archetype to help them build a consistent streak.",
        "Based on the struggling skill in the system data, suggest one new 'Daily Mission' we should assign to students."
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n🗣️ ADMIN PROMPT #{i}: {prompt}")
        print("⏳ Generating response...")
        response = generate_admin_response(prompt, context)
        print("\n" + "="*40)
        print(f"🤖 BOT RESPONSE:\n{response}")
        print("="*40 + "\n")

if __name__ == "__main__":
    run_admin_bot()
