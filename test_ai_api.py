"""
Direct test of OpenRouter API - Run this to see exact errors
"""
import asyncio
import openai

# Test each model directly
MODELS = [
    {
        "name": "meta-llama/llama-3.3-70b-instruct:free",
        "key": "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",
    },
    {
        "name": "google/gemini-2.0-flash-exp:free",
        "key": "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",
    },
    {
        "name": "google/gemma-3-27b-it",
        "key": "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",
    },
]


async def test_model(model_name: str, api_key: str):
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")
    
    client = openai.AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Say hello in one word."}
            ],
            max_tokens=10,
            temperature=0.3,
            extra_headers={
                "HTTP-Referer": "https://eduecosystem.com",
                "X-Title": "Test",
            }
        )
        print(f"✅ SUCCESS: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        return False


async def main():
    print("\n" + "="*60)
    print("OPENROUTER API TEST")
    print("="*60)
    
    results = []
    for model in MODELS:
        success = await test_model(model["name"], model["key"])
        results.append((model["name"], success))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✅ Working" if success else "❌ Failed"
        print(f"  {status}: {name}")


if __name__ == "__main__":
    asyncio.run(main())
