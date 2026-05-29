"""Geometry containers for shapeviz.

These classes are deliberately dependency-light: they store plain Python lists
(or numpy arrays when numpy is available) and expose a small, predictable API
that the loaders, viewer, and tests all rely on.

Two concrete types are provided:

* :class:`Mesh` — vertices + triangular faces (optionally vertex colors / normals)
* :class:`PointCloud` — vertices only (optionally colors / normals)

Both subclass :class:`Geometry`, which holds the shared vertex/color/normal
machinery plus bounding-box helpers and a JSON-serialisable export used by the
viewer.
"""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence

try:  # numpy is optional — everything works without it, just slower.
    import numpy as _np

    HAS_NUMPY = True
except ImportError:  # pragma: no cover - exercised in numpy-free environments
    _np = None
    HAS_NUMPY = False


Vec3 = Sequence[float]


def _to_float_rows(data: Any, width: int, name: str) -> list[list[float]]:
    """Coerce ``data`` into a list of equal-width float rows.

    Accepts nested lists, tuples, flat sequences, or numpy arrays. Raises
    ``ValueError`` if the shape cannot be made rectangular with ``width`` cols.
    """
    if data is None:
        return []

    if HAS_NUMPY and isinstance(data, _np.ndarray):
        arr = _np.asarray(data, dtype=float)
        if arr.ndim == 1:
            if arr.size % width != 0:
                raise ValueError(f"{name}: flat array length {arr.size} not divisible by {width}")
            arr = arr.reshape(-1, width)
        if arr.ndim != 2 or arr.shape[1] != width:
            raise ValueError(f"{name}: expected (N, {width}) array, got shape {arr.shape}")
        return arr.tolist()

    rows = list(data)
    if not rows:
        return []

    # Flat sequence of numbers -> reshape into width-sized rows.
    if isinstance(rows[0], (int, float)):
        if len(rows) % width != 0:
            raise ValueError(f"{name}: flat length {len(rows)} not divisible by {width}")
        return [[float(rows[i + j]) for j in range(width)] for i in range(0, len(rows), width)]

    out: list[list[float]] = []
    for i, row in enumerate(rows):
        vals = list(row)
        if len(vals) != width:
            raise ValueError(f"{name}: row {i} has {len(vals)} values, expected {width}")
        out.append([float(v) for v in vals])
    return out


def _to_int_rows(data: Any, width: int, name: str) -> list[list[int]]:
    """Like :func:`_to_float_rows` but for integer index data (faces)."""
    if data is None:
        return []

    if HAS_NUMPY and isinstance(data, _np.ndarray):
        arr = _np.asarray(data)
        if arr.ndim == 1:
            if arr.size % width != 0:
                raise ValueError(f"{name}: flat array length {arr.size} not divisible by {width}")
            arr = arr.reshape(-1, width)
        if arr.ndim != 2 or arr.shape[1] != width:
            raise ValueError(f"{name}: expected (N, {width}) array, got shape {arr.shape}")
        return arr.astype(int).tolist()

    rows = list(data)
    if not rows:
        return []
    if isinstance(rows[0], (int, float)):
        if len(rows) % width != 0:
            raise ValueError(f"{name}: flat length {len(rows)} not divisible by {width}")
        return [[int(rows[i + j]) for j in range(width)] for i in range(0, len(rows), width)]

    out: list[list[int]] = []
    for i, row in enumerate(rows):
        vals = list(row)
        if len(vals) != width:
            raise ValueError(f"{name}: row {i} has {len(vals)} values, expected {width}")
        out.append([int(v) for v in vals])
    return out


class Geometry:
    """Base container holding vertices and optional per-vertex attributes."""

    def __init__(
        self,
        vertices: Any,
        colors: Optional[Any] = None,
        normals: Optional[Any] = None,
        name: str = "geometry",
    ) -> None:
        self.vertices: list[list[float]] = _to_float_rows(vertices, 3, "vertices")
        self.colors: list[list[float]] = _to_float_rows(colors, 3, "colors")
        self.normals: list[list[float]] = _to_float_rows(normals, 3, "normals")
        self.name = name

        if self.colors and len(self.colors) != len(self.vertices):
            raise ValueError(
                f"colors length {len(self.colors)} != vertices length {len(self.vertices)}"
            )
        if self.normals and len(self.normals) != len(self.vertices):
            raise ValueError(
                f"normals length {len(self.normals)} != vertices length {len(self.vertices)}"
            )

    # -- introspection -----------------------------------------------------

    @property
    def num_vertices(self) -> int:
        return len(self.vertices)

    @property
    def has_colors(self) -> bool:
        return bool(self.colors)

    @property
    def has_normals(self) -> bool:
        return bool(self.normals)

    def bounds(self) -> tuple[list[float], list[float]]:
        """Return ``(min_xyz, max_xyz)`` axis-aligned bounding box corners."""
        if not self.vertices:
            return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        mins = [math.inf, math.inf, math.inf]
        maxs = [-math.inf, -math.inf, -math.inf]
        for v in self.vertices:
            for i in range(3):
                if v[i] < mins[i]:
                    mins[i] = v[i]
                if v[i] > maxs[i]:
                    maxs[i] = v[i]
        return mins, maxs

    def center(self) -> list[float]:
        mins, maxs = self.bounds()
        return [(mins[i] + maxs[i]) / 2.0 for i in range(3)]

    def extent(self) -> float:
        """Largest bounding-box edge length (used for camera framing)."""
        mins, maxs = self.bounds()
        return max(maxs[i] - mins[i] for i in range(3)) or 1.0

    # -- serialisation -----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict consumed by the Three.js viewer."""
        mins, maxs = self.bounds()
        data: dict[str, Any] = {
            "type": self.kind,
            "name": self.name,
            "vertices": _flatten(self.vertices),
            "bounds": {"min": mins, "max": maxs},
        }
        if self.has_colors:
            data["colors"] = _flatten(self.colors)
        if self.has_normals:
            data["normals"] = _flatten(self.normals)
        return data

    @property
    def kind(self) -> str:  # pragma: no cover - overridden by subclasses
        return "geometry"

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} '{self.name}' "
            f"vertices={self.num_vertices} colors={self.has_colors} "
            f"normals={self.has_normals}>"
        )


