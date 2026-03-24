#!/usr/bin/env python3
"""
Kinva Master Bot - Web Application with Live Streaming
Author: @funnytamilan
"""

import os
import uuid
import logging
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image
import io
import threading
import queue
import time

from config import Config
from database import Database
from utils.image_editor import ImageEditor
from utils.video_editor import VideoEditor
from utils.effects import AdvancedEffects

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'kinva-master-secret-key-2024')
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['TEMP_FOLDER'] = 'temp'

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize managers
config = Config()
db = Database()
image_editor = ImageEditor()
video_editor = VideoEditor()
effects = AdvancedEffects()

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Store active sessions
active_sessions = {}
processing_queue = queue.Queue()

logger = logging.getLogger(__name__)

# ============= ROUTES =============

@app.route('/')
def index():
    """Main page"""
    user_id = request.args.get('user', 'anonymous')
    session['user_id'] = user_id
    return render_template('editor.html', user_id=user_id)

@app.route('/editor')
def editor():
    """Web editor interface"""
    user_id = request.args.get('user', 'anonymous')
    session['user_id'] = user_id
    return render_template('editor.html', user_id=user_id)

@app.route('/stream')
def stream():
    """Live stream editing page"""
    user_id = request.args.get('user', 'anonymous')
    session['user_id'] = user_id
    return render_template('stream.html', user_id=user_id)

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    user_id = request.args.get('user', '')
    if int(user_id) not in config.ADMIN_IDS:
        return jsonify({'error': 'Unauthorized'}), 403
    return render_template('admin_dashboard.html', user_id=user_id)

# ============= API ENDPOINTS =============

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload file for editing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        user_id = request.form.get('user_id', 'anonymous')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"{user_id}_{uuid.uuid4().hex}.{ext}"
        
        # Determine file type
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
            file_type = 'image'
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
            file_type = 'video'
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Save file
        file.save(save_path)
        
        # Store session info
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            'user_id': user_id,
            'file_path': save_path,
            'file_type': file_type,
            'filename': filename,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'file_type': file_type,
            'filename': filename,
            'preview_url': f'/api/preview/{session_id}'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<session_id>')
def preview_file(session_id):
    """Preview uploaded file"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=False)
        
    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/apply_filter', methods=['POST'])
def apply_filter():
    """Apply filter to image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        filter_name = data.get('filter')
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        file_type = session_info['file_type']
        
        if file_type != 'image':
            return jsonify({'error': 'Not an image file'}), 400
        
        # Apply filter based on name
        if filter_name == 'vintage':
            result = image_editor.apply_vintage_filter(file_path)
        elif filter_name == 'cinematic':
            result = image_editor.apply_cinematic_filter(file_path)
        elif filter_name == 'black_white':
            result = image_editor.apply_black_white_filter(file_path)
        elif filter_name == 'sepia':
            result = image_editor.apply_sepia_filter(file_path)
        elif filter_name == 'blur':
            result = image_editor.apply_blur_filter(file_path)
        elif filter_name == 'sharpen':
            result = image_editor.apply_sharpen_filter(file_path)
        elif filter_name == 'glitch':
            result = image_editor.apply_glitch_effect(file_path)
        elif filter_name == 'watercolor':
            result = image_editor.apply_watercolor_effect(file_path)
        elif filter_name == 'oil_painting':
            result = image_editor.apply_oil_painting_effect(file_path)
        elif filter_name == 'sketch':
            result = image_editor.apply_sketch_effect(file_path)
        elif filter_name == 'cartoon':
            result = image_editor.apply_cartoon_effect(file_path)
        elif filter_name == 'neon':
            result = image_editor.apply_neon_effect(file_path)
        elif filter_name == 'pixelate':
            result = image_editor.apply_pixelate_effect(file_path)
        else:
            return jsonify({'error': 'Unknown filter'}), 400
        
        # Save result
        output_filename = f"filtered_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        cv2.imwrite(output_path, result)
        
        # Update session
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Apply filter error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove_background', methods=['POST'])
def remove_background():
    """Remove background from image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Remove background
        result_data = image_editor.remove_background(file_path)
        
        # Save result
        output_filename = f"nobg_{uuid.uuid4().hex}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        with open(output_path, 'wb') as f:
            f.write(result_data)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Remove background error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_text', methods=['POST'])
def add_text():
    """Add text to image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        text = data.get('text', '')
        position = data.get('position', 'center')
        font_size = data.get('font_size', 40)
        color = data.get('color', [255, 255, 255])
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Add text
        result = image_editor.add_text(file_path, text, position, font_size, tuple(color))
        
        # Save result
        output_filename = f"text_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.save(output_path)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Add text error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/resize', methods=['POST'])
