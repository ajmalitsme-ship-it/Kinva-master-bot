"""
Effects Processor - Handles video and image effects
Author: @kinva_master
"""

import os
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

try:
    import cv2
    from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
    from moviepy.video.fx import rotate, resize, speedx, time_mirror, lum_contrast, colorx
except ImportError:
    pass

from ..config import Config

logger = logging.getLogger(__name__)

class EffectsProcessor:
    """Handles video and image effects"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'effects'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Available video effects
        self.video_effects = {
            # Color Effects
            'vintage': self.vintage_effect,
            'cinematic': self.cinematic_effect,
            'black_white': self.black_white_effect,
            'sepia': self.sepia_effect,
            'glitch': self.glitch_effect,
            'neon': self.neon_effect,
            'thermal': self.thermal_effect,
            'night_vision': self.night_vision_effect,
            'dreamy': self.dreamy_effect,
            'dramatic': self.dramatic_effect,
            'pastel': self.pastel_effect,
            'vibrant': self.vibrant_effect,
            
            # Transform Effects
            'mirror': self.mirror_effect,
            'flip': self.flip_effect,
            'rotate_90': self.rotate_90_effect,
            'rotate_180': self.rotate_180_effect,
            'rotate_270': self.rotate_270_effect,
            'zoom_in': self.zoom_in_effect,
            'zoom_out': self.zoom_out_effect,
            'pan_left': self.pan_left_effect,
            'pan_right': self.pan_right_effect,
            'tilt_up': self.tilt_up_effect,
            'tilt_down': self.tilt_down_effect,
            
            # Speed Effects
            'slow_motion': self.slow_motion_effect,
            'fast_motion': self.fast_motion_effect,
            'reverse': self.reverse_effect,
            'time_lapse': self.time_lapse_effect,
            
            # Artistic Effects
            'cartoon': self.cartoon_effect,
            'oil_paint': self.oil_paint_effect,
            'watercolor': self.watercolor_effect,
            'sketch': self.sketch_effect,
            'pixelate': self.pixelate_effect,
            'mosaic': self.mosaic_effect,
            'halftone': self.halftone_effect,
            'glow': self.glow_effect,
            'blur': self.blur_effect,
            'sharpen': self.sharpen_effect,
        }
        
        # Available image effects
        self.image_effects = {
            # Color Effects
            'vintage': self.image_vintage,
            'cinematic': self.image_cinematic,
            'black_white': self.image_black_white,
            'sepia': self.image_sepia,
            'glitch': self.image_glitch,
            'neon': self.image_neon,
            'thermal': self.image_thermal,
            'night_vision': self.image_night_vision,
            
            # Artistic Effects
            'cartoon': self.image_cartoon,
            'oil_paint': self.image_oil_paint,
            'watercolor': self.image_watercolor,
            'sketch': self.image_sketch,
            'pixelate': self.image_pixelate,
            'mosaic': self.image_mosaic,
            'halftone': self.image_halftone,
            'glow': self.image_glow,
            
            # Transform Effects
            'mirror': self.image_mirror,
            'flip': self.image_flip,
            'rotate_90': self.image_rotate_90,
            'rotate_180': self.image_rotate_180,
        }
    
    def apply_video_effect(self, video_path: str, effect: str, 
                          params: Dict = None) -> str:
        """Apply effect to video"""
        try:
            if effect not in self.video_effects:
                raise ValueError(f"Effect {effect} not found")
            
            clip = VideoFileClip(video_path)
            
            # Apply effect
            result = self.video_effects[effect](clip, params or {})
            
            output_filename = f"effect_{effect}_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            result.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video effect error: {e}")
            raise
    
    def apply_image_effect(self, image_path: str, effect: str,
                          params: Dict = None) -> str:
        """Apply effect to image"""
        try:
            if effect not in self.image_effects:
                raise ValueError(f"Effect {effect} not found")
            
            img = Image.open(image_path)
            
            # Apply effect
            result = self.image_effects[effect](img, params or {})
            
            output_filename = f"effect_{effect}_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            result.save(output_path, quality=95)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Image effect error: {e}")
            raise
    
    # ============================================
    # VIDEO EFFECTS
    # ============================================
    
    def vintage_effect(self, clip, params):
        """Apply vintage effect"""
        def vintage_filter(get_frame, t):
            frame = get_frame(t)
            frame = np.array(frame)
            sepia = np.array([[0.393, 0.769, 0.189],
                              [0.349, 0.686, 0.168],
                              [0.272, 0.534, 0.131]])
            frame = frame @ sepia.T
            noise = np.random.normal(0, 10, frame.shape)
            frame = frame + noise
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(vintage_filter)
    
    def cinematic_effect(self, clip, params):
        """Apply cinematic effect"""
        def cinematic_filter(get_frame, t):
            frame = get_frame(t)
            frame = np.clip((frame - 128) * 1.2 + 128, 0, 255).astype(np.uint8)
            h, w = frame.shape[:2]
            bar_height = int(h * 0.1)
            frame[:bar_height] = 0
            frame[-bar_height:] = 0
            return frame
        
        return clip.fl(cinematic_filter)
    
    def black_white_effect(self, clip, params):
        """Apply black and white effect"""
        return clip.to_grayscale()
    
    def sepia_effect(self, clip, params):
        """Apply sepia effect"""
        def sepia_filter(get_frame, t):
            frame = get_frame(t)
            sepia = np.array([[0.393, 0.769, 0.189],
                              [0.349, 0.686, 0.168],
                              [0.272, 0.534, 0.131]])
            frame = frame @ sepia.T
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(sepia_filter)
    
    def glitch_effect(self, clip, params):
        """Apply glitch effect"""
        intensity = params.get('intensity', 0.5)
        
        def glitch_filter(get_frame, t):
            frame = get_frame(t)
            if np.random.random() > (1 - intensity):
                shift = np.random.randint(-20, 20)
                frame[:, :, 0] = np.roll(frame[:, :, 0], shift=shift, axis=1)
                frame[::20] = 0
            return frame
        
        return clip.fl(glitch_filter)
    
    def neon_effect(self, clip, params):
        """Apply neon effect"""
        def neon_filter(get_frame, t):
            frame = get_frame(t)
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            kernel = np.ones((5, 5), np.float32) / 25
            blurred = cv2.filter2D(frame, -1, kernel)
            frame = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(neon_filter)
    
    def thermal_effect(self, clip, params):
        """Apply thermal vision effect"""
        def thermal_filter(get_frame, t):
            frame = get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
            return cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB)
        
        return clip.fl(thermal_filter)
    
    def night_vision_effect(self, clip, params):
        """Apply night vision effect"""
        def night_vision_filter(get_frame, t):
            frame = get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            frame[:, :, 0] = frame[:, :, 0] * 0.3
            frame[:, :, 2] = frame[:, :, 2] * 0.3
            noise = np.random.normal(0, 20, frame.shape)
            frame = frame + noise
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(night_vision_filter)
    
    def dreamy_effect(self, clip, params):
        """Apply dreamy effect"""
        def dreamy_filter(get_frame, t):
            frame = get_frame(t)
            kernel = np.ones((7, 7), np.float32) / 49
            blurred = cv2.filter2D(frame, -1, kernel)
            frame = cv2.addWeighted(frame, 0.6, blurred, 0.4, 0)
            return frame
        
        return clip.fl(dreamy_filter)
    
    def dramatic_effect(self, clip, params):
        """Apply dramatic effect"""
        return clip.fx(lum_contrast, contrast=0.5, brightness=0.1)
    
    def pastel_effect(self, clip, params):
        """Apply pastel effect"""
        return clip.fx(colorx, 0.8).fx(lum_contrast, contrast=0.8)
    
    def vibrant_effect(self, clip, params):
        """Apply vibrant effect"""
        return clip.fx(colorx, 1.3)
    
    def mirror_effect(self, clip, params):
        """Apply mirror effect"""
        def mirror_filter(get_frame, t):
            frame = get_frame(t)
            return np.fliplr(frame)
        
        return clip.fl(mirror_filter)
    
    def flip_effect(self, clip, params):
        """Apply flip effect"""
        def flip_filter(get_frame, t):
            frame = get_frame(t)
            return np.flipud(frame)
        
        return clip.fl(flip_filter)
    
    def rotate_90_effect(self, clip, params):
        """Rotate 90 degrees"""
        return rotate(clip, 90)
    
    def rotate_180_effect(self, clip, params):
        """Rotate 180 degrees"""
        return rotate(clip, 180)
    
    def rotate_270_effect(self, clip, params):
        """Rotate 270 degrees"""
        return rotate(clip, 270)
    
    def zoom_in_effect(self, clip, params):
        """Zoom in effect"""
        return clip.fx(resize, lambda t: 1 + 0.5 * t)
    
    def zoom_out_effect(self, clip, params):
        """Zoom out effect"""
        return clip.fx(resize, lambda t: 1 - 0.5 * t)
    
    def pan_left_effect(self, clip, params):
        """Pan left effect"""
        return clip.fx(resize, lambda t: 1 + 0.2 * t)
    
    def pan_right_effect(self, clip, params):
        """Pan right effect"""
        return clip.fx(resize, lambda t: 1 + 0.2 * t)
    
    def tilt_up_effect(self, clip, params):
        """Tilt up effect"""
        return clip.fx(resize, lambda t: 1 + 0.2 * t)
    
    def tilt_down_effect(self, clip, params):
        """Tilt down effect"""
        return clip.fx(resize, lambda t: 1 + 0.2 * t)
    
    def slow_motion_effect(self, clip, params):
        """Slow motion effect"""
        return speedx(clip, 0.5)
    
    def fast_motion_effect(self, clip, params):
        """Fast motion effect"""
        return speedx(clip, 2.0)
    
    def reverse_effect(self, clip, params):
        """Reverse effect"""
        return time_mirror(clip)
    
    def time_lapse_effect(self, clip, params):
        """Time lapse effect"""
        return speedx(clip, 5.0)
    
    def cartoon_effect(self, clip, params):
        """Cartoon effect"""
        def cartoon_filter(get_frame, t):
            frame = get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                          cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(frame, 9, 300, 300)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            return cartoon
        
        return clip.fl(cartoon_filter)
    
    def oil_paint_effect(self, clip, params):
        """Oil paint effect"""
        def oil_paint_filter(get_frame, t):
            frame = get_frame(t)
            kernel = np.ones((5, 5), np.float32) / 25
            frame = cv2.filter2D(frame, -1, kernel)
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.2, 0, 255)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(oil_paint_filter)
    
    def watercolor_effect(self, clip, params):
        """Watercolor effect"""
        def watercolor_filter(get_frame, t):
            frame = get_frame(t)
            frame = cv2.stylization(frame, sigma_s=60, sigma_r=0.07)
            return frame
        
        return clip.fl(watercolor_filter)
    
    def sketch_effect(self, clip, params):
        """Sketch effect"""
        def sketch_filter(get_frame, t):
            frame = get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            inv = 255 - gray
            blur = cv2.GaussianBlur(inv, (21, 21), 0)
            sketch = cv2.divide(gray, 255 - blur, scale=256)
            return cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)
        
        return clip.fl(sketch_filter)
    
    def pixelate_effect(self, clip, params):
        """Pixelate effect"""
        pixel_size = params.get('size', 10)
        
        def pixelate_filter(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            temp = cv2.resize(frame, (w // pixel_size, h // pixel_size), 
                             interpolation=cv2.INTER_LINEAR)
            frame = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
            return frame
        
        return clip.fl(pixelate_filter)
    
    def mosaic_effect(self, clip, params):
        """Mosaic effect"""
        block_size = params.get('size', 20)
        
        def mosaic_filter(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            temp = cv2.resize(frame, (w // block_size, h // block_size), 
                             interpolation=cv2.INTER_LINEAR)
            frame = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
            return frame
        
        return clip.fl(mosaic_filter)
    
    def halftone_effect(self, clip, params):
        """Halftone effect"""
        def halftone_filter(get_frame, t):
            frame = get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            return cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        
        return clip.fl(halftone_filter)
    
    def glow_effect(self, clip, params):
        """Glow effect"""
        def glow_filter(get_frame, t):
            frame = get_frame(t)
            kernel = np.ones((9, 9), np.float32) / 81
            blurred = cv2.filter2D(frame, -1, kernel)
            frame = cv2.addWeighted(frame, 0.6, blurred, 0.4, 0)
            return frame
        
        return clip.fl(glow_filter)
    
    def blur_effect(self, clip, params):
        """Blur effect"""
        radius = params.get('radius', 5)
        
        def blur_filter(get_frame, t):
            frame = get_frame(t)
            kernel = np.ones((radius, radius), np.float32) / (radius * radius)
            frame = cv2.filter2D(frame, -1, kernel)
            return frame
        
        return clip.fl(blur_filter)
    
    def sharpen_effect(self, clip, params):
        """Sharpen effect"""
        def sharpen_filter(get_frame, t):
            frame = get_frame(t)
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            frame = cv2.filter2D(frame, -1, kernel)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(sharpen_filter)
    
    # ============================================
    # IMAGE EFFECTS
    # ============================================
    
    def image_vintage(self, img, params):
        """Apply vintage effect to image"""
        img = self.image_sepia(img, {})
        arr = np.array(img)
        noise = np.random.normal(0, 10, arr.shape)
        arr = arr + noise
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(0.7)
    
    def image_cinematic(self, img, params):
        """Apply cinematic effect to image"""
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        width, height = img.size
        arr = np.array(img)
        X, Y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        mask = np.sqrt(X**2 + Y**2)
        mask = np.clip(1 - mask, 0, 1)
        arr = arr * mask[:, :, np.newaxis]
        
        return Image.fromarray(arr.astype(np.uint8))
    
    def image_black_white(self, img, params):
        """Apply black and white effect to image"""
        return img.convert('L').convert('RGB')
    
    def image_sepia(self, img, params):
        """Apply sepia effect to image"""
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        arr = np.array(img)
        sepia = np.array([[0.393, 0.769, 0.189],
                          [0.349, 0.686, 0.168],
                          [0.272, 0.534, 0.131]])
        arr = arr @ sepia.T
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        
        return Image.fromarray(arr)
    
    def image_glitch(self, img, params):
        """Apply glitch effect to image"""
        arr = np.array(img)
        h, w, c = arr.shape
        
        shift = np.random.randint(-20, 20)
        arr[:, :, 0] = np.roll(arr[:, :, 0], shift=shift, axis=1)
        arr[::20] = 0
        noise = np.random.normal(0, 20, arr.shape)
        arr = arr + noise
        
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def image_neon(self, img, params):
        """Apply neon effect to image"""
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        blurred = img.filter(ImageFilter.GaussianBlur(radius=3))
        return Image.blend(img, blurred, 0.3)
    
    def image_thermal(self, img, params):
        """Apply thermal effect to image"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        return Image.fromarray(cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB))
    
    def image_night_vision(self, img, params):
        """Apply night vision effect to image"""
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        arr = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        arr[:, :, 0] = arr[:, :, 0] * 0.3
        arr[:, :, 2] = arr[:, :, 2] * 0.3
        noise = np.random.normal(0, 20, arr.shape)
        arr = arr + noise
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def image_cartoon(self, img, params):
        """Apply cartoon effect to image"""
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
    
    def image_oil_paint(self, img, params):
        """Apply oil paint effect to image"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        arr = cv2.stylization(arr, sigma_s=60, sigma_r=0.6)
        return Image.fromarray(arr)
    
    def image_watercolor(self, img, params):
        """Apply watercolor effect to image"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        arr = cv2.stylization(arr, sigma_s=60, sigma_r=0.07)
        return Image.fromarray(arr)
    
    def image_sketch(self, img, params):
        """Apply sketch effect to image"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return Image.fromarray(sketch).convert('RGB')
    
    def image_pixelate(self, img, params):
        """Apply pixelate effect to image"""
        pixel_size = params.get('size', 10)
        width, height = img.size
        small = img.resize((width // pixel_size, height // pixel_size), Image.Resampling.NEAREST)
        return small.resize((width, height), Image.Resampling.NEAREST)
    
    def image_mosaic(self, img, params):
        """Apply mosaic effect to image"""
        block_size = params.get('size', 20)
        width, height = img.size
        small = img.resize((width // block_size, height // block_size), Image.Resampling.NEAREST)
        return small.resize((width, height), Image.Resampling.NEAREST)
    
    def image_halftone(self, img, params):
        """Apply halftone effect to image"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        return Image.fromarray(binary).convert('RGB')
    
    def image_glow(self, img, params):
        """Apply glow effect to image"""
        blurred = img.filter(ImageFilter.GaussianBlur(radius=5))
        return Image.blend(img, blurred, 0.3)
    
    def image_mirror(self, img, params):
        """Apply mirror effect to image"""
        return ImageOps.mirror(img)
    
    def image_flip(self, img, params):
        """Apply flip effect to image"""
        return ImageOps.flip(img)
    
    def image_rotate_90(self, img, params):
        """Rotate image 90 degrees"""
        return img.rotate(90, expand=True)
    
    def image_rotate_180(self, img, params):
        """Rotate image 180 degrees"""
        return img.rotate(180, expand=True)

# Create global instance
effects_processor = EffectsProcessor()
