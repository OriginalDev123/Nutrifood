"""
Conversation Memory Service
Manages chat history and session context for multi-turn conversations
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ConversationSession:
    """Conversation session with history"""
    session_id: str
    user_id: Optional[str]
    messages: List[Message]
    created_at: float
    last_active: float
    metadata: Optional[Dict[str, Any]] = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to session"""
        message = Message(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata
        )
        self.messages.append(message)
        self.last_active = time.time()
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages (limited)"""
        return self.messages[-limit:]
    
    def get_context_summary(self, max_turns: int = 5) -> str:
        """
        Get conversation context summary for prompts
        
        Args:
            max_turns: Maximum number of Q&A turns to include
        
        Returns:
            Formatted conversation history string
        """
        recent = self.messages[-(max_turns * 2):]  # Get last N turns (user + assistant)
        
        if not recent:
            return ""
        
        lines = []
        for msg in recent:
            if msg.role == "user":
                lines.append(f"User: {msg.content}")
            else:
                lines.append(f"Assistant: {msg.content}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "last_active": self.last_active,
            "metadata": self.metadata
        }


class ConversationMemoryService:
    """
    Service for managing conversation memory and sessions
    
    Features:
    - Session creation and retrieval
    - Message history storage
    - Context extraction for prompts
    - Automatic cleanup of old sessions
    - Support for in-memory or Redis backend
    """
    
    def __init__(
        self,
        max_session_age_hours: int = 24,
        max_messages_per_session: int = 100,
        cleanup_interval_minutes: int = 60
    ):
        """
        Initialize memory service
        
        Args:
            max_session_age_hours: Maximum age of inactive sessions before cleanup
            max_messages_per_session: Maximum messages to store per session
            cleanup_interval_minutes: How often to run cleanup
        """
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_session_age = timedelta(hours=max_session_age_hours)
        self.max_messages = max_messages_per_session
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.last_cleanup = time.time()
        
        logger.info(
            f"✅ ConversationMemoryService initialized "
            f"(max_age={max_session_age_hours}h, max_msgs={max_messages_per_session})"
        )
    
    def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create new conversation session
        
        Args:
            user_id: Optional user identifier
            metadata: Optional session metadata
        
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            created_at=time.time(),
            last_active=time.time(),
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        
        logger.info(f"📝 Created session: {session_id} (user: {user_id})")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get session by ID
        
        Args:
            session_id: Session identifier
        
        Returns:
            ConversationSession or None if not found
        """
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session expired
            age = time.time() - session.last_active
            if age > self.max_session_age.total_seconds():
                logger.warning(f"⚠️  Session {session_id} expired (age: {age:.0f}s)")
                self.delete_session(session_id)
                return None
        
        return session
    
    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ConversationSession:
        """
        Get existing session or create new one
        
        Args:
            session_id: Optional session ID to retrieve
            user_id: Optional user ID for new session
            metadata: Optional metadata for new session
        
        Returns:
            ConversationSession (existing or new)
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        # Create new session
        new_id = self.create_session(user_id=user_id, metadata=metadata)
        return self.sessions[new_id]
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add message to session
        
        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            metadata: Optional message metadata
        
        Returns:
            bool: True if added successfully
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.warning(f"⚠️  Session {session_id} not found")
            return False
        
        session.add_message(role, content, metadata)
        
        # Trim messages if exceeding limit
        if len(session.messages) > self.max_messages:
            removed = len(session.messages) - self.max_messages
            session.messages = session.messages[-self.max_messages:]
            logger.debug(f"🗑️  Trimmed {removed} old messages from session {session_id}")
        
        logger.debug(
            f"💬 Added {role} message to session {session_id} "
            f"(total: {len(session.messages)})"
        )
        
        return True
    
    def get_conversation_context(
        self,
        session_id: str,
        max_turns: int = 5
    ) -> Optional[str]:
        """
        Get conversation context for prompt
        
        Args:
            session_id: Session identifier
            max_turns: Maximum Q&A turns to include
        
        Returns:
            Formatted conversation history or None
        """
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        return session.get_context_summary(max_turns=max_turns)
    
    def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> Optional[List[Dict]]:
        """
        Get recent messages from session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages
        
        Returns:
            List of message dicts or None
        """
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        recent = session.get_recent_messages(limit=limit)
        return [msg.to_dict() for msg in recent]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session identifier
        
        Returns:
            bool: True if deleted
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️  Deleted session: {session_id}")
            return True
        return False
    
    def cleanup_old_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            int: Number of sessions deleted
        """
        current_time = time.time()
        
        # Check if cleanup needed
        if current_time - self.last_cleanup < self.cleanup_interval.total_seconds():
            return 0
        
        expired = []
        max_age_seconds = self.max_session_age.total_seconds()
        
        for session_id, session in self.sessions.items():
            age = current_time - session.last_active
            if age > max_age_seconds:
                expired.append(session_id)
        
        # Delete expired sessions
        for session_id in expired:
            del self.sessions[session_id]
        
        self.last_cleanup = current_time
        
        if expired:
            logger.info(f"🗑️  Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_stats(self) -> Dict:
        """
        Get memory service statistics
        
        Returns:
            Dict with stats
        """
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        
        return {
            "active_sessions": len(self.sessions),
            "total_messages": total_messages,
            "avg_messages_per_session": (
                total_messages / len(self.sessions) if self.sessions else 0
            ),
            "max_session_age_hours": self.max_session_age.total_seconds() / 3600,
            "max_messages_per_session": self.max_messages
        }


# Global service instance
_memory_service: Optional[ConversationMemoryService] = None


def get_memory_service() -> ConversationMemoryService:
    """
    Get or create global memory service instance
    
    Returns:
        ConversationMemoryService instance
    """
    global _memory_service
    
    if _memory_service is None:
        _memory_service = ConversationMemoryService(
            max_session_age_hours=24,
            max_messages_per_session=100,
            cleanup_interval_minutes=60
        )
    
    return _memory_service


def initialize_memory_service():
    """Initialize memory service on app startup"""
    global _memory_service
    
    if _memory_service is None:
        _memory_service = ConversationMemoryService()
        logger.info("✅ ConversationMemoryService initialized")
