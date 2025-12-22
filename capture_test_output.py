#!/usr/bin/env python
"""Run the test and capture full output"""

import subprocess
import sys

# Run pytest and capture full output
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "app/tests/api/api_v1/test_peer_reviews_flow.py::test_peer_review_flow",
        "--tb=short",
        "-vv",
    ],
    capture_output=True,
    text=True,
    cwd=r"d:\Graphology\Master Software\Eduecosystem\backend",
)

# Write to file for easier reading
with open("full_test_output.txt", "w", encoding="utf-8") as f:
    f.write("=== STDOUT ===\n")
    f.write(result.stdout)
    f.write("\n\n=== STDERR ===\n")
    f.write(result.stderr)
    f.write(f"\n\n=== Exit Code: {result.returncode} ===\n")

print("Output written to full_test_output.txt")
print("\n" + "=" * 60)
print("LAST 100 LINES OF OUTPUT:")
print("=" * 60)
all_out = result.stdout + "\n" + result.stderr
lines = all_out.split("\n")
for line in lines[-100:]:
    print(line)
