"""
Seed Meditation Processes Data - With Video URLs
"""
from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eduecosystem.db")

# Sample video URL for testing
SAMPLE_VIDEO = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

# Format: (name, description, order, duration_min, level, video_url)
MEDITATION_PROCESSES = [
    ("Relaxation", "Complete body relaxation from head to toe", 1, 3, 1, SAMPLE_VIDEO),
    ("Breath Awareness", "Observe natural breathing without controlling", 2, 3, 1, SAMPLE_VIDEO),
    ("Counting Breath", "Count breaths from 1 to 10, then restart", 3, 3, 1, SAMPLE_VIDEO),
    ("Ajna Focus", "Focus attention on the third eye center", 4, 3, 1, SAMPLE_VIDEO),
    ("Om Chanting", "Mental chanting of Om with each breath", 5, 3, 1, SAMPLE_VIDEO),
    ("Light Visualization", "Visualize pure white light at the third eye", 6, 3, 1, SAMPLE_VIDEO),
    ("Heart Opening", "Feel warmth and expansion in the heart center", 7, 3, 1, SAMPLE_VIDEO),
    ("Energy Awareness", "Feel subtle energy in the body", 8, 3, 1, SAMPLE_VIDEO),
    ("Silence", "Rest in complete inner silence", 9, 3, 1, SAMPLE_VIDEO),
    ("Gratitude", "Feel deep gratitude for life and existence", 10, 3, 1, SAMPLE_VIDEO),
    ("Intention Setting", "Set positive intentions for the day", 11, 2, 1, SAMPLE_VIDEO),
    ("Gentle Awakening", "Slowly return to normal awareness", 12, 2, 1, SAMPLE_VIDEO),
]

def seed():
    print("=" * 50)
    print("MEDITATION DATA SEEDER")  
    print("=" * 50)
    print(f"Database: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    if 'meditation_processes' not in inspector.get_table_names():
        print("\nERROR: meditation_processes table does not exist!")
        print("Run migrations first: alembic upgrade head")
        return
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM meditation_processes"))
        existing_count = result.scalar()
        
        if existing_count > 0:
            print(f"\nDatabase already has {existing_count} meditation processes")
            return
        
        for name, desc, order_num, duration, level, video_url in MEDITATION_PROCESSES:
            sql = text(
                'INSERT INTO meditation_processes '
                '(name, description, "order", duration_minutes, level, is_active, video_url) '
                'VALUES (:name, :desc, :order_num, :duration, :level, 1, :video_url)'
            )
            conn.execute(sql, {
                "name": name, 
                "desc": desc, 
                "order_num": order_num, 
                "duration": duration, 
                "level": level,
                "video_url": video_url
            })
        
        conn.commit()
        print(f"\nSuccessfully added {len(MEDITATION_PROCESSES)} meditation processes with video URLs!")
        
        for i, (name, _, _, duration, _, _) in enumerate(MEDITATION_PROCESSES, 1):
            print(f"  {i:2}. {name} ({duration} min)")
        
        print("\nDone!")

if __name__ == "__main__":
    seed()
