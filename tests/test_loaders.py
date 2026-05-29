"""Tests for the file loaders across every supported format."""

from __future__ import annotations

import pytest

from shapeviz.geometry import Mesh, PointCloud
from shapeviz.loaders import LoaderError, load


def test_load_ply_ascii(ply_ascii):
    g = load(ply_ascii)
    assert isinstance(g, Mesh)
    assert g.num_vertices == 8
    assert g.num_faces == 12
    assert g.has_colors


def test_load_ply_binary(ply_binary):
    g = load(ply_binary)
    assert isinstance(g, Mesh)
    assert g.num_vertices == 8
    assert g.num_faces == 12


def test_ply_ascii_and_binary_match(ply_ascii, ply_binary):
    a = load(ply_ascii)
    b = load(ply_binary)
    assert a.num_vertices == b.num_vertices
    assert a.num_faces == b.num_faces
    # Vertex positions should be identical.
    assert a.vertices == b.vertices


def test_load_obj(obj_file):
    g = load(obj_file)
    assert isinstance(g, Mesh)
    assert g.num_vertices == 8
    assert g.num_faces == 12


def test_load_stl_ascii(stl_ascii):
    g = load(stl_ascii)
    assert isinstance(g, Mesh)
    # After de-duplication the cube has 8 unique corners.
    assert g.num_vertices == 8
    assert g.num_faces == 12


def test_load_stl_binary(stl_binary):
    g = load(stl_binary)
    assert isinstance(g, Mesh)
    assert g.num_vertices == 8
    assert g.num_faces == 12


def test_load_xyz(xyz_file):
    g = load(xyz_file)
    assert isinstance(g, PointCloud)
    assert g.num_vertices == 8
    assert not g.has_colors


def test_load_xyzrgb(xyzrgb_file):
    g = load(xyzrgb_file)
    assert isinstance(g, PointCloud)
    assert g.num_vertices == 8
    assert g.has_colors
    for c in g.colors:
        assert all(0.0 <= ch <= 1.0 for ch in c)


def test_load_pcd_ascii(pcd_ascii):
    g = load(pcd_ascii)
    assert isinstance(g, PointCloud)
    assert g.num_vertices == 8


def test_unsupported_format(tmp_path):
    bad = tmp_path / "thing.gltf"
    bad.write_text("not real")
    with pytest.raises(LoaderError):
        load(str(bad))


def test_missing_file():
    with pytest.raises(LoaderError):
        load("does_not_exist.ply")


def test_format_override(xyz_file, tmp_path):
    # Copy to an extensionless name and force the format.
    renamed = tmp_path / "noext"
    renamed.write_text(open(xyz_file).read())
    g = load(str(renamed), format="xyz")
    assert g.num_vertices == 8
