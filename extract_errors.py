import sys
import re

def extract():
    try:
        with open('test_cart_fail_v3.txt', 'rb') as f:
            content = f.read().decode('utf-16', errors='ignore')
        
        # Split by failure blocks
        blocks = re.split(r'_{10,}', content)
        for block in blocks:
            if 'FAIL' in block or 'ERROR' in block or 'E   ' in block:
                print("="*60)
                print(block.strip())
                print("="*60)
                print("\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract()
