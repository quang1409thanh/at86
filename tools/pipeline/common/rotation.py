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

    def __init__(self, rotation_callback=None):
        if self._initialized: return
        self._initialized = True
        
        # Structure: { name: { keys: [{key, label}], models: [], key_idx: 0, model_idx: 0 } }
        self.providers = {}
        self.active_provider = "google"
        self.rotation_callback = rotation_callback  # Callback to notify external systems on rotation
        
        try:
            from backend.app.db.session import SessionLocal
            from backend.app.db.models import LLMProvider, LLMKey
            self.SessionLocal = SessionLocal
            self.LLMProvider = LLMProvider
            self.LLMKey = LLMKey
            self._has_db = True
        except ImportError as e:
            print(f"[!] Warning: Could not import backend.app.db: {e}. Persistence disabled.")
            self._has_db = False

        self._load_config()

    def _load_config(self):
        # 1. Try to load from DB
        if self._has_db:
            try:
                db = self.SessionLocal()
                db_providers = db.query(self.LLMProvider).all()
                if db_providers:
                    for p in db_providers:
                        # Load keys for this provider
                        keys = db.query(self.LLMKey).filter(self.LLMKey.provider_id == p.id).all()
                        self.providers[p.name] = {
                            "keys": [{"key": k.key_value, "label": k.label} for k in keys],
                            "models": p.models,
                            "key_idx": p.current_key_idx,
                            "model_idx": p.current_model_idx
                        }
                        if p.is_active:
                            self.active_provider = p.name
                    db.close()
                    print(f"[*] Loaded LLM config from Database (Active: {self.active_provider})")
                    return
                db.close()
            except Exception as e:
                print(f"[!] Warning: DB Connection failed: {e}")

        # 2. Fallback to Env Vars and Seed DB
        load_dotenv(override=True)
        self.active_provider = os.getenv("LLM_PROVIDER", "google").lower()
        
        google_keys = [k.strip() for k in os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", "")).split(",") if k.strip()]
        self.providers["google"] = {
            "keys": [{"key": k, "label": f"Key {i+1}"} for i, k in enumerate(google_keys)],
            "models": [m.strip() for m in os.getenv("GEMINI_MODELS", "gemini-2.0-flash,gemini-1.5-flash").split(",") if m.strip()],
            "key_idx": 0,
            "model_idx": 0
        }
        
        openai_keys = [k.strip() for k in os.getenv("OPENAI_API_KEY", "").split(",") if k.strip()]
        self.providers["openai"] = {
            "keys": [{"key": k, "label": f"Key {i+1}"} for i, k in enumerate(openai_keys)],
            "models": [m.strip() for m in os.getenv("OPENAI_MODEL", "gpt-4o-mini").split(",") if m.strip()],
            "key_idx": 0,
            "model_idx": 0
        }
        
        # Save initial fallback to DB
        self._save_to_db()

    def _save_to_db(self):
        if not self._has_db: return
        try:
            db = self.SessionLocal()
            for name, data in self.providers.items():
                p = db.query(self.LLMProvider).filter(self.LLMProvider.name == name).first()
                if not p:
                    p = self.LLMProvider(
                        name=name,
                        models=data["models"],
                        is_active=(name == self.active_provider),
                        current_key_idx=data["key_idx"],
                        current_model_idx=data["model_idx"]
                    )
                    db.add(p)
                    db.flush()
                else:
                    p.is_active = (name == self.active_provider)
                    p.models = data["models"]
                    p.current_key_idx = data["key_idx"]
                    p.current_model_idx = data["model_idx"]

                # Handle Keys
                # For simplicity, clear and re-add keys or update if match
                # Let's just sync them
                existing_keys = db.query(self.LLMKey).filter(self.LLMKey.provider_id == p.id).all()
                existing_keys_map = {k.key_value: k for k in existing_keys}
                
                new_key_values = set()
                for k_data in data["keys"]:
                    val = k_data["key"]
                    label = k_data["label"]
                    new_key_values.add(val)
                    if val in existing_keys_map:
                        existing_keys_map[val].label = label
                    else:
                        new_key = self.LLMKey(provider_id=p.id, key_value=val, label=label)
                        db.add(new_key)
                
                # Delete old keys
                for k in existing_keys:
                    if k.key_value not in new_key_values:
                        db.delete(k)

            db.commit()
            db.close()
            print(f"[*] Saved LLM config to Database")
        except Exception as e:
            print(f"[!] Error saving config to DB: {e}")

    def update_settings(self, settings: dict):
        with self._lock:
            self.active_provider = settings.get("active_provider", self.active_provider)
            
            for p_data in settings.get("providers", []):
                name = p_data["name"]
                current_p = self.providers.get(name, {})
                
                new_keys = p_data.get("keys", []) # List of {key, label}
                new_models = p_data.get("models", [])
                
                key_idx = current_p.get("key_idx", 0)
                model_idx = current_p.get("model_idx", 0)
                
                if key_idx >= len(new_keys): key_idx = 0
                if model_idx >= len(new_models): model_idx = 0
                
                self.providers[name] = {
                    "keys": new_keys,
                    "models": new_models,
                    "key_idx": key_idx,
                    "model_idx": model_idx
                }
            
            self._save_to_db()

    def get_current(self):
        with self._lock:
            p = self.providers.get(self.active_provider)
            if not p:
                raise Exception(f"Provider {self.active_provider} not configured.")
            
            if not p.get("keys"):
                raise Exception(f"No API keys configured for {self.active_provider}.")
            
            k_obj = p["keys"][p["key_idx"]]
            return k_obj["key"], p["models"][p["model_idx"]], k_obj["label"]

    def get_active_resource_desc(self):
        with self._lock:
            p = self.providers.get(self.active_provider)
            if not p: return f"Unknown Provider ({self.active_provider})"
            if not p.get("keys"): return f"{self.active_provider.capitalize()} (No Keys)"
            
            k_obj = p["keys"][p["key_idx"]]
            return f"{self.active_provider.capitalize()} {p['models'][p['model_idx']]} ({k_obj['label']})"

    def set_rotation_callback(self, callback):
        """Allows setting a callback after initialization."""
        self.rotation_callback = callback

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
                    self._save_to_db() # Persist the loop back to 0
                    return False
            
            self._save_to_db() # Persist the rotation
            if self.rotation_callback:
                try:
                    self.rotation_callback(self.get_active_resource_desc())
                except Exception:
                    pass  # Don't let callback failures break rotation
            return True

rotation_manager = RotationManager()
