"""Fix all missing columns in all tables."""
import sqlite3

db = sqlite3.connect("eduecosystem_v2.db")
c = db.cursor()

# Fix activity_logs table
c.execute("PRAGMA table_info(activity_logs)")
cols = {r[1] for r in c.fetchall()}
print(f"activity_logs columns: {sorted(cols)}")

activity_fixes = {
    "ip_address": "VARCHAR NULL",
    "user_agent": "VARCHAR NULL",
}
for col, typ in activity_fixes.items():
    if col not in cols:
        c.execute(f"ALTER TABLE activity_logs ADD COLUMN {col} {typ}")
        print(f"  Added: {col}")

db.commit()
db.close()
print("Done fixing activity_logs!")
