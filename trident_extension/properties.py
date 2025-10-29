import bpy

class TRIDENT_LabelItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Label")

def get_color_label_items(self, context):
    """Dynamic enum items based on loaded labels"""
    items = [('NONE', 'None', 'No color attribute')]
    
    # Access through the property group
    trident = context.scene.trident
    for item in trident.labels:
        if item.name:
            items.append((item.name, item.name, f"Color by {item.name}"))
    
    return items

def get_palette_items(self, context):
    """Dynamic enum items for color palettes"""
    try:
        from . import geometry_nodes
        palettes = geometry_nodes.load_palettes()
        items = []
        for palette_name, palette_data in palettes.items():
            description = palette_data.get("description", "")
            items.append((palette_name, palette_name, description))
        return items
    except Exception as e:
        print(f"[TRIDENT] Error loading palettes: {e}")
        return [('Viridis', 'Viridis', 'Default palette')]

def update_point_size(self, context):
    points_obj = context.scene.trident.points_obj
    if not points_obj or points_obj.name not in bpy.data.objects:
        return
    # Find the geometry nodes modifier
    mod = points_obj.modifiers.get("InstancePoints")
    if not mod or not mod.node_group:
        return
    # Find the Value node and update its value
    for node in mod.node_group.nodes:
        if node.bl_idname == 'ShaderNodeValue':
            node.outputs[0].default_value = self.point_size / 10.0
            break

def update_title_size(self, context):
    # Find the title text object in the legend scene(s)
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            if obj.type == 'FONT' and obj.name.startswith("Title"):
                obj.data.size = self.title_size

class TRIDENT_Properties(bpy.types.PropertyGroup):
    """Main TRIDENT property group - consolidates all scene properties"""
    
    # File paths
    filepath_data: bpy.props.StringProperty(name="obsm File Path",
        description="Path to the obsm CSV file",
        default="",
        subtype='FILE_PATH'
    )
    
    filepath_obs: bpy.props.StringProperty(
        name="obs File Path", 
        description="Path to the obs CSV file",
        default="",
        subtype='FILE_PATH'
    )
    
    # Label collections
    all_labels: bpy.props.CollectionProperty(type=TRIDENT_LabelItem)
    labels: bpy.props.CollectionProperty(type=TRIDENT_LabelItem)
    labels_index: bpy.props.IntProperty(default=0)
    excluded_labels: bpy.props.CollectionProperty(type=TRIDENT_LabelItem)
    excluded_labels_index: bpy.props.IntProperty(default=0)

    show_treatment_override: bpy.props.BoolProperty(
        name="Show Treatment Override",
        description="Show/hide label treatment override options",
        default=False
    )
    
    label_treatment_override: bpy.props.EnumProperty(
        name="Label Treatment Override",
        description="Override automatic categorical/continuous detection",
        items=[
            ('AUTO', "Auto", "Use automatic detection based on data type"),
            ('CATEGORICAL', "Categorical", "Force categorical treatment"),
            ('CONTINUOUS', "Continuous", "Force continuous treatment")
        ],
        default='AUTO'
    )
    
    # Color settings
    color_label: bpy.props.EnumProperty(
        name="Color Label",
        description="Label to use for coloring points",
        items=get_color_label_items
    )
    
    color_palette: bpy.props.EnumProperty(
        name="Color Palette",
        description="Color palette to use for visualization",
        items=get_palette_items
    )
    
    # Environment
    environment_transparent: bpy.props.BoolProperty(default=False)
    
    # Data storage
    data_loaded: bpy.props.BoolProperty(
        name="Data Loaded",
        description="Whether TRIDENT data has been loaded",
        default=False
    )
    
    data_serialized: bpy.props.StringProperty(
        name="Serialized Data",
        description="Serialized numpy array data",
        default=""
    )
    
    data_shape: bpy.props.IntVectorProperty(
        name="Data Shape",
        description="Shape of the data array",
        size=2,
        default=(0, 0)
    )
    
    obs_map_json: bpy.props.StringProperty(
        name="Obs Map JSON",
        description="Serialized obs mapping",
        default=""
    )
    
    cat_map_json: bpy.props.StringProperty(
        name="Category Map JSON",
        description="Serialized category mapping",
        default=""
    )
    
    # Legend settings
    legend_title: bpy.props.StringProperty(
        name="Legend Title",
        description="Title for the legend",
        default="TRIDENT Visualization"
    )
    
    title_size: bpy.props.FloatProperty(
        name="Title Size",
        description="Font size for the title",
        default=0.8,
        min=0.1,
        max=2.0,
        update=update_title_size
    )

    current_color_label: bpy.props.StringProperty(
        name="Current Color Label",
        description="Currently selected color label name",
        default=""
    )
    
    # Object references
    instance_obj: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Instance Object",
        description="Reference to TRIDENT_Instance object"
    )
    
    points_obj: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Points Object", 
        description="Reference to TRIDENT_Points object"
    )

    point_size: bpy.props.FloatProperty(
        name="Point Size",
        description="Size of the points in the visualization",
        default=0.2,
        min=0.001,
        max=20.0,
        update=update_point_size
    )

    sun: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Sun Light",
        description="Reference to Sun light object"
    )
    
    plane_floor: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Floor Plane",
        description="Reference to floor plane"
    )
    
    plane_back: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Back Plane",
        description="Reference to back plane (Plane.001)"
    )
    
    plane_side: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Side Plane",
        description="Reference to side plane (Plane.002)"
    )
    
    shadow_material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Shadow Catcher Material",
        description="Reference to shadow catcher material"
    )
    
    legend_title_material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Legend Title Material",
        description="Reference to legend title material"
    )

def register_properties():
    bpy.utils.register_class(TRIDENT_LabelItem)
    bpy.utils.register_class(TRIDENT_Properties)
    
    # Register the single property group on Scene
    bpy.types.Scene.trident = bpy.props.PointerProperty(type=TRIDENT_Properties)

def unregister_properties():
    # Unregister the single property
    del bpy.types.Scene.trident
    
    bpy.utils.unregister_class(TRIDENT_Properties)
    bpy.utils.unregister_class(TRIDENT_LabelItem)