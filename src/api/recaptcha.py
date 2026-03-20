"""
reCAPTCHA API - Google reCAPTCHA verification for bot protection
Author: @kinva_master
"""

import logging
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..config import Config
from ..database import db

logger = logging.getLogger(__name__)

recaptcha_bp = Blueprint('recaptcha', __name__, url_prefix='/api/v1/recaptcha')


class RecaptchaAPI:
    """Google reCAPTCHA verification endpoints"""
    
    # reCAPTCHA versions
    V2_CHECKBOX = 'v2_checkbox'
    V2_INVISIBLE = 'v2_invisible'
    V3 = 'v3'
    
    # Site keys (to be configured in .env)
    RECAPTCHA_SITE_KEY_V2 = Config.RECAPTCHA_SITE_KEY_V2
    RECAPTCHA_SECRET_KEY_V2 = Config.RECAPTCHA_SECRET_KEY_V2
    RECAPTCHA_SITE_KEY_V3 = Config.RECAPTCHA_SITE_KEY_V3
    RECAPTCHA_SECRET_KEY_V3 = Config.RECAPTCHA_SECRET_KEY_V3
    
    # reCAPTCHA verification endpoint
    VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'
    
    @staticmethod
    @recaptcha_bp.route('/verify', methods=['POST'])
    def verify():
        """Verify reCAPTCHA token"""
        try:
            data = request.get_json()
            token = data.get('token')
            version = data.get('version', RecaptchaAPI.V3)
            action = data.get('action', 'submit')
            
            if not token:
                return jsonify({'error': 'reCAPTCHA token required'}), 400
            
            # Select secret key based on version
            if version == RecaptchaAPI.V3:
                secret_key = RecaptchaAPI.RECAPTCHA_SECRET_KEY_V3
                min_score = data.get('min_score', 0.5)
            else:
                secret_key = RecaptchaAPI.RECAPTCHA_SECRET_KEY_V2
                min_score = None
            
            # Verify with Google
            response = requests.post(
                RecaptchaAPI.VERIFY_URL,
                data={
                    'secret': secret_key,
                    'response': token
                },
                timeout=10
            )
            
            result = response.json()
            
            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'error_codes': result.get('error-codes', ['Unknown error']),
                    'message': 'reCAPTCHA verification failed'
                }), 400
            
            # For v3, check score and action
            if version == RecaptchaAPI.V3:
                score = result.get('score', 0)
                result_action = result.get('action', '')
                
                if score < min_score:
                    return jsonify({
                        'success': False,
                        'score': score,
                        'min_score': min_score,
                        'message': f'Score too low ({score} < {min_score})'
                    }), 400
                
                if result_action != action:
                    return jsonify({
                        'success': False,
                        'expected_action': action,
                        'received_action': result_action,
                        'message': 'Action mismatch'
                    }), 400
                
                return jsonify({
                    'success': True,
                    'score': score,
                    'action': result_action,
                    'message': 'reCAPTCHA verified successfully'
                })
            
            # For v2, just return success
            return jsonify({
                'success': True,
                'challenge_ts': result.get('challenge_ts'),
                'hostname': result.get('hostname'),
                'message': 'reCAPTCHA verified successfully'
            })
            
        except requests.RequestException as e:
            logger.error(f"reCAPTCHA verification request error: {e}")
            return jsonify({'error': 'Verification service unavailable'}), 503
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/site-key', methods=['GET'])
    def get_site_key():
        """Get reCAPTCHA site key for frontend"""
        try:
            version = request.args.get('version', RecaptchaAPI.V3)
            
            if version == RecaptchaAPI.V3:
                site_key = RecaptchaAPI.RECAPTCHA_SITE_KEY_V3
            else:
                site_key = RecaptchaAPI.RECAPTCHA_SITE_KEY_V2
            
            return jsonify({
                'site_key': site_key,
                'version': version
            })
            
        except Exception as e:
            logger.error(f"Get site key error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/verify-login', methods=['POST'])
    def verify_login():
        """Verify reCAPTCHA for login attempts"""
        try:
            data = request.get_json()
            token = data.get('token')
            email = data.get('email')
            
            if not token:
                return jsonify({'error': 'reCAPTCHA token required'}), 400
            
            # Verify token
            response = requests.post(
                RecaptchaAPI.VERIFY_URL,
                data={
                    'secret': RecaptchaAPI.RECAPTCHA_SECRET_KEY_V3,
                    'response': token
                },
                timeout=10
            )
            
            result = response.json()
            
            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'message': 'reCAPTCHA verification failed'
                }), 400
            
            score = result.get('score', 0)
            
            if score < 0.5:
                # Log suspicious login attempt
                logger.warning(f"Suspicious login attempt for {email} with score {score}")
                
                # Rate limit or block if too many attempts
                ip = request.remote_addr
                attempts = db.get_login_attempts(ip, email, minutes=15)
                
                if attempts >= 5:
                    db.block_ip(ip, reason='Too many failed logins')
                    return jsonify({
                        'success': False,
                        'message': 'Too many login attempts. Please try again later.'
                    }), 429
            
            return jsonify({
                'success': True,
                'score': score
            })
            
        except Exception as e:
            logger.error(f"Login verification error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/verify-registration', methods=['POST'])
    def verify_registration():
        """Verify reCAPTCHA for registration"""
        try:
            data = request.get_json()
            token = data.get('token')
            email = data.get('email')
            
            if not token:
                return jsonify({'error': 'reCAPTCHA token required'}), 400
            
            # Verify token
            response = requests.post(
                RecaptchaAPI.VERIFY_URL,
                data={
                    'secret': RecaptchaAPI.RECAPTCHA_SECRET_KEY_V3,
                    'response': token
                },
                timeout=10
            )
            
            result = response.json()
            
            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'message': 'reCAPTCHA verification failed'
                }), 400
            
            score = result.get('score', 0)
            
            if score < 0.7:
                logger.warning(f"Suspicious registration attempt for {email} with score {score}")
                
                # Block if too many registrations from same IP
                ip = request.remote_addr
                registrations = db.get_registrations_from_ip(ip, minutes=60)
                
                if registrations >= 3:
                    db.block_ip(ip, reason='Too many registrations')
                    return jsonify({
                        'success': False,
                        'message': 'Too many registration attempts. Please try again later.'
                    }), 429
            
            return jsonify({
                'success': True,
                'score': score
            })
            
        except Exception as e:
            logger.error(f"Registration verification error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/verify-form', methods=['POST'])
    def verify_form():
        """Verify reCAPTCHA for form submissions"""
        try:
            data = request.get_json()
            token = data.get('token')
            form_type = data.get('form_type', 'contact')
            
            if not token:
                return jsonify({'error': 'reCAPTCHA token required'}), 400
            
            # Verify token (use v2 for forms)
            response = requests.post(
                RecaptchaAPI.VERIFY_URL,
                data={
                    'secret': RecaptchaAPI.RECAPTCHA_SECRET_KEY_V2,
                    'response': token
                },
                timeout=10
            )
            
            result = response.json()
            
            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'message': 'reCAPTCHA verification failed'
                }), 400
            
            # Log successful form submission
            ip = request.remote_addr
            db.log_form_submission(ip, form_type)
            
            return jsonify({
                'success': True,
                'message': 'Form verified successfully'
            })
            
        except Exception as e:
            logger.error(f"Form verification error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/verify-bot', methods=['POST'])
    @jwt_required()
    def verify_bot_action():
        """Verify reCAPTCHA for bot actions (premium users bypass)"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            # Premium users can bypass reCAPTCHA
            if user.get('is_premium'):
                return jsonify({
                    'success': True,
                    'bypassed': True,
                    'message': 'Premium user bypassed reCAPTCHA'
                })
            
            data = request.get_json()
            token = data.get('token')
            action = data.get('action', 'bot_action')
            
            if not token:
                return jsonify({'error': 'reCAPTCHA token required'}), 400
            
            # Verify token
            response = requests.post(
                RecaptchaAPI.VERIFY_URL,
                data={
                    'secret': RecaptchaAPI.RECAPTCHA_SECRET_KEY_V3,
                    'response': token
                },
                timeout=10
            )
            
            result = response.json()
            
            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'message': 'reCAPTCHA verification failed'
                }), 400
            
            score = result.get('score', 0)
            result_action = result.get('action', '')
            
            if score < 0.5 or result_action != action:
                return jsonify({
                    'success': False,
                    'score': score,
                    'message': 'Bot detected'
                }), 403
            
            return jsonify({
                'success': True,
                'score': score,
                'message': 'Human verified'
            })
            
        except Exception as e:
            logger.error(f"Bot action verification error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/stats', methods=['GET'])
    @jwt_required()
    def get_stats():
        """Get reCAPTCHA verification statistics (admin only)"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            # Check admin
            if user.get('telegram_id') not in Config.ADMIN_IDS:
                return jsonify({'error': 'Admin access required'}), 403
            
            stats = db.get_recaptcha_stats(days=30)
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/blocked-ips', methods=['GET'])
    @jwt_required()
    def get_blocked_ips():
        """Get list of blocked IPs (admin only)"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            # Check admin
            if user.get('telegram_id') not in Config.ADMIN_IDS:
                return jsonify({'error': 'Admin access required'}), 403
            
            blocked_ips = db.get_blocked_ips()
            
            return jsonify(blocked_ips)
            
        except Exception as e:
            logger.error(f"Get blocked IPs error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @recaptcha_bp.route('/unblock-ip/<ip>', methods=['POST'])
    @jwt_required()
    def unblock_ip(ip):
        """Unblock an IP address (admin only)"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            # Check admin
            if user.get('telegram_id') not in Config.ADMIN_IDS:
                return jsonify({'error': 'Admin access required'}), 403
            
            db.unblock_ip(ip)
            
            return jsonify({
                'success': True,
                'message': f'IP {ip} unblocked successfully'
            })
            
        except Exception as e:
            logger.error(f"Unblock IP error: {e}")
            return jsonify({'error': str(e)}), 500


# Helper decorator for reCAPTCHA protection on endpoints
def require_recaptcha(action='submit', min_score=0.5):
    """Decorator to require reCAPTCHA verification"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Check if reCAPTCHA is enabled
            if not Config.RECAPTCHA_ENABLED:
                return f(*args, **kwargs)
            
            # Get token from request
            token = request.headers.get('X-reCAPTCHA-Token') or request.json.get('recaptcha_token')
            
            if not token:
                return jsonify({'error': 'reCAPTCHA token required'}), 400
            
            # Verify with Google
            try:
                response = requests.post(
                    RecaptchaAPI.VERIFY_URL,
                    data={
                        'secret': RecaptchaAPI.RECAPTCHA_SECRET_KEY_V3,
                        'response': token
                    },
                    timeout=10
                )
                
                result = response.json()
                
                if not result.get('success'):
                    return jsonify({'error': 'reCAPTCHA verification failed'}), 400
                
                score = result.get('score', 0)
                result_action = result.get('action', '')
                
                if score < min_score or result_action != action:
                    return jsonify({'error': 'Bot detected'}), 403
                
                return f(*args, **kwargs)
                
            except requests.RequestException:
                return jsonify({'error': 'Verification service unavailable'}), 503
            except Exception as e:
                logger.error(f"reCAPTCHA decorator error: {e}")
                return jsonify({'error': 'Verification failed'}), 500
        
        # Preserve function metadata
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
