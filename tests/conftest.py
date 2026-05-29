"""Shared fixtures: tiny sample files in each supported format.

Every fixture writes a minimal but valid file into a temp dir and yields its
path, so loader tests run against real on-disk bytes without committing binary
assets to the repo.
"""

from __future__ import annotations

import struct

import pytest

# A unit cube: 8 corners, 12 triangles.
CUBE_VERTS = [
    (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
]
CUBE_FACES = [
    (0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6),
    (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
    (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0),
]


@pytest.fixture
def ply_ascii(tmp_path):
    p = tmp_path / "cube.ply"
    lines = [
        "ply", "format ascii 1.0",
        f"element vertex {len(CUBE_VERTS)}",
        "property float x", "property float y", "property float z",
        "property uchar red", "property uchar green", "property uchar blue",
        f"element face {len(CUBE_FACES)}",
        "property list uchar int vertex_indices", "end_header",
    ]
    for i, v in enumerate(CUBE_VERTS):
        r = (i * 30) % 256
        lines.append(f"{v[0]} {v[1]} {v[2]} {r} 100 200")
    for f in CUBE_FACES:
        lines.append(f"3 {f[0]} {f[1]} {f[2]}")
    p.write_text("\n".join(lines) + "\n")
    return str(p)


@pytest.fixture
def ply_binary(tmp_path):
    p = tmp_path / "cube_bin.ply"
    header = (
        "ply\nformat binary_little_endian 1.0\n"
        f"element vertex {len(CUBE_VERTS)}\n"
        "property float x\nproperty float y\nproperty float z\n"
        f"element face {len(CUBE_FACES)}\n"
        "property list uchar int vertex_indices\nend_header\n"
    ).encode("ascii")
    body = b"".join(struct.pack("<3f", *v) for v in CUBE_VERTS)
    for f in CUBE_FACES:
        body += struct.pack("<B3i", 3, *f)
    p.write_bytes(header + body)
    return str(p)


@pytest.fixture
def obj_file(tmp_path):
    p = tmp_path / "cube.obj"
    lines = ["# sample cube"]
    for v in CUBE_VERTS:
        lines.append(f"v {v[0]} {v[1]} {v[2]}")
    for f in CUBE_FACES:
        lines.append(f"f {f[0]+1} {f[1]+1} {f[2]+1}")
    p.write_text("\n".join(lines) + "\n")
    return str(p)


@pytest.fixture
def stl_ascii(tmp_path):
    p = tmp_path / "cube.stl"
    lines = ["solid cube"]
    for f in CUBE_FACES:
        lines.append("facet normal 0 0 0")
        lines.append("  outer loop")
        for idx in f:
            v = CUBE_VERTS[idx]
            lines.append(f"    vertex {v[0]} {v[1]} {v[2]}")
        lines.append("  endloop")
        lines.append("endfacet")
    lines.append("endsolid cube")
    p.write_text("\n".join(lines) + "\n")
    return str(p)


@pytest.fixture
def stl_binary(tmp_path):
    p = tmp_path / "cube_bin.stl"
    out = bytearray(b"\0" * 80)
    out += struct.pack("<I", len(CUBE_FACES))
    for f in CUBE_FACES:
        out += struct.pack("<3f", 0, 0, 0)  # normal
        for idx in f:
            out += struct.pack("<3f", *CUBE_VERTS[idx])
        out += struct.pack("<H", 0)
    p.write_bytes(bytes(out))
    return str(p)


@pytest.fixture
def xyz_file(tmp_path):
    p = tmp_path / "cloud.xyz"
    lines = [f"{v[0]} {v[1]} {v[2]}" for v in CUBE_VERTS]
    p.write_text("\n".join(lines) + "\n")
    return str(p)


@pytest.fixture
def xyzrgb_file(tmp_path):
    p = tmp_path / "cloud_rgb.xyz"
    lines = [f"{v[0]} {v[1]} {v[2]} {(i*20)%256} 120 220" for i, v in enumerate(CUBE_VERTS)]
    p.write_text("\n".join(lines) + "\n")
    return str(p)


@pytest.fixture
def pcd_ascii(tmp_path):
    p = tmp_path / "cloud.pcd"
    header = [
        "# .PCD v0.7 - Point Cloud Data file format",
        "VERSION 0.7", "FIELDS x y z", "SIZE 4 4 4", "TYPE F F F",
        "COUNT 1 1 1", f"WIDTH {len(CUBE_VERTS)}", "HEIGHT 1",
        "VIEWPOINT 0 0 0 1 0 0 0", f"POINTS {len(CUBE_VERTS)}", "DATA ascii",
    ]
    for v in CUBE_VERTS:
        header.append(f"{v[0]} {v[1]} {v[2]}")
    p.write_text("\n".join(header) + "\n")
    return str(p)
