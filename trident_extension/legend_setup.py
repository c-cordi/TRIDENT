import bpy
from . import data_loader, geometry_nodes

def create_square_legend(context):
    """Create square format legend scene with overlay compositing"""
    import numpy as np
    trident = context.scene.trident
    color_label = trident.current_color_label
    
    if not color_label:
        print("[TRIDENT] No color label selected.")
    
    if data_loader.get_data_type(context.scene) == True:
        trident_data_cache = data_loader.get_data_cache(scene=context.scene)
        trident_label_cache = data_loader.get_label_cache(scene=context.scene)
        color_index = trident_label_cache.index(color_label)
        column_data = trident_data_cache[:, 3 + color_index]
        unique_values = len(sorted(set(column_data[~np.isnan(column_data)])))

        if unique_values > 10: # Force rectangle for too many categories
            create_rectangle_legend(context)
        else:
            create_legend_scene(context, format_type="square")
    else:
        create_legend_scene(context, format_type="square")

def create_rectangle_legend(context):
    """Create rectangle format legend scene with overlay compositing"""
    create_legend_scene(context, format_type="rectangle")

def create_legend_scene(context, format_type="square"):
    """Create legend scene with orthographic camera and compositing overlay"""
    
    # Store reference to main scene
    main_scene = context.scene
    main_scene_name = main_scene.name
    
    # Create or get legend scene
    legend_scene_name = f"TRIDENT_Legend_{format_type.title()}"
    legend_scene = bpy.data.scenes.get(legend_scene_name)
    
    if legend_scene:
        # Clear existing legend scene
        bpy.data.scenes.remove(legend_scene, do_unlink=True)
    
    # Create new legend scene
    legend_scene = bpy.data.scenes.new(legend_scene_name)
    
    # Set resolution based on format
    if format_type == "square":
        main_scene.render.resolution_x = 1080
        main_scene.render.resolution_y = 1080
        legend_scene.render.resolution_x = 1080
        legend_scene.render.resolution_y = 1080

        camera = main_scene.camera
        if camera:
            camera.data.lens = 50
            camera.location = (-32.412, 31.3021, 9.39782)
    else:
        main_scene.render.resolution_x = 1920
        main_scene.render.resolution_y = 1080
        legend_scene.render.resolution_x = 1920
        legend_scene.render.resolution_y = 1080

        camera = main_scene.camera
        if camera:
            camera.data.lens = 31
            camera.location = (-39.9231, 24.1237, 9.39782)

    # Enable transparent background for legend scene
    legend_scene.render.film_transparent = True
    
    # Create orthographic camera pointing downwards
    with context.temp_override(scene=legend_scene):
        bpy.ops.object.camera_add(
            location=(0, 0, 10),
            rotation=(0, 0, 0)
        )
        camera = context.active_object
        camera.name = "Legend_Camera"
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = 20
        legend_scene.camera = camera
    
    # Create legend content
    create_legend_content(context, legend_scene, main_scene, format_type)
    
    # Setup compositing for overlay
    setup_legend_compositing(main_scene, legend_scene)

def create_legend_content(context, legend_scene, main_scene, format_type):
    """Create the actual legend content (title, labels, gradient)"""
    
    # Switch to legend scene context
    with context.temp_override(scene=legend_scene):
        
        # Get legend title from main scene
        trident = main_scene.trident
        title = trident.legend_title or 'TRIDENT Visualization'
        
        # Create title text
        create_title_text(context, title, format_type)
        
        # Get current color label from stored string property
        color_label = trident.current_color_label
        
        # Fallback to label cache if no stored label
        if not color_label:
            trident_label_cache = data_loader.get_label_cache(scene=main_scene)
            if trident_label_cache:
                color_label = trident_label_cache[0]
            else:
                print("[TRIDENT] Warning: No color labels available for legend")
                return

        if color_label and color_label != 'NONE':
            data_type = data_loader.get_data_type(main_scene)
            
            if data_type:
                create_categorical_legend(context, main_scene, legend_scene, color_label, format_type)
            else:
                create_continuous_legend(context, main_scene, format_type)

