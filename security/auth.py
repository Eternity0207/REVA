"""Security utilities for agent authentication"""
import secrets
import hashlib
from typing import Optional
import hmac

class TokenManager:
    """Generate and validate agent tokens"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_agent_credentials(agent_id: str) -> dict:
        """Generate credentials for new agent"""
        token = TokenManager.generate_token(32)
        return {
            "agent_id": agent_id,
            "token": token,
        }
    
    @staticmethod
    def validate_token(agent_id: str, provided_token: str, stored_token: str) -> bool:
        """Validate agent token using constant-time comparison"""
        return hmac.compare_digest(provided_token, stored_token)

class AuthMiddleware:
    """Token validation for API endpoints"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
    
    def verify_agent_token(self, agent_id: str, token: str) -> bool:
        """Verify agent credentials"""
        agent = self.task_manager.get_agent(agent_id)
        if not agent:
            return False
        return TokenManager.validate_token(agent_id, token, agent.token)
