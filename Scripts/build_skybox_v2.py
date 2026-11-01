# -*- coding: utf-8 -*-
"""Generates the SeerCorridor 2:1 equirectangular deep-space panorama.

Rows are authored top-down, then flipped for Blender's bottom-up pixel buffer.
The corridor's windows face -X, which samples u = 0.5, so the hero gas giant is
placed around u = 0.50.
"""
import bpy
import numpy as np
import os

W, H = 4096, 2048
rng = np.random.default_rng(23)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
u = xx / (W - 1.0)
v = yy / (H - 1.0)

px = np.zeros((H, W, 4), dtype=np.float32)
px[..., 0] = 0.0025 + 0.0040 * (1.0 - v)
px[..., 1] = 0.0040 + 0.0055 * (1.0 - v)
px[..., 2] = 0.0120 + 0.0140 * (1.0 - v)
px[..., 3] = 1.0

def add_glow(cx, cy, sx, sy, color, strength=1.0, power=2.0):
    gx = np.exp(-((u - cx) ** 2) / (2.0 * sx * sx))
    gy = np.exp(-((v - cy) ** 2) / (2.0 * sy * sy))
    g = (gx * gy) ** power
    for c in range(3):
        px[..., c] += g * color[c] * strength

# nebulae
add_glow(0.30, 0.62, 0.10, 0.07, (0.030, 0.055, 0.120), 1.0)
add_glow(0.44, 0.55, 0.06, 0.045, (0.090, 0.030, 0.090), 1.0)
add_glow(0.62, 0.38, 0.09, 0.06, (0.070, 0.025, 0.045), 1.0)
add_glow(0.78, 0.58, 0.11, 0.08, (0.015, 0.050, 0.075), 1.0)
add_glow(0.18, 0.38, 0.07, 0.05, (0.045, 0.018, 0.060), 1.0)

# milky-way band
line_d = (v - (0.22 + 0.56 * u)) / np.sqrt(1.0 + 0.56 * 0.56)
band = np.exp(-(line_d * line_d) / (2.0 * 0.055 * 0.055))
for c, base in enumerate((0.020, 0.024, 0.045)):
    px[..., c] += band * base
add_glow(0.52, 0.52, 0.22, 0.035, (0.020, 0.028, 0.060), 0.8)

def stamp(cx, cy, r, brightness, tint):
    rad = max(1, int(r))
    x0, x1 = max(0, int(cx) - rad), min(W, int(cx) + rad + 1)
    y0, y1 = max(0, int(cy) - rad), min(H, int(cy) + rad + 1)
    if x0 >= x1 or y0 >= y1:
        return
    fy = np.arange(y0, y1)[:, None] - cy
    fx = np.arange(x0, x1)[None, :] - cx
    sigma = max(0.55, rad * 0.5)
    fall = np.exp(-(fx * fx + fy * fy) / (2.0 * sigma * sigma))
    for c in range(3):
        px[y0:y1, x0:x1, c] += fall * brightness * tint[c]

def star_color():
    k = rng.random()
    if k < 0.18:
        return (0.62, 0.78, 1.0)
    if k < 0.30:
        return (1.0, 0.82, 0.62)
    if k < 0.36:
        return (1.0, 0.72, 0.55)
    return (1.0, 1.0, 1.0)

N = 22000
for _ in range(N):
    cx = rng.integers(0, W)
    cy = rng.integers(0, H)
    r = rng.choice([0, 0, 0, 0, 1, 1, 1, 2, 2, 3])
    b = rng.uniform(0.10, 0.95) ** 2.3
    stamp(cx, cy, int(r), float(b), star_color())

# extra stars concentrated in the band
for _ in range(9000):
    cu = rng.uniform(0.02, 0.98)
    cv = 0.22 + 0.56 * cu + rng.normal(0.0, 0.05)
    if 0.0 <= cv <= 1.0:
        stamp(cu * W, cv * H, int(rng.choice([0, 0, 1])), float(rng.uniform(0.05, 0.55)), star_color())

