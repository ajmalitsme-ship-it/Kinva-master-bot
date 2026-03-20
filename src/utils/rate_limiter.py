"""
Rate Limiter - Rate limiting utilities for API protection
Author: @kinva_master
"""

import time
import threading
import logging
from collections import defaultdict
from typing import Dict, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from functools import wraps

try:
    import redis
except ImportError:
    redis = None

from ..config import Config

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter with support for in-memory and Redis backends
    """
    
    def __init__(self, backend: str = 'memory', redis_url: str = None):
        """
        Initialize rate limiter
        
        Args:
            backend: 'memory' or 'redis'
            redis_url: Redis URL for Redis backend
        """
        self.backend = backend
        self.redis_client = None
        
        if backend == 'redis' and redis:
            try:
                self.redis_client = redis.from_url(redis_url or Config.REDIS_URL)
                self.redis_client.ping()
                logger.info("Redis rate limiter initialized")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to memory: {e}")
                self.backend = 'memory'
        
        if self.backend == 'memory':
            self.requests = defaultdict(list)
            self._lock = threading.Lock()
            logger.info("In-memory rate limiter initialized")
    
    def _get_memory_count(self, key: str, window: int) -> int:
        """Get request count from memory backend"""
        now = time.time()
        with self._lock:
            # Clean old requests
            self.requests[key] = [t for t in self.requests[key] if now - t < window]
            return len(self.requests[key])
    
    def _add_memory_request(self, key: str) -> None:
        """Add request to memory backend"""
        now = time.time()
        with self._lock:
            self.requests[key].append(now)
    
    def _get_redis_count(self, key: str, window: int) -> int:
        """Get request count from Redis backend"""
        try:
            count = self.redis_client.get(key)
            if count:
                return int(count)
            return 0
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return 0
    
    def _add_redis_request(self, key: str, window: int) -> None:
        """Add request to Redis backend"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            pipe.execute()
        except Exception as e:
            logger.error(f"Redis incr error: {e}")
    
    def check(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """
        Check if request is allowed
        
        Args:
            key: Rate limit key
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        if self.backend == 'redis':
            count = self._get_redis_count(key, window)
            if count < limit:
                self._add_redis_request(key, window)
                return True, limit - count - 1
            return False, 0
        else:
            count = self._get_memory_count(key, window)
            if count < limit:
                self._add_memory_request(key)
                return True, limit - count - 1
            return False, 0
    
    def get_remaining(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests"""
        if self.backend == 'redis':
            count = self._get_redis_count(key, window)
            return max(0, limit - count)
        else:
            count = self._get_memory_count(key, window)
            return max(0, limit - count)
    
    def get_reset_time(self, key: str, window: int) -> float:
        """Get time when rate limit resets"""
        if self.backend == 'redis':
            ttl = self.redis_client.ttl(key)
            if ttl > 0:
                return time.time() + ttl
        return time.time() + window
    
    def clear(self, key: str) -> None:
        """Clear rate limit for key"""
        if self.backend == 'redis':
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        else:
            with self._lock:
                if key in self.requests:
                    del self.requests[key]


# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        backend = 'redis' if Config.REDIS_URL else 'memory'
        _rate_limiter = RateLimiter(backend=backend, redis_url=Config.REDIS_URL)
    return _rate_limiter


def rate_limit_ip(limit: int = 60, window: int = 60):
    """
    Decorator to rate limit by IP address
    
    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            # Get client IP
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            key = f"rate_limit:ip:{ip}"
            
            limiter = get_rate_limiter()
            allowed, remaining = limiter.check(key, limit, window)
            
            if not allowed:
                reset_time = limiter.get_reset_time(key, window)
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': limit,
                    'window': window,
                    'reset_in': int(reset_time - time.time())
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit_user(limit: int = 60, window: int = 60):
    """
    Decorator to rate limit by user ID
    
    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            from flask_jwt_extended import get_jwt_identity
            
            try:
                user_id = get_jwt_identity()
            except:
                user_id = None
            
            if user_id:
                key = f"rate_limit:user:{user_id}"
            else:
                # Fall back to IP for unauthenticated requests
                ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                key = f"rate_limit:ip:{ip}"
            
            limiter = get_rate_limiter()
            allowed, remaining = limiter.check(key, limit, window)
            
            if not allowed:
                reset_time = limiter.get_reset_time(key, window)
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': limit,
                    'window': window,
                    'reset_in': int(reset_time - time.time())
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit_endpoint(limit: int = 60, window: int = 60):
    """
    Decorator to rate limit by endpoint + IP/user
    
    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            from flask_jwt_extended import get_jwt_identity
            
            # Get endpoint path
            endpoint = request.endpoint or request.path
            
            try:
                user_id = get_jwt_identity()
            except:
                user_id = None
            
            if user_id:
                key = f"rate_limit:endpoint:{endpoint}:user:{user_id}"
            else:
                ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                key = f"rate_limit:endpoint:{endpoint}:ip:{ip}"
            
            limiter = get_rate_limiter()
            allowed, remaining = limiter.check(key, limit, window)
            
            if not allowed:
                reset_time = limiter.get_reset_time(key, window)
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': limit,
                    'window': window,
                    'reset_in': int(reset_time - time.time())
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimiterMiddleware:
    """
    ASGI middleware for rate limiting
    """
    
    def __init__(self, app, limit: int = 60, window: int = 60):
        self.app = app
        self.limit = limit
        self.window = window
        self.limiter = get_rate_limiter()
    
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        
        # Get client IP
        headers = dict(scope.get('headers', []))
        ip = headers.get(b'x-forwarded-for', headers.get(b'x-real-ip', scope.get('client', [None])[0]))
        if isinstance(ip, bytes):
            ip = ip.decode()
        
        key = f"rate_limit:ip:{ip}"
        
        allowed, remaining = self.limiter.check(key, self.limit, self.window)
        
        if not allowed:
            # Send 429 response
            response_headers = [
                (b'content-type', b'application/json'),
                (b'retry-after', str(int(self.window)).encode())
            ]
            await send({
                'type': 'http.response.start',
                'status': 429,
                'headers': response_headers
            })
            await send({
                'type': 'http.response.body',
                'body': b'{"error": "Rate limit exceeded"}'
            })
            return
        
        # Add rate limit headers
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.append((b'x-ratelimit-limit', str(self.limit).encode()))
                headers.append((b'x-ratelimit-remaining', str(remaining).encode()))
                headers.append((b'x-ratelimit-reset', str(int(self.limiter.get_reset_time(key, self.window))).encode()))
                message['headers'] = headers
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class RateLimiterManager:
    """
    Advanced rate limiter with multiple strategies
    """
    
    def __init__(self):
        self.limiters = {}
        self._lock = threading.Lock()
    
    def get_limiter(self, name: str, limit: int, window: int) -> RateLimiter:
        """Get or create rate limiter"""
        key = f"{name}:{limit}:{window}"
        with self._lock:
            if key not in self.limiters:
                self.limiters[key] = RateLimiter()
            return self.limiters[key]
    
    def check(self, name: str, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check rate limit for named limiter"""
        limiter = self.get_limiter(name, limit, window)
        return limiter.check(key, limit, window)
    
    def check_multi(self, checks: List[Tuple[str, str, int, int]]) -> Tuple[bool, Dict]:
        """
        Check multiple rate limits
        
        Args:
            checks: List of (name, key, limit, window) tuples
        
        Returns:
            Tuple of (is_allowed, results)
        """
        results = {}
        for name, key, limit, window in checks:
            allowed, remaining = self.check(name, key, limit, window)
            results[name] = {
                'allowed': allowed,
                'remaining': remaining,
                'limit': limit,
                'window': window
            }
            if not allowed:
                return False, results
        return True, results
    
    def clear(self, name: str, key: str = None) -> None:
        """Clear rate limits"""
        if key:
            limiter = self.limiters.get(name)
            if limiter:
                limiter.clear(key)
        else:
            self.limiters.pop(name, None)


# Token bucket rate limiter
class TokenBucket:
    """
    Token bucket algorithm rate limiter
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            True if tokens available, False otherwise
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_tokens(self) -> float:
        """Get current token count"""
        with self._lock:
            self._refill()
            return self.tokens
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait for tokens"""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0
            return (tokens - self.tokens) / self.refill_rate


# Sliding window rate limiter
class SlidingWindowLimiter:
    """
    Sliding window algorithm rate limiter
    """
    
    def __init__(self, limit: int, window: int):
        """
        Initialize sliding window limiter
        
        Args:
            limit: Maximum requests allowed
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.requests = []
        self._lock = threading.Lock()
    
    def check(self) -> Tuple[bool, int]:
        """
        Check if request is allowed
        
        Returns:
            Tuple of (is_allowed, remaining)
        """
        now = time.time()
        with self._lock:
            # Remove old requests
            self.requests = [t for t in self.requests if now - t < self.window]
            
            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True, self.limit - len(self.requests)
            return False, 0
    
    def get_remaining(self) -> int:
        """Get remaining requests"""
        now = time.time()
        with self._lock:
            self.requests = [t for t in self.requests if now - t < self.window]
            return max(0, self.limit - len(self.requests))
    
    def get_reset_time(self) -> float:
        """Get time when oldest request expires"""
        with self._lock:
            if self.requests:
                return self.requests[0] + self.window
            return time.time() + self.window


# Create global manager
rate_limiter_manager = RateLimiterManager()
