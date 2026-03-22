# src/utils/video_utils.py
import subprocess
import json
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

def get_video_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive video information using ffprobe.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Dictionary with complete video information or None if error
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            '-show_programs',
            '-show_chapters',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"ffprobe error: {result.stderr}")
            return None
            
        data = json.loads(result.stdout)
        
        # Parse video information
        video_info = {
            'filename': os.path.basename(file_path),
            'format': data.get('format', {}),
            'streams': data.get('streams', []),
            'programs': data.get('programs', []),
            'chapters': data.get('chapters', []),
            'duration': float(data.get('format', {}).get('duration', 0)),
            'size': int(data.get('format', {}).get('size', 0)),
            'bit_rate': int(data.get('format', {}).get('bit_rate', 0))
        }
        
        # Separate video, audio, and subtitle streams
        video_info['video_streams'] = []
        video_info['audio_streams'] = []
        video_info['subtitle_streams'] = []
        video_info['other_streams'] = []
        
        for stream in data.get('streams', []):
            codec_type = stream.get('codec_type', 'unknown')
            
            if codec_type == 'video':
                video_info['video_streams'].append(stream)
                # Set main video stream properties
                if not video_info.get('video_stream'):
                    video_info['video_stream'] = stream
                    video_info['width'] = int(stream.get('width', 0))
                    video_info['height'] = int(stream.get('height', 0))
                    video_info['codec'] = stream.get('codec_name', 'unknown')
                    video_info['codec_long'] = stream.get('codec_long_name', 'unknown')
                    video_info['fps'] = parse_fps(stream.get('r_frame_rate', '0/1'))
                    video_info['bit_depth'] = stream.get('bits_per_raw_sample', 8)
                    video_info['pixel_format'] = stream.get('pix_fmt', 'unknown')
                    video_info['color_space'] = stream.get('color_space', 'unknown')
                    video_info['color_range'] = stream.get('color_range', 'unknown')
                    video_info['has_b_frames'] = stream.get('has_b_frames', 0)
                    video_info['level'] = stream.get('level', 0)
                    video_info['profile'] = stream.get('profile', 'unknown')
                    video_info['aspect_ratio'] = stream.get('display_aspect_ratio', 'unknown')
                    
            elif codec_type == 'audio':
                video_info['audio_streams'].append(stream)
                # Set main audio stream properties
                if not video_info.get('audio_stream'):
                    video_info['audio_stream'] = stream
                    video_info['audio_codec'] = stream.get('codec_name', 'unknown')
                    video_info['audio_channels'] = stream.get('channels', 0)
                    video_info['audio_sample_rate'] = int(stream.get('sample_rate', 0))
                    video_info['audio_bit_rate'] = int(stream.get('bit_rate', 0))
                    
            elif codec_type == 'subtitle':
                video_info['subtitle_streams'].append(stream)
            else:
                video_info['other_streams'].append(stream)
        
        # Add metadata
        video_info['metadata'] = data.get('format', {}).get('tags', {})
        
        return video_info
        
    except subprocess.TimeoutExpired:
        print("ffprobe timeout - video info retrieval took too long")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing ffprobe output: {e}")
        return None
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

def parse_fps(fps_string: str) -> float:
    """
    Parse FPS string like '30000/1001' to float.
    
    Args:
        fps_string: FPS string from ffprobe
        
    Returns:
        Float FPS value
    """
    try:
        if not fps_string or fps_string == '0/0':
            return 0.0
            
        if '/' in fps_string:
            num, den = fps_string.split('/')
            if float(den) != 0:
                return float(num) / float(den)
        return float(fps_string)
    except (ValueError, ZeroDivisionError):
        return 0.0

def get_video_duration(file_path: str) -> float:
    """
    Get video duration in seconds.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Duration in seconds
    """
    info = get_video_info(file_path)
    return info.get('duration', 0) if info else 0

def get_video_resolution(file_path: str) -> Tuple[int, int]:
    """
    Get video resolution (width, height).
    
    Args:
        file_path: Path to video file
        
    Returns:
        Tuple of (width, height)
    """
    info = get_video_info(file_path)
    if info:
        return (info.get('width', 0), info.get('height', 0))
    return (0, 0)

def get_video_codec(file_path: str) -> str:
    """
    Get video codec name.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Codec name or 'unknown'
    """
    info = get_video_info(file_path)
    return info.get('codec', 'unknown') if info else 'unknown'

def get_video_bitrate(file_path: str) -> int:
    """
    Get video bitrate in bits per second.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Bitrate in bps
    """
    info = get_video_info(file_path)
    return info.get('bit_rate', 0) if info else 0

def get_video_fps(file_path: str) -> float:
    """
    Get video frames per second.
    
    Args:
        file_path: Path to video file
        
    Returns:
        FPS value
    """
    info = get_video_info(file_path)
    return info.get('fps', 0) if info else 0

def get_video_frame_count(file_path: str) -> int:
    """
    Get total number of frames in video.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Number of frames or 0 if cannot determine
    """
    info = get_video_info(file_path)
    if info and info.get('video_stream'):
        # Try to get frame count from stream
        stream = info['video_stream']
        frame_count = stream.get('nb_frames')
        
        if frame_count:
            return int(frame_count)
        
        # Calculate from duration and fps
        duration = info.get('duration', 0)
        fps = info.get('fps', 0)
        if duration > 0 and fps > 0:
            return int(duration * fps)
    
    return 0

