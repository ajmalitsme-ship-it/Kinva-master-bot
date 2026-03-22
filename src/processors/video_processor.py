"""
Video Processor - Handles all video processing operations
Author: @kinva_master
"""

import os
import logging
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

try:
    import cv2
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
    from moviepy.video.fx import resize, rotate, speedx, time_mirror, lum_contrast, colorx
    from moviepy.audio.fx import volumex
except ImportError as e:
    print(f"Warning: Video processing imports failed: {e}")

from ..config import Config
from ..utils import get_video_info, cleanup_file, TemporaryDirectory, format_file_size

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Main video processor class"""
    
    def __init__(self):
        self.temp_dir = Path(Config.TEMP_DIR) / 'video'
        self.output_dir = Path(Config.OUTPUT_DIR) / 'video'
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Available video effects
        self.available_effects = {
            # Color Effects
            'vintage': self._apply_vintage,
            'cinematic': self._apply_cinematic,
            'black_white': self._apply_black_white,
            'sepia': self._apply_sepia,
            'glitch': self._apply_glitch,
            'neon': self._apply_neon,
            'thermal': self._apply_thermal,
            'night_vision': self._apply_night_vision,
            
            # Filter Effects
            'blur': self._apply_blur,
            'sharpen': self._apply_sharpen,
            'edge': self._apply_edge,
            'cartoon': self._apply_cartoon,
            'oil_paint': self._apply_oil_paint,
            'sketch': self._apply_sketch,
            'watercolor': self._apply_watercolor,
            
            # Transform Effects
            'mirror': self._apply_mirror,
            'rotate_90': lambda c: rotate(c, 90),
            'rotate_180': lambda c: rotate(c, 180),
            'rotate_270': lambda c: rotate(c, 270),
            
            # Speed Effects
            'slow_motion': lambda c: speedx(c, 0.5),
            'fast_motion': lambda c: speedx(c, 2.0),
            'reverse': lambda c: time_mirror(c),
            
            # Audio Effects
            'volume_up': lambda c: c.volumex(1.5),
            'volume_down': lambda c: c.volumex(0.5),
            'mute': lambda c: c.without_audio(),
        }
        
        # Compression quality settings
        self.compression_settings = {
            'low': {'crf': 28, 'preset': 'veryfast', 'bitrate': '500k'},
            'medium': {'crf': 32, 'preset': 'faster', 'bitrate': '300k'},
            'high': {'crf': 36, 'preset': 'fast', 'bitrate': '200k'},
            'ultra': {'crf': 40, 'preset': 'medium', 'bitrate': '100k'}
        }
        
        # Export quality settings
        self.quality_settings = {
            '480p': {'width': 854, 'height': 480, 'bitrate': '1000k'},
            '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k'},
            '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k'},
            '4k': {'width': 3840, 'height': 2160, 'bitrate': '15000k'}
        }
    
    def process(self, input_path: str, effects: List[str] = None,
                filters: List[str] = None, transitions: List[str] = None,
                quality: str = '720p', output_format: str = 'mp4') -> str:
        """Process video with effects and filters"""
        
        effects = effects or []
        filters = filters or []
        transitions = transitions or []
        
        # Create temporary directory
        with TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, f"temp_{int(datetime.now().timestamp())}.mp4")
            
            try:
                # Load video
                clip = VideoFileClip(input_path)
                
                # Apply effects
                for effect in effects:
                    if effect in self.available_effects:
                        try:
                            clip = self.available_effects[effect](clip)
                        except Exception as e:
                            logger.error(f"Failed to apply effect {effect}: {e}")
                
                # Apply filters
                for filter_name in filters:
                    clip = self._apply_filter(clip, filter_name)
                
                # Set quality
                quality_settings = self.quality_settings.get(quality, self.quality_settings['720p'])
                clip = clip.resize(height=quality_settings['height'])
                
                # Write output
                output_filename = f"processed_{int(datetime.now().timestamp())}.{output_format}"
                output_path = os.path.join(self.output_dir, output_filename)
                
                clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    bitrate=quality_settings['bitrate'],
                    temp_audiofile=temp_path,
                    remove_temp=True,
                    logger=None,
                    verbose=False
                )
                
                clip.close()
                return output_path
                
            except Exception as e:
                logger.error(f"Video processing error: {e}")
                raise
            finally:
                if 'clip' in locals():
                    clip.close()
    
    def compress(self, input_path: str, level: str = 'medium') -> str:
        """Compress video file"""
        settings = self.compression_settings.get(level, self.compression_settings['medium'])
        
        output_filename = f"compressed_{int(datetime.now().timestamp())}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Use FFmpeg for compression
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-crf', str(settings['crf']),
            '-preset', settings['preset'],
            '-b:v', settings['bitrate'],
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Video compressed: {format_file_size(original_size)} -> {format_file_size(compressed_size)} ({reduction:.1f}% reduction)")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Compression failed: {e.stderr}")
            raise
    
    def merge(self, video_paths: List[str], transitions: List[str] = None) -> str:
        """Merge multiple videos"""
        clips = []
        
        try:
            for path in video_paths:
                clip = VideoFileClip(path)
                clips.append(clip)
            
            # Apply transitions if specified
            if transitions:
                # TODO: Implement transitions between clips
                pass
            
            # Concatenate clips
            final_clip = concatenate_videoclips(clips, method="compose")
            
            output_filename = f"merged_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video merge error: {e}")
            raise
        finally:
            for clip in clips:
                clip.close()
            if 'final_clip' in locals():
                final_clip.close()
    
    def trim(self, input_path: str, start: float, end: float) -> str:
        """Trim video"""
        try:
            clip = VideoFileClip(input_path).subclip(start, end)
            
            output_filename = f"trimmed_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video trim error: {e}")
            raise
    
    def crop(self, input_path: str, x: int, y: int, width: int, height: int) -> str:
        """Crop video"""
        try:
            clip = VideoFileClip(input_path).crop(x1=x, y1=y, x2=x+width, y2=y+height)
            
            output_filename = f"cropped_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video crop error: {e}")
            raise
    
    def resize(self, input_path: str, width: int = None, height: int = None) -> str:
        """Resize video"""
        try:
            clip = VideoFileClip(input_path)
            
            if width and height:
                clip = clip.resize((width, height))
            elif width:
                clip = clip.resize(width=width)
            elif height:
                clip = clip.resize(height=height)
            
            output_filename = f"resized_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video resize error: {e}")
            raise
    
    def extract_audio(self, input_path: str, output_format: str = 'mp3') -> str:
        """Extract audio from video"""
        try:
            clip = VideoFileClip(input_path)
            audio = clip.audio
            
            if audio is None:
                raise ValueError("No audio track found in video")
            
            output_filename = f"audio_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            audio.write_audiofile(output_path)
            clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            raise
    
    def add_audio(self, video_path: str, audio_path: str, volume: float = 1.0) -> str:
        """Add audio to video"""
        try:
            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)
            
            # Trim audio to match video length if longer
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            
            # Adjust audio volume
            audio = audio.volumex(volume)
            
            # Set audio to video
            final = video.set_audio(audio)
            
            output_filename = f"with_audio_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            video.close()
            audio.close()
            final.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Add audio error: {e}")
            raise
    
    def extract_frame(self, input_path: str, timestamp: float) -> str:
        """Extract frame at specific timestamp"""
        try:
            cap = cv2.VideoCapture(input_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            
            ret, frame = cap.read()
            
            if ret:
                output_filename = f"frame_{int(datetime.now().timestamp())}.jpg"
                output_path = os.path.join(self.output_dir, output_filename)
                cv2.imwrite(output_path, frame)
                cap.release()
                return output_path
            
            cap.release()
            return None
            
        except Exception as e:
            logger.error(f"Frame extraction error: {e}")
            raise
    
    def create_gif(self, input_path: str, start: float = 0, duration: float = 5,
                   width: int = 480, fps: int = 10) -> str:
        """Create GIF from video"""
        try:
            clip = VideoFileClip(input_path).subclip(start, start + duration)
            clip = clip.resize(width=width)
            
            output_filename = f"gif_{int(datetime.now().timestamp())}.gif"
            output_path = os.path.join(self.output_dir, output_filename)
            
            clip.write_gif(output_path, fps=fps, verbose=False, logger=None)
            clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"GIF creation error: {e}")
            raise
    
    def reverse(self, input_path: str) -> str:
        """Reverse video"""
        try:
            clip = VideoFileClip(input_path)
            reversed_clip = time_mirror(clip)
            
            output_filename = f"reversed_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            reversed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            clip.close()
            reversed_clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video reverse error: {e}")
            raise
    
    def speed(self, input_path: str, factor: float) -> str:
        """Change video speed"""
        try:
            clip = VideoFileClip(input_path)
            speed_clip = speedx(clip, factor)
            
            output_filename = f"speed_{factor}x_{int(datetime.now().timestamp())}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            speed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            clip.close()
            speed_clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Speed change error: {e}")
            raise
    
    # ============================================
    # EFFECT IMPLEMENTATIONS
    # ============================================
    
    def _apply_vintage(self, clip):
        """Apply vintage effect"""
        def vintage_filter(get_frame, t):
            frame = get_frame(t)
            # Convert to numpy array
            frame = np.array(frame)
            # Sepia transformation
            sepia = np.array([[0.393, 0.769, 0.189],
                              [0.349, 0.686, 0.168],
                              [0.272, 0.534, 0.131]])
            frame = frame @ sepia.T
            frame = np.clip(frame, 0, 255).astype(np.uint8)
            # Add grain
            noise = np.random.normal(0, 10, frame.shape)
            frame = frame + noise
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(vintage_filter)
    
    def _apply_cinematic(self, clip):
        """Apply cinematic effect"""
        def cinematic_filter(get_frame, t):
            frame = get_frame(t)
            # Increase contrast
            frame = np.clip((frame - 128) * 1.2 + 128, 0, 255).astype(np.uint8)
            # Add letterbox
            h, w = frame.shape[:2]
            bar_height = int(h * 0.1)
            frame[:bar_height] = 0
            frame[-bar_height:] = 0
            return frame
        
        return clip.fl(cinematic_filter)
    
    def _apply_black_white(self, clip):
        """Apply black and white effect"""
        return clip.to_grayscale()
    
    def _apply_sepia(self, clip):
        """Apply sepia effect"""
        def sepia_filter(get_frame, t):
            frame = get_frame(t)
            sepia = np.array([[0.393, 0.769, 0.189],
                              [0.349, 0.686, 0.168],
                              [0.272, 0.534, 0.131]])
            frame = frame @ sepia.T
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(sepia_filter)
    
    def _apply_glitch(self, clip):
        """Apply glitch effect"""
        def glitch_filter(get_frame, t):
            frame = get_frame(t)
            if np.random.random() > 0.95:
                # Channel shift
                frame[:, :, 0] = np.roll(frame[:, :, 0], shift=10, axis=1)
                frame[:, :, 1] = np.roll(frame[:, :, 1], shift=-10, axis=1)
                # Add scanlines
                frame[::20] = 0
            return frame
        
        return clip.fl(glitch_filter)
    
    def _apply_neon(self, clip):
        """Apply neon effect"""
        def neon_filter(get_frame, t):
            frame = get_frame(t)
            # Increase saturation
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            # Add glow
            kernel = np.ones((5, 5), np.float32) / 25
            blurred = cv2.filter2D(frame, -1, kernel)
            frame = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(neon_filter)
    
    def _apply_thermal(self, clip):
        """Apply thermal vision effect"""
        def thermal_filter(get_frame, t):
            frame = get_frame(t)
            # Convert to thermal colormap
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
            return cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB)
        
        return clip.fl(thermal_filter)
    
    def _apply_night_vision(self, clip):
        """Apply night vision effect"""
        def night_vision_filter(get_frame, t):
            frame = get_frame(t)
            # Convert to green tint
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            frame[:, :, 0] = frame[:, :, 0] * 0.3
            frame[:, :, 2] = frame[:, :, 2] * 0.3
            # Add noise
            noise = np.random.normal(0, 20, frame.shape)
            frame = frame + noise
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(night_vision_filter)
    
    def _apply_blur(self, clip):
        """Apply blur effect"""
        def blur_filter(get_frame, t):
            frame = get_frame(t)
            kernel = np.ones((5, 5), np.float32) / 25
            frame = cv2.filter2D(frame, -1, kernel)
            return frame
        
        return clip.fl(blur_filter)
    
    def _apply_sharpen(self, clip):
        """Apply sharpen effect"""
        def sharpen_filter(get_frame, t):
            frame = get_frame(t)
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            frame = cv2.filter2D(frame, -1, kernel)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(sharpen_filter)
    
    def _apply_edge(self, clip):
        """Apply edge detection effect"""
        def edge_filter(get_frame, t):
            frame = get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        return clip.fl(edge_filter)
    
    def _apply_cartoon(self, clip):
        """Apply cartoon effect"""
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
    
    def _apply_oil_paint(self, clip):
        """Apply oil paint effect"""
        def oil_paint_filter(get_frame, t):
            frame = get_frame(t)
            # Simple oil paint simulation
            kernel = np.ones((5, 5), np.float32) / 25
            frame = cv2.filter2D(frame, -1, kernel)
            # Increase saturation
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.2, 0, 255)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(oil_paint_filter)
    
    def _apply_sketch(self, clip):
        """Apply sketch effect"""
        def sketch_filter(get_frame, t):
            frame = get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            inv = 255 - gray
            blur = cv2.GaussianBlur(inv, (21, 21), 0)
            sketch = cv2.divide(gray, 255 - blur, scale=256)
            return cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)
        
        return clip.fl(sketch_filter)
    
    def _apply_watercolor(self, clip):
        """Apply watercolor effect"""
        def watercolor_filter(get_frame, t):
            frame = get_frame(t)
            frame = cv2.stylization(frame, sigma_s=60, sigma_r=0.07)
            return frame
        
        return clip.fl(watercolor_filter)
    
    def _apply_mirror(self, clip):
        """Apply mirror effect"""
        def mirror_filter(get_frame, t):
            frame = get_frame(t)
            frame = np.fliplr(frame)
            return frame
        
        return clip.fl(mirror_filter)
    
    def _apply_filter(self, clip, filter_name: str):
        """Apply video filter"""
        # Color filters
        if filter_name == 'brightness':
            return clip.fx(colorx, 1.2)
        elif filter_name == 'contrast':
            return clip.fx(lum_contrast, contrast=0.2)
        elif filter_name == 'saturation':
            return clip.fx(colorx, 1.3)
        
        return clip

# Create global instance
video_processor = VideoProcessor()
