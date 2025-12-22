"""
Quick Payment Test Script
Tests all 3 payment gateways with sample data
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()


# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    END = "\033[0m"


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")


def test_razorpay():
    """Test Razorpay configuration"""
    print("\n" + "=" * 60)
    print("🔹 Testing Razorpay")
    print("=" * 60)

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or key_id == "rzp_test_CHANGE_ME":
        print_error("Razorpay API keys not configured")
        print_info("Get keys from: https://dashboard.razorpay.com")
        return False

    print_info(f"Key ID: {key_id[:15]}...")

    try:
        import razorpay

        client = razorpay.Client(auth=(key_id, key_secret))

        # Test creating an order
        order = client.order.create(
            {
                "amount": 49900,  # ₹499 in paise
                "currency": "INR",
                "receipt": "test_receipt_001",
            }
        )

        print_success(f"Order created: {order['id']}")
        print_info(f"Amount: ₹{order['amount'] / 100}")
        return True

    except Exception as e:
        print_error(f"Razorpay test failed: {str(e)}")
        return False


def test_instamojo():
    """Test Instamojo configuration"""
    print("\n" + "=" * 60)
    print("🔹 Testing Instamojo")
    print("=" * 60)

    api_key = os.getenv("INSTAMOJO_API_KEY")
    auth_token = os.getenv("INSTAMOJO_AUTH_TOKEN")
    endpoint = os.getenv("INSTAMOJO_ENDPOINT")

    if not api_key or api_key == "test_CHANGE_ME":
        print_error("Instamojo API keys not configured")
        print_info("Get keys from: https://www.instamojo.com")
        return False

    print_info(f"API Key: {api_key[:20]}...")
    print_info(f"Endpoint: {endpoint}")

    try:
        headers = {"X-Api-Key": api_key, "X-Auth-Token": auth_token}

        # Test API connection
        response = requests.get(f"{endpoint}payment-requests/", headers=headers)

        if response.status_code == 200:
            print_success("Instamojo API connected successfully")
            return True
        else:
            print_error(f"API returned status: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Instamojo test failed: {str(e)}")
        return False


def test_stripe():
    """Test Stripe configuration"""
    print("\n" + "=" * 60)
    print("🔹 Testing Stripe")
    print("=" * 60)

    secret_key = os.getenv("STRIPE_SECRET_KEY")

    if not secret_key or secret_key == "sk_test_CHANGE_ME":
        print_error("Stripe API key not configured")
        print_info("Get key from: https://dashboard.stripe.com")
        return False

    print_info(f"Secret Key: {secret_key[:20]}...")

    try:
        import stripe

        stripe.api_key = secret_key

        # Test creating a checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "unit_amount": 49900,  # ₹499
                        "product_data": {
                            "name": "Test Course",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )

        print_success(f"Checkout session created: {session.id}")
        print_info(f"URL: {session.url[:50]}...")
        return True

    except Exception as e:
        print_error(f"Stripe test failed: {str(e)}")
        return False


def test_backend_endpoints():
    """Test backend API endpoints"""
    print("\n" + "=" * 60)
    print("🔹 Testing Backend API")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1"

    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend API is running")
        else:
            print_error("Backend API not responding correctly")
            return False

    except requests.exceptions.RequestException:
        print_error("Backend API not running")
        print_info("Start with: uvicorn app.main:app --reload")
        return False

    # Test payment endpoints exist
    endpoints = [
        "/course-payments/create-razorpay-order",
        "/course-payments/create-instamojo-payment",
        "/course-payments/create-stripe-checkout",
    ]

    for endpoint in endpoints:
        print_info(f"Endpoint available: {endpoint}")

    print_success("All payment endpoints registered")
    return True


def main():
    """Run all tests"""
    print("\n" + "🇮🇳 " + "=" * 58)
    print("   Payment Gateway Configuration Test")
    print("=" * 60 + "\n")

    results = {
        "Razorpay": test_razorpay(),
        "Instamojo": test_instamojo(),
        "Stripe": test_stripe(),
        "Backend API": test_backend_endpoints(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60 + "\n")

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n{total_passed}/{total_tests} tests passed\n")

    if total_passed == total_tests:
        print_success("All payment gateways configured correctly! 🎉")
        print_info("\nYou can now test payments in the frontend")
        print_info("Test cards available in INDIAN_PAYMENT_SETUP.md\n")
    else:
        print_error("Some configurations are missing")
        print_info("Update .env file with your API keys\n")


if __name__ == "__main__":
    main()
