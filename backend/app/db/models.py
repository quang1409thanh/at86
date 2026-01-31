from sqlalchemy import Boolean, Column, Integer, String, JSON, DateTime
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

class LLMGlobalConfig(Base):
    __tablename__ = "llm_config"

    id = Column(Integer, primary_key=True)
    active_provider = Column(String(50), default="google")
    providers = Column(JSON, nullable=False) # Stores the list of keys/models
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
