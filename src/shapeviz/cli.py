"""Command-line interface for shapeviz.

Usage examples::

    shapeviz view mesh.ply
    shapeviz view cloud.xyz --mode pointcloud --point-size 3
    shapeviz compare before.ply after.ply
    shapeviz save mesh.ply out.html --color "#ff8866"
    shapeviz info cloud.pcd

Run ``shapeviz --help`` for the full option list.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from . import __version__
from .geometry import Mesh
from .loaders import SUPPORTED_FORMATS, LoaderError, load


def _add_common_view_opts(p: argparse.ArgumentParser) -> None:
    p.add_argument("--mode", choices=["auto", "solid", "wireframe", "pointcloud", "normals"],
                   default=None, help="initial render mode")
    p.add_argument("--color-mode", choices=["auto", "solid", "vertex", "normals", "heatmap"],
                   default=None, help="initial color mode")
    p.add_argument("--point-size", type=float, default=None, help="point size for clouds")
    p.add_argument("--color", default=None, help="solid color as hex, e.g. #6cb6ff")
    p.add_argument("--background", default=None, help="background color as hex")
    p.add_argument("--axes", action="store_true", help="show XYZ axes on start")
    p.add_argument("--no-grid", action="store_true", help="hide the ground grid")
    p.add_argument("--compute-normals", action="store_true",
                   help="compute per-vertex normals for meshes that lack them")
    p.add_argument("--no-browser", action="store_true",
                   help="start the server but do not open a browser")


def _view_kwargs(args: argparse.Namespace) -> dict:
    return {
        "mode": args.mode,
        "color_mode": args.color_mode,
        "point_size": args.point_size,
        "color": args.color,
        "background": args.background,
        "show_axes": True if args.axes else None,
        "show_grid": False if args.no_grid else None,
        "compute_normals": args.compute_normals,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shapeviz",
        description="Lightweight 3D mesh and point cloud viewer in your browser.",
    )
    parser.add_argument("--version", action="version", version=f"shapeviz {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # view
    pv = sub.add_parser("view", help="open a single file in the viewer")
    pv.add_argument("file", help="path to a 3D file " + f"({', '.join(SUPPORTED_FORMATS)})")
    _add_common_view_opts(pv)

    # compare
    pc = sub.add_parser("compare", help="open two or more files side by side")
    pc.add_argument("files", nargs="+", help="two or more 3D files")
    _add_common_view_opts(pc)

    # save
    ps = sub.add_parser("save", help="render a file to a standalone HTML document")
    ps.add_argument("file", help="path to a 3D file")
    ps.add_argument("output", help="output .html path")
    _add_common_view_opts(ps)

    # info
    pi = sub.add_parser("info", help="print stats about a file without rendering")
    pi.add_argument("file", help="path to a 3D file")

    return parser


def _cmd_view(args) -> int:
    from . import view

    server = view(args.file, open_browser=not args.no_browser,
                  inline=False, **_view_kwargs(args))
    return _hold(server)


def _cmd_compare(args) -> int:
    from . import compare

    if len(args.files) < 2:
        print("error: compare needs at least two files", file=sys.stderr)
        return 2
    server = compare(*args.files, open_browser=not args.no_browser,
                     inline=False, **_view_kwargs(args))
    return _hold(server)


def _cmd_save(args) -> int:
    from . import save_html

    kw = _view_kwargs(args)
    kw.pop("compute_normals", None)
    out = save_html(args.file, args.output,
                    compute_normals=args.compute_normals, **kw)
    print(f"saved viewer to {out}")
    return 0


def _cmd_info(args) -> int:
    geom = load(args.file)
    mins, maxs = geom.bounds()
    print(f"file:      {args.file}")
    print(f"type:      {geom.kind}")
    print(f"vertices:  {geom.num_vertices:,}")
    if isinstance(geom, Mesh):
        print(f"faces:     {geom.num_faces:,}")
    print(f"colors:    {'yes' if geom.has_colors else 'no'}")
    print(f"normals:   {'yes' if geom.has_normals else 'no'}")
    print(f"bounds min: ({mins[0]:.4g}, {mins[1]:.4g}, {mins[2]:.4g})")
    print(f"bounds max: ({maxs[0]:.4g}, {maxs[1]:.4g}, {maxs[2]:.4g})")
    return 0


def _hold(server) -> int:
    """Keep the process alive while the viewer server runs."""
    print(f"shapeviz viewer running at {server.url}")
    print("press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nshutting down.")
        server.stop()
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    handlers = {
        "view": _cmd_view,
        "compare": _cmd_compare,
        "save": _cmd_save,
        "info": _cmd_info,
    }
    try:
        return handlers[args.command](args)
    except LoaderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
