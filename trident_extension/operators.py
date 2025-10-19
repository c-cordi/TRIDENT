import bpy
import os
import numpy as np

from . import data_loader
from . import geometry_nodes
from . import scene_environment
from .properties import TRIDENT_LabelItem

trident = data_loader.get_trident_module()
cpp_loader = data_loader.get_cpp_loader()

class TRIDENT_OT_AddLabel(bpy.types.Operator):
    bl_idname = "trident.add_label"
    bl_label = "Add Label"

    def execute(self, context):
        context.scene.trident.labels.add()
        return {'FINISHED'}

class TRIDENT_OT_RemoveLabel(bpy.types.Operator):
    bl_idname = "trident.remove_label"
    bl_label = "Remove Label"
    index: bpy.props.IntProperty()

    def execute(self, context):
        labels = context.scene.trident.labels
        if 0 <= self.index < len(labels):
            labels.remove(self.index)
        return {'FINISHED'}

class TRIDENT_OT_ExcludeSingleLabel(bpy.types.Operator):
    bl_idname = "trident.exclude_single_label"
    bl_label = "Exclude Label"
    bl_description = "Exclude this label from analysis"
    
    label_name: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        selected_labels = scene.trident.labels
        excluded_labels = scene.trident.excluded_labels
        
        # Find and remove from included labels
        for i, item in enumerate(selected_labels):
            if item.name == self.label_name:
                selected_labels.remove(i)
                
                # Add to excluded labels collection
                excluded_item = excluded_labels.add()
                excluded_item.name = self.label_name
                
                self.report({'INFO'}, f"Excluded '{self.label_name}'")
                return {'FINISHED'}
        
        self.report({'WARNING'}, f"Label '{self.label_name}' not found")
        return {'CANCELLED'}

class TRIDENT_OT_IncludeSingleLabel(bpy.types.Operator):
    bl_idname = "trident.include_single_label"
    bl_label = "Include Label"
    bl_description = "Include this label in analysis"
    
    label_name: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        selected_labels = scene.trident.labels
        excluded_labels = scene.trident.excluded_labels
        
        # Check if already included
        for item in selected_labels:
            if item.name == self.label_name:
                self.report({'WARNING'}, f"'{self.label_name}' already included")
                return {'CANCELLED'}
        
        # Add to included labels
        new_item = selected_labels.add()
        new_item.name = self.label_name
        
        # Remove from excluded labels collection
        for i, item in enumerate(excluded_labels):
            if item.name == self.label_name:
                excluded_labels.remove(i)
                break
        
        self.report({'INFO'}, f"Included '{self.label_name}'")
        return {'FINISHED'}

class TRIDENT_OT_IncludeAllLabels(bpy.types.Operator):
    bl_idname = "trident.include_all_labels"
    bl_label = "Include All Labels"
    bl_description = "Include all available labels in analysis"

    def execute(self, context):
        scene = context.scene
        all_labels = scene.trident.all_labels
        selected_labels = scene.trident.labels
        excluded_labels = scene.trident.excluded_labels
        
        # Clear both collections
        selected_labels.clear()
        excluded_labels.clear()
        
        # Add all labels to included
        for label_item in all_labels:
            new_item = selected_labels.add()
            new_item.name = label_item.name
        
        self.report({'INFO'}, f"Included all {len(all_labels)} labels")
        return {'FINISHED'}

class TRIDENT_OT_ExcludeAllLabels(bpy.types.Operator):
    bl_idname = "trident.exclude_all_labels"
    bl_label = "Exclude All Labels"
    bl_description = "Exclude all labels from analysis"

    def execute(self, context):
        scene = context.scene
        all_labels = scene.trident.all_labels
        selected_labels = scene.trident.labels
        excluded_labels = scene.trident.excluded_labels
        
        # Clear both collections
        selected_labels.clear()
        excluded_labels.clear()
        
        # Add all labels to excluded
        for label_item in all_labels:
            new_item = excluded_labels.add()
            new_item.name = label_item.name
        
        self.report({'INFO'}, "Excluded all labels")
        return {'FINISHED'}

