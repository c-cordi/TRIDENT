"""
TRIDENT - High-Performance 3D Data Visualization for Blender

This addon uses a custom C++ extension module (_trident) for fast CSV data processing:
- Parsing large CSV files with mixed numeric/categorical columns
- Automatic type detection and category encoding
- Efficient data merging operations

The C++ module is essential for performance when working with datasets containing
100k+ points and dozens of categorical variables (common in single-cell genomics data).

Core workflow:
1. User loads CSV files (spatial coords + metadata)
2. C++ module parses and encodes data
3. Python creates 3D point cloud in Blender
4. Geometry nodes instance spheres on points
5. Materials colorize by selected attribute
"""

from . import properties
from . import operators
from . import panel

def register():
    properties.register_properties()
    operators.register_operators()
    panel.register_panel()

def unregister():
    panel.unregister_panel()
    operators.unregister_operators()
    properties.unregister_properties()