def create_title_text(context, title, format_type):
    """Create title text object"""
    
    # Create text object
    if format_type == "square":
        bpy.ops.object.text_add(location=(0, 9, 0))
    else:
        bpy.ops.object.text_add(location=(-3, 5, 0))
    title_obj = context.active_object
    title_obj.name = "Title"
    title_obj.data.body = title
    
    # Configure text properties
    title_obj.data.align_x = 'CENTER'
    title_obj.data.align_y = 'CENTER'
    title_obj.data.size = 0.7 if format_type == "square" else 0.5
    
    # Create or get stored material reference
    scene = context.scene
    mat = scene.trident.legend_title_material
    if not mat or mat.name not in bpy.data.materials:
        mat = bpy.data.materials.new(name="Legend_Title_Material")
        scene.trident.legend_title_material = mat
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
    
    # Simple emission material for text
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = (0, 0, 0, 1)
    emission.inputs['Strength'].default_value = 1.0
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    title_obj.data.materials.append(mat)

def create_categorical_legend(context, main_scene, legend_scene, color_label, format_type):
    """Create categorical legend with labeled spheres"""
    import numpy as np
    import json
    
    # Get categorical mappings from scene storage
    trident = main_scene.trident
    cat_map_json = trident.cat_map_json or '{}'

    if not cat_map_json or cat_map_json == '{}':
        print(f"[TRIDENT] Warning: No categorical mappings found")
        return
    
    try:
        cat_maps = json.loads(cat_map_json)
    except json.JSONDecodeError:
        print(f"[TRIDENT] Warning: Invalid categorical mapping JSON")
        return
    
    print(f"[TRIDENT] Creating categorical legend for label: {color_label}")
    print(f"[TRIDENT] Available categorical maps: {list(cat_maps.keys())}")
    
    # Check if the current color label has categorical mappings
    if color_label not in cat_maps:
        print(f"[TRIDENT] Warning: {color_label} not found in categorical mappings")
        return
    
    # Get the category mapping for this label
    label_categories = cat_maps[color_label] 
    
    # Get unique categories from the data
    trident_data_cache = data_loader.get_data_cache(scene=main_scene)
    trident_label_cache = data_loader.get_label_cache(scene=main_scene)

    if trident_data_cache is None or not trident_label_cache:
        print(f"[TRIDENT] Warning: No data cache or label cache available")
        return
    
    if color_label not in trident_label_cache:
        print(f"[TRIDENT] Warning: {color_label} not found in label cache: {trident_label_cache}")
        return
    
    # Get unique values from the actual data
    color_index = trident_label_cache.index(color_label)
    column_data = trident_data_cache[:, 3 + color_index]
    unique_values = sorted(set(column_data[~np.isnan(column_data)]))
    
    print(f"[TRIDENT] Found {len(unique_values)} unique values in data: {unique_values}")
    print(f"[TRIDENT] Category mappings for {color_label}: {label_categories}")
    
    # Create reverse mapping: id -> category_name
    id_to_category = {idx: category for category, idx in label_categories.items()}
    
    # Position settings
    start_y = 8 if format_type == "square" else 4
    spacing = 0.7 if format_type == "square" else 0.7
    x_pos = 4.5 if format_type == "square" else 2
    x_title = 7 if format_type == "square" else 5
    
    # Create sphere instance object (similar to main scene)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.15, location=(0, 0, -10))
    legend_sphere = context.active_object
    legend_sphere.name = "Legend_Sphere_Instance"
    legend_sphere.hide_viewport = True
    legend_sphere.hide_render = True
    
    # Apply smooth shading
    bpy.ops.object.shade_smooth()

    # Add Sun pointing downwards for lighting
    bpy.ops.object.light_add(type='SUN', 
                             radius=1, 
                             align='WORLD', 
                             location=(0, 0, 0), 
                             scale=(1, 1, 1), 
                             rotation=(0, 0, 0))
    sun = context.active_object
    sun.data.energy = 4.7
    sun.data.specular_factor = 0.0

    # Get material from stored reference instead of name lookup
    main_instance = main_scene.trident.instance_obj
    if main_instance and main_instance.name in bpy.data.objects and main_instance.data.materials:
        legend_sphere.data.materials.append(main_instance.data.materials[0])
    else:
        print(f"[TRIDENT] Warning: Could not find TRIDENT_Instance material")

    # Get max_color from the data
    max_color = len(unique_values) - 1 if unique_values else 0
    
    # Create title for legend
    bpy.ops.object.text_add(location=(x_title, start_y + 0.7, 0))
    text_obj = context.active_object
    text_obj.name = f"Legend_Title"
    text_obj.data.body = color_label
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    text_obj.data.size = 0.5 if format_type == "square" else 0.4
    title_obj = text_obj

    mat_title = legend_scene.trident.legend_title_material
    if mat_title and mat_title.name in bpy.data.materials:
        text_obj.data.materials.append(mat_title)

    # Create legend entries for each unique value found in data
    for i, value_id in enumerate(unique_values):
        if max_color < 28:
            text_size = 0.4
            spacing = 0.6
            if i > 13:
                y_pos = start_y - ((i - 14) * spacing)
                x_pos = 6
            else:
                y_pos = start_y - (i * spacing)
        elif max_color >= 28 and max_color < 39:
            text_size = 0.35
            spacing = 0.55
            if i > 19:
                y_pos = start_y - ((i - 20) * spacing)
                x_pos = 5
            else:
                y_pos = start_y - (i * spacing)
        elif max_color > 39:
            text_size = 0.3
            spacing = 0.5
            if i > 19 and i <= 39:
                y_pos = start_y - ((i - 20) * spacing)
                x_pos = 3.5
            elif i > 39:
                y_pos = start_y - ((i - 40) * spacing)
                x_pos = 7
            else:
                y_pos = start_y - (i * spacing)
                x_pos = 0

        # Get category name for this ID
        category_name = id_to_category.get(int(value_id), f"Unknown_{int(value_id)}")
        
        print(f"[TRIDENT] Creating legend entry {i}: ID={value_id}, Category={category_name}")
        
        # Create text for label
        bpy.ops.object.text_add(location=(x_pos + 0.5, y_pos, 0))
        text_obj = context.active_object
        text_obj.name = f"Legend_Label_{i}"
        text_obj.data.body = category_name
        text_obj.data.align_x = 'LEFT'
        text_obj.data.align_y = 'CENTER'
        text_obj.data.size = 0.5 if format_type == "square" else text_size
        
        # Create material for label text
        text_mat = bpy.data.materials.new(name=f"Legend_Text_{i}")
        text_mat.use_nodes = True
        text_mat.node_tree.nodes.clear()
        
        nodes = text_mat.node_tree.nodes
        links = text_mat.node_tree.links
        
        emission = nodes.new(type='ShaderNodeEmission')
        emission.inputs['Color'].default_value = (0, 0, 0, 1)
        emission.inputs['Strength'].default_value = 1.0
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        links.new(emission.outputs['Emission'], output.inputs['Surface'])
        
        text_obj.data.materials.append(text_mat)
        
        # Create sphere with specific value AND max_color
        create_legend_sphere(context, legend_sphere, (x_pos, y_pos, 0), value_id, i, max_color)
    
    title_x = title_obj.location.x

    # Deselect all objects first
    for obj in legend_scene.objects:
        obj.select_set(False)

    # Select all relevant objects
    for obj in legend_scene.objects:
        if obj.name.startswith("Legend_Point") or obj.name.startswith("Legend_Label"):
            obj.select_set(True)

    # Set the legend scene as active
    active_scene = bpy.context.window.scene
    bpy.context.window.scene = legend_scene

    # Get max x dimension to center legend
    x_max = max([obj.dimensions.x for obj in legend_scene.objects if obj.select_get()])

    bpy.ops.transform.translate(
        value=((2 - x_max/2, 0, 0)),
        orient_type='GLOBAL'
    )

    bpy.context.window.scene = active_scene
    for obj in legend_scene.objects:
        obj.select_set(False)

    print(f"[TRIDENT] Created {len(unique_values)} legend entries")

