"""
Script to create missing batch1_test_results table directly in production database
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Create batch1_test_results table if not exists
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS batch1_test_results (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            cycle_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            score FLOAT NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_count INTEGER NOT NULL,
            incorrect_count INTEGER NOT NULL,
            unanswered_count INTEGER NOT NULL,
            answers_json TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_batch1_test_results_user_id ON batch1_test_results(user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_batch1_test_results_id ON batch1_test_results(id)"))
    conn.commit()
    print("✓ batch1_test_results table created!")
    
    # Create ras_topic_progress table if not exists
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ras_topic_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            topic_id VARCHAR NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            hours_spent FLOAT DEFAULT 0.0,
            completed_at TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary_text TEXT,
            mastery_level INTEGER DEFAULT 0
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ras_topic_progress_user_id ON ras_topic_progress(user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ras_topic_progress_topic_id ON ras_topic_progress(topic_id)"))
    conn.commit()
    print("✓ ras_topic_progress table created!")
    
    # Create study_sessions table if not exists
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            topic_id INTEGER,
            topic_name VARCHAR,
            session_type VARCHAR,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds INTEGER,
            completed BOOLEAN DEFAULT FALSE,
            comprehension_score FLOAT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_study_sessions_user_id ON study_sessions(user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_study_sessions_topic_id ON study_sessions(topic_id)"))
    conn.commit()
    print("✓ study_sessions table created!")
    
    print("\n✅ All tables created successfully!")
