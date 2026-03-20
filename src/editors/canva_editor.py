"""
Canva Editor - Canva-style design editor
Author: @kinva_master
"""

import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

from ..config import Config
from ..utils import slugify, generate_uuid

logger = logging.getLogger(__name__)

class CanvaEditor:
    """Canva-style design editor with full features"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'designs'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default canvas sizes for different platforms
        self.canvas_sizes = {
            # Social Media
            'instagram_post': (1080, 1080),
            'instagram_story': (1080, 1920),
            'instagram_reel': (1080, 1920),
            'facebook_post': (1200, 630),
            'facebook_cover': (851, 315),
            'facebook_story': (1080, 1920),
            'twitter_post': (1600, 900),
            'twitter_header': (1500, 500),
            'linkedin_post': (1200, 627),
            'linkedin_banner': (1584, 396),
            'pinterest_pin': (1000, 1500),
            'tiktok_video': (1080, 1920),
            'youtube_thumbnail': (1280, 720),
            'youtube_banner': (2560, 1440),
            'youtube_short': (1080, 1920),
            
            # Business
            'presentation': (1920, 1080),
            'business_card': (1050, 600),
            'flyer': (2550, 3300),
            'poster': (3300, 5100),
            'banner': (728, 90),
            'logo': (500, 500),
            'invoice': (800, 1200),
            'certificate': (1920, 1350),
            
            # Standard
            'square': (1080, 1080),
            'portrait': (1080, 1350),
            'landscape': (1920, 1080),
            'a4': (2480, 3508),
            'a3': (3508, 4961),
            'letter': (2550, 3300),
        }
        
        # Available fonts
        self.fonts = self._load_fonts()
        
        # Available shapes
        self.shapes = {
            'rectangle': self._draw_rectangle,
            'rounded_rectangle': self._draw_rounded_rectangle,
            'circle': self._draw_circle,
            'ellipse': self._draw_ellipse,
            'triangle': self._draw_triangle,
            'line': self._draw_line,
            'arrow': self._draw_arrow,
            'double_arrow': self._draw_double_arrow,
            'star': self._draw_star,
            'heart': self._draw_heart,
            'cloud': self._draw_cloud,
            'speech_bubble': self._draw_speech_bubble,
            'thought_bubble': self._draw_thought_bubble,
            'lightning': self._draw_lightning,
            'sparkle': self._draw_sparkle,
            'checkmark': self._draw_checkmark,
            'cross': self._draw_cross,
            'plus': self._draw_plus,
        }
        
        # Blend modes
        self.blend_modes = ['normal', 'multiply', 'screen', 'overlay', 'darken', 
                           'lighten', 'color_dodge', 'color_burn', 'hard_light', 
                           'soft_light', 'difference', 'exclusion']
    
    def _load_fonts(self) -> List[str]:
        """Load available fonts"""
        fonts = []
        font_dir = Path(Config.FONTS_DIR)
        
        if font_dir.exists():
            for font_file in font_dir.glob("*.ttf"):
                fonts.append(font_file.stem)
        
        # Add default fonts if none found
        if not fonts:
            fonts = ['Arial', 'Roboto', 'OpenSans', 'Poppins', 'Montserrat', 
                    'Lato', 'PlayfairDisplay', 'Pacifico', 'Lobster', 'DancingScript']
        
        return sorted(fonts)
    
    def create_design(self, size: Tuple[int, int] = (1920, 1080),
                      background_color: str = '#ffffff',
                      background_image: str = None) -> Dict:
        """Create new design"""
        design = {
            'id': generate_uuid(),
            'title': 'Untitled Design',
            'width': size[0],
            'height': size[1],
            'background': {
                'type': 'color',
                'value': background_color
            },
            'elements': [],
            'layers': [],
            'grid': {
                'enabled': False,
                'size': 20,
                'color': '#cccccc'
            },
            'guides': [],
            'metadata': {
                'created_by': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        if background_image:
            design['background'] = {
                'type': 'image',
                'value': background_image,
                'opacity': 1.0,
                'fit': 'cover'
            }
        
        return design
    
    def add_element(self, design: Dict, element_type: str, 
                   element_data: Dict) -> Dict:
        """Add element to design"""
        element = {
            'id': generate_uuid(),
            'type': element_type,
            'data': element_data,
            'position': element_data.get('position', {'x': 0, 'y': 0}),
            'size': element_data.get('size', {'width': 100, 'height': 100}),
            'rotation': element_data.get('rotation', 0),
            'opacity': element_data.get('opacity', 1.0),
            'blend_mode': element_data.get('blend_mode', 'normal'),
            'z_index': len(design['elements']),
            'locked': False,
            'visible': True,
            'group': element_data.get('group', None),
            'effects': element_data.get('effects', []),
            'filters': element_data.get('filters', []),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        design['elements'].append(element)
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def add_text(self, design: Dict, text: str, x: int, y: int,
                 font_size: int = 24, font_name: str = 'Arial',
                 font_color: str = '#000000', bold: bool = False,
                 italic: bool = False, underline: bool = False,
                 alignment: str = 'left', line_height: float = 1.2,
                 letter_spacing: float = 0, shadow: bool = False,
                 shadow_color: str = '#000000', shadow_offset: int = 2,
                 outline: bool = False, outline_color: str = '#ffffff',
                 outline_width: int = 1) -> Dict:
        """Add text element with rich formatting"""
        element_data = {
            'text': text,
            'x': x,
            'y': y,
            'font_size': font_size,
            'font_name': font_name,
            'font_color': font_color,
            'bold': bold,
            'italic': italic,
            'underline': underline,
            'alignment': alignment,
            'line_height': line_height,
            'letter_spacing': letter_spacing,
            'shadow': shadow,
            'shadow_color': shadow_color,
            'shadow_offset': shadow_offset,
            'outline': outline,
            'outline_color': outline_color,
            'outline_width': outline_width
        }
        
        return self.add_element(design, 'text', element_data)
    
    def add_image(self, design: Dict, image_path: str, x: int, y: int,
                  width: int = None, height: int = None,
                  rotation: float = 0, opacity: float = 1.0,
                  crop: Dict = None, filters: List = None) -> Dict:
        """Add image element with cropping and filters"""
        element_data = {
            'image_path': image_path,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'rotation': rotation,
            'opacity': opacity,
            'crop': crop or {'x': 0, 'y': 0, 'width': 1, 'height': 1},
            'filters': filters or []
        }
        
        return self.add_element(design, 'image', element_data)
    
    def add_shape(self, design: Dict, shape_type: str, x: int, y: int,
                  width: int = 100, height: int = 100,
                  fill_color: str = '#ff0000', fill_opacity: float = 1.0,
                  stroke_color: str = '#000000', stroke_width: int = 1,
                  stroke_opacity: float = 1.0, rotation: float = 0,
                  shadow: bool = False, shadow_color: str = '#000000',
                  shadow_offset: int = 2, shadow_blur: int = 4) -> Dict:
        """Add shape element with styling"""
        element_data = {
            'shape_type': shape_type,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'fill_color': fill_color,
            'fill_opacity': fill_opacity,
            'stroke_color': stroke_color,
            'stroke_width': stroke_width,
            'stroke_opacity': stroke_opacity,
            'rotation': rotation,
            'shadow': shadow,
            'shadow_color': shadow_color,
            'shadow_offset': shadow_offset,
            'shadow_blur': shadow_blur
        }
        
        return self.add_element(design, 'shape', element_data)
    
    def add_background(self, design: Dict, bg_type: str, value: str,
                      opacity: float = 1.0, fit: str = 'cover') -> Dict:
        """Add background to design"""
        design['background'] = {
            'type': bg_type,
            'value': value,
            'opacity': opacity,
            'fit': fit
        }
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def remove_element(self, design: Dict, element_id: str) -> Dict:
        """Remove element from design"""
        design['elements'] = [e for e in design['elements'] if e['id'] != element_id]
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def update_element(self, design: Dict, element_id: str, 
                      updates: Dict) -> Dict:
        """Update element properties"""
        for element in design['elements']:
            if element['id'] == element_id:
                for key, value in updates.items():
                    if key in ['position', 'size', 'rotation', 'opacity', 'blend_mode']:
                        element[key] = value
                    elif key in element['data']:
                        element['data'][key] = value
                element['updated_at'] = datetime.now().isoformat()
                break
        
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def duplicate_element(self, design: Dict, element_id: str) -> Dict:
        """Duplicate element"""
        for element in design['elements']:
            if element['id'] == element_id:
                new_element = element.copy()
                new_element['id'] = generate_uuid()
                new_element['position'] = {
                    'x': element['position']['x'] + 20,
                    'y': element['position']['y'] + 20
                }
                new_element['created_at'] = datetime.now().isoformat()
                new_element['updated_at'] = datetime.now().isoformat()
                design['elements'].append(new_element)
                break
        
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def group_elements(self, design: Dict, element_ids: List[str]) -> Dict:
        """Group multiple elements"""
        group_id = generate_uuid()
        group = {
            'id': group_id,
            'type': 'group',
            'elements': [],
            'position': {'x': 0, 'y': 0},
            'size': {'width': 0, 'height': 0},
            'rotation': 0,
            'opacity': 1.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Find min x and y to calculate group position
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for element in design['elements']:
            if element['id'] in element_ids:
                group['elements'].append(element)
                min_x = min(min_x, element['position']['x'])
                min_y = min(min_y, element['position']['y'])
                max_x = max(max_x, element['position']['x'] + element['size']['width'])
                max_y = max(max_y, element['position']['y'] + element['size']['height'])
        
        group['position'] = {'x': min_x, 'y': min_y}
        group['size'] = {'width': max_x - min_x, 'height': max_y - min_y}
        
        # Remove original elements and add group
        design['elements'] = [e for e in design['elements'] if e['id'] not in element_ids]
        design['elements'].append(group)
        
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def ungroup_elements(self, design: Dict, group_id: str) -> Dict:
        """Ungroup elements"""
        for element in design['elements']:
            if element['id'] == group_id and element['type'] == 'group':
                design['elements'].extend(element['elements'])
                design['elements'] = [e for e in design['elements'] if e['id'] != group_id]
                break
        
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def align_elements(self, design: Dict, element_ids: List[str], 
                      alignment: str) -> Dict:
        """Align multiple elements"""
        if not element_ids:
            return design
        
        elements = [e for e in design['elements'] if e['id'] in element_ids]
        if not elements:
            return design
        
        # Calculate bounds
        min_x = min(e['position']['x'] for e in elements)
        max_x = max(e['position']['x'] + e['size']['width'] for e in elements)
        min_y = min(e['position']['y'] for e in elements)
        max_y = max(e['position']['y'] + e['size']['height'] for e in elements)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        for element in elements:
            if alignment == 'left':
                element['position']['x'] = min_x
            elif alignment == 'right':
                element['position']['x'] = max_x - element['size']['width']
            elif alignment == 'center_horizontal':
                element['position']['x'] = center_x - element['size']['width'] / 2
            elif alignment == 'top':
                element['position']['y'] = min_y
            elif alignment == 'bottom':
                element['position']['y'] = max_y - element['size']['height']
            elif alignment == 'center_vertical':
                element['position']['y'] = center_y - element['size']['height'] / 2
        
        design['metadata']['updated_at'] = datetime.now().isoformat()
        
        return design
    
    def render(self, design: Dict) -> Image.Image:
        """Render design to image"""
        try:
            # Create canvas
            img = Image.new('RGBA', (design['width'], design['height']), 
                           (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # Add background
            self._add_background(draw, design['background'], img.size)
            
            # Add elements sorted by z_index
            for element in sorted(design['elements'], key=lambda e: e['z_index']):
                self._add_element(draw, element, img)
            
            # Add grid if enabled
            if design.get('grid', {}).get('enabled', False):
                self._add_grid(draw, design)
            
            return img
            
        except Exception as e:
            logger.error(f"Render error: {e}")
            raise
    
    def export(self, design: Dict, format: str = 'png', 
              quality: int = 95, transparent: bool = False) -> str:
        """Export design to file"""
        try:
            img = self.render(design)
            
            # Convert to RGB if not transparent
            if not transparent and format.lower() != 'png':
                img = img.convert('RGB')
            
            filename = f"design_{slugify(design['title'])}_{int(datetime.now().timestamp())}.{format}"
            filepath = os.path.join(self.output_dir, filename)
            
            if format.lower() == 'png':
                img.save(filepath, format='PNG', optimize=True)
            elif format.lower() == 'jpg' or format.lower() == 'jpeg':
                img.save(filepath, format='JPEG', quality=quality, optimize=True)
            elif format.lower() == 'webp':
                img.save(filepath, format='WEBP', quality=quality)
            elif format.lower() == 'pdf':
                img.save(filepath, format='PDF')
            else:
                img.save(filepath, format=format.upper(), quality=quality)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise
    
    def _add_background(self, draw, background, size):
        """Add background to canvas"""
        if background['type'] == 'color':
            # Solid color background
            draw.rectangle([(0, 0), size], fill=background['value'])
        
        elif background['type'] == 'gradient':
            # Linear gradient
            from PIL import ImageDraw
            width, height = size
            gradient = Image.new('RGBA', size)
            for y in range(height):
                ratio = y / height
                color = self._interpolate_color(background['start_color'], 
                                               background['end_color'], ratio)
                draw.line([(0, y), (width, y)], fill=color)
        
        elif background['type'] == 'image':
            # Image background
            try:
                bg_img = Image.open(background['value'])
                if background.get('fit') == 'cover':
                    bg_img = self._cover_fit(bg_img, size)
                elif background.get('fit') == 'contain':
                    bg_img = self._contain_fit(bg_img, size)
                else:
                    bg_img = bg_img.resize(size, Image.Resampling.LANCZOS)
                
                if background.get('opacity', 1.0) < 1.0:
                    bg_img = self._adjust_opacity(bg_img, background['opacity'])
                
                draw._image.paste(bg_img, (0, 0), bg_img)
            except Exception as e:
                logger.error(f"Background image error: {e}")
    
    def _add_grid(self, draw, design):
        """Add grid overlay"""
        grid_size = design['grid']['size']
        color = design['grid']['color']
        width, height = design['width'], design['height']
        
        for x in range(0, width, grid_size):
            draw.line([(x, 0), (x, height)], fill=color, width=1)
        
        for y in range(0, height, grid_size):
            draw.line([(0, y), (width, y)], fill=color, width=1)
    
    def _add_element(self, draw, element, canvas):
        """Add element to canvas"""
        if element['type'] == 'text':
            self._add_text_element(draw, element, canvas)
        
        elif element['type'] == 'image':
            self._add_image_element(draw, element, canvas)
        
        elif element['type'] == 'shape':
            self._add_shape_element(draw, element, canvas)
        
        elif element['type'] == 'group':
            self._add_group_element(draw, element, canvas)
    
    def _add_text_element(self, draw, element, canvas):
        """Add text element with rich formatting"""
        data = element['data']
        position = element['position']
        opacity = element['opacity']
        
        # Load font
        try:
            font_path = os.path.join(Config.FONTS_DIR, f"{data['font_name']}.ttf")
            font = ImageFont.truetype(font_path, data['font_size'])
        except:
            font = ImageFont.load_default()
        
        # Create text image
        temp_img = Image.new('RGBA', (element['size']['width'], element['size']['height']), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Draw outline
        if data.get('outline', False):
            outline_width = data.get('outline_width', 1)
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        temp_draw.text((data['x'] + dx, data['y'] + dy), data['text'],
                                      fill=data['outline_color'], font=font)
        
        # Draw shadow
        if data.get('shadow', False):
            shadow_offset = data.get('shadow_offset', 2)
            temp_draw.text((data['x'] + shadow_offset, data['y'] + shadow_offset), data['text'],
                          fill=data['shadow_color'], font=font)
        
        # Draw text
        temp_draw.text((data['x'], data['y']), data['text'], fill=data['font_color'], font=font)
        
        # Apply opacity
        if opacity < 1.0:
            temp_img = self._adjust_opacity(temp_img, opacity)
        
        # Apply rotation
        if element['rotation'] != 0:
            temp_img = temp_img.rotate(element['rotation'], expand=True, resample=Image.Resampling.BICUBIC)
        
        # Paste onto canvas
        canvas.paste(temp_img, (position['x'], position['y']), temp_img)
    
    def _add_image_element(self, draw, element, canvas):
        """Add image element with effects"""
        data = element['data']
        position = element['position']
        
        try:
            img = Image.open(data['image_path'])
            
            # Apply crop
            if data.get('crop'):
                crop = data['crop']
                w, h = img.size
                img = img.crop((crop['x'] * w, crop['y'] * h,
                               (crop['x'] + crop['width']) * w,
                               (crop['y'] + crop['height']) * h))
            
            # Resize
            if data.get('width') and data.get('height'):
                img = img.resize((data['width'], data['height']), Image.Resampling.LANCZOS)
            
            # Apply filters
            for filter_name in data.get('filters', []):
                if filter_name == 'grayscale':
                    img = img.convert('L').convert('RGB')
                elif filter_name == 'sepia':
                    img = self._apply_sepia(img)
                elif filter_name == 'blur':
                    img = img.filter(ImageFilter.GaussianBlur(radius=3))
            
            # Apply opacity
            if element['opacity'] < 1.0:
                img = self._adjust_opacity(img, element['opacity'])
            
            # Apply rotation
            if element['rotation'] != 0:
                img = img.rotate(element['rotation'], expand=True, resample=Image.Resampling.BICUBIC)
            
            # Apply blend mode
            if element['blend_mode'] != 'normal':
                img = self._apply_blend_mode(img, canvas, element['blend_mode'])
            
            # Paste onto canvas
            canvas.paste(img, (position['x'], position['y']), img if img.mode == 'RGBA' else None)
            
        except Exception as e:
            logger.error(f"Error adding image: {e}")
    
    def _add_shape_element(self, draw, element, canvas):
        """Add shape element with styling"""
        data = element['data']
        position = element['position']
        
        x1 = position['x']
        y1 = position['y']
        x2 = x1 + data['width']
        y2 = y1 + data['height']
        
        shape_type = data['shape_type']
        
        # Create shape image
        temp_img = Image.new('RGBA', (data['width'], data['height']), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        if shape_type in self.shapes:
            self.shapes[shape_type](temp_draw, 0, 0, data['width'], data['height'], data)
        
        # Apply shadow
        if data.get('shadow', False):
            shadow_img = Image.new('RGBA', (data['width'] + 10, data['height'] + 10), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_img)
            shadow_data = data.copy()
            shadow_data['fill_color'] = data['shadow_color']
            shadow_data['fill_opacity'] = 0.5
            self.shapes[shape_type](shadow_draw, data['shadow_offset'], data['shadow_offset'],
                                   data['width'], data['height'], shadow_data)
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=data.get('shadow_blur', 4)))
            canvas.paste(shadow_img, (position['x'] - data['shadow_offset'], 
                                     position['y'] - data['shadow_offset']), shadow_img)
        
        # Apply opacity
        if element['opacity'] < 1.0:
            temp_img = self._adjust_opacity(temp_img, element['opacity'])
        
        # Apply rotation
        if element['rotation'] != 0:
            temp_img = temp_img.rotate(element['rotation'], expand=True, resample=Image.Resampling.BICUBIC)
        
        # Paste onto canvas
        canvas.paste(temp_img, (position['x'], position['y']), temp_img)
    
    def _add_group_element(self, draw, element, canvas):
        """Add group element"""
        for child in element['elements']:
            child['position'] = {
                'x': child['position']['x'] + element['position']['x'],
                'y': child['position']['y'] + element['position']['y']
            }
            self._add_element(draw, child, canvas)
    
    # ============================================
    # SHAPE DRAWING METHODS
    # ============================================
    
    def _draw_rectangle(self, draw, x1, y1, x2, y2, data):
        """Draw rectangle"""
        fill = data['fill_color']
        stroke = data['stroke_color']
        stroke_width = data['stroke_width']
        
        draw.rectangle([x1, y1, x2, y2], fill=fill, outline=stroke, width=stroke_width)
    
    def _draw_rounded_rectangle(self, draw, x1, y1, x2, y2, data):
        """Draw rounded rectangle"""
        radius = min((x2 - x1), (y2 - y1)) // 4
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=stroke)
    
    def _draw_circle(self, draw, x1, y1, x2, y2, data):
        """Draw circle"""
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.ellipse([x1, y1, x2, y2], fill=fill, outline=stroke)
    
    def _draw_ellipse(self, draw, x1, y1, x2, y2, data):
        """Draw ellipse"""
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.ellipse([x1, y1, x2, y2], fill=fill, outline=stroke)
    
    def _draw_triangle(self, draw, x1, y1, x2, y2, data):
        """Draw triangle"""
        cx = (x1 + x2) // 2
        points = [(cx, y1), (x1, y2), (x2, y2)]
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.polygon(points, fill=fill, outline=stroke)
    
    def _draw_line(self, draw, x1, y1, x2, y2, data):
        """Draw line"""
        stroke = data['stroke_color']
        stroke_width = data['stroke_width']
        
        draw.line([x1, y1, x2, y2], fill=stroke, width=stroke_width)
    
    def _draw_arrow(self, draw, x1, y1, x2, y2, data):
        """Draw arrow"""
        import math
        
        stroke = data['stroke_color']
        stroke_width = data['stroke_width']
        
        # Draw line
        draw.line([x1, y1, x2, y2], fill=stroke, width=stroke_width)
        
        # Draw arrow head
        angle = math.atan2(y2 - y1, x2 - x1)
        head_size = min(20, math.sqrt((x2-x1)**2 + (y2-y1)**2) / 3)
        
        x3 = x2 - head_size * math.cos(angle - math.pi/6)
        y3 = y2 - head_size * math.sin(angle - math.pi/6)
        x4 = x2 - head_size * math.cos(angle + math.pi/6)
        y4 = y2 - head_size * math.sin(angle + math.pi/6)
        
        draw.polygon([(x2, y2), (x3, y3), (x4, y4)], fill=stroke)
    
    def _draw_double_arrow(self, draw, x1, y1, x2, y2, data):
        """Draw double arrow"""
        import math
        
        stroke = data['stroke_color']
        stroke_width = data['stroke_width']
        
        # Draw line
        draw.line([x1, y1, x2, y2], fill=stroke, width=stroke_width)
        
        # Draw arrow heads
        angle = math.atan2(y2 - y1, x2 - x1)
        head_size = min(20, math.sqrt((x2-x1)**2 + (y2-y1)**2) / 3)
        
        # Head at end
        x3 = x2 - head_size * math.cos(angle - math.pi/6)
        y3 = y2 - head_size * math.sin(angle - math.pi/6)
        x4 = x2 - head_size * math.cos(angle + math.pi/6)
        y4 = y2 - head_size * math.sin(angle + math.pi/6)
        draw.polygon([(x2, y2), (x3, y3), (x4, y4)], fill=stroke)
        
        # Head at start
        x5 = x1 + head_size * math.cos(angle - math.pi/6)
        y5 = y1 + head_size * math.sin(angle - math.pi/6)
        x6 = x1 + head_size * math.cos(angle + math.pi/6)
        y6 = y1 + head_size * math.sin(angle + math.pi/6)
        draw.polygon([(x1, y1), (x5, y5), (x6, y6)], fill=stroke)
    
    def _draw_star(self, draw, x1, y1, x2, y2, data):
        """Draw star"""
        import math
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        outer_r = min(x2 - x1, y2 - y1) // 2
        inner_r = outer_r // 2
        points = []
        
        for i in range(10):
            angle = i * math.pi * 2 / 10 - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.polygon(points, fill=fill, outline=stroke)
    
    def _draw_heart(self, draw, x1, y1, x2, y2, data):
        """Draw heart"""
        import math
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        size = min(x2 - x1, y2 - y1) // 2
        
        points = []
        for t in range(0, 360, 10):
            rad = math.radians(t)
            x = 16 * math.sin(rad) ** 3
            y = 13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad)
            x = cx + x * size / 20
            y = cy - y * size / 20
            points.append((x, y))
        
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.polygon(points, fill=fill, outline=stroke)
    
    def _draw_cloud(self, draw, x1, y1, x2, y2, data):
        """Draw cloud"""
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        r1 = (x2 - x1) // 4
        r2 = (x2 - x1) // 6
        
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.ellipse([cx - r1, cy - r2, cx + r1, cy + r2], fill=fill, outline=stroke)
        draw.ellipse([cx - r2, cy - r1, cx + r2, cy + r1], fill=fill, outline=stroke)
        draw.ellipse([cx, cy - r1, cx + r2*2, cy + r1], fill=fill, outline=stroke)
    
    def _draw_speech_bubble(self, draw, x1, y1, x2, y2, data):
        """Draw speech bubble"""
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.rounded_rectangle([x1, y1, x2, y2], radius=20, fill=fill, outline=stroke)
        
        # Draw tail
        points = [(x1 + 20, y2), (x1 + 40, y2 + 20), (x1, y2)]
        draw.polygon(points, fill=fill, outline=stroke)
    
    def _draw_thought_bubble(self, draw, x1, y1, x2, y2, data):
        """Draw thought bubble"""
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.ellipse([x1, y1, x2, y2], fill=fill, outline=stroke)
        
        # Draw thought bubbles
        r = min(x2 - x1, y2 - y1) // 8
        draw.ellipse([x1 - r, y2 - r, x1 + r, y2 + r], fill=fill, outline=stroke)
        draw.ellipse([x1 - r*2, y2 - r*2, x1, y2], fill=fill, outline=stroke)
        draw.ellipse([x1 - r*3, y2 - r*3, x1 - r, y2 - r], fill=fill, outline=stroke)
    
    def _draw_lightning(self, draw, x1, y1, x2, y2, data):
        """Draw lightning bolt"""
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        w = x2 - x1
        h = y2 - y1
        
        points = [
            (cx, y1),
            (x1 + w//4, cy),
            (cx, cy),
            (x1 + w//3, y2),
            (cx + w//4, cy + h//3),
            (cx, cy),
            (cx + w//3, cy - h//4),
            (cx, y1)
        ]
        
        fill = data['fill_color']
        stroke = data['stroke_color']
        
        draw.polygon(points, fill=fill, outline=stroke)
    
    def _draw_sparkle(self, draw, x1, y1, x2, y2, data):
        """Draw sparkle/star burst"""
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        size = min(x2 - x1, y2 - y1) // 2
        
        points = []
        for i in range(12):
            angle = i * math.pi * 2 / 12
            r = size if i % 2 == 0 else size // 2
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        
        fill = data['fill_color']
        draw.polygon(points, fill=fill)
    
    def _draw_checkmark(self, draw, x1, y1, x2, y2, data):
        """Draw checkmark"""
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        size = min(x2 - x1, y2 - y1) // 2
        
        points = [
            (cx - size//2, cy),
            (cx - size//4, cy + size//2),
            (cx + size//2, cy - size//2)
        ]
        
        stroke = data['stroke_color']
        stroke_width = data['stroke_width']
        
        draw.line(points, fill=stroke, width=stroke_width)
    
    def _draw_cross(self, draw, x1, y1, x2, y2, data):
        """Draw cross/X"""
        stroke = data['stroke_color']
        stroke_width = data['stroke_width']
        
        draw.line([x1, y1, x2, y2], fill=stroke, width=stroke_width)
        draw.line([x1, y2, x2, y1], fill=stroke, width=stroke_width)
    
    def _draw_plus(self, draw, x1, y1, x2, y2, data):
        """Draw plus sign"""
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        w = x2 - x1
        h = y2 - y1
        
        stroke = data['stroke_color']
        stroke_width = data['stroke_width']
        
        draw.line([cx, y1, cx, y2], fill=stroke, width=stroke_width)
        draw.line([x1, cy, x2, cy], fill=stroke, width=stroke_width)
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _adjust_opacity(self, img: Image.Image, opacity: float) -> Image.Image:
        """Adjust image opacity"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        alpha = img.getchannel('A')
        alpha = alpha.point(lambda p: int(p * opacity))
        img.putalpha(alpha)
        
        return img
    
    def _apply_sepia(self, img: Image.Image) -> Image.Image:
        """Apply sepia filter"""
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        width, height = img.size
        pixels = img.load()
        
        for py in range(height):
            for px in range(width):
                r, g, b = pixels[px, py]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[px, py] = (min(255, tr), min(255, tg), min(255, tb))
        
        return img
    
    def _apply_blend_mode(self, img: Image.Image, canvas: Image.Image, 
                          blend_mode: str) -> Image.Image:
        """Apply blend mode"""
        # This would implement various blend modes
        # Simplified for now
        return img
    
    def _cover_fit(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Cover fit image to size"""
        img_ratio = img.width / img.height
        target_ratio = size[0] / size[1]
        
        if img_ratio > target_ratio:
            new_width = size[0]
            new_height = int(size[0] / img_ratio)
        else:
            new_height = size[1]
            new_width = int(size[1] * img_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to center
        left = (img.width - size[0]) // 2
        top = (img.height - size[1]) // 2
        img = img.crop((left, top, left + size[0], top + size[1]))
        
        return img
    
    def _contain_fit(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Contain fit image to size"""
        img.thumbnail(size, Image.Resampling.LANCZOS)
        return img
    
    def _interpolate_color(self, color1: str, color2: str, ratio: float) -> str:
        """Interpolate between two colors"""
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"

# Create global instance
canva_editor = CanvaEditor()
