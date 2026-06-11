bl_info = {
    "name": "Zoetrope Generator Pro",
    "author": "Corridor Crew",
    "version": (1, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Zoetrope",
    "description": "A fully integrated toolset for generating Basic and Planetary Zoetropes with Animation Baking.",
    "warning": "",
    "doc_url": "",
    "category": "Animation",
}

import bpy
import math
from mathutils import Vector
import mathutils

import urllib.request
import urllib.error
import os
import json
import base64
import threading
from datetime import datetime

# ========================================================================
# AUTO-UPDATER SETTINGS
# ========================================================================
GITHUB_USER = "autonk"
GITHUB_REPO = "ZOETROPE-PROJECT"
GITHUB_BRANCH = "main"
GITHUB_FILE_PATH = "ADDON/zoetrope_generator_addon.py"
GITHUB_TOKEN = "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"
# ========================================================================

remote_info = {'checked': False, 'has_update': False, 'sha': None, 'date': None}

def get_metadata_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "zoetrope_updater_meta.json")

def get_local_meta():
    path = get_metadata_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception: pass
    return {'sha': None, 'date': None}

def save_local_meta(sha, date_str):
    try:
        with open(get_metadata_path(), 'w', encoding='utf-8') as f:
            json.dump({'sha': sha, 'date': date_str}, f)
    except Exception: pass

import time

def get_github_headers():
    headers = {
        'User-Agent': 'Mozilla/5.0 Blender Addon Updater', 
        'Accept': 'application/vnd.github.v3+json',
        'Cache-Control': 'no-cache'
    }
    if GITHUB_TOKEN and "XXXXX" not in GITHUB_TOKEN:
        headers['Authorization'] = f"Bearer {GITHUB_TOKEN}"
    return headers

def format_date(iso_str):
    if not iso_str: return "Unknown"
    try:
        dt = datetime.strptime(iso_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%b %d, %Y - %H:%M")
    except: return iso_str

def background_check_thread():
    global remote_info
    commits_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?path={GITHUB_FILE_PATH}&sha={GITHUB_BRANCH}&per_page=1&t={time.time()}"
    try:
        req = urllib.request.Request(commits_url, headers=get_github_headers())
        with urllib.request.urlopen(req) as response:
            commits = json.loads(response.read().decode('utf-8'))
        if commits:
            remote_sha = commits[0].get('sha')
            remote_date = commits[0].get('commit', {}).get('author', {}).get('date')
            local_sha = get_local_meta().get('sha')
            remote_info.update({'sha': remote_sha, 'date': remote_date, 'has_update': (remote_sha != local_sha), 'checked': True})
    except Exception: pass

def start_background_check():
    t = threading.Thread(target=background_check_thread)
    t.daemon = True
    t.start()

def force_download_update():
    commits_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?path={GITHUB_FILE_PATH}&sha={GITHUB_BRANCH}&per_page=1&t={time.time()}"
    content_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}?ref={GITHUB_BRANCH}&t={time.time()}"
    headers = get_github_headers()
    try:
        req_c = urllib.request.Request(commits_url, headers=headers)
        with urllib.request.urlopen(req_c) as response:
            commits = json.loads(response.read().decode('utf-8'))
        if not commits: return False, "No commits found."
        remote_sha = commits[0].get('sha')
        remote_date = commits[0].get('commit', {}).get('author', {}).get('date')
        
        req_f = urllib.request.Request(content_url, headers=headers)
        with urllib.request.urlopen(req_f) as response:
            data = json.loads(response.read().decode('utf-8'))
        content_b64 = data.get('content', '')
        if not content_b64: return False, "Empty content."
        code = base64.b64decode(content_b64).decode('utf-8')
        
        with open(os.path.realpath(__file__), 'w', encoding='utf-8') as f:
            f.write(code)
            
        save_local_meta(remote_sha, remote_date)
        remote_info['has_update'] = False
        return True, "Update downloaded! Please RESTART Blender to apply changes."
    except Exception as e:
        return False, str(e)

class ZOETROPE_OT_update_self(bpy.types.Operator):
    bl_idname = "zoetrope.update_self"
    bl_label = "Update Now"
    bl_description = "Downloads and applies the latest update"
    def execute(self, context):
        success, msg = force_download_update()
        if not success:
            self.report({'ERROR'}, f"Update failed: {msg}")
        else:
            self.report({'INFO'}, msg)
            def draw(self, context):
                self.layout.label(text="Update Downloaded successfully!")
                self.layout.label(text="Please restart Blender for the changes to take effect.", icon='INFO')
            bpy.context.window_manager.popup_menu(draw, title="Zoetrope Updater", icon='INFO')
        return {'FINISHED'}

class ZOETROPE_OT_check_updates(bpy.types.Operator):
    bl_idname = "zoetrope.check_updates"
    bl_label = "Check Latest Update"
    bl_description = "Checks GitHub for the latest version"
    def execute(self, context):
        global remote_info
        remote_info['checked'] = False
        start_background_check()
        return {'FINISHED'}

class ZOETROPE_PT_updater_panel(bpy.types.Panel):
    bl_label = "Zoetrope Updater"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zoetrope'
    bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        local_meta = get_local_meta()
        box = layout.box()
        box.label(text="Current Version:", icon='FILE_TICK')
        col = box.column(align=True)
        if local_meta.get('sha'):
            col.label(text=f"Commit: {local_meta['sha'][:7]}")
            col.label(text=f"Date: {format_date(local_meta['date'])}")
        else:
            col.label(text="Status: Unversioned (Initial Install)")
            
        if remote_info['checked']:
            if remote_info['has_update']:
                warn_box = layout.box()
                warn_box.label(text="⚠️ Update Available!", icon='ERROR')
                wcol = warn_box.column(align=True)
                wcol.label(text=f"New Commit: {remote_info['sha'][:7]}")
                wcol.label(text=f"New Date: {format_date(remote_info['date'])}")
                layout.separator()
                layout.operator("zoetrope.update_self", icon='IMPORT', text="Download Update")
            else:
                layout.separator()
                layout.label(text="You are on the latest version.", icon='CHECKMARK')
                layout.operator("zoetrope.check_updates", icon='URL', text="Check Latest Update")
                layout.operator("zoetrope.update_self", icon='FILE_REFRESH', text="Force Re-download")
        else:
            layout.separator()
            layout.label(text="Checking GitHub for updates...", icon='TIME')
            layout.operator("zoetrope.update_self", icon='FILE_REFRESH', text="Manual Update")

# ==============================================================================
# BASIC ZOETROPE GENERATOR
# ==============================================================================