class TRIDENT_OT_LoadData(bpy.types.Operator):
    bl_idname = "trident.load_data"
    bl_label = "Load CSV Headers"
    bl_description = "Load available labels from obs file"

    def execute(self, context):
        if trident is None:
            self.report({'ERROR'}, "C++ module not available")
            return {'CANCELLED'}

        filepath_obs = context.scene.trident.filepath_obs

        if not filepath_obs:
            self.report({'ERROR'}, "Please specify obs file path")
            return {'CANCELLED'}

        if not os.path.exists(filepath_obs):
            self.report({'ERROR'}, f"File not found: {filepath_obs}")
            return {'CANCELLED'}

        try:
            # Just read the header line to get available labels
            with open(filepath_obs, 'r') as f:
                header_line = f.readline().strip()
                headers = [h.strip().strip('"') for h in header_line.split(',')]
            
            scene = context.scene
        
            # Populate all_labels
            scene.trident.all_labels.clear()
            for header in headers:
                item = scene.trident.all_labels.add()
                item.name = header
            
            # Pre-select ALL labels (exclusion-based filtering)
            scene.trident.labels.clear()
            scene.trident.excluded_labels.clear()
            for header in headers:
                item = scene.trident.labels.add()
                item.name = header
            
            self.report({'INFO'}, f"Loaded {len(headers)} labels (all preselected)")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read headers: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class TRIDENT_OT_PlotData(bpy.types.Operator):
    bl_idname = "trident.plot_data"
    bl_label = "Plot Data"

    def execute(self, context):
        import numpy as np

        scene = context.scene
        selected_labels = [item.name for item in scene.trident.labels if item.name]
        
        if not selected_labels:
            self.report({'WARNING'}, "No labels selected for analysis")
            return {'CANCELLED'}
        
        filepath_data = scene.trident.filepath_data
        filepath_obs = scene.trident.filepath_obs
        
        if not filepath_data or not os.path.exists(filepath_data):
            self.report({'ERROR'}, "Invalid obsm file path")
            return {'CANCELLED'}
            
        if not filepath_obs or not os.path.exists(filepath_obs):
            self.report({'ERROR'}, "Invalid obs file path")
            return {'CANCELLED'}

        # C++ HIGH-PERFORMANCE DATA LOADING

        # Load spatial coordinates - typically 2D/3D position data
        # Returns: (numpy array, category mappings, is_categorical flags)
        data_array, data_map, data_cat = cpp_loader.load_csv(filepath_data)
        
        # Load observation metadata (obs) with only user-selected labels
        obs_array, cat_map, obs_cat = cpp_loader.load_csv(filepath_obs, selected_labels)
        
        # Store categorical mappings: {label_name: {category_str: int_id}}
        cat_map = dict(zip(selected_labels, cat_map))
        data_loader.set_cat_map(cat_map, scene)
        data_loader.set_obs_map(selected_labels, obs_cat, scene)

        # Merge coordinates + metadata horizontally (column-wise)
        # Result shape: [n_points, 3 + n_labels] where first 3 cols are XYZ
        merged_array = cpp_loader.merge_data(data_array, obs_array)
        
        # Cache the results in Blender scene for visualization
        data_loader.set_data_cache(merged_array, scene)
        data_loader.set_label_cache(selected_labels, scene)

        self.report({'INFO'}, f"Loaded data with {len(selected_labels)} labels ({merged_array.shape[0]} points)")

        trident_data_cache = data_loader.get_data_cache()
        
        if trident_data_cache is None:
            self.report({'ERROR'}, "No data loaded. Please load data first.")
            return {'CANCELLED'}

        # Clear scene
        for o in list(context.scene.objects):
            bpy.data.objects.remove(o, do_unlink=True)

        # Coords
        if trident_data_cache.size == 0:
            self.report({'ERROR'}, "No points to plot.")
            return {'CANCELLED'}

        coords = trident_data_cache[:, :3].astype(np.float32)
        n_points = coords.shape[0]

        # Create the instanced object and store reference
        inst_obj = scene.trident.instance_obj
        if inst_obj is None or not inst_obj.name in bpy.data.objects:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=0, radius=0.05, location=(0, 0, 0))
            inst_obj = context.view_layer.objects.active
            inst_obj.name = "TRIDENT_Instance"
            
            # Store reference in scene
            scene.trident.instance_obj = inst_obj
            
            bpy.context.view_layer.objects.active = inst_obj
            bpy.ops.object.shade_smooth()
        
        inst_obj.hide_viewport = True
        inst_obj.hide_render = True

        # Create mesh from coords and embed label_id attribute
        mesh = bpy.data.meshes.new("TRIDENT_Points_Mesh")
        mesh.from_pydata(coords.tolist(), [], [])

        trident_label_cache = data_loader.get_label_cache()

        n_cols = trident_data_cache.shape[1]
        n_extra = max(0, n_cols - 3)

        if n_extra and trident_label_cache:
            names = list(trident_label_cache)

            use_count = min(len(names), n_extra)
            if len(names) != n_extra:
                self.report({'WARNING'},
                            f"Label names ({len(names)}) != extra columns ({n_extra}); using first {use_count}.")

            for j in range(use_count):
                name = names[j]
                col = trident_data_cache[:, 3 + j]
                
                if np.issubdtype(col.dtype, np.number):
                    vals = np.asarray(col, dtype=np.int32)
                else:
                    as_str = col.astype(str)
                    uniques, inverse = np.unique(as_str, return_inverse=True)
                    vals = inverse.astype(np.int32)

                attr = mesh.attributes.get(name)
                if attr is not None and (attr.data_type != 'INT' or attr.domain != 'POINT'):
                    mesh.attributes.remove(attr)
                    attr = None
                if attr is None:
                    attr = mesh.attributes.new(name=name, type='INT', domain='POINT')
                    
                vals_view = np.asarray(vals[:n_points], dtype=np.int32)
                try:
                    attr.data.foreach_set("value", vals_view)
                except Exception:
                    for idx, v in enumerate(vals_view):
                        attr.data[idx].value = int(v)

        points_obj = bpy.data.objects.new("TRIDENT_Points", mesh)
        context.collection.objects.link(points_obj)
        
        # Store reference
        scene.trident.points_obj = points_obj

        # Set correct origin for the geometry
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        with context.temp_override(
            object=points_obj,
            active_object=points_obj,
            selected_objects=[points_obj],
            selected_editable_objects=[points_obj],
        ):
            bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')

        # Geometry Nodes setup (Object Info → Instance on Points → Realize → Output)
        max_color = trident_data_cache[:, 3].max() if trident_data_cache.shape[1] > 3 else 10
        geometry_nodes.setup_geometry_nodes(points_obj, inst_obj, context, max_color)
        scene_environment.setup_scene_environment(context)

        # Store initial color label for legend use
        trident_label_cache = data_loader.get_label_cache()
        if trident_label_cache:
            context.scene.trident.current_color_label = trident_label_cache[0]
        
        bpy.context.space_data.shading.type = 'MATERIAL'
        # Set camera perspective
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.region_3d.view_perspective = 'CAMERA'
                        break
                break

        self.report({'INFO'}, f"Created point cloud with {n_points} points (instanced & realized).")
        return {'FINISHED'}

