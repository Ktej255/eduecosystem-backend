# Quick Database Setup Guide

## ⚠️ Docker Desktop Issue Detected

Docker Desktop is not starting properly. Here are **2 alternative options**:

---

## Option 1: Use SQLite (Easiest - No Installation Required)

### Step 1: Switch to SQLite

Update `backend/app/core/config.py` line 11 to:

```python
DATABASE_URL: str = "sqlite:///./eduecosystem.db"
```

### Step 2: Create Tables

```bash
cd "d:\Graphology\Master Software\Eduecosystem\backend"
python init_db.py
```

### Step 3: Start Backend

```bash
python -m uvicorn main:app --reload
```

**Done! ✅** Your backend will run with SQLite database.

---

## Option 2: Install PostgreSQL Manually

### Step 1: Download PostgreSQL
- Get from: https://www.postgresql.org/download/windows/
- Install PostgreSQL 15

### Step 2: Create Database

Open "SQL Shell (psql)" from Start Menu:
```sql
CREATE DATABASE eduecosystem;
```

### Step 3: Create Tables

```bash
cd "d:\Graphology\Master Software\Eduecosystem\backend"
python init_db.py
```

### Step 4: Start Backend

```bash
python -m uvicorn main:app --reload
```

---

## Option 3: Fix Docker Desktop (Advanced)

1. **Completely restart Docker:**
   - Right-click Docker Desktop system tray icon
   - Select "Quit Docker Desktop"
   - Wait 10 seconds
   - Start Docker Desktop from Start Menu
   - Wait 2-3 minutes for full startup

2. **Then run:**
   ```bash
   cd "d:\Graphology\Master Software\Eduecosystem"
   docker-compose up -d
   cd backend
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

---

## Recommendation for Beginners

**Use Option 1 (SQLite)** - It's the fastest and requires no additional software installation. SQLite is perfect for development and learning!

The `init_db.py` script is ready in the backend folder. Just update the config file and run it! 🚀
