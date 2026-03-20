"""
Admin API - Admin panel endpoints
Author: @kinva_master
"""

import logging
import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..database import db
from ..config import Config
from ..utils import format_file_size, generate_api_key
from ..payment.subscription import subscription_manager

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


class AdminAPI:
    """Admin API endpoints"""
    
    @staticmethod
    def check_admin(user_id):
        """Check if user is admin"""
        user = db.get_user(user_id)
        return user and user.get('telegram_id') in Config.ADMIN_IDS
    
    @staticmethod
    @admin_bp.route('/dashboard', methods=['GET'])
    @jwt_required()
    def dashboard():
        """Get admin dashboard data"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            # Get statistics
            stats = db.get_admin_stats()
            
            # Get recent activity
            recent_users = db.get_recent_users(limit=10)
            recent_payments = db.get_recent_payments(limit=10)
            recent_exports = db.get_recent_exports(limit=10)
            
            # Get revenue data
            revenue_weekly = db.get_revenue_weekly()
            revenue_monthly = db.get_revenue_monthly()
            revenue_yearly = db.get_revenue_yearly()
            
            # Get user growth
            user_growth = db.get_user_growth(days=30)
            
            return jsonify({
                'stats': stats,
                'recent_users': recent_users,
                'recent_payments': recent_payments,
                'recent_exports': recent_exports,
                'revenue': {
                    'weekly': revenue_weekly,
                    'monthly': revenue_monthly,
                    'yearly': revenue_yearly
                },
                'user_growth': user_growth
            })
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/users', methods=['GET'])
    @jwt_required()
    def get_users():
        """Get all users with filters"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 50, type=int)
            search = request.args.get('search')
            status = request.args.get('status')  # premium, free, active, inactive
            sort_by = request.args.get('sort_by', 'created_at')
            sort_order = request.args.get('sort_order', 'desc')
            
            users = db.get_all_users(
                page=page, limit=limit, search=search,
                status=status, sort_by=sort_by, sort_order=sort_order
            )
            
            total = db.get_total_users(search=search, status=status)
            
            return jsonify({
                'users': users,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            })
            
        except Exception as e:
            logger.error(f"Get users error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/users/<int:target_id>', methods=['GET'])
    @jwt_required()
    def get_user(target_id):
        """Get user details"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            user = db.get_user(target_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get user stats
            stats = db.get_user_stats(target_id)
            payments = db.get_user_payments(target_id, limit=20)
            exports = db.get_user_exports(target_id, limit=20)
            
            return jsonify({
                'user': user,
                'stats': stats,
                'payments': payments,
                'exports': exports
            })
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/users/<int:target_id>', methods=['PUT'])
    @jwt_required()
    def update_user(target_id):
        """Update user (admin only)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            
            # Allowed fields for admin update
            allowed_fields = [
                'username', 'email', 'first_name', 'last_name',
                'is_premium', 'is_banned', 'is_verified', 'plan'
            ]
            updates = {k: v for k, v in data.items() if k in allowed_fields}
            
            if updates:
                db.update_user(target_id, updates)
            
            return jsonify({'success': True, 'message': 'User updated successfully'})
            
        except Exception as e:
            logger.error(f"Update user error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/users/<int:target_id>/ban', methods=['POST'])
    @jwt_required()
    def ban_user(target_id):
        """Ban user"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            reason = data.get('reason', 'No reason provided')
            
            db.ban_user(target_id, reason=reason, banned_by=user_id)
            
            return jsonify({'success': True, 'message': 'User banned successfully'})
            
        except Exception as e:
            logger.error(f"Ban user error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/users/<int:target_id>/unban', methods=['POST'])
    @jwt_required()
    def unban_user(target_id):
        """Unban user"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            db.unban_user(target_id)
            
            return jsonify({'success': True, 'message': 'User unbanned successfully'})
            
        except Exception as e:
            logger.error(f"Unban user error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/users/<int:target_id>/premium', methods=['POST'])
    @jwt_required()
    def grant_premium(target_id):
        """Grant premium to user"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            months = data.get('months', 1)
            plan = data.get('plan', 'pro')
            
            # Activate premium
            if months == 0:
                db.activate_lifetime_premium(target_id)
            else:
                subscription_manager.activate_subscription(target_id, plan, months)
            
            # Add note
            note = data.get('note')
            if note:
                db.add_admin_note(target_id, note, user_id)
            
            return jsonify({'success': True, 'message': f'Granted {months} months premium'})
            
        except Exception as e:
            logger.error(f"Grant premium error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/payments', methods=['GET'])
    @jwt_required()
    def get_payments():
        """Get all payments"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 50, type=int)
            status = request.args.get('status')
            method = request.args.get('method')
            
            payments = db.get_all_payments(
                page=page, limit=limit, status=status, method=method
            )
            
            total = db.get_total_payments(status=status, method=method)
            
            return jsonify({
                'payments': payments,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            })
            
        except Exception as e:
            logger.error(f"Get payments error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/payments/<int:payment_id>', methods=['GET'])
    @jwt_required()
    def get_payment(payment_id):
        """Get payment details"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            payment = db.get_payment_by_id(payment_id)
            if not payment:
                return jsonify({'error': 'Payment not found'}), 404
            
            return jsonify(payment)
            
        except Exception as e:
            logger.error(f"Get payment error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/payments/<int:payment_id>/refund', methods=['POST'])
    @jwt_required()
    def refund_payment(payment_id):
        """Refund payment"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            amount = data.get('amount')
            reason = data.get('reason', 'Admin refund')
            
            payment = db.get_payment_by_id(payment_id)
            if not payment:
                return jsonify({'error': 'Payment not found'}), 404
            
            # Process refund based on payment method
            if payment['method'] == 'stripe':
                from ..payment.stripe_handler import stripe_handler
                result = stripe_handler.create_refund(payment['payment_id'], amount)
            elif payment['method'] == 'razorpay':
                from ..payment.razorpay_handler import razorpay_handler
                result = razorpay_handler.refund_payment(payment['payment_id'], amount)
            else:
                return jsonify({'error': 'Refund not supported for this payment method'}), 400
            
            # Update payment status
            db.update_payment_status(payment['id'], 'refunded')
            
            # Create refund record
            db.create_refund_record(
                payment_id=payment['id'],
                user_id=payment['user_id'],
                amount=amount or payment['amount'],
                reason=reason,
                processed_by=user_id
            )
            
            return jsonify({'success': True, 'message': 'Refund processed'})
            
        except Exception as e:
            logger.error(f"Refund payment error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/templates', methods=['GET'])
    @jwt_required()
    def get_templates():
        """Get all templates (admin view)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 50, type=int)
            category = request.args.get('category')
            
            templates = db.get_all_templates(page=page, limit=limit, category=category)
            
            total = db.get_total_templates(category=category)
            
            return jsonify({
                'templates': templates,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            })
            
        except Exception as e:
            logger.error(f"Get templates error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/templates', methods=['POST'])
    @jwt_required()
    def create_template():
        """Create new template (admin)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            
            title = data.get('title')
            category = data.get('category')
            template_type = data.get('type')
            template_data = data.get('template_data', {})
            is_premium = data.get('is_premium', False)
            thumbnail = data.get('thumbnail')
            
            if not title or not category or not template_type:
                return jsonify({'error': 'Title, category, and type required'}), 400
            
            template_id = db.create_template(
                title=title,
                category=category,
                template_type=template_type,
                template_data=json.dumps(template_data),
                is_premium=is_premium,
                thumbnail=thumbnail,
                created_by=user_id
            )
            
            return jsonify({
                'success': True,
                'id': template_id,
                'message': 'Template created successfully'
            }), 201
            
        except Exception as e:
            logger.error(f"Create template error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/templates/<int:template_id>', methods=['PUT'])
    @jwt_required()
    def update_template(template_id):
        """Update template (admin)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            
            updates = {}
            if 'title' in data:
                updates['title'] = data['title']
            if 'category' in data:
                updates['category'] = data['category']
            if 'type' in data:
                updates['type'] = data['type']
            if 'template_data' in data:
                updates['template_data'] = json.dumps(data['template_data'])
            if 'is_premium' in data:
                updates['is_premium'] = data['is_premium']
            if 'thumbnail' in data:
                updates['thumbnail'] = data['thumbnail']
            
            if updates:
                db.update_template(template_id, updates)
            
            return jsonify({'success': True, 'message': 'Template updated successfully'})
            
        except Exception as e:
            logger.error(f"Update template error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/templates/<int:template_id>', methods=['DELETE'])
    @jwt_required()
    def delete_template(template_id):
        """Delete template (admin)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            template = db.get_template(template_id)
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
            # Delete thumbnail
            if template.get('thumbnail') and os.path.exists(template['thumbnail']):
                os.remove(template['thumbnail'])
            
            db.delete_template(template_id)
            
            return jsonify({'success': True, 'message': 'Template deleted successfully'})
            
        except Exception as e:
            logger.error(f"Delete template error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/promo-codes', methods=['GET'])
    @jwt_required()
    def get_promo_codes():
        """Get all promo codes"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            promos = db.get_all_promo_codes()
            
            return jsonify(promos)
            
        except Exception as e:
            logger.error(f"Get promo codes error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/promo-codes', methods=['POST'])
    @jwt_required()
    def create_promo_code():
        """Create promo code (admin)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            
            code = data.get('code', '').upper()
            discount = data.get('discount')
            discount_type = data.get('type', 'percent')
            expires_in = data.get('expires_in', 30)  # days
            max_uses = data.get('max_uses', 100)
            
            if not code or not discount:
                return jsonify({'error': 'Code and discount required'}), 400
            
            # Check if code exists
            if db.get_promo_code(code):
                return jsonify({'error': 'Promo code already exists'}), 400
            
            expires_at = datetime.now() + timedelta(days=expires_in)
            
            promo_id = db.create_promo_code(
                code=code,
                discount=discount,
                discount_type=discount_type,
                expires_at=expires_at,
                max_uses=max_uses,
                created_by=user_id
            )
            
            return jsonify({
                'success': True,
                'id': promo_id,
                'code': code,
                'discount': discount,
                'type': discount_type,
                'expires_at': expires_at.isoformat(),
                'max_uses': max_uses
            })
            
        except Exception as e:
            logger.error(f"Create promo code error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/promo-codes/<int:promo_id>', methods=['DELETE'])
    @jwt_required()
    def delete_promo_code(promo_id):
        """Delete promo code (admin)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            db.delete_promo_code(promo_id)
            
            return jsonify({'success': True, 'message': 'Promo code deleted'})
            
        except Exception as e:
            logger.error(f"Delete promo code error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/broadcast', methods=['POST'])
    @jwt_required()
    def broadcast():
        """Send broadcast message to users"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            
            message = data.get('message')
            target = data.get('target', 'all')  # all, premium, free, active
            message_type = data.get('type', 'text')  # text, photo, video
            media_url = data.get('media_url')
            
            if not message:
                return jsonify({'error': 'Message required'}), 400
            
            # Queue broadcast
            broadcast_id = db.create_broadcast(
                admin_id=user_id,
                message=message,
                target=target,
                message_type=message_type,
                media_url=media_url,
                status='pending'
            )
            
            # Start broadcast in background
            from ..bot import send_broadcast
            send_broadcast.delay(broadcast_id)
            
            return jsonify({
                'success': True,
                'broadcast_id': broadcast_id,
                'message': 'Broadcast queued'
            })
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/broadcasts', methods=['GET'])
    @jwt_required()
    def get_broadcasts():
        """Get broadcast history"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            broadcasts = db.get_broadcasts(limit=50)
            
            return jsonify(broadcasts)
            
        except Exception as e:
            logger.error(f"Get broadcasts error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/logs', methods=['GET'])
    @jwt_required()
    def get_logs():
        """Get system logs"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            log_type = request.args.get('type', 'app')
            lines = request.args.get('lines', 100, type=int)
            
            log_file = f"logs/{log_type}.log"
            if not os.path.exists(log_file):
                return jsonify({'error': 'Log file not found'}), 404
            
            with open(log_file, 'r') as f:
                logs = f.readlines()[-lines:]
            
            return jsonify({
                'type': log_type,
                'lines': len(logs),
                'logs': logs
            })
            
        except Exception as e:
            logger.error(f"Get logs error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/export-data', methods=['GET'])
    @jwt_required()
    def export_data():
        """Export system data (admin)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data_type = request.args.get('type', 'users')
            
            if data_type == 'users':
                data = db.get_all_users(limit=10000)
                filename = f"users_export_{datetime.now().strftime('%Y%m%d')}.json"
            elif data_type == 'payments':
                data = db.get_all_payments(limit=10000)
                filename = f"payments_export_{datetime.now().strftime('%Y%m%d')}.json"
            elif data_type == 'exports':
                data = db.get_all_exports(limit=10000)
                filename = f"exports_export_{datetime.now().strftime('%Y%m%d')}.json"
            else:
                return jsonify({'error': 'Invalid data type'}), 400
            
            # Write to temp file
            temp_file = f"/tmp/{filename}"
            with open(temp_file, 'w') as f:
                json.dump(data, f, default=str)
            
            return send_file(temp_file, as_attachment=True, download_name=filename)
            
        except Exception as e:
            logger.error(f"Export data error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/settings', methods=['GET'])
    @jwt_required()
    def get_settings():
        """Get system settings"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            settings = {
                'free_video_length': Config.FREE_VIDEO_LENGTH,
                'free_video_exports': Config.FREE_VIDEO_EXPORTS,
                'free_image_exports': Config.FREE_IMAGE_EXPORTS,
                'free_storage': Config.FREE_MAX_STORAGE,
                'premium_price_monthly': Config.PREMIUM_PLANS['pro']['price'],
                'premium_price_yearly': Config.PREMIUM_PLANS['pro_yearly']['price'],
                'max_video_size': Config.MAX_VIDEO_SIZE,
                'max_image_size': Config.MAX_IMAGE_SIZE,
                'supported_video_formats': list(Config.ALLOWED_VIDEOS),
                'supported_image_formats': list(Config.ALLOWED_IMAGES),
                'watermark_text': Config.WATERMARK_TEXT,
                'watermark_opacity': Config.WATERMARK_OPACITY,
                'watermark_position': Config.WATERMARK_POSITION
            }
            
            return jsonify(settings)
            
        except Exception as e:
            logger.error(f"Get settings error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @admin_bp.route('/settings', methods=['PUT'])
    @jwt_required()
    def update_settings():
        """Update system settings (admin)"""
        try:
            user_id = get_jwt_identity()
            if not AdminAPI.check_admin(user_id):
                return jsonify({'error': 'Admin access required'}), 403
            
            data = request.get_json()
            
            # Update settings in database
            for key, value in data.items():
                db.update_system_setting(key, value)
            
            return jsonify({'success': True, 'message': 'Settings updated'})
            
        except Exception as e:
            logger.error(f"Update settings error: {e}")
            return jsonify({'error': str(e)}), 500
