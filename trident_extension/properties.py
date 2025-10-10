import bpy

class TRIDENT_LabelItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Label")

def get_color_label_items(self, context):
    """Dynamic enum items based on loaded labels"""
    items = [('NONE', 'None', 'No color attribute')]
    
    # Get labels from the loaded data
    for item in context.scene.trident_labels:
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

def register_properties():
    bpy.utils.register_class(TRIDENT_LabelItem)

    bpy.types.Scene.trident_filepath_data = bpy.props.StringProperty(
        name="obsm File Path",
        description="Path to the obsm CSV file",
        default="",
        subtype='FILE_PATH'
    )
    bpy.types.Scene.trident_filepath_obs = bpy.props.StringProperty(
        name="obs File Path", 
        description="Path to the obs CSV file",
        default="",
        subtype='FILE_PATH'
    )

    bpy.types.Scene.trident_color_label = bpy.props.EnumProperty(
        name="Color Label",
        description="Label to use for coloring points",
        items=get_color_label_items
    )

    bpy.types.Scene.trident_color_palette = bpy.props.EnumProperty(
        name="Color Palette",
        description="Color palette to use for visualization",
        items=get_palette_items
    )

    bpy.types.Scene.trident_all_labels = bpy.props.CollectionProperty(type=TRIDENT_LabelItem)
    bpy.types.Scene.trident_labels = bpy.props.CollectionProperty(type=TRIDENT_LabelItem)
    bpy.types.Scene.trident_labels_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.trident_excluded_labels = bpy.props.CollectionProperty(type=TRIDENT_LabelItem)
    bpy.types.Scene.trident_excluded_labels_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.trident_environment_transparent = bpy.props.BoolProperty(default=False)

    bpy.types.Scene.trident_data_loaded = bpy.props.BoolProperty(
        name="Data Loaded",
        description="Whether TRIDENT data has been loaded",
        default=False
    )
    
    # Store data as a flattened string
    bpy.types.Scene.trident_data_serialized = bpy.props.StringProperty(
        name="Serialized Data",
        description="Serialized numpy array data",
        default=""
    )
    
    # Store data shape for reconstruction
    bpy.types.Scene.trident_data_shape = bpy.props.IntVectorProperty(
        name="Data Shape",
        description="Shape of the data array",
        size=2,
        default=(0, 0)
    )
    
    # Store obs mapping as JSON string
    bpy.types.Scene.trident_obs_map_json = bpy.props.StringProperty(
        name="Obs Map JSON",
        description="Serialized obs mapping",
        default=""
    )

    # Store category mapping as JSON string
    bpy.types.Scene.trident_cat_map_json = bpy.props.StringProperty(
        name="Category Map JSON",
        description="Serialized category mapping",
        default=""
    )

    bpy.types.Scene.trident_legend_title = bpy.props.StringProperty(
    name="Legend Title",
    description="Title for the legend",
    default="TRIDENT Visualization"
    )

    bpy.types.Scene.trident_current_color_label = bpy.props.StringProperty(
    name="Current Color Label",
    description="Currently selected color label name",
    default=""
    )

def unregister_properties():
    bpy.utils.unregister_class(TRIDENT_LabelItem)

    del bpy.types.Scene.trident_filepath_data
    del bpy.types.Scene.trident_filepath_obs
    del bpy.types.Scene.trident_all_labels
    del bpy.types.Scene.trident_labels
    del bpy.types.Scene.trident_labels_index
    del bpy.types.Scene.trident_excluded_labels
    del bpy.types.Scene.trident_excluded_labels_index
    del bpy.types.Scene.trident_color_label
    del bpy.types.Scene.trident_color_palette
    del bpy.types.Scene.trident_legend_title
    del bpy.types.Scene.trident_current_color_label

    # Recovery
    del bpy.types.Scene.trident_data_loaded
    del bpy.types.Scene.trident_data_serialized
    del bpy.types.Scene.trident_data_shape
    del bpy.types.Scene.trident_obs_map_json
    del bpy.types.Scene.trident_cat_map_json