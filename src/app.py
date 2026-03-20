"""
Kinva Master - Main Flask Web Application
Complete Video & Image Editing Platform
Author: @kinva_master
"""

import os
import json
import uuid
import logging
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from io import BytesIO
import traceback

from flask import (
    Flask, render_template, request, jsonify, 
    send_file, session, redirect, url_for, flash,
    make_response, abort, g
)
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import cv2
import numpy as np

# Import local modules
from .config import Config
from .database import Database
from .models import User, Design, Video, Image as ImageModel
from .processors.video_processor import VideoProcessor
from .processors.image_processor import ImageProcessor
from .processors.watermark import Watermark
from .editors.canva_editor import CanvaEditor
from .editors.video_editor import VideoEditor
from .editors.image_editor import ImageEditor
from .payment.stripe_handler import StripeHandler
from .utils.helpers import allowed_file, format_size, get_file_info
from .utils.logger import setup_logger

# Initialize
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_DIR
app.config['OUTPUT_FOLDER'] = Config.OUTPUT_DIR

# CORS
CORS(app, supports_credentials=True)

# SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize components
db = Database()
video_processor = VideoProcessor()
image_processor = ImageProcessor()
watermark = Watermark()
canva_editor = CanvaEditor()
video_editor = VideoEditor()
image_editor = ImageEditor()
stripe_handler = StripeHandler()

# Setup logger
logger = setup_logger(__name__)

# ============================================
# DECORATORS
# ============================================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def premium_required(f):
    """Decorator to require premium"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        
        user = db.get_user(session['user_id'])
        if not user or not user.get('is_premium'):
            return jsonify({'error': 'Premium subscription required'}), 403
        
        # Check if premium expired
        if user.get('premium_until'):
            premium_until = datetime.fromisoformat(user['premium_until'])
            if premium_until < datetime.now():
                db.update_user_premium(session['user_id'], is_premium=False)
                return jsonify({'error': 'Premium subscription expired'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        
        user = db.get_user(session['user_id'])
        if not user or user.get('telegram_id') not in Config.ADMIN_IDS:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ROUTES - PAGES
# ============================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user = db.get_user(session['user_id'])
    stats = db.get_user_stats(session['user_id'])
    recent_projects = db.get_user_projects(session['user_id'], limit=6)
    
    # Weekly stats for chart
    weekly_data = db.get_weekly_stats(session['user_id'])
    
    return render_template('dashboard.html', 
                         user=user, 
                         stats=stats, 
                         recent_projects=recent_projects,
                         weekly_data=weekly_data)

@app.route('/editor')
@login_required
def editor():
    """Canva-style design editor"""
    user = db.get_user(session['user_id'])
    templates = db.get_templates(limit=12)
    
    return render_template('editor.html', 
                         user=user, 
                         templates=templates)

@app.route('/video-editor')
@login_required
def video_editor_page():
    """Video editor page"""
    user = db.get_user(session['user_id'])
    videos = db.get_user_videos(session['user_id'], limit=10)
    
    return render_template('video-editor.html', 
                         user=user, 
                         videos=videos)

@app.route('/image-editor')
@login_required
def image_editor_page():
    """Image editor page"""
    user = db.get_user(session['user_id'])
    images = db.get_user_images(session['user_id'], limit=10)
    
    return render_template('image-editor.html', 
                         user=user, 
                         images=images)

@app.route('/templates')
def templates_page():
    """Templates gallery"""
    category = request.args.get('category', 'all')
    templates = db.get_templates(category=category)
    categories = db.get_template_categories()
    
    return render_template('templates.html', 
                         templates=templates, 
                         categories=categories,
                         current_category=category)

@app.route('/premium')
def premium_page():
    """Premium plans page"""
    plans = Config.PREMIUM_PLANS
    
    return render_template('premium.html', plans=plans)

@app.route('/profile')
@login_required
def profile_page():
    """User profile page"""
    user = db.get_user(session['user_id'])
    stats = db.get_user_stats(session['user_id'])
    
    return render_template('profile.html', user=user, stats=stats)

@app.route('/settings')
@login_required
def settings_page():
    """User settings page"""
    user = db.get_user(session['user_id'])
    settings = db.get_user_settings(session['user_id'])
    
    return render_template('settings.html', user=user, settings=settings)

@app.route('/my-works')
@login_required
def my_works():
    """My works page"""
    user = db.get_user(session['user_id'])
    designs = db.get_user_designs(session['user_id'])
    videos = db.get_user_videos(session['user_id'])
    images = db.get_user_images(session['user_id'])
    
    return render_template('my-works.html', 
                         user=user, 
                         designs=designs, 
                         videos=videos, 
                         images=images)

@app.route('/history')
@login_required
def history():
    """Export history page"""
    user = db.get_user(session['user_id'])
    exports = db.get_user_exports(session['user_id'])
    
    return render_template('history.html', user=user, exports=exports)

@app.route('/help')
def help_page():
    """Help & support page"""
    return render_template('help.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@app.route('/terms')
def terms():
    """Terms of service"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html')

