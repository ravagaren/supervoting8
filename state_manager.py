"""
State management for bot questionnaire ratings and user votes.

This module provides a centralized StateManager class to replace global dictionaries
for storing message ratings and user votes, improving code organization and testability.
"""

from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MessageRating:
    """Rating data for a single message/questionnaire."""
    like: int = 0
    super_like: int = 0


@dataclass
class UserMessageRating:
    """User's rating for a specific message."""
    like: int = 0
    super_like: int = 0
    wish: int = 0


class StateManager:
    """
    Centralized state management for questionnaire ratings and user votes.
    
    Replaces global dictionaries:
    - dictionary_storing_message_ratings
    - dictionary_storing_user_ratings
    
    Provides clean interface for accessing and updating rating data.
    """
    
    def __init__(self):
        """Initialize state storage."""
        # Stores ratings for each message: {message_id: MessageRating}
        self._message_ratings: Dict[str, MessageRating] = {}
        
        # Stores user ratings for messages: {user_id: {message_id: UserMessageRating}}
        self._user_ratings: Dict[int, Dict[str, UserMessageRating]] = {}
    
    # ============ Message Ratings ============
    
    def get_message_rating(self, message_id: str) -> MessageRating:
        """
        Get or initialize message rating.
        
        Args:
            message_id: The message/questionnaire ID
            
        Returns:
            MessageRating object for the given message_id
        """
        if message_id not in self._message_ratings:
            self._message_ratings[message_id] = MessageRating()
        return self._message_ratings[message_id]
    
    def increment_message_like(self, message_id: str) -> None:
        """Increment like count for a message."""
        rating = self.get_message_rating(message_id)
        rating.like += 1
    
    def increment_message_super_like(self, message_id: str) -> None:
        """Increment super_like count for a message."""
        rating = self.get_message_rating(message_id)
        rating.super_like += 1
    
    def set_message_rating(self, message_id: str, like: int, super_like: int) -> None:
        """
        Set rating values for a message.
        
        Args:
            message_id: The message/questionnaire ID
            like: Number of likes
            super_like: Number of super likes
        """
        self._message_ratings[message_id] = MessageRating(like=like, super_like=super_like)
    
    def get_all_message_ratings(self) -> Dict[str, MessageRating]:
        """Get all message ratings (for logging/debugging)."""
        return self._message_ratings.copy()
    
    # ============ User Ratings ============
    
    def get_user_rating(self, user_id: int, message_id: str) -> UserMessageRating:
        """
        Get or initialize user's rating for a specific message.
        
        Args:
            user_id: The user ID
            message_id: The message/questionnaire ID
            
        Returns:
            UserMessageRating object for the given user and message
        """
        if user_id not in self._user_ratings:
            self._user_ratings[user_id] = {}
        
        if message_id not in self._user_ratings[user_id]:
            self._user_ratings[user_id][message_id] = UserMessageRating()
        
        return self._user_ratings[user_id][message_id]
    
    def increment_user_like(self, user_id: int, message_id: str) -> None:
        """Increment like count for a user on a specific message."""
        rating = self.get_user_rating(user_id, message_id)
        rating.like += 1
    
    def increment_user_super_like(self, user_id: int, message_id: str) -> None:
        """Increment super_like count for a user on a specific message."""
        rating = self.get_user_rating(user_id, message_id)
        rating.super_like += 1
    
    def has_user_voted_super_like(self, user_id: int, message_id: str) -> bool:
        """Check if user has already voted super_like for this message."""
        rating = self.get_user_rating(user_id, message_id)
        return rating.super_like > 0
    
    def get_user_ratings_for_message(self, user_id: int, message_id: str) -> Dict[str, int]:
        """
        Get user's rating dict for a message (for backward compatibility).
        
        Returns dict with 'like', 'super_like', 'wish' keys.
        """
        rating = self.get_user_rating(user_id, message_id)
        return {
            'like': rating.like,
            'super_like': rating.super_like,
            'wish': rating.wish
        }
    
    def get_all_user_ratings(self) -> Dict[int, Dict[str, Dict[str, int]]]:
        """
        Get all user ratings in legacy format (for logging/debugging).
        
        Returns dict structured as: {user_id: {message_id: {rating_type: count}}}
        """
        result = {}
        for user_id, messages in self._user_ratings.items():
            result[user_id] = {}
            for message_id, rating in messages.items():
                result[user_id][message_id] = {
                    'like': rating.like,
                    'super_like': rating.super_like,
                    'wish': rating.wish
                }
        return result
    
    # ============ Utilities ============
    
    def reset(self) -> None:
        """Reset all state (useful for testing)."""
        self._message_ratings.clear()
        self._user_ratings.clear()


# Global state manager instance
state_manager = StateManager()
