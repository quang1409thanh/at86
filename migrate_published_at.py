import os
import json
from datetime import datetime

def migrate():
    test_dir = "data/tests"
    if not os.path.exists(test_dir):
        print("[!] data/tests directory not found.")
        return

    for test_id in os.listdir(test_dir):
        test_path = os.path.join(test_dir, test_id, "test.json")
        if os.path.exists(test_path):
            try:
                with open(test_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "published_at" not in data:
                    # Use file modification time as a proxy or current time
                    mtime = os.path.getmtime(test_path)
                    dt = datetime.fromtimestamp(mtime)
                    data["published_at"] = dt.isoformat()
                    
                    with open(test_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    print(f"[+] Migrated {test_id}: set published_at to {data['published_at']}")
                else:
                    print(f"[*] Skipped {test_id}: published_at already exists.")
            except Exception as e:
                print(f"[!] Error migrating {test_id}: {e}")

if __name__ == "__main__":
    migrate()
