"""
Compression Processor - Handles video and image compression
Author: @kinva_master
"""

import os
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image

try:
    import cv2
    from moviepy.editor import VideoFileClip
except ImportError:
    pass

from ..config import Config
from ..utils import format_file_size

logger = logging.getLogger(__name__)

class CompressionProcessor:
    """Handles compression for videos and images"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'compressed'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Compression levels
        self.compression_levels = {
            'low': {'crf': 28, 'preset': 'veryfast', 'quality': 85, 'target_size': 0.5},
            'medium': {'crf': 32, 'preset': 'faster', 'quality': 75, 'target_size': 0.3},
            'high': {'crf': 36, 'preset': 'fast', 'quality': 65, 'target_size': 0.2},
            'ultra': {'crf': 40, 'preset': 'medium', 'quality': 55, 'target_size': 0.1}
        }
        
        # Video codecs
        self.video_codecs = {
            'h264': 'libx264',
            'h265': 'libx265',
            'vp9': 'libvpx-vp9',
            'av1': 'libaom-av1'
        }
        
        # Image formats
        self.image_formats = {
            'jpg': {'quality': 85, 'optimize': True},
            'png': {'compress_level': 9, 'optimize': True},
            'webp': {'quality': 85, 'method': 6},
            'avif': {'quality': 85, 'speed': 4}
        }
    
    def compress_video(self, input_path: str, level: str = 'medium', 
                       codec: str = 'h264', width: int = None, 
                       height: int = None, bitrate: str = None) -> str:
        """Compress video file"""
        try:
            settings = self.compression_levels.get(level, self.compression_levels['medium'])
            video_codec = self.video_codecs.get(codec, self.video_codecs['h264'])
            
            # Get video info
            cap = cv2.VideoCapture(input_path)
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Calculate new dimensions if needed
            if width or height:
                if width and height:
                    new_width, new_height = width, height
                elif width:
                    ratio = width / original_width
                    new_width = width
                    new_height = int(original_height * ratio)
                else:
                    ratio = height / original_height
                    new_width = int(original_width * ratio)
                    new_height = height
            else:
                new_width, new_height = original_width, original_height
            
            # Build FFmpeg command
            output_filename = f"compressed_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', video_codec,
                '-crf', str(settings['crf']),
                '-preset', settings['preset'],
                '-vf', f'scale={new_width}:{new_height}',
            ]
            
            if bitrate:
                cmd.extend(['-b:v', bitrate])
            
            if codec == 'h265':
                cmd.extend(['-tag:v', 'hvc1'])
            
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',
                output_path
            ])
            
            # Run compression
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
            
            # Calculate compression stats
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Video compressed: {format_file_size(original_size)} -> {format_file_size(compressed_size)} ({reduction:.1f}% reduction)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video compression error: {e}")
            raise
    
    def compress_image(self, input_path: str, level: str = 'medium',
                       format: str = 'jpg', width: int = None, 
                       height: int = None, quality: int = None) -> str:
        """Compress image file"""
        try:
            settings = self.compression_levels.get(level, self.compression_levels['medium'])
            format_settings = self.image_formats.get(format.lower(), self.image_formats['jpg'])
            
            # Open image
            img = Image.open(input_path)
            
            # Resize if needed
            if width or height:
                if width and height:
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                elif width:
                    ratio = width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((width, new_height), Image.Resampling.LANCZOS)
                else:
                    ratio = height / img.height
                    new_width = int(img.width * ratio)
                    img = img.resize((new_width, height), Image.Resampling.LANCZOS)
            
            # Set quality
            if quality is None:
                quality = settings['quality']
            
            # Save compressed image
            output_filename = f"compressed_{int(datetime.now().timestamp())}.{format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            if format.lower() == 'jpg' or format.lower() == 'jpeg':
                img.save(output_path, format='JPEG', quality=quality, optimize=True)
            elif format.lower() == 'png':
                img.save(output_path, format='PNG', compress_level=format_settings['compress_level'], optimize=True)
            elif format.lower() == 'webp':
                img.save(output_path, format='WEBP', quality=quality, method=format_settings['method'])
            else:
                img.save(output_path, format=format.upper(), quality=quality)
            
            # Calculate compression stats
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Image compressed: {format_file_size(original_size)} -> {format_file_size(compressed_size)} ({reduction:.1f}% reduction)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Image compression error: {e}")
            raise
    
    def batch_compress(self, input_paths: List[str], level: str = 'medium',
                       format: str = 'jpg', output_dir: str = None) -> List[str]:
        """Compress multiple files"""
        output_paths = []
        
        for input_path in input_paths:
            try:
                if input_path.lower().endswith(tuple(Config.ALLOWED_VIDEOS)):
                    output_path = self.compress_video(input_path, level)
                else:
                    output_path = self.compress_image(input_path, level, format)
                
                output_paths.append(output_path)
                
            except Exception as e:
                logger.error(f"Batch compression error for {input_path}: {e}")
                continue
        
        return output_paths
    
    def compress_to_target_size(self, input_path: str, target_size_mb: float,
                                 max_attempts: int = 10) -> str:
        """Compress to target file size"""
        try:
            original_size = os.path.getsize(input_path) / (1024 * 1024)
            
            if original_size <= target_size_mb:
                return input_path
            
            # Calculate target reduction
            target_ratio = target_size_mb / original_size
            
            # Find appropriate compression level
            for level, settings in self.compression_levels.items():
                if settings['target_size'] <= target_ratio:
                    return self.compress_video(input_path, level)
            
            # If no level matches, use ultra compression
            return self.compress_video(input_path, 'ultra')
            
        except Exception as e:
            logger.error(f"Target size compression error: {e}")
            raise
    
    def estimate_compression(self, input_path: str, level: str = 'medium') -> Dict:
        """Estimate compression results without actually compressing"""
        try:
            original_size = os.path.getsize(input_path)
            settings = self.compression_levels.get(level, self.compression_levels['medium'])
            
            estimated_size = original_size * settings['target_size']
            estimated_reduction = (1 - estimated_size / original_size) * 100
            
            return {
                'original_size': original_size,
                'original_size_formatted': format_file_size(original_size),
                'estimated_size': estimated_size,
                'estimated_size_formatted': format_file_size(estimated_size),
                'estimated_reduction': estimated_reduction,
                'level': level,
                'settings': settings
            }
            
        except Exception as e:
            logger.error(f"Compression estimate error: {e}")
            return {}
    
    def get_optimal_compression(self, input_path: str, target_quality: int = 80) -> Dict:
        """Get optimal compression settings for target quality"""
        try:
            # For images
            if input_path.lower().endswith(tuple(Config.ALLOWED_IMAGES)):
                img = Image.open(input_path)
                original_size = os.path.getsize(input_path)
                
                results = []
                for level, settings in self.compression_levels.items():
                    # Test compression at this level
                    temp_path = self.compress_image(input_path, level, quality=settings['quality'])
                    compressed_size = os.path.getsize(temp_path)
                    quality_score = self._estimate_image_quality(temp_path)
                    
                    results.append({
                        'level': level,
                        'size': compressed_size,
                        'quality': quality_score,
                        'reduction': (1 - compressed_size / original_size) * 100
                    })
                    
                    # Cleanup
                    os.remove(temp_path)
                
                # Find best balance
                best = min(results, key=lambda x: abs(x['quality'] - target_quality))
                return best
            
            # For videos
            else:
                return {'level': 'medium', 'estimated_reduction': 70}
            
        except Exception as e:
            logger.error(f"Optimal compression error: {e}")
            return {'level': 'medium'}
    
    def _estimate_image_quality(self, image_path: str) -> int:
        """Estimate image quality (0-100)"""
        try:
            import numpy as np
            
            img = cv2.imread(image_path)
            if img is None:
                return 50
            
            # Calculate blur metric
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-100 (higher blur = lower quality)
            quality = max(0, min(100, 100 - (blur / 10)))
            
            return int(quality)
            
        except Exception as e:
            logger.error(f"Quality estimation error: {e}")
            return 50
    
    def web_optimized(self, input_path: str) -> str:
        """Optimize for web delivery"""
        try:
            if input_path.lower().endswith(tuple(Config.ALLOWED_VIDEOS)):
                return self.compress_video(input_path, 'medium', bitrate='500k')
            else:
                return self.compress_image(input_path, 'high', format='webp')
                
        except Exception as e:
            logger.error(f"Web optimization error: {e}")
            return input_path
    
    def compress_gif(self, input_path: str, level: str = 'medium', 
                     width: int = None, fps: int = 15) -> str:
        """Compress GIF file"""
        try:
            from PIL import ImageSequence
            
            settings = self.compression_levels.get(level, self.compression_levels['medium'])
            
            # Open GIF
            img = Image.open(input_path)
            
            frames = []
            for frame in ImageSequence.Iterator(img):
                frame = frame.copy()
                
                # Resize if needed
                if width:
                    ratio = width / frame.width
                    new_height = int(frame.height * ratio)
                    frame = frame.resize((width, new_height), Image.Resampling.LANCZOS)
                
                # Reduce colors for compression
                frame = frame.convert('P', palette=Image.ADAPTIVE, colors=min(256, int(256 * settings['target_size'])))
                frames.append(frame)
            
            # Save compressed GIF
            output_filename = f"compressed_gif_{int(datetime.now().timestamp())}.gif"
            output_path = os.path.join(self.output_dir, output_filename)
            
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=img.info.get('duration', 100),
                loop=img.info.get('loop', 0)
            )
            
            # Calculate compression stats
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / original_size) * 100
            
            logger.info(f"GIF compressed: {format_file_size(original_size)} -> {format_file_size(compressed_size)} ({reduction:.1f}% reduction)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"GIF compression error: {e}")
            raise

# Create global instance
compression_processor = CompressionProcessor()
