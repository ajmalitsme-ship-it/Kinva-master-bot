"""
Kinva Master - Utilities Module
Helper functions, decorators, and common utilities
Author: @kinva_master
"""

import os
import re
import json
import uuid
import hashlib
import hmac
import base64
import secrets
import string
import logging
import tempfile
import subprocess
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List, Tuple, Callable
from pathlib import Path
import mimetypes

from .config import Config

logger = logging.getLogger(__name__)

# ============================================
# STRING UTILITIES
# ============================================

def generate_random_string(length: int = 16) -> str:
    """Generate random string"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_token(length: int = 32) -> str:
    """Generate secure token"""
    return secrets.token_urlsafe(length)

def generate_uuid() -> str:
    """Generate UUID"""
    return str(uuid.uuid4())

def slugify(text: str) -> str:
    """Convert text to slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def capitalize_words(text: str) -> str:
    """Capitalize each word"""
    return ' '.join(word.capitalize() for word in text.split())

def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+'
    return re.findall(pattern, text)

# ============================================
# FILE UTILITIES
# ============================================

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lower().lstrip('.')

def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def get_mime_type(filename: str) -> str:
    """Get MIME type of file"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    ext = get_file_extension(filename)
    return ext in Config.ALLOWED_IMAGES

def is_video_file(filename: str) -> bool:
    """Check if file is a video"""
    ext = get_file_extension(filename)
    return ext in Config.ALLOWED_VIDEOS

def is_audio_file(filename: str) -> bool:
    """Check if file is audio"""
    ext = get_file_extension(filename)
    return ext in Config.ALLOWED_AUDIO

def secure_filename(filename: str) -> str:
    """Secure filename"""
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove any non-alphanumeric characters except . and _
    filename = re.sub(r'[^\w\.-]', '', filename)
    
    # Ensure we have a filename
    if not filename:
        filename = 'file'
    
    return filename

def generate_unique_filename(original_filename: str, prefix: str = '') -> str:
    """Generate unique filename"""
    ext = get_file_extension(original_filename)
    name = secure_filename(original_filename)
    unique_id = generate_random_string(8)
    
    if prefix:
        return f"{prefix}_{unique_id}_{name}"
    return f"{unique_id}_{name}"

def get_temp_file(suffix: str = None) -> str:
    """Get temporary file path"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path

def cleanup_file(filepath: str):
    """Delete file if exists"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        logger.error(f"Failed to delete file {filepath}: {e}")
    return False

# ============================================
# DATE TIME UTILITIES
# ============================================

def get_current_timestamp() -> str:
    """Get current timestamp"""
    return datetime.now().isoformat()

def format_datetime(dt: datetime, format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime"""
    return dt.strftime(format)

def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string"""
    return datetime.fromisoformat(dt_str)

def time_ago(dt: datetime) -> str:
    """Get time ago string"""
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"

def get_date_range(days: int = 7) -> Tuple[datetime, datetime]:
    """Get date range"""
    end = datetime.now()
    start = end - timedelta(days=days)
    return start, end

def is_within_last_hours(dt: datetime, hours: int = 24) -> bool:
    """Check if datetime is within last hours"""
    cutoff = datetime.now() - timedelta(hours=hours)
    return dt >= cutoff

# ============================================
# CRYPTOGRAPHY UTILITIES
# ============================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    import bcrypt
    salt = bcrypt.gensalt(rounds=Config.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_api_key() -> str:
    """Generate API key"""
    return secrets.token_urlsafe(32)

def generate_jwt_token(user_id: int, expires_in: int = 3600) -> str:
    """Generate JWT token"""
    import jwt
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify JWT token"""
    import jwt
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_telegram_hash(data: Dict) -> str:
    """Generate Telegram login hash"""
    auth_data = sorted(data.items())
    auth_string = '\n'.join([f"{k}={v}" for k, v in auth_data if k != 'hash'])
    secret_key = hashlib.sha256(Config.API_HASH.encode()).digest()
    return hmac.new(secret_key, auth_string.encode(), hashlib.sha256).hexdigest()

def verify_telegram_hash(data: Dict) -> bool:
    """Verify Telegram login hash"""
    if 'hash' not in data:
        return False
    
    hash_value = data.pop('hash')
    computed_hash = generate_telegram_hash(data)
    return hmac.compare_digest(computed_hash, hash_value)

# ============================================
# JSON UTILITIES
# ============================================

def json_serialize(obj) -> str:
    """Serialize object to JSON"""
    return json.dumps(obj, default=str, ensure_ascii=False)

