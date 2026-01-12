import urllib.request
import urllib.parse
import json

url = "http://localhost:8000/api/v1/login/access-token"
data = urllib.parse.urlencode({
    "username": "verification_student@example.com", 
    "password": "verification_password"
}).encode()

req = urllib.request.Request(url, data=data, method="POST")
try:
    with urllib.request.urlopen(req) as f:
        print(f.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
