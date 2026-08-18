import bpy
import math
from .properties import *
from .operators import *
from .ui import *
from . import align_to_z

classes = [
    ZoetropeMappingItem,
    ZoetropeGeneratorSettings,
    OBJECT_OT_generate_zoetrope,
    OBJECT_OT_create_frame_template,
    OBJECT_OT_clear_mappings,
    OBJECT_OT_batch_zoetrope_baker,
    OBJECT_OT_export_zoetrope_frames,
    OBJECT_OT_import_zoetrope_frames,
    OBJECT_OT_import_raw_zoetrope_frames,
    OBJECT_OT_clear_all_frames,
    VIEW3D_PT_zoetrope_main,
    VIEW3D_PT_zoetrope_settings,
    VIEW3D_PT_zoetrope_baker,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    align_to_z.register()
        
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
    align_to_z.unregister()
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
