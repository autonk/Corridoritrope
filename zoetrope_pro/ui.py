import bpy
from .properties import *

class VIEW3D_PT_zoetrope_main(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zoetrope'
    bl_label = 'Zoetrope Generator'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.zoetrope_generator
        row = layout.row(align=True)
        row.prop(settings, 'mode', expand=True)
        box = layout.box()
        col = box.column(align=True)
        col.prop(settings, 'radius')
        fps = context.scene.render.fps / context.scene.render.fps_base
        col.label(text=f'Scene FPS: {fps:.2f} (Target)', icon='TIME')
        col.separator()
        col.prop(settings, 'target_rpm')
        col.separator()
        if settings.mode == 'BASIC':
            col.prop(settings, 'basic_frames')
            total_frames = settings.basic_frames
        else:
            row = col.row(align=True)
            row.prop(settings, 'planets')
            row.prop(settings, 'subframes')
            col.prop(settings, 'planet_size', slider=True)
            total_frames = settings.planets * settings.subframes
            col.label(text=f'Total Frames: {total_frames}', icon='RENDER_ANIMATION')
        if total_frames > 0:
            deg_per_frame = 360.0 / total_frames
            col.label(text=f'Degrees per Frame: {deg_per_frame:.2f}°', icon='DRIVER_ROTATIONAL_DIFFERENCE')
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator('object.generate_zoetrope', icon='PLAY')

class VIEW3D_PT_zoetrope_settings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zoetrope'
    bl_label = 'Live Zoetrope Settings'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.zoetrope_generator
        box = layout.box()
        box.prop(settings, 'active_zoetrope')
        if settings.active_zoetrope:
            zoe = settings.active_zoetrope
            col = box.column(align=True)
            col.prop(zoe, 'zoe_rot_z')
            col.prop(zoe, 'zoe_scale')
            col.prop(zoe, 'zoe_offset')
            col.prop(zoe, 'zoe_speed_mult')
            col.prop(zoe, 'zoe_eff_frames', icon='TIME')
            col.prop(zoe, 'zoe_invert', toggle=True)
            if zoe.get('zoe_type') == 'BASIC':
                box.separator()
                v_total = zoe.get('zoe_verts_total', 0)
                v_frame = zoe.get('zoe_verts_per_frame', 0)
                frames = zoe.get('zoe_frames', 1)
                box.label(text=f'Total Vertices: {v_total}', icon='MESH_CIRCLE')
                box.label(text=f'Vertices per Frame: {v_frame}', icon='SNAP_VERTEX')
                if frames > 0 and v_total % frames != 0:
                    box.label(text=f'ERROR: Vertices not divisible by {frames}!', icon='ERROR')
            box.separator()
            box.operator('object.create_frame_template', icon='MESH_CYLINDER')
            box.separator()
            box.label(text='Mass Import Frames', icon='IMPORT')
            box.prop(settings, 'export_dir', text='Directory')
            import os, glob
            outdir = bpy.path.abspath(settings.export_dir)
            if zoe and outdir and os.path.exists(outdir):
                files = glob.glob(os.path.join(outdir, '*.obj'))
                empties_count = sum((1 for obj in zoe.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY'))
                if len(files) != empties_count and len(files) > 0 and (empties_count > 0):
                    box.label(text=f'Mismatch: {len(files)} OBJs vs {empties_count} frames', icon='ERROR')
                    box.prop(settings, 'raw_mismatch_strategy')
            row = box.row()
            row.scale_y = 1.5
            row.operator('object.import_raw_zoetrope_frames', icon='MESH_DATA', text='Import All OBJs to Empties')
            box.separator()
            row = box.row()
            row.operator('object.clear_all_frames', icon='TRASH', text='Clear All Frames')

class VIEW3D_PT_zoetrope_baker(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zoetrope'
    bl_label = 'Animation Collection Baker'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.zoetrope_generator
        box = layout.box()
        box.label(text='Animations', icon='OUTLINER_COLLECTION')
        box.prop(settings, 'baker_source', text='')
        row = box.row(align=True)
        row.operator('object.clear_zoetrope_mappings', icon='TRASH')
        if context.scene.zoetrope_mappings:
            is_single_mapping = len(context.scene.zoetrope_mappings) == 1 and context.scene.zoetrope_mappings[0].anim_collection == settings.baker_source
            if is_single_mapping:
                item = context.scene.zoetrope_mappings[0]
                box.separator()
                box.prop(item, 'target_zoetrope', text='Target Zoetrope')
                if item.target_zoetrope and item.anim_collection:
                    max_frame = 0
                    for obj in item.anim_collection.all_objects:
                        if obj.animation_data and obj.animation_data.action:
                            max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
                    empties_count = sum((1 for obj in item.target_zoetrope.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY'))
                    if int(max_frame) != empties_count and empties_count > 0 and (max_frame > 0):
                        box.label(text=f'Mismatch: {int(max_frame)} anim vs {empties_count} frames', icon='ERROR')
                        box.prop(item, 'mismatch_strategy')
                layout.separator()
                row = layout.row()
                row.scale_y = 1.5
                row.operator('object.batch_zoetrope_baker', icon='RENDER_ANIMATION', text='Bake Animation')
                layout.separator()
                box = layout.box()
                box.label(text='Export to OBJ', icon='EXPORT')
                box.prop(settings, 'export_dir')
                row_axis = box.row(align=True)
                row_axis.prop(settings, 'export_forward_axis')
                row_axis.prop(settings, 'export_up_axis')
                box.prop(settings, 'use_export_frame_range')
                if settings.use_export_frame_range:
                    row = box.row(align=True)
                    row.prop(settings, 'export_frame_start')
                    row.prop(settings, 'export_frame_end')
                row = box.row()
                row.scale_y = 1.5
                row.operator('object.export_zoetrope_frames', icon='MESH_DATA', text='Export Frames')
                row = box.row()
                row.scale_y = 1.5
                row.operator('object.import_zoetrope_frames', icon='IMPORT', text='Import Frames')
            else:
                layout.separator()
                layout.label(text='Animation Mappings:', icon='GRAPH')
                for (i, item) in enumerate(context.scene.zoetrope_mappings):
                    map_box = layout.box()
                    row = map_box.row()
                    if item.anim_collection:
                        row.label(text=item.anim_collection.name, icon='GROUP')
                    else:
                        row.label(text='Unknown Collection', icon='ERROR')
                    col = map_box.column(align=True)
                    col.prop(item, 'target_zoetrope', text='Target')
                    if item.target_zoetrope and item.anim_collection:
                        max_frame = 0
                        for obj in item.anim_collection.all_objects:
                            if obj.animation_data and obj.animation_data.action:
                                max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
                        empties_count = sum((1 for obj in item.target_zoetrope.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY'))
                        if int(max_frame) != empties_count and empties_count > 0 and (max_frame > 0):
                            map_box.label(text=f'Mismatch: {int(max_frame)} anim vs {empties_count} frames', icon='ERROR')
                            map_box.prop(item, 'mismatch_strategy')
                        if item.target_zoetrope and getattr(item.target_zoetrope, 'zoe_speed_mult', 1.0) != 1.0:
                            map_box.label(text='Counteract Speed Multiplier for:', icon='CON_ROTLIKE')
                            sub_box = map_box.box()

                            def draw_subcols(col_to_draw, layout_col, level=0):
                                row = layout_col.row()
                                if level > 0:
                                    row.label(text='    ' * level + '↳ ' + col_to_draw.name)
                                else:
                                    row.label(text=col_to_draw.name, icon='GROUP')
                                row.prop(col_to_draw, 'zoe_counteract_mult', text='')
                                for child in col_to_draw.children:
                                    draw_subcols(child, layout_col, level + 1)
                            draw_subcols(item.anim_collection, sub_box)
                        map_box.prop(item, 'use_custom_frame_range')
                        if item.use_custom_frame_range:
                            row = map_box.row()
                            row.prop(item, 'frame_start')
                            row.prop(item, 'frame_end')
                            row.prop(item, 'frameskip')
                layout.separator()
                row = layout.row()
                row.scale_y = 1.5
                row.operator('object.batch_zoetrope_baker', icon='RENDER_ANIMATION')
                layout.separator()
                box = layout.box()
                box.label(text='Export to OBJ', icon='EXPORT')
                box.prop(settings, 'export_dir')
                row_axis = box.row(align=True)
                row_axis.prop(settings, 'export_forward_axis')
                row_axis.prop(settings, 'export_up_axis')
                box.prop(settings, 'use_export_frame_range')
                if settings.use_export_frame_range:
                    row = box.row()
                    row.prop(settings, 'export_frame_start')
                    row.prop(settings, 'export_frame_end')
                    row.prop(settings, 'export_frameskip')
                row = box.row()
                row.scale_y = 1.5
                row.operator('object.export_zoetrope_frames', icon='MESH_DATA', text='Export Frames')
                row = box.row()
                row.scale_y = 1.5
                row.operator('object.import_zoetrope_frames', icon='IMPORT', text='Import Frames')

