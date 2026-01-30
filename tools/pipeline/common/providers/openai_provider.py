import requests
import base64
from typing import Optional
from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

def call(prompt: str, image_path: Optional[str] = None, json_mode: bool = True, api_key: str = None, model_name: str = None) -> str:
    key = api_key or OPENAI_API_KEY
    model = model_name or OPENAI_MODEL
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    if image_path:
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"OpenAI API Error ({response.status_code}): {response.text}")
    return response.json()['choices'][0]['message']['content']

def transcribe(audio_path: str, api_key: str = None) -> str:
    key = api_key or OPENAI_API_KEY
    headers = {"Authorization": f"Bearer {key}"}
    files = {
        "file": open(audio_path, "rb"),
        "model": (None, "whisper-1"),
        "response_format": (None, "text")
    }
    response = requests.post(f"{OPENAI_BASE_URL}/audio/transcriptions", headers=headers, files=files)
    if response.status_code != 200:
        raise Exception(f"OpenAI STT Error ({response.status_code}): {response.text}")
    return response.text

def list_models(api_key: str = None):
    key = api_key or OPENAI_API_KEY
    headers = {"Authorization": f"Bearer {key}"}
    response = requests.get(f"{OPENAI_BASE_URL}/models", headers=headers)
    if response.status_code == 200:
        return [m["id"] for m in response.json().get("data", [])]
    return []
