"""
Configuration Module - All environment variables and settings
Author: @kinva_master
"""

import os
import secrets
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
    WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://kinva-master.com')
    API_URL = os.getenv('API_URL', 'https://api.kinva-master.com')
    WS_URL = os.getenv('WS_URL', 'wss://kinva-master.com')
    
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
    # JWT CONFIGURATION
    # ============================================
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))  # 30 days
    
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
    PREMIUM_MAX_STORAGE = int(os.getenv('PREMIUM_MAX_STORAGE', '10')) * 1024 * 1024 * 1024  # 10GB
    FREE_MAX_STORAGE = int(os.getenv('FREE_MAX_STORAGE', '100')) * 1024 * 1024  # 100MB
    
    # Video quality settings
    VIDEO_QUALITY_LEVELS = {
        '480p': {'width': 854, 'height': 480, 'bitrate': '1000k'},
        '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k'},
        '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k'},
        '4k': {'width': 3840, 'height': 2160, 'bitrate': '15000k'}
    }
    
    VIDEO_COMPRESSION_LEVELS = {
        'low': {'crf': 23, 'preset': 'veryfast', 'target_size': 0.5},
        'medium': {'crf': 28, 'preset': 'faster', 'target_size': 0.3},
        'high': {'crf': 32, 'preset': 'fast', 'target_size': 0.2},
        'ultra': {'crf': 36, 'preset': 'medium', 'target_size': 0.1}
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
    # PREMIUM PLANS (Indian Rupees)
    # ============================================
    PREMIUM_PLANS = {
        'free': {
            'id': 'free',
            'name': 'Free',
            'price': 0,
            'price_inr': 0,
            'interval': 'forever',
            'features': [
                'Basic video editing (60s max)',
                '10 image filters',
                '100+ templates',
                '720p export',
                'Watermark: @kinva_master.com',
                '3 exports/day',
                '100MB storage'
            ]
        },
        'basic': {
            'id': 'basic',
            'name': 'Basic',
            'price': 9.99,
            'price_inr': 499,
            'interval': 'month',
            'features': [
                '1080p video export',
                '20 image filters',
                '500+ templates',
                'No watermark',
                '50 exports/day',
                '5GB storage',
                'Priority support'
            ]
        },
        'pro': {
            'id': 'pro',
            'name': 'Pro',
            'price': 14.99,
            'price_inr': 799,
            'interval': 'month',
            'features': [
                '4K video export',
                'All 30+ image filters',
                '1000+ templates',
                'No watermark',
                'Unlimited exports',
                '10GB storage',
                'Priority support',
                'API access'
            ]
        },
        'pro_yearly': {
            'id': 'pro_yearly',
            'name': 'Pro Yearly',
            'price': 119.99,
            'price_inr': 5999,
            'interval': 'year',
            'features': [
                '4K video export',
                'All 30+ image filters',
                '1000+ templates',
                'No watermark',
                'Unlimited exports',
                '10GB storage',
                'Priority support',
                'API access',
                '2 months free',
                'Save 33%'
            ]
        },
        'business': {
            'id': 'business',
            'name': 'Business',
            'price': 29.99,
            'price_inr': 1499,
            'interval': 'month',
            'features': [
                'Everything in Pro',
                'Team collaboration (5 users)',
                'Custom branding',
                'White-label export',
                'Dedicated support',
                '100GB storage',
                'Analytics dashboard'
            ]
        },
        'enterprise': {
            'id': 'enterprise',
            'name': 'Enterprise',
            'price': 99.99,
            'price_inr': 4999,
            'interval': 'month',
            'features': [
                'Everything in Business',
                'Unlimited team members',
                'Custom development',
                '24/7 dedicated support',
                'On-premise deployment',
                'SLA guarantee 99.99%'
            ]
        }
    }
    
    # ============================================
    # PAYMENT SETTINGS
    # ============================================
    # Stripe (International)
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    # Razorpay (India)
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
    
    # UPI (India)
    UPI_ID = os.getenv('UPI_ID', 'kinvamaster@okhdfcbank')
    MERCHANT_NAME = os.getenv('MERCHANT_NAME', 'Kinva Master')
    MERCHANT_CODE = os.getenv('MERCHANT_CODE', 'KINVA123')
    MERCHANT_VPA = os.getenv('MERCHANT_VPA', 'kinvamaster@okhdfcbank')
    
    # Cryptocurrency
    BTC_WALLET = os.getenv('BTC_WALLET', '')
    ETH_WALLET = os.getenv('ETH_WALLET', '')
    USDT_WALLET = os.getenv('USDT_WALLET', '')
    USDC_WALLET = os.getenv('USDC_WALLET', '')
    LTC_WALLET = os.getenv('LTC_WALLET', '')
    DOGE_WALLET = os.getenv('DOGE_WALLET', '')
    BNB_WALLET = os.getenv('BNB_WALLET', '')
    SOL_WALLET = os.getenv('SOL_WALLET', '')
    MATIC_WALLET = os.getenv('MATIC_WALLET', '')
    XRP_WALLET = os.getenv('XRP_WALLET', '')
    
    # Blockchain API Keys
    ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
    BSCSCAN_API_KEY = os.getenv('BSCSCAN_API_KEY', '')
    POLYGONSCAN_API_KEY = os.getenv('POLYGONSCAN_API_KEY', '')
    
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
    # reCAPTCHA
    # ============================================
    RECAPTCHA_ENABLED = os.getenv('RECAPTCHA_ENABLED', 'True').lower() == 'true'
    RECAPTCHA_SITE_KEY_V2 = os.getenv('RECAPTCHA_SITE_KEY_V2', '')
    RECAPTCHA_SECRET_KEY_V2 = os.getenv('RECAPTCHA_SECRET_KEY_V2', '')
    RECAPTCHA_SITE_KEY_V3 = os.getenv('RECAPTCHA_SITE_KEY_V3', '')
    RECAPTCHA_SECRET_KEY_V3 = os.getenv('RECAPTCHA_SECRET_KEY_V3', '')
    RECAPTCHA_MIN_SCORE = float(os.getenv('RECAPTCHA_MIN_SCORE', '0.5'))
    
    # ============================================
    # ANALYTICS
    # ============================================
    ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'True').lower() == 'true'
    ANALYTICS_WRITE_KEY = os.getenv('ANALYTICS_WRITE_KEY', '')
    
    # ============================================
    # CDN
    # ============================================
    CDN_URL = os.getenv('CDN_URL', '')
    CDN_ENABLED = os.getenv('CDN_ENABLED', 'False').lower() == 'true'
    
    # ============================================
    # BACKUP
    # ============================================
    BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'True').lower() == 'true'
    BACKUP_INTERVAL = int(os.getenv('BACKUP_INTERVAL', '24'))  # hours
    BACKUP_RETENTION = int(os.getenv('BACKUP_RETENTION', '30'))  # days
    
    # ============================================
    # MAINTENANCE
    # ============================================
    MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'False').lower() == 'true'
    MAINTENANCE_MESSAGE = os.getenv('MAINTENANCE_MESSAGE', 'Under maintenance. Please check back later.')
    
    # ============================================
    # HELPER METHODS
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
            'object_removal', 'face_detection', 'skin_smoothing', 'no_watermark'
        ]
        return feature_name in premium_features
    
    @classmethod
    def get_premium_price(cls, plan='pro'):
        """Get premium plan price"""
        return cls.PREMIUM_PLANS.get(plan, {}).get('price', 0)
    
    @classmethod
    def get_premium_price_inr(cls, plan='pro'):
        """Get premium plan price in INR"""
        return cls.PREMIUM_PLANS.get(plan, {}).get('price_inr', 0)
    
    @classmethod
    def get_user_limits(cls, is_premium=False, plan='free'):
        """Get user limits based on subscription"""
        if is_premium:
            plan_data = cls.PREMIUM_PLANS.get(plan, cls.PREMIUM_PLANS['pro'])
            return {
                'video_length': cls.PREMIUM_VIDEO_LENGTH,
                'video_exports': cls.PREMIUM_VIDEO_EXPORTS,
                'image_exports': cls.PREMIUM_IMAGE_EXPORTS,
                'design_exports': cls.PREMIUM_DESIGN_EXPORTS,
                'storage': cls.PREMIUM_MAX_STORAGE,
                'max_video_size': cls.MAX_VIDEO_SIZE,
                'max_image_size': cls.MAX_IMAGE_SIZE
            }
        else:
            return {
                'video_length': cls.FREE_VIDEO_LENGTH,
                'video_exports': cls.FREE_VIDEO_EXPORTS,
                'image_exports': cls.FREE_IMAGE_EXPORTS,
                'design_exports': cls.FREE_DESIGN_EXPORTS,
                'storage': cls.FREE_MAX_STORAGE,
                'max_video_size': cls.MAX_VIDEO_SIZE,
                'max_image_size': cls.MAX_IMAGE_SIZE
            }
    
    @classmethod
    def is_maintenance_mode(cls):
        """Check if maintenance mode is enabled"""
        return cls.MAINTENANCE_MODE
    
    @classmethod
    def get_maintenance_message(cls):
        """Get maintenance mode message"""
        return cls.MAINTENANCE_MESSAGE
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        if not cls.API_ID or not cls.API_HASH:
            errors.append("API_ID and API_HASH are required")
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY is required")
        if not cls.ADMIN_IDS:
            errors.append("ADMIN_IDS is required")
        
        # Payment validation (optional, show warnings)
        if cls.ENABLE_PREMIUM:
            if not cls.STRIPE_SECRET_KEY and not cls.RAZORPAY_KEY_SECRET:
                import logging
                logging.warning("No payment gateway configured. Premium features will be disabled.")
        
        # reCAPTCHA validation
        if cls.RECAPTCHA_ENABLED:
            if not cls.RECAPTCHA_SITE_KEY_V3 or not cls.RECAPTCHA_SECRET_KEY_V3:
                import logging
                logging.warning("reCAPTCHA enabled but keys not configured. Bot protection will be disabled.")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True


# Create config instance
config = Config()

# Validate on import
try:
    config.validate()
except ValueError as e:
    import logging
    logging.warning(f"Configuration warning: {e}")
