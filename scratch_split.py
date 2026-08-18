import ast
import os
import shutil

source_file = r"v:\01 PROJECTS\02 CORRIDOR CREW\01 Episodes\2026\01_JANUARY\01.05.2026_ZOETROPE\02_VFX\06_BLENDER\ZOETROPE PROJECT\ADDON\zoetrope_extension\__init__.py"
out_dir = r"v:\01 PROJECTS\02 CORRIDOR CREW\01 Episodes\2026\01_JANUARY\01.05.2026_ZOETROPE\02_VFX\06_BLENDER\ZOETROPE PROJECT\zoetrope_pro"

if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir)

with open(source_file, "r", encoding="utf-8") as f:
    source_code = f.read()

tree = ast.parse(source_code)

properties_nodes = []
core_nodes = []
operators_nodes = []
ui_nodes = []
updater_names = {"ZOETROPE_OT_update_self", "ZOETROPE_OT_check_updates", "ZOETROPE_PT_updater_panel"}

# Hardcoded logic to categorize nodes
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        if node.name in updater_names:
            continue
        elif "Settings" in node.name or "MappingItem" in node.name:
            properties_nodes.append(node)
        elif "_OT_" in node.name:
            operators_nodes.append(node)
        elif "_PT_" in node.name:
            ui_nodes.append(node)
    elif isinstance(node, ast.FunctionDef):
        name = node.name
        if name in ("get_eff_frames", "set_eff_frames", "update_live_settings", "update_baker_source", "get_zoetrope_rpm", "set_zoetrope_rpm"):
            properties_nodes.append(node)
        elif name in ("create_basic_zoetrope", "create_gear", "create_ring_gear", "find_best_ring_teeth", "generate_planetary_gearbox", "create_planetary_zoetrope"):
            core_nodes.append(node)

def write_module(filename, nodes, imports):
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
        f.write(imports + "\n\n")
        for node in nodes:
            f.write(ast.unparse(node) + "\n\n")

write_module("properties.py", properties_nodes, "import bpy\nimport math\nfrom mathutils import Vector")
write_module("core_generators.py", core_nodes, "import bpy\nimport math\nfrom mathutils import Vector")

write_module("operators.py", operators_nodes, "import bpy\nimport math\nimport os\nfrom mathutils import Vector\nfrom .core_generators import *\nfrom .properties import *")
write_module("ui.py", ui_nodes, "import bpy\nfrom .properties import *")

init_code = """import bpy
import math
from .properties import *
from .operators import *
from .ui import *

classes = [
    ZoetropeMappingItem,
    ZoetropeGeneratorSettings,
"""
for node in operators_nodes + ui_nodes:
    init_code += f"    {node.name},\n"
init_code += """]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.zoetrope_mappings = bpy.props.CollectionProperty(type=ZoetropeMappingItem)
    bpy.types.Scene.zoetrope_generator = bpy.props.PointerProperty(type=ZoetropeGeneratorSettings)
    
    bpy.types.Collection.zoe_rot_z = bpy.props.FloatProperty(name="Rotation Z", default=math.pi, subtype='ANGLE', update=update_live_settings)
    bpy.types.Collection.zoe_scale = bpy.props.FloatProperty(name="Scale", default=1.0, min=0.01, update=update_live_settings)
    bpy.types.Collection.zoe_offset = bpy.props.FloatVectorProperty(name="Local Offset", default=(0.0, 0.0, 0.0), subtype='TRANSLATION', update=update_live_settings)
    bpy.types.Collection.zoe_speed_mult = bpy.props.FloatProperty(name="Speed Multiplier", default=1.0, update=update_live_settings)
    bpy.types.Collection.zoe_eff_frames = bpy.props.FloatProperty(name="Revolution Frames", get=get_eff_frames, set=set_eff_frames)
    bpy.types.Collection.zoe_counteract_mult = bpy.props.BoolProperty(name="Counteract Speed Multiplier", default=False)
    bpy.types.Collection.zoe_frame_offset = bpy.props.IntProperty(name="Frame Offset", default=0, update=update_live_settings)
    bpy.types.Collection.zoe_invert = bpy.props.BoolProperty(name="Invert Animation", default=False, update=update_live_settings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.zoetrope_mappings
    del bpy.types.Scene.zoetrope_generator
    
    del bpy.types.Collection.zoe_rot_z
    del bpy.types.Collection.zoe_scale
    del bpy.types.Collection.zoe_offset
    del bpy.types.Collection.zoe_speed_mult
    del bpy.types.Collection.zoe_eff_frames
    del bpy.types.Collection.zoe_counteract_mult
    del bpy.types.Collection.zoe_frame_offset
    del bpy.types.Collection.zoe_invert
"""

with open(os.path.join(out_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_code)

shutil.copyfile(os.path.join(os.path.dirname(source_file), "blender_manifest.toml"), os.path.join(out_dir, "blender_manifest.toml"))
print("Done splitting!")
