"""
Debug script to test SQLAlchemy mapper configuration.
Captures full error traces with proper encoding.
"""

import sys
import traceback

try:
    print("Importing models...")
    from app.models import *

    print("✅ Models imported successfully.")

    try:
        from main import app

        print("✅ Main app imported successfully.")
    except ImportError as e:
        print(f"Could not import main: {e}")

    print("\nConfiguring mappers...")
    from sqlalchemy.orm import configure_mappers

    configure_mappers()
    print("✅ Mappers configured successfully!")
    print("\n🎉 All mapper configuration tests passed!")

except Exception as e:
    print(f"\n❌ Error during mapper configuration: {type(e).__name__}")
    print(f"Error message: {str(e)[:200]}...")

    # Write full error to file with proper encoding
    with open("full_error.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("FULL ERROR TRACEBACK\n")
        f.write("=" * 80 + "\n\n")
        traceback.print_exc(file=f)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write(f"Error Type: {type(e).__name__}\n")
        f.write(f"Error Message: {str(e)}\n")
        f.write("=" * 80 + "\n")

    print("\n📝 Full error traceback written to: full_error.txt")
    print("Please review the file for complete details.")

    sys.exit(1)
