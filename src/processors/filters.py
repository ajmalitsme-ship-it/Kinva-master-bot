"""
Filters Processor - Handles video and image filters
Author: @kinva_master
"""

import os
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

try:
    import cv2
    from moviepy.editor import VideoFileClip
except ImportError:
    pass

from ..config import Config

logger = logging.getLogger(__name__)

class FiltersProcessor:
    """Handles video and image filters"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'filters'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Available video filters
        self.video_filters = {
            # Color Filters
            'brightness': self.brightness_filter,
            'contrast': self.contrast_filter,
            'saturation': self.saturation_filter,
            'hue': self.hue_filter,
            'gamma': self.gamma_filter,
            'temperature': self.temperature_filter,
            'tint': self.tint_filter,
            
            # Artistic Filters
            'oil_paint': self.oil_paint_filter,
            'watercolor': self.watercolor_filter,
            'sketch': self.sketch_filter,
            'cartoon': self.cartoon_filter,
            'pencil': self.pencil_filter,
            'charcoal': self.charcoal_filter,
            'pastel': self.pastel_filter,
            
            # Blur Filters
            'gaussian_blur': self.gaussian_blur_filter,
            'motion_blur': self.motion_blur_filter,
            'zoom_blur': self.zoom_blur_filter,
            'radial_blur': self.radial_blur_filter,
            
            # Edge Filters
            'edge_detect': self.edge_detect_filter,
            'canny': self.canny_filter,
            'sobel': self.sobel_filter,
            'laplacian': self.laplacian_filter,
            
            # Special Effects
            'vignette': self.vignette_filter,
            'grain': self.grain_filter,
            'scanlines': self.scanlines_filter,
            'chromatic_aberration': self.chromatic_aberration_filter,
            'lens_distortion': self.lens_distortion_filter,
        }
        
        # Available image filters
        self.image_filters = {
            # Basic Filters
            'brightness': self.image_brightness,
            'contrast': self.image_contrast,
            'saturation': self.image_saturation,
            'sharpness': self.image_sharpness,
            'blur': self.image_blur,
            
            # Color Filters
            'temperature': self.image_temperature,
            'tint': self.image_tint,
            'vibrance': self.image_vibrance,
            'hue': self.image_hue,
            
            # Artistic Filters
            'oil_paint': self.image_oil_paint,
            'watercolor': self.image_watercolor,
            'sketch': self.image_sketch,
            'pencil': self.image_pencil,
            'pastel': self.image_pastel,
            
            # Special Filters
            'vignette': self.image_vignette,
            'grain': self.image_grain,
            'polaroid': self.image_polaroid,
            'instagram': self.image_instagram,
        }
    
    def apply_video_filter(self, video_path: str, filter_name: str,
                          intensity: float = 1.0) -> str:
        """Apply filter to video"""
        try:
            if filter_name not in self.video_filters:
                raise ValueError(f"Filter {filter_name} not found")
            
            clip = VideoFileClip(video_path)
            
            # Apply filter
            result = self.video_filters[filter_name](clip, intensity)
            
            output_filename = f"filter_{filter_name}_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            result.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video filter error: {e}")
            raise
    
    def apply_image_filter(self, image_path: str, filter_name: str,
                          intensity: float = 1.0) -> str:
        """Apply filter to image"""
        try:
            if filter_name not in self.image_filters:
                raise ValueError(f"Filter {filter_name} not found")
            
            img = Image.open(image_path)
            
            # Apply filter
            result = self.image_filters[filter_name](img, intensity)
            
            output_filename = f"filter_{filter_name}_{int(datetime.now().timestamp())}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            result.save(output_path, quality=95)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Image filter error: {e}")
            raise
    
    # ============================================
    # VIDEO FILTERS
    # ============================================
    
    def brightness_filter(self, clip, intensity):
        """Adjust brightness"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._adjust_brightness(img, intensity)))
    
    def contrast_filter(self, clip, intensity):
        """Adjust contrast"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._adjust_contrast(img, intensity)))
    
    def saturation_filter(self, clip, intensity):
        """Adjust saturation"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._adjust_saturation(img, intensity)))
    
    def hue_filter(self, clip, intensity):
        """Adjust hue"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._adjust_hue(img, intensity)))
    
    def gamma_filter(self, clip, intensity):
        """Adjust gamma"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._adjust_gamma(img, intensity)))
    
    def temperature_filter(self, clip, intensity):
        """Adjust color temperature"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._adjust_temperature(img, intensity)))
    
    def tint_filter(self, clip, intensity):
        """Adjust tint"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._adjust_tint(img, intensity)))
    
    def oil_paint_filter(self, clip, intensity):
        """Oil paint effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._oil_paint(img, intensity)))
    
    def watercolor_filter(self, clip, intensity):
        """Watercolor effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._watercolor(img, intensity)))
    
    def sketch_filter(self, clip, intensity):
        """Sketch effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._sketch(img, intensity)))
    
    def cartoon_filter(self, clip, intensity):
        """Cartoon effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._cartoon(img, intensity)))
    
    def pencil_filter(self, clip, intensity):
        """Pencil sketch effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._pencil(img, intensity)))
    
    def charcoal_filter(self, clip, intensity):
        """Charcoal drawing effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._charcoal(img, intensity)))
    
    def pastel_filter(self, clip, intensity):
        """Pastel effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._pastel(img, intensity)))
    
    def gaussian_blur_filter(self, clip, intensity):
        """Gaussian blur"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._gaussian_blur(img, intensity)))
    
    def motion_blur_filter(self, clip, intensity):
        """Motion blur"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._motion_blur(img, intensity)))
    
    def zoom_blur_filter(self, clip, intensity):
        """Zoom blur"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._zoom_blur(img, intensity)))
    
    def radial_blur_filter(self, clip, intensity):
        """Radial blur"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._radial_blur(img, intensity)))
    
    def edge_detect_filter(self, clip, intensity):
        """Edge detection"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._edge_detect(img, intensity)))
    
    def canny_filter(self, clip, intensity):
        """Canny edge detection"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._canny(img, intensity)))
    
    def sobel_filter(self, clip, intensity):
        """Sobel edge detection"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._sobel(img, intensity)))
    
    def laplacian_filter(self, clip, intensity):
        """Laplacian edge detection"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._laplacian(img, intensity)))
    
    def vignette_filter(self, clip, intensity):
        """Vignette effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._vignette(img, intensity)))
    
    def grain_filter(self, clip, intensity):
        """Film grain effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._grain(img, intensity)))
    
    def scanlines_filter(self, clip, intensity):
        """Scanlines effect"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._scanlines(img, intensity)))
    
    def chromatic_aberration_filter(self, clip, intensity):
        """Chromatic aberration"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._chromatic_aberration(img, intensity)))
    
    def lens_distortion_filter(self, clip, intensity):
        """Lens distortion"""
        return clip.fx(lambda c: c.fl_image(lambda img: self._lens_distortion(img, intensity)))
    
    # ============================================
    # IMAGE FILTERS
    # ============================================
    
    def image_brightness(self, img, intensity):
        """Adjust brightness"""
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(intensity)
    
    def image_contrast(self, img, intensity):
        """Adjust contrast"""
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(intensity)
    
    def image_saturation(self, img, intensity):
        """Adjust saturation"""
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(intensity)
    
    def image_sharpness(self, img, intensity):
        """Adjust sharpness"""
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(intensity)
    
    def image_blur(self, img, intensity):
        """Apply blur"""
        radius = int(intensity * 5)
        return img.filter(ImageFilter.GaussianBlur(radius=radius))
    
    def image_temperature(self, img, intensity):
        """Adjust color temperature"""
        if intensity > 1:
            # Warmer (more red)
            r, g, b = img.split()
            r = r.point(lambda i: min(255, int(i * intensity)))
            return Image.merge('RGB', (r, g, b))
        else:
            # Cooler (more blue)
            r, g, b = img.split()
            b = b.point(lambda i: min(255, int(i / intensity)))
            return Image.merge('RGB', (r, g, b))
    
    def image_tint(self, img, intensity):
        """Adjust tint"""
        r, g, b = img.split()
        r = r.point(lambda i: min(255, int(i * (1 + intensity * 0.5))))
        g = g.point(lambda i: min(255, int(i * (1 + intensity * 0.3))))
        b = b.point(lambda i: min(255, int(i * (1 - intensity * 0.2))))
        return Image.merge('RGB', (r, g, b))
    
    def image_vibrance(self, img, intensity):
        """Adjust vibrance"""
        arr = np.array(img)
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * intensity, 0, 255)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return Image.fromarray(result)
    
    def image_hue(self, img, intensity):
        """Adjust hue"""
        arr = np.array(img)
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + intensity * 180) % 180
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return Image.fromarray(result)
    
    def image_oil_paint(self, img, intensity):
        """Oil paint effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        sigma_s = int(50 * intensity)
        sigma_r = 0.6 / intensity
        result = cv2.stylization(arr, sigma_s=sigma_s, sigma_r=sigma_r)
        return Image.fromarray(result)
    
    def image_watercolor(self, img, intensity):
        """Watercolor effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        sigma_s = int(60 * intensity)
        sigma_r = 0.07 / intensity
        result = cv2.stylization(arr, sigma_s=sigma_s, sigma_r=sigma_r)
        return Image.fromarray(result)
    
    def image_sketch(self, img, intensity):
        """Sketch effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return Image.fromarray(sketch).convert('RGB')
    
    def image_pencil(self, img, intensity):
        """Pencil sketch effect"""
        if cv2 is None:
            return img
        
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        pencil = cv2.divide(gray, 255 - blur, scale=256)
        return Image.fromarray(pencil).convert('RGB')
    
    def image_pastel(self, img, intensity):
        """Pastel effect"""
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        return img.filter(ImageFilter.SMOOTH)
    
    def image_vignette(self, img, intensity):
        """Vignette effect"""
        width, height = img.size
        arr = np.array(img)
        
        X, Y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        radius = np.sqrt(X**2 + Y**2)
        mask = 1 - np.clip(radius * intensity, 0, 1)
        mask = mask[:, :, np.newaxis]
        
        arr = arr * mask
        return Image.fromarray(arr.astype(np.uint8))
    
    def image_grain(self, img, intensity):
        """Film grain effect"""
        arr = np.array(img)
        noise = np.random.normal(0, intensity * 20, arr.shape)
        arr = arr + noise
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    
    def image_polaroid(self, img, intensity):
        """Polaroid effect"""
        width, height = img.size
        
        # Add white border
        border = int(width * 0.1)
        result = ImageOps.expand(img, border=border, fill='white')
        
        # Add shadow
        shadow = Image.new('RGBA', result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow)
        draw.rectangle([(0, 0), result.size], fill=(0, 0, 0, 50))
        
        # Composite
        result = result.convert('RGBA')
        result = Image.alpha_composite(result, shadow)
        
        return result.convert('RGB')
    
    def image_instagram(self, img, intensity):
        """Instagram-like filter"""
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # Increase saturation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        
        # Add slight vignette
        width, height = img.size
        arr = np.array(img)
        X, Y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        radius = np.sqrt(X**2 + Y**2)
        mask = 1 - np.clip(radius * 0.5, 0, 1)
        mask = mask[:, :, np.newaxis]
        
        arr = arr * mask
        return Image.fromarray(arr.astype(np.uint8))
    
    # ============================================
    # HELPER FUNCTIONS
    # ============================================
    
    def _adjust_brightness(self, img, intensity):
        return np.clip(img * intensity, 0, 255).astype(np.uint8)
    
    def _adjust_contrast(self, img, intensity):
        mean = np.mean(img)
        return np.clip((img - mean) * intensity + mean, 0, 255).astype(np.uint8)
    
    def _adjust_saturation(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = np.stack([gray] * 3, axis=2)
        return np.clip(gray + (img - gray) * intensity, 0, 255).astype(np.uint8)
    
    def _adjust_hue(self, img, intensity):
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + intensity * 180) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    def _adjust_gamma(self, img, intensity):
        gamma = 1.0 / intensity
        table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype(np.uint8)
        return cv2.LUT(img, table)
    
    def _adjust_temperature(self, img, intensity):
        if intensity > 1:
            # Warmer
            img[:, :, 0] = np.clip(img[:, :, 0] * intensity, 0, 255)
        else:
            # Cooler
            img[:, :, 2] = np.clip(img[:, :, 2] / intensity, 0, 255)
        return img
    
    def _adjust_tint(self, img, intensity):
        img[:, :, 0] = np.clip(img[:, :, 0] * (1 + intensity * 0.5), 0, 255)
        img[:, :, 1] = np.clip(img[:, :, 1] * (1 + intensity * 0.3), 0, 255)
        img[:, :, 2] = np.clip(img[:, :, 2] * (1 - intensity * 0.2), 0, 255)
        return img
    
    def _oil_paint(self, img, intensity):
        kernel_size = max(3, int(5 * intensity))
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        return cv2.filter2D(img, -1, kernel)
    
    def _watercolor(self, img, intensity):
        kernel = np.ones((5, 5), np.float32) / 25
        img = cv2.filter2D(img, -1, kernel)
        return img
    
    def _sketch(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)
    
    def _cartoon(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img, 9, 300, 300)
        return cv2.bitwise_and(color, color, mask=edges)
    
    def _pencil(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        pencil = cv2.divide(gray, 255 - blur, scale=256)
        return cv2.cvtColor(pencil, cv2.COLOR_GRAY2RGB)
    
    def _charcoal(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    def _pastel(self, img, intensity):
        img = cv2.GaussianBlur(img, (5, 5), 0)
        img = np.clip(img * 1.1, 0, 255).astype(np.uint8)
        return img
    
    def _gaussian_blur(self, img, intensity):
        radius = int(5 * intensity)
        if radius % 2 == 0:
            radius += 1
        return cv2.GaussianBlur(img, (radius, radius), 0)
    
    def _motion_blur(self, img, intensity):
        size = int(10 * intensity)
        kernel = np.zeros((size, size))
        kernel[int((size-1)/2), :] = np.ones(size)
        kernel = kernel / size
        return cv2.filter2D(img, -1, kernel)
    
    def _zoom_blur(self, img, intensity):
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        kernel_size = int(20 * intensity)
        kernel = np.zeros((kernel_size, kernel_size))
        for i in range(kernel_size):
            kernel[i, i] = 1
        kernel = kernel / kernel_size
        return cv2.filter2D(img, -1, kernel)
    
    def _radial_blur(self, img, intensity):
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        kernel_size = int(15 * intensity)
        kernel = np.zeros((kernel_size, kernel_size))
        for i in range(kernel_size):
            kernel[i, kernel_size - 1 - i] = 1
        kernel = kernel / kernel_size
        return cv2.filter2D(img, -1, kernel)
    
    def _edge_detect(self, img, intensity):
        return cv2.Laplacian(img, cv2.CV_8U)
    
    def _canny(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    def _sobel(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edges = np.sqrt(sobelx**2 + sobely**2)
        edges = np.clip(edges, 0, 255).astype(np.uint8)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    def _laplacian(self, img, intensity):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Laplacian(gray, cv2.CV_64F)
        edges = np.clip(edges, 0, 255).astype(np.uint8)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    def _vignette(self, img, intensity):
        h, w = img.shape[:2]
        X, Y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
        radius = np.sqrt(X**2 + Y**2)
        mask = 1 - np.clip(radius * intensity, 0, 1)
        mask = mask[:, :, np.newaxis]
        return (img * mask).astype(np.uint8)
    
    def _grain(self, img, intensity):
        noise = np.random.normal(0, intensity * 20, img.shape)
        return np.clip(img + noise, 0, 255).astype(np.uint8)
    
    def _scanlines(self, img, intensity):
        h, w = img.shape[:2]
        for i in range(0, h, 2):
            img[i, :] = img[i, :] * (1 - intensity * 0.5)
        return img
    
    def _chromatic_aberration(self, img, intensity):
        shift = int(5 * intensity)
        h, w, c = img.shape
        result = np.zeros_like(img)
        result[:, :, 0] = np.roll(img[:, :, 0], shift, axis=1)
        result[:, :, 1] = img[:, :, 1]
        result[:, :, 2] = np.roll(img[:, :, 2], -shift, axis=1)
        return result
    
    def _lens_distortion(self, img, intensity):
        h, w = img.shape[:2]
        K = np.array([[w, 0, w/2], [0, h, h/2], [0, 0, 1]])
        D = np.array([intensity, 0, 0, 0])
        map1, map2 = cv2.initUndistortRectifyMap(K, D, None, K, (w, h), cv2.CV_32FC1)
        return cv2.remap(img, map1, map2, cv2.INTER_LINEAR)

# Create global instance
filters_processor = FiltersProcessor()
