import sys
import json
import numpy as np
import bpy
from pathlib import Path

# Import the C++ module
_debug = Path(__file__).resolve().parent / "cpp_build"
if str(_debug) not in sys.path:
    sys.path.insert(0, str(_debug))

try:
    import trident
    cpp_loader = trident.DataLoader()
except Exception as e:
    trident = None
    cpp_loader = None
    print("[TRIDENT] Could not import C++ module:", e)

# Add in-memory cache
_cached_data = None
_cached_data_hash = None

def get_cpp_loader():
    return cpp_loader

def get_trident_module():
    return trident

def get_data_cache():
    """Get data from scene storage with caching"""
    global _cached_data, _cached_data_hash
    
    try:
        scene = bpy.data.scenes["Scene"]
        if not scene.trident_data_loaded or not scene.trident_data_serialized:
            _cached_data = None
            _cached_data_hash = None
            return None
        
        # Create a simple hash of the serialized data
        current_hash = hash(scene.trident_data_serialized)
        
        # Return cached data if it hasn't changed
        if _cached_data is not None and _cached_data_hash == current_hash:
            return _cached_data
        
        # Reconstruct numpy array from serialized data
        shape = tuple(scene.trident_data_shape)
        if shape == (0, 0):
            return None
            
        # Deserialize the array data (only when needed)
        flat_data = json.loads(scene.trident_data_serialized)
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

def set_data_cache(data):
    """Store data in scene storage"""
    global _cached_data, _cached_data_hash
    
    try:
        scene = bpy.data.scenes["Scene"]
        if data is None:
            scene.trident_data_loaded = False
            scene.trident_data_serialized = ""
            scene.trident_data_shape = (0, 0)
            _cached_data = None
            _cached_data_hash = None
        else:
            scene.trident_data_loaded = True
            scene.trident_data_shape = data.shape
            # Serialize numpy array to JSON
            serialized = json.dumps(data.flatten().tolist())
            scene.trident_data_serialized = serialized
            
            # Update cache
            _cached_data = data
            _cached_data_hash = hash(serialized)
            
        print(f"[TRIDENT] Stored data cache: {data.shape if data is not None else 'None'}")
    except Exception as e:
        print(f"[TRIDENT] Error storing data cache: {e}")

def get_label_cache():
    """Get labels from scene storage"""
    try:
        scene = bpy.data.scenes["Scene"]
        if not scene.trident_data_loaded:
            return None
        return [item.name for item in scene.trident_labels if item.name]
    except Exception as e:
        print(f"[TRIDENT] Error loading label cache: {e}")
        return None

def set_label_cache(labels):
    """Labels are already stored in scene.trident_labels, just mark as loaded"""
    try:
        scene = bpy.data.scenes["Scene"]
        scene.trident_data_loaded = True
        print(f"[TRIDENT] Label cache updated: {labels}")
    except Exception as e:
        print(f"[TRIDENT] Error updating label cache: {e}")

def get_obs_map():
    """Get obs map from scene storage"""
    try:
        scene = bpy.data.scenes["Scene"]
        if not scene.trident_obs_map_json:
            return {}
        return json.loads(scene.trident_obs_map_json)
    except Exception as e:
        print(f"[TRIDENT] Error loading obs map: {e}")
        return {}

def set_obs_map(selected_labels, obs_cat):
    """Store obs map in scene storage"""
    try:
        scene = bpy.data.scenes["Scene"]
        obs_map = dict(zip(selected_labels, obs_cat))
        scene.trident_obs_map_json = json.dumps(obs_map)
        print(f"[TRIDENT] Stored obs map: {obs_map}")
    except Exception as e:
        print(f"[TRIDENT] Error storing obs map: {e}")

def get_cat_map(label=None):
    """Get categories for a specific label from original cat_map"""
    if label is None:
        try:
            scene = bpy.data.scenes["Scene"]
            if not scene.trident_cat_map_json:
                return {}
            return json.loads(scene.trident_cat_map_json)
        except Exception as e:
            print(f"[TRIDENT] Error loading cat map: {e}")
            return {}
    else:
        try:
            scene = bpy.data.scenes["Scene"]
            if not scene.trident_cat_map_json:
                return "None"
            full_map = json.loads(scene.trident_cat_map_json)
            return full_map.get(label, "None")
        except Exception as e:
            print(f"[TRIDENT] Error loading cat map for label {label}: {e}")
            return "None"

def set_cat_map(cat_map):
    """Store categories for a specific label in original cat_map"""
    try:
        scene = bpy.data.scenes["Scene"]
        scene.trident_cat_map_json = json.dumps(cat_map)
        print(f"[TRIDENT] Stored cat map: {cat_map}")
    except Exception as e:
        print(f"[TRIDENT] Error storing cat map: {e}")

def get_data_type(scene):
    obs_map = get_obs_map()
    if scene.trident_color_label == '':
        if scene.trident_current_color_label == 'NONE':
            return False
        else:
            return obs_map[scene.trident_current_color_label]
    else:
        if scene.trident_color_label == 'NONE':
            return False
        else:
            return obs_map[scene.trident_color_label]