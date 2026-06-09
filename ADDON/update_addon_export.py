import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    find_export_logic = '''        context.window_manager.progress_begin(0, loop_count)
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')

        import os
        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
                
            anim_length = max_frame - start_frame + 1
            if mismatch_strategy == 'INTERPOLATE':
                target_fbx_frame = start_frame + (i / max(1, loop_count - 1)) * (anim_length - 1)
            else:
                target_fbx_frame = start_frame + i'''
                
    replace_export_logic = '''        settings = context.scene.zoetrope_generator
        if settings.use_export_frame_range:
            loop_count = settings.export_frame_end - settings.export_frame_start + 1
            
        context.window_manager.progress_begin(0, loop_count)
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')

        import os
        for i in range(loop_count):
            if settings.use_export_frame_range:
                target_fbx_frame = settings.export_frame_start + i
            else:
                empty_idx = start_empty_idx + i
                if empty_idx >= num_empties:
                    break
                    
                anim_length = max_frame - start_frame + 1
                if mismatch_strategy == 'INTERPOLATE':
                    target_fbx_frame = start_frame + (i / max(1, loop_count - 1)) * (anim_length - 1)
                else:
                    target_fbx_frame = start_frame + i'''
                    
    content = content.replace(find_export_logic, replace_export_logic)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