def create_basic_zoetrope(num_frames=33, radius=5.0, fps=30.0):
    idx = 1
    while bpy.data.collections.get(f"Basic_Zoetrope_{idx:03d}"):
        idx += 1
    main_col_name = f"Basic_Zoetrope_{idx:03d}"
    main_col = bpy.data.collections.new(main_col_name)
    main_col['zoe_type'] = 'BASIC'
    main_col['zoe_radius'] = radius
    main_col['zoe_frames'] = num_frames
    bpy.context.scene.collection.children.link(main_col)
    
    frames_col = bpy.data.collections.new("Frames")
    main_col.children.link(frames_col)
    
    multiplier = max(1, round(1000 / num_frames))
    if multiplier % 2 != 0:
        multiplier += 1
    total_verts = num_frames * multiplier
    main_col['zoe_verts_total'] = total_verts
    main_col['zoe_verts_per_frame'] = multiplier
    
    verts = []
    edges = []
    angle_step = (2 * math.pi) / total_verts
    
    for i in range(total_verts):
        angle = i * angle_step
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts.append((x, y, 0))
        edges.append((i, (i + 1) % total_verts))
        
    mesh = bpy.data.meshes.new("Basic_Zoetrope_Mesh")
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    
    zoetrope = bpy.data.objects.new("Basic_Zoetrope", mesh)
    main_col.objects.link(zoetrope)
    
    drv = zoetrope.driver_add('rotation_euler', 2).driver
    drv.type = 'SCRIPTED'
    
    var = drv.variables.new()
    var.name = 'frame'
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'SCENE'
    var.targets[0].id = bpy.context.scene
    var.targets[0].data_path = 'frame_current'
    
    expr = f"-(frame - 1) * ({2 * math.pi} / {num_frames})"
    drv.expression = expr
    zoetrope['base_driver_expr'] = expr
    
    frame_angle_step = (2 * math.pi) / num_frames
    for i in range(num_frames):
        angle = i * frame_angle_step
        empty = bpy.data.objects.new(f"Frame_{(i+1):03d}", None)
        empty.empty_display_size = 0.5
        empty.empty_display_type = 'ARROWS'
        empty.show_name = True
        
        frames_col.objects.link(empty)
        empty.location = (radius * math.cos(angle), radius * math.sin(angle), 0)
        
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        empty.rotation_euler = direction.to_track_quat('Y', 'Z').to_euler()
        
        empty.parent = zoetrope
        empty.matrix_parent_inverse = zoetrope.matrix_world.inverted()
        
    bpy.context.scene.frame_set(1)
    return main_col

# ==============================================================================
# PLANETARY GEAR ZOETROPE GENERATOR
# ==============================================================================

def create_gear(name, num_teeth, module, thickness=0.2, col=None):
    if col is None: col = bpy.context.collection
    verts = []
    faces = []
    
    pitch_radius = (module * num_teeth) / 2
    addendum = module
    dedendum = 1.25 * module
    base_radius = pitch_radius - dedendum
    outer_radius = pitch_radius + addendum
    tooth_angle = (2 * math.pi) / num_teeth
    
    for i in range(num_teeth):
        base_angle = i * tooth_angle
        
        a1 = base_angle - tooth_angle * 0.25
        verts.append((base_radius * math.cos(a1), base_radius * math.sin(a1), thickness/2))
        verts.append((outer_radius * math.cos(a1 + tooth_angle * 0.05), outer_radius * math.sin(a1 + tooth_angle * 0.05), thickness/2))
        a2 = base_angle + tooth_angle * 0.25
        verts.append((outer_radius * math.cos(a2 - tooth_angle * 0.05), outer_radius * math.sin(a2 - tooth_angle * 0.05), thickness/2))
        verts.append((base_radius * math.cos(a2), base_radius * math.sin(a2), thickness/2))
    
    num_front = len(verts)
    for i in range(num_front):
        x, y, z = verts[i]
        verts.append((x, y, -thickness/2))
    
    for i in range(num_teeth):
        base = i * 4
        next_base = ((i + 1) % num_teeth) * 4
        faces.append((base, base + 1, base + 2, base + 3))
        back = base + num_front
        faces.append((back + 3, back + 2, back + 1, back))
        for j in range(3):
            faces.append((base + j, base + j + 1, base + j + 1 + num_front, base + j + num_front))
        faces.append((base + 3, next_base, next_base + num_front, base + 3 + num_front))
    
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    
    obj['sun_teeth'] = num_teeth if 'Sun' in name else None
    obj['ring_teeth'] = num_teeth if 'Ring' in name else None
    obj['planet_teeth'] = num_teeth if 'Planet' in name else None
    
    return obj

def create_ring_gear(name, num_teeth, module, thickness=0.2, rim_thickness=0.3, col=None):
    if col is None: col = bpy.context.collection
    verts = []
    faces = []
    
    pitch_radius = (module * num_teeth) / 2
    addendum = module
    dedendum = 1.25 * module
    inner_radius = pitch_radius - addendum
    outer_radius = pitch_radius + dedendum
    outer_rim_radius = outer_radius + rim_thickness
    tooth_angle = (2 * math.pi) / num_teeth
    
    a1 = -tooth_angle * 0.25
    verts.append((outer_rim_radius * math.cos(a1), outer_rim_radius * math.sin(a1), thickness/2))
    verts.append((outer_radius * math.cos(a1), outer_radius * math.sin(a1), thickness/2))
    a2 = -tooth_angle * 0.05
    verts.append((inner_radius * math.cos(a2), inner_radius * math.sin(a2), thickness/2))
    a3 = tooth_angle * 0.05
    verts.append((inner_radius * math.cos(a3), inner_radius * math.sin(a3), thickness/2))
    a4 = tooth_angle * 0.25
    verts.append((outer_radius * math.cos(a4), outer_radius * math.sin(a4), thickness/2))
    verts.append((outer_rim_radius * math.cos(a4), outer_rim_radius * math.sin(a4), thickness/2))
    
    for i in range(6):
        x, y, z = verts[i]
        verts.append((x, y, -thickness/2))
    
    faces.append((1, 2, 3, 4))
    faces.append((0, 1, 4, 5))
    faces.append((7, 8, 9, 10))
    faces.append((11, 10, 7, 6))
    faces.append((0, 1, 7, 6))
    faces.append((1, 2, 8, 7))
    faces.append((2, 3, 9, 8))
    faces.append((3, 4, 10, 9))
    faces.append((4, 5, 11, 10))
    faces.append((5, 0, 6, 11))
    
    mesh = bpy.data.meshes.new(name + "_tooth")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    min_distance = float('inf')
    target_face = None
    
    for face_idx, face in enumerate(obj.data.polygons):
        center = face.center
        distance = math.sqrt(center.x**2 + center.y**2 + center.z**2)
        if distance < min_distance:
            min_distance = distance
            target_face = face_idx
            
    obj.data.polygons[target_face].select = True
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    bpy.ops.transform.resize(value=(1, 4, 1), constraint_axis=(False, True, False))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    array_mod = obj.modifiers.new(name="Array", type='ARRAY')
    array_mod.count = num_teeth
    array_mod.use_relative_offset = False
    array_mod.use_object_offset = False
    array_mod.use_constant_offset = False
    
    empty = bpy.data.objects.new(name + "_pivot", None)
    empty.location = (0, 0, 0)
    col.objects.link(empty)
    
    array_mod.use_object_offset = True
    array_mod.offset_object = empty
    empty.rotation_euler[2] = tooth_angle
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Array")
    bpy.data.objects.remove(empty, do_unlink=True)
    
    obj['ring_teeth'] = num_teeth
    return obj

