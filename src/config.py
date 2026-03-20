"""
Kinva Master - Configuration Module
Handles all environment variables, constants, and settings
Author: @kinva_master
"""

import os
import secrets
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Master Configuration Class"""
    
    # ============================================
    # TELEGRAM API CREDENTIALS
    # ============================================
    # Get from https://my.telegram.org
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    
    # Get from @BotFather
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    BOT_USERNAME = os.getenv('BOT_USERNAME', '@kinva_master_bot')
    BOT_NAME = os.getenv('BOT_NAME', 'Kinva Master')
    
    # ============================================
    # WEB APP CONFIGURATION
    # ============================================
    WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://kinva-master.onrender.com')
    API_URL = os.getenv('API_URL', 'https://api.kinva-master.com')
    WS_URL = os.getenv('WS_URL', 'wss://kinva-master.onrender.com')
    
    # ============================================
    # ADMIN CONFIGURATION
    # ============================================
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    ADMIN_CONTACT = os.getenv('ADMIN_CONTACT', '@kinva_master')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@kinva-master.com')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'kinva_master')
    
    # ============================================
    # APP SETTINGS
    # ============================================
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///kinva_master.db')
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
    DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))
    DATABASE_ECHO = os.getenv('DATABASE_ECHO', 'False').lower() == 'true'
    
    # ============================================
    # REDIS CONFIGURATION (Caching)
    # ============================================
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # ============================================
    # FILE STORAGE
    # ============================================
    BASE_DIR = Path(__file__).parent.parent
    
    UPLOAD_DIR = BASE_DIR / 'uploads'
    OUTPUT_DIR = BASE_DIR / 'outputs'
    TEMP_DIR = BASE_DIR / 'temp'
    THUMBNAIL_DIR = BASE_DIR / 'thumbnails'
    FONTS_DIR = BASE_DIR / 'fonts'
    TEMPLATES_DIR = BASE_DIR / 'data' / 'templates'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Create directories
    for dir_path in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR, THUMBNAIL_DIR, 
                     FONTS_DIR, TEMPLATES_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # ============================================
    # FILE SIZE LIMITS
    # ============================================
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '50')) * 1024 * 1024  # 50MB
    MAX_VIDEO_SIZE = int(os.getenv('MAX_VIDEO_SIZE', '500')) * 1024 * 1024  # 500MB
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '500')) * 1024 * 1024  # 500MB
    MAX_TOTAL_STORAGE = int(os.getenv('MAX_TOTAL_STORAGE', '1024')) * 1024 * 1024  # 1GB
    
    # ============================================
    # SUPPORTED FORMATS
    # ============================================
    ALLOWED_VIDEOS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v', '3gp', 'mpeg'}
    ALLOWED_IMAGES = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'ico'}
    ALLOWED_AUDIO = {'mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a', 'wma'}
    ALLOWED_DOCUMENTS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
    
    # ============================================
    # VIDEO EDITING SETTINGS
    # ============================================
    FREE_VIDEO_LENGTH = int(os.getenv('FREE_VIDEO_LENGTH', '60'))  # 60 seconds
    FREE_VIDEO_EXPORTS = int(os.getenv('FREE_VIDEO_EXPORTS', '3'))  # 3 per day
    FREE_IMAGE_EXPORTS = int(os.getenv('FREE_IMAGE_EXPORTS', '10'))  # 10 per day
    FREE_DESIGN_EXPORTS = int(os.getenv('FREE_DESIGN_EXPORTS', '5'))  # 5 per day
    
    PREMIUM_VIDEO_LENGTH = int(os.getenv('PREMIUM_VIDEO_LENGTH', '7200'))  # 2 hours
    PREMIUM_VIDEO_EXPORTS = int(os.getenv('PREMIUM_VIDEO_EXPORTS', '999999'))  # Unlimited
    PREMIUM_IMAGE_EXPORTS = int(os.getenv('PREMIUM_IMAGE_EXPORTS', '999999'))  # Unlimited
    PREMIUM_DESIGN_EXPORTS = int(os.getenv('PREMIUM_DESIGN_EXPORTS', '999999'))  # Unlimited
    
    # Video processing
    VIDEO_QUALITY_LEVELS = {
        '480p': {'width': 854, 'height': 480, 'bitrate': '1000k'},
        '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k'},
        '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k'},
        '4k': {'width': 3840, 'height': 2160, 'bitrate': '15000k'}
    }
    
    VIDEO_COMPRESSION_LEVELS = {
        'low': {'crf': 23, 'preset': 'veryfast'},
        'medium': {'crf': 28, 'preset': 'faster'},
        'high': {'crf': 32, 'preset': 'fast'},
        'ultra': {'crf': 36, 'preset': 'medium'}
    }
    
    # ============================================
    # IMAGE EDITING SETTINGS
    # ============================================
    IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '90'))
    THUMBNAIL_SIZE = (300, 300)
    PREVIEW_SIZE = (800, 800)
    
    # ============================================
    # WATERMARK SETTINGS
    # ============================================
    WATERMARK_TEXT = os.getenv('WATERMARK_TEXT', '@kinva_master.com')
    WATERMARK_IMAGE = os.getenv('WATERMARK_IMAGE', 'static/images/watermark.png')
    WATERMARK_OPACITY = float(os.getenv('WATERMARK_OPACITY', '0.5'))
    WATERMARK_POSITION = os.getenv('WATERMARK_POSITION', 'bottom-right')
    WATERMARK_SIZE = int(os.getenv('WATERMARK_SIZE', '100'))
    WATERMARK_FONT_SIZE = int(os.getenv('WATERMARK_FONT_SIZE', '24'))
    WATERMARK_FONT_COLOR = os.getenv('WATERMARK_FONT_COLOR', '#ffffff')
    WATERMARK_FONT = os.getenv('WATERMARK_FONT', 'Arial')
    
    # ============================================
    # PREMIUM PLANS
    # ============================================
    PREMIUM_PLANS = {
        'pro_monthly': {
            'id': 'pro_monthly',
            'name': 'Pro Monthly',
            'price': 14.99,
            'interval': 'month',
            'features': [
                '4K Video Export',
                'No Watermark',
                'All Filters & Effects',
                'Unlimited Exports',
                'Priority Support',
                '10GB Cloud Storage'
            ]
        },
        'pro_yearly': {
            'id': 'pro_yearly',
            'name': 'Pro Yearly',
            'price': 149.99,
            'interval': 'year',
            'features': [
                '4K Video Export',
                'No Watermark',
                'All Filters & Effects',
                'Unlimited Exports',
                'Priority Support',
                '10GB Cloud Storage',
                '2 Months Free'
            ]
        },
        'business_monthly': {
            'id': 'business_monthly',
            'name': 'Business Monthly',
            'price': 29.99,
            'interval': 'month',
            'features': [
                'Everything in Pro',
                'Team Collaboration (5 users)',
                'Custom Branding',
                'API Access',
                'Dedicated Support',
                '100GB Cloud Storage'
            ]
        },
        'business_yearly': {
            'id': 'business_yearly',
            'name': 'Business Yearly',
            'price': 299.99,
            'interval': 'year',
            'features': [
                'Everything in Pro',
                'Team Collaboration (5 users)',
                'Custom Branding',
                'API Access',
                'Dedicated Support',
                '100GB Cloud Storage',
                '2 Months Free'
            ]
        },
        'lifetime': {
            'id': 'lifetime',
            'name': 'Lifetime',
            'price': 299.99,
            'interval': 'once',
            'features': [
                'Everything in Pro',
                'Lifetime Access',
                'All Future Updates',
                'Priority Support Forever',
                '100GB Cloud Storage',
                'No Recurring Payments'
            ]
        }
    }
    
    # ============================================
    # PAYMENT SETTINGS
    # ============================================
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', '')
    PAYPAL_SECRET_KEY = os.getenv('PAYPAL_SECRET_KEY', '')
    CRYPTO_WALLET = os.getenv('CRYPTO_WALLET', '')
    
    # ============================================
    # CLOUD STORAGE (Optional)
    # ============================================
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'kinva-master')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')
    
    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT = int(os.getenv('RATE_LIMIT', '100'))
    RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', '60'))  # seconds
    RATE_LIMIT_BY_IP = os.getenv('RATE_LIMIT_BY_IP', 'True').lower() == 'true'
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = LOGS_DIR / 'app.log'
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # ============================================
    # EMAIL CONFIGURATION
    # ============================================
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@kinva-master.com')
    
    # ============================================
    # SESSION SETTINGS
    # ============================================
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'True').lower() == 'true'
    SESSION_USE_SIGNER = os.getenv('SESSION_USE_SIGNER', 'True').lower() == 'true'
    SESSION_KEY_PREFIX = os.getenv('SESSION_KEY_PREFIX', 'kinva_session_')
    SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', '86400'))  # 24 hours
    
    # ============================================
    # SECURITY
    # ============================================
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', '12'))
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))
    
    # ============================================
    # API KEYS (Third Party Services)
    # ============================================
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
    
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    
    INSTAGRAM_CLIENT_ID = os.getenv('INSTAGRAM_CLIENT_ID', '')
    INSTAGRAM_CLIENT_SECRET = os.getenv('INSTAGRAM_CLIENT_SECRET', '')
    
    # ============================================
    # FEATURE FLAGS
    # ============================================
    ENABLE_VIDEO_EDITOR = os.getenv('ENABLE_VIDEO_EDITOR', 'True').lower() == 'true'
    ENABLE_IMAGE_EDITOR = os.getenv('ENABLE_IMAGE_EDITOR', 'True').lower() == 'true'
    ENABLE_CANVA_EDITOR = os.getenv('ENABLE_CANVA_EDITOR', 'True').lower() == 'true'
    ENABLE_PREMIUM = os.getenv('ENABLE_PREMIUM', 'True').lower() == 'true'
    ENABLE_WEBAPP = os.getenv('ENABLE_WEBAPP', 'True').lower() == 'true'
    ENABLE_API = os.getenv('ENABLE_API', 'True').lower() == 'true'
    ENABLE_SOCKETIO = os.getenv('ENABLE_SOCKETIO', 'True').lower() == 'true'
    
    # ============================================
    # VIDEO FILTERS
    # ============================================
    VIDEO_FILTERS = {
        'vintage': {
            'name': 'Vintage',
            'description': 'Old film look with grain and faded colors',
            'icon': '🎞️',
            'premium': False,
            'params': {'contrast': 0.8, 'saturation': 0.7}
        },
        'cinematic': {
            'name': 'Cinematic',
            'description': 'Movie-like color grading with teal and orange',
            'icon': '🎬',
            'premium': False,
            'params': {'contrast': 1.2, 'saturation': 1.1}
        },
        'black_white': {
            'name': 'Black & White',
            'description': 'Classic monochrome effect',
            'icon': '⚫',
            'premium': False,
            'params': {}
        },
        'sepia': {
            'name': 'Sepia',
            'description': 'Warm brown vintage tone',
            'icon': '🟫',
            'premium': False,
            'params': {'intensity': 0.8}
        },
        'glitch': {
            'name': 'Glitch',
            'description': 'Digital distortion effect',
            'icon': '💥',
            'premium': True,
            'params': {'intensity': 0.5}
        },
        'blur': {
            'name': 'Blur',
            'description': 'Gaussian blur effect',
            'icon': '🌀',
            'premium': False,
            'params': {'radius': 5}
        },
        'sharpen': {
            'name': 'Sharpen',
            'description': 'Edge enhancement',
            'icon': '✨',
            'premium': False,
            'params': {'amount': 1.5}
        },
        'mirror': {
            'name': 'Mirror',
            'description': 'Horizontal reflection',
            'icon': '🪞',
            'premium': False,
            'params': {}
        },
        'slow_motion': {
            'name': 'Slow Motion',
            'description': '0.5x speed effect',
            'icon': '🐢',
            'premium': False,
            'params': {'speed': 0.5}
        },
        'fast_motion': {
            'name': 'Fast Motion',
            'description': '2x speed effect',
            'icon': '⚡',
            'premium': False,
            'params': {'speed': 2.0}
        },
        'neon': {
            'name': 'Neon',
            'description': 'Glowing neon effect',
            'icon': '🔥',
            'premium': True,
            'params': {'intensity': 0.8}
        },
        'cartoon': {
            'name': 'Cartoon',
            'description': 'Comic book style',
            'icon': '🎨',
            'premium': True,
            'params': {'smooth': 5}
        },
        '3d': {
            'name': '3D Effect',
            'description': 'Anaglyph 3D effect',
            'icon': '🎥',
            'premium': True,
            'params': {'depth': 10}
        },
        'oil_paint': {
            'name': 'Oil Paint',
            'description': 'Artistic oil painting look',
            'icon': '🎭',
            'premium': True,
            'params': {'radius': 5, 'intensity': 3}
        }
    }
    
    # ============================================
    # IMAGE FILTERS
    # ============================================
    IMAGE_FILTERS = {
        'grayscale': {
            'name': 'Grayscale',
            'description': 'Convert to black and white',
            'icon': '⚫',
            'premium': False
        },
        'sepia': {
            'name': 'Sepia',
            'description': 'Warm vintage tone',
            'icon': '🟫',
            'premium': False
        },
        'invert': {
            'name': 'Invert',
            'description': 'Negative colors',
            'icon': '🔄',
            'premium': False
        },
        'vintage': {
            'name': 'Vintage',
            'description': 'Old photo look',
            'icon': '🎞️',
            'premium': False
        },
        'cinematic': {
            'name': 'Cinematic',
            'description': 'Movie color grading',
            'icon': '🎬',
            'premium': False
        },
        'glitch': {
            'name': 'Glitch',
            'description': 'Digital glitch effect',
            'icon': '💥',
            'premium': True
        },
        'blur': {
            'name': 'Blur',
            'description': 'Gaussian blur',
            'icon': '🌀',
            'premium': False
        },
        'sharpen': {
            'name': 'Sharpen',
            'description': 'Edge enhancement',
            'icon': '✨',
            'premium': False
        },
        'edge': {
            'name': 'Edge Detection',
            'description': 'Outline effect',
            'icon': '✏️',
            'premium': False
        },
        'emboss': {
            'name': 'Emboss',
            'description': '3D embossed effect',
            'icon': '⛰️',
            'premium': False
        },
        'neon': {
            'name': 'Neon',
            'description': 'Glowing neon effect',
            'icon': '🔥',
            'premium': True
        },
        'sketch': {
            'name': 'Sketch',
            'description': 'Pencil drawing look',
            'icon': '✏️',
            'premium': True
        },
        'oil_paint': {
            'name': 'Oil Paint',
            'description': 'Oil painting effect',
            'icon': '🎭',
            'premium': True
        },
        'watercolor': {
            'name': 'Watercolor',
            'description': 'Watercolor painting look',
            'icon': '🎨',
            'premium': True
        },
        'pixelate': {
            'name': 'Pixelate',
            'description': 'Mosaic pixel effect',
            'icon': '🔲',
            'premium': True
        },
        'thermal': {
            'name': 'Thermal',
            'description': 'Heat vision effect',
            'icon': '🔥',
            'premium': True
        }
    }
    
    # ============================================
    # TRANSITIONS
    # ============================================
    TRANSITIONS = {
        'fade': {
            'name': 'Fade',
            'description': 'Smooth fade transition',
            'duration': 1.0,
            'premium': False
        },
        'slide': {
            'name': 'Slide',
            'description': 'Slide to next clip',
            'duration': 1.0,
            'premium': False
        },
        'wipe': {
            'name': 'Wipe',
            'description': 'Wipe transition',
            'duration': 1.0,
            'premium': False
        },
        'zoom': {
            'name': 'Zoom',
            'description': 'Zoom transition',
            'duration': 1.0,
            'premium': False
        },
        'rotate': {
            'name': 'Rotate',
            'description': 'Rotating transition',
            'duration': 1.0,
            'premium': True
        },
        'glitch': {
            'name': 'Glitch',
            'description': 'Digital glitch transition',
            'duration': 1.0,
            'premium': True
        },
        'flash': {
            'name': 'Flash',
            'description': 'White flash transition',
            'duration': 0.5,
            'premium': True
        },
        '3d': {
            'name': '3D Flip',
            'description': '3D flip transition',
            'duration': 1.0,
            'premium': True
        }
    }
    
    # ============================================
    # CANVA FEATURES
    # ============================================
    CANVA_FONTS = [
        'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Georgia',
        'Verdana', 'Tahoma', 'Trebuchet MS', 'Comic Sans MS', 'Impact',
        'Roboto', 'Open Sans', 'Lato', 'Montserrat', 'Poppins',
        'Playfair Display', 'Merriweather', 'Oswald', 'Raleway', 'Nunito',
        'Ubuntu', 'Cabin', 'Josefin Sans', 'Quicksand', 'Pacifico',
        'Dancing Script', 'Lobster', 'Shadows Into Light', 'Indie Flower',
        'Caveat', 'Courgette', 'Kalam', 'Great Vibes', 'Alex Brush'
    ]
    
    CANVA_SHAPES = [
        'rectangle', 'circle', 'triangle', 'line', 'arrow', 'star',
        'heart', 'cloud', 'speech bubble', 'thought bubble', 'callout',
        'pentagon', 'hexagon', 'octagon', 'cross', 'checkmark'
    ]
    
    CANVA_MAX_LAYERS = int(os.getenv('CANVA_MAX_LAYERS', '50'))
    CANVA_MAX_ELEMENTS = int(os.getenv('CANVA_MAX_ELEMENTS', '100'))
    
    # ============================================
    # TEMPLATES
    # ============================================
    TEMPLATE_CATEGORIES = [
        'social_media', 'business', 'education', 'events', 'video',
        'marketing', 'personal', 'art', 'photography', 'technology'
    ]
    
    TEMPLATE_TYPES = [
        'instagram_post', 'instagram_story', 'facebook_post', 'twitter_header',
        'youtube_thumbnail', 'youtube_channel_art', 'linkedin_banner',
        'business_card', 'flyer', 'poster', 'presentation', 'invitation',
        'certificate', 'logo', 'banner', 'email_header'
    ]
    
    # ============================================
    # VALIDATION
    # ============================================
    def validate(self):
        """Validate required configuration"""
        errors = []
        
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        if not self.API_ID or not self.API_HASH:
            errors.append("API_ID and API_HASH are required")
        if not self.SECRET_KEY:
            errors.append("SECRET_KEY is required")
        if not self.ADMIN_IDS:
            errors.append("ADMIN_IDS is required")
            
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
            
        return True
    
    # ============================================
    # HELPERS
    # ============================================
    @classmethod
    def get_video_quality(cls, quality='720p'):
        """Get video quality settings"""
        return cls.VIDEO_QUALITY_LEVELS.get(quality, cls.VIDEO_QUALITY_LEVELS['720p'])
    
    @classmethod
    def get_compression_settings(cls, level='medium'):
        """Get compression settings"""
        return cls.VIDEO_COMPRESSION_LEVELS.get(level, cls.VIDEO_COMPRESSION_LEVELS['medium'])
    
    @classmethod
    def is_premium_feature(cls, feature_name):
        """Check if feature requires premium"""
        premium_features = [
            '4k', 'neon', 'cartoon', '3d', 'oil_paint', 'glitch', 'sketch',
            'watercolor', 'pixelate', 'thermal', 'background_removal',
            'object_removal', 'face_detection', 'skin_smoothing'
        ]
        return feature_name in premium_features
    
    @classmethod
    def get_premium_price(cls, plan='pro_monthly'):
        """Get premium plan price"""
        return cls.PREMIUM_PLANS.get(plan, {}).get('price', 0)
    
    @classmethod
    def get_user_limits(cls, is_premium=False):
        """Get user limits based on subscription"""
        if is_premium:
            return {
                'video_length': cls.PREMIUM_VIDEO_LENGTH,
                'video_exports': cls.PREMIUM_VIDEO_EXPORTS,
                'image_exports': cls.PREMIUM_IMAGE_EXPORTS,
                'design_exports': cls.PREMIUM_DESIGN_EXPORTS,
                'storage': cls.MAX_TOTAL_STORAGE,
                'max_video_size': cls.MAX_VIDEO_SIZE,
                'max_image_size': cls.MAX_IMAGE_SIZE
            }
        else:
            return {
                'video_length': cls.FREE_VIDEO_LENGTH,
                'video_exports': cls.FREE_VIDEO_EXPORTS,
                'image_exports': cls.FREE_IMAGE_EXPORTS,
                'design_exports': cls.FREE_DESIGN_EXPORTS,
                'storage': 100 * 1024 * 1024,  # 100MB
                'max_video_size': cls.MAX_VIDEO_SIZE,
                'max_image_size': cls.MAX_IMAGE_SIZE
            }

# Create config instance
config = Config()

# Validate on import
try:
    config.validate()
except ValueError as e:
    logging.warning(f"Configuration warning: {e}")
