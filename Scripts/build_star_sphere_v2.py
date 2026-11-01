# -*- coding: utf-8 -*-
"""Inward-facing UV sphere used as the SeerCorridor star backdrop.

Units: 1 Blender unit == 1 UE centimetre. Blender Y maps to UE -Y, so the
centre is placed at -1840 in Blender to land at +1840 in UE.
"""
import bpy
import bmesh
import math
import os

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

for coll in (bpy.data.meshes, bpy.data.materials):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)

R = 70000.0
SEG = 96
RINGS = 48
CX, CY, CZ = 0.0, -1840.0, 250.0

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

top = bm.verts.new((CX, CY, CZ + R))
bot = bm.verts.new((CX, CY, CZ - R))
ring = {}
for j in range(1, RINGS):
    phi = j / RINGS * math.pi
    sp, cp = math.sin(phi), math.cos(phi)
    for i in range(SEG):
        theta = i / SEG * 2.0 * math.pi
        x = sp * math.cos(theta)
        y = sp * math.sin(theta)
        ring[(i, j)] = bm.verts.new((CX + R * x, CY + R * y, CZ + R * cp))

def set_uv(face, uvs):
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv

def uv_for(i, j):
    return (i / SEG, j / RINGS)

for i in range(SEG):
    i2 = (i + 1) % SEG
    # north cap (top pole -> ring 1)
    f = bm.faces.new((top, ring[(i, 1)], ring[(i2, 1)]))
    set_uv(f, ((i / SEG, 0.0), uv_for(i, 1), uv_for(i2, 1)))
    # south cap
    f = bm.faces.new((ring[(i, RINGS - 1)], bot, ring[(i2, RINGS - 1)]))
    set_uv(f, (uv_for(i, RINGS - 1), ((i + 0.5) / SEG, 1.0), uv_for(i2, RINGS - 1)))
    # middle quads
    for j in range(1, RINGS - 1):
        f = bm.faces.new((ring[(i, j)], ring[(i, j + 1)], ring[(i2, j + 1)], ring[(i2, j)]))
        set_uv(f, (uv_for(i, j), uv_for(i, j + 1), uv_for(i2, j + 1), uv_for(i2, j)))

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.reverse_faces(bm, faces=bm.faces)   # normals point inward

mesh = bpy.data.meshes.new("SM_CorrStarsV2")
obj = bpy.data.objects.new("SM_CorrStarsV2", mesh)
bpy.context.collection.objects.link(obj)
bm.to_mesh(mesh)
bm.free()

mat = bpy.data.materials.new("M_CorrV2_Star")
mat.use_nodes = True
mesh.materials.append(mat)
for poly in mesh.polygons:
    poly.use_smooth = True

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

out = r"C:\Users\admin\Desktop\UnrealSeerSpaceShip\3dModelResources\processed\SM_CorrStarsV2.fbx"
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'MESH'},
                         apply_scale_options='FBX_SCALE_NONE', global_scale=0.01,
                         apply_unit_scale=True, axis_forward='-Z', axis_up='Y',
                         mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False)

print("STAR_SPHERE_OK verts=%d polys=%d" % (len(mesh.vertices), len(mesh.polygons)))
print("DIMS", tuple(round(v, 1) for v in obj.dimensions))
print("EXPORTED", out, os.path.getsize(out))
