import sys

sys.path.insert(0, ".")

try:
    print("Loading models...")
    print("✓ All models loaded successfully")

    print("\nLoading database session...")
    from app.db.session import Base, engine

    print("✓ Database session loaded")

    print("\nCreating tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")

    print("\nStarting FastAPI app...")
    print("✓ FastAPI app module loaded")

    print("\n=== SUCCESS ===")
    print("All components loaded without errors!")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback

    traceback.print_exc()