def create_legend_sphere(context, instance_sphere, location, value_id, index, max_color):
    """Create a sphere for legend with specific categorical value"""
    
    # Create a single vertex mesh at the location
    mesh = bpy.data.meshes.new(f"Legend_Point_{index}")
    mesh.from_pydata([location], [], [])
    
    # Add the categorical attribute with the specific value
    attr = mesh.attributes.new(name="Color_Value", type='INT', domain='POINT')
    attr.data[0].value = int(value_id)
    
    # Create object
    points_obj = bpy.data.objects.new(f"Legend_Points_{index}", mesh)
    context.collection.objects.link(points_obj)
    
    # Setup geometry nodes for instancing WITH max_color
    setup_legend_geometry_nodes(points_obj, instance_sphere, value_id, max_color)

def setup_legend_geometry_nodes(points_obj, inst_obj, value_id, max_color=10):
    """Setup geometry nodes for legend sphere instancing"""
    
    mod = points_obj.modifiers.new(name=f"LegendInstance", type='NODES')
    if not mod.node_group:
        mod.node_group = bpy.data.node_groups.new(name=f"Legend_GeoNodes_{value_id}", type='GeometryNodeTree')

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

    # Create nodes with proper positioning
    n_in = nodes.new(type='NodeGroupInput')
    n_in.location = (-600, 0)
    
    n_out = nodes.new(type='NodeGroupOutput')
    n_out.location = (600, 0)
    
    n_iop = nodes.new(type='GeometryNodeInstanceOnPoints')
    n_iop.location = (-200, 0)
    
    n_obj = nodes.new(type='GeometryNodeObjectInfo')
    n_obj.location = (-400, -200)
    
    n_attr = nodes.new(type='GeometryNodeInputNamedAttribute')
    n_attr.location = (-400, 200)
    
    n_map = nodes.new(type='ShaderNodeMapRange')
    n_map.location = (100, 200)
    
    n_store = nodes.new(type='GeometryNodeStoreNamedAttribute')
    n_store.location = (300, 0)
    
    n_real = nodes.new(type='GeometryNodeRealizeInstances')
    n_real.location = (400, 0)

    # Configure nodes
    n_obj.inputs['As Instance'].default_value = True
    n_obj.inputs['Object'].default_value = inst_obj
    n_attr.inputs[0].default_value = "Color_Value"
    n_attr.data_type = 'INT'
    
    # Configure Map Range node
    n_map.data_type = 'FLOAT'
    n_map.inputs['From Min'].default_value = 0.0
    n_map.inputs['From Max'].default_value = max_color
    n_map.inputs['To Min'].default_value = 0.0
    n_map.inputs['To Max'].default_value = 1.0
    
    n_store.data_type = 'FLOAT'
    n_store.domain = 'INSTANCE'
    n_store.inputs['Name'].default_value = "Color"

    # Create connections
    links.new(n_in.outputs["Geometry"], n_iop.inputs['Points'])
    links.new(n_obj.outputs['Geometry'], n_iop.inputs['Instance'])
    links.new(n_iop.outputs['Instances'], n_store.inputs['Geometry'])
    links.new(n_attr.outputs['Attribute'], n_map.inputs['Value'])
    links.new(n_map.outputs['Result'], n_store.inputs['Value'])
    links.new(n_store.outputs['Geometry'], n_real.inputs['Geometry'])
    links.new(n_real.outputs['Geometry'], n_out.inputs["Geometry"])

