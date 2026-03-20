"""
Layer Manager - Professional layer management for designs
Author: @kinva_master
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from ..utils import generate_uuid

logger = logging.getLogger(__name__)

class LayerManager:
    """Professional layer management for designs"""
    
    def __init__(self):
        self.layers = []
        self.active_layer_id = None
        self.groups = []
        self.filters = []
        self.masks = []
        
        # Blend modes
        self.blend_modes = [
            'normal', 'multiply', 'screen', 'overlay', 'darken', 'lighten',
            'color_dodge', 'color_burn', 'hard_light', 'soft_light', 'difference',
            'exclusion', 'hue', 'saturation', 'color', 'luminosity'
        ]
        
        # Layer types
        self.layer_types = ['pixel', 'text', 'shape', 'adjustment', 'group', 'smart_object']
        
    def create_layers(self, count: int = 1, name_prefix: str = 'Layer') -> List[Dict]:
        """Create new layers"""
        layers = []
        for i in range(count):
            layer = {
                'id': generate_uuid(),
                'name': f'{name_prefix} {i + 1}',
                'index': i,
                'type': 'pixel',
                'visible': True,
                'locked': False,
                'opacity': 1.0,
                'fill_opacity': 1.0,
                'blend_mode': 'normal',
                'elements': [],
                'effects': [],
                'filters': [],
                'mask': None,
                'group_id': None,
                'parent_id': None,
                'children': [],
                'position': {'x': 0, 'y': 0},
                'size': {'width': 0, 'height': 0},
                'transform': {
                    'scale_x': 1.0,
                    'scale_y': 1.0,
                    'rotation': 0,
                    'skew_x': 0,
                    'skew_y': 0
                },
                'styles': {
                    'shadow': None,
                    'stroke': None,
                    'glow': None,
                    'gradient': None
                },
                'metadata': {
                    'created_by': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            }
            layers.append(layer)
        
        self.layers = layers
        if layers:
            self.active_layer_id = layers[0]['id']
        
        return layers
    
    def add_layer(self, name: str = None, layer_type: str = 'pixel', 
                  position: int = None) -> Dict:
        """Add new layer at specified position"""
        if layer_type not in self.layer_types:
            raise ValueError(f"Invalid layer type: {layer_type}")
        
        if position is None:
            position = len(self.layers)
        
        layer = {
            'id': generate_uuid(),
            'name': name or f'Layer {len(self.layers) + 1}',
            'index': position,
            'type': layer_type,
            'visible': True,
            'locked': False,
            'opacity': 1.0,
            'fill_opacity': 1.0,
            'blend_mode': 'normal',
            'elements': [],
            'effects': [],
            'filters': [],
            'mask': None,
            'group_id': None,
            'parent_id': None,
            'children': [],
            'position': {'x': 0, 'y': 0},
            'size': {'width': 0, 'height': 0},
            'transform': {
                'scale_x': 1.0,
                'scale_y': 1.0,
                'rotation': 0,
                'skew_x': 0,
                'skew_y': 0
            },
            'styles': {
                'shadow': None,
                'stroke': None,
                'glow': None,
                'gradient': None
            },
            'metadata': {
                'created_by': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }
        
        self.layers.insert(position, layer)
        self._update_layer_indices()
        self.active_layer_id = layer['id']
        
        return layer
    
    def remove_layer(self, layer_id: str, delete_children: bool = True) -> bool:
        """Remove layer and optionally its children"""
        for i, layer in enumerate(self.layers):
            if layer['id'] == layer_id:
                if delete_children:
                    # Remove all child layers
                    self.layers = [l for l in self.layers if l.get('parent_id') != layer_id]
                self.layers.pop(i)
                if self.active_layer_id == layer_id:
                    self.active_layer_id = self.layers[0]['id'] if self.layers else None
                self._update_layer_indices()
                return True
        return False
    
    def duplicate_layer(self, layer_id: str) -> Optional[Dict]:
        """Duplicate layer with all properties"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                new_layer = layer.copy()
                new_layer['id'] = generate_uuid()
                new_layer['name'] = f"{layer['name']} Copy"
                new_layer['index'] = layer['index'] + 1
                new_layer['metadata']['created_at'] = datetime.now().isoformat()
                new_layer['metadata']['updated_at'] = datetime.now().isoformat()
                
                # Duplicate children if any
                if layer.get('children'):
                    new_layer['children'] = []
                    for child_id in layer['children']:
                        child_layer = self.get_layer(child_id)
                        if child_layer:
                            new_child = child_layer.copy()
                            new_child['id'] = generate_uuid()
                            new_child['parent_id'] = new_layer['id']
                            new_child['name'] = f"{child_layer['name']} Copy"
                            new_layer['children'].append(new_child['id'])
                            self.layers.append(new_child)
                
                self.layers.insert(new_layer['index'], new_layer)
                self._update_layer_indices()
                return new_layer
        
        return None
    
    def move_layer_up(self, layer_id: str) -> bool:
        """Move layer up in stack"""
        for i, layer in enumerate(self.layers):
            if layer['id'] == layer_id and i < len(self.layers) - 1:
                self.layers[i], self.layers[i + 1] = self.layers[i + 1], self.layers[i]
                self._update_layer_indices()
                return True
        return False
    
    def move_layer_down(self, layer_id: str) -> bool:
        """Move layer down in stack"""
        for i, layer in enumerate(self.layers):
            if layer['id'] == layer_id and i > 0:
                self.layers[i], self.layers[i - 1] = self.layers[i - 1], self.layers[i]
                self._update_layer_indices()
                return True
        return False
    
    def move_layer_to_top(self, layer_id: str) -> bool:
        """Move layer to top of stack"""
        for i, layer in enumerate(self.layers):
            if layer['id'] == layer_id:
                self.layers.append(self.layers.pop(i))
                self._update_layer_indices()
                return True
        return False
    
    def move_layer_to_bottom(self, layer_id: str) -> bool:
        """Move layer to bottom of stack"""
        for i, layer in enumerate(self.layers):
            if layer['id'] == layer_id:
                self.layers.insert(0, self.layers.pop(i))
                self._update_layer_indices()
                return True
        return False
    
    def create_group(self, name: str = None, layer_ids: List[str] = None) -> Dict:
        """Create a group from selected layers"""
        group = {
            'id': generate_uuid(),
            'name': name or f'Group {len(self.groups) + 1}',
            'type': 'group',
            'layers': layer_ids or [],
            'expanded': True,
            'visible': True,
            'locked': False,
            'opacity': 1.0,
            'blend_mode': 'normal',
            'position': {'x': 0, 'y': 0},
            'transform': {
                'scale_x': 1.0,
                'scale_y': 1.0,
                'rotation': 0
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }
        
        self.groups.append(group)
        
        # Update parent_id for layers in group
        if layer_ids:
            for layer_id in layer_ids:
                layer = self.get_layer(layer_id)
                if layer:
                    layer['group_id'] = group['id']
        
        return group
    
    def ungroup(self, group_id: str) -> bool:
        """Ungroup layers"""
        for i, group in enumerate(self.groups):
            if group['id'] == group_id:
                # Remove group_id from layers
                for layer_id in group['layers']:
                    layer = self.get_layer(layer_id)
                    if layer:
                        layer['group_id'] = None
                self.groups.pop(i)
                return True
        return False
    
    def _update_layer_indices(self):
        """Update layer indices"""
        for i, layer in enumerate(self.layers):
            layer['index'] = i
            layer['metadata']['updated_at'] = datetime.now().isoformat()
    
    def set_layer_visibility(self, layer_id: str, visible: bool) -> bool:
        """Set layer visibility"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['visible'] = visible
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def set_layer_lock(self, layer_id: str, locked: bool) -> bool:
        """Lock/unlock layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['locked'] = locked
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def set_layer_opacity(self, layer_id: str, opacity: float) -> bool:
        """Set layer opacity"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['opacity'] = max(0.0, min(1.0, opacity))
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def set_layer_blend_mode(self, layer_id: str, blend_mode: str) -> bool:
        """Set layer blend mode"""
        if blend_mode not in self.blend_modes:
            return False
        
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['blend_mode'] = blend_mode
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def set_layer_transform(self, layer_id: str, transform: Dict) -> bool:
        """Set layer transform properties"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['transform'].update(transform)
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def add_layer_effect(self, layer_id: str, effect_type: str, params: Dict) -> bool:
        """Add effect to layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                effect = {
                    'id': generate_uuid(),
                    'type': effect_type,
                    'params': params,
                    'enabled': True,
                    'created_at': datetime.now().isoformat()
                }
                layer['effects'].append(effect)
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def remove_layer_effect(self, layer_id: str, effect_id: str) -> bool:
        """Remove effect from layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['effects'] = [e for e in layer['effects'] if e['id'] != effect_id]
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def add_layer_mask(self, layer_id: str, mask_type: str, mask_data: Any) -> bool:
        """Add mask to layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['mask'] = {
                    'id': generate_uuid(),
                    'type': mask_type,
                    'data': mask_data,
                    'enabled': True,
                    'inverted': False,
                    'created_at': datetime.now().isoformat()
                }
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def remove_layer_mask(self, layer_id: str) -> bool:
        """Remove mask from layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['mask'] = None
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def add_layer_filter(self, layer_id: str, filter_type: str, params: Dict) -> bool:
        """Add filter to layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                filter_obj = {
                    'id': generate_uuid(),
                    'type': filter_type,
                    'params': params,
                    'enabled': True,
                    'created_at': datetime.now().isoformat()
                }
                layer['filters'].append(filter_obj)
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def remove_layer_filter(self, layer_id: str, filter_id: str) -> bool:
        """Remove filter from layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['filters'] = [f for f in layer['filters'] if f['id'] != filter_id]
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def rename_layer(self, layer_id: str, new_name: str) -> bool:
        """Rename layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                layer['name'] = new_name
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def merge_layers(self, layer_ids: List[str]) -> Optional[Dict]:
        """Merge multiple layers into one"""
        if len(layer_ids) < 2:
            return None
        
        # Find layers to merge
        layers_to_merge = [l for l in self.layers if l['id'] in layer_ids]
        if not layers_to_merge:
            return None
        
        # Create merged layer
        merged_layer = {
            'id': generate_uuid(),
            'name': 'Merged Layer',
            'index': max(l['index'] for l in layers_to_merge),
            'type': 'pixel',
            'visible': True,
            'locked': False,
            'opacity': 1.0,
            'fill_opacity': 1.0,
            'blend_mode': 'normal',
            'elements': [],
            'effects': [],
            'filters': [],
            'mask': None,
            'group_id': None,
            'parent_id': None,
            'children': [],
            'position': {'x': 0, 'y': 0},
            'size': {'width': 0, 'height': 0},
            'transform': {
                'scale_x': 1.0,
                'scale_y': 1.0,
                'rotation': 0,
                'skew_x': 0,
                'skew_y': 0
            },
            'styles': {
                'shadow': None,
                'stroke': None,
                'glow': None,
                'gradient': None
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }
        
        # Combine elements
        for layer in layers_to_merge:
            merged_layer['elements'].extend(layer['elements'])
            merged_layer['effects'].extend(layer['effects'])
            merged_layer['filters'].extend(layer['filters'])
        
        # Remove merged layers
        self.layers = [l for l in self.layers if l['id'] not in layer_ids]
        
        # Add merged layer
        self.layers.append(merged_layer)
        self._update_layer_indices()
        self.active_layer_id = merged_layer['id']
        
        return merged_layer
    
    def flatten_layers(self) -> Dict:
        """Flatten all visible layers"""
        visible_layers = [l for l in self.layers if l['visible']]
        if not visible_layers:
            return None
        
        # Create flattened layer
        flattened_layer = {
            'id': generate_uuid(),
            'name': 'Flattened',
            'index': 0,
            'type': 'pixel',
            'visible': True,
            'locked': False,
            'opacity': 1.0,
            'fill_opacity': 1.0,
            'blend_mode': 'normal',
            'elements': [],
            'effects': [],
            'filters': [],
            'mask': None,
            'group_id': None,
            'parent_id': None,
            'children': [],
            'position': {'x': 0, 'y': 0},
            'size': {'width': 0, 'height': 0},
            'transform': {
                'scale_x': 1.0,
                'scale_y': 1.0,
                'rotation': 0,
                'skew_x': 0,
                'skew_y': 0
            },
            'styles': {
                'shadow': None,
                'stroke': None,
                'glow': None,
                'gradient': None
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }
        
        # Combine all visible layer elements
        for layer in visible_layers:
            flattened_layer['elements'].extend(layer['elements'])
        
        self.layers = [flattened_layer]
        self.active_layer_id = flattened_layer['id']
        
        return flattened_layer
    
    def get_layer(self, layer_id: str) -> Optional[Dict]:
        """Get layer by ID"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                return layer
        return None
    
    def get_layers_by_type(self, layer_type: str) -> List[Dict]:
        """Get all layers of specific type"""
        return [l for l in self.layers if l['type'] == layer_type]
    
    def get_visible_layers(self) -> List[Dict]:
        """Get all visible layers"""
        return [l for l in self.layers if l['visible']]
    
    def get_locked_layers(self) -> List[Dict]:
        """Get all locked layers"""
        return [l for l in self.layers if l['locked']]
    
    def get_layers_ordered(self) -> List[Dict]:
        """Get layers in render order (top to bottom)"""
        return list(reversed(self.layers))
    
    def get_layer_tree(self) -> List[Dict]:
        """Get hierarchical layer tree structure"""
        tree = []
        for layer in self.layers:
            if layer.get('parent_id') is None:
                node = layer.copy()
                node['children'] = self._get_layer_children(layer['id'])
                tree.append(node)
        return tree
    
    def _get_layer_children(self, parent_id: str) -> List[Dict]:
        """Get child layers recursively"""
        children = []
        for layer in self.layers:
            if layer.get('parent_id') == parent_id:
                node = layer.copy()
                node['children'] = self._get_layer_children(layer['id'])
                children.append(node)
        return children
    
    def add_element_to_layer(self, layer_id: str, element: Dict) -> bool:
        """Add element to layer"""
        for layer in self.layers:
            if layer['id'] == layer_id and not layer['locked']:
                layer['elements'].append(element)
                layer['metadata']['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def remove_element_from_layer(self, layer_id: str, element_id: str) -> bool:
        """Remove element from layer"""
        for layer in self.layers:
            if layer['id'] == layer_id:
                original_count = len(layer['elements'])
                layer['elements'] = [e for e in layer['elements'] if e.get('id') != element_id]
                if len(layer['elements']) != original_count:
                    layer['metadata']['updated_at'] = datetime.now().isoformat()
                    return True
        return False
    
    def get_active_layer(self) -> Optional[Dict]:
        """Get active layer"""
        if self.active_layer_id:
            return self.get_layer(self.active_layer_id)
        return None
    
    def set_active_layer(self, layer_id: str) -> bool:
        """Set active layer"""
        if self.get_layer(layer_id):
            self.active_layer_id = layer_id
            return True
        return False
    
    def export_layers(self, format: str = 'json') -> Dict:
        """Export layers data"""
        if format == 'json':
            return {
                'layers': self.layers,
                'groups': self.groups,
                'active_layer': self.active_layer_id
            }
        elif format == 'xml':
            # Convert to XML (simplified)
            import xml.etree.ElementTree as ET
            root = ET.Element('layers')
            for layer in self.layers:
                layer_elem = ET.SubElement(root, 'layer')
                layer_elem.set('id', layer['id'])
                layer_elem.set('name', layer['name'])
                layer_elem.set('type', layer['type'])
                layer_elem.set('visible', str(layer['visible']))
                layer_elem.set('opacity', str(layer['opacity']))
                layer_elem.set('blend_mode', layer['blend_mode'])
            return root
        else:
            raise ValueError(f"Unsupported format: {format}")

# Create global instance
layer_manager = LayerManager()
