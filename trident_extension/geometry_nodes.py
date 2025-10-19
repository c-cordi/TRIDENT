import bpy
import json
from pathlib import Path
from .data_loader import get_obs_map, get_data_type

def load_palettes():
    """Load color palettes from JSON file"""
    palette_file = Path(__file__).parent / "color_palette.json"
    try:
        with open(palette_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[TRIDENT] Warning: color_palette.json not found, using fallback")
        return {"Viridis": {"type": "sequential", "colors": [[0.267, 0.005, 0.329, 1.0], [0.993, 0.906, 0.144, 1.0]]}}

def get_palette_colors(palette_name):
    """Get RGBA colors from palette"""
    palettes = load_palettes()
    if palette_name not in palettes:
        palette_name = "Viridis"
    return [hex_to_srgb_and_linear(color) for color in palettes[palette_name]["colors"]]

def hex_to_srgb_and_linear(hex_code):
    """Convert hex color (#RRGGBB) to both sRGB and linear RGB values [0,1]."""
    hex_code = hex_code.lstrip('#')
    if len(hex_code) != 6:
        raise ValueError("Hex code must be in the format #RRGGBB")
    
    # Hex > normalized sRGB values
    r = int(hex_code[0:2], 16) / 255.0
    g = int(hex_code[2:4], 16) / 255.0
    b = int(hex_code[4:6], 16) / 255.0
    srgb = (r, g, b)

    # Apply inverse sRGB gamma > linear
    def srgb_to_linear(c):
        if c <= 0.04045:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4

    linear = tuple(srgb_to_linear(c) for c in srgb)
    linear = tuple(list(linear) + [1.0]) 

    return linear

def modify_geometry_nodes_for_large_categories(points_obj, max_label):
    """Modify geometry nodes to handle more than 32 categories"""
    
    # Find the geometry nodes modifier
    mod = None
    for modifier in points_obj.modifiers:
        if modifier.type == 'NODES' and modifier.name == "InstancePoints":
            mod = modifier
            break
    
    if not mod or not mod.node_group:
        print("[TRIDENT] Warning: Could not find geometry nodes modifier")
        return
    
    tree = mod.node_group
    nodes = tree.nodes
    links = tree.links
    
    # Find existing nodes
    n_map = None
    n_store = None
    
    for node in nodes:
        if hasattr(node, 'bl_idname'):
            if node.bl_idname == 'ShaderNodeMapRange':
                n_map = node
            elif node.bl_idname == 'GeometryNodeStoreNamedAttribute':
                n_store = node
    
    if not n_map or not n_store:
        print("[TRIDENT] Warning: Could not find required nodes")
        return
    
    # Disconnect the current Map Range -> Store connection
    for link in links:
        if link.from_node == n_map and link.to_node == n_store:
            links.remove(link)
            break
    
    # Create new nodes if they don't exist
    n_floor = None
    n_subtract = None
    
    # Check if nodes already exist
    for node in nodes:
        if hasattr(node, 'bl_idname') and node.bl_idname == 'ShaderNodeMath':
            if hasattr(node, 'operation'):
                if node.operation == 'FLOOR' and n_floor is None:
                    n_floor = node
                elif node.operation == 'SUBTRACT' and n_subtract is None:
                    n_subtract = node
    
    # Create Floor node if it doesn't exist
    if n_floor is None:
        n_floor = nodes.new(type='ShaderNodeMath')
        n_floor.location = (n_map.location[0] + 200, n_map.location[1] + 100)
        n_floor.operation = 'FLOOR'
    
    # Create Subtract node if it doesn't exist
    if n_subtract is None:
        n_subtract = nodes.new(type='ShaderNodeMath')
        n_subtract.location = (n_map.location[0] + 200, n_map.location[1] - 100)
        n_subtract.operation = 'SUBTRACT'
    
    # n_map.inputs['From Max'].default_value = 32.0
    n_map.clamp = False

    # Create new connections
    # Map Range -> Floor (first input)
    links.new(n_map.outputs['Result'], n_floor.inputs[0])
    
    # Map Range -> Subtract (first input) 
    links.new(n_map.outputs['Result'], n_subtract.inputs[0])
    
    # Floor -> Subtract (second input)
    links.new(n_floor.outputs['Value'], n_subtract.inputs[1])
    
    # Subtract -> Store Named Attribute (Value input)
    links.new(n_subtract.outputs['Value'], n_store.inputs['Value'])
    
    print(f"[TRIDENT] Modified geometry nodes for max {max_label} categories")

def reset_connections(points_obj):
    """Reset geometry nodes connections to original state"""
    
    # Find the geometry nodes modifier
    mod = None
    for modifier in points_obj.modifiers:
        if modifier.type == 'NODES' and modifier.name == "InstancePoints":
            mod = modifier
            break
    
    if not mod or not mod.node_group:
        print("[TRIDENT] Warning: Could not find geometry nodes modifier")
        return
    
    tree = mod.node_group
    nodes = tree.nodes
    links = tree.links
    
    # Find existing nodes
    n_map = None
    n_store = None
    
    for node in nodes:
        if hasattr(node, 'bl_idname'):
            if node.bl_idname == 'ShaderNodeMapRange':
                n_map = node
            elif node.bl_idname == 'GeometryNodeStoreNamedAttribute':
                n_store = node
    
    if not n_map or not n_store:
        print("[TRIDENT] Warning: Could not find required nodes")
        return
    
    # Remove all links to Store Named Attribute's Value input
    for link in links:
        if link.to_node == n_store and link.to_socket.name == 'Value':
            links.remove(link)
    
    # Reconnect Map Range directly to Store Named Attribute
    links.new(n_map.outputs['Result'], n_store.inputs['Value'])
    n_map.clamp = True
    
    print("[TRIDENT] Reset geometry nodes connections")

def setup_instance_material(inst_obj, scene, max_label=10, palette_name='Viridis', points_obj=None):
    """Set up material for the instance object with Color attribute support"""
    
    # Create or get the material
    mat_name = "TRIDENT_Instance_Material"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
    
    # Enable use of nodes
    mat.use_nodes = True
    
    # Clear existing nodes
    mat.node_tree.nodes.clear()
    
    # Create nodes
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Create nodes with proper positioning
    attr_node = nodes.new(type='ShaderNodeAttribute')
    attr_node.location = (-400, 0)
    attr_node.attribute_type = 'GEOMETRY'
    attr_node.attribute_name = "Color"
    
    colorramp_node = nodes.new(type='ShaderNodeValToRGB')
    colorramp_node.location = (-200, 0)
    
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.location = (0, 0)
    
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (300, 0)
    
    # Configure Color Ramp
    colorramp = colorramp_node.color_ramp
    data_type = get_data_type(scene)

    if data_type == False:
        colorramp.interpolation = 'LINEAR'
    else:
        colorramp.interpolation = 'CONSTANT'

    # Get the selected palette
    colors = get_palette_colors(palette_name)

    # Set colors to the default elements in the color ramp
    colorramp.elements[0].color = colors[0]
    colorramp.elements[1].color = colors[-1]

    # Add color stops
    if max_label > 32 and data_type == True:
        modify_geometry_nodes_for_large_categories(points_obj, max_label)
    else:
        reset_connections(points_obj)

    if max_label > len(colors) and data_type == True and max_label <= 32:
        print(f"[TRIDENT] Warning: max_label {max_label} exceeds palette size {len(colors)}. Extending palette.")
        repetitions = (max_label // len(colors)) + 1
        colors = (colors * int(repetitions))[:int(max_label)]
        colors = colors[:32]
    
    for i, color in enumerate(colors):
        if i == 0:
            continue
        elif i == len(colors) - 1:
            continue
        else:
            elem = colorramp.elements.new(i / (len(colors) - 1))
            elem.color = color
    
    # Create connections
    links.new(attr_node.outputs['Fac'], colorramp_node.inputs['Fac'])
    links.new(colorramp_node.outputs['Color'], principled_node.inputs['Base Color'])
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    # Assign material to object
    if len(inst_obj.data.materials) == 0:
        inst_obj.data.materials.append(mat)
    else:
        inst_obj.data.materials[0] = mat
    
    return mat

def setup_geometry_nodes(points_obj, inst_obj, context, max_color=10):
    """Set up geometry nodes for point cloud visualization"""
    
    palette = getattr(context.scene, 'trident_color_palette', 'Viridis')
    if not palette:
        palette = 'Viridis'
    setup_instance_material(inst_obj, context.scene, max_label=max_color, palette_name=palette, points_obj=points_obj)

    mod = points_obj.modifiers.new(name="InstancePoints", type='NODES')
    if not mod.node_group:
        mod.node_group = bpy.data.node_groups.new(name="TRIDENT_GeoNodes", type='GeometryNodeTree')

    tree = mod.node_group
    tree.nodes.clear()
    tree.links.clear()

    iface = tree.interface

    def ensure_iface_socket(name, in_out, socket_type):
        for it in iface.items_tree:
            if getattr(it, "in_out", None) == in_out and getattr(it, "name", None) == name:
                return it
        return iface.new_socket(name=name, in_out=in_out, socket_type=socket_type)

    ensure_iface_socket("Geometry", 'INPUT',  'NodeSocketGeometry')
    ensure_iface_socket("Geometry", 'OUTPUT', 'NodeSocketGeometry')

    nodes = tree.nodes
    links = tree.links

    # Create all nodes with proper positioning
    n_in     = nodes.new(type='NodeGroupInput'); n_in.location = (-600, 0)
    n_out    = nodes.new(type='NodeGroupOutput'); n_out.location = ( 800, 0)
    n_iop    = nodes.new(type='GeometryNodeInstanceOnPoints'); n_iop.location = (-200, 0)
    n_obj    = nodes.new(type='GeometryNodeObjectInfo'); n_obj.location = (-400, -200)
    n_attr   = nodes.new(type='GeometryNodeInputNamedAttribute'); n_attr.location = (-400, 200)
    n_map    = nodes.new(type='ShaderNodeMapRange'); n_map.location = ( 100, 200)
    n_store  = nodes.new(type='GeometryNodeStoreNamedAttribute'); n_store.location = ( 300, 0)
    n_real   = nodes.new(type='GeometryNodeRealizeInstances'); n_real.location = ( 600, 0)

    # Configure Object Info node
    n_obj.inputs['As Instance'].default_value = True
    n_obj.inputs['Object'].default_value = inst_obj

    # Configure Named Attribute node
    n_attr.inputs[0].default_value = context.scene.trident.labels[0].name if context.scene.trident.labels else "label"
    n_attr.data_type = 'INT'

    # Configure Map Range node
    n_map.data_type = 'FLOAT'
    n_map.inputs['From Min'].default_value = 0.0
    n_map.inputs['From Max'].default_value = max_color
    n_map.inputs['To Min'].default_value = 0.0
    n_map.inputs['To Max'].default_value = 1.0

    # Configure Store Named Attribute node
    n_store.data_type = 'FLOAT'
    n_store.domain = 'INSTANCE'
    n_store.inputs['Name'].default_value = "Color"

    # Create all the connections
    links.new(n_in.outputs["Geometry"], n_iop.inputs['Points'])           
    links.new(n_obj.outputs['Geometry'], n_iop.inputs['Instance'])        
    links.new(n_iop.outputs['Instances'], n_store.inputs['Geometry'])
    links.new(n_attr.outputs['Attribute'], n_map.inputs['Value'])         
    links.new(n_map.outputs['Result'], n_store.inputs['Value'])
    links.new(n_store.outputs['Geometry'], n_real.inputs['Geometry'])
    links.new(n_real.outputs['Geometry'], n_out.inputs["Geometry"])

    return mod