# a few hero stars with small flares
for _ in range(60):
    cx, cy = int(rng.integers(0, W)), int(rng.integers(0, H))
    b = float(rng.uniform(1.4, 2.6))
    stamp(cx, cy, 2, b, (1.0, 1.0, 1.0))
    stamp(cx, cy, 1, b * 0.6, (0.85, 0.92, 1.0))

def draw_planet(cx, cy, r, col_a, col_b, bands=7.0, tilt=0.0):
    """Simple shaded planet with horizontal bands, lit from the upper left."""
    R = int(r * 1.35)
    x0, x1 = max(0, cx - R), min(W, cx + R + 1)
    y0, y1 = max(0, cy - R), min(H, cy + R + 1)
    if x0 >= x1 or y0 >= y1:
        return
    fy = (np.arange(y0, y1)[:, None] - cy) / r
    fx = (np.arange(x0, x1)[None, :] - cx) / r
    rr = fx * fx + fy * fy
    inside = rr <= 1.0
    nz = np.sqrt(np.clip(1.0 - rr, 0.0, 1.0))
    lx, ly, lz = -0.52, -0.50, 0.69
    lambert = np.clip(fx * lx + fy * ly + nz * lz, 0.0, 1.0)
    shade = 0.12 + 1.05 * lambert
    phase = np.sin(fy * bands + 0.6 * np.sin(fx * 2.4) + tilt)
    mix = 0.5 + 0.5 * phase
    for c in range(3):
        band_col = col_a[c] * (1.0 - mix) + col_b[c] * mix
        px[y0:y1, x0:x1, c] = np.where(inside, band_col * shade, px[y0:y1, x0:x1, c])
    # limb/atmosphere halo
    rim = np.exp(-((np.sqrt(np.maximum(rr, 1e-6)) - 1.0) ** 2) / (2.0 * 0.045 * 0.045))
    rim = rim * (rr > 0.98)
    for c in range(3):
        px[y0:y1, x0:x1, c] += rim * (0.06, 0.10, 0.14)[c] * 0.9

# hero gas giant facing the corridor windows (-X -> u = 0.5)
hero_cx, hero_cy, hero_r = int(0.500 * W), int(0.470 * H), 150
# rings first (behind and around)
ring_dx = (u - 0.500) * W / (hero_r * 2.35)
ring_dy = (v - 0.470) * H / (hero_r * 0.52)
ring_r = np.sqrt(ring_dx * ring_dx + ring_dy * ring_dy)
ring = np.exp(-((ring_r - 1.0) ** 2) / (2.0 * 0.05 * 0.05))
ring *= (ring_r > 0.92) & (ring_r < 1.16)
for c, col in enumerate((0.42, 0.36, 0.30)):
    px[..., c] += ring * col
draw_planet(hero_cx, hero_cy, hero_r, (0.10, 0.32, 0.46), (0.62, 0.78, 0.82), bands=11.0)

# second, warmer planet
draw_planet(int(0.605 * W), int(0.395 * H), 58, (0.32, 0.14, 0.07), (0.85, 0.52, 0.26), bands=6.0)
# ice planet
draw_planet(int(0.332 * W), int(0.575 * H), 34, (0.10, 0.20, 0.30), (0.55, 0.75, 0.86), bands=4.0)
# small moon
draw_planet(int(0.462 * W), int(0.402 * H), 16, (0.10, 0.10, 0.11), (0.55, 0.55, 0.57), bands=3.0)

np.clip(px, 0.0, None, out=px)
img = bpy.data.images.get("T_Starfield")
if img:
    bpy.data.images.remove(img)
img = bpy.data.images.new("T_Starfield", W, H, alpha=False)
img.pixels = np.flipud(px).ravel().tolist()
tex_dir = r"C:\Users\admin\Desktop\UnrealSeerSpaceShip\Content\SeerCorridor\Textures"
os.makedirs(tex_dir, exist_ok=True)
tex_path = os.path.join(tex_dir, "T_Starfield.png")
img.filepath_raw = tex_path
img.file_format = 'PNG'
img.save()
print("SKYBOX", tex_path, os.path.getsize(tex_path))