def create_continuous_legend(context, main_scene, format_type):
    """Create continuous legend with gradient plane"""
    
    # Create a plane for gradient display
    bpy.ops.mesh.primitive_plane_add(
        size=1.5 if format_type == "square" else 1,
        location=(5 if format_type == "rectangle" else 7, 
                  0 if format_type == "rectangle" else 5, 0),
        rotation=(0, 0, 1.5708)
    )
    gradient_plane = context.active_object
    gradient_plane.name = "Legend_Gradient"
    gradient_plane.scale = (3, 0.5, 1) if format_type == "square" else (4.5, 0.8, 1)
    
    # Create gradient material
    create_gradient_material(gradient_plane, main_scene)
    
    # Add min/max labels
    create_gradient_labels(context, main_scene, format_type)

def create_gradient_material(plane_obj, main_scene):
    """Create gradient material matching the main color ramp"""
    
    # Get the palette and create gradient material
    trident = main_scene.trident
    palette_name = trident.color_palette or 'Viridis'
    colors = geometry_nodes.get_palette_colors(palette_name)
    
    # Create material
    mat = bpy.data.materials.new(name="Legend_Gradient_Material")
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Create nodes
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-400, 0)

    separate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
    separate_xyz.location = (-400, 0)
    
    colorramp = nodes.new(type='ShaderNodeValToRGB')
    colorramp.location = (-200, 0)
    
    emission = nodes.new(type='ShaderNodeEmission')
    emission.location = (0, 0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    
    # Setup color ramp with palette colors
    setup_legend_colorramp(colorramp, colors)
    
    # Connect nodes
    links.new(tex_coord.outputs['Generated'], separate_xyz.inputs['Vector'])
    links.new(separate_xyz.outputs['X'], colorramp.inputs['Fac'])
    links.new(colorramp.outputs['Color'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    # Assign material
    plane_obj.data.materials.append(mat)

def setup_legend_colorramp(colorramp_node, colors):
    """Setup color ramp for legend gradient"""
    colorramp = colorramp_node.color_ramp
    colorramp.interpolation = 'LINEAR'
    
    colorramp.elements[0].color = colors[0]
    colorramp.elements[1].color = colors[-1]
    
    # Add color stops
    for i, color in enumerate(colors):
        position = i / (len(colors) - 1) if len(colors) > 1 else 0.0
        elem = colorramp.elements.new(position)
        elem.color = color

def create_gradient_labels(context, main_scene, format_type):
    """Create min/max labels for gradient legend"""
    import numpy as np
    
    if format_type == "rectangle":
        camera = main_scene.camera
        if camera:
            camera.location = (-36.7207, 27.2434, 9.39782)

    # Get data range
    trident_data_cache = data_loader.get_data_cache(scene=main_scene)
    trident = main_scene.trident
    color_label = trident.current_color_label
    trident_label_cache = data_loader.get_label_cache(scene=main_scene)

    if trident_data_cache is not None and color_label in trident_label_cache:
        color_index = trident_label_cache.index(color_label)
        column_data = trident_data_cache[:, 3 + color_index]
        valid_data = column_data[~np.isnan(column_data)]
        print(set(valid_data))
        if len(valid_data) > 0:
            min_val = float(valid_data.min())
            max_val = float(valid_data.max())
        else:
            min_val, max_val = 0.0, 1.0
    else:
        min_val, max_val = 0.0, 1.0

    # Position settings
    x_pos = 5.6 if format_type == "rectangle" else 7.6
    if format_type == "rectangle":
        y_start = 0
        x_title = 5
    else:
        y_start = 5
        x_title = 7

    # Legend title
    bpy.ops.object.text_add(location=(x_title, y_start + 3, 0))
    title_text = context.active_object
    title_text.name = "Legend_Title"
    title_text.data.body = color_label
    title_text.data.align_x = 'CENTER'
    title_text.data.align_y = 'CENTER'
    title_text.data.size = 0.5 if format_type == "square" else 0.5

    # Min label
    bpy.ops.object.text_add(location=(x_pos, y_start - 2.1, 0))
    min_text = context.active_object
    min_text.name = "Legend_Min"
    min_text.data.body = f"{min_val:.0f}"
    min_text.data.align_x = 'LEFT'
    min_text.data.align_y = 'CENTER'
    min_text.data.size = 0.5

    # Middle label
    mid_val = (min_val + max_val) / 2
    bpy.ops.object.text_add(location=(x_pos, y_start, 0))
    mid_text = context.active_object
    mid_text.name = "Legend_Mid"
    mid_text.data.body = f"{mid_val:.0f}"
    mid_text.data.align_x = 'LEFT'
    mid_text.data.align_y = 'CENTER'
    mid_text.data.size = 0.5
    
    # Max label
    bpy.ops.object.text_add(location=(x_pos, y_start + 2.1, 0))
    max_text = context.active_object
    max_text.name = "Legend_Max"
    max_text.data.body = f"{max_val:.0f}"
    max_text.data.align_x = 'LEFT'
    max_text.data.align_y = 'CENTER'
    max_text.data.size = 0.5

def setup_legend_compositing(main_scene, legend_scene):
    """Setup compositing nodes to overlay legend on main render"""
    
    # Enable compositing in main scene
    main_scene.use_nodes = True
    
    # Clear existing nodes
    main_scene.node_tree.nodes.clear()
    
    nodes = main_scene.node_tree.nodes
    links = main_scene.node_tree.links
    
    # Create nodes
    render_main = nodes.new(type='CompositorNodeRLayers')
    render_main.location = (-400, 200)
    render_main.scene = main_scene
    
    render_legend = nodes.new(type='CompositorNodeRLayers')
    render_legend.location = (-400, -200)
    render_legend.scene = legend_scene
    
    alpha_over = nodes.new(type='CompositorNodeAlphaOver')
    alpha_over.location = (-100, 0)
    
    composite = nodes.new(type='CompositorNodeComposite')
    composite.location = (200, 0)
    
    # Connect nodes
    links.new(render_main.outputs['Image'], alpha_over.inputs[1])  # Background
    links.new(render_legend.outputs['Image'], alpha_over.inputs[2])  # Foreground
    links.new(alpha_over.outputs['Image'], composite.inputs['Image'])
    
    print(f"[TRIDENT] Setup compositing overlay for {legend_scene.name}")