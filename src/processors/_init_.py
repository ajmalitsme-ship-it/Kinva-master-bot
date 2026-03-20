"""
Processors Package - Video, Image, Audio Processing Modules
Author: @kinva_master
"""

from .video_processor import VideoProcessor, video_processor
from .image_processor import ImageProcessor, image_processor
from .audio_processor import AudioProcessor, audio_processor
from .watermark import Watermark, watermark
from .compression import CompressionProcessor, compression_processor
from .effects import EffectsProcessor, effects_processor
from .filters import FiltersProcessor, filters_processor

__all__ = [
    'VideoProcessor',
    'video_processor',
    'ImageProcessor',
    'image_processor',
    'AudioProcessor',
    'audio_processor',
    'Watermark',
    'watermark',
    'CompressionProcessor',
    'compression_processor',
    'EffectsProcessor',
    'effects_processor',
    'FiltersProcessor',
    'filters_processor'
]
