import os
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from typing import List, Dict, Optional
import json

# Setup Gemini API key (Ensure this is set in your .env or environment)
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# The Immediate and Mid-term skills to focus on for Daily Missions (Mocked for Prototype)
TARGET_SKILLS = [
    "Prompt Engineering",
    "Automation & Scripting",
    "Digital Literacy & Tool Fluency",
    "Pattern Recognition",
    "Systems Thinking",
    "Analytical Reasoning"
]

RSS_FEEDS = {
    "Technology News": "https://techcrunch.com/feed/",
    "AI Trends": "https://www.technologyreview.com/feed/",
}

def fetch_rss_feed(url: str, limit: int = 3) -> List[Dict]:
    """Fetches and parses an RSS feed, returning the top N items."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        items = []
        
        # Navigate standard RSS format (channel -> item)
        for item in root.findall('.//item')[:limit]:
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            
            items.append({
                'title': title.text if title is not None else 'No Title',
                'link': link.text if link is not None else '#',
                'snippet': description.text[:200] + '...' if description is not None and description.text else 'No Snippet'
            })
        return items
    except Exception as e:
        print(f"Error fetching feed {url}: {e}")
        return []

def generate_daily_mission(article: Dict) -> Optional[Dict]:
    """Uses Gemini LLM to categorize the article and create a 'Daily Mission'."""
    if not api_key:
        # Fallback if no API key is set for local testing
        return {
            "title": article['title'],
            "link": article['link'],
            "mapped_skill": "Prompt Engineering",
            "mission_title": f"Explore: {article['title']}",
            "mission_task": f"Read this article and reflect on its impact: {article['link']}. How would you automate this?"
        }

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert curriculum designer. 
        Read the following tech news snippet:
        Title: {article['title']}
        Snippet: {article['snippet']}
        
        Target Skills constraint: {', '.join(TARGET_SKILLS)}
        
        Task:
        1. Select the SINGLE most relevant skill from the target skills list above that this news applies to.
        2. Create a short, actionable 15-minute "Daily Mission" for a student based on this news.
        
        Format your response as valid JSON like this:
        {{
            "mapped_skill": "The chosen skill",
            "mission_title": "A catchy title for the mission",
            "mission_task": "The 2-3 sentence actionable task instruction"
        }}
        """
        
        response = model.generate_content(prompt)
        # Clean response if wrapped in markdown code blocks
        clean_text = response.text.strip()
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:-3]
            
        result = json.loads(clean_text)
        return {
            "title": article['title'],
            "link": article['link'],
            "mapped_skill": result.get("mapped_skill", "General Awareness"),
            "mission_title": result.get("mission_title", "Read & Reflect"),
            "mission_task": result.get("mission_task", "Review the attached article.")
        }
    except Exception as e:
        print(f"Error generating mission for '{article['title']}': {e}")
        return None

def run_research_agent():
    print("🚀 Initializing AI Research Agent (Industry Scanner)...")
    missions = []
    
    for category, feed_url in RSS_FEEDS.items():
        print(f"\n📡 Scanning {category} ({feed_url})...")
        articles = fetch_rss_feed(feed_url, limit=2) # Get top 2 articles per feed
        
        if not articles:
            print("❌ No articles fetched.")
            continue
            
        for article in articles:
            print(f"🧠 Processing: {article['title']}")
            mission = generate_daily_mission(article)
            if mission:
                missions.append(mission)
                
    print("\n=======================================================")
    print("✅ GENERATED DAILY MISSIONS")
    print("=======================================================\n")
    
    for i, m in enumerate(missions, 1):
        print(f"Mission #{i}: {m['mission_title']}")
        print(f"🔗 Source: {m['title']}")
        print(f"🎯 Mapped Skill: {m['mapped_skill']}")
        print(f"📝 Task: {m['mission_task']}")
        print("-" * 50)

if __name__ == "__main__":
    run_research_agent()
