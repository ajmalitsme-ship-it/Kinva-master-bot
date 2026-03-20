"""
Validators - Input validation functions
Author: @kinva_master
"""

import re
import uuid
from datetime import datetime
from typing import Any, Optional, List, Tuple
import phonenumbers

from ..config import Config

# ============================================
# EMAIL VALIDATION
# ============================================

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_domain(email: str) -> bool:
    """Check if email domain is valid (not disposable)"""
    if not email:
        return False
    
    domain = email.split('@')[-1].lower()
    
    # Common disposable email domains
    disposable_domains = {
        'tempmail.com', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'yopmail.com', 'throwawaymail.com'
    }
    
    return domain not in disposable_domains

# ============================================
# URL VALIDATION
# ============================================

def is_valid_url(url: str, require_http: bool = True) -> bool:
    """Validate URL"""
    if not url:
        return False
    
    pattern = r'^https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+'
    if require_http:
        return bool(re.match(pattern, url))
    else:
        return bool(re.match(r'^(https?://)?(?:[a-zA-Z]|[0-9]|[$-_@.&+])+', url))

def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube link"""
    patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtu\.be/[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+'
    ]
    return any(re.match(p, url) for p in patterns)

def is_valid_instagram_url(url: str) -> bool:
    """Check if URL is a valid Instagram link"""
    patterns = [
        r'^https?://(?:www\.)?instagram\.com/p/[\w-]+',
        r'^https?://(?:www\.)?instagram\.com/reel/[\w-]+',
        r'^https?://(?:www\.)?instagram\.com/stories/[\w-]+'
    ]
    return any(re.match(p, url) for p in patterns)

# ============================================
# USERNAME VALIDATION
# ============================================

def is_valid_username(username: str, min_length: int = 3, max_length: int = 30) -> bool:
    """Validate username"""
    if not username:
        return False
    
    if len(username) < min_length or len(username) > max_length:
        return False
    
    # Only alphanumeric and underscore
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

def is_valid_telegram_username(username: str) -> bool:
    """Validate Telegram username"""
    if not username:
        return False
    
    # Telegram username rules: 5-32 chars, alphanumeric and underscore
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
    return bool(re.match(pattern, username))

# ============================================
# PASSWORD VALIDATION
# ============================================

def is_valid_password(password: str, min_length: int = 8, max_length: int = 128) -> bool:
    """Validate password"""
    if not password:
        return False
    
    if len(password) < min_length or len(password) > max_length:
        return False
    
    return True

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Strong password"

def get_password_strength_score(password: str) -> int:
    """Get password strength score (0-100)"""
    score = 0
    
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    
    if re.search(r'[A-Z]', password):
        score += 15
    if re.search(r'[a-z]', password):
        score += 15
    if re.search(r'[0-9]', password):
        score += 15
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 25
    
    return min(score, 100)

# ============================================
# PHONE VALIDATION
# ============================================

def is_valid_phone(phone: str, country: str = 'IN') -> bool:
    """Validate phone number"""
    if not phone:
        return False
    
    try:
        parsed = phonenumbers.parse(phone, country)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

def format_phone(phone: str, country: str = 'IN') -> str:
    """Format phone number"""
    try:
        parsed = phonenumbers.parse(phone, country)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except:
        return phone

# ============================================
# ID VALIDATION
# ============================================

def is_valid_telegram_id(telegram_id: int) -> bool:
    """Validate Telegram ID"""
    return isinstance(telegram_id, int) and telegram_id > 0

def is_valid_uuid(uuid_str: str) -> bool:
    """Validate UUID"""
    try:
        uuid.UUID(uuid_str)
        return True
    except:
        return False

def is_valid_phonepe_id(phonepe_id: str) -> bool:
    """Validate PhonePe ID"""
    pattern = r'^[a-zA-Z0-9._-]+@(?:ybl|okhdfcbank|okicici|oksbi|paytm|phonepe)$'
    return bool(re.match(pattern, phonepe_id))

# ============================================
# DATE VALIDATION
# ============================================

def is_valid_date(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """Validate date string"""
    try:
        datetime.strptime(date_str, format)
        return True
    except:
        return False

def is_valid_datetime(datetime_str: str) -> bool:
    """Validate datetime string"""
    try:
        datetime.fromisoformat(datetime_str)
        return True
    except:
        return False

def is_future_date(date_str: str) -> bool:
    """Check if date is in future"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date > datetime.now()
    except:
        return False

