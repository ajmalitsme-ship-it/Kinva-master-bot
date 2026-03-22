#!/bin/bash
# ============================================
# KINVA MASTER - SETUP SCRIPT (FULLY FIXED)
# ============================================

echo "🎬 KINVA MASTER - Setup Script"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_info() { echo -e "${BLUE}[i]${NC} $1"; }

# ============================================
# CHECK PYTHON VERSION
# ============================================
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_status "Python $python_version detected"
else
    print_error "Python 3.8+ required. Found $python_version"
    exit 1
fi

# ============================================
# CREATE VIRTUAL ENVIRONMENT
# ============================================
print_info "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
else
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# ============================================
# UPGRADE PIP
# ============================================
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_status "Pip upgraded"

# ============================================
# INSTALL DEPENDENCIES
# ============================================
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_status "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
else
    print_error "requirements.txt not found"
    exit 1
fi

# ============================================
# CREATE DIRECTORY STRUCTURE
# ============================================
print_info "Creating directory structure..."

mkdir -p uploads/{images,videos,audio,designs,projects,temp,archives}
mkdir -p outputs/{images,videos,audio,gifs,designs}
mkdir -p logs
mkdir -p data/{templates,presets,cache,backups}
mkdir -p static/css/themes
mkdir -p static/js/lib
mkdir -p static/images/{icons,backgrounds,templates}
mkdir -p fonts
mkdir -p temp
mkdir -p thumbnails

print_status "Directories created"

# ============================================
# CREATE ALL __init__.py FILES (CRITICAL FIX!)
# ============================================
print_info "Creating __init__.py files..."

# Create src directory if not exists
mkdir -p src
mkdir -p src/utils
mkdir -p src/handlers
mkdir -p src/processors
mkdir -p src/editors
mkdir -p src/payment
mkdir -p src/api

# Create src/__init__.py
cat > src/__init__.py << 'EOF'
"""
Kinva Master - Main Package
Author: @kinva_master
"""
__version__ = "1.0.0"
__author__ = "Kinva Master"
__license__ = "MIT"
EOF
print_status "Created src/__init__.py"

# Create src/utils/__init__.py (MOST IMPORTANT - FIXES THE ERROR!)
cat > src/utils/__init__.py << 'EOF'
"""
Utils Package - Utility functions and helpers
Author: @kinva_master
"""
from .helpers import (
    allowed_file,
    format_size,
    get_file_info,
    format_file_size,
    get_file_extension,
    secure_filename,
    slugify,
    generate_uuid,
    time_ago,
    cleanup_file,
    get_temp_file,
    generate_random_string,
    generate_secure_token
)

from .validators import (
    is_valid_email,
    is_valid_username,
    validate_password_strength,
    is_valid_url
)

from .decorators import (
    require_auth,
    require_premium,
    require_admin,
    rate_limit
)

from .logger import setup_logger, get_logger, log_error

from .rate_limiter import RateLimiter, rate_limit_ip, rate_limit_user

__all__ = [
    'allowed_file', 'format_size', 'get_file_info', 'format_file_size',
    'get_file_extension', 'secure_filename', 'slugify', 'generate_uuid',
    'time_ago', 'cleanup_file', 'get_temp_file', 'generate_random_string',
    'generate_secure_token',
    'is_valid_email', 'is_valid_username', 'validate_password_strength', 'is_valid_url',
    'require_auth', 'require_premium', 'require_admin', 'rate_limit',
    'setup_logger', 'get_logger', 'log_error',
    'RateLimiter', 'rate_limit_ip', 'rate_limit_user'
]
EOF
print_status "Created src/utils/__init__.py (CRITICAL FIX!)"

# Create src/handlers/__init__.py
cat > src/handlers/__init__.py << 'EOF'
"""
Handlers Package - Telegram Bot Handlers
Author: @kinva_master
"""
from .start import StartHandler
from .video import VideoHandler
from .image import ImageHandler
from .design import DesignHandler
from .premium import PremiumHandler
from .admin import AdminHandler
from .callback import CallbackHandler
from .error import ErrorHandler

__all__ = [
    'StartHandler', 'VideoHandler', 'ImageHandler', 'DesignHandler',
    'PremiumHandler', 'AdminHandler', 'CallbackHandler', 'ErrorHandler'
]
EOF
print_status "Created src/handlers/__init__.py"

# Create src/processors/__init__.py
cat > src/processors/__init__.py << 'EOF'
"""
Processors Package - Video, Image, Audio Processing Modules
Author: @kinva_master
"""
from .video_processor import VideoProcessor, video_processor
from .image_processor import ImageProcessor, image_processor
from .audio_processor import AudioProcessor, audio_processor
from .watermark import Watermark, watermark
from .compression import CompressionProcessor, compression_processor
from .effects import EffectsProcessor, effects_processor
from .filters import FiltersProcessor, filters_processor

__all__ = [
    'VideoProcessor', 'video_processor',
    'ImageProcessor', 'image_processor',
    'AudioProcessor', 'audio_processor',
    'Watermark', 'watermark',
    'CompressionProcessor', 'compression_processor',
    'EffectsProcessor', 'effects_processor',
    'FiltersProcessor', 'filters_processor'
]
EOF
print_status "Created src/processors/__init__.py"

# Create src/editors/__init__.py
cat > src/editors/__init__.py << 'EOF'
"""
Editors Package - Canva, Video, Image Editors
Author: @kinva_master
"""
from .canva_editor import CanvaEditor, canva_editor
from .video_editor import VideoEditor, video_editor
from .image_editor import ImageEditor, image_editor
from .timeline import Timeline, timeline
from .layers import LayerManager, layer_manager

