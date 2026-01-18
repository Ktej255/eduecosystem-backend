import sys
import os

# Ensure backend directory is in path
sys.path.append(os.getcwd())

print("Attempting naked import of api_router...")
from app.api.api_v1.api import api_router
print("Success!")
