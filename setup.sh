#!/bin/bash

# ============================================
# KINVA MASTER - SETUP SCRIPT
# ============================================

echo "🎬 KINVA MASTER - Setup Script"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_status "Python $python_version detected"
else
    print_error "Python 3.11+ required. Found $python_version"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
else
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_status "Pip upgraded"

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p uploads/{images,videos,designs,temp}
mkdir -p outputs/{images,videos,designs}
mkdir -p logs
mkdir -p data/{templates,presets,cache}
mkdir -p fonts
mkdir -p static/images/{icons,backgrounds,templates}
mkdir -p static/css/themes
mkdir -p static/js/lib
print_status "Directories created"

# Check .env file
echo "🔐 Checking environment file..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your credentials"
else
    print_status ".env file found"
fi

# Download fonts
echo "🎨 Downloading fonts..."
if [ -f "fonts/download_fonts.py" ]; then
    python fonts/download_fonts.py
else
    print_warning "Font downloader not found"
fi

# Initialize database
echo "🗄️ Initializing database..."
python -c "
import sqlite3
conn = sqlite3.connect('kinva_master.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        file_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print('Database initialized')
"
print_status "Database initialized"

# Create admin user
echo "👑 Creating admin user..."
python -c "
import sqlite3
conn = sqlite3.connect('kinva_master.db')
cursor = conn.cursor()
cursor.execute('''
    INSERT OR IGNORE INTO users (telegram_id, username, is_premium)
    VALUES (?, ?, ?)
''', (123456789, 'admin', True))
conn.commit()
conn.close()
"
print_status "Admin user created"

# Setup complete
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run the web app: python src/app.py"
echo "3. Run the bot: python src/bot.py"
echo "4. Open browser: http://localhost:5000"
echo ""
echo "📊 Default admin:"
echo "   Telegram ID: 123456789"
echo ""
echo "📞 Contact: @kinva_master for support"
echo "=================================="