def find_best_ring_teeth(num_planet_gears, planet_size=1.0):
    valid_configs = []
    for planet_teeth in range(6, 33):
        for sun_teeth in range(planet_teeth, planet_teeth * 15):
            ring_teeth = sun_teeth + 2 * planet_teeth
            if (ring_teeth + sun_teeth) % num_planet_gears != 0:
                continue
            
            sun_radius = sun_teeth / 2
            planet_radius = planet_teeth / 2
            carrier_radius = sun_radius + planet_radius
            spacing = (2 * math.pi * carrier_radius) / num_planet_gears
            planet_diameter = 2 * planet_radius
            
            if planet_diameter < spacing * 0.92:
                ratio = planet_teeth / sun_teeth
                valid_configs.append((ratio, ring_teeth, sun_teeth, planet_teeth))
                
    if not valid_configs:
        ring_teeth = num_planet_gears * 8
        planet_teeth = 12
        sun_teeth = ring_teeth - 2 * planet_teeth
        return (ring_teeth, sun_teeth, planet_teeth)
        
    best_per_ratio = {}
    for ratio, r_t, s_t, p_t in valid_configs:
        round_ratio = round(ratio, 4)
        if round_ratio not in best_per_ratio:
            best_per_ratio[round_ratio] = (r_t, s_t, p_t)
        else:
            curr_best = best_per_ratio[round_ratio]
            if abs(p_t - 16) < abs(curr_best[2] - 16):
                best_per_ratio[round_ratio] = (r_t, s_t, p_t)
                
    unique_configs = list(best_per_ratio.items())
    unique_configs.sort(key=lambda x: x[0])
    
    idx = int(planet_size * (len(unique_configs) - 1))
    if idx < 0: idx = 0
    if idx >= len(unique_configs): idx = len(unique_configs) - 1
    
    return unique_configs[idx][1]

def generate_planetary_gearbox(num_planet_gears=10, target_ring_radius=4.0, planet_size=1.0, col=None):
    if col is None: col = bpy.context.collection
    ring_teeth, sun_teeth, planet_teeth = find_best_ring_teeth(num_planet_gears, planet_size=planet_size)
    module = (2 * target_ring_radius) / ring_teeth
    sun_radius = (module * sun_teeth) / 2
    planet_radius = (module * planet_teeth) / 2
    ring_radius = (module * ring_teeth) / 2
    carrier_radius = sun_radius + planet_radius
    
    sun = create_gear("Sun_Gear", sun_teeth, module, 0.3, col=col)
    ring = create_ring_gear("Ring_Gear", ring_teeth, module, 0.3, 0.5, col=col)
    if planet_teeth % 2 != 0:
        ring.rotation_euler[2] = math.pi / ring_teeth
    
    carrier = bpy.data.objects.new("Carrier", None)
    carrier.empty_display_type = 'ARROWS'
    carrier.empty_display_size = carrier_radius * 0.5
    col.objects.link(carrier)
    
    planets = []
    for i in range(num_planet_gears):
        angle = (2 * math.pi * i) / num_planet_gears
        x = carrier_radius * math.cos(angle)
        y = carrier_radius * math.sin(angle)
        
        empty = bpy.data.objects.new(f"Planet_Position_{i+1}", None)
        empty.empty_display_type = 'PLAIN_AXES'
        empty.empty_display_size = planet_radius * 0.5
        col.objects.link(empty)
        empty.location = (x, y, 0)
        empty.parent = carrier
        
        planet = create_gear(f"Planet_Gear_{i+1}", planet_teeth, module, 0.25, col=col)
        planet.location = (x, y, 0)
        planets.append(planet)
        
        con = planet.constraints.new('COPY_LOCATION')
        con.target = empty
        
    return {
        'sun': sun, 'ring': ring, 'carrier': carrier, 'planets': planets,
        'params': {'P': num_planet_gears, 'Ns': sun_teeth, 'Np': planet_teeth, 'Nr': ring_teeth,
                   'Rp': planet_radius, 'Rc': carrier_radius}
    }

