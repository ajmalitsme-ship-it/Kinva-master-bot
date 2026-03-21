"""
API Routes - REST API Endpoints
Author: @kinva_master
"""

import logging
import os
import json
import base64
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, g, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from ..database import db
from ..config import Config
from ..utils.decorators import require_auth, require_premium, require_admin, rate_limit
from ..utils.validators import validate_user_data, validate_password_strength
from ..utils.helpers import (
    hash_password, verify_password, generate_random_string,
    format_file_size, get_video_info, get_image_info,
    is_valid_email, is_valid_username, allowed_file
)

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# ============================================
# AUTH ENDPOINTS
# ============================================

@api_bp.route('/auth/register', methods=['POST'])
@rate_limit(limit=5, period=60)
def register():
    """User registration"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email and password required'}), 400
        
        if not is_valid_username(data['username']):
            return jsonify({'error': 'Invalid username (3-30 chars, alphanumeric and underscore)'}), 400
        
        if not is_valid_email(data['email']):
            return jsonify({'error': 'Invalid email address'}), 400
        
        valid, msg = validate_password_strength(data['password'])
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Check if user exists
        if db.get_user_by_email(data['email']):
            return jsonify({'error': 'Email already registered'}), 400
        
        if db.get_user_by_username(data['username']):
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create user
        user = db.create_user(
            username=data['username'],
            email=data['email'],
            password_hash=hash_password(data['password']),
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        
        # Create session
        from flask_jwt_extended import create_access_token
        access_token = create_access_token(identity=user['id'], expires_delta=timedelta(hours=24))
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name']
            },
            'access_token': access_token
        }), 201
        
    except Exception as e:
        logger.error(f"Register error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/login', methods=['POST'])
@rate_limit(limit=10, period=60)
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = db.get_user_by_email(data['email'])
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not verify_password(data['password'], user['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        from flask_jwt_extended import create_access_token
        access_token = create_access_token(identity=user['id'], expires_delta=timedelta(hours=24))
        
        # Update last login
        db.update_user(user['id'], {'last_login': datetime.now().isoformat()})
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'is_premium': user.get('is_premium', False)
            },
            'access_token': access_token
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout"""
    try:
        # Add token to blacklist
        jti = get_jwt()['jti']
        db.revoke_token(jti)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def me():
    """Get current user"""
    try:
        user_id = get_jwt_identity()
        user = db.get_user(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'avatar': user.get('avatar'),
            'is_premium': user.get('is_premium', False),
            'created_at': user['created_at']
        })
        
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# USER ENDPOINTS
# ============================================

@api_bp.route('/users/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = db.get_user(user_id)
        stats = db.get_user_stats(user_id)
        
        return jsonify({
            'user': user,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        allowed = ['first_name', 'last_name', 'username', 'avatar', 'bio', 'website']
        updates = {k: v for k, v in data.items() if k in allowed}
        
        if 'username' in updates:
            existing = db.get_user_by_username(updates['username'])
            if existing and existing['id'] != user_id:
                return jsonify({'error': 'Username already taken'}), 400
        
        db.update_user(user_id, updates)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get user settings"""
    try:
        user_id = get_jwt_identity()
        settings = db.get_user_settings(user_id)
        
        return jsonify(settings)
        
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update user settings"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        allowed = ['language', 'theme', 'notifications', 'auto_save', 'default_quality', 'default_format']
        settings = {k: v for k, v in data.items() if k in allowed}
        
        db.update_user_settings(user_id, settings)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Update settings error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get user statistics"""
    try:
        user_id = get_jwt_identity()
        stats = db.get_user_stats(user_id)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# DESIGN ENDPOINTS
# ============================================

@api_bp.route('/designs', methods=['GET'])
@jwt_required()
def get_designs():
    """Get user designs"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        designs = db.get_user_designs(user_id, page=page, limit=limit)
        
        return jsonify(designs)
        
    except Exception as e:
        logger.error(f"Get designs error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/designs', methods=['POST'])
@jwt_required()
def create_design():
    """Create new design"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        design_id = db.create_design(
            user_id=user_id,
            title=data.get('title', 'Untitled'),
            design_data=data.get('design_data', {}),
            thumbnail=data.get('thumbnail'),
            width=data.get('width', 1920),
            height=data.get('height', 1080)
        )
        
        return jsonify({'id': design_id, 'success': True}), 201
        
    except Exception as e:
        logger.error(f"Create design error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/designs/<int:design_id>', methods=['GET'])
@jwt_required()
def get_design(design_id):
    """Get specific design"""
    try:
        user_id = get_jwt_identity()
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user_id:
            return jsonify({'error': 'Not found'}), 404
        
        if isinstance(design['design_data'], str):
            design['design_data'] = json.loads(design['design_data'])
        
        return jsonify(design)
        
    except Exception as e:
        logger.error(f"Get design error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/designs/<int:design_id>', methods=['PUT'])
@jwt_required()
def update_design(design_id):
    """Update design"""
    try:
        user_id = get_jwt_identity()
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user_id:
            return jsonify({'error': 'Not found'}), 404
        
        data = request.get_json()
        
        updates = {}
        if 'title' in data:
            updates['title'] = data['title']
        if 'design_data' in data:
            updates['design_data'] = json.dumps(data['design_data'])
        if 'thumbnail' in data:
            updates['thumbnail'] = data['thumbnail']
        
        if updates:
            db.update_design(design_id, updates)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Update design error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/designs/<int:design_id>', methods=['DELETE'])
@jwt_required()
def delete_design(design_id):
    """Delete design"""
    try:
        user_id = get_jwt_identity()
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user_id:
            return jsonify({'error': 'Not found'}), 404
        
        db.delete_design(design_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Delete design error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/designs/<int:design_id>/export', methods=['POST'])
@jwt_required()
def export_design(design_id):
    """Export design as image"""
    try:
        user_id = get_jwt_identity()
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user_id:
            return jsonify({'error': 'Not found'}), 404
        
        from ..editors.canva_editor import canva_editor
        from ..processors.watermark import watermark
        
        design_data = design['design_data']
        if isinstance(design_data, str):
            design_data = json.loads(design_data)
        
        # Check export limit
        user = db.get_user(user_id)
        if not user.get('is_premium'):
            stats = db.get_user_stats(user_id)
            if stats.get('exports_today', 0) >= Config.FREE_DESIGN_EXPORTS:
                return jsonify({'error': 'Daily export limit reached'}), 403
        
        # Render design
        image = canva_editor.render(design_data)
        
        # Add watermark for free users
        if not user.get('is_premium'):
            image = watermark.add_text_watermark(image)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Update stats
        db.increment_exports(user_id)
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}'
        })
        
    except Exception as e:
        logger.error(f"Export design error: {e}")
        return jsonify({'error': str(e)}), 500
