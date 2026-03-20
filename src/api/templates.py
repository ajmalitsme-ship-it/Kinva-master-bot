"""
Templates API - Template management endpoints
Author: @kinva_master
"""

import logging
import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from ..database import db
from ..config import Config
from ..editors.canva_editor import canva_editor
from ..utils import slugify, format_file_size

logger = logging.getLogger(__name__)

templates_bp = Blueprint('templates', __name__, url_prefix='/api/v1/templates')


class TemplatesAPI:
    """Templates API endpoints"""
    
    @staticmethod
    @templates_bp.route('', methods=['GET'])
    def get_templates():
        """Get templates list"""
        try:
            category = request.args.get('category')
            template_type = request.args.get('type')
            limit = request.args.get('limit', 50, type=int)
            include_premium = request.args.get('premium', 'false').lower() == 'true'
            
            # Check if user is premium
            user_id = None
            is_premium = False
            try:
                user_id = get_jwt_identity()
                user = db.get_user(user_id)
                is_premium = user.get('is_premium', False) if user else False
            except:
                pass
            
            # Get templates
            templates = db.get_templates(
                category=category,
                template_type=template_type,
                limit=limit,
                include_premium=include_premium or is_premium
            )
            
            # Add user-specific data
            for template in templates:
                if user_id:
                    template['is_favorite'] = db.is_template_favorite(user_id, template['id'])
                    template['is_used'] = db.has_user_used_template(user_id, template['id'])
            
            return jsonify(templates)
            
        except Exception as e:
            logger.error(f"Get templates error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/categories', methods=['GET'])
    def get_categories():
        """Get template categories"""
        try:
            categories = db.get_template_categories()
            
            return jsonify(categories)
            
        except Exception as e:
            logger.error(f"Get categories error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/<int:template_id>', methods=['GET'])
    def get_template(template_id):
        """Get specific template"""
        try:
            template = db.get_template(template_id)
            
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
            # Check premium
            if template.get('is_premium'):
                user_id = None
                try:
                    user_id = get_jwt_identity()
                    user = db.get_user(user_id)
                    if not user or not user.get('is_premium'):
                        return jsonify({'error': 'Premium template requires premium subscription'}), 403
                except:
                    return jsonify({'error': 'Login required for premium template'}), 401
            
            # Increment view count
            db.increment_template_views(template_id)
            
            # Parse template data
            if isinstance(template['template_data'], str):
                template['template_data'] = json.loads(template['template_data'])
            
            return jsonify(template)
            
        except Exception as e:
            logger.error(f"Get template error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/<int:template_id>/use', methods=['POST'])
    @jwt_required()
    def use_template(template_id):
        """Use template to create new design"""
        try:
            user_id = get_jwt_identity()
            template = db.get_template(template_id)
            
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
            # Check premium
            if template.get('is_premium'):
                user = db.get_user(user_id)
                if not user or not user.get('is_premium'):
                    return jsonify({'error': 'Premium template requires premium subscription'}), 403
            
            # Parse template data
            template_data = template['template_data']
            if isinstance(template_data, str):
                template_data = json.loads(template_data)
            
            # Create design from template
            design_data = template_data.copy()
            design_data['title'] = f"From {template['title']}"
            design_data['created_at'] = datetime.now().isoformat()
            design_data['updated_at'] = datetime.now().isoformat()
            
            # Save design
            design_id = db.save_design(
                user_id=user_id,
                title=design_data['title'],
                design_data=json.dumps(design_data),
                thumbnail=template.get('thumbnail'),
                width=design_data.get('width', 1920),
                height=design_data.get('height', 1080)
            )
            
            # Increment template usage
            db.increment_template_usage(template_id)
            db.record_template_use(user_id, template_id)
            
            return jsonify({
                'success': True,
                'design_id': design_id,
                'message': f'Design created from {template["title"]}'
            })
            
        except Exception as e:
            logger.error(f"Use template error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/<int:template_id>/preview', methods=['GET'])
    def preview_template(template_id):
        """Get template preview image"""
        try:
            template = db.get_template(template_id)
            
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
            if template.get('thumbnail') and os.path.exists(template['thumbnail']):
                return send_file(template['thumbnail'], mimetype='image/jpeg')
            
            # Generate preview from template data
            template_data = template['template_data']
            if isinstance(template_data, str):
                template_data = json.loads(template_data)
            
            # Render preview
            image = canva_editor.render(template_data)
            
            # Save thumbnail
            filename = f"template_{template_id}_{int(datetime.now().timestamp())}.jpg"
            filepath = os.path.join(Config.THUMBNAIL_DIR, filename)
            image.save(filepath, format='JPEG', quality=85)
            
            # Update template thumbnail
            db.update_template(template_id, {'thumbnail': filepath})
            
            return send_file(filepath, mimetype='image/jpeg')
            
        except Exception as e:
            logger.error(f"Preview template error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/favorites', methods=['GET'])
    @jwt_required()
    def get_favorites():
        """Get user's favorite templates"""
        try:
            user_id = get_jwt_identity()
            favorites = db.get_user_favorite_templates(user_id)
            
            return jsonify(favorites)
            
        except Exception as e:
            logger.error(f"Get favorites error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/<int:template_id>/favorite', methods=['POST'])
    @jwt_required()
    def add_favorite(template_id):
        """Add template to favorites"""
        try:
            user_id = get_jwt_identity()
            template = db.get_template(template_id)
            
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
            db.add_template_favorite(user_id, template_id)
            
            return jsonify({'success': True, 'message': 'Added to favorites'})
            
        except Exception as e:
            logger.error(f"Add favorite error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/<int:template_id>/favorite', methods=['DELETE'])
    @jwt_required()
    def remove_favorite(template_id):
        """Remove template from favorites"""
        try:
            user_id = get_jwt_identity()
            db.remove_template_favorite(user_id, template_id)
            
            return jsonify({'success': True, 'message': 'Removed from favorites'})
            
        except Exception as e:
            logger.error(f"Remove favorite error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/popular', methods=['GET'])
    def get_popular_templates():
        """Get most popular templates"""
        try:
            limit = request.args.get('limit', 10, type=int)
            templates = db.get_popular_templates(limit=limit)
            
            return jsonify(templates)
            
        except Exception as e:
            logger.error(f"Get popular templates error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/recent', methods=['GET'])
    def get_recent_templates():
        """Get recently added templates"""
        try:
            limit = request.args.get('limit', 10, type=int)
            templates = db.get_recent_templates(limit=limit)
            
            return jsonify(templates)
            
        except Exception as e:
            logger.error(f"Get recent templates error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @templates_bp.route('/search', methods=['GET'])
    def search_templates():
        """Search templates"""
        try:
            query = request.args.get('q', '')
            category = request.args.get('category')
            limit = request.args.get('limit', 50, type=int)
            
            if not query:
                return jsonify({'error': 'Search query required'}), 400
            
            templates = db.search_templates(query, category=category, limit=limit)
            
            return jsonify(templates)
            
        except Exception as e:
            logger.error(f"Search templates error: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================
    # ADMIN ENDPOINTS
    # ============================================
    
    @staticmethod
    @templates_bp.route('/admin/create', methods=['POST'])
    @jwt_required()
    def create_template():
        """Create new template (admin only)"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            # Check admin
            if user.get('telegram_id') not in Config.ADMIN_IDS:
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
    @templates_bp.route('/admin/<int:template_id>', methods=['PUT'])
    @jwt_required()
    def update_template(template_id):
        """Update template (admin only)"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            # Check admin
            if user.get('telegram_id') not in Config.ADMIN_IDS:
                return jsonify({'error': 'Admin access required'}), 403
            
            template = db.get_template(template_id)
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
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
    @templates_bp.route('/admin/<int:template_id>', methods=['DELETE'])
    @jwt_required()
    def delete_template(template_id):
        """Delete template (admin only)"""
        try:
            user_id = get_jwt_identity()
            user = db.get_user(user_id)
            
            # Check admin
            if user.get('telegram_id') not in Config.ADMIN_IDS:
                return jsonify({'error': 'Admin access required'}), 403
            
            template = db.get_template(template_id)
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
            # Delete thumbnail if exists
            if template.get('thumbnail') and os.path.exists(template['thumbnail']):
                os.remove(template['thumbnail'])
            
            db.delete_template(template_id)
            
            return jsonify({'success': True, 'message': 'Template deleted successfully'})
            
        except Exception as e:
            logger.error(f"Delete template error: {e}")
            return jsonify({'error': str(e)}), 500
