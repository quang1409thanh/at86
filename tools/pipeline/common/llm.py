import os
import time
from typing import Optional, Dict, Any
from .providers import openai_provider, google_provider
from .rotation import rotation_manager

def list_available_models() -> Dict[str, Any]:
    """Lists available models for the current provider."""
    results = {"provider": rotation_manager.active_provider, "models": []}
    try:
        if rotation_manager.active_provider == "google":
            api_key, _ = rotation_manager.get_current()
            results["models"] = google_provider.list_models(api_key=api_key)
        else:
            api_key, _ = rotation_manager.get_current()
            results["models"] = openai_provider.list_models(api_key=api_key)
    except Exception as e:
        results["error"] = str(e)
    return results

def call_llm(prompt: str, image_path: Optional[str] = None, json_mode: bool = True, retries: int = 5) -> str:
    for attempt in range(retries):
        try:
            api_key, model_name = rotation_manager.get_current()
            if rotation_manager.active_provider == "google":
                print(f"[*] Calling Gemini ({model_name})")
                return google_provider.call(prompt, image_path, json_mode, api_key=api_key, model_name=model_name)
            else:
                print(f"[*] Calling OpenAI ({model_name})")
                return openai_provider.call(prompt, image_path, json_mode, api_key=api_key, model_name=model_name)
        except Exception as e:
            err_msg = str(e)
            print(f"[!] Error in call_llm: {err_msg}")
            
            # Rotate on 429 (Quota), 404 (Not Found), 403 (Auth), 5xx (Server)
            is_error_rotatable = any(x in err_msg.lower() for x in ["429", "quota", "503", "500", "404", "not found", "403", "forbidden"])
            
            if is_error_rotatable and attempt < retries - 1:
                # Rotate resource
                reason = f"Error: {err_msg[:50]}..."
                if rotation_manager.rotate(reason=reason):
                    print("[*] Retrying with new resource immediately...")
                    continue
                else:
                    # All resources exhausted, backoff
                    wait_time = (attempt + 1) * 20
                    print(f"[!] All resources exhausted. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            raise e

def transcribe_audio(audio_path: str, retries: int = 5) -> str:
    print(f"[*] transcribe_audio called with provider={rotation_manager.active_provider}")
    for attempt in range(retries):
        try:
            api_key, model_name = rotation_manager.get_current()
            if rotation_manager.active_provider == "google":
                print(f"[*] Transcribing using Gemini ({model_name})")
                return google_provider.transcribe(audio_path, api_key=api_key, model_name=model_name)
            else:
                print(f"[*] Transcribing using OpenAI (whisper-1)")
                return openai_provider.transcribe(audio_path, api_key=api_key)
        except Exception as e:
            err_msg = str(e)
            print(f"[!] Error in transcribe_audio: {err_msg}")
            
            # Rotate on 429 (Quota), 404 (Not Found), 403 (Auth), 5xx (Server)
            is_error_rotatable = any(x in err_msg.lower() for x in ["429", "quota", "503", "500", "404", "not found", "403", "forbidden"])
            
            if is_error_rotatable and attempt < retries - 1:
                reason = f"Error: {err_msg[:50]}..."
                if rotation_manager.rotate(reason=reason):
                    print("[*] Retrying with new resource immediately...")
                    continue
                else:
                    wait_time = (attempt + 1) * 20
                    print(f"[!] All resources exhausted. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            raise e
