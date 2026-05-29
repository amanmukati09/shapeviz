# shapeviz — Complete Build & Publish Guide (Windows 11, 0% → `pip install shapeviz`)

This is the **full, click-by-click** walkthrough to take the `shapeviz` project
from an empty folder all the way to a package anyone can install with
`pip install shapeviz`. It is written for **Windows 11** using **PowerShell**,
**VS Code (Pylance)**, **git/GitHub**, and **PyPI**.

> You already have everything in this ZIP. So most "create the file" work is
> done — your job is mostly: set up Python correctly, run it locally, push to
> GitHub, and publish. Follow the steps **in order**. Anything you must type is
> in a code block. Lines starting with `#` are comments — don't type them.

---

## Table of contents

0. [Before you start — accounts & tools](#0-before-you-start)
1. [Install a REAL Python (important on Windows)](#1-install-a-real-python)
2. [Put the project on disk](#2-put-the-project-on-disk)
3. [Create & activate a virtual environment](#3-create--activate-a-virtual-environment)
4. [Install shapeviz in editable mode](#4-install-shapeviz-in-editable-mode)
5. [Run the test suite](#5-run-the-test-suite)
6. [Try the viewer for real](#6-try-the-viewer-for-real)
7. [Set up VS Code + Pylance](#7-set-up-vs-code--pylance)
8. [Personalise the package metadata](#8-personalise-the-package-metadata)
9. [Initialise git and push to GitHub](#9-initialise-git-and-push-to-github)
10. [Build the distribution locally](#10-build-the-distribution-locally)
11. [Publish to TestPyPI (rehearsal)](#11-publish-to-testpypi-rehearsal)
12. [Publish to real PyPI](#12-publish-to-real-pypi)
13. [Automate publishing with GitHub Actions (on git tag)](#13-automate-publishing-with-github-actions)
14. [Releasing future versions](#14-releasing-future-versions)
15. [Troubleshooting](#15-troubleshooting)
16. [Project file map](#16-project-file-map)

---

## 0. Before you start

You need these accounts/tools (free):

- **Python 3.9+** (you said 3.14 — great). See step 1, there's a Windows gotcha.
- **Git** — https://git-scm.com/download/win (install with defaults).
- **GitHub account** — https://github.com
- **PyPI account** — https://pypi.org/account/register/
- **TestPyPI account** — https://test.pypi.org/account/register/
  (separate from PyPI — register on both)
- **VS Code** with the **Python** and **Pylance** extensions.

Enable 2FA on both PyPI and TestPyPI (required to upload).

---

## 1. Install a REAL Python

> ⚠️ **Windows gotcha:** Out of the box, typing `python` in PowerShell often
> opens the **Microsoft Store stub** (a fake 0-byte `python.exe`) instead of a
> real interpreter. We must use a real install from python.org.

1. Download Python from https://www.python.org/downloads/windows/
   (3.12 or 3.13 are rock-solid choices; 3.14 is fine too).
2. Run the installer. On the **first screen**:
   - ✅ Check **"Add python.exe to PATH"** (bottom of the window).
   - Click **Install Now**.
3. **Disable the Store alias** so `python` points to the real thing:
   `Settings → Apps → Advanced app settings → App execution aliases` →
   turn **OFF** both `python.exe` and `python3.exe`.
4. **Close and reopen PowerShell**, then verify:

```powershell
python --version
# should print e.g.  Python 3.13.x   (NOT open the Microsoft Store)

py --version
# the 'py' launcher also works and is handy for picking versions
```

If `python --version` still misbehaves, use `py` everywhere below in place of
`python` (e.g. `py -m venv .venv`).

---

## 2. Put the project on disk

1. **Extract the ZIP** (`shapeviz.zip`) somewhere sensible, e.g.
   `C:\Users\<you>\code\shapeviz`.
2. Open PowerShell and go into the project folder (the one that contains
   `pyproject.toml`):

```powershell
cd "C:\Users\<you>\code\shapeviz"
dir
# You should see: pyproject.toml, README.md, src, tests, .github, examples, etc.
```

> Keep this PowerShell window open — every command below runs from this folder.

---

## 3. Create & activate a virtual environment

A venv keeps shapeviz's tooling isolated from your global Python.

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`.

> **If you get** *"running scripts is disabled on this system"*, allow scripts
> for your user once, then re-run the activate line:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

Upgrade pip inside the venv:

```powershell
python -m pip install --upgrade pip
```

To leave the venv later: `deactivate`. To return: re-run the Activate line.

---

## 4. Install shapeviz in editable mode

"Editable" (`-e`) means your code changes take effect immediately without
reinstalling. The `[dev]` extra pulls in pytest, ruff, build, twine, numpy.

```powershell
pip install -e ".[dev]"
```

Verify it imported and the CLI is wired up:

```powershell
python -c "import shapeviz; print(shapeviz.__version__)"
# -> 0.1.0

shapeviz --version
# -> shapeviz 0.1.0

shapeviz --help
```

---

## 5. Run the test suite

```powershell
pytest
```

You should see all tests pass. For coverage:

```powershell
pytest --cov=shapeviz --cov-report=term-missing
```

Lint (style/quality) check:

```powershell
ruff check src tests
```

> The tests generate tiny sample `.ply/.obj/.stl/.xyz/.pcd` files on the fly,
> so nothing extra is needed. They also validate the pure-Python path that runs
> when numpy isn't installed.

---

## 6. Try the viewer for real

Generate a demo mesh + cloud and open them in your browser:

```powershell
python examples\quickstart.py
```

Three browser tabs/windows open: a heat-mapped sphere mesh, a colorful point
cloud, and a side-by-side comparison. Use the floating control panel to switch
render/color modes, toggle wireframe, drag the point-size slider, and take a
screenshot.

Try the CLI on your own files:

```powershell
shapeviz view path\to\your_mesh.ply
shapeviz view path\to\cloud.xyz --mode pointcloud --point-size 3 --color-mode heatmap
shapeviz compare before.ply after.ply
shapeviz save mesh.ply report.html --color "#ff8866"
shapeviz info cloud.pcd
```

(`shapeviz view`/`compare` run a tiny local server; press **Ctrl+C** to stop.)

There's also a pre-rendered `examples\sample_viewer.html` you can just
double-click to open.

---

## 7. Set up VS Code + Pylance

1. `code .` (from the project folder) or open the folder in VS Code.
2. Press **Ctrl+Shift+P** → **"Python: Select Interpreter"** → choose the one
   inside `.venv` (path ends with `.venv\Scripts\python.exe`).
3. Pylance now resolves `import shapeviz` and gives you autocomplete + type
   hints. The code uses `from __future__ import annotations` and type hints
   throughout, so Pylance is happy out of the box.
4. (Optional) The repo's `.gitignore` already excludes `.vscode/`, so any local
   editor settings you add won't be committed.

> If Pylance shows "import could not be resolved", make sure you picked the
> `.venv` interpreter (step 2) and that you ran `pip install -e ".[dev]"`.

---

## 8. Personalise the package metadata

> **PyPI names are globally unique.** First check that `shapeviz` is free:
> open https://pypi.org/project/shapeviz/ — if it 404s, it's available. If it's
> taken, pick another name (e.g. `shapeviz3d`) and change `name = "..."` in
> `pyproject.toml` **and** rename the folder `src/shapeviz` accordingly (and the
> imports). Easiest is to keep `shapeviz` if it's free.

Open `pyproject.toml` and edit:

- `authors` — your name/email (currently set to yours).
- `[project.urls]` — replace every `yourusername` with your real GitHub handle.

Also replace `yourusername` in:
- `README.md` (Development + License sections)
- `CHANGELOG.md` (the two links at the bottom)

> The `version` lives in **two** places that must match: `pyproject.toml`
> (`version = "0.1.0"`) and `src/shapeviz/_version.py`. Keep them in sync.

---

## 9. Initialise git and push to GitHub

Set your git identity once (if you never have):

```powershell
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

Initialise the repo and make the first commit:

```powershell
git init
git branch -M main
git add .
git status          # sanity check: .venv and dist should NOT appear (gitignored)
git commit -m "Initial commit: shapeviz 0.1.0"
```

Create the GitHub repo and push. **Option A — GitHub CLI** (easiest):

```powershell
# install once from https://cli.github.com/ , then:
gh auth login
gh repo create shapeviz --public --source=. --remote=origin --push
```

**Option B — via the website:**

1. Go to https://github.com/new , name it `shapeviz`, **Public**, **don't** add
   a README/license (you already have them). Click **Create repository**.
2. Connect and push (replace `yourusername`):

```powershell
git remote add origin https://github.com/yourusername/shapeviz.git
git push -u origin main
```

After pushing, the **tests** GitHub Action runs automatically (see the
**Actions** tab). It tests on Windows/macOS/Linux across several Python
versions.

---

## 10. Build the distribution locally

This produces the two files PyPI wants: a `.whl` (wheel) and a `.tar.gz`
(source dist).

```powershell
python -m build
```

You'll get a `dist\` folder:

```
dist\shapeviz-0.1.0-py3-none-any.whl
dist\shapeviz-0.1.0.tar.gz
```

Validate them (checks the README renders on PyPI, metadata is valid):

```powershell
twine check dist/*
# both lines should say PASSED
```

---

## 11. Publish to TestPyPI (rehearsal)

Always rehearse on TestPyPI first — it's a throwaway clone of PyPI.

1. Create an API token: https://test.pypi.org/manage/account/token/ →
   "Add API token", scope **Entire account** (you can narrow it later). Copy the
   token (starts with `pypi-...`) — you only see it once.

2. Upload:

```powershell
twine upload --repository testpypi dist/*
# Username:  __token__
# Password:  <paste the TestPyPI token, including the pypi- prefix>
```

3. Test-install it into a **fresh** venv to prove it works for end users.
   TestPyPI doesn't host real deps, so allow falling back to real PyPI for any:

```powershell
# in a NEW folder / new PowerShell window:
python -m venv testenv
.\testenv\Scripts\Activate.ps1
pip install --index-url https://test.pypi.org/simple/ `
            --extra-index-url https://pypi.org/simple/ shapeviz
shapeviz --version
python -c "import shapeviz; print('works:', shapeviz.__version__)"
deactivate
```

> The backtick `` ` `` is PowerShell's line-continuation character.

---

## 12. Publish to real PyPI

Once the TestPyPI install works:

1. Create a **PyPI** token: https://pypi.org/manage/account/token/ (same steps).
2. Upload:

```powershell
twine upload dist/*
# Username:  __token__
# Password:  <paste the PyPI token>
```

3. 🎉 It's live. Verify:

```powershell
pip install shapeviz
```

Your project page: `https://pypi.org/project/shapeviz/`.

> **Tip — save your credentials** so you don't paste tokens each time. Create
> `%USERPROFILE%\.pypirc` (i.e. `C:\Users\<you>\.pypirc`):
> ```ini
> [pypi]
>   username = __token__
>   password = pypi-XXXX...your-pypi-token...
>
> [testpypi]
>   username = __token__
>   password = pypi-XXXX...your-testpypi-token...
> ```
> Keep this file private (never commit it).

---

## 13. Automate publishing with GitHub Actions

The repo ships `.github/workflows/publish.yml`, which **builds and publishes
automatically whenever you push a version tag** like `v0.1.0`. Pick ONE auth
method:

### Option A — Trusted Publishing (recommended, no tokens/secrets)

PyPI can trust your GitHub repo directly via OIDC — nothing to store.

1. On **PyPI**: https://pypi.org/manage/account/publishing/ → "Add a pending
   publisher". Fill in:
   - PyPI Project Name: `shapeviz`
   - Owner: your GitHub username
   - Repository name: `shapeviz`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
2. On **TestPyPI**: https://test.pypi.org/manage/account/publishing/ → same, but
   Environment name: `testpypi`.
3. In GitHub: **Settings → Environments** → create two environments named
   exactly `pypi` and `testpypi` (no secrets needed).
4. Done — the workflow's `id-token: write` permission handles the rest.

### Option B — API tokens (if you prefer)

1. In `.github/workflows/publish.yml`, uncomment the two `password:` lines and
   comment out / ignore the trusted-publishing note.
2. In GitHub: **Settings → Secrets and variables → Actions → New repository
   secret**, add:
   - `PYPI_API_TOKEN` = your PyPI token
   - `TEST_PYPI_API_TOKEN` = your TestPyPI token

### Trigger a release

```powershell
git tag v0.1.0
git push origin v0.1.0
```

Watch the **Actions** tab: it builds, publishes to TestPyPI, then to PyPI.

---

## 14. Releasing future versions

Every new release:

1. Make your code changes; update `CHANGELOG.md`.
2. Bump the version in **both** `pyproject.toml` and `src/shapeviz/_version.py`
   (e.g. `0.1.0` → `0.1.1`). They must match.
3. Commit:
   ```powershell
   git add .
   git commit -m "Release 0.1.1"
   git push
   ```
4. Tag and push the tag to publish:
   ```powershell
   git tag v0.1.1
   git push origin v0.1.1
   ```

> PyPI **never lets you re-upload the same version**. If an upload fails after
> the file was accepted, bump to a new version — you can't overwrite.

---

## 15. Troubleshooting

| Symptom | Fix |
|---|---|
| `python` opens Microsoft Store | Disable the app-execution aliases (step 1.3) or use `py`. |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (step 3). |
| `No module named shapeviz` | Activate the venv, then `pip install -e ".[dev]"`. In VS Code, select the `.venv` interpreter. |
| Pylance "import could not be resolved" | Pick the `.venv` interpreter (Ctrl+Shift+P → Python: Select Interpreter). |
| Viewer tab is blank | You need internet the first time (Three.js loads from a CDN). Check the browser console (F12) for errors. |
| `twine check` fails on README | Ensure `readme = "README.md"` in `pyproject.toml` and the file exists. |
| `403 Forbidden` on upload | Wrong token, or the project name is taken by someone else. Use `__token__` as the username and the full `pypi-...` token as the password. |
| `400 File already exists` | That version was already uploaded — bump the version number. |
| GitHub Action publish fails | For Trusted Publishing, confirm the environment names (`pypi`/`testpypi`) and workflow filename match exactly what you registered on PyPI. |
| Name `shapeviz` already taken on PyPI | Rename in `pyproject.toml` + folder `src/shapeviz` (step 8). |

---

## 16. Project file map

```
shapeviz/
├── pyproject.toml            # package metadata, deps, build config, CLI entry point
├── README.md                 # docs + PyPI long description (same file)
├── LICENSE                   # MIT
├── CHANGELOG.md              # version history
├── MANIFEST.in               # extra files for the source distribution
├── INSTRUCTIONS.md           # this guide
├── .gitignore
├── .github/workflows/
│   ├── tests.yml             # CI: lint + pytest on every push/PR
│   └── publish.yml           # CD: build + publish to PyPI on git tag
├── src/shapeviz/
│   ├── __init__.py           # public API exports (view, compare, load, ...)
│   ├── _version.py           # single source of version truth
│   ├── geometry.py           # Mesh / PointCloud containers + normals
│   ├── loaders.py            # .ply .obj .stl .xyz .pcd parsers
│   ├── viewer.py             # self-contained Three.js HTML generator
│   ├── server.py             # tiny background http.server
│   ├── core.py               # view() / compare() / save_html() orchestration
│   └── cli.py                # argparse command-line interface
├── tests/
│   ├── conftest.py           # generates sample files for every format
│   ├── test_loaders.py
│   ├── test_geometry.py
│   ├── test_viewer.py
│   └── test_cli.py
└── examples/
    ├── quickstart.py         # generate + view a demo mesh and point cloud
    └── sample_viewer.html    # pre-rendered viewer you can just open
```

That's the whole journey — empty folder to `pip install shapeviz`. Happy
shipping! 🚀
