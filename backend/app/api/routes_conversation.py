"""
API routes for conversation thread and message management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.services.conversation_service import ConversationService
from app.models.conversation_models import ConversationThread, ConversationMessage

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# Pydantic models for request/response
class ThreadCreateRequest(BaseModel):
    title: Optional[str] = None


class ThreadUpdateRequest(BaseModel):
    title: str


class MessageRequest(BaseModel):
    content: str


class ThreadResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    is_active: bool
    message_count: int

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    thread_id: str
    role: str
    content: str
    created_at: str
    intent_analysis: Optional[str] = None
    processing_time: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class QueryResponse(BaseModel):
    success: bool
    response: str
    user_message_id: Optional[str] = None
    assistant_message_id: Optional[str] = None
    processing_time: Optional[int] = None
    memory_summary: Optional[dict] = None
    error: Optional[str] = None


class ConversationHistoryResponse(BaseModel):
    thread: ThreadResponse
    messages: List[MessageResponse]


# Dependency to get conversation service
def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    request: ThreadCreateRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Create a new conversation thread.
    
    Args:
        request: Thread creation request with optional title
        conversation_service: Conversation service dependency
        
    Returns:
        Created thread information
    """
    try:
        thread = conversation_service.create_thread(request.title)
        return ThreadResponse(**thread.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create thread: {str(e)}"
        )


@router.get("/threads", response_model=List[ThreadResponse])
async def list_threads(
    limit: int = 50,
    offset: int = 0,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    List conversation threads.
    
    Args:
        limit: Maximum number of threads to return
        offset: Number of threads to skip
        conversation_service: Conversation service dependency
        
    Returns:
        List of thread information
    """
    try:
        threads = conversation_service.list_threads(limit, offset)
        return [ThreadResponse(**thread.to_dict()) for thread in threads]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list threads: {str(e)}"
        )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get a specific conversation thread.
    
    Args:
        thread_id: Thread ID
        conversation_service: Conversation service dependency
        
    Returns:
        Thread information
    """
    thread = conversation_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    return ThreadResponse(**thread.to_dict())


@router.put("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    request: ThreadUpdateRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Update thread title.
    
    Args:
        thread_id: Thread ID
        request: Thread update request
        conversation_service: Conversation service dependency
        
    Returns:
        Updated thread information
    """
    success = conversation_service.update_thread_title(thread_id, request.title)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    thread = conversation_service.get_thread(thread_id)
    return ThreadResponse(**thread.to_dict())


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Delete a conversation thread.
    
    Args:
        thread_id: Thread ID
        conversation_service: Conversation service dependency
    """
    success = conversation_service.delete_thread(thread_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )


@router.post("/threads/{thread_id}/messages", response_model=QueryResponse)
async def send_message(
    thread_id: str,
    request: MessageRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Send a message to a conversation thread and get agent response.
    
    Args:
        thread_id: Thread ID
        request: Message request with content
        conversation_service: Conversation service dependency
        
    Returns:
        Agent response and metadata
    """
    # Verify thread exists
    thread = conversation_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    try:
        result = await conversation_service.process_user_query(thread_id, request.content)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    thread_id: str,
    limit: int = 100,
    offset: int = 0,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get messages for a conversation thread.
    
    Args:
        thread_id: Thread ID
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        conversation_service: Conversation service dependency
        
    Returns:
        List of messages
    """
    # Verify thread exists
    thread = conversation_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    try:
        messages = conversation_service.get_messages(thread_id, limit, offset)
        return [MessageResponse(**message.to_dict()) for message in messages]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/threads/{thread_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    thread_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get complete conversation history for a thread.
    
    Args:
        thread_id: Thread ID
        conversation_service: Conversation service dependency
        
    Returns:
        Thread and message history
    """
    # Verify thread exists
    thread = conversation_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    try:
        messages = conversation_service.get_conversation_history(thread_id)
        return ConversationHistoryResponse(
            thread=ThreadResponse(**thread.to_dict()),
            messages=[MessageResponse(**msg) for msg in messages]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@router.post("/threads/{thread_id}/clear-memory", status_code=status.HTTP_200_OK)
async def clear_agent_memory(
    thread_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Clear agent memory for a specific thread.
    
    Args:
        thread_id: Thread ID
        conversation_service: Conversation service dependency
        
    Returns:
        Success message
    """
    # Verify thread exists
    thread = conversation_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    try:
        success = conversation_service.clear_agent_memory(thread_id)
        if success:
            return {"message": "Agent memory cleared successfully"}
        else:
            return {"message": "No agent memory found for this thread"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear agent memory: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for conversation service."""
    return {"status": "healthy", "service": "conversation-api"}
