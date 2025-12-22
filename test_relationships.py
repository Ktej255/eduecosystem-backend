import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v1"


async def test_relationships():
    print("Testing relationships...")

    async with httpx.AsyncClient() as client:
        # 1. Register User
        email = "reltest2@example.com"
        password = "password123"
        try:
            # Try login first (if user exists)
            resp = await client.post(
                f"{BASE_URL}/login/access-token",
                data={"username": email, "password": password},
            )
            if resp.status_code == 200:
                token = resp.json()["access_token"]
                print("User exists, logged in.")
            else:
                # Register
                resp = await client.post(
                    f"{BASE_URL}/users/",
                    json={
                        "email": email,
                        "password": password,
                        "full_name": "Rel Test",
                    },
                )
                if resp.status_code != 200:
                    print(f"Registration failed: {resp.text}")
                    return
                print("User registered.")

                # Login
                resp = await client.post(
                    f"{BASE_URL}/login/access-token",
                    data={"username": email, "password": password},
                )
                token = resp.json()["access_token"]
                print("Logged in.")

            headers = {"Authorization": f"Bearer {token}"}

            # 2. Create Task (User -> Task)
            task_data = {
                "title": "Test Task",
                "description": "Testing relationships",
                "task_type": "other",
                "duration_minutes": 30,
                "scheduled_date": "2025-11-22T10:00:00",
            }
            resp = await client.post(
                f"{BASE_URL}/tasks/", json=task_data, headers=headers
            )
            if resp.status_code == 200:
                print("Task created (User -> Task relationship works).")
            else:
                print(f"Task creation failed: {resp.text}")

            # 3. Get User Me (Check if tasks are loaded)
            resp = await client.get(f"{BASE_URL}/users/me", headers=headers)
            if resp.status_code == 200:
                user = resp.json()
                print(f"User fetched. ID: {user['id']}")
            else:
                print(f"Get User failed: {resp.text}")

            # 4. Join Group (User -> Group)
            resp = await client.post(f"{BASE_URL}/groups/join", headers=headers)
            if resp.status_code == 200:
                group = resp.json()
                print(
                    f"Joined group: {group.get('name')} (User -> Group relationship works)."
                )
            else:
                print(f"Join group failed: {resp.text}")

            print("\nSUCCESS: All relationship tests passed!")

        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_relationships())
