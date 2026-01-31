import sys
import os

# Ensure project root is in path
# backend/app/db/scripts/init.py -> ../../../../
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from sqlalchemy import create_engine, text
from backend.app.core.config import settings
from backend.app.db.session import engine, SessionLocal
from backend.app.db import models
from backend.app.core import security

def create_database_if_not_exists():
    # Extract base URL (remove database name)
    try:
        url = settings.DATABASE_URL
        if "/at86" in url:
            server_url = url.replace("/at86", "")
        else:
            # Fallback if URL structure differs significantly
            return
            
        server_engine = create_engine(server_url)
        with server_engine.connect() as conn:
            conn.execute(text("CREATE DATABASE IF NOT EXISTS at86"))
            print("[*] Checked/Created database 'at86'")
    except Exception as e:
        print(f"[!] Warning: Database creation check failed (might already exist or permission issue): {e}")

def init_db():
    create_database_if_not_exists()
    
    # Create Tables
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin exists
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if not user:
            print("[*] Creating default admin user...")
            hashed_pw = security.get_password_hash("admin123")
            admin_user = models.User(
                username="admin",
                hashed_password=hashed_pw,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("[+] Admin created: admin / admin123")
        else:
            print("[*] Admin user already exists.")
            print("[+] You can log in as 'admin' / 'admin123'")
            
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
