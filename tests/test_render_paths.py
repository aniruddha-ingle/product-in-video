from __future__ import annotations

from pathlib import Path

import pytest

from piv import paths


def test_defaults_without_env(monkeypatch):
    monkeypatch.delenv("PIV_HOME", raising=False)
    monkeypatch.delenv("CUTOUT_HOME", raising=False)
    assert paths.piv_home() == (Path.home() / ".piv").resolve()
    assert paths.cutout_home() == (Path.home() / ".cutout").resolve()


def test_env_and_subdirs(isolated_homes):
    home = isolated_homes["piv_home"].resolve()
    assert paths.piv_home() == home
    assert paths.runs_dir("r1") == home / "runs" / "r1"
    assert paths.scratch_dir() == home / "scratch"
    assert paths.templates_dir() == home / "templates"
    assert paths.fonts_dir() == home / "fonts"
    assert paths.models_dir() == home / "models"
    assert set(paths.PIV_SUBDIRS) == {"runs", "scratch", "templates", "fonts", "models"}


def test_env_read_at_call_time(monkeypatch, tmp_path):
    monkeypatch.setenv("PIV_HOME", str(tmp_path / "elsewhere"))
    assert paths.runs_dir() == (tmp_path / "elsewhere" / "runs").resolve()


def test_cutout_home_is_read_only(isolated_homes):
    cut = isolated_homes["cutout_home"]
    with pytest.raises(paths.ReadOnlyPathError):
        paths.writable(cut / "catalogue" / "x.json")
    with pytest.raises(paths.ReadOnlyPathError):
        paths.ensure_dir(cut / "new")
    assert not (cut / "new").exists()


def test_cutout_path_stays_inside(isolated_homes):
    root = isolated_homes["cutout_home"].resolve()
    assert paths.cutout_path("catalogue", "a.json") == root / "catalogue" / "a.json"
    with pytest.raises(ValueError):
        paths.cutout_path("..", "escape")


def test_ensure_dir_only_under_piv_home(tmp_path):
    made = paths.ensure_dir(paths.scratch_dir("t"))
    assert made.is_dir()
    with pytest.raises(ValueError):
        paths.ensure_dir(tmp_path / "not-piv-home")
