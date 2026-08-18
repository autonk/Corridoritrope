import bpy
import math
import os
from mathutils import Vector
from .core_generators import *
from .properties import *

class OBJECT_OT_generate_zoetrope(bpy.types.Operator):
    """Generate a Zoetrope based on the selected settings"""
    bl_idname = 'object.generate_zoetrope'
    bl_label = 'Generate Zoetrope'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        fps = context.scene.render.fps / context.scene.render.fps_base
        if settings.mode == 'BASIC':
            col = create_basic_zoetrope(num_frames=settings.basic_frames, radius=settings.radius, fps=fps)
            self.report({'INFO'}, f'Generated Basic Zoetrope ({settings.basic_frames} frames)')
        elif settings.mode == 'PLANETARY':
            col = create_planetary_zoetrope(P=settings.planets, F=settings.subframes, target_ring_radius=settings.radius, planet_size=settings.planet_size, fps=fps)
            self.report({'INFO'}, f'Generated Planetary Zoetrope ({settings.planets * settings.subframes} frames)')
        settings.active_zoetrope = col
        return {'FINISHED'}

class OBJECT_OT_create_frame_template(bpy.types.Operator):
    """Generate a template mesh representing one frame's bounds for the active Zoetrope"""
    bl_idname = 'object.create_frame_template'
    bl_label = 'Make Frame Template'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        zoe = settings.active_zoetrope
        if not zoe:
            self.report({'WARNING'}, 'No active zoetrope selected!')
            return {'CANCELLED'}
        zoe_type = zoe.get('zoe_type', None)
        if not zoe_type:
            self.report({'WARNING'}, 'Selected collection is not a recognized generated zoetrope!')
            return {'CANCELLED'}
        if zoe_type == 'BASIC':
            radius = zoe.get('zoe_radius', 5.0)
            frames = zoe.get('zoe_frames', 45)
            import bmesh
            mesh = bpy.data.meshes.new('Frame_Template_Mesh')
            obj = bpy.data.objects.new('Frame_Template', mesh)
            context.collection.objects.link(obj)
            bm = bmesh.new()
            center = bm.verts.new((-radius, 0, 0))
            multiplier = max(1, round(1000 / frames))
            if multiplier % 2 != 0:
                multiplier += 1
            total_verts = frames * multiplier
            step = 2 * math.pi / total_verts
            segments = multiplier
            start_angle = -(segments / 2) * step
            arc_verts = []
            for i in range(segments + 1):
                a = start_angle + i * step
                v = bm.verts.new((-radius + radius * math.cos(a), radius * math.sin(a), 0))
                arc_verts.append(v)
            for i in range(segments):
                bm.faces.new((center, arc_verts[i], arc_verts[i + 1]))
            bm.to_mesh(mesh)
            bm.free()
            obj.display_type = 'WIRE'
            obj.show_wire = True
            obj.show_all_edges = True
            obj.show_in_front = True
            self.report({'INFO'}, f'Generated Basic Frame Template (Radius: {radius}, Arc: {360 / frames:.1f}°)')
        elif zoe_type == 'PLANETARY':
            rp = zoe.get('zoe_planet_radius', 1.0)
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=rp, depth=0.1, end_fill_type='NGON', location=(0, 0, 0))
            obj = context.active_object
            obj.name = 'Frame_Template'
            obj.display_type = 'WIRE'
            obj.show_wire = True
            obj.show_all_edges = True
            obj.show_in_front = True
            self.report({'INFO'}, f'Generated Planetary Frame Template (Radius: {rp:.2f})')
        return {'FINISHED'}

class OBJECT_OT_clear_mappings(bpy.types.Operator):
    """Clear all current mappings"""
    bl_idname = 'object.clear_zoetrope_mappings'
    bl_label = 'Clear Mappings'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.zoetrope_mappings.clear()
        return {'FINISHED'}

