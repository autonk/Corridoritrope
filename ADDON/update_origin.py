import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add custom_origin to ZoetropeMappingItem
    find_prop = '''    frame_end: bpy.props.IntProperty(
        name="End Frame",
        default=24,
        min=1
    )'''
    replace_prop = '''    frame_end: bpy.props.IntProperty(
        name="End Frame",
        default=24,
        min=1
    )
    custom_origin: bpy.props.PointerProperty(
        name="Custom Origin",
        type=bpy.types.Object,
        description="Select an object (like an Empty) to act as the true center (origin) of the animation when exported or baked"
    )'''
    content = content.replace(find_prop, replace_prop)

    # 2. Update single mapping UI
    find_single_ui = '''                        if item.use_custom_frame_range:
                            row = box.row(align=True)
                            row.prop(item, "frame_start")
                            row.prop(item, "frame_end")'''
    replace_single_ui = '''                        if item.use_custom_frame_range:
                            row = box.row(align=True)
                            row.prop(item, "frame_start")
                            row.prop(item, "frame_end")
                            
                        box.prop(item, "custom_origin")'''
    content = content.replace(find_single_ui, replace_single_ui)

    # 3. Update multi mapping UI
    find_multi_ui = '''                        if item.use_custom_frame_range:
                            row = map_box.row(align=True)
                            row.prop(item, "frame_start")
                            row.prop(item, "frame_end")'''
    replace_multi_ui = '''                        if item.use_custom_frame_range:
                            row = map_box.row(align=True)
                            row.prop(item, "frame_start")
                            row.prop(item, "frame_end")
                            
                        map_box.prop(item, "custom_origin")'''
    content = content.replace(find_multi_ui, replace_multi_ui)

    # 4. Update bake logic
    find_bake = '''            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                combined.parent = empty
                combined.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                combined.matrix_local = orig_matrix'''
    replace_bake = '''            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                if mapping_item and mapping_item.custom_origin:
                    o_mat_inv = mapping_item.custom_origin.matrix_world.inverted()
                    orig_matrix = o_mat_inv @ orig_matrix
                    
                combined.parent = empty
                combined.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                combined.matrix_local = orig_matrix'''
    content = content.replace(find_bake, replace_bake)

    # 5. Update export logic
    find_export = '''                            new_obj = bpy.data.objects.new(f"Temp_Export_{m.name}", real_mesh)
                            new_obj.matrix_world = inst.matrix_world.copy()
                            context.scene.collection.objects.link(new_obj)'''
    replace_export = '''                            new_obj = bpy.data.objects.new(f"Temp_Export_{m.name}", real_mesh)
                            
                            if mapping_item and mapping_item.custom_origin:
                                o_mat_inv = mapping_item.custom_origin.matrix_world.inverted()
                                new_obj.matrix_world = o_mat_inv @ inst.matrix_world.copy()
                            else:
                                new_obj.matrix_world = inst.matrix_world.copy()
                                
                            context.scene.collection.objects.link(new_obj)'''
    content = content.replace(find_export, replace_export)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
