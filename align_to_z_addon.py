bl_info = {
    "name": "Align Selection to Z & Export",
    "author": "Antigravity",
    "version": (1, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Align",
    "description": "Aligns geometry and batch exports subcollections to OBJ",
    "category": "Object",
}

import bpy
import bmesh
import mathutils
import os

class OBJECT_OT_align_selection_to_neg_z(bpy.types.Operator):
    """Aligns the object so the selected geometry faces negative Z at Z=0"""
    bl_idname = "object.align_selection_to_neg_z"
    bl_label = "Align to -Z"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        
        is_edit_mode = (obj.mode == 'EDIT')
        if not is_edit_mode:
            bpy.ops.object.mode_set(mode='EDIT')
            
        bm = bmesh.from_edit_mesh(obj.data)
        
        selected_faces = [f for f in bm.faces if f.select]
        
        avg_normal = mathutils.Vector((0, 0, 0))
        avg_center = mathutils.Vector((0, 0, 0))
        
        if selected_faces:
            for f in selected_faces:
                avg_normal += f.normal
                avg_center += f.calc_center_median()
            avg_center /= len(selected_faces)
        else:
            selected_verts = [v for v in bm.verts if v.select]
            if not selected_verts:
                self.report({'WARNING'}, "No geometry selected.")
                if not is_edit_mode:
                    bpy.ops.object.mode_set(mode='OBJECT')
                return {'CANCELLED'}
                
            for v in selected_verts:
                avg_normal += v.normal
                avg_center += v.co
            avg_center /= len(selected_verts)
            
        if avg_normal.length > 0:
            avg_normal.normalize()
        else:
            self.report({'WARNING'}, "Selected geometry has no valid normal.")
            if not is_edit_mode:
                bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')
        
        mat = obj.matrix_world.copy()
        world_center = mat @ avg_center
        world_normal = (mat.to_3x3() @ avg_normal).normalized()
        
        target_normal = mathutils.Vector((0, 0, -1))
        rot_quat = world_normal.rotation_difference(target_normal)
        
        trans_origin = mathutils.Matrix.Translation(-world_center)
        rot_mat = rot_quat.to_matrix().to_4x4()
        target_pos = mathutils.Vector((world_center.x, world_center.y, 0.0))
        trans_back = mathutils.Matrix.Translation(target_pos)
        
        obj.matrix_world = trans_back @ rot_mat @ trans_origin @ obj.matrix_world
        
        if is_edit_mode:
            bpy.ops.object.mode_set(mode='EDIT')
            
        self.report({'INFO'}, f"Successfully aligned object! New center at {target_pos}")
        return {'FINISHED'}

class OBJECT_OT_export_subcollections_obj(bpy.types.Operator):
    """Batch export all subcollections of the selected collection to OBJs"""
    bl_idname = "object.export_subcollections_obj"
    bl_label = "Batch Export Subcollections"
    bl_options = {'REGISTER', 'UNDO'}
    
    directory: bpy.props.StringProperty(
        name="Outdir Path",
        description="Choose a directory for the exported OBJs",
        subtype='DIR_PATH'
    )

    @classmethod
    def poll(cls, context):
        return context.scene.export_parent_collection is not None

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        parent_col = context.scene.export_parent_collection
        if not parent_col:
            self.report({'ERROR'}, "No parent collection selected")
            return {'CANCELLED'}
            
        if not self.directory:
            self.report({'ERROR'}, "No directory selected")
            return {'CANCELLED'}
            
        # Ensure we don't accidentally export hidden/unselected things from earlier ops
        bpy.ops.object.select_all(action='DESELECT')
        
        count = 0
        for sub_col in parent_col.children:
            # Gather valid objects to export in this subcollection
            objs_to_export = [obj for obj in sub_col.objects if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}]
            
            if not objs_to_export:
                continue
                
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objs_to_export:
                # Ensure they are visible in viewport so export works properly
                obj.hide_viewport = False 
                obj.select_set(True)
                
            filepath = os.path.join(self.directory, f"{sub_col.name}.obj")
            
            try:
                # Modern C++ Exporter (Blender 3.2+)
                bpy.ops.wm.obj_export(
                    filepath=filepath,
                    export_selected_objects=True,
                    export_colors=True,
                    forward_axis='X',
                    up_axis='Y',
                    export_triangulated_mesh=True,
                    apply_modifiers=True
                )
            except AttributeError:
                # Fallback for older Blender versions
                bpy.ops.export_scene.obj(
                    filepath=filepath,
                    use_selection=True,
                    use_triangles=True,
                    axis_forward='X',
                    axis_up='Y'
                )
            count += 1
            
        # Clean up selection state
        bpy.ops.object.select_all(action='DESELECT')
            
        self.report({'INFO'}, f"Successfully batch exported {count} subcollections to {self.directory}")
        return {'FINISHED'}

class VIEW3D_PT_align_to_z(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Align'
    bl_label = "Align & Export"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("object.align_selection_to_neg_z", icon='ANCHOR_BOTTOM')
        
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(context.scene, "export_parent_collection", text="Parent Col")
        
        export_col = col.column()
        export_col.enabled = context.scene.export_parent_collection is not None
        export_col.operator("object.export_subcollections_obj", icon='EXPORT')

classes = (
    OBJECT_OT_align_selection_to_neg_z,
    OBJECT_OT_export_subcollections_obj,
    VIEW3D_PT_align_to_z
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register the collection pointer property on the Scene
    bpy.types.Scene.export_parent_collection = bpy.props.PointerProperty(
        name="Parent Collection",
        type=bpy.types.Collection,
        description="Select the parent collection containing the subcollections to export"
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.export_parent_collection

if __name__ == "__main__":
    register()
