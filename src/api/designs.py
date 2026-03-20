"""
Designs API - Canva-style design management
Author: @kinva_master
"""

import logging
import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from PIL import Image

from ..database import db
from ..editors.canva_editor import canva_editor
from ..processors.watermark import watermark
from ..config import Config
from ..utils import slugify, format_file_size

logger = logging.getLogger(__name__)

designs_bp = Blueprint('designs', __name__, url_prefix='/api/v1/designs')


class DesignsAPI:
    """Designs API endpoints"""
    
    @staticmethod
    @designs_bp.route('', methods=['GET'])
    @jwt_required()
    def get_designs():
        """Get user designs"""
        try:
            user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            category = request.args.get('category')
            
            designs = db.get_user_designs(user_id, page=page, limit=limit, category=category)
            
            return jsonify(designs)
            
        except Exception as e:
            logger.error(f"Get designs error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('', methods=['POST'])
    @jwt_required()
    def create_design():
        """Create new design"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Get canvas size
            size = data.get('size', 'custom')
            width = data.get('width', 1920)
            height = data.get('height', 1080)
            
            if size in canva_editor.canvas_sizes:
                width, height = canva_editor.canvas_sizes[size]
            
            background = data.get('background', {
                'type': 'color',
                'value': '#ffffff'
            })
            
            # Create design
            design = canva_editor.create_design(
                size=(width, height),
                background_color=background.get('value', '#ffffff')
            )
            design['title'] = data.get('title', 'Untitled Design')
            
            # Save to database
            design_id = db.save_design(
                user_id=user_id,
                title=design['title'],
                design_data=json.dumps(design),
                thumbnail=data.get('thumbnail'),
                width=width,
                height=height
            )
            
            return jsonify({
                'success': True,
                'id': design_id,
                'design': design
            }), 201
            
        except Exception as e:
            logger.error(f"Create design error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/<int:design_id>', methods=['GET'])
    @jwt_required()
    def get_design(design_id):
        """Get specific design"""
        try:
            user_id = get_jwt_identity()
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            # Parse design data
            if isinstance(design['design_data'], str):
                design['design_data'] = json.loads(design['design_data'])
            
            return jsonify(design)
            
        except Exception as e:
            logger.error(f"Get design error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/<int:design_id>', methods=['PUT'])
    @jwt_required()
    def update_design(design_id):
        """Update design"""
        try:
            user_id = get_jwt_identity()
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            data = request.get_json()
            
            updates = {}
            if 'title' in data:
                updates['title'] = data['title']
            if 'design_data' in data:
                updates['design_data'] = json.dumps(data['design_data'])
            if 'thumbnail' in data:
                updates['thumbnail'] = data['thumbnail']
            
            if updates:
                db.update_design(design_id, updates)
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Update design error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/<int:design_id>', methods=['DELETE'])
    @jwt_required()
    def delete_design(design_id):
        """Delete design"""
        try:
            user_id = get_jwt_identity()
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            # Delete thumbnail if exists
            if design.get('thumbnail') and os.path.exists(design['thumbnail']):
                os.remove(design['thumbnail'])
            
            db.delete_design(design_id)
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Delete design error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/<int:design_id>/export', methods=['POST'])
    @jwt_required()
    def export_design(design_id):
        """Export design as image"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            design = db.get_design(design_id)
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            format_type = data.get('format', 'png')
            quality = data.get('quality', 95)
            transparent = data.get('transparent', False)
            
            # Check export limit
            user = db.get_user(user_id)
            if not user.get('is_premium'):
                stats = db.get_user_stats(user_id)
                if stats.get('exports_today', 0) >= Config.FREE_DESIGN_EXPORTS:
                    return jsonify({'error': 'Daily export limit reached'}), 403
            
            # Parse design data
            design_data = design['design_data']
            if isinstance(design_data, str):
                design_data = json.loads(design_data)
            
            # Render design
            image = canva_editor.render(design_data)
            
            # Add watermark for free users
            if not user.get('is_premium'):
                image = watermark.add_text_watermark(image)
            
            # Save to temporary file
            filename = f"design_{slugify(design['title'])}_{int(datetime.now().timestamp())}.{format_type}"
            filepath = os.path.join(Config.OUTPUT_DIR, filename)
            
            if format_type.lower() == 'png':
                image.save(filepath, format='PNG', optimize=True)
            elif format_type.lower() == 'jpg' or format_type.lower() == 'jpeg':
                image.save(filepath, format='JPEG', quality=quality, optimize=True)
            elif format_type.lower() == 'webp':
                image.save(filepath, format='WEBP', quality=quality)
            else:
                image.save(filepath, format=format_type.upper(), quality=quality)
            
            # Update stats
            db.increment_exports(user_id)
            db.increment_design_export(design_id)
            
            return send_file(filepath, as_attachment=True, download_name=filename)
            
        except Exception as e:
            logger.error(f"Export design error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/<int:design_id>/duplicate', methods=['POST'])
    @jwt_required()
    def duplicate_design(design_id):
        """Duplicate design"""
        try:
            user_id = get_jwt_identity()
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            # Parse design data
            design_data = design['design_data']
            if isinstance(design_data, str):
                design_data = json.loads(design_data)
            
            # Create new design
            new_design = design_data.copy()
            new_design['title'] = f"{design['title']} (Copy)"
            new_design['id'] = None
            
            # Save to database
            new_id = db.save_design(
                user_id=user_id,
                title=new_design['title'],
                design_data=json.dumps(new_design),
                thumbnail=design.get('thumbnail'),
                width=design.get('width'),
                height=design.get('height')
            )
            
            return jsonify({
                'success': True,
                'id': new_id,
                'message': 'Design duplicated successfully'
            })
            
        except Exception as e:
            logger.error(f"Duplicate design error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/<int:design_id>/share', methods=['POST'])
    @jwt_required()
    def share_design(design_id):
        """Generate shareable link for design"""
        try:
            user_id = get_jwt_identity()
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Not found'}), 404
            
            # Generate share token
            share_token = db.create_share_token(design_id, user_id)
            share_url = f"{Config.WEBAPP_URL}/share/{share_token}"
            
            # Increment share count
            db.increment_design_shares(design_id)
            
            return jsonify({
                'success': True,
                'share_url': share_url,
                'share_token': share_token
            })
            
        except Exception as e:
            logger.error(f"Share design error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/add-text', methods=['POST'])
    @jwt_required()
    def add_text():
        """Add text element to design"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            design_id = data.get('design_id')
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Design not found'}), 404
            
            # Parse design data
            design_data = design['design_data']
            if isinstance(design_data, str):
                design_data = json.loads(design_data)
            
            # Add text
            text = data.get('text', '')
            x = data.get('x', 100)
            y = data.get('y', 100)
            font_size = data.get('font_size', 24)
            font_name = data.get('font_name', 'Arial')
            font_color = data.get('font_color', '#000000')
            bold = data.get('bold', False)
            italic = data.get('italic', False)
            alignment = data.get('alignment', 'left')
            
            design_data = canva_editor.add_text(
                design_data, text, x, y,
                font_size, font_name, font_color,
                bold, italic, alignment
            )
            
            # Update design
            db.update_design(design_id, {
                'design_data': json.dumps(design_data)
            })
            
            return jsonify({
                'success': True,
                'design': design_data
            })
            
        except Exception as e:
            logger.error(f"Add text error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/add-image', methods=['POST'])
    @jwt_required()
    def add_image():
        """Add image element to design"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            design_id = data.get('design_id')
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Design not found'}), 404
            
            # Parse design data
            design_data = design['design_data']
            if isinstance(design_data, str):
                design_data = json.loads(design_data)
            
            # Add image
            image_url = data.get('image_url')
            x = data.get('x', 0)
            y = data.get('y', 0)
            width = data.get('width')
            height = data.get('height')
            
            # Download image from URL (simplified)
            import requests
            response = requests.get(image_url)
            temp_path = os.path.join(Config.TEMP_DIR, f"temp_{int(datetime.now().timestamp())}.jpg")
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            design_data = canva_editor.add_image(
                design_data, temp_path, x, y, width, height
            )
            
            # Cleanup
            os.remove(temp_path)
            
            # Update design
            db.update_design(design_id, {
                'design_data': json.dumps(design_data)
            })
            
            return jsonify({
                'success': True,
                'design': design_data
            })
            
        except Exception as e:
            logger.error(f"Add image error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/add-shape', methods=['POST'])
    @jwt_required()
    def add_shape():
        """Add shape element to design"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            design_id = data.get('design_id')
            design = db.get_design(design_id)
            
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Design not found'}), 404
            
            # Parse design data
            design_data = design['design_data']
            if isinstance(design_data, str):
                design_data = json.loads(design_data)
            
            # Add shape
            shape_type = data.get('shape_type', 'rectangle')
            x = data.get('x', 0)
            y = data.get('y', 0)
            width = data.get('width', 100)
            height = data.get('height', 100)
            fill_color = data.get('fill_color', '#ff0000')
            stroke_color = data.get('stroke_color', '#000000')
            stroke_width = data.get('stroke_width', 1)
            
            design_data = canva_editor.add_shape(
                design_data, shape_type, x, y,
                width, height, fill_color, stroke_color, stroke_width
            )
            
            # Update design
            db.update_design(design_id, {
                'design_data': json.dumps(design_data)
            })
            
            return jsonify({
                'success': True,
                'design': design_data
            })
            
        except Exception as e:
            logger.error(f"Add shape error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/remove-element', methods=['POST'])
    @jwt_required()
    def remove_element():
        """Remove element from design"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            design_id = data.get('design_id')
            element_id = data.get('element_id')
            
            design = db.get_design(design_id)
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Design not found'}), 404
            
            # Parse design data
            design_data = design['design_data']
            if isinstance(design_data, str):
                design_data = json.loads(design_data)
            
            # Remove element
            design_data = canva_editor.remove_element(design_data, element_id)
            
            # Update design
            db.update_design(design_id, {
                'design_data': json.dumps(design_data)
            })
            
            return jsonify({
                'success': True,
                'design': design_data
            })
            
        except Exception as e:
            logger.error(f"Remove element error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @designs_bp.route('/update-element', methods=['POST'])
    @jwt_required()
    def update_element():
        """Update element properties"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            design_id = data.get('design_id')
            element_id = data.get('element_id')
            updates = data.get('updates', {})
            
            design = db.get_design(design_id)
            if not design or design['user_id'] != user_id:
                return jsonify({'error': 'Design not found'}), 404
            
            # Parse design data
            design_data = design['design_data']
            if isinstance(design_data, str):
                design_data = json.loads(design_data)
            
            # Update element
            design_data = canva_editor.update_element(design_data, element_id, updates)
            
            # Update design
            db.update_design(design_id, {
                'design_data': json.dumps(design_data)
            })
            
            return jsonify({
                'success': True,
                'design': design_data
            })
            
        except Exception as e:
            logger.error(f"Update element error: {e}")
            return jsonify({'error': str(e)}), 500
