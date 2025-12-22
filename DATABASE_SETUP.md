# Database Setup Instructions

## Current Status

✅ Alembic is installed and configured  
⚠️ Docker Desktop service is stopped  
⏳ Need to start Docker to run PostgreSQL

## Steps to Complete Database Setup

### Option A: Start Docker Desktop (Recommended)

1. **Start Docker Desktop**
   - Open Docker Desktop application from Start Menu
   - Wait for it to fully start (icon in system tray will turn green)

2. **Start Database Services**
   ```bash
   cd "d:\Graphology\Master Software\Eduecosystem"
   docker-compose up -d
   ```

3. **Generate and Apply Migration**
   ```bash
   cd backend
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

4. **Verify Tables Created**
   ```bash
   docker exec -it eduecosystem-db-1 psql -U postgres -d eduecosystem -c "\dt"
   ```

### Option B: Manual PostgreSQL Installation

If you prefer not to use Docker:

1. Install PostgreSQL 15+ from https://www.postgresql.org/download/windows/
2. Create database: `CREATE DATABASE eduecosystem;`
3. Update backend/.env (if exists) or use default settings
4. Run migrations as in step 3 above

## What's Been Done

✅ Installed Alembic v1.17.2  
✅ Configured alembic.ini with project settings  
✅ Created env.py with all 11 models imported:
   - users, groups, tasks, handwriting_submissions
   - meditation_sessions, activity_logs, user_rewards
   - mood_entries, exam_sessions, quizzes, study_rooms

## Next Actions

Once Docker is running, run this command to continue:
```bash
cd "d:\Graphology\Master Software\Eduecosystem\backend"
alembic revision --autogenerate -m "Initial migration - create all tables"
alembic upgrade head
```
