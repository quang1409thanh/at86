from sqlalchemy import Boolean, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user") # "admin" or "user"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # "google", "openai"
    is_active = Column(Boolean, default=False)
    models = Column(JSON, nullable=False) # ["gemini-2.0-flash", ...]
    current_model_idx = Column(Integer, default=0)
    current_key_idx = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    keys = relationship("LLMKey", back_populates="provider", cascade="all, delete-orphan")

class LLMKey(Base):
    __tablename__ = "llm_keys"

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), nullable=False)
    key_value = Column(String(255), nullable=False)
    label = Column(String(100), nullable=False) # e.g., "Account 1", "Backup Key"
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    provider = relationship("LLMProvider", back_populates="keys")
