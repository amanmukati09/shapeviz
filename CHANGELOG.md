# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-29

### Added
- Initial release.
- File loaders for `.ply` (ASCII + binary), `.obj`, `.stl` (ASCII + binary),
  `.xyz` / `.xyzrgb` / `.pts`, and `.pcd` (ASCII + binary).
- Interactive Three.js viewer with orbit/zoom/pan controls.
- Render modes: solid, wireframe, point cloud, normals overlay.
- Color modes: solid color, vertex colors, normals-as-color, heatmap by Z.
- Python API: `shapeviz.view()`, `shapeviz.compare()`, `shapeviz.save_html()`.
- CLI: `shapeviz view | compare | save | info`.
- Inline Jupyter rendering via data-URI IFrame.
- Optional numpy acceleration for normal computation.
- Full pytest suite and GitHub Actions PyPI auto-publish on tag.

[Unreleased]: https://github.com/amanmukati09/shapeviz/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/amanmukati09/shapeviz/releases/tag/v0.1.0
