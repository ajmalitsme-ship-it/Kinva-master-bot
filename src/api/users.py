"""
Users API - User profile and account management
Author: @kinva_master
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..database import db
from ..config import Config
from ..utils import format_file_size, generate_api_key

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


class UsersAPI:
    """Users API endpoints"""
    
    @staticmethod
    @users_bp.route('/me', methods=['GET'])
    @jwt_required()
    def get_profile():
        """Get current user profile"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get subscription status
            from ..payment.subscription import subscription_manager
            subscription = subscription_manager.get_subscription_status(user_id)
            
            # Get usage stats
            stats = db.get_user_stats(user_id)
            plan = subscription_manager.get_plan(user.get('plan', 'free'))
            limits = plan.get('limits', {}) if plan else {}
            
            return jsonify({
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'avatar': user.get('avatar'),
                    'is_premium': user.get('is_premium', False),
                    'plan': user.get('plan', 'free'),
                    'created_at': user['created_at'],
                    'last_login': user.get('last_login')
                },
                'subscription': subscription,
                'usage': {
                    'exports_today': stats.get('exports_today', 0),
                    'exports_limit': limits.get('exports_per_day', 3),
                    'storage_used': format_file_size(stats.get('storage_used', 0)),
                    'storage_limit': format_file_size(limits.get('storage', 100 * 1024 * 1024)),
                    'storage_percentage': (stats.get('storage_used', 0) / limits.get('storage', 1)) * 100 if limits.get('storage') else 0,
                    'videos_edited': stats.get('videos_edited', 0),
                    'images_edited': stats.get('images_edited', 0),
                    'designs_created': stats.get('designs_created', 0)
                }
            })
            
        except Exception as e:
            logger.error(f"Get profile error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me', methods=['PUT'])
    @jwt_required()
    def update_profile():
        """Update user profile"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Allowed fields to update
            allowed_fields = ['first_name', 'last_name', 'username', 'avatar', 'bio', 'website', 'location']
            updates = {k: v for k, v in data.items() if k in allowed_fields}
            
            # Check username uniqueness
            if 'username' in updates:
                existing = db.get_user_by_username(updates['username'])
                if existing and existing['id'] != user_id:
                    return jsonify({'error': 'Username already taken'}), 400
            
            db.update_user(user_id, updates)
            
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
            
        except Exception as e:
            logger.error(f"Update profile error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/settings', methods=['GET'])
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
    
    @staticmethod
    @users_bp.route('/me/settings', methods=['PUT'])
    @jwt_required()
    def update_settings():
        """Update user settings"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Allowed settings
            allowed = [
                'language', 'theme', 'notifications', 'auto_save', 
                'default_quality', 'default_format', 'email_notifications',
                'telegram_notifications', 'watermark_enabled'
            ]
            settings = {k: v for k, v in data.items() if k in allowed}
            
            db.update_user_settings(user_id, settings)
            
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
            
        except Exception as e:
            logger.error(f"Update settings error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/stats', methods=['GET'])
    @jwt_required()
    def get_stats():
        """Get user statistics"""
        try:
            user_id = get_jwt_identity()
            stats = db.get_user_stats(user_id)
            
            # Get weekly and monthly stats
            weekly = db.get_weekly_stats(user_id)
            monthly = db.get_monthly_stats(user_id)
            
            return jsonify({
                'daily': stats,
                'weekly': weekly,
                'monthly': monthly
            })
            
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/activity', methods=['GET'])
    @jwt_required()
    def get_activity():
        """Get user activity timeline"""
        try:
            user_id = get_jwt_identity()
            days = request.args.get('days', 30, type=int)
            
            activity = db.get_user_activity(user_id, days=days)
            
            return jsonify(activity)
            
        except Exception as e:
            logger.error(f"Get activity error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/delete', methods=['DELETE'])
    @jwt_required()
    def delete_account():
        """Delete user account"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            password = data.get('password')
            
            user = db.get_user(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Verify password if email login
            if user.get('password_hash'):
                from ..utils import verify_password
                if not verify_password(password, user['password_hash']):
                    return jsonify({'error': 'Invalid password'}), 401
            
            # Delete user data
            db.delete_user(user_id)
            
            return jsonify({'success': True, 'message': 'Account deleted successfully'})
            
        except Exception as e:
            logger.error(f"Delete account error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/exports', methods=['GET'])
    @jwt_required()
    def get_exports():
        """Get user export history"""
        try:
            user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            type_filter = request.args.get('type')  # video, image, design
            
            exports = db.get_user_exports(user_id, page=page, limit=limit, type_filter=type_filter)
            
            return jsonify(exports)
            
        except Exception as e:
            logger.error(f"Get exports error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/referrals', methods=['GET'])
    @jwt_required()
    def get_referrals():
        """Get user referrals"""
        try:
            user_id = get_jwt_identity()
            referrals = db.get_user_referrals(user_id)
            
            return jsonify({
                'total': len(referrals),
                'active': len([r for r in referrals if r.get('active')]),
                'rewards_earned': len(referrals) * 7,  # 7 days per referral
                'referrals': referrals,
                'referral_link': f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"
            })
            
        except Exception as e:
            logger.error(f"Get referrals error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/notifications', methods=['GET'])
    @jwt_required()
    def get_notifications():
        """Get user notifications"""
        try:
            user_id = get_jwt_identity()
            limit = request.args.get('limit', 20, type=int)
            unread_only = request.args.get('unread', 'false').lower() == 'true'
            
            notifications = db.get_user_notifications(user_id, limit=limit, unread_only=unread_only)
            
            return jsonify(notifications)
            
        except Exception as e:
            logger.error(f"Get notifications error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/notifications/<int:notification_id>/read', methods=['POST'])
    @jwt_required()
    def mark_notification_read(notification_id):
        """Mark notification as read"""
        try:
            user_id = get_jwt_identity()
            notification = db.get_notification(notification_id)
            
            if not notification or notification['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            db.mark_notification_read(notification_id)
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Mark notification read error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/notifications/read-all', methods=['POST'])
    @jwt_required()
    def mark_all_notifications_read():
        """Mark all notifications as read"""
        try:
            user_id = get_jwt_identity()
            db.mark_all_notifications_read(user_id)
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Mark all notifications read error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/api-keys', methods=['GET'])
    @jwt_required()
    def get_api_keys():
        """Get user API keys"""
        try:
            user_id = get_jwt_identity()
            api_keys = db.get_user_api_keys(user_id)
            
            return jsonify(api_keys)
            
        except Exception as e:
            logger.error(f"Get API keys error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/api-keys', methods=['POST'])
    @jwt_required()
    def create_api_key():
        """Create new API key"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            name = data.get('name', 'API Key')
            expires_in = data.get('expires_in', 30)  # days
            
            # Generate API key
            api_key = generate_api_key()
            
            # Save to database
            key_id = db.create_api_key(
                user_id=user_id,
                name=name,
                key=api_key,
                expires_in=expires_in
            )
            
            return jsonify({
                'success': True,
                'id': key_id,
                'key': api_key,
                'name': name,
                'expires_at': (datetime.now() + timedelta(days=expires_in)).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Create API key error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/me/api-keys/<int:key_id>', methods=['DELETE'])
    @jwt_required()
    def revoke_api_key(key_id):
        """Revoke API key"""
        try:
            user_id = get_jwt_identity()
            api_key = db.get_api_key(key_id)
            
            if not api_key or api_key['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            db.revoke_api_key(key_id)
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Revoke API key error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @users_bp.route('/<int:user_id>', methods=['GET'])
    @jwt_required()
    def get_user(user_id):
        """Get public user profile"""
        try:
            current_user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Return only public information
            return jsonify({
                'id': user['id'],
                'username': user['username'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'avatar': user.get('avatar'),
                'is_premium': user.get('is_premium', False),
                'created_at': user['created_at']
            })
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return jsonify({'error': str(e)}), 500
