@echo off
REM ============================================================================
REM Indian Payment Gateways - Quick Setup Script (Windows)
REM Supports: Razorpay, Instamojo, Stripe (INR)
REM ============================================================================

echo.
echo ============================================================================
echo 🇮🇳 Setting up Indian Payment Gateways for LMS...
echo ============================================================================
echo.

REM ============================================================================
REM Step 1: Check Prerequisites
REM ============================================================================

echo 📋 Checking prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
echo ✅ Python found
python --version

REM Check pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip not found. Please install pip
    pause
    exit /b 1
)
echo ✅ pip found

echo.

REM ============================================================================
REM Step 2: Install Python Dependencies
REM ============================================================================

echo 📦 Installing Python payment gateway packages...
echo.

pip install razorpay stripe --quiet
if %errorlevel% neq 0 (
    echo ❌ Failed to install packages
    pause
    exit /b 1
)
echo ✅ Installed: razorpay, stripe

echo.

REM ============================================================================
REM Step 3: Create/Update Environment Variables
REM ============================================================================

echo ⚙️ Setting up environment variables...
echo.

set ENV_FILE=.env

if not exist "%ENV_FILE%" (
    echo Creating new .env file...
    (
        echo # Database
        echo DATABASE_URL=postgresql://user:password@localhost/eduecosystem
        echo.
        echo # Security
        echo SECRET_KEY=your-super-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # CORS
        echo BACKEND_CORS_ORIGINS=["http://localhost:3000"]
        echo.
        echo # ============================================================================
        echo # PAYMENT GATEWAYS (INR^)
        echo # ============================================================================
        echo.
        echo # Razorpay (Primary - Most Popular in India^)
        echo RAZORPAY_KEY_ID=rzp_test_CHANGE_ME
        echo RAZORPAY_KEY_SECRET=CHANGE_ME
        echo.
        echo # Instamojo
        echo INSTAMOJO_API_KEY=test_CHANGE_ME
        echo INSTAMOJO_AUTH_TOKEN=test_CHANGE_ME
        echo INSTAMOJO_ENDPOINT=https://test.instamojo.com/api/1.1/
        echo.
        echo # Stripe
        echo STRIPE_SECRET_KEY=sk_test_CHANGE_ME
        echo STRIPE_WEBHOOK_SECRET=whsec_CHANGE_ME
        echo.
        echo # Frontend URL
        echo FRONTEND_URL=http://localhost:3000
    ) > "%ENV_FILE%"
    echo ✅ Created .env file
) else (
    echo ⚠️ .env file already exists
    echo Check and update payment gateway keys manually
)

echo.

REM ============================================================================
REM Step 4: Database Migration
REM ============================================================================

echo 🗄️ Running database migrations...
echo.

REM Check if alembic is installed
python -c "import alembic" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing alembic...
    pip install alembic --quiet
)

REM Generate migration
echo Generating migration for payment gateways...
alembic revision --autogenerate -m "add_multi_gateway_payment_support"

REM Apply migration
echo Applying migrations...
alembic upgrade head

if %errorlevel% neq 0 (
    echo ⚠️ Migration had issues, but continuing...
) else (
    echo ✅ Database migrations complete
)

echo.

REM ============================================================================
REM Step 5: Display Next Steps
REM ============================================================================

echo.
echo ============================================================================
echo 🎉 Payment Gateway Setup Complete!
echo ============================================================================
echo.
echo 📝 IMPORTANT: Update your .env file with real API keys!
echo.
echo 1️⃣  Get Razorpay Test Keys:
echo    → Visit: https://dashboard.razorpay.com/signin
echo    → Go to: Settings ^> API Keys ^> Generate Test Key
echo    → Update: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET
echo.
echo 2️⃣  Get Instamojo Test Keys:
echo    → Visit: https://www.instamojo.com/accounts/login/
echo    → Go to: Settings ^> API ^& Plugins
echo    → Update: INSTAMOJO_API_KEY and INSTAMOJO_AUTH_TOKEN
echo.
echo 3️⃣  Get Stripe Test Keys:
echo    → Visit: https://dashboard.stripe.com/login
echo    → Go to: Developers ^> API keys (Test mode)
echo    → Update: STRIPE_SECRET_KEY
echo.
echo 4️⃣  Start the backend server:
echo    → uvicorn app.main:app --reload --port 8000
echo.
echo 5️⃣  Test payment endpoints:
echo    → Open: http://localhost:8000/docs
echo    → Test: POST /course-payments/create-razorpay-order
echo.
echo ============================================================================
echo.
echo 📚 For detailed instructions, see: INDIAN_PAYMENT_SETUP.md
echo.

pause
