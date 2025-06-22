"""
Rate Limiting and Connection Pooling for Energy Grid Management Agent
"""
import time
import threading
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
from dataclasses import dataclass
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
import logging
from config import config
from logging_config import get_logger, get_performance_logger, get_security_logger

logger = get_logger('rate_limiter')
perf_logger = get_performance_logger('rate_limiter')
security_logger = get_security_logger('rate_limiter')

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int
    requests_per_day: int
    tokens_per_minute: int
    window_size: int = 60  # seconds

class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float, refill_time: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_time = refill_time
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from the bucket."""
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_available_tokens(self) -> int:
        """Get number of available tokens."""
        with self.lock:
            self._refill()
            return int(self.tokens)

class RateLimiter:
    """Rate limiter for API calls with multiple limits."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_bucket = TokenBucket(
            capacity=config.requests_per_minute,
            refill_rate=config.requests_per_minute / 60.0
        )
        self.token_bucket = TokenBucket(
            capacity=config.tokens_per_minute,
            refill_rate=config.tokens_per_minute / 60.0
        )
        
        # Daily request tracking
        self.daily_requests = deque()
        self.daily_lock = threading.Lock()
        
        # User-specific rate limiting
        self.user_limits: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=config.requests_per_minute // 10,  # 10% of global limit per user
                refill_rate=(config.requests_per_minute // 10) / 60.0
            )
        )
        self.user_lock = threading.Lock()
    
    def check_rate_limit(self, user_id: str = None, tokens_required: int = 1) -> bool:
        """Check if request is within rate limits."""
        # Check global request limit
        if not self.request_bucket.consume(1):
            logger.warning("Global request rate limit exceeded")
            return False
        
        # Check global token limit
        if not self.token_bucket.consume(tokens_required):
            logger.warning("Global token rate limit exceeded")
            return False
        
        # Check daily limit
        if not self._check_daily_limit():
            logger.warning("Daily request limit exceeded")
            return False
        
        # Check user-specific limit
        if user_id and not self._check_user_limit(user_id):
            security_logger.log_rate_limit_exceeded(user_id, "claude_api", self.config.requests_per_minute)
            logger.warning(f"User {user_id} rate limit exceeded")
            return False
        
        return True
    
    def _check_daily_limit(self) -> bool:
        """Check daily request limit."""
        with self.daily_lock:
            now = datetime.now()
            cutoff_time = now - timedelta(days=1)
            
            # Remove old requests
            while self.daily_requests and self.daily_requests[0] < cutoff_time:
                self.daily_requests.popleft()
            
            # Check if adding this request would exceed daily limit
            if len(self.daily_requests) >= self.config.requests_per_day:
                return False
            
            # Add current request
            self.daily_requests.append(now)
            return True
    
    def _check_user_limit(self, user_id: str) -> bool:
        """Check user-specific rate limit."""
        with self.user_lock:
            return self.user_limits[user_id].consume(1)
    
    def get_limits_status(self, user_id: str = None) -> Dict[str, Any]:
        """Get current rate limit status."""
        status = {
            'global_requests_available': self.request_bucket.get_available_tokens(),
            'global_tokens_available': self.token_bucket.get_available_tokens(),
            'daily_requests_used': len(self.daily_requests),
            'daily_requests_limit': self.config.requests_per_day
        }
        
        if user_id:
            with self.user_lock:
                status['user_requests_available'] = self.user_limits[user_id].get_available_tokens()
        
        return status

