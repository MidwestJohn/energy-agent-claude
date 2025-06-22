"""
Cloud-Optimized Caching System for Energy Grid Management Agent
Optimized for Streamlit Cloud deployment with efficient memory management.
"""
import streamlit as st
import logging
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
import pandas as pd

logger = logging.getLogger(__name__)

class CloudCacheManager:
    """
    Advanced caching manager optimized for Streamlit Cloud.
    Provides intelligent cache management with memory optimization.
    """
    
    def __init__(self, default_ttl: int = 300, max_cache_size: int = 100):
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        
        # Initialize cache in session state if not exists
        if 'cloud_cache' not in st.session_state:
            st.session_state.cloud_cache = {}
            st.session_state.cache_metadata = {}
    
    def _generate_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate a unique cache key for the function call."""
        # Create a hash of the function name and arguments
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else []
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in st.session_state.cache_metadata:
            return False
        
        metadata = st.session_state.cache_metadata[cache_key]
        current_time = time.time()
        
        # Check TTL
        if current_time - metadata['created_at'] > metadata['ttl']:
            return False
        
        return True
    
    def _cleanup_expired_cache(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        for key, metadata in st.session_state.cache_metadata.items():
            if current_time - metadata['created_at'] > metadata['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_from_cache(key)
            self.cache_stats['evictions'] += 1
    
    def _remove_from_cache(self, cache_key: str):
        """Remove an item from cache."""
        if cache_key in st.session_state.cloud_cache:
            del st.session_state.cloud_cache[cache_key]
        if cache_key in st.session_state.cache_metadata:
            del st.session_state.cache_metadata[cache_key]
    
    def _enforce_cache_size_limit(self):
        """Enforce maximum cache size by removing oldest entries."""
        if len(st.session_state.cloud_cache) <= self.max_cache_size:
            return
        
        # Sort by creation time and remove oldest
        sorted_items = sorted(
            st.session_state.cache_metadata.items(),
            key=lambda x: x[1]['created_at']
        )
        
        items_to_remove = len(st.session_state.cloud_cache) - self.max_cache_size
        for i in range(items_to_remove):
            key = sorted_items[i][0]
            self._remove_from_cache(key)
            self.cache_stats['evictions'] += 1
    
    def get(self, cache_key: str) -> Optional[Any]:
        """Get data from cache."""
        self.cache_stats['total_requests'] += 1
        
        # Cleanup expired cache first
        self._cleanup_expired_cache()
        
        if cache_key in st.session_state.cloud_cache and self._is_cache_valid(cache_key):
            self.cache_stats['hits'] += 1
            return st.session_state.cloud_cache[cache_key]
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, cache_key: str, data: Any, ttl: int = None) -> None:
        """Store data in cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Store the data
        st.session_state.cloud_cache[cache_key] = data
        
        # Store metadata
        st.session_state.cache_metadata[cache_key] = {
            'created_at': time.time(),
            'ttl': ttl,
            'size': self._estimate_data_size(data)
        }
        
        # Enforce size limits
        self._enforce_cache_size_limit()
    
    def _estimate_data_size(self, data: Any) -> int:
        """Estimate the size of cached data."""
        try:
            if isinstance(data, pd.DataFrame):
                return data.memory_usage(deep=True).sum()
            elif isinstance(data, (list, dict)):
                return len(str(data))
            else:
                return len(str(data))
        except:
            return 0
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        st.session_state.cloud_cache.clear()
        st.session_state.cache_metadata.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = 0
        if self.cache_stats['total_requests'] > 0:
            hit_rate = self.cache_stats['hits'] / self.cache_stats['total_requests']
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'total_requests': self.cache_stats['total_requests'],
            'hit_rate': hit_rate,
            'current_size': len(st.session_state.cloud_cache),
            'max_size': self.max_cache_size
        }

def cloud_cache(ttl: int = None, key_prefix: str = ""):
    """
    Decorator for cloud-optimized caching.
    
    Args:
        ttl: Time to live in seconds (default: 300)
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager from session state
            if 'cache_manager' not in st.session_state:
                st.session_state.cache_manager = CloudCacheManager()
            
            cache_manager = st.session_state.cache_manager
            
            # Generate cache key
            func_name = f"{key_prefix}{func.__name__}" if key_prefix else func.__name__
            cache_key = cache_manager._generate_cache_key(func_name, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def streamlit_cache_data(ttl: int = 300, max_entries: int = 100):
    """
    Streamlit's built-in cache_data with cloud optimizations.
    """
    return st.cache_data(ttl=ttl, max_entries=max_entries)

def streamlit_cache_resource(ttl: int = 300, max_entries: int = 100):
    """
    Streamlit's built-in cache_resource with cloud optimizations.
    """
    return st.cache_resource(ttl=ttl, max_entries=max_entries)

def display_cache_stats():
    """Display cache statistics in Streamlit interface."""
    if 'cache_manager' not in st.session_state:
        return
    
    cache_manager = st.session_state.cache_manager
    stats = cache_manager.get_cache_stats()
    
    with st.sidebar.expander("📊 Cache Statistics", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Hit Rate", f"{stats['hit_rate']:.1%}")
            st.metric("Cache Size", f"{stats['current_size']}/{stats['max_size']}")
        
        with col2:
            st.metric("Total Requests", stats['total_requests'])
            st.metric("Evictions", stats['evictions'])
        
        # Cache management buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Cache", help="Clear all cached data"):
                cache_manager.clear_cache()
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh Stats", help="Refresh cache statistics"):
                st.rerun()

# Pre-configured cache decorators for common use cases
@streamlit_cache_data(ttl=600)  # 10 minutes
def cache_database_query(query: str, params: dict = None):
    """Cache database query results."""
    pass

@streamlit_cache_data(ttl=300)  # 5 minutes
def cache_chart_data(data: pd.DataFrame):
    """Cache chart data."""
    pass

@streamlit_cache_data(ttl=1800)  # 30 minutes
def cache_analysis_results(analysis_type: str, data: dict):
    """Cache analysis results."""
    pass

@streamlit_cache_resource(ttl=3600)  # 1 hour
def cache_database_connection(uri: str, username: str, password: str):
    """Cache database connections."""
    pass 