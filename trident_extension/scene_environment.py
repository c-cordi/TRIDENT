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