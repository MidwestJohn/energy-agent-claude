"""
Structured Logging Configuration for Energy Grid Management Agent
"""
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import traceback
from config import config

class StructuredFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, service_name: str, environment: str, version: str):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.version = version
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': self.service_name,
            'environment': self.environment,
            'version': self.version,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add performance metrics if available
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

class PerformanceLogger:
    """Logger for performance metrics and monitoring."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_function_performance(self, function_name: str, execution_time: float, 
                                success: bool, error: Optional[str] = None):
        """Log function performance metrics."""
        extra_fields = {
            'metric_type': 'function_performance',
            'function_name': function_name,
            'execution_time': execution_time,
            'success': success
        }
        
        if error:
            extra_fields['error'] = error
        
        self.logger.info(f"Function performance: {function_name}", 
                        extra={'extra_fields': extra_fields})
    
    def log_database_query(self, query: str, execution_time: float, 
                          success: bool, rows_returned: Optional[int] = None):
        """Log database query performance."""
        extra_fields = {
            'metric_type': 'database_query',
            'query_type': self._get_query_type(query),
            'execution_time': execution_time,
            'success': success
        }
        
        if rows_returned is not None:
            extra_fields['rows_returned'] = rows_returned
        
        self.logger.info(f"Database query executed", 
                        extra={'extra_fields': extra_fields})
    
    def log_api_call(self, service: str, endpoint: str, execution_time: float,
                     success: bool, status_code: Optional[int] = None):
        """Log API call performance."""
        extra_fields = {
            'metric_type': 'api_call',
            'service': service,
            'endpoint': endpoint,
            'execution_time': execution_time,
            'success': success
        }
        
        if status_code:
            extra_fields['status_code'] = status_code
        
        self.logger.info(f"API call to {service}: {endpoint}", 
                        extra={'extra_fields': extra_fields})
    
    def _get_query_type(self, query: str) -> str:
        """Determine the type of database query."""
        query_upper = query.strip().upper()
        if query_upper.startswith('MATCH'):
            return 'read'
        elif query_upper.startswith('CREATE'):
            return 'create'
        elif query_upper.startswith('MERGE'):
            return 'merge'
        elif query_upper.startswith('DELETE'):
            return 'delete'
        elif query_upper.startswith('SET'):
            return 'update'
        else:
            return 'other'

class SecurityLogger:
    """Logger for security-related events."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_authentication_attempt(self, user_id: str, success: bool, 
                                 ip_address: Optional[str] = None):
        """Log authentication attempts."""
        extra_fields = {
            'event_type': 'authentication_attempt',
            'user_id': user_id,
            'success': success
        }
        
        if ip_address:
            extra_fields['ip_address'] = ip_address
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Authentication attempt for user {user_id}", 
                       extra={'extra_fields': extra_fields})
    
    def log_api_key_usage(self, api_key_hash: str, service: str, success: bool):
        """Log API key usage (without exposing the actual key)."""
        extra_fields = {
            'event_type': 'api_key_usage',
            'api_key_hash': api_key_hash,
            'service': service,
            'success': success
        }
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"API key usage for {service}", 
                       extra={'extra_fields': extra_fields})
    
    def log_rate_limit_exceeded(self, user_id: str, service: str, limit: int):
        """Log rate limit violations."""
        extra_fields = {
            'event_type': 'rate_limit_exceeded',
            'user_id': user_id,
            'service': service,
            'limit': limit
        }
        
        self.logger.warning(f"Rate limit exceeded for {service}", 
                           extra={'extra_fields': extra_fields})

def setup_logging() -> logging.Logger:
    """Setup structured logging configuration."""
    log_config = config.get_logging_config()
    
    # Create logger
    logger = logging.getLogger('energy_agent')
    logger.setLevel(getattr(logging, log_config['level'].upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = StructuredFormatter(
        service_name=log_config['service_name'],
        environment=log_config['environment'],
        version=log_config['version']
    )
    
    # Setup handlers based on output configuration
    if log_config['output'] in ['file', 'both']:
        # File handler with rotation
        log_file = Path(log_config['log_file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=log_config['max_file_size'],
            backupCount=log_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    if log_config['output'] in ['stdout', 'both']:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with the specified name."""
    if name:
        return logging.getLogger(f'energy_agent.{name}')
    return logging.getLogger('energy_agent')

def get_performance_logger(name: str = None) -> PerformanceLogger:
    """Get a performance logger instance."""
    return PerformanceLogger(get_logger(name))

def get_security_logger(name: str = None) -> SecurityLogger:
    """Get a security logger instance."""
    return SecurityLogger(get_logger(name))

class LoggingContext:
    """Context manager for adding request context to logs."""
    
    def __init__(self, request_id: str = None, user_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.old_request_id = None
        self.old_user_id = None
    
    def __enter__(self):
        # Store current context
        logger = get_logger()
        self.old_request_id = getattr(logger, 'request_id', None)
        self.old_user_id = getattr(logger, 'user_id', None)
        
        # Set new context
        if self.request_id:
            logger.request_id = self.request_id
        if self.user_id:
            logger.user_id = self.user_id
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        logger = get_logger()
        if self.old_request_id is not None:
            logger.request_id = self.old_request_id
        else:
            delattr(logger, 'request_id')
        
        if self.old_user_id is not None:
            logger.user_id = self.old_user_id
        else:
            delattr(logger, 'user_id')

def log_function_call(func):
    """Decorator to automatically log function calls with performance metrics."""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        perf_logger = get_performance_logger()
        
        start_time = datetime.now()
        success = True
        error = None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            error = str(e)
            logger.error(f"Function {func.__name__} failed: {error}", exc_info=True)
            raise
        finally:
            execution_time = (datetime.now() - start_time).total_seconds()
            perf_logger.log_function_performance(
                function_name=func.__name__,
                execution_time=execution_time,
                success=success,
                error=error
            )
    
    return wrapper

# Initialize logging on module import
main_logger = setup_logging()
performance_logger = get_performance_logger()
security_logger = get_security_logger()

# Log application startup
main_logger.info("Energy Grid Management Agent starting up", extra={
    'extra_fields': {
        'event_type': 'application_startup',
        'environment': config.logging.ENVIRONMENT,
        'version': config.logging.VERSION
    }
}) 