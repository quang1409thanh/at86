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
        
        # Database connection is imported inside methods to avoid circular imports during startup if needed
        # or we rely on sys.path hacks. Assuming backend is importable.
        try:
            from backend.app.db.session import SessionLocal
            from backend.app.db.models import LLMGlobalConfig
            self.SessionLocal = SessionLocal
            self.LLMGlobalConfig = LLMGlobalConfig
            self._has_db = True
        except ImportError as e:
            print(f"[!] Warning: Could not import backend.app.db: {e}. Persistence disabled.")
            self._has_db = False

        self._load_config()

    def _load_config(self):
        # 1. Try to load from DB
        db_config = None
        if self._has_db:
            try:
                db = self.SessionLocal()
                db_config = db.query(self.LLMGlobalConfig).first()
                db.close()
            except Exception as e:
                print(f"[!] Warning: DB Connection failed: {e}")

        if db_config:
            self.active_provider = db_config.active_provider
            self.providers = db_config.providers
            print(f"[*] Loaded LLM config from Database (Provider: {self.active_provider})")
            return

        # 2. Fallback to Env Vars (same as before)
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

    def _save_to_db(self):
        if not self._has_db: return
        try:
            db = self.SessionLocal()
            config = db.query(self.LLMGlobalConfig).first()
            if not config:
                config = self.LLMGlobalConfig()
                db.add(config)
            
            config.active_provider = self.active_provider
            config.providers = self.providers
            db.commit()
            db.refresh(config)
            db.close()
            print(f"[*] Saved LLM config to Database")
        except Exception as e:
             print(f"[!] Error saving config to DB: {e}")

    def update_settings(self, settings: dict):
        with self._lock:
            self.active_provider = settings.get("active_provider", self.active_provider)
            
            # Logic: Update internal state from request
            for p_data in settings.get("providers", []):
                name = p_data["name"]
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
            
            self._save_to_db()

    def get_current(self):
        with self._lock:
            p = self.providers.get(self.active_provider)
            if not p:
                # auto-heal if missing structure but valid provider name?
                # or just fallback
                raise Exception(f"Provider {self.active_provider} not configured.")
            
            if not p.get("keys"):
                raise Exception(f"No API keys configured for {self.active_provider}.")
            
            return p["keys"][p["key_idx"]], p["models"][p["model_idx"]]

    def get_active_resource_desc(self):
        with self._lock:
            p = self.providers.get(self.active_provider)
            if not p: return f"Unknown Provider ({self.active_provider})"
            if not p.get("keys"): return f"{self.active_provider.capitalize()} (No Keys)"
            
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
