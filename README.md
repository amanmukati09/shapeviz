# shapeviz

**A lightweight 3D mesh and point cloud viewer that opens an interactive browser tab.**

No Open3D. No VTK. No 500 MB install that breaks every time you change Python
versions. Just `pip install shapeviz`, point it at a file, call `view()`, and a
beautiful interactive 3D viewer opens in your browser — powered by Three.js
loaded straight from a CDN.

```python
import shapeviz

shapeviz.view("mesh.ply")
shapeviz.view("cloud.xyz", mode="pointcloud", point_size=2)
shapeviz.compare("before.ply", "after.ply")   # side by side
```

---

## Why shapeviz?

If you work with 3D geometry in Python — robotics, point-cloud ML, NeRF, mesh
processing, game assets — your options for *just looking at the thing* are
heavy. Open3D and VTK are powerful but large, native, and notoriously fragile
across Python/OS versions.

shapeviz is the opposite:

| | shapeviz | Open3D |
|---|---|---|
| Install size | a few KB | ~500 MB |
| Required dependencies | **zero** | many native libs |
| Rendering | Three.js in your browser | native OpenGL window |
| Works over SSH / in notebooks | ✅ (browser / inline IFrame) | ✗ awkward |
| Breaks on Python upgrade | basically never | often |

numpy and scipy are **optional** — install them only if you want faster mesh
processing. Everything works without them.

---

## Installation

```bash
pip install shapeviz
```

Optional extras:

```bash
pip install "shapeviz[numpy]"   # faster normal computation / heatmaps
pip install "shapeviz[full]"    # numpy + scipy
pip install "shapeviz[dev]"     # contributor tooling (pytest, ruff, build…)
```

Requires Python 3.9+. Works on Windows, macOS, and Linux.

---

## Supported formats

| Extension | Type | ASCII | Binary |
|---|---|:---:|:---:|
| `.ply` | mesh / point cloud | ✅ | ✅ |
| `.obj` | mesh (with vertex colors) | ✅ | — |
| `.stl` | mesh | ✅ | ✅ |
| `.xyz`, `.xyzrgb`, `.pts` | point cloud (XYZ / XYZRGB / XYZ+normals) | ✅ | — |
| `.pcd` | point cloud | ✅ | ✅ |

The loader auto-detects meshes vs. point clouds and reads vertex colors and
normals when present.

---

## Python API

### `view(source, **options)`

Open a single mesh or point cloud.

```python
import shapeviz

# From a file path...
shapeviz.view("bunny.ply")

# ...or from an in-memory object you built yourself.
from shapeviz import Mesh
m = Mesh(vertices=[[0,0,0],[1,0,0],[0,1,0]], faces=[[0,1,2]])
shapeviz.view(m)
```

Common options (all keyword-only):

| Option | Values | Description |
|---|---|---|
| `mode` | `"solid"`, `"wireframe"`, `"pointcloud"`, `"normals"` | initial render mode |
| `color_mode` | `"solid"`, `"vertex"`, `"normals"`, `"heatmap"` | initial coloring |
| `point_size` | float | point size for clouds |
| `color` | hex string, e.g. `"#6cb6ff"` | solid color |
| `background` | hex string | background color |
| `show_axes` | bool | show XYZ axes on start |
| `show_grid` | bool | show the ground grid |
| `compute_normals` | bool | compute per-vertex normals for meshes that lack them |
| `open_browser` | bool | open the system browser (default `True`) |
| `inline` | bool | force/disable inline Jupyter rendering (default: auto) |
| `return_html` | bool | return the raw HTML string instead of viewing |

```python
shapeviz.view("cloud.xyz", mode="pointcloud", point_size=3, color_mode="heatmap")
shapeviz.view("part.stl", color="#ff8866", compute_normals=True)
```

### `compare(*sources, titles=None, **options)`

Show two or more geometries side by side with **synchronised cameras** — rotate
one, they all rotate. Perfect for before/after, ground-truth vs. prediction,
raw vs. filtered.

```python
shapeviz.compare("before.ply", "after.ply")
shapeviz.compare(raw, filtered, meshed, titles=["raw", "filtered", "meshed"])
```

### `save_html(source, path, **options)`

Render to a standalone `.html` file you can email, embed, or open later. (The
only external thing it needs is the Three.js CDN at view time.)

```python
shapeviz.save_html("scan.pcd", "report.html", color_mode="heatmap", point_size=2)
```

### `load(path)`

Just parse a file into geometry without rendering.

```python
g = shapeviz.load("mesh.ply")
print(g)                       # <Mesh 'mesh.ply' vertices=35947 faces=69451 ...>
print(g.num_vertices, g.bounds())
```

---

## Interactive viewer controls

Once the viewer opens, a floating panel gives you:

- **Render mode** — solid · wireframe · point cloud · normals overlay
- **Color mode** — solid color · vertex colors · normals-as-color · heatmap (by Z)
- **Solid color** picker and **point size** slider
- Toggles for **grid**, **axes**, and a **light/dark background**
- **Sync cameras** (in compare mode)
- **Reset view** and **Screenshot** (saves a PNG)

Mouse: **drag** to rotate · **right-drag** to pan · **scroll** to zoom.

---

## Command line

shapeviz installs a `shapeviz` command:

```bash
shapeviz view mesh.ply
shapeviz view cloud.xyz --mode pointcloud --point-size 3 --color-mode heatmap
shapeviz compare before.ply after.ply
shapeviz save mesh.ply out.html --color "#ff8866"
shapeviz info cloud.pcd          # print stats without rendering
```

`shapeviz view`/`compare` start a tiny local HTTP server and open your browser;
press **Ctrl+C** to stop. Add `--no-browser` to start the server without
opening a tab. Run `shapeviz --help` or `shapeviz <command> --help` for all
options.

---

## Jupyter notebooks

Inside a notebook, `view()` and `compare()` render **inline** automatically via
an IFrame — no server, no new tab:

```python
import shapeviz
shapeviz.view("mesh.ply", height=500)
```

Use `inline=False` to force a browser tab instead, or `inline=True` to force
inline rendering outside a notebook.

---

## How it works

1. **Parse** the file in pure Python into a `Mesh` or `PointCloud`.
2. **Serialise** vertices/faces/colors/normals into a compact JSON payload.
3. **Embed** that payload into a self-contained HTML document that pulls
   Three.js from a CDN and builds a `BufferGeometry` in the browser.
4. **Serve** it from Python's built-in `http.server` (or inline it as a
   data-URI IFrame in Jupyter, or write it to disk with `save_html`).

No native rendering, no GPU drivers to fight with — your browser already has a
great WebGL renderer.

---

## Development

```bash
git clone https://github.com/amanmukati09/shapeviz.git
cd shapeviz
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # macOS/Linux
pip install -e ".[dev]"
pytest
ruff check src tests
```

The test suite generates tiny sample files for every format on the fly and runs
both with and without numpy, so it verifies the pure-Python fallbacks too.

---

## License

MIT © Aman Mukati. See [LICENSE](LICENSE).
