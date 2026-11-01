# -*- coding: utf-8 -*-
"""
SeerCorridor V2 — parametric corridor built to match imageResources/走廊图片.png.

Units: 1 Blender unit == 1 UE centimetre (same convention as the previous
SM_CorrShell.fbx round-trip).
Axes: X = width, Y = corridor length, Z = up. Floor top at z = 0.

Cross-section (inner surface):
    (-220,   0) -- floor / left wall base
    (-220, 300) -- left wall top
    (-120, 400) -- left chamfer top
    ( 120, 400) -- ceiling right
    ( 220, 300) -- right chamfer top
    ( 220,   0) -- right wall base
    closing floor segment back to (-220, 0)

12 bays x 300 cm = 3600 cm long. Right wall gets a window per bay.
"""

import bpy
import bmesh
import math

# ---------------------------------------------------------------- scene reset
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

for coll in (bpy.data.meshes, bpy.data.materials):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)

# ---------------------------------------------------------------- materials
MAT_DEFS = [
    # name,                 base rgb,                 metallic, roughness, emission rgb
    ("M_CorrV2_Cream",      (0.72, 0.69, 0.62),       0.00, 0.35, None),
    ("M_CorrV2_Teal",       (0.02, 0.28, 0.30),       0.35, 0.22, None),
    ("M_CorrV2_Dark",       (0.018, 0.022, 0.028),    0.90, 0.10, None),
    ("M_CorrV2_GlowTeal",   (0.00, 0.00, 0.00),       0.00, 0.50, (0.05, 3.20, 3.60)),
    ("M_CorrV2_GlowWarm",   (0.00, 0.00, 0.00),       0.00, 0.50, (4.00, 3.60, 2.90)),
    ("M_CorrV2_Amber",      (0.90, 0.42, 0.06),       0.00, 0.30, (6.00, 2.20, 0.20)),
    ("M_CorrV2_Glass",      (0.02, 0.05, 0.07),       0.20, 0.05, None),
    ("M_CorrV2_Seam",       (0.035, 0.040, 0.045),    0.20, 0.50, None),
]

def make_material(name, base, metallic, roughness, emission):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    def setin(key, value):
        if bsdf and key in bsdf.inputs:
            bsdf.inputs[key].default_value = value
    setin('Base Color', (*base, 1.0))
    setin('Metallic', metallic)
    setin('Roughness', roughness)
    if emission is not None:
        setin('Emission Color', (*emission, 1.0))
        setin('Emission Strength', 1.0)
    else:
        setin('Emission Strength', 0.0)
    if name.endswith('Glass'):
        setin('Alpha', 0.18)
        try:
            m.blend_method = 'BLEND'
        except Exception:
            pass
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    return m

MATS = [make_material(*d) for d in MAT_DEFS]
MI = {m.name: i for i, m in enumerate(MATS)}
CREAM, TEAL, DARK, GLOWT, GLOWW, AMBER, GLASS, SEAM = range(8)

# ---------------------------------------------------------------- bmesh utils
bm = bmesh.new()

def box(mi, x0, x1, y0, y1, z0, z1):
    co = ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
    vs = [bm.verts.new(c) for c in co]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        face = bm.faces.new([vs[i] for i in f])
        face.material_index = mi

PROFILE = [(-220, 0), (-220, 300), (-120, 400), (120, 400), (220, 300), (220, 0)]
N = len(PROFILE)

def profile_normals():
    """Outward segment normals + mitred outward vertex normals (2D, XZ)."""
    seg = []
    for i in range(N):
        x0, z0 = PROFILE[i]
        x1, z1 = PROFILE[(i + 1) % N]
        dx, dz = x1 - x0, z1 - z0
        L = math.hypot(dx, dz) or 1.0
        nx, nz = dz / L, -dx / L
        mx, mz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
        # make it point away from the corridor interior (0, 200)
        if (mx - 0.0) * nx + (mz - 200.0) * nz < 0.0:
            nx, nz = -nx, -nz
        seg.append((nx, nz))
    vert = []
    for i in range(N):
        p = seg[(i - 1) % N]
        q = seg[i]
        vx, vz = p[0] + q[0], p[1] + q[1]
        L = math.hypot(vx, vz) or 1.0
        vert.append((vx / L, vz / L))
    return seg, vert

SEG_N, VERT_N = profile_normals()

def offset_profile(d):
    """Closed polyline offset inward by d cm."""
    return [(PROFILE[i][0] - VERT_N[i][0] * d, PROFILE[i][1] - VERT_N[i][1] * d)
            for i in range(N)]

