from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.api.api_v1.endpoints.planner import get_all_topics

def list_first_days_topics():
    all_topics = get_all_topics()
    num_topics = len(all_topics)
    topics_per_day = max(1, num_topics // 40)
    
    print(f"Total topics: {num_topics}")
    print(f"Topics per day: {topics_per_day}")
    
    for day in range(1, 6):
        start_idx = (day - 1) * topics_per_day
        day_topics = all_topics[start_idx:start_idx + topics_per_day]
        print(f"Day {day}: {[t['id'] for t in day_topics]}")

if __name__ == "__main__":
    list_first_days_topics()