@app.route('/login')
def login_page():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Register page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/admin')
@admin_required
def admin_page():
    """Admin dashboard"""
    stats = db.get_admin_stats()
    users = db.get_all_users(limit=50)
    payments = db.get_all_payments(limit=50)
    
    return render_template('admin.html', 
                         stats=stats, 
                         users=users, 
                         payments=payments)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# ============================================
# API ENDPOINTS - AUTH
# ============================================

@app.route('/api/auth/telegram', methods=['POST'])
def auth_telegram():
    """Authenticate with Telegram"""
    try:
        data = request.json
        telegram_data = data.get('telegram_data')
        
        if not telegram_data:
            return jsonify({'error': 'No telegram data'}), 400
        
        # Verify Telegram data hash
        hash_key = telegram_data.get('hash')
        if not verify_telegram_hash(telegram_data):
            return jsonify({'error': 'Invalid hash'}), 401
        
        # Get or create user
        user = db.get_or_create_user(
            telegram_id=telegram_data['id'],
            username=telegram_data.get('username'),
            first_name=telegram_data.get('first_name'),
            last_name=telegram_data.get('last_name')
        )
        
        # Set session
        session['user_id'] = user['id']
        session['telegram_id'] = user['telegram_id']
        session['is_premium'] = user['is_premium']
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'first_name': user['first_name'],
                'is_premium': user['is_premium']
            }
        })
        
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Email/password login"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        user = db.get_user_by_email(email)
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        session['user_id'] = user['id']
        session['is_premium'] = user['is_premium']
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'is_premium': user['is_premium']
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """Email/password registration"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Check if user exists
        if db.get_user_by_email(email):
            return jsonify({'error': 'Email already registered'}), 400
        
        if db.get_user_by_username(username):
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create user
        user = db.create_user(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        session['user_id'] = user['id']
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me')
@login_required
def auth_me():
    """Get current user"""
    user = db.get_user(session['user_id'])
    return jsonify(user)

# ============================================
# API ENDPOINTS - USERS
# ============================================

@app.route('/api/users/profile')
@login_required
def get_profile():
    """Get user profile"""
    user = db.get_user(session['user_id'])
    stats = db.get_user_stats(session['user_id'])
    
    return jsonify({
        'user': user,
        'stats': stats
    })

@app.route('/api/users/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.json
    user = db.update_user(session['user_id'], data)
    return jsonify(user)

@app.route('/api/users/settings')
@login_required
def get_settings():
    """Get user settings"""
    settings = db.get_user_settings(session['user_id'])
    return jsonify(settings)

@app.route('/api/users/settings', methods=['PUT'])
@login_required
def update_settings():
    """Update user settings"""
    data = request.json
    settings = db.update_user_settings(session['user_id'], data)
    return jsonify(settings)

@app.route('/api/users/stats')
@login_required
def get_stats():
    """Get user statistics"""
    stats = db.get_user_stats(session['user_id'])
    return jsonify(stats)

# ============================================
# API ENDPOINTS - DESIGNS
# ============================================

@app.route('/api/designs')
@login_required
def get_designs():
    """Get user designs"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    designs = db.get_user_designs(session['user_id'], page=page, limit=limit)
    return jsonify(designs)

