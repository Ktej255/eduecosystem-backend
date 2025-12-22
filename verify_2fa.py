import requests
import pyotp

# Configuration
API_URL = "http://localhost:8000/api/v1"
EMAIL = "test_2fa@example.com"
PASSWORD = "password123"
USERNAME = "Test 2FA User"


def print_step(msg):
    print(f"\n[STEP] {msg}")


def run_verification():
    session = requests.Session()

    # 1. Register User
    print_step("Registering User")
    reg_data = {
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": USERNAME,
        "username": EMAIL.split("@")[0],
    }
    # Try to register, if exists, login
    resp = session.post(f"{API_URL}/login/register", json=reg_data)
    if resp.status_code == 200:
        print("User registered.")
    elif resp.status_code == 400 and "exists" in resp.text:
        print("User already exists.")
    else:
        print(f"Registration failed: {resp.text}")
        return

    # 2. Login (Initial)
    print_step("Logging in (Initial)")
    login_data = {"username": EMAIL, "password": PASSWORD}
    resp = session.post(f"{API_URL}/login/access_token", data=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return

    token_data = resp.json()
    access_token = token_data["access_token"]
    require_2fa = token_data.get("require_2fa", False)
    print(f"Logged in. Require 2FA: {require_2fa}")

    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. Setup 2FA
    print_step("Setting up 2FA")
    # First, check status
    resp = session.get(f"{API_URL}/2fa/status", headers=headers)
    if resp.json()["is_enabled"]:
        print("2FA already enabled. Disabling first...")
        # Need a code to disable? Yes.
        # This might fail if we don't have the secret.
        # For testing, we might need to manually reset DB or use a known secret if possible.
        # But let's assume fresh user or we can't proceed easily without manual intervention.
        print(
            "Cannot proceed with automated test on already enabled user without current secret."
        )
        return

    resp = session.post(f"{API_URL}/2fa/setup", headers=headers)
    if resp.status_code != 200:
        print(f"Setup failed: {resp.text}")
        return

    setup_data = resp.json()
    secret = setup_data["secret"]
    print(f"Got secret: {secret}")

    # 4. Verify Setup
    print_step("Verifying Setup")
    totp = pyotp.TOTP(secret)
    code = totp.now()

    verify_data = {"secret": secret, "code": code}
    resp = session.post(
        f"{API_URL}/2fa/verify-setup", json=verify_data, headers=headers
    )
    if resp.status_code != 200:
        print(f"Verify setup failed: {resp.text}")
        return

    print("2FA Enabled!")
    backup_codes = resp.json()["backup_codes"]
    print(f"Backup codes: {backup_codes}")

    # 5. Re-login (Should require 2FA)
    print_step("Re-logging in (Expect 2FA)")
    resp = session.post(f"{API_URL}/login/access_token", data=login_data)
    token_data = resp.json()
    temp_token = token_data["access_token"]
    require_2fa = token_data.get("require_2fa", False)

    if not require_2fa:
        print("ERROR: Login did not require 2FA!")
        return
    print("Login required 2FA as expected.")

    # 6. Verify Login
    print_step("Verifying Login with Code")
    # Wait a bit or generate new code? TOTP is time based.
    # Same code might work if within window, but let's generate fresh.
    code = totp.now()

    verify_login_headers = {"Authorization": f"Bearer {temp_token}"}
    verify_login_data = {
        "code": code,
        "user_id": 0,
    }  # user_id ignored by endpoint logic using token

    resp = session.post(
        f"{API_URL}/2fa/verify-login",
        json=verify_login_data,
        headers=verify_login_headers,
    )
    if resp.status_code != 200:
        print(f"Verify login failed: {resp.text}")
        return

    final_token = resp.json()["access_token"]
    print("Got final access token!")

    # 7. Disable 2FA (Cleanup)
    print_step("Disabling 2FA")
    final_headers = {"Authorization": f"Bearer {final_token}"}
    code = totp.now()
    disable_data = {"code": code}

    resp = session.post(
        f"{API_URL}/2fa/disable", json=disable_data, headers=final_headers
    )
    if resp.status_code == 200:
        print("2FA Disabled successfully.")
    else:
        print(f"Disable failed: {resp.text}")


if __name__ == "__main__":
    run_verification()
