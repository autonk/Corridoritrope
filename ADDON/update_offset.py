import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove custom_origin property
    find_prop = '''    custom_origin: bpy.props.PointerProperty(
        name="Custom Origin",
        type=bpy.types.Object,
        description="Select an object (like an Empty) to act as the true center (origin) of the animation when exported or baked"
    )'''
    content = content.replace(find_prop, "")

    # 2. Remove custom_origin from UI
    find_single_ui = '''                            row.prop(item, "frame_end")
                            
                        box.prop(item, "custom_origin")'''
    replace_single_ui = '''                            row.prop(item, "frame_end")'''
    content = content.replace(find_single_ui, replace_single_ui)

    find_multi_ui = '''                            row.prop(item, "frame_end")
                            
                        map_box.prop(item, "custom_origin")'''
    replace_multi_ui = '''                            row.prop(item, "frame_end")'''
    content = content.replace(find_multi_ui, replace_multi_ui)

    # 3. Add zoe_offset to register
    find_reg = '''    bpy.types.Collection.zoe_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Scale the animation instances",
        default=1.0,
        min=0.01,
        update=update_live_settings
    )'''
    replace_reg = '''    bpy.types.Collection.zoe_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Scale the animation instances",
        default=1.0,
        min=0.01,
        update=update_live_settings
    )
    bpy.types.Collection.zoe_offset = bpy.props.FloatVectorProperty(
        name="Local Offset",
        description="Offset the animation instances",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION',
        update=update_live_settings
    )'''
    content = content.replace(find_reg, replace_reg)
    
    # Add zoe_offset to unregister
    find_unreg = '''    del bpy.types.Collection.zoe_scale'''
    replace_unreg = '''    del bpy.types.Collection.zoe_scale
    del bpy.types.Collection.zoe_offset'''
    content = content.replace(find_unreg, replace_unreg)

    # 4. Update live settings
    find_live = '''    # Apply Scale and Rotation via Delta Transforms
    for empty in empties:
        empty.delta_scale = (col.zoe_scale, col.zoe_scale, col.zoe_scale)
        empty.delta_rotation_euler[2] = col.zoe_rot_z'''
    replace_live = '''    # Apply Scale, Rotation, and Offset via Delta Transforms
    for empty in empties:
        empty.delta_scale = (col.zoe_scale, col.zoe_scale, col.zoe_scale)
        empty.delta_rotation_euler[2] = col.zoe_rot_z
        empty.delta_location = col.zoe_offset'''
    content = content.replace(find_live, replace_live)

    # 5. Update settings UI
    find_settings_ui = '''        box.prop(col, "zoe_rot_z")
        box.prop(col, "zoe_scale")'''
    replace_settings_ui = '''        box.prop(col, "zoe_rot_z")
        box.prop(col, "zoe_scale")
        box.prop(col, "zoe_offset")'''
    content = content.replace(find_settings_ui, replace_settings_ui)

    # 6. Update bake logic
    find_bake = '''            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                if mapping_item and mapping_item.custom_origin:
                    o_mat_inv = mapping_item.custom_origin.matrix_world.inverted()
                    orig_matrix = o_mat_inv @ orig_matrix
                    
                combined.parent = empty
                combined.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                combined.matrix_local = orig_matrix'''
    replace_bake = '''            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                template_obj = bpy.data.objects.get("Frame_Template")
                if template_obj:
                    o_mat_inv = template_obj.matrix_world.inverted()
                    orig_matrix = o_mat_inv @ orig_matrix
                    
                combined.parent = empty
                combined.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                combined.matrix_local = orig_matrix'''
    content = content.replace(find_bake, replace_bake)

    # 7. Update export logic
    find_export = '''                            new_obj = bpy.data.objects.new(f"Temp_Export_{m.name}", real_mesh)
                            
                            if mapping_item and mapping_item.custom_origin:
                                o_mat_inv = mapping_item.custom_origin.matrix_world.inverted()
                                new_obj.matrix_world = o_mat_inv @ inst.matrix_world.copy()
                            else:
                                new_obj.matrix_world = inst.matrix_world.copy()
                                
                            context.scene.collection.objects.link(new_obj)'''
    replace_export = '''                            new_obj = bpy.data.objects.new(f"Temp_Export_{m.name}", real_mesh)
                            
                            template_obj = bpy.data.objects.get("Frame_Template")
                            if template_obj:
                                o_mat_inv = template_obj.matrix_world.inverted()
                                new_obj.matrix_world = o_mat_inv @ inst.matrix_world.copy()
                            else:
                                new_obj.matrix_world = inst.matrix_world.copy()
                                
                            context.scene.collection.objects.link(new_obj)'''
    content = content.replace(find_export, replace_export)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
