"""
Video Editor - Video editing timeline editor with advanced features
Author: @kinva_master
"""

import os
import logging
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip
    from moviepy.video.fx import resize, rotate, speedx, time_mirror, lum_contrast, colorx
    from moviepy.audio.fx import volumex
except ImportError:
    VideoFileClip = None
    logger = logging.getLogger(__name__)
    logger.warning("MoviePy not installed. Video editing features will be limited.")

from ..config import Config
from ..utils import generate_uuid, slugify, get_video_info, format_file_size

logger = logging.getLogger(__name__)

class VideoEditor:
    """Video editing timeline editor with professional features"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'videos'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Available transitions
        self.transitions = {
            'fade': self._apply_fade_transition,
            'crossfade': self._apply_crossfade_transition,
            'slide_left': self._apply_slide_left_transition,
            'slide_right': self._apply_slide_right_transition,
            'slide_up': self._apply_slide_up_transition,
            'slide_down': self._apply_slide_down_transition,
            'wipe_left': self._apply_wipe_left_transition,
            'wipe_right': self._apply_wipe_right_transition,
            'zoom': self._apply_zoom_transition,
            'rotate': self._apply_rotate_transition,
            'glitch': self._apply_glitch_transition,
            'flash': self._apply_flash_transition,
            'pixelate': self._apply_pixelate_transition,
            'blur': self._apply_blur_transition,
            'circle_wipe': self._apply_circle_wipe_transition,
            'star_wipe': self._apply_star_wipe_transition,
            'heart_wipe': self._apply_heart_wipe_transition,
            'page_turn': self._apply_page_turn_transition,
            'cube': self._apply_cube_transition,
            '3d_flip': self._apply_3d_flip_transition,
        }
        
        # Available video effects
        self.effects = {
            # Color Effects
            'vintage': self._apply_vintage,
            'cinematic': self._apply_cinematic,
            'black_white': self._apply_black_white,
            'sepia': self._apply_sepia,
            'glitch': self._apply_glitch,
            'neon': self._apply_neon,
            'thermal': self._apply_thermal,
            'night_vision': self._apply_night_vision,
            'dreamy': self._apply_dreamy,
            'dramatic': self._apply_dramatic,
            'pastel': self._apply_pastel,
            'vibrant': self._apply_vibrant,
            'hdr': self._apply_hdr,
            
            # Filter Effects
            'blur': self._apply_blur,
            'sharpen': self._apply_sharpen,
            'edge': self._apply_edge,
            'emboss': self._apply_emboss,
            'cartoon': self._apply_cartoon,
            'oil_paint': self._apply_oil_paint,
            'watercolor': self._apply_watercolor,
            'sketch': self._apply_sketch,
            'pixelate': self._apply_pixelate,
            'mosaic': self._apply_mosaic,
            
            # Transform Effects
            'mirror_horizontal': self._apply_mirror_horizontal,
            'mirror_vertical': self._apply_mirror_vertical,
            'rotate_90': self._apply_rotate_90,
            'rotate_180': self._apply_rotate_180,
            'rotate_270': self._apply_rotate_270,
            'flip': self._apply_flip,
            
            # Speed Effects
            'slow_motion_2x': self._apply_slow_motion_2x,
            'slow_motion_4x': self._apply_slow_motion_4x,
            'fast_motion_2x': self._apply_fast_motion_2x,
            'fast_motion_4x': self._apply_fast_motion_4x,
            'reverse': self._apply_reverse,
            'time_lapse': self._apply_time_lapse,
        }
        
        # Quality presets
        self.quality_presets = {
            '240p': {'width': 426, 'height': 240, 'bitrate': '300k'},
            '360p': {'width': 640, 'height': 360, 'bitrate': '500k'},
            '480p': {'width': 854, 'height': 480, 'bitrate': '1000k'},
            '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k'},
            '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k'},
            '2k': {'width': 2560, 'height': 1440, 'bitrate': '10000k'},
            '4k': {'width': 3840, 'height': 2160, 'bitrate': '20000k'},
        }
        
        # Audio effects
        self.audio_effects = {
            'volume_up': self._volume_up,
            'volume_down': self._volume_down,
            'fade_in': self._audio_fade_in,
            'fade_out': self._audio_fade_out,
            'echo': self._audio_echo,
            'reverb': self._audio_reverb,
            'bass_boost': self._audio_bass_boost,
            'treble_boost': self._audio_treble_boost,
        }
    
    def create_project(self, title: str = "Untitled Project", 
                       width: int = 1920, height: int = 1080, 
                       fps: int = 30) -> Dict:
        """Create new video project"""
        project = {
            'id': generate_uuid(),
            'title': title,
            'settings': {
                'width': width,
                'height': height,
                'fps': fps,
                'quality': '1080p',
                'format': 'mp4'
            },
            'timeline': {
                'tracks': [
                    {'id': generate_uuid(), 'name': 'Video 1', 'type': 'video', 'clips': [], 'muted': False},
                    {'id': generate_uuid(), 'name': 'Video 2', 'type': 'video', 'clips': [], 'muted': False},
                    {'id': generate_uuid(), 'name': 'Audio 1', 'type': 'audio', 'clips': [], 'muted': False},
                    {'id': generate_uuid(), 'name': 'Audio 2', 'type': 'audio', 'clips': [], 'muted': False},
                ],
                'duration': 0
            },
            'clips': [],
            'transitions': [],
            'effects': [],
            'markers': [],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        return project
    
    def add_clip(self, project: Dict, video_path: str, track_index: int = 0,
                 start_time: float = 0, end_time: float = None,
                 position: float = None, volume: float = 1.0) -> Dict:
        """Add video clip to project"""
        clip_info = get_video_info(video_path)
        
        if end_time is None:
            end_time = clip_info.get('duration', 0)
        
        duration = end_time - start_time
        
        if position is None:
            # Find position at end of track
            track = project['timeline']['tracks'][track_index]
            if track['clips']:
                position = max(c['end_time'] for c in track['clips'])
            else:
                position = 0
        
        clip = {
            'id': generate_uuid(),
            'path': video_path,
            'track': track_index,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'position': position,
            'volume': volume,
            'speed': 1.0,
            'effects': [],
            'filters': [],
            'transitions': [],
            'info': clip_info,
            'created_at': datetime.now().isoformat()
        }
        
        project['clips'].append(clip)
        project['timeline']['tracks'][track_index]['clips'].append(clip)
        
        # Update timeline duration
        clip_end = position + duration
        if clip_end > project['timeline']['duration']:
            project['timeline']['duration'] = clip_end
        
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def add_audio(self, project: Dict, audio_path: str, track_index: int = 2,
                  position: float = 0, volume: float = 1.0) -> Dict:
        """Add audio track to project"""
        try:
            audio = AudioFileClip(audio_path)
            
            audio_clip = {
                'id': generate_uuid(),
                'path': audio_path,
                'track': track_index,
                'position': position,
                'duration': audio.duration,
                'volume': volume,
                'effects': [],
                'created_at': datetime.now().isoformat()
            }
            
            project['clips'].append(audio_clip)
            project['timeline']['tracks'][track_index]['clips'].append(audio_clip)
            
            # Update timeline duration
            audio_end = position + audio.duration
            if audio_end > project['timeline']['duration']:
                project['timeline']['duration'] = audio_end
            
            project['metadata']['updated_at'] = datetime.now().isoformat()
            
            audio.close()
            
            return project
            
        except Exception as e:
            logger.error(f"Add audio error: {e}")
            return project
    
    def add_transition(self, project: Dict, clip1_id: str, clip2_id: str,
                      transition_type: str, duration: float = 1.0) -> Dict:
        """Add transition between clips"""
        transition = {
            'id': generate_uuid(),
            'type': transition_type,
            'clip1': clip1_id,
            'clip2': clip2_id,
            'duration': duration,
            'created_at': datetime.now().isoformat()
        }
        
        project['transitions'].append(transition)
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def add_effect(self, project: Dict, clip_id: str, effect_type: str,
                  intensity: float = 1.0, start_time: float = None,
                  end_time: float = None) -> Dict:
        """Add effect to clip"""
        effect = {
            'id': generate_uuid(),
            'type': effect_type,
            'clip_id': clip_id,
            'intensity': intensity,
            'start_time': start_time,
            'end_time': end_time,
            'created_at': datetime.now().isoformat()
        }
        
        project['effects'].append(effect)
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def add_marker(self, project: Dict, time: float, label: str, 
                   color: str = '#ff0000') -> Dict:
        """Add marker at timestamp"""
        marker = {
            'id': generate_uuid(),
            'time': time,
            'label': label,
            'color': color,
            'created_at': datetime.now().isoformat()
        }
        
        project['markers'].append(marker)
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def trim_clip(self, project: Dict, clip_id: str, 
                 new_start: float, new_end: float) -> Dict:
        """Trim video clip"""
        for clip in project['clips']:
            if clip['id'] == clip_id:
                old_duration = clip['duration']
                clip['start_time'] = new_start
                clip['end_time'] = new_end
                clip['duration'] = new_end - new_start
                
                # Adjust position of subsequent clips on same track
                if clip['duration'] != old_duration:
                    delta = clip['duration'] - old_duration
                    for other in project['clips']:
                        if (other['track'] == clip['track'] and 
                            other['position'] > clip['position']):
                            other['position'] += delta
                
                break
        
        # Update timeline duration
        max_end = 0
        for clip in project['clips']:
            clip_end = clip.get('position', 0) + clip.get('duration', 0)
            max_end = max(max_end, clip_end)
        project['timeline']['duration'] = max_end
        
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def split_clip(self, project: Dict, clip_id: str, split_time: float) -> Dict:
        """Split clip at timestamp"""
        for clip in project['clips']:
            if clip['id'] == clip_id:
                if split_time <= clip['start_time'] or split_time >= clip['end_time']:
                    continue
                
                # Calculate split position
                split_position = clip['position'] + (split_time - clip['start_time'])
                
                # Create second clip
                new_clip = clip.copy()
                new_clip['id'] = generate_uuid()
                new_clip['start_time'] = split_time
                new_clip['duration'] = clip['end_time'] - split_time
                new_clip['position'] = split_position
                new_clip['created_at'] = datetime.now().isoformat()
                
                # Update first clip
                clip['end_time'] = split_time
                clip['duration'] = split_time - clip['start_time']
                
                # Add second clip
                project['clips'].append(new_clip)
                project['timeline']['tracks'][clip['track']]['clips'].append(new_clip)
                break
        
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def change_speed(self, project: Dict, clip_id: str, speed: float) -> Dict:
        """Change clip playback speed"""
        for clip in project['clips']:
            if clip['id'] == clip_id:
                old_duration = clip['duration']
                clip['speed'] = speed
                clip['duration'] = (clip['end_time'] - clip['start_time']) / speed
                
                # Adjust position of subsequent clips
                delta = clip['duration'] - old_duration
                for other in project['clips']:
                    if (other['track'] == clip['track'] and 
                        other['position'] > clip['position']):
                        other['position'] += delta
                break
        
        # Update timeline duration
        max_end = 0
        for clip in project['clips']:
            clip_end = clip.get('position', 0) + clip.get('duration', 0)
            max_end = max(max_end, clip_end)
        project['timeline']['duration'] = max_end
        
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def set_volume(self, project: Dict, clip_id: str, volume: float) -> Dict:
        """Set clip volume"""
        for clip in project['clips']:
            if clip['id'] == clip_id:
                clip['volume'] = max(0.0, min(2.0, volume))
                break
        
        project['metadata']['updated_at'] = datetime.now().isoformat()
        
        return project
    
    def export(self, project: Dict, output_format: str = 'mp4',
              quality: str = '1080p', include_audio: bool = True) -> str:
        """Export video project"""
        if VideoFileClip is None:
            raise ImportError("MoviePy not installed")
        
        try:
            # Sort clips by track and position
            video_clips = []
            audio_clips = []
            
            # Collect clips by track
            tracks = {}
            for clip in project['clips']:
                track = clip.get('track', 0)
                if track not in tracks:
                    tracks[track] = []
                tracks[track].append(clip)
            
            # Sort clips in each track by position
            for track in tracks:
                tracks[track].sort(key=lambda c: c.get('position', 0))
            
            # Process each track
            for track_idx in sorted(tracks.keys()):
                track_clips = tracks[track_idx]
                track_type = project['timeline']['tracks'][track_idx]['type']
                
                for clip_data in track_clips:
                    # Load clip
                    clip = VideoFileClip(clip_data['path'])
                    
                    # Trim
                    clip = clip.subclip(clip_data['start_time'], clip_data['end_time'])
                    
                    # Apply speed
                    if clip_data.get('speed', 1.0) != 1.0:
                        clip = speedx(clip, clip_data['speed'])
                    
                    # Apply effects
                    for effect in project['effects']:
                        if effect['clip_id'] == clip_data['id']:
                            if effect['type'] in self.effects:
                                clip = self.effects[effect['type']](clip, effect['intensity'])
                    
                    # Set volume for audio
                    if track_type == 'audio':
                        clip = clip.volumex(clip_data.get('volume', 1.0))
                    
                    # Set position in timeline
                    clip = clip.set_start(clip_data.get('position', 0))
                    
                    if track_type == 'video':
                        video_clips.append(clip)
                    else:
                        audio_clips.append(clip)
            
            # Composite video clips
            if video_clips:
                final_video = CompositeVideoClip(video_clips, 
                                                 size=(project['settings']['width'], 
                                                       project['settings']['height']))
            else:
                final_video = None
            
            # Composite audio clips
            if audio_clips and include_audio:
                final_audio = CompositeAudioClip(audio_clips)
                if final_video:
                    final_video = final_video.set_audio(final_audio)
            
            # Apply transitions
            for transition in project['transitions']:
                # This would need more complex implementation
                pass
            
            # Set quality
            quality_settings = self.quality_presets.get(quality, self.quality_presets['1080p'])
            if final_video:
                final_video = final_video.resize(height=quality_settings['height'])
            
            # Export
            filename = f"{slugify(project['title'])}_{int(datetime.now().timestamp())}.{output_format}"
            filepath = os.path.join(self.output_dir, filename)
            
            if final_video:
                final_video.write_videofile(
                    filepath, 
                    codec='libx264', 
                    audio_codec='aac',
                    bitrate=quality_settings['bitrate'],
                    verbose=False,
                    logger=None
                )
            else:
                # Export only audio
                if audio_clips:
                    final_audio = CompositeAudioClip(audio_clips)
                    final_audio.write_audiofile(filepath)
            
            # Cleanup
            if final_video:
                final_video.close()
            for clip in video_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()
            
            return filepath
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise
    
    # ============================================
    # TRANSITION METHODS
    # ============================================
    
    def _apply_fade_transition(self, clip1, clip2, duration):
        """Apply fade transition"""
        return [clip1.crossfadeout(duration), clip2.crossfadein(duration)]
    
    def _apply_crossfade_transition(self, clip1, clip2, duration):
        """Apply crossfade transition"""
        return [clip1.crossfadeout(duration), clip2.crossfadein(duration)]
    
    def _apply_slide_left_transition(self, clip1, clip2, duration):
        """Apply slide left transition"""
        return [clip1, clip2]
    
    def _apply_slide_right_transition(self, clip1, clip2, duration):
        """Apply slide right transition"""
        return [clip1, clip2]
    
    def _apply_slide_up_transition(self, clip1, clip2, duration):
        """Apply slide up transition"""
        return [clip1, clip2]
    
    def _apply_slide_down_transition(self, clip1, clip2, duration):
        """Apply slide down transition"""
        return [clip1, clip2]
    
    def _apply_wipe_left_transition(self, clip1, clip2, duration):
        """Apply wipe left transition"""
        return [clip1, clip2]
    
    def _apply_wipe_right_transition(self, clip1, clip2, duration):
        """Apply wipe right transition"""
        return [clip1, clip2]
    
    def _apply_zoom_transition(self, clip1, clip2, duration):
        """Apply zoom transition"""
        return [clip1, clip2]
    
    def _apply_rotate_transition(self, clip1, clip2, duration):
        """Apply rotate transition"""
        return [clip1, clip2]
    
    def _apply_glitch_transition(self, clip1, clip2, duration):
        """Apply glitch transition"""
        return [clip1, clip2]
    
    def _apply_flash_transition(self, clip1, clip2, duration):
        """Apply flash transition"""
        return [clip1, clip2]
    
    def _apply_pixelate_transition(self, clip1, clip2, duration):
        """Apply pixelate transition"""
        return [clip1, clip2]
    
    def _apply_blur_transition(self, clip1, clip2, duration):
        """Apply blur transition"""
        return [clip1, clip2]
    
    def _apply_circle_wipe_transition(self, clip1, clip2, duration):
        """Apply circle wipe transition"""
        return [clip1, clip2]
    
    def _apply_star_wipe_transition(self, clip1, clip2, duration):
        """Apply star wipe transition"""
        return [clip1, clip2]
    
    def _apply_heart_wipe_transition(self, clip1, clip2, duration):
        """Apply heart wipe transition"""
        return [clip1, clip2]
    
    def _apply_page_turn_transition(self, clip1, clip2, duration):
        """Apply page turn transition"""
        return [clip1, clip2]
    
    def _apply_cube_transition(self, clip1, clip2, duration):
        """Apply cube transition"""
        return [clip1, clip2]
    
    def _apply_3d_flip_transition(self, clip1, clip2, duration):
        """Apply 3D flip transition"""
        return [clip1, clip2]
    
    # ============================================
    # EFFECT METHODS
    # ============================================
    
    def _apply_vintage(self, clip, intensity):
        """Apply vintage effect"""
        def vintage_filter(get_frame, t):
            frame = get_frame(t)
            import numpy as np
            frame = np.array(frame)
            sepia = np.array([[0.393, 0.769, 0.189],
                              [0.349, 0.686, 0.168],
                              [0.272, 0.534, 0.131]])
            frame = frame @ sepia.T
            noise = np.random.normal(0, 10 * intensity, frame.shape)
            frame = frame + noise
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(vintage_filter)
    
    def _apply_cinematic(self, clip, intensity):
        """Apply cinematic effect"""
        def cinematic_filter(get_frame, t):
            frame = get_frame(t)
            frame = np.clip((frame - 128) * (1 + 0.2 * intensity) + 128, 0, 255)
            h, w = frame.shape[:2]
            bar_height = int(h * 0.1 * intensity)
            frame[:bar_height] = 0
            frame[-bar_height:] = 0
            return frame.astype(np.uint8)
        
        return clip.fl(cinematic_filter)
    
    def _apply_black_white(self, clip, intensity):
        """Apply black and white effect"""
        return clip.to_grayscale()
    
    def _apply_sepia(self, clip, intensity):
        """Apply sepia effect"""
        def sepia_filter(get_frame, t):
            frame = get_frame(t)
            import numpy as np
            sepia = np.array([[0.393, 0.769, 0.189],
                              [0.349, 0.686, 0.168],
                              [0.272, 0.534, 0.131]])
            frame = frame @ sepia.T
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(sepia_filter)
    
    def _apply_glitch(self, clip, intensity):
        """Apply glitch effect"""
        def glitch_filter(get_frame, t):
            frame = get_frame(t)
            import numpy as np
            if np.random.random() > (1 - intensity * 0.5):
                shift = np.random.randint(-20, 20)
                frame[:, :, 0] = np.roll(frame[:, :, 0], shift=shift, axis=1)
                frame[::20] = 0
            return frame
        
        return clip.fl(glitch_filter)
    
    def _apply_neon(self, clip, intensity):
        """Apply neon effect"""
        def neon_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + intensity), 0, 255)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            kernel = np.ones((5, 5), np.float32) / 25
            blurred = cv2.filter2D(frame, -1, kernel)
            frame = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(neon_filter)
    
    def _apply_thermal(self, clip, intensity):
        """Apply thermal vision effect"""
        def thermal_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
            return cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB)
        
        return clip.fl(thermal_filter)
    
    def _apply_night_vision(self, clip, intensity):
        """Apply night vision effect"""
        def night_vision_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            frame[:, :, 0] = frame[:, :, 0] * 0.3
            frame[:, :, 2] = frame[:, :, 2] * 0.3
            noise = np.random.normal(0, 20 * intensity, frame.shape)
            frame = frame + noise
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(night_vision_filter)
    
    def _apply_dreamy(self, clip, intensity):
        """Apply dreamy effect"""
        def dreamy_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            kernel = np.ones((7, 7), np.float32) / 49
            blurred = cv2.filter2D(frame, -1, kernel)
            frame = cv2.addWeighted(frame, 0.6, blurred, 0.4, 0)
            return frame
        
        return clip.fl(dreamy_filter)
    
    def _apply_dramatic(self, clip, intensity):
        """Apply dramatic effect"""
        return clip.fx(lum_contrast, contrast=0.5 * intensity, brightness=0.1 * intensity)
    
    def _apply_pastel(self, clip, intensity):
        """Apply pastel effect"""
        return clip.fx(colorx, 0.8).fx(lum_contrast, contrast=0.8)
    
    def _apply_vibrant(self, clip, intensity):
        """Apply vibrant effect"""
        return clip.fx(colorx, 1 + 0.3 * intensity)
    
    def _apply_hdr(self, clip, intensity):
        """Apply HDR effect"""
        def hdr_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0 + intensity, tileGridSize=(8,8))
            l = clahe.apply(l)
            lab = cv2.merge((l, a, b))
            frame = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            return frame
        
        return clip.fl(hdr_filter)
    
    def _apply_blur(self, clip, intensity):
        """Apply blur effect"""
        def blur_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            kernel_size = max(3, int(5 * intensity))
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
            frame = cv2.filter2D(frame, -1, kernel)
            return frame
        
        return clip.fl(blur_filter)
    
    def _apply_sharpen(self, clip, intensity):
        """Apply sharpen effect"""
        def sharpen_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            kernel = np.array([[-1, -1, -1],
                               [-1, 9 * intensity, -1],
                               [-1, -1, -1]])
            frame = cv2.filter2D(frame, -1, kernel)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(sharpen_filter)
    
    def _apply_edge(self, clip, intensity):
        """Apply edge detection effect"""
        def edge_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        return clip.fl(edge_filter)
    
    def _apply_emboss(self, clip, intensity):
        """Apply emboss effect"""
        def emboss_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            kernel = np.array([[-2, -1, 0],
                               [-1, 1, 1],
                               [0, 1, 2]])
            frame = cv2.filter2D(frame, -1, kernel)
            return np.clip(frame + 128, 0, 255).astype(np.uint8)
        
        return clip.fl(emboss_filter)
    
    def _apply_cartoon(self, clip, intensity):
        """Apply cartoon effect"""
        def cartoon_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                          cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(frame, 9, 300, 300)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            return cartoon
        
        return clip.fl(cartoon_filter)
    
    def _apply_oil_paint(self, clip, intensity):
        """Apply oil paint effect"""
        def oil_paint_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            import numpy as np
            kernel = np.ones((5, 5), np.float32) / 25
            frame = cv2.filter2D(frame, -1, kernel)
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.2, 0, 255)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(oil_paint_filter)
    
    def _apply_watercolor(self, clip, intensity):
        """Apply watercolor effect"""
        def watercolor_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            frame = cv2.stylization(frame, sigma_s=60, sigma_r=0.07)
            return frame
        
        return clip.fl(watercolor_filter)
    
    def _apply_sketch(self, clip, intensity):
        """Apply sketch effect"""
        def sketch_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            inv = 255 - gray
            blur = cv2.GaussianBlur(inv, (21, 21), 0)
            sketch = cv2.divide(gray, 255 - blur, scale=256)
            return cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)
        
        return clip.fl(sketch_filter)
    
    def _apply_pixelate(self, clip, intensity):
        """Apply pixelate effect"""
        pixel_size = max(2, int(10 * intensity))
        
        def pixelate_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            h, w = frame.shape[:2]
            temp = cv2.resize(frame, (w // pixel_size, h // pixel_size), 
                             interpolation=cv2.INTER_LINEAR)
            frame = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
            return frame
        
        return clip.fl(pixelate_filter)
    
    def _apply_mosaic(self, clip, intensity):
        """Apply mosaic effect"""
        block_size = max(2, int(20 * intensity))
        
        def mosaic_filter(get_frame, t):
            frame = get_frame(t)
            import cv2
            h, w = frame.shape[:2]
            temp = cv2.resize(frame, (w // block_size, h // block_size), 
                             interpolation=cv2.INTER_LINEAR)
            frame = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
            return frame
        
        return clip.fl(mosaic_filter)
    
    def _apply_mirror_horizontal(self, clip, intensity):
        """Apply horizontal mirror effect"""
        def mirror_filter(get_frame, t):
            frame = get_frame(t)
            import numpy as np
            return np.fliplr(frame)
        
        return clip.fl(mirror_filter)
    
    def _apply_mirror_vertical(self, clip, intensity):
        """Apply vertical mirror effect"""
        def mirror_filter(get_frame, t):
            frame = get_frame(t)
            import numpy as np
            return np.flipud(frame)
        
        return clip.fl(mirror_filter)
    
    def _apply_rotate_90(self, clip, intensity):
        """Rotate 90 degrees"""
        return rotate(clip, 90)
    
    def _apply_rotate_180(self, clip, intensity):
        """Rotate 180 degrees"""
        return rotate(clip, 180)
    
    def _apply_rotate_270(self, clip, intensity):
        """Rotate 270 degrees"""
        return rotate(clip, 270)
    
    def _apply_flip(self, clip, intensity):
        """Apply flip effect"""
        return clip.fx(time_mirror)
    
    def _apply_slow_motion_2x(self, clip, intensity):
        """Apply 2x slow motion"""
        return speedx(clip, 0.5)
    
    def _apply_slow_motion_4x(self, clip, intensity):
        """Apply 4x slow motion"""
        return speedx(clip, 0.25)
    
    def _apply_fast_motion_2x(self, clip, intensity):
        """Apply 2x fast motion"""
        return speedx(clip, 2.0)
    
    def _apply_fast_motion_4x(self, clip, intensity):
        """Apply 4x fast motion"""
        return speedx(clip, 4.0)
    
    def _apply_reverse(self, clip, intensity):
        """Apply reverse effect"""
        return time_mirror(clip)
    
    def _apply_time_lapse(self, clip, intensity):
        """Apply time lapse effect"""
        return speedx(clip, 5.0)
    
    # ============================================
    # AUDIO EFFECT METHODS
    # ============================================
    
    def _volume_up(self, clip, intensity):
        """Increase volume"""
        return clip.volumex(1 + intensity)
    
    def _volume_down(self, clip, intensity):
        """Decrease volume"""
        return clip.volumex(1 - intensity * 0.5)
    
    def _audio_fade_in(self, clip, intensity):
        """Audio fade in"""
        return clip.audio_fadein(intensity * 2)
    
    def _audio_fade_out(self, clip, intensity):
        """Audio fade out"""
        return clip.audio_fadeout(intensity * 2)
    
    def _audio_echo(self, clip, intensity):
        """Audio echo effect"""
        return clip.audio_echo(intensity)
    
    def _audio_reverb(self, clip, intensity):
        """Audio reverb effect"""
        return clip.audio_reverb(intensity)
    
    def _audio_bass_boost(self, clip, intensity):
        """Bass boost effect"""
        return clip.audio_bass_boost(intensity)
    
    def _audio_treble_boost(self, clip, intensity):
        """Treble boost effect"""
        return clip.audio_treble_boost(intensity)

# Create global instance
video_editor = VideoEditor()
