#!/bin/bash

# ============================================
# KINVA MASTER - SETUP SCRIPT
# ============================================

echo "🎬 𝐊ɪɴᴠᴀ 𝐌ᴀꜱᴛᴇʀ ᴀʟɪᴠᴇ"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================
# CHECK SYSTEM REQUIREMENTS
# ============================================

print_info "Checking system requirements..."

# Check Python version
if command_exists python3; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python $python_version detected"
    
    # Check Python version is 3.8+
    required_version="3.8.0"
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
        print_status "Python version meets requirements (>=3.8)"
    else
        print_error "Python version $python_version is too old. Please upgrade to Python 3.8+"
        exit 1
    fi
else
    print_error "Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check pip
if command_exists pip3; then
    print_status "pip3 detected"
else
    print_warning "pip3 not found. Installing..."
    python3 -m ensurepip --upgrade
fi

# Check FFmpeg
if command_exists ffmpeg; then
    ffmpeg_version=$(ffmpeg -version | head -n1 | awk '{print $3}')
    print_status "FFmpeg $ffmpeg_version detected"
else
    print_warning "FFmpeg not found. Please install FFmpeg for video processing"
    print_info "On Ubuntu/Debian: sudo apt-get install ffmpeg"
    print_info "On macOS: brew install ffmpeg"
    print_info "On Windows: Download from ffmpeg.org"
fi

echo ""
print_info "Creating virtual environment..."

# ============================================
# CREATE VIRTUAL ENVIRONMENT
# ============================================

# Check if virtual environment already exists
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_status "Virtual environment recreated"
    else
        print_status "Using existing virtual environment"
    fi
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

echo ""
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_status "Pip upgraded"

# ============================================
# INSTALL DEPENDENCIES
# ============================================

echo ""
print_info "Installing Python dependencies..."

# Check if requirements.txt exists
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

echo ""
print_info "Creating directory structure..."

# Create main directories
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
# DOWNLOAD FONTS
# ============================================

echo ""
print_info "Downloading fonts..."

# Create Python script to download fonts
cat > /tmp/download_fonts.py << 'EOF'
import os
import requests
from pathlib import Path

fonts_dir = Path('fonts')
fonts_dir.mkdir(exist_ok=True)

# List of fonts to download
fonts = [
    ('Roboto-Regular.ttf', 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf'),
    ('Roboto-Bold.ttf', 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Bold.ttf'),
    ('Roboto-Italic.ttf', 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Italic.ttf'),
    ('OpenSans-Regular.ttf', 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Regular.ttf'),
    ('OpenSans-Bold.ttf', 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Bold.ttf'),
    ('Poppins-Regular.ttf', 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf'),
    ('Poppins-Bold.ttf', 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf'),
    ('Montserrat-Regular.ttf', 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Regular.ttf'),
    ('Montserrat-Bold.ttf', 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf'),
    ('Lato-Regular.ttf', 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf'),
    ('Lato-Bold.ttf', 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf'),
]

print("Downloading fonts...")
for font_name, url in fonts:
    try:
        response = requests.get(url, timeout=10)
        with open(fonts_dir / font_name, 'wb') as f:
            f.write(response.content)
        print(f'  ✓ Downloaded {font_name}')
    except Exception as e:
        print(f'  ✗ Failed to download {font_name}: {e}')

print("Font download complete!")
EOF

# Run the font download script
python /tmp/download_fonts.py
rm /tmp/download_fonts.py

print_status "Fonts downloaded"

# ============================================
# INITIALIZE DATABASE
# ============================================

echo ""
print_info "Initializing database..."

# Create database initialization script
cat > /tmp/init_db.py << 'EOF'
import sqlite3
import os

db_path = 'kinva_master.db'

# Remove existing database if it exists
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create users table
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

# Create designs table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS designs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        design_data TEXT,
        thumbnail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# Create videos table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        file_path TEXT,
        thumbnail TEXT,
        duration REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# Create images table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        file_path TEXT,
        thumbnail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# Create payments table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        currency TEXT DEFAULT 'USD',
        payment_id TEXT UNIQUE,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

conn.commit()
conn.close()

print("Database initialized successfully")
EOF

# Run the database initialization script
python /tmp/init_db.py
rm /tmp/init_db.py

print_status "Database initialized"

# ============================================
# CHECK ENVIRONMENT FILE
# ============================================

echo ""
print_info "Checking environment file..."

if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status ".env file created from .env.example"
        print_warning "Please edit .env file with your credentials"
    else
        print_info "Creating .env file from template..."
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
    fi
else
    print_status ".env file found"
fi

# ============================================
# CREATE LOG FILES
# ============================================

echo ""
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
echo "   http://Kinv-master.com"
echo ""
echo "📊 Default admin (if using email login):"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📞 Contact: @kinva_master for support"
echo "🌐 Website: https://kinva-master.com"
echo "=========================================="
