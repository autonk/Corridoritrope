import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add properties to ZoetropeGeneratorSettings
    prop_addition = '''    export_dir: bpy.props.StringProperty(
        name="Export Directory",
        description="Directory to save the exported OBJ frames",
        subtype='DIR_PATH',
        default=""
    )
    use_export_frame_range: bpy.props.BoolProperty(
        name="Use Frame Range",
        description="Export a specific frame range instead of mapping to zoetrope frames",
        default=False
    )
    export_frame_start: bpy.props.IntProperty(
        name="Start",
        default=1,
        min=1
    )
    export_frame_end: bpy.props.IntProperty(
        name="End",
        default=24,
        min=1
    )'''
    content = content.replace('''    export_dir: bpy.props.StringProperty(
        name="Export Directory",
        description="Directory to save the exported OBJ frames",
        subtype='DIR_PATH',
        default=""
    )''', prop_addition)

    # 2. Update UI
    ui_find = '''                box.label(text="Export to OBJ", icon='EXPORT')
                box.prop(settings, "export_dir")
                row = box.row()'''
    ui_replace = '''                box.label(text="Export to OBJ", icon='EXPORT')
                box.prop(settings, "export_dir")
                box.prop(settings, "use_export_frame_range")
                if settings.use_export_frame_range:
                    row = box.row(align=True)
                    row.prop(settings, "export_frame_start")
                    row.prop(settings, "export_frame_end")
                row = box.row()'''
    content = content.replace(ui_find, ui_replace)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