def slab(mi, p0, p1, n, thick, y0, y1):
    """Solid slab along a 2D profile segment, extruded outward by thick."""
    q0 = (p0[0] + n[0] * thick, p0[1] + n[1] * thick)
    q1 = (p1[0] + n[0] * thick, p1[1] + n[1] * thick)
    co = ((p0[0], y0, p0[1]), (p1[0], y0, p1[1]),
          (q1[0], y0, q1[1]), (q0[0], y0, q0[1]),
          (p0[0], y1, p0[1]), (p1[0], y1, p1[1]),
          (q1[0], y1, q1[1]), (q0[0], y1, q0[1]))
    vs = [bm.verts.new(c) for c in co]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
              (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        face = bm.faces.new([vs[i] for i in f])
        face.material_index = mi

def prism_two_profiles(mi, outer, inner, y0, y1):
    """Closed prism between two closed 2D polylines (same order)."""
    n = len(outer)
    vo0 = [bm.verts.new((x, y0, z)) for x, z in outer]
    vo1 = [bm.verts.new((x, y1, z)) for x, z in outer]
    vi0 = [bm.verts.new((x, y0, z)) for x, z in inner]
    vi1 = [bm.verts.new((x, y1, z)) for x, z in inner]
    for i in range(n):
        j = (i + 1) % n
        faces = [
            (vo0[i], vo0[j], vi0[j], vi0[i]),      # front annulus
            (vo1[i], vi1[i], vi1[j], vo1[j]),      # back annulus
            (vo0[i], vi0[i], vi1[i], vo1[i]),      # inner rim
            (vo0[j], vo1[j], vi1[j], vi0[j]),      # outer rim
        ]
        for f in faces:
            try:
                face = bm.faces.new(f)
                face.material_index = mi
            except ValueError:
                pass

def ring(mi, depth, y0, y1):
    prism_two_profiles(mi, PROFILE, offset_profile(depth), y0, y1)

def band(mi, d_inner, d_outer, y0, y1):
    """Annulus band between two inward offsets (d_inner < d_outer)."""
    prism_two_profiles(mi, offset_profile(d_inner), offset_profile(d_outer), y0, y1)

def cap(mi, y0, y1):
    """Solid cap filling the tunnel cross-section between y0 and y1."""
    vs0 = [bm.verts.new((x, y0, z)) for x, z in PROFILE]
    vs1 = [bm.verts.new((x, y1, z)) for x, z in PROFILE]
    f0 = bm.faces.new(vs0)
    f0.material_index = mi
    f1 = bm.faces.new(list(reversed(vs1)))
    f1.material_index = mi
    for i in range(N):
        j = (i + 1) % N
        face = bm.faces.new((vs0[i], vs0[j], vs1[j], vs1[i]))
        face.material_index = mi

def disc_xz(mi, cx, cz, r, y0, y1, seg=48):
    a0 = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), y0,
                        cz + r * math.sin(2 * math.pi * i / seg))) for i in range(seg)]
    a1 = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), y1,
                        cz + r * math.sin(2 * math.pi * i / seg))) for i in range(seg)]
    f0 = bm.faces.new(list(reversed(a0)))
    f0.material_index = mi
    f1 = bm.faces.new(a1)
    f1.material_index = mi
    for i in range(seg):
        j = (i + 1) % seg
        face = bm.faces.new((a0[i], a0[j], a1[j], a1[i]))
        face.material_index = mi

def annulus_xz(mi, cx, cz, r_in, r_out, y0, y1, seg=48, a_start=0.0, a_end=None):
    full = a_end is None
    if full:
        a_end = a_start + 2 * math.pi
    angles = [a_start + (a_end - a_start) * i / seg for i in range(seg + 1)]
    if full:
        angles = angles[:-1]
    ob0 = [bm.verts.new((cx + r_out * math.cos(a), y0, cz + r_out * math.sin(a))) for a in angles]
    ob1 = [bm.verts.new((cx + r_out * math.cos(a), y1, cz + r_out * math.sin(a))) for a in angles]
    ib0 = [bm.verts.new((cx + r_in * math.cos(a), y0, cz + r_in * math.sin(a))) for a in angles]
    ib1 = [bm.verts.new((cx + r_in * math.cos(a), y1, cz + r_in * math.sin(a))) for a in angles]
    m = len(angles)
    for i in range(m if full else m - 1):
        j = (i + 1) % m
        for f in ((ob0[i], ob0[j], ib0[j], ib0[i]),
                  (ob1[i], ib1[i], ib1[j], ob1[j]),
                  (ob0[i], ib0[i], ib1[i], ob1[i]),
                  (ob0[j], ob1[j], ib1[j], ib0[j])):
            try:
                face = bm.faces.new(f)
                face.material_index = mi
            except ValueError:
                pass

