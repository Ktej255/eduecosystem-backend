#!/bin/bash

# ============================================================================
# Indian Payment Gateways - Quick Setup Script
# Supports: Razorpay, Instamojo, Stripe (INR)
# ============================================================================

set -e  # Exit on error

echo "🇮🇳 Setting up Indian Payment Gateways for LMS..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================

echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL CLI not found. Make sure PostgreSQL is running.${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL found${NC}"
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip not found. Please install pip${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip found${NC}"

echo ""

# ============================================================================
# Step 2: Install Python Dependencies
# ============================================================================

echo "📦 Installing Python payment gateway packages..."

pip3 install razorpay stripe --quiet
echo -e "${GREEN}✅ Installed: razorpay, stripe${NC}"

echo ""

# ============================================================================
# Step 3: Create/Update Environment Variables
# ============================================================================

echo "⚙️  Setting up environment variables..."

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating new .env file..."
    cat > "$ENV_FILE" << 'EOF'
# Database
DATABASE_URL=postgresql://user:password@localhost/eduecosystem

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# ============================================================================
# PAYMENT GATEWAYS (INR)
# ============================================================================

# Razorpay (Primary - Most Popular in India)
# Sign up: https://razorpay.com
# Get keys: Dashboard > Settings > API Keys > Generate Test Key
RAZORPAY_KEY_ID=rzp_test_CHANGE_ME
RAZORPAY_KEY_SECRET=CHANGE_ME

# Instamojo (Alternative Indian Gateway)
# Sign up: https://www.instamojo.com
# Get keys: Settings > API & Plugins > Generate Test Credentials
INSTAMOJO_API_KEY=test_CHANGE_ME
INSTAMOJO_AUTH_TOKEN=test_CHANGE_ME
INSTAMOJO_ENDPOINT=https://test.instamojo.com/api/1.1/

# Stripe (International Cards)
# Sign up: https://dashboard.stripe.com/register
# Get keys: Developers > API keys (Test mode)
STRIPE_SECRET_KEY=sk_test_CHANGE_ME
STRIPE_WEBHOOK_SECRET=whsec_CHANGE_ME

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Genkit AI (Optional)
GENKIT_URL=http://localhost:3400
GOOGLE_API_KEY=your-google-ai-key
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists. Backing up to .env.backup${NC}"
    cp "$ENV_FILE" "${ENV_FILE}.backup"
    
    # Add payment gateway vars if not present
    if ! grep -q "RAZORPAY_KEY_ID" "$ENV_FILE"; then
        echo "" >> "$ENV_FILE"
        echo "# Payment Gateways (Added by setup script)" >> "$ENV_FILE"
        echo "RAZORPAY_KEY_ID=rzp_test_CHANGE_ME" >> "$ENV_FILE"
        echo "RAZORPAY_KEY_SECRET=CHANGE_ME" >> "$ENV_FILE"
        echo "INSTAMOJO_API_KEY=test_CHANGE_ME" >> "$ENV_FILE"
        echo "INSTAMOJO_AUTH_TOKEN=test_CHANGE_ME" >> "$ENV_FILE"
        echo "INSTAMOJO_ENDPOINT=https://test.instamojo.com/api/1.1/" >> "$ENV_FILE"
        echo "STRIPE_SECRET_KEY=sk_test_CHANGE_ME" >> "$ENV_FILE"
        echo "STRIPE_WEBHOOK_SECRET=whsec_CHANGE_ME" >> "$ENV_FILE"
        echo -e "${GREEN}✅ Added payment gateway variables to .env${NC}"
    fi
fi

echo ""

# ============================================================================
# Step 4: Database Migration
# ============================================================================

echo "🗄️  Running database migrations..."

# Check if alembic is installed
if ! python3 -c "import alembic" 2>/dev/null; then
    echo "Installing alembic..."
    pip3 install alembic --quiet
fi

# Generate migration
echo "Generating migration for payment gateways..."
alembic revision --autogenerate -m "add_multi_gateway_payment_support" || true

# Apply migration
echo "Applying migrations..."
alembic upgrade head

echo -e "${GREEN}✅ Database migrations complete${NC}"
echo ""

# ============================================================================
# Step 5: Verify Setup
# ============================================================================

echo "🔍 Verifying setup..."

# Check if course_payments table exists
PAYMENT_TABLE_EXISTS=$(psql $DATABASE_URL -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'course_payments');" 2>/dev/null || echo "false")

if [ "$PAYMENT_TABLE_EXISTS" = " t" ]; then
    echo -e "${GREEN}✅ course_payments table exists${NC}"
else
    echo -e "${YELLOW}⚠️  Could not verify course_payments table${NC}"
fi

echo ""

# ============================================================================
# Step 6: Display Next Steps
# ============================================================================

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Payment Gateway Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📝 IMPORTANT: Update your .env file with real API keys!"
echo ""
echo "1️⃣  Get Razorpay Test Keys:"
echo "   → Visit: https://dashboard.razorpay.com/signin"
echo "   → Go to: Settings > API Keys > Generate Test Key"
echo "   → Update: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET"
echo ""
echo "2️⃣  Get Instamojo Test Keys:"
echo "   → Visit: https://www.instamojo.com/accounts/login/"
echo "   → Go to: Settings > API & Plugins"
echo "   → Update: INSTAMOJO_API_KEY and INSTAMOJO_AUTH_TOKEN"
echo ""
echo "3️⃣  Get Stripe Test Keys:"
echo "   → Visit: https://dashboard.stripe.com/login"
echo "   → Go to: Developers > API keys (Test mode)"
echo "   → Update: STRIPE_SECRET_KEY"
echo ""
echo "4️⃣  Start the backend server:"
echo "   → cd backend"
echo "   → uvicorn app.main:app --reload --port 8000"
echo ""
echo "5️⃣  Test payment endpoints:"
echo "   → Open: http://localhost:8000/docs"
echo "   → Test: POST /course-payments/create-razorpay-order"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📚 For detailed instructions, see: INDIAN_PAYMENT_SETUP.md"
echo ""
echo "Test credentials available in the setup guide!"
echo ""
