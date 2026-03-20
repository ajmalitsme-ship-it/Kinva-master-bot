"""
Image Editor - Professional image editing tools
Author: @kinva_master
"""

import os
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageChops

from ..config import Config
from ..utils import generate_uuid, slugify

logger = logging.getLogger(__name__)

class ImageEditor:
    """Professional image editing tools"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'images'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Available filters
        self.filters = {
            # Basic Filters
            'grayscale': self._apply_grayscale,
            'sepia': self._apply_sepia,
            'invert': self._apply_invert,
            'threshold': self._apply_threshold,
            'posterize': self._apply_posterize,
            'solarize': self._apply_solarize,
            
            # Color Filters
            'vintage': self._apply_vintage,
            'cinematic': self._apply_cinematic,
            'glitch': self._apply_glitch,
            'neon': self._apply_neon,
            'thermal': self._apply_thermal,
            'night_vision': self._apply_night_vision,
            'dreamy': self._apply_dreamy,
            'dramatic': self._apply_dramatic,
            'pastel': self._apply_pastel,
            'vibrant': self._apply_vibrant,
            
            # Artistic Filters
            'oil_paint': self._apply_oil_paint,
            'watercolor': self._apply_watercolor,
            'sketch': self._apply_sketch,
            'cartoon': self._apply_cartoon,
            'pixelate': self._apply_pixelate,
            'mosaic': self._apply_mosaic,
            'halftone': self._apply_halftone,
            'pointillism': self._apply_pointillism,
            
            # Effect Filters
            'blur': lambda img: img.filter(ImageFilter.GaussianBlur(radius=3)),
            'sharpen': lambda img: img.filter(ImageFilter.SHARPEN),
            'edge': lambda img: img.filter(ImageFilter.FIND_EDGES),
            'emboss': lambda img: img.filter(ImageFilter.EMBOSS),
            'contour': lambda img: img.filter(ImageFilter.CONTOUR),
            'smooth': lambda img: img.filter(ImageFilter.SMOOTH),
            'detail': lambda img: img.filter(ImageFilter.DETAIL),
            
            # Advanced Filters
            'vignette': self._apply_vignette,
            'grain': self._apply_grain,
            'glow': self._apply_glow,
            'bokeh': self._apply_bokeh,
            'tilt_shift': self._apply_tilt_shift,
            'chromatic_aberration': self._apply_chromatic_aberration,
        }
        
        # Available adjustments
        self.adjustments = {
            'brightness': self._adjust_brightness,
            'contrast': self._adjust_contrast,
            'saturation': self._adjust_saturation,
            'sharpness': self._adjust_sharpness,
            'temperature': self._adjust_temperature,
            'tint': self._adjust_tint,
            'exposure': self._adjust_exposure,
            'gamma': self._adjust_gamma,
            'highlights': self._adjust_highlights,
            'shadows': self._adjust_shadows,
            'vibrance': self._adjust_vibrance,
        }
        
        # Blend modes
        self.blend_modes = {
            'normal': self._blend_normal,
            'multiply': self._blend_multiply,
            'screen': self._blend_screen,
            'overlay': self._blend_overlay,
            'darken': self._blend_darken,
            'lighten': self._blend_lighten,
            'color_dodge': self._blend_color_dodge,
            'color_burn': self._blend_color_burn,
            'hard_light': self._blend_hard_light,
            'soft_light': self._blend_soft_light,
            'difference': self._blend_difference,
            'exclusion': self._blend_exclusion,
            'hue': self._blend_hue,
            'saturation': self._blend_saturation,
            'color': self._blend_color,
            'luminosity': self._blend_luminosity,
        }
    
    def open_image(self, image_path: str) -> Dict:
        """Open image for editing"""
        try:
            img = Image.open(image_path)
            
            return {
                'id': generate_uuid(),
                'path': image_path,
                'width': img.width,
                'height': img.height,
                'mode': img.mode,
                'format': img.format,
                'size': os.path.getsize(image_path),
                'history': [img.copy()],
                'current': img,
                'filters_applied': [],
                'adjustments': {},
                'layers': [],
                'selection': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Open image error: {e}")
            raise
    
    def apply_filter(self, image_data: Dict, filter_name: str, 
                    intensity: float = 1.0, params: Dict = None) -> Dict:
        """Apply filter to image"""
        if filter_name not in self.filters:
            raise ValueError(f"Filter {filter_name} not found")
        
        # Save current state to history
        image_data['history'].append(image_data['current'].copy())
        
        # Apply filter
        try:
            result = self.filters[filter_name](image_data['current'], intensity, params or {})
            image_data['current'] = result
            image_data['filters_applied'].append({
                'name': filter_name,
                'intensity': intensity,
                'params': params,
                'timestamp': datetime.now().isoformat()
            })
            image_data['updated_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Apply filter error: {e}")
            raise
        
        return image_data
    
    def apply_adjustment(self, image_data: Dict, adjustment: str, 
                        value: float) -> Dict:
        """Apply adjustment to image"""
        if adjustment not in self.adjustments:
            raise ValueError(f"Adjustment {adjustment} not found")
        
        # Save current state to history
        image_data['history'].append(image_data['current'].copy())
        
        # Apply adjustment
        try:
            result = self.adjustments[adjustment](image_data['current'], value)
            image_data['current'] = result
            image_data['adjustments'][adjustment] = value
            image_data['updated_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Apply adjustment error: {e}")
            raise
        
        return image_data
    
    def resize(self, image_data: Dict, width: int = None, height: int = None,
               maintain_aspect: bool = True) -> Dict:
        """Resize image"""
        img = image_data['current']
        
        if width and height:
            if maintain_aspect:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
        elif width:
            ratio = width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((width, new_height), Image.Resampling.LANCZOS)
        elif height:
            ratio = height / img.height
            new_width = int(img.width * ratio)
            img = img.resize((new_width, height), Image.Resampling.LANCZOS)
        
        image_data['history'].append(image_data['current'].copy())
        image_data['current'] = img
        image_data['width'] = img.width
        image_data['height'] = img.height
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def crop(self, image_data: Dict, x: int, y: int, width: int, height: int) -> Dict:
        """Crop image"""
        img = image_data['current']
        img = img.crop((x, y, x + width, y + height))
        
        image_data['history'].append(image_data['current'].copy())
        image_data['current'] = img
        image_data['width'] = img.width
        image_data['height'] = img.height
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def rotate(self, image_data: Dict, angle: float) -> Dict:
        """Rotate image"""
        img = image_data['current']
        img = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        
        image_data['history'].append(image_data['current'].copy())
        image_data['current'] = img
        image_data['width'] = img.width
        image_data['height'] = img.height
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def flip(self, image_data: Dict, direction: str = 'horizontal') -> Dict:
        """Flip image"""
        img = image_data['current']
        
        if direction == 'horizontal':
            img = ImageOps.mirror(img)
        elif direction == 'vertical':
            img = ImageOps.flip(img)
        
        image_data['history'].append(image_data['current'].copy())
        image_data['current'] = img
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def add_text(self, image_data: Dict, text: str, x: int = None, y: int = None,
                 font_size: int = 24, font_name: str = 'Arial',
                 font_color: str = '#ffffff', bold: bool = False,
                 italic: bool = False, shadow: bool = False,
                 outline: bool = False, outline_color: str = '#000000',
                 background: bool = False, background_color: str = '#000000',
                 opacity: float = 1.0) -> Dict:
        """Add text to image"""
        img = image_data['current'].copy()
        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            font_path = os.path.join(Config.FONTS_DIR, f"{font_name}.ttf")
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Default position (center)
        if x is None:
            x = (img.width - text_width) // 2
        if y is None:
            y = (img.height - text_height) // 2
        
        # Create text layer
        text_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        
        # Apply bold/italic (simplified)
        if bold and italic:
            font = ImageFont.truetype(font_path, font_size)
        elif bold:
            try:
                font = ImageFont.truetype(font_path.replace('.ttf', '-Bold.ttf'), font_size)
            except:
                pass
        elif italic:
            try:
                font = ImageFont.truetype(font_path.replace('.ttf', '-Italic.ttf'), font_size)
            except:
                pass
        
        # Draw background
        if background:
            padding = 10
            text_draw.rectangle([x - padding, y - padding, 
                                 x + text_width + padding, 
                                 y + text_height + padding], 
                                fill=background_color)
        
        # Draw outline
        if outline:
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        text_draw.text((x + dx, y + dy), text, fill=outline_color, font=font)
        
        # Draw shadow
        if shadow:
            text_draw.text((x + 2, y + 2), text, fill='#000000', font=font)
        
        # Draw text
        text_draw.text((x, y), text, fill=font_color, font=font)
        
        # Apply opacity
        if opacity < 1.0:
            text_layer = self._adjust_opacity(text_layer, opacity)
        
        # Composite text onto image
        img = Image.alpha_composite(img.convert('RGBA'), text_layer).convert('RGB')
        
        image_data['history'].append(image_data['current'].copy())
        image_data['current'] = img
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def add_shape(self, image_data: Dict, shape_type: str, x: int, y: int,
                  width: int, height: int, fill_color: str = '#ff0000',
                  stroke_color: str = '#000000', stroke_width: int = 1,
                  opacity: float = 1.0, rotation: float = 0) -> Dict:
        """Add shape to image"""
        img = image_data['current'].copy()
        draw = ImageDraw.Draw(img)
        
        # Create shape layer
        shape_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        shape_draw = ImageDraw.Draw(shape_layer)
        
        if shape_type == 'rectangle':
            shape_draw.rectangle([x, y, x + width, y + height],
                                fill=fill_color, outline=stroke_color, width=stroke_width)
        elif shape_type == 'circle':
            shape_draw.ellipse([x, y, x + width, y + height],
                              fill=fill_color, outline=stroke_color, width=stroke_width)
        elif shape_type == 'triangle':
            points = [(x + width//2, y), (x, y + height), (x + width, y + height)]
            shape_draw.polygon(points, fill=fill_color, outline=stroke_color)
        elif shape_type == 'line':
            shape_draw.line([x, y, x + width, y + height],
                           fill=stroke_color, width=stroke_width)
        elif shape_type == 'star':
            self._draw_star(shape_draw, x, y, width, height, fill_color, stroke_color)
        elif shape_type == 'heart':
            self._draw_heart(shape_draw, x, y, width, height, fill_color, stroke_color)
        
        # Apply rotation
        if rotation != 0:
            shape_layer = shape_layer.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
        
        # Apply opacity
        if opacity < 1.0:
            shape_layer = self._adjust_opacity(shape_layer, opacity)
        
        # Composite shape onto image
        img = Image.alpha_composite(img.convert('RGBA'), shape_layer).convert('RGB')
        
        image_data['history'].append(image_data['current'].copy())
        image_data['current'] = img
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def remove_background(self, image_data: Dict) -> Dict:
        """Remove background from image (premium feature)"""
        try:
            import cv2
            
            img = image_data['current']
            arr = np.array(img.convert('RGB'))
            
            # Create mask using grabCut
            mask = np.zeros(arr.shape[:2], np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            height, width = arr.shape[:2]
            rect = (10, 10, width - 10, height - 10)
            
            cv2.grabCut(arr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            
            # Create mask
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Apply mask
            result = arr * mask2[:, :, np.newaxis]
            result_img = Image.fromarray(result)
            
            image_data['history'].append(image_data['current'].copy())
            image_data['current'] = result_img
            image_data['updated_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            raise
        
        return image_data
    
    def add_layer(self, image_data: Dict, layer_type: str, content: Any) -> Dict:
        """Add new layer to image"""
        layer = {
            'id': generate_uuid(),
            'type': layer_type,
            'content': content,
            'visible': True,
            'opacity': 1.0,
            'blend_mode': 'normal',
            'position': {'x': 0, 'y': 0},
            'created_at': datetime.now().isoformat()
        }
        
        image_data['layers'].append(layer)
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def merge_layers(self, image_data: Dict) -> Dict:
        """Merge all layers"""
        base = image_data['current'].copy()
        
        for layer in image_data['layers']:
            if not layer['visible']:
                continue
            
            # Create layer image
            if layer['type'] == 'text':
                # Render text
                pass
            elif layer['type'] == 'shape':
                # Render shape
                pass
            
            # Apply blend mode
            if layer['blend_mode'] != 'normal':
                base = self._apply_blend(base, layer['content'], layer['blend_mode'])
            else:
                # Apply opacity
                if layer['opacity'] < 1.0:
                    layer_content = self._adjust_opacity(layer['content'], layer['opacity'])
                else:
                    layer_content = layer['content']
                base = Image.alpha_composite(base.convert('RGBA'), layer_content).convert('RGB')
        
        image_data['history'].append(image_data['current'].copy())
        image_data['current'] = base
        image_data['layers'] = []
        image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def undo(self, image_data: Dict) -> Dict:
        """Undo last operation"""
        if len(image_data['history']) > 1:
            image_data['current'] = image_data['history'].pop()
            image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def reset(self, image_data: Dict) -> Dict:
        """Reset to original image"""
        if image_data['history']:
            image_data['current'] = image_data['history'][0].copy()
            image_data['history'] = [image_data['current'].copy()]
            image_data['filters_applied'] = []
            image_data['adjustments'] = {}
            image_data['layers'] = []
            image_data['updated_at'] = datetime.now().isoformat()
        
        return image_data
    
    def export(self, image_data: Dict, format: str = 'png', 
              quality: int = 95, transparent: bool = False) -> str:
        """Export image to file"""
        try:
            img = image_data['current']
            
            # Convert to RGB if not transparent
            if not transparent and format.lower() != 'png':
                img = img.convert('RGB')
            
            filename = f"edited_{slugify(image_data.get('id', 'image'))}_{int(datetime.now().timestamp())}.{format}"
            filepath = os.path.join(self.output_dir, filename)
            
            if format.lower() == 'png':
                img.save(filepath, format='PNG', optimize=True)
            elif format.lower() == 'jpg' or format.lower() == 'jpeg':
                img.save(filepath, format='JPEG', quality=quality, optimize=True)
            elif format.lower() == 'webp':
                img.save(filepath, format='WEBP', quality=quality)
            else:
                img.save(filepath, format=format.upper(), quality=quality)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise
    
    # ============================================
    # FILTER IMPLEMENTATIONS
    # ============================================
    
    def _apply_grayscale(self, img, intensity, params):
        return img.convert('L').convert('RGB')
    
    def _apply_sepia(self, img, intensity, params):
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        arr = np.array(img)
        sepia = np.array([[0.393, 0.769, 0.189],
                          [0.349, 0.686, 0.168],
                          [0.272, 0.534, 0.131]])
        arr = arr @ sepia.T
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        
        return Image.fromarray(arr)
    
    def _apply_invert(self, img, intensity, params):
        return ImageOps.invert(img)
    
    def _apply_threshold(self, img, intensity, params):
        threshold = int(128 * intensity)
        return img.convert('L').point(lambda x: 255 if x > threshold else 0).convert('RGB')
    
    def _apply_posterize(self, img, intensity, params):
        bits = max(1, int(8 * intensity))
        return ImageOps.posterize(img, bits)
    
    def _apply_solarize(self, img, intensity, params):
        threshold = int(128 * intensity)
        return ImageOps.solarize(img, threshold)
    
    def _apply_vintage(self, img, intensity, params):
        img = self._apply_sepia(img, intensity, params)
        arr = np.array(img)
        noise = np.random.normal(0, 10 * intensity, arr.shape)
        arr = arr + noise
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(0.7)
    
    def _apply_cinematic(self, img, intensity, params):
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1 + 0.2 * intensity)
        
        width, height = img.size
        arr = np.array(img)
        X, Y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        mask = np.sqrt(X**2 + Y**2)
        mask = np.clip(1 - mask * intensity, 0, 1)
        arr = arr * mask[:, :, np.newaxis]
        
        return Image.fromarray(arr.astype(np.uint8))
    
    def _apply_glitch(self, img, intensity, params):
        arr = np.array(img)
        h, w, c = arr.shape
        
        shift = int(np.random.randint(-20, 20) * intensity)
        arr[:, :, 0] = np.roll(arr[:, :, 0], shift=shift, axis=1)
        arr[::int(20 / max(intensity, 0.1))] = 0
        noise = np.random.normal(0, 20 * intensity, arr.shape)
        arr = arr + noise
        
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def _apply_neon(self, img, intensity, params):
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1 + 0.5 * intensity)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1 + 0.3 * intensity)
        blurred = img.filter(ImageFilter.GaussianBlur(radius=3 * intensity))
        return Image.blend(img, blurred, 0.3)
    
    def _apply_thermal(self, img, intensity, params):
        import cv2
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        return Image.fromarray(cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB))
    
    def _apply_night_vision(self, img, intensity, params):
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        arr = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        arr[:, :, 0] = arr[:, :, 0] * 0.3
        arr[:, :, 2] = arr[:, :, 2] * 0.3
        noise = np.random.normal(0, 20 * intensity, arr.shape)
        arr = arr + noise
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def _apply_dreamy(self, img, intensity, params):
        blurred = img.filter(ImageFilter.GaussianBlur(radius=5 * intensity))
        return Image.blend(img, blurred, 0.3)
    
    def _apply_dramatic(self, img, intensity, params):
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1 + 0.5 * intensity)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(1 - 0.1 * intensity)
    
    def _apply_pastel(self, img, intensity, params):
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        return img.filter(ImageFilter.SMOOTH)
    
    def _apply_vibrant(self, img, intensity, params):
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(1 + 0.3 * intensity)
    
    def _apply_oil_paint(self, img, intensity, params):
        import cv2
        arr = np.array(img)
        sigma_s = int(50 * intensity)
        sigma_r = 0.6 / intensity
        arr = cv2.stylization(arr, sigma_s=sigma_s, sigma_r=sigma_r)
        return Image.fromarray(arr)
    
    def _apply_watercolor(self, img, intensity, params):
        import cv2
        arr = np.array(img)
        sigma_s = int(60 * intensity)
        sigma_r = 0.07 / intensity
        arr = cv2.stylization(arr, sigma_s=sigma_s, sigma_r=sigma_r)
        return Image.fromarray(arr)
    
    def _apply_sketch(self, img, intensity, params):
        import cv2
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return Image.fromarray(sketch).convert('RGB')
    
    def _apply_cartoon(self, img, intensity, params):
        import cv2
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(arr, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return Image.fromarray(cartoon)
    
    def _apply_pixelate(self, img, intensity, params):
        pixel_size = max(2, int(10 * intensity))
        width, height = img.size
        small = img.resize((width // pixel_size, height // pixel_size), Image.Resampling.NEAREST)
        return small.resize((width, height), Image.Resampling.NEAREST)
    
    def _apply_mosaic(self, img, intensity, params):
        block_size = max(2, int(20 * intensity))
        width, height = img.size
        small = img.resize((width // block_size, height // block_size), Image.Resampling.NEAREST)
        return small.resize((width, height), Image.Resampling.NEAREST)
    
    def _apply_halftone(self, img, intensity, params):
        import cv2
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        return Image.fromarray(binary).convert('RGB')
    
    def _apply_pointillism(self, img, intensity, params):
        # Simplified pointillism
        width, height = img.size
        point_size = max(2, int(5 * intensity))
        result = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(result)
        
        for y in range(0, height, point_size):
            for x in range(0, width, point_size):
                sample = img.crop((x, y, x + point_size, y + point_size))
                avg_color = ImageStat.Stat(sample).mean
                color = tuple(int(c) for c in avg_color[:3])
                draw.ellipse([x, y, x + point_size, y + point_size], fill=color)
        
        return result
    
    def _apply_vignette(self, img, intensity, params):
        width, height = img.size
        arr = np.array(img)
        
        X, Y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        radius = np.sqrt(X**2 + Y**2)
        mask = 1 - np.clip(radius * intensity, 0, 1)
        mask = mask[:, :, np.newaxis]
        
        arr = arr * mask
        return Image.fromarray(arr.astype(np.uint8))
    
    def _apply_grain(self, img, intensity, params):
        arr = np.array(img)
        noise = np.random.normal(0, 20 * intensity, arr.shape)
        arr = arr + noise
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def _apply_glow(self, img, intensity, params):
        blurred = img.filter(ImageFilter.GaussianBlur(radius=5 * intensity))
        return Image.blend(img, blurred, 0.5)
    
    def _apply_bokeh(self, img, intensity, params):
        blurred = img.filter(ImageFilter.GaussianBlur(radius=10 * intensity))
        return Image.blend(img, blurred, 0.3)
    
    def _apply_tilt_shift(self, img, intensity, params):
        width, height = img.size
        arr = np.array(img)
        
        Y, X = np.meshgrid(np.linspace(-1, 1, height), np.linspace(-1, 1, width))
        mask = 1 - np.abs(Y) * intensity
        mask = np.clip(mask, 0, 1)
        mask = mask[:, :, np.newaxis]
        
        blurred = np.array(img.filter(ImageFilter.GaussianBlur(radius=5)))
        result = arr * mask + blurred * (1 - mask)
        
        return Image.fromarray(result.astype(np.uint8))
    
    def _apply_chromatic_aberration(self, img, intensity, params):
        arr = np.array(img)
        shift = int(5 * intensity)
        h, w, c = arr.shape
        result = np.zeros_like(arr)
        result[:, :, 0] = np.roll(arr[:, :, 0], shift, axis=1)
        result[:, :, 1] = arr[:, :, 1]
        result[:, :, 2] = np.roll(arr[:, :, 2], -shift, axis=1)
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    
    # ============================================
    # ADJUSTMENT IMPLEMENTATIONS
    # ============================================
    
    def _adjust_brightness(self, img, value):
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(value)
    
    def _adjust_contrast(self, img, value):
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(value)
    
    def _adjust_saturation(self, img, value):
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(value)
    
    def _adjust_sharpness(self, img, value):
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(value)
    
    def _adjust_temperature(self, img, value):
        if value > 1:
            r, g, b = img.split()
            r = r.point(lambda i: min(255, int(i * value)))
            return Image.merge('RGB', (r, g, b))
        else:
            r, g, b = img.split()
            b = b.point(lambda i: min(255, int(i / value)))
            return Image.merge('RGB', (r, g, b))
    
    def _adjust_tint(self, img, value):
        r, g, b = img.split()
        r = r.point(lambda i: min(255, int(i * (1 + value * 0.5))))
        g = g.point(lambda i: min(255, int(i * (1 + value * 0.3))))
        b = b.point(lambda i: min(255, int(i * (1 - value * 0.2))))
        return Image.merge('RGB', (r, g, b))
    
    def _adjust_exposure(self, img, value):
        arr = np.array(img)
        arr = arr * value
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def _adjust_gamma(self, img, value):
        gamma = 1.0 / value
        table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype(np.uint8)
        return Image.fromarray(np.array(img)).point(table)
    
    def _adjust_highlights(self, img, value):
        arr = np.array(img)
        highlight_mask = arr > 200
        arr[highlight_mask] = arr[highlight_mask] * value
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def _adjust_shadows(self, img, value):
        arr = np.array(img)
        shadow_mask = arr < 55
        arr[shadow_mask] = arr[shadow_mask] * value
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def _adjust_vibrance(self, img, value):
        arr = np.array(img)
        gray = np.mean(arr, axis=2, keepdims=True)
        diff = arr - gray
        arr = gray + diff * value
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
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
    
    def _draw_star(self, draw, x, y, width, height, fill, stroke):
        """Draw star shape"""
        import math
        cx = x + width // 2
        cy = y + height // 2
        outer_r = min(width, height) // 2
        inner_r = outer_r // 2
        points = []
        
        for i in range(10):
            angle = i * math.pi * 2 / 10 - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            points.append((px, py))
        
        draw.polygon(points, fill=fill, outline=stroke)
    
    def _draw_heart(self, draw, x, y, width, height, fill, stroke):
        """Draw heart shape"""
        import math
        cx = x + width // 2
        cy = y + height // 2
        size = min(width, height) // 2
        
        points = []
        for t in range(0, 360, 10):
            rad = math.radians(t)
            px = 16 * math.sin(rad) ** 3
            py = 13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad)
            px = cx + px * size / 20
            py = cy - py * size / 20
            points.append((px, py))
        
        draw.polygon(points, fill=fill, outline=stroke)
    
    def _apply_blend(self, base, overlay, mode):
        """Apply blend mode"""
        if mode in self.blend_modes:
            return self.blend_modes[mode](base, overlay)
        return base
    
    def _blend_normal(self, base, overlay):
        return Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    
    def _blend_multiply(self, base, overlay):
        return ImageChops.multiply(base, overlay)
    
    def _blend_screen(self, base, overlay):
        return ImageChops.screen(base, overlay)
    
    def _blend_overlay(self, base, overlay):
        return ImageChops.overlay(base, overlay)
    
    def _blend_darken(self, base, overlay):
        return ImageChops.darker(base, overlay)
    
    def _blend_lighten(self, base, overlay):
        return ImageChops.lighter(base, overlay)
    
    def _blend_color_dodge(self, base, overlay):
        return ImageChops.color_dodge(base, overlay)
    
    def _blend_color_burn(self, base, overlay):
        return ImageChops.color_burn(base, overlay)
    
    def _blend_hard_light(self, base, overlay):
        return ImageChops.hard_light(base, overlay)
    
    def _blend_soft_light(self, base, overlay):
        return ImageChops.soft_light(base, overlay)
    
    def _blend_difference(self, base, overlay):
        return ImageChops.difference(base, overlay)
    
    def _blend_exclusion(self, base, overlay):
        return ImageChops.exclusion(base, overlay)
    
    def _blend_hue(self, base, overlay):
        # Simplified hue blend
        return base
    
    def _blend_saturation(self, base, overlay):
        return base
    
    def _blend_color(self, base, overlay):
        return base
    
    def _blend_luminosity(self, base, overlay):
        return base

# Create global instance
image_editor = ImageEditor()
