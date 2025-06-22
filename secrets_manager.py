"""
Secrets Management System for Energy Grid Management Agent
Optimized for Streamlit Cloud deployment with fallback to environment variables.
"""
import streamlit as st
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class SecretsConfig:
    """Configuration for secrets management."""
    # Neo4j Database
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str
    
    # Claude AI
    CLAUDE_API_KEY: str
    
    # Optional configurations
    ENCRYPTION_KEY: Optional[str] = None
    HASH_SALT: Optional[str] = None
    SESSION_TIMEOUT: int = 3600
    LOG_LEVEL: str = "INFO"
    CACHE_TTL: int = 300
    MAX_WORKERS: int = 4
    HEALTH_CHECK_INTERVAL: int = 300
    SERVICE_NAME: str = "energy-grid-agent"
    APP_VERSION: str = "1.0.0"

class SecretsManager:
    """
    Manages application secrets with priority:
    1. Streamlit Cloud secrets (st.secrets)
    2. Environment variables (local development)
    3. Default values (fallback)
    """
    
    def __init__(self):
        self._secrets = None
        self._validation_errors = []
        self._load_secrets()
    
    def _load_secrets(self) -> None:
        """Load secrets from Streamlit Cloud or environment variables."""
        try:
            # Try to load from Streamlit Cloud secrets first
            if hasattr(st, 'secrets') and st.secrets:
                self._secrets = self._load_from_streamlit_secrets()
                logger.info("Loaded secrets from Streamlit Cloud")
            else:
                # Fallback to environment variables
                self._secrets = self._load_from_environment()
                logger.info("Loaded secrets from environment variables")
                
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            self._secrets = self._load_defaults()
    
    def _load_from_streamlit_secrets(self) -> SecretsConfig:
        """Load secrets from Streamlit Cloud st.secrets."""
        try:
            return SecretsConfig(
                # Neo4j Database
                NEO4J_URI=st.secrets.get("NEO4J_URI", ""),
                NEO4J_USERNAME=st.secrets.get("NEO4J_USERNAME", "neo4j"),
                NEO4J_PASSWORD=st.secrets.get("NEO4J_PASSWORD", ""),
                NEO4J_DATABASE=st.secrets.get("NEO4J_DATABASE", "neo4j"),
                
                # Claude AI
                CLAUDE_API_KEY=st.secrets.get("CLAUDE_API_KEY", ""),
                
                # Optional configurations
                ENCRYPTION_KEY=st.secrets.get("ENCRYPTION_KEY"),
                HASH_SALT=st.secrets.get("HASH_SALT"),
                SESSION_TIMEOUT=int(st.secrets.get("SESSION_TIMEOUT", "3600")),
                LOG_LEVEL=st.secrets.get("LOG_LEVEL", "INFO"),
                CACHE_TTL=int(st.secrets.get("CACHE_TTL", "300")),
                MAX_WORKERS=int(st.secrets.get("MAX_WORKERS", "4")),
                HEALTH_CHECK_INTERVAL=int(st.secrets.get("HEALTH_CHECK_INTERVAL", "300")),
                SERVICE_NAME=st.secrets.get("SERVICE_NAME", "energy-grid-agent"),
                APP_VERSION=st.secrets.get("APP_VERSION", "1.0.0")
            )
        except Exception as e:
            logger.error(f"Error loading from Streamlit secrets: {e}")
            raise
    
    def _load_from_environment(self) -> SecretsConfig:
        """Load secrets from environment variables."""
        try:
            return SecretsConfig(
                # Neo4j Database
                NEO4J_URI=os.getenv("NEO4J_URI", ""),
                NEO4J_USERNAME=os.getenv("NEO4J_USERNAME", "neo4j"),
                NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD", ""),
                NEO4J_DATABASE=os.getenv("NEO4J_DATABASE", "neo4j"),
                
                # Claude AI
                CLAUDE_API_KEY=os.getenv("CLAUDE_API_KEY", ""),
                
                # Optional configurations
                ENCRYPTION_KEY=os.getenv("ENCRYPTION_KEY"),
                HASH_SALT=os.getenv("HASH_SALT"),
                SESSION_TIMEOUT=int(os.getenv("SESSION_TIMEOUT", "3600")),
                LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
                CACHE_TTL=int(os.getenv("CACHE_TTL", "300")),
                MAX_WORKERS=int(os.getenv("MAX_WORKERS", "4")),
                HEALTH_CHECK_INTERVAL=int(os.getenv("HEALTH_CHECK_INTERVAL", "300")),
                SERVICE_NAME=os.getenv("SERVICE_NAME", "energy-grid-agent"),
                APP_VERSION=os.getenv("APP_VERSION", "1.0.0")
            )
        except Exception as e:
            logger.error(f"Error loading from environment: {e}")
            raise
    
    def _load_defaults(self) -> SecretsConfig:
        """Load default secrets (for development/testing)."""
        return SecretsConfig(
            NEO4J_URI="",
            NEO4J_USERNAME="neo4j",
            NEO4J_PASSWORD="",
            NEO4J_DATABASE="neo4j",
            CLAUDE_API_KEY="",
            SESSION_TIMEOUT=3600,
            LOG_LEVEL="INFO",
            CACHE_TTL=300,
            MAX_WORKERS=4,
            HEALTH_CHECK_INTERVAL=300,
            SERVICE_NAME="energy-grid-agent",
            APP_VERSION="1.0.0"
        )
    
    def validate_secrets(self) -> bool:
        """Validate that all required secrets are present."""
        self._validation_errors = []
        
        # Required secrets validation
        if not self._secrets.NEO4J_URI:
            self._validation_errors.append("NEO4J_URI is required")
        
        if not self._secrets.NEO4J_PASSWORD:
            self._validation_errors.append("NEO4J_PASSWORD is required")
        
        if not self._secrets.CLAUDE_API_KEY:
            self._validation_errors.append("CLAUDE_API_KEY is required")
        
        # Optional but recommended
        if not self._secrets.ENCRYPTION_KEY:
            logger.warning("ENCRYPTION_KEY not set - using default")
        
        if not self._secrets.HASH_SALT:
            logger.warning("HASH_SALT not set - using default")
        
        return len(self._validation_errors) == 0
    
    def get_secrets(self) -> SecretsConfig:
        """Get the loaded secrets configuration."""
        return self._secrets
    
    def get_validation_errors(self) -> list:
        """Get list of validation errors."""
        return self._validation_errors.copy()
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get Neo4j database configuration."""
        return {
            'uri': self._secrets.NEO4J_URI,
            'username': self._secrets.NEO4J_USERNAME,
            'password': self._secrets.NEO4J_PASSWORD,
            'database': self._secrets.NEO4J_DATABASE
        }
    
    def get_claude_config(self) -> Dict[str, Any]:
        """Get Claude AI configuration."""
        return {
            'api_key': self._secrets.CLAUDE_API_KEY,
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': 4096,
            'temperature': 0.7
        }
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return {
            'session_timeout': self._secrets.SESSION_TIMEOUT,
            'log_level': self._secrets.LOG_LEVEL,
            'cache_ttl': self._secrets.CACHE_TTL,
            'max_workers': self._secrets.MAX_WORKERS,
            'health_check_interval': self._secrets.HEALTH_CHECK_INTERVAL,
            'service_name': self._secrets.SERVICE_NAME,
            'app_version': self._secrets.APP_VERSION
        }

def initialize_secrets() -> SecretsManager:
    """Initialize and validate secrets manager."""
    secrets_manager = SecretsManager()
    
    if not secrets_manager.validate_secrets():
        errors = secrets_manager.get_validation_errors()
        error_msg = "Secrets validation failed:\n" + "\n".join(f"• {error}" for error in errors)
        st.error(error_msg)
        st.stop()
    
    return secrets_manager

def display_secrets_status(secrets_manager: SecretsManager) -> None:
    """Display secrets status in the Streamlit interface."""
    secrets = secrets_manager.get_secrets()
    
    with st.expander("🔐 Secrets Status", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Database Configuration:**")
            st.write(f"• URI: {'✅ Set' if secrets.NEO4J_URI else '❌ Missing'}")
            st.write(f"• Username: {'✅ Set' if secrets.NEO4J_USERNAME else '❌ Missing'}")
            st.write(f"• Password: {'✅ Set' if secrets.NEO4J_PASSWORD else '❌ Missing'}")
            st.write(f"• Database: {'✅ Set' if secrets.NEO4J_DATABASE else '❌ Missing'}")
        
        with col2:
            st.write("**AI Configuration:**")
            st.write(f"• Claude API Key: {'✅ Set' if secrets.CLAUDE_API_KEY else '❌ Missing'}")
            st.write(f"• Encryption Key: {'✅ Set' if secrets.ENCRYPTION_KEY else '⚠️ Default'}")
            st.write(f"• Hash Salt: {'✅ Set' if secrets.HASH_SALT else '⚠️ Default'}")
        
        # Show source
        if hasattr(st, 'secrets') and st.secrets:
            st.info("📡 Secrets loaded from Streamlit Cloud")
        else:
            st.info("🏠 Secrets loaded from environment variables") 