import os
import sys
import json
import asyncio
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from ...schemas import PipelineConfig, PipelineRunRequest, LLMSettings, ProviderConfig

# Add pipeline to path
# Current file: backend/app/api/v1/pipeline.py
# Root is at ../../../../
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "tools", "pipeline"))

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

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
    try:
        main_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass # Loop might happen later

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

@router.post("/run")
def run_pipeline(request: PipelineRunRequest):
    # Merge test_id into config so batch scripts can use it
    run_config = request.config or {}
    run_config["test_id"] = request.test_id
    
    global active_process
    if active_process and active_process.is_alive():
        return {"status": "error", "message": "Pipeline already running"}

    # Queue for inter-process communication
    log_queue = multiprocessing.Queue()
    
    # Start worker process
    p = multiprocessing.Process(
        target=_worker_entry,
        args=(request.part, request.test_id, run_config, log_queue)
    )
    p.start()
    active_process = p
    
    # Start thread to consume logs from queue
    threading.Thread(target=_log_cconsumer, args=(log_queue,), daemon=True).start()
    
    return {"status": "started", "part": request.part}

@router.post("/stop")
def stop_pipeline():
    global active_process
    if active_process and active_process.is_alive():
        active_process.terminate()
        active_process.join()  # Wait for it to die
        broadcast_log("[!] Pipeline forced stopped by user.")
        active_process = None
        return {"status": "success", "message": "Pipeline stopped"}
    return {"status": "error", "message": "No active pipeline running"}

# --- Multiprocessing Helpers ---

import multiprocessing

# Global to hold the active process
active_process = None

def _log_cconsumer(queue: multiprocessing.Queue):
    """Consumes logs from the child process and broadcasts them."""
    while True:
        try:
            msg = queue.get()
            if msg == "STOP_LOGGING":
                break
            broadcast_log(msg)
        except Exception:
            break

def _worker_entry(part: int, test_id: str, config: Dict[str, Any], queue: multiprocessing.Queue):
    """Entry point for the worker process."""
    # Define a simple callback wrapper
    def log_wrapper(msg: str):
        queue.put(msg)
    
    try:
        log_wrapper(f"[*] Initializing Part {part} Worker PID: {os.getpid()}")
        if part == 1:
            run_part1_batch.run_batch(log_callback=log_wrapper, input_config=config)
        elif part == 2:
            run_part2_batch.run_batch(log_callback=log_wrapper, input_config=config)
        else:
            log_wrapper(f"[!] Error: Unknown part {part}")
    except Exception as e:
        log_wrapper(f"[!] Critical Worker Error: {e}")
    finally:
        log_wrapper("[*] Batch process ended")
        # Ensure queue flushes?
        pass
