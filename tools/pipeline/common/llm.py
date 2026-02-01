import os
import time
import json
import re
from typing import Optional, Dict, Any
from .providers import openai_provider, google_provider
from .rotation import rotation_manager

def safe_parse_json(text: str) -> Any:
    """Attempts to parse JSON from text, repairing common LLM mistakes like trailing commas."""
    # 1. Try direct parse
    try:
        return json.loads(text)
    except:
        pass

    # 2. Extract JSON block if wrapped in markdown
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
        try:
            return json.loads(text)
        except:
            pass

    # 3. Basic repair: remove trailing commas before } or ]
    # This regex looks for a comma followed by whitespace and then a closing brace or bracket
    repaired = re.sub(r',\s*([}\]])', r'\1', text)
    
    try:
        return json.loads(repaired)
    except Exception as e:
        # 4. Final attempt: strip everything outside the first { and last }
        try:
            start = repaired.find('{')
            end = repaired.rfind('}')
            if start != -1 and end != -1:
                return json.loads(repaired[start:end+1])
        except:
            pass
        raise e

def list_available_models() -> Dict[str, Any]:
    """Lists available models for the current provider."""
    results = {"provider": rotation_manager.active_provider, "models": []}
    try:
        if rotation_manager.active_provider == "google":
            api_key, _, label = rotation_manager.get_current()
            results["models"] = google_provider.list_models(api_key=api_key)
        else:
            api_key, _, label = rotation_manager.get_current()
            results["models"] = openai_provider.list_models(api_key=api_key)
    except Exception as e:
        results["error"] = str(e)
    return results

def call_llm(prompt: str, image_path: Optional[str] = None, json_mode: bool = True, retries: int = 100, validate_json: bool = False) -> Any:
    """
    Calls the active LLM provider and returns the response.
    If validate_json is True, it will attempt to parse the response as JSON and retry on failure.
    Default retries is set high (100) to allow exhausting the rotation pool.
    """
    for attempt in range(retries):
        raw_response = ""
        try:
            api_key, model_name, label = rotation_manager.get_current()
            if rotation_manager.active_provider == "google":
                print(f"[*] Calling Gemini ({model_name}) with Key: [{label}]")
                raw_response = google_provider.call(prompt, image_path, json_mode, api_key=api_key, model_name=model_name)
            else:
                print(f"[*] Calling OpenAI ({model_name}) with Key: [{label}]")
                raw_response = openai_provider.call(prompt, image_path, json_mode, api_key=api_key, model_name=model_name)
            
            if not validate_json:
                return raw_response
            
            # Application-level validation: try to parse the JSON
            try:
                return safe_parse_json(raw_response)
            except Exception as parse_err:
                print(f"[!] JSON Parsing failed (Attempt {attempt+1}/{retries}): {parse_err}")
                if attempt < retries - 1:
                    # Maybe rotate even on parsing error if it persists? 
                    # For now, just retry with the same or next resource
                    reason = "JSON Parsing Failure"
                    rotation_manager.rotate(reason=reason) 
                    continue
                else:
                    raise parse_err

        except Exception as e:
            err_msg = str(e)
            print(f"[!] Error in call_llm: {err_msg}")
            
            # Rotate on 429 (Quota), 400 (Invalid Arg/Modality), 404 (Not Found), 403 (Auth), 5xx (Server)
            is_error_rotatable = any(x in err_msg.lower() for x in ["429", "quota", "503", "500", "404", "not found", "403", "forbidden", "400", "invalid_argument", "modality"])
            
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

def transcribe_audio(audio_path: str, retries: int = 100) -> str:
    print(f"[*] transcribe_audio called with provider={rotation_manager.active_provider}")
    for attempt in range(retries):
        try:
            api_key, model_name, label = rotation_manager.get_current()
            if rotation_manager.active_provider == "google":
                print(f"[*] Transcribing using Gemini ({model_name}) with Key: [{label}]")
                return google_provider.transcribe(audio_path, api_key=api_key, model_name=model_name)
            else:
                print(f"[*] Transcribing using OpenAI (whisper-1) with Key: [{label}]")
                return openai_provider.transcribe(audio_path, api_key=api_key)
        except Exception as e:
            err_msg = str(e)
            print(f"[!] Error in transcribe_audio: {err_msg}")
            
            # Rotate on 429 (Quota), 400 (Invalid Arg/Modality), 404 (Not Found), 403 (Auth), 5xx (Server)
            is_error_rotatable = any(x in err_msg.lower() for x in ["429", "quota", "503", "500", "404", "not found", "403", "forbidden", "400", "invalid_argument", "modality"])
            
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
