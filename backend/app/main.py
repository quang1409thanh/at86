import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Adjust imports for new structure
from .api.v1 import pipeline, auth, toeic

from .core.config import settings

app = FastAPI(title="TOEIC Platform API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers with API prefix
# Routes become /api/pipeline/..., /api/auth/..., /api/toeic/...
app.include_router(pipeline.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(toeic.router, prefix="/api")

# --- Service Endpoints ---
# Endpoints moved to api/v1/toeic.py
# Keeping only health check or root if needed, but for now we are clean.

# Mount static files
# Access audio/images via /static/Folder/file.mp3
STATIC_DIR = os.path.join(settings.DATA_DIR, "tests")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# No __main__ block needed, run via run.py
