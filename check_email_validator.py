try:
    from pydantic import EmailStr
    import email_validator
    print("email-validator is installed")
except ImportError as e:
    print(f"Missing dependency: {e}")
except Exception as e:
    print(f"Error: {e}")
