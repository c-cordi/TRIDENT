import bpy
from . import data_loader

trident = data_loader.get_trident_module()

class TRIDENT_PT_Base:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TRIDENT"
    
    @classmethod
    def poll(cls, context):
        return trident is not None

class TRIDENT_PT_DataInput(TRIDENT_PT_Base, bpy.types.Panel):
    bl_label = "Data Input"
    bl_idname = "TRIDENT_PT_data_input"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # File path input for obsm
        layout.label(text="adata.obsm:")
        layout.prop(scene.trident, "filepath_data", text="")  # Changed: scene.trident.filepath_data

        # File path input for obs
        layout.label(text="adata.obs:")
        layout.prop(scene.trident, "filepath_obs", text="")  # Changed: scene.trident.filepath_obs

        # Load headers only
        row = layout.row()
        row.operator("trident.load_data", text="Load Headers", icon='TEXT')

class TRIDENT_UL_IncludedLabelsList(bpy.types.UIList):
    """Custom UIList for included labels with exclude buttons"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Show label name
            layout.label(text=item.name, icon='NONE')
            
            # Exclude button
            exclude_op = layout.operator("trident.exclude_single_label", text="", icon='X', emboss=False)
            exclude_op.label_name = item.name
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='CHECKMARK')

class TRIDENT_UL_ExcludedLabelsList(bpy.types.UIList):
    """Custom UIList for excluded labels with include buttons"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Show label name
            layout.label(text=item.name, icon='NONE')
            
            # Include button
            include_op = layout.operator("trident.include_single_label", text="", icon='ADD', emboss=False)
            include_op.label_name = item.name
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='X')

class TRIDENT_PT_Labels(TRIDENT_PT_Base, bpy.types.Panel):
    bl_label = "Labels Configuration"
    bl_idname = "TRIDENT_PT_labels"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Show all loaded labels automatically
        all_labels = scene.trident.all_labels  # Changed: use PropertyGroup
        
        if not all_labels:
            layout.label(text="No headers loaded", icon='INFO')
            layout.label(text="Load CSV headers first")
        else:
            # Get included/excluded counts
            included_labels = [item.name for item in scene.trident.labels if item.name]
            excluded_count = len(all_labels) - len(included_labels)
            
            # Header with counts
            layout.label(text=f"Labels for Analysis ({len(included_labels)}/{len(all_labels)}):")
            
            # Control buttons row
            row = layout.row()
            row.operator("trident.include_all_labels", text="Include All", icon='CHECKMARK')
            row.operator("trident.exclude_all_labels", text="Exclude All", icon='X')
            
            layout.separator()
            
            # Labels box with scrollable list
            box = layout.box()
            if included_labels:
                box.label(text="Included Labels:", icon='CHECKMARK')
                
                # Use template_list for scrollable interface
                box.template_list(
                    "TRIDENT_UL_IncludedLabelsList", "",  
                    scene.trident, "labels",  # Changed: scene.trident (object), "labels" (property name)
                    scene.trident, "labels_index",  # Changed
                    rows=5,
                    maxrows=5
                )
            else:
                box.label(text="No labels selected", icon='ERROR')
                box.label(text="Click 'Include All' to start")
            
            # Show excluded labels (collapsible)
            if excluded_count > 0:
                layout.separator()
                
                # Excluded labels section with scrollable list
                box = layout.box()
                box.label(text=f"Excluded ({excluded_count}):", icon='X')
                
                # Use template_list for scrollable interface
                box.template_list(
                    "TRIDENT_UL_ExcludedLabelsList", "",
                    scene.trident, "excluded_labels",  # Changed
                    scene.trident, "excluded_labels_index",  # Changed
                    rows=3,
                    maxrows=3
                )

            # Plot data
            row = layout.row()
            row.operator("trident.plot_data", text="Plot Data", icon='GRAPH')
            row.enabled = len(included_labels) > 0

class TRIDENT_PT_Visualization(TRIDENT_PT_Base, bpy.types.Panel):
    bl_label = "Visualization"
    bl_idname = "TRIDENT_PT_visualization"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Check if data exists
        data_loaded = scene.trident.data_loaded  # Changed
        
        if not data_loaded:
            layout.label(text="No filtered data", icon='INFO')
            layout.label(text="Load and filter data first")
            return

        # Check if data is plotted
        points_obj = scene.trident.points_obj  # Changed: use stored reference
        if not points_obj or points_obj.name not in bpy.data.objects:
            return

        # Show controls without loading data
        layout.label(text="Color Configuration:")
        row = layout.row()
        row.prop(scene.trident, "color_label", text="Attribute")  # Changed
        
        layout.label(text="Palette:")
        row = layout.row()
        row.prop(scene.trident, "color_palette", text="")  # Changed
        
        row = layout.row()
        row.operator("trident.update_colors", text="Update Colors", icon='COLOR')

        layout.separator()
        layout.label(text="Environment:")
        row = layout.row()
        row.operator("trident.toggle_transparent_environment", text="Transparency", icon='WORLD')

        layout.separator()
        layout.label(text="Legend:")
        
        # Title input for legend
        layout.prop(scene.trident, "legend_title", text="Title")  # Changed
        
        # Legend format buttons
        row = layout.row()
        row.operator("trident.create_square_legend", text="Square (1080x1080)", icon='MESH_PLANE')
        row = layout.row()
        row.operator("trident.create_rectangle_legend", text="Rectangle (1920x1080)", icon='MESH_PLANE')


# Error panel - only shows when C++ module is not available
class TRIDENT_PT_Error(bpy.types.Panel):
    bl_label = "TRIDENT - Error"
    bl_idname = "TRIDENT_PT_error"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TRIDENT"

    @classmethod
    def poll(cls, context):
        # Only show if C++ module is NOT available
        return trident is None

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="C++ module not found", icon='ERROR')
        layout.label(text="Build the module first.")

def register_panel():
    bpy.utils.register_class(TRIDENT_PT_DataInput)
    bpy.utils.register_class(TRIDENT_PT_Labels)
    bpy.utils.register_class(TRIDENT_UL_IncludedLabelsList)
    bpy.utils.register_class(TRIDENT_UL_ExcludedLabelsList)
    bpy.utils.register_class(TRIDENT_PT_Visualization)
    bpy.utils.register_class(TRIDENT_PT_Error)

def unregister_panel():
    bpy.utils.unregister_class(TRIDENT_PT_Error)
    bpy.utils.unregister_class(TRIDENT_PT_Visualization)
    bpy.utils.unregister_class(TRIDENT_PT_Labels)
    bpy.utils.unregister_class(TRIDENT_UL_ExcludedLabelsList)
    bpy.utils.unregister_class(TRIDENT_UL_IncludedLabelsList)
    bpy.utils.unregister_class(TRIDENT_PT_DataInput)