import time
import os
from PIL import Image, ImageDraw
from app.services.ocr import analyze_handwriting


def create_test_image(filename="test_ocr.jpg"):
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Use default font
    d.text((10, 10), "Hello World. This is a handwriting test.", fill=(0, 0, 0))
    d.text((10, 50), "The quick brown fox jumps over the lazy dog.", fill=(0, 0, 0))
    img.save(filename)
    return filename


def test_ocr_performance():
    print("Testing OCR Performance...")

    # 1. Create Image
    image_path = create_test_image()
    print(f"Created test image: {image_path}")

    try:
        # 2. Warmup (first run loads model)
        print("Warming up (loading model)...")
        start_time = time.time()
        analyze_handwriting(image_path)
        warmup_time = time.time() - start_time
        print(f"Warmup time: {warmup_time:.2f}s")

        # 3. Performance Run
        print("Running performance test...")
        start_time = time.time()
        result = analyze_handwriting(image_path)
        duration = time.time() - start_time

        print(f"Performance run time: {duration:.2f}s")
        print(f"Extracted Text: {result.get('extracted_text', '')[:50]}...")

        # Threshold (e.g., 5 seconds for CPU is reasonable for EasyOCR)
        if duration < 5.0:
            print("✓ OCR Performance is acceptable (< 5s).")
        else:
            print("⚠ OCR Performance is slow (> 5s). Consider GPU or optimization.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        if os.path.exists(image_path):
            os.remove(image_path)


if __name__ == "__main__":
    test_ocr_performance()
