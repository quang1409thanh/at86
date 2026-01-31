import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "TOEIC Platform"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/at86")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Data Paths - Default to project_root/data if not set
    # backend/app/core/config.py -> ../../../data
    _default_data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
    DATA_DIR: str = os.getenv("DATA_DIR", _default_data_dir)

settings = Settings()
