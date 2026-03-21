"""
Web Package - Flask Web Application
Author: @kinva_master
"""

from .app import create_app
from .routes import web_bp
from .api import api_bp
from .websocket import socketio

__all__ = [
    'create_app',
    'web_bp',
    'api_bp',
    'socketio'
]
