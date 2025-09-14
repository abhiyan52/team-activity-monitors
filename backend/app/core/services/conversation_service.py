"""
Service for managing conversation threads and messages in the database.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime
import json

from app.models.conversation_models import ConversationThread, ConversationMessage, AgentSession
from app.core.services.enhanced_integrated_agent import EnhancedIntegratedAgent


class ConversationService:
    """
    Service for managing conversation threads, messages, and agent sessions.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self._agent_instances = {}  # Cache for agent instances per thread
    
    def create_thread(self, title: Optional[str] = None) -> ConversationThread:
        """
        Create a new conversation thread.
        
        Args:
            title: Optional title for the thread
            
        Returns:
            Created ConversationThread object
        """
        thread = ConversationThread(
            title=title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        
        # Create agent session for this thread
        agent_session = AgentSession(thread_id=thread.id)
        self.db.add(agent_session)
        self.db.commit()
        
        return thread
    
    def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """
        Get a conversation thread by ID.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            ConversationThread object or None
        """
        return self.db.query(ConversationThread).filter(
            ConversationThread.id == thread_id,
            ConversationThread.is_active == True
        ).first()
    
    def list_threads(self, limit: int = 50, offset: int = 0) -> List[ConversationThread]:
        """
        List conversation threads.
        
        Args:
            limit: Maximum number of threads to return
            offset: Number of threads to skip
            
        Returns:
            List of ConversationThread objects
        """
        return self.db.query(ConversationThread).filter(
            ConversationThread.is_active == True
        ).order_by(desc(ConversationThread.updated_at)).offset(offset).limit(limit).all()
    
    def update_thread_title(self, thread_id: str, title: str) -> bool:
        """
        Update thread title.
        
        Args:
            thread_id: Thread ID
            title: New title
            
        Returns:
            True if updated successfully
        """
        thread = self.get_thread(thread_id)
        if thread:
            thread.title = title
            thread.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def delete_thread(self, thread_id: str) -> bool:
        """
        Soft delete a conversation thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            True if deleted successfully
        """
        thread = self.get_thread(thread_id)
        if thread:
            thread.is_active = False
            thread.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def add_message(self, thread_id: str, role: str, content: str, 
                   intent_analysis: Optional[Dict[str, Any]] = None,
                   processing_time: Optional[int] = None,
                   error_message: Optional[str] = None) -> ConversationMessage:
        """
        Add a message to a conversation thread.
        
        Args:
            thread_id: Thread ID
            role: Message role ('user' or 'assistant')
            content: Message content
            intent_analysis: Optional intent analysis data
            processing_time: Optional processing time in milliseconds
            error_message: Optional error message
            
        Returns:
            Created ConversationMessage object
        """
        message = ConversationMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            intent_analysis=json.dumps(intent_analysis) if intent_analysis else None,
            processing_time=processing_time,
            error_message=error_message
        )
        
        self.db.add(message)
        
        # Update thread timestamp
        thread = self.get_thread(thread_id)
        if thread:
            thread.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_messages(self, thread_id: str, limit: int = 100, offset: int = 0) -> List[ConversationMessage]:
        """
        Get messages for a conversation thread.
        
        Args:
            thread_id: Thread ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of ConversationMessage objects
        """
        return self.db.query(ConversationMessage).filter(
            ConversationMessage.thread_id == thread_id
        ).order_by(asc(ConversationMessage.created_at)).offset(offset).limit(limit).all()
    
    def get_agent_for_thread(self, thread_id: str) -> EnhancedIntegratedAgent:
        """
        Get or create an agent instance for a thread.
        This ensures memory persistence across requests.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            EnhancedIntegratedAgent instance
        """
        if thread_id not in self._agent_instances:
            # Create new agent instance for this thread
            agent = EnhancedIntegratedAgent()
            
            # Load existing conversation history into agent memory
            messages = self.get_messages(thread_id)
            for message in messages:
                if message.role == "user":
                    # Find the corresponding assistant response
                    next_message = self.db.query(ConversationMessage).filter(
                        ConversationMessage.thread_id == thread_id,
                        ConversationMessage.created_at > message.created_at,
                        ConversationMessage.role == "assistant"
                    ).order_by(asc(ConversationMessage.created_at)).first()
                    
                    if next_message:
                        agent.add_to_memory(message.content, next_message.content)
            
            self._agent_instances[thread_id] = agent
        
        return self._agent_instances[thread_id]
    
    async def process_user_query(self, thread_id: str, user_query: str) -> Dict[str, Any]:
        """
        Process a user query using the agent and store the conversation.
        
        Args:
            thread_id: Thread ID
            user_query: User's query
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Store user message
            user_message = self.add_message(thread_id, "user", user_query)
            
            # Get agent for this thread
            agent = self.get_agent_for_thread(thread_id)
            
            # Process query with agent
            response = await agent.run(user_query)
            
            # Calculate processing time
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Store assistant response
            assistant_message = self.add_message(
                thread_id, 
                "assistant", 
                response,
                processing_time=processing_time
            )
            
            # Get memory summary for debugging
            memory_summary = agent.get_memory_summary()
            
            return {
                "success": True,
                "response": response,
                "user_message_id": user_message.id,
                "assistant_message_id": assistant_message.id,
                "processing_time": processing_time,
                "memory_summary": memory_summary
            }
            
        except Exception as e:
            # Store error message
            error_response = f"❌ Error processing query: {str(e)}"
            self.add_message(
                thread_id, 
                "assistant", 
                error_response,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "response": error_response,
                "error": str(e)
            }
    
    def get_conversation_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            List of message dictionaries
        """
        messages = self.get_messages(thread_id)
        return [message.to_dict() for message in messages]
    
    def clear_agent_memory(self, thread_id: str) -> bool:
        """
        Clear agent memory for a specific thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            True if cleared successfully
        """
        if thread_id in self._agent_instances:
            self._agent_instances[thread_id].clear_memory()
            return True
        return False
    
    def cleanup_old_agents(self, max_age_hours: int = 24):
        """
        Clean up old agent instances to free memory.
        
        Args:
            max_age_hours: Maximum age of agent instances in hours
        """
        # This is a simple implementation - in production you might want
        # to track agent creation time and clean up based on that
        pass
