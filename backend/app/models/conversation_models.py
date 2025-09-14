"""
Database models for conversation threads and messages.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List
import uuid

Base = declarative_base()


class ConversationThread(Base):
    """
    Model for conversation threads.
    Each thread represents a conversation session with the agent.
    """
    __tablename__ = "conversation_threads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)  # Auto-generated or user-provided title
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    messages = relationship("ConversationMessage", back_populates="thread", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """Convert thread to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "message_count": len(self.messages) if self.messages else 0
        }


class ConversationMessage(Base):
    """
    Model for individual messages in a conversation thread.
    """
    __tablename__ = "conversation_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, ForeignKey("conversation_threads.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Optional metadata
    intent_analysis = Column(Text, nullable=True)  # JSON string of intent analysis
    processing_time = Column(Integer, nullable=True)  # Processing time in milliseconds
    error_message = Column(Text, nullable=True)  # Error message if processing failed
    
    # Relationships
    thread = relationship("ConversationThread", back_populates="messages")
    
    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "intent_analysis": self.intent_analysis,
            "processing_time": self.processing_time,
            "error_message": self.error_message
        }


class AgentSession(Base):
    """
    Model for storing agent session state and memory.
    This helps maintain agent memory across requests.
    """
    __tablename__ = "agent_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, ForeignKey("conversation_threads.id"), nullable=False, unique=True)
    agent_memory = Column(Text, nullable=True)  # JSON string of agent memory state
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    thread = relationship("ConversationThread")
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
