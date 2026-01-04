import os
import sys
from sqlalchemy import create_engine, text

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def count_rows():
    engine = create_engine(PROD_DB_URL)
    try:
        with engine.connect() as conn:
            count = conn.execute(text("SELECT count(*) FROM ras_topic_progress")).scalar()
            print(f"Total rows in 'ras_topic_progress': {count}")
            if count > 0:
                rows = conn.execute(text("SELECT * FROM ras_topic_progress")).fetchall()
                for r in rows:
                    print(f"Row: {r}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    count_rows()
