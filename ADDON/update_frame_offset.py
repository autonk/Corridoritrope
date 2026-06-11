import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add zoe_frame_offset to register
    find_reg = '''    bpy.types.Collection.zoe_offset = bpy.props.FloatVectorProperty(
        name="Local Offset",
        description="Offset the animation instances",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION',
        update=update_live_settings
    )'''
    replace_reg = '''    bpy.types.Collection.zoe_offset = bpy.props.FloatVectorProperty(
        name="Local Offset",
        description="Offset the animation instances",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION',
        update=update_live_settings
    )
    bpy.types.Collection.zoe_frame_offset = bpy.props.IntProperty(
        name="Frame Offset",
        description="Offset the animation playback by N frames",
        default=0,
        update=update_live_settings
    )'''
    content = content.replace(find_reg, replace_reg)
    
    # Add zoe_frame_offset to unregister
    find_unreg = '''    del bpy.types.Collection.zoe_offset'''
    replace_unreg = '''    del bpy.types.Collection.zoe_offset
    del bpy.types.Collection.zoe_frame_offset'''
    content = content.replace(find_unreg, replace_unreg)

    # 2. Update UI
    find_ui = '''              col.prop(zoe, "zoe_offset")
              col.prop(zoe, "zoe_invert", toggle=True)'''
    replace_ui = '''              col.prop(zoe, "zoe_offset")
              col.prop(zoe, "zoe_frame_offset")
              col.prop(zoe, "zoe_invert", toggle=True)'''
    content = content.replace(find_ui, replace_ui)

    # 3. Update live settings driver logic
    find_live = '''        # Apply Invert
        root_obj = empties[0].parent
        if root_obj and 'base_driver_expr' in root_obj:
            expr = root_obj['base_driver_expr']
            
            # Modify driver
            if root_obj.animation_data and root_obj.animation_data.drivers:
                for fc in root_obj.animation_data.drivers:
                    if fc.data_path == 'rotation_euler' and fc.array_index == 2:
                        if col.zoe_invert:
                            fc.driver.expression = f"-({expr})"
                        else:
                            fc.driver.expression = expr
                        break'''
    
    replace_live = '''        # Apply Invert and Frame Offset
        root_obj = empties[0].parent
        if root_obj and 'base_driver_expr' in root_obj:
            expr = root_obj['base_driver_expr']
            
            # Inject Frame Offset
            if hasattr(col, 'zoe_frame_offset') and col.zoe_frame_offset != 0:
                offset = col.zoe_frame_offset
                expr = expr.replace("(frame - 1)", f"(frame - 1 + {offset})")
            
            # Modify driver
            if root_obj.animation_data and root_obj.animation_data.drivers:
                for fc in root_obj.animation_data.drivers:
                    if fc.data_path == 'rotation_euler' and fc.array_index == 2:
                        if col.zoe_invert:
                            fc.driver.expression = f"-({expr})"
                        else:
                            fc.driver.expression = expr
                        break'''
    content = content.replace(find_live, replace_live)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
