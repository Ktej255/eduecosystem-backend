import requests
import sys

base_url = "https://cbdzkgkpmh.us-east-1.awsapprunner.com/api/v1"

def check_endpoint(path, method="GET", json_data=None):
    url = f"{base_url}{path}"
    try:
        if method == "POST":
            r = requests.post(url, json=json_data)
        else:
            r = requests.get(url)
        print(f"{path}: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"{path}: Error {e}")
        return 0

print("Checking deployment status...")
status_prod = check_endpoint("/productivity/news-quiz", method="POST", json_data={})
status_comm = check_endpoint("/community/presence", method="GET")

if status_prod == 404 or status_comm == 404:
    print("RESULT: NOT_DEPLOYED (404 Not Found)")
    sys.exit(1)
elif status_prod in [200, 422, 401] and status_comm in [200, 422, 401]:
    print("RESULT: DEPLOYED (Endpoints exist)")
    sys.exit(0)
else:
    print(f"RESULT: UNKNOWN_STATUS (Prod: {status_prod}, Comm: {status_comm})")
    sys.exit(0)
