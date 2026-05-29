"""Tests for HTML generation and the high-level view/compare/save API."""

from __future__ import annotations

import json

from shapeviz import compare, save_html, view
from shapeviz.geometry import Mesh, PointCloud
from shapeviz.viewer import build_html


def _panel(geom):
    return {"geometry": geom.to_dict(), "title": geom.name}


def test_build_html_contains_payload():
    m = Mesh([[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]], name="tri")
    html = build_html([_panel(m)])
    assert "<!DOCTYPE html>" in html
    assert "shapeviz-data" in html
    assert "three.module.js" in html
    assert "OrbitControls" in html


def test_build_html_payload_roundtrips():
    pc = PointCloud([[0, 0, 0], [1, 1, 1]], name="pc")
    html = build_html([_panel(pc)])
    start = html.index('type="application/json">') + len('type="application/json">')
    end = html.index("</script>", start)
    payload = json.loads(html[start:end].replace("<\\/", "</"))
    assert payload["panels"][0]["geometry"]["type"] == "pointcloud"
    assert payload["panels"][0]["geometry"]["vertices"] == [0, 0, 0, 1, 1, 1]


def test_view_return_html_from_path(ply_ascii):
    html = view(ply_ascii, return_html=True)
    assert "<!DOCTYPE html>" in html


def test_view_with_geometry_object():
    m = Mesh([[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]])
    html = view(m, return_html=True, mode="wireframe", color="#ff0000")
    assert "wireframe" in html  # config serialised in payload
    assert "ff0000" in html.lower()


def test_compare_two_files(ply_ascii, obj_file):
    html = compare(ply_ascii, obj_file, return_html=True)
    payload_start = html.index('type="application/json">')
    assert html.count('"title"') >= 2
    assert "<!DOCTYPE html>" in html


def test_compare_requires_two():
    import pytest

    m = Mesh([[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]])
    with pytest.raises(ValueError):
        compare(m, return_html=True)


def test_save_html(ply_ascii, tmp_path):
    out = tmp_path / "viewer.html"
    path = save_html(ply_ascii, str(out))
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert path.endswith("viewer.html")


def test_compute_normals_flows_into_html(ply_ascii):
    html = view(ply_ascii, compute_normals=True, return_html=True)
    assert "normals" in html