# ---------------------------------------------------------------- dimensions
BAYS = 12
BAY = 300.0
Y0 = 0.0
Y1 = BAYS * BAY            # 3600
RIB_W = 24.0               # rib thickness along Y
RIB_D = 6.0                # rib protrusion into the corridor
WIN_Z0, WIN_Z1 = 90.0, 270.0
WIN_MARGIN = 45.0          # solid wall either side of the window

# ---------------------------------------------------------------- shell
# floor slab (dark glossy), full length
slab(DARK, (220, 0), (-220, 0), (0, -1), 20.0, Y0, Y1)

# chamfers / ceiling: continuous slabs. The -X wall is built per bay below
# (it carries the windows); the +X wall is a continuous slab.
slab(CREAM, (-220, 300), (-120, 400), SEG_N[1], 20.0, Y0, Y1)
slab(CREAM, (-120, 400), (120, 400), SEG_N[2], 20.0, Y0, Y1)
slab(CREAM, (120, 400), (220, 300), SEG_N[3], 20.0, Y0, Y1)
# solid wall on +X (the window wall is on -X, the player's right when facing +Y)
slab(CREAM, (220, 300), (220, 0), SEG_N[4], 20.0, Y0, Y1)

# baseboards (teal) along both walls
box(TEAL, -220.0, -216.0, Y0, Y1, 0.0, 26.0)
box(TEAL,  216.0,  220.0, Y0, Y1, 0.0, 26.0)
# dark shadow gap above the baseboard
box(SEAM, -219.0, -216.0, Y0, Y1, 26.0, 29.0)
box(SEAM,  216.0,  219.0, Y0, Y1, 26.0, 29.0)

# ---------------------------------------------------------------- window wall (player's right = -X)
for b in range(BAYS):
    ya = Y0 + b * BAY
    yb = ya + BAY
    # bottom and top panels, full bay
    box(CREAM, -240.0, -220.0, ya, yb, 0.0, WIN_Z0)
    box(CREAM, -240.0, -220.0, ya, yb, WIN_Z1, 300.0)
    # side pieces around the opening
    box(CREAM, -240.0, -220.0, ya, ya + WIN_MARGIN, WIN_Z0, WIN_Z1)
    box(CREAM, -240.0, -220.0, yb - WIN_MARGIN, yb, WIN_Z0, WIN_Z1)

    wy0 = ya + WIN_MARGIN
    wy1 = yb - WIN_MARGIN
    # teal window frame (protrudes 4 cm inward)
    box(TEAL, -220.0, -216.0, wy0, wy0 + 6.0, WIN_Z0, WIN_Z1)
    box(TEAL, -220.0, -216.0, wy1 - 6.0, wy1, WIN_Z0, WIN_Z1)
    box(TEAL, -220.0, -216.0, wy0, wy1, WIN_Z0, WIN_Z0 + 6.0)
    box(TEAL, -220.0, -216.0, wy0, wy1, WIN_Z1 - 6.0, WIN_Z1)
    # sill
    box(SEAM, -220.0, -212.0, wy0, wy1, WIN_Z0 - 6.0, WIN_Z0)
    # glass pane
    box(GLASS, -221.0, -219.0, wy0 + 6.0, wy1 - 6.0, WIN_Z0 + 6.0, WIN_Z1 - 6.0)

# ---------------------------------------------------------------- ceiling lights
for b in range(BAYS):
    ya = Y0 + b * BAY
    yb = ya + BAY
    for px0, px1 in ((-95.0, -25.0), (25.0, 95.0)):
        py0, py1 = ya + 60.0, yb - 60.0
        # bezel sits up against the ceiling
        box(TEAL, px0 - 5.0, px1 + 5.0, py0 - 5.0, py1 + 5.0, 398.6, 400.0)
        # emissive insert, clearly proud of the bezel (no z-fighting)
        box(GLOWW, px0, px1, py0, py1, 397.2, 398.4)

# continuous cyan strips at the ceiling edges
box(GLOWT, -120.0, -116.0, Y0, Y1, 399.0, 400.0)
box(GLOWT,  116.0,  120.0, Y0, Y1, 399.0, 400.0)
# wall base glow line
box(GLOWT, -219.0, -217.0, Y0, Y1, 29.0, 32.0)
box(GLOWT,  217.0,  219.0, Y0, Y1, 29.0, 32.0)
# floor centre strip
box(GLOWT, -6.0, 6.0, Y0, Y1, 0.0, 0.7)

# solid wall light slots (one per bay, on +X)
for b in range(BAYS):
    ya = Y0 + b * BAY
    yc = ya + BAY * 0.5
    box(GLOWW, 218.5, 219.5, yc - 7.0, yc + 7.0, 110.0, 290.0)

