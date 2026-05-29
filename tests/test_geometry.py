"""Tests for the geometry containers and normal computation."""

from __future__ import annotations

import math

import pytest

from shapeviz.geometry import Mesh, PointCloud, compute_vertex_normals


def test_pointcloud_basic():
    pc = PointCloud([[0, 0, 0], [1, 2, 3]])
    assert pc.num_vertices == 2
    assert pc.kind == "pointcloud"
    assert not pc.has_colors


def test_flat_vertex_input():
    pc = PointCloud([0, 0, 0, 1, 1, 1])
    assert pc.num_vertices == 2
    assert pc.vertices[1] == [1.0, 1.0, 1.0]


def test_mesh_triangulates_quads():
    # A single quad face should become two triangles.
    m = Mesh([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], faces=[[0, 1, 2, 3]])
    assert m.num_faces == 2


def test_mesh_rejects_bad_face_index():
    with pytest.raises(ValueError):
        Mesh([[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 5]])


def test_color_length_validation():
    with pytest.raises(ValueError):
        PointCloud([[0, 0, 0], [1, 1, 1]], colors=[[1, 0, 0]])


def test_bounds_and_center():
    pc = PointCloud([[-1, -2, -3], [1, 2, 3]])
    mins, maxs = pc.bounds()
    assert mins == [-1, -2, -3]
    assert maxs == [1, 2, 3]
    assert pc.center() == [0, 0, 0]
    assert pc.extent() == 6


def test_to_dict_flattens():
    m = Mesh([[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]])
    d = m.to_dict()
    assert d["type"] == "mesh"
    assert d["vertices"] == [0, 0, 0, 1, 0, 0, 0, 1, 0]
    assert d["faces"] == [0, 1, 2]
    assert "bounds" in d


def test_compute_normals_unit_length():
    # Flat triangle in XY plane -> normal should be +/- Z.
    verts = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
    faces = [[0, 1, 2]]
    normals = compute_vertex_normals(verts, faces)
    assert len(normals) == 3
    for n in normals:
        length = math.sqrt(sum(c * c for c in n))
        assert pytest.approx(length, abs=1e-6) == 1.0
        assert pytest.approx(abs(n[2]), abs=1e-6) == 1.0


def test_mesh_compute_normals_in_place():
    m = Mesh([[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]])
    assert not m.has_normals
    m.compute_normals()
    assert m.has_normals
    assert len(m.normals) == 3
