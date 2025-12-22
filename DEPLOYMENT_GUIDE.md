# Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Eduecosystem backend to production.

---

## Prerequisites

### Required
- ✅ Python 3.8+
- ✅ PostgreSQL 12+
- ✅ SSL certificates for HTTPS
- ✅ Domain name configured

### Optional
- Redis (for caching and performance)
- SMTP server (for email notifications)
- CDN (for static file delivery)
- Error tracking service (Sentry, Rollbar)

---

## Step 1: Environment Configuration

### Generate SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Save this key securely!** You'll need it for the next step.

### Create Production .env File
Create `.env` in the backend directory:

```bash
# Environment
ENVIRONMENT=production

# Security
SECRET_KEY=<paste-your-generated-secret-key-here>

# Database - PostgreSQL (REQUIRED for production)
DATABASE_URL=postgresql://username:password@hostname:5432/database_name

# Redis (Optional but recommended)
REDIS_URL=redis://hostname:6379/0

# CORS - Update with your frontend domains
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME=Eduecosystem

# Additional Settings
PROJECT_NAME="Eduecosystem Production"
API_V1_STR=/api/v1

# Sentry (Error Tracking)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

> [!CAUTION]
> **Never commit the `.env` file to version control!**
> Add it to `.gitignore` to prevent accidental exposure.

---

## Step 2: Database Setup

### PostgreSQL Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Production Database
```bash
# Login as postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE eduecosystem_prod;
CREATE USER eduecosystem_user WITH PASSWORD 'strong-password-here';
GRANT ALL PRIVILEGES ON DATABASE eduecosystem_prod TO eduecosystem_user;
\q
```

### Run Database Migrations
```bash
cd backend

# Install Alembic if not installed
pip install alembic

# Run migrations
alembic upgrade head
```

---

## Step 3: Application Setup

### Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn
```

### Verify Configuration
```bash
# Test configuration loading
python -c "from app.core.config import settings; print('✅ Config valid')"

# Test database connection
python -c "from app.db.session import engine; engine.connect(); print('✅ Database connected')"
```

---

## Step 4: Run Application

### Option A: Gunicorn (Recommended)
```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Option B: Uvicorn
```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

### Create Systemd Service (Linux)
Create `/etc/systemd/system/eduecosystem.service`:

```ini
[Unit]
Description=Eduecosystem Backend API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/eduecosystem/backend
Environment="PATH=/opt/eduecosystem/backend/venv/bin"
ExecStart=/opt/eduecosystem/backend/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable eduecosystem
sudo systemctl start eduecosystem
sudo systemctl status eduecosystem
```

---

## Step 5: Reverse Proxy (Nginx)

### Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### Configure Nginx
Create `/etc/nginx/sites-available/eduecosystem`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Client upload size limit
    client_max_body_size 100M;

    # API endpoints
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (for load balancer)
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        access_log off;
    }

    # Static files
    location /uploads {
        alias /opt/eduecosystem/backend/uploads;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Frontend (if serving from same domain)
    location / {
        root /opt/eduecosystem/frontend/build;
        try_files $uri $uri/ /index.html;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/eduecosystem /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Step 6: Health Check Verification

### Test Health Endpoint
```bash
curl https://yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": 1732426315.123,
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache connection successful"
    }
  }
}
```

### Configure Load Balancer Health Check
If using a load balancer (AWS ALB, GCP LB, etc.):

**AWS Application Load Balancer:**
```yaml
health_check:
  path: /health
  protocol: HTTPS
  port: 443
  interval: 30
  timeout: 5
  healthy_threshold: 2
  unhealthy_threshold: 3
  matcher: 200
```

---

## Step 7: Monitoring & Logging

### Application Logs
```bash
# View systemd logs
sudo journalctl -u eduecosystem -f

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Sentry Integration
Already configured via `SENTRY_DSN` in `.env`. Errors will be automatically reported.

### CloudWatch (AWS)
Install CloudWatch agent:
```bash
sudo apt install amazon-cloudwatch-agent

# Configure log shipping
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

---

## Step 8: Security Hardening

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Fail2Ban (Brute Force Protection)
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Database Connection Security
- Use strong passwords (32+ characters)
- Enable SSL for database connections
- Restrict database access to application server IPs only
- Regular backup schedule

---

## Step 9: Backup Strategy

### Database Backups
Create backup script `/opt/eduecosystem/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/eduecosystem/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/eduecosystem_$DATE.sql.gz"

# Create backup
pg_dump -U eduecosystem_user -h localhost eduecosystem_prod | gzip > "$BACKUP_FILE"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

Schedule with cron:
```bash
# Run daily at 2 AM
0 2 * * * /opt/eduecosystem/backup.sh >> /var/log/eduecosystem-backup.log 2>&1
```

### File Uploads Backup
```bash
# Sync to S3 (AWS)
aws s3 sync /opt/eduecosystem/backend/uploads s3://your-bucket/uploads --delete
```

---

## Step 10: Performance Optimization

### Redis Caching (Optional)
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: bind 127.0.0.1
# Set: requirepass strong-password-here

# Restart Redis
sudo systemctl restart redis
```

### Database Performance
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_courses_created_at ON courses(created_at);
CREATE INDEX idx_enrollments_user_course ON enrollments(user_id, course_id);
```

### Application Performance
- Enable gzip compression in Nginx
- Use CDN for static assets
- Implement database connection pooling (already configured in SQLAlchemy)
- Monitor slow queries and optimize

---

## Deployment Checklist

### Pre-Deployment
- [ ] Generate and secure SECRET_KEY
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis (optional)
- [ ] Configure SMTP settings
- [ ] Update CORS origins to production domains
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Review and update all environment variables
- [ ] Test configuration locally with production settings

### Deployment
- [ ] Install dependencies
- [ ] Run database migrations
- [ ] Verify database connection
- [ ] Start application server
- [ ] Configure Nginx reverse proxy
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up systemd service

### Post-Deployment
- [ ] Verify `/health` endpoint returns healthy
- [ ] Test API endpoints
- [ ] Configure monitoring and alerts
- [ ] Set up log aggregation
- [ ] Configure automated backups
- [ ] Test error tracking (Sentry)
- [ ] Document production credentials securely
- [ ] Create runbook for common issues

### Ongoing
- [ ] Monitor application health daily
- [ ] Review error logs weekly
- [ ] Rotate SECRET_KEY every 90 days
- [ ] Update SSL certificates before expiry
- [ ] Apply security updates monthly
- [ ] Review and optimize database queries
- [ ] Monitor disk space and performance

---

## Troubleshooting

### Issue: Application won't start
**Check:**
```bash
# Verify Python environment
python --version

# Check dependencies
pip list | grep fastapi

# Test configuration
python -c "from app.core.config import settings; print(settings.ENVIRONMENT)"

# Check logs
sudo journalctl -u eduecosystem -n 50
```

### Issue: Database connection failed
**Check:**
```bash
# Test PostgreSQL connection
psql -U eduecosystem_user -h localhost -d eduecosystem_prod

# Verify DATABASE_URL format
echo $DATABASE_URL

# Check PostgreSQL service
sudo systemctl status postgresql
```

### Issue: Health check failing
**Check:**
```bash
# Direct API test
curl http://localhost:8000/health

# Check Nginx configuration
sudo nginx -t

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Issue: SECRET_KEY validation error
**Error:** `ValueError: SECRET_KEY must be set in production environment`

**Solution:**
```bash
# Verify ENVIRONMENT is set
echo $ENVIRONMENT

# Ensure SECRET_KEY is set and has 32+ characters
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file with the generated key
```

---

## Support Resources

- **Backend Repository:** [Link to your repo]
- **API Documentation:** https://yourdomain.com/api/v1/docs
- **Health Check:** https://yourdomain.com/health
- **Security Guide:** [SECURITY_IMPROVEMENTS.md](file:///d:/Graphology/Master%20Software/Eduecosystem/backend/SECURITY_IMPROVEMENTS.md)
- **Production Improvements:** [PRODUCTION_IMPROVEMENTS.md](file:///d:/Graphology/Master%20Software/Eduecosystem/backend/PRODUCTION_IMPROVEMENTS.md)

---

## Next Steps

1. **Set up monitoring:** CloudWatch, Datadog, or New Relic
2. **Configure CI/CD:** GitHub Actions, GitLab CI, or Jenkins
3. **Implement auto-scaling:** Based on CPU/memory usage
4. **Set up staging environment:** Mirror production for testing
5. **Create disaster recovery plan:** Backup restoration procedures
6. **Document incident response:** Procedures for downtime scenarios

---

> [!IMPORTANT]
> **Always test in a staging environment before deploying to production!**

> [!WARNING]
> **Never commit production credentials to version control.**
> Use environment variables or secrets management systems.
