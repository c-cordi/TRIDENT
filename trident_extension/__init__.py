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
