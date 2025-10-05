bl_info = {
    "name": "TRIDENT",
    "author": "Cristiano Cordì",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D Viewport › N-panel › TRIDENT",
    "description": "UMAP/t-SNE embeddings from AnnData into Blender.",
    "category": "3D View"
}

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
