"""shapeviz — a lightweight 3D mesh and point cloud viewer for the browser.

Load a file, call :func:`view`, and a beautiful interactive 3D viewer opens in
your browser. No Open3D, no VTK, no heavy native dependencies — just pure Python
plus Three.js loaded from a CDN.

Quick start
-----------
    import shapeviz

    shapeviz.view("mesh.ply")
    shapeviz.view("cloud.xyz", mode="pointcloud", point_size=2)
    shapeviz.compare("before.ply", "after.ply")

Inside a Jupyter notebook the viewer renders inline automatically.
"""

from __future__ import annotations

from ._version import __version__
from .core import compare, save_html, view
from .geometry import Geometry, Mesh, PointCloud
from .loaders import SUPPORTED_FORMATS, LoaderError, load

__all__ = [
    "__version__",
    "view",
    "compare",
    "save_html",
    "load",
    "Geometry",
    "Mesh",
    "PointCloud",
    "LoaderError",
    "SUPPORTED_FORMATS",
]
