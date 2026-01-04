import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def verify_db_columns():
    db_path = "eduecosystem.db"
    print(f"Checking database: {db_path}")
    
    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    expected_columns = ['is_ras_authorized', 'is_batch1_authorized', 'is_batch2_authorized']
    
    print("\nColumn Status:")
    all_found = True
    for col in expected_columns:
        if col in columns:
            print(f"[OK] {col} exists")
        else:
            print(f"[MISSING] {col} is not in the table")
            all_found = False
            
    if all_found:
        print("\nAll required columns are present in the 'users' table.")
    else:
        print("\nSome columns are missing. Please check the migration process.")

if __name__ == "__main__":
    verify_db_columns()
