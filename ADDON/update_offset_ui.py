import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    find_settings_ui = '''              col.prop(zoe, "zoe_rot_z")
              col.prop(zoe, "zoe_scale")'''
    replace_settings_ui = '''              col.prop(zoe, "zoe_rot_z")
              col.prop(zoe, "zoe_scale")
              col.prop(zoe, "zoe_offset")'''
    
    if find_settings_ui in content:
        content = content.replace(find_settings_ui, replace_settings_ui)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
    else:
        print(f"Could not find string in {filepath}")

modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_generator_addon.py")
modify_file("v:\\01 PROJECTS\\02 CORRIDOR CREW\\01 Episodes\\2026\\01_JANUARY\\01.05.2026_ZOETROPE\\02_VFX\\06_BLENDER\\ZOETROPE PROJECT\\ADDON\\zoetrope_extension\\__init__.py")
