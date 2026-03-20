"""
API Package - REST API endpoints for external integrations
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

__all__ = [
    'auth_bp',
    'users_bp',
    'videos_bp',
    'images_bp',
    'designs_bp',
    'payments_bp',
    'templates_bp',
    'admin_bp',
    'webhooks_bp'
]
