import subprocess
import sys

with open("error_full.txt", "w", encoding="utf-8") as f:
    subprocess.run([sys.executable, "debug_mappers.py"], stderr=f, stdout=f, text=True)
