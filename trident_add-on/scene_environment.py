import bpy

def set_transparent_environment():
    bpy.context.scene.render.film_transparent = True
    
    bpy.data.objects["Plane.001"].hide_render = True
    bpy.data.objects["Plane.001"].hide_viewport = True
    bpy.data.objects["Plane.002"].hide_render = True
    bpy.data.objects["Plane.002"].hide_viewport = True
    
    mat = bpy.data.materials["Shadow_Catcher"]
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Nodes
    diffuse = nodes["Diffuse BSDF"]
    bsdf = nodes.get("Principled BSDF")
    color_ramp = nodes["Color Ramp"]
    shaderRGB = nodes["Shader to RGB"]
    output = nodes["Material Output"]

    # Link nodes
    links.new(diffuse.outputs['BSDF'], shaderRGB.inputs['Shader'])
    links.new(shaderRGB.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Alpha'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    sun = bpy.data.objects.get("Sun")
    sun.data.energy = 6.7

def disable_transparent_environment():
    bpy.context.scene.render.film_transparent = False
    
    bpy.data.objects["Plane.001"].hide_render = False
    bpy.data.objects["Plane.001"].hide_viewport = False
    bpy.data.objects["Plane.002"].hide_render = False
    bpy.data.objects["Plane.002"].hide_viewport = False
    
    mat_name = "Shadow_Catcher"
    mat = bpy.data.materials.get(mat_name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Nodes
    diffuse = nodes["Diffuse BSDF"]
    output = nodes["Material Output"]
    
    # Link nodes
    links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
    
    sun = bpy.data.objects.get("Sun")
    sun.data.energy = 4.7

def setup_scene_environment(context):
    '''
    - World properties: Color (#FFFFFF), Strenght (0.35)
        - Sun: Strenght (7.0), Rotation (X: 45.82, Y: 33.97, Z: 30.44), Specular (0.0)
        - Plane below and around.
        - Put camera in a TBD position.
        - Render properties Color Management: Display Device (sRGB), View Transform (Standard), Look (None), Sequencer (Filmic log)
    '''

    scene = context.scene
    world = scene.world
    
    scene.view_settings.view_transform = 'Standard'
    scene.sequencer_colorspace_settings.name = 'Filmic Log'


    # Set world properties
    world.color = (1.0, 1.0, 1.0)
    world.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 1.0, 1.0, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.35

    # Set up sun lamp
    if bpy.data.objects.get("Sun") == None:
        bpy.ops.object.light_add(type='SUN', 
                                 radius=1, 
                                 align='WORLD', 
                                 location=(0, 0, 0), 
                                 scale=(1, 1, 1), 
                                 rotation=(45.82, 33.97, 30.44))
                                 
        sun = bpy.data.objects.get("Sun")
        sun.data.specular_factor = 0.0
        sun.data.energy = 4.7
    
    # Create Camera
    if bpy.data.objects.get("Camera") == None:
        bpy.ops.object.camera_add(enter_editmode=False, 
                                  align='VIEW', 
                                  location=(-31.3817, 32.3135, 9.39782), 
                                  rotation=(1.38367, 0, 3.90514), 
                                  scale=(1, 1, 1))
        camera = bpy.data.objects.get("Camera")
        bpy.context.scene.render.resolution_x = 1080
        bpy.context.scene.render.resolution_y = 1080
    
    # Create 3 planes
    if bpy.data.objects.get("Plane") == None:
        bpy.ops.mesh.primitive_plane_add(size=2, 
                                         enter_editmode=False, 
                                         align='WORLD', 
                                         location=(0, 0, -16.18), 
                                         scale=(1, 1, 1))
        plane_1 = bpy.data.objects.get('Plane')
        plane_1.scale[0] = 50
        plane_1.scale[1] = 50
        
        mat_name = "Shadow_Catcher"
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
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
        
        # Assign material to object
        if len(plane_1.data.materials) == 0:
            plane_1.data.materials.append(mat)
        else:
            plane_1.data.materials[0] = mat
        plane_1.active_material.blend_method = 'BLEND'
        
    if bpy.data.objects.get("Plane.001") == None:
        bpy.ops.mesh.primitive_plane_add(size = 2, 
                                         enter_editmode = False, 
                                         align = 'WORLD', 
                                         location = (0, -29.9, 13.02),
                                         rotation = (1.5708, 0, 0),
                                         scale = (1, 1, 1))
        plane_2 = bpy.data.objects.get('Plane.001')
        plane_2.scale[0] = 30
        plane_2.scale[1] = 30

        # Create and assign a material before setting shadow_method
        if not plane_2.data.materials:
            mat_plane2 = bpy.data.materials.new(name="Plane2_Material")
            plane_2.data.materials.append(mat_plane2)
        
        plane_2.active_material.shadow_method = 'NONE'

    if bpy.data.objects.get("Plane.002") == None:
        bpy.ops.mesh.primitive_plane_add(size=2, 
                                         enter_editmode=False, 
                                         align='WORLD', 
                                         location=(29.9, 0, 13.02),
                                         rotation=(0, 1.5708, 0), 
                                         scale=(1, 1, 1))
        plane_3 = bpy.data.objects.get('Plane.002')
        plane_3.scale[0] = 30
        plane_3.scale[1] = 30

