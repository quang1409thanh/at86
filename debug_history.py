import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from backend.app.services import data_service
    print("Attempting to load history...")
    history = data_service.get_history()
    print(f"Loaded {len(history)} items.")
    for h in history:
        print(f" - {h.id}: {h.score}")
except Exception as e:
    import traceback
    traceback.print_exc()