class PointCloud(Geometry):
    """An unordered set of 3D points with optional colors and normals."""

    @property
    def kind(self) -> str:
        return "pointcloud"


class Mesh(Geometry):
    """A triangular surface mesh.

    Faces are stored as triangles. Quad (or larger) polygons are fan-triangulated
    on construction so the viewer only ever deals with triangles.
    """

    def __init__(
        self,
        vertices: Any,
        faces: Any = None,
        colors: Optional[Any] = None,
        normals: Optional[Any] = None,
        name: str = "mesh",
    ) -> None:
        super().__init__(vertices, colors=colors, normals=normals, name=name)
        self.faces: list[list[int]] = _triangulate(faces)
        max_index = max((idx for f in self.faces for idx in f), default=-1)
        if max_index >= self.num_vertices:
            raise ValueError(
                f"face references vertex {max_index} but only {self.num_vertices} vertices exist"
            )

    @property
    def kind(self) -> str:
        return "mesh"

    @property
    def num_faces(self) -> int:
        return len(self.faces)

    def compute_normals(self) -> "Mesh":
        """Compute per-vertex normals (area-weighted) in place and return self."""
        self.normals = compute_vertex_normals(self.vertices, self.faces)
        return self

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["faces"] = _flatten(self.faces)
        return data

    def __repr__(self) -> str:
        return (
            f"<Mesh '{self.name}' vertices={self.num_vertices} faces={self.num_faces} "
            f"colors={self.has_colors} normals={self.has_normals}>"
        )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _flatten(rows: list[list[float]]) -> list[float]:
    """Flatten ``[[a, b, c], ...]`` into ``[a, b, c, ...]`` for compact JSON."""
    out: list[float] = []
    for row in rows:
        out.extend(row)
    return out


def _triangulate(faces: Any) -> list[list[int]]:
    """Normalise arbitrary face data into a list of triangles."""
    if faces is None:
        return []

    if HAS_NUMPY and isinstance(faces, _np.ndarray):
        faces = faces.tolist()

    rows = list(faces)
    if not rows:
        return []

    # Flat list of ints assumed to be triangles already.
    if isinstance(rows[0], (int, float)):
        if len(rows) % 3 != 0:
            raise ValueError(f"flat face list length {len(rows)} not divisible by 3")
        return [[int(rows[i]), int(rows[i + 1]), int(rows[i + 2])] for i in range(0, len(rows), 3)]

    out: list[list[int]] = []
    for face in rows:
        idx = [int(i) for i in face]
        if len(idx) < 3:
            continue
        # Fan-triangulate polygons with more than 3 vertices.
        for i in range(1, len(idx) - 1):
            out.append([idx[0], idx[i], idx[i + 1]])
    return out


def compute_vertex_normals(
    vertices: Sequence[Vec3], faces: Sequence[Sequence[int]]
) -> list[list[float]]:
    """Compute area-weighted per-vertex normals.

    Uses numpy when available for speed; otherwise falls back to a pure-Python
    implementation. Returns a list of unit normals, one per vertex.
    """
    if HAS_NUMPY:
        return _compute_vertex_normals_numpy(vertices, faces)
    return _compute_vertex_normals_python(vertices, faces)


def _compute_vertex_normals_numpy(vertices, faces):  # pragma: no cover - needs numpy
    verts = _np.asarray(vertices, dtype=float)
    if len(faces) == 0 or len(verts) == 0:
        return _np.zeros_like(verts).tolist()
    tris = _np.asarray(faces, dtype=int)
    v0 = verts[tris[:, 0]]
    v1 = verts[tris[:, 1]]
    v2 = verts[tris[:, 2]]
    # Cross product magnitude is proportional to triangle area -> area weighting.
    face_normals = _np.cross(v1 - v0, v2 - v0)
    normals = _np.zeros_like(verts)
    for i in range(3):
        _np.add.at(normals, tris[:, i], face_normals)
    lengths = _np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1.0
    return (normals / lengths).tolist()


def _compute_vertex_normals_python(vertices, faces):
    verts = [list(v) for v in vertices]
    normals = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in faces:
        va, vb, vc = verts[a], verts[b], verts[c]
        e1 = [vb[i] - va[i] for i in range(3)]
        e2 = [vc[i] - va[i] for i in range(3)]
        fn = [
            e1[1] * e2[2] - e1[2] * e2[1],
            e1[2] * e2[0] - e1[0] * e2[2],
            e1[0] * e2[1] - e1[1] * e2[0],
        ]
        for idx in (a, b, c):
            for i in range(3):
                normals[idx][i] += fn[i]
    for n in normals:
        length = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
        n[0] /= length
        n[1] /= length
        n[2] /= length
    return normals
