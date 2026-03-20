"""
Image Processor - Handles all image processing operations
Author: @kinva_master
"""

import os
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

try:
    import cv2
except ImportError:
    cv2 = None

from ..config import Config
from ..utils import get_image_info, cleanup_file, format_file_size

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Main image processor class"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'image'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Available image filters
        self.available_filters = {
            # Basic Filters
            'grayscale': self._apply_grayscale,
            'sepia': self._apply_sepia,
            'invert': self._apply_invert,
            'threshold': self._apply_threshold,
            
            # Color Filters
            'vintage': self._apply_vintage,
            'cinematic': self._apply_cinematic,
            'glitch': self._apply_glitch,
            'neon': self._apply_neon,
            'thermal': self._apply_thermal,
            
            # Artistic Filters
            'oil_paint': self._apply_oil_paint,
            'watercolor': self._apply_watercolor,
            'sketch': self._apply_sketch,
            'cartoon': self._apply_cartoon,
            'pixelate': self._apply_pixelate,
            'mosaic': self._apply_mosaic,
            
            # Effect Filters
            'blur': lambda img: img.filter(ImageFilter.GaussianBlur(radius=2)),
            'sharpen': lambda img: img.filter(ImageFilter.SHARPEN),
            'edge': lambda img: img.filter(ImageFilter.FIND_EDGES),
            'emboss': lambda img: img.filter(ImageFilter.EMBOSS),
            'contour': lambda img: img.filter(ImageFilter.CONTOUR),
            'smooth': lambda img: img.filter(ImageFilter.SMOOTH),
            'detail': lambda img: img.filter(ImageFilter.DETAIL),
            
            # Advanced Filters
            'vignette': self._apply_vignette,
            'halftone': self._apply_halftone,
            'tilt_shift': self._apply_tilt_shift,
        }
    
    def process(self, input_path: str, filters: List[str] = None,
                adjustments: Dict = None, output_format: str = 'jpg',
                quality: int = 95) -> str:
        """Process image with filters and adjustments"""
        
        filters = filters or []
        adjustments = adjustments or {}
        
        try:
            # Open image
            img = Image.open(input_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply adjustments
            img = self._apply_adjustments(img, adjustments)
            
            # Apply filters
            for filter_name in filters:
                if filter_name in self.available_filters:
                    try:
                        img = self.available_filters[filter_name](img)
                    except Exception as e:
                        logger.error(f"Failed to apply filter {filter_name}: {e}")
            
            # Save output
            output_filename = f"processed_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, format=output_format.upper(), quality=quality)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            raise
    
    def _apply_adjustments(self, img: Image.Image, adjustments: Dict) -> Image.Image:
        """Apply brightness, contrast, saturation adjustments"""
        
        if 'brightness' in adjustments:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(adjustments['brightness'])
        
        if 'contrast' in adjustments:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(adjustments['contrast'])
        
        if 'saturation' in adjustments:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(adjustments['saturation'])
        
        if 'sharpness' in adjustments:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(adjustments['sharpness'])
        
        if 'blur' in adjustments:
            img = img.filter(ImageFilter.GaussianBlur(radius=adjustments['blur']))
        
        return img
    
    def resize(self, input_path: str, width: int = None, height: int = None,
               maintain_aspect: bool = True) -> str:
        """Resize image"""
        try:
            img = Image.open(input_path)
            
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
            
            output_filename = f"resized_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"Resize error: {e}")
            raise
    
    def crop(self, input_path: str, x: int, y: int, width: int, height: int) -> str:
        """Crop image"""
        try:
            img = Image.open(input_path)
            img = img.crop((x, y, x + width, y + height))
            
            output_filename = f"cropped_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"Crop error: {e}")
            raise
    
    def rotate(self, input_path: str, angle: float) -> str:
        """Rotate image"""
        try:
            img = Image.open(input_path)
            img = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
            
            output_filename = f"rotated_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"Rotate error: {e}")
            raise
    
    def flip(self, input_path: str, direction: str = 'horizontal') -> str:
        """Flip image horizontally or vertically"""
        try:
            img = Image.open(input_path)
            
            if direction == 'horizontal':
                img = ImageOps.mirror(img)
            elif direction == 'vertical':
                img = ImageOps.flip(img)
            
            output_filename = f"flipped_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"Flip error: {e}")
            raise
    
    def add_text(self, input_path: str, text: str, x: int = None, y: int = None,
                 font_size: int = 24, font_color: str = '#ffffff',
                 font_name: str = 'Arial', shadow: bool = False,
                 outline: bool = False, outline_color: str = '#000000') -> str:
        """Add text to image"""
        try:
            img = Image.open(input_path)
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
            
            # Draw outline
            if outline:
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), text, fill=outline_color, font=font)
            
            # Draw shadow
            if shadow:
                draw.text((x + 2, y + 2), text, fill='#000000', font=font)
            
            # Draw text
            draw.text((x, y), text, fill=font_color, font=font)
            
            output_filename = f"text_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"Add text error: {e}")
            raise
    
    def add_shape(self, input_path: str, shape_type: str, x: int, y: int,
                  width: int, height: int, fill_color: str = '#ff0000',
                  outline_color: str = '#000000', outline_width: int = 1) -> str:
        """Add shape to image"""
        try:
            img = Image.open(input_path)
            draw = ImageDraw.Draw(img)
            
            if shape_type == 'rectangle':
                draw.rectangle([x, y, x + width, y + height],
                              fill=fill_color, outline=outline_color, width=outline_width)
            elif shape_type == 'circle':
                draw.ellipse([x, y, x + width, y + height],
                            fill=fill_color, outline=outline_color, width=outline_width)
            elif shape_type == 'line':
                draw.line([x, y, x + width, y + height],
                         fill=outline_color, width=outline_width)
            elif shape_type == 'triangle':
                points = [(x + width//2, y), (x, y + height), (x + width, y + height)]
                draw.polygon(points, fill=fill_color, outline=outline_color)
            
            output_filename = f"shape_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"Add shape error: {e}")
            raise
    
    def remove_background(self, input_path: str) -> str:
        """Remove background from image (premium feature)"""
        if cv2 is None:
            raise ImportError("OpenCV required for background removal")
        
        try:
            img = cv2.imread(input_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Create mask using grabCut
            mask = np.zeros(img.shape[:2], np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Define rectangle around subject
            height, width = img.shape[:2]
            rect = (10, 10, width - 10, height - 10)
            
            cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            
            # Create mask
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Apply mask
            result = img_rgb * mask2[:, :, np.newaxis]
            
            # Convert to PIL
            result_pil = Image.fromarray(result)
            
            output_filename = f"nobg_{int(datetime.now().timestamp())}.png"
            output_path = os.path.join(self.output_dir, output_filename)
            
            result_pil.save(output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            raise
    
    def compress(self, input_path: str, quality: int = 70) -> str:
        """Compress image"""
        try:
            img = Image.open(input_path)
            
            output_filename = f"compressed_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            img.save(output_path, quality=quality, optimize=True)
            
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Image compressed: {format_file_size(original_size)} -> {format_file_size(compressed_size)} ({reduction:.1f}% reduction)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Compress error: {e}")
            raise
    
    def convert_format(self, input_path: str, output_format: str = 'png') -> str:
        """Convert image format"""
        try:
            img = Image.open(input_path)
            
            output_filename = f"converted_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            if output_format.lower() == 'png':
                img.save(output_path, format='PNG')
            elif output_format.lower() == 'webp':
                img.save(output_path, format='WEBP')
            else:
                img.save(output_path, format=output_format.upper())
            
            return output_path
            
        except Exception as e:
            logger.error(f"Convert format error: {e}")
            raise
    
    def create_collage(self, image_paths: List[str], rows: int = 2, cols: int = 2,
                       spacing: int = 10, background_color: str = '#ffffff') -> str:
        """Create collage from multiple images"""
        try:
            images = [Image.open(path) for path in image_paths[:rows*cols]]
            
            # Calculate cell size
            cell_width = max(img.width for img in images)
            cell_height = max(img.height for img in images)
            
            # Calculate total size
            total_width = cols * cell_width + (cols - 1) * spacing
            total_height = rows * cell_height + (rows - 1) * spacing
            
            # Create blank canvas
            collage = Image.new('RGB', (total_width, total_height), background_color)
            
            # Paste images
            for idx, img in enumerate(images):
                row = idx // cols
                col = idx % cols
                
                x = col * (cell_width + spacing)
                y = row * (cell_height + spacing)
                
                # Center image in cell
                x_offset = (cell_width - img.width) // 2
                y_offset = (cell_height - img.height) // 2
                
                collage.paste(img, (x + x_offset, y + y_offset))
            
            output_filename = f"collage_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            collage.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"Collage creation error: {e}")
            raise
    
    # ============================================
    # FILTER IMPLEMENTATIONS
    # ============================================
    
    def _apply_grayscale(self, img: Image.Image) -> Image.Image:
        """Convert to grayscale"""
        return img.convert('L').convert('RGB')
    
    def _apply_sepia(self, img: Image.Image) -> Image.Image:
        """Apply sepia filter"""
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        arr = np.array(img)
        sepia = np.array([[0.393, 0.769, 0.189],
                          [0.349, 0.686, 0.168],
                          [0.272, 0.534, 0.131]])
        arr = arr @ sepia.T
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        
        return Image.fromarray(arr)
    
    def _apply_invert(self, img: Image.Image) -> Image.Image:
        """Invert colors"""
        return ImageOps.invert(img)
    
    def _apply_threshold(self, img: Image.Image, threshold: int = 128) -> Image.Image:
        """Apply threshold filter"""
        return img.convert('L').point(lambda x: 255 if x > threshold else 0).convert('RGB')
    
    def _apply_vintage(self, img: Image.Image) -> Image.Image:
        """Apply vintage effect"""
        img = self._apply_sepia(img)
        arr = np.array(img)
        noise = np.random.normal(0, 10, arr.shape)
        arr = arr + noise
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(0.7)
    
    def _apply_cinematic(self, img: Image.Image) -> Image.Image:
        """Apply cinematic effect"""
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        width, height = img.size
        arr = np.array(img)
        X, Y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        mask = np.sqrt(X**2 + Y**2)
        mask = np.clip(1 - mask, 0, 1)
        arr = arr * mask[:, :, np.newaxis]
        
        return Image.fromarray(arr.astype(np.uint8))
    
    def _apply_glitch(self, img: Image.Image) -> Image.Image:
        """Apply glitch effect"""
        arr = np.array(img)
        h, w, c = arr.shape
        
        # Channel shift
        shift = np.random.randint(-20, 20)
        arr[:, :, 0] = np.roll(arr[:, :, 0], shift=shift, axis=1)
        
        # Add scanlines
        arr[::20] = 0
        
        # Add noise
        noise = np.random.normal(0, 20, arr.shape)
        arr = arr + noise
        
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def _apply_neon(self, img: Image.Image) -> Image.Image:
        """Apply neon effect"""
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        
        blurred = img.filter(ImageFilter.GaussianBlur(radius=3))
        img = Image.blend(img, blurred, 0.3)
        
        return img
    
    def _apply_thermal(self, img: Image.Image) -> Image.Image:
        """Apply thermal vision effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        return Image.fromarray(cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB))
    
    def _apply_oil_paint(self, img: Image.Image) -> Image.Image:
        """Apply oil paint effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        arr = cv2.stylization(arr, sigma_s=60, sigma_r=0.6)
        return Image.fromarray(arr)
    
    def _apply_watercolor(self, img: Image.Image) -> Image.Image:
        """Apply watercolor effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        arr = cv2.stylization(arr, sigma_s=60, sigma_r=0.07)
        return Image.fromarray(arr)
    
    def _apply_sketch(self, img: Image.Image) -> Image.Image:
        """Apply sketch effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return Image.fromarray(sketch).convert('RGB')
    
    def _apply_cartoon(self, img: Image.Image) -> Image.Image:
        """Apply cartoon effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(arr, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return Image.fromarray(cartoon)
    
    def _apply_pixelate(self, img: Image.Image, pixel_size: int = 10) -> Image.Image:
        """Apply pixelate effect"""
        width, height = img.size
        small = img.resize((width // pixel_size, height // pixel_size), Image.Resampling.NEAREST)
        return small.resize((width, height), Image.Resampling.NEAREST)
    
    def _apply_mosaic(self, img: Image.Image, block_size: int = 20) -> Image.Image:
        """Apply mosaic effect"""
        width, height = img.size
        small = img.resize((width // block_size, height // block_size), Image.Resampling.NEAREST)
        return small.resize((width, height), Image.Resampling.NEAREST)
    
    def _apply_vignette(self, img: Image.Image) -> Image.Image:
        """Apply vignette effect"""
        width, height = img.size
        arr = np.array(img)
        
        X, Y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        radius = np.sqrt(X**2 + Y**2)
        mask = 1 - np.clip(radius, 0, 1)
        mask = mask[:, :, np.newaxis]
        
        arr = arr * mask
        return Image.fromarray(arr.astype(np.uint8))
    
    def _apply_halftone(self, img: Image.Image) -> Image.Image:
        """Apply halftone effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        return Image.fromarray(binary).convert('RGB')
    
    def _apply_tilt_shift(self, img: Image.Image) -> Image.Image:
        """Apply tilt-shift effect"""
        width, height = img.size
        arr = np.array(img)
        
        # Create gradient mask
        Y, X = np.meshgrid(np.linspace(-1, 1, height), np.linspace(-1, 1, width))
        mask = 1 - np.abs(Y)
        mask = np.clip(mask, 0, 1)
        mask = mask[:, :, np.newaxis]
        
        # Apply blur based on mask
        blurred = cv2.GaussianBlur(arr, (15, 15), 0)
        result = arr * mask + blurred * (1 - mask)
        
        return Image.fromarray(result.astype(np.uint8))

# Create global instance
image_processor = ImageProcessor()
