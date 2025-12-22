import subprocess
import sys

result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "app/tests/api/api_v1/test_peer_reviews_flow.py::test_peer_review_flow",
        "-v",
        "--tb=long",
    ],
    capture_output=True,
    text=True,
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)
