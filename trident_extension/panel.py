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
        layout.prop(scene.trident, "filepath_data", text="")

        # File path input for obs
        layout.label(text="adata.obs:")
        layout.prop(scene.trident, "filepath_obs", text="")

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
        all_labels = scene.trident.all_labels
        
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
                    scene.trident, "labels",  
                    scene.trident, "labels_index",
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
                    scene.trident, "excluded_labels",
                    scene.trident, "excluded_labels_index",
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
    bl_order = 0

    @classmethod
    def poll(cls, context):
        """Only show visualization panel if data is loaded and plotted"""
        if not super().poll(context):
            return False
        s = context.scene
        if not getattr(s.trident, "data_loaded", False):
            return False
        po = s.trident.points_obj
        return bool(po and po.name in bpy.data.objects)

    def draw(self, context):
        layout = self.layout
        pass

class TRIDENT_PT_Color_Configuration(TRIDENT_PT_Base, bpy.types.Panel):
    bl_label = "Color Configuration"
    bl_idname = "TRIDENT_PT_color_configuration"
    bl_parent_id = "TRIDENT_PT_visualization"
    bl_order = 0

    def draw(self, context):
        s = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row()
        row.prop(s.trident, "color_label", text="Label")

        layout.separator()

        row = layout.row()
        row.prop(s.trident, "color_palette", text="Palette")
        
        row = layout.row()
        row.operator("trident.update_colors", text="Update Colors", icon='COLOR')

class TRIDENT_PT_Visualization_Override(TRIDENT_PT_Base, bpy.types.Panel):
    bl_label = "Override Label Treatment"
    bl_idname = "TRIDENT_PT_visualization_override"
    bl_parent_id = "TRIDENT_PT_visualization"
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        s = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        color_label = s.trident.color_label
        if color_label and color_label != 'NONE':
            is_cat = data_loader.get_data_type(s)
            default_treatment = "Categorical" if is_cat else "Continuous"
        else:
            default_treatment = "Unknown"

        col = layout.column(align=True)
        col.label(text=f"Default: {default_treatment}", icon='INFO')
        col.separator()
        col.label(text="Force Treatment As:")
        row = col.row(align=True)
        row.prop(s.trident, "label_treatment_override", expand=True)

class TRIDENT_PT_Customization(TRIDENT_PT_Base, bpy.types.Panel):
    bl_label = "Customization"
    bl_idname = "TRIDENT_PT_customization"
    bl_parent_id = "TRIDENT_PT_visualization"
    bl_order = 2

    def draw(self, context):
        s = context.scene
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.label(text="Points:")
        layout.prop(s.trident, "point_size", text="Size")
        
        
        layout.label(text="Environment:")
        row = layout.row()
        row.operator("trident.toggle_transparent_environment", text="Transparency", icon='WORLD')

        layout.separator()
        layout.label(text="Legend:")
        layout.prop(s.trident, "legend_title", text="Title")
        layout.prop(s.trident, "title_size", text="Title Size")

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
    bpy.utils.register_class(TRIDENT_PT_Visualization_Override)
    bpy.utils.register_class(TRIDENT_PT_Color_Configuration)
    bpy.utils.register_class(TRIDENT_PT_Customization)
    bpy.utils.register_class(TRIDENT_PT_Error)

def unregister_panel():
    bpy.utils.unregister_class(TRIDENT_PT_Error)
    bpy.utils.unregister_class(TRIDENT_PT_Customization)
    bpy.utils.unregister_class(TRIDENT_PT_Color_Configuration)
    bpy.utils.unregister_class(TRIDENT_PT_Visualization_Override)
    bpy.utils.unregister_class(TRIDENT_PT_Visualization)
    bpy.utils.unregister_class(TRIDENT_PT_Labels)
    bpy.utils.unregister_class(TRIDENT_UL_ExcludedLabelsList)
    bpy.utils.unregister_class(TRIDENT_UL_IncludedLabelsList)
    bpy.utils.unregister_class(TRIDENT_PT_DataInput)