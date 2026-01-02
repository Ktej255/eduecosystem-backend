import sys

def check_dependencies():
    missing = []
    try:
        import fitz
        print("fitz (PyMuPDF) is installed.")
        print(f"Version: {fitz.__doc__}")
    except ImportError:
        print("fitz (PyMuPDF) is MISSING.")
        missing.append("pymupdf")

    try:
        import PIL
        print("PIL (Pillow) is installed.")
    except ImportError:
        print("PIL (Pillow) is MISSING.")
        missing.append("pillow")
        
    if missing:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    check_dependencies()
