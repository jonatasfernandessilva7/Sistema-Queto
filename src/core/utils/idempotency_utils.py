"""
Idempotency utilities for handling duplicate requests.
"""

import functools
import asyncio
from typing import Callable, Any, Dict

# Global cache for idempotent requests
_idempotency_cache: Dict[str, Any] = {}


def idempotency(func: Callable) -> Callable:
    """
    Decorator for making async functions idempotent.
    
    Prevents the same operation from being executed multiple times
    if the same idempotency_key is provided.
    
    Args:
        func: The async function to be made idempotent
        
    Returns:
        A wrapper function that implements idempotency
        
    Raises:
        ValueError: If idempotency_key is not provided
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        idempotency_key = kwargs.pop('idempotency_key', None)
        if not idempotency_key:
            raise ValueError("idempotency_key is required in kwargs")

        # Check if we've already processed this request
        if idempotency_key in _idempotency_cache:
            print(f"[IDEMPOTENCY] Request with key '{idempotency_key}' already processed, returning cached result")
            return _idempotency_cache[idempotency_key]

        # Execute the function
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        # Cache the result
        _idempotency_cache[idempotency_key] = result
        print(f"[IDEMPOTENCY] Request with key '{idempotency_key}' processed and cached")
        return result

    return wrapper


def clear_idempotency_cache(idempotency_key: str | None = None) -> None:
    """
    Clear idempotency cache entries.
    
    Args:
        idempotency_key: Specific key to clear, or None to clear all
    """
    global _idempotency_cache
    
    if idempotency_key:
        if idempotency_key in _idempotency_cache:
            del _idempotency_cache[idempotency_key]
            print(f"[IDEMPOTENCY] Cache cleared for key '{idempotency_key}'")
    else:
        _idempotency_cache.clear()
        print("[IDEMPOTENCY] All cache cleared")
