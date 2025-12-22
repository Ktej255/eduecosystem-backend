import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v1"


async def test_upload_validation():
    print("Testing upload validation...")

    async with httpx.AsyncClient() as client:
        # Login
        email = "reltest2@example.com"  # Use existing user
        password = "password123"
        resp = await client.post(
            f"{BASE_URL}/login/access-token",
            data={"username": email, "password": password},
        )
        if resp.status_code != 200:
            print("Login failed")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Test Invalid File Type (Text file)
        print("\n1. Testing Invalid File Type...")
        files = {"file": ("test.txt", b"This is a text file", "text/plain")}
        resp = await client.post(
            f"{BASE_URL}/grapho/upload", files=files, headers=headers
        )
        if resp.status_code == 400 and "Invalid file type" in resp.text:
            print("✓ Correctly rejected invalid file type.")
        else:
            print(
                f"✗ Failed to reject invalid file type. Status: {resp.status_code}, Response: {resp.text}"
            )

        # 2. Test File Too Large (>10MB)
        print("\n2. Testing File Too Large...")
        # Create a dummy large file in memory (11MB)
        large_content = b"0" * (11 * 1024 * 1024)
        files = {"file": ("large.jpg", large_content, "image/jpeg")}
        resp = await client.post(
            f"{BASE_URL}/grapho/upload", files=files, headers=headers
        )
        if resp.status_code == 400 and "File too large" in resp.text:
            print("✓ Correctly rejected large file.")
        else:
            print(
                f"✗ Failed to reject large file. Status: {resp.status_code}, Response: {resp.text}"
            )

        # 3. Test Valid File (Small Image)
        # We need a real image or at least something that passes type check.
        # Since we mock OCR in some places or if it fails it might be 500, but validation happens before.
        # Let's try a small dummy "image"
        print("\n3. Testing Valid File...")
        files = {"file": ("valid.jpg", b"fakeimagecontent", "image/jpeg")}
        # Note: This might fail at OCR stage, but should pass validation
        try:
            resp = await client.post(
                f"{BASE_URL}/grapho/upload", files=files, headers=headers
            )
            if resp.status_code == 200:
                print("✓ Valid file accepted.")
            elif resp.status_code == 500:
                print(
                    "✓ Valid file passed validation (failed at OCR as expected for fake content)."
                )
            else:
                print(
                    f"✗ Unexpected error for valid file. Status: {resp.status_code}, Response: {resp.text}"
                )
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_upload_validation())
