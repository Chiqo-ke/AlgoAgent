"""
LangChain Conversation Manager for AlgoAgent
============================================

This module provides conversation memory and context management using LangChain
integrated with Django's SQLite database for persistent storage.

Note: Updated for LangChain 1.0+ which deprecated the memory module.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


class DjangoSQLiteChatHistory(BaseChatMessageHistory):
    """
    Custom chat history implementation that stores messages in Django SQLite database.
    This integrates LangChain's conversation memory with our Django models.
    """
    
    def __init__(self, session_id: str):
        """
        Initialize chat history for a specific session.
        
        Args:
            session_id: Unique identifier for the chat session
        """
        self.session_id = session_id
        self._session = None
        self._ensure_session()
    
    def _ensure_session(self):
        """Ensure the chat session exists in the database"""
        from strategy_api.models import StrategyChat
        
        try:
            self._session = StrategyChat.objects.get(session_id=self.session_id)
        except StrategyChat.DoesNotExist:
            logger.warning(f"Session {self.session_id} not found. Creating new session.")
            self._session = StrategyChat.objects.create(
                session_id=self.session_id,
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve all messages from the database for this session"""
        from strategy_api.models import StrategyChatMessage
        
        db_messages = StrategyChatMessage.objects.filter(session=self._session).order_by('created_at')
        
        langchain_messages = []
        for msg in db_messages:
            if msg.role == 'user':
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == 'assistant':
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == 'system':
                langchain_messages.append(SystemMessage(content=msg.content))
        
        return langchain_messages
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the database"""
        from strategy_api.models import StrategyChatMessage
        from django.utils import timezone
        
        # Determine role based on message type
        if isinstance(message, HumanMessage):
            role = 'user'
        elif isinstance(message, AIMessage):
            role = 'assistant'
        elif isinstance(message, SystemMessage):
            role = 'system'
        else:
            role = 'user'  # Default fallback
        
        # Create message in database
        StrategyChatMessage.objects.create(
            session=self._session,
            role=role,
            content=message.content,
            metadata=getattr(message, 'additional_kwargs', {})
        )
        
        # Update session metadata
        self._session.message_count += 1
        self._session.last_message_at = timezone.now()
        self._session.save(update_fields=['message_count', 'last_message_at'])
    
    def clear(self) -> None:
        """Clear all messages from this session"""
        from strategy_api.models import StrategyChatMessage
        
        StrategyChatMessage.objects.filter(session=self._session).delete()
        self._session.message_count = 0
        self._session.save(update_fields=['message_count'])


class ConversationManager:
    """
    Manages conversation sessions with LangChain chat history and Django persistence.
    
    Note: Updated for LangChain 1.0+ - ConversationBufferMemory has been deprecated.
    We now use the chat_history directly for memory management.
    """
    
    def __init__(self, session_id: Optional[str] = None, user=None):
        """
        Initialize conversation manager.
        
        Args:
            session_id: Optional existing session ID. If None, creates a new session.
            user: Django User object for this conversation
        """
        self.session_id = session_id or self._generate_session_id()
        self.user = user
        self.chat_history = DjangoSQLiteChatHistory(self.session_id)
        
        logger.info(f"Initialized ConversationManager for session {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"chat_{uuid.uuid4().hex[:16]}"
    
    def get_session(self):
        """Get the StrategyChat model instance"""
        from strategy_api.models import StrategyChat
        return StrategyChat.objects.get(session_id=self.session_id)
    
    def get_messages(self) -> List[BaseMessage]:
        """
        Get all messages in the conversation.
        
        Returns:
            List of LangChain message objects
        """
        return self.chat_history.messages
    
    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a user message to the conversation.
        
        Args:
            content: Message content
            metadata: Optional metadata to store with the message
        """
        message = HumanMessage(content=content)
        if metadata:
            message.additional_kwargs = metadata
        
        self.chat_history.add_message(message)
        logger.debug(f"Added user message to session {self.session_id}")
    
    def add_ai_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Add an AI assistant message to the conversation.
        
        Args:
            content: Message content
            metadata: Optional metadata to store with the message
        """
        message = AIMessage(content=content)
        if metadata:
            message.additional_kwargs = metadata
        
        self.chat_history.add_message(message)
        logger.debug(f"Added AI message to session {self.session_id}")
    
    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the conversation.
        
        Args:
            content: Message content
        """
        message = SystemMessage(content=content)
        self.chat_history.add_message(message)
        logger.debug(f"Added system message to session {self.session_id}")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the full conversation history as a list of dictionaries.
        
        Returns:
            List of messages with 'role' and 'content' keys
        """
        messages = self.chat_history.messages
        history = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            elif isinstance(msg, AIMessage):
                role = 'assistant'
            elif isinstance(msg, SystemMessage):
                role = 'system'
            else:
                role = 'unknown'
            
            history.append({
                'role': role,
                'content': msg.content
            })
        
        return history
    
    def get_context_window(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get recent conversation context (last N messages).
        
        Args:
            max_messages: Maximum number of recent messages to return
            
        Returns:
            List of recent messages
        """
        history = self.get_conversation_history()
        return history[-max_messages:] if len(history) > max_messages else history
    
    def get_conversation_summary(self) -> str:
        """
        Generate a summary of the conversation context.
        
        Returns:
            String summary of the conversation
        """
        history = self.get_conversation_history()
        
        if not history:
            return "No conversation history yet."
        
        user_messages = [msg for msg in history if msg['role'] == 'user']
        ai_messages = [msg for msg in history if msg['role'] == 'assistant']
        
        summary = f"Conversation has {len(history)} messages "
        summary += f"({len(user_messages)} from user, {len(ai_messages)} from assistant). "
        
        # Get session info
        session = self.get_session()
        if session.strategy:
            summary += f"Discussing strategy: {session.strategy.name}. "
        
        return summary
    
    def update_session_summary(self, ai_generated_summary: str) -> None:
        """
        Update the session's context summary (useful for long conversations).
        
        Args:
            ai_generated_summary: AI-generated summary of the conversation
        """
        session = self.get_session()
        session.context_summary = ai_generated_summary
        session.save(update_fields=['context_summary'])
        logger.info(f"Updated summary for session {self.session_id}")
    
    def link_strategy(self, strategy_id: int) -> None:
        """
        Link this chat session to a specific strategy.
        
        Args:
            strategy_id: ID of the Strategy model to link
        """
        from strategy_api.models import Strategy
        
        session = self.get_session()
        try:
            strategy = Strategy.objects.get(id=strategy_id)
            session.strategy = strategy
            session.save(update_fields=['strategy'])
            logger.info(f"Linked session {self.session_id} to strategy {strategy_id}")
        except Strategy.DoesNotExist:
            logger.error(f"Strategy {strategy_id} not found")
    
    def set_session_title(self, title: str) -> None:
        """
        Set a custom title for the session.
        
        Args:
            title: Session title
        """
        session = self.get_session()
        session.title = title
        session.save(update_fields=['title'])
    
    def clear_conversation(self) -> None:
        """Clear all messages from this conversation"""
        self.chat_history.clear()
        logger.info(f"Cleared conversation for session {self.session_id}")
    
    def deactivate_session(self) -> None:
        """Mark this session as inactive"""
        session = self.get_session()
        session.is_active = False
        session.save(update_fields=['is_active'])
        logger.info(f"Deactivated session {self.session_id}")


def get_or_create_conversation(session_id: Optional[str] = None, user=None) -> ConversationManager:
    """
    Helper function to get or create a conversation manager.
    
    Args:
        session_id: Optional session ID. If None, creates a new session.
        user: Django User object
        
    Returns:
        ConversationManager instance
    """
    return ConversationManager(session_id=session_id, user=user)


def list_user_sessions(user) -> List[Dict[str, Any]]:
    """
    List all chat sessions for a user.
    
    Args:
        user: Django User object
        
    Returns:
        List of session dictionaries
    """
    from strategy_api.models import StrategyChat
    
    sessions = StrategyChat.objects.filter(user=user).order_by('-updated_at')
    
    return [{
        'session_id': s.session_id,
        'title': s.title,
        'message_count': s.message_count,
        'is_active': s.is_active,
        'created_at': s.created_at,
        'updated_at': s.updated_at,
        'last_message_at': s.last_message_at,
        'strategy': s.strategy.name if s.strategy else None,
    } for s in sessions]
