"""
Decorators - Function decorators for common patterns
Author: @kinva_master
"""

import functools
import time
import logging
import asyncio
from typing import Callable, Any, Optional
from flask import jsonify, request, g
from functools import wraps

from ..database import db
from ..config import Config

logger = logging.getLogger(__name__)

# ============================================
# RETRY DECORATORS
# ============================================

def retry(max_attempts: int = 3, delay: int = 1, backoff: int = 2, 
          exceptions: tuple = (Exception,)):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}")
                    time.sleep(_delay)
                    _delay *= backoff
            return None
        return wrapper
    return decorator

def async_retry(max_attempts: int = 3, delay: int = 1, backoff: int = 2,
                exceptions: tuple = (Exception,)):
    """
    Async retry decorator with exponential backoff
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            _delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Async retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}")
                    await asyncio.sleep(_delay)
                    _delay *= backoff
            return None
        return wrapper
    return decorator

# ============================================
# TIMING DECORATORS
# ============================================

def timer(func: Callable) -> Callable:
    """Time function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

def async_timer(func: Callable) -> Callable:
    """Time async function execution"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

# ============================================
# LOGGING DECORATORS
# ============================================

def log_execution(func: Callable) -> Callable:
    """Log function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

def log_async_execution(func: Callable) -> Callable:
    """Log async function execution"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

# ============================================
# AUTHENTICATION DECORATORS
# ============================================

def require_auth(func: Callable) -> Callable:
    """Require authentication decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check for JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            g.user_id = user_id
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return wrapper

def require_premium(func: Callable) -> Callable:
    """Require premium subscription decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            if not user or not user.get('is_premium'):
                return jsonify({'error': 'Premium subscription required'}), 403
            
            # Check if premium is expired
            if user.get('premium_until'):
                from datetime import datetime
                premium_until = datetime.fromisoformat(user['premium_until'])
                if premium_until < datetime.now():
                    return jsonify({'error': 'Premium subscription expired'}), 403
            
            g.user_id = user_id
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return wrapper

def require_admin(func: Callable) -> Callable:
    """Require admin access decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            if not user or user.get('telegram_id') not in Config.ADMIN_IDS:
                return jsonify({'error': 'Admin access required'}), 403
            
            g.user_id = user_id
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return wrapper

# ============================================
# RATE LIMITING DECORATORS
# ============================================

def rate_limit(limit: int = 60, period: int = 60, key_func: Callable = None):
    """
    Rate limit decorator
    
    Args:
        limit: Maximum number of requests
        period: Time period in seconds
        key_func: Function to generate rate limit key
    """
    from collections import defaultdict
    import time
    
    requests = defaultdict(list)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = request.remote_addr
            
            now = time.time()
            
            # Clean old requests
            requests[key] = [t for t in requests[key] if now - t < period]
            
            # Check limit
            if len(requests[key]) >= limit:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request
            requests[key].append(now)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit_ip(limit: int = 60, period: int = 60):
    """Rate limit by IP address"""
    return rate_limit(limit=limit, period=period, key_func=lambda *args, **kwargs: request.remote_addr)

def rate_limit_user(limit: int = 60, period: int = 60):
    """Rate limit by user ID"""
    def key_func(*args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        try:
            return get_jwt_identity()
        except:
            return request.remote_addr
    return rate_limit(limit=limit, period=period, key_func=key_func)

# ============================================
# CACHE DECORATORS
# ============================================

def cache_result(ttl: int = 300, key_func: Callable = None):
    """
    Cache function results
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key
    """
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{args}:{kwargs}"
            
            now = time.time()
            
            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    return result
            
            # Execute function
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            
            return result
        return wrapper
    return decorator

def async_cache_result(ttl: int = 300, key_func: Callable = None):
    """Async cache function results"""
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{args}:{kwargs}"
            
            now = time.time()
            
            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    return result
            
            # Execute function
            result = await func(*args, **kwargs)
            cache[key] = (result, now)
            
            return result
        return wrapper
    return decorator

# ============================================
# TRANSACTION DECORATORS
# ============================================

def transactional(func: Callable) -> Callable:
    """Database transaction decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from ..database import db
        
        try:
            result = func(*args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
    return wrapper

def async_transactional(func: Callable) -> Callable:
    """Async database transaction decorator"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        from ..database import db
        
        try:
            result = await func(*args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
    return wrapper

# ============================================
# VALIDATION DECORATORS
# ============================================

def validate_json(schema: dict = None):
    """Validate JSON request body"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            
            if schema:
                # Basic schema validation
                for field, field_type in schema.items():
                    if field not in data:
                        return jsonify({'error': f'Missing field: {field}'}), 400
                    
                    if not isinstance(data[field], field_type):
                        return jsonify({'error': f'Invalid type for {field}'}), 400
            
            g.validated_data = data
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_query_params(schema: dict = None):
    """Validate query parameters"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = request.args.to_dict()
            
            if schema:
                for field, field_type in schema.items():
                    if field in data and not isinstance(data[field], field_type):
                        return jsonify({'error': f'Invalid type for {field}'}), 400
            
            g.validated_query = data
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ============================================
# FILE VALIDATION DECORATORS
# ============================================

def validate_file(allowed_extensions: list = None, max_size: int = None):
    """Validate uploaded file"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            
            if allowed_extensions:
                ext = file.filename.split('.')[-1].lower()
                if ext not in allowed_extensions:
                    return jsonify({'error': f'Invalid file type. Allowed: {allowed_extensions}'}), 400
            
            if max_size:
                file.seek(0, 2)
                size = file.tell()
                file.seek(0)
                if size > max_size:
                    return jsonify({'error': f'File too large. Max size: {max_size / (1024*1024)}MB'}), 400
            
            g.uploaded_file = file
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ============================================
# ERROR HANDLING DECORATORS
# ============================================

def handle_errors(func: Callable) -> Callable:
    """Global error handling decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unhandled error in {func.__name__}: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper

def async_handle_errors(func: Callable) -> Callable:
    """Async global error handling decorator"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unhandled error in {func.__name__}: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper

# ============================================
# MEASUREMENT DECORATORS
# ============================================

def measure_performance(func: Callable) -> Callable:
    """Measure function performance metrics"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        
        # Log performance
        logger.info(f"Performance: {func.__name__} took {elapsed:.4f}s")
        
        # Store in g for response headers
        if hasattr(g, 'performance'):
            g.performance[func.__name__] = elapsed
        else:
            g.performance = {func.__name__: elapsed}
        
        return result
    return wrapper

# ============================================
# DEPRECATION DECORATORS
# ============================================

def deprecated(reason: str = None):
    """Mark function as deprecated"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"{func.__name__} is deprecated"
            if reason:
                msg += f": {reason}"
            logger.warning(msg)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ============================================
# COMBINED DECORATORS
# ============================================

def api_endpoint(require_auth: bool = False, require_premium: bool = False,
                 require_admin: bool = False, rate_limit: Optional[int] = None):
    """
    Combined API endpoint decorator
    
    Args:
        require_auth: Require authentication
        require_premium: Require premium subscription
        require_admin: Require admin access
        rate_limit: Rate limit per minute (if None, no limit)
    """
    def decorator(func):
        # Apply decorators in order
        if require_admin:
            func = require_admin(func)
        elif require_premium:
            func = require_premium(func)
        elif require_auth:
            func = require_auth(func)
        
        if rate_limit:
            func = rate_limit_user(limit=rate_limit, period=60)(func)
        
        func = handle_errors(func)
        func = measure_performance(func)
        
        return func
    return decorator
