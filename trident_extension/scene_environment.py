import bpy

def set_transparent_environment():
    scene = bpy.context.scene
    scene.render.film_transparent = True
    
    # Use stored plane references
    plane_back = scene.trident.plane_back
    if plane_back and plane_back.name in bpy.data.objects:
        plane_back.hide_render = True
        plane_back.hide_viewport = True
    
    plane_side = scene.trident.plane_side
    if plane_side and plane_side.name in bpy.data.objects:
        plane_side.hide_render = True
        plane_side.hide_viewport = True
    
    # Use stored material reference
    mat = scene.trident.shadow_material
    if not mat or mat.name not in bpy.data.materials:
        print("[TRIDENT] Warning: Shadow_Catcher material not found")
        return
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Node lookups
    diffuse = nodes.get("Diffuse BSDF")
    bsdf = nodes.get("Principled BSDF")
    color_ramp = nodes.get("Color Ramp")
    shaderRGB = nodes.get("Shader to RGB")
    output = nodes.get("Material Output")
    
    if not all([diffuse, bsdf, color_ramp, shaderRGB, output]):
        print("[TRIDENT] Warning: Required nodes not found")
        return
    
    # Link nodes
    links.new(diffuse.outputs['BSDF'], shaderRGB.inputs['Shader'])
    links.new(shaderRGB.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Alpha'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Use stored sun reference
    sun = scene.trident.sun
    if sun and sun.name in bpy.data.objects:
        sun.data.energy = 6.7

def disable_transparent_environment():
    scene = bpy.context.scene
    scene.render.film_transparent = False
    
    plane_back = scene.trident.plane_back
    if plane_back and plane_back.name in bpy.data.objects:
        plane_back.hide_render = False
        plane_back.hide_viewport = False
    
    plane_side = scene.trident.plane_side
    if plane_side and plane_side.name in bpy.data.objects:
        plane_side.hide_render = False
        plane_side.hide_viewport = False
    
    mat = scene.trident.shadow_material
    if not mat or mat.name not in bpy.data.materials:
        print("[TRIDENT] Warning: Shadow_Catcher material not found")
        return
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    diffuse = nodes.get("Diffuse BSDF")
    output = nodes.get("Material Output")
    
    if diffuse and output:
        links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
    
    sun = scene.trident.sun
    if sun and sun.name in bpy.data.objects:
        sun.data.energy = 4.7

def create_gizmo(context):
    scene = context.scene
    points_obj = scene.trident.points_obj

    # Clear scene first
    for obj in context.scene.objects:
        if "TRIDENT_Gizmo" in obj.name:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Z-Axis
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(0, 0, 1))
    z_cyl = context.active_object
    z_cyl.name = "TRIDENT_Gizmo_Z"
    ### Cone Z-axis
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=0.5, location=(0, 0, 2))
    z_con = context.active_object
    z_con.name = "TRIDENT_Gizmo_Z_Cone"
    ### Add text Z-Axis
    bpy.ops.object.text_add(location=(0, 0, 2.5), rotation=(1.5708, 0, 0.78), radius=0.4)
    z_text = context.active_object
    z_text.name = "TRIDENT_Gizmo_Z_Text"
    z_text.data.body = "Z"
    z_text.data.align_x = 'CENTER'

    # X-Axis
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(1, 0, 0), rotation=(0, 1.5708, 0))
    x_cyl = context.active_object
    x_cyl.name = "TRIDENT_Gizmo_X"
    ### Cone X-axis
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=0.5, location=(2, 0, 0), rotation=(0, 1.5708, 0))
    x_con = context.active_object
    x_con.name = "TRIDENT_Gizmo_X_Cone"
    ### Add text X-Axis
    bpy.ops.object.text_add(location=(2.3, 0, 0.3), rotation=(1.5708, 0, 0.78), radius=0.4)
    x_text = context.active_object
    x_text.name = "TRIDENT_Gizmo_X_Text"
    x_text.data.body = "X"
    x_text.data.align_x = 'CENTER'

    # Y-Axis
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(0, 1, 0), rotation=(0, 1.5708, 1.5708))
    y_cyl = context.active_object
    y_cyl.name = "TRIDENT_Gizmo_Y"
    ### Cone Y-Axis
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=0.5, location=(0, 2, 0), rotation=(0, 1.5708, 1.5708))
    y_con = context.active_object
    y_con.name = "TRIDENT_Gizmo_Y_Cone"
    ### Add text Y-Axis
    bpy.ops.object.text_add(location=(0, 2.3, 0.3), rotation=(1.5708, 0, 0.78), radius=0.4)
    y_text = context.active_object
    y_text.name = "TRIDENT_Gizmo_Y_Text"
    y_text.data.body = "Y"
    y_text.data.align_x = 'CENTER'

    # Add sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 0))
    sphere = context.active_object
    sphere.name = "TRIDENT_Gizmo_Sphere"

    # Join all in one object
    bpy.ops.object.select_all(action='DESELECT')
    z_cyl.select_set(True)
    x_cyl.select_set(True)
    y_cyl.select_set(True)
    z_con.select_set(True)
    x_con.select_set(True)
    y_con.select_set(True)
    sphere.select_set(True)
    bpy.context.view_layer.objects.active = sphere
    bpy.ops.object.join()
    gizmo = context.active_object
    gizmo.name = "TRIDENT_Gizmo"

    # Setup Constraints
    gizmo.vertex_groups.new(name='z_group')
    gizmo.vertex_groups['z_group'].add([578], weight=1.0, type='REPLACE')
    gizmo.vertex_groups.new(name='y_group')
    gizmo.vertex_groups['y_group'].add([772], weight=1.0, type='REPLACE')
    gizmo.vertex_groups.new(name='x_group')
    gizmo.vertex_groups['x_group'].add([675], weight=1.0, type='REPLACE')

    # Z_TEXT
    z_text.constraints.new(type='COPY_LOCATION')
    z_text.constraints['Copy Location'].target = bpy.data.objects["TRIDENT_Gizmo"]
    z_text.constraints['Copy Location'].subtarget = 'z_group'
    z_text.constraints.new(type='LOCKED_TRACK')
    z_text.constraints['Locked Track'].target = bpy.data.objects["Camera"]
    z_text.constraints['Locked Track'].track_axis = 'TRACK_Z'
    z_text.constraints['Locked Track'].lock_axis = 'LOCK_Y'
    z_text.constraints.new(type='LOCKED_TRACK')
    z_text.constraints['Locked Track.001'].target = bpy.data.objects["Camera"]
    z_text.constraints['Locked Track.001'].track_axis = 'TRACK_Z'
    z_text.constraints['Locked Track.001'].lock_axis = 'LOCK_X'

    # Y_TEXT
    y_text.constraints.new(type='COPY_LOCATION')
    y_text.constraints['Copy Location'].target = bpy.data.objects["TRIDENT_Gizmo"]
    y_text.constraints['Copy Location'].subtarget = 'y_group'
    y_text.constraints.new(type='LOCKED_TRACK')
    y_text.constraints['Locked Track'].target = bpy.data.objects["Camera"]
    y_text.constraints['Locked Track'].track_axis = 'TRACK_Z'
    y_text.constraints['Locked Track'].lock_axis = 'LOCK_Y'
    y_text.constraints.new(type='LOCKED_TRACK')
    y_text.constraints['Locked Track.001'].target = bpy.data.objects["Camera"]
    y_text.constraints['Locked Track.001'].track_axis = 'TRACK_Z'
    y_text.constraints['Locked Track.001'].lock_axis = 'LOCK_X'

    # X_TEXT
    x_text.constraints.new(type='COPY_LOCATION')
    x_text.constraints['Copy Location'].target = bpy.data.objects["TRIDENT_Gizmo"]
    x_text.constraints['Copy Location'].subtarget = 'x_group'
    x_text.constraints.new(type='LOCKED_TRACK')
    x_text.constraints['Locked Track'].target = bpy.data.objects["Camera"]
    x_text.constraints['Locked Track'].track_axis = 'TRACK_Z'
    x_text.constraints['Locked Track'].lock_axis = 'LOCK_Y'
    x_text.constraints.new(type='LOCKED_TRACK')
    x_text.constraints['Locked Track.001'].target = bpy.data.objects["Camera"]
    x_text.constraints['Locked Track.001'].track_axis = 'TRACK_Z'
    x_text.constraints['Locked Track.001'].lock_axis = 'LOCK_X'

    # Constraint to the object
    gizmo.constraints.new(type='COPY_ROTATION')
    gizmo.constraints['Copy Rotation'].target = points_obj
    gizmo.constraints['Copy Rotation'].mix_mode = 'BEFORE'

    # Move gizmo
    gizmo.location = (-14, 21.5, 11)
    gizmo.scale = (0.5, 0.5, 0.5)
    
    # Hide all gizmo parts in viewport
    gizmo.hide_viewport = True
    x_text.hide_viewport = True
    y_text.hide_viewport = True
    z_text.hide_viewport = True

    # Set material for the gizmo and for text
    mat_gizmo = bpy.data.materials.new(name="TRIDENT_Gizmo_Material")
    mat_gizmo.use_nodes = True
    bsdf = mat_gizmo.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.03, 0.03, 0.03, 1)

    mat_gizmo_text = bpy.data.materials.new(name="TRIDENT_Gizmo_Text_Material")
    mat_gizmo_text.use_nodes = True
    bsdf_text = mat_gizmo_text.node_tree.nodes['Principled BSDF']
    bsdf_text.inputs['Base Color'].default_value = (0, 0, 0, 1)

    if gizmo.data.materials:
        gizmo.data.materials[0] = mat_gizmo
    else:
        gizmo.data.materials.append(mat_gizmo)

    for obj in [x_text, y_text, z_text]:
        if obj.data.materials:
            obj.data.materials[0] = mat_gizmo_text
        else:
            obj.data.materials.append(mat_gizmo_text)