def create_planetary_zoetrope(P=10, F=5, target_ring_radius=4.0, planet_size=1.0, fps=30.0):
    idx = 1
    while bpy.data.collections.get(f"Planetary_Zoetrope_{idx:03d}"):
        idx += 1
    main_col_name = f"Planetary_Zoetrope_{idx:03d}"
    main_col = bpy.data.collections.new(main_col_name)
    bpy.context.scene.collection.children.link(main_col)
    
    frames_col = bpy.data.collections.new("Frames")
    main_col.children.link(frames_col)
            
    result = generate_planetary_gearbox(P, target_ring_radius=target_ring_radius, planet_size=planet_size, col=main_col)
    sun, ring, carrier, planets = result['sun'], result['ring'], result['carrier'], result['planets']
    Ns, Nr, Np, Rp, Rc = result['params']['Ns'], result['params']['Nr'], result['params']['Np'], result['params']['Rp'], result['params']['Rc']
    
    main_col['zoe_type'] = 'PLANETARY'
    main_col['zoe_planet_radius'] = Rp
    
    S_rel = - (P // F) + 1.0 / F
    if S_rel == 0: S_rel = 1.0 / F
    
    a = (Ns/(Ns+Nr)) - (Ns*Nr)/(Np*(Ns+Nr))
    b = (Nr/(Ns+Nr)) + (Ns*Nr)/(Np*(Ns+Nr))
    left = S_rel * Nr / (Ns+Nr) - b
    right = a - S_rel * Ns / (Ns+Nr)
    K = right / left
    M = a + b * K
    slope_c = (Ns + Nr*K) / (Ns + Nr)
    
    drv_ring = ring.driver_add('rotation_euler', 2).driver
    drv_ring.type = 'SCRIPTED'
    var = drv_ring.variables.new()
    var.name, var.type = 'Srot', 'TRANSFORMS'
    var.targets[0].id, var.targets[0].transform_type = sun, 'ROT_Z'
    var.targets[0].transform_space = 'TRANSFORM_SPACE'
    drv_ring.expression = f"Srot * {K}"
    
    drv_carrier = carrier.driver_add('rotation_euler', 2).driver
    drv_carrier.type = 'SCRIPTED'
    var_s, var_r = drv_carrier.variables.new(), drv_carrier.variables.new()
    var_s.name, var_r.name = 'Srot', 'Rrot'
    var_s.type, var_r.type = 'TRANSFORMS', 'TRANSFORMS'
    var_s.targets[0].id, var_s.targets[0].transform_type = sun, 'ROT_Z'
    var_s.targets[0].transform_space = 'TRANSFORM_SPACE'
    var_r.targets[0].id, var_r.targets[0].transform_type = ring, 'ROT_Z'
    var_r.targets[0].transform_space = 'TRANSFORM_SPACE'
    drv_carrier.expression = f"({Ns}*Srot + {Nr}*Rrot) / ({Ns + Nr})"
    
    for i, p in enumerate(planets):
        angle = i * (2 * math.pi / P)
        if Np % 2 == 0:
            planet_offset = angle * (1 + Ns / Np) + (math.pi / Np)
        else:
            planet_offset = angle * (1 + Ns / Np)
        
        drv_rot = p.driver_add('rotation_euler', 2).driver
        drv_rot.type = 'SCRIPTED'
        var_s = drv_rot.variables.new()
        var_s.name, var_s.type = 'Srot', 'TRANSFORMS'
        var_s.targets[0].id, var_s.targets[0].transform_type = sun, 'ROT_Z'
        var_s.targets[0].transform_space = 'TRANSFORM_SPACE'
        drv_rot.expression = f"Srot * {M} + {planet_offset}"
            
    for n in range(P * F):
        crot = n / P
        planet_idx = (-n) % P
        if Np % 2 == 0:
            offset_turns = planet_idx * (1 + Ns / Np) / P + 1 / (2 * Np)
        else:
            offset_turns = planet_idx * (1 + Ns / Np) / P
        prot_turns = S_rel * crot + offset_turns
        
        phi_turns = -prot_turns % 1.0
        
        empty = bpy.data.objects.new(f"Frame_{(n+1):03d}", None)
        empty.empty_display_size, empty.empty_display_type, empty.show_name = 0.5, 'ARROWS', True
        frames_col.objects.link(empty)
        
        angle_rad = phi_turns * 2 * math.pi
        empty.location = (Rp * math.cos(angle_rad), Rp * math.sin(angle_rad), 0)
        empty.rotation_euler = Vector((math.cos(angle_rad), math.sin(angle_rad), 0)).to_track_quat('Y', 'Z').to_euler()
        empty.parent = planets[planet_idx]
        
    sun.driver_remove('rotation_euler', 2)
    drv_sun = sun.driver_add('rotation_euler', 2).driver
    drv_sun.type = 'SCRIPTED'
    v_frame = drv_sun.variables.new()
    v_frame.name = 'frame'
    v_frame.type = 'SINGLE_PROP'
    v_frame.targets[0].id_type = 'SCENE'
    v_frame.targets[0].id = bpy.context.scene
    v_frame.targets[0].data_path = 'frame_current'

    rads_per_slot = (2 * math.pi) / P
    expr = f"(frame - 1) * ({rads_per_slot}/{slope_c})"
    drv_sun.expression = expr
    sun['base_driver_expr'] = expr

    bpy.context.scene.frame_set(1)
    return main_col

# ==============================================================================
# PROPERTIES & OPERATORS
# ==============================================================================

def update_baker_source(self, context):
    context.scene.zoetrope_mappings.clear()
    anim_parent = self.baker_source
    if not anim_parent: return
        
    if anim_parent.children:
        for child in anim_parent.children:
            item = context.scene.zoetrope_mappings.add()
            item.anim_collection = child
    else:
        item = context.scene.zoetrope_mappings.add()
        item.anim_collection = anim_parent

def update_live_settings(self, context):
    col = self
    empties = [obj for obj in col.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY']
    if not empties: return
    
    # Apply Scale, Rotation, and Offset via Delta Transforms
    for empty in empties:
        empty.delta_scale = (col.zoe_scale, col.zoe_scale, col.zoe_scale)
        empty.delta_rotation_euler[2] = col.zoe_rot_z
        empty.delta_location = col.zoe_offset
        
    # Apply Invert
    root_obj = empties[0].parent
    if root_obj and 'base_driver_expr' in root_obj:
        expr = root_obj['base_driver_expr']
        
        # Modify driver
        if root_obj.animation_data and root_obj.animation_data.drivers:
            for fc in root_obj.animation_data.drivers:
                if fc.data_path == 'rotation_euler' and fc.array_index == 2:
                    if col.zoe_invert:
                        fc.driver.expression = f"-({expr})"
                    else:
                        fc.driver.expression = expr
                    break
                    
        # Reverse empties names
        empties.sort(key=lambda x: x.name)
        names = [e.name for e in empties]
        
        if col.zoe_invert:
            new_names = [names[0]] + list(reversed(names[1:]))
        else:
            # We want to restore original names. Since names are 1-indexed (Frame_001, Frame_002...)
            # we can just reliably rename them based on their physical order.
            # But wait, their order in the collection is fixed. 
            # To avoid issues, let's just rename them back to their sorted order.
            # However, if we invert them multiple times, we need to know the true base order.
            # Let's save a custom property on the empty.
            pass
            
        for e in empties:
            if 'base_frame_idx' not in e:
                e['base_frame_idx'] = int(e.name.split('_')[1])
                
        for e in empties:
            idx = e['base_frame_idx']
            if col.zoe_invert:
                # 1 stays 1, 2 becomes N, 3 becomes N-1
                if idx == 1:
                    target_idx = 1
                else:
                    target_idx = len(empties) - idx + 2
            else:
                target_idx = idx
                
            # append TEMP to avoid naming collisions during rename
            e.name = f"Frame_{target_idx:03d}_TEMP"
            
        for e in empties:
            e.name = e.name.replace("_TEMP", "")

class ZoetropeMappingItem(bpy.types.PropertyGroup):
    anim_collection: bpy.props.PointerProperty(
        name="Animation",
        type=bpy.types.Collection
    )
    target_zoetrope: bpy.props.PointerProperty(
        name="Target Zoetrope",
        type=bpy.types.Collection,
        description="Select the Zoetrope collection to assign this animation to"
    )
    mismatch_strategy: bpy.props.EnumProperty(
        name="Mismatch Strategy",
        description="How to handle frame length mismatches",
        items=[
            ('INTERPOLATE', "Interpolate", "Compress or stretch animation to fit available frames", 'MOD_TIME', 0),
            ('CLIP', "Clip (1:1)", "Play 1:1. Clips end if too long, clips beginning if too short.", 'MOD_DATA_TRANSFER', 1)
        ],
        default='INTERPOLATE'
    )
    use_custom_frame_range: bpy.props.BoolProperty(
        name="Custom Frame Range",
        description="Override automatic frame range detection",
        default=False
    )
    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        default=1,
        min=1
    )
    frame_end: bpy.props.IntProperty(
        name="End Frame",
        default=24,
        min=1
    )

def get_zoetrope_rpm(self):
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    if self.mode == 'BASIC':
        frames = self.basic_frames
    else:
        frames = self.planets * self.subframes
        
    if frames == 0: return 0.0
    return (60.0 * fps) / frames

def set_zoetrope_rpm(self, value):
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    if value <= 0: return
    target_frames = round((60.0 * fps) / value)
    if target_frames < 2: target_frames = 2
    
    if self.mode == 'BASIC':
        self.basic_frames = target_frames
    else:
        self.subframes = max(1, round(target_frames / self.planets))

class ZoetropeGeneratorSettings(bpy.types.PropertyGroup):
    mode: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('BASIC', "Basic", "Standard Zoetrope", 'MESH_CIRCLE', 0), 
            ('PLANETARY', "Planetary", "Planetary Gear Zoetrope", 'MOD_ARRAY', 1)
        ],
        default='BASIC'
    )
    target_rpm: bpy.props.FloatProperty(
        name="Target RPM",
        description="Target Rotational Speed. Automatically scales the number of frames to maintain sync",
        get=get_zoetrope_rpm,
        set=set_zoetrope_rpm
    )
    radius: bpy.props.FloatProperty(
        name="Radius",
        default=5.0,
        min=0.1,
        subtype='DISTANCE',
        description="The radius of the Zoetrope"
    )
    basic_frames: bpy.props.IntProperty(
        name="Frames",
        default=45,
        min=2,
        description="Total number of frames (vertices) for the Basic Zoetrope"
    )
    planets: bpy.props.IntProperty(
        name="Planets",
        default=10,
        min=2,
        description="Number of planet gears"
    )
    subframes: bpy.props.IntProperty(
        name="Sub-frames",
        default=5,
        min=1,
        description="Number of frames per planet gear"
    )
    planet_size: bpy.props.FloatProperty(
        name="Planet Size",
        default=1.0,
        min=0.0,
        max=1.0,
        description="Scale planet gears relative to sun (1.0 = Max Planets, 0.0 = Max Sun)"
    )
    baker_source: bpy.props.PointerProperty(
        name="Source Collection",
        type=bpy.types.Collection,
        description="Collection containing the animations or subcollections to map",
        update=update_baker_source
    )
    active_zoetrope: bpy.props.PointerProperty(
        name="Active Zoetrope",
        type=bpy.types.Collection,
        description="Select a generated Zoetrope collection to tweak its live settings"
    )
    export_dir: bpy.props.StringProperty(
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
    )
    raw_mismatch_strategy: bpy.props.EnumProperty(
        name="Mismatch Strategy",
        description="How to handle frame length mismatches",
        items=[
            ('INTERPOLATE', "Interpolate", "Compress or stretch to fit available frames", 'MOD_TIME', 0),
            ('CLIP', "Clip (1:1)", "Play 1:1. Clips end if too long, clips beginning if too short.", 'MOD_DATA_TRANSFER', 1)
        ],
        default='INTERPOLATE'
    )

