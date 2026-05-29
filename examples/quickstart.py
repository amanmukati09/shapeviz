"""shapeviz quickstart — generate a sample mesh and point cloud, then view them.

Run from the project root after installing the package::

    python examples/quickstart.py
"""

from __future__ import annotations

import math
import os
import tempfile

import shapeviz


def make_sphere_ply(path: str, n: int = 24) -> None:
    """Write a small UV-sphere mesh to an ASCII .ply file."""
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    for i in range(n + 1):
        lat = math.pi * i / n
        for j in range(n + 1):
            lon = 2 * math.pi * j / n
            x = math.sin(lat) * math.cos(lon)
            y = math.cos(lat)
            z = math.sin(lat) * math.sin(lon)
            verts.append((x, y, z))
    row = n + 1
    for i in range(n):
        for j in range(n):
            a = i * row + j
            faces.append((a, a + 1, a + row))
            faces.append((a + 1, a + row + 1, a + row))

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("ply\nformat ascii 1.0\n")
        fh.write(f"element vertex {len(verts)}\n")
        fh.write("property float x\nproperty float y\nproperty float z\n")
        fh.write(f"element face {len(faces)}\n")
        fh.write("property list uchar int vertex_indices\nend_header\n")
        for v in verts:
            fh.write(f"{v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
        for f in faces:
            fh.write(f"3 {f[0]} {f[1]} {f[2]}\n")


def make_spiral_xyz(path: str, n: int = 4000) -> None:
    """Write a colorful spiral point cloud to an .xyz file (XYZRGB)."""
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            t = i / n
            r = t
            x = r * math.cos(40 * t)
            z = r * math.sin(40 * t)
            y = t * 2 - 1
            cr = int(255 * t)
            cg = int(255 * (1 - t))
            cb = 180
            fh.write(f"{x:.4f} {y:.4f} {z:.4f} {cr} {cg} {cb}\n")


def main() -> None:
    tmp = tempfile.mkdtemp(prefix="shapeviz_demo_")
    sphere = os.path.join(tmp, "sphere.ply")
    spiral = os.path.join(tmp, "spiral.xyz")
    make_sphere_ply(sphere)
    make_spiral_xyz(spiral)

    print("Opening a mesh in your browser...")
    shapeviz.view(sphere, color_mode="heatmap", compute_normals=True)

    print("Opening a point cloud...")
    shapeviz.view(spiral, mode="pointcloud", point_size=3)

    print("Comparing the two side by side...")
    shapeviz.compare(sphere, spiral, titles=["sphere mesh", "spiral cloud"])

    input("Press Enter to exit (viewers stay open in the browser)...")


if __name__ == "__main__":
    main()
