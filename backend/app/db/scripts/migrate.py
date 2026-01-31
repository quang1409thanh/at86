import json
import sys
import os

# Ensure project root is in path
# backend/app/db/scripts/migrate.py -> ../../../../
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal
from backend.app.db.models import LLMGlobalConfig

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "llm_config.json")

def migrate_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] No legacy config found at {CONFIG_PATH}")
        return

    print(f"[*] Reading legacy config from {CONFIG_PATH}...")
    try:
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Failed to read JSON file: {e}")
        return

    db = SessionLocal()
    try:
        # Check if config exists in DB
        db_config = db.query(LLMGlobalConfig).first()
        if db_config:
            print("[*] DB config already exists. Skipping overwrite.")
            # Optional: Update it? For safety, let's not overwrite if DB has data.
            # But if DB was just created by init_db (empty), we should populate it.
            # init_db doesn't create LLMConfig row.
            return

        print("[*] Migrating to Database...")
        new_config = LLMGlobalConfig(
            active_provider=data.get("active_provider", "google"),
            providers=data.get("providers", {})
        )
        db.add(new_config)
        db.commit()
        print("[+] Migration successful! settings moved to MySQL.")
        
        # Optional: Rename old file to .bak?
        # os.rename(CONFIG_PATH, CONFIG_PATH + ".bak")
        # print("[*] Renamed llm_config.json to llm_config.json.bak")
        
    except Exception as e:
        print(f"[!] Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_config()