class OBJECT_OT_batch_zoetrope_baker(bpy.types.Operator):
    """Batch Bake Animations to Zoetropes"""
    bl_idname = 'object.batch_zoetrope_baker'
    bl_label = 'Batch Bake Animations'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        processed_zoetropes = set()
        count = 0
        for item in context.scene.zoetrope_mappings:
            if not item.target_zoetrope or not item.anim_collection:
                continue
            clear_baked = item.target_zoetrope.name not in processed_zoetropes
            self.bake_single_mapping(context, item.anim_collection, item.target_zoetrope, item.mismatch_strategy, clear_baked)
            processed_zoetropes.add(item.target_zoetrope.name)
            count += 1
        if count == 0:
            self.report({'WARNING'}, 'No mappings executed. Please ensure target zoetropes are assigned.')
            return {'CANCELLED'}
        self.report({'INFO'}, f'Batch baked {count} animations successfully!')
        return {'FINISHED'}

    def bake_single_mapping(self, context, anim_col, target_zoetrope, mismatch_strategy, clear_baked=True):
        empties = [obj for obj in target_zoetrope.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY']
        if not empties:
            self.report({'WARNING'}, f"No 'Frame_XXX' empties found in {target_zoetrope.name}!")
            return
        empties.sort(key=lambda x: x.name)
        valid_types = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'POINTCLOUD'}
        exportable_objects = []
        for obj in anim_col.all_objects:
            if obj.type in valid_types:
                exportable_objects.append(obj)
        if not exportable_objects:
            self.report({'WARNING'}, f'No meshes found in {anim_col.name}!')
            return
        mapping_item = None
        for item in context.scene.zoetrope_mappings:
            if item.anim_collection == anim_col and item.target_zoetrope == target_zoetrope:
                mapping_item = item
                break
        if mapping_item and mapping_item.use_custom_frame_range:
            start_frame = mapping_item.frame_start
            max_frame = mapping_item.frame_end
            frameskip = mapping_item.frameskip
        else:
            start_frame = 1
            max_frame = 0
            frameskip = 1
            for obj in exportable_objects:
                if obj.animation_data and obj.animation_data.action:
                    max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
            if max_frame == 0:
                self.report({'WARNING'}, f'No actions with keyframes found in {anim_col.name}! Defaulting to 24.')
                max_frame = 24
        num_empties = len(empties)

        def find_layer_collection(parent, name):
            if parent.name == name:
                return parent
            for child in parent.children:
                res = find_layer_collection(child, name)
                if res:
                    return res
            return None
        layer_col = find_layer_collection(context.view_layer.layer_collection, anim_col.name)
        was_exclude = False
        if layer_col:
            was_exclude = layer_col.exclude
            layer_col.exclude = False
        depsgraph = context.evaluated_depsgraph_get()
        baked_collection = None
        for child in target_zoetrope.children:
            if child.name == 'Baked_Frames':
                baked_collection = child
                break
        if baked_collection:
            if clear_baked:
                for obj in list(baked_collection.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
        else:
            baked_collection = bpy.data.collections.new('Baked_Frames')
            target_zoetrope.children.link(baked_collection)
        anim_frame_count = int(max_frame - start_frame + 1)
        if mismatch_strategy == 'CLIP':
            if anim_frame_count < num_empties:
                start_empty_idx = num_empties - anim_frame_count
                loop_count = anim_frame_count
            else:
                start_empty_idx = 0
                loop_count = num_empties
        else:
            start_empty_idx = 0
            loop_count = num_empties
        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
            anim_length = max_frame - start_frame + 1
            if mismatch_strategy == 'INTERPOLATE':
                target_fbx_frame = start_frame + i / max(1, loop_count - 1) * (anim_length - 1)
            else:
                target_fbx_frame = start_frame + i * frameskip
            context.scene.frame_set(int(target_fbx_frame))
            context.view_layer.update()
            depsgraph = context.evaluated_depsgraph_get()
            counteract_collections = set()

            def find_counteracts(col_iter, current_state):
                state = current_state or getattr(col_iter, 'zoe_counteract_mult', False)
                if state:
                    counteract_collections.add(col_iter.name)
                for child in col_iter.children:
                    find_counteracts(child, state)
            find_counteracts(anim_col, False)
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            temp_obj_path = os.path.join(temp_dir, f'zoetrope_bake_{i}.obj')
            bpy.ops.object.select_all(action='DESELECT')
            for m in exportable_objects:
                if m.name in context.view_layer.objects and (not m.hide_viewport):
                    m.select_set(True)
            bpy.ops.wm.obj_export(filepath=temp_obj_path, export_selected_objects=True, export_uv=True, export_normals=True, export_colors=True, export_materials=False, export_triangulated_mesh=True, export_animation=False, apply_modifiers=True, export_eval_mode='DAG_EVAL_VIEWPORT')
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.wm.obj_import(filepath=temp_obj_path)
            baked_meshes = context.selected_objects
            for new_obj in baked_meshes:
                orig_name = new_obj.name.split('.')[0]
                needs_counteract = False
                for m in exportable_objects:
                    if orig_name in m.name or m.name in orig_name:
                        for c in m.users_collection:
                            if c.name in counteract_collections:
                                needs_counteract = True
                                break
                        break
                new_obj.name = f'Baked_{i + 1:03d}_{orig_name}'
                new_obj['needs_counteract'] = needs_counteract
                if needs_counteract:
                    zoe = target_zoetrope
                    speed_mult = getattr(zoe, 'zoe_speed_mult', 1.0)
                    if speed_mult != 1.0:
                        base_frames = zoe.get('zoe_frames', 1) if zoe.get('zoe_type') == 'BASIC' else zoe.get('zoe_planets', 1) * zoe.get('zoe_subframes', 1)
                        if base_frames > 0:
                            import math
                            drift_angle = empty_idx * (speed_mult - 1.0) * (2 * math.pi / base_frames)
                            root_obj = empties[0].parent
                            if root_obj:
                                is_inverted = getattr(zoe, 'zoe_invert', False)
                                rot_sign = -1 if is_inverted else 1
                                num_copies = max(1, int(math.ceil(abs(speed_mult))))
                                template_obj = bpy.data.objects.get('Frame_Template')
                                t_mat = template_obj.matrix_world if template_obj else mathutils.Matrix.Identity(4)
                                t_inv = t_mat.inverted()
                                for k in range(num_copies):
                                    if k == 0:
                                        obj_to_transform = new_obj
                                    else:
                                        copy_mesh = new_obj.data.copy()
                                        obj_to_transform = bpy.data.objects.new(f'{new_obj.name}_copy{k}', copy_mesh)
                                        obj_to_transform.matrix_world = new_obj.matrix_world.copy()
                                        obj_to_transform['needs_counteract'] = needs_counteract
                                        context.scene.collection.objects.link(obj_to_transform)
                                        baked_meshes.append(obj_to_transform)
                                    offset_angle = k * (2 * math.pi / base_frames)
                                    rot_mat = mathutils.Matrix.Rotation(rot_sign * (drift_angle - offset_angle), 4, 'Z')
                                    zoe_rot = root_obj.matrix_world @ rot_mat @ root_obj.matrix_world.inverted()
                                    pre_transform = t_mat @ empties[empty_idx].matrix_world.inverted() @ zoe_rot @ empties[empty_idx].matrix_world @ t_inv
                                    obj_to_transform.matrix_world = pre_transform @ obj_to_transform.matrix_world
                for col_old in list(new_obj.users_collection):
                    col_old.objects.unlink(new_obj)
                baked_collection.objects.link(new_obj)
            if not baked_meshes:
                continue
            bpy.ops.object.select_all(action='DESELECT')
            for b in baked_meshes:
                b.select_set(True)
            context.view_layer.objects.active = baked_meshes[0]
            if len(baked_meshes) > 1:
                bpy.ops.object.join()
            combined = context.active_object
            combined.name = f'Anim_Frame_{i + 1:03d}'
            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                template_obj = bpy.data.objects.get('Frame_Template')
                if template_obj:
                    o_mat_inv = template_obj.matrix_world.inverted()
                    orig_matrix = o_mat_inv @ orig_matrix
                combined.parent = empty
                combined.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                combined.matrix_local = orig_matrix
        context.scene.frame_set(1)
        if layer_col:
            layer_col.exclude = was_exclude

class OBJECT_OT_export_zoetrope_frames(bpy.types.Operator):
    """Export Mapped Animations to OBJ Frames"""
    bl_idname = 'object.export_zoetrope_frames'
    bl_label = 'Export Frames to OBJ'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        outdir = bpy.path.abspath(settings.export_dir)
        if not outdir:
            self.report({'WARNING'}, 'Please specify an export directory.')
            return {'CANCELLED'}
        import os
        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except Exception as e:
                self.report({'ERROR'}, f'Failed to create directory: {e}')
                return {'CANCELLED'}
        count = 0
        for item in context.scene.zoetrope_mappings:
            if not item.target_zoetrope or not item.anim_collection:
                continue
            self.export_single_mapping(context, item.anim_collection, item.target_zoetrope, item.mismatch_strategy, outdir)
            count += 1
        if count == 0:
            self.report({'WARNING'}, 'No mappings found to export.')
            return {'CANCELLED'}
        self.report({'INFO'}, f'Successfully exported {count} animations!')
        return {'FINISHED'}

    def export_single_mapping(self, context, anim_col, target_zoetrope, mismatch_strategy, outdir):
        empties = [obj for obj in target_zoetrope.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY']
        if not empties:
            self.report({'WARNING'}, f"No 'Frame_XXX' empties found in {target_zoetrope.name}!")
            return
        empties.sort(key=lambda x: x.name)
        valid_types = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'POINTCLOUD'}
        exportable_objects = []
        for obj in anim_col.all_objects:
            if obj.type in valid_types:
                exportable_objects.append(obj)
        if not exportable_objects:
            self.report({'WARNING'}, f'No exportable objects found in {anim_col.name}!')
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
                self.report({'WARNING'}, f'No actions with keyframes found in {anim_col.name}! Defaulting to 24 frames.')
                max_frame = 24
        num_empties = len(empties)

        def find_layer_collection(parent, name):
            if parent.name == name:
                return parent
            for child in parent.children:
                res = find_layer_collection(child, name)
                if res:
                    return res
            return None
        layer_col = find_layer_collection(context.view_layer.layer_collection, anim_col.name)
        was_exclude = False
        if layer_col:
            was_exclude = layer_col.exclude
            layer_col.exclude = False
        depsgraph = context.evaluated_depsgraph_get()
        anim_frame_count = int(max_frame - start_frame + 1)
        if mismatch_strategy == 'CLIP':
            if anim_frame_count < num_empties:
                start_empty_idx = num_empties - anim_frame_count
                loop_count = anim_frame_count
            else:
                start_empty_idx = 0
                loop_count = num_empties
        else:
            start_empty_idx = 0
            loop_count = num_empties
        settings = context.scene.zoetrope_generator
        if settings.use_export_frame_range:
            loop_count = (settings.export_frame_end - settings.export_frame_start) // max(1, settings.export_frameskip) + 1
        context.window_manager.progress_begin(0, loop_count)
        bpy.ops.object.select_all(action='DESELECT')
        import os
        for i in range(loop_count):
            if settings.use_export_frame_range:
                target_fbx_frame = settings.export_frame_start + i * settings.export_frameskip
            else:
                empty_idx = start_empty_idx + i
                if empty_idx >= num_empties:
                    break
                anim_length = max_frame - start_frame + 1
                if mismatch_strategy == 'INTERPOLATE':
                    target_fbx_frame = start_frame + i / max(1, loop_count - 1) * (anim_length - 1)
                else:
                    target_fbx_frame = start_frame + i
            context.scene.frame_set(int(target_fbx_frame))
            context.view_layer.update()
            depsgraph = context.evaluated_depsgraph_get()
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_obj_path = os.path.join(temp_dir, f'zoetrope_temp_export_{i}.obj')
            bpy.ops.object.select_all(action='DESELECT')
            for m in exportable_objects:
                if m.name in context.view_layer.objects and (not m.hide_viewport):
                    m.select_set(True)
            bpy.ops.wm.obj_export(filepath=temp_obj_path, export_selected_objects=True, export_uv=True, export_normals=True, export_colors=True, export_materials=False, export_triangulated_mesh=True, export_animation=False, apply_modifiers=True, export_eval_mode='DAG_EVAL_VIEWPORT')
            bpy.ops.object.select_all(action='DESELECT')
            try:
                bpy.ops.wm.obj_import(filepath=temp_obj_path)
            except AttributeError:
                bpy.ops.import_scene.obj(filepath=temp_obj_path)
            imported_objects = context.selected_objects
            if imported_objects:
                template_obj = bpy.data.objects.get('Frame_Template')
                if template_obj:
                    o_mat_inv = template_obj.matrix_world.inverted()
                    for o in imported_objects:
                        o.matrix_world = o_mat_inv @ o.matrix_world
                context.view_layer.objects.active = imported_objects[0]
                if len(imported_objects) > 1:
                    bpy.ops.object.join()
                final_obj = context.view_layer.objects.active
                prefix = anim_col.name.replace(' ', '_')
                out_path = os.path.join(outdir, f'{prefix}_frame_{i + 1:03d}.obj')
                bpy.ops.object.select_all(action='DESELECT')
                final_obj.select_set(True)
                try:
                    try:
                        try:
                            bpy.ops.wm.obj_export(filepath=out_path, export_selected_objects=True, export_colors=True, export_triangulated_mesh=True, up_axis=settings.export_up_axis, forward_axis=settings.export_forward_axis)
                        except TypeError:
                            bpy.ops.wm.obj_export(filepath=out_path, export_selected_objects=True, up_axis=settings.export_up_axis, forward_axis=settings.export_forward_axis)
                    except AttributeError:
                        bpy.ops.export_scene.obj(filepath=out_path, use_selection=True, use_triangles=True, axis_up=settings.export_up_axis, axis_forward=settings.export_forward_axis)
                except Exception as e:
                    self.report({'ERROR'}, f'Failed to export OBJ {out_path}: {e}')
                    print(f'Export Error: {e}')
                final_mesh = final_obj.data
                bpy.data.objects.remove(final_obj, do_unlink=True)
                if final_mesh:
                    bpy.data.meshes.remove(final_mesh, do_unlink=True)
            if os.path.exists(temp_obj_path):
                try:
                    os.remove(temp_obj_path)
                except:
                    pass
            mtl_path = temp_obj_path.replace('.obj', '.mtl')
            if os.path.exists(mtl_path):
                try:
                    os.remove(mtl_path)
                except:
                    pass
            context.window_manager.progress_update(i + 1)
        context.window_manager.progress_end()
        context.scene.frame_set(1)
        if layer_col:
            layer_col.exclude = was_exclude

class OBJECT_OT_import_zoetrope_frames(bpy.types.Operator):
    """Import OBJ Frames and map them to Zoetrope"""
    bl_idname = 'object.import_zoetrope_frames'
    bl_label = 'Import Frames from OBJ'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        outdir = bpy.path.abspath(settings.export_dir)
        if not outdir:
            self.report({'WARNING'}, 'Please specify an export directory.')
            return {'CANCELLED'}
        import os
        if not os.path.exists(outdir):
            self.report({'ERROR'}, 'Export directory does not exist.')
            return {'CANCELLED'}
        count = 0
        for item in context.scene.zoetrope_mappings:
            if not item.target_zoetrope or not item.anim_collection:
                continue
            self.import_single_mapping(context, item.anim_collection, item.target_zoetrope, item.mismatch_strategy, outdir)
            count += 1
        if count == 0:
            self.report({'WARNING'}, 'No mappings found to import.')
            return {'CANCELLED'}
        return {'FINISHED'}

    def import_single_mapping(self, context, anim_col, target_zoetrope, mismatch_strategy, outdir):
        import os
        import glob
        import mathutils
        prefix = anim_col.name.replace(' ', '_')
        search_pattern = os.path.join(outdir, f'{prefix}_frame_*.obj')
        files = sorted(glob.glob(search_pattern))
        if not files:
            self.report({'WARNING'}, f'No OBJs found for {anim_col.name} in {outdir}')
            return
        empties = [obj for obj in target_zoetrope.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY']
        if not empties:
            self.report({'WARNING'}, f"No 'Frame_XXX' empties found in {target_zoetrope.name}!")
            return
        empties.sort(key=lambda x: x.name)
        num_empties = len(empties)
        max_frame = len(files)
        imported_collection = None
        for child in target_zoetrope.children:
            if child.name == 'Imported_Frames':
                imported_collection = child
                break
        if imported_collection:
            for obj in list(imported_collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            imported_collection = bpy.data.collections.new('Imported_Frames')
            target_zoetrope.children.link(imported_collection)
        if mismatch_strategy == 'CLIP':
            if max_frame < num_empties:
                start_empty_idx = num_empties - int(max_frame)
                loop_count = int(max_frame)
            else:
                start_empty_idx = 0
                loop_count = num_empties
        else:
            start_empty_idx = 0
            loop_count = num_empties
        context.window_manager.progress_begin(0, loop_count)
        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
            if mismatch_strategy == 'INTERPOLATE':
                target_file_idx = int(round(i / max(1, loop_count - 1) * (max_frame - 1)))
            else:
                target_file_idx = i
            if target_file_idx >= len(files):
                continue
            filepath = files[target_file_idx]
            objs_before = set(bpy.data.objects)
            try:
                try:
                    bpy.ops.wm.obj_import(filepath=filepath)
                except AttributeError:
                    bpy.ops.import_scene.obj(filepath=filepath)
            except Exception as e:
                self.report({'ERROR'}, f'Failed to import {os.path.basename(filepath)}: {e}')
                continue
            objs_after = set(bpy.data.objects)
            imported_objs = list(objs_after - objs_before)
            if not imported_objs:
                continue
            bpy.ops.object.select_all(action='DESELECT')
            for obj in imported_objs:
                obj.select_set(True)
            context.view_layer.objects.active = imported_objs[0]
            if len(imported_objs) > 1:
                bpy.ops.object.join()
            combined = context.view_layer.objects.active
            combined.name = f'Imported_{i + 1:03d}_{prefix}'
            imported_collection.objects.link(combined)
            for coll in combined.users_collection:
                if coll != imported_collection:
                    coll.objects.unlink(combined)
            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                template_obj = bpy.data.objects.get('Frame_Template')
                if template_obj:
                    o_mat_inv = template_obj.matrix_world.inverted()
                    orig_matrix = o_mat_inv @ orig_matrix
                combined.parent = empty
                combined.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                combined.matrix_local = orig_matrix
            context.window_manager.progress_update(i + 1)
        context.window_manager.progress_end()

class OBJECT_OT_import_raw_zoetrope_frames(bpy.types.Operator):
    """Import all OBJ files from a directory onto the active zoetrope sequentially"""
    bl_idname = 'object.import_raw_zoetrope_frames'
    bl_label = 'Import Raw Frames'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        zoe = settings.active_zoetrope
        outdir = bpy.path.abspath(settings.export_dir)
        if not zoe:
            self.report({'WARNING'}, 'No active zoetrope selected.')
            return {'CANCELLED'}
        import os
        import glob
        import mathutils
        search_pattern = os.path.join(outdir, '*.obj')
        files = sorted(glob.glob(search_pattern))
        if not files:
            self.report({'WARNING'}, f'No OBJ files found in {outdir}')
            return {'CANCELLED'}
        empties = [obj for obj in zoe.all_objects if ('Frame_' in obj.name or 'Slot' in obj.name) and obj.type == 'EMPTY']
        if not empties:
            self.report({'WARNING'}, f"No 'Frame_XXX' empties found in {zoe.name}!")
            return {'CANCELLED'}
        empties.sort(key=lambda x: x.name)
        num_empties = len(empties)
        num_files = len(files)
        imported_collection = None
        for child in zoe.children:
            if child.name == 'Imported_Frames':
                imported_collection = child
                break
        if imported_collection:
            for obj in list(imported_collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            imported_collection = bpy.data.collections.new('Imported_Frames')
            zoe.children.link(imported_collection)
        context.window_manager.progress_begin(0, num_empties)
        mismatch_strategy = settings.raw_mismatch_strategy
        for i in range(num_empties):
            if mismatch_strategy == 'CLIP':
                if num_files < num_empties:
                    start_empty_idx = num_empties - num_files
                    if i < start_empty_idx:
                        continue
                    file_idx = i - start_empty_idx
                else:
                    file_idx = i
            else:
                file_idx = int(round(i / max(1, num_empties - 1) * (num_files - 1)))
            if file_idx >= num_files:
                break
            filepath = files[file_idx]
            objs_before = set(bpy.data.objects)
            try:
                try:
                    bpy.ops.wm.obj_import(filepath=filepath)
                except AttributeError:
                    bpy.ops.import_scene.obj(filepath=filepath)
            except Exception as e:
                self.report({'ERROR'}, f'Failed to import {os.path.basename(filepath)}: {e}')
                continue
            objs_after = set(bpy.data.objects)
            imported_objs = list(objs_after - objs_before)
            if not imported_objs:
                continue
            bpy.ops.object.select_all(action='DESELECT')
            for obj in imported_objs:
                obj.select_set(True)
            context.view_layer.objects.active = imported_objs[0]
            if len(imported_objs) > 1:
                bpy.ops.object.join()
            combined = context.view_layer.objects.active
            combined.name = f'Imported_{i + 1:03d}_{os.path.splitext(os.path.basename(filepath))[0]}'
            imported_collection.objects.link(combined)
            for coll in combined.users_collection:
                if coll != imported_collection:
                    coll.objects.unlink(combined)
            empty = empties[i]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                combined.parent = empty
                combined.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                combined.matrix_local = orig_matrix
            context.window_manager.progress_update(i + 1)
        context.window_manager.progress_end()
        return {'FINISHED'}

class OBJECT_OT_clear_all_frames(bpy.types.Operator):
    """Deletes all baked and imported frames from the active zoetrope"""
    bl_idname = 'object.clear_all_frames'
    bl_label = 'Clear All Frames'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        zoe = settings.active_zoetrope
        if not zoe:
            self.report({'WARNING'}, 'No active zoetrope selected.')
            return {'CANCELLED'}
        cleared = 0
        for child in list(zoe.children):
            if child.name in ['Baked_Frames', 'Imported_Frames']:
                for obj in list(child.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                cleared += 1
        if cleared == 0:
            self.report({'INFO'}, 'No frames found to clear.')
        else:
            self.report({'INFO'}, 'Successfully cleared all frames.')
        return {'FINISHED'}

