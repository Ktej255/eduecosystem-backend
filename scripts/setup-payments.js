/**
 * Quick Setup Script for Indian Payment Gateways
 * Automates environment setup and verification
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const colors = {
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    red: '\x1b[31m',
    reset: '\x1b[0m',
    cyan: '\x1b[36m'
};

const log = {
    success: (msg) => console.log(`${colors.green}✅ ${msg}${colors.reset}`),
    warning: (msg) => console.log(`${colors.yellow}⚠️  ${msg}${colors.reset}`),
    error: (msg) => console.log(`${colors.red}❌ ${msg}${colors.reset}`),
    info: (msg) => console.log(`${colors.cyan}ℹ️  ${msg}${colors.reset}`)
};

console.log('\n🇮🇳 Indian Payment Gateway Setup\n');

// Check if .env exists
const envPath = path.join(__dirname, '..', '.env');
let envExists = fs.existsSync(envPath);

if (!envExists) {
    log.info('Creating .env file template...');
    const envTemplate = `# Database
DATABASE_URL=postgresql://user:password@localhost/eduecosystem

# Payment Gateways
RAZORPAY_KEY_ID=rzp_test_CHANGE_ME
RAZORPAY_KEY_SECRET=CHANGE_ME
INSTAMOJO_API_KEY=test_CHANGE_ME
INSTAMOJO_AUTH_TOKEN=test_CHANGE_ME
INSTAMOJO_ENDPOINT=https://test.instamojo.com/api/1.1/
STRIPE_SECRET_KEY=sk_test_CHANGE_ME
STRIPE_WEBHOOK_SECRET=whsec_CHANGE_ME
FRONTEND_URL=http://localhost:3000
`;
    fs.writeFileSync(envPath, envTemplate);
    log.success('Created .env file');
} else {
    log.warning('.env file already exists');
}

// Install Python packages
log.info('Installing Python dependencies...');
try {
    execSync('pip install razorpay stripe', { stdio: 'inherit' });
    log.success('Installed razorpay and stripe packages');
} catch (error) {
    log.error('Failed to install Python packages');
    process.exit(1);
}

// Run Alembic migration
log.info('Running database migrations...');
try {
    execSync('alembic upgrade head', { stdio: 'inherit', cwd: path.join(__dirname, '..') });
    log.success('Database migrations complete');
} catch (error) {
    log.warning('Migration failed or already applied');
}

// Display next steps
console.log('\n' + '='.repeat(60));
console.log(colors.green + '🎉 Setup Complete!' + colors.reset);
console.log('='.repeat(60) + '\n');

console.log('📝 Next Steps:\n');
console.log('1. Update .env with your API keys:');
console.log('   - Razorpay: https://dashboard.razorpay.com');
console.log('   - Instamojo: https://www.instamojo.com');
console.log('   - Stripe: https://dashboard.stripe.com\n');
console.log('2. Start backend: uvicorn app.main:app --reload');
console.log('3. Test API: http://localhost:8000/docs\n');
console.log('Test cards available in INDIAN_PAYMENT_SETUP.md\n');
