"""File loaders for shapeviz.

Supported formats:

* ``.ply`` — Stanford Polygon (ASCII + binary little/big endian)
* ``.obj`` — Wavefront OBJ (vertices, faces, vertex colors)
* ``.stl`` — Stereolithography (ASCII + binary)
* ``.xyz`` — plain point clouds (XYZ, optionally XYZRGB / XYZNxNyNz)
* ``.pcd`` — Point Cloud Data (ASCII; binary header parsed best-effort)

The public entry point is :func:`load`, which dispatches on file extension and
returns a :class:`~shapeviz.geometry.Mesh` or
:class:`~shapeviz.geometry.PointCloud`.
"""

from __future__ import annotations

import os
import struct
from typing import Optional

from .geometry import Mesh, PointCloud

SUPPORTED_FORMATS = (".ply", ".obj", ".stl", ".xyz", ".xyzrgb", ".pts", ".pcd")


class LoaderError(Exception):
    """Raised when a file cannot be parsed into geometry."""


def load(path: str, *, format: Optional[str] = None):
    """Load a 3D file and return a :class:`Mesh` or :class:`PointCloud`.

    Parameters
    ----------
    path:
        Path to the file.
    format:
        Override auto-detection (e.g. ``"ply"``). By default the file extension
        is used.
    """
    if not os.path.exists(path):
        raise LoaderError(f"file not found: {path}")

    ext = (format or os.path.splitext(path)[1].lstrip(".")).lower()
    name = os.path.basename(path)

    dispatch = {
        "ply": load_ply,
        "obj": load_obj,
        "stl": load_stl,
        "xyz": load_xyz,
        "xyzrgb": load_xyz,
        "pts": load_xyz,
        "pcd": load_pcd,
    }
    loader = dispatch.get(ext)
    if loader is None:
        raise LoaderError(
            f"unsupported format '.{ext}'. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    try:
        return loader(path, name=name)
    except LoaderError:
        raise
    except Exception as exc:  # noqa: BLE001 - wrap any parser failure cleanly
        raise LoaderError(f"failed to parse {name}: {exc}") from exc


# --------------------------------------------------------------------------- #
# PLY
# --------------------------------------------------------------------------- #

_PLY_TYPE_FMT = {
    "char": "b", "int8": "b",
    "uchar": "B", "uint8": "B",
    "short": "h", "int16": "h",
    "ushort": "H", "uint16": "H",
    "int": "i", "int32": "i",
    "uint": "I", "uint32": "I",
    "float": "f", "float32": "f",
    "double": "d", "float64": "d",
}
_PLY_TYPE_SIZE = {fmt: struct.calcsize(fmt) for fmt in set(_PLY_TYPE_FMT.values())}


def load_ply(path: str, name: str = "mesh"):
    with open(path, "rb") as fh:
        raw = fh.read()

    if not raw.startswith(b"ply"):
        raise LoaderError("not a PLY file (missing 'ply' magic)")

    header_end = raw.find(b"end_header")
    if header_end == -1:
        raise LoaderError("PLY header has no 'end_header'")
    # Move past 'end_header' and its trailing newline.
    body_start = raw.find(b"\n", header_end) + 1
    header_text = raw[:header_end].decode("ascii", errors="replace")

    fmt = "ascii"
    elements: list[dict] = []
    for line in header_text.splitlines():
        line = line.strip()
        if line.startswith("format"):
            parts = line.split()
            fmt = parts[1]
        elif line.startswith("element"):
            _, ename, count = line.split()[:3]
            elements.append({"name": ename, "count": int(count), "props": []})
        elif line.startswith("property") and elements:
            elements[-1]["props"].append(line.split()[1:])

    if fmt == "ascii":
        return _parse_ply_ascii(raw[body_start:].decode("ascii", errors="replace"), elements, name)
    little_endian = "little" in fmt
    return _parse_ply_binary(raw[body_start:], elements, little_endian, name)


def _parse_ply_ascii(body: str, elements, name):
    tokens = body.split()
    pos = 0
    vertices, colors, normals, faces = [], [], [], []

    for el in elements:
        props = el["props"]
        if el["name"] == "vertex":
            prop_names = [p[-1] for p in props]
            for _ in range(el["count"]):
                vals = [float(tokens[pos + j]) for j in range(len(props))]
                pos += len(props)
                row = dict(zip(prop_names, vals))
                vertices.append([row.get("x", 0.0), row.get("y", 0.0), row.get("z", 0.0)])
                if "red" in row:
                    colors.append([row["red"] / 255.0, row["green"] / 255.0, row["blue"] / 255.0])
                if "nx" in row:
                    normals.append([row["nx"], row["ny"], row["nz"]])
        elif el["name"] == "face":
            for _ in range(el["count"]):
                n = int(tokens[pos]); pos += 1
                idx = [int(tokens[pos + j]) for j in range(n)]
                pos += n
                faces.append(idx)
        else:
            # Skip unknown elements (one scalar per property assumed).
            pos += el["count"] * len(props)

    return _build(vertices, faces, colors, normals, name)


def _parse_ply_binary(body: bytes, elements, little_endian, name):
    endian = "<" if little_endian else ">"
    offset = 0
    vertices, colors, normals, faces = [], [], [], []

    def read(fmt_char):
        nonlocal offset
        size = _PLY_TYPE_SIZE[fmt_char]
        val = struct.unpack_from(endian + fmt_char, body, offset)[0]
        offset += size
        return val

    for el in elements:
        props = el["props"]
        if el["name"] == "vertex":
            prop_info = [(p[-1], _PLY_TYPE_FMT[p[0]]) for p in props]
            for _ in range(el["count"]):
                row = {pname: read(pfmt) for pname, pfmt in prop_info}
                vertices.append([row.get("x", 0.0), row.get("y", 0.0), row.get("z", 0.0)])
                if "red" in row:
                    colors.append([row["red"] / 255.0, row["green"] / 255.0, row["blue"] / 255.0])
                if "nx" in row:
                    normals.append([row["nx"], row["ny"], row["nz"]])
        elif el["name"] == "face":
            for _ in range(el["count"]):
                for p in props:
                    if len(p) == 4 and p[0] == "list":
                        count_fmt = _PLY_TYPE_FMT[p[1]]
                        idx_fmt = _PLY_TYPE_FMT[p[2]]
                        n = read(count_fmt)
                        faces.append([read(idx_fmt) for _ in range(n)])
                    else:
                        read(_PLY_TYPE_FMT[p[0]])
        else:
            for _ in range(el["count"]):
                for p in props:
                    read(_PLY_TYPE_FMT[p[0]])

    return _build(vertices, faces, colors, normals, name)


# --------------------------------------------------------------------------- #
# OBJ
# --------------------------------------------------------------------------- #


def load_obj(path: str, name: str = "mesh"):
    vertices, colors, normals_raw, faces = [], [], [], []
    have_colors = False

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            tag = parts[0]
            if tag == "v":
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                if len(parts) >= 7:  # x y z r g b extension
                    colors.append([float(parts[4]), float(parts[5]), float(parts[6])])
                    have_colors = True
                elif have_colors:
                    colors.append([0.7, 0.7, 0.7])
            elif tag == "vn":
                normals_raw.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif tag == "f":
                idx = []
                for token in parts[1:]:
                    # Handles v, v/vt, v//vn, v/vt/vn. Negative indices supported.
                    v = token.split("/")[0]
                    vi = int(v)
                    idx.append(vi - 1 if vi > 0 else len(vertices) + vi)
                faces.append(idx)

    # OBJ normals are indexed separately; only attach them if 1:1 with vertices.
    normals = normals_raw if len(normals_raw) == len(vertices) else []
    return _build(vertices, faces, colors if have_colors else [], normals, name)


# --------------------------------------------------------------------------- #
# STL
# --------------------------------------------------------------------------- #


def load_stl(path: str, name: str = "mesh"):
    with open(path, "rb") as fh:
        head = fh.read(5)
        fh.seek(0)
        raw = fh.read()

    # ASCII STL begins with "solid"; but some binary files do too, so verify.
    is_ascii = head.lower().startswith(b"solid") and b"facet" in raw[:2048].lower()
    if is_ascii:
        return _parse_stl_ascii(raw.decode("ascii", errors="replace"), name)
    return _parse_stl_binary(raw, name)


def _parse_stl_ascii(text: str, name):
    vertices, faces = [], []
    current = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("vertex"):
            _, x, y, z = line.split()[:4]
            vertices.append([float(x), float(y), float(z)])
            current.append(len(vertices) - 1)
        elif line.startswith("endloop"):
            if len(current) >= 3:
                faces.append(current[:])
            current = []
    return _dedup_mesh(vertices, faces, name)


def _parse_stl_binary(raw: bytes, name):
    if len(raw) < 84:
        raise LoaderError("binary STL too short")
    (count,) = struct.unpack_from("<I", raw, 80)
    vertices, faces = [], []
    offset = 84
    for _ in range(count):
        # 12 floats: normal(3) + 3 vertices(9); we recompute normals later.
        vals = struct.unpack_from("<12f", raw, offset)
        offset += 50  # 48 bytes data + 2 byte attribute count
        base = len(vertices)
        vertices.append([vals[3], vals[4], vals[5]])
        vertices.append([vals[6], vals[7], vals[8]])
        vertices.append([vals[9], vals[10], vals[11]])
        faces.append([base, base + 1, base + 2])
    return _dedup_mesh(vertices, faces, name)


# --------------------------------------------------------------------------- #
# XYZ / PTS point clouds
# --------------------------------------------------------------------------- #


def load_xyz(path: str, name: str = "cloud"):
    vertices, colors, normals = [], [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            parts = line.replace(",", " ").split()
            try:
                nums = [float(p) for p in parts]
            except ValueError:
                continue  # skip header rows like a leading point count
            if len(nums) < 3:
                continue
            vertices.append(nums[:3])
            if len(nums) >= 6:
                tail = nums[3:6]
                # Heuristic: values in [0, 255] with any >1 look like colors.
                if any(v > 1.0 for v in tail) and all(0.0 <= v <= 255.0 for v in tail):
                    colors.append([v / 255.0 for v in tail])
                elif all(-1.0001 <= v <= 1.0001 for v in tail):
                    normals.append(tail)
                else:
                    colors.append([min(max(v, 0.0), 1.0) for v in tail])
    return PointCloud(vertices, colors=colors or None, normals=normals or None, name=name)


# --------------------------------------------------------------------------- #
# PCD
# --------------------------------------------------------------------------- #


def load_pcd(path: str, name: str = "cloud"):
    with open(path, "rb") as fh:
        raw = fh.read()

    # Header is always ASCII lines; find where DATA begins.
    text_head, _, rest = raw.partition(b"DATA ")
    header_lines = text_head.decode("ascii", errors="replace").splitlines()
    data_mode_line, _, body = rest.partition(b"\n")
    data_mode = data_mode_line.decode("ascii", errors="replace").strip()

    fields, sizes, types, counts = [], [], [], []
    points = 0
    for line in header_lines:
        line = line.strip()
        if line.startswith("FIELDS"):
            fields = line.split()[1:]
        elif line.startswith("SIZE"):
            sizes = [int(s) for s in line.split()[1:]]
        elif line.startswith("TYPE"):
            types = line.split()[1:]
        elif line.startswith("COUNT"):
            counts = [int(c) for c in line.split()[1:]]
        elif line.startswith("POINTS"):
            points = int(line.split()[1])
        elif line.startswith("WIDTH") and points == 0:
            points = int(line.split()[1])

    if data_mode.startswith("ascii"):
        return _parse_pcd_ascii(body.decode("ascii", errors="replace"), fields, name)
    return _parse_pcd_binary(body, fields, sizes, types, counts or [1] * len(fields), points, name)


def _parse_pcd_ascii(text, fields, name):
    vertices, colors = [], []
    idx = {f: i for i, f in enumerate(fields)}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        try:
            x = float(parts[idx["x"]])
            y = float(parts[idx["y"]])
            z = float(parts[idx["z"]])
        except (KeyError, IndexError, ValueError):
            continue
        vertices.append([x, y, z])
        if "rgb" in idx:
            colors.append(_unpack_pcd_rgb(float(parts[idx["rgb"]])))
    return PointCloud(vertices, colors=colors or None, name=name)


def _parse_pcd_binary(body, fields, sizes, types, counts, points, name):
    fmt_map = {("F", 4): "f", ("F", 8): "d", ("U", 1): "B", ("U", 2): "H",
               ("U", 4): "I", ("I", 1): "b", ("I", 2): "h", ("I", 4): "i"}
    field_fmts = []
    for f, s, t, c in zip(fields, sizes, types, counts):
        ch = fmt_map.get((t, s), "f")
        field_fmts.append((f, ch * c, c))
    stride = sum(struct.calcsize("<" + fmt) for _, fmt, _ in field_fmts)
    vertices, colors = [], []
    offset = 0
    for _ in range(points):
        if offset + stride > len(body):
            break
        values = {}
        for fname, fmt, c in field_fmts:
            unpacked = struct.unpack_from("<" + fmt, body, offset)
            offset += struct.calcsize("<" + fmt)
            values[fname] = unpacked[0] if c == 1 else unpacked
        if "x" in values:
            vertices.append([values["x"], values["y"], values["z"]])
            if "rgb" in values:
                colors.append(_unpack_pcd_rgb(values["rgb"]))
    return PointCloud(vertices, colors=colors or None, name=name)


def _unpack_pcd_rgb(value):
    """PCD packs RGB into a single float's bit pattern."""
    try:
        packed = struct.unpack("<I", struct.pack("<f", float(value)))[0]
    except (struct.error, ValueError, OverflowError):
        packed = int(value)
    r = (packed >> 16) & 0xFF
    g = (packed >> 8) & 0xFF
    b = packed & 0xFF
    return [r / 255.0, g / 255.0, b / 255.0]


# --------------------------------------------------------------------------- #
# Shared builders
# --------------------------------------------------------------------------- #


def _build(vertices, faces, colors, normals, name):
    """Return a Mesh if faces exist, otherwise a PointCloud."""
    if faces:
        return Mesh(vertices, faces=faces, colors=colors or None, normals=normals or None, name=name)
    return PointCloud(vertices, colors=colors or None, normals=normals or None, name=name)


def _dedup_mesh(vertices, faces, name):
    """Merge identical vertices (STL stores them per-triangle) into a clean mesh."""
    lookup: dict[tuple, int] = {}
    new_verts: list[list[float]] = []
    remap: list[int] = []
    for v in vertices:
        key = (round(v[0], 6), round(v[1], 6), round(v[2], 6))
        if key not in lookup:
            lookup[key] = len(new_verts)
            new_verts.append(v)
        remap.append(lookup[key])
    new_faces = [[remap[i] for i in f] for f in faces]
    return Mesh(new_verts, faces=new_faces, name=name)
