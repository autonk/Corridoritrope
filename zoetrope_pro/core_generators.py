import bpy
import math
from mathutils import Vector

def create_basic_zoetrope(num_frames=33, radius=5.0, fps=30.0):
    idx = 1
    while bpy.data.collections.get(f'Basic_Zoetrope_{idx:03d}'):
        idx += 1
    main_col_name = f'Basic_Zoetrope_{idx:03d}'
    main_col = bpy.data.collections.new(main_col_name)
    main_col['zoe_type'] = 'BASIC'
    main_col['zoe_radius'] = radius
    main_col['zoe_frames'] = num_frames
    bpy.context.scene.collection.children.link(main_col)
    frames_col = bpy.data.collections.new('Frames')
    main_col.children.link(frames_col)
    multiplier = max(1, round(1000 / num_frames))
    if multiplier % 2 != 0:
        multiplier += 1
    total_verts = num_frames * multiplier
    main_col['zoe_verts_total'] = total_verts
    main_col['zoe_verts_per_frame'] = multiplier
    verts = []
    edges = []
    angle_step = 2 * math.pi / total_verts
    for i in range(total_verts):
        angle = i * angle_step
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts.append((x, y, 0))
        edges.append((i, (i + 1) % total_verts))
    mesh = bpy.data.meshes.new('Basic_Zoetrope_Mesh')
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    zoetrope = bpy.data.objects.new('Basic_Zoetrope', mesh)
    main_col.objects.link(zoetrope)
    drv = zoetrope.driver_add('rotation_euler', 2).driver
    drv.type = 'SCRIPTED'
    var = drv.variables.new()
    var.name = 'frame'
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'SCENE'
    var.targets[0].id = bpy.context.scene
    var.targets[0].data_path = 'frame_current'
    expr = f'-(frame - 1) * ({2 * math.pi} / {num_frames})'
    drv.expression = expr
    zoetrope['base_driver_expr'] = expr
    frame_angle_step = 2 * math.pi / num_frames
    for i in range(num_frames):
        angle = i * frame_angle_step
        empty = bpy.data.objects.new(f'Frame_{i + 1:03d}', None)
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

def create_gear(name, num_teeth, module, thickness=0.2, col=None):
    if col is None:
        col = bpy.context.collection
    verts = []
    faces = []
    pitch_radius = module * num_teeth / 2
    addendum = module
    dedendum = 1.25 * module
    base_radius = pitch_radius - dedendum
    outer_radius = pitch_radius + addendum
    tooth_angle = 2 * math.pi / num_teeth
    for i in range(num_teeth):
        base_angle = i * tooth_angle
        a1 = base_angle - tooth_angle * 0.25
        verts.append((base_radius * math.cos(a1), base_radius * math.sin(a1), thickness / 2))
        verts.append((outer_radius * math.cos(a1 + tooth_angle * 0.05), outer_radius * math.sin(a1 + tooth_angle * 0.05), thickness / 2))
        a2 = base_angle + tooth_angle * 0.25
        verts.append((outer_radius * math.cos(a2 - tooth_angle * 0.05), outer_radius * math.sin(a2 - tooth_angle * 0.05), thickness / 2))
        verts.append((base_radius * math.cos(a2), base_radius * math.sin(a2), thickness / 2))
    num_front = len(verts)
    for i in range(num_front):
        (x, y, z) = verts[i]
        verts.append((x, y, -thickness / 2))
    for i in range(num_teeth):
        base = i * 4
        next_base = (i + 1) % num_teeth * 4
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
    if col is None:
        col = bpy.context.collection
    verts = []
    faces = []
    pitch_radius = module * num_teeth / 2
    addendum = module
    dedendum = 1.25 * module
    inner_radius = pitch_radius - addendum
    outer_radius = pitch_radius + dedendum
    outer_rim_radius = outer_radius + rim_thickness
    tooth_angle = 2 * math.pi / num_teeth
    a1 = -tooth_angle * 0.25
    verts.append((outer_rim_radius * math.cos(a1), outer_rim_radius * math.sin(a1), thickness / 2))
    verts.append((outer_radius * math.cos(a1), outer_radius * math.sin(a1), thickness / 2))
    a2 = -tooth_angle * 0.05
    verts.append((inner_radius * math.cos(a2), inner_radius * math.sin(a2), thickness / 2))
    a3 = tooth_angle * 0.05
    verts.append((inner_radius * math.cos(a3), inner_radius * math.sin(a3), thickness / 2))
    a4 = tooth_angle * 0.25
    verts.append((outer_radius * math.cos(a4), outer_radius * math.sin(a4), thickness / 2))
    verts.append((outer_rim_radius * math.cos(a4), outer_rim_radius * math.sin(a4), thickness / 2))
    for i in range(6):
        (x, y, z) = verts[i]
        verts.append((x, y, -thickness / 2))
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
    mesh = bpy.data.meshes.new(name + '_tooth')
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
    for (face_idx, face) in enumerate(obj.data.polygons):
        center = face.center
        distance = math.sqrt(center.x ** 2 + center.y ** 2 + center.z ** 2)
        if distance < min_distance:
            min_distance = distance
            target_face = face_idx
    obj.data.polygons[target_face].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    bpy.ops.transform.resize(value=(1, 4, 1), constraint_axis=(False, True, False))
    bpy.ops.object.mode_set(mode='OBJECT')
    array_mod = obj.modifiers.new(name='Array', type='ARRAY')
    array_mod.count = num_teeth
    array_mod.use_relative_offset = False
    array_mod.use_object_offset = False
    array_mod.use_constant_offset = False
    empty = bpy.data.objects.new(name + '_pivot', None)
    empty.location = (0, 0, 0)
    col.objects.link(empty)
    array_mod.use_object_offset = True
    array_mod.offset_object = empty
    empty.rotation_euler[2] = tooth_angle
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='Array')
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
            spacing = 2 * math.pi * carrier_radius / num_planet_gears
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
    for (ratio, r_t, s_t, p_t) in valid_configs:
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
    if idx < 0:
        idx = 0
    if idx >= len(unique_configs):
        idx = len(unique_configs) - 1
    return unique_configs[idx][1]