class ConnectionPool:
    """Connection pool for Neo4j database with health monitoring."""
    
    def __init__(self, uri: str, username: str, password: str, **kwargs):
        self.uri = uri
        self.username = username
        self.password = password
        self.pool_config = kwargs
        self.driver = None
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = 0
        self.health_status = {'status': 'unknown', 'last_check': None}
        self.lock = threading.Lock()
        
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                **self.pool_config
            )
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            self.health_status = {
                'status': 'healthy',
                'last_check': datetime.now(),
                'message': 'Connection pool initialized successfully'
            }
            
            logger.info("Neo4j connection pool initialized successfully")
            
        except Exception as e:
            self.health_status = {
                'status': 'unhealthy',
                'last_check': datetime.now(),
                'message': f'Failed to initialize connection pool: {str(e)}'
            }
            logger.error(f"Failed to initialize Neo4j connection pool: {e}")
            raise
    
    def get_session(self):
        """Get a database session from the pool."""
        if not self.driver:
            raise ConnectionError("Database driver not initialized")
        
        return self.driver.session()
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query with connection pooling and retry logic."""
        start_time = time.time()
        success = False
        rows_returned = 0
        
        try:
            with self.get_session() as session:
                result = session.run(query, parameters or {})
                data = [dict(record) for record in result]
                rows_returned = len(data)
                success = True
                return data
                
        except (ServiceUnavailable, AuthError, ClientError) as e:
            logger.error(f"Database query failed: {e}")
            perf_logger.log_database_query(query, time.time() - start_time, False)
            raise
        finally:
            execution_time = time.time() - start_time
            perf_logger.log_database_query(query, execution_time, success, rows_returned)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the connection pool."""
        now = time.time()
        
        # Only check if enough time has passed
        if now - self.last_health_check < self.health_check_interval:
            return self.health_status
        
        with self.lock:
            try:
                start_time = time.time()
                with self.get_session() as session:
                    result = session.run("RETURN 1 as health_check")
                    result.single()
                
                response_time = time.time() - start_time
                
                self.health_status = {
                    'status': 'healthy',
                    'last_check': datetime.now(),
                    'response_time': response_time,
                    'message': f'Health check passed in {response_time:.3f}s'
                }
                
                self.last_health_check = now
                
            except Exception as e:
                self.health_status = {
                    'status': 'unhealthy',
                    'last_check': datetime.now(),
                    'response_time': None,
                    'message': f'Health check failed: {str(e)}'
                }
                self.last_health_check = now
        
        return self.health_status
    
    def close(self):
        """Close the connection pool."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection pool closed")

class RetryHandler:
    """Handler for retrying failed operations with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded for {func.__name__}")
                    raise last_exception
                
                delay = self.base_delay * (self.backoff_factor ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay:.2f}s: {e}")
                time.sleep(delay)
        
        raise last_exception

# Global instances
claude_rate_limiter = RateLimiter(RateLimitConfig(
    requests_per_minute=config.claude.REQUESTS_PER_MINUTE,
    requests_per_day=config.claude.REQUESTS_PER_DAY,
    tokens_per_minute=config.claude.TOKENS_PER_MINUTE
))

retry_handler = RetryHandler(
    max_retries=config.claude.MAX_RETRIES,
    base_delay=config.claude.RETRY_DELAY,
    backoff_factor=config.claude.BACKOFF_FACTOR
)

def get_connection_pool() -> ConnectionPool:
    """Get or create a Neo4j connection pool."""
    db_config = config.get_database_config()
    
    return ConnectionPool(
        uri=db_config['uri'],
        username=db_config['username'],
        password=db_config['password'],
        max_connection_pool_size=db_config['max_connection_pool_size'],
        connection_timeout=db_config['connection_timeout'],
        acquisition_timeout=db_config['acquisition_timeout'],
        max_connection_lifetime=db_config['max_connection_lifetime']
    )

def rate_limited_api_call(func):
    """Decorator for rate-limited API calls."""
    def wrapper(*args, **kwargs):
        # Estimate tokens (rough approximation)
        tokens_required = 1  # Default for simple calls
        
        # Check rate limits
        if not claude_rate_limiter.check_rate_limit(tokens_required=tokens_required):
            raise Exception("Rate limit exceeded")
        
        # Execute with retry logic
        return retry_handler.execute_with_retry(func, *args, **kwargs)
    
    return wrapper 