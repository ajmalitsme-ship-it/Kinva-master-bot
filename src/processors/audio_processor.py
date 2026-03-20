"""
Audio Processor - Handles all audio processing operations
Author: @kinva_master
"""

import os
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, low_pass_filter, high_pass_filter
    from pydub.generators import Sine, Square, Sawtooth
    import librosa
    import soundfile as sf
except ImportError as e:
    AudioSegment = None
    logger = logging.getLogger(__name__)
    logger.warning(f"Audio processing libraries not installed: {e}")

from ..config import Config
from ..utils import get_temp_file, cleanup_file, format_file_size

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Main audio processor class"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR) / 'audio'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Available audio effects
        self.available_effects = {
            'normalize': self.normalize_audio,
            'fade_in': self.fade_in,
            'fade_out': self.fade_out,
            'reverse': self.reverse_audio,
            'speed_up': self.speed_up,
            'slow_down': self.slow_down,
            'volume_up': self.volume_up,
            'volume_down': self.volume_down,
            'bass_boost': self.bass_boost,
            'treble_boost': self.treble_boost,
            'echo': self.add_echo,
            'reverb': self.add_reverb,
            'chorus': self.add_chorus,
            'pitch_up': self.pitch_up,
            'pitch_down': self.pitch_down,
            'noise_reduction': self.noise_reduction,
            'silence_remove': self.remove_silence,
        }
        
        # Audio formats
        self.supported_formats = ['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a']
    
    def process(self, input_path: str, effects: List[str] = None,
                adjustments: Dict = None, output_format: str = 'mp3',
                bitrate: str = '192k') -> str:
        """Process audio with effects"""
        
        effects = effects or []
        adjustments = adjustments or {}
        
        if AudioSegment is None:
            raise ImportError("Audio processing libraries not installed")
        
        try:
            # Load audio
            audio = AudioSegment.from_file(input_path)
            
            # Apply adjustments
            audio = self._apply_adjustments(audio, adjustments)
            
            # Apply effects
            for effect in effects:
                if effect in self.available_effects:
                    try:
                        audio = self.available_effects[effect](audio)
                    except Exception as e:
                        logger.error(f"Failed to apply effect {effect}: {e}")
            
            # Export audio
            output_filename = f"processed_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            audio.export(output_path, format=output_format, bitrate=bitrate)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            raise
    
    def _apply_adjustments(self, audio: AudioSegment, adjustments: Dict) -> AudioSegment:
        """Apply volume and speed adjustments"""
        
        if 'volume' in adjustments:
            audio = audio + adjustments['volume']  # Volume in dB
        
        if 'speed' in adjustments:
            audio = audio.speedup(playback_speed=adjustments['speed'])
        
        if 'pan' in adjustments:
            audio = audio.pan(adjustments['pan'])
        
        return audio
    
    def extract_from_video(self, video_path: str, output_format: str = 'mp3') -> str:
        """Extract audio from video file"""
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(video_path)
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
    
    def merge_audio(self, audio_paths: List[str], output_format: str = 'mp3') -> str:
        """Merge multiple audio files"""
        try:
            combined = AudioSegment.empty()
            
            for path in audio_paths:
                audio = AudioSegment.from_file(path)
                combined += audio
            
            output_filename = f"merged_audio_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            combined.export(output_path, format=output_format)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio merge error: {e}")
            raise
    
    def trim_audio(self, audio_path: str, start: float, end: float, 
                   output_format: str = 'mp3') -> str:
        """Trim audio file"""
        try:
            audio = AudioSegment.from_file(audio_path)
            trimmed = audio[start * 1000:end * 1000]  # Convert to milliseconds
            
            output_filename = f"trimmed_audio_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            trimmed.export(output_path, format=output_format)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio trim error: {e}")
            raise
    
    def convert_format(self, input_path: str, output_format: str = 'mp3',
                       bitrate: str = '192k') -> str:
        """Convert audio format"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            output_filename = f"converted_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            audio.export(output_path, format=output_format, bitrate=bitrate)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            raise
    
    def change_speed(self, input_path: str, speed: float = 1.0,
                     output_format: str = 'mp3') -> str:
        """Change audio speed"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            if speed != 1.0:
                audio = audio.speedup(playback_speed=speed)
            
            output_filename = f"speed_{speed}x_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            audio.export(output_path, format=output_format)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Speed change error: {e}")
            raise
    
    def change_volume(self, input_path: str, volume_db: float = 0,
                      output_format: str = 'mp3') -> str:
        """Change audio volume"""
        try:
            audio = AudioSegment.from_file(input_path)
            audio = audio + volume_db  # Volume in dB
            
            output_filename = f"volume_{volume_db}db_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            audio.export(output_path, format=output_format)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Volume change error: {e}")
            raise
    
    def get_audio_info(self, input_path: str) -> Dict:
        """Get audio file information"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            return {
                'duration': len(audio) / 1000,  # seconds
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'size_bytes': len(audio.raw_data),
                'size_mb': len(audio.raw_data) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Get audio info error: {e}")
            return {}
    
    # ============================================
    # EFFECT IMPLEMENTATIONS
    # ============================================
    
    def normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """Normalize audio volume"""
        return normalize(audio)
    
    def fade_in(self, audio: AudioSegment, duration: float = 3.0) -> AudioSegment:
        """Apply fade in effect"""
        return audio.fade_in(duration * 1000)
    
    def fade_out(self, audio: AudioSegment, duration: float = 3.0) -> AudioSegment:
        """Apply fade out effect"""
        return audio.fade_out(duration * 1000)
    
    def reverse_audio(self, audio: AudioSegment) -> AudioSegment:
        """Reverse audio"""
        return audio.reverse()
    
    def speed_up(self, audio: AudioSegment, factor: float = 1.5) -> AudioSegment:
        """Speed up audio"""
        return audio.speedup(playback_speed=factor)
    
    def slow_down(self, audio: AudioSegment, factor: float = 0.75) -> AudioSegment:
        """Slow down audio"""
        return audio.speedup(playback_speed=factor)
    
    def volume_up(self, audio: AudioSegment, db: float = 10) -> AudioSegment:
        """Increase volume"""
        return audio + db
    
    def volume_down(self, audio: AudioSegment, db: float = -10) -> AudioSegment:
        """Decrease volume"""
        return audio + db
    
    def bass_boost(self, audio: AudioSegment, gain: int = 10) -> AudioSegment:
        """Boost bass frequencies"""
        return low_pass_filter(audio, 200).apply_gain(gain) + high_pass_filter(audio, 200)
    
    def treble_boost(self, audio: AudioSegment, gain: int = 10) -> AudioSegment:
        """Boost treble frequencies"""
        return high_pass_filter(audio, 2000).apply_gain(gain) + low_pass_filter(audio, 2000)
    
    def add_echo(self, audio: AudioSegment, delay: float = 0.5, 
                 decay: float = 0.5) -> AudioSegment:
        """Add echo effect"""
        # Create echo by overlaying delayed copy
        echo = audio - (1 - decay) * 20  # Reduce volume
        echo = echo * decay
        echo = echo.shift(delay * 1000)
        
        return audio.overlay(echo)
    
    def add_reverb(self, audio: AudioSegment, room_size: float = 0.5) -> AudioSegment:
        """Add reverb effect (simplified)"""
        # Simple reverb simulation
        reverb = audio - 10  # Reduce volume
        reverb = reverb.low_pass_filter(3000)
        
        for i in range(1, 4):
            reverb = reverb.overlay(
                audio.shift(i * 100).low_pass_filter(3000).apply_gain(-i * 3)
            )
        
        return reverb
    
    def add_chorus(self, audio: AudioSegment, rate: float = 0.5) -> AudioSegment:
        """Add chorus effect"""
        chorus = audio
        for i in range(1, 3):
            chorus = chorus.overlay(
                audio.shift(i * 30).apply_gain(-i * 2)
            )
        
        return chorus
    
    def pitch_up(self, audio: AudioSegment, semitones: int = 2) -> AudioSegment:
        """Increase pitch"""
        # Change pitch by changing frame rate
        new_frame_rate = int(audio.frame_rate * (2 ** (semitones / 12)))
        return audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
    
    def pitch_down(self, audio: AudioSegment, semitones: int = 2) -> AudioSegment:
        """Decrease pitch"""
        new_frame_rate = int(audio.frame_rate * (2 ** (-semitones / 12)))
        return audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
    
    def noise_reduction(self, audio: AudioSegment, threshold: int = 10) -> AudioSegment:
        """Reduce background noise"""
        # Simple noise gate
        return audio.apply_gain_stereo(-threshold, -threshold)
    
    def remove_silence(self, audio: AudioSegment, silence_thresh: int = -50,
                       chunk_size: int = 10) -> AudioSegment:
        """Remove silence from audio"""
        chunks = []
        for chunk in audio[::chunk_size * 1000]:
            if chunk.dBFS > silence_thresh:
                chunks.append(chunk)
        
        return sum(chunks) if chunks else audio
    
    def add_background_music(self, main_audio_path: str, bg_audio_path: str,
                            bg_volume: float = 0.3, output_format: str = 'mp3') -> str:
        """Add background music to audio"""
        try:
            main = AudioSegment.from_file(main_audio_path)
            bg = AudioSegment.from_file(bg_audio_path)
            
            # Loop background if shorter
            if len(bg) < len(main):
                bg = bg * (len(main) // len(bg) + 1)
            
            # Trim background to match main length
            bg = bg[:len(main)]
            
            # Reduce background volume
            bg = bg - (1 - bg_volume) * 20
            
            # Mix
            mixed = main.overlay(bg)
            
            output_filename = f"with_bg_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            mixed.export(output_path, format=output_format)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Add background music error: {e}")
            raise
    
    def extract_voice(self, input_path: str, output_format: str = 'mp3') -> str:
        """Extract voice from audio (basic implementation)"""
        # This is a placeholder - for proper voice extraction, use ML models
        try:
            # Load with librosa for more advanced processing
            y, sr = librosa.load(input_path, sr=22050)
            
            # Simple high-pass filter to remove low frequencies (music)
            from scipy import signal
            b, a = signal.butter(4, 300, 'hp', fs=sr)
            voice = signal.filtfilt(b, a, y)
            
            output_filename = f"voice_{int(datetime.now().timestamp())}.{output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            sf.write(output_path, voice, sr)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Voice extraction error: {e}")
            raise
    
    def create_waveform(self, input_path: str, width: int = 800, 
                        height: int = 200) -> str:
        """Create waveform image from audio"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            y, sr = librosa.load(input_path, sr=22050)
            
            plt.figure(figsize=(width/100, height/100), dpi=100)
            plt.plot(y, color='#667eea', alpha=0.8)
            plt.axis('off')
            plt.margins(0)
            
            output_filename = f"waveform_{int(datetime.now().timestamp())}.png"
            output_path = os.path.join(self.output_dir, output_filename)
            
            plt.savefig(output_path, bbox_inches='tight', pad_inches=0, 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Waveform creation error: {e}")
            raise
    
    def create_spectrogram(self, input_path: str, width: int = 800, 
                           height: int = 400) -> str:
        """Create spectrogram image from audio"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            y, sr = librosa.load(input_path, sr=22050)
            
            # Compute spectrogram
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
            
            plt.figure(figsize=(width/100, height/100), dpi=100)
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
            plt.colorbar(format='%+2.0f dB')
            plt.axis('off')
            
            output_filename = f"spectrogram_{int(datetime.now().timestamp())}.png"
            output_path = os.path.join(self.output_dir, output_filename)
            
            plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
            plt.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Spectrogram creation error: {e}")
            raise

# Create global instance
audio_processor = AudioProcessor()
