import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Global Provider Setting
# Options: 'openai' or 'google'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google").lower() 

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

# Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Using the model name confirmed to work in test.py
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
