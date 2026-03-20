"""
Authentication API - User login, registration, and token management
Author: @kinva_master
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)

from ..database import db
from ..config import Config
from ..utils import hash_password, verify_password, generate_api_key

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


class AuthAPI:
    """Authentication API endpoints"""
    
    @staticmethod
    @auth_bp.route('/register', methods=['POST'])
    def register():
        """Register new user"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required = ['username', 'email', 'password']
            for field in required:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
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
                last_name=data.get('last_name'),
                telegram_id=data.get('telegram_id')
            )
            
            # Create access token
            access_token = create_access_token(
                identity=user['id'],
                expires_delta=timedelta(hours=24)
            )
            refresh_token = create_refresh_token(
                identity=user['id'],
                expires_delta=timedelta(days=30)
            )
            
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
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 201
            
        except Exception as e:
            logger.error(f"Register error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/login', methods=['POST'])
    def login():
        """Login user"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('email') or not data.get('password'):
                return jsonify({'error': 'Email and password required'}), 400
            
            # Get user by email
            user = db.get_user_by_email(data['email'])
            if not user:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Verify password
            if not verify_password(data['password'], user['password_hash']):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Create tokens
            access_token = create_access_token(
                identity=user['id'],
                expires_delta=timedelta(hours=24)
            )
            refresh_token = create_refresh_token(
                identity=user['id'],
                expires_delta=timedelta(days=30)
            )
            
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
                'access_token': access_token,
                'refresh_token': refresh_token
            })
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/telegram', methods=['POST'])
    def telegram_auth():
        """Authenticate with Telegram"""
        try:
            data = request.get_json()
            telegram_data = data.get('telegram_data')
            
            if not telegram_data:
                return jsonify({'error': 'Telegram data required'}), 400
            
            # Verify Telegram data hash
            from ..utils import verify_telegram_hash
            if not verify_telegram_hash(telegram_data):
                return jsonify({'error': 'Invalid hash'}), 401
            
            # Get or create user
            user = db.get_or_create_user(
                telegram_id=telegram_data['id'],
                username=telegram_data.get('username'),
                first_name=telegram_data.get('first_name'),
                last_name=telegram_data.get('last_name')
            )
            
            # Create tokens
            access_token = create_access_token(
                identity=user['id'],
                expires_delta=timedelta(hours=24)
            )
            refresh_token = create_refresh_token(
                identity=user['id'],
                expires_delta=timedelta(days=30)
            )
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'is_premium': user.get('is_premium', False)
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            })
            
        except Exception as e:
            logger.error(f"Telegram auth error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        """Refresh access token"""
        try:
            user_id = get_jwt_identity()
            
            access_token = create_access_token(
                identity=user_id,
                expires_delta=timedelta(hours=24)
            )
            
            return jsonify({
                'success': True,
                'access_token': access_token
            })
            
        except Exception as e:
            logger.error(f"Refresh token error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/logout', methods=['POST'])
    @jwt_required()
    def logout():
        """Logout user (revoke token)"""
        try:
            jti = get_jwt()['jti']
            # Add token to blacklist
            db.revoke_token(jti)
            
            return jsonify({'success': True, 'message': 'Logged out successfully'})
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/forgot-password', methods=['POST'])
    def forgot_password():
        """Request password reset"""
        try:
            data = request.get_json()
            email = data.get('email')
            
            if not email:
                return jsonify({'error': 'Email required'}), 400
            
            user = db.get_user_by_email(email)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Generate reset token
            reset_token = generate_api_key()
            db.create_password_reset_token(user['id'], reset_token)
            
            # Send reset email
            reset_url = f"{Config.WEBAPP_URL}/reset-password?token={reset_token}"
            
            # In production, send email
            logger.info(f"Password reset token for {email}: {reset_token}")
            
            return jsonify({
                'success': True,
                'message': 'Password reset instructions sent to email'
            })
            
        except Exception as e:
            logger.error(f"Forgot password error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/reset-password', methods=['POST'])
    def reset_password():
        """Reset password with token"""
        try:
            data = request.get_json()
            token = data.get('token')
            new_password = data.get('password')
            
            if not token or not new_password:
                return jsonify({'error': 'Token and password required'}), 400
            
            # Verify token
            reset = db.get_password_reset_token(token)
            if not reset or reset.get('expires_at') < datetime.now().isoformat():
                return jsonify({'error': 'Invalid or expired token'}), 400
            
            # Update password
            user_id = reset['user_id']
            db.update_user(user_id, {
                'password_hash': hash_password(new_password)
            })
            
            # Mark token as used
            db.mark_token_used(token)
            
            return jsonify({'success': True, 'message': 'Password reset successfully'})
            
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/change-password', methods=['POST'])
    @jwt_required()
    def change_password():
        """Change user password"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            if not current_password or not new_password:
                return jsonify({'error': 'Current and new password required'}), 400
            
            user = db.get_user(user_id)
            if not verify_password(current_password, user['password_hash']):
                return jsonify({'error': 'Current password is incorrect'}), 401
            
            # Update password
            db.update_user(user_id, {
                'password_hash': hash_password(new_password)
            })
            
            return jsonify({'success': True, 'message': 'Password changed successfully'})
            
        except Exception as e:
            logger.error(f"Change password error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/verify-email', methods=['POST'])
    def verify_email():
        """Verify email address"""
        try:
            data = request.get_json()
            token = data.get('token')
            
            if not token:
                return jsonify({'error': 'Token required'}), 400
            
            verification = db.get_email_verification(token)
            if not verification or verification.get('expires_at') < datetime.now().isoformat():
                return jsonify({'error': 'Invalid or expired token'}), 400
            
            # Mark email as verified
            db.update_user(verification['user_id'], {'email_verified': True})
            db.mark_verification_used(token)
            
            return jsonify({'success': True, 'message': 'Email verified successfully'})
            
        except Exception as e:
            logger.error(f"Verify email error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @auth_bp.route('/resend-verification', methods=['POST'])
    @jwt_required()
    def resend_verification():
        """Resend email verification"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            if not user.get('email'):
                return jsonify({'error': 'No email registered'}), 400
            
            # Create verification token
            token = generate_api_key()
            db.create_email_verification(user_id, token)
            
            # Send verification email
            verify_url = f"{Config.WEBAPP_URL}/verify-email?token={token}"
            
            # In production, send email
            logger.info(f"Verification link for {user['email']}: {verify_url}")
            
            return jsonify({'success': True, 'message': 'Verification email sent'})
            
        except Exception as e:
            logger.error(f"Resend verification error: {e}")
            return jsonify({'error': str(e)}), 500
