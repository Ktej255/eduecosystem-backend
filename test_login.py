import requests

url = "http://localhost:8000/api/v1/login/access-token"
data = {
    "username": "ktej255@gmail.com",
    "password": "Tej@1106"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
