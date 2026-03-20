"""
Utils Package - Utility functions and helpers
Author: @kinva_master
"""

from .helpers import (
    generate_random_string, generate_secure_token, generate_uuid,
    slugify, truncate_text, capitalize_words, extract_emails, extract_urls,
    format_file_size, get_file_extension, get_file_size, get_mime_type,
    is_image_file, is_video_file, is_audio_file, secure_filename,
    generate_unique_filename, get_temp_file, cleanup_file,
    get_current_timestamp, format_datetime, parse_datetime, time_ago,
    get_date_range, is_within_last_hours, deep_merge, filter_dict, exclude_keys,
    json_serialize, json_deserialize, safe_json_loads
)

from .validators import (
    is_valid_email, is_valid_url, is_valid_username, is_valid_telegram_id,
    is_valid_password, is_valid_phone, is_valid_date, is_valid_uuid,
    validate_telegram_hash, validate_password_strength, validate_file_type,
    validate_file_size, validate_video_duration
)

from .decorators import (
    retry, timer, log_execution, async_retry, require_premium, 
    rate_limit, cache_result, require_admin
)

from .logger import (
    setup_logger, get_logger, log_error, log_user_activity,
    log_api_call, log_payment, log_security_event
)

from .rate_limiter import (
    RateLimiter, rate_limit_ip, rate_limit_user, rate_limit_endpoint
)

__all__ = [
    # Helpers
    'generate_random_string', 'generate_secure_token', 'generate_uuid',
    'slugify', 'truncate_text', 'capitalize_words', 'extract_emails', 'extract_urls',
    'format_file_size', 'get_file_extension', 'get_file_size', 'get_mime_type',
    'is_image_file', 'is_video_file', 'is_audio_file', 'secure_filename',
    'generate_unique_filename', 'get_temp_file', 'cleanup_file',
    'get_current_timestamp', 'format_datetime', 'parse_datetime', 'time_ago',
    'get_date_range', 'is_within_last_hours', 'deep_merge', 'filter_dict', 'exclude_keys',
    'json_serialize', 'json_deserialize', 'safe_json_loads',
    
    # Validators
    'is_valid_email', 'is_valid_url', 'is_valid_username', 'is_valid_telegram_id',
    'is_valid_password', 'is_valid_phone', 'is_valid_date', 'is_valid_uuid',
    'validate_telegram_hash', 'validate_password_strength', 'validate_file_type',
    'validate_file_size', 'validate_video_duration',
    
    # Decorators
    'retry', 'timer', 'log_execution', 'async_retry', 'require_premium', 
    'rate_limit', 'cache_result', 'require_admin',
    
    # Logger
    'setup_logger', 'get_logger', 'log_error', 'log_user_activity',
    'log_api_call', 'log_payment', 'log_security_event',
    
    # Rate Limiter
    'RateLimiter', 'rate_limit_ip', 'rate_limit_user', 'rate_limit_endpoint'
]
