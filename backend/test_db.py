import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from app.config import settings
from app.services.storage import storage_service

print(f"USE_MONGODB setting: {settings.USE_MONGODB}")
print(f"Actual Storage Mode: {'MongoDB' if storage_service.use_mongodb else 'JSON File'}")

if storage_service.use_mongodb:
    try:
        # Test connection
        storage_service.client.admin.command('ping')
        print("✓ MongoDB Connection Successful!")
    except Exception as e:
        print(f"✗ MongoDB Connection Failed: {e}")
else:
    print("Running in JSON fallback mode.")
