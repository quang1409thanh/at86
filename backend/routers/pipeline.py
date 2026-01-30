import os
import sys
import json
import asyncio
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from schemas import PipelineConfig, PipelineRunRequest, LLMSettings, ProviderConfig

# Add pipeline to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "tools", "pipeline"))

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Import pipeline components
try:
    from common.rotation import rotation_manager
    import run_part1_batch
    import run_part2_batch
except ImportError as e:
    print(f"[!] Warning: Pipeline imports failed in router: {e}")

# Global state for active pipeline runs to stream logs
active_log_queues = {}
# Capture the main event loop
main_loop = None

@router.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()

def broadcast_log(msg: str):
    # This is often called from background threads
    global main_loop
    if not main_loop:
        return

    for client_id, queue in list(active_log_queues.items()):
        try:
             main_loop.call_soon_threadsafe(queue.put_nowait, msg)
        except Exception:
            pass

@router.get("/config", response_model=PipelineConfig)
def get_pipeline_config():
    providers = []
    for name, p in rotation_manager.providers.items():
        providers.append(ProviderConfig(
            name=name,
            keys=p["keys"],
            models=p["models"],
            current_key_index=p["key_idx"],
            current_model_index=p["model_idx"]
        ))
    
    settings = LLMSettings(
        active_provider=rotation_manager.active_provider,
        providers=providers
    )
    return PipelineConfig(
        settings=settings,
        active_resource=rotation_manager.get_active_resource_desc()
    )

@router.get("/models")
def get_available_models():
    """Lists available models for the current active provider."""
    # We can use the helper from common.llm or just call the provider directly 
    # but using common.llm ensures consistent logic if we added it there
    from common.llm import list_available_models
    return list_available_models()

@router.post("/config")
def update_pipeline_config(settings: LLMSettings):
    rotation_manager.update_settings(settings.dict())
    return {"status": "success"}

@router.websocket("/logs")
async def pipeline_logs_websocket(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    client_id = id(websocket)
    active_log_queues[client_id] = queue
    try:
        await websocket.send_text(f"[*] Connected. Active: {rotation_manager.get_active_resource_desc()}")
        while True:
            log_msg = await queue.get()
            await websocket.send_text(log_msg)
    except WebSocketDisconnect:
        if client_id in active_log_queues:
            del active_log_queues[client_id]

@router.get("/browse")
def browse_filesystem(path: str = "."):
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return {"error": "Path does not exist", "items": []}
        
        items = []
        # Parent
        parent = os.path.dirname(abs_path)
        items.append({"name": "..", "path": parent, "type": "dir"})
        
        for name in sorted(os.listdir(abs_path)):
            full_path = os.path.join(abs_path, name)
            is_dir = os.path.isdir(full_path)
            items.append({
                "name": name,
                "path": full_path,
                "type": "dir" if is_dir else "file"
            })
        return {"current_path": abs_path, "items": items}
    except Exception as e:
        return {"error": str(e), "items": []}

    threading.Thread(target=start_run, daemon=True).start()
    return {"status": "started", "part": request.part}

@router.post("/run")
async def run_pipeline(request: PipelineRunRequest):
    # Merge test_id into config so batch scripts can use it
    run_config = request.config or {}
    run_config["test_id"] = request.test_id
    
    def start_run():
        broadcast_log(f"[*] Initializing Part {request.part} Processing for Test ID: {request.test_id}")
        if request.part == 1:
            run_part1_batch.run_batch(log_callback=broadcast_log, input_config=run_config)
        elif request.part == 2:
            run_part2_batch.run_batch(log_callback=broadcast_log, input_config=run_config)
        else:
            broadcast_log(f"[!] Critical Error: Part {request.part} implementation missing.")
    
    threading.Thread(target=start_run, daemon=True).start()
    return {"status": "started", "part": request.part}
