"""
Conversation management for the AI analytics chatbot
Handles chat sessions, message history, and context
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from flask import session

from models import db, ChatConversation, ChatMessage
from .utils import generate_session_token, MessageFormatter


class ConversationManager:
    """Manages chat conversations and message history"""
    
    def __init__(self):
        self.current_conversation = None
    
    def get_or_create_conversation(self, admin_email: str) -> ChatConversation:
        """Get existing active conversation or create a new one"""
        
        # Check if there's an active conversation for this admin
        conversation = ChatConversation.query.filter_by(
            admin_email=admin_email,
            status='active'
        ).order_by(ChatConversation.updated_at.desc()).first()
        
        # Create new conversation if none exists or if the last one is old
        if not conversation or self._is_conversation_expired(conversation):
            conversation = self._create_new_conversation(admin_email)
        
        self.current_conversation = conversation
        return conversation
    
    def _create_new_conversation(self, admin_email: str) -> ChatConversation:
        """Create a new conversation session"""
        
        # Create conversation with explicit naive datetime
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        conversation = ChatConversation(
            admin_email=admin_email,
            session_token=generate_session_token(),
            status='active'
        )
        # Set timestamps explicitly to ensure consistency
        conversation.created_at = now_naive
        conversation.updated_at = now_naive
        
        db.session.add(conversation)
        db.session.commit()
        
        # Add welcome message
        self.add_system_message(
            conversation.id,
            "Welcome to AI Analytics! Ask me questions about your Minipass data."
        )
        
        return conversation
    
    def _is_conversation_expired(self, conversation: ChatConversation) -> bool:
        """Check if conversation is expired (older than 24 hours)"""
        from datetime import timedelta
        
        if not conversation.updated_at:
            return True
        
        # Handle timezone-aware vs naive datetime comparison
        now = datetime.now(timezone.utc)
        updated_at = conversation.updated_at
        
        # If the stored datetime is naive, assume it's UTC
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        
        age = now - updated_at
        return age > timedelta(hours=24)
    
    def add_user_message(self, conversation_id: int, content: str) -> ChatMessage:
        """Add a user message to the conversation"""
        
        message = ChatMessage(
            conversation_id=conversation_id,
            message_type='user',
            content=content
        )
        
        db.session.add(message)
        self._update_conversation_timestamp(conversation_id)
        db.session.commit()
        
        return message
    
    def add_assistant_message(self, conversation_id: int, content: str,
                            sql_query: Optional[str] = None,
                            query_result: Optional[str] = None,
                            ai_provider: Optional[str] = None,
                            ai_model: Optional[str] = None,
                            tokens_used: int = 0,
                            cost_cents: int = 0,
                            response_time_ms: int = 0) -> ChatMessage:
        """Add an assistant message to the conversation"""
        
        message = ChatMessage(
            conversation_id=conversation_id,
            message_type='assistant',
            content=content,
            sql_query=sql_query,
            query_result=query_result,
            ai_provider=ai_provider,
            ai_model=ai_model,
            tokens_used=tokens_used,
            cost_cents=cost_cents,
            response_time_ms=response_time_ms
        )
        
        db.session.add(message)
        self._update_conversation_timestamp(conversation_id)
        db.session.commit()
        
        return message
    
    def add_error_message(self, conversation_id: int, error: str) -> ChatMessage:
        """Add an error message to the conversation"""
        
        message = ChatMessage(
            conversation_id=conversation_id,
            message_type='error',
            content=f"Error: {error}"
        )
        
        db.session.add(message)
        self._update_conversation_timestamp(conversation_id)
        db.session.commit()
        
        return message
    
    def add_system_message(self, conversation_id: int, content: str) -> ChatMessage:
        """Add a system message to the conversation"""
        
        message = ChatMessage(
            conversation_id=conversation_id,
            message_type='system',
            content=content
        )
        
        db.session.add(message)
        self._update_conversation_timestamp(conversation_id)
        db.session.commit()
        
        return message
    
    def get_conversation_messages(self, conversation_id: int, 
                                limit: int = 50) -> List[ChatMessage]:
        """Get messages for a conversation"""
        
        return ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
    
    def get_conversation_context(self, conversation_id: int, 
                               context_messages: int = 5) -> str:
        """Get recent conversation context for AI"""
        
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.created_at.desc()).limit(context_messages).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        context_parts = []
        for msg in messages:
            if msg.message_type == 'user':
                context_parts.append(f"User: {msg.content}")
            elif msg.message_type == 'assistant':
                context_parts.append(f"Assistant: {msg.content}")
                if msg.sql_query:
                    context_parts.append(f"SQL: {msg.sql_query}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _update_conversation_timestamp(self, conversation_id: int):
        """Update conversation's updated_at timestamp"""
        
        conversation = ChatConversation.query.get(conversation_id)
        if conversation:
            # Store as naive datetime (SQLite default behavior)
            conversation.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    def format_messages_for_display(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Format messages for chat UI display"""
        
        messages = self.get_conversation_messages(conversation_id)
        formatted_messages = []
        
        for msg in messages:
            if msg.message_type == 'user':
                formatted_msg = MessageFormatter.format_user_message(
                    msg.content, msg.created_at
                )
            elif msg.message_type == 'assistant':
                # Parse query result for chart data
                chart_data = None
                if msg.query_result:
                    try:
                        result_data = json.loads(msg.query_result)
                        if result_data.get('chart_suggestion'):
                            chart_data = result_data['chart_suggestion']
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                formatted_msg = MessageFormatter.format_assistant_message(
                    msg.content, msg.created_at, msg.sql_query, chart_data
                )
            elif msg.message_type == 'error':
                formatted_msg = MessageFormatter.format_error_message(
                    msg.content, msg.created_at
                )
            else:  # system
                formatted_msg = MessageFormatter.format_system_message(
                    msg.content, msg.created_at
                )
            
            # Add metadata
            formatted_msg.update({
                'id': msg.id,
                'ai_provider': msg.ai_provider,
                'ai_model': msg.ai_model,
                'tokens_used': msg.tokens_used,
                'cost_cents': msg.cost_cents,
                'response_time_ms': msg.response_time_ms
            })
            
            formatted_messages.append(formatted_msg)
        
        return formatted_messages
    
    def archive_conversation(self, conversation_id: int):
        """Archive a conversation"""
        
        conversation = ChatConversation.query.get(conversation_id)
        if conversation:
            conversation.status = 'archived'
            db.session.commit()
    
    def delete_conversation(self, conversation_id: int):
        """Delete a conversation and all its messages"""
        
        conversation = ChatConversation.query.get(conversation_id)
        if conversation:
            # Messages will be deleted automatically due to cascade
            db.session.delete(conversation)
            db.session.commit()
    
    def get_user_conversations(self, admin_email: str, 
                             limit: int = 10) -> List[ChatConversation]:
        """Get user's recent conversations"""
        
        return ChatConversation.query.filter_by(
            admin_email=admin_email
        ).order_by(ChatConversation.updated_at.desc()).limit(limit).all()
    
    def get_conversation_stats(self, conversation_id: int) -> Dict[str, Any]:
        """Get statistics for a conversation"""
        
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return {}
        
        messages = ChatMessage.query.filter_by(conversation_id=conversation_id).all()
        
        total_tokens = sum(msg.tokens_used for msg in messages if msg.tokens_used)
        total_cost = sum(msg.cost_cents for msg in messages if msg.cost_cents)
        
        message_counts = {
            'user': len([m for m in messages if m.message_type == 'user']),
            'assistant': len([m for m in messages if m.message_type == 'assistant']),
            'error': len([m for m in messages if m.message_type == 'error']),
            'system': len([m for m in messages if m.message_type == 'system'])
        }
        
        providers_used = list(set(msg.ai_provider for msg in messages 
                                if msg.ai_provider))
        
        return {
            'conversation_id': conversation_id,
            'session_token': conversation.session_token,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at,
            'status': conversation.status,
            'total_messages': len(messages),
            'message_counts': message_counts,
            'total_tokens': total_tokens,
            'total_cost_cents': total_cost,
            'providers_used': providers_used
        }


# Global conversation manager instance
conversation_manager = ConversationManager()