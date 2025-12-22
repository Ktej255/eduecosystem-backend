import threading
import time
import json
import requests
import websocket
import sys
import random

# Configuration
API_URL = "http://localhost:8006/api/v1"
WS_URL = "ws://localhost:8006/api/v1"
NUM_CONNECTIONS = 50
DURATION = 30  # seconds

# Test User Credentials
import uuid
EMAIL = f"stress_test_{uuid.uuid4()}@example.com"
PASSWORD = "password123"

def get_auth_token():
    """Register and get access token"""
    print(f"Attempting to register user: {EMAIL}")
    try:
        response = requests.post(
            f"{API_URL}/login/register",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "full_name": "WS Stress Test User",
                "role": "student"
            }
        )
        if response.status_code != 200:
            print(f"Registration failed: {response.status_code} - {response.text}")
            return None, None
            
        # Login
        response = requests.post(
            f"{API_URL}/login/access-token",
            data={"username": EMAIL, "password": PASSWORD}
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            user_id = get_user_id(token)
            return token, user_id
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None, None

    except Exception as e:
        print(f"Auth Exception: {e}")
        return None, None

def get_user_id(token):
    # Helper to get user ID from /users/me
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/users/me", headers=headers)
    if resp.status_code == 200:
        return resp.json()["id"]
    return None

class WSClient(threading.Thread):
    def __init__(self, url, token, client_id):
        threading.Thread.__init__(self)
        self.url = f"{url}?token={token}"
        self.client_id = client_id
        self.ws = None
        self.connected = False
        self.error = None

    def run(self):
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever()

    def on_open(self, ws):
        self.connected = True
        # print(f"Client {self.client_id}: Connected")

    def on_message(self, ws, message):
        pass
        # print(f"Client {self.client_id}: Received {message}")

    def on_error(self, ws, error):
        self.error = error
        print(f"Client {self.client_id}: Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        # print(f"Client {self.client_id}: Closed")

    def close(self):
        if self.ws:
            self.ws.close()

def run_stress_test():
    print(f"Starting WebSocket Stress Test with {NUM_CONNECTIONS} connections...")
    
    token, user_id = get_auth_token()
    if not token:
        print("Failed to authenticate. Exiting.")
        sys.exit(1)
        
    print(f"Authenticated as user {user_id}")
    
    clients = []
    target_url = f"{WS_URL}/ws/notifications/{user_id}"
    
    # Spawn clients
    for i in range(NUM_CONNECTIONS):
        client = WSClient(target_url, token, i)
        client.start()
        clients.append(client)
        time.sleep(0.05) # Stagger connections slightly
        
    print("All clients started. Waiting for connections to establish...")
    time.sleep(5)
    
    # Check status
    connected_count = sum(1 for c in clients if c.connected)
    print(f"Connected: {connected_count}/{NUM_CONNECTIONS}")
    
    if connected_count < NUM_CONNECTIONS:
        print("WARNING: Not all clients connected!")
        
    print(f"Holding connections for {DURATION} seconds...")
    time.sleep(DURATION)
    
    # Final check
    final_connected_count = sum(1 for c in clients if c.connected)
    print(f"Final Connected: {final_connected_count}/{NUM_CONNECTIONS}")
    
    # Cleanup
    print("Closing connections...")
    for client in clients:
        client.close()
        client.join()
        
    print("Test Complete.")
    
    if final_connected_count == NUM_CONNECTIONS:
        print("SUCCESS: All connections maintained.")
        sys.exit(0)
    else:
        print(f"FAILURE: Lost {NUM_CONNECTIONS - final_connected_count} connections.")
        sys.exit(1)

if __name__ == "__main__":
    run_stress_test()
