import os
import sys
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List

# Add pipeline to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "tools", "pipeline"))

app = FastAPI(title="TOEIC Platform API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
from schemas import TestSummary, TestDetail, UserResult
import data_service
from routers import pipeline

app.include_router(pipeline.router)

@app.get("/api/tests", response_model=list[TestSummary])
def get_tests():
    return data_service.get_all_tests()

@app.get("/api/tests/{test_id}", response_model=TestDetail)
def get_test_detail(test_id: str):
    # Here test_id is treated as the folder name
    result = data_service.get_test_detail(test_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Test not found")
    return result

@app.post("/api/results")
def save_result(result: UserResult):
    data_service.save_result(result)
    return {"status": "success"}

@app.get("/api/results/{result_id}", response_model=UserResult)
def get_result(result_id: str):
    result = data_service.get_result_by_id(result_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Result not found")
    return result

@app.get("/api/history", response_model=list[UserResult])
def get_history():
    return data_service.get_history()

# Mount static files for data
# Access audio/images via /static/Folder/file.mp3
app.mount("/static", StaticFiles(directory="../data/tests"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
