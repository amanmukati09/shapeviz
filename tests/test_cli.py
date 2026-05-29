"""Tests for the argparse CLI (without actually launching a browser)."""

from __future__ import annotations

import shapeviz.cli as cli


def test_info_command(ply_ascii, capsys):
    rc = cli.main(["info", ply_ascii])
    out = capsys.readouterr().out
    assert rc == 0
    assert "vertices:" in out
    assert "faces:" in out
    assert "mesh" in out


def test_info_point_cloud(xyz_file, capsys):
    rc = cli.main(["info", xyz_file])
    out = capsys.readouterr().out
    assert rc == 0
    assert "pointcloud" in out


def test_save_command(ply_ascii, tmp_path, capsys):
    out = tmp_path / "out.html"
    rc = cli.main(["save", ply_ascii, str(out), "--color", "#abcdef"])
    assert rc == 0
    assert out.exists()
    assert "abcdef" in out.read_text(encoding="utf-8").lower()


def test_version_flag(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "shapeviz" in capsys.readouterr().out


def test_no_command_prints_help(capsys):
    rc = cli.main([])
    assert rc == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_compare_needs_two(ply_ascii, capsys):
    rc = cli.main(["compare", ply_ascii])
    assert rc == 2


def test_info_missing_file():
    rc = cli.main(["info", "nope.ply"])
    assert rc == 1
