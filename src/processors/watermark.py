"""
Watermark Processor - Handles adding watermarks to videos and images
Author: @kinva_master
"""

import os
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
except ImportError:
    pass

from ..config import Config

logger = logging.getLogger(__name__)

class Watermark:
    """Handles adding watermarks to media files"""
    
    def __init__(self):
        self.watermark_text = Config.WATERMARK_TEXT
        self.watermark_opacity = Config.WATERMARK_OPACITY
        self.watermark_position = Config.WATERMARK_POSITION
        self.watermark_size = Config.WATERMARK_SIZE
        self.font_size = Config.WATERMARK_FONT_SIZE
        self.font_color = Config.WATERMARK_FONT_COLOR
        self.font_name = Config.WATERMARK_FONT
        
        # Watermark positions
        self.positions = {
            'top-left': (10, 10),
            'top-right': (-10, 10),
            'bottom-left': (10, -10),
            'bottom-right': (-10, -10),
            'center': (0, 0)
        }
        
        self.output_dir = Path(Config.OUTPUT_DIR) / 'watermark'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def add_text_watermark(self, image: Image.Image) -> Image.Image:
        """Add text watermark to image"""
        try:
            # Create a copy of the image
            img = image.copy()
            draw = ImageDraw.Draw(img)
            
            # Load font
            try:
                font_path = os.path.join(Config.FONTS_DIR, f"{self.font_name}.ttf")
                font = ImageFont.truetype(font_path, self.font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text size
            bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position
            x, y = self._calculate_position(img.width, img.height, text_width, text_height)
            
            # Create watermark layer with opacity
            watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
            watermark_draw = ImageDraw.Draw(watermark_layer)
            
            # Draw text with shadow
            shadow_offset = 2
            watermark_draw.text((x + shadow_offset, y + shadow_offset), 
                               self.watermark_text, fill=(0, 0, 0, int(255 * self.watermark_opacity)), font=font)
            watermark_draw.text((x, y), self.watermark_text, 
                               fill=(255, 255, 255, int(255 * self.watermark_opacity)), font=font)
            
            # Composite watermark onto image
            img = Image.alpha_composite(img.convert('RGBA'), watermark_layer).convert('RGB')
            
            return img
            
        except Exception as e:
            logger.error(f"Add text watermark error: {e}")
            return image
    
    def add_image_watermark(self, image: Image.Image, watermark_path: str = None) -> Image.Image:
        """Add image watermark to image"""
        try:
            if watermark_path is None:
                watermark_path = Config.WATERMARK_IMAGE
            
            if not os.path.exists(watermark_path):
                return self.add_text_watermark(image)
            
            # Load watermark image
            watermark = Image.open(watermark_path).convert('RGBA')
            
            # Resize watermark if needed
            if watermark.width > self.watermark_size:
                ratio = self.watermark_size / watermark.width
                new_size = (self.watermark_size, int(watermark.height * ratio))
                watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
            
            # Calculate position
            x, y = self._calculate_position(image.width, image.height, watermark.width, watermark.height)
            
            # Create watermark layer with opacity
            watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            watermark_layer.paste(watermark, (x, y), watermark)
            
            # Adjust opacity
            watermark_layer = self._adjust_opacity(watermark_layer, self.watermark_opacity)
            
            # Composite watermark onto image
            img = Image.alpha_composite(image.convert('RGBA'), watermark_layer).convert('RGB')
            
            return img
            
        except Exception as e:
            logger.error(f"Add image watermark error: {e}")
            return self.add_text_watermark(image)
    
    def add_video_watermark(self, video_path: str, watermark_path: str = None) -> str:
        """Add watermark to video"""
        try:
            # Create temporary watermark image
            temp_watermark = self._create_watermark_image()
            
            # Use FFmpeg to add watermark
            output_filename = f"watermarked_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # FFmpeg command for overlay
            cmd = [
                'ffmpeg', '-i', video_path,
                '-i', temp_watermark,
                '-filter_complex',
                f'[1:v]format=rgba,colorchannelmixer=aa={self.watermark_opacity}[watermark];'
                f'[0:v][watermark]overlay={self._get_ffmpeg_position()}',
                '-c:a', 'copy',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Cleanup
            if os.path.exists(temp_watermark):
                os.remove(temp_watermark)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Add video watermark error: {e}")
            return video_path
    
    def _create_watermark_image(self) -> str:
        """Create watermark image from text"""
        try:
            # Create image with text
            font_path = os.path.join(Config.FONTS_DIR, f"{self.font_name}.ttf")
            font = ImageFont.truetype(font_path, self.font_size)
            
            # Calculate text size
            temp_img = Image.new('RGBA', (1, 1))
            draw = ImageDraw.Draw(temp_img)
            bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Add padding
            padding = 20
            img = Image.new('RGBA', (text_width + padding, text_height + padding), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw text
            x = padding // 2
            y = padding // 2
            draw.text((x, y), self.watermark_text, fill=(255, 255, 255, 255), font=font)
            
            # Save to temp file
            temp_path = os.path.join(self.output_dir, f"temp_watermark_{int(datetime.now().timestamp())}.png")
            img.save(temp_path)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Create watermark image error: {e}")
            return None
    
    def _adjust_opacity(self, image: Image.Image, opacity: float) -> Image.Image:
        """Adjust image opacity"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        alpha = image.getchannel('A')
        alpha = alpha.point(lambda p: p * opacity)
        image.putalpha(alpha)
        
        return image
    
    def _calculate_position(self, container_width: int, container_height: int, 
                           element_width: int, element_height: int) -> Tuple[int, int]:
        """Calculate watermark position"""
        position = self.watermark_position.lower()
        
        if position == 'top-left':
            x = self.positions['top-left'][0]
            y = self.positions['top-left'][1]
        elif position == 'top-right':
            x = container_width - element_width - abs(self.positions['top-right'][0])
            y = self.positions['top-right'][1]
        elif position == 'bottom-left':
            x = self.positions['bottom-left'][0]
            y = container_height - element_height - abs(self.positions['bottom-left'][1])
        elif position == 'bottom-right':
            x = container_width - element_width - abs(self.positions['bottom-right'][0])
            y = container_height - element_height - abs(self.positions['bottom-right'][1])
        elif position == 'center':
            x = (container_width - element_width) // 2
            y = (container_height - element_height) // 2
        else:
            # Default to bottom-right
            x = container_width - element_width - 10
            y = container_height - element_height - 10
        
        return max(0, x), max(0, y)
    
    def _get_ffmpeg_position(self) -> str:
        """Get FFmpeg position string"""
        position = self.watermark_position.lower()
        
        if position == 'top-left':
            return '10:10'
        elif position == 'top-right':
            return 'W-w-10:10'
        elif position == 'bottom-left':
            return '10:H-h-10'
        elif position == 'bottom-right':
            return 'W-w-10:H-h-10'
        elif position == 'center':
            return '(W-w)/2:(H-h)/2'
        else:
            return 'W-w-10:H-h-10'
    
    def remove_watermark(self, image_path: str) -> str:
        """Remove watermark from image (premium feature)"""
        # This is a placeholder - in production, you'd need AI-based watermark removal
        return image_path
    
    def add_custom_watermark(self, image: Image.Image, watermark_path: str, 
                             position: str = 'bottom-right', opacity: float = 0.5,
                             size: int = 100) -> Image.Image:
        """Add custom watermark image"""
        try:
            if not os.path.exists(watermark_path):
                return image
            
            # Load watermark
            watermark = Image.open(watermark_path).convert('RGBA')
            
            # Resize
            if watermark.width > size:
                ratio = size / watermark.width
                new_size = (size, int(watermark.height * ratio))
                watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
            
            # Calculate position
            x, y = self._calculate_position(image.width, image.height, watermark.width, watermark.height)
            
            # Create layer
            layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            layer.paste(watermark, (x, y), watermark)
            
            # Adjust opacity
            layer = self._adjust_opacity(layer, opacity)
            
            # Composite
            result = Image.alpha_composite(image.convert('RGBA'), layer).convert('RGB')
            
            return result
            
        except Exception as e:
            logger.error(f"Add custom watermark error: {e}")
            return image

# Create global instance
watermark = Watermark()