def generate_planetary_gearbox(num_planet_gears=10, target_ring_radius=4.0, planet_size=1.0, col=None):
    if col is None:
        col = bpy.context.collection
    (ring_teeth, sun_teeth, planet_teeth) = find_best_ring_teeth(num_planet_gears, planet_size=planet_size)
    module = 2 * target_ring_radius / ring_teeth
    sun_radius = module * sun_teeth / 2
    planet_radius = module * planet_teeth / 2
    ring_radius = module * ring_teeth / 2
    carrier_radius = sun_radius + planet_radius
    sun = create_gear('Sun_Gear', sun_teeth, module, 0.3, col=col)
    ring = create_ring_gear('Ring_Gear', ring_teeth, module, 0.3, 0.5, col=col)
    if planet_teeth % 2 != 0:
        ring.rotation_euler[2] = math.pi / ring_teeth
    carrier = bpy.data.objects.new('Carrier', None)
    carrier.empty_display_type = 'ARROWS'
    carrier.empty_display_size = carrier_radius * 0.5
    col.objects.link(carrier)
    planets = []
    for i in range(num_planet_gears):
        angle = 2 * math.pi * i / num_planet_gears
        x = carrier_radius * math.cos(angle)
        y = carrier_radius * math.sin(angle)
        empty = bpy.data.objects.new(f'Planet_Position_{i + 1}', None)
        empty.empty_display_type = 'PLAIN_AXES'
        empty.empty_display_size = planet_radius * 0.5
        col.objects.link(empty)
        empty.location = (x, y, 0)
        empty.parent = carrier
        planet = create_gear(f'Planet_Gear_{i + 1}', planet_teeth, module, 0.25, col=col)
        planet.location = (x, y, 0)
        planets.append(planet)
        con = planet.constraints.new('COPY_LOCATION')
        con.target = empty
    return {'sun': sun, 'ring': ring, 'carrier': carrier, 'planets': planets, 'params': {'P': num_planet_gears, 'Ns': sun_teeth, 'Np': planet_teeth, 'Nr': ring_teeth, 'Rp': planet_radius, 'Rc': carrier_radius}}

