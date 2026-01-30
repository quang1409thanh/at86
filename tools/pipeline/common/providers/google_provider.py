from google import genai
from typing import Optional
from ..config import GEMINI_API_KEY, GEMINI_MODEL

def call(prompt: str, image_path: Optional[str] = None, json_mode: bool = True, api_key: str = None, model_name: str = None) -> str:
    key = api_key or GEMINI_API_KEY
    model = model_name or GEMINI_MODEL
    client = genai.Client(api_key=key)
    contents = [prompt]
    if image_path:
        with open(image_path, "rb") as f:
            contents.append(genai.types.Part.from_bytes(data=f.read(), mime_type="image/jpeg"))

    config = {"temperature": 0.2}
    if json_mode:
        config["response_mime_type"] = "application/json"

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=genai.types.GenerateContentConfig(**config)
    )
    return response.text

def transcribe(audio_path: str, api_key: str = None, model_name: str = None) -> str:
    key = api_key or GEMINI_API_KEY
    model = model_name or GEMINI_MODEL
    client = genai.Client(api_key=key)
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    
    response = client.models.generate_content(
        model=model,
        contents=[
            "Transcribe exactly. No commentary.",
            genai.types.Part.from_bytes(data=audio_data, mime_type="audio/mpeg")
        ]
    )
    return response.text

def list_models(api_key: str = None):
    key = api_key or GEMINI_API_KEY
    client = genai.Client(api_key=key)
    return [model.name for model in client.models.list()]