def is_past_date(date_str: str) -> bool:
    """Check if date is in past"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date < datetime.now()
    except:
        return False

# ============================================
# FILE VALIDATION
# ============================================

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type against allowed extensions"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return ext in allowed_types

def validate_file_size(size: int, max_size: int) -> bool:
    """Validate file size"""
    return size <= max_size

def validate_video_duration(duration: float, max_duration: float) -> bool:
    """Validate video duration"""
    return duration <= max_duration

def validate_image_dimensions(width: int, height: int, max_width: int, max_height: int) -> bool:
    """Validate image dimensions"""
    return width <= max_width and height <= max_height

# ============================================
# TELEGRAM VALIDATION
# ============================================

def validate_telegram_hash(data: dict) -> bool:
    """Validate Telegram login hash"""
    from .helpers import verify_telegram_hash
    return verify_telegram_hash(data)

def validate_telegram_bot_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    pattern = r'^\d+:[\w-]{35}$'
    return bool(re.match(pattern, token))

# ============================================
# CARD VALIDATION
# ============================================

def is_valid_card_number(card_number: str) -> bool:
    """Validate credit card number using Luhn algorithm"""
    if not card_number:
        return False
    
    # Remove spaces
    card_number = card_number.replace(' ', '')
    
    if not card_number.isdigit():
        return False
    
    # Luhn algorithm
    total = 0
    is_second = False
    
    for digit in reversed(card_number):
        d = int(digit)
        
        if is_second:
            d *= 2
            if d > 9:
                d -= 9
        
        total += d
        is_second = not is_second
    
    return total % 10 == 0

def is_valid_cvv(cvv: str) -> bool:
    """Validate CVV"""
    return cvv.isdigit() and len(cvv) in [3, 4]

def is_valid_expiry_date(month: str, year: str) -> bool:
    """Validate card expiry date"""
    try:
        exp_month = int(month)
        exp_year = int(year)
        
        now = datetime.now()
        if exp_year < now.year % 100:
            return False
        if exp_year == now.year % 100 and exp_month < now.month:
            return False
        
        return 1 <= exp_month <= 12
    except:
        return False

# ============================================
# UPI VALIDATION
# ============================================

def is_valid_upi_id(upi_id: str) -> bool:
    """Validate UPI ID"""
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$'
    return bool(re.match(pattern, upi_id))

# ============================================
# CRYPTO VALIDATION
# ============================================

def is_valid_bitcoin_address(address: str) -> bool:
    """Validate Bitcoin address"""
    # Basic validation (P2PKH, P2SH, Bech32)
    patterns = [
        r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',  # P2PKH/P2SH
        r'^bc1[a-z0-9]{39,59}$'  # Bech32
    ]
    return any(re.match(p, address) for p in patterns)

def is_valid_ethereum_address(address: str) -> bool:
    """Validate Ethereum address"""
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))

def is_valid_usdt_address(address: str) -> bool:
    """Validate USDT (TRC-20) address"""
    pattern = r'^T[a-zA-Z0-9]{33}$'
    return bool(re.match(pattern, address))

# ============================================
# SOCIAL MEDIA VALIDATION
# ============================================

def is_valid_instagram_username(username: str) -> bool:
    """Validate Instagram username"""
    pattern = r'^[a-zA-Z0-9_.]{1,30}$'
    return bool(re.match(pattern, username))

def is_valid_twitter_username(username: str) -> bool:
    """Validate Twitter username"""
    pattern = r'^[a-zA-Z0-9_]{1,15}$'
    return bool(re.match(pattern, username))

def is_valid_facebook_username(username: str) -> bool:
    """Validate Facebook username"""
    pattern = r'^[a-zA-Z0-9.]{5,50}$'
    return bool(re.match(pattern, username))

# ============================================
# IP ADDRESS VALIDATION
# ============================================

def is_valid_ipv4(ip: str) -> bool:
    """Validate IPv4 address"""
    pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

def is_valid_ipv6(ip: str) -> bool:
    """Validate IPv6 address"""
    try:
        import ipaddress
        ipaddress.IPv6Address(ip)
        return True
    except:
        return False

# ============================================
# COMBINED VALIDATION
# ============================================

class Validator:
    """Combined validator class"""
    
    @staticmethod
    def validate_user_data(data: dict) -> Tuple[bool, List[str]]:
        """Validate user registration data"""
        errors = []
        
        if 'username' in data and not is_valid_username(data['username']):
            errors.append("Invalid username (3-30 chars, alphanumeric and underscore)")
        
        if 'email' in data and not is_valid_email(data['email']):
            errors.append("Invalid email address")
        
        if 'password' in data:
            valid, msg = validate_password_strength(data['password'])
            if not valid:
                errors.append(msg)
        
        if 'phone' in data and data['phone'] and not is_valid_phone(data['phone']):
            errors.append("Invalid phone number")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_payment_data(data: dict) -> Tuple[bool, List[str]]:
        """Validate payment data"""
        errors = []
        
        if 'card_number' in data and not is_valid_card_number(data['card_number']):
            errors.append("Invalid card number")
        
        if 'cvv' in data and not is_valid_cvv(data['cvv']):
            errors.append("Invalid CVV")
        
        if 'expiry_month' in data and 'expiry_year' in data:
            if not is_valid_expiry_date(data['expiry_month'], data['expiry_year']):
                errors.append("Card expired or invalid expiry date")
        
        if 'upi_id' in data and not is_valid_upi_id(data['upi_id']):
            errors.append("Invalid UPI ID")
        
        return len(errors) == 0, errors
