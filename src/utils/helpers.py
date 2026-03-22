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
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple


# ============================================
# STRING UTILITIES
# ============================================

def generate_random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def capitalize_words(text: str) -> str:
    return ' '.join(word.capitalize() for word in text.split())


def extract_emails(text: str) -> List[str]:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)


def extract_urls(text: str) -> List[str]:
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+'
    return re.findall(pattern, text)


# ============================================
# FILE UTILITIES
# ============================================

def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower().lstrip('.')


def get_file_size(filepath: str) -> int:
    try:
        return os.path.getsize(filepath)
    except:
        return 0


def format_file_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"


def format_size(size_bytes: int) -> str:
    """Alias for format_file_size"""
    return format_file_size(size_bytes)


def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def is_image_file(filepath: str) -> bool:
    ext = get_file_extension(filepath)
    return ext in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}


def is_video_file(filepath: str) -> bool:
    ext = get_file_extension(filepath)
    return ext in {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'}


def is_audio_file(filepath: str) -> bool:
    ext = get_file_extension(filepath)
    return ext in {'mp3', 'wav', 'aac', 'ogg', 'flac'}


def secure_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^\w\.-]', '', filename)
    return filename if filename else 'file'


def generate_unique_filename(original_filename: str, prefix: str = '') -> str:
    ext = get_file_extension(original_filename)
    name = secure_filename(original_filename)
    unique_id = generate_random_string(8)
    return f"{prefix}_{unique_id}_{name}" if prefix else f"{unique_id}_{name}"


def get_temp_file(suffix: str = None) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def cleanup_file(filepath: str) -> bool:
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except:
        pass
    return False


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and get_file_extension(filename) in allowed_extensions


def get_file_info(filepath: str) -> Dict:
    """Get file information"""
    info = {
        'size': get_file_size(filepath),
        'extension': get_file_extension(filepath),
        'filename': os.path.basename(filepath),
        'path': filepath
    }
    
    if is_image_file(filepath):
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                info['width'] = img.width
                info['height'] = img.height
                info['format'] = img.format
        except:
            pass
    
    return info


# ============================================
# DATE TIME UTILITIES
# ============================================

def get_current_timestamp() -> str:
    return datetime.now().isoformat()


def format_datetime(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    return dt.strftime(fmt)


def parse_datetime(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


def time_ago(dt: datetime) -> str:
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    else:
        return f"{int(seconds / 86400)} days ago"


def get_date_range(days: int = 7) -> Tuple[datetime, datetime]:
    end = datetime.now()
    start = end - timedelta(days=days)
    return start, end


def is_within_last_hours(dt: datetime, hours: int = 24) -> bool:
    cutoff = datetime.now() - timedelta(hours=hours)
    return dt >= cutoff


# ============================================
# DICTIONARY UTILITIES
# ============================================

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def filter_dict(data: Dict, keys: List[str]) -> Dict:
    return {k: v for k, v in data.items() if k in keys}


def exclude_keys(data: Dict, keys: List[str]) -> Dict:
    return {k: v for k, v in data.items() if k not in keys}


# ============================================
# JSON UTILITIES
# ============================================

def json_serialize(obj: Any) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)


def json_deserialize(json_str: str) -> Any:
    try:
        return json.loads(json_str)
    except:
        return None


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    try:
        return json.loads(json_str)
    except:
        return default


# ============================================
# TEMPORARY DIRECTORY CONTEXT MANAGER
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