def json_deserialize(json_str: str) -> Any:
    """Deserialize JSON string"""
    try:
        return json.loads(json_str)
    except:
        return None

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safe JSON load"""
    try:
        return json.loads(json_str)
    except:
        return default

# ============================================
# VALIDATION UTILITIES
# ============================================

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_url(url: str) -> bool:
    """Validate URL"""
    pattern = r'^https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+'
    return bool(re.match(pattern, url))

def is_valid_username(username: str) -> bool:
    """Validate username"""
    if len(username) < 3 or len(username) > 30:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

def is_valid_telegram_id(telegram_id: int) -> bool:
    """Validate Telegram ID"""
    return isinstance(telegram_id, int) and telegram_id > 0

# ============================================
# DICTIONARY UTILITIES
# ============================================

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result

def filter_dict(data: Dict, keys: List[str]) -> Dict:
    """Filter dictionary by keys"""
    return {k: v for k, v in data.items() if k in keys}

def exclude_keys(data: Dict, keys: List[str]) -> Dict:
    """Exclude keys from dictionary"""
    return {k: v for k, v in data.items() if k not in keys}

# ============================================
# DECORATORS
# ============================================

def retry(max_attempts: int = 3, delay: int = 1):
    """Retry decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def timer(func):
    """Timer decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

def log_execution(func):
    """Log execution decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Executing {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

def async_retry(max_attempts: int = 3, delay: int = 1):
    """Async retry decorator"""
    import asyncio
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator

def require_premium(func):
    """Require premium decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from .database import db
        
        # Get user from first argument
        user = None
        if args and hasattr(args[0], 'user_id'):
            user = db.get_user(args[0].user_id)
        elif 'user_id' in kwargs:
            user = db.get_user(kwargs['user_id'])
        
        if user and user.get('is_premium'):
            return func(*args, **kwargs)
        else:
            raise PermissionError("Premium subscription required")
    
    return wrapper

# ============================================
# CONTEXT MANAGERS
# ============================================

class TemporaryDirectory:
    """Temporary directory context manager"""
    
    def __init__(self):
        self.path = None
    
    def __enter__(self):
        import tempfile
        self.path = tempfile.mkdtemp()
        return self.path
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import shutil
        if self.path and os.path.exists(self.path):
            shutil.rmtree(self.path)

class Timing:
    """Timing context manager"""
    
    def __init__(self, name: str = None):
        self.name = name
        self.start = None
        self.elapsed = None
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start
        if self.name:
            logger.debug(f"{self.name} took {self.elapsed:.2f}s")

# ============================================
# PERFORMANCE UTILITIES
# ============================================

def memoize(func):
    """Memoization decorator"""
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    return wrapper

def rate_limit(limit: int = 60, period: int = 60):
    """Rate limit decorator"""
    from collections import defaultdict
    import time
    
    calls = defaultdict(list)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            key = func.__name__
            
            # Clean old calls
            calls[key] = [t for t in calls[key] if now - t < period]
            
            # Check limit
            if len(calls[key]) >= limit:
                raise Exception(f"Rate limit exceeded: {limit} per {period}s")
            
            # Add call
            calls[key].append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# ============================================
# COLOR UTILITIES
# ============================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def is_dark_color(hex_color: str) -> bool:
    """Check if color is dark"""
    r, g, b = hex_to_rgb(hex_color)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return brightness < 128

def get_contrast_color(hex_color: str) -> str:
    """Get contrast color (black or white)"""
    return '#000000' if is_dark_color(hex_color) else '#ffffff'

# ============================================
# MEDIA UTILITIES
# ============================================

def get_video_info(filepath: str) -> Dict:
    """Get video information"""
    try:
        import cv2
        
        cap = cv2.VideoCapture(filepath)
        
        if not cap.isOpened():
            return {}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': duration,
            'resolution': f"{width}x{height}"
        }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {}

def get_image_info(filepath: str) -> Dict:
    """Get image information"""
    try:
        from PIL import Image
        
        with Image.open(filepath) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size': os.path.getsize(filepath)
            }
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return {}

# ============================================
# IMPORT UTILITIES
# ============================================

def import_string(import_name: str) -> Any:
    """Import string path to object"""
    import importlib
    
    module_name, attr_name = import_name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)

# ============================================
# EXPORTS
# ============================================

__all__ = [
    # String utilities
    'generate_random_string', 'generate_secure_token', 'generate_uuid',
    'slugify', 'truncate_text', 'capitalize_words',
    'extract_emails', 'extract_urls',
    
    # File utilities
    'get_file_extension', 'get_file_size', 'format_file_size',
    'get_mime_type', 'is_image_file', 'is_video_file', 'is_audio_file',
    'secure_filename', 'generate_unique_filename', 'get_temp_file', 'cleanup_file',
    
    # Date time utilities
    'get_current_timestamp', 'format_datetime', 'parse_datetime',
    'time_ago', 'get_date_range', 'is_within_last_hours',
    
    # Cryptography utilities
    'hash_password', 'verify_password', 'generate_api_key',
    'generate_jwt_token', 'verify_jwt_token',
    'generate_telegram_hash', 'verify_telegram_hash',
    
    # JSON utilities
    'json_serialize', 'json_deserialize', 'safe_json_loads',
    
    # Validation utilities
    'is_valid_email', 'is_valid_url', 'is_valid_username', 'is_valid_telegram_id',
    
    # Dictionary utilities
    'deep_merge', 'filter_dict', 'exclude_keys',
    
    # Decorators
    'retry', 'timer', 'log_execution', 'async_retry', 'require_premium',
    
    # Context managers
    'TemporaryDirectory', 'Timing',
    
    # Performance utilities
    'memoize', 'rate_limit',
    
    # Color utilities
    'hex_to_rgb', 'rgb_to_hex', 'is_dark_color', 'get_contrast_color',
    
    # Media utilities
    'get_video_info', 'get_image_info',
    
    # Import utilities
    'import_string'
]