# horizontal teal trim just under the chamfer, both walls
box(TEAL, -220.0, -218.0, Y0, Y1, 296.0, 300.0)
box(TEAL,  218.0,  220.0, Y0, Y1, 296.0, 300.0)

# ---------------------------------------------------------------- ribs
for b in range(1, BAYS):
    yr = Y0 + b * BAY
    ring(TEAL, RIB_D, yr - RIB_W * 0.5, yr + RIB_W * 0.5)
    # glowing inner edge of the rib
    band(GLOWT, RIB_D - 0.5, RIB_D + 2.5, yr - RIB_W * 0.5, yr + RIB_W * 0.5)
    # little teal step where the rib meets the floor
    box(TEAL, -220.0, 220.0, yr - RIB_W * 0.5, yr + RIB_W * 0.5, 0.0, 3.0)

# ---------------------------------------------------------------- end caps
cap(CREAM, Y0 - 20.0, Y0)          # back wall behind the player
cap(CREAM, Y1, Y1 + 20.0)          # far wall carrying the hatch

# ---------------------------------------------------------------- far hatch (y = Y1)
CZ = 200.0
# surround ring (fits inside the tunnel cross-section)
annulus_xz(TEAL, 0.0, CZ, 168.0, 195.0, Y1 - 8.0, Y1, seg=64)
# hatch outer ring + disc
annulus_xz(TEAL, 0.0, CZ, 146.0, 168.0, Y1 - 12.0, Y1, seg=64)
disc_xz(CREAM, 0.0, CZ, 146.0, Y1 - 11.0, Y1 - 1.0, seg=64)
# concentric teal rings
for rr in (126.0, 96.0, 66.0):
    annulus_xz(TEAL, 0.0, CZ, rr, rr + 5.0, Y1 - 13.0, Y1 - 11.0, seg=64)
# amber segmented ring
for k in range(8):
    a0 = k * math.pi / 4.0 + math.radians(6.0)
    a1 = (k + 1) * math.pi / 4.0 - math.radians(6.0)
    annulus_xz(AMBER, 0.0, CZ, 110.0, 122.0, Y1 - 14.0, Y1 - 12.0, seg=20, a_start=a0, a_end=a1)
# spokes
for k in range(4):
    a = k * math.pi / 2.0 + math.pi / 4.0
    cx, cz = math.cos(a) * 81.0, math.sin(a) * 81.0
    dx, dz = math.cos(a), math.sin(a)
    px, pz = -dz, dx
    hw, hl = 4.5, 15.0
    corners = []
    for sy in (Y1 - 13.0, Y1 - 11.0):
        for sx, sz in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)):
            corners.append((cx + dx * sx + px * sz, sy, CZ + cz + dz * sx + pz * sz))
    vs = [bm.verts.new(c) for c in corners]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        face = bm.faces.new([vs[i] for i in f])
        face.material_index = TEAL
# hub
disc_xz(CREAM, 0.0, CZ, 32.0, Y1 - 13.0, Y1 - 9.0, seg=40)
disc_xz(GLOWW, 0.0, CZ, 20.0, Y1 - 14.2, Y1 - 13.0, seg=40)

# ---------------------------------------------------------------- back hatch (y = Y0)
annulus_xz(TEAL, 0.0, CZ, 146.0, 168.0, Y0, Y0 + 8.0, seg=64)
disc_xz(CREAM, 0.0, CZ, 146.0, Y0 + 1.0, Y0 + 7.0, seg=64)
annulus_xz(TEAL, 0.0, CZ, 96.0, 101.0, Y0 + 7.0, Y0 + 8.0, seg=64)
disc_xz(GLOWW, 0.0, CZ, 20.0, Y0 + 7.0, Y0 + 8.0, seg=40)

# ---------------------------------------------------------------- finish mesh
# Blender Y maps to -Y in UE through FBX, so mirror the mesh to land the
# corridor on +Y in UE (y = -20 .. 3620, matching the old SM_CorrShell).
for v in bm.verts:
    v.co.y = -v.co.y

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

mesh = bpy.data.meshes.new("SM_CorrShellV2")
obj = bpy.data.objects.new("SM_CorrShellV2", mesh)
bpy.context.collection.objects.link(obj)
bm.to_mesh(mesh)
bm.free()
for m in MATS:
    mesh.materials.append(m)

# flat shading for hard-surface look
for poly in mesh.polygons:
    poly.use_smooth = False

bpy.context.view_layer.objects.active = obj
obj.select_set(True)

print("BUILD_OK verts=%d polys=%d slots=%d" % (len(mesh.vertices), len(mesh.polygons), len(mesh.materials)))
print("DIMS", tuple(round(v, 2) for v in obj.dimensions))
print("MATS", [m.name for m in mesh.materials])