@app.route('/api/designs/<int:design_id>')
@login_required
def get_design(design_id):
    """Get specific design"""
    design = db.get_design(design_id)
    if design and design['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(design)

@app.route('/api/designs', methods=['POST'])
@login_required
def create_design():
    """Create new design"""
    data = request.json
    
    design_id = db.create_design(
        user_id=session['user_id'],
        title=data.get('title', 'Untitled'),
        design_data=data.get('design_data', {}),
        thumbnail=data.get('thumbnail'),
        width=data.get('width', 1920),
        height=data.get('height', 1080)
    )
    
    return jsonify({'id': design_id, 'success': True})

@app.route('/api/designs/<int:design_id>', methods=['PUT'])
@login_required
def update_design(design_id):
    """Update design"""
    data = request.json
    
    design = db.get_design(design_id)
    if not design or design['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.update_design(design_id, data)
    return jsonify({'success': True})

@app.route('/api/designs/<int:design_id>', methods=['DELETE'])
@login_required
def delete_design(design_id):
    """Delete design"""
    design = db.get_design(design_id)
    if not design or design['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.delete_design(design_id)
    return jsonify({'success': True})

@app.route('/api/designs/export', methods=['POST'])
@login_required
def export_design():
    """Export design as image"""
    try:
        data = request.json
        design_data = data.get('design_data', {})
        format_type = data.get('format', 'png')
        
        # Check export limit
        user = db.get_user(session['user_id'])
        if not user['is_premium']:
            stats = db.get_user_stats(session['user_id'])
            if stats['exports_today'] >= Config.FREE_EXPORTS:
                return jsonify({'error': 'Daily export limit reached'}), 403
        
        # Render design
        image = canva_editor.render(design_data)
        
        # Add watermark for free users
        if not user['is_premium']:
            image = watermark.add_text_watermark(image)
        
        # Save to output
        filename = f"design_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(Config.OUTPUT_DIR, filename)
        image.save(filepath, format=format_type.upper())
        
        # Save to database
        db.save_export(
            user_id=session['user_id'],
            type='design',
            file_path=filepath,
            size=os.path.getsize(filepath)
        )
        
        # Increment export count
        db.increment_exports(session['user_id'])
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Export design error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# API ENDPOINTS - VIDEOS
# ============================================

@app.route('/api/videos')
@login_required
def get_videos():
    """Get user videos"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    videos = db.get_user_videos(session['user_id'], page=page, limit=limit)
    return jsonify(videos)

@app.route('/api/videos/upload', methods=['POST'])
@login_required
def upload_video():
    """Upload video file"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, Config.ALLOWED_VIDEOS):
            return jsonify({'error': 'Invalid file format'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        user = db.get_user(session['user_id'])
        max_size = Config.PREMIUM_MAX_VIDEO_SIZE if user['is_premium'] else Config.MAX_VIDEO_SIZE
        
        if size > max_size:
            return jsonify({'error': f'File too large. Max size: {max_size // (1024*1024)}MB'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_id = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(Config.UPLOAD_DIR, file_id)
        file.save(filepath)
        
        # Get video info
        info = get_file_info(filepath)
        
        # Check duration
        if not user['is_premium'] and info.get('duration', 0) > Config.FREE_VIDEO_LENGTH:
            os.remove(filepath)
            return jsonify({'error': f'Free users can only edit videos up to {Config.FREE_VIDEO_LENGTH} seconds'}), 403
        
        # Save to database
        video_id = db.save_video(
            user_id=session['user_id'],
            title=filename,
            file_path=filepath,
            duration=info.get('duration'),
            width=info.get('width'),
            height=info.get('height'),
            file_size=size,
            format=info.get('format')
        )
        
        return jsonify({
            'success': True,
            'id': video_id,
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Video upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<int:video_id>')
@login_required
def get_video(video_id):
    """Get video details"""
    video = db.get_video(video_id)
    if not video or video['user_id'] != session['user_id']:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(video)

@app.route('/api/videos/<int:video_id>', methods=['DELETE'])
@login_required
def delete_video(video_id):
    """Delete video"""
    video = db.get_video(video_id)
    if not video or video['user_id'] != session['user_id']:
        return jsonify({'error': 'Not found'}), 404
    
    # Delete file
    if os.path.exists(video['file_path']):
        os.remove(video['file_path'])
    
    db.delete_video(video_id)
    return jsonify({'success': True})

@app.route('/api/videos/process', methods=['POST'])
@login_required
def process_video():
    """Process video with effects"""
    try:
        data = request.json
        video_id = data.get('video_id')
        effects = data.get('effects', [])
        filters = data.get('filters', [])
        transitions = data.get('transitions', [])
        quality = data.get('quality', '720p')
        
        # Get video
        video = db.get_video(video_id)
        if not video or video['user_id'] != session['user_id']:
            return jsonify({'error': 'Video not found'}), 404
        
        # Check premium for quality
        user = db.get_user(session['user_id'])
        if quality == '1080p' and not user['is_premium']:
            quality = '720p'
        elif quality == '4k' and not user['is_premium']:
            return jsonify({'error': '4K export requires premium subscription'}), 403
        
        # Process video
        output_path = video_processor.process(
            video['file_path'],
            effects=effects,
            filters=filters,
            transitions=transitions,
            quality=quality
        )
        
        # Add watermark for free users
        if not user['is_premium']:
            output_path = watermark.add_video_watermark(output_path)
        
        # Save to database
        export_id = db.save_export(
            user_id=session['user_id'],
            type='video',
            file_path=output_path,
            size=os.path.getsize(output_path)
        )
        
        # Increment export count
        db.increment_exports(session['user_id'])
        
        return send_file(output_path, as_attachment=True, download_name=f"processed_{video['title']}")
        
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/compress', methods=['POST'])
@login_required
def compress_video():
    """Compress video"""
    try:
        data = request.json
        video_id = data.get('video_id')
        level = data.get('level', 'medium')
        
        # Check premium
        user = db.get_user(session['user_id'])
        if not user['is_premium'] and level == 'high':
            return jsonify({'error': 'High compression requires premium'}), 403
        
        # Get video
        video = db.get_video(video_id)
        if not video or video['user_id'] != session['user_id']:
            return jsonify({'error': 'Video not found'}), 404
        
        # Compress
        output_path = video_processor.compress(video['file_path'], level=level)
        
        # Add watermark
        if not user['is_premium']:
            output_path = watermark.add_video_watermark(output_path)
        
        return send_file(output_path, as_attachment=True, download_name=f"compressed_{video['title']}")
        
    except Exception as e:
        logger.error(f"Video compression error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/merge', methods=['POST'])
@login_required
def merge_videos():
    """Merge multiple videos"""
    try:
        data = request.json
        video_ids = data.get('video_ids', [])
        
        # Check premium
        user = db.get_user(session['user_id'])
        if not user['is_premium']:
            return jsonify({'error': 'Video merge requires premium'}), 403
        
        # Get videos
        videos = []
        for video_id in video_ids:
            video = db.get_video(video_id)
            if video and video['user_id'] == session['user_id']:
                videos.append(video['file_path'])
        
        if len(videos) < 2:
            return jsonify({'error': 'Need at least 2 videos to merge'}), 400
        
        # Merge videos
        output_path = video_processor.merge(videos)
        
        return send_file(output_path, as_attachment=True, download_name="merged_video.mp4")
        
    except Exception as e:
        logger.error(f"Video merge error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# API ENDPOINTS - IMAGES
# ============================================

@app.route('/api/images')
@login_required
def get_images():
    """Get user images"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    images = db.get_user_images(session['user_id'], page=page, limit=limit)
    return jsonify(images)

@app.route('/api/images/upload', methods=['POST'])
@login_required
def upload_image():
    """Upload image file"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, Config.ALLOWED_IMAGES):
            return jsonify({'error': 'Invalid file format'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > Config.MAX_IMAGE_SIZE:
            return jsonify({'error': f'File too large. Max size: {Config.MAX_IMAGE_SIZE // (1024*1024)}MB'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_id = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(Config.UPLOAD_DIR, file_id)
        file.save(filepath)
        
        # Get image info
        img = Image.open(filepath)
        info = {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode
        }
        
        # Save to database
        image_id = db.save_image(
            user_id=session['user_id'],
            title=filename,
            file_path=filepath,
            width=img.width,
            height=img.height,
            file_size=size,
            format=img.format
        )
        
        return jsonify({
            'success': True,
            'id': image_id,
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<int:image_id>')
@login_required
def get_image(image_id):
    """Get image details"""
    image = db.get_image(image_id)
    if not image or image['user_id'] != session['user_id']:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(image)

@app.route('/api/images/<int:image_id>', methods=['DELETE'])
@login_required
def delete_image(image_id):
    """Delete image"""
    image = db.get_image(image_id)
    if not image or image['user_id'] != session['user_id']:
        return jsonify({'error': 'Not found'}), 404
    
    # Delete file
    if os.path.exists(image['file_path']):
        os.remove(image['file_path'])
    
    db.delete_image(image_id)
    return jsonify({'success': True})

@app.route('/api/images/process', methods=['POST'])
@login_required
def process_image():
    """Process image with filters"""
    try:
        data = request.json
        image_id = data.get('image_id')
        filters = data.get('filters', [])
        adjustments = data.get('adjustments', {})
        
        # Get image
        image = db.get_image(image_id)
        if not image or image['user_id'] != session['user_id']:
            return jsonify({'error': 'Image not found'}), 404
        
        # Process image
        output_path = image_processor.process(
            image['file_path'],
            filters=filters,
            adjustments=adjustments
        )
        
        # Add watermark for free users
        user = db.get_user(session['user_id'])
        if not user['is_premium']:
            output_path = watermark.add_image_watermark(output_path)
        
        # Save to database
        export_id = db.save_export(
            user_id=session['user_id'],
            type='image',
            file_path=output_path,
            size=os.path.getsize(output_path)
        )
        
        # Increment export count
        db.increment_exports(session['user_id'])
        
        return send_file(output_path, as_attachment=True, download_name=f"processed_{image['title']}")
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/background-removal', methods=['POST'])
@login_required
def remove_background():
    """Remove image background (premium)"""
    try:
        data = request.json
        image_id = data.get('image_id')
        
        # Check premium
        user = db.get_user(session['user_id'])
        if not user['is_premium']:
            return jsonify({'error': 'Background removal requires premium'}), 403
        
        # Get image
        image = db.get_image(image_id)
        if not image or image['user_id'] != session['user_id']:
            return jsonify({'error': 'Image not found'}), 404
        
        # Remove background
        output_path = image_processor.remove_background(image['file_path'])
        
        return send_file(output_path, as_attachment=True, download_name=f"nobg_{image['title']}")
        
    except Exception as e:
        logger.error(f"Background removal error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# API ENDPOINTS - TEMPLATES
# ============================================

@app.route('/api/templates')
def get_templates():
    """Get templates"""
    category = request.args.get('category', 'all')
    limit = request.args.get('limit', 50, type=int)
    include_premium = request.args.get('premium', 'false').lower() == 'true'
    
    # Check if user is premium
    user_id = session.get('user_id')
    is_premium = False
    if user_id:
        user = db.get_user(user_id)
        is_premium = user.get('is_premium', False)
    
    templates = db.get_templates(
        category=category,
        limit=limit,
        include_premium=include_premium or is_premium
    )
    
    return jsonify(templates)

@app.route('/api/templates/<int:template_id>')
def get_template(template_id):
    """Get specific template"""
    template = db.get_template(template_id)
    if not template:
        return jsonify({'error': 'Not found'}), 404
    
    # Check premium
    if template.get('is_premium'):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Premium template requires login'}), 401
        
        user = db.get_user(user_id)
        if not user.get('is_premium'):
            return jsonify({'error': 'Premium template requires premium subscription'}), 403
    
    return jsonify(template)

@app.route('/api/templates/use/<int:template_id>', methods=['POST'])
@login_required
def use_template(template_id):
    """Use template for new design"""
    template = db.get_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Check premium
    if template.get('is_premium'):
        user = db.get_user(session['user_id'])
        if not user.get('is_premium'):
            return jsonify({'error': 'Premium template requires premium subscription'}), 403
    
    # Create design from template
    design_id = db.create_design_from_template(
        user_id=session['user_id'],
        template_id=template_id,
        title=f"From {template['title']}"
    )
    
    # Increment template usage
    db.increment_template_usage(template_id)
    
    return jsonify({
        'success': True,
        'design_id': design_id,
        'design_data': template['template_data']
    })

# ============================================
# API ENDPOINTS - PREMIUM
# ============================================

@app.route('/api/premium/check')
@login_required
def check_premium():
    """Check premium status"""
    user = db.get_user(session['user_id'])
    
    return jsonify({
        'is_premium': user.get('is_premium', False),
        'premium_until': user.get('premium_until')
    })

@app.route('/api/premium/plans')
def get_premium_plans():
    """Get premium plans"""
    return jsonify(Config.PREMIUM_PLANS)

@app.route('/api/premium/create-payment', methods=['POST'])
@login_required
def create_payment():
    """Create premium payment"""
    try:
        data = request.json
        plan_id = data.get('plan_id')
        months = data.get('months', 1)
        
        # Get plan
        plan = Config.PREMIUM_PLANS.get(plan_id)
        if not plan:
            return jsonify({'error': 'Invalid plan'}), 400
        
        # Create payment record
        payment = db.create_payment(
            user_id=session['user_id'],
            amount=plan['price'],
            months=months,
            plan_id=plan_id
        )
        
        # Create Stripe session
        session_url = stripe_handler.create_checkout_session(
            payment_id=payment['id'],
            amount=plan['price'],
            currency='usd',
            success_url=f"{Config.WEBAPP_URL}/payment/success?payment_id={payment['id']}",
            cancel_url=f"{Config.WEBAPP_URL}/payment/cancel"
        )
        
        return jsonify({
            'success': True,
            'payment_id': payment['id'],
            'url': session_url
        })
        
    except Exception as e:
        logger.error(f"Payment creation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/premium/activate', methods=['POST'])
@login_required
def activate_premium():
    """Activate premium after payment"""
    try:
        data = request.json
        payment_id = data.get('payment_id')
        
        payment = db.get_payment(payment_id)
        if not payment or payment['user_id'] != session['user_id']:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Activate premium
        db.activate_premium(
            user_id=session['user_id'],
            months=payment['months']
        )
        
        # Update payment status
        db.update_payment_status(payment_id, 'completed')
        
        session['is_premium'] = True
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Premium activation error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# API ENDPOINTS - ADMIN
# ============================================

@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    """Get admin statistics"""
    stats = db.get_admin_stats()
    return jsonify(stats)

@app.route('/api/admin/users')
@admin_required
def admin_users():
    """Get all users"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    search = request.args.get('search', '')
    
    users = db.get_all_users(page=page, limit=limit, search=search)
    return jsonify(users)

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def admin_update_user(user_id):
    """Update user"""
    data = request.json
    user = db.update_user(user_id, data)
    return jsonify(user)

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    """Delete user"""
    db.delete_user(user_id)
    return jsonify({'success': True})

@app.route('/api/admin/grant-premium', methods=['POST'])
@admin_required
def admin_grant_premium():
    """Grant premium to user"""
    data = request.json
    user_id = data.get('user_id')
    months = data.get('months', 1)
    
    db.activate_premium(user_id, months=months)
    return jsonify({'success': True})

@app.route('/api/admin/broadcast', methods=['POST'])
@admin_required
def admin_broadcast():
    """Send broadcast message"""
    data = request.json
    message = data.get('message')
    user_filter = data.get('filter', 'all')
    
    # Send broadcast via Telegram
    from .bot import send_broadcast
    send_broadcast.delay(message, user_filter)
    
    return jsonify({'success': True})

# ============================================
# API ENDPOINTS - FONTS
# ============================================

@app.route('/api/fonts')
def get_fonts():
    """Get available fonts"""
    fonts = []
    font_dir = Path(Config.FONTS_DIR)
    
    for font_file in font_dir.glob("*.ttf"):
        fonts.append({
            'name': font_file.stem,
            'file': font_file.name,
            'path': str(font_file)
        })
    
    return jsonify(sorted(fonts, key=lambda x: x['name']))

@app.route('/api/fonts/categories')
def get_font_categories():
    """Get fonts by category"""
    categories = {
        'sans_serif': ['Roboto', 'Open Sans', 'Poppins', 'Montserrat', 'Lato'],
        'serif': ['Times New Roman', 'Georgia', 'Playfair Display', 'Merriweather'],
        'monospace': ['Courier New', 'Source Code Pro', 'Fira Code'],
        'handwriting': ['Pacifico', 'Dancing Script', 'Lobster', 'Caveat'],
        'display': ['Bangers', 'Anton', 'Bebas Neue', 'Oswald']
    }
    
    return jsonify(categories)

# ============================================
# WEBSOCKET EVENTS
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_design_room')
def handle_join_design_room(data):
    """Join design collaboration room"""
    design_id = data.get('design_id')
    if design_id:
        room = f"design_{design_id}"
        join_room(room)
        emit('user_joined', {'user': session.get('user_id')}, room=room)

@socketio.on('design_update')
def handle_design_update(data):
    """Handle real-time design updates"""
    design_id = data.get('design_id')
    updates = data.get('updates')
    
    if design_id:
        room = f"design_{design_id}"
        emit('design_updated', updates, room=room, include_self=False)

@socketio.on('video_progress')
def handle_video_progress(data):
    """Handle video processing progress"""
    task_id = data.get('task_id')
    progress = data.get('progress')
    emit('progress_update', {'progress': progress}, room=f"task_{task_id}")

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}\n{traceback.format_exc()}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('403.html'), 403

@app.errorhandler(413)
def too_large_error(error):
    """Handle file too large errors"""
    return jsonify({'error': 'File too large'}), 413

# ============================================
# HELPER FUNCTIONS
# ============================================

def verify_telegram_hash(data):
    """Verify Telegram login hash"""
    try:
        hash_key = data.pop('hash')
        auth_data = sorted(data.items())
        auth_string = '\n'.join([f"{k}={v}" for k, v in auth_data])
        
        secret_key = hashlib.sha256(Config.API_HASH.encode()).digest()
        computed_hash = hmac.new(secret_key, auth_string.encode(), hashlib.sha256).hexdigest()
        
        return computed_hash == hash_key
    except:
        return False

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    logger.info("Starting Kinva Master Web App...")
    logger.info(f"Environment: {Config.FLASK_ENV}")
    logger.info(f"Port: {Config.PORT}")
    
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
)