class TRIDENT_OT_UpdateColors(bpy.types.Operator):
    bl_idname = "trident.update_colors"
    bl_label = "Update Point Colors"
    bl_description = "Update the color attribute and palette used for point visualization"

    def execute(self, context):
        scene = context.scene
        color_label = scene.trident.color_label
        palette = scene.trident.color_palette

        try:
            context.scene.trident.current_color_label = color_label
        except:
            trident_label_cache = data_loader.get_label_cache(scene=scene)
            if trident_label_cache:
                context.scene.trident.current_color_label = trident_label_cache[0]
            else:
                context.scene.trident.current_color_label = ""
        
        trident_data_cache = data_loader.get_data_cache(scene)
        trident_label_cache = data_loader.get_label_cache(scene)
        
        # Fix the NaN handling issue
        if not color_label or color_label == 'NONE':
            self.report({'WARNING'}, "No color label selected")
            return {'CANCELLED'}
        
        if trident_data_cache is None or trident_label_cache is None:
            self.report({'ERROR'}, "No data loaded. Plot data first.")
            return {'CANCELLED'}
        
        # Calculate max color with proper NaN handling
        if color_label in trident_label_cache:
            color_index = trident_label_cache.index(color_label)
            column_data = trident_data_cache[:, 3 + color_index]
            
            # Filter out NaN values
            valid_data = column_data[~np.isnan(column_data)]
            
            if len(valid_data) > 0:
                max_color = float(valid_data.max())
                print(f"[DEBUG] Color Index: {color_index}, Color Label: {color_label}")
                print(f"[DEBUG] Valid data points: {len(valid_data)}/{len(column_data)}")
                print(f"[DEBUG] Max Color: {max_color}")
            else:
                max_color = 1.0
                self.report({'WARNING'}, f"No valid data found for {color_label}")
        else:
            self.report({'ERROR'}, f"Label '{color_label}' not found in {trident_label_cache}")
            return {'CANCELLED'}

        # Find the TRIDENT points object
        points_obj = scene.trident.points_obj
        if not points_obj or points_obj.name not in bpy.data.objects:
            self.report({'ERROR'}, "TRIDENT_Points object not found. Plot data first.")
            return {'CANCELLED'}
        
        # Use stored reference
        inst_obj = scene.trident.instance_obj
        if inst_obj and inst_obj.name in bpy.data.objects:
            geometry_nodes.setup_instance_material(inst_obj, scene, max_label=max_color, palette_name=palette, points_obj=points_obj)
        else:
            self.report({'WARNING'}, "Instance object not found")
        
        # Find the geometry nodes modifier
        gn_mod = None
        for mod in points_obj.modifiers:
            if mod.type == 'NODES' and mod.name in ["TRIDENT_GeoNodes", "InstancePoints"]:
                gn_mod = mod
                break
        
        if not gn_mod or not gn_mod.node_group:
            self.report({'ERROR'}, "Geometry nodes modifier not found")
            return {'CANCELLED'}
        
        # Update the named attribute node
        tree = gn_mod.node_group
        attr_node = None

        for node in tree.nodes:
            if hasattr(node, 'bl_idname') and node.bl_idname == 'GeometryNodeInputNamedAttribute':
                attr_node = node
                break
            elif hasattr(node, 'inputs') and len(node.inputs) > 0:
                if hasattr(node.inputs[0], 'name') and 'Name' in node.inputs[0].name:
                    attr_node = node
                    break
                    
        if attr_node:
            attr_node.inputs[0].default_value = color_label
            self.report({'INFO'}, f"Updated color attribute to: {color_label}")
        else:
            self.report({'WARNING'}, "Named attribute node not found in geometry nodes")
            return {'CANCELLED'}
        
        # Find ShaderNodeMapRange and change max
        map_range_node = None
        for node in tree.nodes:
            if hasattr(node, 'bl_idname') and node.bl_idname == 'ShaderNodeMapRange':
                map_range_node = node
                break
        
        data_type = data_loader.get_data_type(scene)

        if map_range_node:
            if max_color < 32:
                map_range_node.inputs['From Max'].default_value = max_color
            else:
                if data_type == True:
                    map_range_node.inputs['From Max'].default_value = 32
                else:
                    map_range_node.inputs['From Max'].default_value = max_color
            self.report({'INFO'}, f"Updated Map Range max to: {max_color}")
        else:
            self.report({'WARNING'}, "Map Range node not found in geometry nodes")
        
        # Final success message
        self.report({'INFO'}, f"Updated colors: {color_label} with {palette} palette (max: {max_color})")
        
        return {'FINISHED'}