class OBJECT_OT_generate_zoetrope(bpy.types.Operator):
    """Generate a Zoetrope based on the selected settings"""
    bl_idname = "object.generate_zoetrope"
    bl_label = "Generate Zoetrope"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.zoetrope_generator
        fps = context.scene.render.fps / context.scene.render.fps_base
        
        if settings.mode == 'BASIC':
            col = create_basic_zoetrope(num_frames=settings.basic_frames, radius=settings.radius, fps=fps)
            self.report({'INFO'}, f"Generated Basic Zoetrope ({settings.basic_frames} frames)")
        elif settings.mode == 'PLANETARY':
            col = create_planetary_zoetrope(P=settings.planets, F=settings.subframes, target_ring_radius=settings.radius, planet_size=settings.planet_size, fps=fps)
            self.report({'INFO'}, f"Generated Planetary Zoetrope ({settings.planets * settings.subframes} frames)")
            
        settings.active_zoetrope = col
        return {'FINISHED'}

class OBJECT_OT_create_frame_template(bpy.types.Operator):
    """Generate a template mesh representing one frame's bounds for the active Zoetrope"""
    bl_idname = "object.create_frame_template"
    bl_label = "Make Frame Template"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        zoe = settings.active_zoetrope
        if not zoe:
            self.report({'WARNING'}, "No active zoetrope selected!")
            return {'CANCELLED'}
            
        zoe_type = zoe.get('zoe_type', None)
        if not zoe_type:
            self.report({'WARNING'}, "Selected collection is not a recognized generated zoetrope!")
            return {'CANCELLED'}
            
        if zoe_type == 'BASIC':
            radius = zoe.get('zoe_radius', 5.0)
            frames = zoe.get('zoe_frames', 45)
            
            import bmesh
            mesh = bpy.data.meshes.new("Frame_Template_Mesh")
            obj = bpy.data.objects.new("Frame_Template", mesh)
            context.collection.objects.link(obj)
            
            bm = bmesh.new()
            center = bm.verts.new((-radius, 0, 0))
            
            multiplier = max(1, round(1000 / frames))
            if multiplier % 2 != 0:
                multiplier += 1
            total_verts = frames * multiplier
            step = (2 * math.pi) / total_verts
            
            segments = multiplier
            start_angle = - (segments / 2) * step
            
            arc_verts = []
            for i in range(segments + 1):
                a = start_angle + i * step
                v = bm.verts.new((-radius + radius * math.cos(a), radius * math.sin(a), 0))
                arc_verts.append(v)
                
            for i in range(segments):
                bm.faces.new((center, arc_verts[i], arc_verts[i+1]))
                
            bm.to_mesh(mesh)
            bm.free()
            
            obj.display_type = 'WIRE'
            obj.show_wire = True
            obj.show_all_edges = True
            obj.show_in_front = True
            
            self.report({'INFO'}, f"Generated Basic Frame Template (Radius: {radius}, Arc: {360/frames:.1f}°)")
            
        elif zoe_type == 'PLANETARY':
            rp = zoe.get('zoe_planet_radius', 1.0)
            
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=32, 
                radius=rp, 
                depth=0.1, 
                end_fill_type='NGON', 
                location=(0, 0, 0)
            )
            obj = context.active_object
            obj.name = "Frame_Template"
            obj.display_type = 'WIRE'
            obj.show_wire = True
            obj.show_all_edges = True
            obj.show_in_front = True
            
            self.report({'INFO'}, f"Generated Planetary Frame Template (Radius: {rp:.2f})")
            
        return {'FINISHED'}

class OBJECT_OT_clear_mappings(bpy.types.Operator):
    """Clear all current mappings"""
    bl_idname = "object.clear_zoetrope_mappings"
    bl_label = "Clear Mappings"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.zoetrope_mappings.clear()
        return {'FINISHED'}

