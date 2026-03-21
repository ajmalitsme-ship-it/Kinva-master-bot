"""
WebSocket - Real-time communication
Author: @kinva_master
"""

import logging
import json
import uuid
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request, session
from flask_jwt_extended import decode_token, get_jwt_identity

from ..database import db
from ..config import Config

logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

# Store active connections
active_connections = {}
collaboration_rooms = {}
typing_status = {}

def init_socketio(app):
    """Initialize SocketIO with app"""
    socketio.init_app(app, cors_allowed_origins="*")

# ============================================
# Connection Handlers
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        client_id = request.sid
        logger.info(f"Client connected: {client_id}")
        
        # Store connection info
        active_connections[client_id] = {
            'sid': client_id,
            'connected_at': datetime.now().isoformat(),
            'user_id': None,
            'rooms': []
        }
        
        emit('connected', {
            'sid': client_id,
            'message': 'Connected to server',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Connect error: {e}")
        disconnect()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        client_id = request.sid
        logger.info(f"Client disconnected: {client_id}")
        
        # Clean up active connections
        if client_id in active_connections:
            user_id = active_connections[client_id].get('user_id')
            rooms = active_connections[client_id].get('rooms', [])
            
            # Leave all rooms
            for room in rooms:
                leave_room(room)
                
                # Notify others in collaboration rooms
                if room.startswith('design_'):
                    emit('user_left', {
                        'user_id': user_id,
                        'sid': client_id,
                        'timestamp': datetime.now().isoformat()
                    }, room=room)
            
            # Remove from active connections
            del active_connections[client_id]
        
    except Exception as e:
        logger.error(f"Disconnect error: {e}")

# ============================================
# Authentication
# ============================================

@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticate client with JWT token"""
    try:
        client_id = request.sid
        token = data.get('token')
        
        if not token:
            emit('auth_error', {'error': 'No token provided'})
            return
        
        # Decode token
        decoded = decode_token(token)
        user_id = decoded['sub']
        
        # Get user from database
        user = db.get_user(user_id)
        if not user:
            emit('auth_error', {'error': 'User not found'})
            return
        
        # Update connection info
        if client_id in active_connections:
            active_connections[client_id]['user_id'] = user_id
            active_connections[client_id]['user'] = {
                'id': user['id'],
                'username': user['username'],
                'first_name': user['first_name'],
                'is_premium': user.get('is_premium', False)
            }
        
        # Join user room
        user_room = f'user_{user_id}'
        join_room(user_room)
        active_connections[client_id]['rooms'].append(user_room)
        
        emit('auth_success', {
            'user_id': user_id,
            'username': user['username'],
            'is_premium': user.get('is_premium', False)
        })
        
        logger.info(f"User {user_id} authenticated successfully")
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        emit('auth_error', {'error': str(e)})

# ============================================
# Design Collaboration
# ============================================

@socketio.on('join_design_room')
def handle_join_design_room(data):
    """Join design collaboration room"""
    try:
        client_id = request.sid
        design_id = data.get('design_id')
        
        if not design_id:
            emit('error', {'error': 'Design ID required'})
            return
        
        # Check if user is authenticated
        if client_id not in active_connections or not active_connections[client_id].get('user_id'):
            emit('error', {'error': 'Not authenticated'})
            return
        
        user_id = active_connections[client_id]['user_id']
        user = active_connections[client_id]['user']
        
        # Check if user has access to design
        design = db.get_design(design_id)
        if not design or (design['user_id'] != user_id and not design.get('is_public')):
            emit('error', {'error': 'Access denied'})
            return
        
        # Create room name
        room = f'design_{design_id}'
        
        # Join room
        join_room(room)
        active_connections[client_id]['rooms'].append(room)
        
        # Initialize room if not exists
        if room not in collaboration_rooms:
            collaboration_rooms[room] = {
                'design_id': design_id,
                'users': [],
                'created_at': datetime.now().isoformat()
            }
        
        # Add user to room users
        collaboration_rooms[room]['users'].append({
            'user_id': user_id,
            'sid': client_id,
            'username': user['username'],
            'joined_at': datetime.now().isoformat()
        })
        
        # Notify others in room
        emit('user_joined', {
            'user_id': user_id,
            'username': user['username'],
            'sid': client_id,
            'timestamp': datetime.now().isoformat()
        }, room=room, include_self=False)
        
        # Send current users to new user
        current_users = [u for u in collaboration_rooms[room]['users'] if u['sid'] != client_id]
        emit('room_users', {
            'users': current_users,
            'total': len(current_users)
        })
        
        logger.info(f"User {user_id} joined design room {design_id}")
        
    except Exception as e:
        logger.error(f"Join design room error: {e}")
        emit('error', {'error': str(e)})

@socketio.on('leave_design_room')
def handle_leave_design_room(data):
    """Leave design collaboration room"""
    try:
        client_id = request.sid
        design_id = data.get('design_id')
        
        if not design_id:
            emit('error', {'error': 'Design ID required'})
            return
        
        room = f'design_{design_id}'
        
        if room in collaboration_rooms:
            # Remove user from room
            collaboration_rooms[room]['users'] = [
                u for u in collaboration_rooms[room]['users'] if u['sid'] != client_id
            ]
            
            # Clean up empty room
            if not collaboration_rooms[room]['users']:
                del collaboration_rooms[room]
        
        # Leave room
        leave_room(room)
        
        if client_id in active_connections and room in active_connections[client_id]['rooms']:
            active_connections[client_id]['rooms'].remove(room)
        
        # Notify others
        user_id = active_connections[client_id].get('user_id')
        emit('user_left', {
            'user_id': user_id,
            'sid': client_id,
            'timestamp': datetime.now().isoformat()
        }, room=room, include_self=False)
        
        logger.info(f"User left design room {design_id}")
        
    except Exception as e:
        logger.error(f"Leave design room error: {e}")
        emit('error', {'error': str(e)})

@socketio.on('design_update')
def handle_design_update(data):
    """Handle real-time design updates"""
    try:
        client_id = request.sid
        design_id = data.get('design_id')
        updates = data.get('updates', {})
        
        if not design_id:
            emit('error', {'error': 'Design ID required'})
            return
        
        room = f'design_{design_id}'
        
        # Broadcast update to all users in room except sender
        emit('design_updated', {
            'user_id': active_connections[client_id].get('user_id'),
            'updates': updates,
            'timestamp': datetime.now().isoformat()
        }, room=room, include_self=False)
        
    except Exception as e:
        logger.error(f"Design update error: {e}")
        emit('error', {'error': str(e)})

# ============================================
# Video Processing Progress
# ============================================

@socketio.on('video_progress')
def handle_video_progress(data):
    """Handle video processing progress"""
    try:
        client_id = request.sid
        task_id = data.get('task_id')
        progress = data.get('progress', 0)
        
        if not task_id:
            emit('error', {'error': 'Task ID required'})
            return
        
        room = f'task_{task_id}'
        
        # Broadcast progress update
        emit('progress_update', {
            'task_id': task_id,
            'progress': progress,
            'status': data.get('status', 'processing'),
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
    except Exception as e:
        logger.error(f"Video progress error: {e}")

# ============================================
# Chat System
# ============================================

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat message"""
    try:
        client_id = request.sid
        room = data.get('room', 'general')
        message = data.get('message')
        
        if not message:
            emit('error', {'error': 'Message required'})
            return
        
        user_id = active_connections[client_id].get('user_id')
        user = active_connections[client_id].get('user')
        
        # Save message to database
        chat_id = db.save_chat_message(
            user_id=user_id,
            room=room,
            message=message,
            message_type=data.get('type', 'text')
        )
        
        # Broadcast message
        emit('chat_message', {
            'id': chat_id,
            'user_id': user_id,
            'username': user.get('username') if user else 'Anonymous',
            'message': message,
            'type': data.get('type', 'text'),
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        emit('error', {'error': str(e)})

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    try:
        client_id = request.sid
        room = data.get('room', 'general')
        is_typing = data.get('is_typing', True)
        
        user_id = active_connections[client_id].get('user_id')
        user = active_connections[client_id].get('user')
        
        # Store typing status
        typing_key = f"{room}_{user_id}"
        if is_typing:
            typing_status[typing_key] = datetime.now().isoformat()
        else:
            typing_status.pop(typing_key, None)
        
        # Broadcast typing status
        emit('user_typing', {
            'user_id': user_id,
            'username': user.get('username') if user else 'Anonymous',
            'is_typing': is_typing,
            'timestamp': datetime.now().isoformat()
        }, room=room, include_self=False)
        
    except Exception as e:
        logger.error(f"Typing indicator error: {e}")
        emit('error', {'error': str(e)})

# ============================================
# Notification System
# ============================================

@socketio.on('notification_read')
def handle_notification_read(data):
    """Handle notification read status"""
    try:
        client_id = request.sid
        notification_id = data.get('notification_id')
        
        if not notification_id:
            emit('error', {'error': 'Notification ID required'})
            return
        
        user_id = active_connections[client_id].get('user_id')
        
        # Mark notification as read
        db.mark_notification_read(notification_id, user_id)
        
        emit('notification_read', {
            'notification_id': notification_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Notification read error: {e}")
        emit('error', {'error': str(e)})

def send_notification(user_id, title, message, notification_type='info'):
    """Send notification to user"""
    try:
        # Save to database
        notification_id = db.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        
        # Send via socket if user is connected
        room = f'user_{user_id}'
        socketio.emit('notification', {
            'id': notification_id,
            'title': title,
            'message': message,
            'type': notification_type,
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
        return notification_id
        
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        return None

# ============================================
# Collaboration Events
# ============================================

@socketio.on('cursor_move')
def handle_cursor_move(data):
    """Handle cursor position in collaboration"""
    try:
        client_id = request.sid
        design_id = data.get('design_id')
        position = data.get('position', {'x': 0, 'y': 0})
        
        if not design_id:
            emit('error', {'error': 'Design ID required'})
            return
        
        room = f'design_{design_id}'
        user_id = active_connections[client_id].get('user_id')
        user = active_connections[client_id].get('user')
        
        emit('cursor_moved', {
            'user_id': user_id,
            'username': user.get('username') if user else 'Anonymous',
            'position': position,
            'timestamp': datetime.now().isoformat()
        }, room=room, include_self=False)
        
    except Exception as e:
        logger.error(f"Cursor move error: {e}")
        emit('error', {'error': str(e)})

@socketio.on('element_selected')
def handle_element_selected(data):
    """Handle element selection in collaboration"""
    try:
        client_id = request.sid
        design_id = data.get('design_id')
        element_id = data.get('element_id')
        
        if not design_id:
            emit('error', {'error': 'Design ID required'})
            return
        
        room = f'design_{design_id}'
        user_id = active_connections[client_id].get('user_id')
        user = active_connections[client_id].get('user')
        
        emit('element_selected', {
            'user_id': user_id,
            'username': user.get('username') if user else 'Anonymous',
            'element_id': element_id,
            'timestamp': datetime.now().isoformat()
        }, room=room, include_self=False)
        
    except Exception as e:
        logger.error(f"Element selected error: {e}")
        emit('error', {'error': str(e)})

# ============================================
# Error Handling
# ============================================

@socketio.on_error()
def error_handler(e):
    """Handle SocketIO errors"""
    logger.error(f"SocketIO error: {e}")
    emit('error', {'error': str(e)})

@socketio.on_error_default
def default_error_handler(e):
    """Handle default SocketIO errors"""
    logger.error(f"SocketIO default error: {e}")
    emit('error', {'error': 'An error occurred'})
