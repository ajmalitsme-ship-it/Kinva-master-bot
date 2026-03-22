"""
Utils Package - Utility functions and helpers
Author: @kinva_master
"""

from .helpers import (
    # String utilities
    generate_random_string, generate_secure_token, generate_uuid,
    slugify, truncate_text, capitalize_words, extract_emails, extract_urls,
    # File utilities
    format_file_size, format_size, get_file_extension, get_file_size,
    get_mime_type, is_image_file, is_video_file, is_audio_file,
    secure_filename, generate_unique_filename, get_temp_file, cleanup_file,
    allowed_file, get_file_info,
    # Date time utilities
    get_current_timestamp, format_datetime, parse_datetime, time_ago,
    get_date_range, is_within_last_hours,
    # Dictionary utilities
    deep_merge, filter_dict, exclude_keys,
    # JSON utilities
    json_serialize, json_deserialize, safe_json_loads,
    # Context manager
    TemporaryDirectory
)

__all__ = [
    # String utilities
    'generate_random_string', 'generate_secure_token', 'generate_uuid',
    'slugify', 'truncate_text', 'capitalize_words', 'extract_emails', 'extract_urls',
    # File utilities
    'format_file_size', 'format_size', 'get_file_extension', 'get_file_size',
    'get_mime_type', 'is_image_file', 'is_video_file', 'is_audio_file',
    'secure_filename', 'generate_unique_filename', 'get_temp_file', 'cleanup_file',
    'allowed_file', 'get_file_info',
    # Date time utilities
    'get_current_timestamp', 'format_datetime', 'parse_datetime', 'time_ago',
    'get_date_range', 'is_within_last_hours',
    # Dictionary utilities
    'deep_merge', 'filter_dict', 'exclude_keys',
    # JSON utilities
    'json_serialize', 'json_deserialize', 'safe_json_loads',
    # Context manager
    'TemporaryDirectory'
]
