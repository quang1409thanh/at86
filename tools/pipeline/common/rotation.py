import os
import threading
from dotenv import load_dotenv

class RotationManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RotationManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized = True
        
        # Structure: { name: { keys: [], models: [], key_idx: 0, model_idx: 0 } }
        self.providers = {}
        self.active_provider = "google"
        
        self.config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "llm_config.json"))
        self._load_config()

    def _load_config(self):
        import json
        
        # 1. Try to load from file first
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.active_provider = data.get("active_provider", "google")
                    self.providers = data.get("providers", {})
                    # Ensure minimal structure for known providers if missing? 
                    # Actually, if we load from file, we trust it.
                    # But maybe we should merge with env vars if file is empty or partial? 
                    # For now, let's treat file as source of truth if it exists.
                    print(f"[*] Loaded LLM config from {self.config_path}")
                    return
            except Exception as e:
                print(f"[!] Warning: Failed to load config file: {e}")

        # 2. Fallback to Env Vars
        load_dotenv(override=True)
        self.active_provider = os.getenv("LLM_PROVIDER", "google").lower()
        
        self.providers["google"] = {
            "keys": [k.strip() for k in os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", "")).split(",") if k.strip()],
            "models": [m.strip() for m in os.getenv("GEMINI_MODELS", "gemini-2.0-flash,gemini-1.5-flash").split(",") if m.strip()],
            "key_idx": 0,
            "model_idx": 0
        }
        
        self.providers["openai"] = {
            "keys": [k.strip() for k in os.getenv("OPENAI_API_KEY", "").split(",") if k.strip()],
            "models": [m.strip() for m in os.getenv("OPENAI_MODEL", "gpt-4o-mini").split(",") if m.strip()],
            "key_idx": 0,
            "model_idx": 0
        }

    def _save_to_file(self):
        import json
        data = {
            "active_provider": self.active_provider,
            "providers": self.providers
        }
        try:
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"[*] Saved LLM config to {self.config_path}")
        except Exception as e:
             print(f"[!] Error saving config: {e}")

    def update_settings(self, settings: dict):
        with self._lock:
            self.active_provider = settings.get("active_provider", self.active_provider)
            
            # Update internal state from request
            # Logic: We might receive a list of ProviderConfig objects or dicts
            for p_data in settings.get("providers", []):
                name = p_data["name"]
                
                # Preserve indices if not explicitly reset? 
                # For simplicity, let's reset indices or keep them if they are in range.
                # But typically updates from UI might not send current indices, or sends 0.
                # Let's trust the UI or just take keys/models.
                
                # If we want to keep current rotation state, we need to check existing
                current_p = self.providers.get(name, {})
                current_key_idx = current_p.get("key_idx", 0)
                current_model_idx = current_p.get("model_idx", 0)

                new_keys = p_data.get("keys", [])
                new_models = p_data.get("models", [])
                
                # Safety check for indices
                if current_key_idx >= len(new_keys): current_key_idx = 0
                if current_model_idx >= len(new_models): current_model_idx = 0
                
                self.providers[name] = {
                    "keys": new_keys,
                    "models": new_models,
                    "key_idx": current_key_idx,
                    "model_idx": current_model_idx
                }
            
            self._save_to_file()

    def get_current(self):
        with self._lock:
            p = self.providers.get(self.active_provider)
            if not p:
                raise Exception(f"Provider {self.active_provider} not configured.")
            
            if not p["keys"]:
                raise Exception(f"No API keys configured for {self.active_provider}.")
            
            return p["keys"][p["key_idx"]], p["models"][p["model_idx"]]

    def get_active_resource_desc(self):
        with self._lock:
            p = self.providers.get(self.active_provider)
            if not p: return f"Unknown Provider ({self.active_provider})"
            if not p["keys"]: return f"{self.active_provider.capitalize()} (No Keys)"
            
            return f"{self.active_provider.capitalize()} {p['models'][p['model_idx']]} (Key {p['key_idx'] + 1}/{len(p['keys'])})"

    def rotate(self, reason="") -> bool:
        with self._lock:
            p = self.providers.get(self.active_provider)
            if not p or not p["keys"]: return False
            
            print(f"[*] Rotating {self.active_provider} due to: {reason}")
            p["model_idx"] += 1
            if p["model_idx"] >= len(p["models"]):
                p["model_idx"] = 0
                p["key_idx"] += 1
                if p["key_idx"] >= len(p["keys"]):
                    p["key_idx"] = 0
                    return False
            return True

rotation_manager = RotationManager()
