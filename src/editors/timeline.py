"""
Timeline Editor - Video timeline management with professional features
Author: @kinva_master
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import math

from ..utils import generate_uuid

logger = logging.getLogger(__name__)

class Timeline:
    """Professional video timeline management"""
    
    def __init__(self):
        self.tracks = []
        self.duration = 0
        self.current_time = 0
        self.playback_rate = 1.0
        self.zoom_level = 1.0
        self.frame_rate = 30
        self.timecode_format = 'hh:mm:ss:ff'
        
    def create_timeline(self, tracks: int = 3, frame_rate: int = 30) -> Dict:
        """Create new timeline with multiple tracks"""
        timeline = {
            'id': generate_uuid(),
            'tracks': [],
            'duration': 0,
            'current_time': 0,
            'playback_rate': 1.0,
            'zoom_level': 1.0,
            'frame_rate': frame_rate,
            'timecode_format': 'hh:mm:ss:ff',
            'markers': [],
            'regions': [],
            'selected_clips': [],
            'settings': {
                'snap_enabled': True,
                'snap_distance': 10,
                'ripple_edit': False,
                'auto_scroll': True,
                'waveform_visible': True,
                'thumbnail_visible': True
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Create tracks
        track_types = ['video', 'video', 'audio', 'audio']
        for i in range(tracks):
            track_type = track_types[i] if i < len(track_types) else 'video'
            timeline['tracks'].append({
                'id': generate_uuid(),
                'index': i,
                'name': f'Track {i + 1}',
                'type': track_type,
                'clips': [],
                'muted': False,
                'solo': False,
                'locked': False,
                'color': self._get_track_color(i),
                'height': 80 if track_type == 'video' else 60,
                'expanded': True,
                'created_at': datetime.now().isoformat()
            })
        
        return timeline
    
    def _get_track_color(self, index: int) -> str:
        """Get color for track"""
        colors = ['#667eea', '#48bb78', '#f56565', '#ed8936', '#9f7aea', '#fbbf24']
        return colors[index % len(colors)]
    
    def add_clip(self, timeline: Dict, track_index: int, clip_data: Dict) -> Dict:
        """Add clip to timeline at specific track"""
        if track_index >= len(timeline['tracks']):
            raise ValueError(f"Track {track_index} does not exist")
        
        track = timeline['tracks'][track_index]
        
        # Validate clip position
        start_time = clip_data.get('start_time', 0)
        end_time = clip_data.get('end_time', start_time + clip_data.get('duration', 1))
        duration = end_time - start_time
        
        # Check for overlap if snap is enabled
        if timeline['settings']['snap_enabled']:
            for existing_clip in track['clips']:
                if self._clips_overlap(existing_clip, start_time, end_time):
                    # Snap to end of overlapping clip
                    start_time = existing_clip['end_time']
                    end_time = start_time + duration
        
        clip = {
            'id': generate_uuid(),
            'name': clip_data.get('name', f'Clip {len(track["clips"]) + 1}'),
            'source': clip_data.get('source', ''),
            'type': clip_data.get('type', track['type']),
            'track': track_index,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'source_start': clip_data.get('source_start', 0),
            'source_end': clip_data.get('source_end', duration),
            'source_duration': duration,
            'speed': clip_data.get('speed', 1.0),
            'volume': clip_data.get('volume', 1.0),
            'effects': clip_data.get('effects', []),
            'filters': clip_data.get('filters', []),
            'transitions': {
                'in': clip_data.get('transition_in', None),
                'out': clip_data.get('transition_out', None)
            },
            'color': clip_data.get('color', '#667eea'),
            'selected': False,
            'locked': False,
            'muted': False,
            'info': clip_data.get('info', {}),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Add to track
        track['clips'].append(clip)
        track['clips'].sort(key=lambda c: c['start_time'])
        
        # Update timeline duration
        timeline['duration'] = max(timeline['duration'], end_time)
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def remove_clip(self, timeline: Dict, clip_id: str) -> Dict:
        """Remove clip from timeline"""
        for track in timeline['tracks']:
            track['clips'] = [c for c in track['clips'] if c['id'] != clip_id]
        
        timeline['updated_at'] = datetime.now().isoformat()
        
        # Recalculate duration
        max_end = 0
        for track in timeline['tracks']:
            for clip in track['clips']:
                max_end = max(max_end, clip['end_time'])
        timeline['duration'] = max_end
        
        return timeline
    
    def move_clip(self, timeline: Dict, clip_id: str, new_start_time: float,
                  new_track: int = None) -> Dict:
        """Move clip to new position or track"""
        clip = None
        old_track = None
        old_start = None
        
        # Find clip
        for i, track in enumerate(timeline['tracks']):
            for c in track['clips']:
                if c['id'] == clip_id:
                    clip = c
                    old_track = i
                    old_start = c['start_time']
                    break
            if clip:
                break
        
        if not clip:
            return timeline
        
        # Remove from old track
        timeline['tracks'][old_track]['clips'] = [
            c for c in timeline['tracks'][old_track]['clips'] if c['id'] != clip_id
        ]
        
        # Update clip position
        duration = clip['duration']
        clip['start_time'] = new_start_time
        clip['end_time'] = new_start_time + duration
        clip['updated_at'] = datetime.now().isoformat()
        
        # Add to new track
        if new_track is not None:
            clip['track'] = new_track
            timeline['tracks'][new_track]['clips'].append(clip)
            timeline['tracks'][new_track]['clips'].sort(key=lambda c: c['start_time'])
        else:
            timeline['tracks'][old_track]['clips'].append(clip)
            timeline['tracks'][old_track]['clips'].sort(key=lambda c: c['start_time'])
        
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def trim_clip(self, timeline: Dict, clip_id: str, new_start: float, new_end: float) -> Dict:
        """Trim clip edges"""
        for track in timeline['tracks']:
            for clip in track['clips']:
                if clip['id'] == clip_id:
                    old_duration = clip['duration']
                    clip['start_time'] = new_start
                    clip['end_time'] = new_end
                    clip['duration'] = new_end - new_start
                    
                    # Adjust source times proportionally
                    ratio = clip['duration'] / old_duration
                    source_duration = clip['source_end'] - clip['source_start']
                    clip['source_end'] = clip['source_start'] + source_duration * ratio
                    clip['updated_at'] = datetime.now().isoformat()
                    break
        
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def split_clip(self, timeline: Dict, clip_id: str, split_time: float) -> Dict:
        """Split clip at specified time"""
        for track in timeline['tracks']:
            for clip in track['clips']:
                if clip['id'] == clip_id:
                    if split_time <= clip['start_time'] or split_time >= clip['end_time']:
                        continue
                    
                    # Calculate split position in source
                    source_split = clip['source_start'] + (split_time - clip['start_time']) * \
                                  (clip['source_duration'] / clip['duration'])
                    
                    # Create first clip
                    clip1 = clip.copy()
                    clip1['id'] = generate_uuid()
                    clip1['start_time'] = clip['start_time']
                    clip1['end_time'] = split_time
                    clip1['duration'] = split_time - clip['start_time']
                    clip1['source_end'] = source_split
                    clip1['source_duration'] = source_split - clip['source_start']
                    
                    # Create second clip
                    clip2 = clip.copy()
                    clip2['id'] = generate_uuid()
                    clip2['start_time'] = split_time
                    clip2['end_time'] = clip['end_time']
                    clip2['duration'] = clip['end_time'] - split_time
                    clip2['source_start'] = source_split
                    clip2['source_duration'] = clip['source_end'] - source_split
                    
                    # Replace original clip
                    index = track['clips'].index(clip)
                    track['clips'].pop(index)
                    track['clips'].insert(index, clip1)
                    track['clips'].insert(index + 1, clip2)
                    
                    timeline['updated_at'] = datetime.now().isoformat()
                    break
        
        return timeline
    
    def add_marker(self, timeline: Dict, time: float, label: str, 
                   color: str = '#ff0000') -> Dict:
        """Add marker at specific time"""
        marker = {
            'id': generate_uuid(),
            'time': time,
            'label': label,
            'color': color,
            'created_at': datetime.now().isoformat()
        }
        
        timeline['markers'].append(marker)
        timeline['markers'].sort(key=lambda m: m['time'])
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def remove_marker(self, timeline: Dict, marker_id: str) -> Dict:
        """Remove marker"""
        timeline['markers'] = [m for m in timeline['markers'] if m['id'] != marker_id]
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def add_region(self, timeline: Dict, start: float, end: float, 
                   label: str, color: str = '#48bb78') -> Dict:
        """Add region/range"""
        region = {
            'id': generate_uuid(),
            'start': start,
            'end': end,
            'label': label,
            'color': color,
            'created_at': datetime.now().isoformat()
        }
        
        timeline['regions'].append(region)
        timeline['regions'].sort(key=lambda r: r['start'])
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def remove_region(self, timeline: Dict, region_id: str) -> Dict:
        """Remove region"""
        timeline['regions'] = [r for r in timeline['regions'] if r['id'] != region_id]
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def set_playback_rate(self, timeline: Dict, rate: float) -> Dict:
        """Set timeline playback rate"""
        timeline['playback_rate'] = max(0.1, min(4.0, rate))
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def set_zoom(self, timeline: Dict, zoom: float, center_time: float = None) -> Dict:
        """Set timeline zoom level"""
        old_zoom = timeline['zoom_level']
        timeline['zoom_level'] = max(0.1, min(10.0, zoom))
        
        # Adjust current time to keep center
        if center_time is not None:
            timeline['current_time'] = center_time
        
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def zoom_to_fit(self, timeline: Dict) -> Dict:
        """Zoom to fit entire timeline"""
        if timeline['duration'] > 0:
            timeline['zoom_level'] = 1.0
            timeline['current_time'] = timeline['duration'] / 2
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def zoom_to_selection(self, timeline: Dict) -> Dict:
        """Zoom to selected clips"""
        selected_clips = self.get_selected_clips(timeline)
        if not selected_clips:
            return timeline
        
        min_start = min(c['start_time'] for c in selected_clips)
        max_end = max(c['end_time'] for c in selected_clips)
        duration = max_end - min_start
        
        if duration > 0:
            timeline['zoom_level'] = timeline['duration'] / duration
            timeline['current_time'] = min_start + duration / 2
        
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def select_clip(self, timeline: Dict, clip_id: str, clear_selection: bool = True) -> Dict:
        """Select a clip"""
        if clear_selection:
            for track in timeline['tracks']:
                for clip in track['clips']:
                    clip['selected'] = False
        
        for track in timeline['tracks']:
            for clip in track['clips']:
                if clip['id'] == clip_id:
                    clip['selected'] = True
                    if clip_id not in timeline['selected_clips']:
                        timeline['selected_clips'].append(clip_id)
                    break
        
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def select_range(self, timeline: Dict, start_time: float, end_time: float) -> Dict:
        """Select clips in time range"""
        for track in timeline['tracks']:
            for clip in track['clips']:
                if self._clips_overlap(clip, start_time, end_time):
                    clip['selected'] = True
                    if clip['id'] not in timeline['selected_clips']:
                        timeline['selected_clips'].append(clip['id'])
                else:
                    clip['selected'] = False
        
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def clear_selection(self, timeline: Dict) -> Dict:
        """Clear all selections"""
        for track in timeline['tracks']:
            for clip in track['clips']:
                clip['selected'] = False
        timeline['selected_clips'] = []
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def get_selected_clips(self, timeline: Dict) -> List[Dict]:
        """Get all selected clips"""
        selected = []
        for track in timeline['tracks']:
            for clip in track['clips']:
                if clip.get('selected', False):
                    selected.append(clip)
        return selected
    
    def ripple_delete(self, timeline: Dict, clip_id: str) -> Dict:
        """Delete clip and shift later clips"""
        clip_to_delete = None
        track_index = None
        clip_index = None
        
        # Find clip
        for i, track in enumerate(timeline['tracks']):
            for j, clip in enumerate(track['clips']):
                if clip['id'] == clip_id:
                    clip_to_delete = clip
                    track_index = i
                    clip_index = j
                    break
            if clip_to_delete:
                break
        
        if not clip_to_delete:
            return timeline
        
        # Remove clip
        duration = clip_to_delete['duration']
        timeline['tracks'][track_index]['clips'].pop(clip_index)
        
        # Shift later clips on same track
        for clip in timeline['tracks'][track_index]['clips']:
            if clip['start_time'] > clip_to_delete['start_time']:
                clip['start_time'] -= duration
                clip['end_time'] -= duration
        
        # Shift clips on other tracks that start after
        for i, track in enumerate(timeline['tracks']):
            if i != track_index:
                for clip in track['clips']:
                    if clip['start_time'] > clip_to_delete['start_time']:
                        clip['start_time'] -= duration
                        clip['end_time'] -= duration
        
        # Update timeline duration
        timeline['duration'] -= duration
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def ripple_insert(self, timeline: Dict, clip_data: Dict, insert_time: float) -> Dict:
        """Insert clip and shift later clips"""
        duration = clip_data.get('duration', 1)
        
        # Shift clips after insert time
        for track in timeline['tracks']:
            for clip in track['clips']:
                if clip['start_time'] >= insert_time:
                    clip['start_time'] += duration
                    clip['end_time'] += duration
        
        # Add new clip
        clip_data['start_time'] = insert_time
        clip_data['end_time'] = insert_time + duration
        self.add_clip(timeline, 0, clip_data)
        
        # Update timeline duration
        timeline['duration'] += duration
        timeline['updated_at'] = datetime.now().isoformat()
        
        return timeline
    
    def get_clip_at_time(self, timeline: Dict, time: float) -> Optional[Dict]:
        """Get clip at specific time"""
        for track in timeline['tracks']:
            for clip in track['clips']:
                if clip['start_time'] <= time <= clip['end_time']:
                    return clip
        return None
    
    def get_clips_in_range(self, timeline: Dict, start: float, end: float) -> List[Dict]:
        """Get clips within time range"""
        clips = []
        for track in timeline['tracks']:
            for clip in track['clips']:
                if self._clips_overlap(clip, start, end):
                    clips.append(clip)
        return clips
    
    def get_timeline_range(self, timeline: Dict) -> Tuple[float, float]:
        """Get visible timeline range based on zoom and position"""
        visible_duration = timeline['duration'] / timeline['zoom_level']
        start = max(0, timeline['current_time'] - visible_duration / 2)
        end = min(timeline['duration'], start + visible_duration)
        return start, end
    
    def timecode_to_seconds(self, timecode: str, frame_rate: int = 30) -> float:
        """Convert timecode to seconds"""
        parts = timecode.split(':')
        if len(parts) == 4:  # hh:mm:ss:ff
            h, m, s, f = map(int, parts)
            return h * 3600 + m * 60 + s + f / frame_rate
        elif len(parts) == 3:  # hh:mm:ss
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:  # mm:ss
            m, s = map(int, parts)
            return m * 60 + s
        else:
            return float(timecode)
    
    def seconds_to_timecode(self, seconds: float, frame_rate: int = 30) -> str:
        """Convert seconds to timecode"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds - int(seconds)) * frame_rate)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}:{frames:02d}"
    
    def render_preview(self, timeline: Dict, width: int = 800, height: int = 400) -> str:
        """Render timeline preview image"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Draw timeline background
            draw.rectangle([0, 0, width, height], fill='#1a1a2e')
            
            # Draw ruler
            ruler_height = 40
            draw.rectangle([0, 0, width, ruler_height], fill='#2d3748')
            
            # Draw time markers
            visible_start, visible_end = self.get_timeline_range(timeline)
            visible_duration = visible_end - visible_start
            
            # Calculate marker interval
            interval = self._get_marker_interval(visible_duration)
            if interval > 0:
                start_marker = math.floor(visible_start / interval) * interval
                for t in range(int(start_marker), int(visible_end), int(interval)):
                    x = ((t - visible_start) / visible_duration) * width
                    if 0 <= x <= width:
                        draw.line([x, ruler_height - 10, x, ruler_height], fill='#718096')
                        timecode = self.seconds_to_timecode(t, timeline['frame_rate'])
                        draw.text((x - 15, ruler_height - 30), timecode, fill='#a0aec0')
            
            # Draw tracks
            track_height = (height - ruler_height) // len(timeline['tracks'])
            y_offset = ruler_height
            
            for i, track in enumerate(timeline['tracks']):
                y1 = y_offset + i * track_height
                y2 = y1 + track_height
                
                # Track background
                draw.rectangle([0, y1, width, y2], fill='#2d3748', outline='#4a5568')
                
                # Track label
                draw.text((5, y1 + 5), track['name'], fill='#a0aec0')
                
                # Draw clips
                for clip in track['clips']:
                    if clip['end_time'] < visible_start or clip['start_time'] > visible_end:
                        continue
                    
                    start_x = ((clip['start_time'] - visible_start) / visible_duration) * width
                    end_x = ((clip['end_time'] - visible_start) / visible_duration) * width
                    clip_width = end_x - start_x
                    
                    if clip_width > 0:
                        # Clip background
                        color = clip.get('color', track['color'])
                        draw.rectangle([start_x, y1 + 5, end_x, y2 - 5], fill=color)
                        
                        # Clip outline if selected
                        if clip.get('selected', False):
                            draw.rectangle([start_x, y1 + 5, end_x, y2 - 5], outline='#fbbf24', width=2)
                        
                        # Clip name
                        if clip_width > 30:
                            name = clip.get('name', 'Clip')[:10]
                            draw.text((start_x + 5, y1 + track_height // 2 - 5), name, fill='#ffffff')
            
            # Draw playhead
            playhead_x = ((timeline['current_time'] - visible_start) / visible_duration) * width
            if 0 <= playhead_x <= width:
                draw.line([playhead_x, 0, playhead_x, height], fill='#f56565', width=2)
            
            # Draw markers
            for marker in timeline['markers']:
                if visible_start <= marker['time'] <= visible_end:
                    x = ((marker['time'] - visible_start) / visible_duration) * width
                    draw.line([x, ruler_height, x, height], fill=marker['color'], width=1)
                    draw.ellipse([x - 3, ruler_height - 3, x + 3, ruler_height + 3], fill=marker['color'])
            
            # Draw regions
            for region in timeline['regions']:
                if region['end'] >= visible_start and region['start'] <= visible_end:
                    start_x = max(0, ((region['start'] - visible_start) / visible_duration) * width)
                    end_x = min(width, ((region['end'] - visible_start) / visible_duration) * width)
                    draw.rectangle([start_x, 0, end_x, ruler_height], fill=region['color'], outline=None)
            
            # Save preview
            output_path = f"/tmp/timeline_preview_{int(datetime.now().timestamp())}.png"
            img.save(output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Render timeline preview error: {e}")
            return None
    
    def _get_marker_interval(self, duration: float) -> float:
        """Get appropriate marker interval based on duration"""
        if duration <= 5:
            return 0.5
        elif duration <= 10:
            return 1
        elif duration <= 30:
            return 5
        elif duration <= 60:
            return 10
        elif duration <= 300:
            return 30
        elif duration <= 600:
            return 60
        else:
            return 300
    
    def _clips_overlap(self, clip: Dict, start: float, end: float) -> bool:
        """Check if clip overlaps with time range"""
        return not (clip['end_time'] <= start or clip['start_time'] >= end)
    
    def export_timeline(self, timeline: Dict, format: str = 'json') -> Dict:
        """Export timeline data"""
        if format == 'json':
            return timeline
        elif format == 'xml':
            # Convert to XML (simplified)
            import xml.etree.ElementTree as ET
            root = ET.Element('timeline')
            root.set('duration', str(timeline['duration']))
            root.set('frame_rate', str(timeline['frame_rate']))
            
            for track in timeline['tracks']:
                track_elem = ET.SubElement(root, 'track')
                track_elem.set('name', track['name'])
                track_elem.set('type', track['type'])
                
                for clip in track['clips']:
                    clip_elem = ET.SubElement(track_elem, 'clip')
                    clip_elem.set('id', clip['id'])
                    clip_elem.set('name', clip['name'])
                    clip_elem.set('start', str(clip['start_time']))
                    clip_elem.set('end', str(clip['end_time']))
                    clip_elem.set('duration', str(clip['duration']))
            
            return root
        else:
            raise ValueError(f"Unsupported format: {format}")

# Create global instance
timeline = Timeline()
