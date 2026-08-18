import bpy
import math
from mathutils import Vector

def update_baker_source(self, context):
    context.scene.zoetrope_mappings.clear()
    anim_parent = self.baker_source
    if not anim_parent:
        return
    if anim_parent.children:
        for child in anim_parent.children:
            item = context.scene.zoetrope_mappings.add()
            item.anim_collection = child
    else:
        item = context.scene.zoetrope_mappings.add()
        item.anim_collection = anim_parent

def get_eff_frames(self):
    base = self.get('zoe_frames', 1) if self.get('zoe_type') == 'BASIC' else self.get('zoe_planets', 1) * self.get('zoe_subframes', 1)
    if self.zoe_speed_mult == 0:
        return 0.0
    return base / self.zoe_speed_mult

def set_eff_frames(self, value):
    if value <= 0:
        return
    base = self.get('zoe_frames', 1) if self.get('zoe_type') == 'BASIC' else self.get('zoe_planets', 1) * self.get('zoe_subframes', 1)
    self.zoe_speed_mult = base / value

def update_live_settings(self, context):
    col = self
    empties = [obj for obj in col.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY']
    if not empties:
        return
    for empty in empties:
        empty.delta_scale = (col.zoe_scale, col.zoe_scale, col.zoe_scale)
        empty.delta_rotation_euler[2] = col.zoe_rot_z
        empty.delta_location = col.zoe_offset
    root_obj = empties[0].parent
    if root_obj and 'base_driver_expr' in root_obj:
        expr = f"({root_obj['base_driver_expr']}) * {col.zoe_speed_mult}"
        if root_obj.animation_data and root_obj.animation_data.drivers:
            for fc in root_obj.animation_data.drivers:
                if fc.data_path == 'rotation_euler' and fc.array_index == 2:
                    if col.zoe_invert:
                        fc.driver.expression = f'-({expr})'
                    else:
                        fc.driver.expression = expr
                    break
        empties.sort(key=lambda x: x.name)
        names = [e.name for e in empties]
        if col.zoe_invert:
            new_names = [names[0]] + list(reversed(names[1:]))
        else:
            pass
        for e in empties:
            if 'base_frame_idx' not in e:
                e['base_frame_idx'] = int(e.name.split('_')[1])
        for e in empties:
            idx = e['base_frame_idx']
            if col.zoe_invert:
                if idx == 1:
                    target_idx = 1
                else:
                    target_idx = len(empties) - idx + 2
            else:
                target_idx = idx
            e.name = f'Frame_{target_idx:03d}_TEMP'
        for e in empties:
            e.name = e.name.replace('_TEMP', '')

class ZoetropeMappingItem(bpy.types.PropertyGroup):
    anim_collection: bpy.props.PointerProperty(name='Animation', type=bpy.types.Collection)
    target_zoetrope: bpy.props.PointerProperty(name='Target Zoetrope', type=bpy.types.Collection, description='Select the Zoetrope collection to assign this animation to')
    mismatch_strategy: bpy.props.EnumProperty(name='Mismatch Strategy', description='How to handle frame length mismatches', items=[('INTERPOLATE', 'Interpolate', 'Compress or stretch animation to fit available frames', 'MOD_TIME', 0), ('CLIP', 'Clip (1:1)', 'Play 1:1. Clips end if too long, clips beginning if too short.', 'MOD_DATA_TRANSFER', 1)], default='INTERPOLATE')
    use_custom_frame_range: bpy.props.BoolProperty(name='Custom Frame Range', description='Override automatic frame range detection', default=False)
    frame_start: bpy.props.IntProperty(name='Start Frame', default=1, min=1)
    frame_end: bpy.props.IntProperty(name='End Frame', default=24, min=1)
    frameskip: bpy.props.IntProperty(name='Frame Skip', description='Number of frames to skip (e.g. 1 means skip 0 frames, 2 means skip every other)', default=1, min=1)

def get_zoetrope_rpm(self):
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    if self.mode == 'BASIC':
        frames = self.basic_frames
    else:
        frames = self.planets * self.subframes
    if frames == 0:
        return 0.0
    return 60.0 * fps / frames

def set_zoetrope_rpm(self, value):
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    if value <= 0:
        return
    target_frames = round(60.0 * fps / value)
    if target_frames < 2:
        target_frames = 2
    if self.mode == 'BASIC':
        self.basic_frames = target_frames
    else:
        self.subframes = max(1, round(target_frames / self.planets))

class ZoetropeGeneratorSettings(bpy.types.PropertyGroup):
    mode: bpy.props.EnumProperty(name='Type', items=[('BASIC', 'Basic', 'Standard Zoetrope', 'MESH_CIRCLE', 0), ('PLANETARY', 'Planetary', 'Planetary Gear Zoetrope', 'MOD_ARRAY', 1)], default='BASIC')
    target_rpm: bpy.props.FloatProperty(name='Target RPM', description='Target Rotational Speed. Automatically scales the number of frames to maintain sync', get=get_zoetrope_rpm, set=set_zoetrope_rpm)
    radius: bpy.props.FloatProperty(name='Radius', default=5.0, min=0.1, subtype='DISTANCE', description='The radius of the Zoetrope')
    basic_frames: bpy.props.IntProperty(name='Frames', default=45, min=2, description='Total number of frames (vertices) for the Basic Zoetrope')
    planets: bpy.props.IntProperty(name='Planets', default=10, min=2, description='Number of planet gears')
    subframes: bpy.props.IntProperty(name='Sub-frames', default=5, min=1, description='Number of frames per planet gear')
    planet_size: bpy.props.FloatProperty(name='Planet Size', default=1.0, min=0.0, max=1.0, description='Scale planet gears relative to sun (1.0 = Max Planets, 0.0 = Max Sun)')
    baker_source: bpy.props.PointerProperty(name='Source Collection', type=bpy.types.Collection, description='Collection containing the animations or subcollections to map', update=update_baker_source)
    active_zoetrope: bpy.props.PointerProperty(name='Active Zoetrope', type=bpy.types.Collection, description='Select a generated Zoetrope collection to tweak its live settings')
    export_dir: bpy.props.StringProperty(name='Export Directory', description='Directory to save the exported OBJ frames', subtype='DIR_PATH', default='')
    export_up_axis: bpy.props.EnumProperty(name='Up', items=[('X', 'X', ''), ('Y', 'Y', ''), ('Z', 'Z', ''), ('-X', '-X', ''), ('-Y', '-Y', ''), ('-Z', '-Z', '')], default='Y')
    export_forward_axis: bpy.props.EnumProperty(name='Forward', items=[('X', 'X', ''), ('Y', 'Y', ''), ('Z', 'Z', ''), ('-X', '-X', ''), ('-Y', '-Y', ''), ('-Z', '-Z', '')], default='-Z')
    use_export_frame_range: bpy.props.BoolProperty(name='Use Frame Range', description='Export a specific frame range instead of mapping to zoetrope frames', default=False)
    export_frame_start: bpy.props.IntProperty(name='Start', default=1, min=1)
    export_frame_end: bpy.props.IntProperty(name='Export End Frame', default=24, min=1)
    export_frameskip: bpy.props.IntProperty(name='Export Frame Skip', description='Number of frames to skip during export', default=1, min=1)
    raw_mismatch_strategy: bpy.props.EnumProperty(name='Mismatch Strategy', description='How to handle frame length mismatches', items=[('INTERPOLATE', 'Interpolate', 'Compress or stretch to fit available frames', 'MOD_TIME', 0), ('CLIP', 'Clip (1:1)', 'Play 1:1. Clips end if too long, clips beginning if too short.', 'MOD_DATA_TRANSFER', 1)], default='INTERPOLATE')

