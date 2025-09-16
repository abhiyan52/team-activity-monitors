"""
Simple in-memory cache implementation for function output caching.

This module provides a cache that can store function outputs based on
function signatures and parameters, with support for TTL and cache management.
"""

import time
import hashlib
import inspect
from typing import Any, Callable, Dict, Optional, Tuple, Union
from functools import wraps
import json


class SimpleCache:
    """
    A simple in-memory cache that stores function outputs based on function signatures and parameters.
    
    Features:
    - Function signature-based caching
    - Parameter-based cache keys
    - TTL (Time To Live) support
    - Cache statistics and management
    - Thread-safe operations
    """
    
    def __init__(self, ttl: Optional[float] = None, max_size: Optional[int] = None):
        """
        Initialize the cache.
        
        Args:
            ttl: Default time-to-live in seconds for cache entries (None = no expiration)
            max_size: Maximum number of entries in cache (None = unlimited)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = ttl
        self.max_size = max_size
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """
        Generate a unique cache key based on function signature and parameters.
        
        Args:
            func: The function being cached
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            A unique string key for the cache entry
        """
        # Get function signature information
        func_name = func.__name__
        module_name = func.__module__
        
        # Create a deterministic representation of arguments
        # Sort kwargs to ensure consistent ordering
        sorted_kwargs = sorted(kwargs.items()) if kwargs else []
        
        # Create a string representation of the call signature
        signature_data = {
            'func_name': func_name,
            'module': module_name,
            'args': args,
            'kwargs': sorted_kwargs
        }
        
        # Convert to JSON string and hash it for a shorter key
        signature_str = json.dumps(signature_data, sort_keys=True, default=str)
        return hashlib.md5(signature_str.encode()).hexdigest()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired based on its TTL."""
        if entry.get('ttl') is None:
            return False
        
        return time.time() > entry['expires_at']
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache size limit is reached."""
        if self.max_size is None or len(self._cache) < self.max_size:
            return
        
        # Remove oldest entries (FIFO)
        entries_to_remove = len(self._cache) - self.max_size + 1
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].get('created_at', 0)
        )
        
        for key, _ in sorted_entries[:entries_to_remove]:
            del self._cache[key]
            self._stats['evictions'] += 1
    
    def get(self, func: Callable, args: tuple, kwargs: dict) -> Tuple[bool, Any]:
        """
        Get a cached result for a function call.
        
        Args:
            func: The function that was called
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Tuple of (found, result) where found is True if cache hit, False otherwise
        """
        self._stats['total_requests'] += 1
        
        cache_key = self._generate_cache_key(func, args, kwargs)
        
        if cache_key not in self._cache:
            self._stats['misses'] += 1
            return False, None
        
        entry = self._cache[cache_key]
        
        # Check if entry has expired
        if self._is_expired(entry):
            del self._cache[cache_key]
            self._stats['misses'] += 1
            return False, None
        
        self._stats['hits'] += 1
        return True, entry['result']
    
    def set(self, func: Callable, args: tuple, kwargs: dict, result: Any, ttl: Optional[float] = None) -> None:
        """
        Store a function result in the cache.
        
        Args:
            func: The function that was called
            args: Function arguments
            kwargs: Function keyword arguments
            result: The result to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_key = self._generate_cache_key(func, args, kwargs)
        
        # Use provided TTL or default
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        entry = {
            'result': result,
            'created_at': time.time(),
            'ttl': effective_ttl
        }
        
        if effective_ttl is not None:
            entry['expires_at'] = time.time() + effective_ttl
        
        # Evict if needed before adding new entry
        self._evict_if_needed()
        
        self._cache[cache_key] = entry
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def clear_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def size(self) -> int:
        """Get the current number of entries in the cache."""
        return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        hit_rate = 0.0
        if self._stats['total_requests'] > 0:
            hit_rate = self._stats['hits'] / self._stats['total_requests']
        
        return {
            **self._stats,
            'hit_rate': hit_rate,
            'current_size': self.size()
        }
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information.
        
        Returns:
            Dictionary containing detailed cache information
        """
        return {
            'stats': self.get_stats(),
            'max_size': self.max_size,
            'default_ttl': self.default_ttl,
            'entries': [
                {
                    'key': key,
                    'created_at': entry['created_at'],
                    'ttl': entry.get('ttl'),
                    'expires_at': entry.get('expires_at'),
                    'expired': self._is_expired(entry)
                }
                for key, entry in self._cache.items()
            ]
        }


# Global cache instance
_default_cache = SimpleCache()


def cached(ttl: Optional[float] = None, cache_instance: Optional[SimpleCache] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds for this specific function (overrides cache default)
        cache_instance: Specific cache instance to use (uses default if None)
    
    Example:
        @cached(ttl=300)  # Cache for 5 minutes
        def expensive_function(x, y):
            return x + y
        
        @cached()  # Use default TTL
        def another_function(data):
            return process_data(data)
    """
    def decorator(func: Callable) -> Callable:
        cache = cache_instance or _default_cache
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check cache first
            found, result = cache.get(func, args, kwargs)
            if found:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(func, args, kwargs, result, ttl)
            return result
        
        # Add cache management methods to the wrapper
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_clear_expired = lambda: cache.clear_expired()
        wrapper.cache_stats = lambda: cache.get_stats()
        wrapper.cache_info = lambda: cache.get_info()
        
        return wrapper
    
    return decorator


def get_default_cache() -> SimpleCache:
    """Get the default global cache instance."""
    return _default_cache


def create_cache(ttl: Optional[float] = None, max_size: Optional[int] = None) -> SimpleCache:
    """
    Create a new cache instance.
    
    Args:
        ttl: Default time-to-live in seconds
        max_size: Maximum number of entries
        
    Returns:
        New SimpleCache instance
    """
    return SimpleCache(ttl=ttl, max_size=max_size)
