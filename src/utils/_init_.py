cat > src/utils/__init__.py << 'EOF'
"""
Utils Package - Helper functions for Kinva Master
"""
from ..utils.video_utils import get_video_info
# Import ALL needed functions from helpers
from .helpers import (
    get_video_info,
    cleanup_file,
    TemporaryDirectory,
    format_file_size,
    format_file_size as format_size,
    get_file_extension,
    get_file_size,
    get_file_info,
    secure_filename,
    allowed_file,
    slugify,
    generate_uuid,
    time_ago,
)

# Import from decorators (optional - remove if not needed)
try:
    from .decorators import require_auth, require_premium, require_admin, rate_limit
except ImportError:
    require_auth = require_premium = require_admin = rate_limit = None

# Import from logger (optional - remove if not needed)
try:
    from .logger import setup_logger, get_logger, log_error
except ImportError:
    setup_logger = get_logger = log_error = None

# Import from rate_limiter (optional - remove if not needed)
try:
    from .rate_limiter import RateLimiter, rate_limit_ip, rate_limit_user
except ImportError:
    RateLimiter = rate_limit_ip = rate_limit_user = None

# Import from validators (optional - remove if not needed)
try:
    from .validators import is_valid_email, is_valid_username, validate_password_strength
except ImportError:
    is_valid_email = is_valid_username = validate_password_strength = None

# Export only what's needed for video_processor
__all__ = [
    'get_video_info',
    'cleanup_file',
    'TemporaryDirectory',
    'format_file_size',
    'format_size',
]
EOF
