from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class User(BaseModel):
    """User model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    plan: str = "free"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Credit(BaseModel):
    """Credit model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    balance: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Transaction(BaseModel):
    """Transaction model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float
    description: str
    model: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class APIKey(BaseModel):
    """API key model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None 