class TRIDENT_OT_ToggleTransparentEnvironment(bpy.types.Operator):
    bl_idname = "trident.toggle_transparent_environment"
    bl_label = "Toggle Transparent Environment"
    bl_description = "Toggle the transparent environment setup for rendering"

    def execute(self, context):
        scene = context.scene
        if scene.trident.environment_transparent:
            scene_environment.disable_transparent_environment()
            scene.trident.environment_transparent = False
            self.report({'INFO'}, "Disabled transparent environment")
        else:
            scene_environment.set_transparent_environment()
            scene.trident.environment_transparent = True
            self.report({'INFO'}, "Enabled transparent environment")

        return {'FINISHED'}

class TRIDENT_OT_CreateSquareLegend(bpy.types.Operator):
    bl_idname = "trident.create_square_legend"
    bl_label = "Create Square Legend"
    bl_description = "Create square format legend (1080x1080)"

    def execute(self, context):
        # Import the legend_setup module and create legend
        from . import legend_setup
        legend_setup.create_square_legend(context)
        
        self.report({'INFO'}, "Created square legend setup")
        return {'FINISHED'}

class TRIDENT_OT_CreateRectangleLegend(bpy.types.Operator):
    bl_idname = "trident.create_rectangle_legend"
    bl_label = "Create Rectangle Legend"
    bl_description = "Create rectangle format legend (1920x1080)"

    def execute(self, context):
        
        # Import the legend_setup module and create legend
        from . import legend_setup
        legend_setup.create_rectangle_legend(context)
        
        self.report({'INFO'}, "Created rectangle legend setup")
        return {'FINISHED'}


