"""
Production Configuration for Energy Grid Management Agent
"""
import os
import logging
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
import secrets
import hashlib

@dataclass
class SecurityConfig:
    """Security configuration settings."""
    # API Key encryption
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY', secrets.token_hex(32))
    HASH_SALT: str = os.getenv('HASH_SALT', secrets.token_hex(16))
    
    # Session security
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    
    # Rate limiting
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # 1 hour
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '1000'))
    
    # CORS settings
    ALLOWED_ORIGINS: list = None
    
    def __post_init__(self):
        if self.ALLOWED_ORIGINS is None:
            self.ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8501').split(',')

@dataclass
class DatabaseConfig:
    """Neo4j database configuration with connection pooling."""
    URI: str = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
    USERNAME: str = os.getenv('NEO4J_USERNAME', 'neo4j')
    PASSWORD: str = os.getenv('NEO4J_PASSWORD', '')
    DATABASE: str = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    # Connection pooling settings
    MAX_CONNECTION_POOL_SIZE: int = int(os.getenv('NEO4J_MAX_POOL_SIZE', '50'))
    CONNECTION_TIMEOUT: int = int(os.getenv('NEO4J_CONNECTION_TIMEOUT', '30'))
    ACQUISITION_TIMEOUT: int = int(os.getenv('NEO4J_ACQUISITION_TIMEOUT', '60'))
    MAX_CONNECTION_LIFETIME: int = int(os.getenv('NEO4J_MAX_LIFETIME', '3600'))
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv('NEO4J_MAX_RETRIES', '3'))
    RETRY_DELAY: float = float(os.getenv('NEO4J_RETRY_DELAY', '1.0'))
    
    # SSL/TLS settings
    USE_SSL: bool = os.getenv('NEO4J_USE_SSL', 'true').lower() == 'true'
    VERIFY_SSL: bool = os.getenv('NEO4J_VERIFY_SSL', 'true').lower() == 'true'

@dataclass
class ClaudeConfig:
    """Claude AI API configuration with rate limiting awareness."""
    API_KEY: str = os.getenv('CLAUDE_API_KEY', '')
    MODEL: str = os.getenv('CLAUDE_MODEL', 'claude-3-sonnet-20240229')
    MAX_TOKENS: int = int(os.getenv('CLAUDE_MAX_TOKENS', '4096'))
    TEMPERATURE: float = float(os.getenv('CLAUDE_TEMPERATURE', '0.7'))
    
    # Rate limiting settings
    REQUESTS_PER_MINUTE: int = int(os.getenv('CLAUDE_RPM', '50'))
    REQUESTS_PER_DAY: int = int(os.getenv('CLAUDE_RPD', '10000'))
    TOKENS_PER_MINUTE: int = int(os.getenv('CLAUDE_TPM', '50000'))
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv('CLAUDE_MAX_RETRIES', '3'))
    RETRY_DELAY: float = float(os.getenv('CLAUDE_RETRY_DELAY', '1.0'))
    BACKOFF_FACTOR: float = float(os.getenv('CLAUDE_BACKOFF_FACTOR', '2.0'))

@dataclass
class LoggingConfig:
    """Structured logging configuration."""
    LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    FORMAT: str = os.getenv('LOG_FORMAT', 'json')
    OUTPUT: str = os.getenv('LOG_OUTPUT', 'file')  # file, stdout, or both
    
    # File logging
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/energy_agent.log')
    MAX_FILE_SIZE: int = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
    BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Structured logging fields
    SERVICE_NAME: str = os.getenv('SERVICE_NAME', 'energy-grid-agent')
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'production')
    VERSION: str = os.getenv('APP_VERSION', '1.0.0')

@dataclass
class AppConfig:
    """Application configuration."""
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8501'))
    
    # Performance settings
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    
    # Health check settings
    HEALTH_CHECK_INTERVAL: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '300'))  # 5 minutes
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv('HEALTH_CHECK_TIMEOUT', '30'))
    
    # Data export settings
    MAX_EXPORT_SIZE: int = int(os.getenv('MAX_EXPORT_SIZE', '10000'))
    EXPORT_FORMATS: list = None
    
    def __post_init__(self):
        if self.EXPORT_FORMATS is None:
            self.EXPORT_FORMATS = os.getenv('EXPORT_FORMATS', 'csv,json').split(',')

class Config:
    """Main configuration class that combines all config sections."""
    
    def __init__(self):
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.claude = ClaudeConfig()
        self.logging = LoggingConfig()
        self.app = AppConfig()
        
        # Validate configuration on startup
        self._validate_config()
    
    def _validate_config(self):
        """Validate all configuration settings."""
        errors = []
        
        # Database validation
        if not self.database.URI:
            errors.append("NEO4J_URI is required")
        if not self.database.PASSWORD:
            errors.append("NEO4J_PASSWORD is required")
        
        # Claude API validation
        if not self.claude.API_KEY:
            errors.append("CLAUDE_API_KEY is required")
        
        # Security validation
        if len(self.security.ENCRYPTION_KEY) < 32:
            errors.append("ENCRYPTION_KEY must be at least 32 characters")
        
        # Logging validation
        if self.logging.OUTPUT == 'file':
            log_dir = Path(self.logging.LOG_FILE).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory: {e}")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def get_database_config(self) -> dict:
        """Get Neo4j database configuration as a dictionary."""
        return {
            'uri': self.database.URI,
            'username': self.database.USERNAME,
            'password': self.database.PASSWORD,
            'database': self.database.DATABASE,
            'max_connection_pool_size': self.database.MAX_CONNECTION_POOL_SIZE,
            'connection_timeout': self.database.CONNECTION_TIMEOUT,
            'acquisition_timeout': self.database.ACQUISITION_TIMEOUT,
            'max_connection_lifetime': self.database.MAX_CONNECTION_LIFETIME,
            'use_ssl': self.database.USE_SSL,
            'verify_ssl': self.database.VERIFY_SSL
        }
    
    def get_claude_config(self) -> dict:
        """Get Claude API configuration as a dictionary."""
        return {
            'api_key': self.claude.API_KEY,
            'model': self.claude.MODEL,
            'max_tokens': self.claude.MAX_TOKENS,
            'temperature': self.claude.TEMPERATURE,
            'requests_per_minute': self.claude.REQUESTS_PER_MINUTE,
            'requests_per_day': self.claude.REQUESTS_PER_DAY,
            'tokens_per_minute': self.claude.TOKENS_PER_MINUTE,
            'max_retries': self.claude.MAX_RETRIES,
            'retry_delay': self.claude.RETRY_DELAY,
            'backoff_factor': self.claude.BACKOFF_FACTOR
        }
    
    def get_logging_config(self) -> dict:
        """Get logging configuration as a dictionary."""
        return {
            'level': self.logging.LEVEL,
            'format': self.logging.FORMAT,
            'output': self.logging.OUTPUT,
            'log_file': self.logging.LOG_FILE,
            'max_file_size': self.logging.MAX_FILE_SIZE,
            'backup_count': self.logging.BACKUP_COUNT,
            'service_name': self.logging.SERVICE_NAME,
            'environment': self.logging.ENVIRONMENT,
            'version': self.logging.VERSION
        }
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.app.DEBUG and self.logging.ENVIRONMENT == 'production'
    
    def get_health_check_config(self) -> dict:
        """Get health check configuration."""
        return {
            'interval': self.app.HEALTH_CHECK_INTERVAL,
            'timeout': self.app.HEALTH_CHECK_TIMEOUT,
            'database': self.database.URI is not None,
            'claude': self.claude.API_KEY is not None
        }

# Global configuration instance
config = Config() 