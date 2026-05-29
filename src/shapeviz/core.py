"""High-level public API: :func:`view`, :func:`compare`, and :func:`save_html`.

These functions tie the loaders, viewer, and server together and add the
niceties users expect: auto-loading from paths, Jupyter inline rendering,
opening the browser, and saving self-contained HTML files.
"""

from __future__ import annotations

import os
import tempfile
import webbrowser
from typing import Any, Optional, Union

from .geometry import Geometry, Mesh
from .loaders import load
from .server import ViewerServer
from .viewer import build_html

# Geometry or a path to a file that can be loaded into geometry.
GeometryLike = Union[str, os.PathLike, Geometry]


def _resolve(obj: GeometryLike, *, compute_normals: bool = False) -> Geometry:
    """Accept a path or a Geometry and always return a Geometry."""
    if isinstance(obj, Geometry):
        geom = obj
    else:
        geom = load(os.fspath(obj))
    if compute_normals and isinstance(geom, Mesh) and not geom.has_normals:
        geom.compute_normals()
    return geom


def _to_panel(geom: Geometry, title: Optional[str] = None) -> dict[str, Any]:
    return {"geometry": geom.to_dict(), "title": title or geom.name}


def _in_notebook() -> bool:
    """Best-effort detection of an IPython/Jupyter kernel."""
    try:
        from IPython import get_ipython  # type: ignore

        ip = get_ipython()
        if ip is None:
            return False
        return "IPKernelApp" in ip.config  # zmq kernel => notebook/lab
    except Exception:  # noqa: BLE001
        return False


def _build_config(**kwargs: Any) -> dict[str, Any]:
    """Collect only the explicitly-provided (non-None) viewer settings."""
    keys = ("mode", "color_mode", "point_size", "color", "background",
            "show_axes", "show_grid", "title")
    return {k: kwargs[k] for k in keys if kwargs.get(k) is not None}


def view(
    source: GeometryLike,
    *,
    mode: Optional[str] = None,
    color_mode: Optional[str] = None,
    point_size: Optional[float] = None,
    color: Optional[str] = None,
    background: Optional[str] = None,
    show_axes: Optional[bool] = None,
    show_grid: Optional[bool] = None,
    title: Optional[str] = None,
    compute_normals: bool = False,
    inline: Optional[bool] = None,
    width: Union[int, str] = "100%",
    height: int = 600,
    open_browser: bool = True,
    return_html: bool = False,
):
    """Open an interactive 3D viewer for a mesh or point cloud.

    Parameters
    ----------
    source:
        A file path (``.ply``, ``.obj``, ``.stl``, ``.xyz``, ``.pcd`` …) or an
        in-memory :class:`Mesh` / :class:`PointCloud`.
    mode:
        Initial render mode: ``"solid"``, ``"wireframe"``, ``"pointcloud"`` or
        ``"normals"``. Defaults to auto (solid for meshes, points for clouds).
    color_mode:
        ``"solid"``, ``"vertex"``, ``"normals"`` or ``"heatmap"`` (by Z).
    point_size:
        Point size for point-cloud rendering.
    color:
        Hex solid color, e.g. ``"#6cb6ff"``.
    compute_normals:
        Compute per-vertex normals for meshes that lack them.
    inline:
        Force (``True``) or disable (``False``) inline Jupyter rendering. By
        default, detected automatically.
    open_browser:
        Open the system browser (ignored when rendering inline).
    return_html:
        Return the raw HTML string instead of viewing. Useful for tests/saving.

    Returns
    -------
    The HTML string (if ``return_html``), an IPython ``IFrame`` (in notebooks),
    or a :class:`ViewerServer` (desktop), so callers can introspect ``.url``.
    """
    geom = _resolve(source, compute_normals=compute_normals)
    config = _build_config(
        mode=mode, color_mode=color_mode, point_size=point_size, color=color,
        background=background, show_axes=show_axes, show_grid=show_grid,
        title=title or geom.name,
    )
    html = build_html([_to_panel(geom, title)], config)
    return _present(html, inline=inline, width=width, height=height,
                    open_browser=open_browser, return_html=return_html)


def compare(
    *sources: GeometryLike,
    titles: Optional[list[str]] = None,
    mode: Optional[str] = None,
    color_mode: Optional[str] = None,
    point_size: Optional[float] = None,
    color: Optional[str] = None,
    background: Optional[str] = None,
    show_axes: Optional[bool] = None,
    show_grid: Optional[bool] = None,
    title: Optional[str] = None,
    compute_normals: bool = False,
    inline: Optional[bool] = None,
    width: Union[int, str] = "100%",
    height: int = 600,
    open_browser: bool = True,
    return_html: bool = False,
):
    """Show two or more geometries side by side with synchronised cameras.

    Example
    -------
        shapeviz.compare("before.ply", "after.ply")
        shapeviz.compare(a, b, c, titles=["raw", "filtered", "meshed"])
    """
    if len(sources) < 2:
        raise ValueError("compare() needs at least two sources")

    panels = []
    for i, src in enumerate(sources):
        geom = _resolve(src, compute_normals=compute_normals)
        t = titles[i] if titles and i < len(titles) else None
        panels.append(_to_panel(geom, t))

    config = _build_config(
        mode=mode, color_mode=color_mode, point_size=point_size, color=color,
        background=background, show_axes=show_axes, show_grid=show_grid,
        title=title or "shapeviz · compare",
    )
    html = build_html(panels, config)
    return _present(html, inline=inline, width=width, height=height,
                    open_browser=open_browser, return_html=return_html)


def save_html(source: GeometryLike, path: str, **kwargs: Any) -> str:
    """Render ``source`` to a standalone HTML file and return its path.

    Accepts the same keyword arguments as :func:`view` (e.g. ``mode=``,
    ``color=``). The resulting file is fully self-contained except for the
    Three.js CDN script, so it can be shared or embedded anywhere.
    """
    kwargs.pop("return_html", None)
    kwargs.pop("open_browser", None)
    kwargs.pop("inline", None)
    html = view(source, return_html=True, **kwargs)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return os.path.abspath(path)


def _present(html: str, *, inline, width, height, open_browser, return_html):
    if return_html:
        return html

    use_inline = _in_notebook() if inline is None else inline
    if use_inline:
        return _render_inline(html, width, height)

    server = ViewerServer(html).start()
    if open_browser:
        webbrowser.open(server.url)
    return server


def _render_inline(html: str, width, height):
    """Render inside Jupyter via a data-URI IFrame (no server needed)."""
    from urllib.parse import quote

    try:
        from IPython.display import IFrame  # type: ignore
    except Exception:  # noqa: BLE001 - IPython not installed
        # Fall back to writing a temp file and returning its path.
        fd, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(html)
        return path

    src = "data:text/html;charset=utf-8," + quote(html)
    return IFrame(src=src, width=width, height=height)
