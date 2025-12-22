#!/usr/bin/env python
"""Test runner to capture the exact eror"""

import sys
import os

# Set up the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try importing the test module
    from app.tests.api.api_v1 import test_peer_reviews_flow

    print("✓ Import successful")

    # Try to access the fixtures
    print("✓ Test module loaded")
    print(
        "Functions:", [n for n in dir(test_peer_reviews_flow) if not n.startswith("_")]
    )

except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
