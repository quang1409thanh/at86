
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure project root is in path
    sys.path.append(os.path.dirname(__file__))
    
    # Run Uvicorn
    # Use "backend.app.main:app" string to enable reload
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