def is_video_file(file_path: str) -> bool:
    """
    Check if a file is a valid video file.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file is a valid video
    """
    if not os.path.exists(file_path):
        return False
    
    # Check file extension first (quick check)
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg'}
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext not in video_extensions:
        return False
    
    # Verify with ffprobe
    info = get_video_info(file_path)
    return info is not None and len(info.get('video_streams', [])) > 0

def get_video_thumbnail(file_path: str, output_path: str, timestamp: str = '00:00:01') -> bool:
    """
    Extract a thumbnail from video at specified timestamp.
    
    Args:
        file_path: Source video file
        output_path: Output thumbnail image path
        timestamp: Timestamp to capture (format: HH:MM:SS or seconds)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-ss', timestamp,
            '-vframes', '1',
            '-vf', 'scale=320:-1',  # Scale to width 320, maintain aspect ratio
            '-y',  # Overwrite output
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error extracting thumbnail: {e}")
        return False

def get_video_metadata_quick(file_path: str) -> Dict[str, Any]:
    """
    Get basic video metadata quickly without full ffprobe.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Dictionary with basic metadata
    """
    if not os.path.exists(file_path):
        return {'error': 'File not found'}
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,duration,codec_name',
            '-show_entries', 'format=duration,size,bit_rate',
            '-of', 'default=noprint_wrappers=1:nokey=0',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {'error': 'Failed to probe video'}
        
        # Parse output
        metadata = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                metadata[key] = value
        
        # Parse FPS
        if 'r_frame_rate' in metadata:
            metadata['fps'] = parse_fps(metadata['r_frame_rate'])
            del metadata['r_frame_rate']
        
        # Convert numeric values
        numeric_keys = ['width', 'height', 'duration', 'size', 'bit_rate']
        for key in numeric_keys:
            if key in metadata:
                try:
                    metadata[key] = float(metadata[key]) if '.' in metadata[key] else int(metadata[key])
                except ValueError:
                    pass
        
        return metadata
        
    except subprocess.TimeoutExpired:
        return {'error': 'Timeout'}
    except Exception as e:
        return {'error': str(e)}

def get_video_stream_info(file_path: str, stream_index: int = 0) -> Optional[Dict[str, Any]]:
    """
    Get specific video stream information.
    
    Args:
        file_path: Path to video file
        stream_index: Index of video stream (default: 0)
        
    Returns:
        Dictionary with stream information or None
    """
    info = get_video_info(file_path)
    if info and stream_index < len(info.get('video_streams', [])):
        return info['video_streams'][stream_index]
    return None

def get_all_streams_info(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get information about all streams in the video.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Dictionary with lists of video, audio, subtitle streams
    """
    info = get_video_info(file_path)
    if info:
        return {
            'video': info.get('video_streams', []),
            'audio': info.get('audio_streams', []),
            'subtitle': info.get('subtitle_streams', []),
            'other': info.get('other_streams', [])
        }
    return {'video': [], 'audio': [], 'subtitle': [], 'other': []}

def get_video_aspect_ratio(file_path: str) -> str:
    """
    Get video aspect ratio.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Aspect ratio string (e.g., '16:9') or 'unknown'
    """
    info = get_video_info(file_path)
    if info and info.get('video_stream'):
        width = info.get('width', 0)
        height = info.get('height', 0)
        
        if width > 0 and height > 0:
            # Calculate simplified ratio
            from math import gcd
            divisor = gcd(width, height)
            return f"{width//divisor}:{height//divisor}"
    
    return 'unknown'

def validate_video_file(file_path: str, check_corruption: bool = False) -> Dict[str, Any]:
    """
    Validate video file and optionally check for corruption.
    
    Args:
        file_path: Path to video file
        check_corruption: If True, perform deeper corruption check
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': False,
        'exists': False,
        'readable': False,
        'has_video_stream': False,
        'has_audio_stream': False,
        'errors': [],
        'warnings': []
    }
    
    # Check if file exists
    if not os.path.exists(file_path):
        result['errors'].append('File does not exist')
        return result
    
    result['exists'] = True
    
    # Check if file is readable
    if not os.access(file_path, os.R_OK):
        result['errors'].append('File is not readable')
        return result
    
    result['readable'] = True
    
    # Get video info
    info = get_video_info(file_path)
    
    if not info:
        result['errors'].append('Cannot probe video file')
        return result
    
    # Check streams
    if len(info.get('video_streams', [])) > 0:
        result['has_video_stream'] = True
    else:
        result['errors'].append('No video stream found')
    
    if len(info.get('audio_streams', [])) > 0:
        result['has_audio_stream'] = True
    
    # Check duration
    if info.get('duration', 0) <= 0:
        result['warnings'].append('Video duration is zero or unknown')
    
    # Check file size
    if info.get('size', 0) <= 0:
        result['warnings'].append('File size is zero')
    
    # Optional corruption check
    if check_corruption and result['has_video_stream']:
        try:
            # Try to decode first few frames
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-frames:v', '5',
                '-f', 'null',
                '-'
            ]
            result_check = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result_check.returncode != 0:
                result['errors'].append('Possible file corruption detected')
            else:
                result['valid'] = True
        except Exception as e:
            result['errors'].append(f'Corruption check failed: {str(e)}')
    else:
        result['valid'] = result['has_video_stream']
    
    return result

# Alias for backward compatibility
eval_fps = parse_fps
