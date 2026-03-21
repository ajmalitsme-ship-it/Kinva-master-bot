"""
Flask Application Factory
Author: @kinva_master
"""

import os
import logging
import time
from flask import Flask, render_template, jsonify, request, g, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from ..config import Config
from ..database import db
from ..utils.logger import setup_logger, log_api_call
from .routes import web_bp
from .api import api_bp
from .websocket import socketio

logger = setup_logger('web')

def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    
    app.config.from_object(config_class)
    
    # Fix for reverse proxy (for production)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    CORS(app, supports_credentials=True)
    JWTManager(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=Config.REDIS_URL if Config.REDIS_URL else "memory://"
    )
    
    # ============================================
    # Request/Response Hooks
    # ============================================
    
    @app.before_request
    def before_request():
        """Before request handler"""
        # Store start time for performance monitoring
        g.start_time = time.time()
        
        # Store request ID for tracing
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        
        # Database connection
        g.db = db.get_connection()
        
        # User from session
        if 'user_id' in session:
            g.user_id = session['user_id']
            g.user = db.get_user(g.user_id)
    
    @app.after_request
    def after_request(response):
        """After request handler"""
        # Add request ID header
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = Config.WEBAPP_URL
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        """Teardown request handler"""
        # Close database connection
        if hasattr(g, 'db'):
            g.db.close()
        
        # Log API call
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            log_api_call(
                endpoint=request.path,
                method=request.method,
                user_id=getattr(g, 'user_id', None),
                status_code=getattr(g, 'status_code', None),
                duration=duration,
                request_id=getattr(g, 'request_id', None)
            )
    
    # ============================================
    # Error Handlers
    # ============================================
    
    @app.errorhandler(404)
    def not_found(error):
        """404 Not Found handler"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 Forbidden handler"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 Internal Server Error handler"""
        logger.error(f"Internal server error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """429 Rate Limit Exceeded handler"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """413 Request Entity Too Large handler"""
        return jsonify({
            'error': 'File too large',
            'message': f'Maximum file size is {Config.MAX_FILE_SIZE // (1024*1024)}MB'
        }), 413
    
    # ============================================
    # Maintenance Mode
    # ============================================
    
    @app.before_request
    def check_maintenance():
        """Check if maintenance mode is enabled"""
        if Config.MAINTENANCE_MODE and request.path not in ['/maintenance', '/health', '/api/health']:
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Service temporarily unavailable',
                    'message': Config.MAINTENANCE_MESSAGE,
                    'status': 'maintenance'
                }), 503
            return render_template('maintenance.html', message=Config.MAINTENANCE_MESSAGE), 503
    
    # ============================================
    # Register Blueprints
    # ============================================
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # ============================================
    # Health Check
    # ============================================
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'environment': Config.FLASK_ENV,
            'database': 'connected' if db.test_connection() else 'disconnected'
        })
    
    @app.route('/api/health')
    def api_health():
        """API health check"""
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        })
    
    # ============================================
    # Maintenance Route
    # ============================================
    
    @app.route('/maintenance')
    def maintenance():
        """Maintenance page"""
        return render_template('maintenance.html', message=Config.MAINTENANCE_MESSAGE)
    
    # ============================================
    # Static File Caching
    # ============================================
    
    @app.after_request
    def add_header(response):
        """Add caching headers for static files"""
        if request.path.startswith('/static/'):
            response.cache_control.max_age = 31536000  # 1 year
            response.cache_control.public = True
        return response
    
    # ============================================
    # Template Context Processor
    # ============================================
    
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'config': Config,
            'current_year': datetime.now().year,
            'app_name': Config.BOT_NAME,
            'app_url': Config.WEBAPP_URL,
            'admin_contact': Config.ADMIN_CONTACT
        }
    
    return app