def setup_scene_environment(context):
    scene = context.scene
    world = scene.world
    
    scene.view_settings.view_transform = 'Standard'
    scene.sequencer_colorspace_settings.name = 'Filmic Log'

    # Set world properties
    world.color = (1.0, 1.0, 1.0)
    world.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 1.0, 1.0, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.35

    # Create/get sun and store reference
    sun = scene.trident.sun
    if not sun or sun.name not in bpy.data.objects:
        bpy.ops.object.light_add(type='SUN', 
                                 radius=1, 
                                 align='WORLD', 
                                 location=(0, 0, 0), 
                                 scale=(1, 1, 1), 
                                 rotation=(45.82, 33.97, 30.44))
        sun = context.active_object
        scene.trident.sun = sun
        sun.data.specular_factor = 0.0
        sun.data.energy = 4.7
    
    # Create camera or use scene's camera
    if scene.camera is None:
        bpy.ops.object.camera_add(enter_editmode=False, 
                                  align='VIEW', 
                                  location=(-31.3817, 32.3135, 9.39782), 
                                  rotation=(1.38367, 0, 3.90514), 
                                  scale=(1, 1, 1))
        scene.camera = context.active_object
        scene.render.resolution_x = 1080
        scene.render.resolution_y = 1080
    
    # Create floor plane and store reference
    plane_floor = scene.trident.plane_floor
    if not plane_floor or plane_floor.name not in bpy.data.objects:
        bpy.ops.mesh.primitive_plane_add(size=2, 
                                         enter_editmode=False, 
                                         align='WORLD', 
                                         location=(0, 0, -16.18), 
                                         scale=(1, 1, 1))
        plane_floor = context.active_object
        scene.trident.plane_floor = plane_floor
        plane_floor.scale[0] = 50
        plane_floor.scale[1] = 50
        
        # Create shadow catcher material and store reference
        mat = bpy.data.materials.new(name="Shadow_Catcher")
        scene.trident.shadow_material = mat
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Create nodes
        diffuse = nodes.new(type="ShaderNodeBsdfDiffuse")
        diffuse.location = (-500, 0)
        
        shaderRGB = nodes.new(type="ShaderNodeShaderToRGB")
        shaderRGB.location = (-300, 200)
        
        color_ramp = nodes.new(type="ShaderNodeValToRGB")
        color_ramp.location = (0, 200)
        color_ramp.color_ramp.elements[0].position = 0
        color_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
        color_ramp.color_ramp.elements[1].position = 0.659091
        color_ramp.color_ramp.elements[1].color = (0, 0, 0, 1)

        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.location = (300, 200)
        bsdf.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
        bsdf.inputs[2].default_value = 1.0
        
        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (700, 0)
        
        # Link nodes
        links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
        
        # Assign material
        plane_floor.data.materials.append(mat)
        plane_floor.active_material.blend_method = 'BLEND'
        
    # Create back plane and store reference
    plane_back = scene.trident.plane_back
    if not plane_back or plane_back.name not in bpy.data.objects:
        bpy.ops.mesh.primitive_plane_add(size=2, 
                                         enter_editmode=False, 
                                         align='WORLD', 
                                         location=(0, -29.9, 13.02),
                                         rotation=(1.5708, 0, 0),
                                         scale=(1, 1, 1))
        plane_back = context.active_object
        scene.trident.plane_back = plane_back
        plane_back.scale[0] = 30
        plane_back.scale[1] = 30

        mat_plane2 = bpy.data.materials.new(name="Plane2_Material")
        plane_back.data.materials.append(mat_plane2)
        plane_back.visible_shadow = False

    # Create side plane and store reference
    plane_side = scene.trident.plane_side
    if not plane_side or plane_side.name not in bpy.data.objects:
        bpy.ops.mesh.primitive_plane_add(size=2, 
                                         enter_editmode=False, 
                                         align='WORLD', 
                                         location=(29.9, 0, 13.02),
                                         rotation=(0, 1.5708, 0), 
                                         scale=(1, 1, 1))
        plane_side = context.active_object
        scene.trident.plane_side = plane_side
        plane_side.scale[0] = 30
        plane_side.scale[1] = 30

    create_gizmo(context)