def register_operators():
    bpy.utils.register_class(TRIDENT_OT_AddLabel)
    bpy.utils.register_class(TRIDENT_OT_RemoveLabel)
    bpy.utils.register_class(TRIDENT_OT_LoadData)
    bpy.utils.register_class(TRIDENT_OT_ExcludeSingleLabel)
    bpy.utils.register_class(TRIDENT_OT_IncludeSingleLabel)
    bpy.utils.register_class(TRIDENT_OT_IncludeAllLabels)
    bpy.utils.register_class(TRIDENT_OT_ExcludeAllLabels)
    bpy.utils.register_class(TRIDENT_OT_ToggleTransparentEnvironment)
    bpy.utils.register_class(TRIDENT_OT_CreateSquareLegend)
    bpy.utils.register_class(TRIDENT_OT_CreateRectangleLegend)
    bpy.utils.register_class(TRIDENT_OT_PlotData)
    bpy.utils.register_class(TRIDENT_OT_UpdateColors)

def unregister_operators():
    bpy.utils.unregister_class(TRIDENT_OT_LoadData)
    bpy.utils.unregister_class(TRIDENT_OT_RemoveLabel)
    bpy.utils.unregister_class(TRIDENT_OT_AddLabel)
    bpy.utils.unregister_class(TRIDENT_OT_ExcludeAllLabels)
    bpy.utils.unregister_class(TRIDENT_OT_IncludeAllLabels)
    bpy.utils.unregister_class(TRIDENT_OT_IncludeSingleLabel)
    bpy.utils.unregister_class(TRIDENT_OT_ExcludeSingleLabel)
    bpy.utils.unregister_class(TRIDENT_OT_ToggleTransparentEnvironment)
    bpy.utils.unregister_class(TRIDENT_OT_CreateRectangleLegend)
    bpy.utils.unregister_class(TRIDENT_OT_CreateSquareLegend)
    bpy.utils.unregister_class(TRIDENT_OT_PlotData)
    bpy.utils.unregister_class(TRIDENT_OT_UpdateColors)
    