__all__ = [
    'CanvaEditor', 'canva_editor',
    'VideoEditor', 'video_editor',
    'ImageEditor', 'image_editor',
    'Timeline', 'timeline',
    'LayerManager', 'layer_manager'
]
EOF
print_status "Created src/editors/__init__.py"

# Create src/payment/__init__.py
cat > src/payment/__init__.py << 'EOF'
"""
Payment Package - Payment processing modules
Author: @kinva_master
"""
from .stripe_handler import StripeHandler, stripe_handler
from .razorpay_handler import RazorpayHandler, razorpay_handler
from .upi_handler import UPIHandler, upi_handler
from .crypto_handler import CryptoHandler, crypto_handler
from .subscription import SubscriptionManager, subscription_manager

__all__ = [
    'StripeHandler', 'stripe_handler',
    'RazorpayHandler', 'razorpay_handler',
    'UPIHandler', 'upi_handler',
    'CryptoHandler', 'crypto_handler',
    'SubscriptionManager', 'subscription_manager'
]
EOF
print_status "Created src/payment/__init__.py"

# Create src/api/__init__.py
cat > src/api/__init__.py << 'EOF'
"""
API Package - REST API endpoints
Author: @kinva_master
"""
from .auth import auth_bp
from .users import users_bp
from .videos import videos_bp
from .images import images_bp
from .designs import designs_bp
from .payments import payments_bp
from .templates import templates_bp
from .admin import admin_bp
from .webhooks import webhooks_bp
from .recaptcha import recaptcha_bp

__all__ = [
    'auth_bp', 'users_bp', 'videos_bp', 'images_bp',
    'designs_bp', 'payments_bp', 'templates_bp',
    'admin_bp', 'webhooks_bp', 'recaptcha_bp'
]
EOF
print_status "Created src/api/__init__.py"

# Verify all __init__.py files exist
print_info "Verifying __init__.py files..."
echo ""
ls -la src/__init__.py
ls -la src/utils/__init__.py
ls -la src/handlers/__init__.py
ls -la src/processors/__init__.py
ls -la src/editors/__init__.py
ls -la src/payment/__init__.py
ls -la src/api/__init__.py
echo ""

print_status "All __init__.py files created successfully"

# ============================================
# CREATE .env FILE
# ============================================
print_info "Checking environment file..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cat > .env << 'EOF'
# Telegram API Credentials (from https://my.telegram.org)
API_ID=1234567
API_HASH=your_api_hash_here

# Telegram Bot Token (from @BotFather)
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=@kinva_master_bot

# Web App URL
WEBAPP_URL=http://localhost:5000

# Admin Configuration
ADMIN_IDS=123456789
ADMIN_CONTACT=@kinva_master

# App Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=5000

# Database
DATABASE_URL=sqlite:///kinva_master.db

# Premium Pricing
PREMIUM_PRICE_INR=499
PREMIUM_PRICE_USD=14.99

# Watermark
WATERMARK_TEXT=@kinva_master.com
WATERMARK_OPACITY=0.5
WATERMARK_POSITION=bottom-right
EOF
    print_status ".env file created"
    print_warning "Please edit .env file with your credentials"
else
    print_status ".env file found"
fi

# ============================================
# DOWNLOAD BASIC FONTS
# ============================================
print_info "Downloading fonts..."
python -c "
import os
import requests
from pathlib import Path

fonts_dir = Path('fonts')
fonts_dir.mkdir(exist_ok=True)

fonts = [
    ('Roboto-Regular.ttf', 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf'),
    ('Roboto-Bold.ttf', 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Bold.ttf'),
    ('OpenSans-Regular.ttf', 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Regular.ttf'),
    ('OpenSans-Bold.ttf', 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Bold.ttf'),
    ('Poppins-Regular.ttf', 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf'),
    ('Poppins-Bold.ttf', 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf'),
]

for font_name, url in fonts:
    try:
        response = requests.get(url, timeout=10)
        with open(fonts_dir / font_name, 'wb') as f:
            f.write(response.content)
        print(f'✅ Downloaded {font_name}')
    except Exception as e:
        print(f'❌ Failed to download {font_name}: {e}')
"
print_status "Fonts downloaded"

# ============================================
# INITIALIZE DATABASE
# ============================================
print_info "Initializing database..."
python -c "
import sqlite3
conn = sqlite3.connect('kinva_master.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        is_premium BOOLEAN DEFAULT 0,
        premium_until TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS designs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        design_data TEXT,
        thumbnail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        file_path TEXT,
        thumbnail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        file_path TEXT,
        thumbnail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        payment_id TEXT UNIQUE,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print('✅ Database initialized')
"
print_status "Database initialized"

# ============================================
# CREATE LOG FILES
# ============================================
print_info "Creating log files..."
touch logs/app.log
touch logs/bot.log
touch logs/error.log
print_status "Log files created"

# ============================================
# SETUP COMPLETE
# ============================================
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Edit the .env file with your credentials:"
echo "   nano .env"
echo ""
echo "2. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the web application:"
echo "   python src/app.py"
echo ""
echo "4. Run the Telegram bot (in another terminal):"
echo "   python src/bot.py"
echo ""
echo "5. Open your browser:"
echo "   http://localhost:5000"
echo ""
echo "📊 Default admin:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📞 Contact: @kinva_master for support"
echo "🌐 Website: https://kinva-master.com"
echo "=========================================="
