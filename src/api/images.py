"""
Images API - Image processing endpoints
Author: @kinva_master
"""

import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from ..database import db
from ..processors.image_processor import image_processor
from ..processors.watermark import watermark
from ..config import Config
from ..utils import allowed_file, get_image_info, format_file_size

logger = logging.getLogger(__name__)

images_bp = Blueprint('images', __name__, url_prefix='/api/v1/images')


class ImagesAPI:
    """Images API endpoints"""
    
    @staticmethod
    @images_bp.route('', methods=['GET'])
    @jwt_required()
    def get_images():
        """Get user images"""
        try:
            user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            
            images = db.get_user_images(user_id, page=page, limit=limit)
            
            return jsonify(images)
            
        except Exception as e:
            logger.error(f"Get images error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/upload', methods=['POST'])
    @jwt_required()
    def upload_image():
        """Upload image file"""
        try:
            user_id = get_jwt_identity()
            
            if 'image' not in request.files:
                return jsonify({'error': 'No image file'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename, Config.ALLOWED_IMAGES):
                return jsonify({'error': 'Invalid file format'}), 400
            
            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > Config.MAX_IMAGE_SIZE:
                return jsonify({'error': f'File too large. Max: {format_file_size(Config.MAX_IMAGE_SIZE)}'}), 400
            
            # Save file
            filename = secure_filename(file.filename)
            file_id = f"{user_id}_{int(datetime.now().timestamp())}_{filename}"
            filepath = os.path.join(Config.UPLOAD_DIR, file_id)
            file.save(filepath)
            
            # Get image info
            info = get_image_info(filepath)
            
            # Save to database
            image_id = db.save_image(
                user_id=user_id,
                title=filename,
                file_path=filepath,
                width=info.get('width'),
                height=info.get('height'),
                file_size=size,
                format=info.get('format')
            )
            
            return jsonify({
                'success': True,
                'id': image_id,
                'info': info
            })
            
        except Exception as e:
            logger.error(f"Upload image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>', methods=['GET'])
    @jwt_required()
    def get_image(image_id):
        """Get image details"""
        try:
            user_id = get_jwt_identity()
            image = db.get_image(image_id)
            
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            return jsonify(image)
            
        except Exception as e:
            logger.error(f"Get image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>', methods=['DELETE'])
    @jwt_required()
    def delete_image(image_id):
        """Delete image"""
        try:
            user_id = get_jwt_identity()
            image = db.get_image(image_id)
            
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            # Delete file
            if os.path.exists(image['file_path']):
                os.remove(image['file_path'])
            
            db.delete_image(image_id)
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Delete image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/process', methods=['POST'])
    @jwt_required()
    def process_image(image_id):
        """Process image with filters"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image = db.get_image(image_id)
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            filters = data.get('filters', [])
            adjustments = data.get('adjustments', {})
            
            # Check premium for certain filters
            user = db.get_user(user_id)
            premium_filters = ['neon', 'sketch', 'oil_paint', 'watercolor', 'pixelate']
            
            if not user.get('is_premium'):
                # Filter out premium filters
                filters = [f for f in filters if f not in premium_filters]
            
            # Process image
            output_path = image_processor.process(
                image['file_path'],
                filters=filters,
                adjustments=adjustments
            )
            
            # Add watermark for free users
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            # Update stats
            db.increment_exports(user_id)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"processed_{image['title']}")
            
        except Exception as e:
            logger.error(f"Process image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/background-removal', methods=['POST'])
    @jwt_required()
    def remove_background(image_id):
        """Remove image background (premium)"""
        try:
            user_id = get_jwt_identity()
            image = db.get_image(image_id)
            
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            # Check premium
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                return jsonify({'error': 'Background removal requires premium'}), 403
            
            # Remove background
            output_path = image_processor.remove_background(image['file_path'])
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"nobg_{image['title']}")
            
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/resize', methods=['POST'])
    @jwt_required()
    def resize_image(image_id):
        """Resize image"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image = db.get_image(image_id)
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            width = data.get('width')
            height = data.get('height')
            maintain_aspect = data.get('maintain_aspect', True)
            
            if not width and not height:
                return jsonify({'error': 'Width or height required'}), 400
            
            # Resize image
            output_path = image_processor.resize(
                image['file_path'],
                width=width,
                height=height,
                maintain_aspect=maintain_aspect
            )
            
            # Add watermark for free users
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"resized_{image['title']}")
            
        except Exception as e:
            logger.error(f"Resize image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/crop', methods=['POST'])
    @jwt_required()
    def crop_image(image_id):
        """Crop image"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image = db.get_image(image_id)
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            x = data.get('x')
            y = data.get('y')
            width = data.get('width')
            height = data.get('height')
            
            if None in (x, y, width, height):
                return jsonify({'error': 'x, y, width, height required'}), 400
            
            # Crop image
            output_path = image_processor.crop(image['file_path'], x, y, width, height)
            
            # Add watermark for free users
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"cropped_{image['title']}")
            
        except Exception as e:
            logger.error(f"Crop image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/rotate', methods=['POST'])
    @jwt_required()
    def rotate_image(image_id):
        """Rotate image"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image = db.get_image(image_id)
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            angle = data.get('angle', 0)
            
            # Rotate image
            output_path = image_processor.rotate(image['file_path'], angle)
            
            # Add watermark for free users
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"rotated_{image['title']}")
            
        except Exception as e:
            logger.error(f"Rotate image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/flip', methods=['POST'])
    @jwt_required()
    def flip_image(image_id):
        """Flip image"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image = db.get_image(image_id)
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            direction = data.get('direction', 'horizontal')
            
            # Flip image
            output_path = image_processor.flip(image['file_path'], direction)
            
            # Add watermark for free users
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"flipped_{image['title']}")
            
        except Exception as e:
            logger.error(f"Flip image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/compress', methods=['POST'])
    @jwt_required()
    def compress_image(image_id):
        """Compress image"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image = db.get_image(image_id)
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            quality = data.get('quality', 70)
            
            # Check premium for high compression
            user = db.get_user(user_id)
            if quality < 50 and not user.get('is_premium'):
                quality = 50
            
            # Compress image
            output_path = image_processor.compress(image['file_path'], quality=quality)
            
            # Add watermark for free users
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"compressed_{image['title']}")
            
        except Exception as e:
            logger.error(f"Compress image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/<int:image_id>/convert', methods=['POST'])
    @jwt_required()
    def convert_image(image_id):
        """Convert image format"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image = db.get_image(image_id)
            if not image or image['user_id'] != user_id:
                return jsonify({'error': 'Image not found'}), 404
            
            format_type = data.get('format', 'png')
            
            # Convert image
            output_path = image_processor.convert_format(image['file_path'], format_type)
            
            # Add watermark for free users
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"converted_{image['title']}.{format_type}")
            
        except Exception as e:
            logger.error(f"Convert image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @images_bp.route('/collage', methods=['POST'])
    @jwt_required()
    def create_collage():
        """Create collage from multiple images"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            image_ids = data.get('image_ids', [])
            rows = data.get('rows', 2)
            cols = data.get('cols', 2)
            spacing = data.get('spacing', 10)
            background_color = data.get('background_color', '#ffffff')
            
            if len(image_ids) < 2:
                return jsonify({'error': 'Need at least 2 images'}), 400
            
            # Get image paths
            image_paths = []
            for image_id in image_ids:
                image = db.get_image(image_id)
                if image and image['user_id'] == user_id:
                    image_paths.append(image['file_path'])
            
            if len(image_paths) < 2:
                return jsonify({'error': 'Valid images not found'}), 404
            
            # Create collage
            output_path = image_processor.create_collage(
                image_paths, rows, cols, spacing, background_color
            )
            
            # Add watermark for free users
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                output_path = watermark.add_image_watermark(output_path)
            
            return send_file(output_path, as_attachment=True, 
                           download_name="collage.jpg")
            
        except Exception as e:
            logger.error(f"Create collage error: {e}")
            return jsonify({'error': str(e)}), 500
