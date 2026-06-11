import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix UI
    find_ui = '''              col.prop(zoe, "zoe_offset")
              col.prop(zoe, "zoe_invert", toggle=True)'''
    replace_ui = '''              col.prop(zoe, "zoe_offset")
              col.prop(zoe, "zoe_frame_offset")
              col.prop(zoe, "zoe_invert", toggle=True)'''
    content = content.replace(find_ui, replace_ui)

    # 2. Fix update_live_settings for individual origins
    find_live = '''      # Apply Scale, Rotation, and Offset via Delta Transforms
      for empty in empties:
          empty.delta_scale = (col.zoe_scale, col.zoe_scale, col.zoe_scale)
          empty.delta_rotation_euler[2] = col.zoe_rot_z
          empty.delta_location = col.zoe_offset'''
    replace_live = '''      # Apply Scale, Rotation, and Offset via Delta Transforms
      for empty in empties:
          empty.delta_scale = (col.zoe_scale, col.zoe_scale, col.zoe_scale)
          empty.delta_rotation_euler[2] = col.zoe_rot_z
          empty.delta_location = (0, 0, 0)
          for child in empty.children:
              child.delta_location = col.zoe_offset'''
    content = content.replace(find_live, replace_live)

    # 3. Fix Updater
    find_updater = '''        else:
            self.report({'INFO'}, msg)
            def draw(self, context):
                self.layout.label(text="Update Downloaded successfully!")
                self.layout.label(text="Please restart Blender for the changes to take effect.", icon='INFO')
            bpy.context.window_manager.popup_menu(draw, title="Zoetrope Updater", icon='INFO')'''
    replace_updater = '''        else:
            try:
                bpy.ops.wm.save_mainfile()
                bpy.ops.script.reload()
                self.report({'INFO'}, "Update installed and reloaded successfully!")
            except Exception as e:
                self.report({'WARNING'}, f"Update installed, but failed to reload automatically: {e}")'''
    content = content.replace(find_updater, replace_updater)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