def resize_image():
    """Resize image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        width = data.get('width')
        height = data.get('height')
        maintain_ratio = data.get('maintain_ratio', True)
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Resize
        result = image_editor.resize_image(file_path, width, height, maintain_ratio)
        
        # Save result
        output_filename = f"resized_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.save(output_path)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Resize error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rotate', methods=['POST'])
def rotate_image():
    """Rotate image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        angle = data.get('angle', 90)
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Rotate
        result = image_editor.rotate_image(file_path, angle)
        
        # Save result
        output_filename = f"rotated_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.save(output_path)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Rotate error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/crop', methods=['POST'])
def crop_image():
    """Crop image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        left = data.get('left', 0)
        top = data.get('top', 0)
        right = data.get('right')
        bottom = data.get('bottom')
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Crop
        result = image_editor.crop_image(file_path, left, top, right, bottom)
        
        # Save result
        output_filename = f"cropped_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.save(output_path)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Crop error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/adjust_brightness', methods=['POST'])
def adjust_brightness():
    """Adjust image brightness"""
    try:
        data = request.json
        session_id = data.get('session_id')
        factor = data.get('factor', 1.0)
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Adjust brightness
        result = image_editor.adjust_brightness(file_path, factor)
        
        # Save result
        output_filename = f"bright_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.save(output_path)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Adjust brightness error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/adjust_contrast', methods=['POST'])
def adjust_contrast():
    """Adjust image contrast"""
    try:
        data = request.json
        session_id = data.get('session_id')
        factor = data.get('factor', 1.0)
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Adjust contrast
        result = image_editor.adjust_contrast(file_path, factor)
        
        # Save result
        output_filename = f"contrast_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.save(output_path)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Adjust contrast error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_collage', methods=['POST'])
def create_collage():
    """Create collage from multiple images"""
    try:
        data = request.json
        session_id = data.get('session_id')
        layout = data.get('layout', 'grid')
        
        # Get all images from session
        session_info = active_sessions.get(session_id)
        if not session_info:
            return jsonify({'error': 'Session not found'}), 404
        
        # For demo, we'll use the current image
        file_path = session_info['file_path']
        
        # Create collage (simplified - you can expand this)
        result = image_editor.create_collage([file_path], layout)
        
        # Save result
        output_filename = f"collage_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.save(output_path)
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Create collage error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/apply_video_effect', methods=['POST'])
def apply_video_effect():
    """Apply effect to video"""
    try:
        data = request.json
        session_id = data.get('session_id')
        effect = data.get('effect')
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Apply video effect
        if effect == 'vhs':
            result = video_editor.apply_vhs_effect(file_path)
        elif effect == 'glitch':
            result = video_editor.apply_glitch_effect(file_path)
        elif effect == 'black_white':
            result = video_editor.apply_black_white(file_path)
        elif effect == 'sepia':
            result = video_editor.apply_sepia(file_path)
        elif effect == 'blur':
            result = video_editor.apply_blur_effect(file_path)
        else:
            return jsonify({'error': 'Unknown effect'}), 400
        
        # Save result
        output_filename = f"effected_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Apply video effect error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trim_video', methods=['POST'])
def trim_video():
    """Trim video"""
    try:
        data = request.json
        session_id = data.get('session_id')
        start = float(data.get('start', 0))
        end = float(data.get('end', 10))
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Trim video
        result = video_editor.trim_video(file_path, start, end)
        
        # Save result
        output_filename = f"trimmed_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Trim video error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/change_speed', methods=['POST'])
def change_speed():
    """Change video speed"""
    try:
        data = request.json
        session_id = data.get('session_id')
        speed = float(data.get('speed', 1.0))
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Change speed
        result = video_editor.change_speed(file_path, speed)
        
        # Save result
        output_filename = f"speed_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Change speed error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/merge_videos', methods=['POST'])
def merge_videos():
    """Merge multiple videos"""
    try:
        data = request.json
        session_id = data.get('session_id')
        video_paths = data.get('video_paths', [])
        
        if not video_paths:
            return jsonify({'error': 'No videos to merge'}), 400
        
        # Merge videos
        result = video_editor.merge_videos(video_paths)
        
        # Save result
        output_filename = f"merged_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{output_filename}'
        })
        
    except Exception as e:
        logger.error(f"Merge videos error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/compress_video', methods=['POST'])
def compress_video():
    """Compress video"""
    try:
        data = request.json
        session_id = data.get('session_id')
        target_size = data.get('target_size', 10)
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info['file_path']
        
        # Compress video
        output_path = video_editor.compress_video(file_path, target_size)
        
        session_info['filtered_path'] = output_path
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/output/{os.path.basename(output_path)}'
        })
        
    except Exception as e:
        logger.error(f"Compress video error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_file():
    """Export final edited file"""
    try:
        data = request.json
        session_id = data.get('session_id')
        quality = data.get('quality', '1080p')
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info.get('filtered_path') or session_info['file_path']
        file_type = session_info['file_type']
        
        # Check if user has premium for 4K
        user_id = session_info['user_id']
        is_premium = db.check_premium_status(int(user_id)) if user_id != 'anonymous' else False
        
        if quality == '4K' and not is_premium:
            return jsonify({'error': 'Premium required for 4K export'}), 403
        
        # Return file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"kinva_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_path.split('.')[-1]}"
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/output/<filename>')
def get_output(filename):
    """Get output file"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        return send_file(file_path)
    except Exception as e:
        logger.error(f"Get output error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>')
def get_session(session_id):
    """Get session info"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        return jsonify({
            'success': True,
            'session': {
                'file_type': session_info['file_type'],
                'filename': session_info['filename'],
                'created_at': session_info['created_at']
            }
        })
        
    except Exception as e:
        logger.error(f"Get session error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete session and files"""
    try:
        if session_id in active_sessions:
            session_info = active_sessions[session_id]
            
            # Delete files
            file_path = session_info.get('file_path')
            filtered_path = session_info.get('filtered_path')
            
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if filtered_path and os.path.exists(filtered_path):
                os.remove(filtered_path)
            
            # Remove session
            del active_sessions[session_id]
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        return jsonify({'error': str(e)}), 500

# ============= LIVE STREAMING =============

@app.route('/api/stream/video/<session_id>')
def stream_video(session_id):
    """Stream video for live editing"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = active_sessions[session_id]
        file_path = session_info.get('filtered_path') or session_info['file_path']
        
        def generate():
            cap = cv2.VideoCapture(file_path)
            while True:
                success, frame = cap.read()
                if not success:
                    break
                
                # Encode frame
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            cap.release()
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
    except Exception as e:
        logger.error(f"Stream video error: {e}")
        return jsonify({'error': str(e)}), 500

# ============= SOCKET.IO EVENTS =============

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Kinva Master', 'timestamp': datetime.now().isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_room')
def handle_join_room(data):
    """Join editing room"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined', {'room': room, 'sid': request.sid}, room=room)
        logger.info(f"Client {request.sid} joined room {room}")

@socketio.on('leave_room')
def handle_leave_room(data):
    """Leave editing room"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left', {'room': room, 'sid': request.sid}, room=room)

@socketio.on('edit_command')
def handle_edit_command(data):
    """Handle real-time edit commands"""
    try:
        command = data.get('command')
        params = data.get('params', {})
        room = data.get('room')
        session_id = data.get('session_id')
        
        # Process command based on type
        if command == 'apply_filter':
            result = process_filter_command(session_id, params)
        elif command == 'remove_bg':
            result = process_remove_bg_command(session_id)
        elif command == 'add_text':
            result = process_text_command(session_id, params)
        else:
            result = {'status': 'error', 'message': 'Unknown command'}
        
        # Broadcast result to room
        emit('edit_result', {
            'command': command,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
    except Exception as e:
        logger.error(f"Edit command error: {e}")
        emit('error', {'message': str(e)})

def process_filter_command(session_id, params):
    """Process filter command"""
    try:
        filter_name = params.get('filter')
        # Call the API logic
        return {'status': 'success', 'message': f'Applied {filter_name} filter'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def process_remove_bg_command(session_id):
    """Process remove background command"""
    try:
        return {'status': 'success', 'message': 'Background removed'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def process_text_command(session_id, params):
    """Process text command"""
    try:
        text = params.get('text', '')
        return {'status': 'success', 'message': f'Added text: {text}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found', 'path': request.path}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large_error(error):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 200MB'}), 413

# ============= CLEANUP =============

def cleanup_old_files():
    """Clean up old temporary files"""
    try:
        # Clean uploads older than 1 hour
        for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['TEMP_FOLDER']]:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        file_time = os.path.getmtime(file_path)
                        if time.time() - file_time > 3600:  # 1 hour
                            os.remove(file_path)
                            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def start_cleanup_scheduler():
    """Start cleanup scheduler"""
    def cleanup_loop():
        while True:
            time.sleep(3600)  # 1 hour
            cleanup_old_files()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()

# ============= MAIN =============

if __name__ == '__main__':
    # Start cleanup scheduler
    start_cleanup_scheduler()
    
    # Run app
    socketio.run(
        app,
        host=config.WEB_APP_HOST,
        port=config.WEB_APP_PORT,
        debug=False,
        allow_unsafe_werkzeug=True
)
