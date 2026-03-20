"""
Helper Functions - Common utility functions
Author: @kinva_master
"""

import os
import re
import json
import uuid
import secrets
import string
import mimetypes
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import hashlib
import base64
import hmac

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

def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text"""
    pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{3,4}'
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
    return ext in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico'}

def is_video_file(filename: str) -> bool:
    """Check if file is a video"""
    ext = get_file_extension(filename)
    return ext in {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v', '3gp'}

def is_audio_file(filename: str) -> bool:
    """Check if file is audio"""
    ext = get_file_extension(filename)
    return ext in {'mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a', 'wma'}

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

def cleanup_file(filepath: str) -> bool:
    """Delete file if exists"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False

def cleanup_directory(dirpath: str) -> bool:
    """Delete directory and its contents"""
    try:
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)
            return True
    except Exception:
        pass
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

def days_between(date1: datetime, date2: datetime) -> int:
    """Get days between two dates"""
    return abs((date2 - date1).days)

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

def flatten_dict(data: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# ============================================
# JSON UTILITIES
# ============================================

def json_serialize(obj: Any) -> str:
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
# CRYPTOGRAPHY UTILITIES
# ============================================

def hash_string(text: str) -> str:
    """Hash string using SHA256"""
    return hashlib.sha256(text.encode()).hexdigest()

def generate_telegram_hash(data: Dict) -> str:
    """Generate Telegram login hash"""
    auth_data = sorted(data.items())
    auth_string = '\n'.join([f"{k}={v}" for k, v in auth_data if k != 'hash'])
    secret_key = hashlib.sha256(os.getenv('API_HASH', '').encode()).digest()
    return hmac.new(secret_key, auth_string.encode(), hashlib.sha256).hexdigest()

def verify_telegram_hash(data: Dict) -> bool:
    """Verify Telegram login hash"""
    if 'hash' not in data:
        return False
    
    hash_value = data.pop('hash')
    computed_hash = generate_telegram_hash(data)
    return hmac.compare_digest(computed_hash, hash_value)

def encode_base64(text: str) -> str:
    """Encode string to base64"""
    return base64.b64encode(text.encode()).decode()

def decode_base64(encoded: str) -> str:
    """Decode base64 string"""
    return base64.b64decode(encoded).decode()

# ============================================
# IMAGE UTILITIES
# ============================================

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
    except Exception:
        return {}

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
    except Exception:
        return {}

# ============================================
# NETWORK UTILITIES
# ============================================

def get_client_ip(request) -> str:
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def get_user_agent(request) -> str:
    """Get user agent from request"""
    return request.headers.get('User-Agent', 'Unknown')

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
        if self.path and os.path.exists(self.path):
            shutil.rmtree(self.path)

class Timer:
    """Timer context manager"""
    
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
            print(f"{self.name} took {self.elapsed:.2f}s")

# ============================================
# MEMOIZATION
# ============================================

def memoize(func):
    """Memoization decorator"""
    cache = {}
    
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    return wrapper

# ============================================
# IMPORT UTILITIES
# ============================================

def import_string(import_name: str) -> Any:
    """Import string path to object"""
    import importlib
    
    try:
        module_name, attr_name = import_name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not import '{import_name}': {e}")