def create_planetary_zoetrope(P=10, F=5, target_ring_radius=4.0, planet_size=1.0, fps=30.0):
    idx = 1
    while bpy.data.collections.get(f'Planetary_Zoetrope_{idx:03d}'):
        idx += 1
    main_col_name = f'Planetary_Zoetrope_{idx:03d}'
    main_col = bpy.data.collections.new(main_col_name)
    bpy.context.scene.collection.children.link(main_col)
    frames_col = bpy.data.collections.new('Frames')
    main_col.children.link(frames_col)
    result = generate_planetary_gearbox(P, target_ring_radius=target_ring_radius, planet_size=planet_size, col=main_col)
    (sun, ring, carrier, planets) = (result['sun'], result['ring'], result['carrier'], result['planets'])
    (Ns, Nr, Np, Rp, Rc) = (result['params']['Ns'], result['params']['Nr'], result['params']['Np'], result['params']['Rp'], result['params']['Rc'])
    main_col['zoe_type'] = 'PLANETARY'
    main_col['zoe_planet_radius'] = Rp
    S_rel = -(P // F) + 1.0 / F
    if S_rel == 0:
        S_rel = 1.0 / F
    a = Ns / (Ns + Nr) - Ns * Nr / (Np * (Ns + Nr))
    b = Nr / (Ns + Nr) + Ns * Nr / (Np * (Ns + Nr))
    left = S_rel * Nr / (Ns + Nr) - b
    right = a - S_rel * Ns / (Ns + Nr)
    K = right / left
    M = a + b * K
    slope_c = (Ns + Nr * K) / (Ns + Nr)
    drv_ring = ring.driver_add('rotation_euler', 2).driver
    drv_ring.type = 'SCRIPTED'
    var = drv_ring.variables.new()
    (var.name, var.type) = ('Srot', 'TRANSFORMS')
    (var.targets[0].id, var.targets[0].transform_type) = (sun, 'ROT_Z')
    var.targets[0].transform_space = 'TRANSFORM_SPACE'
    drv_ring.expression = f'Srot * {K}'
    drv_carrier = carrier.driver_add('rotation_euler', 2).driver
    drv_carrier.type = 'SCRIPTED'
    (var_s, var_r) = (drv_carrier.variables.new(), drv_carrier.variables.new())
    (var_s.name, var_r.name) = ('Srot', 'Rrot')
    (var_s.type, var_r.type) = ('TRANSFORMS', 'TRANSFORMS')
    (var_s.targets[0].id, var_s.targets[0].transform_type) = (sun, 'ROT_Z')
    var_s.targets[0].transform_space = 'TRANSFORM_SPACE'
    (var_r.targets[0].id, var_r.targets[0].transform_type) = (ring, 'ROT_Z')
    var_r.targets[0].transform_space = 'TRANSFORM_SPACE'
    drv_carrier.expression = f'({Ns}*Srot + {Nr}*Rrot) / ({Ns + Nr})'
    for (i, p) in enumerate(planets):
        angle = i * (2 * math.pi / P)
        if Np % 2 == 0:
            planet_offset = angle * (1 + Ns / Np) + math.pi / Np
        else:
            planet_offset = angle * (1 + Ns / Np)
        drv_rot = p.driver_add('rotation_euler', 2).driver
        drv_rot.type = 'SCRIPTED'
        var_s = drv_rot.variables.new()
        (var_s.name, var_s.type) = ('Srot', 'TRANSFORMS')
        (var_s.targets[0].id, var_s.targets[0].transform_type) = (sun, 'ROT_Z')
        var_s.targets[0].transform_space = 'TRANSFORM_SPACE'
        drv_rot.expression = f'Srot * {M} + {planet_offset}'
    for n in range(P * F):
        crot = n / P
        planet_idx = -n % P
        if Np % 2 == 0:
            offset_turns = planet_idx * (1 + Ns / Np) / P + 1 / (2 * Np)
        else:
            offset_turns = planet_idx * (1 + Ns / Np) / P
        prot_turns = S_rel * crot + offset_turns
        phi_turns = -prot_turns % 1.0
        empty = bpy.data.objects.new(f'Frame_{n + 1:03d}', None)
        (empty.empty_display_size, empty.empty_display_type, empty.show_name) = (0.5, 'ARROWS', True)
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
    rads_per_slot = 2 * math.pi / P
    expr = f'(frame - 1) * ({rads_per_slot}/{slope_c})'
    drv_sun.expression = expr
    sun['base_driver_expr'] = expr
    bpy.context.scene.frame_set(1)
    return main_col

