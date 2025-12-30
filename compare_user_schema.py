import psycopg2
from app.models.user import User

def compare_schema():
    try:
        conn = psycopg2.connect('postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod')
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
        db_cols = set(c[0] for c in cur.fetchall())
        
        # Get columns from SQLAlchemy model
        model_cols = set()
        for attr in dir(User):
            val = getattr(User, attr)
            if hasattr(val, 'property') and hasattr(val.property, 'columns'):
                model_cols.add(attr)
        
        missing_in_db = model_cols - db_cols
        print(f"Columns in Model: {model_cols}")
        print(f"Columns in DB: {db_cols}")
        print(f"Missing in DB: {missing_in_db}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    compare_schema()
