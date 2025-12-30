import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod')
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
    cols = [c[0] for c in cur.fetchall()]
    print("ALL_COLUMNS:" + ",".join(sorted(cols)))
    conn.close()
except Exception as e:
    print(f"Error: {e}")