class OBJECT_OT_batch_zoetrope_baker(bpy.types.Operator):
    """Batch Bake Animations to Zoetropes"""
    bl_idname = "object.batch_zoetrope_baker"
    bl_label = "Batch Bake Animations"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for item in context.scene.zoetrope_mappings:
            if not item.target_zoetrope or not item.anim_collection:
                continue
            
            self.bake_single_mapping(context, item.anim_collection, item.target_zoetrope, item.mismatch_strategy)
            count += 1
            
        if count == 0:
            self.report({'WARNING'}, "No mappings executed. Please ensure target zoetropes are assigned.")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Batch baked {count} animations successfully!")
        return {'FINISHED'}
        
    def bake_single_mapping(self, context, anim_col, target_zoetrope, mismatch_strategy):
        empties = [obj for obj in target_zoetrope.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY']
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
            self.report({'WARNING'}, f"No meshes found in {anim_col.name}!")
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
                self.report({'WARNING'}, f"No actions with keyframes found in {anim_col.name}! Defaulting to 24.")
                max_frame = 24

        num_empties = len(empties)
        
        def find_layer_collection(parent, name):
            if parent.name == name: return parent
            for child in parent.children:
                res = find_layer_collection(child, name)
                if res: return res
            return None
            
        layer_col = find_layer_collection(context.view_layer.layer_collection, anim_col.name)
        was_exclude = False
        if layer_col:
            was_exclude = layer_col.exclude
            layer_col.exclude = False
            
        depsgraph = context.evaluated_depsgraph_get()
        
        baked_collection = None
        for child in target_zoetrope.children:
            if child.name == "Baked_Frames":
                baked_collection = child
                break
                
        if baked_collection:
            for obj in list(baked_collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            baked_collection = bpy.data.collections.new("Baked_Frames")
            target_zoetrope.children.link(baked_collection)

        if mismatch_strategy == 'CLIP':
            if max_frame < num_empties:
                # Too short: beginning is clipped (map to the LAST max_frame empties)
                start_empty_idx = num_empties - int(max_frame)
                loop_count = int(max_frame)
            else:
                # Too long: end is clipped (map to the FIRST num_empties)
                start_empty_idx = 0
                loop_count = num_empties
        else:
            # INTERPOLATE
            start_empty_idx = 0
            loop_count = num_empties

        for i in range(loop_count):
            empty_idx = start_empty_idx + i
            if empty_idx >= num_empties:
                break
                
            anim_length = max_frame - start_frame + 1
            if mismatch_strategy == 'INTERPOLATE':
                target_fbx_frame = start_frame + (i / max(1, loop_count - 1)) * (anim_length - 1)
            else:
                target_fbx_frame = start_frame + i
                
            context.scene.frame_set(int(target_fbx_frame))
            context.view_layer.update()
            depsgraph = context.evaluated_depsgraph_get()
            
            baked_meshes = []
            for m in exportable_objects:
                for inst in depsgraph.object_instances:
                    is_match = False
                    if inst.object.original.name == m.name:
                        is_match = True
                    elif inst.parent and inst.parent.original.name == m.name:
                        is_match = True
                        
                    if is_match and inst.object.type == 'MESH':
                        try:
                            eval_mesh = inst.object.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                            real_mesh = eval_mesh.copy()
                            inst.object.to_mesh_clear()
                            
                            new_obj = bpy.data.objects.new(f"Baked_{i+1:03d}_{m.name}", real_mesh)
                            new_obj.matrix_world = inst.matrix_world.copy()
                            baked_collection.objects.link(new_obj)
                            
                            if hasattr(inst.object.data, 'materials'):
                                for mat in inst.object.data.materials:
                                    if mat and mat.name not in real_mesh.materials:
                                        real_mesh.materials.append(mat)
                                        
                            baked_meshes.append(new_obj)
                        except Exception:
                            pass
                
            if not baked_meshes:
                continue
                
            bpy.ops.object.select_all(action='DESELECT')
            for b in baked_meshes:
                b.select_set(True)
            context.view_layer.objects.active = baked_meshes[0]
            if len(baked_meshes) > 1:
                bpy.ops.object.join()
            
            combined = context.active_object
            combined.name = f"Anim_Frame_{i+1:03d}"
            
            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                template_obj = bpy.data.objects.get("Frame_Template")
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
    bl_idname = "object.export_zoetrope_frames"
    bl_label = "Export Frames to OBJ"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        outdir = bpy.path.abspath(settings.export_dir)
        
        if not outdir:
            self.report({'WARNING'}, "Please specify an export directory.")
            return {'CANCELLED'}
            
        import os
        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to create directory: {e}")
                return {'CANCELLED'}

        count = 0
        for item in context.scene.zoetrope_mappings:
            if not item.target_zoetrope or not item.anim_collection:
                continue
            
            self.export_single_mapping(context, item.anim_collection, item.target_zoetrope, item.mismatch_strategy, outdir)
            count += 1
            
        if count == 0:
            self.report({'WARNING'}, "No mappings found to export.")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Successfully exported {count} animations!")
        return {'FINISHED'}
        
    def export_single_mapping(self, context, anim_col, target_zoetrope, mismatch_strategy, outdir):
        empties = [obj for obj in target_zoetrope.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY']
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
            self.report({'WARNING'}, f"No exportable objects found in {anim_col.name}!")
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
                self.report({'WARNING'}, f"No actions with keyframes found in {anim_col.name}! Defaulting to 24 frames.")
                max_frame = 24

        num_empties = len(empties)
        
        def find_layer_collection(parent, name):
            if parent.name == name: return parent
            for child in parent.children:
                res = find_layer_collection(child, name)
                if res: return res
            return None
            
        layer_col = find_layer_collection(context.view_layer.layer_collection, anim_col.name)
        was_exclude = False
        if layer_col:
            was_exclude = layer_col.exclude
            layer_col.exclude = False
            
        depsgraph = context.evaluated_depsgraph_get()

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

        settings = context.scene.zoetrope_generator
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
                    target_fbx_frame = start_frame + i
                
            context.scene.frame_set(int(target_fbx_frame))
            context.view_layer.update()
            depsgraph = context.evaluated_depsgraph_get()
            
            temp_objects = []
            for m in exportable_objects:
                for inst in depsgraph.object_instances:
                    is_match = False
                    if inst.object.original.name == m.name:
                        is_match = True
                    elif inst.parent and inst.parent.original.name == m.name:
                        is_match = True
                        
                    if is_match and inst.object.type == 'MESH':
                        try:
                            eval_mesh = inst.object.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                            real_mesh = eval_mesh.copy()
                            inst.object.to_mesh_clear()
                            
                            new_obj = bpy.data.objects.new(f"Temp_Export_{m.name}", real_mesh)
                            
                            template_obj = bpy.data.objects.get("Frame_Template")
                            if template_obj:
                                o_mat_inv = template_obj.matrix_world.inverted()
                                new_obj.matrix_world = o_mat_inv @ inst.matrix_world.copy()
                            else:
                                new_obj.matrix_world = inst.matrix_world.copy()
                                
                            context.scene.collection.objects.link(new_obj)
                            
                            # Ensure vertex colors are active so OBJ exporter picks them up
                            if hasattr(real_mesh, 'color_attributes') and real_mesh.color_attributes:
                                real_mesh.color_attributes.active_color = real_mesh.color_attributes[0]
                            elif hasattr(real_mesh, 'vertex_colors') and real_mesh.vertex_colors:
                                real_mesh.vertex_colors.active_index = 0
                            
                            if hasattr(inst.object.data, 'materials'):
                                for mat in inst.object.data.materials:
                                    if mat and mat.name not in real_mesh.materials:
                                        real_mesh.materials.append(mat)
                                        
                            temp_objects.append(new_obj)
                        except Exception:
                            pass
                
            if not temp_objects:
                continue
                
            bpy.ops.object.select_all(action='DESELECT')
            for temp_obj in temp_objects:
                temp_obj.select_set(True)
                
            context.view_layer.objects.active = temp_objects[0]
            
            prefix = anim_col.name.replace(" ", "_")
            out_path = os.path.join(outdir, f"{prefix}_frame_{i+1:03d}.obj")
            
            try:
                try:
                    # Blender 3.2+ new C++ exporter
                    try:
                        bpy.ops.wm.obj_export(filepath=out_path, export_selected_objects=True, export_colors=True, export_triangulated_mesh=True)
                    except TypeError:
                        # Fallback if export_colors or export_triangulated_mesh is unrecognized
                        bpy.ops.wm.obj_export(filepath=out_path, export_selected_objects=True)
                except AttributeError:
                    # Fallback to old python exporter (pre-3.2)
                    bpy.ops.export_scene.obj(filepath=out_path, use_selection=True, use_triangles=True)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to export OBJ {out_path}: {e}")
                print(f"Export Error: {e}")
                
            # Cleanup memory
            temp_meshes = [obj.data for obj in temp_objects if obj.data]
            for temp_obj in temp_objects:
                bpy.data.objects.remove(temp_obj, do_unlink=True)
            for mesh in temp_meshes:
                bpy.data.meshes.remove(mesh, do_unlink=True)
                    
            context.window_manager.progress_update(i + 1)
            
        context.window_manager.progress_end()
        context.scene.frame_set(1)
        
        if layer_col:
            layer_col.exclude = was_exclude

class OBJECT_OT_import_zoetrope_frames(bpy.types.Operator):
    """Import OBJ Frames and map them to Zoetrope"""
    bl_idname = "object.import_zoetrope_frames"
    bl_label = "Import Frames from OBJ"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        outdir = bpy.path.abspath(settings.export_dir)
        
        if not outdir:
            self.report({'WARNING'}, "Please specify an export directory.")
            return {'CANCELLED'}
            
        import os
        if not os.path.exists(outdir):
            self.report({'ERROR'}, "Export directory does not exist.")
            return {'CANCELLED'}
            
        count = 0
        for item in context.scene.zoetrope_mappings:
            if not item.target_zoetrope or not item.anim_collection:
                continue
            
            self.import_single_mapping(context, item.anim_collection, item.target_zoetrope, item.mismatch_strategy, outdir)
            count += 1
            
        if count == 0:
            self.report({'WARNING'}, "No mappings found to import.")
            return {'CANCELLED'}
            
        return {'FINISHED'}

    def import_single_mapping(self, context, anim_col, target_zoetrope, mismatch_strategy, outdir):
        import os
        import glob
        import mathutils
        
        prefix = anim_col.name.replace(" ", "_")
        search_pattern = os.path.join(outdir, f"{prefix}_frame_*.obj")
        files = sorted(glob.glob(search_pattern))
        
        if not files:
            self.report({'WARNING'}, f"No OBJs found for {anim_col.name} in {outdir}")
            return
            
        empties = [obj for obj in target_zoetrope.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY']
        if not empties:
            self.report({'WARNING'}, f"No 'Frame_XXX' empties found in {target_zoetrope.name}!")
            return
            
        empties.sort(key=lambda x: x.name)
        num_empties = len(empties)
        max_frame = len(files)
        
        imported_collection = None
        for child in target_zoetrope.children:
            if child.name == "Imported_Frames":
                imported_collection = child
                break
                
        if imported_collection:
            for obj in list(imported_collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            imported_collection = bpy.data.collections.new("Imported_Frames")
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
                target_file_idx = int(round((i / max(1, loop_count - 1)) * (max_frame - 1)))
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
                self.report({'ERROR'}, f"Failed to import {os.path.basename(filepath)}: {e}")
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
            combined.name = f"Imported_{i+1:03d}_{prefix}"
            
            imported_collection.objects.link(combined)
            for coll in combined.users_collection:
                if coll != imported_collection:
                    coll.objects.unlink(combined)
                    
            empty = empties[empty_idx]
            if empty:
                orig_matrix = combined.matrix_world.copy()
                template_obj = bpy.data.objects.get("Frame_Template")
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
    bl_idname = "object.import_raw_zoetrope_frames"
    bl_label = "Import Raw Frames"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.zoetrope_generator
        zoe = settings.active_zoetrope
        outdir = bpy.path.abspath(settings.export_dir)
        
        if not zoe:
            self.report({'WARNING'}, "No active zoetrope selected.")
            return {'CANCELLED'}
            
        import os
        import glob
        import mathutils
        
        search_pattern = os.path.join(outdir, "*.obj")
        files = sorted(glob.glob(search_pattern))
        
        if not files:
            self.report({'WARNING'}, f"No OBJ files found in {outdir}")
            return {'CANCELLED'}
            
        empties = [obj for obj in zoe.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY']
        if not empties:
            self.report({'WARNING'}, f"No 'Frame_XXX' empties found in {zoe.name}!")
            return {'CANCELLED'}
            
        empties.sort(key=lambda x: x.name)
        num_empties = len(empties)
        num_files = len(files)
        
        imported_collection = None
        for child in zoe.children:
            if child.name == "Imported_Frames":
                imported_collection = child
                break
                
        if imported_collection:
            for obj in list(imported_collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            imported_collection = bpy.data.collections.new("Imported_Frames")
            zoe.children.link(imported_collection)
            
        context.window_manager.progress_begin(0, num_empties)
        
        mismatch_strategy = settings.raw_mismatch_strategy
        
        for i in range(num_empties):
            if mismatch_strategy == 'CLIP':
                if num_files < num_empties:
                    # Too short: map to the LAST len(files) empties
                    start_empty_idx = num_empties - num_files
                    if i < start_empty_idx:
                        continue
                    file_idx = i - start_empty_idx
                else:
                    # Too long: play 1:1, clip end
                    file_idx = i
            else: # INTERPOLATE
                file_idx = int(round((i / max(1, num_empties - 1)) * (num_files - 1)))
                
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
                self.report({'ERROR'}, f"Failed to import {os.path.basename(filepath)}: {e}")
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
            combined.name = f"Imported_{i+1:03d}_{os.path.splitext(os.path.basename(filepath))[0]}"
            
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
    bl_idname = "object.clear_all_frames"
    bl_label = "Clear All Frames"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.zoetrope_generator
        zoe = settings.active_zoetrope
        
        if not zoe:
            self.report({'WARNING'}, "No active zoetrope selected.")
            return {'CANCELLED'}
            
        cleared = 0
        for child in list(zoe.children):
            if child.name in ["Baked_Frames", "Imported_Frames"]:
                for obj in list(child.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                cleared += 1
                
        if cleared == 0:
            self.report({'INFO'}, "No frames found to clear.")
        else:
            self.report({'INFO'}, "Successfully cleared all frames.")
            
        return {'FINISHED'}

# ==============================================================================
# UI PANELS
# ==============================================================================

class VIEW3D_PT_zoetrope_main(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zoetrope'
    bl_label = 'Zoetrope Generator'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.zoetrope_generator
        
        row = layout.row(align=True)
        row.prop(settings, "mode", expand=True)
        
        box = layout.box()
        col = box.column(align=True)
        
        col.prop(settings, "radius")
        fps = context.scene.render.fps / context.scene.render.fps_base
        col.label(text=f"Scene FPS: {fps:.2f} (Target)", icon='TIME')
        
        col.separator()
        col.prop(settings, "target_rpm")
        col.separator()
        
        if settings.mode == 'BASIC':
            col.prop(settings, "basic_frames")
            total_frames = settings.basic_frames
        else:
            row = col.row(align=True)
            row.prop(settings, "planets")
            row.prop(settings, "subframes")
            col.prop(settings, "planet_size", slider=True)
            total_frames = settings.planets * settings.subframes
            col.label(text=f"Total Frames: {total_frames}", icon='RENDER_ANIMATION')
            
        if total_frames > 0:
            deg_per_frame = 360.0 / total_frames
            col.label(text=f"Degrees per Frame: {deg_per_frame:.2f}°", icon='DRIVER_ROTATIONAL_DIFFERENCE')
            
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.generate_zoetrope", icon='PLAY')

class VIEW3D_PT_zoetrope_settings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zoetrope'
    bl_label = 'Live Zoetrope Settings'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.zoetrope_generator
        
        box = layout.box()
        box.prop(settings, "active_zoetrope")
        
        if settings.active_zoetrope:
            zoe = settings.active_zoetrope
            col = box.column(align=True)
            col.prop(zoe, "zoe_rot_z")
            col.prop(zoe, "zoe_scale")
            col.prop(zoe, "zoe_invert", toggle=True)
            
            if zoe.get('zoe_type') == 'BASIC':
                box.separator()
                v_total = zoe.get('zoe_verts_total', 0)
                v_frame = zoe.get('zoe_verts_per_frame', 0)
                frames = zoe.get('zoe_frames', 1)
                box.label(text=f"Total Vertices: {v_total}", icon='MESH_CIRCLE')
                box.label(text=f"Vertices per Frame: {v_frame}", icon='SNAP_VERTEX')
                if frames > 0 and v_total % frames != 0:
                    box.label(text=f"ERROR: Vertices not divisible by {frames}!", icon='ERROR')
            
            box.separator()
            box.operator("object.create_frame_template", icon='MESH_CYLINDER')
            
            box.separator()
            box.label(text="Mass Import Frames", icon='IMPORT')
            box.prop(settings, "export_dir", text="Directory")
            
            # Show mismatch warning
            import os, glob
            outdir = bpy.path.abspath(settings.export_dir)
            if zoe and outdir and os.path.exists(outdir):
                files = glob.glob(os.path.join(outdir, "*.obj"))
                empties_count = sum(1 for obj in zoe.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY')
                if len(files) != empties_count and len(files) > 0 and empties_count > 0:
                    box.label(text=f"Mismatch: {len(files)} OBJs vs {empties_count} frames", icon='ERROR')
                    box.prop(settings, "raw_mismatch_strategy")
                    
            row = box.row()
            row.scale_y = 1.5
            row.operator("object.import_raw_zoetrope_frames", icon='MESH_DATA', text="Import All OBJs to Empties")
            
            box.separator()
            row = box.row()
            row.operator("object.clear_all_frames", icon='TRASH', text="Clear All Frames")

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
        box.label(text="Animations", icon='OUTLINER_COLLECTION')
        box.prop(settings, "baker_source", text="")
        
        row = box.row(align=True)
        row.operator("object.clear_zoetrope_mappings", icon='TRASH')
        
        if context.scene.zoetrope_mappings:
            is_single_mapping = len(context.scene.zoetrope_mappings) == 1 and context.scene.zoetrope_mappings[0].anim_collection == settings.baker_source
            
            if is_single_mapping:
                item = context.scene.zoetrope_mappings[0]
                box.separator()
                box.prop(item, "target_zoetrope", text="Target Zoetrope")
                
                if item.target_zoetrope and item.anim_collection:
                    max_frame = 0
                    for obj in item.anim_collection.all_objects:
                        if obj.animation_data and obj.animation_data.action:
                            max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
                    empties_count = sum(1 for obj in item.target_zoetrope.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY')
                    if int(max_frame) != empties_count and empties_count > 0 and max_frame > 0:
                        box.label(text=f"Mismatch: {int(max_frame)} anim vs {empties_count} frames", icon='ERROR')
                        box.prop(item, "mismatch_strategy")
                        
                layout.separator()
                row = layout.row()
                row.scale_y = 1.5
                row.operator("object.batch_zoetrope_baker", icon='RENDER_ANIMATION', text="Bake Animation")
                
                layout.separator()
                box = layout.box()
                box.label(text="Export to OBJ", icon='EXPORT')
                box.prop(settings, "export_dir")
                box.prop(settings, "use_export_frame_range")
                if settings.use_export_frame_range:
                    row = box.row(align=True)
                    row.prop(settings, "export_frame_start")
                    row.prop(settings, "export_frame_end")
                row = box.row()
                row.scale_y = 1.5
                row.operator("object.export_zoetrope_frames", icon='MESH_DATA', text="Export Frames")
                row = box.row()
                row.scale_y = 1.5
                row.operator("object.import_zoetrope_frames", icon='IMPORT', text="Import Frames")
                
            else:
                layout.separator()
                layout.label(text="Animation Mappings:", icon='GRAPH')
                
                for i, item in enumerate(context.scene.zoetrope_mappings):
                    map_box = layout.box()
                    
                    row = map_box.row()
                    if item.anim_collection:
                        row.label(text=item.anim_collection.name, icon='GROUP')
                    else:
                        row.label(text="Unknown Collection", icon='ERROR')
                    
                    col = map_box.column(align=True)
                    col.prop(item, "target_zoetrope", text="Target")
                    
                    if item.target_zoetrope and item.anim_collection:
                        max_frame = 0
                        for obj in item.anim_collection.all_objects:
                            if obj.animation_data and obj.animation_data.action:
                                max_frame = max(max_frame, obj.animation_data.action.frame_range[1])
                        
                        empties_count = sum(1 for obj in item.target_zoetrope.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY')
                        
                        if int(max_frame) != empties_count and empties_count > 0 and max_frame > 0:
                            map_box.label(text=f"Mismatch: {int(max_frame)} anim vs {empties_count} frames", icon='ERROR')
                            map_box.prop(item, "mismatch_strategy")
                            
                        map_box.prop(item, "use_custom_frame_range")
                        if item.use_custom_frame_range:
                            row = map_box.row(align=True)
                            row.prop(item, "frame_start")
                            row.prop(item, "frame_end")
                
                layout.separator()
                row = layout.row()
                row.scale_y = 1.5
                row.operator("object.batch_zoetrope_baker", icon='RENDER_ANIMATION')
                
                layout.separator()
                box = layout.box()
                box.label(text="Export to OBJ", icon='EXPORT')
                box.prop(settings, "export_dir")
                box.prop(settings, "use_export_frame_range")
                if settings.use_export_frame_range:
                    row = box.row(align=True)
                    row.prop(settings, "export_frame_start")
                    row.prop(settings, "export_frame_end")
                row = box.row()
                row.scale_y = 1.5
                row.operator("object.export_zoetrope_frames", icon='MESH_DATA', text="Export Frames")
                row = box.row()
                row.scale_y = 1.5
                row.operator("object.import_zoetrope_frames", icon='IMPORT', text="Import Frames")

# ==============================================================================
# REGISTRATION
# ==============================================================================

classes = (
    ZoetropeMappingItem,
    ZoetropeGeneratorSettings,
    ZOETROPE_OT_update_self,
    ZOETROPE_OT_check_updates,
    ZOETROPE_PT_updater_panel,
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
    VIEW3D_PT_zoetrope_baker
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.zoetrope_mappings = bpy.props.CollectionProperty(type=ZoetropeMappingItem)
    bpy.types.Scene.zoetrope_generator = bpy.props.PointerProperty(type=ZoetropeGeneratorSettings)
    
    # Custom properties on Collection for live updates
    bpy.types.Collection.zoe_rot_z = bpy.props.FloatProperty(
        name="Rotation Z",
        description="Offset the rotation of the animation instances",
        default=math.pi,
        subtype='ANGLE',
        update=update_live_settings
    )
    bpy.types.Collection.zoe_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Scale the animation instances",
        default=1.0,
        min=0.01,
        update=update_live_settings
    )
    bpy.types.Collection.zoe_offset = bpy.props.FloatVectorProperty(
        name="Local Offset",
        description="Offset the animation instances",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION',
        update=update_live_settings
    )
    bpy.types.Collection.zoe_invert = bpy.props.BoolProperty(
        name="Invert Animation",
        description="Spins the zoetrope counter-clockwise and maps frames in reverse",
        default=False,
        update=update_live_settings
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.zoetrope_mappings
    del bpy.types.Scene.zoetrope_generator
    
    del bpy.types.Collection.zoe_rot_z
    del bpy.types.Collection.zoe_scale
    del bpy.types.Collection.zoe_offset
    del bpy.types.Collection.zoe_invert

if __name__ == "__main__":
    register()
    
# Start background check timer when the module loads
try:
    if bpy.app.timers.is_registered(start_background_check):
        bpy.app.timers.unregister(start_background_check)
    bpy.app.timers.register(start_background_check, first_interval=3.0)
except Exception:
    pass
