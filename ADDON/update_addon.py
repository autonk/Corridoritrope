import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update ZoetropeMappingItem
    prop_addition = '''    mismatch_strategy: bpy.props.EnumProperty(
        name="Mismatch Strategy",
        description="How to handle frame length mismatches",
        items=[
            ('INTERPOLATE', "Interpolate", "Compress or stretch animation to fit available frames", 'MOD_TIME', 0),
            ('CLIP', "Clip (1:1)", "Play 1:1. Clips end if too long, clips beginning if too short.", 'MOD_DATA_TRANSFER', 1)
        ],
        default='INTERPOLATE'
    )
    use_custom_frame_range: bpy.props.BoolProperty(
        name="Custom Frame Range",
        description="Override automatic frame range detection",
        default=False
    )
    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        default=1,
        min=1
    )
    frame_end: bpy.props.IntProperty(
        name="End Frame",
        default=24,
        min=1
    )'''
    content = content.replace('''    mismatch_strategy: bpy.props.EnumProperty(
        name="Mismatch Strategy",
        description="How to handle frame length mismatches",
        items=[
            ('INTERPOLATE', "Interpolate", "Compress or stretch animation to fit available frames", 'MOD_TIME', 0),
            ('CLIP', "Clip (1:1)", "Play 1:1. Clips end if too long, clips beginning if too short.", 'MOD_DATA_TRANSFER', 1)
        ],
        default='INTERPOLATE'
    )''', prop_addition)

    # 2. Update bake_single_mapping
    bake_find = '''        max_frame = 0
        valid_types = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'POINTCLOUD'}
        exportable_objects = []
        for obj in anim_col.all_objects:
            if obj.type in valid_types:
                exportable_objects.append(obj)
            if obj.animation_data and obj.animation_data.action:
                max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
                
        if not exportable_objects:
            self.report({'WARNING'}, f"No meshes found in {anim_col.name}!")
            return

        if max_frame == 0:
            self.report({'WARNING'}, f"No actions with keyframes found in {anim_col.name}!")
            return'''
    
    bake_replace = '''        valid_types = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'POINTCLOUD'}
        exportable_objects = []
        for obj in anim_col.all_objects:
            if obj.type in valid_types:
                exportable_objects.append(obj)
                
        if not exportable_objects:
            self.report({'WARNING'}, f"No meshes found in {anim_col.name}!")
            return

        mapping_item = None
        for item in context.scene.zoetrope_mappings:
            if item.anim_collection == anim_col and item.target_zoetrope == target_zoetrope:
                mapping_item = item
                break
                
        if mapping_item and mapping_item.use_custom_frame_range:
            start_frame = mapping_item.frame_start
            max_frame = mapping_item.frame_end
        else:
            start_frame = 1
            max_frame = 0
            for obj in exportable_objects:
                if obj.animation_data and obj.animation_data.action:
                    max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
            if max_frame == 0:
                self.report({'WARNING'}, f"No actions with keyframes found in {anim_col.name}! Defaulting to 24.")
                max_frame = 24'''
    content = content.replace(bake_find, bake_replace)

    # 3. Update target_fbx_frame calculations in bake_single_mapping
    target_fbx_find = '''        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
                
            if mismatch_strategy == 'INTERPOLATE':
                target_fbx_frame = 1 + (i / max(1, loop_count - 1)) * (max_frame - 1)
            else:
                target_fbx_frame = i + 1'''
                
    target_fbx_replace = '''        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
                
            anim_length = max_frame - start_frame + 1
            if mismatch_strategy == 'INTERPOLATE':
                target_fbx_frame = start_frame + (i / max(1, loop_count - 1)) * (anim_length - 1)
            else:
                target_fbx_frame = start_frame + i'''
    content = content.replace(target_fbx_find, target_fbx_replace)

    # 4. Update export_single_mapping (has slightly different print logic)
    export_find = '''        max_frame = 0
        valid_types = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'POINTCLOUD'}
        exportable_objects = []
        for obj in anim_col.all_objects:
            if obj.type in valid_types:
                exportable_objects.append(obj)
            if obj.animation_data and obj.animation_data.action:
                max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
                
        if not exportable_objects:
            self.report({'WARNING'}, f"No exportable objects found in {anim_col.name}!")
            return

        if max_frame == 0:
            self.report({'WARNING'}, f"No actions with keyframes found in {anim_col.name}! Defaulting to 24 frames.")
            max_frame = 24'''
    
    export_replace = '''        valid_types = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'POINTCLOUD'}
        exportable_objects = []
        for obj in anim_col.all_objects:
            if obj.type in valid_types:
                exportable_objects.append(obj)
                
        if not exportable_objects:
            self.report({'WARNING'}, f"No exportable objects found in {anim_col.name}!")
            return

        mapping_item = None
        for item in context.scene.zoetrope_mappings:
            if item.anim_collection == anim_col and item.target_zoetrope == target_zoetrope:
                mapping_item = item
                break
                
        if mapping_item and mapping_item.use_custom_frame_range:
            start_frame = mapping_item.frame_start
            max_frame = mapping_item.frame_end
        else:
            start_frame = 1
            max_frame = 0
            for obj in exportable_objects:
                if obj.animation_data and obj.animation_data.action:
                    max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
            if max_frame == 0:
                self.report({'WARNING'}, f"No actions with keyframes found in {anim_col.name}! Defaulting to 24 frames.")
                max_frame = 24'''
    content = content.replace(export_find, export_replace)
    
    # 5. Update target_fbx_frame calculation in export_single_mapping
    export_fbx_find = '''        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
                
            if mismatch_strategy == 'INTERPOLATE':
                target_fbx_frame = 1 + (i / max(1, loop_count - 1)) * (max_frame - 1)
            else:
                target_fbx_frame = i + 1'''
                
    export_fbx_replace = '''        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
                
            anim_length = max_frame - start_frame + 1
            if mismatch_strategy == 'INTERPOLATE':
                target_fbx_frame = start_frame + (i / max(1, loop_count - 1)) * (anim_length - 1)
            else:
                target_fbx_frame = start_frame + i'''
    content = content.replace(export_fbx_find, export_fbx_replace)
    
    # 6. Update UI in single mapping
    ui_find_single = '''                        if int(max_frame) != empties_count and empties_count > 0 and max_frame > 0:
                            box.label(text=f"Mismatch: {int(max_frame)} anim vs {empties_count} frames", icon='ERROR')
                            box.prop(item, "mismatch_strategy")'''
    ui_replace_single = '''                        if int(max_frame) != empties_count and empties_count > 0 and max_frame > 0:
                            box.label(text=f"Mismatch: {int(max_frame)} anim vs {empties_count} frames", icon='ERROR')
                            box.prop(item, "mismatch_strategy")
                        
                        box.separator()
                        box.prop(item, "use_custom_frame_range")
                        if item.use_custom_frame_range:
                            row = box.row(align=True)
                            row.prop(item, "frame_start")
                            row.prop(item, "frame_end")'''
    content = content.replace(ui_find_single, ui_replace_single)
    
    # 7. Update UI in multi mapping
    ui_find_multi = '''                        if int(max_frame) != empties_count and empties_count > 0 and max_frame > 0:
                            map_box.label(text=f"Mismatch: {int(max_frame)} anim vs {empties_count} frames", icon='ERROR')
                            map_box.prop(item, "mismatch_strategy")'''
    ui_replace_multi = '''                        if int(max_frame) != empties_count and empties_count > 0 and max_frame > 0:
                            map_box.label(text=f"Mismatch: {int(max_frame)} anim vs {empties_count} frames", icon='ERROR')
                            map_box.prop(item, "mismatch_strategy")
                            
                        map_box.prop(item, "use_custom_frame_range")
                        if item.use_custom_frame_range:
                            row = map_box.row(align=True)
                            row.prop(item, "frame_start")
                            row.prop(item, "frame_end")'''
    content = content.replace(ui_find_multi, ui_replace_multi)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
