import json
import numpy as np
import bpy

# ============================================================================
# C++ MODULE IMPORT - Core high-performance CSV loading functionality
# ============================================================================
# The _trident C++ module provides:
# - Fast CSV parsing with automatic type detection (numeric vs categorical)
# - Category encoding for string columns
# - Efficient data merging
try:
    from .bin import _trident
    cpp_loader = _trident.DataLoader()
    trident_module = _trident
    print("[TRIDENT] Successfully loaded C++ performance module")
except Exception as e:
    trident_module = None
    cpp_loader = None
    print("[TRIDENT] ERROR: Could not import C++ module:", e)
    print("[TRIDENT] The addon will not work without the compiled C++ module.")

# Add in-memory cache
_cached_data = None
_cached_data_hash = None

def get_cpp_loader():
    """Get the C++ DataLoader instance for CSV operations"""
    return cpp_loader

def get_trident_module():
    """Get the C++ trident module (for availability checks)"""
    return trident_module

def get_data_cache(scene=None):
    """Get data from scene storage with caching"""
    global _cached_data, _cached_data_hash
    
    try:
        if scene is None:
            scene = bpy.context.scene

        if not scene.trident.data_loaded or not scene.trident.data_serialized:
            _cached_data = None
            _cached_data_hash = None
            return None
        
        # Create a simple hash of the serialized data
        current_hash = hash(scene.trident.data_serialized)
        
        # Return cached data if it hasn't changed
        if _cached_data is not None and _cached_data_hash == current_hash:
            return _cached_data
        
        # Reconstruct numpy array from serialized data
        shape = tuple(scene.trident.data_shape)
        if shape == (0, 0):
            return None
            
        # Deserialize the array data (only when needed)
        flat_data = json.loads(scene.trident.data_serialized)
        array = np.array(flat_data, dtype=np.float32).reshape(shape)
        
        # Cache the result
        _cached_data = array
        _cached_data_hash = current_hash
        
        return array
        
    except Exception as e:
        print(f"[TRIDENT] Error loading data cache: {e}")
        _cached_data = None
        _cached_data_hash = None
        return None

def set_data_cache(data, scene=None):
    """Store data in scene storage"""
    global _cached_data, _cached_data_hash
    
    try:
        if scene is None:
            scene = bpy.context.scene
        if data is None:
            scene.trident.data_loaded = False
            scene.trident.data_serialized = ""
            scene.trident.data_shape = (0, 0)
            _cached_data = None
            _cached_data_hash = None
        else:
            scene.trident.data_loaded = True
            scene.trident.data_shape = data.shape
            # Serialize numpy array to JSON
            serialized = json.dumps(data.flatten().tolist())
            scene.trident.data_serialized = serialized
            
            # Update cache
            _cached_data = data
            _cached_data_hash = hash(serialized)
            
        print(f"[TRIDENT] Stored data cache: {data.shape if data is not None else 'None'}")
    except Exception as e:
        print(f"[TRIDENT] Error storing data cache: {e}")

def get_label_cache(scene=None):
    """Get labels from scene storage"""
    try:
        if scene is None:
            scene = bpy.context.scene
        if not scene.trident.data_loaded:
            return None
        return [item.name for item in scene.trident.labels if item.name]
    except Exception as e:
        print(f"[TRIDENT] Error loading label cache: {e}")
        return None

def set_label_cache(labels, scene=None):
    """Labels are already stored in scene.trident.labels, just mark as loaded"""
    try:
        if scene is None:
            scene = bpy.context.scene
        scene.trident.data_loaded = True
        print(f"[TRIDENT] Label cache updated: {labels}")
    except Exception as e:
        print(f"[TRIDENT] Error updating label cache: {e}")

def get_obs_map(scene=None):
    """Get obs map from scene storage"""
    try:
        if scene is None:
            scene = bpy.context.scene
        if not scene.trident.obs_map_json:
            return {}
        return json.loads(scene.trident.obs_map_json)
    except Exception as e:
        print(f"[TRIDENT] Error loading obs map: {e}")
        return {}

def set_obs_map(selected_labels, obs_cat, scene=None):
    """Store obs map in scene storage"""
    try:
        if scene is None:
            scene = bpy.context.scene

        obs_map = dict(zip(selected_labels, obs_cat))
        scene.trident.obs_map_json = json.dumps(obs_map)
        print(f"[TRIDENT] Stored obs map: {obs_map}")
    except Exception as e:
        print(f"[TRIDENT] Error storing obs map: {e}")

def get_cat_map(label=None, scene=None):
    """Get categories for a specific label from original cat_map"""
    if label is None:
        try:
            if scene is None:
                scene = bpy.context.scene
            if not scene.trident.cat_map_json:
                return {}
            return json.loads(scene.trident.cat_map_json)
        except Exception as e:
            print(f"[TRIDENT] Error loading cat map: {e}")
            return {}
    else:
        try:
            scene = bpy.context.scene
            if not scene.trident.cat_map_json:
                return "None"
            full_map = json.loads(scene.trident.cat_map_json)
            return full_map.get(label, "None")
        except Exception as e:
            print(f"[TRIDENT] Error loading cat map for label {label}: {e}")
            return "None"

def set_cat_map(cat_map, scene=None):
    """Store categories for a specific label in original cat_map"""
    try:
        if scene is None:
            scene = bpy.context.scene
        scene.trident.cat_map_json = json.dumps(cat_map)
        print(f"[TRIDENT] Stored cat map: {cat_map}")
    except Exception as e:
        print(f"[TRIDENT] Error storing cat map: {e}")

def get_data_type(scene=None):
    """
    Return True if the selected color label is categorical, False if continuous.
    Returns False if label not found or on error (safer fallback).
    """
    try:
        if scene is None:
            scene = bpy.context.scene
        
        obs_map = get_obs_map(scene)
        
        if not obs_map:
            return False
        
        trident = scene.trident
        color_label = trident.current_color_label or trident.color_label or ''
        
        if not color_label or color_label == 'NONE':
            return False
        
        return obs_map[color_label]
        
    except Exception as e:
        print(f"[TRIDENT] Error in get_data_type: {e}")
        return False